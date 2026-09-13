# Scale, Stability, Reranking, Storage, and Parameter Evaluation

Date: 2026-09-13  
Implementation digest: `5335a3c71f247cdec434e48eca674d2538870decd3b5c60d06c507056fb8b2a2`  
Data boundary: frozen synthetic fixtures only; no Thunderbird profile or real
mail was read.

This is the immutable report for implementation digest `5335a3c…`. The suite
later expanded to 136 tests for source-linked whole-email/thread memory and now
passes 156 tests with template-aware/extreme-scale coverage. Its newer
measurements and open three-repeat qualification are in
[`thread-memory-evaluation-summary.md`](thread-memory-evaluation-summary.md).

## Outcome

The deferred hardening evaluation is complete. The lab now has deterministic
50/100/250/500-message thread tests, a normalized parent-passage schema, a
three-load embedding-drift investigation, a genuine cross-encoder lane, hard
aggregate context packing, and live context/output/evidence parameter tests.
Build and all 106 deterministic tests pass.

This does **not** certify the Thunderbird integration as production-ready. The
results justify specific broader-evaluation candidates, but the lab still uses
synthetic labeled facts. Porting a selected configuration into Thunderbird and
validating it against safe, representative real-mail distributions is a
separate TODO.

## Changes made to the lab

- `storage.Index` now has an optional normalized parent layout. A scoped
  `parent_passages` row stores one canonical parent passage, while child chunks
  store a parent identifier. Exact, lexical, dense, hybrid, and direct chunk
  fetches resolve the same canonical evidence text as the legacy layout.
- `PipelineVariant` now supports an explicit retrieval-candidate count and a
  hard total context-character budget. Packing never exceeds the configured
  total and still returns source-verifiable spans.
- `RerankerClient` now supports TEI `/rerank` as well as Cohere-compatible
  payloads. Query and documents are bounded. Missing, duplicate, out-of-range,
  non-finite, or malformed result indexes fail closed.
- `scale_evaluation` creates frozen large-thread fixtures and compares direct
  top-K, full ranges, paged ranges, and hierarchical fact ledgers.
- `live_hardening` measures vector drift, cross-encoder quality/safety, and
  generation parameters. The drift test now distinguishes first-to-second from
  second-to-third calls, which exposed a cold/warm effect.
- `OllamaClient` now compares a requested runtime context with the model's
  separately discovered advertised context. The old code incorrectly treated
  a deliberately selected 8K window as though the model itself advertised only
  8K, causing a false `CONTEXT_INCOMPATIBLE` result after generation.
- The source fact contract accepts three-digit scale fact IDs (`T001` through
  `T500`) while retaining the same strict schema and citation checks.

## Reproduction commands

```sh
./scripts/run.sh scale-hardening-evaluate \
  --page-size 32 --reduction-batch-size 16 --repeats 3 \
  --name hardening-final

./scripts/run.sh embedding-drift-evaluate \
  --embedding-model qwen3-embedding:4b --batch-size 24 --repeats 3 \
  --name embedding-drift-final

./scripts/run.sh embedding-drift-evaluate \
  --embedding-model qwen3-embedding:4b --batch-size 1 --repeats 3 \
  --name embedding-drift-singleton-final

./scripts/run.sh answer-parameter-evaluate \
  --chat-model qwen3:8b --repeats 3 \
  --name answer-parameters-final

RERANKER_URL=http://127.0.0.1:18081/rerank \
RERANKER_MODEL=Alibaba-NLP/gte-reranker-modernbert-base \
RERANKER_DEVICE=cpu RERANKER_VRAM_BYTES=0 \
./scripts/run.sh cross-encoder-evaluate \
  --embedding-model qwen3-embedding:4b \
  --candidate-count 8 --repeats 3 --api-format tei \
  --name cross-encoder-candidates-8-final

./scripts/benchmark.sh --name hardening-post-change-1000
./scripts/build.sh
./scripts/test.sh
```

