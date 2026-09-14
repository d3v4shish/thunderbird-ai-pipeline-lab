from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tb_ai_lab.context_ladder import (
    ContextLadderError,
    MAX_DIRECT_EMAIL_CHARACTERS,
    _drain_assignments,
    _template_offer,
    context_ladder_fixture,
    evaluate_context_ladder,
    live_screen_plan,
    run_live_screen,
    template_confirmation_messages,
    validate_template_confirmation,
    write_context_ladder_report,
)


class FakeLadderClient:
    def __init__(self, *, malformed: bool = False, cancel: bool = False) -> None:
        self.malformed = malformed
        self.cancel = cancel
        self.calls = 0
        self.options: list[dict[str, object]] = []

    def chat(self, _model: str, messages: list[dict], **options: object) -> dict:
        self.calls += 1
        self.options.append(options)
        if self.cancel:
            raise KeyboardInterrupt
        if self.malformed:
            return {"message": {"content": "not json"}}
        if "Classify untrusted email" in messages[0]["content"]:
            return {"message": {"content": '{"family_id":null,"slots":[]}'}}
        return {
            "message": {"content": '{"context":"Bounded retrieval metadata."}'},
            "prompt_eval_count": 12,
            "eval_count": 6,
        }


class ContextLadderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.documents, self.cases = context_ladder_fixture()
        self.invoice = next(item for item in self.documents if item.id == "ladder-invoice-04")

    def test_fixture_has_required_synthetic_controls_and_scope_shadow(self) -> None:
        self.assertEqual(len(self.cases), 7)
        long_documents = [item for item in self.documents if item.metadata["kind"] == "long-control"]
        self.assertEqual([len(item.text) for item in long_documents], [10 * 1024, 256 * 1024, 1024 * 1024])
        self.assertTrue(any(item.tenant == "tenant-beta" for item in self.documents))
        self.assertTrue(any("IGNORE ALL PRIOR" in item.text for item in self.documents))
        self.assertTrue(any("RELAMPAGO-7" in item.text for item in self.documents))

    def test_template_confirmation_is_closed_world_and_source_offset_checked(self) -> None:
        offers = [
            {"id": "family-invoice", "slot_names": ["invoice", "amount"]},
            {"id": "family-shipment", "slot_names": ["shipment"]},
        ]
        messages = template_confirmation_messages(self.invoice, offers)
        self.assertEqual(json.loads(messages[1]["content"])["source"]["text"], self.invoice.text)
        self.assertIn("host-offered", messages[0]["content"])
        amount_start = self.invoice.text.index("USD 440.00")
        accepted = validate_template_confirmation(
            json.dumps(
                {
                    "family_id": "family-invoice",
                    "slots": [
                        {
                            "name": "amount",
                            "value": "USD 440.00",
                            "start": amount_start,
                            "end": amount_start + len("USD 440.00"),
                        }
                    ],
                }
            ),
            self.invoice,
            offers,
        )
        self.assertEqual(accepted["family_id"], "family-invoice")
        with self.assertRaisesRegex(ContextLadderError, "host-offered"):
            validate_template_confirmation('{"family_id":"family-private","slots":[]}', self.invoice, offers)
        with self.assertRaisesRegex(ContextLadderError, "source-backed"):
            validate_template_confirmation(
                '{"family_id":"family-invoice","slots":[{"name":"amount","value":"USD 440.00","start":0,"end":10}]}',
                self.invoice,
                offers,
            )

    def test_drain_offer_is_chronological_and_never_includes_cross_scope_shadow(self) -> None:
        small = [item for item in self.documents if item.metadata["kind"] != "long-control"]
        assignments = _drain_assignments(small)
        self.assertNotIn("ladder-invoice-03", assignments)
        self.assertIn("ladder-invoice-04", assignments)
        offers = _template_offer(self.invoice, small)
        self.assertTrue(offers)
        self.assertTrue(all(item["id"].startswith("template-") for item in offers))
        self.assertNotIn("ladder-cross-scope-shadow", json.dumps(offers))

    def test_staged_evaluation_preserves_scope_and_promotes_only_after_pairs(self) -> None:
        report = evaluate_context_ladder()
        by_id = {item["config"]["id"]: item for item in report["results"]}
        self.assertTrue(report["hard_contract_pass"])
        self.assertTrue(by_id["control-raw-hybrid"]["promotion_gate"]["passed"])
        self.assertFalse(by_id["retrieval-exact"]["promotion_gate"]["passed"])
        self.assertEqual(by_id["full-context-template-memory-package"]["status"], "measured")
        for result in report["results"]:
            for case in result.get("cases", []):
                self.assertNotIn("ladder-cross-scope-shadow", case["retrieved_document_ids"])
                self.assertEqual(case["metrics"]["source_span_validity"], 1.0)
                self.assertEqual(case["metrics"]["scope_validity"], 1.0)
        self.assertEqual(len(report["manual_review"]), 20)
        self.assertEqual(len(report["manual_review_key"]["review_key"]), 20)

    def test_long_source_and_thread_controls_are_complete_without_direct_oversize_calls(self) -> None:
        report = evaluate_context_ladder()
        controls = {item["document_id"]: item for item in report["large_source_controls"]}
        self.assertTrue(controls["LARGE-10K"]["direct_whole_email_allowed"])
        self.assertFalse(controls["LARGE-256K"]["direct_whole_email_allowed"])
        self.assertFalse(controls["LARGE-1M"]["direct_whole_email_allowed"])
        self.assertTrue(all(item["complete"] for item in controls.values()))
        scale = {item["message_count"]: item for item in report["thread_scale_controls"]}
        self.assertEqual(scale[5_000]["ledger_fact_recall"], 1.0)
        self.assertLess(scale[5_000]["top_k_fact_recall"], 0.01)
        plan = live_screen_plan(self.documents, ["qwen3:8b"], 1)
        self.assertEqual(plan["oversized_direct_calls"], 0)
        self.assertEqual(plan["oversized_page_contract"]["maximum_direct_characters"], MAX_DIRECT_EMAIL_CHARACTERS)
        self.assertEqual(plan["paged_context_calls_per_repeat"], 0)
        expanded_plan = live_screen_plan(
            self.documents, ["qwen3:8b"], 1, include_large_pages=True
        )
        self.assertEqual(expanded_plan["paged_context_calls_per_repeat"], 134)
        large = next(item for item in self.documents if item.id == "LARGE-256K")
        with tempfile.TemporaryDirectory(prefix="tb-ai-context-ladder-pages-") as temporary:
            paged = run_live_screen(
                FakeLadderClient(),
                "mock-pages",
                "digest",
                [large],
                1,
                Path(temporary) / "pages.json",
                include_large_pages=True,
            )
        self.assertTrue(paged["complete"])
        self.assertEqual(paged["summary"]["record_count"], 28)
        self.assertEqual(paged["paged_source_contracts"], [{
            "document_id": "LARGE-256K",
            "page_count": 14,
            "source_coverage": True,
            "direct_model_call": False,
        }])

    def test_live_screen_is_resumable_and_fail_closed_on_malformed_or_cancelled_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="tb-ai-context-ladder-") as temporary:
            cache = Path(temporary) / "cache.json"
            first = FakeLadderClient()
            result = run_live_screen(first, "mock", "digest", self.documents, 1, cache)
            self.assertTrue(result["complete"])
            self.assertGreater(first.calls, 0)
            self.assertTrue(all("json_schema" in options for options in first.options))
            second = FakeLadderClient()
            resumed = run_live_screen(second, "mock", "digest", self.documents, 1, cache)
            self.assertTrue(resumed["complete"])
            self.assertEqual(second.calls, 0)

            malformed = run_live_screen(
                FakeLadderClient(malformed=True),
                "bad",
                "digest",
                self.documents,
                1,
                Path(temporary) / "malformed.json",
            )
            self.assertFalse(malformed["complete"])
            self.assertIn("valid JSON", malformed["fatal_error"])
            cancelled = run_live_screen(
                FakeLadderClient(cancel=True),
                "cancel",
                "digest",
                self.documents,
                1,
                Path(temporary) / "cancelled.json",
            )
            self.assertTrue(cancelled["cancelled"])
            self.assertFalse(cancelled["complete"])

    def test_report_writes_all_reviewable_formats(self) -> None:
        with tempfile.TemporaryDirectory(prefix="tb-ai-context-ladder-report-") as temporary:
            report = evaluate_context_ladder()
            paths = write_context_ladder_report(Path(temporary), "ladder", report)
            self.assertEqual(set(paths), {"json", "jsonl", "markdown", "html", "review", "review_key"})
            self.assertTrue(all(path.is_file() for path in paths.values()))
            review = paths["review"].read_text(encoding="utf-8")
            self.assertNotIn("expected_facts", review)
            parsed = json.loads(paths["json"].read_text(encoding="utf-8"))
            self.assertEqual(parsed["version"], "context-ladder-v1")


if __name__ == "__main__":
    unittest.main()
