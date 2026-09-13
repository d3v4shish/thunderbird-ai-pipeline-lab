# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Versioned, JSON-compatible contracts shared by every lab stage."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from hashlib import sha256
import json
import math
from typing import Any, Mapping
from urllib.parse import quote


SCHEMA_VERSION = 1


class ContractError(ValueError):
    """Raised before work starts when an external contract is malformed."""


def canonical_json(value: Any) -> str:
    def convert(item: Any) -> Any:
        if is_dataclass(item):
            return asdict(item)
        if hasattr(item, "as_dict"):
            return item.as_dict()
        if isinstance(item, set):
            return sorted(item)
        raise TypeError(f"Object of type {type(item).__name__} is not JSON serializable")

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=convert,
    )


def content_digest(value: Any) -> str:
    payload = value if isinstance(value, str) else canonical_json(value)
    return sha256(payload.encode("utf-8")).hexdigest()


def _version(data: Mapping[str, Any]) -> int:
    version = data.get("schema_version", SCHEMA_VERSION)
    if not isinstance(version, int) or isinstance(version, bool) or version != SCHEMA_VERSION:
        raise ContractError(f"Unsupported schema_version: {version!r}")
    return version


def _required_text(data: Mapping[str, Any], name: str, limit: int = 1000) -> str:
    value = data.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{name} must be a non-empty string")
    if len(value) > limit:
        raise ContractError(f"{name} exceeds {limit} characters")
    return value.strip()


def _strings(value: Any, name: str, limit: int = 1000) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ContractError(f"{name} must be a list of strings")
    if len(value) > 1000 or any(len(item) > limit for item in value):
        raise ContractError(f"{name} exceeds its count or size limit")
    return tuple(value)


@dataclass(frozen=True, slots=True)
class Scope:
    tenant: str
    collection: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.tenant, str)
            or not isinstance(self.collection, str)
            or not self.tenant.strip()
            or not self.collection.strip()
            or len(self.tenant) > 200
            or len(self.collection) > 200
        ):
            raise ContractError("Scope requires tenant and collection")

    def as_dict(self) -> dict[str, str]:
        return {"tenant": self.tenant, "collection": self.collection}


@dataclass(frozen=True, slots=True)
class Document:
    id: str
    tenant: str
    collection: str
    title: str
    text: str
    timestamp: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Document":
        _version(data)
        metadata = data.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise ContractError("metadata must be an object")
        if not all(isinstance(key, str) for key in metadata):
            raise ContractError("metadata keys must be strings")
        try:
            metadata_bytes = len(canonical_json(dict(metadata)).encode("utf-8"))
        except (TypeError, ValueError, RecursionError) as error:
            raise ContractError("metadata must be JSON-compatible") from error
        if metadata_bytes > 1024 * 1024:
            raise ContractError("metadata exceeds the 1 MiB ingestion limit")
        text = data.get("text")
        if not isinstance(text, str):
            raise ContractError("text must be a string")
        title = data.get("title", "")
        timestamp = data.get("timestamp", "")
        if not isinstance(title, str) or len(title) > 1000:
            raise ContractError("title must be a string of at most 1000 characters")
        if not isinstance(timestamp, str) or len(timestamp) > 80:
            raise ContractError("timestamp must be a string of at most 80 characters")
        if len(text.encode("utf-8")) > 16 * 1024 * 1024:
            raise ContractError("document exceeds the 16 MiB ingestion limit")
        return cls(
            id=_required_text(data, "id"),
            tenant=_required_text(data, "tenant", 200),
            collection=_required_text(data, "collection", 200),
            title=title,
            text=text,
            timestamp=timestamp,
            metadata=dict(metadata),
        )

    @property
    def scope(self) -> Scope:
        return Scope(self.tenant, self.collection)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Chunk:
    id: str
    document_id: str
    tenant: str
    collection: str
    ordinal: int
    text: str
    contextual_text: str
    start: int
    end: int
    section: str = ""
    source_field: str = "text"
    retrieval_text: str = ""

    def __post_init__(self) -> None:
        if self.start < 0 or self.end < self.start:
            raise ContractError("Invalid chunk source span")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Evidence:
    chunk_id: str
    document_id: str
    tenant: str
    collection: str
    text: str
    start: int
    end: int
    score: float
    channels: tuple[str, ...] = ()
    section: str = ""

    @property
    def citation(self) -> str:
        return f"doc://{quote(self.document_id, safe='')}#{self.start}-{self.end}"

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["citation"] = self.citation
        return result