The cross-encoder command was repeated with candidate counts 16, 32, and 64.
All endpoint URLs were validated as loopback addresses.

## 1. Thread scaling: 50 to 500 messages

### Test design

Each frozen thread has exactly one independent action fact in every message,
twelve unrelated messages in the same tenant/collection, and one matching
private-shadow message in another tenant. The query asks for every action code
from one explicit thread identifier. The expected output is all `N` fact/value
pairs in canonical timestamp/document order, with no duplicate, cross-tenant,
or unverifiable source span.

Fixture digests:

- 50: `00ed5bbdee4c34b95838b6365ff6119fc7989b119b044d18bba68f77856b4953`
- 100: `102aa3ab0d057aea660ff194029e47495f2a216711a49a3d876d388abcc513be`
- 250: `83c085ce03a3b6c16f1bc4bd6ac9b120988b76c32af2391810af0e6190854358`
- 500: `8dc40b0b8682fae06c143eeeb708f9f78174c8027d816c3aa9e66d55038ecf1d`

Four methods were compared:

1. `direct-top-8`: ordinary relevance retrieval, included as the failure
   control for an exhaustive request.
2. `full-thread-range`: all canonical messages in one unbounded evidence set.
3. `paged-thread-range`: the same range split into pages of at most 32 messages.
4. `hierarchical-ledger`: page-level validated fact ledgers merged in bounded
   reduction batches of 16.

### Expected versus actual

Direct top-8 was expected to lose facts as thread size increased; it returned
exactly eight facts, so recall was 0.160, 0.080, 0.032, and 0.016. This confirms
that ranking quality or a larger context window cannot make fixed K answer an
unbounded all/every request.

Full, paged, and hierarchical methods were expected to return every fact. All
three achieved 1.000 fact recall and document recall at every size. Scope
integrity, source-span validity, order, and duplicate checks all passed. At 500
messages, unbounded evidence contained 152,392 characters. Paging limited each
source page to 9,760 characters; the hierarchy's largest page/reduction stage
was 13,484 characters and traced peak Python allocation was 529,356 bytes.
Hierarchy p50 rose approximately linearly from 3.012 ms at 50 messages to
30.752 ms at 500.

Reduction batch sizes 4, 8, 16, 32, and 64 all retained all 500 facts. Batches
4 and 8 had the smallest working set; 16 remains a reasonable throughput test
default. This stage is deterministic extraction, not an LLM summary, so its
purpose is to prove coverage, ordering, bounds, and omission visibility before
a generative reducer is trusted.

Raw reports: `hardening-final-threads.json` and
`hardening-final-threads.md`.

## 2. Normalized sentence-window parent storage

### Test design

The same documents, chunks, local vectors, queries, and pipeline variant were
ingested three times with the legacy duplicated-parent layout and three times
with normalized parent rows. The acceptance contract required byte-identical
rankings/evidence, source verification, scope integrity, equal retrieval
quality, and a database no larger than the control.

### Expected versus actual

Behavioral parity passed exactly. Both layouts produced document recall 1.000,
fact recall 0.8919, MRR 1.000, scope integrity 1.000, and identical ranking
records. The old database was 569,344 bytes and represented 179,594 repeated
passage characters. The normalized database was 356,352 bytes and stored
11,072 parent characters, reducing the SQLite file by 37.410%.

Median ingest was 12.702 ms for duplication and 13.116 ms for normalization.
That small +3.3% result is not a portable regression or a speed claim; the
storage reduction and exact parity are the promotion evidence.

Raw reports: `hardening-final-storage.json` and
`hardening-final-storage.md`.

## 3. Embedding drift investigation

### Questions tested

The drift harness asks six separate questions rather than treating unchanged
aggregate recall as determinism:

- Does the exact same full input sequence produce equal vectors twice in one
  loaded model?
