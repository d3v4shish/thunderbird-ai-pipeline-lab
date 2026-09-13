# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0.

"""Deterministic thread-scale, storage-layout, and parameter ablations."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import statistics
import tempfile
import time
import tracemalloc
from typing import Any, Callable

from .contracts import Document, EvaluationCase, Evidence, PipelineVariant, Scope, content_digest
from .evaluation import percentile
from .pipeline import Pipeline
from .rag_evaluation import aggregate_retrieval_cases, score_retrieval_case
from .reporting import checkpoint
from .storage import Index
from .text import chunk_document


THREAD_SIZES = (50, 100, 250, 500)
EXTENDED_THREAD_SIZES = (1000, 2500, 5000)
SUPPORTED_THREAD_SIZES = THREAD_SIZES + EXTENDED_THREAD_SIZES
THREAD_PAGE_SIZE = 32
THREAD_FIXTURE_VERSION = "synthetic-thread-scale-v1"
THREAD_FIXTURE_DIGESTS = {
    50: "00ed5bbdee4c34b95838b6365ff6119fc7989b119b044d18bba68f77856b4953",
    100: "102aa3ab0d057aea660ff194029e47495f2a216711a49a3d876d388abcc513be",
    250: "83c085ce03a3b6c16f1bc4bd6ac9b120988b76c32af2391810af0e6190854358",
    500: "8dc40b0b8682fae06c143eeeb708f9f78174c8027d816c3aa9e66d55038ecf1d",
}
EXTENDED_THREAD_FIXTURE_DIGESTS = {
    1000: "cd197e5f3e3043112739ca1c2c1183b5aba90536e994e04f2a96b3386e6be965",
    2500: "404667b107acc2d352a536f82f36a2d3473ce5fe97198f1f012546cad17f2903",
    5000: "0800a4ea8a76713799972eb1721eefcf62af569934905b7dca8ea82ad18de523",
}
SCALE_FACT_RE = re.compile(r"\[FACT (T\d{3,5})\]\s*action_code:\s*([^\.\n]+)\.")


def scaled_thread_fixture(size: int) -> tuple[list[Document], EvaluationCase]:
    if size not in SUPPORTED_THREAD_SIZES:
        raise ValueError(f"thread size must be one of {SUPPORTED_THREAD_SIZES}")
    thread_id = f"SCALE-{size:04d}"
    scope = Scope("tenant-alpha", "mail")
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    documents = []
    facts = {}
    expected_document_ids = []
    for sequence in range(1, size + 1):
        fact_id = f"T{sequence:03d}"
        value = f"{thread_id}-ACTION-{sequence:03d}"
        document_id = f"{thread_id.casefold()}-message-{sequence:03d}"
        facts[fact_id] = value
        expected_document_ids.append(document_id)
        documents.append(
            Document(
                id=document_id,
                tenant=scope.tenant,
                collection=scope.collection,
                title=f"{thread_id} action update {sequence:03d}",
                timestamp=(started + timedelta(minutes=sequence)).isoformat(),
                text=(
                    "From: scale-team@example.invalid\n"
                    "To: reviewer@example.invalid\n"
                    f"Subject: {thread_id} action update {sequence:03d}\n"
                    f"Thread-ID: {thread_id}\n"
                    f"Sequence: {sequence} of {size}\n\n"
                    "This synthetic update records one independent action. "
                    "Earlier and later messages remain separately authoritative.\n"
                    f"[FACT {fact_id}] action_code: {value}."
                ),
                metadata={
                    "synthetic": True,
                    "thread_id": thread_id,
                    "sequence": sequence,
                    "thread_size": size,
                },
            )
        )
    for sequence in range(1, 13):
        documents.append(
            Document(
                id=f"{thread_id.casefold()}-distractor-{sequence:02d}",
                tenant=scope.tenant,
                collection=scope.collection,
                title=f"Routine unrelated update {sequence}",
                timestamp=(started + timedelta(days=1, minutes=sequence)).isoformat(),
                text=(
                    "From: routine@example.invalid\n"
                    "To: reviewer@example.invalid\n"
                    f"Subject: Routine unrelated update {sequence}\n\n"
                    "Routine status is unchanged and has no action code for the requested thread."
                ),
                metadata={"synthetic": True, "thread_id": f"OTHER-{sequence:03d}"},
            )
        )
    documents.append(
        Document(
            id=f"{thread_id.casefold()}-shadow-private",
            tenant="tenant-beta",
            collection=scope.collection,
            title=f"{thread_id} private shadow",
            timestamp=(started + timedelta(days=2)).isoformat(),
            text=(
                "From: private@example.invalid\n"
                f"Subject: {thread_id} private shadow\n"
                f"Thread-ID: {thread_id}\n"
                "[FACT X999] action_code: PRIVATE-SHADOW-999."
            ),
            metadata={"synthetic": True, "thread_id": thread_id, "sequence": size + 1},
        )
    )
    case = EvaluationCase(
        id=f"thread-scale-{size}",
        query=f"List every action code from thread {thread_id} without omission.",
        scope=scope,
        expected_document_ids=tuple(expected_document_ids),
        expected_facts=facts,
        expected_answer_values=tuple(facts.values()),
        forbidden_claims=("PRIVATE-SHADOW-999",),
    )
    return documents, case


def thread_fixture_digest(size: int) -> str:
    documents, case = scaled_thread_fixture(size)
    return content_digest(
        {
            "version": THREAD_FIXTURE_VERSION,
            "documents": [item.as_dict() for item in documents],
            "case": case.as_dict(),
        }
    )


def canonical_thread_range(
    documents: list[Document], case: EvaluationCase, *, limit: int = 10_000
) -> list[Evidence]:
    identifier = re.search(r"\bSCALE-\d{4}\b", case.query, re.IGNORECASE)
    if not identifier:
        return []
    thread_id = identifier.group(0).upper()
    matching = [
        item
        for item in documents
        if item.tenant == case.scope.tenant
        and item.collection == case.scope.collection
        and str(item.metadata.get("thread_id", "")).upper() == thread_id
    ]
    matching.sort(key=lambda item: (item.timestamp, item.id))
    evidence = []
    for document in matching[:limit]:
        chunks = chunk_document(document, "structure-aware", 1200, 0, 16)
        for chunk in chunks:
            evidence.append(
                Evidence(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    tenant=document.tenant,
                    collection=document.collection,
                    text=chunk.text,
                    start=chunk.start,
                    end=chunk.end,
                    score=1.0,
                    channels=("thread-range",),
                    section=chunk.section,
                )
            )
    return evidence


def _extract_scale_facts(evidence: list[Evidence]) -> dict[str, str]:
    return {
        match.group(1): match.group(2).strip()
        for item in evidence
        for match in SCALE_FACT_RE.finditer(item.text)
    }


def _measure(operation: Callable[[], Any], repeats: int = 7) -> tuple[Any, list[float]]:
    result = None
    timings = []
    for _ in range(repeats):
        started = time.perf_counter()
        result = operation()
        timings.append((time.perf_counter() - started) * 1000)
    return result, timings


def _scale_method(
    name: str,
    evidence: list[Evidence],
    case: EvaluationCase,
    documents: list[Document],
    timings: list[float],
    *,
    page_size: int | None = None,
    final_facts: dict[str, str] | None = None,
    peak_stage_characters: int | None = None,
    reduction_characters: int = 0,
    peak_python_bytes: int = 0,
) -> dict[str, Any]:
    documents_by_id = {
        (item.tenant, item.collection, item.id): item for item in documents
    }
    source_valid = all(
        (
            source := documents_by_id.get((item.tenant, item.collection, item.document_id))
        )
        and source.text[item.start : item.end] == item.text
        for item in evidence
    )
    found = _extract_scale_facts(evidence)
    answer_facts = final_facts if final_facts is not None else found
    expected_ids = list(case.expected_document_ids)
    returned_ids = [item.document_id for item in evidence]
    return {
        "method": name,
        "message_count": len(case.expected_document_ids),
        "page_size": page_size,
        "pages": (len(evidence) + page_size - 1) // page_size if page_size else 1,
        "retrieved_messages": len(returned_ids),
        "retrieval_fact_count": len(set(found) & set(case.expected_facts)),
        "answer_fact_count": len(set(answer_facts) & set(case.expected_facts)),
        "metrics": {
            "document_recall": len(set(returned_ids) & set(expected_ids)) / len(expected_ids),
            "retrieval_fact_recall": len(set(found) & set(case.expected_facts))
            / len(case.expected_facts),
            "answer_fact_recall": len(set(answer_facts) & set(case.expected_facts))
            / len(case.expected_facts),
            "scope_integrity": float(
                all(
                    item.tenant == case.scope.tenant
                    and item.collection == case.scope.collection
                    for item in evidence
                )
            ),
            "source_span_validity": float(source_valid),
            "ordered": float(returned_ids == expected_ids[: len(returned_ids)]),
            "duplicate_count": len(returned_ids) - len(set(returned_ids)),
            "total_evidence_characters": sum(len(item.text) for item in evidence),
            "peak_stage_characters": peak_stage_characters
            if peak_stage_characters is not None
            else sum(len(item.text) for item in evidence),
            "reduction_characters": reduction_characters,
            "latency_p50_ms": percentile(timings, 0.5),
            "latency_p95_ms": percentile(timings, 0.95),
            "peak_python_bytes": peak_python_bytes,
        },
        "missing_fact_ids": sorted(set(case.expected_facts) - set(answer_facts)),
        "evidence_digest": content_digest([item.as_dict() for item in evidence]),
    }


def _hierarchical_reduce(
    pages: list[list[Evidence]], reduction_batch_size: int
) -> tuple[dict[str, str], int, int]:
    if not 1 <= reduction_batch_size <= 128:
        raise ValueError("reduction_batch_size must be between 1 and 128")
    summaries = []
    peak_characters = 0
    for page in pages:
        facts = _extract_scale_facts(page)
        summary = "\n".join(f"{key}={facts[key]}" for key in sorted(facts))
        peak_characters = max(peak_characters, sum(len(item.text) for item in page))
        summaries.append(summary)
    reduced = []
    for start in range(0, len(summaries), reduction_batch_size):
        batch = summaries[start : start + reduction_batch_size]
        peak_characters = max(peak_characters, sum(len(item) for item in batch))
        reduced.append("\n".join(batch))
    final_ledger = "\n".join(reduced)
    facts = {
        line.split("=", 1)[0]: line.split("=", 1)[1]
        for line in final_ledger.splitlines()
        if "=" in line
    }
    return facts, peak_characters, len(final_ledger)


def evaluate_thread_scale(
    sizes: tuple[int, ...] = THREAD_SIZES,
    page_size: int = THREAD_PAGE_SIZE,
    reduction_batch_size: int = 16,
) -> dict[str, Any]:
    if not 1 <= page_size <= 128:
        raise ValueError("page_size must be between 1 and 128")
    results = []
    for size in sizes:
        documents, case = scaled_thread_fixture(size)
        with tempfile.TemporaryDirectory(prefix=f"tb-ai-thread-{size}-") as temporary:
            database = Path(temporary) / "thread.sqlite"
            with Index(database) as index:
                started = time.perf_counter()
                for document in documents:
                    chunks = chunk_document(document, "structure-aware", 1200, 0, 16)
                    index.add_document(document, chunks)
                ingest_ms = (time.perf_counter() - started) * 1000
                direct, direct_timings = _measure(
                    lambda: index.hybrid_search(
                        case.query,
                        case.scope,
                        32,
                        candidate_mode="full-scan",
                    )[:8]
                )
                full, full_timings = _measure(
                    lambda: canonical_thread_range(documents, case)
                )
                pages, paged_timings = _measure(
                    lambda: [
                        items[start : start + page_size]
                        for items in [canonical_thread_range(documents, case)]
                        for start in range(0, len(items), page_size)
                    ]
                )
                flat_pages = [item for page in pages for item in page]

                def hierarchical_operation() -> tuple[
                    list[Evidence], dict[str, str], int, int
                ]:
                    items = canonical_thread_range(documents, case)
                    item_pages = [
                        items[start : start + page_size]
                        for start in range(0, len(items), page_size)
                    ]
                    facts, peak, ledger = _hierarchical_reduce(
                        item_pages, reduction_batch_size
                    )
                    return items, facts, peak, ledger

                tracemalloc.start()
                reduced, hierarchical_timings = _measure(
                    hierarchical_operation
                )
                _, peak_python_bytes = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                hierarchical_evidence, answer_facts, peak_characters, reduction_characters = reduced
                index.connection.execute("VACUUM")
                database_bytes = database.stat().st_size
                methods = [
                    _scale_method(
                        "direct-top-8", direct, case, documents, direct_timings
                    ),
                    _scale_method(
                        "full-thread-range", full, case, documents, full_timings
                    ),
                    _scale_method(
                        "paged-thread-range",
                        flat_pages,
                        case,
                        documents,
                        paged_timings,
                        page_size=page_size,
                        peak_stage_characters=max(
                            (sum(len(item.text) for item in page) for page in pages),
                            default=0,
                        ),
                    ),
                    _scale_method(
                        "hierarchical-ledger",
                        hierarchical_evidence,
                        case,
                        documents,
                        hierarchical_timings,
                        page_size=page_size,
                        final_facts=answer_facts,
                        peak_stage_characters=peak_characters,
                        reduction_characters=reduction_characters,
                        peak_python_bytes=peak_python_bytes,
                    ),
                ]
            results.append(
                {
                    "thread_size": size,
                    "fixture_digest": thread_fixture_digest(size),
                    "document_count_with_controls": len(documents),
                    "ingest_ms": ingest_ms,
                    "database_bytes": database_bytes,
                    "methods": methods,
                }
            )
    hierarchy = [
        next(item for item in result["methods"] if item["method"] == "hierarchical-ledger")
        for result in results
    ]
    largest_documents, largest_case = scaled_thread_fixture(max(sizes))
    largest_evidence = canonical_thread_range(largest_documents, largest_case)
    largest_pages = [
        largest_evidence[start : start + page_size]
        for start in range(0, len(largest_evidence), page_size)
    ]
    reduction_batch_sweep = []
    for batch_size in (4, 8, 16, 32, 64):
        reduced, timings = _measure(
            lambda batch_size=batch_size: _hierarchical_reduce(
                largest_pages, batch_size
            )
        )
        facts, peak_characters, ledger_characters = reduced
        reduction_batch_sweep.append(
            {
                "batch_size": batch_size,
                "fact_recall": len(set(facts) & set(largest_case.expected_facts))
                / len(largest_case.expected_facts),
                "peak_stage_characters": peak_characters,
                "ledger_characters": ledger_characters,
                "latency_p50_ms": percentile(timings, 0.5),
            }
        )
    return {
        "schema_version": 1,
        "title": "Synthetic Large-Thread Scale Evaluation",
        "production_ready": False,
        "method": (
            f"Frozen synthetic {min(sizes)}-{max(sizes)}-message threads compare direct top-K, an unbounded "
            "control range, bounded paging, and deterministic hierarchical fact ledgers."
        ),
        "page_size": page_size,
        "reduction_batch_size": reduction_batch_size,
        "reduction_batch_sweep": reduction_batch_sweep,
        "results": results,
        "hard_gate_pass": all(
            item["metrics"]["answer_fact_recall"] == 1.0
            and item["metrics"]["scope_integrity"] == 1.0
            and item["metrics"]["source_span_validity"] == 1.0
            and not item["missing_fact_ids"]
            for item in hierarchy
        ),
        "decision": (
            "Use ordered paging plus hierarchical reduction for exhaustive threads; "
            "never place a 50-500-message full range in one model prompt."
        ),
    }


def _storage_lane(
    documents: list[Document],
    cases: list[EvaluationCase],
    variant: PipelineVariant,
    normalized: bool,
    repeats: int,
) -> dict[str, Any]:
    records = []
    for repeat in range(1, repeats + 1):
        with tempfile.TemporaryDirectory(prefix="tb-ai-parent-storage-") as temporary:
            database = Path(temporary) / "index.sqlite"
            with Index(database, normalized_parent_storage=normalized) as index:
                pipeline = Pipeline(index, variant)
                started = time.perf_counter()
                ingest = pipeline.ingest(documents)
                ingest_ms = (time.perf_counter() - started) * 1000
                scored_cases = []
                rankings = {}
                for case in cases:
                    started = time.perf_counter()
                    evidence = pipeline.retrieve(case.query, case.scope)[:8]
                    elapsed_ms = (time.perf_counter() - started) * 1000
                    rankings[case.id] = [item.as_dict() for item in evidence]
                    scored_cases.append(
                        score_retrieval_case(
                            index, case, evidence, 8, variant.context_chars, elapsed_ms
                        )
                    )
                aggregate = aggregate_retrieval_cases(
                    variant, 8, ingest, scored_cases
                )["aggregate"]
                storage = index.storage_stats()
                index.connection.execute("VACUUM")
                database_bytes = database.stat().st_size
            records.append(
                {
                    "repeat": repeat,
                    "ingest_ms": ingest_ms,
                    "database_bytes": database_bytes,
                    "storage": storage,
                    "aggregate": aggregate,
                    "rankings": rankings,
                }
            )
    return {
        "layout": "normalized-parent" if normalized else "duplicated-parent",
        "records": records,
        "summary": {
            "ingest_p50_ms": percentile([item["ingest_ms"] for item in records], 0.5),
            "database_bytes": [item["database_bytes"] for item in records],
            "passage_characters": [
                item["storage"]["chunk_passage_characters"]
                + item["storage"]["parent_passage_characters"]
                for item in records
            ],
            "fact_recall": [item["aggregate"]["fact_recall_at_k"] for item in records],
            "mrr": [item["aggregate"]["mrr"] for item in records],
            "scope_integrity": [item["aggregate"]["scope_integrity"] for item in records],
        },
    }


def evaluate_parent_storage(
    documents: list[Document],
    cases: list[EvaluationCase],
    base: PipelineVariant,
    repeats: int = 3,
) -> dict[str, Any]:
    variant = replace(
        base,
        id="sentence-window-storage",
        chunking="sentence-window",
        chunk_chars=1200,
        chunk_overlap=0,
        max_chunks=4096,
        retrieval="hybrid",
        dense_candidates="full-scan",
        reranking="deterministic",
        graph="off",
        tools="none",
        model="deterministic",
        embedding_model="deterministic-local-v1",
    )
    legacy = _storage_lane(documents, cases, variant, False, repeats)
    normalized = _storage_lane(documents, cases, variant, True, repeats)
    parity = all(
        left["rankings"] == right["rankings"]
        for left, right in zip(legacy["records"], normalized["records"], strict=True)
    )
    legacy_size = statistics.fmean(legacy["summary"]["database_bytes"])
    normalized_size = statistics.fmean(normalized["summary"]["database_bytes"])
    return {
        "schema_version": 1,
        "title": "Normalized Sentence-Window Parent Storage Evaluation",
        "production_ready": False,
        "method": (
            "Paired fresh SQLite indexes store identical sentence children either with "
            "duplicated parent text or one canonical parent row referenced by each child."
        ),
        "variant": variant.as_dict(),
        "lanes": [legacy, normalized],
        "behavioral_parity": parity,
        "database_change_percent": (
            (normalized_size - legacy_size) / legacy_size * 100 if legacy_size else 0.0
        ),
        "candidate": parity
        and min(normalized["summary"]["scope_integrity"]) == 1.0
        and normalized_size <= legacy_size,
        "decision": (
            "Promote normalized parent storage only if source/ranking parity is exact and "
            "the measured database is no larger."
        ),
    }


def _parameter_lane(
    documents: list[Document],
    cases: list[EvaluationCase],
    variant: PipelineVariant,
    factor: str,
    value: int,
    top_k: int,
) -> dict[str, Any]:
    with Index() as index:
        pipeline = Pipeline(index, variant)
        ingest = pipeline.ingest(documents)
        scored = []
        packed_digests = {}
        truncations = 0
        for case in cases:
            started = time.perf_counter()
            retrieved = pipeline.retrieve(case.query, case.scope)
            selected = retrieved[: variant.context_records]
            packed = pipeline._pack(selected, case.scope)
            elapsed_ms = (time.perf_counter() - started) * 1000
            if len(packed) < len(selected) or any(
                len(left.text) != len(right.text)
                for left, right in zip(packed, selected, strict=False)
            ):
                truncations += 1
            evidence = retrieved[:top_k] if factor == "top_k" else packed
            scored.append(
                score_retrieval_case(
                    index,
                    case,
                    evidence,
                    len(evidence) or 1,
                    variant.context_chars,
                    elapsed_ms,
                )
            )
            packed_digests[case.id] = content_digest(
                [item.as_dict() for item in packed]
            )
        aggregate = aggregate_retrieval_cases(
            variant, top_k, ingest, scored
        )["aggregate"]
    return {
        "factor": factor,
        "value": value,
        "variant": variant.as_dict(),
        "top_k": top_k,
        "aggregate": aggregate,
        "truncated_case_count": truncations,
        "packed_evidence_digests": packed_digests,
    }


def evaluate_deterministic_parameters(
    documents: list[Document],
    cases: list[EvaluationCase],
    base: PipelineVariant,
) -> dict[str, Any]:
    baseline = replace(
        base,
        id="parameter-baseline",
        chunking="structure-aware",
        chunk_chars=1200,
        chunk_overlap=180,
        max_chunks=4096,
        context_records=8,
        context_chars=1800,
        context_total_chars=0,
        retrieval="hybrid",
        retrieval_candidates=0,
        dense_candidates="full-scan",
        reranking="deterministic",
        graph="off",
        tools="none",
        prompt="strict-schema",
        rrf_k=60,
        model="deterministic",
        embedding_model="deterministic-local-v1",
    )
    factors = {
        "chunk_chars": (400, 800, 1200, 1800),
        "chunk_overlap": (0, 120, 180, 300),
        "retrieval_candidates": (8, 16, 24, 32, 64),
        "top_k": (4, 8, 12, 16),
        "context_records": (4, 8, 12, 16),
        "context_chars": (600, 1200, 1800, 2400),
        "context_total_chars": (4096, 8192, 14400, 32768),
        "rrf_k": (10, 30, 60, 120),
    }
    baseline_result = _parameter_lane(
        documents, cases, baseline, "baseline", 0, 8
    )
    lanes = []
    for factor, values in factors.items():
        for value in values:
            changes: dict[str, Any] = {} if factor == "top_k" else {factor: value}
            top_k = value if factor == "top_k" else 8
            if factor == "chunk_chars":
                changes["chunk_overlap"] = round(value * 0.15)
            variant = replace(
                baseline,
                id=f"parameter-{factor}-{value}",
                **changes,
            )
            lanes.append(
                _parameter_lane(documents, cases, variant, factor, value, top_k)
            )
    recommendations = {}
    default_values = {
        "chunk_chars": baseline.chunk_chars,
        "chunk_overlap": baseline.chunk_overlap,
        "retrieval_candidates": baseline.retrieval_candidates,
        "top_k": 8,
        "context_records": baseline.context_records,
        "context_chars": baseline.context_chars,
        "context_total_chars": baseline.context_total_chars,
        "rrf_k": baseline.rrf_k,
    }
    quality_keys = ("fact_recall_at_k", "document_recall_at_k", "mrr")
    for factor in factors:
        candidates = [item for item in lanes if item["factor"] == factor]
        winner = max(
            candidates,
            key=lambda item: (
                item["aggregate"]["fact_recall_at_k"],
                item["aggregate"]["document_recall_at_k"],
                item["aggregate"]["mrr"],
                -item["aggregate"]["mean_packed_characters_at_k"],
                -item["value"],
                -item["aggregate"]["latency_p50_ms"],
            ),
        )
        baseline_quality = tuple(
            baseline_result["aggregate"][key] for key in quality_keys
        )
        winner_quality = tuple(winner["aggregate"][key] for key in quality_keys)
        if factor == "rrf_k" and winner_quality <= baseline_quality:
            winner = next(
                item for item in candidates if item["value"] == default_values[factor]
            )
            winner_quality = baseline_quality
        if winner["value"] == default_values[factor]:
            status = "keep"
        elif winner_quality > baseline_quality:
            status = "quality-change-candidate"
        else:
            status = "budget-reduction-candidate"
        recommendations[factor] = {
            "status": status,
            "value": winner["value"],
            "variant_id": winner["variant"]["id"],
            "fact_recall_at_k": winner["aggregate"]["fact_recall_at_k"],
            "mrr": winner["aggregate"]["mrr"],
            "mean_packed_characters": winner["aggregate"]["mean_packed_characters_at_k"],
            "provisional": True,
        }
    return {
        "schema_version": 1,
        "title": "Deterministic One-Factor RAG Parameter Sweep",
        "production_ready": False,
        "method": (
            "Each lane changes one retrieval, chunking, or evidence-budget parameter "
            "from the documented structure-aware baseline."
        ),
        "baseline": baseline.as_dict(),
        "baseline_result": baseline_result,
        "factors": {key: list(values) for key, values in factors.items()},
        "lanes": lanes,
        "recommendations": recommendations,
        "limitations": [
            "Local 32-dimensional embeddings are deterministic controls, not a production retriever.",
            "Model context-window and output-token settings require a separate live lane.",
            "Latency samples are local and uncontended, not portable service-level guarantees.",
        ],
    }


def markdown_scale_report(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['title']}",
        "",
        report["method"],
        "",
        "| Thread | Method | Fact recall | Peak stage chars | p50 ms | Pages |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for result in report["results"]:
        for method in result["methods"]:
            metrics = method["metrics"]
            lines.append(
                f"| {result['thread_size']} | {method['method']} | "
                f"{metrics['answer_fact_recall']:.3f} | {metrics['peak_stage_characters']} | "
                f"{metrics['latency_p50_ms']:.3f} | {method['pages']} |"
            )
    lines.extend(
        [
            "",
            "## Reduction batch sweep on the largest thread",
            "",
            "| Batch size | Fact recall | Peak stage chars | Ledger chars | p50 ms |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for item in report["reduction_batch_sweep"]:
        lines.append(
            f"| {item['batch_size']} | {item['fact_recall']:.3f} | "
            f"{item['peak_stage_characters']} | {item['ledger_characters']} | "
            f"{item['latency_p50_ms']:.3f} |"
        )
    lines.extend(["", "## Decision", "", report["decision"], ""])
    return "\n".join(lines)


def markdown_storage_report(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['title']}",
        "",
        report["method"],
        "",
        "| Layout | DB bytes | Passage chars | Ingest p50 ms | Fact recall | MRR |",
        "|---|---|---|---:|---|---|",
    ]
    for lane in report["lanes"]:
        summary = lane["summary"]
        lines.append(
            f"| {lane['layout']} | {summary['database_bytes']} | "
            f"{summary['passage_characters']} | {summary['ingest_p50_ms']:.3f} | "
            f"{summary['fact_recall']} | {summary['mrr']} |"
        )
    lines.extend(
        [
            "",
            f"Behavioral parity: {report['behavioral_parity']}. Candidate: {report['candidate']}.",
            f"Database change: {report['database_change_percent']:.2f}%.",
            "",
            report["decision"],
            "",
        ]
    )
    return "\n".join(lines)


def markdown_parameter_report(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['title']}",
        "",
        report["method"],
        "",
        "| Factor | Value | Fact recall | MRR | Packed chars | p50 ms | Truncated cases |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for lane in report["lanes"]:
        aggregate = lane["aggregate"]
        lines.append(
            f"| {lane['factor']} | {lane['value']} | "
            f"{aggregate['fact_recall_at_k']:.3f} | {aggregate['mrr']:.3f} | "
            f"{aggregate['mean_packed_characters_at_k']:.1f} | "
            f"{aggregate['latency_p50_ms']:.3f} | {lane['truncated_case_count']} |"
        )
    lines.extend(["", "## Provisional winners", ""])
    for factor, item in report["recommendations"].items():
        lines.append(
            f"- `{factor}`: `{item['value']}` (fact recall "
            f"{item['fact_recall_at_k']:.3f}, MRR {item['mrr']:.3f})."
        )
    lines.append("")
    return "\n".join(lines)


def write_scale_report(
    directory: Path, name: str, report: dict[str, Any], markdown: str
) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / f"{name}.json"
    markdown_path = directory / f"{name}.md"
    checkpoint(json_path, report)
    temporary = markdown_path.with_suffix(markdown_path.suffix + ".tmp")
    temporary.write_text(markdown, encoding="utf-8")
    temporary.replace(markdown_path)
    return {"json": json_path, "markdown": markdown_path}