@dataclass(frozen=True, slots=True)
class EvaluationCase:
    id: str
    query: str
    scope: Scope
    expected_document_ids: tuple[str, ...] = ()
    expected_facts: Mapping[str, str] = field(default_factory=dict)
    expected_answer_values: tuple[str, ...] = ()
    forbidden_claims: tuple[str, ...] = ()
    expected_relations: tuple[tuple[str, str, str], ...] = ()
    allowed_tools: tuple[str, ...] = ()
    require_abstention: bool = False
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EvaluationCase":
        _version(data)
        scope = data.get("scope")
        if not isinstance(scope, Mapping):
            raise ContractError("scope must be an object")
        facts = data.get("expected_facts", {})
        if not isinstance(facts, Mapping) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in facts.items()
        ):
            raise ContractError("expected_facts must map strings to strings")
        if len(facts) > 1000 or any(
            len(key) > 200 or len(value) > 10_000 for key, value in facts.items()
        ):
            raise ContractError("expected_facts exceeds its count or size limit")
        relations = data.get("expected_relations", [])
        if not isinstance(relations, list) or not all(
            isinstance(item, list)
            and len(item) == 3
            and all(isinstance(value, str) for value in item)
            for item in relations
        ):
            raise ContractError("expected_relations must contain string triples")
        if len(relations) > 1000 or any(
            len(value) > 300 for relation in relations for value in relation
        ):
            raise ContractError("expected_relations exceeds its count or size limit")
        require_abstention = data.get("require_abstention", False)
        if not isinstance(require_abstention, bool):
            raise ContractError("require_abstention must be a boolean")
        return cls(
            id=_required_text(data, "id"),
            query=_required_text(data, "query", 10_000),
            scope=Scope(
                _required_text(scope, "tenant", 200),
                _required_text(scope, "collection", 200),
            ),
            expected_document_ids=_strings(
                data.get("expected_document_ids"), "expected_document_ids"
            ),
            expected_facts=dict(facts),
            expected_answer_values=_strings(
                data.get("expected_answer_values"), "expected_answer_values", 10_000
            ),
            forbidden_claims=_strings(data.get("forbidden_claims"), "forbidden_claims"),
            expected_relations=tuple(tuple(item) for item in relations),
            allowed_tools=_strings(data.get("allowed_tools"), "allowed_tools", 200),
            require_abstention=require_abstention,
        )

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["scope"] = self.scope.as_dict()
        return result