- Is a third pass equal to the second after warm-up?
- Does changing batch size or order change a text's vector?
- Do two identical texts inside one request receive equal vectors?
- Are two separate immediate singleton requests equal?
- Do three fresh model loads produce equal vector digests, rankings, and
  retrieval quality?

It records maximum/mean absolute component deltas, mean/minimum cosine,
document and query vector digests, top-8 overlap, exact ranking rate, maximum
shared-score delta, fact recall, document recall, time, and VRAM.

### Batch 24 result

The expectation was either exact vectors or a clearly bounded tolerance. Exact
determinism failed. First-to-second and second-to-third passes both changed;
minimum cosine was 0.997264. Duplicate texts in one multi-item request also
differed, while repeated standalone singleton calls were exact. Fresh-load
document digests differed. Relative to load one, exact ranking rates were 0.538
and 0.769 and mean overlap@8 was 0.971 and 0.981.

The measured quality tolerance passed: fact recall stayed 0.8462, document
recall stayed 0.9697, overlap remained above 0.95, and aggregate quality delta
was zero. A normal document pass took 6.85–6.95 seconds. This is acceptable only
if the application persists built embeddings and monitors the explicit
tolerance; it is not byte-reproducible indexing.

### Singleton result

Batch 1 exposed a repeatable cold/warm pattern. The first pass differed from
the second with minimum cosine 0.999101, but the second and third passes were
exactly equal in all three fresh loads. The complete first-pass request sequence
was itself equal across all three fresh loads, and all rankings were identical.
A document pass took 25.99–26.70 seconds, roughly four times batch 24.

Recommendation: persist embeddings. If exact rebuild reproducibility is a hard
requirement, perform one warm pass and then index via singleton requests. If
throughput matters more, use batching only behind the >=95% top-8 overlap and
<=1% quality-delta gate. Peak Ollama allocation was 6,455,432,314 bytes.

Raw reports: `embedding-drift-final.json` and
`embedding-drift-singleton-final.json` plus their Markdown companions.

## 4. Genuine cross-encoder reranking

### Runtime selection and failed attempts

The first selected model was
`Alibaba-NLP/gte-multilingual-reranker-base` (306M, multilingual, 8,192-token
maximum). GPU TEI could not start because Docker reported no device driver with
GPU capabilities. TEI 1.7 CPU downloaded that model's safetensors after finding
no ONNX export, then crashed while initializing the GTE Candle CPU backend with
Intel MKL SGEMM errors. These failures were retained rather than described as
quality results.

The successful fallback was the TEI-supported
`Alibaba-NLP/gte-reranker-modernbert-base` in TEI 1.9.3. `/info` reported a true
reranker model, float32, 8,192 maximum input tokens, maximum runtime batch 8,
and CPU execution. A smoke query, `approved cutover date`, scored the relevant
passage `5.3479` and unrelated lunch text `-1.7130`.

### Evaluation contract

For every email case, hybrid retrieval first created one candidate set. Four
lanes then ordered those exact candidates: unchanged, deterministic heuristic,
embedding similarity, and the cross-encoder's joint query/passage scores. The
reranker could not retrieve or rewrite evidence. Every returned candidate had
to retain its tenant, collection, canonical source span, and membership in the
input set.

### Expected versus actual

All safety checks passed in all repeats. Fact/document recall@8 remained
0.9697. Cross-encoder fact MRR improved from 0.7933 to 0.8388 in every repeat,
so it is a broader-evaluation candidate. It did not recover the one fact absent
from the candidate/top-8 control.

| Candidates | Mean cross-encoder p50 | Mean p95 | Fact recall@8 | Fact MRR |
|---:|---:|---:|---:|---:|
| 8 | 281 ms | 309 ms | 0.9697 | 0.8388 |
| 16 | 557 ms | 601 ms | 0.9697 | 0.8388 |
| 32 | 1,086 ms | 1,198 ms | 0.9697 | 0.8388 |
| 64 | 2,159 ms | 2,252 ms | 0.9697 | 0.8388 |

