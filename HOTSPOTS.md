# Hotspots

Expected hotspots to verify with `scripts/benchmark.sh --full`:

- Chunk insertion and FTS maintenance during large rebuilds.
- Full-scan deterministic cosine search; this intentionally favors transparent
  parity over an external vector dependency.
- Graph path expansion on high-degree entity nodes.
- Evidence packing and model prefill for long-context cases.
- Model generation and repeated tool rounds in the live lane.

The benchmark records wall time, CPU time, peak RSS, database I/O size, query
latency, and throughput. Live runs add request bytes, tokens, and peak VRAM.
Change a hotspot only after capturing a baseline; update this file and
`BENCHMARKS.md` with measured before/after results.

## Observed baseline

The first 100K run exposed quadratic replacement lookups caused by missing
`document_id` and provenance indexes; it had not completed after three minutes.
After adding those indexes, ingestion remained near 2.1K documents/s and
completed 100K in 48.326 seconds.

Full-scan dense retrieval was the next measured hotspot: hybrid query p50 rose
from 8.710 ms at 1K to 81.912 ms at 10K and 894.558 ms at 100K. Porting
Thunderbird's deterministic LSH buckets reduced the corresponding 100K p50 to
138.300 ms, but raised ingestion from 48.326 to 80.573 seconds and database
size from 235,012,096 to 296,927,232 bytes. Remaining hotspots are LSH
candidate scoring at large scope, bucket write amplification, and live-model
prefill/generation. The matrix retains both strategies for recall and Pareto
analysis.

The 10K trace-retention profile found 50,000 ingestion `StageTrace` objects
that were discarded before query evaluation. Per-stage aggregation reduced
peak RSS from 94,412 KiB to 72,156 KiB (23.57%) and wall time from 5.26 to
4.70 seconds (10.65%) in the same in-memory profile. These are local paired
measurements. Trace storage is now bounded independently of corpus size, while
query traces remain unabridged for report review.

The post-hardening file-backed LSH rerun completed 100K ingestion in 72.290
seconds at 1,383 documents/s with 101,176 KiB peak RSS. Relative to the earlier
LSH run, ingestion was 10.3% faster and RSS 68.9% lower, while query p50 was
2.2% slower at 141.352 ms and storage was 10.9% larger at 329,154,560 bytes.
Index writes remain the dominant ingestion stage (56.410 of 72.290 seconds).

The first reviewed Qwen3 8B full smoke made the model path the dominant query
cost: p50 was 1.000 seconds and the 10KB extraction case took 5.970 seconds.
It returned 26/32 long-document facts, so evidence coverage and constrained
complete extraction—not raw retrieval latency—are the current live quality
hotspots. Three partial-matrix cases exhausted the four-round tool budget
without a final answer, making repeated tool-call termination another measured
hotspot to address before increasing tool budgets.

The completed corrected matrix confirmed two distinct quality hotspots. The
best Qwen3 configuration was fully stable and answered every direct question,
but top-eight evidence packing stopped at character 8,316 and omitted F27-F32
from the 10KB document. A second Qwen3 configuration used coverage-aware tools
and returned all 32 facts, but exact fact formatting and keyword GraphRAG failed
their gates. The next optimization target is therefore deterministic range
coverage combined with intent-multihop graph context, not a larger generation
model. Exact source-value canonicalization is the remaining output-contract
hotspot. Runtime model residency also needs diagnosis: one of 24 survivor repeat
slots returned zero loaded Ollama bytes and failed closed.

The staged RAG suite isolated two additional costs. Sentence-window indexing
created 173 child records for the frozen corpus versus 19 structure-aware
chunks and repeated 93.8% of parent-passage characters in the current flat
schema. It improved K=8 fact recall by 5.4 percentage points, but should use a
normalized parent table before production evaluation. Separately, K=16 reached
complete retrieval fact recall while nearly doubling mean packed context from
5,117 to 9,770 characters per query. This supports intent-specific exhaustive
coverage rather than a global K increase.

