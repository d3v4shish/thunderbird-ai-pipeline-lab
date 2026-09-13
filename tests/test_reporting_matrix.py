from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tb_ai_lab.cli import (
    artifact_name,
    enumerate_variants,
    partition_variants_by_vram,
    select_calibration_variants,
)
from tb_ai_lab.evaluation import combine_repeats, pareto_frontier, summarize_matrix
from tb_ai_lab.reporting import checkpoint, write_report


def result(identifier: str, quality: float, latency: float, passing: bool = True) -> dict:
    return {
        "variant": {"id": identifier},
        "aggregate": {
            "quality_score": quality,
            "recall_at_8": quality,
            "mrr": quality,
            "required_fact_recall": quality,
            "citation_precision": 1.0,
            "latency_p50_ms": latency,
            "hard_gate_pass": passing,
            "quality_pass": passing,
        },
        "cases": [],
    }


class ReportingMatrixTests(unittest.TestCase):
    def test_artifact_names_cannot_escape_the_report_directory(self) -> None:
        self.assertEqual(artifact_name("safe-report_1"), "safe-report_1")
        with self.assertRaises(Exception):
            artifact_name("../../outside")

    def test_matrix_enumeration_is_deterministic_and_role_aware(self) -> None:
        first = enumerate_variants(["chat-a"], ["deterministic-local-v1", "embed-a"])
        second = enumerate_variants(["chat-a"], ["deterministic-local-v1", "embed-a"])
        self.assertEqual([item.id for item in first], [item.id for item in second])
        self.assertEqual(len({item.id for item in first}), len(first))
        self.assertTrue(any(item.embedding_model == "embed-a" for item in first if item.retrieval == "dense"))
        self.assertTrue(all(item.embedding_model == "deterministic-local-v1" for item in first if item.retrieval == "exact" and item.reranking != "embedding"))

    def test_adaptive_selection_is_bounded_deterministic_and_covers_choices(self) -> None:
        variants = enumerate_variants(
            ["chat-a", "chat-b"], ["deterministic-local-v1", "embed-a"]
        )
        first = select_calibration_variants(variants, 24)
        second = select_calibration_variants(variants, 24)
        self.assertEqual([item.id for item in first], [item.id for item in second])
        self.assertEqual(len(first), 24)
        for field in (
            "model",
            "embedding_model",
            "chunking",
            "retrieval",
            "dense_candidates",
            "reranking",
            "graph",
            "tools",
            "prompt",
        ):
            self.assertEqual(
                {getattr(item, field) for item in first},
                {getattr(item, field) for item in variants},
                field,
            )

    def test_live_variants_are_partitioned_by_combined_measured_vram(self) -> None:
        gib = 1024**3
        variants = enumerate_variants(
            ["chat-a"],
            ["deterministic-local-v1", "embed-exact", "embed-over"],
        )
        eligible, rejected = partition_variants_by_vram(
            variants,
            {
                "chat-a": 10 * gib,
                "embed-exact": 7 * gib,
                "embed-over": 7 * gib + 1,
            },
            17,
        )
        self.assertTrue(
            any(item.embedding_model == "embed-exact" for item in eligible)
        )
        self.assertFalse(
            any(item.embedding_model == "embed-over" for item in eligible)
        )
        self.assertTrue(
            any(
                item["embedding_model"] == "embed-over"
                and item["reason"] == "CONFIGURATION_VRAM_CAP_EXCEEDED"
                for item in rejected
            )
        )

    def test_live_variants_fail_closed_without_vram_measurement(self) -> None:
        variants = enumerate_variants(["chat-a"], ["deterministic-local-v1"])
        eligible, rejected = partition_variants_by_vram(variants, {}, 17)
        self.assertEqual(eligible, [])
        self.assertEqual({item["reason"] for item in rejected}, {"VRAM_NOT_MEASURED"})

    def test_pareto_and_winners(self) -> None:
        results = [result("balanced", 0.9, 20), result("fast", 0.85, 10), result("dominated", 0.8, 30)]
        self.assertEqual(pareto_frontier(results), ["balanced", "fast"])
        summary = summarize_matrix(results)
        self.assertEqual(summary["max_quality"], "balanced")
        self.assertEqual(summary["fastest_passing"], "fast")
        self.assertFalse(summary["production_ready"])

    def test_repeats_are_combined_with_variance_and_raw_runs(self) -> None:
        first = result("same", 0.9, 10)
        first.update({"repeat": 0, "cases": []})
        second = result("same", 0.9, 20)
        second.update({"repeat": 1, "cases": []})
        combined = combine_repeats([first, second])
        self.assertEqual(len(combined), 1)
        self.assertEqual(len(combined[0]["runs"]), 2)
        self.assertEqual(combined[0]["aggregate"]["repeat_count"], 2)
        self.assertEqual(combined[0]["aggregate"]["repeat_variance"]["latency_p50_ms"], 25.0)

    def test_failed_empty_repeat_cannot_be_hidden_by_successful_runs(self) -> None:
        successful = result("same", 1.0, 10)
        successful["aggregate"].update(
            {
                "answer_correctness": 1.0,
                "structured_output_acceptance": 1.0,
                "tool_argument_validity": 1.0,
                "endpoint_success": 1.0,
                "graph_relation_recall": 1.0,
                "hard_failures": [],
            }
        )
        successful.update({"repeat": 0, "cases": []})
        failed = result("same", 0.0, 0, passing=False)
        failed["aggregate"].update(
            {
                "hard_failures": ["VRAM_CAP_EXCEEDED"],
                "quality_failures": [],
            }
        )
        failed.update({"repeat": 1, "cases": [], "error": "VRAM_CAP_EXCEEDED"})
        aggregate = combine_repeats([successful, failed])[0]["aggregate"]
        self.assertFalse(aggregate["hard_gate_pass"])
        self.assertFalse(aggregate["quality_pass"])
        self.assertIn("VRAM_CAP_EXCEEDED", aggregate["hard_failures"])
        self.assertEqual(aggregate["answer_correctness"], 0.5)

    def test_reports_and_checkpoints_are_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            report_result = result("one", 1.0, 1.0)
            report_result["cases"] = [{"case_id": "case-1", "query": "test"}]
            paths = write_report(directory, "test", [report_result], {"seed": 0})
            self.assertEqual(set(paths), {"json", "jsonl", "markdown", "html"})
            self.assertTrue(all(path.is_file() for path in paths.values()))
            report = json.loads(paths["json"].read_text())
            self.assertEqual(report["manifest"]["seed"], 0)
            rendered_html = paths["html"].read_text()
            self.assertIn("<table>", rendered_html)
            self.assertIn("<details>", rendered_html)
            target = directory / "checkpoint.json"
            checkpoint(target, {"schema_version": 1, "completed": {"a": 1}})
            self.assertEqual(json.loads(target.read_text())["completed"], {"a": 1})
            self.assertFalse(target.with_suffix(".json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
