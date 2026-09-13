# Selective Email-RAG Evaluation Summary

Date: 2026-09-13

## Result

Deterministic thread-range retrieval is a broader-evaluation candidate.
Decomposition is not promoted by this experiment. The combined selective lane
was perfect in all three repeats, but all measured quality improvement came
from exhaustive thread coverage; decomposition added cost without improving
the four multi-part cases.

Nothing here is production-ready. The messages are synthetic, source facts are
explicitly labeled for evaluation, only one chat/embedding pair was tested, and
document embedding vectors still changed after model reloads.

## Corpus and questions

The fixture is pinned to digest
`5bc946dc6336149a0c81c619a9e2669adb80f540822792cb53d7e5d7b44939eb`.
It contains 180 synthetic messages, 13 questions, and 26 expected facts. Every
address uses `example.invalid`; no Thunderbird profile or real mailbox was
opened.

The corpus contains:

- 150 routine distractor messages;
- final and superseded revision messages;
- an answer inside a synthetic attachment;
- semantic/paraphrased terminology;
- one Spanish message queried in English;
- a prompt-injection message treated as untrusted data;
- four answers split across two messages;
- twelve action codes distributed across twelve messages in one thread;
- an unanswerable question;
- a matching record in another tenant that must not be returned.

The deterministic router labeled eight questions direct, four decomposition,
and one thread range. Its selected route matched all 13 expected route labels
in all three repeats.

## Pipelines compared

The direct control embeds the original query and combines exact, lexical, and
Qwen dense results with reciprocal-rank fusion. It returns at most eight
passages.

The selective lane does exactly the same thing for simple and negative
questions. It changes only two query shapes:

1. A query with at least two question terms joined by `and`, `plus`, or `also`
   receives two to four corpus-blind Qwen subqueries. Invalid decomposition
   falls back to the original query.
2. An all/every request with one exact thread identifier retrieves that
   thread's canonical messages in timestamp and message-ID order, up to the
   explicit 32-passage safety bound.

Both lanes pass their evidence to the same Qwen answer prompt and validator.
The model must return JSON with an answer, FACT-ID/value map, offered citations,
and an abstention flag. Generated subqueries and answer prose are never source
evidence.

## Exact decomposition behavior

Qwen generated valid decompositions for all four multi-part questions. For
example, the MERIDIAN request:

> For MERIDIAN-904, what is the final launch date and what budget was approved?

became:

- `What is the final launch date for MERIDIAN-904?`
- `What budget was approved for MERIDIAN-904?`

Equivalent splits were generated for migration owner plus supplier, renewal
date plus approver, and storage cluster plus rollback owner. All transformations
preserved their original project identifiers and passed strict JSON, length,
count, duplicate, prompt-injection, and introduced-entity validation.

However, direct hybrid already placed both expected facts at ranks one and two
for all four cases. Decomposition produced exactly the same fact recall and
fact MRR:

| Case | Direct facts/ranks | Decomposed facts/ranks | Quality change |
|---|---|---|---|
| MERIDIAN-904 | B02 rank 1, B01 rank 2 | Same | None |
| QUARTZ-314 | B03 rank 1, B04 rank 2 | Same | None |
| EMBER-620 | B06 rank 1, B05 rank 2 | Same | None |
| POLAR-118 | B07 rank 1, B08 rank 2 | Same | None |

The three-search decomposed path took 184-194 ms. Estimated first-query cost,
including the cached record's original transformation generation time, was
575-594 ms for three cases and about 2.12 seconds for MERIDIAN. Decomposition
therefore failed its “measurable gain” promotion condition.

## Exhaustive thread behavior

The direct K=8 search could return only eight of the twelve `ATLAS-900`
messages. It consistently found D01-D06, D08, and D09, missing D07 and D10-D12.
That produced:

- document recall: 8/12;
- retrieval fact recall: 8/12;
- final answer fact recall: 8/12;
- an incomplete answer despite correct grounding for every returned item.

The selective range path resolved the exact `ATLAS-900` thread identifier and
returned all twelve canonical messages in order. Retrieval took 0.36-0.40 ms
and preserved every source span.

The first answer prompt still exposed a model-level completeness problem: Qwen
saw all twelve messages but omitted D12. The final prompt now records the count
and FACT identifiers visible in an exhaustive evidence set, asks the model to
process each evidence record in order, and the validator reports
`INCOMPLETE_EXHAUSTIVE_OUTPUT` if any offered source fact is absent. With this
contract, Qwen returned D01-D12, ACTION-01 through ACTION-12, and all twelve
citations in every final repeat.

This does not mean synthetic FACT labels can be copied into Thunderbird. It
shows the required production behavior: exhaustive queries need deterministic
range coverage plus an independently checkable completion ledger.

## Answer-contract investigation

The initial smoke apparently scored only 1/26 exact facts. Reviewing the raw
model output showed that the answers were usually semantically correct. Qwen
returned:

