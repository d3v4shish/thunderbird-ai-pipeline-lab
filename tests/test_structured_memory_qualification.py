from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from tb_ai_lab.structured_memory import (
    MAX_EVENT_CANDIDATES,
    StructuredMemoryError,
    build_event_candidates,
    public_event_candidates,
    structured_selection_messages,
    validate_structured_selection,
)
from tb_ai_lab.structured_memory_qualification import (
    THREAD_SIZES,
    _case_result,
    _cap_sweep,
    _scale_case,
    _scale_result,
    evaluate_structured_memory_qualification,
    fixture_digest,
    qualification_fixture,
    qualification_contract_digest,
    qualification_live_plan,
    run_live_qualification,
)
from tb_ai_lab.contracts import Scope
from tb_ai_lab.related_email_rag import _template_catalog


class FakeQualificationClient:
    def __init__(self, *, malformed: bool = False) -> None:
        self.malformed = malformed
        self.calls = 0

    def chat(self, _model: str, messages: list[dict], **_options: object) -> dict:
        self.calls += 1
        if self.malformed:
            return {"message": {"content": "not json"}}
        payload = json.loads(messages[1]["content"])
        events = payload["host_event_candidates"]
        relations = [
            item
            for item in payload["host_relation_candidates"]
            if item["predicate"] == "confirms"
        ]
        selected_events = {item["candidate_id"] for item in events}
        selected_events.update(
            item["assertion_event_candidate_id"] for item in relations
        )
        assigned = next(
            (
                item
                for item in payload["offered_template_families"]
                if item.get("assigned_to_current")
            ),
            None,
        )
        value = {
            "selected_event_candidate_ids": sorted(selected_events),
            "selected_relation_candidate_ids": [
                item["candidate_id"] for item in relations
            ],
            "family_id": assigned["id"] if assigned else None,
            "selected_slot_candidate_ids": [],
        }
        return {
            "message": {"content": json.dumps(value)},
            "prompt_eval_count": 100,
            "eval_count": 20,
        }


class StructuredMemoryQualificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.documents, self.cases = qualification_fixture()
        self.scope = Scope("tenant-alpha", "mail")
        self.families, self.assignments, self.labels = _template_catalog(
            self.documents, self.scope
        )

    def _document(self, identifier: str):
        return next(item for item in self.documents if item.id == identifier)

    def test_fixture_is_frozen_synthetic_and_qualification_passes(self) -> None:
        self.assertEqual(
            fixture_digest(),
            "efc617918a8f390b049865d00352c21f8d29519da07a09fa943a9305c4da6489",
        )
        self.assertEqual(
            qualification_contract_digest(),
            "88be0fb5424ce0aab821fb31a749a6938fc179332b876526e30e78e92a663b3e",
        )
        self.assertTrue(all(item.metadata.get("synthetic") for item in self.documents))
        result = evaluate_structured_memory_qualification()
        self.assertTrue(result["hard_contract_pass"])
        self.assertEqual(result["aggregate"]["case_pass_rate"], 1.0)
        self.assertEqual(result["aggregate"]["scale_pass_rate"], 1.0)

    def test_durable_events_outlive_the_smaller_hint_schema(self) -> None:
        document = self._document("qual-late-event")
        events = build_event_candidates(document)
        self.assertEqual(len(events), 31)
        self.assertEqual(len(public_event_candidates(events)), MAX_EVENT_CANDIDATES)
        self.assertEqual(
            events[-1]["source_quote"], "The final launch decision is Cedar Harbor."
        )
        hidden = str(events[-1]["candidate_id"])
        value = {
            "selected_event_candidate_ids": [hidden],
            "selected_relation_candidate_ids": [],
            "family_id": None,
            "selected_slot_candidate_ids": [],
        }
        with self.assertRaisesRegex(StructuredMemoryError, "not host-offered"):
            validate_structured_selection(value, document, [], [], [], events, [])

    def test_quotes_signatures_and_paraphrased_instructions_are_not_events(self) -> None:
        expected_counts = {
            "qual-forwarded": 1,
            "qual-signature": 1,
            "qual-paraphrased-injection": 1,
        }
        for identifier, visible_count in expected_counts.items():
            with self.subTest(identifier=identifier):
                document = self._document(identifier)
                events = build_event_candidates(document)
                self.assertEqual(len(public_event_candidates(events)), visible_count)
                result = _case_result(
                    document,
                    [],
                    self.documents,
                    self.families,
                    self.assignments,
                    self.labels,
                )
                self.assertEqual(result["checks"]["quote_signature_isolation"], 1.0)

    def test_optional_slot_family_remains_selectable(self) -> None:
        result = _case_result(
            self._document("qual-template-optional"),
            [],
            self.documents,
            self.families,
            self.assignments,
            self.labels,
        )
        self.assertEqual(result["checks"]["family_accuracy"], 1.0)
        self.assertTrue(result["filtered_offer_ids"])
        self.assertEqual(result["validated"]["slots"], [])

    def test_explicit_old_reply_target_survives_all_thread_sizes(self) -> None:
        for size in THREAD_SIZES:
            with self.subTest(size=size):
                result = _scale_result(size)
                self.assertTrue(result["passed"])
                self.assertEqual(result["prompt_prior_count"], 24)
                self.assertEqual(result["relation_candidate_count"], 1)

    def test_candidate_cap_sweep_separates_durable_events_from_model_hints(self) -> None:
        sweep = _cap_sweep()
        self.assertEqual(
            [item["late_event_retained"] for item in sweep["event_caps"]],
            [False, True, True, True],
        )
        self.assertEqual(
            [item["visible_hint_count"] for item in sweep["event_caps"]],
            [24, 24, 24, 24],
        )
        self.assertEqual(
            [item["candidate_count"] for item in sweep["relation_caps"]],
            [64, 96, 96],
        )

    def test_prompt_includes_old_reference_but_never_all_500_records(self) -> None:
        document, prior, target = _scale_case(500)
        events = build_event_candidates(document)
        from tb_ai_lab.structured_memory import build_relation_candidates

        relations = build_relation_candidates(document, prior, events)
        messages, _schema = structured_selection_messages(
            document, prior, [], [], events, relations
        )
        payload = json.loads(messages[1]["content"])
        prior_ids = {
            item["document_id"]
            for item in payload["prior_structured_thread_memory"]
        }
        self.assertIn(target, prior_ids)
        self.assertEqual(len(prior_ids), 24)

        many_references = replace(
            document,
            metadata={
                **document.metadata,
                "references": [str(item["message_id"]) for item in prior],
            },
        )
        events = build_event_candidates(many_references)
        messages, _schema = structured_selection_messages(
            many_references, prior, [], [], events, []
        )
        bounded = json.loads(messages[1]["content"])[
            "prior_structured_thread_memory"
        ]
        self.assertEqual(len(bounded), 24)
        self.assertEqual(bounded[0]["document_id"], target)

    def test_live_three_repeat_gate_is_complete_stable_and_resumable(self) -> None:
        plan = qualification_live_plan(["mock"], 3)
        self.assertEqual(plan["total_calls"], 21)
        self.assertEqual(plan["generated_context_calls"], 0)
        with tempfile.TemporaryDirectory(prefix="tb-ai-qualification-") as temporary:
            cache = Path(temporary) / "checkpoint.json"
            client = FakeQualificationClient()
            result = run_live_qualification(
                client, "mock", "digest", 3, cache, resume=False
            )
            self.assertTrue(result["complete"])
            self.assertTrue(result["quality_gate_pass"])
            self.assertEqual(client.calls, 21)
            resumed_client = FakeQualificationClient()
            resumed = run_live_qualification(
                resumed_client, "mock", "digest", 3, cache
            )
            self.assertTrue(resumed["quality_gate_pass"])
            self.assertEqual(resumed_client.calls, 0)

    def test_live_gate_fails_closed_on_malformed_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="tb-ai-qualification-bad-") as temporary:
            result = run_live_qualification(
                FakeQualificationClient(malformed=True),
                "mock",
                "digest",
                1,
                Path(temporary) / "checkpoint.json",
                resume=False,
            )
        self.assertFalse(result["complete"])
        self.assertFalse(result["quality_gate_pass"])
        self.assertIn("valid JSON", result["fatal_error"])


if __name__ == "__main__":
    unittest.main()
