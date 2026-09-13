# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0.

"""Deterministic scale and limit validation for thread-memory candidates."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import re
import time
from typing import Any, Iterable

from .contracts import Document, Evidence, EvaluationCase, Scope, content_digest
from .corpus import LONG_FACTS, cases as corpus_cases, documents as corpus_documents
from .email_rag import email_rag_fixture
from .oversized_email import extract_facts, oversized_email_fixture, source_pages
from .scale_evaluation import (
    THREAD_FIXTURE_DIGESTS,
    canonical_thread_range,
    scaled_thread_fixture,
    thread_fixture_digest,
)
from .thread_memory import (
    EmailEnvelope,
    ThreadMemoryStore,
    ThreadMemoryVariant,
    atomic_json,
    email_envelope,
    materialize_thread_rollup,
    ordered_thread_documents,
    render_thread_memory,
    structural_relations,
)
from .thread_memory_evaluation import (
    DEFAULT_THREAD_MEMORY_PARAMETERS,
    ThreadMemoryParameters,
    VectorProvider,
    artifact_map_key,
    evaluate_retrieval_cell,
)


HARDENING_VERSION = "thread-memory-hardening-v1"
FACT_RE = re.compile(r"\[FACT ([A-Z]\d{2,4})\]\s*[^:\n]+:\s*([^\.\n]+(?:\.\d{2})?)\.")
MEMORY_BUDGETS = (2_000, 6_000, 12_000)
SUMMARY_WORD_LIMITS = (80, 200, 400)
THREAD_PARENT_LIMITS = (2, 4, 8)
EMAIL_PARENT_LIMITS = (4, 8, 16)
PAGE_CHARACTERS = (12_000, 20_000, 30_000)


def _source_linked_artifact(document: Document, envelope: EmailEnvelope) -> dict[str, Any]:
    claims = []
    for index, match in enumerate(FACT_RE.finditer(document.text)):
        quote = match.group(0)
        claims.append(
            {
                "claim_id": f"claim-{index:02d}",
                "text": quote,
                "evidence": [
                    {
                        "message_id": document.id,
                        "message_identifier": envelope.message_id,
                        "quote": quote,
                        "start": match.start(),
                        "end": match.end(),
                    }
                ],
            }
        )
    narrative = " ".join(item["text"] for item in claims) or envelope.subject
    return {
        "context": envelope.subject[:600] or envelope.thread_id[:600],
        "evidence_summary": claims[:12],
        "narrative_summary": " ".join(narrative.split()[:400])[:4_800],
        "events": [],
        "relations": [],
        "validation_rejections": [],
    }


def deterministic_artifact_stream(
    documents: list[Document],
) -> tuple[dict[str, dict[str, Any]], ThreadMemoryStore, dict[str, Any]]:
    """Create a perfect-source control without using generated model text."""
    config = {"version": HARDENING_VERSION, "lane": "source-linked-control"}
    config_digest = content_digest(config)
    store = ThreadMemoryStore()
    artifacts: dict[str, dict[str, Any]] = {}
    prior_by_scope_thread: dict[tuple[str, str, str], dict[str, EmailEnvelope]] = {}
    positions: dict[tuple[str, str, str], int] = {}
    started = time.perf_counter()
    for document in ordered_thread_documents(documents):
        envelope = email_envelope(document)
        key = (document.tenant, document.collection, envelope.thread_id)
        prior = prior_by_scope_thread.setdefault(key, {})
        position = positions.get(key, 0)
        artifact = _source_linked_artifact(document, envelope)
        store.add_artifact(
            document,
            envelope,
            artifact,
            structural_relations(envelope, prior),
            config_digest=config_digest,
            position=position,
            audit={"status": "deterministic-source-control"},
        )
        artifacts[artifact_map_key(document)] = {
            "document_id": document.id,
            "tenant": document.tenant,
            "collection": document.collection,
            "thread_id": envelope.thread_id,
            "position": position,
            "artifact": artifact,
            "audit": {"status": "deterministic-source-control"},
        }
        prior[document.id] = envelope
        positions[key] = position + 1
    for tenant, collection, thread_id in sorted(prior_by_scope_thread):
        materialize_thread_rollup(
            store,
            Scope(tenant, collection),
            thread_id,
            config_digest,
            budget_characters=12_000,
        )
    return artifacts, store, {
        "config": config,
        "config_digest": config_digest,
        "message_count": len(documents),
        "successful_messages": len(documents),
        "failures": 0,
        "rejected_fields": 0,
        "cache_hits": 0,
        "endpoint_requests": 0,
        "request_bytes": 0,
        "response_bytes": 0,
        "wall_ms": (time.perf_counter() - started) * 1_000,
        "prompt_eval_count": 0,
        "eval_count": 0,
        "storage": store.storage_stats(),
        "records": [],
    }


def _variant(placement: str, identifier: str) -> ThreadMemoryVariant:
    return ThreadMemoryVariant(
        extraction_architecture="deterministic-control",
        summary_usage="both",
        relation_policy="structural",
        memory_mode="both",
        index_placement=placement,
        chat_model="none",
        repeat=1,
        id=identifier,
    )


def _parameter_sweep() -> list[tuple[str, ThreadMemoryParameters]]:
    base = DEFAULT_THREAD_MEMORY_PARAMETERS
    values = [("baseline", base)]
    values.extend(
        (f"memory-{budget}", replace(base, thread_parent_budget_characters=budget))
        for budget in MEMORY_BUDGETS
        if budget != base.thread_parent_budget_characters
    )
    values.extend(
        (f"summary-{words}", replace(base, summary_max_words=words))
        for words in SUMMARY_WORD_LIMITS
        if words != base.summary_max_words
    )
    values.extend(
        (f"thread-parent-k-{limit}", replace(base, thread_parent_k=limit))
        for limit in THREAD_PARENT_LIMITS
        if limit != base.thread_parent_k
    )
    values.extend(
        (f"email-parent-k-{limit}", replace(base, email_parent_k=limit))
        for limit in EMAIL_PARENT_LIMITS
        if limit != base.email_parent_k
    )
    return values


def _fact_recall(evidence: Iterable[Evidence], expected: dict[str, str]) -> float:
    text = "\n".join(item.text for item in evidence)
    found = {
        fact_id
        for fact_id, value in expected.items()
        if f"[FACT {fact_id}]" in text and value.casefold() in text.casefold()
    }
    return len(found) / len(expected) if expected else 1.0


def _valid_evidence(documents: list[Document], evidence: Iterable[Evidence]) -> bool:
    sources = {
        (item.tenant, item.collection, item.id): item
        for item in documents
    }
    return all(
        (source := sources.get((item.tenant, item.collection, item.document_id)))
        is not None
        and source.text[item.start : item.end] == item.text
        for item in evidence
    )


def _email_parameter_results() -> list[dict[str, Any]]:
    documents, cases, _ = email_rag_fixture()
    artifacts, store, generation = deterministic_artifact_stream(documents)
    results = []
    try:
        for parameter_name, parameters in _parameter_sweep():
            for placement in ("repeated", "hierarchical"):
                cell = evaluate_retrieval_cell(
                    documents,
                    cases,
                    artifacts,
                    store,
                    generation,
                    _variant(placement, f"{parameter_name}-{placement}"),
                    VectorProvider(None),
                    parameters,
                )
                results.append(
                    {
                        "parameter": parameter_name,
                        "placement": placement,
                        "parameters": parameters.as_dict(),
                        "aggregate": cell["aggregate"],
                    }
                )
    finally:
        store.close()
    return results


def _scale_results() -> list[dict[str, Any]]:
    results = []
    for size, expected_digest in THREAD_FIXTURE_DIGESTS.items():
        if thread_fixture_digest(size) != expected_digest:
            raise ValueError(f"scaled thread fixture {size} drifted")
        documents, case = scaled_thread_fixture(size)
        artifacts, store, generation = deterministic_artifact_stream(documents)
        try:
            cell = evaluate_retrieval_cell(
                documents,
                [case],
                artifacts,
                store,
                generation,
                _variant("hierarchical", f"scale-{size}-hierarchical"),
                VectorProvider(None),
            )
            complete = canonical_thread_range(documents, case)
            scope = case.scope
            thread_id = f"SCALE-{size:04d}"
            bounded_memory = []
            for budget in MEMORY_BUDGETS:
                rendered = render_thread_memory(
                    store,
                    scope,
                    thread_id,
                    generation["config_digest"],
                    "both",
                    budget_characters=budget,
                    max_entries=size * 2,
                    max_edges=size * 2,
                )
                bounded_memory.append(
                    {
                        "budget_characters": budget,
                        "actual_characters": len(rendered),
                        "within_budget": len(rendered) <= budget,
                        "digest": content_digest(rendered),
                    }
                )
            results.append(
                {
                    "message_count": size,
                    "document_count_with_controls": len(documents),
                    "top_k_memory_retrieval": cell["aggregate"],
                    "exhaustive_source_route": {
                        "evidence_count": len(complete),
                        "fact_recall": _fact_recall(complete, case.expected_facts),
                        "scope_integrity": float(
                            all(
                                item.tenant == case.scope.tenant
                                and item.collection == case.scope.collection
                                for item in complete
                            )
                        ),
                        "source_span_validity": float(
                            _valid_evidence(documents, complete)
                        ),
                        "page_count_at_32_messages": (len(complete) + 31) // 32,
                    },
                    "memory_bounds": bounded_memory,
                    "storage": generation["storage"],
                }
            )
        finally:
            store.close()
    return results


def _email_document(document: Document, thread_id: str) -> Document:
    return replace(
        document,
        collection="mail",
        metadata={
            **document.metadata,
            "synthetic": True,
            "thread_id": thread_id,
            "message_id": f"{document.id}@hardening.invalid",
        },
    )


def _large_document_results() -> list[dict[str, Any]]:
    long_record = next(item for item in corpus_documents() if item["id"] == "long-10240")
    long_document = _email_document(Document.from_dict(long_record), "LONG-10240")
    long_case_record = next(
        item for item in corpus_cases() if item["id"] == "long-document-coverage"
    )
    long_case = replace(
        EvaluationCase.from_dict(long_case_record),
        scope=Scope(long_document.tenant, long_document.collection),
    )
    oversized, oversized_case = oversized_email_fixture()
    oversized = _email_document(oversized, "OVERSIZED-262144")
    oversized_case = replace(
        oversized_case,
        scope=Scope(oversized.tenant, oversized.collection),
    )
    results = []
    direct_chunks = source_pages(long_document, page_chars=12_000, overlap=0)
    results.append(
        {
            "name": "10KB-direct",
            "bytes": len(long_document.text.encode("utf-8")),
            "route": "direct-complete-email",
            "context_windows": [8_192, 16_384, 32_768],
            "page_characters": 12_000,
            "page_count": len(direct_chunks),
            "fact_recall": _fact_recall(direct_chunks, dict(LONG_FACTS)),
            "source_span_validity": float(_valid_evidence([long_document], direct_chunks)),
            "expected_case": long_case.id,
        }
    )
    for page_characters in PAGE_CHARACTERS:
        pages = source_pages(
            oversized,
            page_chars=page_characters,
            overlap=256,
        )
        results.append(
            {
                "name": f"256KiB-paged-{page_characters}",
                "bytes": len(oversized.text.encode("utf-8")),
                "route": "complete-source-paging",
                "context_windows": [8_192, 16_384, 32_768],
                "page_characters": page_characters,
                "page_count": len(pages),
                "fact_recall": _fact_recall(pages, oversized_case.expected_facts),
                "source_span_validity": float(_valid_evidence([oversized], pages)),
                "forbidden_value_present_in_source": bool(
                    extract_facts(oversized.text)
                    and "FABRICATED-CHECKPOINT-99999" in oversized.text
                ),
                "expected_case": oversized_case.id,
            }
        )
    return results


def evaluate_thread_memory_hardening_deterministic() -> dict[str, Any]:
    started = time.perf_counter()
    parameter_results = _email_parameter_results()
    scale_results = _scale_results()
    large_document_results = _large_document_results()
    hard_failures = []
    if any(item["aggregate"]["scope_integrity"] < 1 for item in parameter_results):
        hard_failures.append("SCOPE_LEAK")
    if any(item["aggregate"]["source_span_validity"] < 1 for item in parameter_results):
        hard_failures.append("SOURCE_SPAN_FAILURE")
    if any(
        route["fact_recall"] < 1 or route["source_span_validity"] < 1
        for route in large_document_results
    ):
        hard_failures.append("LARGE_SOURCE_COVERAGE_FAILURE")
    if any(
        item["exhaustive_source_route"]["fact_recall"] < 1
        or item["exhaustive_source_route"]["scope_integrity"] < 1
        or item["exhaustive_source_route"]["source_span_validity"] < 1
        or any(not bound["within_budget"] for bound in item["memory_bounds"])
        for item in scale_results
    ):
        hard_failures.append("THREAD_SCALE_FAILURE")
    return {
        "schema_version": 1,
        "title": "Thread-memory deterministic hardening",
        "version": HARDENING_VERSION,
        "method": {
            "parameter_design": "one-factor-at-a-time",
            "memory_budgets": list(MEMORY_BUDGETS),
            "summary_word_limits": list(SUMMARY_WORD_LIMITS),
            "thread_parent_limits": list(THREAD_PARENT_LIMITS),
            "email_parent_limits": list(EMAIL_PARENT_LIMITS),
            "page_characters": list(PAGE_CHARACTERS),
            "generated_model_calls": 0,
        },
        "email_180_parameter_sweep": parameter_results,
        "thread_scale": scale_results,
        "large_documents": large_document_results,
        "hard_gate_failures": hard_failures,
        "runtime": {"wall_ms": (time.perf_counter() - started) * 1_000},
        "limitations": [
            "This hardening pass isolates storage, retrieval, bounds, paging, scope, and provenance without a model.",
            "Live Qwen3/Phi4 extraction and answer stability still require three completed repeats of the focused matrix and selected finalists.",
            "Exhaustive user mode uses canonical source paging; generated memory is never treated as proof of completeness.",
        ],
    }


def markdown_thread_memory_hardening(report: dict[str, Any]) -> str:
    lines = [
        "# Thread-memory deterministic hardening",
        "",
        f"- Hard-gate failures: {', '.join(report['hard_gate_failures']) or 'none'}.",
        f"- Runtime: {report['runtime']['wall_ms']:.1f} ms.",
        "- Model calls: 0 (this report isolates deterministic mechanics).",
        "",
        "## 180-message parameter sweep",
        "",
        "| Parameter | Placement | Fact recall | MRR | Indexed characters | Retrieval ms |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for item in report["email_180_parameter_sweep"]:
        aggregate = item["aggregate"]
        lines.append(
            f"| {item['parameter']} | {item['placement']} | "
            f"{aggregate['fact_recall_at_k']:.3f} | {aggregate['mrr']:.3f} | "
            f"{aggregate['indexed_characters']} | {aggregate['retrieval_wall_ms']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Thread scale",
            "",
            "| Messages | Top-K fact recall | Exhaustive fact recall | Pages (32) | DB bytes |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for item in report["thread_scale"]:
        lines.append(
            f"| {item['message_count']} | "
            f"{item['top_k_memory_retrieval']['fact_recall_at_k']:.3f} | "
            f"{item['exhaustive_source_route']['fact_recall']:.3f} | "
            f"{item['exhaustive_source_route']['page_count_at_32_messages']} | "
            f"{item['storage']['database_bytes']} |"
        )
    lines.extend(
        [
            "",
            "## Large emails",
            "",
            "| Design | Bytes | Route | Pages | Fact recall | Source spans |",
            "|---|---:|---|---:|---:|---:|",
        ]
    )
    for item in report["large_documents"]:
        lines.append(
            f"| {item['name']} | {item['bytes']} | {item['route']} | "
            f"{item['page_count']} | {item['fact_recall']:.3f} | "
            f"{item['source_span_validity']:.3f} |"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    return "\n".join(lines) + "\n"


def write_thread_memory_hardening_report(
    directory: Path, name: str, report: dict[str, Any]
) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / f"{name}.json"
    markdown_path = directory / f"{name}.md"
    atomic_json(json_path, report)
    temporary = markdown_path.with_suffix(".md.tmp")
    temporary.write_text(markdown_thread_memory_hardening(report), encoding="utf-8")
    temporary.replace(markdown_path)
    return {"json": json_path, "markdown": markdown_path}
