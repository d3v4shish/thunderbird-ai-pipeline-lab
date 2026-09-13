# Complete test catalog and reproduction

## What “tested” means

The project used four distinct validation layers. They should not be confused:

1. **Build validation** checks configuration, Python syntax/imports, and frozen
   corpus generation.
2. **Deterministic tests** check contracts and known behavior without a model,
   network, profile, or mutable corpus.
3. **Measured evaluations** compare retrieval/generation variants and retain
   prompts, evidence, raw output, metrics, model digests, and resource telemetry.
4. **Benchmarks** measure one fixed ingestion/search workload. They do not prove
   model quality or production latency.

The current deterministic suite passed **156/156 tests in 19.079 seconds** on
the recorded host. Live evaluations were separate because they depend on installed
Ollama models and, for the cross-encoder, a separately started loopback TEI
service.

## Reproducible top-level commands

From the project directory:

```sh
./scripts/build.sh
./scripts/run.sh
./scripts/test.sh
./scripts/benchmark.sh
```

These scripts resolve paths relative to themselves, use fixed seeds/frozen
fixtures, and do not depend on the caller's working directory. Build, test, and
benchmark do not download models. See [`BUILD.md`](../BUILD.md) for optional
environment variables and complete live commands.

## Deterministic test inventory: 156 tests

The exact executable methods are in [`tests/`](../tests/). The inventory below
groups every test by its source file.

### Contracts — 7 tests

[`test_contracts.py`](../tests/test_contracts.py) verifies:

- documents and scopes require stable identity;
- unknown schema versions fail;
- invalid chunk limits fail;
- oversized documents fail before pipeline work;
- non-JSON metadata fails;
- unknown variant fields and modes fail;
- booleans are not silently coerced and tool lists are not silently truncated.

### Frozen corpus and text processing — 9 tests

[`test_corpus_text.py`](../tests/test_corpus_text.py) verifies:

- `long-10240` is exactly 10,240 bytes with all 32 distributed facts;
- fixtures are synthetic and versioned;
- expected answers cover positive and abstention cases;
- every fixed chunk maps to the reported canonical source span;
- structure-aware chunks retain the final fact;
- sentence-window children return verified parent passages;
- normalization and local embeddings are deterministic;
- PII scanning is bounded and deterministic;
- exact-entity extraction is bounded.

### Core pipeline and answer validation — 15 tests

[`test_pipeline_evaluation.py`](../tests/test_pipeline_evaluation.py) verifies:

- baseline safety while reproducing long-document coverage loss;
- the coverage candidate recovers all 32 facts;
- prompt-injection text remains data;
- no-answer and cross-tenant queries abstain;
- an abstention may repeat an identifier already present in the query;
- fact scoring requires the expected fact identifier, not just a matching word;
- answer correctness is scored separately from graph context;
- live prompts do not leak copyable expected FACT identifiers;
- every citation belongs to the offered evidence pack;
- total context budgets are hard and preserve source verification;
- ingestion trace aggregation is bounded;
- live tool evidence reaches answer validation;
- a claimed fact must be supported by a cited passage;
- query and abstention contracts fail closed;
- the model cannot call tools outside the case allowlist.

### Storage, retrieval, graph, and tools — 16 tests

[`test_storage_graph_tools.py`](../tests/test_storage_graph_tools.py) verifies:

- exact search distinguishes similar identifiers;
- tenant scope applies in every search lane;
- embedding reranking uses stored vectors;
- normalized parent storage removes text duplication without changing results;
- identical document IDs in different scopes cannot overwrite each other;
- scope delimiters cannot create colliding chunk IDs;
- GraphRAG finds a source-backed multihop path;
- graph edges not asserted in one source sentence are rejected;
- clearing storage removes both retrieval and graph state;
- unknown or disallowed tool calls fail;
- an explicitly empty allowlist denies every tool;
- fetch cannot cross scope;
- tool budgets are hard;
- document outlines do not consume text-evidence budget;
- tool arguments are strictly validated;
- range offsets beyond the end return an empty verified span.

### Staged RAG evaluation — 6 tests

[`test_rag_evaluation.py`](../tests/test_rag_evaluation.py) verifies:

- stages are isolated across supported RAG dimensions;
- chunk and graph metrics expose known fixture behavior;
- full-pipeline comparison occurs only after ablations;
- sentence-window results deduplicate shared parent spans;
- JSON/Markdown review artifacts are parseable;
- invalid top-K fails before evaluation.

### Contextual RAG — 6 tests

