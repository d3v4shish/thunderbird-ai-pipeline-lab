# How the pipeline and RAG methods work

## RAG in one sentence

Retrieval-Augmented Generation first finds source material and then asks a
language model to answer from that material. The important word is *source*:
the model is not supposed to answer from memory when the mailbox should be the
authority.

The lab's baseline data flow is:

```text
synthetic documents
  -> validate identity, scope, metadata, and size
  -> normalize text and extract source-backed entities/relations
  -> split into source-verifiable chunks
  -> store canonical text + exact/FTS/vector indexes + graph edges
user query
  -> lock tenant and collection scope
  -> exact + lexical + dense retrieval
  -> reciprocal-rank fusion
  -> optional reranking / graph / bounded read-only tools
  -> pack unchanged evidence under record and character limits
  -> generate a strict JSON answer
  -> validate facts, citations, abstention, scope, and source spans
```

Every experimental technique changes one or more boxes in this flow. That is
why “RAG” is not one algorithm and why a method can improve one query while
hurting the full suite.

## The baseline retrieval methods

### Exact retrieval

Exact retrieval looks for literal identifiers or indexed metadata. It is very
good for `ORCHID-271` and poor when the user paraphrases the source. In the
staged suite it had 0.500 document recall and only 0.081 fact recall@8.

### Lexical retrieval

Lexical retrieval uses SQLite FTS5 to find shared words. It handled the
exact-term synthetic suite well: 1.000 document recall and 0.757 fact recall@8.
Its weakness is a vocabulary gap—for example, a query using “funding” may miss
a passage that only says “settlement value.”

### Dense retrieval

Dense retrieval embeds the query and chunks as vectors. Similar meaning can
match even without identical words. The deterministic local embedding lane
scored 0.583 document recall and 0.676 fact recall@8 on the staged suite. The
live suites also used `qwen3-embedding:4b`; its quality was useful, but normal
batched vectors were not byte-identical across calls or model reloads.

### Hybrid retrieval

Hybrid retrieval runs exact, lexical, and dense search, then combines ranks
with reciprocal-rank fusion (RRF). It is the practical default because mailbox
questions mix project codes, names, dates, and semantic paraphrases. The
staged hybrid lane scored 1.000 document recall and 0.757 fact recall@8. A
deterministic reranker then raised fact recall to 0.838.

RRF uses rank positions instead of incomparable raw BM25/vector scores. In
simplified form, each result receives `1 / (rrf_k + rank)` from each list. The
tested `rrf_k` values 10, 30, 60, and 120 had essentially the same fact recall;
60 remains the conservative default.

## Chunking-related RAG

### Fixed chunks

Fixed chunking slices near a character limit, with overlap to reduce boundary
loss. It is simple and predictable, but may split headings from bodies or one
email section from another.

### Structure-aware chunks

Structure-aware chunking prefers paragraph/section boundaries while preserving
canonical offsets. It matched fixed chunk quality in the first staged suite and
is easier to audit. At 1,800 characters it recovered all labeled staged facts
at K=8, though this larger size also packed more text.

### Sentence-window / parent-child retrieval

This method indexes a small child sentence but returns a larger parent passage.
The child makes matching precise; the parent gives the answer model context.
It raised staged retrieval fact recall from 0.838 to 0.892 at K=8, but the first
schema repeated parent text heavily: 0.938 measured redundancy and 173 child
rows versus 19 ordinary chunks. Normalizing each parent into one canonical row
reduced the measured SQLite database from 569,344 to 356,352 bytes while
preserving rankings and evidence exactly.

This is not the same as overlap. Overlap repeats source characters between
adjacent chunks; sentence-window retrieval deliberately maps many small search
units to one verified context unit.

### Deterministic thread-range retrieval

An “all/every” question is a coverage request, not an ordinary relevance
question. A fixed K=8 can never return 12, 50, or 500 independently relevant
messages. The selective pipeline recognizes an exact thread identifier and
reads that thread's canonical messages in timestamp/message-ID order.

