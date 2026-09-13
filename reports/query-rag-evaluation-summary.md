# Query-time Advanced-RAG Evaluation Summary

Date: 2026-09-12

Verdict: **Keep direct endpoint hybrid retrieval as the default. None of the new
methods is production-ready. Decomposition is the only method worth evaluating
on a larger realistic corpus.**

## What was tested

This experiment tested query-time retrieval methods independently of final
answer generation. That distinction matters: it measures whether the right
source text reaches the model, not whether a chat model can turn that evidence
into a good final email answer.

The 13-case suite combines the existing frozen tests with six new synthetic
documents and five targeted cases:

- semantic paraphrase: retrieve `Harbor Team` when the query asks who runs a
  service-restoration drill but the source uses continuity-program language;
- vocabulary mismatch: retrieve `West Atrium` for a badge-pickup question when
  the source calls it a physical entry token;
- compositional retrieval: combine launch date `2028-04-17` from one document
  and approved budget `USD 91,300.00` from another for `MERIDIAN-552`;
- policy abstraction: find a contract-retention period of `7 years`;
- semantic negative: reject a lunar-elevator question absent from the corpus.

The inherited cases cover exact identifiers, latest-version selection,
multi-hop graph evidence, multilingual text, prompt injection, tenant scope,
no-answer behavior, and all 32 labeled facts spread through an exact
10,240-byte document. Three cases have no valid in-scope answer. There are 42
expected facts across positive cases.

Every method used the same structure-aware chunks, the same K=8 limit, and a
fresh index made with `qwen3-embedding:4b`. `qwen3:8b` generated transformations,
corrective grades, and adaptive routes. Both exact model digests are retained in
the JSON report. The pair peaked at 12,843,231,476 bytes of Ollama-reported VRAM,
below the 17-GiB cap.

The live experiment was repeated three times with both models unloaded between
repeats. This deliberately exposes restart instability instead of benefiting
from one resident model state. The standard build, unit tests, source-span
checks, scope checks, cache checks, and before/after benchmark were separate
validation layers.

## The compared pipelines

Direct hybrid is the control: lexical and Qwen dense search run on the original
query, then their ranks are fused.