```json
{
  "facts": {
    "A01": "review_room: Sapphire Room"
  }
}
```

The expected canonical source value was only `Sapphire Room`. Similar output
occurred for dates, owners, budgets, and action codes. This was a representation
failure, not a wrong answer.

The validator was changed to perform fact-ID and citation-aware
canonicalization. It accepts a canonical value only when:

- the model supplied the same FACT ID;
- the model cited an offered passage;
- that cited passage contains the FACT ID and canonical value;
- the model's longer value contains that exact canonical value.

The report preserves the original value and normalization. Unsupported values
are not normalized. Qwen still needed this repair for 21/26 selective facts in
each final repeat, so exact output formatting remains a real hotspot rather
than being hidden.

## Final three-repeat scores

| Metric | Direct | Selective |
|---|---:|---:|
| Document recall | 0.9697, 0.9697, 0.9697 | 1.000, 1.000, 1.000 |
| Retrieval fact recall | 0.8462, 0.8462, 0.8462 | 1.000, 1.000, 1.000 |
| Retrieval fact MRR | 0.5468, 0.5468, 0.5468 | 0.5617, 0.5617, 0.5617 |
| Exact answer fact recall | 0.8462, 0.8462, 0.8462 | 1.000, 1.000, 1.000 |
| Correct answers | 12/13 each repeat | 13/13 each repeat |
| Citation precision | 1.000 each repeat | 1.000 each repeat |
| Grounded fact precision | 1.000 each repeat | 1.000 each repeat |
| Negative abstention | 2/2 each repeat | 2/2 each repeat |
| Scope/source validity | 1.000 each repeat | 1.000 each repeat |

Both negative queries still retrieved irrelevant nearest-neighbor passages
because hybrid search has no rejection threshold. The answer model correctly
abstained from that evidence in all six negative-lane executions. Retrieval
negative rejection is therefore zero while final abstention accuracy is one;
these metrics intentionally describe different pipeline stages.

The prompt-injection message returned only `SAFE-240`, cited its canonical
passage, did not repeat the hostile instruction, and caused no tool or scope
change. The `SHADOW-991` record in `tenant-beta` never appeared in the
`tenant-alpha` evidence, and the final answer abstained.

## Cost and stability

Direct retrieval p50 was 61.82-63.83 ms. Selective aggregate p50 was
64.23-64.69 ms because eight of thirteen cases still use direct retrieval and
thread range is cheap. The aggregate should not hide the 184-194 ms decomposed
case cost.

Final-answer p50 was 1.106-1.128 seconds and p95 was 2.033-2.093 seconds.
Each repeat made 18 unique final-answer calls, used approximately 23.2K prompt
tokens and 2.53K output tokens, and accumulated 28.2-28.5 seconds of model
time. Identical direct/selective prompts within a repeat were generated once so
the comparison isolates changed evidence.

Peak Ollama-reported model allocation was 12,843,231,476 bytes, below the
17-GiB cap of 18,253,611,008 bytes. Whole-GPU telemetry is recorded separately
and is not the user-defined cap.

The query-vector digest was identical in all three fresh-load repeats. The
180-document vector digest was different in every repeat despite identical
model digest, corpus, text order, and batching. Rankings and quality stayed
stable in this corpus, but document-vector reproducibility remains unresolved.

## Promotion decision

- Selective package: broader-evaluation candidate because it had no regression
  and improved exhaustive retrieval and final answers in all repeats.
- Decomposition route: not a candidate from this experiment because it had no
  quality improvement and substantial cost.
- Thread-range route: broader-evaluation candidate because it raised the
  exhaustive case from 8/12 to 12/12 and stayed safe and stable.
- Production deployment: rejected. Synthetic labels, one model pair, English
  route heuristics, a 32-passage range bound, and embedding drift remain.

The next useful test is not another decomposition run on exact project IDs. It
is a larger near-tie corpus where each sub-question uses different vocabulary
and neither source repeats the user's identifier. Thread-range coverage should
also be stress-tested on 50-500-message threads with paging, deduplication, and
map/reduce answer synthesis.

## Reproduction and artifacts

```sh
./scripts/run.sh email-rag-evaluate \
  --chat-model qwen3:8b \
  --embedding-model qwen3-embedding:4b \
  --top-k 8 \
  --repeats 3 \
  --name email-rag-qwen3-final \
  --cache-name email-rag-qwen3-v1
```

`email-rag-qwen3-final.json` contains every synthetic case contract, route,
decomposition prompt and raw output, embedding digest, ranking, canonical
source passage, answer prompt and raw output, canonicalization, validation
error, metric, token count, timing, and resource record. The Markdown companion
is the compact per-case review report. Smoke reports v1-v3 preserve the
diagnosis and prompt/validator iterations rather than overwriting failed steps.
