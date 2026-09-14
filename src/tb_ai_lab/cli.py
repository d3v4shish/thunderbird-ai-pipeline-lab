# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0.

"""Command-line interface for deterministic and live evaluation workflows."""

from __future__ import annotations

import argparse
from dataclasses import replace
from hashlib import sha256
from itertools import product
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
from typing import Any

from .benchmark import run_benchmark
from .contracts import Document, EvaluationCase, PipelineVariant, Scope, content_digest
from .contextual_rag import (
    contextual_challenge_fixture,
    evaluate_contextual_rag,
    write_contextual_rag_report,
)
from .context_ladder import (
    context_ladder_fixture,
    evaluate_context_ladder,
    live_screen_plan,
    run_live_screen,
    write_context_ladder_report,
)
from .corpus import load_cases, load_documents, write_frozen_corpus
from .evaluation import combine_repeats, evaluate_variant
from .email_rag import (
    EMAIL_CORPUS_DIGEST,
    combine_email_rag_repeats,
    email_fixture_digest,
    email_rag_fixture,
    evaluate_email_rag_repeat,
    write_email_rag_report,
)
from .models import (
    ModelError,
    OllamaClient,
    RerankerClient,
    nvidia_total_used_bytes,
    prepare_allowlisted_models,
)
from .oversized_email import (
    DEFAULT_CONTEXT_WINDOW,
    DEFAULT_EMAIL_BYTES,
    DEFAULT_FACT_COUNT,
    DEFAULT_PAGE_CHARS,
    evaluate_oversized_email_deterministic,
    evaluate_oversized_email_live,
    evaluate_oversized_stress_suite,
    oversized_fixture_digest,
    write_oversized_email_report,
)
from .oversized_designs import (
    evaluate_oversized_designs_deterministic,
    evaluate_oversized_designs_live,
    write_oversized_design_report,
)
from .live_hardening import (
    combine_cross_encoder_repeats,
    evaluate_answer_parameters,
    evaluate_cross_encoder_repeat,
    evaluate_embedding_drift,
    markdown_answer_parameters,
    markdown_cross_encoder,
    markdown_embedding_drift,
    write_live_report,
)
from .pipeline import Pipeline
from .query_rag import (
    combine_query_rag_repeats,
    evaluate_query_rag_repeat,
    query_rag_challenge_fixture,
    write_query_rag_report,
)
from .related_email_rag import (
    evaluate_related_email_rag,
    live_related_plan,
    related_email_fixture,
    run_live_related_screen,
    write_related_email_report,
)
from .rag_evaluation import evaluate_rag_stages, write_rag_report
from .reporting import checkpoint, write_report
from .scale_evaluation import (
    EXTENDED_THREAD_FIXTURE_DIGESTS,
    EXTENDED_THREAD_SIZES,
    THREAD_FIXTURE_DIGESTS,
    THREAD_SIZES,
    evaluate_deterministic_parameters,
    evaluate_parent_storage,
    evaluate_thread_scale,
    markdown_parameter_report,
    markdown_scale_report,
    markdown_storage_report,
    write_scale_report,
)
from .slot_candidates import (
    evaluate_slot_candidates_deterministic,
    run_live_slot_candidate_screen,
    slot_candidate_live_plan,
    write_slot_candidate_report,
)
from .structured_memory import (
    evaluate_structured_memory_deterministic,
    run_live_structured_memory_screen,
    structured_memory_live_plan,
    write_structured_memory_report,
)
from .structured_memory_qualification import (
    evaluate_structured_memory_qualification,
    qualification_live_plan,
    run_live_qualification,
    write_qualification_report,
)
from .storage import Index
from .template_evaluation import evaluate_template_mining, write_template_report
from .template_scale import evaluate_template_scale, write_template_scale_report
from .template_live import (
    APPROVED_TEMPLATE_CHAT_MODELS,
    TEMPLATE_LIVE_STAGES,
    combine_template_live,
    evaluate_template_embedding,
    evaluate_template_live_repeat,
    load_template_live_checkpoint,
    template_live_identity,
    write_template_live_report,
)
from .thread_memory import atomic_json
from .thread_memory_evaluation import (
    THREAD_MEMORY_CORPUS_DIGEST,
    evaluate_thread_memory_live,
    full_matrix_plan,
    thread_memory_fixture_digest,
    write_thread_memory_report,
)
from .thread_memory_hardening import (
    evaluate_thread_memory_hardening_deterministic,
    write_thread_memory_hardening_report,
)


PROJECT = Path(__file__).resolve().parents[2]
CONFIG = PROJECT / "config"
DATA = PROJECT / "data" / "generated"
DEFAULT_REPORTS = PROJECT / "reports"
ARTIFACT_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}\Z")


def artifact_name(value: str) -> str:
    if not ARTIFACT_NAME_RE.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "must start with an alphanumeric character and contain only letters, numbers, '.', '_' or '-'"
        )
    return value


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError(f"Unsupported or malformed configuration: {path}")
    return value


def source_drift(source_root: Path | None = None) -> dict[str, Any]:
    manifest = read_json(CONFIG / "source-manifest.json")
    if source_root is None:
        configured = os.environ.get("LAB_SOURCE_ROOT")
        source_root = Path(configured).resolve() if configured else None
    records = []
    for source in manifest["sources"]:
        path = source_root / source["path"] if source_root else None
        if path is None or not path.is_file():
            records.append({**source, "status": "unavailable", "actual_sha256": None})
            continue
        actual = sha256(path.read_bytes()).hexdigest()
        records.append(
            {
                **source,
                "status": "match" if actual == source["sha256"] else "drift",
                "actual_sha256": actual,
            }
        )
    return {
        "source_root": str(source_root) if source_root else None,
        "records": records,
        "drift": any(item["status"] == "drift" for item in records),
    }


def implementation_digest() -> str:
    sources = PROJECT / "src" / "tb_ai_lab"
    return content_digest(
        {
            path.name: sha256(path.read_bytes()).hexdigest()
            for path in sorted(sources.glob("*.py"))
        }
    )


