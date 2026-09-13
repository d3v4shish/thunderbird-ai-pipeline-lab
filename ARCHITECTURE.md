# Architecture

## Components and data flow

The CLI loads versioned contracts and a frozen corpus. `Pipeline` validates and
normalizes documents, produces source-verifiable chunks, and writes canonical
documents, chunks, exact entities, deterministic vectors, and graph records to
one SQLite database. FTS5, exact lookup, dense cosine search, reciprocal-rank
fusion, and reranking produce a scope-locked evidence pack.

Document identity is the composite `(tenant, collection, document_id)`. Chunk
IDs percent-encode those components. Graph relationships are admitted only
when source label, normalized predicate, and target label occur in one source
sentence; every edge stores that assertion's canonical character span.

Sentence-window/parent-child candidates index a sentence-sized retrieval unit
while returning a larger canonical parent span. Parent spans shared by several
children are deduplicated before packing or exhaustive expansion. The optional
normalized SQLite layout stores each parent once in `parent_passages`; child
rows hold a scoped parent identifier and retrieval text. All exact, lexical,
dense, and chunk-fetch paths join the canonical parent before returning
evidence, preserving the same character offsets and source verification as the
legacy duplicated layout. The legacy layout remains available for paired tests.

`ToolExecutor` exposes only bounded read operations over that same scope.
`OllamaClient` can run a bounded tool loop or structured synthesis over the
evidence. Empty allowlists deny all calls, malformed/rejected attempts are
audited, and unique text spans—not outlines—consume the evidence budget. Tool
evidence joins the validation ledger. The deterministic model lane provides
reproducible tests without a server. The validator accepts facts only when a
provided citation points to a source span containing the value.

`Evaluator` scores frozen cases, applies hard safety gates, checkpoints every
run atomically, and passes records to the report writer. Fact scoring requires
the exact expected source identifier and value. Answer correctness is scored
separately from whether GraphRAG placed expected relations in context. Combined
repeat results include run-level failures even when a run ends before producing
case records. Reports preserve stage hashes, timings, evidence, prompts, tool
calls, original output, validated output, and failures. The adaptive matrix
chooses a deterministic, categorically balanced calibration subset from the
compatible Cartesian product and promotes the highest-quality hard-gate
survivors. Exhaustive mode remains explicit.

`rag_evaluation` runs before model evaluation and isolates one factor at a
time: chunker, chunk size, retrieval channel, top-K, query expansion,
reranking, and graph depth. It reports source coverage, labeled-fact integrity,
document/fact Recall@K, MRR, nDCG, evidence redundancy, packed characters,
scope integrity, graph-relation recall, and provenance validity. Only after
those ablations does it invoke deterministic generation and output validation.

`contextual_rag` is a separate live indexing experiment. For each
structure-aware chunk, a loopback chat model receives the complete bounded
synthetic document and that chunk, but no user query. Its short JSON context is
schema/length checked and rejects exact identifiers, dates, or amounts absent
from the source. Raw passage, deterministic metadata, and generated-context
indexes are then compared over identical source spans with local and endpoint
embeddings. Generated prose is stored only in `contextual_text`; retrieval
returns canonical `passage_text`, so it cannot satisfy citation validation.
Atomic cache identity includes corpus, model digest, and prompt version.

`query_rag` is a separate live query-time experiment over a frozen semantic,
paraphrase, compositional, negative, and long-document challenge set. It builds
one structure-aware endpoint-embedding index per repeat, then compares direct
hybrid retrieval with HyDE, model-generated RAG Fusion, decomposition,
step-back retrieval, local corrective retrieval, and adaptive model routing.
Transformation calls receive only the untrusted query, never corpus passages.
Their strict JSON outputs are bounded, checked for prompt-like content and
invented exact entities, and cached by query, model digest, prompt version,
validation version, and evidence digest where applicable. Invalid output falls
back to the original query.

Generated transformations may influence ranking but can never become answer
evidence. Reciprocal-rank fusion always resolves results back to unchanged
canonical source passages. The corrective lane grades direct top-K evidence,
may retry with local Fusion, and retains only passages the grader labels
relevant; it is intentionally a partial CRAG implementation because it has no
web or external-knowledge fallback. The adaptive router chooses only measured
retrieval methods and has no no-retrieval route. Reports preserve prompts, raw
outputs, validation diagnostics, rankings, latency, tokens, vector digests,
resource use, and per-repeat promotion decisions.