Generated Contextual RAG adds an indexing-time model call per chunk. The
23-chunk focused run spent 14.811 seconds in context generation before
embedding/indexing, making generation the dominant cost even on the tiny
corpus. Generated search text increased the Qwen-embedding SQLite index by
12,288 bytes over metadata context. More importantly, repeated generic context
can crowd distinct long-document chunks in top-K results: endpoint-hybrid
Recall@8 lost one aggregate fact even though fact MRR improved. Context caching,
batch/offline scheduling, short discriminative prompts, semantic-query routing,
and deterministic exhaustive coverage are therefore required before any
Thunderbird integration.

Three fresh endpoint-embedding loads also produced different vector digests
for identical contextualized inputs. Metadata-hybrid Recall@8 remained stable,
but generated-context hybrid varied from 0.7105 to 0.7895 and p50 varied from
341 to 399 ms. The endpoint was deterministic for repeated calls within one
load, so cross-load model/runtime variation—not corpus or cached-context drift—
is the current stability hotspot. Persisted embeddings avoid query-independent
reindex drift, but query-vector/ranking repeatability still needs diagnosis.

Whole-email context extraction reduces model work to one call per document:
the 11-email run used 5,391 prompt tokens and 5.924 seconds of model latency,
versus 31,540 tokens and 17.081 seconds for 23 per-chunk contexts. Its remaining
hotspot moves into retrieval: duplicating the same 141-character average
context across every passage added 2,503 indexed characters and 8,192 SQLite
bytes over metadata context, then crowded distinct sections out of hybrid
Top-K. It recovered the targeted late BOREALIS passage but reduced aggregate
hybrid Recall@8 from 0.8158 to 0.7632 in three runs. Whole-email context should
therefore be routed only to semantic cross-chunk questions, never used to prove
exhaustive coverage; documents above the 48,000-character context-call limit
still require paging or hierarchical reduction.

The query-time advanced-RAG matrix made model control calls the dominant online
cost. Direct endpoint hybrid retrieval had an 8.4 ms p50. Estimated uncached
p50 rose to about 291 ms for step-back, 370 ms for adaptive routing, 413-418 ms
for decomposition, 508-509 ms for Fusion, and 1.213 seconds for HyDE.
Transformation caching removes repeat generation during evaluation but does not
represent a first-seen user query, so cached search latency must not be reported
as online latency.

Query expansion also diluted exhaustive evidence. Direct retrieval found 26/32
facts in the 10,240-byte case, while HyDE and Fusion found 23/32. HyDE generated
unsupported dates and amounts despite a placeholder instruction; for the
MERIDIAN case it invented 2025 and $12.5 million instead of the source values
2028-04-17 and USD 91,300.00. These values remained retrieval metadata and
never became evidence, but they show why HyDE cannot be trusted as answer
context and why numeric drift should be treated as a routing warning.

Corrective grading is both a quality and latency hotspot. It correctly rejected
all three negative cases, but verdict accuracy fell from 82.4% to 77.8% and it
discarded complete two-document MERIDIAN evidence. Its estimated online p50
ranged from 537 ms to 1.097 seconds as correction retries varied. A production
sufficiency gate needs a deterministic exact-entity/fact path, calibrated
abstention thresholds, and a larger adversarial grader set before model-only
filtering is considered.

Fresh Qwen embedding loads again changed vector digests for identical model
digests, texts, and batching. Aggregate direct rankings remained stable in this
suite, but persisted document embeddings do not solve possible query-vector
variation after restart. Cross-load repeatability remains a release blocker,
along with deterministic document-range coverage for exhaustive requests.

The 180-message email experiment confirms that final answer generation, not
search, dominates ordinary query latency: answer p50 was 1.11-1.13 seconds,
while direct retrieval p50 was about 62 ms. Eighteen unique answer prompts
consumed 28.3-28.5 seconds of summed model time per repeat. Within routed cases,
decomposition performed three hybrid searches and took 184-194 ms; first-seen
query transformation raised three cases to roughly 0.58 seconds and one to
2.12 seconds. Decomposition should therefore remain limited to query shapes
that demonstrably need multiple searches.

