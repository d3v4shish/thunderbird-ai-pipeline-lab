from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tb_ai_lab.cli import baseline_variant
from tb_ai_lab.contracts import Document, EvaluationCase
from tb_ai_lab.corpus import cases, documents
from tb_ai_lab.pipeline import Pipeline
from tb_ai_lab.rag_evaluation import evaluate_rag_stages, write_rag_report
from tb_ai_lab.storage import Index


class RagEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.documents = [Document.from_dict(item) for item in documents()]
        cls.cases = [EvaluationCase.from_dict(item) for item in cases()]
        cls.report = evaluate_rag_stages(
            cls.documents, cls.cases, baseline_variant(), top_k=8
        )

    def test_stages_are_isolated_and_cover_the_supported_rag_dimensions(self) -> None:
        stages = self.report["stages"]
        self.assertEqual(
            set(stages),
            {
                "chunking",
                "chunk_size",
                "retrieval",
                "retrieval_depth",
                "query_expansion",
                "reranking",
                "graph",
                "full_pipeline",
            },
        )
        retrieval_variants = [item["variant"] for item in stages["retrieval"]]
        controls = []
        for variant in retrieval_variants:
            controls.append(
                {
                    key: value
                    for key, value in variant.items()
                    if key not in {"id", "retrieval"}
                }
            )
        self.assertTrue(all(item == controls[0] for item in controls))
        self.assertEqual(
            {item["variant"]["retrieval"] for item in stages["retrieval"]},
            {"exact", "lexical", "dense", "hybrid"},
        )

    def test_chunking_and_graph_metrics_expose_known_behavior(self) -> None:
        chunking = {
            item["variant"]["chunking"]: item for item in self.report["stages"]["chunking"]
        }
        self.assertEqual(chunking["sentence-window"]["metrics"]["source_coverage"], 1.0)
        self.assertEqual(chunking["sentence-window"]["metrics"]["fact_integrity"], 1.0)
        self.assertGreater(
            chunking["sentence-window"]["metrics"]["passage_redundancy"],
            chunking["structure-aware"]["metrics"]["passage_redundancy"],
        )
        graph = {
            item["variant"]["graph"]: item["aggregate"]["relation_recall"]
            for item in self.report["stages"]["graph"]
        }
        self.assertEqual(graph["off"], 0.0)
        self.assertLess(graph["keyword"], graph["intent-multihop"])
        self.assertEqual(graph["intent-multihop"], 1.0)

    def test_full_pipeline_runs_only_after_stage_ablations(self) -> None:
        full = {
            item["variant"]["id"]: item
            for item in self.report["stages"]["full_pipeline"]
        }
        self.assertLess(
            full["full-current"]["aggregate"]["required_fact_recall"], 1.0
        )
        self.assertEqual(
            full["full-advanced-structure"]["aggregate"]["required_fact_recall"],
            1.0,
        )
        self.assertTrue(
            full["full-advanced-sentence-window"]["aggregate"]["quality_pass"]
        )

    def test_sentence_window_retrieval_deduplicates_shared_parent_spans(self) -> None:
        variant = baseline_variant(
            chunking="sentence-window",
            max_chunks=4096,
            graph="off",
            tools="none",
        )
        case = next(item for item in self.cases if item.id == "exact-identifier")
        with Index() as index:
            pipeline = Pipeline(index, variant)
            pipeline.ingest(self.documents)
            evidence = pipeline.retrieve(case.query, case.scope)
        spans = [
            (item.tenant, item.collection, item.document_id, item.start, item.end)
            for item in evidence
        ]
        self.assertEqual(len(spans), len(set(spans)))

    def test_report_writer_emits_parseable_review_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="tb-ai-rag-report-") as temporary:
            paths = write_rag_report(Path(temporary), "staged", self.report)
            self.assertTrue(paths["json"].is_file())
            markdown = paths["markdown"].read_text(encoding="utf-8")
            self.assertIn("## Technique coverage", markdown)
            self.assertIn("## Full deterministic pipeline", markdown)

    def test_top_k_contract_fails_before_evaluation(self) -> None:
        with self.assertRaisesRegex(ValueError, "top_k"):
            evaluate_rag_stages(
                self.documents, self.cases, baseline_variant(), top_k=0
            )


if __name__ == "__main__":
    unittest.main()
