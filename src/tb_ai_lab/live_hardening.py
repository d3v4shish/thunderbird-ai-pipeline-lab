# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0.

"""Live embedding, cross-encoder, and answer-parameter evaluations."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import statistics
import time
from typing import Any

from .contracts import Document, EvaluationCase, Evidence, content_digest
from .email_rag import EmailRagError, answer_messages, validate_grounded_answer
from .evaluation import percentile
from .models import ModelError, OllamaClient, RerankerClient, nvidia_total_used_bytes
from .reporting import checkpoint
from .scale_evaluation import (
    _extract_scale_facts,
    canonical_thread_range,
    scaled_thread_fixture,
)
from .storage import Index, deterministic_rerank
from .text import chunk_document, cosine


def _embed_batched(
    client: OllamaClient,
    model: str,
    texts: list[str],
    batch_size: int,
) -> tuple[list[list[float]], float]:
    if not 1 <= batch_size <= 128:
        raise ValueError("batch_size must be between 1 and 128")
    started = time.perf_counter()
    vectors = []
    for start in range(0, len(texts), batch_size):
        vectors.extend(client.embed(model, texts[start : start + batch_size]))
    return vectors, (time.perf_counter() - started) * 1000


def _vector_comparison(
    baseline: list[list[float]], candidate: list[list[float]]
) -> dict[str, Any]:
    if len(baseline) != len(candidate) or any(
        len(left) != len(right)
        for left, right in zip(baseline, candidate, strict=True)
    ):
        return {
            "shape_equal": False,
            "exact_equal": False,
            "max_absolute_component_delta": None,
            "mean_absolute_component_delta": None,
            "mean_cosine_similarity": None,
            "minimum_cosine_similarity": None,
        }
    deltas = [
        abs(left_component - right_component)
        for left, right in zip(baseline, candidate, strict=True)
        for left_component, right_component in zip(left, right, strict=True)
    ]
    similarities = [
        cosine(left, right)
        for left, right in zip(baseline, candidate, strict=True)
    ]
    return {
        "shape_equal": True,
        "exact_equal": baseline == candidate,
        "max_absolute_component_delta": max(deltas, default=0.0),
        "mean_absolute_component_delta": statistics.fmean(deltas) if deltas else 0.0,
        "mean_cosine_similarity": statistics.fmean(similarities)
        if similarities
        else 1.0,
        "minimum_cosine_similarity": min(similarities, default=1.0),
    }


def _dense_rankings(
    documents: list[Document],
    document_vectors: list[list[float]],
    cases: list[EvaluationCase],
    query_vectors: list[list[float]],
    limit: int = 8,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, float]]:
    rankings = {}
    recalls = []
    fact_hits = 0
    fact_total = 0
    for case, query_vector in zip(cases, query_vectors, strict=True):
        scored = [
            (cosine(query_vector, vector), document)
            for document, vector in zip(documents, document_vectors, strict=True)
            if document.tenant == case.scope.tenant
            and document.collection == case.scope.collection
        ]
        scored.sort(key=lambda item: (-item[0], item[1].id))
        top = scored[:limit]
        rankings[case.id] = [
            {"document_id": document.id, "score": score}
            for score, document in top
        ]
        if case.expected_document_ids:
            expected = set(case.expected_document_ids)
            recalls.append(
                len(expected & {document.id for _, document in top}) / len(expected)
            )
        for fact_id, value in case.expected_facts.items():
            fact_total += 1
            fact_hits += int(
                any(
                    f"[fact {fact_id}]".casefold() in document.text.casefold()
                    and value.casefold() in document.text.casefold()
                    for _, document in top
                )
            )
    return rankings, {
        "mean_document_recall_at_8": statistics.fmean(recalls) if recalls else 1.0,
        "fact_recall_at_8": fact_hits / fact_total if fact_total else 1.0,
    }


def _ranking_comparison(
    baseline: dict[str, list[dict[str, Any]]],
    candidate: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    overlaps = []
    identical = 0
    score_deltas = []
    for case_id, baseline_items in baseline.items():
        candidate_items = candidate[case_id]
        baseline_ids = [item["document_id"] for item in baseline_items]
        candidate_ids = [item["document_id"] for item in candidate_items]
        overlaps.append(len(set(baseline_ids) & set(candidate_ids)) / len(baseline_ids))
        identical += int(baseline_ids == candidate_ids)
        candidate_scores = {
            item["document_id"]: item["score"] for item in candidate_items
        }
        score_deltas.extend(
            abs(item["score"] - candidate_scores[item["document_id"]])
            for item in baseline_items
            if item["document_id"] in candidate_scores
        )
    return {
        "mean_overlap_at_8": statistics.fmean(overlaps) if overlaps else 1.0,
        "identical_ranking_rate": identical / len(baseline) if baseline else 1.0,
        "maximum_shared_score_delta": max(score_deltas, default=0.0),
    }


def evaluate_embedding_drift(
    client: OllamaClient,
    model: str,
    model_digest: str,
    documents: list[Document],
    cases: list[EvaluationCase],
    repeats: int = 3,
    batch_size: int = 24,
) -> dict[str, Any]:
    if not 3 <= repeats <= 10:
        raise ValueError("embedding drift evaluation requires 3 to 10 repeats")
    chunks = [
        chunk_document(document, "structure-aware", 1200, 0, 16)[0]
        for document in documents
    ]
    document_texts = [item.contextual_text for item in chunks]
    queries = [item.query for item in cases]
    records = []
    retained_vectors = []
    retained_query_vectors = []
    for repeat in range(1, repeats + 1):
        client.unload(model)
        document_vectors, document_ms = _embed_batched(
            client, model, document_texts, batch_size
        )
        same_vectors, same_ms = _embed_batched(
            client, model, document_texts, batch_size
        )
        steady_vectors, steady_ms = _embed_batched(
            client, model, document_texts, batch_size
        )
        sample_count = min(8, len(document_texts))
        singleton_vectors, singleton_ms = _embed_batched(
            client, model, document_texts[:sample_count], 1
        )
        reversed_vectors, reversed_ms = _embed_batched(
            client, model, list(reversed(document_texts[:sample_count])), sample_count
        )
        reversed_vectors.reverse()
        duplicate_vectors, duplicate_ms = _embed_batched(
            client, model, [document_texts[0], document_texts[0]], 2
        )
        singleton_repeat_vectors, singleton_repeat_ms = _embed_batched(
            client, model, [document_texts[0]], 1
        )
        singleton_repeat_again, singleton_repeat_again_ms = _embed_batched(
            client, model, [document_texts[0]], 1
        )
        query_vectors, query_ms = _embed_batched(client, model, queries, batch_size)
        rankings, quality = _dense_rankings(
            documents, document_vectors, cases, query_vectors
        )
        records.append(
            {
                "repeat": repeat,
                "document_vector_digest": content_digest(document_vectors),
                "query_vector_digest": content_digest(query_vectors),
                "same_load_repeat": _vector_comparison(document_vectors, same_vectors),
                "steady_state_repeat": _vector_comparison(
                    same_vectors, steady_vectors
                ),
                "batch_size_one_sample": _vector_comparison(
                    document_vectors[:sample_count], singleton_vectors
                ),
                "reversed_order_sample": _vector_comparison(
                    document_vectors[:sample_count], reversed_vectors
                ),
                "duplicate_in_one_request": _vector_comparison(
                    duplicate_vectors[:1], duplicate_vectors[1:]
                ),
                "repeated_singleton_request": _vector_comparison(
                    singleton_repeat_vectors, singleton_repeat_again
                ),
                "dimensions": len(document_vectors[0]) if document_vectors else 0,
                "document_count": len(document_vectors),
                "quality": quality,
                "rankings": rankings,
                "timing_ms": {
                    "documents": document_ms,
                    "same_load_repeat": same_ms,
                    "steady_state_repeat": steady_ms,
                    "singleton_sample": singleton_ms,
                    "reversed_sample": reversed_ms,
                    "duplicate_pair": duplicate_ms,
                    "singleton_repeat": singleton_repeat_ms
                    + singleton_repeat_again_ms,
                    "queries": query_ms,
                },
                "runtime": {
                    "active_ollama_vram_bytes": client.peak_ollama_vram_bytes,
                    "active_whole_gpu_bytes": client.peak_gpu_used_bytes,
                },
            }
        )
        retained_vectors.append(document_vectors)
        retained_query_vectors.append(query_vectors)
    baseline_vectors = retained_vectors[0]
    baseline_query_vectors = retained_query_vectors[0]
    cross_load = []
    for index, record in enumerate(records):
        cross_load.append(
            {
                "repeat": record["repeat"],
                "documents": _vector_comparison(baseline_vectors, retained_vectors[index]),
                "queries": _vector_comparison(
                    baseline_query_vectors, retained_query_vectors[index]
                ),
                "rankings": _ranking_comparison(records[0]["rankings"], record["rankings"]),
                "quality_delta": {
                    key: record["quality"][key] - records[0]["quality"][key]
                    for key in records[0]["quality"]
                },
            }
        )
    within_load_exact = all(
        record["same_load_repeat"]["exact_equal"] for record in records
    )
    steady_state_exact = all(
        record["steady_state_repeat"]["exact_equal"] for record in records
    )
    batch_invariant = all(
        record["batch_size_one_sample"]["exact_equal"]
        and record["reversed_order_sample"]["exact_equal"]
        for record in records
    )
    batch_order_isolatable = within_load_exact
    cross_load_exact = all(
        item["documents"]["exact_equal"] and item["queries"]["exact_equal"]
        for item in cross_load
    )
    rank_tolerance_pass = all(
        item["rankings"]["mean_overlap_at_8"] >= 0.95
        and abs(item["quality_delta"]["fact_recall_at_8"]) <= 0.01
        and abs(item["quality_delta"]["mean_document_recall_at_8"]) <= 0.01
        for item in cross_load
    )
    return {
        "schema_version": 1,
        "title": "Endpoint Embedding Drift Investigation",
        "production_ready": False,
        "model": {"name": model, "digest": model_digest},
        "batch_size": batch_size,
        "repeats": records,
        "cross_load_comparisons": cross_load,
        "within_load_exact": within_load_exact,
        "steady_state_exact": steady_state_exact,
        "batch_and_order_invariant": batch_invariant,
        "batch_order_isolatable": batch_order_isolatable,
        "duplicate_in_request_exact": all(
            item["duplicate_in_one_request"]["exact_equal"] for item in records
        ),
        "repeated_singleton_exact": all(
            item["repeated_singleton_request"]["exact_equal"] for item in records
        ),
        "cross_load_exact": cross_load_exact,
        "rank_quality_tolerance_pass": rank_tolerance_pass,
        "decision": (
            "Persist document embeddings and permit this endpoint only if steady-state "
            "calls are exact and cross-load ranking remains at least 95% overlapping "
            "with no more than 1% aggregate quality drift; byte-level nondeterminism "
            "remains separately visible."
        ),
    }


def _fact_support(evidence: list[Evidence], fact_id: str, value: str) -> bool:
    return any(
        f"[fact {fact_id}]".casefold() in item.text.casefold()
        and value.casefold() in item.text.casefold()
        for item in evidence
    )


def _reranker_case(
    case: EvaluationCase,
    candidates: list[Evidence],
    ranked: list[Evidence],
    index: Index,
    elapsed_ms: float,
) -> dict[str, Any]:
    top = ranked[:8]
    expected = set(case.expected_document_ids)
    fact_ranks = {
        fact_id: next(
            (
                rank
                for rank, item in enumerate(top, 1)
                if _fact_support([item], fact_id, value)
            ),
            None,
        )
        for fact_id, value in case.expected_facts.items()
    }
    candidate_ids = {item.chunk_id for item in candidates}
    return {
        "case_id": case.id,
        "query": case.query,
        "candidate_count": len(candidates),
        "candidate_document_recall": len(
            expected & {item.document_id for item in candidates}
        )
        / len(expected)
        if expected
        else None,
        "metrics": {
            "document_recall_at_8": len(expected & {item.document_id for item in top})
            / len(expected)
            if expected
            else None,
            "fact_recall_at_8": sum(rank is not None for rank in fact_ranks.values())
            / len(fact_ranks)
            if fact_ranks
            else None,
            "fact_mrr": sum(1.0 / rank for rank in fact_ranks.values() if rank)
            / len(fact_ranks)
            if fact_ranks
            else None,
            "scope_integrity": float(
                all(
                    item.tenant == case.scope.tenant
                    and item.collection == case.scope.collection
                    for item in top
                )
            ),
            "source_span_validity": float(
                all(index.verify_evidence(item, case.scope) for item in top)
            ),
            "candidate_set_preserved": float(
                len(ranked) == len(candidates)
                and {item.chunk_id for item in ranked} == candidate_ids
            ),
            "latency_ms": elapsed_ms,
        },
        "fact_ranks": fact_ranks,
        "evidence": [item.as_dict() for item in top],
    }


def _aggregate_reranker(method: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    facts = [item for item in records if item["metrics"]["fact_recall_at_8"] is not None]
    documents = [
        item for item in records if item["metrics"]["document_recall_at_8"] is not None
    ]
    return {
        "method": method,
        "aggregate": {
            "document_recall_at_8": statistics.fmean(
                item["metrics"]["document_recall_at_8"] for item in documents
            )
            if documents
            else 1.0,
            "fact_recall_at_8": statistics.fmean(
                item["metrics"]["fact_recall_at_8"] for item in facts
            )
            if facts
            else 1.0,
            "fact_mrr": statistics.fmean(
                item["metrics"]["fact_mrr"] for item in facts
            )
            if facts
            else 1.0,
            "scope_integrity": min(
                item["metrics"]["scope_integrity"] for item in records
            ),
            "source_span_validity": min(
                item["metrics"]["source_span_validity"] for item in records
            ),
            "candidate_set_preserved": min(
                item["metrics"]["candidate_set_preserved"] for item in records
            ),
            "latency_p50_ms": percentile(
                [item["metrics"]["latency_ms"] for item in records], 0.5
            ),
            "latency_p95_ms": percentile(
                [item["metrics"]["latency_ms"] for item in records], 0.95
            ),
        },
        "cases": records,
    }


def evaluate_cross_encoder_repeat(
    ollama: OllamaClient,
    reranker: RerankerClient,
    embedding_model: str,
    documents: list[Document],
    cases: list[EvaluationCase],
    repeat: int,
    candidate_count: int = 32,
) -> dict[str, Any]:
    if not 8 <= candidate_count <= 100:
        raise ValueError("candidate_count must be between 8 and 100")
    chunks = [
        chunk_document(document, "structure-aware", 1200, 0, 16)[0]
        for document in documents
    ]
    vectors, embedding_ms = _embed_batched(
        ollama,
        embedding_model,
        [item.contextual_text for item in chunks],
        24,
    )
    with Index() as index:
        for document, chunk, vector in zip(documents, chunks, vectors, strict=True):
            index.add_document(
                document, [chunk], {chunk.id: vector}, build_vector_buckets=False
            )
        lanes: dict[str, list[dict[str, Any]]] = {
            "none": [],
            "deterministic": [],
            "embedding": [],
            "cross-encoder": [],
        }
        query_vectors, query_embedding_ms = _embed_batched(
            ollama, embedding_model, [item.query for item in cases], 24
        )
        for case, query_vector in zip(cases, query_vectors, strict=True):
            candidates = index.hybrid_search(
                case.query,
                case.scope,
                candidate_count,
                query_vector=query_vector,
                candidate_mode="full-scan",
            )
            operations = {
                "none": lambda: list(candidates),
                "deterministic": lambda: deterministic_rerank(case.query, candidates),
                "embedding": lambda: index.embedding_rerank(query_vector, candidates),
            }
            for method, operation in operations.items():
                started = time.perf_counter()
                ranked = operation()
                elapsed_ms = (time.perf_counter() - started) * 1000
                lanes[method].append(
                    _reranker_case(case, candidates, ranked, index, elapsed_ms)
                )
            started = time.perf_counter()
            scores = reranker.rerank(case.query, [item.text for item in candidates])
            ranked = [
                Evidence(
                    chunk_id=candidates[position].chunk_id,
                    document_id=candidates[position].document_id,
                    tenant=candidates[position].tenant,
                    collection=candidates[position].collection,
                    text=candidates[position].text,
                    start=candidates[position].start,
                    end=candidates[position].end,
                    score=score,
                    channels=candidates[position].channels + ("cross-encoder",),
                    section=candidates[position].section,
                )
                for position, score in scores
            ]
            elapsed_ms = (time.perf_counter() - started) * 1000
            lanes["cross-encoder"].append(
                _reranker_case(case, candidates, ranked, index, elapsed_ms)
            )
    return {
        "repeat": repeat,
        "candidate_count": candidate_count,
        "document_embedding_ms": embedding_ms,
        "query_embedding_ms": query_embedding_ms,
        "document_vector_digest": content_digest(vectors),
        "query_vector_digest": content_digest(query_vectors),
        "lanes": [
            _aggregate_reranker(method, records) for method, records in lanes.items()
        ],
        "runtime": {
            "ollama_peak_vram_bytes": ollama.peak_ollama_vram_bytes,
            "whole_gpu_bytes": nvidia_total_used_bytes(),
            "reranker_requests": reranker.request_count,
            "reranker_request_bytes": reranker.request_bytes,
            "reranker_response_bytes": reranker.response_bytes,
        },
    }


def combine_cross_encoder_repeats(
    repeats: list[dict[str, Any]],
    reranker_model: str,
    reranker_info: dict[str, Any],
) -> dict[str, Any]:
    if len(repeats) < 3:
        raise ValueError("cross-encoder evaluation requires at least three repeats")
    methods = [item["method"] for item in repeats[0]["lanes"]]
    stability = []
    for method in methods:
        lanes = [
            next(item for item in repeat["lanes"] if item["method"] == method)
            for repeat in repeats
        ]
        stability.append(
            {
                "method": method,
                **{
                    key: [item["aggregate"][key] for item in lanes]
                    for key in lanes[0]["aggregate"]
                },
            }
        )
    control = next(item for item in stability if item["method"] == "none")
    cross = next(item for item in stability if item["method"] == "cross-encoder")
    no_regression = all(
        cross[key][repeat] >= control[key][repeat]
        for key in ("document_recall_at_8", "fact_recall_at_8", "fact_mrr")
        for repeat in range(len(repeats))
    )
    improves = any(
        cross[key][repeat] > control[key][repeat]
        for key in ("document_recall_at_8", "fact_recall_at_8", "fact_mrr")
        for repeat in range(len(repeats))
    )
    safety = all(
        all(
            lane["aggregate"]["scope_integrity"] == 1.0
            and lane["aggregate"]["source_span_validity"] == 1.0
            and lane["aggregate"]["candidate_set_preserved"] == 1.0
            for lane in repeat["lanes"]
        )
        for repeat in repeats
    )
    return {
        "schema_version": 1,
        "title": "True Cross-Encoder Reranking Evaluation",
        "production_ready": False,
        "reranker": {"model": reranker_model, "server": reranker_info},
        "repeat_count": len(repeats),
        "repeats": repeats,
        "stability": stability,
        "safety_pass": safety,
        "candidate_decision": {
            "no_quality_regression_in_all_repeats": no_regression,
            "improves_quality_in_at_least_one_repeat": improves,
            "broader_evaluation_candidate": safety and no_regression and improves,
        },
        "decision": (
            "Promote only if the joint query-passage scorer improves the unchanged "
            "candidate set in all safety-valid repeats without recall regression."
        ),
    }


@dataclass(frozen=True, slots=True)
class AnswerParameter:
    factor: str
    value: int | float | str
    context_window: int
    max_output_tokens: int
    evidence_budget: int
    temperature: float

    @property
    def key(self) -> tuple[int, int, int, float]:
        return (
            self.context_window,
            self.max_output_tokens,
            self.evidence_budget,
            self.temperature,
        )


def answer_parameter_matrix() -> list[AnswerParameter]:
    baseline = AnswerParameter("baseline", "current-candidate", 16_384, 4096, 0, 0.0)
    parameters = [baseline]
    parameters.extend(
        AnswerParameter("context_window", value, value, 4096, 0, 0.0)
        for value in (4096, 8192, 32_768)
    )
    parameters.extend(
        AnswerParameter("max_output_tokens", value, 16_384, value, 0, 0.0)
        for value in (256, 512, 1024, 2048)
    )
    parameters.extend(
        AnswerParameter("evidence_budget", value, 16_384, 4096, value, 0.0)
        for value in (4096, 8192, 16_384)
    )
    parameters.append(AnswerParameter("temperature", 0.2, 16_384, 4096, 0, 0.2))
    return parameters


def answer_finalist_matrix() -> list[AnswerParameter]:
    return [
        AnswerParameter(
            "combined_context_output",
            f"{context_window}/2048",
            context_window,
            2048,
            0,
            0.0,
        )
        for context_window in (6144, 7168, 8192)
    ]


def _budget_evidence(evidence: list[Evidence], budget: int) -> list[Evidence]:
    if budget == 0:
        return list(evidence)
    result = []
    remaining = budget
    for item in evidence:
        if remaining <= 0:
            break
        text = item.text[:remaining]
        if not text:
            break
        result.append(
            Evidence(
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                tenant=item.tenant,
                collection=item.collection,
                text=text,
                start=item.start,
                end=item.start + len(text),
                score=item.score,
                channels=item.channels,
                section=item.section,
            )
        )
        remaining -= len(text)
    return result


def evaluate_answer_parameters(
    client: OllamaClient,
    model: str,
    model_digest: str,
    repeats: int = 3,
) -> dict[str, Any]:
    if not 3 <= repeats <= 10:
        raise ValueError("answer parameter evaluation requires 3 to 10 repeats")
    documents, case = scaled_thread_fixture(50)
    evidence = canonical_thread_range(documents, case)[:32]
    page_expected = _extract_scale_facts(evidence)
    one_factor_parameters = answer_parameter_matrix()
    finalist_parameters = answer_finalist_matrix()
    parameters = one_factor_parameters + finalist_parameters
    records = []
    for repeat in range(1, repeats + 1):
        cache: dict[tuple[int, int, int, float], dict[str, Any]] = {}
        for parameter in parameters:
            offered = _budget_evidence(evidence, parameter.evidence_budget)
            messages = answer_messages(case.query, offered)
            if parameter.key in cache:
                result = {**cache[parameter.key], "reused": True}
            else:
                started = time.perf_counter()
                try:
                    response = client.chat(
                        model,
                        messages,
                        context_window=parameter.context_window,
                        max_output_tokens=parameter.max_output_tokens,
                        temperature=parameter.temperature,
                    )
                    wall_ms = (time.perf_counter() - started) * 1000
                    raw = str(response["message"].get("content", ""))
                    validated = validate_grounded_answer(raw, offered, case.query)
                    error = None
                except (ModelError, EmailRagError, ValueError, KeyError) as failure:
                    wall_ms = (time.perf_counter() - started) * 1000
                    response = {}
                    raw = ""
                    validated = {
                        "facts": {},
                        "citations": [],
                        "errors": ["GENERATION_FAILURE"],
                        "abstained": False,
                    }
                    error = f"{type(failure).__name__}: {failure}"
                expected = page_expected
                returned = validated.get("facts", {})
                matched = {
                    key: value
                    for key, value in expected.items()
                    if returned.get(key) == value
                }
                result = {
                    "reused": False,
                    "wall_ms": wall_ms,
                    "raw_output": raw,
                    "validation": validated,
                    "error": error,
                    "prompt_tokens": int(response.get("prompt_eval_count", 0) or 0),
                    "output_tokens": int(response.get("eval_count", 0) or 0),
                    "model_total_ms": float(response.get("total_duration", 0) or 0)
                    / 1_000_000,
                    "matched_fact_count": len(matched),
                    "fact_recall": len(matched) / len(expected),
                    "structured_valid": not validated.get("errors"),
                    "offered_messages": len(offered),
                    "offered_characters": sum(len(item.text) for item in offered),
                    "missing_fact_ids": sorted(set(expected) - set(matched)),
                }
                cache[parameter.key] = result
            records.append(
                {
                    "repeat": repeat,
                    "factor": parameter.factor,
                    "value": parameter.value,
                    "settings": {
                        "context_window": parameter.context_window,
                        "max_output_tokens": parameter.max_output_tokens,
                        "evidence_budget": parameter.evidence_budget,
                        "temperature": parameter.temperature,
                    },
                    **result,
                }
            )
    stability = []
    for parameter in parameters:
        matching = [
            item
            for item in records
            if item["factor"] == parameter.factor and item["value"] == parameter.value
        ]
        stability.append(
            {
                "factor": parameter.factor,
                "value": parameter.value,
                "settings": matching[0]["settings"],
                "fact_recall": [item["fact_recall"] for item in matching],
                "structured_valid": [item["structured_valid"] for item in matching],
                "wall_ms": [item["wall_ms"] for item in matching],
                "prompt_tokens": [item["prompt_tokens"] for item in matching],
                "output_tokens": [item["output_tokens"] for item in matching],
            }
        )
    recommendations = {}
    for factor in ("context_window", "max_output_tokens", "evidence_budget", "temperature"):
        candidates = [item for item in stability if item["factor"] in {factor, "baseline"}]
        passing = [
            item
            for item in candidates
            if min(item["fact_recall"]) == 1.0 and all(item["structured_valid"])
        ]
        if not passing:
            recommendations[factor] = {"status": "no-passing-setting"}
            continue
        winner = min(
            passing,
            key=lambda item: (
                item["settings"].get(factor, 0),
                statistics.fmean(item["wall_ms"]),
            ),
        )
        recommendations[factor] = {
            "status": "keep-or-change",
            "value": winner["settings"].get(factor),
            "source_lane": {"factor": winner["factor"], "value": winner["value"]},
        }
    finalist_results = [
        item for item in stability if item["factor"] == "combined_context_output"
    ]
    passing_finalists = [
        item
        for item in finalist_results
        if min(item["fact_recall"]) == 1.0 and all(item["structured_valid"])
    ]
    recommendations["combined_context_output"] = (
        {
            "status": "keep-or-change",
            "context_window": min(
                passing_finalists,
                key=lambda item: item["settings"]["context_window"],
            )["settings"]["context_window"],
            "max_output_tokens": 2048,
        }
        if passing_finalists
        else {"status": "no-passing-setting"}
    )
    return {
        "schema_version": 1,
        "title": "Live Context and Output Parameter Evaluation",
        "production_ready": False,
        "model": {"name": model, "digest": model_digest},
        "fixture": {
            "thread_size": 50,
            "map_page_messages": len(evidence),
            "map_page_expected_facts": len(page_expected),
            "full_thread_evaluated_by": "scale-hardening-evaluate hierarchical-ledger",
        },
        "records": records,
        "stability": stability,
        "recommendations": recommendations,
        "runtime": {
            "peak_ollama_vram_bytes": client.peak_ollama_vram_bytes,
            "peak_whole_gpu_bytes": client.peak_gpu_used_bytes,
            "vram_cap_gib": client.vram_cap_gib,
        },
        "decision": (
            "Use one-factor lanes to identify safe reductions, then select the smallest "
            "three-repeat combined context/output finalist that returns all 32 map-page "
            "facts with valid structure. Full-thread completeness is evaluated by "
            "the paged hierarchical lane, never by expanding this prompt."
        ),
    }


def markdown_embedding_drift(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['title']}",
        "",
        f"Model: `{report['model']['name']}` / `{report['model']['digest']}`.",
        "",
        "| Repeat | Document digest | Query digest | First/second exact | Second/third exact | Batch/order exact | Fact recall@8 |",
        "|---:|---|---|---|---|---|---:|",
    ]
    for item in report["repeats"]:
        lines.append(
            f"| {item['repeat']} | `{item['document_vector_digest']}` | "
            f"`{item['query_vector_digest']}` | {item['same_load_repeat']['exact_equal']} | "
            f"{item['steady_state_repeat']['exact_equal']} | "
            f"{item['batch_size_one_sample']['exact_equal'] and item['reversed_order_sample']['exact_equal']} | "
            f"{item['quality']['fact_recall_at_8']:.3f} |"
        )
    lines.extend(
        [
            "",
            f"Cross-load exact: {report['cross_load_exact']}.",
            f"Steady-state exact: {report['steady_state_exact']}.",
            f"Batch/order effect isolatable: {report['batch_order_isolatable']}.",
            f"Rank/quality tolerance pass (95% top-8 overlap, 1% quality): {report['rank_quality_tolerance_pass']}.",
            "",
            report["decision"],
            "",
        ]
    )
    return "\n".join(lines)


def markdown_cross_encoder(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['title']}",
        "",
        f"Reranker: `{report['reranker']['model']}`. Repeats: {report['repeat_count']}.",
        "",
        "| Method | Fact recall@8 | Fact MRR | p50 ms | p95 ms |",
        "|---|---|---|---|---|",
    ]
    for item in report["stability"]:
        lines.append(
            f"| {item['method']} | {item['fact_recall_at_8']} | {item['fact_mrr']} | "
            f"{item['latency_p50_ms']} | {item['latency_p95_ms']} |"
        )
    lines.extend(
        [
            "",
            f"Safety pass: {report['safety_pass']}.",
            f"Broader-evaluation candidate: {report['candidate_decision']['broader_evaluation_candidate']}.",
            "",
            report["decision"],
            "",
        ]
    )
    return "\n".join(lines)


def markdown_answer_parameters(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['title']}",
        "",
        f"Model: `{report['model']['name']}`. Bounded map-page facts: 32 of a 50-message thread.",
        "",
        "| Factor | Value | Fact recall | Valid | Prompt tokens | Output tokens | Wall ms |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in report["stability"]:
        lines.append(
            f"| {item['factor']} | {item['value']} | {item['fact_recall']} | "
            f"{item['structured_valid']} | {item['prompt_tokens']} | "
            f"{item['output_tokens']} | {item['wall_ms']} |"
        )
    lines.extend(["", "## Recommendations", ""])
    for factor, value in report["recommendations"].items():
        lines.append(f"- `{factor}`: `{json.dumps(value, sort_keys=True)}`")
    lines.extend(["", report["decision"], ""])
    return "\n".join(lines)


def write_live_report(
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
