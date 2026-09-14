# Results, failures, and decisions

## Executive result

The original adaptive and advanced-RAG test program is complete. The older
free-prose source-linked memory lane still has an open qualification. Its
candidate-only v4 successor passed three fresh repeats with Qwen3, Granite 3.1
MoE, and Qwen 2.5, then failed closed on DeepSeek and stopped before Phi-4 and
Granite 4.1. The pipeline is **not production-ready**.

That statement does not mean everything failed. Several components behaved
very well under synthetic tests. It means the combined evidence is not broad or
stable enough to claim safe production behavior:

- no complete end-to-end configuration in the adaptive RAG matrix passed every
  quality threshold;
- endpoint embeddings were not byte-stable under normal batching;
- generated Contextual RAG helped one cross-chunk case but hurt aggregate
  recall;
- HyDE and Fusion reduced aggregate fact recall;
- the corrective model grader deleted complete evidence;
- model output often needed citation-aware value canonicalization;
- source-linked summaries recovered their smoke facts, but semantic relation
  precision/recall/F1 was only 0.500;
- candidate-only v4 fixed every measured host-side v3 failure, but one of four
  attempted chat models violated the strict output schema;
- tests used synthetic data and no Thunderbird integration was performed;
- the measured standard benchmark regressed rather than improved.

## Result dashboard

| Evaluation | Expected | Actual | Decision |
|---|---|---|---|
| Build + deterministic tests | reproducible, no profile/network dependency | build passed; current suite 202/202 | lab contracts validated |
| Staged modular RAG | identify stage-level strengths | advanced structure and sentence-window pipelines scored 1.000 deterministic quality | structure-aware candidate; retain modular routing |
| Contextual RAG | improve cross-chunk semantic retrieval without source drift | BOREALIS rose from absent to hybrid rank 3, but full-suite recall fell | selective candidate only |
| Query-time RAG | generated transforms beat direct retrieval without regression | decomposition only small rank gain; HyDE/Fusion worse; step-back/adaptive no net gain; corrective regressed | direct hybrid default; no global generated method |
| Selective email RAG | multi-part and exhaustive routing improve answers | selective 13/13 versus direct 12/13; all gain came from thread range | promote thread-range to broader evaluation; not decomposition |
| 50–500-message threads | expose K loss and prove bounded exhaustive coverage | direct recall 0.160 to 0.016; full/paged/hierarchy all 1.000 | page + hierarchy for all/every |
| Source-linked thread memory | retain final state without repeating all memory | hierarchy matched 0.9744 recall while using 54.4% fewer indexed chars; both model relation streams scored 0.500 F1 | hierarchical localized candidate; canonical exhaustive route; live qualification open |
| Candidate-only structured memory v4 | keep source anchors and completeness out of model control | deterministic 6/6 email and 4/4 scale pass; three models 21/21 each; DeepSeek rejected on duplicate IDs | strongest memory design tested; broader validation required |
| Parent storage normalization | smaller DB with exact parity | -37.410% DB, exact ranking/evidence parity | integration candidate |
| Embedding drift | exact vectors or bounded quality tolerance | batch 24 not exact; overlap/quality tolerance passed; warmed singleton exact | persist vectors; monitor tolerance |
| True cross-encoder | improve order without candidate/safety mutation | fact MRR 0.7933 to 0.8388; +281 ms p50 at depth 8 | optional broader evaluation, CPU cost high |
| Answer parameters | find safe context/output floor | 7,168/2,048 smallest measured passing pair; 8,192/2,048 gives margin | bounded page candidate |
| Adaptive model matrix | find a live quality/safety winner under 17 GiB | 0/48 calibration variants passed every quality threshold | no model pipeline promotion |
| Standard benchmark | avoid unmeasured performance claims | ingest/search/RSS/DB all slightly worse | no performance-improvement claim |

## Deterministic RAG result

The stage-isolated suite first removed live-model variation. At K=8:

| Stage | Best measured lane | Key result |
|---|---|---|
| Chunking | sentence-window for recall; structure-aware for balance | 0.892 versus 0.838 fact recall, but sentence-window had 0.938 duplicate-parent redundancy before normalization |
| Chunk size | 1,800 chars | 1.000 fact recall versus 0.838 at 1,200 |
| Retrieval | lexical on this exact-term corpus | 1.000 document, 0.757 fact recall |
| Retrieval depth | K=16 | 1.000 fact recall versus 0.838 at K=8 |
| Query expansion | deterministic adaptive | fact recall 0.784 versus 0.757 and MRR 0.889 versus 0.778 |
| Reranking | deterministic | fact recall 0.838 and MRR 1.000 |
| Graph | intent-multihop | 1.000 relation recall versus 0.667 keyword |
| Full pipeline | advanced structure | 1.000 quality and all hard/quality gates |

