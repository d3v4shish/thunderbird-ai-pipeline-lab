# Oversized Email Design Evaluation Report

Date: 2026-09-13

## Executive verdict

There is no single best design for every oversized-email request.

| Objective | Best tested design | Result | Important limitation |
|---|---|---:|---|
| Find one requested fact | full-source structure-aware index, targeted lexical/hybrid retrieval, strict grounded answer | live 9/9 | retrieval quality must also be tested on paraphrases, not only exact IDs |
| Extract every known record | bounded structure-aware map, exact per-page validation, deterministic host ledger, paged output | live 64/64 in 3/3 repeats | completeness oracle requires a known schema or source-derived checklist |
| Extract a deterministically recognizable schema | source scanner compacts only verified records, then optional model rendering | live 64/64 in 3/3 repeats | cannot be used when the desired information has no reliable parser |
| Produce a high-level summary | hierarchical cited summaries | not objectively scored here | must be labelled non-exhaustive; fact recall is not summary quality |

Do not use one giant prompt, silent truncation, fixed-K retrieval for “every”
requests, rolling model memory, or the current six-call agent as exhaustive
designs. GraphRAG and Contextual RAG solve different retrieval problems and do
not remove the need for complete source traversal.

This is a synthetic evaluation result, not a production-readiness
certification.

## Exact reproduction

Deterministic matrix:

```sh
./scripts/run.sh oversized-design-evaluate \
  --name oversized-design-deterministic-final
```

Self-contained live matrix:

```sh
./scripts/run.sh oversized-design-evaluate \
  --live --chat-model qwen3:8b --repeats 3 \
  --name oversized-design-qwen3-v3-final
```

Validation and standard benchmark:

```sh
./scripts/build.sh
./scripts/test.sh
./scripts/benchmark.sh --name oversized-design-post-change-1000
```

The live command does not read an earlier report or cache. It reruns direct
generation, bounded mapping, schema compaction, targeted RAG, alternate page
sizes, rolling state, model hierarchy, and the bounded tool agent. Every prompt
and raw response is retained in the JSON companion.

## Frozen input and model

- Email size: exactly 262,144 bytes.
- Facts: 64 checkpoint records distributed from beginning to end.
- Planning estimate: 65,536 tokens at four characters/token.
- Fixture digest:
  `815e8169d6c432c24e8701f3becec9831bbb122b3022852cc3dca000c6c5e58d`.
- Implementation digest:
  `06a3f6c2b5d46c75ed5f0cde4965ab6c869622a1724196f416ddd9030de90aba`.