`email_rag` moves the decomposition candidate into a larger end-to-end
experiment. A pinned 180-message synthetic corpus models threads, revisions,
attachments, cross-message facts, multilingual text, prompt injection,
distractors, negative requests, and cross-tenant records. A deterministic
query-shape router keeps simple questions on direct endpoint hybrid retrieval,
uses model-generated decomposition only for multi-part questions, and uses a
canonical thread range for all/every requests with one resolvable thread ID.
Failed or invalid decomposition falls back to the original query.

Both direct and selective evidence enter the same live grounded-answer stage.
The answer validator requires exact offered citations and source FACT IDs. If a
model returns a field-qualified value such as `review_room: Sapphire Room`, the
validator maps it to `Sapphire Room` only when the same fact ID and canonical
value occur in a cited passage; the original value and normalization remain in
the report. For exhaustive queries, the prompt states the fact IDs visible in
the offered thread range and the validator rejects any omitted source fact.
Generated subqueries and answer prose never become source evidence.

`scale_evaluation` creates frozen 50, 100, 250, and 500-message threads with
one labeled fact per message, unrelated same-scope distractors, and a
cross-tenant shadow record. It compares fixed top-8 retrieval with canonical
full ranges, 32-message pages, and a hierarchical fact ledger. Page maps retain
canonical source evidence and stable order; reduction merges only validated
fact/value/source tuples in bounded batches. This makes omissions explicit
without placing an unbounded thread into one model prompt.

`template_mining` adds source-preserving body/signature/quoted segmentation,
sender-scoped bounded Drain families, deterministic typed-slot extraction,
boilerplate fingerprints, and shingle duplicate candidates. Families and
assignments are tenant/collection scoped; each assignment is keyed to the
canonical body digest and every slot stores an exact source offset. SQLite
stores family, assignment, and slot records in normalized tables and invalidates
assignments when source changes.

`template_evaluation` chronologically trains and holds out a frozen 113-message
family corpus. It isolates exact-subject, normalized-skeleton, Drain threshold/
support/cap/scope, shingle, and boilerplate factors, then rebuilds identical
indexes for raw, segmented, skeleton, Drain, deduplicated, and combined search
representations. Indexed metadata may change ranking; each returned `Evidence`
still resolves to the unchanged source span.

`template_scale` combines the selected family/slot design with 500–5,000-message
threads, exact source ledgers, latest-family lookup, bounded family graph
expansion, and normalized SQLite measurements. `template_live` separately
renders source-validated ledgers in 64-record pages. Ollama receives a dynamic
JSON schema containing allowed/required IDs but no expected values. Host code
validates output values against the source ledger and records every rejected
attempt; model output is never completeness authority.

`live_hardening` separates endpoint and generation concerns. Embedding drift is
measured across repeated calls, a third steady-state pass, batch/order changes,
duplicates, singleton requests, and three fresh loads; it records exact vector
digests, component deltas, cosine similarity, top-8 overlap/order, and retrieval
quality. Cross-encoder evaluation sends one unchanged hybrid candidate set to a
loopback TEI or Cohere-compatible reranker and compares no reranker,
deterministic, embedding, and joint query/passage scoring. Endpoint results may
only reorder all candidates; missing, duplicate, or malformed indexes fail
closed.

The answer-parameter lane uses the first 32-message map page of a frozen
50-message thread. It changes context window, output tokens, evidence budget,
and temperature one factor at a time, then tests combined context/output
finalists. `OllamaClient` compares the requested runtime context with the
model's separately discovered advertised capacity; VRAM residency and the
17-GiB allocation cap remain enforced independently. Full 50–500-message
completeness belongs to the paged hierarchy rather than an oversized prompt.

`oversized_email` isolates the single-document version of that problem. It
generates an exact-size synthetic email with facts distributed across the full
source, compares lossy truncation and top-K controls, and maps the complete
canonical document through overlapping bounded pages. Model tuples are
accepted only when their identifier and exact value occur in the page's source
span. Host code merges accepted tuples in source order, deduplicates overlap,
and paginates the deterministic ledger when it exceeds the output budget. The
optional final model renderer consumes only that verified ledger; it is not the
authority for completeness.

`oversized_designs` runs an objective-specific architecture matrix over that
same immutable fixture. It isolates input sampling, known-schema compaction,
chunk layout, retrieval channel/K, reranking, page size/overlap, hard-boundary
loss, rolling state, host/model hierarchical reduction, result pagination, and
bounded agent tools. Localized QA validates only the explicitly requested fact;
exhaustive page lanes validate every fact present in each page. This avoids
misapplying an exhaustive completeness contract to top-K distractor passages.
Contextual RAG and GraphRAG are recorded as specialized retrieval designs, not
as substitutes for exhaustive source traversal.

