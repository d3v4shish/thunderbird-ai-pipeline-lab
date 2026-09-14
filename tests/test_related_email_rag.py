from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import re
import tempfile
import unittest

from tb_ai_lab.related_email_rag import (
    RelatedEmailRagError,
    _prepare_index,
    _template_catalog,
    evaluate_related_email_rag,
    expand_seed,
    live_related_plan,
    operation_messages,
    prior_thread_memory,
    related_email_fixture,
    related_fixture_digest,
    resolve_source_value,
    run_live_related_screen,
    seed_is_qualified,
    template_offers,
    validate_template_selection,
    write_related_email_report,
)
from tb_ai_lab.contracts import Scope
from tb_ai_lab.slot_candidates import build_slot_candidates
from tb_ai_lab.text import chunk_document


class FakeRelatedClient:
    def __init__(self, *, malformed: bool = False, cancel: bool = False) -> None:
        self.malformed = malformed
        self.cancel = cancel
        self.calls = 0

    def chat(self, _model: str, messages: list[dict], **_options: object) -> dict:
        self.calls += 1
        if self.cancel:
            raise KeyboardInterrupt
        if self.malformed:
            return {"message": {"content": "not json"}}
        payload = json.loads(messages[1]["content"])
        document_id = payload["current_email"]["document_id"]
        source = payload["current_email"]["source"]
        offers = payload.get("offered_template_families", [])
        candidates = payload.get("host_slot_candidates", [])
        system = messages[0]["content"]
        selects_template = "In one pass" in system or "Choose one host-offered" in system
        family_id = None
        selected_candidate_ids = []
        if selects_template and (
            (
                document_id.startswith("rel-invoice-")
                and not document_id.endswith("reply")
            )
            or document_id.startswith("rel-shipment-")
            or document_id.startswith("rel-factura-")
        ):
            family_id = offers[0]["id"]
            if document_id.startswith("rel-invoice-"):
                value = re.search(r"\$\d+\.\d{2}", source).group(0)
            elif document_id.startswith("rel-shipment-"):
                value = re.search(r"2031-05-\d{2}", source).group(0)
            else:
                value = re.search(r"\d+\.\d{2} EUR", source).group(0)
            selected_candidate_ids = [
                next(item["candidate_id"] for item in candidates if item["value"] == value)
            ]
        template = {
            "family_id": family_id,
            "selected_slot_candidate_ids": selected_candidate_ids,
        }
        context = {"context": "Synthetic source record."}
        memory = {
            "summary": "Synthetic source record summary.",
            "events": [],
            "relations": [],
        }
        if "In one pass" in system:
            value = {**context, **memory, **template}
        elif "query-independent context" in system:
            value = context
        elif "detailed current-email summary" in system:
            value = memory
        else:
            value = template
        return {
            "message": {"content": json.dumps(value)},
            "prompt_eval_count": 100,
            "eval_count": 20,
        }


