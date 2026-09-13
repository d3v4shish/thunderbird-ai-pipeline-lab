# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0.

"""Objective case scoring, hard gates, and aggregate metrics."""

from __future__ import annotations

from pathlib import Path
import resource
import statistics
import tempfile
import time
from typing import Any

from .contracts import Document, EvaluationCase, PipelineVariant
from .models import OllamaClient, RerankerClient
from .pipeline import Pipeline
from .graph import graph_id
from .storage import Index


QUALITY_THRESHOLDS = {
    "recall_at_8": 0.95,
    "mrr": 0.85,
    "required_fact_recall": 0.90,
    "answer_correctness": 1.0,
    "citation_precision": 1.0,
    "structured_output_acceptance": 0.98,
    "tool_argument_validity": 0.99,
    "endpoint_success": 0.98,
    "graph_relation_recall": 0.90,
}


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * fraction))))
    return ordered[index]


def score_case(case: EvaluationCase, output: Any, elapsed_ms: float) -> dict[str, Any]:
    retrieved = [item.document_id for item in output.evidence[:8]]
    expected_documents = set(case.expected_document_ids)
    if expected_documents:
        recall = len(expected_documents & set(retrieved)) / len(expected_documents)
        ranks = [retrieved.index(item) + 1 for item in expected_documents if item in retrieved]
        reciprocal_rank = 1 / min(ranks) if ranks else 0.0
    else:
        recall = 1.0 if output.abstained else 0.0
        reciprocal_rank = recall
    combined_output = f"{output.answer}\n{' '.join(output.facts.values())}"
    matched_facts = {
        key: value
        for key, value in case.expected_facts.items()
        if output.facts.get(key) == value
    }
    fact_id_mismatches = {
        expected_key: sorted(
            actual_key
            for actual_key, actual_value in output.facts.items()
            if actual_key != expected_key and actual_value == expected_value
        )
        for expected_key, expected_value in case.expected_facts.items()
        if output.facts.get(expected_key) != expected_value
        and any(
            actual_key != expected_key and actual_value == expected_value
            for actual_key, actual_value in output.facts.items()
        )
    }
    fact_recall = len(matched_facts) / len(case.expected_facts) if case.expected_facts else 1.0
    answer_scored = bool(case.expected_answer_values) or case.require_abstention
    if case.expected_answer_values:
        answer_correct = not output.abstained and all(
            value.casefold() in output.answer.casefold()
            for value in case.expected_answer_values
        )
    elif case.require_abstention:
        answer_correct = output.abstained
    else:
        answer_correct = True
    evidence_citations = {item.citation for item in output.evidence}
    valid_citations = [citation for citation in output.citations if citation in evidence_citations]
    citation_precision = (
        len(valid_citations) / len(output.citations) if output.citations else (1.0 if output.abstained else 0.0)
    )
    forbidden = [claim for claim in case.forbidden_claims if claim.casefold() in combined_output.casefold()]
    scope_leaks = [
        item.citation
        for item in output.evidence
        if item.tenant != case.scope.tenant or item.collection != case.scope.collection
    ]
    span_failures = [
        error for error in output.errors if "SOURCE_SPAN" in error
    ]
    invalid_tools = [
        call
        for call in output.tool_calls
        if call.get("name") not in case.allowed_tools
    ]
    invalid_tool_arguments = [
        call for call in output.tool_calls if not call.get("accepted", True)
    ]
    structured = not any(
        error
        in {
            "MALFORMED_MODEL_JSON",
            "MODEL_OUTPUT_NOT_OBJECT",
            "MODEL_OUTPUT_SCHEMA_INVALID",
            "ABSTENTION_CONFLICT",
        }
        for error in output.errors
    )
    hard_failures: list[str] = []
    if scope_leaks:
        hard_failures.append("SCOPE_LEAKAGE")
    if forbidden:
        hard_failures.append("FORBIDDEN_OR_SUBSTITUTED_CLAIM")
    if "CITATION_OUTSIDE_EVIDENCE" in output.errors:
        hard_failures.append("CITATION_OUTSIDE_EVIDENCE")
    if invalid_tools:
        hard_failures.append("OUT_OF_SCOPE_TOOL_CALL")
    if span_failures:
        hard_failures.append("SOURCE_SPAN_FAILURE")
    if case.require_abstention and not output.abstained:
        hard_failures.append("FAILED_TO_ABSTAIN")
    graph_edges = output.graph_context.get("edges", [])
    matched_relations = []
    for source, predicate, target in case.expected_relations:
        source_suffix = graph_id("entity", source).split(":", 1)[1]
        target_suffix = graph_id("entity", target).split(":", 1)[1]
        if any(
            edge.get("predicate") == predicate
            and str(edge.get("source_id", "")).endswith(source_suffix)
            and str(edge.get("target_id", "")).endswith(target_suffix)
            for edge in graph_edges
        ):
            matched_relations.append((source, predicate, target))
    graph_recall = (
        len(matched_relations) / len(case.expected_relations)
        if case.expected_relations
        else 1.0
    )
    return {
        "case_id": case.id,
        "query": case.query,
        "scope": case.scope.as_dict(),
        "expected_document_ids": list(case.expected_document_ids),
        "expected_facts": dict(case.expected_facts),
        "expected_answer_values": list(case.expected_answer_values),
        "forbidden_claims": list(case.forbidden_claims),
        "expected_relations": [list(item) for item in case.expected_relations],
        "matched_relations": [list(item) for item in matched_relations],
        "retrieved_document_ids": retrieved,
        "matched_facts": matched_facts,
        "fact_id_mismatches": fact_id_mismatches,
        "answer_scored": answer_scored,
        "forbidden_matches": forbidden,
        "metrics": {
            "recall_at_8": recall,
            "reciprocal_rank": reciprocal_rank,
            "required_fact_recall": fact_recall,
            "answer_correctness": 1.0 if answer_correct else 0.0,
            "citation_precision": citation_precision,
            "structured_output_acceptance": 1.0 if structured else 0.0,
            "tool_argument_validity": 1.0 if not invalid_tool_arguments else 0.0,
            "endpoint_success": 0.0 if output.errors and not structured else 1.0,
            "graph_relation_recall": graph_recall,
            "latency_ms": elapsed_ms,
        },
        "hard_failures": hard_failures,
        "output": output.as_dict(),
    }


