from __future__ import annotations

import unittest

from tb_ai_lab.oversized_designs import (
    evaluate_oversized_designs_deterministic,
    markdown_oversized_designs,
)


class OversizedDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = evaluate_oversized_designs_deterministic()

    def test_input_designs_separate_lossy_sampling_from_schema_compaction(self) -> None:
        lanes = {item["design"]: item for item in self.report["input_selection"]}
        for design in ("prefix", "suffix", "head-tail", "middle"):
            self.assertEqual(lanes[design]["metrics"]["fact_recall"], 0.09375)
            self.assertFalse(lanes[design]["completeness_provable"])
        self.assertEqual(
            lanes["uniform-eight-windows"]["metrics"]["fact_recall"], 0.125
        )
        compact = lanes["known-schema-source-compaction"]
        self.assertEqual(compact["metrics"]["fact_recall"], 1.0)
        self.assertTrue(compact["completeness_provable"])
        self.assertLess(compact["model_input_characters"], 4096)

    def test_chunk_designs_measure_coverage_integrity_and_amplification(self) -> None:
        lanes = {item["design"]: item for item in self.report["chunking"]}
        self.assertLess(lanes["fixed-capped-current"]["source_coverage"], 0.1)
        self.assertEqual(lanes["fixed-uncapped"]["source_coverage"], 1.0)
        self.assertEqual(lanes["fixed-uncapped"]["unique_fact_count"], 64)
        self.assertEqual(lanes["structure-aware"]["unique_fact_count"], 64)
        sentence = lanes["sentence-window"]
        self.assertEqual(sentence["source_coverage"], 1.0)
        self.assertEqual(sentence["unique_fact_count"], 63)
        self.assertGreater(sentence["returned_passage_characters"], 4_000_000)
        self.assertTrue(all(item["source_span_valid"] for item in lanes.values()))

    def test_retrieval_designs_keep_targeted_and_exhaustive_contracts_separate(self) -> None:
        targeted = {
            (item["mode"], item["top_k"]): item
            for item in self.report["retrieval"]["targeted"]
        }
        self.assertEqual(targeted[("lexical", 1)]["passed_count"], 3)
        self.assertEqual(targeted[("hybrid", 4)]["passed_count"], 3)
        self.assertEqual(targeted[("exact", 16)]["passed_count"], 0)
        exhaustive = {
            (item["mode"], item["top_k"]): item
            for item in self.report["retrieval"]["exhaustive"]
        }
        self.assertLess(exhaustive[("hybrid", 8)]["metrics"]["fact_recall"], 0.1)
        lexical_all = exhaustive[("lexical", 128)]
        self.assertEqual(lexical_all["metrics"]["fact_recall"], 1.0)
        self.assertGreater(lexical_all["returned_characters"], 200_000)
        reranking = self.report["retrieval"]["reranking"]
        self.assertTrue(
            all(
                item["rank"] == 1
                for item in reranking
                if item["method"] == "deterministic"
            )
        )
        self.assertTrue(
            all(
                not item["passed"]
                for item in reranking
                if item["method"] == "embedding"
            )
        )

    def test_paging_reduction_output_and_tool_budgets_expose_failure_modes(self) -> None:
        structured = [
            item
            for item in self.report["paging"]
            if item["design"] == "structure-aware-pages"
        ]
        self.assertTrue(
            all(item["metrics"]["fact_recall"] == 1.0 for item in structured)
        )
        adversarial = next(
            item
            for item in self.report["paging"]
            if item["design"] == "hard-character-adversarial-boundary"
        )
        self.assertLess(adversarial["metrics"]["matched_fact_count"], 64)
        reduction = self.report["reduction"]
        self.assertTrue(
            all(
                item["metrics"]["fact_recall"] == 1.0
                for item in reduction["host_hierarchies"]
            )
        )
        self.assertEqual(
            reduction["rolling_4096_character_tail"]["metrics"]["fact_recall"],
            0.875,
        )
        output_4096 = next(
            item
            for item in reduction["output_delivery"]
            if item["character_budget"] == 4096
        )
        self.assertEqual(output_4096["single_response_metrics"]["fact_recall"], 0.875)
        self.assertEqual(output_4096["paged_response_metrics"]["fact_recall"], 1.0)
        tool = self.report["bounded_agent_tool"]
        self.assertFalse(tool["exhaustive_possible_under_current_budget"])
        self.assertEqual(tool["metrics"]["matched_fact_count"], 6)
        self.assertTrue(tool["source_span_valid"])

    def test_report_names_objectives_limitations_and_decisions(self) -> None:
        self.assertFalse(self.report["production_ready"])
        self.assertEqual(
            set(self.report["objectives"]),
            {"localized_question", "exhaustive_known_schema", "open_ended_summary"},
        )
        self.assertEqual(len(self.report["specialized_designs"]), 4)
        markdown = markdown_oversized_designs({"deterministic": self.report})
        self.assertIn("Localized question", markdown)
        self.assertIn("Open-ended summary", markdown)
        self.assertIn("Every prompt and raw live output", markdown)


if __name__ == "__main__":
    unittest.main()