Direct top-K is still the exhaustive-coverage hotspot. It returned eight of
twelve messages from the `ATLAS-900` thread. Canonical thread-range retrieval
returned all twelve in under 0.5 ms on this corpus and raised end-to-end fact
recall from 22/26 to 26/26, but its work and answer context grow linearly with
thread size and are currently capped at 32 passages. Large-thread paging,
deduplication, and hierarchical reduction need a separate scale benchmark.

Qwen ignored the exact-value formatting instruction for 21/26 selective facts,
usually returning `field_name: value`. Deterministic fact-ID/citation-aware
canonicalization repaired this without trusting generated values, but the high
normalization rate makes output formatting a continuing model-contract hotspot.
Real mail lacks synthetic FACT labels, so equivalent canonical field extraction
must be independently validated before Thunderbird integration.

Document embedding digests differed across all three fresh loads while query
embedding digests and rank-level metrics remained stable. This narrows, but does
not resolve, the endpoint-repeatability issue: a larger near-tie corpus could
turn small vector drift into ranking drift. Persisted vectors and restart-time
query comparisons remain required release checks.

## Hardening findings: 2026-09-13

The 50–500-message scale run confirms that top-K is structurally incapable of
answering exhaustive thread questions: top-8 recall falls to 1.6% at 500
messages. Full-range evidence grows to 152,392 characters, while 32-message
pages cap source text at 9,760 characters. The deterministic hierarchical
ledger restores all 500 facts with a 13,484-character maximum stage and about
529 KiB peak traced Python allocation. The remaining hotspot is generative map
and reduce validation on unlabeled real mail; the deterministic ledger does not
measure that model cost or error accumulation.

Normalized parent storage removes the measured sentence-window write
amplification: database size fell 37.4% with exact ranking/source parity. Median
ingest rose about 3.3% on this tiny corpus, and the standard 1K benchmark was
also slower in one post-change run. Index writes and FTS maintenance remain the
dominant deterministic ingestion cost; no performance improvement is claimed.

The Qwen embedding instability is now bounded rather than unexplained. Batch 24
continues to drift after multiple passes and across reloads. Top-8 overlap
remained at least 0.971 in the final three-load run with no recall delta, but
exact order changed. Singleton embedding is roughly four times slower per
180-document pass; after one warm pass, later passes and fresh-load rebuilds are
byte-identical. Production indexing must choose explicitly between batched
throughput plus tolerance monitoring and warmed singleton reproducibility, then
persist document embeddings rather than rebuilding opportunistically.

True cross-encoder quality is not free. On CPU, ModernBERT improved fact MRR by
0.0455 without changing recall, but median rerank time rose from 281 ms at eight
candidates to 2.159 seconds at 64. Because all depths produced identical
quality, eight candidates is the current test setting. GPU latency remains
unmeasured because the Docker host lacks the NVIDIA container runtime. The
idle CPU TEI container also occupied 9.327 GiB of host RAM, making memory a
deployment hotspot in addition to latency.

Exhaustive answer generation is the dominant live latency and token hotspot.
The 32-message page required 4,410 prompt tokens and 1,932 output tokens, taking
about 20–23 seconds per successful call. A 2,048 output cap is sufficient;
1,024 truncates JSON. A 7,168 context window is the smallest passing combined
finalist, but it leaves limited margin. Full 50–500-message work must stay in
the paged hierarchy, with checkpointed map outputs and omission validation,
rather than increasing one prompt's context window.

## Oversized single-email findings: 2026-09-13

The legacy fixed chunker's 20,000-character source cap is a correctness
hotspot. On the 262,144-byte fixture it covered only 7.629% of the source and
five of 64 unique facts. Structure-aware chunking covered the full source and
all facts. Oversized ingestion must not route through that fixed cap.

