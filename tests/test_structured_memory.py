from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from tb_ai_lab.contracts import Scope
from tb_ai_lab.related_email_rag import (
    _template_catalog,
    related_email_fixture,
    template_offers,
)
from tb_ai_lab.slot_candidates import build_slot_candidates
from tb_ai_lab.structured_memory import (
    StructuredMemoryError,
    build_event_candidates,
    build_relation_candidates,
    evaluate_structured_memory_deterministic,
    filter_template_offers,
    public_event_candidates,
    public_memory_record,
    public_relation_candidates,
    run_live_structured_memory_screen,
    structured_memory_live_plan,
    structured_selection_messages,
    validate_structured_selection,
    write_structured_memory_report,
)


class FakeStructuredMemoryClient:
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
        events = payload["host_event_candidates"]
        relations = payload["host_relation_candidates"]
        slots = payload["host_slot_candidates"]
        offers = payload["offered_template_families"]
        selected_slots = []
        family_id = None
        if slots:
            selected = sorted(
                slots,
                key=lambda item: (
                    "[FACT" not in item["source_quote"],
                    item["candidate_id"],
                ),
            )[0]
            selected_slots = [selected["candidate_id"]]
            family_id = offers[0]["id"]
        response = {
            "selected_event_candidate_ids": [
                item["candidate_id"] for item in events
            ],
            "selected_relation_candidate_ids": [
                item["candidate_id"]
                for item in relations
                if item["predicate"] == "confirms"
            ],
            "family_id": family_id,
            "selected_slot_candidate_ids": selected_slots,
        }
        return {
            "message": {"content": json.dumps(response)},
            "prompt_eval_count": 100,
            "eval_count": 20,
        }


class StructuredMemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.documents, self.cases = related_email_fixture()
        self.scope = Scope("tenant-alpha", "mail")
        self.families, self.assignments, self.labels = _template_catalog(
            self.documents, self.scope
        )
        self.deterministic = evaluate_structured_memory_deterministic()

    def _document(self, identifier: str):
        return next(item for item in self.documents if item.id == identifier)

    def _validated(self, identifier: str) -> dict:
        return next(
            item["validated"]
            for item in self.deterministic["records"]
            if item["document_id"] == identifier
        )

    def _inputs(self, document, prior: list[dict]):
        offers = template_offers(
            document,
            self.documents,
            self.families,
            self.assignments,
            self.labels,
        )
        slots = build_slot_candidates(document, offers)
        offers = filter_template_offers(offers, slots)
        slots = build_slot_candidates(document, offers)
        events = build_event_candidates(document)
        relations = build_relation_candidates(document, prior, events)
        return offers, slots, events, relations

    def test_fixture_and_deterministic_contract_are_frozen(self) -> None:
        self.assertEqual(
            self.deterministic["fixture_digest"],
            "1b324bab5abdf6b2df4e243446ea15a41122f5fe94a073b99af1de180681d33a",
        )
        self.assertEqual(self.deterministic["document_count"], 8)
        self.assertTrue(self.deterministic["hard_contract_pass"])
        self.assertEqual(set(self.deterministic["quality"].values()), {1.0})
        self.assertTrue(self.deterministic["retrieval"]["localized_no_regression"])
        self.assertEqual(
            self.deterministic["retrieval"]["complete_related_recall"], 1.0
        )

    def test_event_candidates_are_source_bound_and_hide_instruction_context(self) -> None:
        document = self._document("rel-invoice-05")
        candidates = build_event_candidates(document)
        self.assertEqual(len(candidates), 3)
        self.assertEqual(len(public_event_candidates(candidates)), 2)
        rejected = [item for item in candidates if not item["eligible"]]
        self.assertEqual(len(rejected), 1)
        self.assertIn("Ignore all previous", rejected[0]["source_quote"])
        for item in candidates:
            self.assertEqual(
                document.text[item["start"] : item["end"]], item["source_quote"]
            )
        self.assertNotIn("start", public_event_candidates(candidates)[0])
        self.assertNotIn("end", public_event_candidates(candidates)[0])

    def test_relation_candidates_target_only_prior_same_thread_records(self) -> None:
        document = self._document("rel-invoice-04-reply")
        prior = [self._validated("rel-invoice-04")]
        _offers, _slots, events, relations = self._inputs(document, prior)
        self.assertEqual(len(relations), 1)
        self.assertEqual({item["target_document_id"] for item in relations}, {"rel-invoice-04"})
        self.assertIn("confirms", {item["predicate"] for item in relations})
        self.assertNotIn("start", public_relation_candidates(relations)[0])
        polluted = dict(prior[0])
        polluted["scope"] = {"tenant": "tenant-beta", "collection": "mail"}
        with self.assertRaisesRegex(StructuredMemoryError, "crossed scope"):
            build_relation_candidates(document, [polluted], events)
        wrong_thread = dict(prior[0])
        wrong_thread["thread_id"] = "OTHER-THREAD"
        with self.assertRaisesRegex(StructuredMemoryError, "crossed thread"):
            build_relation_candidates(document, [wrong_thread], events)
        future = dict(prior[0])
        future["timestamp"] = "2099-01-01T00:00:00Z"
        with self.assertRaisesRegex(StructuredMemoryError, "not chronological"):
            build_relation_candidates(document, [future], events)

    def test_prompt_and_schema_expose_only_closed_world_ids(self) -> None:
        document = self._document("rel-invoice-04-reply")
        prior = [self._validated("rel-invoice-04")]
        offers, slots, events, relations = self._inputs(document, prior)
        messages, schema = structured_selection_messages(
            document, prior, offers, slots, events, relations
        )
        payload = json.loads(messages[1]["content"])
        self.assertEqual(payload["current_email"]["source"], document.text)
        self.assertEqual(
            set(schema["required"]),
            {
                "selected_event_candidate_ids",
                "selected_relation_candidate_ids",
                "family_id",
                "selected_slot_candidate_ids",
            },
        )
        self.assertNotIn("summary", schema["properties"])
        self.assertNotIn("context", schema["properties"])
        self.assertNotIn("start", payload["host_event_candidates"][0])
        self.assertNotIn("end", payload["host_relation_candidates"][0])
        self.assertNotIn("source_digest", payload["prior_structured_thread_memory"][0])
        invoice = self._document("rel-invoice-04")
        invoice_inputs = self._inputs(invoice, [])
        _invoice_messages, invoice_schema = structured_selection_messages(
            invoice, [], *invoice_inputs
        )
        self.assertEqual(
            invoice_schema["properties"]["selected_slot_candidate_ids"]["maxItems"],
            1,
        )

    def test_validator_resolves_ids_and_rejects_unsupported_or_stale_selection(self) -> None:
        document = self._document("rel-invoice-05")
        offers, slots, events, relations = self._inputs(document, [])
        expected = next(
            item["selection"]
            for item in self.deterministic["records"]
            if item["document_id"] == document.id
        )
        accepted = validate_structured_selection(
            expected, document, [], offers, slots, events, relations
        )
        self.assertEqual(len(accepted["events"]), 2)
        self.assertEqual(accepted["slots"][0]["value"], "$550.00")
        invented = {**expected, "selected_event_candidate_ids": ["event-invented"]}
        with self.assertRaisesRegex(StructuredMemoryError, "not host-offered"):
            validate_structured_selection(
                invented, document, [], offers, slots, events, relations
            )
        duplicate = {
            **expected,
            "selected_event_candidate_ids": [
                expected["selected_event_candidate_ids"][0],
                expected["selected_event_candidate_ids"][0],
            ],
        }
        with self.assertRaisesRegex(StructuredMemoryError, "duplicate event"):
            validate_structured_selection(
                duplicate, document, [], offers, slots, events, relations
            )
        unsafe_id = next(item["candidate_id"] for item in events if not item["eligible"])
        unsafe = {**expected, "selected_event_candidate_ids": [unsafe_id]}
        with self.assertRaisesRegex(StructuredMemoryError, "not host-offered"):
            validate_structured_selection(
                unsafe, document, [], offers, slots, events, relations
            )
        edited = replace(document, text=document.text + "\nEdited.")
        with self.assertRaisesRegex(StructuredMemoryError, "stale"):
            validate_structured_selection(
                expected, edited, [], offers, slots, events, relations
            )

    def test_relation_requires_selected_assertion_event(self) -> None:
        document = self._document("rel-invoice-04-reply")
        prior = [self._validated("rel-invoice-04")]
        offers, slots, events, relations = self._inputs(document, prior)
        relation_id = next(
            item["candidate_id"]
            for item in relations
            if item["predicate"] == "confirms"
        )
        value = {
            "selected_event_candidate_ids": [],
            "selected_relation_candidate_ids": [relation_id],
            "family_id": None,
            "selected_slot_candidate_ids": [],
        }
        with self.assertRaisesRegex(StructuredMemoryError, "assertion event"):
            validate_structured_selection(
                value, document, prior, offers, slots, events, relations
            )
        confirms = next(
            item for item in relations if item["predicate"] == "confirms"
        )
        answers = {
            **confirms,
            "candidate_id": "relation-host-offered-second-predicate",
            "predicate": "answers",
        }
        duplicate_semantics = {
            **value,
            "selected_event_candidate_ids": [
                confirms["assertion_event_candidate_id"]
            ],
            "selected_relation_candidate_ids": [
                confirms["candidate_id"],
                answers["candidate_id"],
            ],
        }
        with self.assertRaisesRegex(StructuredMemoryError, "multiple relation predicates"):
            validate_structured_selection(
                duplicate_semantics,
                document,
                prior,
                offers,
                slots,
                events,
                relations + [answers],
            )

    def test_public_memory_is_host_validated_and_offset_free(self) -> None:
        record = public_memory_record(self._validated("rel-invoice-05"))
        self.assertNotIn("source_digest", record)
        self.assertNotIn("start", record["events"][0])
        self.assertFalse(
            any("Ignore all previous" in item["source_quote"] for item in record["events"])
        )
        reply = self._validated("rel-invoice-04-reply")
        self.assertEqual(reply["structural_relations"][0]["predicate"], "reply_to")
        self.assertEqual(
            reply["structural_relations"][0]["target_document_id"],
            "rel-invoice-04",
        )

    def test_live_fake_screen_is_complete_stable_and_resumable(self) -> None:
        plan = structured_memory_live_plan(["mock"], 1)
        self.assertEqual(plan["total_calls"], 8)
        self.assertEqual(plan["generated_context_calls"], 0)
        with tempfile.TemporaryDirectory(prefix="tb-ai-structured-memory-") as temporary:
            cache = Path(temporary) / "checkpoint.json"
            client = FakeStructuredMemoryClient()
            result = run_live_structured_memory_screen(
                client, "mock", "digest", self.documents, 1, cache
            )
            self.assertTrue(result["complete"])
            self.assertTrue(result["quality_gate_pass"])
            self.assertEqual(client.calls, 8)
            resumed_client = FakeStructuredMemoryClient()
            resumed = run_live_structured_memory_screen(
                resumed_client, "mock", "digest", self.documents, 1, cache
            )
            self.assertTrue(resumed["quality_gate_pass"])
            self.assertEqual(resumed_client.calls, 0)
            repeated = run_live_structured_memory_screen(
                FakeStructuredMemoryClient(),
                "mock",
                "digest",
                self.documents,
                3,
                Path(temporary) / "three-repeats.json",
            )
            self.assertTrue(repeated["quality_gate_pass"])
            self.assertEqual(repeated["summary"]["successful"], 24)

    def test_live_screen_fails_closed_on_malformed_output_and_cancellation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="tb-ai-structured-failure-") as temporary:
            malformed = run_live_structured_memory_screen(
                FakeStructuredMemoryClient(malformed=True),
                "bad",
                "digest",
                self.documents,
                1,
                Path(temporary) / "malformed.json",
            )
            self.assertFalse(malformed["complete"])
            self.assertIn("valid JSON", malformed["fatal_error"])
            cancelled = run_live_structured_memory_screen(
                FakeStructuredMemoryClient(cancel=True),
                "cancel",
                "digest",
                self.documents,
                1,
                Path(temporary) / "cancelled.json",
            )
            self.assertFalse(cancelled["complete"])
            self.assertTrue(cancelled["cancelled"])

    def test_report_preserves_live_failure_in_all_formats(self) -> None:
        report = evaluate_structured_memory_deterministic()
        report["live"] = {
            "requested": True,
            "dry_run": False,
            "plan": structured_memory_live_plan(["mock"], 1),
            "runs": [
                {
                    "model": "mock",
                    "result": {
                        "complete": False,
                        "quality_gate_pass": False,
                        "fatal_error": "diagnostic failure",
                        "records": [],
                        "summary": {},
                    },
                }
            ],
        }
        with tempfile.TemporaryDirectory(prefix="tb-ai-structured-report-") as temporary:
            paths = write_structured_memory_report(Path(temporary), "structured", report)
            self.assertEqual(set(paths), {"json", "jsonl", "markdown", "html"})
            self.assertIn(
                "diagnostic failure", paths["markdown"].read_text(encoding="utf-8")
            )
            self.assertIn(
                "diagnostic failure", paths["html"].read_text(encoding="utf-8")
            )


if __name__ == "__main__":
    unittest.main()