This proved that the pipeline code could preserve scope, source spans, and
facts. It did **not** prove a live LLM/embedding configuration would behave the
same way.

## Contextual RAG: one strong win, one global loss

Expected behavior: generated query-independent metadata should connect a late
chunk to the parent document without replacing source evidence.

Actual targeted behavior:

- query: `How much funding did Project BOREALIS-204 receive?`;
- expected: source fact `C01 = USD 6,400.00`;
- raw and metadata hybrid: absent from K=8;
- contextual hybrid: rank 3 in all three live repeats;
- all 23 generated contexts passed source-span and exact-entity grounding.

Actual suite behavior:

| Repeat | Metadata hybrid recall | Contextual hybrid recall | Metadata fact MRR | Contextual fact MRR |
|---:|---:|---:|---:|---:|
| 1 | 0.8158 | 0.7895 | 0.3494 | 0.3604 |
| 2 | 0.8158 | 0.7105 | 0.3483 | 0.3422 |
| 3 | 0.8158 | 0.7105 | 0.3494 | 0.3291 |

Generated descriptions repeated common terms across 10KB ledger chunks and
displaced unique facts from K=8. Decision: route Contextual RAG only to measured
cross-chunk/anaphora shapes and keep its prose outside answer evidence.

## Query-time RAG result

The suite contained 13 queries and 42 expected positive facts. Every method
used the same chunks, `qwen3-embedding:4b`, K=8, tenant/collection scope, and
canonical evidence rules. Three repeats unloaded models between runs.

| Method | Fact recall@8 | Fact MRR | First-query p50 estimate | Expected vs actual |
|---|---:|---:|---:|---|
| Direct hybrid | 0.857 | 0.410 | 8.4 ms | reliable control; keep |
| HyDE | 0.786 | 0.403–0.415 | 1,213 ms | expected semantic help; instead lost 3 facts and hallucinated numbers |
| Fusion | 0.786 | 0.398 | 508–509 ms | expected wording robustness; instead displaced useful long-document chunks |
| Decomposition | 0.857 | 0.416 | 413–418 ms | preserved recall, raised MRR 0.950 to 1.000; larger-test candidate |
| Step-back | 0.857 | 0.410 | 291 ms | same quality as direct, extra call |
| Corrective | 0.738–0.810 | 0.380–0.387 | 537–1,097 ms | rejected negatives, but deleted valid positive evidence |
| Adaptive | 0.857 | 0.410 | 370 ms | route choice 12/13, but no end-to-end gain |

On the 10,240-byte case, direct returned 26/32 facts while HyDE and Fusion
returned 23/32. Two of 65 transformation records remained invalid after bounded
retries: one duplicate decomposition and one literal HyDE placeholder. Six HyDE
records introduced new numeric tokens. All generated text remained retrieval
metadata, so source-span validity and scope integrity stayed 1.000.

The corrective failure is especially important. Complete MERIDIAN date and
budget passages were ranks 1 and 2, yet the grader returned `incorrect` with no
relevant labels and discarded both. Verdict accuracy was only 0.824, 0.778,
and 0.778. A model judge cannot be an unprotected deletion gate.

Decision: keep direct hybrid as the normal route. Keep decomposition as a
selective research candidate, not a default. Do not promote HyDE, Fusion,
step-back, corrective, or the tested adaptive router.

## Email RAG result

The later fixture contained 180 synthetic messages, 13 questions, and 26 facts:
150 routine distractors, revisions, attachment content, semantic paraphrases,
Spanish, prompt injection, four two-message answers, one twelve-message
exhaustive thread, a negative, and a cross-tenant shadow.

| Metric | Direct | Selective |
|---|---:|---:|
| Document recall | 0.9697 | 1.0000 |
| Retrieval fact recall | 0.8462 | 1.0000 |
| Retrieval fact MRR | 0.5468 | 0.5617 |
| Exact answer fact recall | 0.8462 | 1.0000 |
| Correct answers | 12/13 | 13/13 |
| Citation precision | 1.0000 | 1.0000 |
| Grounded fact precision | 1.0000 | 1.0000 |
| Final negative abstention | 2/2 | 2/2 |
| Scope/source validity | 1.0000 | 1.0000 |