Depth 8 is the measured choice because larger pools add nearly linear CPU cost
without quality. This is not a production latency result: GPU TEI remains
untested on this host. The reranker consumed zero VRAM but its idle container
used 9.327 GiB host RAM; the embedding model remained under the 17-GiB Ollama
allocation cap.

Raw reports: `cross-encoder-candidates-8-final.json`,
`cross-encoder-candidates-16-final.json`, `cross-encoder-final.json` (32), and
`cross-encoder-candidates-64-final.json`, plus Markdown companions.

## 5. Context windows and generation parameters

### Prompt and expected output

The live model was `qwen3:8b`. Evidence was the first 32-message page from the
frozen 50-message thread. The system prompt treats query/evidence as untrusted,
requires one JSON object with exactly `answer`, `facts`, `citations`, and
`abstained`, lists all 32 visible source fact IDs, demands every fact once in
order, requires exact source values, and permits only offered citation strings.
The expected result was 32 exact `T001`–`T032` mappings and valid citations.
The validator rejected malformed JSON, missing facts, unsupported values,
duplicate/out-of-set citations, and any structure outside that schema.

Each one-factor setting and each combined finalist ran three separate calls.
Seed was zero and thinking was disabled. Raw output and every missing fact ID
are retained in the JSON report.

### Results

- Baseline 16,384 context / 4,096 output / full evidence returned all 32 facts
  in every repeat. It used 4,410 prompt and 1,932 output tokens.
- Context 4,096 failed; 8,192 and 32,768 passed with the old output allowance.
- Output caps 256, 512, and 1,024 truncated the JSON and failed validation.
  Output 2,048 passed all repeats, so 4,096 is unnecessary for this page.
- Evidence budget 4,096 characters retained 13/32 facts (0.4063). Budget 8,192
  retained 27/32 (0.8438). The full 9,687 characters retained 32/32. Evidence
  cannot be reduced by dropping source records for an exhaustive request.
- Temperature 0.2 happened to return the same complete output, but temperature
  zero remains preferable for a deterministic extraction contract.
- Combined 6,144 context / 2,048 output failed. Combined 7,168/2,048 and
  8,192/2,048 both returned all facts in every repeat. The smallest measured
  finalist is therefore 7,168/2,048; integration should retain safety margin.

Successful calls took roughly 20–23 seconds because generating 32 values and
citations dominates retrieval. Peak Ollama allocation was 7,704,810,618 bytes;
peak whole-GPU telemetry was 9,345,957,888 bytes. Both are below the evaluation
cap, which applies to Ollama model allocations.

The first combined test falsely reported `CONTEXT_INCOMPATIBLE` because the
runtime guard confused selected context with advertised model capacity. The
guard was fixed and covered by pass/fail tests before the final matrix was run.

Raw report: `answer-parameters-final.json`; review table:
`answer-parameters-final.md`.

## 6. Other one-factor parameters

The deterministic sweep changed only one field per lane. Quality was preferred
before packed size; one-run timing noise was not used to select a winner.

- `chunk_chars=1800`: provisional quality candidate; fact recall 1.000.
- `chunk_overlap=0`: provisional quality candidate; fact recall 0.9189 versus
  0.8378 baseline and lower repeated text.
- `top_k=12` and `context_records=12`: provisional quality candidates; fact
  recall 1.000 with about 8,902 mean packed characters.
- `context_chars=1200`: same baseline quality with lower per-record budget.
- `context_total_chars=14400`: first hard total cap with baseline quality.
- `retrieval_candidates=8`: smallest tested candidate pool with baseline
  quality. The live cross-encoder depth sweep independently supports 8.
- `rrf_k=60`: keep; alternatives produced no quality improvement.
- Reduction batch 8 minimizes the large-thread working set; batch 16 remains a
  reasonable throughput candidate. Generative reduction still needs a
  separately labeled real-distribution test.

