# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0.

"""Deterministic, source-linked mail template mining primitives."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import re
from typing import Iterable

from .contracts import Document, Scope, content_digest


TEMPLATE_SCHEMA_VERSION = 1
TEMPLATE_ALGORITHM_VERSION = "thunderbird-drain-parity-v1"
WILDCARD = "<*>"
VARIABLE_TOKEN_RE = re.compile(
    r"^(?:https?://|[\w.%+-]+@[\w.-]+\.|\d|[a-f\d]{8,})", re.IGNORECASE
)
UPPER_IDENTIFIER_RE = re.compile(r"^[A-Z]{2,}[\d-][A-Z\d-]{3,}$")
QUOTED_REPLY_RE = re.compile(
    r"^(?:>|On .+wrote:|From:\s+.+|Begin forwarded message:)", re.IGNORECASE
)
FORWARDED_MESSAGE_RE = re.compile(
    r"^(?:-+\s*(?:original|forwarded) message\s*-+|Begin forwarded message:)",
    re.IGNORECASE,
)
SIGNATURE_RE = re.compile(r"^--\s*$")
FOOTER_RE = re.compile(
    r"\b(?:unsubscribe|privacy policy|terms of service|view (?:this )?"
    r"(?:email|message) in (?:your )?browser)\b",
    re.IGNORECASE,
)

SLOT_PATTERNS = {
    "amount": re.compile(
        r"(?:[$€£₹]\s?\d[\d,]*(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?\s?"
        r"(?:inr|rs\.?|usd|eur|gbp)\b)",
        re.IGNORECASE,
    ),
    "date": re.compile(
        r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|today|tomorrow|yesterday|"
        r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
        r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
        r"dec(?:ember)?)[\w\s,.-]{0,24}\b",
        re.IGNORECASE,
    ),
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "int": re.compile(r"\b\d{2,}\b"),
    "order_id": re.compile(
        r"\b(?:order|invoice|reference|txn|transaction)"
        r"(?:\s*(?:id|no|number|#))?\s*[:#-]?\s*[A-Z0-9-]{4,}\b",
        re.IGNORECASE,
    ),
    "tracking_id": re.compile(
        r"\b(?:tracking|awb|shipment)(?:\s*(?:id|no|number|#))?"
        r"\s*[:#-]?\s*[A-Z0-9-]{4,}\b",
        re.IGNORECASE,
    ),
    "url": re.compile(r"\bhttps?://[^\s<>()]+", re.IGNORECASE),
}


@dataclass(frozen=True, slots=True)
class TextSegment:
    kind: str
    text: str
    start: int
    end: int
    included_for_ai: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class TemplateSlot:
    slot_type: str
    value: str
    start: int
    end: int
    schema_version: int = TEMPLATE_SCHEMA_VERSION

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class TemplateFamily:
    id: str
    tenant: str
    collection: str
    sender_domain: str
    surface: str
    template_tokens: tuple[str, ...]
    regex: str
    observations: int
    mature: bool
    algorithm_version: str = TEMPLATE_ALGORITHM_VERSION
    schema_version: int = TEMPLATE_SCHEMA_VERSION

    @property
    def template(self) -> str:
        return " ".join(self.template_tokens)

    def as_dict(self) -> dict[str, object]:
        return {**asdict(self), "template": self.template}


@dataclass(frozen=True, slots=True)
class TemplateAssignment:
    tenant: str
    collection: str
    document_id: str
    source_digest: str
    family_id: str
    score: float
    slots: tuple[TemplateSlot, ...]
    analysis_text: str
    schema_version: int = TEMPLATE_SCHEMA_VERSION

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class _Cluster:
    id: str
    sender_domain: str
    surface: str
    template: list[str]
    observations: int
    last_observed_serial: int


def _clean_token(value: str) -> str:
    return re.sub(r"^[^\w]+|[^\w:/@._-]+$", "", value, flags=re.UNICODE)


def drain_tokens(value: str) -> list[str]:
    result = []
    for raw in str(value).strip().split():
        token = _clean_token(raw)
        if not token:
            continue
        if VARIABLE_TOKEN_RE.match(token) or UPPER_IDENTIFIER_RE.match(token):
            result.append(WILDCARD)
        else:
            result.append(token.casefold())
        if len(result) >= 80:
            break
    return result


def _constant_alignment(left: list[str], right: list[str]) -> list[tuple[int, int, str]]:
    rows = [[0] * (len(right) + 1) for _ in range(len(left) + 1)]
    for left_index in range(1, len(left) + 1):
        for right_index in range(1, len(right) + 1):
            if (
                left[left_index - 1] != WILDCARD
                and left[left_index - 1] == right[right_index - 1]
            ):
                rows[left_index][right_index] = rows[left_index - 1][right_index - 1] + 1
            else:
                rows[left_index][right_index] = max(
                    rows[left_index - 1][right_index],
                    rows[left_index][right_index - 1],
                )
    alignment = []
    left_index = len(left)
    right_index = len(right)
    while left_index and right_index:
        if (
            left[left_index - 1] != WILDCARD
            and left[left_index - 1] == right[right_index - 1]
        ):
            alignment.insert(
                0,
                (left_index - 1, right_index - 1, left[left_index - 1]),
            )
            left_index -= 1
            right_index -= 1
        elif rows[left_index - 1][right_index] >= rows[left_index][right_index - 1]:
            left_index -= 1
        else:
            right_index -= 1
    return alignment


def drain_similarity(template: list[str], candidate: list[str]) -> float:
    if not template or not candidate:
        return 0.0
    if len(template) != len(candidate):
        alignment = _constant_alignment(template, candidate)
        return len(alignment) / max(
            1,
            sum(token != WILDCARD for token in template),
            sum(token != WILDCARD for token in candidate),
        )
    matched = sum(
        template[index] == WILDCARD or template[index] == candidate[index]
        for index in range(len(template))
    )
    return matched / len(template)


def _collapse_wildcards(template: Iterable[str]) -> list[str]:
    result = []
    for token in template:
        if token != WILDCARD or not result or result[-1] != WILDCARD:
            result.append(token)
    return result


def merge_drain_template(template: list[str], candidate: list[str]) -> list[str]:
    if len(template) == len(candidate):
        return [
            token if token == candidate[index] else WILDCARD
            for index, token in enumerate(template)
        ]
    alignment = _constant_alignment(template, candidate)
    if not alignment:
        return [WILDCARD]
    merged = []
    previous_left = -1
    previous_right = -1
    for left_index, right_index, token in alignment:
        if left_index > previous_left + 1 or right_index > previous_right + 1:
            merged.append(WILDCARD)
        merged.append(token)
        previous_left = left_index
        previous_right = right_index
    if previous_left < len(template) - 1 or previous_right < len(candidate) - 1:
        merged.append(WILDCARD)
    return _collapse_wildcards(merged)


def render_template_regex(template: Iterable[str]) -> str:
    parts = []
    for token in template:
        parts.append(r"(?:\S+(?:\s+\S+){0,11})" if token == WILDCARD else re.escape(token))
    return r"^\s*" + r"(?:[\s\W_]+)".join(parts) + r"\s*[.!?]?\s*$"


class DrainTemplateMiner:
    """A bounded online miner with separate scope and optional sender lanes."""

    def __init__(
        self,
        scope: Scope,
        *,
        similarity_threshold: float = 0.6,
        max_clusters: int = 1000,
        min_support: int = 3,
        sender_scoped: bool = True,
    ) -> None:
        if not 0 <= similarity_threshold <= 1:
            raise ValueError("similarity_threshold must be between 0 and 1")
        if not 1 <= max_clusters <= 5000:
            raise ValueError("max_clusters must be between 1 and 5000")
        if not 1 <= min_support <= 100:
            raise ValueError("min_support must be between 1 and 100")
        self.scope = scope
        self.similarity_threshold = similarity_threshold
        self.max_clusters = max_clusters
        self.min_support = min_support
        self.sender_scoped = sender_scoped
        self._clusters: list[_Cluster] = []
        self._serial = 0

    def _lane(self, sender_domain: str) -> str:
        return sender_domain.casefold() if self.sender_scoped else "all"

    def _candidates(self, sender_domain: str, surface: str) -> list[_Cluster]:
        lane = self._lane(sender_domain)
        return [
            cluster
            for cluster in self._clusters
            if self._lane(cluster.sender_domain) == lane and cluster.surface == surface
        ]

    def _family(self, cluster: _Cluster) -> TemplateFamily:
        return TemplateFamily(
            id=cluster.id,
            tenant=self.scope.tenant,
            collection=self.scope.collection,
            sender_domain=cluster.sender_domain,
            surface=cluster.surface,
            template_tokens=tuple(cluster.template),
            regex=render_template_regex(cluster.template),
            observations=cluster.observations,
            mature=cluster.observations >= self.min_support,
        )

    def observe(
        self, value: str, *, sender_domain: str = "", surface: str = "subject"
    ) -> TemplateFamily | None:
        candidate = drain_tokens(value)
        if not candidate:
            return None
        candidates = self._candidates(sender_domain, surface)
        best: tuple[_Cluster, float] | None = None
        for cluster in candidates:
            score = drain_similarity(cluster.template, candidate)
            if best is None or score > best[1]:
                best = (cluster, score)
        if best is None or best[1] < self.similarity_threshold:
            if len(self._clusters) >= self.max_clusters:
                self._clusters.sort(
                    key=lambda item: (item.observations, item.last_observed_serial)
                )
                self._clusters.pop(0)
            self._serial += 1
            family_id = "template-" + content_digest(
                {
                    "scope": self.scope.as_dict(),
                    "lane": self._lane(sender_domain),
                    "surface": surface,
                    "serial": self._serial,
                    "candidate": candidate,
                }
            )[:20]
            cluster = _Cluster(
                id=family_id,
                sender_domain=sender_domain.casefold(),
                surface=surface,
                template=candidate,
                observations=1,
                last_observed_serial=self._serial,
            )
            self._clusters.append(cluster)
            return self._family(cluster)
        cluster = best[0]
        cluster.template = merge_drain_template(cluster.template, candidate)
        cluster.observations += 1
        self._serial += 1
        cluster.last_observed_serial = self._serial
        return self._family(cluster)

    def match(
        self, value: str, *, sender_domain: str = "", surface: str = "subject"
    ) -> tuple[TemplateFamily, float] | None:
        candidate = drain_tokens(value)
        best: tuple[_Cluster, float] | None = None
        for cluster in self._candidates(sender_domain, surface):
            score = drain_similarity(cluster.template, candidate)
            if cluster.observations < self.min_support or score < self.similarity_threshold:
                continue
            if best is None or score > best[1]:
                best = (cluster, score)
        return (self._family(best[0]), best[1]) if best else None

    def families(self, *, mature_only: bool = False) -> list[TemplateFamily]:
        result = [self._family(cluster) for cluster in self._clusters]
        if mature_only:
            result = [family for family in result if family.mature]
        return sorted(result, key=lambda item: item.id)


def sender_domain(author: str) -> str:
    angle = re.search(r"<([^>]+)>", str(author))
    email = angle.group(1) if angle else ""
    if not email:
        plain = re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", str(author), re.I)
        email = plain.group(0) if plain else ""
    return email.casefold().rsplit("@", 1)[-1] if "@" in email else ""


def normalized_skeleton(value: str) -> str:
    text = " ".join(str(value).casefold().split())
    text = re.sub(r"\bhttps?://\S+\b", "#", text)
    text = re.sub(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", "#", text)
    text = re.sub(r"\b[a-f0-9]{8,}\b", "#", text)
    text = re.sub(r"\b\d+\b", "#", text)
    text = re.sub(r"[^\w#]+", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def segment_mail_text(value: str) -> list[TextSegment]:
    source = str(value)
    lines = source.splitlines(keepends=True)
    segments: list[TextSegment] = []
    section = "body"
    current_start = 0
    offset = 0

    def append(end: int, kind: str) -> None:
        text = source[current_start:end]
        if text.strip():
            segments.append(
                TextSegment(
                    kind=kind,
                    text=text,
                    start=current_start,
                    end=end,
                    included_for_ai=kind == "body",
                )
            )

    for line in lines:
        surface = line.rstrip("\r\n")
        next_section = section
        if section != "quoted" and (
            QUOTED_REPLY_RE.match(surface) or FORWARDED_MESSAGE_RE.match(surface)
        ):
            next_section = "quoted"
        elif section == "body" and SIGNATURE_RE.match(surface):
            next_section = "signature"
        if next_section != section:
            append(offset, section)
            current_start = offset
            section = next_section
        offset += len(line)
    append(len(source), section)
    return segments


def analysis_text(value: str) -> str:
    return "\n".join(
        segment.text.strip()
        for segment in segment_mail_text(value)
        if segment.included_for_ai
    ).strip()


def meaningful_body_units(value: str, limit: int = 8) -> list[str]:
    units = []
    for segment in segment_mail_text(value):
        if not segment.included_for_ai:
            continue
        for raw_line in segment.text.splitlines():
            line = raw_line.strip()[:280]
            if len(line) < 12 or FOOTER_RE.search(line):
                continue
            units.append(line)
            if len(units) >= limit:
                return units
    return units


def extract_template_slots(
    value: str,
    slot_types: Iterable[str] = SLOT_PATTERNS,
    *,
    strict_identifiers: bool = True,
) -> tuple[TemplateSlot, ...]:
    slots = []
    for slot_type in slot_types:
        pattern = SLOT_PATTERNS.get(slot_type)
        if pattern is None:
            continue
        seen = set()
        for match in pattern.finditer(value):
            if slot_type in {"order_id", "tracking_id"} and strict_identifiers:
                identifier = match.group(0).split()[-1]
                if not re.search(r"\d", identifier) or not re.search(r"[A-Z]", identifier, re.I):
                    continue
            candidate = (match.start(), match.end(), match.group(0))
            if candidate in seen:
                continue
            seen.add(candidate)
            slots.append(
                TemplateSlot(
                    slot_type=slot_type,
                    value=match.group(0),
                    start=match.start(),
                    end=match.end(),
                )
            )
            if len(seen) >= 6:
                break
    return tuple(sorted(slots, key=lambda item: (item.start, item.end, item.slot_type)))


def document_template_surface(document: Document) -> str:
    units = meaningful_body_units(document.text, 1)
    return "\n".join(part for part in (document.title, units[0] if units else "") if part)


def assign_template(
    document: Document,
    miner: DrainTemplateMiner,
    *,
    author: str = "",
    surface: str = "mail",
) -> TemplateAssignment | None:
    if document.scope != miner.scope:
        raise ValueError("template assignment cannot cross scope")
    domain = sender_domain(author or str(document.metadata.get("author", "")))
    value = document.title if surface == "subject" else document_template_surface(document)
    matched = miner.match(value, sender_domain=domain, surface=surface)
    if not matched:
        return None
    family, score = matched
    derived = analysis_text(document.text)
    return TemplateAssignment(
        tenant=document.tenant,
        collection=document.collection,
        document_id=document.id,
        source_digest=content_digest(document.text),
        family_id=family.id,
        score=score,
        slots=extract_template_slots(document.text),
        analysis_text=derived,
    )


def normalized_line(value: str) -> str:
    return " ".join(drain_tokens(value))


def boilerplate_catalog(
    documents: Iterable[Document],
    labels: dict[str, str],
    *,
    minimum_support: int = 3,
    family_fraction: float = 0.8,
) -> dict[str, set[str]]:
    if not 0 < family_fraction <= 1:
        raise ValueError("family_fraction must be between 0 and 1")
    family_documents: dict[str, list[Document]] = {}
    for document in documents:
        family = labels.get(document.id, "")
        if family:
            family_documents.setdefault(family, []).append(document)
    catalog = {}
    for family, members in family_documents.items():
        counts: Counter[str] = Counter()
        for document in members:
            fingerprints = set()
            for line in analysis_text(document.text).splitlines():
                stripped = line.strip()
                if (
                    len(stripped) < 12
                    or FOOTER_RE.search(stripped)
                    or extract_template_slots(stripped)
                    or "[FACT " in stripped
                ):
                    continue
                fingerprint = normalized_line(stripped)
                if fingerprint:
                    fingerprints.add(fingerprint)
            counts.update(fingerprints)
        threshold = max(minimum_support, int(len(members) * family_fraction + 0.999999))
        catalog[family] = {line for line, count in counts.items() if count >= threshold}
    return catalog


def template_retrieval_text(document: Document, boilerplate: set[str] | None = None) -> str:
    boilerplate = boilerplate or set()
    kept = []
    for line in analysis_text(document.text).splitlines():
        stripped = line.strip()
        if not stripped or FOOTER_RE.search(stripped):
            continue
        fingerprint = normalized_line(stripped)
        if fingerprint in boilerplate and not extract_template_slots(stripped):
            continue
        kept.append(stripped)
    return "\n".join(kept)


def shingle_similarity(left: str, right: str, width: int = 5) -> float:
    def shingles(value: str) -> set[tuple[str, ...]]:
        tokens = normalized_line(value).split()
        if len(tokens) < width:
            return {tuple(tokens)} if tokens else set()
        return {tuple(tokens[index : index + width]) for index in range(len(tokens) - width + 1)}

    left_shingles = shingles(left)
    right_shingles = shingles(right)
    union = left_shingles | right_shingles
    return len(left_shingles & right_shingles) / len(union) if union else 0.0
