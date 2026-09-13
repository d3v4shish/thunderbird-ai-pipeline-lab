# Build and Run

## Requirements

- Python 3.14 or newer with SQLite FTS5.
- Optional: Ollama at `http://127.0.0.1:11434`.
- Optional for GPU eligibility: `nvidia-smi`.

No third-party Python package is required.

## Deterministic commands

```sh
./scripts/build.sh
./scripts/run.sh
./scripts/test.sh
./scripts/benchmark.sh
```

`build.sh` validates configuration and regenerates the frozen corpus.
`run.sh` defaults to the deterministic calibration evaluation and forwards any
arguments to the CLI. `test.sh` runs the standard-library unittest suite.
`benchmark.sh` runs fixed-seed 1K ingestion/search unless `--full` is supplied,
which runs 1K, 10K, and 100K.

The deterministic staged RAG suite is:

```sh
./scripts/run.sh rag-evaluate --name staged-rag-evaluation
```

Use `--top-k N` to change the main comparison depth. The suite also runs its
fixed K=4/8/16 depth ablation and writes JSON/Markdown under `reports/`.

The live generated Contextual RAG suite is:

```sh
./scripts/run.sh contextual-rag-evaluate \
  --chat-model qwen3:8b \
  --embedding-model qwen3-embedding:4b \
  --top-k 8 \
  --name contextual-rag-evaluation
```

The command never downloads a model. It checks installed model roles, enforces
the configured 17-GiB Ollama allocation cap, checkpoints both per-chunk and
one-per-email generated contexts, and writes paired JSON/Markdown reports.
Each whole-email call receives the complete bounded email and no target chunk;
its accepted context is shared across canonical evidence passages. Repeating
the same command reuses only successful cache records with the same corpus,
model digest, and prompt version. Use `--no-resume` for a fresh run.

The live query-time advanced-RAG suite is:

```sh
./scripts/run.sh query-rag-evaluate \
  --chat-model qwen3:8b \
  --embedding-model qwen3-embedding:4b \
  --top-k 8 \
  --repeats 3 \
  --name query-rag-evaluation
```

The first repeat generates and atomically caches bounded HyDE, rewrite,
decomposition, step-back, and routing records. Later repeats reuse accepted
transformations while rebuilding and re-embedding the identical index, making
cross-load ranking variation visible. Corrective grades are keyed by the exact
evidence digest. `--cache-name NAME` reuses a named compatible cache;
`--no-resume` regenerates it on every repeat and is therefore intentionally
more expensive.

The selective email/thread RAG suite is:

```sh
./scripts/run.sh email-rag-evaluate \
  --chat-model qwen3:8b \
  --embedding-model qwen3-embedding:4b \
  --top-k 8 \
  --repeats 3 \
  --name email-rag-evaluation
```

The command builds a fresh endpoint-embedded index of 180 frozen synthetic
messages per repeat. It calls decomposition only for the four labeled
multi-part query shapes, uses source-verifiable thread ranges for exhaustive
requests, and generates strict grounded answers for direct and selective
evidence. Successful decompositions are atomically cached by corpus, model,
prompt, and validation versions; final answers are regenerated on every repeat.
Use `--cache-name NAME` to reuse a compatible decomposition cache.

The oversized single-email suite is:

```sh
./scripts/run.sh oversized-email-evaluate \
  --name oversized-email-deterministic
./scripts/run.sh oversized-email-evaluate \
  --live --chat-model qwen3:8b --repeats 3 \
  --email-bytes 262144 --fact-count 64 \
  --context-window 8192 --page-chars 20000 \
  --name oversized-email-qwen3-current-final
```

The deterministic command requires no endpoint. The live command uses only the
configured loopback Ollama endpoint and never downloads a model. It records
direct context-limited attempts, bounded map pages, raw outputs, exact source
validation, the merged ledger, output pagination, latency, token counts, and
VRAM telemetry. Use `--page-chars 30000 --repeats 1` for the retained page-size
comparison; 20,000 is the safer measured setting for `qwen3:8b` at 8K runtime
context.

Run the full oversized-email design matrix:

```sh
./scripts/run.sh oversized-design-evaluate \
  --name oversized-design-deterministic-final
./scripts/run.sh oversized-design-evaluate \
  --live --chat-model qwen3:8b --repeats 3 \
  --name oversized-design-qwen3-v3-final
```

The live matrix is deliberately self-contained and does not reuse earlier
reports or model-output caches. Promoted direct/map, schema-compaction, and
targeted-RAG lanes run three repeats. Alternate page sizes, rolling model state,
model hierarchy, and the bounded tool agent are one-repeat diagnostic lanes and
are labelled accordingly. The command is serial, loopback-only, enforces the
configured Ollama allocation cap, and retains every prompt and raw response.

## Hardening commands

Run the template-mining retrieval ablation, extended deterministic scale, and
staged live qualification:

```sh
./scripts/run.sh template-evaluate --name template-isolated-v2-retrieval
./scripts/run.sh template-scale-evaluate --name template-long-thread-v1
./scripts/run.sh scale-hardening-evaluate --extended \
  --name template-extended-scale-v1
./scripts/run.sh oversized-email-evaluate --stress-suite \
  --name template-oversized-stress-v1
./scripts/run.sh template-live-evaluate --stage smoke --repeats 1 \
  --name template-live-smoke-v2-schema
```