@dataclass(frozen=True, slots=True)
class PipelineVariant:
    id: str
    chunking: str = "fixed"
    chunk_chars: int = 1200
    chunk_overlap: int = 180
    max_chunks: int = 24
    context_records: int = 8
    context_chars: int = 1800
    context_total_chars: int = 0
    retrieval_candidates: int = 0
    retrieval: str = "hybrid"
    dense_candidates: str = "lsh"
    reranking: str = "deterministic"
    graph: str = "keyword"
    tools: str = "bounded"
    prompt: str = "compact"
    rrf_k: int = 60
    adaptive_searches: int = 3
    tool_rounds: int = 4
    tool_calls: int = 6
    tool_evidence: int = 24
    temperature: float = 0.2
    context_window: int = 16_384
    max_output_tokens: int = 1024
    model: str = "deterministic"
    embedding_model: str = "deterministic-local-v1"
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PipelineVariant":
        _version(data)
        values = dict(data)
        values.pop("schema_version", None)
        try:
            variant = cls(**values)
        except TypeError as error:
            raise ContractError(f"invalid pipeline variant: {error}") from error
        if variant.chunking not in {"fixed", "structure-aware", "sentence-window"}:
            raise ContractError("unsupported chunking mode")
        if variant.retrieval not in {"exact", "lexical", "dense", "hybrid"}:
            raise ContractError("unsupported retrieval mode")
        if variant.dense_candidates not in {"lsh", "full-scan"}:
            raise ContractError("dense_candidates must be lsh or full-scan")
        if variant.reranking not in {"none", "deterministic", "embedding", "endpoint"}:
            raise ContractError("unsupported reranking mode")
        if variant.graph not in {"off", "keyword", "intent-multihop"}:
            raise ContractError("unsupported graph mode")
        if variant.tools not in {"none", "bounded", "coverage-aware"}:
            raise ContractError("unsupported tool mode")
        if variant.prompt not in {"compact", "strict-schema", "evidence-ledger"}:
            raise ContractError("unsupported prompt mode")
        try:
            if variant.chunk_chars < 128 or variant.chunk_chars > 32_768:
                raise ContractError("chunk_chars must be between 128 and 32768")
            if variant.chunk_overlap < 0 or variant.chunk_overlap >= variant.chunk_chars:
                raise ContractError("chunk_overlap must be smaller than chunk_chars")
            if not 1 <= variant.max_chunks <= 4096:
                raise ContractError("max_chunks must be between 1 and 4096")
            if not 1 <= variant.context_records <= 100:
                raise ContractError("context_records must be between 1 and 100")
            if not 128 <= variant.context_chars <= 32_768:
                raise ContractError("context_chars must be between 128 and 32768")
            if not 0 <= variant.context_total_chars <= 1024 * 1024:
                raise ContractError("context_total_chars must be between 0 and 1048576")
            if not 0 <= variant.retrieval_candidates <= 400:
                raise ContractError("retrieval_candidates must be between 0 and 400")
            if not 1 <= variant.rrf_k <= 10_000:
                raise ContractError("rrf_k must be between 1 and 10000")
            if not 1 <= variant.adaptive_searches <= 16:
                raise ContractError("adaptive_searches must be between 1 and 16")
            if not 0 <= variant.tool_rounds <= 16 or not 0 <= variant.tool_calls <= 64:
                raise ContractError("invalid tool-call budget")
            if not 1 <= variant.tool_evidence <= 100:
                raise ContractError("tool_evidence must be between 1 and 100")
            if not math.isfinite(variant.temperature) or not 0 <= variant.temperature <= 2:
                raise ContractError("temperature must be between 0 and 2")
            if not 1024 <= variant.context_window <= 262_144:
                raise ContractError("context_window must be between 1024 and 262144")
            if not 1 <= variant.max_output_tokens <= 32_768:
                raise ContractError("max_output_tokens must be between 1 and 32768")
        except TypeError as error:
            raise ContractError("pipeline variant numeric fields are malformed") from error
        if not isinstance(variant.id, str) or not variant.id.strip():
            raise ContractError("variant id must be a non-empty string")
        if not isinstance(variant.model, str) or not variant.model.strip():
            raise ContractError("model must be a non-empty string")
        if not isinstance(variant.embedding_model, str) or not variant.embedding_model.strip():
            raise ContractError("embedding_model must be a non-empty string")
        return variant

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class StageTrace:
    stage: str
    input_hash: str
    output_hash: str
    wall_ms: float
    cpu_ms: float
    status: str = "ok"
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PipelineOutput:
    query: str
    scope: Scope
    evidence: list[Evidence]
    prompt: str
    raw_output: str
    answer: str
    facts: dict[str, str]
    citations: list[str]
    abstained: bool
    tool_calls: list[dict[str, Any]]
    graph_context: dict[str, Any]
    traces: list[StageTrace]
    errors: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "scope": self.scope.as_dict(),
            "evidence": [item.as_dict() for item in self.evidence],
            "prompt": self.prompt,
            "raw_output": self.raw_output,
            "answer": self.answer,
            "facts": self.facts,
            "citations": self.citations,
            "abstained": self.abstained,
            "tool_calls": self.tool_calls,
            "graph_context": self.graph_context,
            "traces": [trace.as_dict() for trace in self.traces],
            "errors": self.errors,
        }