For ATLAS-900, direct K=8 returned 8/12 action codes. Thread range returned
12/12. At 50, 100, 250, and 500 messages, direct K=8 recall necessarily fell to
0.160, 0.080, 0.032, and 0.016; full, paged, and hierarchical range methods all
retained 1.000 recall.

### Paged and hierarchical reduction

Paging bounds how much source enters one stage. Hierarchical reduction makes a
validated page ledger and merges ledgers in bounded batches. It differs from
RAPTOR in this lab: the current ledger is deterministic extraction with source
IDs, not model-generated recursive semantic summaries.

At 500 messages, one unbounded source set held 152,392 characters. Paging kept
one source page to 9,760 characters; the hierarchy's largest page/reduction
stage was 13,484 characters while retaining all 500 facts.

### Source-linked whole-email and thread memory

The follow-up memory design gives the model one complete current bounded email,
deterministic headers, and only earlier same-scope thread memory. The model
produces a short retrieval context, a source-linked evidence summary, a longer
narrative summary, events, and optional semantic relations. The current email's
summary cannot borrow facts from earlier messages. Cross-email state lives in a
separate chronological ledger and relation graph.

This is different from ordinary chunk-level Contextual RAG below: the generated
artifact belongs to an email and thread-memory record, not to the answer. It may
help rank canonical passages, but only original email spans can be evidence.
On 180 deterministic messages, hierarchical thread→email→passage placement
matched repeated-context recall of 0.9744 while indexing 54.4% fewer characters.
In one-repeat live smokes it cut Qwen/Phi answer context by about 72%, but model
semantic relation F1 was only 0.500. It is therefore an evaluation candidate,
not a production result.

## Contextual RAG

Contextual RAG generates a short, query-independent description for each chunk
using the whole parent document. That description is prepended only to the
chunk's *search representation*. The unchanged chunk remains answer evidence.

Example: the late BOREALIS passage says only `settlement_value: USD 6,400.00`;
the project name occurs more than 3,000 characters earlier. Qwen generated:

> The chunk details the working group's review of packaging, staffing, and
> transport checks for Project BOREALIS-204, with final approval of a USD
> 6,400.00 settlement.

Raw and metadata hybrid retrieval missed the fact at K=8. Contextual hybrid put
it at rank 3 in all three repeats. However, generated context diluted ranking
on repetitive 10KB chunks, reducing full-suite hybrid fact recall from 0.8158
to 0.7895, then 0.7105 and 0.7105. The correct conclusion is selective use for
cross-chunk references, not global replacement.

## Query-time generated RAG

These techniques generate search material *after* seeing the user query. All
transformations were corpus-blind and could influence retrieval only.

### HyDE

Hypothetical Document Embeddings asks a model to write the sort of passage that
might answer the question, then embeds that hypothetical passage. It can bridge
vocabulary gaps but can also invent plausible details. For MERIDIAN-552, the
model invented a 2025 launch and a roughly $12.5 million budget; the source says
2028-04-17 and USD 91,300.00. The invented text was never evidence, but it still
changed ranking. Aggregate fact recall fell from 0.857 to 0.786.

### Multi-query RAG Fusion

RAG Fusion asks for several synonymous search queries, searches each, and
merges ranks with RRF. It is useful when wording is ambiguous. Here it also fell
to 0.786 fact recall because extra queries displaced useful 10KB ranges from
K=8.

### Query decomposition

Decomposition splits a multi-part request into independently searchable
questions. It preserved aggregate recall and improved aggregate MRR from 0.950
to 1.000 in the query-time suite. In the later 180-email suite, direct hybrid
already put both parts at ranks 1 and 2 for all four multi-part cases, so
decomposition added 184–194 ms retrieval-path cost without a quality gain.

Decomposition therefore remains selective: it is not useful merely because a
query contains the word “and.”

### Step-back retrieval