`thread_memory` adds normalized SQLite tables for per-email artifacts,
source-linked claims/events, deterministic and model relations, and bounded
thread rollups. Composite tenant/collection/document identity is retained in
memory and storage. RFC-like headers supply authoritative thread, reply, and
reference edges. The model receives the complete current bounded email plus a
prior-only ledger/graph rendering; current-email summaries cannot cite prior
messages, while semantic relations must target an earlier same-thread source
and quote a current-email assertion. Oversized emails switch to independent
source pages and a separate link pass. Generated content is search metadata;
retrieval and answers always resolve to original source spans.

`thread_memory_evaluation` compares one- versus two-pass extraction, four
summary uses, structural/allowlisted/open relations, four memory modes,
repeated/hierarchical placement, two chat models, and three repeats. The
hierarchy ranks thread parents, then email parents, then canonical passages.
Deterministic metadata and structural-graph controls provide paired baselines.
Hard gates cover scope, source spans, generation, grounded citations, validated
output, and forbidden claims. Candidate aggregation requires three repeats,
no baseline regression, a quality gain, the explicit thresholds recorded in
the matrix plan, and non-dominated artifact/retrieval/answer/stability/cost. Exact
fact/value matches may receive a host-added source citation; the repair is
audited and cannot add or remove facts.

`thread_memory_hardening` isolates deterministic bounds and scale. Its
one-factor sweep uses the 180-message corpus; 50-500-message threads compare
localized top-K memory with the explicit exhaustive source route; 10KB is sent
as one source and 256KiB is traversed in 12K/20K/30K pages. This validates
mechanics only and cannot replace live three-repeat model evaluation.

## Concurrency and boundaries

- SQLite writes are transactional; each pipeline run owns its connection.
- Query traces retain hashes and timings in full. Ingestion trace counts,
  timings, and errors are aggregated by stage so memory use is corpus-size
  independent.
- GPU model runs are serial (`concurrency=1`); deterministic indexing batches
  writes but does not use background workers. Models are unloaded after every
  matrix variant so residency from one candidate cannot affect the next.
- Context generation is serial and checkpointed per chunk. Context and
  embedding models may coexist only while their measured combined Ollama VRAM
  remains within the configured cap; both are unloaded after the experiment.
- Query transformation and corrective-grading calls are serial and atomically
  cached. Endpoint document and query embeddings are batched. A fresh index is
  built and both models are unloaded between query-time repeats so cross-load
  variation remains measurable.
- Email decomposition is serial and cached; final answers are deliberately
  regenerated for each fresh-load repeat. Identical answer prompts within one
  repeat are deduplicated so direct and selective lanes differ only when their
  evidence differs. Thread-range retrieval is local, scope locked, and ordered
  by canonical message timestamp and ID.
- Scale-thread page maps and hierarchical reductions are serial and bounded by
  explicit page/reduction sizes. They do not retain full model prompts.
- Oversized-email map calls are serial, checkpointed in the report, and bounded
  by explicit source-page, context, and output limits. Future parallelism must
  preserve source order and remain inside measured endpoint concurrency and
  aggregate VRAM limits.
- The design matrix runs serially and is self-contained: it does not read prior
  reports or model-output caches. Only the direct/map, schema-compaction, and
  targeted-RAG finalists receive three repeats; intentionally inferior or
  diagnostic rolling, hierarchy, page-size, and tool-agent lanes run once and
  cannot satisfy a stability gate.
- Cross-encoder requests are serial and loopback-only. CPU and GPU deployment
  are separately labeled; the reranker cannot mutate evidence.
- Thread-memory generation is chronological and serial. Successful artifacts,
  grounded answers, and completed model repeats are atomically checkpointed.
  Model switches wait for Ollama `/api/ps` to confirm unload, preventing a
  large chat model and embedding model from transiently competing for VRAM.
- Template live qualification is serial and staged: all approved models receive
  one smoke repeat, at most two passers receive three 1,000-record repeats, and
  one winner receives three 5,000-record repeats. Each call is bounded to 64
  records; total thread size changes page count, not context size. Checkpoints
  retain every completed model repeat.
- Storage stays inside the selected run directory.
- Network access during evaluation is loopback-only and used solely for Ollama
  and an explicitly configured reranker API.
- Documents are untrusted data. They cannot change scope, tools, prompts, or
  endpoint configuration.

## Decisions

- Standard-library-only keeps the harness reproducible and auditable.
- Character offsets are measured in normalized canonical text and checked on
  every retrieved chunk.