Direct large-context generation is both ineffective and expensive for
exhaustive extraction. `qwen3:8b` returned zero contract-valid facts at 8,192
and 40,960 context in every repeat. The 40,960 setting received 20,482 measured
prompt tokens but returned a generic error, showing that advertised capacity is
not an instruction-following or completeness guarantee.

Bounded mapping moved the hotspot from one unreliable call to 14 independently
validatable calls. At 20,000 source characters/page, map time averaged 30.892
seconds and the largest prompt was 4,031 tokens. A 30,000-character candidate
used only nine pages but took 31.055 seconds and consumed 5,964 prompt tokens;
fewer calls did not improve wall time. Twenty thousand characters retains more
context margin and is the current measured candidate.

Model prediction across page boundaries is a correctness hotspot. Two raw
outputs per repeat invented the immediately following source fact. Exact
per-page validation rejected both while preserving all 64 grounded facts.
Retries are reserved for omissions or malformed output; retrying a page that
already yielded every source fact would add cost without repairing an
unsupported extra.

The optional model renderer is a removable latency hotspot. It reproduced the
64-record ledger in all three runs but added 14.760 seconds on average. Render
the verified deterministic ledger directly unless natural-language synthesis
is required. If the ledger is large, page or stream it: the 512-fact stress
control needed ten bounded output pages. Parallel page mapping is not yet
measured and must not be enabled without endpoint-concurrency, VRAM, ordering,
and cancellation tests.

## Oversized architecture matrix findings: 2026-09-13

Rolling model memory is the clearest avoidable hotspot. It repeatedly emitted
the entire accumulated state, reached 34 retained facts at page seven, then
collapsed to five at page eight as prompt/output pressure grew. It ended at
30/64 facts after 78.507 seconds—more than twice the validated host-map time.
Persistent ledger state must remain outside the model context.

Model hierarchy avoids rolling-state collapse but is unnecessary for exact
records the host can merge. The fan-in-four diagnostic retained 64/64, but its
five reducer calls added 29.657 seconds after deterministic leaves. Combined
with live page mapping, that is about 60.494 seconds versus 30.837 seconds for
map plus host ledger. Reserve model hierarchy for lossy thematic summaries or
outputs the host cannot combine semantically.

Over-fine sentence windows are a memory/context hotspot on long repetitive
email. They created 2,485 child records and 4,463,067 returned passage
characters, versus 163 chunks and 291,104 characters for structure-aware
chunking. Despite full character coverage, one labeled fact was split. Parent
deduplication helps packing but does not repair an integrity break.

Exhaustive top-K merely relocates the context overflow. Lexical K=128 found all
64 facts but returned 229,474 characters; hybrid needed all 163 chunks and
291,104 characters. Retrieval should remain targeted, while explicit all/every
requests use complete page traversal.

Tool-agent traversal is bounded by both call count and range size. The live
agent used six 2,000-character calls, covered 4.578%, and returned three facts.
The deterministic theoretical maximum under current tool limits is 9.155%.
Increasing autonomous rounds to cover the whole source would make progress,
resume, and completeness harder than a host-owned page loop.

Known-schema compaction is the measured fast path: full-source deterministic
scanning reduced model input to 3,391 characters and the model returned 64/64
in 14.663 seconds mean. When model prose is unnecessary, direct deterministic
rendering removes even that generation cost.

## Source-linked thread-memory findings: 2026-09-13

Repeating complete thread memory on every passage is the main new indexing
hotspot. On 180 synthetic messages it indexed 631,854 characters, versus
287,925 for thread→email→passage hierarchy with identical 0.9744 fact recall
and 0.8077 MRR. The hierarchy is the current scale candidate, but its email
fan-out cannot be reduced from eight to four: that lost one aggregate fact.
The final deterministic run measured 295.249 ms for repeated retrieval and
124.951 ms for hierarchical retrieval. These one-run local timings identify
where work occurs; they are not a production latency claim.