class RelatedEmailRagTests(unittest.TestCase):
    def setUp(self) -> None:
        self.documents, self.cases = related_email_fixture()
        self.scope = Scope("tenant-alpha", "mail")
        self.invoice = next(item for item in self.documents if item.id == "rel-invoice-04")

    def test_fixture_has_thread_family_and_scope_controls(self) -> None:
        self.assertEqual(len(self.documents), 18)
        self.assertEqual(len(self.cases), 8)
        self.assertEqual(
            related_fixture_digest(),
            "37b586643dcf9cf1863cbf8ebcfdca032cba8de0d7edc8fd1df3ece956c5f8b6",
        )
        self.assertTrue(any(item.tenant == "tenant-beta" for item in self.documents))
        self.assertTrue(any("Ignore all previous" in item.text for item in self.documents))
        memory = prior_thread_memory(
            next(item for item in self.documents if item.id == "rel-invoice-04-reply"),
            self.documents,
        )
        self.assertIn("rel-invoice-04", memory)
        self.assertNotIn("rel-invoice-05", memory)
        self.assertNotIn("rel-cross-scope-shadow", memory)

    def test_value_resolution_uses_unique_source_or_exact_anchor(self) -> None:
        unique = resolve_source_value("before VALUE after", "VALUE")
        self.assertEqual((unique["start"], unique["end"]), (7, 12))
        source = "first VALUE here; second VALUE there"
        with self.assertRaisesRegex(RelatedEmailRagError, "ambiguous"):
            resolve_source_value(source, "VALUE")
        anchored = resolve_source_value(source, "VALUE", "second VALUE there")
        self.assertEqual(source[anchored["start"] : anchored["end"]], "VALUE")
        with self.assertRaisesRegex(RelatedEmailRagError, "absent"):
            resolve_source_value(source, "MISSING")

    def test_template_selection_rejects_model_offsets_and_bad_families(self) -> None:
        families, assignments, labels = _template_catalog(self.documents, self.scope)
        offers = template_offers(
            self.invoice, self.documents, families, assignments, labels
        )
        amount = "$540.00"
        anchor_start = self.invoice.text.index("[FACT I04]")
        anchor_end = self.invoice.text.index(". Payment", anchor_start) + 1
        accepted = validate_template_selection(
            {
                "family_id": assignments[self.invoice.id].family_id,
                "slots": [
                    {
                        "name": "amount",
                        "value": amount,
                        "anchor": self.invoice.text[anchor_start:anchor_end],
                    }
                ],
            },
            self.invoice,
            offers,
        )
        self.assertEqual(
            self.invoice.text[accepted["slots"][0]["start"] : accepted["slots"][0]["end"]],
            amount,
        )
        with self.assertRaisesRegex(RelatedEmailRagError, "fields"):
            validate_template_selection(
                {
                    "family_id": assignments[self.invoice.id].family_id,
                    "slots": [
                        {"name": "amount", "value": amount, "start": 1, "end": 2}
                    ],
                },
                self.invoice,
                offers,
            )
        with self.assertRaisesRegex(RelatedEmailRagError, "host-offered"):
            validate_template_selection(
                {"family_id": "private-family", "slots": []},
                self.invoice,
                offers,
            )

    def test_live_prompt_exposes_only_host_candidate_ids_for_slots(self) -> None:
        families, assignments, labels = _template_catalog(self.documents, self.scope)
        offers = template_offers(
            self.invoice, self.documents, families, assignments, labels
        )
        candidates = build_slot_candidates(self.invoice, offers)
        self.assertEqual(
            [item["value"] for item in candidates if item["name"] == "amount"],
            ["$540.00", "$540.00"],
        )
        for kind in ("combined", "modular-template"):
            messages, schema = operation_messages(
                kind, self.invoice, "", {}, offers, candidates
            )
            instruction = messages[0]["content"]
            self.assertIn("host_slot_candidates", instruction)
            self.assertIn("candidate IDs", instruction)
            self.assertIn("selected_slot_candidate_ids", schema["required"])
            payload = json.loads(messages[1]["content"])
            self.assertNotIn("start", payload["host_slot_candidates"][0])
            self.assertNotIn("end", payload["host_slot_candidates"][0])
        context_messages, _ = operation_messages(
            "modular-context", self.invoice, "prior", {}, offers, candidates
        )
        context_payload = json.loads(context_messages[1]["content"])
        self.assertEqual(set(context_payload), {"current_email"})
        memory_messages, _ = operation_messages(
            "modular-memory", self.invoice, "prior", {}, offers, candidates
        )
        memory_payload = json.loads(memory_messages[1]["content"])
        self.assertNotIn("offered_template_families", memory_payload)
        self.assertNotIn("host_slot_candidates", memory_payload)

    def test_storage_enumerates_scope_and_invalidates_stale_assignments(self) -> None:
        config = {
            "context": True,
            "memory": True,
            "template": True,
        }
        index, assignments, _labels, _families = _prepare_index(self.documents, config)
        try:
            family_id = assignments[self.invoice.id].family_id
            family_ids = index.template_family_document_ids(family_id, self.scope)
            self.assertEqual(len(family_ids), 6)
            self.assertNotIn("rel-cross-scope-shadow", family_ids)
            self.assertEqual(
                index.thread_document_ids("BILL-04", self.scope),
                ["rel-invoice-04", "rel-invoice-04-reply"],
            )
            edited = replace(self.invoice, text=self.invoice.text + "\nEdited.")
            index.add_document(
                edited,
                chunk_document(edited, "structure-aware", 900, 120, 256),
                build_vector_buckets=False,
            )
            self.assertIsNone(index.template_assignment(edited.id, self.scope))
            self.assertNotIn(edited.id, index.template_family_document_ids(family_id, self.scope))
        finally:
            index.close()

    def test_qualified_seed_expands_non_recursively_to_thread_family_union(self) -> None:
        config = {"context": True, "memory": True, "template": True}
        index, _assignments, _labels, _families = _prepare_index(self.documents, config)
        try:
            query = "Find every message related to invoice INV-5104."
            direct = index.search(query, self.scope, "hybrid", 8, candidate_mode="full-scan")
            seed = direct[0]
            self.assertTrue(seed_is_qualified(index, seed, query, self.scope))
            evidence, audit = expand_seed(
                index, seed, query, self.scope, "union", complete=True
            )
            expected = set(next(item for item in self.cases if item["id"] == "complete-invoice-related")["expected_related_ids"])
            self.assertEqual(set(audit["expanded_document_ids"]), expected)
            self.assertFalse(audit["recursive"])
            self.assertTrue(audit["ledger"]["complete"])
            self.assertNotIn("rel-cross-scope-shadow", {item.document_id for item in evidence})
        finally:
            index.close()

    def test_deterministic_evaluation_is_staged_and_complete(self) -> None:
        report = evaluate_related_email_rag()
        self.assertTrue(report["hard_contract_pass"])
        by_id = {item["config"]["id"]: item for item in report["results"]}
        complete = by_id["complete-union-expansion"]
        self.assertEqual(complete["aggregate"]["related_precision"], 1.0)
        self.assertEqual(complete["aggregate"]["related_recall"], 1.0)
        self.assertEqual(complete["aggregate"]["source_span_validity"], 1.0)
        self.assertEqual(complete["aggregate"]["scope_validity"], 1.0)
        self.assertEqual(complete["aggregate"]["unrelated_document_count"], 0)
        self.assertEqual(report["long_source_contract"]["fact_recall"], 1.0)
        self.assertFalse(report["long_source_contract"]["direct_allowed"])
        self.assertTrue(report["long_source_contract"]["source_coverage"])
        self.assertEqual(report["scale_controls"][-1]["complete_ledger_recall"], 1.0)

    def test_live_combined_and_modular_screen_is_resumable(self) -> None:
        plan = live_related_plan(self.documents, ["mock"], 1)
        self.assertEqual(plan["total_calls"], 32)
        with tempfile.TemporaryDirectory(prefix="tb-ai-related-live-") as temporary:
            cache = Path(temporary) / "checkpoint.json"
            client = FakeRelatedClient()
            result = run_live_related_screen(
                client, "mock", "digest", self.documents, 1, cache
            )
            self.assertTrue(result["complete"])
            self.assertTrue(result["quality_gate_pass"])
            self.assertEqual(client.calls, 32)
            self.assertEqual(result["quality"]["combined"]["family_f1"], 1.0)
            self.assertEqual(result["quality"]["combined"]["slot_recall"], 1.0)
            resumed_client = FakeRelatedClient()
            resumed = run_live_related_screen(
                resumed_client, "mock", "digest", self.documents, 1, cache
            )
            self.assertTrue(resumed["complete"])
            self.assertEqual(resumed_client.calls, 0)

    def test_live_screen_fails_closed_on_malformed_output_and_cancellation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="tb-ai-related-failure-") as temporary:
            malformed_cache = Path(temporary) / "malformed.json"
            malformed = run_live_related_screen(
                FakeRelatedClient(malformed=True),
                "bad",
                "digest",
                self.documents,
                1,
                malformed_cache,
            )
            self.assertFalse(malformed["complete"])
            self.assertIn("valid JSON", malformed["fatal_error"])
            self.assertEqual(malformed["summary"]["record_count"], 1)
            self.assertEqual(malformed["summary"]["errors"], 1)
            resumed_client = FakeRelatedClient()
            resumed_failure = run_live_related_screen(
                resumed_client,
                "bad",
                "digest",
                self.documents,
                1,
                malformed_cache,
            )
            self.assertEqual(resumed_client.calls, 0)
            self.assertEqual(resumed_failure["fatal_error"], malformed["fatal_error"])
            cancelled = run_live_related_screen(
                FakeRelatedClient(cancel=True),
                "cancel",
                "digest",
                self.documents,
                1,
                Path(temporary) / "cancelled.json",
            )
            self.assertFalse(cancelled["complete"])
            self.assertTrue(cancelled["cancelled"])
            self.assertEqual(cancelled["summary"]["record_count"], 1)

    def test_report_writes_live_visible_and_blinded_formats(self) -> None:
        report = evaluate_related_email_rag()
        report["live"] = {
            "requested": True,
            "dry_run": False,
            "plan": live_related_plan(self.documents, ["mock"], 1),
            "runs": [
                {
                    "model": "mock",
                    "result": {
                        "complete": False,
                        "quality_gate_pass": False,
                        "fatal_error": "diagnostic failure",
                        "records": [],
                    },
                }
            ],
        }
        with tempfile.TemporaryDirectory(prefix="tb-ai-related-report-") as temporary:
            paths = write_related_email_report(Path(temporary), "related", report)
            self.assertEqual(
                set(paths),
                {"json", "jsonl", "markdown", "html", "review", "review_key"},
            )
            markdown = paths["markdown"].read_text(encoding="utf-8")
            self.assertIn("diagnostic failure", markdown)
            self.assertIn("0/32 successful; 0 attempted", markdown)
            jsonl = [
                json.loads(line)
                for line in paths["jsonl"].read_text(encoding="utf-8").splitlines()
            ]
            live = [item for item in jsonl if item["record_type"] == "live-run"]
            self.assertEqual(len(live), 1)
            self.assertEqual(live[0]["result"]["fatal_error"], "diagnostic failure")
            review = paths["review"].read_text(encoding="utf-8")
            self.assertNotIn("expected_related_ids", review)


if __name__ == "__main__":
    unittest.main()
