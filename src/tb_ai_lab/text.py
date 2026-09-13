# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0.

"""Canonical text, source-verifiable chunking, entities, and local vectors."""

from __future__ import annotations

from collections.abc import Iterable
import math
import re
import unicodedata
from urllib.parse import quote

from .contracts import Chunk, Document


WORD_RE = re.compile(r"[^\W_]{2,}", re.UNICODE)
IDENTIFIER_RE = re.compile(r"\b(?=[A-Z0-9-]{5,}\b)(?=[A-Z0-9-]*[A-Z])(?=[A-Z0-9-]*\d)[A-Z0-9]+(?:-[A-Z0-9]+)+\b")
DATE_RE = re.compile(r"\b(?:20\d{2})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])\b")
AMOUNT_RE = re.compile(r"\b(?:USD|EUR|GBP|INR)\s*\d+(?:,\d{3})*(?:\.\d{2})?\b", re.IGNORECASE)
INJECTION_RE = re.compile(
    r"(?:ignore (?:all |the )?(?:previous|system)|system prompt|developer message|"
    r"execute (?:this|the following)|call (?:a |the )?tool|exfiltrate)",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)")
HEADING_RE = re.compile(
    r"^(?:#{1,6}\s+|\d+(?:\.\d+)*[.)]\s+|[A-Z][A-Za-z0-9/& -]{2,}:)(.+)$"
)
SENTENCE_RE = re.compile(r"[^\n.!?]+(?:[.!?]+(?=\s|$)|(?=\n|$))")


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))
    value = "".join(
        character
        for character in value
        if character in "\n\t" or unicodedata.category(character) != "Cc"
    )
    lines = [re.sub(r"[ \t]+$", "", line) for line in value.split("\n")]
    return "\n".join(lines).strip()


def terms(value: str) -> list[str]:
    return [match.group(0).casefold() for match in WORD_RE.finditer(value)]


def exact_entities(value: str, limit: int = 256) -> list[tuple[str, str]]:
    entities: list[tuple[str, str]] = []
    entities.extend(("identifier", match.group(0).upper()) for match in IDENTIFIER_RE.finditer(value))
    entities.extend(("date", match.group(0)) for match in DATE_RE.finditer(value))
    entities.extend(
        ("amount", re.sub(r"\s+", " ", match.group(0).upper()))
        for match in AMOUNT_RE.finditer(value)
    )
    return list(dict.fromkeys(entities))[: max(0, min(limit, 4096))]


def _chunk_id(document: Document, ordinal: int) -> str:
    scope = "/".join(
        quote(value, safe="")
        for value in (document.tenant, document.collection, document.id)
    )
    return f"{scope}:chunk:{ordinal}"


def contains_prompt_injection(value: str) -> bool:
    return bool(INJECTION_RE.search(value))


def detect_pii(value: str) -> dict[str, list[str]]:
    """Return bounded deterministic PII matches for policy/reporting."""
    return {
        "emails": list(dict.fromkeys(match.group(0) for match in EMAIL_RE.finditer(value)))[:20],
        "phones": list(dict.fromkeys(match.group(0) for match in PHONE_RE.finditer(value)))[:20],
    }


def _section_for_offset(body: str, offset: int) -> str:
    before = body[max(0, offset - 6000) : offset].splitlines()
    for line in reversed(before):
        line = line.strip()
        if not line or len(line) > 160:
            continue
        match = HEADING_RE.match(line)
        if match:
            return (match.group(1) or line).strip()[:160]
        words = line.split()
        if 4 <= len(line) <= 80 and len(words) <= 10 and line[0].isupper():
            return line
    for line in body[offset : offset + 1200].splitlines():
        match = HEADING_RE.match(line.strip())
        if match:
            return (match.group(1) or line).strip()[:160]
    return ""


def _context_header(document: Document) -> str:
    fields = [
        f"Title: {document.title}" if document.title else "",
        f"Date: {document.timestamp}" if document.timestamp else "",
        f"Category: {document.metadata.get('category', '')}"
        if document.metadata.get("category")
        else "",
    ]
    return " ".join(item for item in fields if item)[:1200]