Generated relation quality is the current correctness hotspot. Qwen3 and Phi-4
both scored 0.5 relation precision/recall/F1 on the four-message smoke. These
edges remain untrusted retrieval metadata; deterministic reply/reference edges
and original source spans remain authoritative. A full three-repeat matrix is
required before choosing one-pass versus two-pass or allowlisted versus open
relations.

Answer provenance should not depend on a model copying the right citation.
Qwen returned the correct M02 value but cited only the later confirmation.
Host code now attached the offered passage that literally contained M02 and
its exact value, recording one repair in each Qwen lane. Phi's hierarchical
answer cited the source itself; its repeated answer included an obsolete M01
fact and therefore failed correctness. Deterministic repair never invents or
deletes facts.

Large-model switching was a stability hotspot. Phi extraction fit the policy at
16,972,072,876 Ollama VRAM bytes, but loading it immediately after the embedding
model produced partial residency and a cap failure. Ollama unload now polls
`/api/ps` for up to 15 seconds before the next model is loaded, and endpoint
failures remain retryable in the repeat checkpoint. The retry passed. This does
not replace three fresh-load repeats.

Fixed Top-K recall necessarily falls as an exhaustive thread grows: it retained
8/50, 8/100, 8/250, and 8/500 source facts. Do not increase global K or trust a
summary to hide that omission. User-selected exhaustive mode must traverse the
canonical thread in bounded pages; localized mode can use hierarchical memory.
For oversized individual messages, the effective direct limit reserves room
for prompt, prior memory, and output; larger input uses independent map pages.

The complete measured record, including live answer latency, citation repair,
VRAM, storage growth, and the open qualification gates, is in
[`reports/thread-memory-evaluation-summary.md`](reports/thread-memory-evaluation-summary.md).

## Template-aware and extreme-scale findings: 2026-09-13

Repeated boilerplate is an avoidable indexing hotspot. On the paired held-out
fixture, the deduplicated representation retained 1.000 document/family
Recall@4 and raised MRR from 0.955 to 0.977 while reducing indexed characters
from 11,214 to 4,798. Concatenating every family/template/slot record into chunk
text grew the index to 11,461 characters. Keep that metadata normalized and
join it only when routing needs it.

Online template clustering itself was not the dominant scale cost: mining
5,000 synthetic messages took 620.1ms, versus 12.782s for normalized SQLite
ingestion. Index/FTS writes remain the deterministic hotspot. Drain is
order-sensitive and synthetic family prevalence is favorable; cluster drift,
adversarial poisoning, multilingual variants, and realistic sender cardinality
remain unmeasured.

Fixed Top-K is the correctness hotspot for exhaustive intent. Top-8 retained
0.16% of 5,000 facts. Ordered pages and a host ledger retained all facts but
make cost linear in source/result size: a 16MiB message required roughly
850 20K-character pages, and a 5,000-record model render required 79 calls per
repeat. Large results must be paged/streamed; neither a bigger K nor a larger
single context solves output completeness.

Prompt-only output contracts were a measured security/stability hotspot. Three
models copied an injected private key, Granite 3.1 changed schema on larger
pages, and Granite 4.1 repeatedly hit the 120-second timeout. A required-ID,
no-extra-key Ollama JSON schema plus exact host value validation repaired the
selected lane. Granite then used no retries across 237 stress pages. Structured
decoding and host validation are required controls, not optional prompt polish.

Live rendering dominates cost even after repair. Template mining took under a
second at 5,000 messages; Granite's exhaustive render took about nine minutes
per repeat and generated 120,869 output tokens. Prefer direct deterministic
ledger display when prose is unnecessary. The largest page used only 1,745
prompt tokens, so raising the 16K context would spend additional KV-cache/VRAM
without reducing the 79-page output workload.

See
[`reports/template-aware-evaluation-summary.md`](reports/template-aware-evaluation-summary.md)
for the complete before/after model failures and retained artifacts.