[`test_contextual_rag.py`](../tests/test_contextual_rag.py) verifies:

- the context prompt is query-independent and contains verified source;
- malformed output and unsupported generated entities fail;
- whole-email prompts contain neither a target chunk nor a user query;
- the atomic cache is reusable and never replaces canonical evidence;
- one whole-email context is cached and shared without changing passages;
- the BOREALIS fact chunk genuinely needs earlier document context.

### Query-time RAG — 9 tests

[`test_query_rag.py`](../tests/test_query_rag.py) verifies:

- transformation prompts are corpus-blind and strict;
- malformed or entity-drifting transformations fail;
- corrective labels are bounded to offered evidence;
- rejected transformations fall back to the original query;
- the corrective oracle requires every expected fact;
- rank fusion preserves canonical source evidence;
- the generation cache is atomic and reusable;
- challenge/corrective prompts keep sources untrusted;
- repeat decisions count rank-quality improvement correctly.

### Email/thread RAG — 10 tests

[`test_email_rag.py`](../tests/test_email_rag.py) verifies:

- the 180-message fixture is frozen, synthetic, and route-balanced;
- decomposition is limited to genuine multi-part shapes;
- thread ranges are ordered, scoped, and source-verifiable;
- decomposition calls only multi-part cases and caches safely;
- prompt injection remains data through answer generation;
- abstentions may safely repeat a query identifier;
- exhaustive prompts enumerate and require every source fact;
- repeat combination requires no regression and safety;
- the measured gain is correctly attributed to thread range, not decomposition;
- report writes are atomic and parseable.

### Scale, storage, and deterministic parameters — 7 tests

[`test_scale_evaluation.py`](../tests/test_scale_evaluation.py) verifies:

- 50/100/250/500-message fixtures are frozen and scope-separated;
- range and hierarchy results are complete, ordered, and bounded;
- evaluation exposes fixed top-K loss and hierarchical recovery;
- normalized parent storage has exact behavioral parity;
- each parameter lane changes only the named factor;
- scale report writes are atomic and parseable.
- 1,000/2,500/5,000-message extended fixtures retain pinned digests and bounded
  complete-source hierarchy behavior.

### Oversized single email — 5 tests

[`test_oversized_email.py`](../tests/test_oversized_email.py) verifies:

- the 256-KiB fixture has an exact digest/size, distributed facts, and untrusted
  instruction text;
- bounded source pages preserve complete coverage and exact canonical spans;
- truncation and exhaustive top-K expose loss while the page/ledger path also
  recovers the deterministic 1-MiB/512-fact stress fixture;
- model output validation fails closed on malformed, omitted, and unsupported
  records, and retries only errors that can improve completeness.
- template-dense and unique-prose stress fixtures pass exact 256KiB/1MiB/4MiB/
  16MiB sizing, pinned digests, complete paging, and bounded-memory checks.

### Oversized architecture designs — 5 tests

[`test_oversized_designs.py`](../tests/test_oversized_designs.py) verifies:

- input selection distinguishes lossy sampling from complete known-schema
  compaction;
- chunk lanes measure source coverage, fact integrity, and passage
  amplification separately;
- targeted and exhaustive retrieval contracts remain separate across channel,
  K, and reranking choices;
- page boundaries, rolling state, hierarchy, output limits, and tool budgets
  expose their expected failure modes;
- the report names all three objectives, limitations, and objective-specific
  decisions without a production claim.

### Live-hardening contracts with fake endpoints — 4 tests

[`test_live_hardening.py`](../tests/test_live_hardening.py) verifies:

- vector exactness is distinct from cosine/ranking tolerance;
- drift reports cover batching, ordering, reloads, and rankings;
- cross-encoder reranking preserves scope, source, and candidate membership;
- answer-parameter matrices are one-factor and enforce hard budgets.

### Model and endpoint contracts — 12 tests

[`test_models.py`](../tests/test_models.py) verifies:

- non-loopback endpoints are rejected;
- runtime discovery distinguishes chat and embedding roles;
- embedding count, shape, and finite-value contracts fail closed;
- chat requests are seeded and bounded;
- JSON-schema output constraints are forwarded exactly and cannot be mixed
  ambiguously with native tool calls;
- selected runtime context is not confused with advertised model capacity;
- requests above advertised capacity fail;
- VRAM policy requires measurement, full residency, compatible context, and cap;
- an over-cap model is aborted and unloaded;
- endpoint reranker responses are validated and ordered;
- TEI requests contain joint query/text pairs;
- preparation recognizes aliases and writes an exact manifest.

