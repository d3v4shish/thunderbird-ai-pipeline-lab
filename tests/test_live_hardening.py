from __future__ import annotations

import unittest

from tb_ai_lab.contracts import Document, EvaluationCase, Scope
from tb_ai_lab.live_hardening import (
    _budget_evidence,
    _vector_comparison,
    answer_finalist_matrix,
    answer_parameter_matrix,
    combine_cross_encoder_repeats,
    evaluate_cross_encoder_repeat,
    evaluate_embedding_drift,
)
from tb_ai_lab.scale_evaluation import canonical_thread_range, scaled_thread_fixture
from tb_ai_lab.text import local_embedding


class FakeEmbeddingClient:
    def __init__(self) -> None:
        self.peak_ollama_vram_bytes = 1024
        self.peak_gpu_used_bytes = 2048
        self.unloads = 0

    def unload(self, _model: str) -> None:
        self.unloads += 1

    def embed(self, _model: str, inputs: list[str]) -> list[list[float]]:
        return [local_embedding(item) for item in inputs]


class FakeCrossEncoder:
    def __init__(self) -> None:
        self.request_count = 0
        self.request_bytes = 0
        self.response_bytes = 0

    def rerank(self, query: str, documents: list[str]) -> list[tuple[int, float]]:
        self.request_count += 1
        query_terms = set(query.casefold().split())
        scored = [
            (index, len(query_terms & set(document.casefold().split())))
            for index, document in enumerate(documents)
        ]
        scored.sort(key=lambda item: (-item[1], item[0]))
        return [(index, float(score)) for index, score in scored]


class LiveHardeningTests(unittest.TestCase):
    @staticmethod
    def fixture() -> tuple[list[Document], list[EvaluationCase]]:
        scope = Scope("tenant-alpha", "mail")
        documents = [
            Document("alpha", scope.tenant, scope.collection, "Alpha", "[FACT A01] code: ALPHA-101."),
            Document("beta", scope.tenant, scope.collection, "Beta", "[FACT A02] code: BETA-202."),
            Document("noise", scope.tenant, scope.collection, "Noise", "Routine unrelated note."),
        ]
        cases = [
            EvaluationCase(
                "alpha-query",
                "What is ALPHA-101?",
                scope,
                ("alpha",),
                {"A01": "ALPHA-101"},
            ),
            EvaluationCase(
                "beta-query",
                "What is BETA-202?",
                scope,
                ("beta",),
                {"A02": "BETA-202"},
            ),
        ]
        return documents, cases

    def test_vector_comparison_separates_exactness_from_cosine_tolerance(self) -> None:
        result = _vector_comparison([[1.0, 0.0]], [[1.0, 1e-12]])
        self.assertFalse(result["exact_equal"])
        self.assertAlmostEqual(result["mean_cosine_similarity"], 1.0)
        self.assertEqual(result["max_absolute_component_delta"], 1e-12)

    def test_embedding_drift_report_checks_batch_order_reload_and_rankings(self) -> None:
        documents, cases = self.fixture()
        client = FakeEmbeddingClient()
        report = evaluate_embedding_drift(
            client,  # type: ignore[arg-type]
            "fake",
            "digest",
            documents,
            cases,
            repeats=3,
            batch_size=2,
        )
        self.assertTrue(report["within_load_exact"])
        self.assertTrue(report["batch_and_order_invariant"])
        self.assertTrue(report["cross_load_exact"])
        self.assertTrue(report["rank_quality_tolerance_pass"])
        self.assertEqual(client.unloads, 3)

    def test_cross_encoder_lane_preserves_scope_sources_and_candidates(self) -> None:
        documents, cases = self.fixture()
        ollama = FakeEmbeddingClient()
        reranker = FakeCrossEncoder()
        repeat = evaluate_cross_encoder_repeat(
            ollama,  # type: ignore[arg-type]
            reranker,  # type: ignore[arg-type]
            "fake",
            documents,
            cases,
            repeat=1,
            candidate_count=8,
        )
        cross = next(item for item in repeat["lanes"] if item["method"] == "cross-encoder")
        self.assertEqual(cross["aggregate"]["scope_integrity"], 1.0)
        self.assertEqual(cross["aggregate"]["source_span_validity"], 1.0)
        self.assertEqual(cross["aggregate"]["candidate_set_preserved"], 1.0)
        combined = combine_cross_encoder_repeats(
            [repeat, {**repeat, "repeat": 2}, {**repeat, "repeat": 3}],
            "fake-cross-encoder",
            {"model_type": "reranker"},
        )
        self.assertTrue(combined["safety_pass"])

    def test_answer_parameter_matrix_is_one_factor_and_budget_is_hard(self) -> None:
        matrix = answer_parameter_matrix()
        baseline = matrix[0]
        for item in matrix[1:]:
            changed = sum(
                left != right
                for left, right in zip(item.key, baseline.key, strict=True)
            )
            self.assertEqual(changed, 1, item)
        for item in answer_finalist_matrix():
            self.assertEqual(item.factor, "combined_context_output")
            self.assertEqual(item.max_output_tokens, 2048)
            self.assertEqual(item.evidence_budget, 0)
            self.assertEqual(item.temperature, 0.0)
        documents, case = scaled_thread_fixture(50)
        evidence = canonical_thread_range(documents, case)
        budgeted = _budget_evidence(evidence, 4096)
        self.assertLessEqual(sum(len(item.text) for item in budgeted), 4096)
        self.assertTrue(all(item.tenant == case.scope.tenant for item in budgeted))


if __name__ == "__main__":
    unittest.main()