- Deterministic 32-dimensional vectors mirror Thunderbird's local fallback;
  endpoint embeddings are a separately labelled candidate lane.
- The 17-GiB eligibility gate uses the sum of Ollama-reported VRAM allocations
  for the active candidate configuration. Whole-GPU use is report-only
  telemetry.
- Source drift is visible through a manifest rather than silently changing the
  frozen baseline.
- Contextual retrieval has separate per-chunk and whole-email ablations. The
  latter sends one complete document of at most 48,000 characters to the model
  without a target chunk, validates one query-independent context, and shares
  it across unchanged source passages. Both generated forms remain untrusted
  index metadata and never evidence. They are candidates for cross-chunk
  semantic references, not exhaustive coverage: “All/every” requests retain
  the deterministic document-range path because repeated context can dilute
  Top-K ordering on repetitive documents.
- Direct endpoint hybrid remains the query-time default. Decomposition is a
  broader-evaluation candidate because it improved ranking without aggregate
  recall regression, but its cost and case-specific rank tradeoffs prevent
  promotion. HyDE, Fusion, step-back, corrective, and adaptive routing remain
  experimental; none passed the complete quality/stability criteria.
- Selective routing passed the larger synthetic email matrix in three repeats,
  but route attribution assigns the quality gain entirely to deterministic
  thread-range coverage. Decomposition had no quality gain on four multi-part
  exact-identifier cases and is not promoted by this experiment. Thread-range
  coverage advances only to broader evaluation, not a Thunderbird default or
  production-ready status: real-mail distribution, unlabeled extraction,
  router language coverage, and endpoint vector stability remain unresolved.
- Normalized parent storage is the measured storage candidate: it preserves
  exact rankings and source spans while reducing the paired database by 37.4%.
- Direct top-K is not valid for exhaustive thread requests. The bounded
  page-map/hierarchical-ledger path preserved all facts through 500 messages;
  it remains synthetic and requires Thunderbird integration testing.
- Template families are retrieval/routing metadata, not truth. The current
  candidate uses sender scope, similarity 0.6, support 3, and cap 1000. Search
  indexes boilerplate-deduplicated body text; family and slot records remain in
  normalized tables instead of being repeated in every chunk. Shingle F1 was
  only 0.894 and is not an authoritative deduplication rule.
- Strict structured output is a required boundary for template-ledger model
  rendering. Prompt-only JSON failed under injected source text; required-ID/
  no-extra-key schemas plus exact source-value validation passed the selected
  three-repeat stress lane. A larger context is not selected because the
  largest 5,000-record page used 1,745 prompt tokens at the 16K setting.
- For source-linked thread memory, hierarchical thread→email→passage placement
  matched repeated-memory retrieval quality on 180 messages while reducing
  indexed characters from 631,854 to 287,925. One-repeat Qwen3 and Phi-4
  smokes also used about 72% less answer context in the hierarchical lane. This
  selects an evaluation candidate, not a production default: semantic relation
  F1 was 0.500 and three-repeat live qualification is unfinished.
- Batch-24 Qwen embeddings are not byte deterministic even after warm-up.
  Singleton requests become exact after one warm pass and reproduce across
  fresh loads, at a measured throughput cost. Persisted embeddings remain the
  default operational assumption.
- The CPU ModernBERT cross-encoder improves fact MRR without recall regression,
  but its measured latency prevents default promotion. Candidate depth 8 is the
  current broader-evaluation setting because 16/32/64 add no quality.
- For the 32-message exhaustive map page, `qwen3:8b` passed at 7168 context and
  2048 output tokens in three repeats. Keep margin in integration; this is a
  measured fixture setting, not a universal model default.
- For one 256-KiB synthetic email, direct prompting failed the exhaustive JSON
  contract at both 8,192 and the advertised 40,960 context. Fourteen bounded
  20,000-character page maps plus exact source validation produced a complete
  64-record ledger in all three repeats. Use targeted top-K only for localized
  questions and the complete page/ledger path for known-schema exhaustive
  work. Open-ended summaries cannot inherit the synthetic completeness claim.
- Schema-aware deterministic compaction is preferred whenever exact source
  parsing is possible; its 3,391-character source retained all 64 records.
  Otherwise use independent bounded maps and keep accumulated state in the
  host. Rolling model state lost 34 earlier records, while a model hierarchy
  retained all facts but added five calls and 29.657 seconds of reducer work.
  Bounded agents remain targeted tools because six live range calls covered
  only 4.578% of the source.