def fixed_chunks(
    document: Document,
    chunk_chars: int = 1200,
    overlap: int = 180,
    limit: int = 24,
    source_cap: int | None = 20_000,
) -> list[Chunk]:
    body = document.text if source_cap is None else document.text[:source_cap]
    header = _context_header(document)
    chunks: list[Chunk] = []
    start = 0
    while start < len(body) and len(chunks) < limit:
        end = min(start + chunk_chars, len(body))
        if end < len(body):
            boundary = body.rfind(" ", start, end + 1)
            if boundary > start + chunk_chars // 2:
                end = boundary
        raw = body[start:end]
        leading = len(raw) - len(raw.lstrip())
        trailing = len(raw) - len(raw.rstrip())
        passage_start = start + leading
        passage_end = max(passage_start, end - trailing)
        passage = body[passage_start:passage_end]
        if passage:
            section = _section_for_offset(body, passage_start)
            contextual = "\n".join(
                part
                for part in (
                    header,
                    f"Section: {section}" if section else "",
                    f"Passage {len(chunks) + 1}: {re.sub(r'\s+', ' ', passage)}",
                )
                if part
            )
            chunks.append(
                Chunk(
                    id=_chunk_id(document, len(chunks)),
                    document_id=document.id,
                    tenant=document.tenant,
                    collection=document.collection,
                    ordinal=len(chunks),
                    text=passage,
                    contextual_text=contextual,
                    start=passage_start,
                    end=passage_end,
                    section=section,
                )
            )
        if end >= len(body):
            break
        next_start = max(0, end - overlap)
        start = next_start if next_start > start else end
    return chunks


def structure_aware_chunks(
    document: Document,
    chunk_chars: int = 1200,
    overlap: int = 180,
    limit: int = 4096,
) -> list[Chunk]:
    """Chunk the complete document, preferring paragraph and line boundaries."""
    body = document.text
    chunks: list[Chunk] = []
    start = 0
    while start < len(body) and len(chunks) < limit:
        target = min(start + chunk_chars, len(body))
        end = target
        if target < len(body):
            floor = start + chunk_chars // 2
            candidates = [body.rfind("\n\n", floor, target + 1), body.rfind("\n", floor, target + 1), body.rfind(". ", floor, target + 1), body.rfind(" ", floor, target + 1)]
            boundary = max(candidates)
            if boundary >= floor:
                end = boundary + (2 if body[boundary : boundary + 2] in {"\n\n", ". "} else 1)
        raw = body[start:end]
        leading = len(raw) - len(raw.lstrip())
        trailing = len(raw) - len(raw.rstrip())
        passage_start = start + leading
        passage_end = max(passage_start, end - trailing)
        passage = body[passage_start:passage_end]
        if passage:
            section = _section_for_offset(body, passage_start)
            chunks.append(
                Chunk(
                    id=_chunk_id(document, len(chunks)),
                    document_id=document.id,
                    tenant=document.tenant,
                    collection=document.collection,
                    ordinal=len(chunks),
                    text=passage,
                    contextual_text="\n".join(
                        part
                        for part in (
                            _context_header(document),
                            f"Section: {section}" if section else "",
                            f"Passage {len(chunks) + 1}: {re.sub(r'\s+', ' ', passage)}",
                        )
                        if part
                    ),
                    start=passage_start,
                    end=passage_end,
                    section=section,
                )
            )
        if end >= len(body):
            break
        next_start = max(0, end - overlap)
        start = next_start if next_start > start else end
    return chunks