Step-back generates a broader conceptual question intended to retrieve a rule
or policy behind a narrow request. Several outputs simply repeated the original
query. Quality exactly matched direct retrieval while adding a model call, so
it was not promoted.

### Corrective RAG (local subset)

The corrective lane grades evidence as correct, ambiguous, or incorrect. It
may run a broader local Fusion search and retain only passages labeled relevant.
No web search was allowed.

It rejected all unanswerable cases, but its grader wrongly rejected complete
MERIDIAN evidence. Fact recall varied from 0.810 to 0.738, below direct 0.857.
This demonstrates a critical rule: a model grader cannot be an uncalibrated
hard deletion gate.

### Adaptive RAG

Adaptive RAG routes a query among direct, HyDE, Fusion, decomposition, and
step-back paths. The tested router used a Qwen prompt, not the trained
classifier from the Adaptive-RAG paper. It chose the utility-optimal lane on
12/13 cases but produced exactly direct retrieval's aggregate quality while
adding about 370 ms estimated first-query p50.

Routing accuracy is not enough; the selected route must improve final evidence.

## GraphRAG

The implemented graph stores source-backed entity/relation edges and can walk
one or more hops under the same scope. Keyword graph matching recovered two of
three tested relations; intent-aware multihop traversal recovered all three.

This is a focused, local GraphRAG implementation. It is **not** Microsoft-style
community clustering, community summaries, or global corpus synthesis. Graph
passages remain linked to their canonical source sentences.

GraphRAG helps relationship questions such as “which team owns the vendor that
supplies X?” It does not solve exhaustive thread coverage and does not replace
normal retrieval.

## Agentic RAG and tool calling

Agentic RAG means the model or a controller can choose a sequence of retrieval
actions instead of receiving one fixed search result. In this lab, the bounded
read-only tool surface contains search, fetch, range coverage, document outline,
graph neighborhood/path, and document aggregation operations.

The “agentic” part is constrained:

- a case-level allowlist controls which tool names may run;
- every argument has a strict schema;
- tenant/collection scope is supplied by trusted state, not model text;
- call, round, evidence-record, and character budgets are hard limits;
- tool evidence must still pass source/citation validation;
- unknown tools, malformed arguments, and cross-scope fetches fail closed.

This is safer than giving the model arbitrary shell, network, or mailbox access.
It is still not autonomous production deployment: only deterministic/mock tool
contracts and sampled live model behavior were evaluated.

## Methods deliberately not claimed as complete

| Method | Status | Why |
|---|---|---|
| Self-RAG | Deferred | Needs a compatible reflection-trained model and token protocol. Existing support validation is not Self-RAG. |
| RAPTOR | Deferred | Needs model-generated recursive summary trees and a larger corpus; current deterministic hierarchy is not RAPTOR. |
| Web-augmented CRAG | Not run | The lab is loopback-only and used local corrective retrieval. |
| Community/global GraphRAG | Not run | Only source-backed local relation traversal was implemented. |
| GPU cross-encoder | Not run | This host lacked a Docker NVIDIA device driver; CPU TEI was measured instead. |

## What this evidence supports

For this workload, the strongest design is a modular pipeline: hybrid retrieval
for normal questions, deterministic range/paging for exhaustive thread requests,
source-backed graph traversal for relationship questions, optional contextual
metadata only for measured cross-chunk cases, and strict answer validation.
Generated query transformations should be routed by demonstrated need rather
than enabled globally.

Primary evidence:
[`staged-rag-evaluation.json`](../reports/staged-rag-evaluation.json),
[`contextual-rag-qwen3-focused.json`](../reports/contextual-rag-qwen3-focused.json),
[`query-rag-qwen3-final.json`](../reports/query-rag-qwen3-final.json),
[`email-rag-qwen3-final.json`](../reports/email-rag-qwen3-final.json), and
[`hardening-final-threads.json`](../reports/hardening-final-threads.json). The
source-linked follow-up is in
[`thread-memory-evaluation-summary.md`](../reports/thread-memory-evaluation-summary.md).