These values were identical across three repeats.

The deterministic router labeled eight direct, four decomposition, and one
thread-range query and selected all 13 correctly. However, the four decomposed
cases had exactly the same fact ranks as direct retrieval. Their three-search
path took 184–194 ms, versus approximately 62–64 ms aggregate direct p50, and
added model transformation time on the first query.

The entire quality gain came from ATLAS-900:

- direct K=8: D01–D06, D08, D09; 8/12;
- ordered range: D01–D12; 12/12;
- direct raw answer was accurately grounded but incomplete;
- final selective output included every value and citation in all repeats.

The first range smoke still omitted D12 after receiving all passages. Adding an
explicit 12-ID completion ledger to the prompt and enforcing
`INCOMPLETE_EXHAUSTIVE_OUTPUT` fixed the final run. This is evidence that
retrieval completeness and generation completeness need separate checks.

Qwen commonly returned values like `review_room: Sapphire Room` instead of the
canonical `Sapphire Room`. Citation-aware normalization repaired 21/26
selective facts per repeat only when the same FACT ID and canonical value were
present in a cited source. This made semantic answers score correctly, but it
also exposes a model-formatting weakness.

Decision: thread-range coverage is a broader-evaluation candidate.
Decomposition is not promoted from this experiment. The entire selective
package remains non-production because it uses synthetic labels, one model
pair, English route heuristics, and a bounded test corpus.

## Scale result: 50 to 500 messages

Every synthetic thread placed one independent fact in every message, plus 12
same-scope distractors and one cross-tenant shadow. The expected output was all
facts in canonical order with no duplicate or unverifiable span.

| Thread | Direct top-8 | Full range | Paged range | Hierarchical ledger |
|---:|---:|---:|---:|---:|
| 50 | 0.160 | 1.000 | 1.000 | 1.000 |
| 100 | 0.080 | 1.000 | 1.000 | 1.000 |
| 250 | 0.032 | 1.000 | 1.000 | 1.000 |
| 500 | 0.016 | 1.000 | 1.000 | 1.000 |

At 500 messages, full evidence was 152,392 characters. Pages of 32 limited a
source page to 9,760 characters. The hierarchical path's largest stage was
13,484 characters, traced peak Python allocation 529,356 bytes, and p50 30.752
ms. Reduction batches 4, 8, 16, 32, and 64 all retained 500/500 facts.

Decision: never answer unbounded all/every requests with fixed top-K or one
full prompt. Use ordered range, paging, validated map ledgers, and bounded
reduction.

## Source-linked email and thread-memory result

The follow-up experiment processed each synthetic email chronologically. A
model saw the complete current bounded email plus deterministic headers and
prior-only thread memory. Current-email summaries had to resolve to current
source spans. Generated summaries, events, and model relations could improve
retrieval but could never become answer evidence.

On the 180-message deterministic sweep, repeated and hierarchical placement
both scored 0.9744 Recall@8 and 0.8077 MRR. Hierarchy indexed 287,925 instead of
631,854 characters and measured 124.951 instead of 295.249 ms in the final
single run. Email-parent K=4 reduced recall to 0.9487; K=8 retained baseline
quality.

The live smoke asked for the final approved venue after a thread changed its
proposal from M01 `Silver Room` to M02 `Sapphire Room`:

| Lane | Retrieval recall | MRR | Answer correct | Context | Answer latency |
|---|---:|---:|---:|---:|---:|
| Qwen3 repeated | 1.000 | 0.500 | 1.000 | 42,874 | 2.726 s |
| Qwen3 hierarchical | 1.000 | 1.000 | 1.000 | 12,009 | 0.848 s |
| Phi-4 repeated | 1.000 | 1.000 | 0.000 | 42,032 | 13.544 s |
| Phi-4 hierarchical | 1.000 | 1.000 | 1.000 | 11,987 | 2.079 s |

Both models extracted 4/4 messages and achieved complete evidence/narrative
summary fact recall. Each had one field rejected. Qwen required an audited
citation attachment to a passage already offered with the exact M02/value;
Phi's repeated output failed because it included obsolete M01. Both relation
streams scored 0.500 precision, recall, and F1.

Decision: advance hierarchical retrieval for localized questions and retain
canonical paging for explicit exhaustive mode. Do not promote the model lane:
these are one-repeat diagnostics, semantic relation quality is below threshold,
and finalist validation is unfinished. See the
[`thread-memory evaluation summary`](../reports/thread-memory-evaluation-summary.md).

