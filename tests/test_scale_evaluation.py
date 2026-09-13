from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from tb_ai_lab.cli import baseline_variant
from tb_ai_lab.contracts import Document, EvaluationCase
from tb_ai_lab.corpus import cases, documents
from tb_ai_lab.scale_evaluation import (
    EXTENDED_THREAD_FIXTURE_DIGESTS,
    EXTENDED_THREAD_SIZES,
    THREAD_FIXTURE_DIGESTS,
    THREAD_SIZES,
    _extract_scale_facts,
    _hierarchical_reduce,
    canonical_thread_range,
    evaluate_deterministic_parameters,
    evaluate_parent_storage,
    evaluate_thread_scale,
    markdown_scale_report,
    scaled_thread_fixture,
    thread_fixture_digest,
    write_scale_report,
)


class ScaleEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.documents = [Document.from_dict(item) for item in documents()]
        cls.cases = [EvaluationCase.from_dict(item) for item in cases()]

    def test_scale_fixtures_are_frozen_synthetic_and_scope_separated(self) -> None:
        for size in THREAD_SIZES:
            corpus, case = scaled_thread_fixture(size)
            self.assertEqual(thread_fixture_digest(size), THREAD_FIXTURE_DIGESTS[size])
            self.assertEqual(len(case.expected_facts), size)
            self.assertEqual(len(corpus), size + 13)
            self.assertTrue(all(item.metadata.get("synthetic") is True for item in corpus))
            self.assertTrue(all("@example.invalid" in item.text for item in corpus))

    def test_thread_range_and_hierarchy_are_complete_ordered_and_bounded(self) -> None:
        corpus, case = scaled_thread_fixture(500)
        evidence = canonical_thread_range(corpus, case)
        self.assertEqual([item.document_id for item in evidence], list(case.expected_document_ids))
        self.assertNotIn("PRIVATE-SHADOW-999", " ".join(item.text for item in evidence))
        pages = [evidence[start : start + 32] for start in range(0, len(evidence), 32)]
        facts, peak_characters, _ledger_characters = _hierarchical_reduce(pages, 16)
        self.assertEqual(facts, dict(case.expected_facts))
        self.assertLess(peak_characters, sum(len(item.text) for item in evidence))
        self.assertEqual(_extract_scale_facts(evidence), dict(case.expected_facts))

    def test_extended_thread_fixtures_are_frozen_and_complete(self) -> None:
        for size in EXTENDED_THREAD_SIZES:
            corpus, case = scaled_thread_fixture(size)
            self.assertEqual(
                thread_fixture_digest(size), EXTENDED_THREAD_FIXTURE_DIGESTS[size]
            )
            evidence = canonical_thread_range(corpus, case)
            self.assertEqual(len(evidence), size)
            self.assertEqual(_extract_scale_facts(evidence), dict(case.expected_facts))

    def test_scale_evaluation_exposes_top_k_loss_and_hierarchical_recovery(self) -> None:
        report = evaluate_thread_scale((50,), page_size=16, reduction_batch_size=8)
        methods = {item["method"]: item for item in report["results"][0]["methods"]}
        self.assertEqual(methods["direct-top-8"]["metrics"]["answer_fact_recall"], 8 / 50)
        self.assertEqual(methods["hierarchical-ledger"]["metrics"]["answer_fact_recall"], 1.0)
        self.assertTrue(report["hard_gate_pass"])

    def test_parent_storage_has_exact_behavioral_parity(self) -> None:
        report = evaluate_parent_storage(
            self.documents, self.cases, baseline_variant(), repeats=1
        )
        self.assertTrue(report["behavioral_parity"])
        normalized = next(
            item for item in report["lanes"] if item["layout"] == "normalized-parent"
        )
        self.assertEqual(normalized["records"][0]["storage"]["chunk_passage_characters"], 0)

    def test_parameter_sweep_changes_only_named_factor(self) -> None:
        report = evaluate_deterministic_parameters(
            self.documents, self.cases, baseline_variant()
        )
        self.assertEqual(set(report["factors"]), set(report["recommendations"]))
        baseline = report["baseline"]
        for lane in report["lanes"]:
            changed = {
                key
                for key, value in lane["variant"].items()
                if value != baseline[key] and key != "id"
            }
            if lane["factor"] == "chunk_chars":
                self.assertLessEqual(changed, {"chunk_chars", "chunk_overlap"})
            else:
                self.assertLessEqual(changed, {lane["factor"]})

    def test_report_writer_is_atomic_and_parseable(self) -> None:
        report = evaluate_thread_scale((50,))
        with tempfile.TemporaryDirectory(prefix="tb-ai-scale-report-") as temporary:
            paths = write_scale_report(
                Path(temporary), "scale", report, markdown_scale_report(report)
            )
            self.assertTrue(paths["json"].is_file())
            self.assertIn("Synthetic Large-Thread", paths["markdown"].read_text())


if __name__ == "__main__":
    unittest.main()
