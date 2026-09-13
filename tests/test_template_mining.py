# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0.

from __future__ import annotations

import re
from dataclasses import replace
import json
import unittest

from tb_ai_lab.contracts import Document, Scope, content_digest
from tb_ai_lab.template_mining import (
    DrainTemplateMiner,
    analysis_text,
    assign_template,
    boilerplate_catalog,
    extract_template_slots,
    segment_mail_text,
    shingle_similarity,
    template_retrieval_text,
)
from tb_ai_lab.storage import Index
from tb_ai_lab.text import chunk_document
from tb_ai_lab.template_evaluation import (
    TEMPLATE_FIXTURE_VERSION,
    evaluate_template_mining,
    template_evaluation_fixture,
    template_fixture_digest,
)
from tb_ai_lab.template_scale import (
    TEMPLATE_SCALE_DIGESTS,
    TEMPLATE_SCALE_SIZES,
    evaluate_template_scale,
    template_scale_digest,
    template_scale_fixture,
)
from tb_ai_lab.template_live import (
    TEMPLATE_LIVE_PROMPT_VERSION,
    combine_template_live,
    evaluate_template_live_repeat,
    ledger_json_schema,
    ledger_messages,
    template_live_records,
    validate_ledger_output,
)


class TemplateMiningTests(unittest.TestCase):
    def test_matches_thunderbird_drain_subject_examples(self) -> None:
        miner = DrainTemplateMiner(Scope("tenant-alpha", "mail"), min_support=1)
        family = None
        for value in (
            "Invoice 4107 review",
            "Invoice 4108 review",
            "Invoice 4109 review",
        ):
            family = miner.observe(value)
        self.assertIsNotNone(family)
        self.assertEqual(family.template, "invoice <*> review")
        self.assertEqual(family.observations, 3)
        self.assertIsNotNone(miner.match("Invoice 9999 review"))
        self.assertRegex("Invoice 9999 review", re.compile(family.regex, re.I))

    def test_variable_length_gaps_and_normal_words_do_not_overmerge(self) -> None:
        miner = DrainTemplateMiner(Scope("tenant-alpha", "mail"), min_support=1)
        family = None
        for value in (
            "Invoice 4107 is ready for review",
            "Invoice INV-4108 for Northwind is ready for review",
            "Invoice 4109 from Contoso Europe is ready for review",
        ):
            family = miner.observe(value)
        self.assertTrue(family.template.startswith("invoice <*>"))
        security = miner.observe("Security-update available")
        customer = miner.observe("Customer-notice available")
        self.assertNotEqual(security.id, customer.id)

    def test_sender_scope_support_and_eviction_are_bounded(self) -> None:
        scope = Scope("tenant-alpha", "mail")
        miner = DrainTemplateMiner(scope, max_clusters=2, min_support=2)
        first = miner.observe("Invoice 4107 review", sender_domain="one.invalid")
        miner.observe("Invoice 4108 review", sender_domain="one.invalid")
        same_words = miner.observe("Invoice 4109 review", sender_domain="two.invalid")
        self.assertNotEqual(first.id, same_words.id)
        self.assertIsNotNone(
            miner.match("Invoice 4110 review", sender_domain="one.invalid")
        )
        self.assertIsNone(
            miner.match("Invoice 4110 review", sender_domain="two.invalid")
        )
        miner.observe("Security alert password changed", sender_domain="three.invalid")
        self.assertLessEqual(len(miner.families()), 2)

    def test_segmentation_preserves_exact_source_spans(self) -> None:
        source = (
            "Body fact INV-4107.\r\n"
            "-- \r\n"
            "Billing operations\r\n"
            "> quoted reply must not be analyzed\r\n"
        )
        segments = segment_mail_text(source)
        self.assertEqual([item.kind for item in segments], ["body", "signature", "quoted"])
        self.assertTrue(all(source[item.start : item.end] == item.text for item in segments))
        self.assertEqual(analysis_text(source), "Body fact INV-4107.")

    def test_slots_retain_exact_source_offsets(self) -> None:
        source = (
            "Invoice INV-4107 amount 225.00 INR is due 13/09/2026. "
            "Tracking ID TRK-99117 at https://example.invalid/t/TRK-99117"
        )
        slots = extract_template_slots(source)
        self.assertTrue(slots)
        self.assertTrue(all(source[item.start : item.end] == item.value for item in slots))
        slot_types = {item.slot_type for item in slots}
        self.assertTrue({"amount", "date", "order_id", "tracking_id", "url"} <= slot_types)

    def test_assignment_is_scope_and_source_digest_linked(self) -> None:
        scope = Scope("tenant-alpha", "mail")
        miner = DrainTemplateMiner(scope, min_support=2)
        for sequence in (4107, 4108):
            document = Document(
                id=f"invoice-{sequence}",
                tenant=scope.tenant,
                collection=scope.collection,
                title=f"Invoice {sequence} review",
                text=f"Invoice {sequence} amount INR 225.00 is ready for review.",
                metadata={"author": "Billing <billing@example.invalid>"},
            )
            miner.observe(
                f"{document.title}\n{document.text}",
                sender_domain="example.invalid",
                surface="mail",
            )
        candidate = Document(
            id="invoice-4109",
            tenant=scope.tenant,
            collection=scope.collection,
            title="Invoice 4109 review",
            text="Invoice 4109 amount INR 226.00 is ready for review.",
            metadata={"author": "Billing <billing@example.invalid>"},
        )
        assignment = assign_template(candidate, miner)
        self.assertIsNotNone(assignment)
        self.assertEqual(assignment.source_digest, content_digest(candidate.text))
        self.assertEqual(assignment.tenant, scope.tenant)
        self.assertTrue(
            all(candidate.text[item.start : item.end] == item.value for item in assignment.slots)
        )

    def test_boilerplate_removal_keeps_dynamic_slot_lines(self) -> None:
        documents = []
        labels = {}
        for sequence in range(1, 4):
            document = Document(
                id=f"invoice-{sequence}",
                tenant="tenant-alpha",
                collection="mail",
                title=f"Invoice {sequence}",
                text=(
                    f"Invoice INV-{sequence:04d} amount INR {200 + sequence}.00 is ready.\n"
                    "This mailbox is not monitored.\n"
                    "Unsubscribe from notices.\n"
                    "-- \nBilling"
                ),
            )
            documents.append(document)
            labels[document.id] = "invoice"
        catalog = boilerplate_catalog(documents, labels)
        retrieval = template_retrieval_text(documents[-1], catalog["invoice"])
        self.assertIn("INV-0003", retrieval)
        self.assertIn("INR 203.00", retrieval)
        self.assertNotIn("mailbox is not monitored", retrieval)
        self.assertNotIn("Unsubscribe", retrieval)
        self.assertNotIn("Billing", retrieval)

    def test_shingle_similarity_is_deterministic(self) -> None:
        left = "Invoice INV-4107 amount INR 225 is ready for review"
        right = "Invoice INV-4108 amount INR 226 is ready for review"
        unrelated = "Security alert requires a password reset"
        self.assertGreater(shingle_similarity(left, right), 0.7)
        self.assertEqual(shingle_similarity(left, right), shingle_similarity(left, right))
        self.assertLess(shingle_similarity(left, unrelated), 0.1)

    def test_frozen_template_fixture_is_split_synthetic_and_scope_separated(self) -> None:
        documents = template_evaluation_fixture()
        self.assertEqual(TEMPLATE_FIXTURE_VERSION, "synthetic-template-mail-v1")
        self.assertEqual(
            template_fixture_digest(),
            "c29125164aa129a94bfe26872aec6b264c81b7484ebb98f50ed9b843e6407741",
        )
        self.assertEqual(len(documents), 113)
        self.assertTrue(all(item.metadata.get("synthetic") is True for item in documents))
        self.assertEqual(sum(item.tenant == "tenant-beta" for item in documents), 1)
        recurring = [
            item
            for item in documents
            if item.tenant == "tenant-alpha"
            and item.metadata.get("expected_template_family")
        ]
        self.assertEqual(sum(item.metadata["split"] == "train" for item in recurring), 48)
        self.assertEqual(sum(item.metadata["split"] == "test" for item in recurring), 32)
        for document in recurring:
            for _, value in document.metadata["expected_slots"]:
                self.assertIn(value, document.text)

    def test_isolated_evaluation_exposes_controls_sweeps_and_hard_gates(self) -> None:
        report = evaluate_template_mining()
        controls = {item["method"]: item for item in report["lookup_controls"]}
        self.assertEqual(controls["exact-subject"]["metrics"]["recall"], 0.0)
        self.assertEqual(controls["subject-skeleton"]["metrics"]["f1"], 1.0)
        self.assertEqual(len(report["one_factor_sweeps"]), 11)
        self.assertTrue(report["hard_gate_pass"])
        self.assertTrue(report["selected_candidate"]["settings"]["sender_scoped"])
        self.assertEqual(
            report["boilerplate_reduction"]["metrics"]["dynamic_value_recall"],
            1.0,
        )
        lanes = {item["lane"]: item for item in report["retrieval_ablation"]}
        self.assertEqual(
            set(lanes),
            {
                "raw",
                "segmented",
                "subject-skeleton",
                "drain-family",
                "deduplicated",
                "combined",
            },
        )
        self.assertTrue(
            all(item["metrics"]["source_span_validity"] == 1.0 for item in lanes.values())
        )
        self.assertTrue(
            all(item["metrics"]["cross_scope_result_count"] == 0 for item in lanes.values())
        )
        self.assertEqual(lanes["combined"]["metrics"]["dynamic_value_recall"], 1.0)
        self.assertLess(
            lanes["deduplicated"]["metrics"]["indexed_characters"],
            lanes["raw"]["metrics"]["indexed_characters"],
        )
        self.assertEqual(report["retrieval_decision"]["selected_lane"], "deduplicated")
        self.assertTrue(report["gates"]["retrieval_no_recall_regression"])
        self.assertTrue(report["gates"]["deterministic_cost_gain"])

    def test_identifier_slot_hardening_rejects_structural_words(self) -> None:
        source = "Order operations. Shipment operations. Order ID ORD-5511."
        slots = extract_template_slots(source)
        identifiers = [item.value for item in slots if item.slot_type in {"order_id", "tracking_id"}]
        self.assertEqual(identifiers, ["Order ID ORD-5511"])

    def test_normalized_storage_round_trip_and_source_invalidation(self) -> None:
        scope = Scope("tenant-alpha", "mail")
        training = []
        miner = DrainTemplateMiner(scope, min_support=2)
        for sequence in (4107, 4108):
            document = Document(
                id=f"stored-{sequence}",
                tenant=scope.tenant,
                collection=scope.collection,
                title=f"Invoice {sequence} review",
                text=f"Invoice {sequence} amount {sequence}.00 INR is ready for review.",
                metadata={"author": "Billing <billing@example.invalid>"},
            )
            training.append(document)
            miner.observe(
                document.title,
                sender_domain="example.invalid",
                surface="subject",
            )
        candidate = Document(
            id="stored-4109",
            tenant=scope.tenant,
            collection=scope.collection,
            title="Invoice 4109 review",
            text="Invoice 4109 amount 4109.00 INR is ready for review.",
            metadata={"author": "Billing <billing@example.invalid>"},
        )
        assignment = assign_template(candidate, miner, surface="subject")
        family = next(item for item in miner.families() if item.id == assignment.family_id)
        with Index() as index:
            index.add_document(
                candidate,
                chunk_document(candidate, "structure-aware", 1200, 0, 16),
            )
            index.put_template_family(family)
            index.put_template_assignment(assignment)
            self.assertEqual(index.template_assignment(candidate.id, scope), assignment)

            changed = replace(candidate, text=candidate.text + " Changed source.")
            index.add_document(
                changed,
                chunk_document(changed, "structure-aware", 1200, 0, 16),
            )
            self.assertIsNone(index.template_assignment(candidate.id, scope))

            updated = assign_template(changed, miner, surface="subject")
            index.put_template_assignment(updated)
            index.delete_document(changed.id, scope)
            self.assertIsNone(index.template_assignment(changed.id, scope))
            self.assertIsNone(index.document(changed.id, scope))

    def test_template_scale_fixtures_are_frozen_and_scope_separated(self) -> None:
        for size in TEMPLATE_SCALE_SIZES:
            documents, facts = template_scale_fixture(size)
            self.assertEqual(template_scale_digest(size), TEMPLATE_SCALE_DIGESTS[size])
            self.assertEqual(len(facts), size)
            self.assertEqual(len(documents), size + 1)
            self.assertEqual(sum(item.tenant == "tenant-beta" for item in documents), 1)

    def test_template_scale_preserves_complete_ledgers_and_bounded_graph(self) -> None:
        report = evaluate_template_scale((500,))
        result = report["results"][0]
        metrics = result["metrics"]
        self.assertTrue(report["hard_gate_pass"])
        self.assertEqual(metrics["family"]["f1"], 1.0)
        self.assertEqual(metrics["fact_recall"], 1.0)
        self.assertEqual(metrics["direct_top_8_fact_recall"], 8 / 500)
        self.assertGreater(metrics["character_reduction"], 0.5)
        self.assertTrue(all(item["fact_recall"] == 1.0 for item in result["page_sweep"]))
        self.assertLessEqual(result["graph"]["max_neighbors"], 8)

    def test_template_live_fixture_prompt_and_validator_are_bounded(self) -> None:
        records = template_live_records("smoke")
        self.assertEqual(len(records), 32)
        self.assertTrue(all(item["source_valid"] for item in records))
        messages = ledger_messages(records, 1, 1)
        self.assertEqual(
            TEMPLATE_LIVE_PROMPT_VERSION, "template-ledger-render-v2-schema"
        )
        self.assertIn("untrusted_note", messages[1]["content"])
        schema = ledger_json_schema(records)
        self.assertEqual(schema["properties"]["facts"]["required"], [
            item["id"] for item in records
        ])
        self.assertNotIn("TS-", json.dumps(schema))
        expected = {item["id"]: item["value"] for item in records}
        valid = validate_ledger_output(json.dumps({"facts": expected}), records)
        self.assertTrue(valid["contract_valid"])
        poisoned = validate_ledger_output(
            json.dumps({"facts": {**expected, "S99999": "PRIVATE-TEMPLATE-SHADOW"}}),
            records,
        )
        self.assertFalse(poisoned["contract_valid"])
        self.assertEqual(
            poisoned["unsupported_facts"],
            {"S99999": "PRIVATE-TEMPLATE-SHADOW"},
        )

    def test_template_live_gate_counts_rejected_unsupported_output(self) -> None:
        class PoisonedClient:
            def chat(self, _model, messages, **_options):
                payload = json.loads(messages[1]["content"])
                facts = {
                    item["id"]: item["value"] for item in payload["records"]
                }
                facts["S99999"] = "PRIVATE-TEMPLATE-SHADOW"
                return {"message": {"content": json.dumps({"facts": facts})}}

        result = evaluate_template_live_repeat(
            PoisonedClient(), "poisoned", "smoke", 1
        )
        self.assertEqual(result["metrics"]["fact_recall"], 1.0)
        self.assertEqual(result["metrics"]["unsupported_fact_count"], 1)
        self.assertEqual(
            result["unsupported_facts"],
            {"S99999": "PRIVATE-TEMPLATE-SHADOW"},
        )

    def test_template_live_repeat_and_three_repeat_gate(self) -> None:
        class FakeClient:
            def chat(self, _model, messages, **_options):
                payload = json.loads(messages[1]["content"])
                return {
                    "message": {
                        "content": json.dumps(
                            {
                                "facts": {
                                    item["id"]: item["value"]
                                    for item in payload["records"]
                                }
                            }
                        )
                    },
                    "prompt_eval_count": 100,
                    "eval_count": 50,
                    "total_duration": 1_000_000,
                    "_lab_request_bytes": 1000,
                    "_lab_response_bytes": 500,
                }

        model = {
            "name": "fake-template-model",
            "digest": "a" * 64,
            "advertised_context": 16384,
        }
        runs = []
        for repeat in range(1, 4):
            result = evaluate_template_live_repeat(
                FakeClient(), model["name"], "smoke", repeat
            )
            self.assertEqual(result["metrics"]["fact_recall"], 1.0)
            runs.append({"model": model["name"], "result": result})
        report = combine_template_live("smoke", [model], None, runs, 3)
        self.assertTrue(report["hard_gate_pass"])
        self.assertEqual(report["ranked_passing_models"], [model["name"]])


if __name__ == "__main__":
    unittest.main()