def aggregate_scores(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    if not case_results:
        return {"hard_gate_pass": False, "quality_pass": False, "reason": "NO_CASES"}
    expected_fact_count = sum(len(item.get("expected_facts", {})) for item in case_results)
    matched_fact_count = sum(len(item.get("matched_facts", {})) for item in case_results)
    graph_cases = [item for item in case_results if item.get("expected_relations")]
    answer_cases = [item for item in case_results if item.get("answer_scored")]
    means = {
        "recall_at_8": statistics.fmean(item["metrics"]["recall_at_8"] for item in case_results),
        "mrr": statistics.fmean(item["metrics"]["reciprocal_rank"] for item in case_results),
        "required_fact_recall": matched_fact_count / expected_fact_count if expected_fact_count else 1.0,
        "answer_correctness": statistics.fmean(
            item["metrics"]["answer_correctness"] for item in answer_cases
        ) if answer_cases else 1.0,
        "citation_precision": statistics.fmean(item["metrics"]["citation_precision"] for item in case_results),
        "structured_output_acceptance": statistics.fmean(item["metrics"]["structured_output_acceptance"] for item in case_results),
        "tool_argument_validity": statistics.fmean(item["metrics"]["tool_argument_validity"] for item in case_results),
        "endpoint_success": statistics.fmean(item["metrics"]["endpoint_success"] for item in case_results),
        "graph_relation_recall": statistics.fmean(
            item["metrics"]["graph_relation_recall"] for item in graph_cases
        ) if graph_cases else 1.0,
    }
    latencies = [item["metrics"]["latency_ms"] for item in case_results]
    hard_failures = sorted({failure for item in case_results for failure in item["hard_failures"]})
    quality_failures = [
        metric for metric, threshold in QUALITY_THRESHOLDS.items() if means[metric] < threshold
    ]
    quality_score = statistics.fmean(
        [
            means["recall_at_8"],
            means["mrr"],
            means["required_fact_recall"],
            means["answer_correctness"],
            means["citation_precision"],
            means["graph_relation_recall"],
        ]
    )
    return {
        **means,
        "quality_score": quality_score,
        "latency_p50_ms": percentile(latencies, 0.50),
        "latency_p95_ms": percentile(latencies, 0.95),
        "hard_failures": hard_failures,
        "quality_failures": quality_failures,
        "hard_gate_pass": not hard_failures,
        "quality_pass": not hard_failures and not quality_failures,
        "production_ready": False,
    }


def evaluate_variant(
    documents: list[Document],
    cases: list[EvaluationCase],
    variant: PipelineVariant,
    client: OllamaClient | None = None,
    reranker: RerankerClient | None = None,
) -> dict[str, Any]:
    cpu_start = time.process_time()
    endpoint_start = {
        "requests": (client.request_count if client else 0)
        + (reranker.request_count if reranker else 0),
        "request_bytes": (client.request_bytes if client else 0)
        + (reranker.request_bytes if reranker else 0),
        "response_bytes": (client.response_bytes if client else 0)
        + (reranker.response_bytes if reranker else 0),
    }
    with tempfile.TemporaryDirectory(prefix="tb-ai-lab-eval-") as temporary:
        database = Path(temporary) / "index.sqlite"
        with Index(database) as index:
            pipeline = Pipeline(index, variant, client, reranker)
            ingest_start = time.perf_counter()
            ingest_counts = pipeline.ingest(documents)
            ingest_ms = (time.perf_counter() - ingest_start) * 1000
            case_results = []
            for case in cases:
                start = time.perf_counter()
                try:
                    output = pipeline.query(case.query, case.scope, case.allowed_tools)
                    case_results.append(score_case(case, output, (time.perf_counter() - start) * 1000))
                except Exception as error:
                    elapsed = (time.perf_counter() - start) * 1000
                    error_text = f"{type(error).__name__}: {error}"
                    runtime_failure = next(
                        (
                            marker
                            for marker in (
                                "VRAM_CAP_EXCEEDED",
                                "PARTIAL_GPU_RESIDENCY",
                                "VRAM_MEASUREMENT_UNAVAILABLE",
                                "CONTEXT_INCOMPATIBLE",
                            )
                            if marker in error_text
                        ),
                        "PIPELINE_ERROR",
                    )
                    case_results.append(
                        {
                            "case_id": case.id,
                            "query": case.query,
                            "scope": case.scope.as_dict(),
                            "expected_document_ids": list(case.expected_document_ids),
                            "expected_facts": dict(case.expected_facts),
                            "expected_answer_values": list(case.expected_answer_values),
                            "expected_relations": [list(item) for item in case.expected_relations],
                            "matched_facts": {},
                            "fact_id_mismatches": {},
                            "answer_scored": bool(case.expected_answer_values)
                            or case.require_abstention,
                            "matched_relations": [],
                            "hard_failures": [runtime_failure],
                            "metrics": {
                                "recall_at_8": 0.0,
                                "reciprocal_rank": 0.0,
                                "required_fact_recall": 0.0,
                                "answer_correctness": 0.0,
                                "citation_precision": 0.0,
                                "structured_output_acceptance": 0.0,
                                "tool_argument_validity": 0.0,
                                "endpoint_success": 0.0,
                                "graph_relation_recall": 0.0,
                                "latency_ms": elapsed,
                            },
                            "error": error_text,
                        }
                    )
            database_bytes = database.stat().st_size
    generation_details = [
        trace["details"]
        for case in case_results
        for trace in case.get("output", {}).get("traces", [])
        if trace["stage"] == "generate"
    ]
    endpoint_end = {
        "requests": (client.request_count if client else 0)
        + (reranker.request_count if reranker else 0),
        "request_bytes": (client.request_bytes if client else 0)
        + (reranker.request_bytes if reranker else 0),
        "response_bytes": (client.response_bytes if client else 0)
        + (reranker.response_bytes if reranker else 0),
    }
    return {
        "schema_version": 1,
        "variant": variant.as_dict(),
        "ingest": {**ingest_counts, "wall_ms": ingest_ms},
        "performance": {
            "cpu_ms": (time.process_time() - cpu_start) * 1000,
            "process_lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "sqlite_bytes": database_bytes,
            "requests": endpoint_end["requests"] - endpoint_start["requests"],
            "network_request_bytes": endpoint_end["request_bytes"] - endpoint_start["request_bytes"],
            "network_response_bytes": endpoint_end["response_bytes"] - endpoint_start["response_bytes"],
            "generation_requests": sum(item.get("requests", 0) for item in generation_details),
            "prompt_tokens": sum(item.get("prompt_eval_count", 0) for item in generation_details),
            "completion_tokens": sum(item.get("eval_count", 0) for item in generation_details),
        },
        "aggregate": aggregate_scores(case_results),
        "cases": case_results,
    }


def pareto_frontier(results: list[dict[str, Any]]) -> list[str]:
    candidates = [item for item in results if item.get("aggregate", {}).get("hard_gate_pass")]
    frontier: list[str] = []
    for candidate in candidates:
        quality = candidate["aggregate"]["quality_score"]
        latency = candidate["aggregate"]["latency_p50_ms"]
        dominated = any(
            other is not candidate
            and other["aggregate"]["quality_score"] >= quality
            and other["aggregate"]["latency_p50_ms"] <= latency
            and (
                other["aggregate"]["quality_score"] > quality
                or other["aggregate"]["latency_p50_ms"] < latency
            )
            for other in candidates
        )
        if not dominated:
            frontier.append(candidate["variant"]["id"])
    return sorted(frontier)


def summarize_matrix(results: list[dict[str, Any]]) -> dict[str, Any]:
    passing = [item for item in results if item.get("aggregate", {}).get("quality_pass")]
    hard_passing = [item for item in results if item.get("aggregate", {}).get("hard_gate_pass")]
    max_quality = max(hard_passing, key=lambda item: item["aggregate"]["quality_score"], default=None)
    fastest = min(passing, key=lambda item: item["aggregate"]["latency_p50_ms"], default=None)
    vram_candidates = [
        item
        for item in passing
        if item.get("residency", {}).get("configuration_ollama_vram_bytes")
        is not None
    ]
    vram_efficient = min(
        vram_candidates,
        key=lambda item: item["residency"]["configuration_ollama_vram_bytes"],
        default=None,
    )
    return {
        "result_count": len(results),
        "hard_gate_passing": len(hard_passing),
        "quality_passing": len(passing),
        "max_quality": max_quality["variant"]["id"] if max_quality else None,
        "fastest_passing": fastest["variant"]["id"] if fastest else None,
        "vram_efficient": vram_efficient["variant"]["id"] if vram_efficient else None,
        "pareto_frontier": pareto_frontier(results),
        "production_ready": False,
    }


def combine_repeats(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault(result["variant"]["id"], []).append(result)
    combined = []
    for variant_id in sorted(grouped):
        runs = sorted(grouped[variant_id], key=lambda item: item.get("repeat", 0))
        case_results = [case for run in runs for case in run.get("cases", [])]
        aggregate = aggregate_scores(case_results)
        for metric in QUALITY_THRESHOLDS:
            aggregate[metric] = statistics.fmean(
                float(run.get("aggregate", {}).get(metric, 0.0)) for run in runs
            )
        aggregate["quality_score"] = statistics.fmean(
            [
                aggregate["recall_at_8"],
                aggregate["mrr"],
                aggregate["required_fact_recall"],
                aggregate["answer_correctness"],
                aggregate["citation_precision"],
                aggregate["graph_relation_recall"],
            ]
        )
        aggregate["hard_failures"] = sorted(
            {
                failure
                for run in runs
                for failure in run.get("aggregate", {}).get("hard_failures", [])
            }
        )
        aggregate["quality_failures"] = [
            metric
            for metric, threshold in QUALITY_THRESHOLDS.items()
            if aggregate[metric] < threshold
        ]
        aggregate["hard_gate_pass"] = not aggregate["hard_failures"]
        aggregate["quality_pass"] = (
            aggregate["hard_gate_pass"] and not aggregate["quality_failures"]
        )
        aggregate["production_ready"] = False
        repeated_metrics = (
            "quality_score",
            "recall_at_8",
            "mrr",
            "required_fact_recall",
            "answer_correctness",
            "citation_precision",
            "graph_relation_recall",
            "latency_p50_ms",
            "latency_p95_ms",
        )
        aggregate["repeat_count"] = len(runs)
        aggregate["repeat_variance"] = {
            metric: (
                statistics.pvariance(
                    float(run["aggregate"].get(metric, 0.0)) for run in runs
                )
                if len(runs) > 1
                else 0.0
            )
            for metric in repeated_metrics
        }
        record = {
            **runs[0],
            "phase": "full-combined",
            "aggregate": aggregate,
            "runs": runs,
        }
        combined.append(record)
    return combined