`template-live-evaluate` is resumable, serial, loopback-only, and limited to
three repeats. It uses `qwen3-embedding:4b`, checks model role/context and the
17-GiB measured Ollama cap, unloads models between candidates, and retains
prompts/raw output/validation in JSON. Advance at most two smoke passers to
`--stage qualify`; advance one qualification winner to `--stage stress`.
The retained run used 16K context throughout because the largest stress page
used only 1,745 prompt tokens. No command downloads a model.

Plan and smoke-test source-linked email/thread memory, then run its deterministic
scale harness:

```sh
./scripts/run.sh thread-memory-evaluate \
  --chat-model qwen3:8b --chat-model phi4:14b-q8_0 \
  --embedding-model qwen3-embedding:4b --repeats 3 --dry-run
./scripts/run.sh thread-memory-evaluate \
  --chat-model qwen3:8b --embedding-model qwen3-embedding:4b \
  --repeats 1 --smoke --name qwen3-thread-memory-smoke
./scripts/run.sh thread-memory-hardening-evaluate \
  --name thread-memory-hardening
```

Remove `--dry-run` only when the full 1,152-cell live run is intended. The
default chat set is Qwen3 8B and Phi-4 14B Q8. Generation, answer, and
model-repeat checkpoints live beside the report. `--cache-name NAME` reuses a
compatible cache while writing a different report; `--no-resume` deliberately
regenerates all model work. Endpoint failures remain retryable.

Run deterministic scale, storage-layout, and one-factor parameter evaluation:

```sh
./scripts/run.sh scale-hardening-evaluate \
  --page-size 32 --reduction-batch-size 16 --repeats 3 \
  --name hardening-final
```

Run three fresh-load endpoint drift evaluations. Batch 24 measures normal
throughput behavior; batch 1 measures the deterministic singleton workaround:

```sh
./scripts/run.sh embedding-drift-evaluate \
  --embedding-model qwen3-embedding:4b --batch-size 24 --repeats 3 \
  --name embedding-drift-final
./scripts/run.sh embedding-drift-evaluate \
  --embedding-model qwen3-embedding:4b --batch-size 1 --repeats 3 \
  --name embedding-drift-singleton-final
```

Run context-window, output-token, evidence-budget, temperature, and combined
finalist evaluation on a bounded 32-message map page:

```sh
./scripts/run.sh answer-parameter-evaluate \
  --chat-model qwen3:8b --repeats 3 --name answer-parameters-final
```

With an already running loopback rerank service, run a true cross-encoder lane:

```sh
RERANKER_URL=http://127.0.0.1:18081/rerank \
RERANKER_MODEL=Alibaba-NLP/gte-reranker-modernbert-base \
RERANKER_DEVICE=cpu RERANKER_VRAM_BYTES=0 \
./scripts/run.sh cross-encoder-evaluate \
  --embedding-model qwen3-embedding:4b \
  --candidate-count 8 --repeats 3 --api-format tei \
  --name cross-encoder-candidates-8-final
```

The final evaluation also retained candidate-depth reports for 16, 32, and 64.
No hardening command downloads Ollama models. Starting or installing the
optional reranker runtime is an explicit external step.

## Live commands

```sh
./scripts/prepare-models.sh
./scripts/run.sh models probe
./scripts/run.sh matrix --live --repeats 3
```

Use repeatable `--model TAG` options on `models probe` or `matrix --live` to
work through configured candidates one at a time. Omitting the option selects
all approved candidates and installed controls.

Use `./scripts/run.sh matrix --live --dry-run` to perform capability/VRAM
preflight and write the exact compatible variant plan without executing cases.
The default adaptive run calibrates a deterministic, coverage-balanced set of
48 variants and promotes the best eight hard-gate survivors to three-repeat
full-corpus runs. Pass `--exhaustive` only when you intentionally want the full
Cartesian product.

For a short end-to-end smoke before a full adaptive run, use explicit small
budgets, for example:

```sh
./scripts/run.sh matrix --live --model qwen3:8b --calibration-limit 4 --survivor-limit 1 --repeats 1 --name qwen3-smoke
```

Supported environment variables:

- `OLLAMA_BASE_URL`: loopback URL; default `http://127.0.0.1:11434`.
- `LAB_REPORT_DIR`: artifact directory; default `<project>/reports`.
- `LAB_SOURCE_ROOT`: optional Thunderbird checkout for explicit source-drift
  checks. It is not auto-discovered, so default commands do not depend on
  sibling checkout state.
- `RERANKER_URL`: optional loopback Cohere-compatible or TEI rerank endpoint.
- `RERANKER_MODEL`: optional model name sent to that rerank endpoint.
- `RERANKER_DEVICE`: report label such as `cpu` or `gpu`.
- `RERANKER_VRAM_BYTES`: measured reranker model allocation; use `0` for CPU.

Model preparation refuses non-loopback endpoints, pulls only the allowlisted
tags in `config/models.json`, processes them sequentially, records resolved
digests, and stops when projected free space would fall below 64 GiB.

## Verify retained evaluation artifacts

The public repository keeps synthetic generated fixtures and non-transient
reports, including failed runs and raw model outputs. It excludes local model
caches, resumable checkpoints, dry-run plans, and temporary files.

Verify every retained artifact against the committed digest list:

```sh
./scripts/results-manifest.sh verify
```

After intentionally adding or regenerating a retained report, update the list
and verify it before committing:

```sh
./scripts/results-manifest.sh update
./scripts/results-manifest.sh verify
```

The script resolves the project directory from its own path, sorts paths under
the C locale, and therefore does not depend on the caller's working directory.
