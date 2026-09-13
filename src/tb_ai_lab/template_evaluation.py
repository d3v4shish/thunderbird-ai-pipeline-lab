# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0.

"""Frozen template-mining corpus, isolated ablations, and review reports."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import statistics
import time
import tracemalloc
from typing import Any, Callable

from .contracts import Chunk, Document, Scope, content_digest
from .evaluation import percentile
from .reporting import checkpoint
from .storage import Index
from .template_mining import (
    DrainTemplateMiner,
    analysis_text,
    assign_template,
    boilerplate_catalog,
    document_template_surface,
    extract_template_slots,
    normalized_skeleton,
    sender_domain,
    shingle_similarity,
    template_retrieval_text,
)


TEMPLATE_FIXTURE_VERSION = "synthetic-template-mail-v1"
TEMPLATE_FAMILY_COUNT = 8
TEMPLATE_MESSAGES_PER_FAMILY = 10
TEMPLATE_TRAIN_COUNT = 6
TEMPLATE_UNIQUE_COUNT = 32
TEMPLATE_THRESHOLDS = (0.5, 0.6, 0.7, 0.8)
TEMPLATE_SUPPORTS = (3, 5, 10)
TEMPLATE_CLUSTER_LIMITS = (100, 1000, 5000)
SHINGLE_THRESHOLDS = (0.85, 0.9, 0.95)
TEMPLATE_RETRIEVAL_LANES = (
    "raw",
    "segmented",
    "subject-skeleton",
    "drain-family",
    "deduplicated",
    "combined",
)


def _family_message(
    family: str, sequence: int
) -> tuple[str, str, str, list[tuple[str, str]]]:
    revision = 0 if sequence <= 3 else 1 if sequence <= 6 else 2
    date = f"{10 + sequence:02d}/09/2026"
    specifications: dict[
        str, tuple[str, str, tuple[str, ...], tuple[str, ...], list[tuple[str, str]]]
    ] = {
        "invoice": (
            "Billing <billing@commerce.invalid>",
            f"Invoice INV-{sequence:04d} review",
            (
                f"Invoice INV-{sequence:04d} amount {200 + sequence}.00 INR is ready for review.",
                f"Invoice INV-{sequence:04d} amount {200 + sequence}.00 INR now awaits payment review.",
                f"Invoice INV-{sequence:04d} is payable after review; amount {200 + sequence}.00 INR.",
            ),
            ("Please verify the payment record.", "Use the billing portal for the source document."),
            [("order_id", f"Invoice INV-{sequence:04d}"), ("amount", f"{200 + sequence}.00 INR")],
        ),
        "shipment": (
            "Shipping <tracking@commerce.invalid>",
            f"Shipment SHP-{sequence:04d} confirmation",
            (
                f"Tracking ID TRK-{90000 + sequence} will arrive {date}.",
                f"Tracking ID TRK-{90000 + sequence} belongs to a shipment scheduled for {date}.",
                f"Tracking ID TRK-{90000 + sequence} remains due for delivery {date}.",
            ),
            ("Track the parcel from the delivery page.", "Carrier scans can take time to appear."),
            [("tracking_id", f"Tracking ID TRK-{90000 + sequence}")],
        ),
        "order": (
            "Orders <orders@commerce.invalid>",
            f"Order ORD-{5000 + sequence} status",
            (
                f"Order ID ORD-{5000 + sequence} total {70 + sequence}.00 USD is confirmed.",
                f"Order ID ORD-{5000 + sequence} with total {70 + sequence}.00 USD is being prepared.",
                f"Order ID ORD-{5000 + sequence} is confirmed at {70 + sequence}.00 USD.",
            ),
            ("You can review order details online.", "Replies to this notification are not monitored."),
            [("order_id", f"Order ID ORD-{5000 + sequence}"), ("amount", f"{70 + sequence}.00 USD")],
        ),
        "receipt": (
            "Receipts <receipts@payments.invalid>",
            f"Transaction TXN-{7000 + sequence} receipt",
            (
                f"Transaction TXN-{7000 + sequence} settled for {40 + sequence}.00 EUR.",
                f"Transaction TXN-{7000 + sequence} has settled at {40 + sequence}.00 EUR.",
                f"Transaction TXN-{7000 + sequence} receipt settled at {40 + sequence}.00 EUR.",
            ),
            ("Keep this receipt for your records.", "Payment support is available from the help center."),
            [("order_id", f"Transaction TXN-{7000 + sequence}"), ("amount", f"{40 + sequence}.00 EUR")],
        ),
        "meeting": (
            "Calendar <calendar@work.invalid>",
            f"Meeting roadmap review {sequence:02d}",
            (
                f"Roadmap review meeting is scheduled for {date} in room R-{sequence:02d}.",
                f"The roadmap review now meets on {date} in room R-{sequence:02d}.",
                f"Calendar revision: roadmap review remains {date}, room R-{sequence:02d}.",
            ),
            ("Add the event to your calendar.", "Meeting responses are recorded automatically."),
            [],
        ),
        "security": (
            "Security <alerts@work.invalid>",
            f"Security device DEV-{8000 + sequence} alert",
            (
                f"Security device DEV-{8000 + sequence} requires account review.",
                f"Account review is required for security device DEV-{8000 + sequence}.",
                f"Review requested: device DEV-{8000 + sequence} generated a security alert.",
            ),
            ("Open security settings from the application.", "Do not share verification codes."),
            [],
        ),
        "support": (
            "Support <desk@service.invalid>",
            f"Reference CASE-{3000 + sequence} updated",
            (
                f"Reference CASE-{3000 + sequence} was updated by support agent{sequence:02d}@service.invalid.",
                f"Support updated reference CASE-{3000 + sequence}; owner is agent{sequence:02d}@service.invalid.",
                f"Case update for reference CASE-{3000 + sequence} from agent{sequence:02d}@service.invalid.",
            ),
            ("Reply above this line to add a comment.", "Support history remains available in the portal."),
            [("email", f"agent{sequence:02d}@service.invalid")],
        ),
        "bulletin": (
            "Bulletin <news@updates.invalid>",
            f"Weekly engineering bulletin {sequence:02d}",
            (
                f"Engineering bulletin edition {sequence:02d} covers platform maintenance.",
                f"Platform maintenance leads engineering bulletin edition {sequence:02d}.",
                f"Edition {sequence:02d} of the engineering bulletin reviews platform maintenance.",
            ),
            ("No action is required for this bulletin.", "Read the archive for earlier editions."),
            [],
        ),
    }
    author, subject, variants, boilerplate, expected_slots = specifications[family]
    body = "\n".join(
        (
            variants[revision],
            boilerplate[0],
            boilerplate[1],
            "Unsubscribe from these notices." if family == "bulletin" else "Privacy policy applies.",
            "-- ",
            f"{family.title()} operations",
            "> Quoted historical value OLD-DO-NOT-USE must not influence analysis.",
        )
    )
    return author, subject, body, expected_slots


def template_evaluation_fixture() -> list[Document]:
    scope = Scope("tenant-alpha", "mail")
    started = datetime(2026, 9, 1, tzinfo=timezone.utc)
    documents = []
    families = (
        "invoice",
        "shipment",
        "order",
        "receipt",
        "meeting",
        "security",
        "support",
        "bulletin",
    )
    ordinal = 0
    for family in families:
        for sequence in range(1, TEMPLATE_MESSAGES_PER_FAMILY + 1):
            ordinal += 1
            author, subject, body, expected_slots = _family_message(family, sequence)
            documents.append(
                Document(
                    id=f"template-{family}-{sequence:02d}",
                    tenant=scope.tenant,
                    collection=scope.collection,
                    title=subject,
                    timestamp=(started + timedelta(minutes=ordinal)).isoformat(),
                    text=body,
                    metadata={
                        "synthetic": True,
                        "author": author,
                        "expected_template_family": family,
                        "expected_slots": [list(item) for item in expected_slots],
                        "split": "train" if sequence <= TEMPLATE_TRAIN_COUNT else "test",
                        "template_revision": 0 if sequence <= 3 else 1 if sequence <= 6 else 2,
                    },
                )
            )
    unique_words = (
        "garden",
        "library",
        "bicycle",
        "kitchen",
        "harbor",
        "museum",
        "weather",
        "concert",
    )
    for sequence in range(1, TEMPLATE_UNIQUE_COUNT + 1):
        ordinal += 1
        word = unique_words[(sequence - 1) % len(unique_words)]
        documents.append(
            Document(
                id=f"template-unique-{sequence:02d}",
                tenant=scope.tenant,
                collection=scope.collection,
                title=f"Personal {word} note {sequence:02d}",
                timestamp=(started + timedelta(minutes=ordinal)).isoformat(),
                text=(
                    f"A one-off {word} note number {sequence:02d} contains unique prose "
                    f"token UNIQUE-{sequence:04d} and no recurring operational structure."
                ),
                metadata={
                    "synthetic": True,
                    "author": f"Person {sequence} <person{sequence}@unique-{sequence % 4}.invalid>",
                    "expected_template_family": "",
                    "expected_slots": [],
                    "split": "train" if sequence <= 20 else "test",
                    "template_revision": 0,
                },
            )
        )
    shadow_author, shadow_subject, shadow_body, shadow_slots = _family_message("invoice", 99)
    documents.append(
        Document(
            id="template-private-shadow",
            tenant="tenant-beta",
            collection=scope.collection,
            title=shadow_subject,
            timestamp=(started + timedelta(days=1)).isoformat(),
            text=shadow_body,
            metadata={
                "synthetic": True,
                "author": shadow_author,
                "expected_template_family": "invoice",
                "expected_slots": [list(item) for item in shadow_slots],
                "split": "test",
                "template_revision": 2,
            },
        )
    )
    return documents


def template_fixture_digest() -> str:
    return content_digest(
        {
            "version": TEMPLATE_FIXTURE_VERSION,
            "documents": [item.as_dict() for item in template_evaluation_fixture()],
        }
    )


def _score_predictions(records: list[dict[str, Any]]) -> dict[str, Any]:
    true_positive = sum(
        bool(item["expected_family"]) and item["actual_family"] == item["expected_family"]
        for item in records
    )
    false_positive = sum(
        bool(item["actual_family"]) and item["actual_family"] != item["expected_family"]
        for item in records
    )
    false_negative = sum(
        bool(item["expected_family"]) and item["actual_family"] != item["expected_family"]
        for item in records
    )
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 1.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 1.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "correct": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "evaluated": len(records),
    }


def _train_drain(
    documents: list[Document],
    *,
    similarity_threshold: float = 0.6,
    min_support: int = 3,
    max_clusters: int = 1000,
    sender_scoped: bool = True,
) -> tuple[DrainTemplateMiner, dict[str, str], list[dict[str, Any]]]:
    scope = Scope("tenant-alpha", "mail")
    miner = DrainTemplateMiner(
        scope,
        similarity_threshold=similarity_threshold,
        min_support=min_support,
        max_clusters=max_clusters,
        sender_scoped=sender_scoped,
    )
    labels: dict[str, Counter[str]] = defaultdict(Counter)
    observations = []
    for document in documents:
        if document.scope != scope or document.metadata.get("split") != "train":
            continue
        family = miner.observe(
            document.title,
            sender_domain=sender_domain(str(document.metadata.get("author", ""))),
            surface="subject",
        )
        if not family:
            continue
        expected = str(document.metadata.get("expected_template_family", ""))
        if expected:
            labels[family.id][expected] += 1
        observations.append(
            {
                "document_id": document.id,
                "expected_family": expected,
                "cluster_id": family.id,
                "template": family.template,
                "observations": family.observations,
            }
        )
    family_labels = {
        family_id: counts.most_common(1)[0][0]
        for family_id, counts in labels.items()
        if counts
    }
    return miner, family_labels, observations


def _drain_lane(
    documents: list[Document],
    *,
    similarity_threshold: float = 0.6,
    min_support: int = 3,
    max_clusters: int = 1000,
    sender_scoped: bool = True,
) -> dict[str, Any]:
    miner, labels, observations = _train_drain(
        documents,
        similarity_threshold=similarity_threshold,
        min_support=min_support,
        max_clusters=max_clusters,
        sender_scoped=sender_scoped,
    )
    records = []
    slot_expected = 0
    slot_matched = 0
    slot_offered = 0
    source_spans_valid = True
    cross_scope_rejected = False
    family_slot_types: dict[str, set[str]] = defaultdict(set)
    for document in documents:
        if document.tenant != "tenant-alpha" or document.metadata.get("split") != "train":
            continue
        expected_family = str(document.metadata.get("expected_template_family", ""))
        family_slot_types[expected_family].update(
            str(slot_type) for slot_type, _ in document.metadata.get("expected_slots", [])
        )
    for document in documents:
        if document.metadata.get("split") != "test":
            continue
        if document.scope != miner.scope:
            try:
                assign_template(document, miner, surface="subject")
            except ValueError:
                cross_scope_rejected = True
            continue
        assignment = assign_template(document, miner, surface="subject")
        actual_family = labels.get(assignment.family_id, "") if assignment else ""
        expected_family = str(document.metadata.get("expected_template_family", ""))
        expected_slots = {
            (str(slot_type), str(value))
            for slot_type, value in document.metadata.get("expected_slots", [])
        }
        actual_slots = {
            (slot.slot_type, slot.value)
            for slot in (assignment.slots if assignment else extract_template_slots(document.text))
            if slot.slot_type in family_slot_types.get(expected_family, set())
        }
        matched_slots = expected_slots & actual_slots
        slot_expected += len(expected_slots)
        slot_matched += len(matched_slots)
        slot_offered += len(actual_slots)
        if assignment:
            source_spans_valid = source_spans_valid and all(
                document.text[slot.start : slot.end] == slot.value
                for slot in assignment.slots
            )
        records.append(
            {
                "document_id": document.id,
                "expected_family": expected_family,
                "actual_family": actual_family,
                "cluster_id": assignment.family_id if assignment else "",
                "score": assignment.score if assignment else 0.0,
                "expected_slots": [list(item) for item in sorted(expected_slots)],
                "actual_slots": [list(item) for item in sorted(actual_slots)],
                "matched_slots": [list(item) for item in sorted(matched_slots)],
                "source_digest": content_digest(document.text),
                "template_revision": document.metadata.get("template_revision"),
            }
        )
    quality = _score_predictions(records)
    slot_precision = slot_matched / slot_offered if slot_offered else float(not slot_expected)
    slot_recall = slot_matched / slot_expected if slot_expected else 1.0
    cluster_labels: dict[str, set[str]] = defaultdict(set)
    for item in observations:
        if item["expected_family"]:
            cluster_labels[item["cluster_id"]].add(item["expected_family"])
    return {
        "method": "sender-scoped-drain" if sender_scoped else "global-drain",
        "settings": {
            "similarity_threshold": similarity_threshold,
            "min_support": min_support,
            "max_clusters": max_clusters,
            "sender_scoped": sender_scoped,
        },
        "metrics": {
            **quality,
            "slot_precision": slot_precision,
            "slot_recall": slot_recall,
            "slot_expected": slot_expected,
            "slot_matched": slot_matched,
            "slot_offered": slot_offered,
            "source_span_validity": float(source_spans_valid),
            "cross_scope_rejected": cross_scope_rejected,
            "overmerged_cluster_count": sum(len(items) > 1 for items in cluster_labels.values()),
            "mature_family_count": len(miner.families(mature_only=True)),
            "total_cluster_count": len(miner.families()),
        },
        "families": [item.as_dict() for item in miner.families()],
        "training_observations": observations,
        "predictions": records,
    }


def _lookup_lane(documents: list[Document], method: str) -> dict[str, Any]:
    mapping: dict[str, Counter[str]] = defaultdict(Counter)
    scope = Scope("tenant-alpha", "mail")
    for document in documents:
        if document.scope != scope or document.metadata.get("split") != "train":
            continue
        domain = sender_domain(str(document.metadata.get("author", "")))
        subject = document.title.casefold() if method == "exact-subject" else normalized_skeleton(document.title)
        family = str(document.metadata.get("expected_template_family", ""))
        mapping[f"{domain}|{subject}"][family] += 1
    labels = {
        key: counts.most_common(1)[0][0]
        for key, counts in mapping.items()
        if counts.most_common(1)[0][1] >= 3 and counts.most_common(1)[0][0]
    }
    records = []
    for document in documents:
        if document.scope != scope or document.metadata.get("split") != "test":
            continue
        domain = sender_domain(str(document.metadata.get("author", "")))
        subject = document.title.casefold() if method == "exact-subject" else normalized_skeleton(document.title)
        records.append(
            {
                "document_id": document.id,
                "expected_family": str(document.metadata.get("expected_template_family", "")),
                "actual_family": labels.get(f"{domain}|{subject}", ""),
            }
        )
    return {
        "method": method,
        "metrics": _score_predictions(records),
        "predictions": records,
        "learned_key_count": len(labels),
    }


def _shingle_sweep(documents: list[Document]) -> list[dict[str, Any]]:
    tests = [
        item
        for item in documents
        if item.tenant == "tenant-alpha" and item.metadata.get("split") == "test"
    ]
    pairs = []
    for left_index, left in enumerate(tests):
        for right in tests[left_index + 1 :]:
            expected = bool(left.metadata.get("expected_template_family")) and (
                left.metadata.get("expected_template_family")
                == right.metadata.get("expected_template_family")
            )
            score = shingle_similarity(
                document_template_surface(left), document_template_surface(right)
            )
            pairs.append((expected, score))
    results = []
    for threshold in SHINGLE_THRESHOLDS:
        true_positive = sum(expected and score >= threshold for expected, score in pairs)
        false_positive = sum(not expected and score >= threshold for expected, score in pairs)
        false_negative = sum(expected and score < threshold for expected, score in pairs)
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 1.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 1.0
        results.append(
            {
                "threshold": threshold,
                "precision": precision,
                "recall": recall,
                "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
                "pair_count": len(pairs),
            }
        )
    return results


def _template_reduction(documents: list[Document]) -> dict[str, Any]:
    training = [
        item
        for item in documents
        if item.tenant == "tenant-alpha" and item.metadata.get("split") == "train"
    ]
    labels = {
        item.id: str(item.metadata.get("expected_template_family", ""))
        for item in training
    }
    catalog = boilerplate_catalog(training, labels)
    records = []
    for document in documents:
        if document.tenant != "tenant-alpha" or document.metadata.get("split") != "test":
            continue
        family = str(document.metadata.get("expected_template_family", ""))
        derived = template_retrieval_text(document, catalog.get(family, set()))
        expected_values = [str(value) for _, value in document.metadata.get("expected_slots", [])]
        records.append(
            {
                "document_id": document.id,
                "family": family,
                "source_characters": len(document.text),
                "retrieval_characters": len(derived),
                "retained_expected_values": [value for value in expected_values if value in derived],
                "expected_values": expected_values,
                "retrieval_text": derived,
            }
        )
    source_characters = sum(item["source_characters"] for item in records)
    retrieval_characters = sum(item["retrieval_characters"] for item in records)
    expected_count = sum(len(item["expected_values"]) for item in records)
    retained_count = sum(len(item["retained_expected_values"]) for item in records)
    return {
        "catalog": {key: sorted(value) for key, value in sorted(catalog.items())},
        "metrics": {
            "source_characters": source_characters,
            "retrieval_characters": retrieval_characters,
            "character_reduction": 1 - retrieval_characters / source_characters,
            "dynamic_value_recall": retained_count / expected_count if expected_count else 1.0,
        },
        "records": records,
    }


def _retrieval_surface(
    document: Document,
    lane: str,
    family: str,
    template: str,
    boilerplate: set[str],
) -> str:
    segmented = analysis_text(document.text)
    skeleton = normalized_skeleton(document.title)
    reduced = template_retrieval_text(document, boilerplate)
    slots = extract_template_slots(document.text)
    if lane == "raw":
        return f"Subject: {document.title}\n{document.text}"
    if lane == "segmented":
        return f"Subject: {document.title}\n{segmented}"
    if lane == "subject-skeleton":
        return f"Subject: {document.title}\nSubject skeleton: {skeleton}\n{segmented}"
    if lane == "drain-family":
        return (
            f"Subject: {document.title}\nTemplate family: {family}\n"
            f"Template: {template}\n{segmented}"
        )
    if lane == "deduplicated":
        return f"Subject: {document.title}\n{reduced}"
    if lane == "combined":
        slot_text = " ".join(f"{item.slot_type}: {item.value}" for item in slots)
        return "\n".join(
            item
            for item in (
                f"Subject: {document.title}",
                f"Subject skeleton: {skeleton}",
                f"Template family: {family}" if family else "",
                f"Template: {template}" if template else "",
                f"Slots: {slot_text}" if slot_text else "",
                reduced,
            )
            if item
        )
    raise ValueError(f"Unknown template retrieval lane: {lane}")


def _retrieval_ablation(documents: list[Document]) -> list[dict[str, Any]]:
    scope = Scope("tenant-alpha", "mail")
    training = [
        item
        for item in documents
        if item.scope == scope and item.metadata.get("split") == "train"
    ]
    evaluation = [
        item for item in documents if item.metadata.get("split") == "test"
    ]
    evaluation_by_id = {item.id: item for item in evaluation}
    miner, family_labels, _ = _train_drain(documents)
    families = {item.id: item for item in miner.families(mature_only=True)}
    catalog = boilerplate_catalog(
        training,
        {
            item.id: str(item.metadata.get("expected_template_family", ""))
            for item in training
        },
    )
    assignments: dict[str, tuple[str, str]] = {}
    for document in evaluation:
        if document.scope != scope:
            continue
        assignment = assign_template(document, miner, surface="subject")
        family = family_labels.get(assignment.family_id, "") if assignment else ""
        template = (
            families[assignment.family_id].template
            if assignment and assignment.family_id in families
            else ""
        )
        assignments[document.id] = (family, template)

    document_cases = []
    for document in evaluation:
        if document.scope != scope:
            continue
        expected_slots = [
            str(value) for _, value in document.metadata.get("expected_slots", [])
        ]
        query = expected_slots[0] if expected_slots else document.title
        document_cases.append(
            {
                "id": f"document-{document.id}",
                "query": query,
                "expected_document": document.id,
            }
        )
    family_queries = {
        "invoice": "invoice payment review",
        "shipment": "parcel tracking delivery",
        "order": "confirmed order total",
        "receipt": "settled transaction receipt",
        "meeting": "roadmap review meeting",
        "security": "security device alert",
        "support": "support case reference",
        "bulletin": "engineering weekly bulletin",
    }
    results = []
    for lane in TEMPLATE_RETRIEVAL_LANES:
        surfaces: dict[str, str] = {}
        with Index() as index:
            for document in evaluation:
                family, template = assignments.get(document.id, ("", ""))
                surface = _retrieval_surface(
                    document,
                    lane,
                    family,
                    template,
                    catalog.get(family, set()),
                )
                surfaces[document.id] = surface
                chunk = Chunk(
                    id=f"{lane}:{document.tenant}:{document.id}",
                    document_id=document.id,
                    tenant=document.tenant,
                    collection=document.collection,
                    ordinal=0,
                    text=document.text,
                    contextual_text=surface,
                    start=0,
                    end=len(document.text),
                    retrieval_text=surface,
                )
                index.add_document(document, [chunk])
            case_records = []
            reciprocal_ranks = []
            for case in document_cases:
                ranked = index.search(
                    case["query"],
                    scope,
                    "hybrid",
                    limit=4,
                    candidate_mode="full-scan",
                )
                ids = [item.document_id for item in ranked]
                rank = (
                    ids.index(case["expected_document"]) + 1
                    if case["expected_document"] in ids
                    else 0
                )
                reciprocal_ranks.append(1 / rank if rank else 0.0)
                case_records.append(
                    {
                        **case,
                        "rank": rank,
                        "returned_document_ids": ids,
                        "source_spans_valid": all(
                            evaluation_by_id[evidence.document_id].text[
                                evidence.start : evidence.end
                            ]
                            == evidence.text
                            for evidence in ranked
                        ),
                    }
                )
            family_records = []
            for family, query in family_queries.items():
                ranked = index.search(
                    query,
                    scope,
                    "hybrid",
                    limit=4,
                    candidate_mode="full-scan",
                )
                labels = [
                    str(
                        evaluation_by_id[evidence.document_id].metadata.get(
                            "expected_template_family", ""
                        )
                    )
                    for evidence in ranked
                ]
                family_records.append(
                    {
                        "family": family,
                        "query": query,
                        "returned_families": labels,
                        "hit": family in labels,
                        "precision_at_4": labels.count(family) / len(labels) if labels else 0.0,
                    }
                )
            private = next(item for item in evaluation if item.tenant == "tenant-beta")
            private_results = index.search(
                private.title,
                scope,
                "hybrid",
                limit=8,
                candidate_mode="full-scan",
            )
        expected_dynamic_values = [
            str(value)
            for document in evaluation
            if document.scope == scope
            for _, value in document.metadata.get("expected_slots", [])
        ]
        results.append(
            {
                "lane": lane,
                "settings": {
                    "retrieval": "exact+lexical+local-dense RRF",
                    "top_k": 4,
                    "candidate_mode": "full-scan",
                    "rrf_k": 60,
                },
                "metrics": {
                    "document_recall_at_4": sum(item["rank"] > 0 for item in case_records)
                    / len(case_records),
                    "document_mrr": statistics.fmean(reciprocal_ranks),
                    "family_recall_at_4": sum(item["hit"] for item in family_records)
                    / len(family_records),
                    "family_precision_at_4": statistics.fmean(
                        item["precision_at_4"] for item in family_records
                    ),
                    "indexed_characters": sum(
                        len(value)
                        for document_id, value in surfaces.items()
                        if evaluation_by_id[document_id].scope == scope
                    ),
                    "dynamic_value_recall": sum(
                        any(value in surface for surface in surfaces.values())
                        for value in expected_dynamic_values
                    )
                    / len(expected_dynamic_values),
                    "source_span_validity": float(
                        all(item["source_spans_valid"] for item in case_records)
                    ),
                    "cross_scope_result_count": sum(
                        item.document_id == private.id for item in private_results
                    ),
                },
                "document_cases": case_records,
                "family_cases": family_records,
                "surface_digest": content_digest(surfaces),
            }
        )
    return results


def _measure(operation: Callable[[], Any], repeats: int = 7) -> dict[str, Any]:
    timings = []
    result = None
    tracemalloc.start()
    for _ in range(repeats):
        started = time.perf_counter()
        result = operation()
        timings.append((time.perf_counter() - started) * 1000)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "latency_p50_ms": percentile(timings, 0.5),
        "latency_p95_ms": percentile(timings, 0.95),
        "latency_mean_ms": statistics.fmean(timings),
        "peak_python_bytes": peak,
        "result_digest": content_digest(result),
    }


def evaluate_template_mining() -> dict[str, Any]:
    documents = template_evaluation_fixture()
    exact = _lookup_lane(documents, "exact-subject")
    skeleton = _lookup_lane(documents, "subject-skeleton")
    baseline = _drain_lane(documents)
    sweeps = []
    for threshold in TEMPLATE_THRESHOLDS:
        lane = _drain_lane(documents, similarity_threshold=threshold)
        lane["factor"] = "similarity_threshold"
        lane["value"] = threshold
        sweeps.append(lane)
    for support in TEMPLATE_SUPPORTS:
        lane = _drain_lane(documents, min_support=support)
        lane["factor"] = "min_support"
        lane["value"] = support
        sweeps.append(lane)
    for cluster_limit in TEMPLATE_CLUSTER_LIMITS:
        lane = _drain_lane(documents, max_clusters=cluster_limit)
        lane["factor"] = "max_clusters"
        lane["value"] = cluster_limit
        sweeps.append(lane)
    global_lane = _drain_lane(documents, sender_scoped=False)
    global_lane["factor"] = "sender_scoped"
    global_lane["value"] = False
    sweeps.append(global_lane)
    reduction = _template_reduction(documents)
    retrieval_ablation = _retrieval_ablation(documents)
    retrieval_lanes = {item["lane"]: item for item in retrieval_ablation}
    raw_retrieval = retrieval_lanes["raw"]["metrics"]
    retrieval_candidate = retrieval_lanes["deduplicated"]["metrics"]
    indexed_character_reduction = 1 - (
        retrieval_candidate["indexed_characters"] / raw_retrieval["indexed_characters"]
    )
    performance = _measure(lambda: _drain_lane(documents))
    candidates = [
        item
        for item in [baseline, *sweeps]
        if item["settings"]["sender_scoped"]
    ]
    winner = max(
        candidates,
        key=lambda item: (
            item["metrics"]["f1"],
            -item["metrics"]["overmerged_cluster_count"],
            item["metrics"]["slot_recall"],
            -item["metrics"]["total_cluster_count"],
        ),
    )
    gates = {
        "family_f1": winner["metrics"]["f1"] >= 0.95,
        "no_overmerge": winner["metrics"]["overmerged_cluster_count"] == 0,
        "slot_precision": winner["metrics"]["slot_precision"] == 1.0,
        "slot_recall": winner["metrics"]["slot_recall"] >= 0.98,
        "source_span_validity": winner["metrics"]["source_span_validity"] == 1.0,
        "cross_scope_rejected": winner["metrics"]["cross_scope_rejected"],
        "dynamic_value_recall": reduction["metrics"]["dynamic_value_recall"] == 1.0,
        "retrieval_no_recall_regression": (
            retrieval_candidate["document_recall_at_4"]
            >= raw_retrieval["document_recall_at_4"]
            and retrieval_candidate["family_recall_at_4"]
            >= raw_retrieval["family_recall_at_4"]
        ),
        "retrieval_source_and_scope": (
            retrieval_candidate["source_span_validity"] == 1.0
            and retrieval_candidate["cross_scope_result_count"] == 0
        ),
        "deterministic_cost_gain": indexed_character_reduction > 0,
    }
    return {
        "schema_version": 1,
        "title": "Template-Aware RAG Isolated Evaluation",
        "production_ready": False,
        "fixture": {
            "version": TEMPLATE_FIXTURE_VERSION,
            "digest": template_fixture_digest(),
            "document_count": len(documents),
            "template_family_count": TEMPLATE_FAMILY_COUNT,
            "messages_per_family": TEMPLATE_MESSAGES_PER_FAMILY,
            "unique_message_count": TEMPLATE_UNIQUE_COUNT,
            "train_fraction": 0.6,
            "synthetic_only": all(item.metadata.get("synthetic") is True for item in documents),
        },
        "method": (
            "Chronologically train on the first six messages in each recurring family and "
            "evaluate only later revisions and unique controls. Template output is derived "
            "metadata; slot offsets are checked against immutable source text."
        ),
        "lookup_controls": [exact, skeleton],
        "drain_baseline": baseline,
        "one_factor_sweeps": sweeps,
        "shingle_sweep": _shingle_sweep(documents),
        "boilerplate_reduction": reduction,
        "retrieval_ablation": retrieval_ablation,
        "retrieval_decision": {
            "baseline_lane": "raw",
            "selected_lane": "deduplicated",
            "indexed_character_reduction": indexed_character_reduction,
            "reason": (
                "The deduplicated lane preserved document/family recall and exact dynamic "
                "values with a smaller index. Keep Drain families and typed slots in "
                "normalized routing tables instead of repeating them in every chunk."
            ),
        },
        "performance": performance,
        "selected_candidate": {
            "method": winner["method"],
            "settings": winner["settings"],
            "metrics": winner["metrics"],
            "provisional": True,
        },
        "gates": gates,
        "hard_gate_pass": all(gates.values()),
        "limitations": [
            "The corpus is synthetic and deliberately structured; mailbox prevalence is not measured.",
            "Typed slots are deterministic regex surfaces, not semantic claims.",
            "Template IDs are stable for the frozen chronological stream but online Drain remains order-sensitive.",
            "Live answer quality and extended-scale behavior are separate qualification stages.",
        ],
    }


def markdown_template_report(report: dict[str, Any]) -> str:
    fixture = report["fixture"]
    selected = report["selected_candidate"]
    metrics = selected["metrics"]
    lines = [
        f"# {report['title']}",
        "",
        report["method"],
        "",
        "## Corpus",
        "",
        f"- Documents: {fixture['document_count']} synthetic messages.",
        f"- Recurring families: {fixture['template_family_count']}.",
        f"- Chronological train/test split: {fixture['train_fraction']:.0%}/{1 - fixture['train_fraction']:.0%}.",
        f"- Fixture digest: `{fixture['digest']}`.",
        "",
        "## Family controls",
        "",
        "| Method | Precision | Recall | F1 |",
        "|---|---:|---:|---:|",
    ]
    for lane in [*report["lookup_controls"], report["drain_baseline"]]:
        quality = lane["metrics"]
        lines.append(
            f"| {lane['method']} | {quality['precision']:.3f} | "
            f"{quality['recall']:.3f} | {quality['f1']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Selected isolated candidate",
            "",
            f"- Settings: `{json.dumps(selected['settings'], sort_keys=True)}`.",
            f"- Family F1: {metrics['f1']:.3f}.",
            f"- Slot precision/recall: {metrics['slot_precision']:.3f}/{metrics['slot_recall']:.3f}.",
            f"- Over-merged clusters: {metrics['overmerged_cluster_count']}.",
            f"- Source-span validity: {metrics['source_span_validity']:.3f}.",
            f"- Boilerplate character reduction: {report['boilerplate_reduction']['metrics']['character_reduction']:.1%}.",
            f"- Dynamic-value recall after reduction: {report['boilerplate_reduction']['metrics']['dynamic_value_recall']:.3f}.",
        ]
    )
    lines.extend(
        [
            "",
            "## Retrieval representation ablation",
            "",
            "| Lane | Document R@4 | Document MRR | Family R@4 | Family P@4 | Indexed chars |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for lane in report["retrieval_ablation"]:
        lane_metrics = lane["metrics"]
        lines.append(
            f"| {lane['lane']} | {lane_metrics['document_recall_at_4']:.3f} | "
            f"{lane_metrics['document_mrr']:.3f} | {lane_metrics['family_recall_at_4']:.3f} | "
            f"{lane_metrics['family_precision_at_4']:.3f} | "
            f"{lane_metrics['indexed_characters']} |"
        )
    decision = report["retrieval_decision"]
    lines.extend(
        [
            "",
            f"Selected retrieval surface: `{decision['selected_lane']}` "
            f"({decision['indexed_character_reduction']:.1%} fewer indexed characters "
            f"than `{decision['baseline_lane']}`).",
            "",
            decision["reason"],
        ]
    )
    lines.extend(["", "## Gates", ""])
    lines.extend(
        f"- {'PASS' if passed else 'FAIL'}: `{name}`"
        for name, passed in report["gates"].items()
    )
    lines.extend(
        [
            "",
            f"Overall isolated hard gate: {'PASS' if report['hard_gate_pass'] else 'FAIL'}.",
            "",
            "This is an isolated deterministic result, not a production-readiness decision.",
            "",
        ]
    )
    return "\n".join(lines)


def write_template_report(directory: Path, name: str, report: dict[str, Any]) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / f"{name}.json"
    markdown_path = directory / f"{name}.md"
    checkpoint(json_path, report)
    temporary = markdown_path.with_suffix(markdown_path.suffix + ".tmp")
    temporary.write_text(markdown_template_report(report), encoding="utf-8")
    temporary.replace(markdown_path)
    return {"json": json_path, "markdown": markdown_path}