### Source-linked email and thread memory — 19 tests

[`test_thread_memory.py`](../tests/test_thread_memory.py) verifies:

- the synthetic fixture and complete 1,152-cell matrix are pinned;
- the 18-cell one-factor hardening matrix and 10KB/256KiB routes are complete;
- reply ordering comes from source-backed headers;
- generated claims and events resolve to exact current-email source spans;
- future, cross-scope, prompt-injected, and prior-only fields are rejected;
- partial field rejection preserves the rest of a valid artifact;
- normalized storage, rollups, graph rendering, and edit invalidation are
  bounded;
- prompts contain the current source and prior-only memory but no user query;
- generation cache identity includes the exact corpus and can replay without a
  model call;
- in-memory and SQLite identity include tenant, collection, and document;
- direct and paged extraction routes are explicit;
- repeated and hierarchical retrieval always return canonical source evidence;
- collection Graphviz output is one valid graph document;
- promotion requires three safe repeats and a measured quality gain;
- completed smoke repeats resume without another endpoint request.

### Template mining and template-aware scale — 17 tests

[`test_template_mining.py`](../tests/test_template_mining.py) verifies:

- Thunderbird-style Drain matching, variable gaps, sender lanes, support, and
  bounded cluster eviction;
- body/signature/quoted segmentation preserves exact CRLF source spans;
- typed slots retain exact offsets and strict IDs reject structural prose;
- family assignments are scope/source-digest keyed;
- boilerplate removal keeps dynamic slot lines;
- shingle duplicate scoring is deterministic;
- the 113-message chronological fixture and 500–5,000-message scale fixtures
  have pinned digests and a cross-tenant shadow;
- exact-subject, skeleton, Drain parameter, shingle, and raw/segmented/
  skeleton/Drain/deduplicated/combined retrieval ablations expose all gates;
- normalized family/assignment/slot storage round-trips and invalidates on edit
  or delete;
- long-thread ledgers remain complete while family graph expansion is bounded;
- live prompts keep source data untrusted, schemas contain no expected values,
  validators reject private output, and rejected values reach aggregate gates;
- three-repeat promotion logic fails closed and resumes through fake endpoints.

### Matrix, reporting, and checkpoints — 9 tests

[`test_reporting_matrix.py`](../tests/test_reporting_matrix.py) verifies:

- artifact names cannot escape the report directory;
- matrix enumeration is deterministic and role-aware;
- adaptive selection is bounded, deterministic, and choice-covering;
- live variants are partitioned by combined measured VRAM;
- missing VRAM measurement fails closed;
- Pareto frontier and winner selection are correct;
- repeats retain variance and raw runs;
- a failed/empty repeat cannot be hidden by successful repeats;
- reports and checkpoints are complete.

## Evaluation runs that were actually executed

### Baseline and optimized deterministic pipeline

```sh
./scripts/run.sh evaluate --name baseline-evaluation
./scripts/run.sh evaluate --optimized --name optimized-evaluation
```

This established that the safe baseline reproduced K-limited loss on the
10,240-byte source and that deterministic coverage/graph changes could recover
the labeled facts. These early reports are historical, not the final model
selection.

### Stage-isolated deterministic RAG

```sh
./scripts/run.sh rag-evaluate --name staged-rag-evaluation
```

It compared fixed/structure/sentence-window chunking, sizes 400/800/1200/1800,
exact/lexical/dense/hybrid retrieval, K=4/8/16, adaptive deterministic query
expansion, no/deterministic/embedding reranking, graph off/keyword/multihop,
and complete deterministic pipelines. Raw evidence:
[`staged-rag-evaluation.json`](../reports/staged-rag-evaluation.json).

### Live Contextual RAG

```sh
./scripts/run.sh contextual-rag-evaluate \
  --name contextual-rag-qwen3-focused \
  --chat-model qwen3:8b \
  --embedding-model qwen3-embedding:4b \
  --top-k 8 --no-resume
```

It generated 23/23 query-independent contexts, then compared raw,
deterministic-metadata, and generated-context indexes under lexical, dense, and
hybrid retrieval. Three retrieval repeats reused the same immutable context
cache. Evidence: [`contextual-rag-evaluation-summary.md`](../reports/contextual-rag-evaluation-summary.md).

### Live query-time RAG

```sh
./scripts/run.sh query-rag-evaluate \
  --chat-model qwen3:8b \
  --embedding-model qwen3-embedding:4b \
  --top-k 8 --repeats 3 \
  --name query-rag-qwen3-final \
  --cache-name query-rag-qwen3-v2
```

