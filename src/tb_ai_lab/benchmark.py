# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0.

"""Fixed-seed ingestion and retrieval benchmark."""

from __future__ import annotations

from pathlib import Path
import resource
import statistics
import tempfile
import time
from typing import Any

from .contracts import Document, PipelineVariant, Scope
from .pipeline import Pipeline
from .storage import Index


def generated_document(index: int) -> Document:
    project = f"BENCH-{index:06d}"
    group = index % 97
    body = (
        f"[FACT B{index % 100:02d}] benchmark_value: {project}. "
        f"Synthetic record {index} belongs to group {group}. "
        "Deterministic filler measures indexing and hybrid retrieval without external state."
    )
    return Document(
        id=f"benchmark-{index:06d}",
        tenant="benchmark",
        collection="fixed-seed-1",
        title=f"Benchmark record {index}",
        text=body,
        metadata={"category": f"group-{group}", "status": "synthetic"},
    )


def run_benchmark(size: int, variant: PipelineVariant) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="tb-ai-lab-benchmark-") as temporary:
        database = Path(temporary) / "index.sqlite"
        with Index(database) as index:
            pipeline = Pipeline(index, variant)
            documents = [generated_document(item) for item in range(size)]
            wall_start = time.perf_counter()
            cpu_start = time.process_time()
            counts = pipeline.ingest(documents)
            ingest_wall = time.perf_counter() - wall_start
            ingest_cpu = time.process_time() - cpu_start
            scope = Scope("benchmark", "fixed-seed-1")
            latencies = []
            for item in (0, size // 4, size // 2, max(0, size - 1)):
                query_start = time.perf_counter()
                results = index.hybrid_search(
                    f"BENCH-{item:06d}",
                    scope,
                    8,
                    variant.rrf_k,
                    candidate_mode=variant.dense_candidates,
                )
                latencies.append((time.perf_counter() - query_start) * 1000)
                if not results or results[0].document_id != f"benchmark-{item:06d}":
                    raise AssertionError(f"exact benchmark retrieval failed for {item}")
            return {
                "schema_version": 1,
                "size": size,
                "seed": 1,
                "counts": counts,
                "ingest_wall_seconds": ingest_wall,
                "ingest_cpu_seconds": ingest_cpu,
                "documents_per_second": size / ingest_wall,
                "query_p50_ms": statistics.median(latencies),
                "query_p95_ms": sorted(latencies)[-1],
                "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "database_bytes": database.stat().st_size,
            }