HyDE asks Qwen to write a hypothetical passage that might answer the query. The
original query remains the lexical query, while the hypothetical passage is
embedded for semantic search. HyDE is based on the idea described in the
[HyDE paper](https://arxiv.org/abs/2212.10496), but generated prose is never
accepted as evidence here.

RAG Fusion asks Qwen for three synonymous search queries. Each query is
searched separately and the rankings are merged with reciprocal-rank fusion,
following the broad approach evaluated in
[RAG-Fusion](https://arxiv.org/abs/2402.03367).

Decomposition asks for two to four independently searchable subquestions. For
example, Qwen split the MERIDIAN request into “When is the launch date for
MERIDIAN-552?” and “What budget was approved for MERIDIAN-552?” The original
query and subquery rankings are fused.

Step-back asks for one broader conceptual search question, then fuses it with
the original query. It is intended to find policy or terminology that a narrow
question does not state.

Corrective retrieval grades direct evidence as correct, ambiguous, or
incorrect. If evidence is incomplete or wrong, it retries local Fusion and
grades again, then keeps only source passages explicitly marked relevant. This
is a local subset of the workflow in
[Corrective RAG](https://arxiv.org/abs/2401.15884): there is intentionally no
web search or external knowledge source.

Adaptive retrieval asks Qwen to route each query to direct, HyDE, Fusion,
decomposition, or step-back. It cannot answer without retrieval. This tests the
routing principle from [Adaptive-RAG](https://arxiv.org/abs/2403.14403), but is
not a reproduction of its trained classifier.

## Safety and failure behavior

Transformation prompts contain only the user query, never corpus passages.
They label the query as untrusted, forbid following embedded instructions,
require exact JSON, preserve identifiers already in the query, and prohibit new
exact names, codes, dates, or amounts. Outputs have schema, count, length,
duplicate, placeholder, prompt-like-language, and exact-entity checks.

Invalid transformations fail closed to the original query. Two of 65 remained
invalid after bounded retries: one decomposition duplicated the exact same
query, and one HyDE response returned the literal placeholder `string`. No
retrieval request escaped the fixed tenant and collection.

HyDE can hallucinate even when told to use placeholders. For MERIDIAN-552 it
wrote that launch was in 2025 with a budget of about $12.5 million. The actual
source facts are 2028-04-17 and USD 91,300.00. Six final HyDE records contained
new numeric tokens and were flagged. They were allowed to affect only dense
ranking; the invented text was never displayed as source evidence and could
not satisfy fact or citation scoring.

All seven lanes scored 1.0 for scope integrity and canonical source-span
validity in every repeat. Rank fusion resolves generated searches back to exact
source passages. This is the most important safety result of the experiment.

## Aggregate results

| Method | Fact Recall@8 | Fact MRR | MRR | Rejects negatives | Estimated first-query p50 | Outcome |
|---|---:|---:|---:|---:|---:|---|
| Direct | 0.857 | 0.410 | 0.950 | 0.000 | 8.4 ms | Keep as default |
| HyDE | 0.786 | 0.403-0.415 | 0.950 | 0.000 | 1,213 ms | Worse recall |
| Fusion | 0.786 | 0.398 | 0.950 | 0.000 | 508-509 ms | Worse recall |
| Decomposition | 0.857 | 0.416 | 1.000 | 0.000 | 413-418 ms | Larger-test candidate |
| Step-back | 0.857 | 0.410 | 0.950 | 0.000 | 291 ms | Same quality, higher cost |
| Corrective | 0.738-0.810 | 0.380-0.387 | 0.900 | 1.000 | 537-1,097 ms | Unsafe regression |
| Adaptive | 0.857 | 0.410 | 0.950 | 0.000 | 370 ms | Same quality, higher cost |

Fact Recall@8 answers “what fraction of every labeled answer fact appeared in
the eight returned passages?” Fact MRR rewards putting each fact near the top.
MRR rewards putting the first relevant document near the top. Negative
rejection requires returning no evidence for questions that the corpus cannot
answer. The online estimate adds the generation time that a new, uncached user
query would pay; the much smaller retrieval-only time is also retained in the
full report.

Direct found all expected documents but 36/42 expected facts. Its missing facts
are mostly an exhaustive-coverage problem in the long document, not a semantic
matching problem. All targeted semantic positive cases already succeeded with
the Qwen embedding at K=8, leaving little room for generated expansion to help.

Decomposition was the only no-regression quality candidate. It preserved 36/42
facts, raised aggregate MRR from 0.95 to 1.0, and slightly raised fact MRR from
0.410 to 0.416. The gain was not uniform: it moved retention fact Q05 from rank
two to rank one, but moved graph fact G02 from rank two to rank four. It also
cost about 50 times direct retrieval on a first query. That is evidence for a
larger evaluation, not for enabling it globally.

HyDE and Fusion both fell to 33/42 facts. On the 10,240-byte case, direct found
26/32 facts while each found 23/32. Their extra text pulled different repetitive
chunks into K=8 and displaced useful ranges. This demonstrates why query
expansion should be evaluated by labeled fact coverage, not by whether the
generated text sounds plausible.

Step-back produced exactly the direct quality scores while adding a model call.
Several generated “broader” questions merely repeated the original request, so
there is no case for promotion.

Corrective retrieval was the only method to reject all three negative cases in
all three repeats. However, it also had the worst positive reliability. For the
MERIDIAN question, direct retrieval placed the budget and date passages at ranks
one and two, which is complete evidence. The grader returned `incorrect` with
no relevant labels, so the corrective lane discarded both. Grader verdict
accuracy was only 0.824, 0.778, and 0.778 across repeats; fact recall varied from
0.810 to 0.738. The grader therefore cannot be a production sufficiency gate.

Adaptive routing chose a utility-optimal lane for 12/13 cases, but its final
aggregate result exactly matched direct. It selected direct for the retention
case where decomposition ranked the fact better. Good route-choice accuracy is
not useful unless it improves end-to-end retrieval quality enough to repay the
model call.

## Stability and performance findings

The principal direct metrics and most rank-level method metrics were stable over
three fresh loads. However, both document and query embedding byte digests
changed every time the same Qwen model was reloaded with identical inputs and
batching. Corrective grading also changed enough to alter fact recall. These are
release blockers until the runtime cause is understood or a bounded quality
tolerance is established.

The ordinary deterministic 1,000-document benchmark showed no meaningful code
path win: ingestion changed from 0.719 to 0.733 seconds, p50 from 1.728 to 1.722
ms, p95 from 1.996 to 2.040 ms, and RSS from 31,968 to 32,244 KiB. These are
single local measurements, so no performance claim is made.

## Decision and next test

Do not add these methods to Thunderbird as defaults yet. Keep direct hybrid
retrieval, retain deterministic document-range coverage for “all/every”
requests, and keep generated text outside answer evidence.

The next justified experiment is decomposition on a substantially larger,
email-like corpus with paraphrases, long threads, attachments, revisions,
cross-message answers, and calibrated negative questions. It should compare a
route limited to genuinely multi-part queries against direct retrieval, measure
final grounded answer quality as well as retrieval, and repeat over fresh model
loads. In parallel, diagnose Qwen embedding digest drift and replace the
model-only corrective gate with deterministic exact-identifier/fact checks plus
a calibrated abstention model.

## Reproduction and evidence

Run the full live matrix with:

```sh
./scripts/run.sh query-rag-evaluate \
  --chat-model qwen3:8b \
  --embedding-model qwen3-embedding:4b \
  --top-k 8 \
  --repeats 3 \
  --name query-rag-qwen3-final \
  --cache-name query-rag-qwen3-v2
```

The complete human-readable report is `query-rag-qwen3-final.md`. The
4.5-MB JSON companion contains every prompt, raw model response, accepted
transformation, validation warning/failure, corrective grade, adaptive route,
embedding digest, ranking, canonical source span, metric, and resource record.
The generation cache is `query-rag-qwen3-v2-generation-cache.json` and is
atomically written.