It compared direct hybrid, HyDE, three-query Fusion, decomposition, step-back,
local corrective retrieval, and adaptive routing on identical chunks and K.
The 4.5MB JSON preserves all transformations and evidence:
[`query-rag-qwen3-final.json`](../reports/query-rag-qwen3-final.json).

### Live selective email RAG and final answers

```sh
./scripts/run.sh email-rag-evaluate \
  --chat-model qwen3:8b \
  --embedding-model qwen3-embedding:4b \
  --top-k 8 --repeats 3 \
  --name email-rag-qwen3-final \
  --cache-name email-rag-qwen3-v1
```

Each repeat rebuilt/embedded 180 messages, ran 13 questions through direct and
selective routes, and generated strict final answers. It made 18 unique answer
calls per repeat; shared evidence prompts were reused within a repeat to keep
the comparison paired. Evidence:
[`email-rag-qwen3-final.json`](../reports/email-rag-qwen3-final.json).

### 50–500-message scale, normalized storage, and deterministic parameters

```sh
./scripts/run.sh scale-hardening-evaluate \
  --page-size 32 --reduction-batch-size 16 --repeats 3 \
  --name hardening-final
```

It wrote separate thread, storage, and parameter reports. It compared direct
top-8, full range, paged range, hierarchical ledger, parent duplication versus
normalization, eight parameter families, and reduction batch sizes 4–64.

### Source-linked thread-memory evaluation

```sh
./scripts/run.sh thread-memory-evaluate --dry-run --repeats 3
./scripts/run.sh thread-memory-hardening-evaluate \
  --name thread-memory-hardening
./scripts/run.sh thread-memory-evaluate \
  --chat-model qwen3:8b --embedding-model qwen3-embedding:4b \
  --repeats 1 --smoke --name qwen3-thread-memory-smoke
```

The preflight enumerated 1,152 answer/retrieval cells and 144 generation
streams. Deterministic hardening executed 18 parameter cells, 50–500-message
threads, and complete 10KB/256KiB source routes with no hard-gate failure.
Separate one-repeat Qwen3 and Phi-4 smokes tested whole-email extraction,
prior-only memory, repeated versus hierarchical placement, grounded final
answers, checkpoint resumption, and measured model residency. Exact results and
the still-open three-repeat qualification are in the
[`thread-memory evaluation summary`](../reports/thread-memory-evaluation-summary.md).

### Template-aware retrieval and extreme scale

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

The deterministic lanes compare template classification, typed slots,
boilerplate/shingle handling, six paired retrieval representations,
500–5,000-message threads, and 256KiB–16MiB messages. The live matrix tested six
chat models at smoke, two at three-repeat 1,000-record qualification, and
Granite 3.1 MoE at three-repeat 5,000-record stress. Exact results and all raw
artifact names are in the
[`template-aware evaluation summary`](../reports/template-aware-evaluation-summary.md).

### Embedding drift

```sh
./scripts/run.sh embedding-drift-evaluate \
  --embedding-model qwen3-embedding:4b --batch-size 24 --repeats 3 \
  --name embedding-drift-final
./scripts/run.sh embedding-drift-evaluate \
  --embedding-model qwen3-embedding:4b --batch-size 1 --repeats 3 \
  --name embedding-drift-singleton-final
```

These runs separated vector equality, cosine closeness, ranking equality,
top-8 overlap, quality drift, batch/order effects, immediate repetition, and
three fresh model loads.

### True cross-encoder and candidate-depth sweep

```sh
RERANKER_URL=http://127.0.0.1:18081/rerank \
RERANKER_MODEL=Alibaba-NLP/gte-reranker-modernbert-base \
RERANKER_DEVICE=cpu RERANKER_VRAM_BYTES=0 \
./scripts/run.sh cross-encoder-evaluate \
  --embedding-model qwen3-embedding:4b \
  --candidate-count 8 --repeats 3 --api-format tei \
  --name cross-encoder-candidates-8-final
```

The same evaluation was retained at depths 16, 32, and 64. The successful
runtime was CPU TEI 1.9.3. Failed GPU/alternate-model starts are documented in
the results article rather than counted as quality tests.

### Answer parameter evaluation

```sh
./scripts/run.sh answer-parameter-evaluate \
  --chat-model qwen3:8b --repeats 3 \
  --name answer-parameters-final
```

This used the same first 32 messages of a frozen thread and changed only model
context, output tokens, evidence characters, temperature, or a named combined
finalist. Every setting ran three calls.

### Live adaptive model matrix