These values come from local deterministic vectors unless explicitly described
as live. They are candidates, not universal defaults.

Raw report: `hardening-final-parameters.json` and Markdown companion.

## 7. Performance comparison

The pre-change baseline artifact `email-rag-baseline-1000.json` was compared
with `hardening-post-change-1000.json` using the same fixed 1,000-document
benchmark contract.

| Metric | Baseline | Post-change | Change |
|---|---:|---:|---:|
| Ingest wall | 0.726 s | 0.762 s | +4.96% |
| Query p50 | 1.705 ms | 1.804 ms | +5.79% |
| Query p95 | 2.126 ms | 2.370 ms | +11.51% |
| Peak RSS | 32,120 KiB | 32,880 KiB | +2.37% |
| SQLite bytes | 3,420,160 | 3,432,448 | +0.36% |

This is one uncontended run per side. It is recorded as a local
regression/noise signal, not as proof of a portable slowdown. The normalized
parent-specific paired test is the stronger storage measurement and showed a
37.4% reduction for sentence-window data.

## 8. Validation completed

- `./scripts/build.sh`: passed; Python 3.14, SQLite FTS5, frozen corpus and
  configuration contracts validated.
- `./scripts/test.sh`: 106/106 tests passed in 2.701 seconds.
- Frozen base corpus remained 10 documents/eight cases with an exact
  10,240-byte document and 32 distributed facts.
- Final implementation digest is identical in each final JSON report:
  `5335a3c71f247cdec434e48eca674d2538870decd3b5c60d06c507056fb8b2a2`.
- Tenant/collection isolation, source-span verification, bounded requests,
  malformed-output rejection, and 17-GiB Ollama allocation checks remained
  active throughout live runs.

## Recommended next configuration for broader testing

- Exhaustive threads: canonical thread routing, 32-message page maps, validated
  hierarchical merge; never direct fixed top-K.
- Parent/child storage: normalized parents.
- Embedding operations: persist vectors; normal batch 24 only with drift
  tolerance monitoring, or warm once plus singleton requests when exact rebuild
  reproducibility is required.
- General retrieval control candidate: 1,800-character chunks, zero overlap,
  retrieval candidates 8, K/context records 12, 1,200 per-record characters,
  14,400 total characters, RRF 60. Validate these with live embeddings before
  integration.
- Cross-encoder: candidate depth 8. Do not make it default until GPU latency and
  a larger multilingual/adversarial corpus are measured.
- `qwen3:8b` 32-message exhaustive map page: 7,168 context and 2,048 output is
  the smallest passing combination; use 8,192/2,048 when margin is preferable.
  Keep temperature zero and retain all page evidence.

## Remaining work

The hardening milestone is complete, but production readiness is not. Remaining
explicit work is:

- port a selected configuration into Thunderbird and run Thunderbird parity,
  xpcshell/browser, UI, migration, cancellation, startup/restart, and realistic
  mailbox tests;
- validate unlabeled field extraction and map/reduce completeness on a safe,
  representative real-mail distribution, including long multilingual threads;
- enable the NVIDIA container runtime and measure cross-encoder GPU latency and
  combined residency;
- add RAPTOR only if a larger long-document corpus demonstrates a need, and
  consider Self-RAG only with a compatible reflection-trained model under the
  measured VRAM cap.

## External runtime references

- TEI supported models and hardware:
  https://huggingface.co/docs/text-embeddings-inference/en/supported_models
- TEI reranker quick tour and `/rerank` behavior:
  https://huggingface.co/docs/text-embeddings-inference/en/quick_tour
- TEI source/runtime documentation:
  https://github.com/huggingface/text-embeddings-inference
- ModernBERT reranker model:
  https://huggingface.co/Alibaba-NLP/gte-reranker-modernbert-base