- Prompt version: `oversized-design-matrix-v3`.
- Model: `qwen3:8b`, digest
  `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.
- Advertised model context: 40,960 tokens.
- All data is synthetic; no Thunderbird profile or mailbox was accessed.

Three objectives were scored separately:

1. Localized QA requires only the requested grounded fact.
2. Exhaustive extraction requires every source record and proof that every
   source page was processed.
3. Open-ended summary quality is subjective; labeled-fact retention is only a
   detail-loss proxy and cannot prove summary completeness.

## Design 1: direct and sampled input

Every sampling lane had the same 24,576-character source budget used by the
8K planning control.

| Input selection | Characters sent | Facts available | Recall ceiling | Complete result possible? |
|---|---:|---:|---:|---|
| Prefix | 24,576 | 6/64 | 9.375% | no |
| Suffix | 24,576 | 6/64 | 9.375% | no |
| Head + tail | 24,577 including separator | 6/64 | 9.375% | no |
| Middle | 24,576 | 6/64 | 9.375% | no |
| Eight uniformly sampled windows | 24,583 including separators | 8/64 | 12.5% | no |
| Known-schema source compaction | 3,391 | 64/64 | 100% | yes, for this schema |

Sampling can create a preview but cannot answer “all/every.” Uniform sampling
was slightly less position-biased but still omitted 56 facts.

The direct model call failed independently of those deterministic ceilings. In
all three repeats, strict recall was 0/64 at both 8,192 and 40,960 runtime
context. At 8K, Qwen returned an invented `status/summary/analysis` object and
mentioned only the final visible checkpoint. At 40,960 it returned a generic
error. Mean direct call times are not promoted because both designs failed;
the individual 8K calls took 5.36–7.08 seconds and the 40,960 calls took
8.60–8.77 seconds.

Conclusion: input capacity and instruction-following completeness are separate
properties. Increasing `num_ctx` is not a recovery strategy.

## Design 2: chunking architecture

| Chunk design | Source coverage | Unique facts | Chunks | Returned passage characters | Finding |
|---|---:|---:|---:|---:|---|
| Current fixed/capped | 7.629% | 5/64 | 13 | 22,159 | hard correctness failure after character 20,000 |
| Fixed, cap removed | 100% | 64/64 | 163 | 291,296 | complete, but splits without structural preference |
| Structure-aware | 100% | 64/64 | 163 | 291,104 | complete and preferred |
| Sentence-window | 100% | 63/64 | 2,485 | 4,463,067 | one fact split; 15.3x passage amplification versus structure-aware |

Sentence-window demonstrates why source coverage alone is not enough. Its
parent spans collectively covered the source, yet one fact was not intact in
any extracted window and overlapping parents repeated 992 fact occurrences.
The design is useful for some local semantic questions, but it is a poor
default for exhaustive extraction of this long repetitive email.

Conclusion: remove the fixed source cap for oversized ingestion and prefer
structure-aware, source-verifiable chunks. Measure fact integrity and context
amplification in addition to character coverage.

## Design 3: targeted retrieval

Beginning, middle, and end probes asked separately for `L0001`, `L0032`, and
`L0064`.

| Retriever | K=1 | K=4 | K=8 | K=16 |
|---|---:|---:|---:|---:|
| Exact-entity channel | 0/3 | 0/3 | 0/3 | 0/3 |
| SQLite FTS5 lexical | 3/3 | 3/3 | 3/3 | 3/3 |
| 32-D local dense | 0/3 | 0/3 | 0/3 | 0/3 |
| Hybrid RRF | 2/3 | 3/3 | 3/3 | 3/3 |

The exact channel did not recognize these four-digit synthetic IDs. The tiny
local embedding did not model them usefully. Hybrid K=1 inherited dense-channel
ranking noise and missed one target; K=4 repaired it. The deterministic
reranker moved all three targets to rank 1, while embedding reranking pushed
all three outside top-8.

The live finalist used hybrid K=8. Retrieval placed the targets at ranks 3, 4,
and 2. Under the objective-specific prompt and validator, Qwen returned exactly
one grounded record for every probe in all three repeats: 9/9 contract-valid
answers. It used 2,964–2,984 prompt tokens, 34 output tokens, and averaged
693 ms/call, including colder first-repeat calls.

Example raw output:

```json
{
  "facts": {
    "L0001": "OVERSIZED-L0001-07001"
  }
}
```

Conclusion: RAG is the best design for a narrow question, but retrieval mode,
K, and reranker must be evaluated on the actual query distribution. For exact
IDs in this fixture, lexical K=1 was better than hybrid K=1.

## Design 4: trying to make retrieval exhaustive

Retrieval can eventually return every fact only by making K so large that the
context-window problem returns.

| K | Lexical facts/chars | Dense facts/chars | Hybrid facts/chars |
|---:|---:|---:|---:|
| 8 | 4 / 14,341 | 0 / 13,049 | 1 / 13,038 |
| 16 | 12 / 28,661 | 5 / 27,379 | 8 / 27,366 |
| 32 | 27 / 57,311 | 14 / 56,092 | 20 / 56,069 |
| 64 | 56 / 114,705 | 21 / 113,549 | 38 / 113,427 |
| 128 | 64 / 229,474 | 41 / 228,317 | 61 / 228,265 |
| 256 | 64 / 291,104 | 64 / 291,104 | 64 / 291,104 |

Lexical K=128 found every labeled fact while covering only 80.9% of source,
but returned 229,474 characters—far beyond the selected context. K=256
returned all 163 overlapping chunks and 291,104 characters. Exact retrieval
returned nothing for the generic “list every checkpoint” query.

Conclusion: “retrieve nearly the entire index” is not a useful exhaustive RAG
design. Route explicit all/every requests to complete source paging.

## Design 5: page construction and boundaries

Structure-aware pages were tested at 4,096, 8,192, 12,000, 20,000, and 30,000
characters with 0, 128, 256, and 512 characters of overlap: 20 one-factor
configurations. Every configuration covered 100% of source and retained all 64
facts. Page counts ranged from 74 at 4,096/512 to nine at every 30K setting.
Overlap produced between zero and nine duplicate fact occurrences, all removed
by stable fact-ID reduction.

Ordinary hard character cuts happened to retain every fact at the sampled 4K
and 20K sizes. A deliberately placed 6,472-character boundary split `L0002`
and another record, reducing independently parsed hard pages to 62/64. This is
why a few passing page sizes do not establish boundary safety.

Live page-size results:

| Source-page size | Pages | Recall | Rejected extras | Max prompt | Map wall time | Repeat status |
|---:|---:|---:|---:|---:|---:|---|
| 8,192 chars / 128 overlap | 33 | 64/64 | 1 | 1,746 tokens | 30.100 s | one diagnostic |
| 20,000 chars / 256 overlap | 14 | 64/64 | 2 per repeat | 4,031 tokens | 30.840 / 30.728 / 30.942 s | three repeats |
| 30,000 chars / 256 overlap | 9 | 64/64 | 1 | 5,964 tokens | 29.087 s | one diagnostic |

The apparent 1.75-second advantage of 30K over the 20K mean is one-repeat
noise, not a promotion result. It also leaves much less room inside an 8K
context. The three-repeat 20K setting remains the measured-margin candidate.

Qwen still predicted exact next-page facts not present in the current page.
The source validator rejected them. No retries were needed because every
source fact had already been accepted.

Conclusion: structure-aware boundaries plus exact source validation matter
more than a small page-count difference.

## Design 6: deterministic schema compaction

The host scanned the complete source and copied only the 64 exact, verified
record spans into a 3,391-character compact source. This is not generic model
summarization; it is deterministic schema extraction.

Qwen rendered all 64 records with valid JSON in all three repeats. Prompt size
was 1,801 tokens, output was 1,546 tokens, and wall time was 14.947, 14.523,
and 14.517 seconds (14.663-second mean).

This is the fastest complete live design tested, but only because the answer
schema is recognizable without the model. In that situation, the model is
optional: deterministic UI rendering is faster and safer still.

Conclusion: use deterministic parsers for dates, addresses, message headers,
known IDs, and other source-verifiable structures before invoking a model.

## Design 7: bounded map plus deterministic host ledger

The promoted exhaustive design mapped every 20K source page independently,
accepted only exact page-backed tuples, and merged them in host code. It
retained 64/64 facts in all three repeats with a 30.837-second mean map time.
The raw page contract failed where Qwen predicted two unsupported boundary
facts per repeat, but neither entered the ledger.

The optional final model renderer also returned 64/64 in all repeats, but added
14.668, 14.796, and 14.861 seconds (14.775-second mean). Direct deterministic
ledger rendering avoids that cost and another possible omission point.

Conclusion: model at the bounded extraction edge; deterministic code for
validation, ordering, deduplication, completeness state, and display.

## Design 8: rolling model memory

The rolling design sent one page plus the model's previous fact state, then
asked it to reproduce the whole accumulated state on every call. It grew from
five facts at page 1 to 34 at page 7. At page 8, with a 4,721-token prompt and
an increasingly long expected output, it collapsed to only five facts:

```json
{
  "facts": {
    "L0035": "OVERSIZED-L0035-07035",
    "L0036": "OVERSIZED-L0036-07036",
    "L0037": "OVERSIZED-L0037-07037",
    "L0038": "OVERSIZED-L0038-07038",
    "L0039": "OVERSIZED-L0039-07039"
  }
}
```

It ended with 30/64 facts (46.875% recall), took 14 calls and 78.507 seconds,
and repeatedly emitted unsupported boundary predictions. This is slower and
less correct than independent maps plus host state.

A deterministic 4,096-character rolling text tail similarly retained only the
last 56/64 ledger records. A fixed memory window necessarily forgets something
once accumulated state exceeds the budget.

Conclusion: persistent state belongs outside the model context.

## Design 9: hierarchical reduction

Deterministic host hierarchies with fan-in 2, 4, and 8 all retained 64/64 facts.
They are useful when the final data structure itself needs bounded merging.

A one-repeat model hierarchy used four first-level groups and one final merge.
It also retained 64/64, with five calls, a largest 1,801-token prompt, and
29.657 seconds of reducer latency. Its leaves were deterministically extracted,
so this isolates reduction; adding the 20K model-map mean would make the full
model map-plus-hierarchy path approximately 60.494 seconds.

Conclusion: hierarchy is useful for genuinely oversized outputs or thematic
summaries. For a ledger that host code can merge exactly, model reduction adds
cost and risk without adding information.

## Design 10: output truncation, pagination, and streaming

The verified ledger is 4,619 characters.

| Output character budget | One-response facts | Result pages | Paged facts |
|---:|---:|---:|---:|
| 1,024 | 14/64 | 5 | 64/64 |
| 2,048 | 28/64 | 3 | 64/64 |
| 4,096 | 56/64 | 2 | 64/64 |
| 8,192 | 64/64 | 1 | 64/64 |

A 1-MiB/512-fact control from the preceding oversized-email evaluation needed
ten 4,096-character result pages. Output limits are therefore a separate
problem from input limits.

Conclusion: return a cursor/page count and stream or paginate deterministic
records. Never silently cut a generated answer.

## Design 11: bounded agent and tool calling

The deterministic best case for the current `range_coverage` tool is six calls
times 4,000 characters: 24,000 characters, 9.155% source coverage, and 6/64
facts. Complete traversal would require at least 66 calls before overlap,
validation, or retries.

In the live run, Qwen omitted the optional `length`, so each tool call used the
2,000-character default. It correctly advanced offsets 0, 2,000, 4,000, 6,000,
8,000, and 10,000, then exhausted the six-call budget. It covered 4.578% of the
email and returned the three observed facts correctly: 3/64 overall.

Agentic control cannot override a hard tool budget. Raising the budget to 66+
autonomous calls would be slower, harder to resume, and harder to prove complete
than a host-owned 14-page loop.

Conclusion: use tools for bounded targeted investigation, not as the primary
exhaustive scanner. The host should own traversal and progress.

## Designs that solve different problems

| Design | Useful here for | Why it was not given an exhaustive score |
|---|---|---|
| Contextual RAG | semantic/cross-chunk localized retrieval | generated metadata can change ranking but cannot remove finite K |
| GraphRAG | relationship and path questions | this flat record fixture contains no source-asserted relation graph |
| Corrective or Agentic RAG | retrying poor targeted evidence | grading/search loops do not prove all source ranges were visited |
| RAPTOR-like summaries | themes and high-level navigation | recursive summaries are lossy and cannot guarantee exact detail retention |
| Larger-context model | fewer input pages | still bounded; capacity does not guarantee schema compliance or output completeness |

Those methods remain valuable in their intended routes. They should compose
with, not replace, the complete source traversal needed by exhaustive requests.

## Performance and resource result

The self-contained matrix made 131 chat calls and 537 total loopback endpoint
requests. It sent 3,499,249 bytes and received 8,088,292 bytes. Peak
Ollama-reported model allocation was 8,648,549,990 bytes (about 8.05 GiB), and
peak whole-GPU use was 10,389,291,008 bytes (about 9.68 GiB), below the 17-GiB
allocation cap.

The standard fixed 1K benchmark after the isolated evaluator change measured:

| Metric | Result |
|---|---:|
| Ingest wall | 0.736191 s |
| Throughput | 1,358 docs/s |
| Query p50 | 1.790135 ms |
| Query p95 | 2.276921 ms |
| Peak RSS | 33,568 KiB |
| SQLite bytes | 3,432,448 |

The previous hardening run was 0.762134 seconds ingest, 1.804227 ms p50,
2.370168 ms p95, and 32,880 KiB RSS. These are single-run local differences;
the new code is an isolated evaluator and no production-pipeline performance
improvement is claimed.

## Recommended production architecture

```text
canonical email
  -> full-source structure-aware ingestion (no hidden source cap)
  -> classify request
       narrow question
         -> lexical + dense/hybrid candidates
         -> deterministic rerank where measured useful
         -> strict cited answer validator
       exhaustive known-schema request
         -> bounded source pages
         -> independent model extraction only where parsing is insufficient
         -> exact per-page source validation
         -> checkpointed host ledger in canonical order
         -> paged/streamed deterministic rendering
       open-ended summary
         -> bounded hierarchical cited summaries
         -> explicit “summary, not exhaustive” status