def build(_: argparse.Namespace) -> int:
    if sys.version_info < (3, 14):
        raise RuntimeError("Python 3.14 or newer is required")
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE VIRTUAL TABLE fts_probe USING fts5(text)")
    connection.close()
    variant = PipelineVariant.from_dict(read_json(CONFIG / "tb-current.json"))
    candidate_config = read_json(CONFIG / "candidates.json")
    model_config = read_json(CONFIG / "models.json")
    corpus_manifest = write_frozen_corpus(DATA)
    result = {
        "schema_version": 1,
        "python_required": "3.14",
        "sqlite_version": sqlite3.sqlite_version,
        "fts5": True,
        "baseline_digest": content_digest(variant.as_dict()),
        "candidate_config_digest": content_digest(candidate_config),
        "model_config_digest": content_digest(model_config),
        "implementation_digest": implementation_digest(),
        "corpus": corpus_manifest,
        "sources": source_drift(),
    }
    checkpoint(DATA / "build-manifest.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["sources"]["drift"] else 0


def ensure_corpus() -> dict[str, Any]:
    return write_frozen_corpus(DATA)


def baseline_variant(**updates: Any) -> PipelineVariant:
    base = PipelineVariant.from_dict(read_json(CONFIG / "tb-current.json"))
    return replace(base, **updates)


def report_directory() -> Path:
    return Path(os.environ.get("LAB_REPORT_DIR", str(DEFAULT_REPORTS))).resolve()


def evaluate(arguments: argparse.Namespace) -> int:
    corpus_manifest = ensure_corpus()
    documents = load_documents(DATA / "documents.jsonl")
    cases = load_cases(DATA / "cases.jsonl")
    if arguments.calibration:
        selected = set(read_json(CONFIG / "candidates.json")["calibration_case_ids"])
        cases = [case for case in cases if case.id in selected]
    variant = baseline_variant()
    if arguments.optimized:
        variant = replace(
            variant,
            id="coverage-graph-candidate",
            chunking="structure-aware",
            max_chunks=4096,
            graph="intent-multihop",
            tools="coverage-aware",
            prompt="evidence-ledger",
        )
    result = evaluate_variant(documents, cases, variant)
    paths = write_report(
        report_directory(),
        arguments.name,
        [result],
        {
            "corpus": corpus_manifest,
            "implementation_digest": implementation_digest(),
            "source_drift": source_drift(),
            "variant_digest": content_digest(variant.as_dict()),
            "seed": 0,
        },
    )
    print(json.dumps({"aggregate": result["aggregate"], "reports": {key: str(value) for key, value in paths.items()}}, indent=2))
    return 0


def rag_evaluate(arguments: argparse.Namespace) -> int:
    corpus_manifest = ensure_corpus()
    documents = load_documents(DATA / "documents.jsonl")
    cases = load_cases(DATA / "cases.jsonl")
    report = evaluate_rag_stages(
        documents, cases, baseline_variant(), arguments.top_k
    )
    report["manifest"] = {
        "corpus": corpus_manifest,
        "implementation_digest": implementation_digest(),
        "variant_digest": content_digest(baseline_variant().as_dict()),
        "seed": 0,
    }
    paths = write_rag_report(report_directory(), arguments.name, report)
    print(
        json.dumps(
            {
                "recommendations": report["recommendations"],
                "reports": {key: str(value) for key, value in paths.items()},
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def contextual_rag_evaluate(arguments: argparse.Namespace) -> int:
    corpus_manifest = ensure_corpus()
    documents = load_documents(DATA / "documents.jsonl")
    cases = load_cases(DATA / "cases.jsonl")
    challenge_documents, challenge_cases = contextual_challenge_fixture()
    documents.extend(challenge_documents)
    cases.extend(challenge_cases)
    config = read_json(CONFIG / "models.json")
    client = model_client()
    discovered = {item["name"]: item for item in client.discover()}
    chat = discovered.get(arguments.chat_model)
    embedding = discovered.get(arguments.embedding_model)
    if not chat:
        raise ModelError(f"Context generator is not installed: {arguments.chat_model}")
    if not embedding:
        raise ModelError(f"Embedding model is not installed: {arguments.embedding_model}")
    if "chat" not in chat.get("roles", []):
        raise ModelError(f"Context generator is not chat-capable: {arguments.chat_model}")
    if "embedding" not in embedding.get("roles", []):
        raise ModelError(f"Embedding model is not embedding-capable: {arguments.embedding_model}")

    client.vram_cap_gib = float(config["vram_cap_gib"])
    directory = report_directory()
    cache_name = arguments.cache_name or arguments.name
    cache_path = directory / f"{cache_name}-contexts-cache.json"
    whole_email_cache_path = (
        directory / f"{cache_name}-whole-email-contexts-cache.json"
    )
    selected_models = {arguments.chat_model, arguments.embedding_model}
    try:
        report = evaluate_contextual_rag(
            documents,
            cases,
            baseline_variant(),
            client,
            arguments.chat_model,
            str(chat.get("digest", "")),
            arguments.embedding_model,
            str(embedding.get("digest", "")),
            cache_path,
            content_digest(
                {
                    "documents": [item.as_dict() for item in documents],
                    "cases": [item.as_dict() for item in cases],
                }
            ),
            top_k=arguments.top_k,
            resume=arguments.resume,
            whole_email_cache_path=whole_email_cache_path,
        )
        loaded = [
            item
            for item in client.ps()
            if str(item.get("name") or item.get("model") or "") in selected_models
        ]
        report["manifest"] = {
            "corpus": corpus_manifest,
            "contextual_challenge": {
                "document_ids": [item.id for item in challenge_documents],
                "case_ids": [item.id for item in challenge_cases],
            },
            "implementation_digest": implementation_digest(),
            "source_drift": source_drift(),
            "seed": 0,
            "context_cache": str(cache_path),
            "whole_email_context_cache": str(whole_email_cache_path),
        }
        report["runtime"] = {
            "vram_cap_gib": client.vram_cap_gib,
            "active_model_allocations": loaded,
            "active_ollama_vram_bytes": sum(
                int(item.get("size_vram", 0) or 0) for item in loaded
            ),
            "peak_observed_ollama_vram_bytes": client.peak_ollama_vram_bytes,
            "peak_observed_whole_gpu_bytes": client.peak_gpu_used_bytes,
            "endpoint_requests": client.request_count,
            "request_bytes": client.request_bytes,
            "response_bytes": client.response_bytes,
        }
        paths = write_contextual_rag_report(directory, arguments.name, report)
    finally:
        for model in selected_models:
            try:
                client.unload(model)
            except ModelError:
                pass
    print(
        json.dumps(
            {
                "generation": report["generation"],
                "whole_email_generation": report["whole_email_generation"],
                "pairs": report["pairs"],
                "promotion_recommended": report["promotion_recommended"],
                "whole_email_promotion_recommended": report[
                    "whole_email_promotion_recommended"
                ],
                "reports": {key: str(value) for key, value in paths.items()},
                "context_cache": str(cache_path),
                "whole_email_context_cache": str(whole_email_cache_path),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def context_ladder_evaluate(arguments: argparse.Namespace) -> int:
    """Run the deterministic ladder and optionally a bounded live screen."""
    if not 1 <= arguments.repeats <= 3:
        raise ValueError("context-ladder repeats must be between 1 and 3")
    report = evaluate_context_ladder()
    documents, _ = context_ladder_fixture()
    requested_models = list(arguments.chat_model) or ["qwen3:8b"]
    plan = live_screen_plan(
        documents,
        requested_models,
        arguments.repeats,
        include_large_pages=arguments.include_large_pages,
    )
    live: dict[str, Any] = {
        "requested": bool(arguments.live),
        "dry_run": bool(arguments.dry_run),
        "plan": plan,
        "runs": [],
    }
    if arguments.live and not arguments.dry_run:
        config = read_json(CONFIG / "models.json")
        client = model_client()
        client.vram_cap_gib = float(config["vram_cap_gib"])
        discovered = {item["name"]: item for item in client.discover()}
        cache_base = arguments.cache_name or arguments.name
        for model in requested_models:
            record = discovered.get(model)
            if not record or "chat" not in record.get("roles", []):
                raise ModelError(f"Chat model is unavailable or incompatible: {model}")
            if int(record.get("advertised_context", 0) or 0) < 16_384:
                raise ModelError(f"Chat model context is too small for ladder screen: {model}")
            model_key = sha256(model.encode("utf-8")).hexdigest()[:12]
            cache_path = report_directory() / f"{cache_base}-{model_key}-context-ladder-checkpoint.json"
            try:
                result = run_live_screen(
                    client,
                    model,
                    str(record.get("digest", "")),
                    documents,
                    arguments.repeats,
                    cache_path,
                    resume=not arguments.no_resume,
                    include_large_pages=arguments.include_large_pages,
                )
                try:
                    residency = client.residency(
                        model,
                        int(record.get("advertised_context", 0) or 0),
                        float(config["vram_cap_gib"]),
                        required_context=16_384,
                    ).as_dict()
                except ModelError as error:
                    residency = {"eligible": False, "reason": str(error)}
                live["runs"].append(
                    {
                        "model": model,
                        "model_digest": record.get("digest", ""),
                        "checkpoint": str(cache_path),
                        "residency": residency,
                        "result": result,
                    }
                )
            finally:
                try:
                    client.unload(model)
                except ModelError:
                    pass
    report["live"] = live
    report["manifest"] = {
        "implementation_digest": implementation_digest(),
        "source_drift": source_drift(),
        "seed": 0,
        "loopback_only": True,
    }
    paths = write_context_ladder_report(report_directory(), arguments.name, report)
    print(
        json.dumps(
            {
                "hard_contract_pass": report["hard_contract_pass"],
                "production_ready": False,
                "live": {
                    "requested": live["requested"],
                    "dry_run": live["dry_run"],
                    "run_count": len(live["runs"]),
                },
                "reports": {key: str(value) for key, value in paths.items()},
            },
            indent=2,
            sort_keys=True,
        )
    )
    live_passed = all(
        run.get("result", {}).get("complete", False)
        for run in live["runs"]
    )
    return 1 if live["requested"] and not live["dry_run"] and not live_passed else 0


def related_email_rag_evaluate(arguments: argparse.Namespace) -> int:
    """Evaluate source-backed thread/template expansion and optional live metadata."""
    if not 1 <= arguments.repeats <= 3:
        raise ValueError("related-email repeats must be between 1 and 3")
    report = evaluate_related_email_rag()
    documents, _ = related_email_fixture()
    requested_models = list(arguments.chat_model) or ["qwen3:8b"]
    live: dict[str, Any] = {
        "requested": bool(arguments.live),
        "dry_run": bool(arguments.dry_run),
        "plan": live_related_plan(documents, requested_models, arguments.repeats),
        "runs": [],
    }
    live_passed = True
    if arguments.live and not arguments.dry_run:
        config = read_json(CONFIG / "models.json")
        client = model_client()
        client.vram_cap_gib = float(config["vram_cap_gib"])
        discovered = {item["name"]: item for item in client.discover()}
        cache_base = arguments.cache_name or arguments.name
        for model in requested_models:
            record = discovered.get(model)
            if not record or "chat" not in record.get("roles", []):
                raise ModelError(f"Chat model is unavailable or incompatible: {model}")
            if int(record.get("advertised_context", 0) or 0) < 16_384:
                raise ModelError(f"Chat model context is too small for related-email screen: {model}")
            model_key = sha256(model.encode("utf-8")).hexdigest()[:12]
            cache_path = report_directory() / f"{cache_base}-{model_key}-related-email-checkpoint.json"
            try:
                result = run_live_related_screen(
                    client,
                    model,
                    str(record.get("digest", "")),
                    documents,
                    arguments.repeats,
                    cache_path,
                    resume=not arguments.no_resume,
                )
                try:
                    residency = client.residency(
                        model,
                        int(record.get("advertised_context", 0) or 0),
                        float(config["vram_cap_gib"]),
                        required_context=16_384,
                    ).as_dict()
                except ModelError as error:
                    residency = {"eligible": False, "reason": str(error)}
                run_passed = bool(
                    result.get("complete")
                    and result.get("quality_gate_pass")
                    and residency.get("eligible")
                )
                live["runs"].append(
                    {
                        "model": model,
                        "model_digest": record.get("digest", ""),
                        "checkpoint": str(cache_path),
                        "residency": residency,
                        "passed": run_passed,
                        "result": result,
                    }
                )
                live_passed = live_passed and run_passed
                if not run_passed:
                    break
            finally:
                try:
                    client.unload(model)
                except ModelError:
                    pass
    report["live"] = live
    report["manifest"] = {
        "implementation_digest": implementation_digest(),
        "source_drift": source_drift(),
        "seed": 0,
        "loopback_only": True,
    }
    paths = write_related_email_report(report_directory(), arguments.name, report)
    print(
        json.dumps(
            {
                "hard_contract_pass": report["hard_contract_pass"],
                "production_ready": False,
                "live_passed": live_passed if live["requested"] and not live["dry_run"] else None,
                "reports": {key: str(value) for key, value in paths.items()},
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 1 if live["requested"] and not live["dry_run"] and not live_passed else 0


def slot_candidate_evaluate(arguments: argparse.Namespace) -> int:
    """Evaluate host-owned source candidates and optional model ID selection."""
    if not 1 <= arguments.repeats <= 3:
        raise ValueError("slot-candidate repeats must be between 1 and 3")
    report = evaluate_slot_candidates_deterministic()
    requested_models = list(arguments.chat_model) or ["qwen3:8b"]
    live: dict[str, Any] = {
        "requested": bool(arguments.live),
        "dry_run": bool(arguments.dry_run),
        "plan": slot_candidate_live_plan(requested_models, arguments.repeats),
        "runs": [],
    }
    live_passed = True
    if arguments.live and not arguments.dry_run:
        config = read_json(CONFIG / "models.json")
        client = model_client()
        client.vram_cap_gib = float(config["vram_cap_gib"])
        discovered = {item["name"]: item for item in client.discover()}
        cache_base = arguments.cache_name or arguments.name
        for model in requested_models:
            record = discovered.get(model)
            if not record or "chat" not in record.get("roles", []):
                raise ModelError(f"Chat model is unavailable or incompatible: {model}")
            if int(record.get("advertised_context", 0) or 0) < 16_384:
                raise ModelError(f"Chat model context is too small for slot-candidate screen: {model}")
            model_key = sha256(model.encode("utf-8")).hexdigest()[:12]
            cache_path = report_directory() / f"{cache_base}-{model_key}-slot-candidate-checkpoint.json"
            try:
                result = run_live_slot_candidate_screen(
                    client,
                    model,
                    str(record.get("digest", "")),
                    arguments.repeats,
                    cache_path,
                    resume=not arguments.no_resume,
                )
                try:
                    residency = client.residency(
                        model,
                        int(record.get("advertised_context", 0) or 0),
                        float(config["vram_cap_gib"]),
                        required_context=16_384,
                    ).as_dict()
                except ModelError as error:
                    residency = {"eligible": False, "reason": str(error)}
                run_passed = bool(
                    result.get("complete")
                    and result.get("quality_gate_pass")
                    and residency.get("eligible")
                )
                live["runs"].append(
                    {
                        "model": model,
                        "model_digest": record.get("digest", ""),
                        "checkpoint": str(cache_path),
                        "residency": residency,
                        "passed": run_passed,
                        "result": result,
                    }
                )
                live_passed = live_passed and run_passed
                if not run_passed:
                    break
            finally:
                try:
                    client.unload(model)
                except ModelError:
                    pass
    report["live"] = live
    report["manifest"] = {
        "implementation_digest": implementation_digest(),
        "source_drift": source_drift(),
        "seed": 0,
        "loopback_only": True,
    }
    paths = write_slot_candidate_report(report_directory(), arguments.name, report)
    print(
        json.dumps(
            {
                "hard_contract_pass": report["hard_contract_pass"],
                "live_passed": live_passed if live["requested"] and not live["dry_run"] else None,
                "production_ready": False,
                "reports": {key: str(value) for key, value in paths.items()},
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 1 if live["requested"] and not live["dry_run"] and not live_passed else 0


def structured_memory_evaluate(arguments: argparse.Namespace) -> int:
    """Evaluate host-built candidate-only thread memory."""
    if not 1 <= arguments.repeats <= 3:
        raise ValueError("structured-memory repeats must be between 1 and 3")
    report = evaluate_structured_memory_deterministic()
    documents, _ = related_email_fixture()
    requested_models = list(arguments.chat_model) or ["qwen3:8b"]
    live: dict[str, Any] = {
        "requested": bool(arguments.live),
        "dry_run": bool(arguments.dry_run),
        "plan": structured_memory_live_plan(requested_models, arguments.repeats),
        "runs": [],
    }
    live_passed = True
    if arguments.live and not arguments.dry_run:
        config = read_json(CONFIG / "models.json")
        client = model_client()
        client.vram_cap_gib = float(config["vram_cap_gib"])
        discovered = {item["name"]: item for item in client.discover()}
        cache_base = arguments.cache_name or arguments.name
        for model in requested_models:
            record = discovered.get(model)
            if not record or "chat" not in record.get("roles", []):
                raise ModelError(f"Chat model is unavailable or incompatible: {model}")
            if int(record.get("advertised_context", 0) or 0) < 16_384:
                raise ModelError(
                    f"Chat model context is too small for structured-memory screen: {model}"
                )
            model_key = sha256(model.encode("utf-8")).hexdigest()[:12]
            cache_path = (
                report_directory()
                / f"{cache_base}-{model_key}-structured-memory-checkpoint.json"
            )
            try:
                result = run_live_structured_memory_screen(
                    client,
                    model,
                    str(record.get("digest", "")),
                    documents,
                    arguments.repeats,
                    cache_path,
                    resume=not arguments.no_resume,
                )
                try:
                    residency = client.residency(
                        model,
                        int(record.get("advertised_context", 0) or 0),
                        float(config["vram_cap_gib"]),
                        required_context=16_384,
                    ).as_dict()
                except ModelError as error:
                    residency = {"eligible": False, "reason": str(error)}
                run_passed = bool(
                    result.get("complete")
                    and result.get("quality_gate_pass")
                    and residency.get("eligible")
                )
                live["runs"].append(
                    {
                        "model": model,
                        "model_digest": record.get("digest", ""),
                        "checkpoint": str(cache_path),
                        "residency": residency,
                        "passed": run_passed,
                        "result": result,
                    }
                )
                live_passed = live_passed and run_passed
                if not run_passed:
                    break
            finally:
                try:
                    client.unload(model)
                except ModelError:
                    pass
    report["live"] = live
    report["manifest"] = {
        "implementation_digest": implementation_digest(),
        "source_drift": source_drift(),
        "seed": 0,
        "loopback_only": True,
    }
    paths = write_structured_memory_report(
        report_directory(), arguments.name, report
    )
    print(
        json.dumps(
            {
                "hard_contract_pass": report["hard_contract_pass"],
                "live_passed": (
                    live_passed
                    if live["requested"] and not live["dry_run"]
                    else None
                ),
                "production_ready": False,
                "reports": {key: str(value) for key, value in paths.items()},
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 1 if live["requested"] and not live["dry_run"] and not live_passed else 0


def structured_memory_qualify(arguments: argparse.Namespace) -> int:
    if not 1 <= arguments.repeats <= 3:
        raise ValueError("qualification repeats must be between 1 and 3")
    report = evaluate_structured_memory_qualification()
    requested_models = arguments.chat_model or ["qwen3:8b"]
    live = {
        "requested": bool(arguments.live),
        "dry_run": bool(arguments.dry_run),
        "plan": qualification_live_plan(requested_models, arguments.repeats),
        "runs": [],
    }
    live_passed = True
    if arguments.live and not arguments.dry_run:
        if not report["hard_contract_pass"]:
            raise RuntimeError("deterministic qualification prerequisite failed")
        config = read_json(CONFIG / "models.json")
        client = model_client()
        client.vram_cap_gib = float(config["vram_cap_gib"])
        discovered = {item["name"]: item for item in client.discover()}
        cache_base = arguments.cache_name or arguments.name
        for model in requested_models:
            record = discovered.get(model)
            if not record or "chat" not in record.get("roles", []):
                raise ModelError(f"Chat model is unavailable or incompatible: {model}")
            advertised_context = int(record.get("advertised_context", 0) or 0)
            if advertised_context < 16_384:
                raise ModelError(
                    f"Chat model context is too small for qualification: {model}"
                )
            model_key = sha256(model.encode("utf-8")).hexdigest()[:12]
            cache_path = (
                report_directory()
                / f"{cache_base}-{model_key}-qualification-checkpoint.json"
            )
            try:
                result = run_live_qualification(
                    client,
                    model,
                    str(record.get("digest", "")),
                    arguments.repeats,
                    cache_path,
                    resume=not arguments.no_resume,
                )
                try:
                    residency = client.residency(
                        model,
                        advertised_context,
                        float(config["vram_cap_gib"]),
                        required_context=16_384,
                    ).as_dict()
                except ModelError as error:
                    residency = {"eligible": False, "reason": str(error)}
                run_passed = bool(
                    result.get("complete")
                    and result.get("quality_gate_pass")
                    and residency.get("eligible")
                )
                live["runs"].append(
                    {
                        "model": model,
                        "model_digest": record.get("digest", ""),
                        "checkpoint": str(cache_path),
                        "residency": residency,
                        "passed": run_passed,
                        "result": result,
                    }
                )
                live_passed = live_passed and run_passed
                if not run_passed:
                    break
            finally:
                try:
                    client.unload(model)
                except ModelError:
                    pass
    report["live"] = live
    report["manifest"] = {
        "implementation_digest": implementation_digest(),
        "source_drift": source_drift(),
        "seed": 0,
        "loopback_only": True,
    }
    paths = write_qualification_report(report_directory(), arguments.name, report)
    print(
        json.dumps(
            {
                "hard_contract_pass": report["hard_contract_pass"],
                "live_passed": (
                    live_passed
                    if live["requested"] and not live["dry_run"]
                    else None
                ),
                "production_ready": False,
                "reports": {key: str(value) for key, value in paths.items()},
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 1 if live["requested"] and not live["dry_run"] and not live_passed else (
        0 if report["hard_contract_pass"] else 1
    )


def thread_memory_evaluate(arguments: argparse.Namespace) -> int:
    if not 1 <= arguments.repeats <= 10:
        raise ValueError("repeats must be between 1 and 10")
    chat_model_names = arguments.chat_model or ["qwen3:8b", "phi4:14b-q8_0"]
    chat_model_names = list(dict.fromkeys(chat_model_names))
    if thread_memory_fixture_digest() != THREAD_MEMORY_CORPUS_DIGEST:
        raise ValueError("Thread-memory fixture digest does not match its pinned contract")
    directory = report_directory()
    plan = full_matrix_plan(chat_model_names, arguments.repeats)
    plan.update(
        {
            "corpus_digest": THREAD_MEMORY_CORPUS_DIGEST,
            "chat_models": chat_model_names,
            "embedding_model": arguments.embedding_model,
            "vram_cap_gib": float(read_json(CONFIG / "models.json")["vram_cap_gib"]),
        }
    )
    if arguments.dry_run:
        if arguments.smoke:
            plan.update(
                {
                    "matrix": "live-smoke",
                    "cell_count": len(chat_model_names) * arguments.repeats * 2,
                    "generation_stream_count": len(chat_model_names) * arguments.repeats,
                }
            )
        destination = directory / f"{arguments.name}-plan.json"
        atomic_json(destination, plan)
        print(
            json.dumps(
                {
                    "cell_count": plan["cell_count"],
                    "generation_stream_count": plan["generation_stream_count"],
                    "report": str(destination),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    client = model_client()
    discovered = {item["name"]: item for item in client.discover()}
    chat_models: list[tuple[str, str]] = []
    for name in chat_model_names:
        record = discovered.get(name)
        if not record:
            raise ModelError(f"Thread-memory chat model is not installed: {name}")
        if "chat" not in record.get("roles", []):
            raise ModelError(f"Thread-memory model is not chat-capable: {name}")
        chat_models.append((name, str(record.get("digest", ""))))
    embedding = discovered.get(arguments.embedding_model)
    if not embedding:
        raise ModelError(
            f"Thread-memory embedding model is not installed: {arguments.embedding_model}"
        )
    if "embedding" not in embedding.get("roles", []):
        raise ModelError(
            f"Thread-memory model is not embedding-capable: {arguments.embedding_model}"
        )
    client.vram_cap_gib = float(read_json(CONFIG / "models.json")["vram_cap_gib"])
    cache_name = arguments.cache_name or arguments.name
    cache_directory = directory / f"{cache_name}-thread-memory-cache"
    selected_models = {*chat_model_names, arguments.embedding_model}
    try:
        report = evaluate_thread_memory_live(
            client,
            chat_models=chat_models,
            embedding_model=arguments.embedding_model,
            embedding_model_digest=str(embedding.get("digest", "")),
            repeats=arguments.repeats,
            cache_directory=cache_directory,
            resume=arguments.resume,
            smoke=arguments.smoke,
        )
        report["manifest"] = {
            "implementation_digest": implementation_digest(),
            "source_drift": source_drift(),
            "seed": 0,
            "cache_directory": str(cache_directory),
        }
        paths = write_thread_memory_report(directory, arguments.name, report)
    finally:
        for model in selected_models:
            try:
                client.unload(model)
            except ModelError:
                pass
    print(
        json.dumps(
            {
                "cell_count": len(report["cells"]),
                "pareto_frontier": report["pareto_frontier"],
                "hard_gate_failures": report["hard_gate_failures"],
                "reports": {key: str(value) for key, value in paths.items()},
                "cache_directory": str(cache_directory),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def thread_memory_hardening_evaluate(arguments: argparse.Namespace) -> int:
    report = evaluate_thread_memory_hardening_deterministic()
    report["manifest"] = {
        "implementation_digest": implementation_digest(),
        "source_drift": source_drift(),
        "seed": 0,
    }
    paths = write_thread_memory_hardening_report(
        report_directory(), arguments.name, report
    )
    print(
        json.dumps(
            {
                "hard_gate_failures": report["hard_gate_failures"],
                "parameter_cells": len(report["email_180_parameter_sweep"]),
                "thread_sizes": [
                    item["message_count"] for item in report["thread_scale"]
                ],
                "reports": {key: str(value) for key, value in paths.items()},
            },
            indent=2,
            sort_keys=True,
        )
    )
    return int(bool(report["hard_gate_failures"]))


def query_rag_evaluate(arguments: argparse.Namespace) -> int:
    if not 1 <= arguments.repeats <= 10:
        raise ValueError("repeats must be between 1 and 10")
    corpus_manifest = ensure_corpus()
    documents = load_documents(DATA / "documents.jsonl")
    cases = load_cases(DATA / "cases.jsonl")
    challenge_documents, challenge_cases = query_rag_challenge_fixture()
    documents.extend(challenge_documents)
    cases.extend(challenge_cases)
    config = read_json(CONFIG / "models.json")
    client = model_client()
    discovered = {item["name"]: item for item in client.discover()}
    chat = discovered.get(arguments.chat_model)
    embedding = discovered.get(arguments.embedding_model)
    if not chat:
        raise ModelError(f"Query generator is not installed: {arguments.chat_model}")
    if not embedding:
        raise ModelError(f"Embedding model is not installed: {arguments.embedding_model}")
    if "chat" not in chat.get("roles", []):
        raise ModelError(f"Query generator is not chat-capable: {arguments.chat_model}")
    if "embedding" not in embedding.get("roles", []):
        raise ModelError(f"Embedding model is not embedding-capable: {arguments.embedding_model}")

    client.vram_cap_gib = float(config["vram_cap_gib"])
    directory = report_directory()
    cache_name = arguments.cache_name or arguments.name
    cache_path = directory / f"{cache_name}-generation-cache.json"
    selected_models = {arguments.chat_model, arguments.embedding_model}
    experiment_digest = content_digest(
        {
            "documents": [item.as_dict() for item in documents],
            "cases": [item.as_dict() for item in cases],
        }
    )
    repeats = []
    for repeat_index in range(arguments.repeats):
        print(
            f"query-RAG repeat {repeat_index + 1}/{arguments.repeats}",
            file=sys.stderr,
            flush=True,
        )
        request_start = client.request_count
        request_bytes_start = client.request_bytes
        response_bytes_start = client.response_bytes
        client.peak_gpu_used_bytes = None
        client.peak_ollama_vram_bytes = 0
        try:
            repeat = evaluate_query_rag_repeat(
                documents,
                cases,
                baseline_variant(),
                client,
                arguments.chat_model,
                str(chat.get("digest", "")),
                arguments.embedding_model,
                str(embedding.get("digest", "")),
                cache_path,
                experiment_digest,
                arguments.top_k,
                arguments.resume,
            )
            loaded = [
                item
                for item in client.ps()
                if str(item.get("name") or item.get("model") or "")
                in selected_models
            ]
            repeat["repeat"] = repeat_index + 1
            repeat["runtime"] = {
                "vram_cap_gib": client.vram_cap_gib,
                "active_model_allocations": loaded,
                "active_ollama_vram_bytes": sum(
                    int(item.get("size_vram", 0) or 0) for item in loaded
                ),
                "peak_observed_ollama_vram_bytes": client.peak_ollama_vram_bytes,
                "peak_observed_whole_gpu_bytes": client.peak_gpu_used_bytes,
                "endpoint_requests": client.request_count - request_start,
                "request_bytes": client.request_bytes - request_bytes_start,
                "response_bytes": client.response_bytes - response_bytes_start,
            }
            repeats.append(repeat)
        finally:
            for model in selected_models:
                try:
                    client.unload(model)
                except ModelError:
                    pass

    report = combine_query_rag_repeats(repeats)
    report["manifest"] = {
        "corpus": corpus_manifest,
        "query_rag_challenge": {
            "document_ids": [item.id for item in challenge_documents],
            "case_ids": [item.id for item in challenge_cases],
        },
        "experiment_digest": experiment_digest,
        "implementation_digest": implementation_digest(),
        "source_drift": source_drift(),
        "seed": 0,
        "generation_cache": str(cache_path),
    }
    paths = write_query_rag_report(directory, arguments.name, report)
    print(
        json.dumps(
            {
                "stability": report["stability"],
                "candidate_decisions": report["candidate_decisions"],
                "safety_pass": report["safety_pass"],
                "reports": {key: str(value) for key, value in paths.items()},
                "generation_cache": str(cache_path),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def email_rag_evaluate(arguments: argparse.Namespace) -> int:
    if not 1 <= arguments.repeats <= 10:
        raise ValueError("repeats must be between 1 and 10")
    corpus_manifest = ensure_corpus()
    documents, cases, expected_routes = email_rag_fixture()
    experiment_digest = email_fixture_digest(documents, cases, expected_routes)
    if experiment_digest != EMAIL_CORPUS_DIGEST:
        raise ValueError("Synthetic email corpus digest changed unexpectedly")
    config = read_json(CONFIG / "models.json")
    client = model_client()
    discovered = {item["name"]: item for item in client.discover()}
    chat = discovered.get(arguments.chat_model)
    embedding = discovered.get(arguments.embedding_model)
    if not chat:
        raise ModelError(f"Answer/decomposition model is not installed: {arguments.chat_model}")
    if not embedding:
        raise ModelError(f"Embedding model is not installed: {arguments.embedding_model}")
    if "chat" not in chat.get("roles", []):
        raise ModelError(f"Answer/decomposition model is not chat-capable: {arguments.chat_model}")
    if "embedding" not in embedding.get("roles", []):
        raise ModelError(f"Embedding model is not embedding-capable: {arguments.embedding_model}")

    client.vram_cap_gib = float(config["vram_cap_gib"])
    directory = report_directory()
    cache_name = arguments.cache_name or arguments.name
    cache_path = directory / f"{cache_name}-decomposition-cache.json"
    selected_models = {arguments.chat_model, arguments.embedding_model}
    repeats = []
    for repeat_index in range(arguments.repeats):
        print(
            f"email-RAG repeat {repeat_index + 1}/{arguments.repeats}",
            file=sys.stderr,
            flush=True,
        )
        request_start = client.request_count
        request_bytes_start = client.request_bytes
        response_bytes_start = client.response_bytes
        client.peak_gpu_used_bytes = None
        client.peak_ollama_vram_bytes = 0
        try:
            repeat = evaluate_email_rag_repeat(
                documents,
                cases,
                expected_routes,
                baseline_variant(),
                client,
                arguments.chat_model,
                str(chat.get("digest", "")),
                arguments.embedding_model,
                str(embedding.get("digest", "")),
                cache_path,
                experiment_digest,
                arguments.top_k,
                arguments.resume,
            )
            loaded = [
                item
                for item in client.ps()
                if str(item.get("name") or item.get("model") or "")
                in selected_models
            ]
            repeat["repeat"] = repeat_index + 1
            repeat["runtime"] = {
                "vram_cap_gib": client.vram_cap_gib,
                "active_model_allocations": loaded,
                "active_ollama_vram_bytes": sum(
                    int(item.get("size_vram", 0) or 0) for item in loaded
                ),
                "peak_observed_ollama_vram_bytes": client.peak_ollama_vram_bytes,
                "peak_observed_whole_gpu_bytes": client.peak_gpu_used_bytes,
                "endpoint_requests": client.request_count - request_start,
                "request_bytes": client.request_bytes - request_bytes_start,
                "response_bytes": client.response_bytes - response_bytes_start,
            }
            repeats.append(repeat)
        finally:
            for model in selected_models:
                try:
                    client.unload(model)
                except ModelError:
                    pass

    report = combine_email_rag_repeats(repeats)
    report["manifest"] = {
        "base_corpus": corpus_manifest,
        "synthetic_email_corpus": {
            "version": "synthetic-email-v1",
            "digest": experiment_digest,
            "document_count": len(documents),
            "case_count": len(cases),
            "expected_routes": expected_routes,
        },
        "implementation_digest": implementation_digest(),
        "source_drift": source_drift(),
        "seed": 0,
        "decomposition_cache": str(cache_path),
    }
    paths = write_email_rag_report(directory, arguments.name, report)
    print(
        json.dumps(
            {
                "stability": report["stability"],
                "candidate_decision": report["candidate_decision"],
                "safety_pass": report["safety_pass"],
                "reports": {key: str(value) for key, value in paths.items()},
                "decomposition_cache": str(cache_path),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def scale_hardening_evaluate(arguments: argparse.Namespace) -> int:
    if not 1 <= arguments.repeats <= 10:
        raise ValueError("repeats must be between 1 and 10")
    corpus_manifest = ensure_corpus()
    documents = load_documents(DATA / "documents.jsonl")
    cases = load_cases(DATA / "cases.jsonl")
    directory = report_directory()
    sizes = THREAD_SIZES + EXTENDED_THREAD_SIZES if arguments.extended else THREAD_SIZES
    fixture_digests = dict(THREAD_FIXTURE_DIGESTS)
    if arguments.extended:
        fixture_digests.update(EXTENDED_THREAD_FIXTURE_DIGESTS)
    manifest = {
        "corpus": corpus_manifest,
        "thread_fixture_digests": fixture_digests,
        "implementation_digest": implementation_digest(),
        "source_drift": source_drift(),
        "seed": 0,
    }
    scale = evaluate_thread_scale(
        sizes=sizes,
        page_size=arguments.page_size,
        reduction_batch_size=arguments.reduction_batch_size,
    )
    scale["manifest"] = manifest
    scale_paths = write_scale_report(
        directory,
        f"{arguments.name}-threads",
        scale,
        markdown_scale_report(scale),
    )
    storage = evaluate_parent_storage(
        documents, cases, baseline_variant(), arguments.repeats
    )
    storage["manifest"] = manifest
    storage_paths = write_scale_report(
        directory,
        f"{arguments.name}-storage",
        storage,
        markdown_storage_report(storage),
    )
    parameters = evaluate_deterministic_parameters(
        documents, cases, baseline_variant()
    )
    parameters["manifest"] = manifest
    parameter_paths = write_scale_report(
        directory,
        f"{arguments.name}-parameters",
        parameters,
        markdown_parameter_report(parameters),
    )
    print(
        json.dumps(
            {
                "thread_hard_gate_pass": scale["hard_gate_pass"],
                "normalized_storage_candidate": storage["candidate"],
                "parameter_recommendations": parameters["recommendations"],
                "reports": {
                    "threads": {key: str(value) for key, value in scale_paths.items()},
                    "storage": {key: str(value) for key, value in storage_paths.items()},
                    "parameters": {key: str(value) for key, value in parameter_paths.items()},
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def template_evaluate(arguments: argparse.Namespace) -> int:
    report = evaluate_template_mining()
    report["manifest"] = {
        "implementation_digest": implementation_digest(),
        "source_drift": source_drift(),
        "seed": 0,
    }
    paths = write_template_report(report_directory(), arguments.name, report)
    print(
        json.dumps(
            {
                "hard_gate_pass": report["hard_gate_pass"],
                "selected_candidate": report["selected_candidate"],
                "reports": {key: str(value) for key, value in paths.items()},
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def template_scale_evaluate(arguments: argparse.Namespace) -> int:
    report = evaluate_template_scale()
    report["manifest"] = {
        "implementation_digest": implementation_digest(),
        "source_drift": source_drift(),
        "seed": 0,
    }
    paths = write_template_scale_report(
        report_directory(), arguments.name, report
    )
    print(
        json.dumps(
            {
                "hard_gate_pass": report["hard_gate_pass"],
                "results": [
                    {
                        "thread_size": item["thread_size"],
                        "metrics": item["metrics"],
                        "hard_gate_pass": item["hard_gate_pass"],
                    }
                    for item in report["results"]
                ],
                "reports": {key: str(value) for key, value in paths.items()},
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def template_live_evaluate(arguments: argparse.Namespace) -> int:
    if not 1 <= arguments.repeats <= 3:
        raise ValueError("template live repeats must be between 1 and 3")
    config = read_json(CONFIG / "models.json")
    client = model_client()
    client.vram_cap_gib = float(config["vram_cap_gib"])
    discovered = {item["name"]: item for item in client.discover()}
    requested = list(arguments.chat_model) or list(APPROVED_TEMPLATE_CHAT_MODELS)
    models = []
    for name in requested:
        record = discovered.get(name)
        if not record or "chat" not in record.get("roles", []):
            raise ModelError(f"Chat model is unavailable or incompatible: {name}")
        if int(record.get("advertised_context", 0) or 0) < arguments.context_window:
            raise ModelError(f"Chat model context is too small for {arguments.context_window}: {name}")
        models.append(record)
    embedding_model = discovered.get(arguments.embedding_model)
    if not embedding_model or "embedding" not in embedding_model.get("roles", []):
        raise ModelError(
            f"Embedding model is unavailable or incompatible: {arguments.embedding_model}"
        )
    cache_name = arguments.cache_name or arguments.name
    checkpoint_path = report_directory() / f"{cache_name}-checkpoint.json"
    identity = template_live_identity(
        arguments.stage,
        models,
        embedding_model,
        arguments.repeats,
        arguments.context_window,
    )
    state = (
        load_template_live_checkpoint(checkpoint_path, identity)
        if arguments.resume
        else {"schema_version": 1, "identity": identity, "runs": []}
    )
    if not state.get("embedding"):
        try:
            state["embedding"] = evaluate_template_embedding(
                client,
                arguments.embedding_model,
                str(embedding_model.get("digest", "")),
            )
        finally:
            try:
                client.unload(arguments.embedding_model)
            except ModelError:
                pass
        checkpoint(checkpoint_path, state)
    completed = {
        (item.get("model"), int(item.get("result", {}).get("repeat", 0)))
        for item in state["runs"]
    }
    for model in models:
        for repeat in range(1, arguments.repeats + 1):
            if (model["name"], repeat) in completed:
                continue
            before_requests = client.request_count
            before_request_bytes = client.request_bytes
            before_response_bytes = client.response_bytes
            result = evaluate_template_live_repeat(
                client,
                model["name"],
                arguments.stage,
                repeat,
                context_window=arguments.context_window,
                progress=lambda message: print(message, file=sys.stderr, flush=True),
            )
            try:
                residency = client.residency(
                    model["name"],
                    int(model.get("advertised_context", 0) or 0),
                    float(config["vram_cap_gib"]),
                    required_context=arguments.context_window,
                ).as_dict()
            except ModelError as error:
                residency = {"eligible": False, "reason": str(error)}
            state["runs"].append(
                {
                    "model": model["name"],
                    "model_digest": model.get("digest", ""),
                    "residency": residency,
                    "runtime": {
                        "endpoint_requests": client.request_count - before_requests,
                        "request_bytes": client.request_bytes - before_request_bytes,
                        "response_bytes": client.response_bytes - before_response_bytes,
                        "peak_ollama_vram_bytes": client.peak_ollama_vram_bytes,
                        "peak_whole_gpu_bytes": client.peak_gpu_used_bytes,
                    },
                    "result": result,
                }
            )
            checkpoint(checkpoint_path, state)
        try:
            client.unload(model["name"])
        except ModelError:
            pass
    report = combine_template_live(
        arguments.stage,
        models,
        state.get("embedding"),
        state["runs"],
        arguments.repeats,
    )
    report["manifest"] = {
        "identity": identity,
        "checkpoint": str(checkpoint_path),
        "implementation_digest": implementation_digest(),
        "source_drift": source_drift(),
        "vram_cap_gib": config["vram_cap_gib"],
        "seed": 0,
    }
    paths = write_template_live_report(report_directory(), arguments.name, report)
    print(
        json.dumps(
            {
                "stage": arguments.stage,
                "hard_gate_pass": report["hard_gate_pass"],
                "ranked_passing_models": report["ranked_passing_models"],
                "reports": {key: str(value) for key, value in paths.items()},
                "checkpoint": str(checkpoint_path),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def embedding_drift_evaluate(arguments: argparse.Namespace) -> int:
    documents, cases, expected_routes = email_rag_fixture()
    config = read_json(CONFIG / "models.json")
    client = model_client()
    discovered = {item["name"]: item for item in client.discover()}
    embedding = discovered.get(arguments.embedding_model)
    if not embedding or "embedding" not in embedding.get("roles", []):
        raise ModelError(
            f"Embedding model is unavailable or incompatible: {arguments.embedding_model}"
        )
    client.vram_cap_gib = float(config["vram_cap_gib"])
    try:
        report = evaluate_embedding_drift(
            client,
            arguments.embedding_model,
            str(embedding.get("digest", "")),
            documents,
            cases,
            arguments.repeats,
            arguments.batch_size,
        )
    finally:
        try:
            client.unload(arguments.embedding_model)
        except ModelError:
            pass
    report["manifest"] = {
        "synthetic_email_corpus_digest": email_fixture_digest(
            documents, cases, expected_routes
        ),
        "implementation_digest": implementation_digest(),
        "source_drift": source_drift(),
        "seed": 0,
    }
    paths = write_live_report(
        report_directory(),
        arguments.name,
        report,
        markdown_embedding_drift(report),
    )
    print(
        json.dumps(
            {
                "within_load_exact": report["within_load_exact"],
                "batch_and_order_invariant": report["batch_and_order_invariant"],
                "cross_load_exact": report["cross_load_exact"],
                "rank_quality_tolerance_pass": report["rank_quality_tolerance_pass"],
                "reports": {key: str(value) for key, value in paths.items()},
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cross_encoder_evaluate(arguments: argparse.Namespace) -> int:
    if not 3 <= arguments.repeats <= 10:
        raise ValueError("cross-encoder repeats must be between 3 and 10")
    endpoint = os.environ.get("RERANKER_URL", "")
    if not endpoint:
        raise ModelError("RERANKER_URL must point to a loopback rerank endpoint")
    reranker_model = os.environ.get("RERANKER_MODEL", "")
    reranker = RerankerClient(endpoint, reranker_model, arguments.api_format)
    reranker_info = reranker.info()
    documents, cases, expected_routes = email_rag_fixture()
    config = read_json(CONFIG / "models.json")
    client = model_client()
    discovered = {item["name"]: item for item in client.discover()}
    embedding = discovered.get(arguments.embedding_model)
    if not embedding or "embedding" not in embedding.get("roles", []):
        raise ModelError(
            f"Embedding model is unavailable or incompatible: {arguments.embedding_model}"
        )
    client.vram_cap_gib = float(config["vram_cap_gib"])
    repeats = []
    try:
        for repeat_index in range(arguments.repeats):
            print(
                f"cross-encoder repeat {repeat_index + 1}/{arguments.repeats}",
                file=sys.stderr,
                flush=True,
            )
            client.unload(arguments.embedding_model)
            repeats.append(
                evaluate_cross_encoder_repeat(
                    client,
                    reranker,
                    arguments.embedding_model,
                    documents,
                    cases,
                    repeat_index + 1,
                    arguments.candidate_count,
                )
            )
    finally:
        try:
            client.unload(arguments.embedding_model)
        except ModelError:
            pass
    report = combine_cross_encoder_repeats(
        repeats, reranker_model or str(reranker_info.get("model_id", "")), reranker_info
    )
    execution_device = os.environ.get("RERANKER_DEVICE", "unknown")
    configured_vram = os.environ.get("RERANKER_VRAM_BYTES")
    report["deployment"] = {
        "api_format": arguments.api_format,
        "endpoint": endpoint,
        "execution_device": execution_device,
        "model_vram_bytes": (
            int(configured_vram)
            if configured_vram is not None
            else (0 if execution_device == "cpu" else None)
        ),
    }
    report["manifest"] = {
        "synthetic_email_corpus_digest": email_fixture_digest(
            documents, cases, expected_routes
        ),
        "embedding_model": {
            "name": arguments.embedding_model,
            "digest": str(embedding.get("digest", "")),
        },
        "implementation_digest": implementation_digest(),
        "source_drift": source_drift(),
        "seed": 0,
    }
    paths = write_live_report(
        report_directory(),
        arguments.name,
        report,
        markdown_cross_encoder(report),
    )
    print(
        json.dumps(
            {
                "candidate_decision": report["candidate_decision"],
                "safety_pass": report["safety_pass"],
                "reports": {key: str(value) for key, value in paths.items()},
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def answer_parameter_evaluate(arguments: argparse.Namespace) -> int:
    config = read_json(CONFIG / "models.json")
    client = model_client()
    discovered = {item["name"]: item for item in client.discover()}
    chat = discovered.get(arguments.chat_model)
    if not chat or "chat" not in chat.get("roles", []):
        raise ModelError(f"Chat model is unavailable or incompatible: {arguments.chat_model}")
    client.vram_cap_gib = float(config["vram_cap_gib"])
    try:
        report = evaluate_answer_parameters(
            client,
            arguments.chat_model,
            str(chat.get("digest", "")),
            arguments.repeats,
        )
    finally:
        try:
            client.unload(arguments.chat_model)
        except ModelError:
            pass
    report["manifest"] = {
        "thread_fixture_digest": THREAD_FIXTURE_DIGESTS[50],
        "implementation_digest": implementation_digest(),
        "source_drift": source_drift(),
        "seed": 0,
    }
    paths = write_live_report(
        report_directory(),
        arguments.name,
        report,
        markdown_answer_parameters(report),
    )
    print(
        json.dumps(
            {
                "recommendations": report["recommendations"],
                "runtime": report["runtime"],
                "reports": {key: str(value) for key, value in paths.items()},
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def oversized_email_evaluate(arguments: argparse.Namespace) -> int:
    deterministic = evaluate_oversized_email_deterministic(
        arguments.email_bytes,
        arguments.fact_count,
        arguments.page_chars,
    )
    report: dict[str, Any] = {
        "schema_version": 1,
        "title": "Oversized Single-Email Evaluation",
        "production_ready": False,
        "deterministic": deterministic,
        "decision": deterministic["decision"],
    }
    if arguments.stress_suite:
        report["stress_suite"] = evaluate_oversized_stress_suite()
    if arguments.live:
        config = read_json(CONFIG / "models.json")
        client = model_client()
        discovered = {item["name"]: item for item in client.discover()}
        chat = discovered.get(arguments.chat_model)
        if not chat or "chat" not in chat.get("roles", []):
            raise ModelError(
                f"Chat model is unavailable or incompatible: {arguments.chat_model}"
            )
        advertised_context = int(chat.get("advertised_context", 0) or 0)
        client.vram_cap_gib = float(config["vram_cap_gib"])
        try:
            report["live"] = evaluate_oversized_email_live(
                client,
                arguments.chat_model,
                str(chat.get("digest", "")),
                advertised_context,
                target_bytes=arguments.email_bytes,
                fact_count=arguments.fact_count,
                context_window=arguments.context_window,
                page_chars=arguments.page_chars,
                repeats=arguments.repeats,
                progress=lambda message: print(message, file=sys.stderr, flush=True),
            )
        finally:
            try:
                client.unload(arguments.chat_model)
            except ModelError:
                pass
    report["manifest"] = {
        "fixture_version": "synthetic-oversized-email-v1",
        "fixture_digest": oversized_fixture_digest(
            arguments.email_bytes, arguments.fact_count
        ),
        "implementation_digest": implementation_digest(),
        "source_drift": source_drift(),
        "seed": 0,
    }
    paths = write_oversized_email_report(
        report_directory(), arguments.name, report
    )
    summary: dict[str, Any] = {
        "deterministic": {
            "targeted_top_8_pass": deterministic["retrieval"]["targeted_all_pass"],
            "exhaustive_top_8_recall": deterministic["retrieval"]["exhaustive_top_8"]["metrics"]["fact_recall"],
            "bounded_map_recall": deterministic["bounded_map_reduce"]["metrics"]["fact_recall"],
            "stress_result_pages": deterministic["high_cardinality_stress"]["result_page_count"],
        },
        "reports": {key: str(value) for key, value in paths.items()},
    }
    if report.get("live"):
        summary["live_stability"] = report["live"]["stability"]
        summary["runtime"] = report["live"]["runtime"]
    if report.get("stress_suite"):
        summary["stress_suite"] = {
            "hard_gate_pass": report["stress_suite"]["hard_gate_pass"],
            "suite_digest": report["stress_suite"]["suite_digest"],
            "lane_count": len(report["stress_suite"]["lanes"]),
        }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def oversized_design_evaluate(arguments: argparse.Namespace) -> int:
    deterministic = evaluate_oversized_designs_deterministic()
    report: dict[str, Any] = {
        "schema_version": 1,
        "title": "Oversized Email Architecture Design Matrix",
        "production_ready": False,
        "deterministic": deterministic,
    }
    if arguments.live:
        config = read_json(CONFIG / "models.json")
        client = model_client()
        discovered = {item["name"]: item for item in client.discover()}
        chat = discovered.get(arguments.chat_model)
        if not chat or "chat" not in chat.get("roles", []):
            raise ModelError(
                f"Chat model is unavailable or incompatible: {arguments.chat_model}"
            )
        client.vram_cap_gib = float(config["vram_cap_gib"])
        try:
            report["live"] = evaluate_oversized_designs_live(
                client,
                arguments.chat_model,
                str(chat.get("digest", "")),
                int(chat.get("advertised_context", 0) or 0),
                repeats=arguments.repeats,
                progress=lambda message: print(message, file=sys.stderr, flush=True),
            )
        finally:
            try:
                client.unload(arguments.chat_model)
            except ModelError:
                pass
    report["manifest"] = {
        "fixture_version": "synthetic-oversized-email-v1",
        "fixture_digest": oversized_fixture_digest(),
        "implementation_digest": implementation_digest(),
        "source_drift": source_drift(),
        "seed": 0,
    }
    paths = write_oversized_design_report(
        report_directory(), arguments.name, report
    )
    summary: dict[str, Any] = {
        "fixture": deterministic["fixture"],
        "decision": deterministic["decision"],
        "reports": {key: str(value) for key, value in paths.items()},
    }
    if report.get("live"):
        summary["live_stability"] = report["live"]["stability"]
        summary["runtime"] = report["live"]["runtime"]
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def query(arguments: argparse.Namespace) -> int:
    ensure_corpus()
    documents = load_documents(DATA / "documents.jsonl")
    variant = baseline_variant(
        chunking=arguments.chunking,
        retrieval=arguments.retrieval,
        graph=arguments.graph,
        tools=arguments.tools,
        max_chunks=(
            4096
            if arguments.chunking in {"structure-aware", "sentence-window"}
            else 24
        ),
    )
    scope = Scope(arguments.tenant, arguments.collection)
    with Index() as index:
        pipeline = Pipeline(index, variant)
        pipeline.ingest(documents)
        output = pipeline.query(arguments.query, scope)
    print(json.dumps(output.as_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def benchmark(arguments: argparse.Namespace) -> int:
    if arguments.size < 1:
        raise ValueError("benchmark size must be positive")
    sizes = [1000, 10_000, 100_000] if arguments.full else [arguments.size]
    variant = baseline_variant(dense_candidates=arguments.dense_candidates)
    results = [run_benchmark(size, variant) for size in sizes]
    name = arguments.name
    directory = report_directory()
    payload = {
        "schema_version": 1,
        "title": "Deterministic pipeline benchmark",
        "variant": variant.as_dict(),
        "results": results,
    }
    checkpoint(directory / f"{name}.json", payload)
    lines = [
        "# Deterministic Pipeline Benchmark",
        "",
        "| Documents | Ingest wall s | Ingest CPU s | Docs/s | Query p50 ms | Query p95 ms | Peak RSS KiB | DB bytes |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in results:
        lines.append(
            f"| {item['size']} | {item['ingest_wall_seconds']:.3f} | {item['ingest_cpu_seconds']:.3f} | "
            f"{item['documents_per_second']:.1f} | {item['query_p50_ms']:.3f} | {item['query_p95_ms']:.3f} | "
            f"{item['peak_rss_kib']} | {item['database_bytes']} |"
        )
    destination = directory / f"{name}.md"
    temporary = destination.with_suffix(".md.tmp")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temporary.replace(destination)
    print(json.dumps({"results": results, "report": str(destination)}, indent=2))
    return 0


def model_client() -> OllamaClient:
    return OllamaClient(os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))


def models_prepare(_: argparse.Namespace) -> int:
    config = read_json(CONFIG / "models.json")
    output = report_directory() / "prepared-models.json"
    result = prepare_allowlisted_models(
        model_client(), config, output, lambda message: print(message, flush=True)
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def models_probe(arguments: argparse.Namespace) -> int:
    config = read_json(CONFIG / "models.json")
    client = model_client()
    records = client.discover()
    selected = set(config["download_allowlist"]) | set(config["installed_controls"])
    requested = set(arguments.model)
    unknown_requested = requested - selected
    if unknown_requested:
        raise ModelError(
            f"Requested models are not candidates or controls: {', '.join(sorted(unknown_requested))}"
        )
    for record in records:
        if requested and not (
            record["name"] in requested
            or record["name"].removesuffix(":latest") in requested
        ):
            record["residency"] = {"eligible": False, "reason": "NOT_REQUESTED"}
            continue
        if (
            record["name"] not in selected
            and record["name"].removesuffix(":latest") not in selected
        ):
            record["residency"] = {"eligible": False, "reason": "NOT_SELECTED_OR_CONTROL"}
            continue
        if record.get("discovery_error"):
            record["residency"] = {
                "eligible": False,
                "reason": f"DISCOVERY_FAILED:{record['discovery_error']}",
            }
            continue
        if not arguments.no_warmup:
            print(f"probing {record['name']}...", file=sys.stderr, flush=True)
            try:
                if "embedding" in record["roles"]:
                    client.embed(record["name"], ["deterministic residency probe"])
                else:
                    client.chat(
                        record["name"],
                        [{"role": "user", "content": "Return {\"status\":\"ok\"}."}],
                        context_window=int(config["standard_context"]),
                        max_output_tokens=32,
                        temperature=0,
                    )
                record["residency"] = client.residency(
                    record["name"], record["advertised_context"], float(config["vram_cap_gib"])
                ).as_dict()
            except ModelError as error:
                record["residency"] = {"eligible": False, "reason": f"PROBE_FAILED:{error}"}
            finally:
                try:
                    client.unload(record["name"])
                except ModelError:
                    pass
            print(
                f"{record['name']}: {record['residency'].get('reason', 'UNKNOWN')}",
                file=sys.stderr,
                flush=True,
            )
        else:
            record["residency"] = {"eligible": False, "reason": "NOT_MEASURED"}
    result = {"schema_version": 1, "models": records, "vram_cap_gib": config["vram_cap_gib"]}
    checkpoint(report_directory() / "model-probe.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def enumerate_variants(
    chat_models: list[str],
    embedding_models: list[str],
    tool_capable_models: set[str] | None = None,
    endpoint_reranker: bool = False,
) -> list[PipelineVariant]:
    dimensions = read_json(CONFIG / "candidates.json")["dimensions"]
    base = baseline_variant()
    variants = []
    keys = [
        "chunking",
        "retrieval",
        "dense_candidates",
        "reranking",
        "graph",
        "tools",
        "prompt",
    ]
    for values in product(*(dimensions[key] for key in keys)):
        choices = dict(zip(keys, values, strict=True))
        if choices["reranking"] == "endpoint" and not endpoint_reranker:
            continue
        if (
            choices["retrieval"] not in {"dense", "hybrid"}
            and choices["dense_candidates"] != "lsh"
        ):
            continue
        compatible_embeddings = (
            embedding_models
            if choices["retrieval"] in {"dense", "hybrid"} or choices["reranking"] == "embedding"
            else ["deterministic-local-v1"]
        )
        for model, embedding_model in product(chat_models, compatible_embeddings):
            if (
                tool_capable_models is not None
                and choices["tools"] != "none"
                and model not in tool_capable_models
            ):
                continue
            candidate = replace(
                base,
                id="candidate-pending",
                model=model,
                embedding_model=embedding_model,
                max_chunks=(
                    4096
                    if choices["chunking"] in {"structure-aware", "sentence-window"}
                    else base.max_chunks
                ),
                **choices,
            )
            identity = candidate.as_dict()
            identity.pop("id")
            identity.pop("schema_version")
            variants.append(
                PipelineVariant.from_dict(
                    replace(
                        candidate, id=f"candidate-{content_digest(identity)[:12]}"
                    ).as_dict()
                )
            )
    return variants


def select_calibration_variants(
    variants: list[PipelineVariant], limit: int
) -> list[PipelineVariant]:
    """Select a deterministic set that covers models and categorical choices."""
    if limit < 1:
        raise ValueError("calibration variant limit must be positive")
    if len(variants) <= limit:
        return list(variants)
    fields = (
        "model",
        "embedding_model",
        "chunking",
        "retrieval",
        "dense_candidates",
        "reranking",
        "graph",
        "tools",
        "prompt",
    )

    def features(variant: PipelineVariant) -> set[tuple[str, str]]:
        return {(field, str(getattr(variant, field))) for field in fields}

    remaining = sorted(variants, key=lambda item: item.id)
    uncovered = set().union(*(features(variant) for variant in remaining))
    selected: list[PipelineVariant] = []
    while remaining and len(selected) < limit:
        candidate = max(
            remaining,
            key=lambda item: (len(features(item) & uncovered), item.id),
        )
        selected.append(candidate)
        uncovered -= features(candidate)
        remaining.remove(candidate)
        if not uncovered:
            break
    if remaining and len(selected) < limit:
        slots = limit - len(selected)
        step = len(remaining) / slots
        indexes = {min(len(remaining) - 1, int(index * step)) for index in range(slots)}
        selected.extend(remaining[index] for index in sorted(indexes))
    return selected[:limit]


def _loaded_residency(client: OllamaClient, names: set[str], contexts: dict[str, int], cap: float) -> dict[str, Any]:
    records = []
    for name in sorted(names):
        records.append(client.residency(name, contexts.get(name, 0), cap).as_dict())
    total = nvidia_total_used_bytes()
    configuration_vram = sum(record["ollama_vram_bytes"] for record in records)
    configuration_within_cap = configuration_vram <= cap * 1024**3
    eligible = bool(records) and all(record["eligible"] for record in records) and configuration_within_cap
    reasons = {record["reason"] for record in records if not record["eligible"]}
    if not configuration_within_cap:
        reasons.add("CONFIGURATION_VRAM_CAP_EXCEEDED")
    return {
        "models": records,
        "configuration_ollama_vram_bytes": configuration_vram,
        "total_gpu_used_bytes": total,
        "peak_gpu_used_bytes": client.peak_gpu_used_bytes,
        "peak_ollama_vram_bytes": client.peak_ollama_vram_bytes,
        "eligible": eligible,
        "reason": "ELIGIBLE" if eligible else ",".join(sorted(reasons)),
    }


def partition_variants_by_vram(
    variants: list[PipelineVariant],
    measured_vram: dict[str, int],
    cap_gib: float,
) -> tuple[list[PipelineVariant], list[dict[str, Any]]]:
    """Split live variants using the summed, individually measured Ollama allocation."""
    cap_bytes = int(cap_gib * 1024**3)
    eligible: list[PipelineVariant] = []
    rejected: list[dict[str, Any]] = []
    for variant in variants:
        names = {variant.model}
        if variant.embedding_model != "deterministic-local-v1":
            names.add(variant.embedding_model)
        missing = sorted(name for name in names if name not in measured_vram)
        configuration_vram = (
            None if missing else sum(measured_vram[name] for name in names)
        )
        reason = None
        if missing:
            reason = "VRAM_NOT_MEASURED"
        elif configuration_vram is not None and configuration_vram > cap_bytes:
            reason = "CONFIGURATION_VRAM_CAP_EXCEEDED"
        if reason:
            rejected.append(
                {
                    "variant_id": variant.id,
                    "model": variant.model,
                    "embedding_model": variant.embedding_model,
                    "configuration_ollama_vram_bytes": configuration_vram,
                    "vram_cap_bytes": cap_bytes,
                    "reason": reason,
                    "missing_models": missing,
                }
            )
        else:
            eligible.append(variant)
    return eligible, rejected


def _matrix_variant_result(
    documents: list[Document],
    cases: list[EvaluationCase],
    variant: PipelineVariant,
    client: OllamaClient | None,
    reranker: RerankerClient | None,
    contexts: dict[str, int],
    cap: float,
) -> dict[str, Any]:
    names = {variant.model}
    if variant.embedding_model != "deterministic-local-v1":
        names.add(variant.embedding_model)
    if client:
        client.peak_gpu_used_bytes = None
        client.peak_ollama_vram_bytes = 0
    try:
        result = evaluate_variant(documents, cases, variant, client, reranker)
    except Exception as error:
        result = {
            "schema_version": 1,
            "variant": variant.as_dict(),
            "ingest": {},
            "performance": {},
            "aggregate": {
                "quality_score": 0.0,
                "hard_gate_pass": False,
                "quality_pass": False,
                "production_ready": False,
                "hard_failures": ["PIPELINE_ERROR"],
                "quality_failures": [],
            },
            "cases": [],
            "error": f"{type(error).__name__}: {error}",
        }
    if client:
        try:
            try:
                residency = _loaded_residency(client, names, contexts, cap)
            except ModelError as error:
                residency = {
                    "models": [],
                    "configuration_ollama_vram_bytes": None,
                    "total_gpu_used_bytes": nvidia_total_used_bytes(),
                    "peak_gpu_used_bytes": client.peak_gpu_used_bytes,
                    "peak_ollama_vram_bytes": client.peak_ollama_vram_bytes,
                    "eligible": False,
                    "reason": f"RESIDENCY_MEASUREMENT_FAILED:{error}",
                }
            result["residency"] = residency
            if not residency["eligible"]:
                result["aggregate"]["hard_gate_pass"] = False
                result["aggregate"]["quality_pass"] = False
                result["aggregate"]["hard_failures"] = sorted(
                    set(result["aggregate"].get("hard_failures", []) + [residency["reason"]])
                )
        finally:
            for name in sorted(names):
                try:
                    client.unload(name)
                except ModelError:
                    pass
    return result


def matrix(arguments: argparse.Namespace) -> int:
    if not 1 <= arguments.repeats <= 20:
        raise ValueError("repeats must be between 1 and 20")
    if arguments.model and not arguments.live:
        raise ValueError("--model requires --live")
    corpus_manifest = ensure_corpus()
    documents = load_documents(DATA / "documents.jsonl")
    all_cases = load_cases(DATA / "cases.jsonl")
    candidate_config = read_json(CONFIG / "candidates.json")
    calibration_ids = set(candidate_config["calibration_case_ids"])
    calibration_cases = [case for case in all_cases if case.id in calibration_ids]
    config = read_json(CONFIG / "models.json")
    requested_models = set(arguments.model)
    configured_models = set(config["download_allowlist"]) | set(
        config["installed_controls"]
    )
    unknown_requested = requested_models - configured_models
    if unknown_requested:
        raise ModelError(
            f"Requested models are not candidates or controls: {', '.join(sorted(unknown_requested))}"
        )
    client = model_client() if arguments.live else None
    if client:
        client.vram_cap_gib = float(config["vram_cap_gib"])
    compatibility: list[dict[str, Any]] = []
    reranker_url = os.environ.get("RERANKER_URL", "")
    reranker = (
        RerankerClient(reranker_url, os.environ.get("RERANKER_MODEL", ""))
        if reranker_url
        else None
    )
    if not reranker:
        compatibility.append(
            {
                "component": "endpoint-reranker",
                "status": "incompatible",
                "reason": "RERANKER_URL_NOT_CONFIGURED",
            }
        )
    contexts: dict[str, int] = {}
    measured_vram: dict[str, int] = {}
    if client:
        discovered = client.discover()
        chat_models = []
        embedding_models = ["deterministic-local-v1"]
        tool_capable_models: set[str] = set()
        selected_names = set(config["download_allowlist"]) | set(config["installed_controls"])
        discovered_selected: set[str] = set()
        for record in discovered:
            canonical_name = record["name"].removesuffix(":latest")
            selected_name = (
                record["name"]
                if record["name"] in selected_names
                else canonical_name
                if canonical_name in selected_names
                else None
            )
            if selected_name is None:
                compatibility.append({"model": record["name"], "status": "ignored", "reason": "NOT_SELECTED_OR_CONTROL"})
                continue
            if requested_models and selected_name not in requested_models:
                compatibility.append(
                    {"model": record["name"], "status": "ignored", "reason": "NOT_REQUESTED"}
                )
                continue
            discovered_selected.add(selected_name)
            contexts[record["name"]] = record["advertised_context"]
            if record.get("discovery_error"):
                compatibility.append(
                    {
                        "model": record["name"],
                        "status": "incompatible",
                        "reason": f"DISCOVERY_FAILED:{record['discovery_error']}",
                    }
                )
                continue
            if record["advertised_context"] < int(config["standard_context"]):
                compatibility.append({"model": record["name"], "status": "compatibility-lane", "reason": "CONTEXT_INCOMPATIBLE"})
                continue
            print(f"preflighting {record['name']}...", file=sys.stderr, flush=True)
            try:
                if "embedding" in record["roles"]:
                    client.embed(record["name"], ["matrix capability probe"])
                else:
                    client.chat(
                        record["name"],
                        [{"role": "user", "content": "Return {\"status\":\"ok\"}."}],
                        context_window=int(config["standard_context"]),
                        max_output_tokens=32,
                        temperature=0,
                    )
                residency = client.residency(
                    record["name"],
                    record["advertised_context"],
                    float(config["vram_cap_gib"]),
                )
                record["preflight_residency"] = residency.as_dict()
            except ModelError as error:
                compatibility.append(
                    {
                        "model": record["name"],
                        "status": "incompatible",
                        "reason": str(error),
                    }
                )
                continue
            finally:
                try:
                    client.unload(record["name"])
                except ModelError:
                    pass
            if not residency.eligible:
                compatibility.append(
                    {
                        "model": record["name"],
                        "status": "incompatible",
                        "reason": residency.reason,
                    }
                )
                continue
            measured_vram[record["name"]] = residency.ollama_vram_bytes
            if "embedding" in record["roles"]:
                embedding_models.append(record["name"])
            else:
                chat_models.append(record["name"])
                if record["tool_template"]:
                    tool_capable_models.add(record["name"])
                else:
                    compatibility.append(
                        {
                            "model": record["name"],
                            "status": "limited",
                            "reason": "NATIVE_TOOLS_UNSUPPORTED;NO_TOOL_VARIANTS_ONLY",
                        }
                    )
        expected_names = requested_models or selected_names
        missing = sorted(expected_names - discovered_selected)
        compatibility.extend({"model": name, "status": "incompatible", "reason": "NOT_INSTALLED"} for name in missing)
    else:
        chat_models = ["deterministic"]
        embedding_models = ["deterministic-local-v1"]
        tool_capable_models = {"deterministic"}
    variants = enumerate_variants(
        chat_models,
        list(dict.fromkeys(embedding_models)),
        tool_capable_models,
        bool(reranker),
    )
    if arguments.stress_32k:
        stress_variants = []
        for variant in variants:
            if variant.model == "deterministic" or contexts.get(variant.model, 0) >= int(config["optional_stress_context"]):
                identity = {**variant.as_dict(), "context_window": int(config["optional_stress_context"])}
                stress_variants.append(
                    replace(
                        variant,
                        id=f"{variant.id}-ctx32k-{content_digest(identity)[:8]}",
                        context_window=int(config["optional_stress_context"]),
                    )
                )
        variants.extend(stress_variants)
    enumerated_variants = variants
    rejected_variants: list[dict[str, Any]] = []
    if client:
        variants, rejected_variants = partition_variants_by_vram(
            enumerated_variants,
            measured_vram,
            float(config["vram_cap_gib"]),
        )
    eligible_variants = variants
    if arguments.exhaustive:
        calibration_variants = eligible_variants
        survivor_limit = len(eligible_variants)
    else:
        calibration_limit = (
            arguments.calibration_limit
            if arguments.calibration_limit is not None
            else int(candidate_config["adaptive_calibration_variants"])
        )
        calibration_variants = select_calibration_variants(
            eligible_variants,
            calibration_limit,
        )
        survivor_limit = (
            arguments.survivor_limit
            if arguments.survivor_limit is not None
            else int(candidate_config["adaptive_full_survivors"])
        )
        if survivor_limit < 1:
            raise ValueError("survivor limit must be positive")
    directory = report_directory()
    model_signature_records = [
        {
            key: record.get(key)
            for key in (
                "name",
                "digest",
                "size",
                "family",
                "parameter_size",
                "quantization",
                "advertised_context",
                "roles",
                "capabilities",
                "tool_template",
                "discovery_error",
            )
        }
        for record in (discovered if client else [])
    ]
    run_signature = content_digest(
        {
            "corpus": corpus_manifest,
            "implementation_digest": implementation_digest(),
            "baseline": read_json(CONFIG / "tb-current.json"),
            "candidates": read_json(CONFIG / "candidates.json"),
            "models": config,
            "live": arguments.live,
            "repeats": arguments.repeats,
            "stress_32k": arguments.stress_32k,
            "discovered_models": model_signature_records,
            "reranker_url": reranker_url,
            "reranker_model": os.environ.get("RERANKER_MODEL", ""),
            "requested_models": sorted(requested_models),
            "exhaustive": arguments.exhaustive,
            "enumerated_variant_digests": [
                variant.id for variant in enumerated_variants
            ],
            "eligible_variant_digests": [
                variant.id for variant in eligible_variants
            ],
            "rejected_variants": rejected_variants,
            "calibration_variant_digests": [
                variant.id for variant in calibration_variants
            ],
            "survivor_limit": survivor_limit,
        }
    )
    if arguments.dry_run:
        plan_path = directory / f"{arguments.name}-plan.json"
        plan = {
            "schema_version": 1,
            "run_signature": run_signature,
            "implementation_digest": implementation_digest(),
            "enumerated_variant_count": len(enumerated_variants),
            "enumerated_variant_digests": [variant.id for variant in enumerated_variants],
            "eligible_variant_count": len(eligible_variants),
            "eligible_variant_digests": [variant.id for variant in eligible_variants],
            "rejected_variant_count": len(rejected_variants),
            "rejected_variants": rejected_variants,
            "calibration_variant_count": len(calibration_variants),
            "calibration_variants": [variant.as_dict() for variant in calibration_variants],
            "selection": "exhaustive" if arguments.exhaustive else "coverage-balanced-v1",
            "full_survivor_limit": survivor_limit,
            "compatibility": compatibility,
            "discovered_models": discovered if client else [],
        }
        checkpoint(plan_path, plan)
        print(
            json.dumps(
                {
                    "enumerated_variant_count": len(enumerated_variants),
                    "eligible_variant_count": len(eligible_variants),
                    "rejected_variant_count": len(rejected_variants),
                    "calibration_variant_count": len(calibration_variants),
                    "compatibility": compatibility,
                    "plan": str(plan_path),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    checkpoint_path = directory / f"{arguments.name}-checkpoint.json"
    state = {
        "schema_version": 1,
        "run_signature": run_signature,
        "completed": {},
        "compatibility": compatibility,
    }
    if arguments.resume and checkpoint_path.is_file():
        state = read_json(checkpoint_path)
        if state.get("run_signature") != run_signature:
            raise ModelError(
                "Checkpoint inputs changed; use a new --name or pass --no-resume"
            )
    else:
        checkpoint(checkpoint_path, state)
    completed: dict[str, Any] = state.setdefault("completed", {})
    calibration_results: list[dict[str, Any]] = []
    survivors: list[PipelineVariant] = []
    for calibration_index, variant in enumerate(calibration_variants, 1):
        key = f"calibration:{variant.id}"
        if key in completed:
            result = completed[key]
        else:
            print(
                f"calibration {calibration_index}/{len(calibration_variants)}: {variant.id}",
                file=sys.stderr,
                flush=True,
            )
            result = _matrix_variant_result(
                documents,
                calibration_cases,
                variant,
                client,
                reranker,
                contexts,
                float(config["vram_cap_gib"]),
            )
            result["phase"] = "calibration"
            completed[key] = result
            checkpoint(checkpoint_path, state)
        calibration_results.append(result)
        if result.get("aggregate", {}).get("hard_gate_pass"):
            survivors.append(variant)
    survivors.sort(
        key=lambda variant: (
            -float(completed[f"calibration:{variant.id}"]["aggregate"].get("quality_score", 0)),
            float(completed[f"calibration:{variant.id}"]["aggregate"].get("latency_p50_ms", float("inf"))),
            variant.id,
        )
    )
    survivors = survivors[:survivor_limit]
    calibration_paths = write_report(
        directory,
        f"{arguments.name}-calibration",
        calibration_results,
        {
            "corpus": corpus_manifest,
            "compatibility": compatibility,
            "enumerated_variants": len(enumerated_variants),
            "eligible_variants": len(eligible_variants),
            "rejected_variants": len(rejected_variants),
            "calibration_variants": len(calibration_variants),
            "selected_survivors": [variant.id for variant in survivors],
            "selection": "exhaustive" if arguments.exhaustive else "coverage-balanced-v1",
            "seed": 0,
        },
    )
    full_results: list[dict[str, Any]] = []
    for survivor_index, variant in enumerate(survivors, 1):
        for repeat in range(arguments.repeats):
            key = f"full:{variant.id}:{repeat}"
            if key in completed:
                result = completed[key]
            else:
                print(
                    f"full {survivor_index}/{len(survivors)} repeat {repeat + 1}/{arguments.repeats}: {variant.id}",
                    file=sys.stderr,
                    flush=True,
                )
                result = _matrix_variant_result(
                    documents,
                    all_cases,
                    variant,
                    client,
                    reranker,
                    contexts,
                    float(config["vram_cap_gib"]),
                )
                result["phase"] = "full"
                result["repeat"] = repeat
                completed[key] = result
                checkpoint(checkpoint_path, state)
            full_results.append(result)
    ranked_results = combine_repeats(full_results) if full_results else calibration_results
    paths = write_report(
        directory,
        arguments.name,
        ranked_results,
        {
            "corpus": corpus_manifest,
            "source_drift": source_drift(),
            "models": config,
            "compatibility": compatibility,
            "discovered_models": discovered if client else [],
            "enumerated_variants": len(enumerated_variants),
            "eligible_variants": len(eligible_variants),
            "rejected_variants": len(rejected_variants),
            "calibration_variants": len(calibration_variants),
            "survivors": len(survivors),
            "repeats": arguments.repeats,
            "seed": 0,
        },
    )
    print(
        json.dumps(
            {
                "enumerated_variants": len(enumerated_variants),
                "calibration_variants": len(calibration_variants),
                "survivors": len(survivors),
                "calibration_reports": {
                    key: str(value) for key, value in calibration_paths.items()
                },
                "reports": {key: str(value) for key, value in paths.items()},
            },
            indent=2,
        )
    )
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="tb-ai-lab")
    commands = result.add_subparsers(dest="command", required=True)
    build_parser = commands.add_parser("build")
    build_parser.set_defaults(handler=build)

    evaluate_parser = commands.add_parser("evaluate")
    evaluate_parser.add_argument("--calibration", action="store_true")
    evaluate_parser.add_argument("--optimized", action="store_true")
    evaluate_parser.add_argument("--name", type=artifact_name, default="baseline-evaluation")
    evaluate_parser.set_defaults(handler=evaluate)

    rag_parser = commands.add_parser("rag-evaluate")
    rag_parser.add_argument("--top-k", type=int, default=8)
    rag_parser.add_argument(
        "--name", type=artifact_name, default="staged-rag-evaluation"
    )
    rag_parser.set_defaults(handler=rag_evaluate)

    contextual_rag_parser = commands.add_parser("contextual-rag-evaluate")
    contextual_rag_parser.add_argument("--top-k", type=int, default=8)
    contextual_rag_parser.add_argument(
        "--chat-model", default="qwen3:8b"
    )
    contextual_rag_parser.add_argument(
        "--embedding-model", default="qwen3-embedding:4b"
    )
    contextual_rag_parser.add_argument(
        "--resume", action=argparse.BooleanOptionalAction, default=True
    )
    contextual_rag_parser.add_argument(
        "--name", type=artifact_name, default="contextual-rag-evaluation"
    )
    contextual_rag_parser.add_argument(
        "--cache-name",
        type=artifact_name,
        help="reuse a named context cache while writing a different report",
    )
    contextual_rag_parser.set_defaults(handler=contextual_rag_evaluate)

    context_ladder_parser = commands.add_parser("context-ladder-evaluate")
    context_ladder_parser.add_argument(
        "--chat-model", action="append", default=[], help="Loopback chat model for an opt-in live screen"
    )
    context_ladder_parser.add_argument("--repeats", type=int, default=1)
    context_ladder_parser.add_argument("--live", action="store_true")
    context_ladder_parser.add_argument(
        "--include-large-pages",
        action="store_true",
        help="Run bounded page metadata extraction for synthetic sources above 48K characters",
    )
    context_ladder_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write the deterministic report and live-call plan without contacting Ollama",
    )
    context_ladder_parser.add_argument("--no-resume", action="store_true")
    context_ladder_parser.add_argument("--cache-name", type=artifact_name)
    context_ladder_parser.add_argument(
        "--name", type=artifact_name, default="context-ladder-evaluation"
    )
    context_ladder_parser.set_defaults(handler=context_ladder_evaluate)

    related_parser = commands.add_parser("related-email-rag-evaluate")
    related_parser.add_argument(
        "--chat-model",
        action="append",
        default=[],
        help="Loopback chat model for the staged whole-email screen",
    )
    related_parser.add_argument("--repeats", type=int, default=1)
    related_parser.add_argument("--live", action="store_true")
    related_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write deterministic results and the exact live-call plan without Ollama",
    )
    related_parser.add_argument("--no-resume", action="store_true")
    related_parser.add_argument("--cache-name", type=artifact_name)
    related_parser.add_argument(
        "--name", type=artifact_name, default="related-email-rag-evaluation"
    )
    related_parser.set_defaults(handler=related_email_rag_evaluate)

    slot_candidate_parser = commands.add_parser("slot-candidate-evaluate")
    slot_candidate_parser.add_argument(
        "--chat-model",
        action="append",
        default=[],
        help="Loopback chat model for host-owned slot candidate selection",
    )
    slot_candidate_parser.add_argument("--repeats", type=int, default=1)
    slot_candidate_parser.add_argument("--live", action="store_true")
    slot_candidate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write deterministic candidate results and the live-call plan without Ollama",
    )
    slot_candidate_parser.add_argument("--no-resume", action="store_true")
    slot_candidate_parser.add_argument("--cache-name", type=artifact_name)
    slot_candidate_parser.add_argument(
        "--name", type=artifact_name, default="slot-candidate-evaluation"
    )
    slot_candidate_parser.set_defaults(handler=slot_candidate_evaluate)

    structured_memory_parser = commands.add_parser("structured-memory-evaluate")
    structured_memory_parser.add_argument(
        "--chat-model",
        action="append",
        default=[],
        help="Loopback chat model for candidate-only structured thread memory",
    )
    structured_memory_parser.add_argument("--repeats", type=int, default=1)
    structured_memory_parser.add_argument("--live", action="store_true")
    structured_memory_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write deterministic structured-memory results and live plan without Ollama",
    )
    structured_memory_parser.add_argument("--no-resume", action="store_true")
    structured_memory_parser.add_argument("--cache-name", type=artifact_name)
    structured_memory_parser.add_argument(
        "--name", type=artifact_name, default="structured-memory-evaluation"
    )
    structured_memory_parser.set_defaults(handler=structured_memory_evaluate)

    qualification_parser = commands.add_parser("structured-memory-qualify")
    qualification_parser.add_argument("--chat-model", action="append", default=[])
    qualification_parser.add_argument("--repeats", type=int, default=3)
    qualification_parser.add_argument("--live", action="store_true")
    qualification_parser.add_argument("--dry-run", action="store_true")
    qualification_parser.add_argument("--no-resume", action="store_true")
    qualification_parser.add_argument("--cache-name", type=artifact_name)
    qualification_parser.add_argument(
        "--name",
        type=artifact_name,
        default="structured-memory-qualification",
    )
    qualification_parser.set_defaults(handler=structured_memory_qualify)

    thread_memory_parser = commands.add_parser("thread-memory-evaluate")
    thread_memory_parser.add_argument(
        "--chat-model",
        action="append",
        default=[],
        help="chat model to evaluate; repeatable (defaults to qwen3:8b and phi4:14b-q8_0)",
    )
    thread_memory_parser.add_argument(
        "--embedding-model", default="qwen3-embedding:4b"
    )
    thread_memory_parser.add_argument("--repeats", type=int, default=3)
    thread_memory_parser.add_argument(
        "--resume", action=argparse.BooleanOptionalAction, default=True
    )
    thread_memory_parser.add_argument("--dry-run", action="store_true")
    thread_memory_parser.add_argument(
        "--smoke",
        action="store_true",
        help="run one four-message, two-placement live validation before the full matrix",
    )
    thread_memory_parser.add_argument(
        "--name", type=artifact_name, default="thread-memory-evaluation"
    )
    thread_memory_parser.add_argument(
        "--cache-name",
        type=artifact_name,
        help="reuse compatible per-stream generation caches under a different report name",
    )
    thread_memory_parser.set_defaults(handler=thread_memory_evaluate)

    thread_memory_hardening_parser = commands.add_parser(
        "thread-memory-hardening-evaluate"
    )
    thread_memory_hardening_parser.add_argument(
        "--name", type=artifact_name, default="thread-memory-hardening"
    )
    thread_memory_hardening_parser.set_defaults(
        handler=thread_memory_hardening_evaluate
    )

    template_parser = commands.add_parser("template-evaluate")
    template_parser.add_argument(
        "--name", type=artifact_name, default="template-isolated-evaluation"
    )
    template_parser.set_defaults(handler=template_evaluate)

    template_scale_parser = commands.add_parser("template-scale-evaluate")
    template_scale_parser.add_argument(
        "--name", type=artifact_name, default="template-scale-evaluation"
    )
    template_scale_parser.set_defaults(handler=template_scale_evaluate)

    template_live_parser = commands.add_parser("template-live-evaluate")
    template_live_parser.add_argument(
        "--stage", choices=tuple(TEMPLATE_LIVE_STAGES), default="smoke"
    )
    template_live_parser.add_argument(
        "--chat-model", action="append", default=[], help="chat model; repeatable"
    )
    template_live_parser.add_argument(
        "--embedding-model", default="qwen3-embedding:4b"
    )
    template_live_parser.add_argument("--repeats", type=int, default=1)
    template_live_parser.add_argument("--context-window", type=int, default=16_384)
    template_live_parser.add_argument(
        "--resume", action=argparse.BooleanOptionalAction, default=True
    )
    template_live_parser.add_argument(
        "--name", type=artifact_name, default="template-live-evaluation"
    )
    template_live_parser.add_argument(
        "--cache-name", type=artifact_name, help="reuse a compatible live checkpoint"
    )
    template_live_parser.set_defaults(handler=template_live_evaluate)

    query_rag_parser = commands.add_parser("query-rag-evaluate")
    query_rag_parser.add_argument("--top-k", type=int, default=8)
    query_rag_parser.add_argument("--chat-model", default="qwen3:8b")
    query_rag_parser.add_argument(
        "--embedding-model", default="qwen3-embedding:4b"
    )
    query_rag_parser.add_argument("--repeats", type=int, default=3)
    query_rag_parser.add_argument(
        "--resume", action=argparse.BooleanOptionalAction, default=True
    )
    query_rag_parser.add_argument(
        "--name", type=artifact_name, default="query-rag-evaluation"
    )
    query_rag_parser.add_argument(
        "--cache-name",
        type=artifact_name,
        help="reuse a named generation cache while writing a different report",
    )
    query_rag_parser.set_defaults(handler=query_rag_evaluate)

    email_rag_parser = commands.add_parser("email-rag-evaluate")
    email_rag_parser.add_argument("--top-k", type=int, default=8)
    email_rag_parser.add_argument("--chat-model", default="qwen3:8b")
    email_rag_parser.add_argument(
        "--embedding-model", default="qwen3-embedding:4b"
    )
    email_rag_parser.add_argument("--repeats", type=int, default=3)
    email_rag_parser.add_argument(
        "--resume", action=argparse.BooleanOptionalAction, default=True
    )
    email_rag_parser.add_argument(
        "--name", type=artifact_name, default="email-rag-evaluation"
    )
    email_rag_parser.add_argument(
        "--cache-name",
        type=artifact_name,
        help="reuse a named decomposition cache while writing a different report",
    )
    email_rag_parser.set_defaults(handler=email_rag_evaluate)

    scale_parser = commands.add_parser("scale-hardening-evaluate")
    scale_parser.add_argument("--page-size", type=int, default=32)
    scale_parser.add_argument("--reduction-batch-size", type=int, default=16)
    scale_parser.add_argument("--repeats", type=int, default=3)
    scale_parser.add_argument(
        "--extended",
        action="store_true",
        help="include frozen 1000, 2500, and 5000-message stress threads",
    )
    scale_parser.add_argument(
        "--name", type=artifact_name, default="scale-hardening-evaluation"
    )
    scale_parser.set_defaults(handler=scale_hardening_evaluate)

    drift_parser = commands.add_parser("embedding-drift-evaluate")
    drift_parser.add_argument("--embedding-model", default="qwen3-embedding:4b")
    drift_parser.add_argument("--batch-size", type=int, default=24)
    drift_parser.add_argument("--repeats", type=int, default=3)
    drift_parser.add_argument(
        "--name", type=artifact_name, default="embedding-drift-evaluation"
    )
    drift_parser.set_defaults(handler=embedding_drift_evaluate)

    cross_parser = commands.add_parser("cross-encoder-evaluate")
    cross_parser.add_argument("--embedding-model", default="qwen3-embedding:4b")
    cross_parser.add_argument("--candidate-count", type=int, default=32)
    cross_parser.add_argument("--repeats", type=int, default=3)
    cross_parser.add_argument(
        "--api-format", choices=["cohere", "tei"], default="tei"
    )
    cross_parser.add_argument(
        "--name", type=artifact_name, default="cross-encoder-evaluation"
    )
    cross_parser.set_defaults(handler=cross_encoder_evaluate)

    answer_parameter_parser = commands.add_parser("answer-parameter-evaluate")
    answer_parameter_parser.add_argument("--chat-model", default="qwen3:8b")
    answer_parameter_parser.add_argument("--repeats", type=int, default=3)
    answer_parameter_parser.add_argument(
        "--name", type=artifact_name, default="answer-parameter-evaluation"
    )
    answer_parameter_parser.set_defaults(handler=answer_parameter_evaluate)

    oversized_parser = commands.add_parser("oversized-email-evaluate")
    oversized_parser.add_argument("--live", action="store_true")
    oversized_parser.add_argument(
        "--stress-suite",
        action="store_true",
        help="run both source shapes at 256 KiB, 1 MiB, 4 MiB, and 16 MiB",
    )
    oversized_parser.add_argument("--chat-model", default="qwen3:8b")
    oversized_parser.add_argument("--repeats", type=int, default=3)
    oversized_parser.add_argument(
        "--email-bytes", type=int, default=DEFAULT_EMAIL_BYTES
    )
    oversized_parser.add_argument(
        "--fact-count", type=int, default=DEFAULT_FACT_COUNT
    )
    oversized_parser.add_argument(
        "--context-window", type=int, default=DEFAULT_CONTEXT_WINDOW
    )
    oversized_parser.add_argument(
        "--page-chars", type=int, default=DEFAULT_PAGE_CHARS
    )
    oversized_parser.add_argument(
        "--name", type=artifact_name, default="oversized-email-evaluation"
    )
    oversized_parser.set_defaults(handler=oversized_email_evaluate)

    oversized_design_parser = commands.add_parser("oversized-design-evaluate")
    oversized_design_parser.add_argument("--live", action="store_true")
    oversized_design_parser.add_argument("--chat-model", default="qwen3:8b")
    oversized_design_parser.add_argument("--repeats", type=int, default=3)
    oversized_design_parser.add_argument(
        "--name", type=artifact_name, default="oversized-design-evaluation"
    )
    oversized_design_parser.set_defaults(handler=oversized_design_evaluate)

    query_parser = commands.add_parser("query")
    query_parser.add_argument("--query", required=True)
    query_parser.add_argument("--tenant", default="tenant-alpha")
    query_parser.add_argument("--collection", default="primary")
    query_parser.add_argument(
        "--chunking",
        choices=["fixed", "structure-aware", "sentence-window"],
        default="fixed",
    )
    query_parser.add_argument("--retrieval", choices=["exact", "lexical", "dense", "hybrid"], default="hybrid")
    query_parser.add_argument("--graph", choices=["off", "keyword", "intent-multihop"], default="keyword")
    query_parser.add_argument("--tools", choices=["none", "bounded", "coverage-aware"], default="bounded")
    query_parser.set_defaults(handler=query)

    benchmark_parser = commands.add_parser("benchmark")
    benchmark_parser.add_argument("--size", type=int, default=1000)
    benchmark_parser.add_argument("--full", action="store_true")
    benchmark_parser.add_argument("--name", type=artifact_name, default="deterministic-benchmark")
    benchmark_parser.add_argument(
        "--dense-candidates", choices=["lsh", "full-scan"], default="lsh"
    )
    benchmark_parser.set_defaults(handler=benchmark)

    model_parser = commands.add_parser("models")
    model_commands = model_parser.add_subparsers(dest="model_command", required=True)
    prepare_parser = model_commands.add_parser("prepare")
    prepare_parser.set_defaults(handler=models_prepare)
    probe_parser = model_commands.add_parser("probe")
    probe_parser.add_argument("--no-warmup", action="store_true")
    probe_parser.add_argument(
        "--model", action="append", default=[], help="probe only this configured tag; repeatable"
    )
    probe_parser.set_defaults(handler=models_probe)

    matrix_parser = commands.add_parser("matrix")
    matrix_parser.add_argument("--live", action="store_true")
    matrix_parser.add_argument(
        "--model", action="append", default=[], help="evaluate only this configured chat-model tag; repeatable"
    )
    matrix_parser.add_argument("--repeats", type=int, default=3)
    matrix_parser.add_argument("--resume", action=argparse.BooleanOptionalAction, default=True)
    matrix_parser.add_argument("--name", type=artifact_name, default="adaptive-matrix")
    matrix_parser.add_argument("--stress-32k", action="store_true")
    matrix_parser.add_argument("--dry-run", action="store_true")
    matrix_parser.add_argument(
        "--exhaustive", action="store_true", help="calibrate every compatible Cartesian-product variant"
    )
    matrix_parser.add_argument(
        "--calibration-limit", type=int, help="override the adaptive calibration budget"
    )
    matrix_parser.add_argument(
        "--survivor-limit", type=int, help="override the number of promoted variants"
    )
    matrix_parser.set_defaults(handler=matrix)
    return result


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    try:
        return int(arguments.handler(arguments))
    except (ValueError, RuntimeError, ModelError, sqlite3.Error) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