## Candidate-only structured-memory v4 result

V4 stopped asking the model to create source anchors, event prose, values,
offsets, targets, or email lists. Host code mined the current source, created
opaque candidate IDs, retained all safe events, and resolved selected IDs back
to immutable spans. The model received one complete bounded email, no user
query, at most 24 selected prior records, and only closed-world choices.

The unchanged v3 baseline passed 1/6 adversarial emails and 0/4 old-reference
thread cases. It lost the optional template family, treated quoted/signature/
injection text as current events, dropped the decision after sentence 24, and
omitted the explicitly referenced oldest message. V4 passed 6/6 and 4/4. It
retained all 31 events with a durable cap of 48 or more while holding model
hints to 24, and it found the exact oldest reply target at 50, 100, 250, and
500 prior messages.

Three fresh temperature-zero repeats produced:

| Model | Result | Summed latency | Measured allocation |
|---|---:|---:|---:|
| Granite 3.1 MoE | 21/21 | 16.181 s | 7,325,289,020 B |
| Qwen3 8B | 21/21 | 34.358 s | 6,387,799,162 B |
| Qwen 2.5 14B | 21/21 | 52.484 s | 10,521,914,899 B |
| DeepSeek V2 16B | 5/6 attempted | 36.762 s | 11,340,947,127 B |

DeepSeek's sixth output contained 24 entries but duplicated six IDs. The host
rejected the response and did not silently deduplicate it. Per the staged gate,
Phi-4 and Granite 4.1 were not run. This makes v4 the strongest memory design
tested here, not a production result. The exact prompt, expected and raw output,
tokens, telemetry, and failure are in the
[`structured-memory v4 qualification`](09-structured-memory-v4-qualification.md).

## Storage result

Expected: normalized parents must be no larger and must preserve exact behavior.

Actual across three repeats:

- ranking and evidence parity: exact;
- document recall: 1.000 both;
- fact recall: 0.8919 both;
- MRR/scope integrity: 1.000 both;
- duplicated database: 569,344 bytes;
- normalized database: 356,352 bytes;
- database change: -37.410%;
- median ingest: 12.702 ms duplicated, 13.116 ms normalized.

Decision: normalization is an integration candidate on storage/parity evidence.
No ingestion-speed claim is made.

## Embedding stability result

Expected: either exact reproducibility or a measured, explicit quality bound.

Actual batch-24 behavior:

- repeated vectors, warm vectors, order changes, and duplicate-in-request
  vectors were not exact;
- minimum cosine remained at least 0.997264 in the recorded comparisons;
- fresh-load ranking exactness was 0.5385 and 0.7692 versus load one;
- mean overlap@8 was 0.9712 and 0.9808;
- fact/document recall did not change;
- one pass took 6.85–6.95 seconds.

Actual singleton behavior:

- first cold pass differed from second;
- second and third passes were exact;
- the full singleton sequence was exact across three fresh loads;
- ranks and quality were exact;
- one pass took 25.99–26.70 seconds.

Decision: persist embeddings. Normal batching may be considered only behind
the measured >=0.95 overlap@8 and <=0.01 aggregate quality-drift gate. Warmed
singleton indexing is the exact but slow fallback.

## Cross-encoder result and runtime failures

The intended first reranker did not run successfully:

- GPU `gte-multilingual-reranker-base`: Docker had no NVIDIA device driver;
- CPU TEI 1.7 fallback: no ONNX export, then an Intel MKL SGEMM crash in the
  Candle GTE backend.

These are infrastructure/runtime failures, not low model scores.

The successful CPU fallback, `gte-reranker-modernbert-base` on TEI 1.9.3,
preserved candidate membership, scope, source spans, and recall in all repeats.
Fact MRR improved from 0.7933 to 0.8388. Candidate depth added no quality:

| Candidates | Mean p50 | Mean p95 | Fact recall | Fact MRR |
|---:|---:|---:|---:|---:|
| 8 | 281 ms | 309 ms | 0.9697 | 0.8388 |
| 16 | 557 ms | 601 ms | 0.9697 | 0.8388 |
| 32 | 1,086 ms | 1,198 ms | 0.9697 | 0.8388 |
| 64 | 2,159 ms | 2,252 ms | 0.9697 | 0.8388 |

Decision: depth 8 CPU cross-encoder is a broader-evaluation candidate when the
rank gain is worth about 281 ms and 9.327 GiB idle host RAM. GPU quality/latency
remains untested.

## Model and answer-parameter result

