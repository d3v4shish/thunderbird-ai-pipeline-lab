# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0.

"""Stage-isolated, deterministic RAG evaluation and reporting."""

from __future__ import annotations

from dataclasses import replace
import json
from math import log2
from pathlib import Path
import statistics
import time
from typing import Any

from .contracts import Document, EvaluationCase, Evidence, PipelineVariant
from .evaluation import evaluate_variant, percentile
from .graph import graph_id
from .pipeline import Pipeline
from .storage import Index
from .text import chunk_document, verify_chunks


TOP_K_DEFAULT = 8


def _supports_fact(text: str, fact_id: str, value: str) -> bool:
    folded = text.casefold()
    return f"[fact {fact_id}]".casefold() in folded and value.casefold() in folded


def _covered_characters(spans: list[tuple[int, int]]) -> int:
    if not spans:
        return 0
    covered = 0
    current_start, current_end = sorted(spans)[0]
    for start, end in sorted(spans)[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            covered += current_end - current_start
            current_start, current_end = start, end
    return covered + current_end - current_start


def _evidence_redundancy(evidence: list[Evidence]) -> float:
    total = sum(max(0, item.end - item.start) for item in evidence)
    if not total:
        return 0.0
    grouped: dict[str, list[tuple[int, int]]] = {}
    for item in evidence:
        grouped.setdefault(item.document_id, []).append((item.start, item.end))
    unique = sum(_covered_characters(spans) for spans in grouped.values())
    return max(0.0, 1.0 - unique / total)


def _chunking_metrics(
    documents: list[Document],
    cases: list[EvaluationCase],
    variant: PipelineVariant,
) -> dict[str, Any]:
    started = time.perf_counter()
    chunks_by_document = {}
    source_characters = 0
    covered_characters = 0
    total_context_characters = 0
    total_retrieval_characters = 0
    total_passage_characters = 0
    truncated_documents = []
    section_chunks = 0
    chunk_count = 0
    for document in documents:
        chunks = chunk_document(
            document,
            variant.chunking,
            variant.chunk_chars,
            variant.chunk_overlap,
            variant.max_chunks,
        )
        verify_chunks(document, chunks)
        chunks_by_document[(document.tenant, document.collection, document.id)] = chunks
        source_characters += len(document.text)
        covered = _covered_characters([(item.start, item.end) for item in chunks])
        covered_characters += covered
        total_passage_characters += sum(len(item.text) for item in chunks)
        total_context_characters += sum(len(item.contextual_text) for item in chunks)
        total_retrieval_characters += sum(
            len(item.retrieval_text or item.contextual_text) for item in chunks
        )
        section_chunks += sum(bool(item.section) for item in chunks)
        chunk_count += len(chunks)
        if covered < len(document.text):
            truncated_documents.append(
                {
                    "document_id": document.id,
                    "source_characters": len(document.text),
                    "covered_characters": covered,
                }
            )

    labeled_facts: dict[tuple[str, str], dict[str, Any]] = {}
    for case in cases:
        for fact_id, value in case.expected_facts.items():
            key = (fact_id, value)
            if key in labeled_facts:
                continue
            source_ids = [
                document.id
                for document in documents
                if document.tenant == case.scope.tenant
                and document.collection == case.scope.collection
                and _supports_fact(document.text, fact_id, value)
            ]
            intact_ids = [
                document_id
                for document_id in source_ids
                if any(
                    _supports_fact(chunk.text, fact_id, value)
                    for chunk in chunks_by_document.get(
                        (case.scope.tenant, case.scope.collection, document_id), []
                    )
                )
            ]
            labeled_facts[key] = {
                "fact_id": fact_id,
                "value": value,
                "source_document_ids": source_ids,
                "intact_document_ids": intact_ids,
                "intact": bool(source_ids) and set(source_ids) <= set(intact_ids),
            }
    split_facts = [item for item in labeled_facts.values() if not item["intact"]]
    fact_count = len(labeled_facts)
    return {
        "variant": variant.as_dict(),
        "metrics": {
            "source_coverage": covered_characters / source_characters
            if source_characters
            else 1.0,
            "fact_integrity": (fact_count - len(split_facts)) / fact_count
            if fact_count
            else 1.0,
            "passage_redundancy": 1.0 - covered_characters / total_passage_characters
            if total_passage_characters
            else 0.0,
            "section_label_rate": section_chunks / chunk_count if chunk_count else 0.0,
            "mean_passage_characters": total_passage_characters / chunk_count
            if chunk_count
            else 0.0,
            "mean_retrieval_characters": total_retrieval_characters / chunk_count
            if chunk_count
            else 0.0,
            "index_context_characters": total_context_characters,
            "chunk_count": chunk_count,
            "truncated_document_count": len(truncated_documents),
            "wall_ms": (time.perf_counter() - started) * 1000,
        },
        "truncated_documents": truncated_documents,
        "split_facts": split_facts,
        "documents": [
            {
                "document_id": document.id,
                "source_characters": len(document.text),
                "chunk_count": len(
                    chunks_by_document[(document.tenant, document.collection, document.id)]
                ),
                "covered_characters": _covered_characters(
                    [
                        (item.start, item.end)
                        for item in chunks_by_document[
                            (document.tenant, document.collection, document.id)
                        ]
                    ]
                ),
            }
            for document in documents
        ],
    }


def score_retrieval_case(
    index: Index,
    case: EvaluationCase,
    evidence: list[Evidence],
    top_k: int,
    context_chars: int,
    elapsed_ms: float,
) -> dict[str, Any]:
    """Score already-retrieved canonical evidence for one frozen case."""
    evidence = evidence[:top_k]
    expected_documents = set(case.expected_document_ids)
    retrieved_documents = list(dict.fromkeys(item.document_id for item in evidence))
    matched_documents = expected_documents & set(retrieved_documents)
    document_recall = (
        len(matched_documents) / len(expected_documents)
        if expected_documents
        else None
    )
    first_relevant = next(
        (
            rank
            for rank, item in enumerate(evidence, 1)
            if item.document_id in expected_documents
        ),
        None,
    )
    reciprocal_rank = 1.0 / first_relevant if first_relevant else 0.0
    seen_documents: set[str] = set()
    gains = []
    for item in evidence:
        gain = int(
            item.document_id in expected_documents
            and item.document_id not in seen_documents
        )
        gains.append(gain)
        if gain:
            seen_documents.add(item.document_id)
    dcg = sum(gain / log2(rank + 1) for rank, gain in enumerate(gains, 1))
    ideal_count = min(len(expected_documents), top_k)
    ideal_dcg = sum(1.0 / log2(rank + 1) for rank in range(1, ideal_count + 1))
    matched_facts = {
        fact_id: value
        for fact_id, value in case.expected_facts.items()
        if any(_supports_fact(item.text, fact_id, value) for item in evidence)
    }
    fact_ranks = {
        fact_id: next(
            rank
            for rank, item in enumerate(evidence, 1)
            if _supports_fact(item.text, fact_id, value)
        )
        for fact_id, value in matched_facts.items()
    }
    source_coverage = None
    expected_source_characters = 0
    covered_source_characters = 0
    for document_id in expected_documents:
        document = index.document(document_id, case.scope)
        if not document:
            continue
        expected_source_characters += len(document.text)
        covered_source_characters += _covered_characters(
            [
                (item.start, item.end)
                for item in evidence
                if item.document_id == document_id
            ]
        )
    if expected_source_characters:
        source_coverage = covered_source_characters / expected_source_characters
    scope_violations = [
        item.citation
        for item in evidence
        if item.tenant != case.scope.tenant or item.collection != case.scope.collection
    ]
    return {
        "case_id": case.id,
        "query": case.query,
        "expected_document_ids": list(case.expected_document_ids),
        "expected_facts": dict(case.expected_facts),
        "matched_facts": matched_facts,
        "fact_ranks": fact_ranks,
        "metrics": {
            "document_recall_at_k": document_recall,
            "reciprocal_rank": reciprocal_rank if expected_documents else None,
            "ndcg_at_k": dcg / ideal_dcg if ideal_dcg else None,
            "fact_recall_at_k": len(matched_facts) / len(case.expected_facts)
            if case.expected_facts
            else None,
            "fact_mrr": sum(1.0 / rank for rank in fact_ranks.values())
            / len(case.expected_facts)
            if case.expected_facts
            else None,
            "expected_source_coverage_at_k": source_coverage,
            "evidence_redundancy": _evidence_redundancy(evidence),
            "packed_characters_at_k": sum(
                min(len(item.text), context_chars)
                for item in evidence
            ),
            "scope_integrity": 0.0 if scope_violations else 1.0,
            "latency_ms": elapsed_ms,
        },
        "scope_violations": scope_violations,
        "evidence": [item.as_dict() for item in evidence],
    }


def _retrieval_case(
    pipeline: Pipeline,
    index: Index,
    case: EvaluationCase,
    top_k: int,
) -> dict[str, Any]:
    started = time.perf_counter()
    evidence = pipeline.retrieve(case.query, case.scope)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return score_retrieval_case(
        index,
        case,
        evidence,
        top_k,
        pipeline.variant.context_chars,
        elapsed_ms,
    )


def _retrieval_metrics(
    documents: list[Document],
    cases: list[EvaluationCase],
    variant: PipelineVariant,
    top_k: int,
) -> dict[str, Any]:
    with Index() as index:
        pipeline = Pipeline(index, variant)
        ingest = pipeline.ingest(documents)
        return retrieval_metrics_from_index(
            pipeline, index, cases, top_k, ingest
        )


def retrieval_metrics_from_index(
    pipeline: Pipeline,
    index: Index,
    cases: list[EvaluationCase],
    top_k: int,
    ingest: dict[str, Any],
) -> dict[str, Any]:
    """Score a prebuilt index with the staged suite's retrieval contract."""
    results = [_retrieval_case(pipeline, index, case, top_k) for case in cases]
    return aggregate_retrieval_cases(
        pipeline.variant, top_k, ingest, results
    )


def aggregate_retrieval_cases(
    variant: PipelineVariant,
    top_k: int,
    ingest: dict[str, Any],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate case records produced by :func:`score_retrieval_case`."""
    scored = [
        item
        for item in results
        if item["metrics"]["document_recall_at_k"] is not None
    ]
    expected_fact_count = sum(len(item["expected_facts"]) for item in results)
    matched_fact_count = sum(len(item["matched_facts"]) for item in results)
    fact_reciprocal_rank_sum = sum(
        sum(1.0 / rank for rank in item["fact_ranks"].values())
        for item in results
    )
    latencies = [item["metrics"]["latency_ms"] for item in results]
    return {
        "variant": variant.as_dict(),
        "top_k": top_k,
        "ingest": ingest,
        "aggregate": {
            "document_recall_at_k": statistics.fmean(
                item["metrics"]["document_recall_at_k"] for item in scored
            )
            if scored
            else 1.0,
            "mrr": statistics.fmean(
                item["metrics"]["reciprocal_rank"] for item in scored
            )
            if scored
            else 1.0,
            "ndcg_at_k": statistics.fmean(
                item["metrics"]["ndcg_at_k"] for item in scored
            )
            if scored
            else 1.0,
            "fact_recall_at_k": matched_fact_count / expected_fact_count
            if expected_fact_count
            else 1.0,
            "fact_mrr": fact_reciprocal_rank_sum / expected_fact_count
            if expected_fact_count
            else 1.0,
            "scope_integrity": min(
                item["metrics"]["scope_integrity"] for item in results
            )
            if results
            else 1.0,
            "mean_evidence_redundancy": statistics.fmean(
                item["metrics"]["evidence_redundancy"] for item in results
            )
            if results
            else 0.0,
            "mean_packed_characters_at_k": statistics.fmean(
                item["metrics"]["packed_characters_at_k"] for item in results
            )
            if results
            else 0.0,
            "latency_p50_ms": percentile(latencies, 0.50),
            "latency_p95_ms": percentile(latencies, 0.95),
        },
        "cases": results,
    }


def _graph_metrics(
    documents: list[Document],
    graph_cases: list[EvaluationCase],
    variant: PipelineVariant,
    top_k: int,
) -> dict[str, Any]:
    with Index() as index:
        pipeline = Pipeline(index, variant)
        ingest = pipeline.ingest(documents)
        results = []
        for case in graph_cases:
            started = time.perf_counter()
            evidence = pipeline.retrieve(case.query, case.scope)[:top_k]
            graph_context = pipeline.last_graph_context
            elapsed_ms = (time.perf_counter() - started) * 1000
            edges = graph_context.get("edges", [])
            matched_relations = []
            for source, predicate, target in case.expected_relations:
                source_suffix = graph_id("entity", source).split(":", 1)[1]
                target_suffix = graph_id("entity", target).split(":", 1)[1]
                if any(
                    edge.get("predicate") == predicate
                    and str(edge.get("source_id", "")).endswith(source_suffix)
                    and str(edge.get("target_id", "")).endswith(target_suffix)
                    for edge in edges
                ):
                    matched_relations.append((source, predicate, target))
            invalid_provenance = []
            for edge in edges:
                document = index.document(str(edge["source_document_id"]), case.scope)
                start, end = int(edge["source_start"]), int(edge["source_end"])
                if not document or start < 0 or end <= start or end > len(document.text):
                    invalid_provenance.append(str(edge.get("id", "unknown")))
            matched_facts = {
                fact_id: value
                for fact_id, value in case.expected_facts.items()
                if any(_supports_fact(item.text, fact_id, value) for item in evidence)
            }
            results.append(
                {
                    "case_id": case.id,
                    "query": case.query,
                    "expected_relations": [list(item) for item in case.expected_relations],
                    "matched_relations": [list(item) for item in matched_relations],
                    "matched_facts": matched_facts,
                    "metrics": {
                        "relation_recall": len(matched_relations)
                        / len(case.expected_relations)
                        if case.expected_relations
                        else 1.0,
                        "fact_recall_at_k": len(matched_facts)
                        / len(case.expected_facts)
                        if case.expected_facts
                        else 1.0,
                        "provenance_validity": 0.0 if invalid_provenance else 1.0,
                        "latency_ms": elapsed_ms,
                    },
                    "invalid_provenance": invalid_provenance,
                    "graph_context": graph_context,
                    "evidence": [item.as_dict() for item in evidence],
                }
            )
    return {
        "variant": variant.as_dict(),
        "top_k": top_k,
        "ingest": ingest,
        "aggregate": {
            "relation_recall": statistics.fmean(
                item["metrics"]["relation_recall"] for item in results
            )
            if results
            else 1.0,
            "fact_recall_at_k": statistics.fmean(
                item["metrics"]["fact_recall_at_k"] for item in results
            )
            if results
            else 1.0,
            "provenance_validity": min(
                item["metrics"]["provenance_validity"] for item in results
            )
            if results
            else 1.0,
        },
        "cases": results,
    }


def _retrieval_variant(
    base: PipelineVariant, variant_id: str, **updates: Any
) -> PipelineVariant:
    return replace(
        base,
        id=variant_id,
        model="deterministic",
        embedding_model="deterministic-local-v1",
        tools="none",
        prompt="strict-schema",
        **updates,
    )


def evaluate_rag_stages(
    documents: list[Document],
    cases: list[EvaluationCase],
    base: PipelineVariant,
    top_k: int = TOP_K_DEFAULT,
) -> dict[str, Any]:
    if not 1 <= top_k <= 100:
        raise ValueError("top_k must be between 1 and 100")
    chunking = []
    for mode in ("fixed", "structure-aware", "sentence-window"):
        variant = _retrieval_variant(
            base,
            f"chunk-{mode}",
            chunking=mode,
            max_chunks=4096 if mode != "fixed" else base.max_chunks,
            retrieval="hybrid",
            reranking="deterministic",
            graph="off",
            adaptive_searches=1,
        )
        probe = _retrieval_metrics(documents, cases, variant, top_k)
        chunking.append(
            {
                **_chunking_metrics(documents, cases, variant),
                "retrieval_probe": probe["aggregate"],
                "retrieval_cases": probe["cases"],
            }
        )

    chunk_size = []
    for chunk_chars in (400, 800, 1200, 1800):
        overlap = round(chunk_chars * 0.15)
        variant = _retrieval_variant(
            base,
            f"chunk-size-{chunk_chars}",
            chunking="structure-aware",
            chunk_chars=chunk_chars,
            chunk_overlap=overlap,
            max_chunks=4096,
            retrieval="hybrid",
            reranking="deterministic",
            graph="off",
            adaptive_searches=1,
        )
        probe = _retrieval_metrics(documents, cases, variant, top_k)
        chunk_size.append(
            {
                **_chunking_metrics(documents, cases, variant),
                "retrieval_probe": probe["aggregate"],
                "retrieval_cases": probe["cases"],
            }
        )

    retrieval = []
    for mode in ("exact", "lexical", "dense", "hybrid"):
        variant = _retrieval_variant(
            base,
            f"retrieval-{mode}",
            chunking="structure-aware",
            max_chunks=4096,
            retrieval=mode,
            reranking="none",
            graph="off",
            adaptive_searches=1,
        )
        retrieval.append(_retrieval_metrics(documents, cases, variant, top_k))

    retrieval_depth = []
    for depth in (4, 8, 16):
        variant = _retrieval_variant(
            base,
            f"top-k-{depth}",
            chunking="structure-aware",
            max_chunks=4096,
            retrieval="hybrid",
            reranking="deterministic",
            graph="off",
            adaptive_searches=1,
        )
        retrieval_depth.append(
            _retrieval_metrics(documents, cases, variant, depth)
        )

    query_expansion = []
    for label, searches in (("single", 1), ("adaptive", 3)):
        variant = _retrieval_variant(
            base,
            f"query-{label}",
            chunking="structure-aware",
            max_chunks=4096,
            retrieval="hybrid",
            reranking="none",
            graph="off",
            adaptive_searches=searches,
        )
        query_expansion.append(_retrieval_metrics(documents, cases, variant, top_k))

    reranking = []
    for mode in ("none", "deterministic", "embedding"):
        variant = _retrieval_variant(
            base,
            f"rerank-{mode}",
            chunking="structure-aware",
            max_chunks=4096,
            retrieval="hybrid",
            reranking=mode,
            graph="off",
            adaptive_searches=1,
        )
        reranking.append(_retrieval_metrics(documents, cases, variant, top_k))

    graph_cases = [case for case in cases if case.expected_relations]
    graph = []
    for mode in ("off", "keyword", "intent-multihop"):
        variant = _retrieval_variant(
            base,
            f"graph-{mode}",
            chunking="structure-aware",
            max_chunks=4096,
            retrieval="hybrid",
            reranking="deterministic",
            graph=mode,
            adaptive_searches=3,
        )
        graph.append(_graph_metrics(documents, graph_cases, variant, top_k))

    full_variants = [
        replace(base, id="full-current", model="deterministic"),
        replace(
            base,
            id="full-advanced-structure",
            model="deterministic",
            chunking="structure-aware",
            max_chunks=4096,
            retrieval="hybrid",
            reranking="deterministic",
            graph="intent-multihop",
            tools="coverage-aware",
            prompt="evidence-ledger",
            adaptive_searches=3,
        ),
        replace(
            base,
            id="full-advanced-sentence-window",
            model="deterministic",
            chunking="sentence-window",
            max_chunks=4096,
            retrieval="hybrid",
            reranking="deterministic",
            graph="intent-multihop",
            tools="coverage-aware",
            prompt="evidence-ledger",
            adaptive_searches=3,
        ),
    ]
    full_pipeline = [
        evaluate_variant(documents, cases, variant) for variant in full_variants
    ]

    def best_retrieval(records: list[dict[str, Any]]) -> str:
        return max(
            records,
            key=lambda item: (
                item["aggregate"]["fact_recall_at_k"],
                item["aggregate"]["document_recall_at_k"],
                item["aggregate"]["mrr"],
                -item["aggregate"]["mean_evidence_redundancy"],
                item["variant"]["id"],
            ),
        )["variant"]["id"]

    chunking_candidates = [
        item
        for item in chunking
        if item["metrics"]["source_coverage"] == 1.0
        and item["metrics"]["fact_integrity"] == 1.0
        and item["metrics"]["passage_redundancy"] <= 0.5
    ]
    recommended_chunking = max(
        chunking_candidates or chunking,
        key=lambda item: (
            item["retrieval_probe"]["fact_recall_at_k"],
            -item["metrics"]["passage_redundancy"],
            item["variant"]["id"],
        ),
    )["variant"]["id"]

    return {
        "schema_version": 1,
        "title": "Staged Advanced-RAG Evaluation",
        "top_k": top_k,
        "production_ready": False,
        "method": (
            "One-factor deterministic ablations run before final generation; "
            "no live model or external corpus is used."
        ),
        "technique_coverage": [
            {"technique": "Hybrid retrieval", "status": "tested", "stage": "retrieval"},
            {"technique": "Cross-encoder reranking", "status": "partial", "stage": "reranking", "note": "Local deterministic and embedding rerankers are tested; a true cross-encoder remains an endpoint lane."},
            {"technique": "Contextual retrieval", "status": "partial", "stage": "chunking", "note": "Deterministic metadata context is tested here; query-independent LLM-generated context has a separate live contextual-rag-evaluate lane."},
            {"technique": "HyDE", "status": "tested", "stage": "query transformation", "note": "A separate live query-rag-evaluate lane tests corpus-blind model generation while retaining only canonical source passages as evidence."},
            {"technique": "Self-RAG", "status": "deferred", "stage": "generation", "note": "Requires a reflection-trained model; current validation provides only a support gate."},
            {"technique": "CRAG", "status": "partial", "stage": "quality gate", "note": "A separate live lane grades, locally retries, and filters evidence; web fallback is intentionally excluded from the loopback-only lab."},
            {"technique": "Adaptive RAG", "status": "tested", "stage": "query routing", "note": "A separate live model router chooses only measured retrieval methods and always retrieves corpus evidence."},
            {"technique": "GraphRAG", "status": "partial", "stage": "graph", "note": "Source-backed relation traversal is tested; Microsoft-style community summaries and global search are not implemented."},
            {"technique": "RAPTOR", "status": "deferred", "stage": "hierarchical retrieval", "note": "Tree summaries need a larger long-document benchmark and extra indexing calls."},
            {"technique": "RAG Fusion", "status": "tested", "stage": "query expansion", "note": "A separate live lane generates bounded model rewrites and combines their canonical rankings with reciprocal-rank fusion."},
            {"technique": "Sentence window / parent-child", "status": "tested", "stage": "chunking"},
            {"technique": "Modular RAG", "status": "tested", "stage": "all", "note": "The report isolates swappable chunking, retrieval, reranking, graph, and generation stages."},
        ],
        "stages": {
            "chunking": chunking,
            "chunk_size": chunk_size,
            "retrieval": retrieval,
            "retrieval_depth": retrieval_depth,
            "query_expansion": query_expansion,
            "reranking": reranking,
            "graph": graph,
            "full_pipeline": full_pipeline,
        },
        "recommendations": {
            "chunking": recommended_chunking,
            "chunk_size": max(
                chunk_size,
                key=lambda item: (
                    item["retrieval_probe"]["fact_recall_at_k"],
                    -item["retrieval_probe"]["mean_packed_characters_at_k"],
                    -item["metrics"]["passage_redundancy"],
                ),
            )["variant"]["id"],
            "retrieval": best_retrieval(retrieval),
            "retrieval_depth": best_retrieval(retrieval_depth),
            "query_expansion": best_retrieval(query_expansion),
            "reranking": best_retrieval(reranking),
            "graph": max(
                graph,
                key=lambda item: (
                    item["aggregate"]["relation_recall"],
                    item["aggregate"]["fact_recall_at_k"],
                    item["variant"]["id"],
                ),
            )["variant"]["id"],
            "full_pipeline": max(
                full_pipeline,
                key=lambda item: (
                    item["aggregate"]["hard_gate_pass"],
                    item["aggregate"]["quality_score"],
                    -item["aggregate"]["latency_p50_ms"],
                ),
            )["variant"]["id"],
        },
        "recommendation_notes": {
            "chunking": "Sentence-window has the highest retrieval fact recall but is not the default while duplicated parent passages exceed 50% redundancy; normalize parent storage before promotion.",
            "chunk_size": "Chunk-size and top-K winners optimize recall first, then packed context size. Re-run these sweeps on realistic thread-length and paraphrase cases before changing Thunderbird defaults.",
            "retrieval": "Lexical search wins this exact-term synthetic corpus. Keep hybrid as the production candidate until a semantic/paraphrase corpus and real embedding model are evaluated.",
            "advanced_methods": "HyDE, generated RAG Fusion, decomposition, step-back, local corrective retrieval, and adaptive model routing are evaluated by a separate live command. RAPTOR, Self-RAG, and a true cross-encoder remain deferred and are not mixed into this deterministic baseline.",
        },
    }


def markdown_rag_report(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['title']}",
        "",
        report["method"],
        "",
        f"Top-K: {report['top_k']}. Production ready: {report['production_ready']}.",
        "",
        "## Technique coverage",
        "",
        "| Technique | Status | Isolated stage | Note |",
        "|---|---|---|---|",
    ]
    for item in report["technique_coverage"]:
        lines.append(
            f"| {item['technique']} | {item['status']} | {item['stage']} | {item.get('note', '')} |"
        )
    lines.extend(
        [
            "",
            "## Chunking",
            "",
            "| Variant | Source coverage | Fact integrity | Redundancy | Chunks | Retrieval fact recall | Retrieval MRR |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for item in report["stages"]["chunking"]:
        metrics = item["metrics"]
        probe = item["retrieval_probe"]
        lines.append(
            f"| {item['variant']['id']} | {metrics['source_coverage']:.3f} | "
            f"{metrics['fact_integrity']:.3f} | {metrics['passage_redundancy']:.3f} | "
            f"{metrics['chunk_count']} | {probe['fact_recall_at_k']:.3f} | {probe['mrr']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Chunk-size sweep",
            "",
            "| Variant | Size | Overlap | Chunks | Fact recall | Packed chars/query | Redundancy |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for item in report["stages"]["chunk_size"]:
        variant = item["variant"]
        metrics = item["metrics"]
        probe = item["retrieval_probe"]
        lines.append(
            f"| {variant['id']} | {variant['chunk_chars']} | {variant['chunk_overlap']} | "
            f"{metrics['chunk_count']} | {probe['fact_recall_at_k']:.3f} | "
            f"{probe['mean_packed_characters_at_k']:.1f} | {metrics['passage_redundancy']:.3f} |"
        )
    for stage in ("retrieval", "retrieval_depth", "query_expansion", "reranking"):
        lines.extend(
            [
                "",
                f"## {stage.replace('_', ' ').title()}",
                "",
                "| Variant | K | Document recall | Fact recall | MRR | nDCG | Packed chars/query | Redundancy | p50 ms |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for item in report["stages"][stage]:
            metrics = item["aggregate"]
            lines.append(
                f"| {item['variant']['id']} | {item['top_k']} | {metrics['document_recall_at_k']:.3f} | "
                f"{metrics['fact_recall_at_k']:.3f} | {metrics['mrr']:.3f} | "
                f"{metrics['ndcg_at_k']:.3f} | {metrics['mean_packed_characters_at_k']:.1f} | "
                f"{metrics['mean_evidence_redundancy']:.3f} | "
                f"{metrics['latency_p50_ms']:.3f} |"
            )
    lines.extend(
        [
            "",
            "## Graph retrieval",
            "",
            "| Variant | Relation recall | Fact recall | Provenance validity |",
            "|---|---:|---:|---:|",
        ]
    )
    for item in report["stages"]["graph"]:
        metrics = item["aggregate"]
        lines.append(
            f"| {item['variant']['id']} | {metrics['relation_recall']:.3f} | "
            f"{metrics['fact_recall_at_k']:.3f} | {metrics['provenance_validity']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Full deterministic pipeline",
            "",
            "| Variant | Quality | Document recall | Fact recall | Answer | Graph | Hard gate | Quality gate |",
            "|---|---:|---:|---:|---:|---:|:---:|:---:|",
        ]
    )
    for item in report["stages"]["full_pipeline"]:
        metrics = item["aggregate"]
        lines.append(
            f"| {item['variant']['id']} | {metrics['quality_score']:.3f} | "
            f"{metrics['recall_at_8']:.3f} | {metrics['required_fact_recall']:.3f} | "
            f"{metrics['answer_correctness']:.3f} | {metrics['graph_relation_recall']:.3f} | "
            f"{'pass' if metrics['hard_gate_pass'] else 'fail'} | "
            f"{'pass' if metrics['quality_pass'] else 'fail'} |"
        )
    lines.extend(["", "## Stage recommendations", ""])
    for stage, winner in report["recommendations"].items():
        lines.append(f"- {stage.replace('_', ' ').title()}: `{winner}`")
    lines.extend(["", "## Recommendation notes", ""])
    for note in report["recommendation_notes"].values():
        lines.append(f"- {note}")
    lines.extend(
        [
            "",
            "## Per-case retrieval audit",
            "",
            "Every evidence span below is preserved in full in the JSON companion.",
        ]
    )

    def formatted(value: float | None) -> str:
        return "not scored" if value is None else f"{value:.3f}"

    for stage in (
        "chunking",
        "chunk_size",
        "retrieval",
        "retrieval_depth",
        "query_expansion",
        "reranking",
    ):
        lines.extend(
            [
                "",
                f"### {stage.replace('_', ' ').title()}",
                "",
                "| Variant | K | Case | Document recall | Fact recall | MRR | Source coverage | Evidence spans |",
                "|---|---:|---|---:|---:|---:|---:|---|",
            ]
        )
        for item in report["stages"][stage]:
            case_results = item.get("cases", item.get("retrieval_cases", []))
            item_top_k = item.get("top_k", report["top_k"])
            for case in case_results:
                metrics = case["metrics"]
                citations = "; ".join(
                    evidence["citation"] for evidence in case["evidence"]
                ) or "none"
                lines.append(
                    f"| {item['variant']['id']} | {item_top_k} | {case['case_id']} | "
                    f"{formatted(metrics['document_recall_at_k'])} | "
                    f"{formatted(metrics['fact_recall_at_k'])} | "
                    f"{formatted(metrics['reciprocal_rank'])} | "
                    f"{formatted(metrics['expected_source_coverage_at_k'])} | {citations} |"
                )
    lines.extend(
        [
            "",
            "## Per-case graph audit",
            "",
            "| Variant | Case | Relations matched | Relations expected | Fact recall | Provenance | Evidence spans |",
            "|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for item in report["stages"]["graph"]:
        for case in item["cases"]:
            citations = "; ".join(
                evidence["citation"] for evidence in case["evidence"]
            ) or "none"
            lines.append(
                f"| {item['variant']['id']} | {case['case_id']} | "
                f"{len(case['matched_relations'])} | {len(case['expected_relations'])} | "
                f"{case['metrics']['fact_recall_at_k']:.3f} | "
                f"{case['metrics']['provenance_validity']:.3f} | {citations} |"
            )
    lines.extend(
        [
            "",
            "## Per-case full-pipeline audit",
            "",
            "| Variant | Case | Facts matched | Facts expected | Answer score | Graph score | Hard failures | Validated answer |",
            "|---|---|---:|---:|---:|---:|---|---|",
        ]
    )
    for item in report["stages"]["full_pipeline"]:
        for case in item["cases"]:
            output = case.get("output", {})
            answer = str(output.get("answer", case.get("error", ""))).replace(
                "|", "\\|"
            )
            lines.append(
                f"| {item['variant']['id']} | {case['case_id']} | "
                f"{len(case.get('matched_facts', {}))} | {len(case.get('expected_facts', {}))} | "
                f"{case['metrics']['answer_correctness']:.3f} | "
                f"{case['metrics']['graph_relation_recall']:.3f} | "
                f"{', '.join(case.get('hard_failures', [])) or 'none'} | {answer} |"
            )
    lines.extend(
        [
            "",
            "These winners are corpus-specific deterministic measurements, not a production-readiness claim.",
            "The JSON companion contains every case metric, evidence span, graph edge, prompt, and validated output.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_rag_report(
    directory: Path, name: str, report: dict[str, Any]
) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": directory / f"{name}.json",
        "markdown": directory / f"{name}.md",
    }
    payloads = {
        paths["json"]: json.dumps(
            report, ensure_ascii=False, indent=2, sort_keys=True
        )
        + "\n",
        paths["markdown"]: markdown_rag_report(report),
    }
    for path, payload in payloads.items():
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(payload, encoding="utf-8")
        temporary.replace(path)
    return paths