```sh
./scripts/prepare-models.sh
./scripts/run.sh models probe
./scripts/run.sh matrix --live --repeats 3
```

All six approved tags and installed controls were discovered by runtime role.
The adaptive matrix executed 48 calibration variants, attempted all 24 planned
survivor repeat slots, and retained one runtime failure instead of dropping it.
Eight combined survivor records appear in
[`adaptive-live-evaluation-v2.json`](../reports/adaptive-live-evaluation-v2.json).
No variant passed every quality threshold.

### Oversized single-email evaluation

```sh
./scripts/run.sh oversized-email-evaluate \
  --name oversized-email-deterministic
./scripts/run.sh oversized-email-evaluate \
  --live --chat-model qwen3:8b --repeats 3 \
  --email-bytes 262144 --fact-count 64 \
  --context-window 8192 --page-chars 20000 \
  --name oversized-email-qwen3-current-final
```

The deterministic lane compared prefix/head-tail truncation, targeted and
exhaustive top-K, legacy and structure-aware chunking, complete source paging,
ledger reduction, overlap deduplication, and bounded output pagination. The
live lane compared direct 8K and advertised 40,960-token prompting with 14
bounded map calls in three repeats. Complete prompts and raw outputs are in
[`oversized-email-qwen3-current-final.json`](../reports/oversized-email-qwen3-current-final.json),
with the reviewed result in the
[`oversized-email evaluation summary`](../reports/oversized-email-evaluation-summary.md).

### Complete oversized architecture matrix

```sh
./scripts/run.sh oversized-design-evaluate \
  --name oversized-design-deterministic-final
./scripts/run.sh oversized-design-evaluate \
  --live --chat-model qwen3:8b --repeats 3 \
  --name oversized-design-qwen3-v3-final
```

This added prefix/suffix/head-tail/middle/uniform sampling, capped/uncapped/
structure/sentence-window chunks, exact/lexical/dense/hybrid retrieval across
K=1–256, three rerankers, 24 page/boundary lanes, schema compaction, rolling
state, host and model hierarchy, four result budgets, and a bounded tool agent.
Promoted designs received three live repeats; diagnostic designs received one
and remain labelled as such. The complete expected-versus-actual result is in
[`oversized-design-evaluation-summary.md`](../reports/oversized-design-evaluation-summary.md).

## Benchmark method and result

The standard benchmark uses a fixed synthetic 1,000-document corpus and seeded
queries. Baseline `email-rag-baseline-1000` versus final hardening code:

| Metric | Baseline | Final | Change |
|---|---:|---:|---:|
| Ingest wall time | 0.726129 s | 0.762134 s | +4.96% |
| Search p50 | 1.705490 ms | 1.804227 ms | +5.79% |
| Search p95 | 2.125555 ms | 2.370168 ms | +11.51% |
| Peak RSS | 32,120 KiB | 32,880 KiB | +2.37% |
| SQLite bytes | 3,420,160 | 3,432,448 | +0.36% |

This is a measured local regression, not evidence of an optimization. No speed
improvement is claimed. Detailed method and historical runs are in
[`BENCHMARKS.md`](../BENCHMARKS.md) and [`HOTSPOTS.md`](../HOTSPOTS.md).

The isolated design evaluator's post-change verification measured 0.736191
seconds ingest, 1.790135 ms p50, 2.276921 ms p95, 33,568 KiB peak RSS, and the
same 3,432,448-byte database. It is a single local run and does not establish a
production-pipeline improvement.

The latest template-aware post-change 1K verification measured 0.751673
seconds ingest, 1.850639 ms p50, 2.622365 ms p95, 33,920 KiB peak RSS, and a
3,465,216-byte database. Its immediately preceding same-command run was
0.745197 seconds and 1.860272 ms p50 with identical storage. The mixed
single-run movement does not establish a performance change.

## What was not tested

- no real Thunderbird profile or email;
- no production account synchronization or mutation;
- no web fallback in Corrective RAG;
- no reflection-trained Self-RAG;
- no recursive model-summary RAPTOR;
- no community/global GraphRAG;
- no successful GPU TEI cross-encoder on this host;
- no Thunderbird integration/parity run for a selected candidate;
- no production workload, concurrency soak, or production-readiness sign-off;
- no oversized real email, arbitrary-summary completeness oracle, or parallel
  page-generation soak.
- no real-mail estimate of template prevalence, multilingual family drift, or
  adversarial online cluster poisoning under mailbox concurrency.

Those limits are part of the test result, not footnotes to ignore.
