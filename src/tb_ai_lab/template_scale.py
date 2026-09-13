# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0.

"""Template-aware retrieval and ledger evaluation on long synthetic threads."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import tempfile
import time
import tracemalloc
from typing import Any

from .contracts import Document, Scope, content_digest
from .reporting import checkpoint
from .storage import Index
from .template_evaluation import _family_message
from .template_mining import (
    DrainTemplateMiner,
    assign_template,
    boilerplate_catalog,
    sender_domain,
    template_retrieval_text,
)
from .text import chunk_document


TEMPLATE_SCALE_VERSION = "synthetic-template-thread-scale-v1"
TEMPLATE_SCALE_SIZES = (500, 1000, 2500, 5000)
TEMPLATE_SCALE_FAMILIES = (
    "invoice",
    "shipment",
    "order",
    "receipt",
    "meeting",
    "security",
    "support",
    "bulletin",
)
TEMPLATE_SCALE_FACT_RE = re.compile(
    r"\[FACT (S\d{5})\]\s*state_code:\s*([A-Z0-9-]+)\."
)
TEMPLATE_SCALE_DIGESTS = {
    500: "c597f8064c193dd978364f39f0798814efe403b6dce5cfba4efe66a307a4bdd7",
    1000: "4ca43e001ba6fe61f8f18b32f8706182ea141bfaa5cd1e124c72a8b68dc180a8",
    2500: "a833e243820635ff8af01129ec59ba4fed399a69fbc84baba970a861ca54eaa7",
    5000: "9d11c6afa9db245664b4efb92a9af72aeedb5d834ea5f083d440319b470c0fb2",
}


def template_scale_fixture(size: int) -> tuple[list[Document], dict[str, str]]:
    if size not in TEMPLATE_SCALE_SIZES:
        raise ValueError(f"template scale size must be one of {TEMPLATE_SCALE_SIZES}")
    scope = Scope("tenant-alpha", "mail")
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    documents = []
    facts = {}
    for ordinal in range(1, size + 1):
        family = TEMPLATE_SCALE_FAMILIES[(ordinal - 1) % len(TEMPLATE_SCALE_FAMILIES)]
        family_sequence = (ordinal - 1) // len(TEMPLATE_SCALE_FAMILIES) + 1
        author, subject, body, expected_slots = _family_message(family, family_sequence)
        fact_id = f"S{ordinal:05d}"
        fact_value = f"TS-{size:05d}-{ordinal:05d}"
        facts[fact_id] = fact_value
        signature = body.find("\n-- ")
        fact_line = f"\n[FACT {fact_id}] state_code: {fact_value}."
        body = body + fact_line if signature < 0 else body[:signature] + fact_line + body[signature:]
        documents.append(
            Document(
                id=f"template-scale-{size:05d}-{ordinal:05d}",
                tenant=scope.tenant,
                collection=scope.collection,
                title=subject,
                timestamp=(started + timedelta(minutes=ordinal)).isoformat(),
                text=body,
                metadata={
                    "synthetic": True,
                    "author": author,
                    "thread_id": f"TEMPLATE-SCALE-{size:05d}",
                    "sequence": ordinal,
                    "expected_template_family": family,
                    "expected_slots": [list(item) for item in expected_slots],
                    "template_training": ordinal <= len(TEMPLATE_SCALE_FAMILIES) * 6,
                },
            )
        )
    documents.append(
        Document(
            id=f"template-scale-{size:05d}-private-shadow",
            tenant="tenant-beta",
            collection=scope.collection,
            title="Invoice INV-9999 review",
            timestamp=(started + timedelta(days=365)).isoformat(),
            text="[FACT S99999] state_code: PRIVATE-TEMPLATE-SHADOW.",
            metadata={
                "synthetic": True,
                "author": "Billing <billing@commerce.invalid>",
                "thread_id": f"TEMPLATE-SCALE-{size:05d}",
                "expected_template_family": "invoice",
            },
        )
    )
    return documents, facts


def template_scale_digest(size: int) -> str:
    documents, facts = template_scale_fixture(size)
    return content_digest(
        {
            "version": TEMPLATE_SCALE_VERSION,
            "documents": [item.as_dict() for item in documents],
            "facts": facts,
        }
    )


def _facts(value: str) -> dict[str, str]:
    return {match.group(1): match.group(2) for match in TEMPLATE_SCALE_FACT_RE.finditer(value)}


def _train(documents: list[Document]) -> tuple[DrainTemplateMiner, dict[str, str]]:
    scope = Scope("tenant-alpha", "mail")
    miner = DrainTemplateMiner(scope, similarity_threshold=0.6, min_support=3)
    labels: dict[str, Counter[str]] = defaultdict(Counter)
    for document in documents:
        if document.scope != scope or not document.metadata.get("template_training"):
            continue
        family = miner.observe(
            document.title,
            sender_domain=sender_domain(str(document.metadata.get("author", ""))),
            surface="subject",
        )
        labels[family.id][str(document.metadata["expected_template_family"])] += 1
    return miner, {
        family_id: counts.most_common(1)[0][0]
        for family_id, counts in labels.items()
    }


def _family_metrics(expected: list[str], actual: list[str]) -> dict[str, float | int]:
    correct = sum(left == right for left, right in zip(expected, actual, strict=True))
    offered = sum(bool(item) for item in actual)
    return {
        "precision": correct / offered if offered else 0.0,
        "recall": correct / len(expected) if expected else 1.0,
        "f1": (
            2 * correct / offered * correct / len(expected)
            / (correct / offered + correct / len(expected))
            if correct and offered and expected
            else 0.0
        ),
        "correct": correct,
        "expected": len(expected),
        "offered": offered,
    }


def _page_metrics(
    documents: list[Document], expected_facts: dict[str, str], page_size: int
) -> dict[str, Any]:
    pages = [
        documents[start : start + page_size]
        for start in range(0, len(documents), page_size)
    ]
    mapped = {}
    peak_source_characters = 0
    peak_ledger_characters = 0
    for page in pages:
        peak_source_characters = max(
            peak_source_characters, sum(len(item.text) for item in page)
        )
        page_facts = {
            key: value for document in page for key, value in _facts(document.text).items()
        }
        peak_ledger_characters = max(
            peak_ledger_characters,
            len("\n".join(f"{key}={value}" for key, value in sorted(page_facts.items()))),
        )
        mapped.update(page_facts)
    matched = {
        key: value for key, value in expected_facts.items() if mapped.get(key) == value
    }
    return {
        "page_size": page_size,
        "page_count": len(pages),
        "fact_recall": len(matched) / len(expected_facts),
        "missing_fact_ids": sorted(set(expected_facts) - set(matched)),
        "unsupported_facts": {
            key: value for key, value in mapped.items() if expected_facts.get(key) != value
        },
        "peak_source_characters": peak_source_characters,
        "peak_ledger_characters": peak_ledger_characters,
    }


def _evaluate_size(size: int) -> dict[str, Any]:
    documents, expected_facts = template_scale_fixture(size)
    scope = Scope("tenant-alpha", "mail")
    scoped_documents = [item for item in documents if item.scope == scope]
    training_documents = [
        item for item in scoped_documents if item.metadata.get("template_training")
    ]
    labels = {
        item.id: str(item.metadata["expected_template_family"])
        for item in training_documents
    }
    boilerplate = boilerplate_catalog(training_documents, labels)
    mining_started = time.perf_counter()
    miner, family_labels = _train(documents)
    assignments = []
    expected_families = []
    actual_families = []
    source_spans_valid = True
    slot_source_valid = True
    raw_characters = 0
    analysis_characters = 0
    for document in scoped_documents:
        assignment = assign_template(document, miner, surface="subject")
        expected_family = str(document.metadata["expected_template_family"])
        actual_family = family_labels.get(assignment.family_id, "") if assignment else ""
        reduced = template_retrieval_text(
            document, boilerplate.get(actual_family, set())
        )
        raw_characters += len(document.text)
        analysis_characters += len(reduced)
        expected_families.append(expected_family)
        actual_families.append(actual_family)
        if assignment:
            assignments.append((document, assignment, actual_family, reduced))
            source_spans_valid = source_spans_valid and assignment.source_digest == content_digest(
                document.text
            )
            slot_source_valid = slot_source_valid and all(
                document.text[slot.start : slot.end] == slot.value
                for slot in assignment.slots
            )
    mining_ms = (time.perf_counter() - mining_started) * 1000
    family_quality = _family_metrics(expected_families, actual_families)
    ledger = "\n".join(
        f"{key}={value}" for key, value in sorted(expected_facts.items())
    )
    extracted = {
        key: value
        for document in scoped_documents
        for key, value in _facts(document.text).items()
    }

    latest_correct = 0
    graph_neighbors = {}
    for family in TEMPLATE_SCALE_FAMILIES:
        members = [
            item
            for item in assignments
            if item[2] == family
        ]
        members.sort(key=lambda item: (item[0].timestamp, item[0].id), reverse=True)
        expected_latest = next(
            item for item in reversed(scoped_documents)
            if item.metadata["expected_template_family"] == family
        )
        latest_correct += int(bool(members) and members[0][0].id == expected_latest.id)
        graph_neighbors[family] = [item[0].id for item in members[:8]]

    with tempfile.TemporaryDirectory(prefix=f"tb-ai-template-scale-{size}-") as temporary:
        database = Path(temporary) / "template-scale.sqlite"
        tracemalloc.start()
        ingest_started = time.perf_counter()
        with Index(database, normalized_parent_storage=True) as index:
            for family in miner.families(mature_only=True):
                index.put_template_family(family)
            for document, assignment, actual_family, reduced in assignments:
                chunks = chunk_document(document, "structure-aware", 1200, 0, 16)
                contextual = (
                    f"Template family: {actual_family}\n{reduced}"
                    if actual_family
                    else reduced
                )
                chunks = [
                    replace(chunk, contextual_text=contextual, retrieval_text=reduced)
                    for chunk in chunks
                ]
                index.add_document(document, chunks)
                index.put_template_assignment(assignment)
            index.connection.execute("VACUUM")
        ingest_ms = (time.perf_counter() - ingest_started) * 1000
        _, peak_python_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        database_bytes = database.stat().st_size

    pages = [_page_metrics(scoped_documents, expected_facts, value) for value in (16, 32, 64)]
    direct_top_8 = dict(list(extracted.items())[:8])
    matched = {
        key: value for key, value in expected_facts.items() if extracted.get(key) == value
    }
    hard_gate_pass = (
        family_quality["f1"] >= 0.95
        and len(matched) == len(expected_facts)
        and source_spans_valid
        and slot_source_valid
        and len(assignments) == len(scoped_documents)
        and all(item["fact_recall"] == 1.0 for item in pages)
        and all(not item["unsupported_facts"] for item in pages)
        and all(len(items) <= 8 for items in graph_neighbors.values())
        and "PRIVATE-TEMPLATE-SHADOW" not in ledger
    )
    return {
        "thread_size": size,
        "fixture_digest": template_scale_digest(size),
        "metrics": {
            "family": family_quality,
            "assignment_recall": len(assignments) / len(scoped_documents),
            "source_digest_validity": float(source_spans_valid),
            "slot_source_validity": float(slot_source_valid),
            "fact_recall": len(matched) / len(expected_facts),
            "direct_top_8_fact_recall": len(direct_top_8) / len(expected_facts),
            "latest_family_accuracy": latest_correct / len(TEMPLATE_SCALE_FAMILIES),
            "raw_characters": raw_characters,
            "template_retrieval_characters": analysis_characters,
            "character_reduction": 1 - analysis_characters / raw_characters,
            "ledger_characters": len(ledger),
            "mining_ms": mining_ms,
            "ingest_ms": ingest_ms,
            "database_bytes": database_bytes,
            "peak_python_bytes": peak_python_bytes,
        },
        "page_sweep": pages,
        "graph": {
            "family_node_count": len(graph_neighbors),
            "max_neighbors": max(map(len, graph_neighbors.values())),
            "neighbors": graph_neighbors,
        },
        "hard_gate_pass": hard_gate_pass,
    }


def evaluate_template_scale(
    sizes: tuple[int, ...] = TEMPLATE_SCALE_SIZES,
) -> dict[str, Any]:
    results = [_evaluate_size(size) for size in sizes]
    return {
        "schema_version": 1,
        "title": "Template-Aware Long-Thread Scale Evaluation",
        "production_ready": False,
        "fixture_version": TEMPLATE_SCALE_VERSION,
        "results": results,
        "hard_gate_pass": all(item["hard_gate_pass"] for item in results),
        "decision": (
            "Use sender-scoped template families as bounded retrieval metadata, retain "
            "source-validated slots and facts in deterministic ledgers, and cap family "
            "graph expansion. Top-K remains unsuitable for exhaustive thread requests."
        ),
    }


def markdown_template_scale(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['title']}",
        "",
        "| Messages | Family F1 | Assignments | Fact recall | Top-8 recall | Latest | Reduction | Mining ms | Ingest ms | DB bytes | Peak bytes |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in report["results"]:
        metrics = result["metrics"]
        lines.append(
            f"| {result['thread_size']} | {metrics['family']['f1']:.3f} | "
            f"{metrics['assignment_recall']:.3f} | {metrics['fact_recall']:.3f} | "
            f"{metrics['direct_top_8_fact_recall']:.4f} | "
            f"{metrics['latest_family_accuracy']:.3f} | "
            f"{metrics['character_reduction']:.1%} | {metrics['mining_ms']:.1f} | "
            f"{metrics['ingest_ms']:.1f} | {metrics['database_bytes']} | "
            f"{metrics['peak_python_bytes']} |"
        )
    lines.extend(
        [
            "",
            f"Hard gate: {'PASS' if report['hard_gate_pass'] else 'FAIL'}.",
            "",
            "## Decision",
            "",
            report["decision"],
            "",
        ]
    )
    return "\n".join(lines)


def write_template_scale_report(
    directory: Path, name: str, report: dict[str, Any]
) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / f"{name}.json"
    markdown_path = directory / f"{name}.md"
    checkpoint(json_path, report)
    temporary = markdown_path.with_suffix(markdown_path.suffix + ".tmp")
    temporary.write_text(markdown_template_scale(report), encoding="utf-8")
    temporary.replace(markdown_path)
    return {"json": json_path, "markdown": markdown_path}