The adaptive matrix's best calibration record used `qwen3:8b`, deterministic
local vectors, and embedding reranking, with quality 0.9619. Its three-repeat
combined result scored 0.9550, answer correctness 1.000, required-fact recall
0.7297, structured output 1.000, and p50 782 ms. It remained below the complete
quality requirement. Larger models did not automatically perform better; see
the model article for the per-family table.

The separate 32-fact answer test established:

- 4K context failed; 8K, 16K, and 32K passed;
- 256/512/1,024 output tokens truncated; 2,048 passed;
- 4,096 evidence characters retained 13/32 facts;
- 8,192 retained 27/32;
- the full 9,687 characters retained 32/32;
- 7,168 context / 2,048 output was the smallest combined passing pair;
- 8,192 / 2,048 is the sensible measured-margin candidate;
- temperature 0 remains preferred even though 0.2 happened to pass.

Decision: use bounded page-level answer generation. Do not enlarge a single
prompt to cover a 50–500-message thread.

## One email larger than the context window

The oversized-email lane used one exact 262,144-byte synthetic message with 64
facts spread from beginning to end. Prefix-only and head-tail truncation each
recovered 6/64 facts. An exhaustive top-8 query recovered 1/64, while separate
targeted questions found the requested beginning, middle, and end facts. The
legacy fixed chunker also exposed a 20,000-character source cap: it indexed only
7.629% of the message and five unique facts. Structure-aware chunking covered
the full source and all 64 facts.

Direct `qwen3:8b` extraction failed the required JSON contract in all three
repeats at both 8,192 and the advertised 40,960-token context. The 8K response
mentioned only one exact value in the wrong schema; the 40,960 response
mentioned none. More context therefore did not solve exhaustive instruction
following.

Fourteen overlapping 20,000-character source pages recovered a validated
64/64 ledger in all three repeats. Raw output was not perfect: Qwen predicted
two next-page facts per repeat. Exact page-source validation rejected those
extras before reduction. Map time averaged 30.892 seconds; the optional final
model renderer added 14.760 seconds and can be removed by displaying the
verified ledger directly. A 30K page setting used fewer calls but was no faster
and left less context headroom. A deterministic 1-MiB/512-fact stress case
retained all facts and required ten bounded output pages.

Decision: use top-K for narrow questions; use full structure-aware source
paging, fail-closed per-page validation, deterministic ledger merge, and paged
delivery for known-schema exhaustive requests. Open-ended summaries remain
hierarchical and cited but cannot claim that every detail is present. Full
evidence is in the
[`oversized-email evaluation summary`](../reports/oversized-email-evaluation-summary.md).

The follow-up architecture matrix tested the alternatives rather than stopping
at the first passing design. Its decisive results were:

- all four contiguous 24,576-character samples found 6/64 facts and eight
  uniform windows found 8/64;
- deterministic schema compaction reduced the complete source to 3,391
  characters and passed 64/64 in all three live repeats;
- targeted hybrid RAG produced 9/9 contract-valid answers, averaging 693 ms;
- exhaustive lexical retrieval eventually found 64/64 at K=128 but returned
  229,474 characters, recreating the context overflow;
- rolling model state took 78.507 seconds, collapsed at page eight, and ended
  with 30/64;
- model hierarchy preserved 64/64 but added 29.657 seconds and no information
  beyond deterministically validated leaves;
- the bounded live agent used all six range calls, covered 4.578%, and returned
  3/64 facts.

This sharpens the decision: deterministic schema extraction is the fast path
where possible; targeted RAG is for narrow questions; host-owned page mapping
and state are for exhaustive model extraction. Model hierarchy is reserved for
semantic summaries, and agent/tool traversal is not the exhaustive scanner.
See the
[`complete oversized design matrix`](../reports/oversized-design-evaluation-summary.md).

## Template-aware and extreme-scale result

The sender-scoped Drain miner passed the 60/40 chronological holdout with
family F1 1.000, slot precision/recall 1.000/1.000, no over-merged family, and
valid source spans. Boilerplate-deduplicated search text preserved all measured
Recall@4 and dynamic values while indexing 4,798 rather than 11,214 raw
characters. Fully concatenating family/template/slot text reached slightly
higher MRR but made the index larger than raw, so normalized metadata plus the
deduplicated surface is the current Pareto design.

At 5,000 messages, deterministic template mining took 620.1ms, reduced search
text by 66.4%, and preserved exact family/assignment/latest/ledger results.
Direct Top-8 exhaustive recall fell to 0.0016, while ordered paging and the
host ledger retained 1.000. Both template-dense and unique-prose 16MiB emails
also retained 1.000 known-schema recall under complete bounded traversal;
prefix recall was about 0.001.