```

Required operational behavior:

- persist page completion and ledger state outside model context;
- show partial status and failed page numbers;
- support cancellation and resumable retries;
- reserve context and output headroom using measured tokenizer counts;
- reject source-invalid records even when every source fact was also returned;
- bound future parallel maps by measured endpoint concurrency and aggregate
  VRAM, preserving canonical result order;
- do not send deterministic structured data back through a model merely for
  formatting.

## Remaining production gaps

- Real unlabeled mail, HTML, quoted reply chains, attachments, tables, OCR, and
  multilingual oversized messages were not tested in this lane.
- Open-ended summary usefulness and omission severity need a human-rated,
  privacy-safe corpus; 64 synthetic fact labels are not a summary oracle.
- Exact-entity support for identifier shapes such as `L0001` needs a deliberate
  contract if such IDs matter in production.
- Cancellation, checkpoint recovery, partial-result UI, output cursors, and
  bounded parallel mapping are not integrated into Thunderbird.
- Model hierarchy, rolling state, alternate page sizes, and the tool agent have
  one live diagnostic each and are not stability-qualified.
- The complete Thunderbird parity, security, concurrency, soak, and crash tests
  remain outstanding.

## Evidence

- Compact final matrix: [`oversized-design-qwen3-v3-final.md`](oversized-design-qwen3-v3-final.md)
- Complete live JSON: [`oversized-design-qwen3-v3-final.json`](oversized-design-qwen3-v3-final.json)
- Deterministic matrix: [`oversized-design-deterministic-final.json`](oversized-design-deterministic-final.json)
- Standard benchmark: [`oversized-design-post-change-1000.md`](oversized-design-post-change-1000.md)
- Evaluator: [`../src/tb_ai_lab/oversized_designs.py`](../src/tb_ai_lab/oversized_designs.py)
- Deterministic tests: [`../tests/test_oversized_designs.py`](../tests/test_oversized_designs.py)