def sentence_window_chunks(
    document: Document,
    parent_chars: int = 1200,
    limit: int = 4096,
) -> list[Chunk]:
    """Index sentence-sized children while returning source-backed parent blocks."""
    parents = structure_aware_chunks(document, parent_chars, 0, 4096)
    chunks: list[Chunk] = []
    header = _context_header(document)
    previous_parent_end = 0
    for parent in parents:
        parent_start = previous_parent_end
        parent_text = document.text[parent_start : parent.end]
        previous_parent_end = parent.end
        for match in SENTENCE_RE.finditer(parent.text):
            raw = match.group(0)
            leading = len(raw) - len(raw.lstrip())
            trailing = len(raw) - len(raw.rstrip())
            child_start = match.start() + leading
            child_end = match.end() - trailing
            if child_end <= child_start:
                continue
            child = parent.text[child_start:child_end]
            contextual_text = "\n".join(
                part
                for part in (
                    header,
                    f"Section: {parent.section}" if parent.section else "",
                    f"Retrieval sentence: {re.sub(r'\s+', ' ', child)}",
                )
                if part
            )
            chunks.append(
                Chunk(
                    id=_chunk_id(document, len(chunks)),
                    document_id=document.id,
                    tenant=document.tenant,
                    collection=document.collection,
                    ordinal=len(chunks),
                    text=parent_text,
                    contextual_text=contextual_text,
                    start=parent_start,
                    end=parent.end,
                    section=parent.section,
                    retrieval_text=child,
                )
            )
            if len(chunks) >= limit:
                return chunks
    return chunks


def chunk_document(
    document: Document,
    mode: str,
    chunk_chars: int,
    overlap: int,
    limit: int,
) -> list[Chunk]:
    if mode == "fixed":
        return fixed_chunks(document, chunk_chars, overlap, limit, 20_000)
    if mode == "structure-aware":
        return structure_aware_chunks(document, chunk_chars, overlap, limit)
    if mode == "sentence-window":
        return sentence_window_chunks(document, chunk_chars, limit)
    raise ValueError(f"Unsupported chunking mode: {mode}")


def verify_chunks(document: Document, chunks: Iterable[Chunk]) -> None:
    previous_start = -1
    for chunk in chunks:
        if chunk.document_id != document.id or chunk.tenant != document.tenant or chunk.collection != document.collection:
            raise ValueError("Chunk escaped its source document or scope")
        if document.text[chunk.start : chunk.end] != chunk.text:
            raise ValueError(f"Source span mismatch for {chunk.id}")
        if chunk.start < previous_start:
            raise ValueError("Chunk order is not monotonic")
        previous_start = chunk.start


def local_embedding(value: str, dimensions: int = 32) -> list[float]:
    vector = [0.0] * dimensions
    for word in re.split(r"\W+", value.casefold(), flags=re.UNICODE):
        if len(word) < 2:
            continue
        word_hash = 0
        for character in word:
            word_hash = ((word_hash * 31) + ord(character)) & 0xFFFFFFFF
        vector[word_hash % dimensions] += 1.0
    return vector


def cosine(left: list[float], right: list[float]) -> float:
    if not left or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_magnitude = sum(value * value for value in left)
    right_magnitude = sum(value * value for value in right)
    if not left_magnitude or not right_magnitude:
        return 0.0
    return dot / math.sqrt(left_magnitude * right_magnitude)


def _projection_sign(table: int, bit: int, dimension: int) -> int:
    value = ((dimension + 1) * 0x045D9F3B) & 0xFFFFFFFF
    value ^= ((table + 1) * 0x27D4EB2D) & 0xFFFFFFFF
    value ^= ((bit + 1) * 0x165667B1) & 0xFFFFFFFF
    value ^= value >> 16
    return 1 if value & 1 else -1


def vector_bucket_keys(vector: list[float], include_neighbors: bool = False) -> list[str]:
    """Mirror Thunderbird's four-table, eight-bit deterministic LSH."""
    if not vector or len(vector) > 16_384 or not any(vector):
        return []
    keys: list[str] = []
    for table in range(4):
        bucket = 0
        for bit in range(8):
            projection = sum(
                component * _projection_sign(table, bit, dimension)
                for dimension, component in enumerate(vector)
            )
            if projection >= 0:
                bucket |= 1 << bit
        keys.append(f"{table}:{bucket}")
        if include_neighbors:
            keys.extend(f"{table}:{bucket ^ (1 << bit)}" for bit in range(8))
    return list(dict.fromkeys(keys))