The first unconstrained live prompt exposed a real boundary failure: Phi-4,
Qwen 2.5, and Qwen 3 copied an injected private key, Granite 3.1 changed output
shape on larger pages, and Granite 4.1 repeatedly timed out. Adding an
allowed-ID JSON schema—without expected values—and fixing unsupported-output
accounting produced five smoke passers. Granite 3.1 and Qwen 3 then passed all
three 1,000-record repeats. Granite was roughly twice as fast and passed three
5,000-record repeats: 15,000/15,000 exact values, 237 pages, no retry, no
unsupported output, and 7,325,289,020 measured Ollama VRAM bytes.

This promotes the template/ledger design to broader Thunderbird integration
testing, not production. It does not repair the separate 0.500 semantic-
relation F1 or complete the older thread-memory live Cartesian matrix. See the
[`template-aware evaluation summary`](../reports/template-aware-evaluation-summary.md).

## Performance result

Baseline versus final standard 1,000-document benchmark:

| Metric | Baseline | Final | Direction |
|---|---:|---:|---|
| Ingest | 0.726129 s | 0.762134 s | +4.96% slower |
| p50 search | 1.705490 ms | 1.804227 ms | +5.79% slower |
| p95 search | 2.125555 ms | 2.370168 ms | +11.51% slower |
| Peak RSS | 32,120 KiB | 32,880 KiB | +2.37% |
| SQLite | 3,420,160 B | 3,432,448 B | +0.36% |

These are one-host measurements and do not establish a stable regression size,
but they clearly do not support a performance-improvement claim. The major live
hotspots were model generation, embedding rebuilds, CPU cross-encoder scoring,
and exhaustive output length—not the millisecond deterministic retrieval path.

The later same-method structured-memory v4 check measured baseline/final ingest
at 0.730760/0.732320 seconds, p50 at 1.797299/1.852720 ms, p95 at
2.320323/2.367568 ms, RSS at 34,860/35,108 KiB, and identical 3,465,216-byte
databases. That movement is also mixed and unreplicated; no improvement is
claimed.

## What is ready for broader integration testing

- structure-aware, source-verifiable chunks;
- exact + lexical + dense hybrid retrieval;
- deterministic reranking and stable tie-breaking;
- source-backed local graph traversal for relationship queries;
- ordered thread/document range for explicit exhaustive requests;
- page-level ledgers and bounded hierarchical reduction;
- normalized parent storage;
- host-generated, source-digest-bound event and slot candidates;
- model-selected IDs as optional semantic hints rather than memory authority;
- strict scope, source-span, fact, citation, abstention, and completeness gates;
- persisted embeddings with visible drift policy;
- optional selective contextual/cross-encoder lanes behind measurements.

## What should not be enabled globally

- HyDE, Fusion, step-back, or the tested adaptive router;
- model-only corrective deletion;
- decomposition for every multi-clause question;
- generated context on every chunk;
- fixed top-K for all/every requests;
- one giant full-thread prompt;
- batched embedding rebuilds treated as byte-deterministic;
- a configuration chosen solely by parameter count or one quality score.

## Remaining production gap

Before a production claim, the selected design still needs a reviewed
Thunderbird port, parity tests against Thunderbird's interfaces, realistic and
privacy-safe email evaluation without synthetic FACT labels, multilingual route
coverage, concurrency/soak/crash recovery, GPU reranker evaluation if desired,
security review of the actual integration boundary, and quality gates that all
pass across repeated runs. The older free-prose memory lane still has its open
matrix. Candidate-only v4 needs a DeepSeek disposition, followed by the blocked
Phi-4/Granite 4.1 ladder, plus HTML/MIME, multilingual, deletion/invalidation,
larger unlabeled retrieval, human review, concurrency, cancellation, and
selected 180-message/oversized finalists.

The authoritative consolidated review is
[`hardening-evaluation-summary.md`](../reports/hardening-evaluation-summary.md).
The newer source-linked result is
[`thread-memory-evaluation-summary.md`](../reports/thread-memory-evaluation-summary.md).
The latest template/scale result is
[`template-aware-evaluation-summary.md`](../reports/template-aware-evaluation-summary.md).
The candidate-only result is
[`structured-memory-qualification-summary.md`](../reports/structured-memory-qualification-summary.md).
Earlier raw evidence remains under [`reports/`](../reports/).
