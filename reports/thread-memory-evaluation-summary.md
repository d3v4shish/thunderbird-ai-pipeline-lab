# Source-linked email and thread-memory evaluation

Snapshot: 2026-09-13. All inputs were frozen synthetic messages. No Thunderbird
profile, mailbox, credential store, or real email was accessed.

## Verdict

The implementation and deterministic mechanics pass. Hierarchical
thread-to-email-to-passage retrieval is the measured candidate for localized
questions because it preserved quality with substantially less indexed and
answer context than repeating thread memory on every passage. Explicit
all/every requests must use canonical source paging; fixed Top-K cannot prove
completeness.

This is not a production or Thunderbird-promotion result. Qwen3 and Phi-4 each
have only one completed live smoke repeat, and model-generated semantic
relations scored 0.500 precision, recall, and F1. The complete three-repeat
live matrix and live validation of selected Pareto finalists remain open.

## Final implementation verification

- Build: passed.
- Snapshot deterministic suite: 136/136 tests passed in 3.248 seconds. The
  current repository suite, including later template/scale coverage, passes
  156/156; that does not retroactively complete this live-memory matrix.
- Focused thread-memory suite: 19/19 tests passed.
- Implementation digest:
  `0d23814ba46039a26e3f7d01653622978366ad5de66b94c038e55c80328253d7`.
- Complete dry-run plan: 1,152 retrieval/answer cells backed by 144 reusable
  model-generation streams.

## What the pipeline did

Each message was processed chronologically. The model received the complete
current bounded email, deterministic headers, and only bounded memory from
earlier messages in the same tenant, collection, and thread. It generated a
short retrieval context, source-linked evidence summary, narrative summary,
events, and optional allowlisted relations. Current-email summaries could cite
only the current source. Generated artifacts remained untrusted retrieval
metadata; answers could cite only unchanged canonical email spans.

The four-message live fixture first proposed `M01 = Silver Room`, asked whether
that proposal was final, then established `M02 = Sapphire Room` as the final
room. The answer contract required the final value and rejected an obsolete
M01 fact even if M02 was also present.

## Deterministic 180-message parameter sweep

The final model-free hardening run executed 18 one-factor cells in 14.196
seconds with no hard-gate failure.

| Configuration | Placement | Fact Recall@8 | MRR | Indexed characters | Retrieval |
|---|---|---:|---:|---:|---:|
| Baseline | repeated | 0.9744 | 0.8077 | 631,854 | 295.249 ms |
| Baseline | hierarchical | 0.9744 | 0.8077 | 287,925 | 124.951 ms |
| Memory 2,000 | hierarchical | 0.9744 | 0.8077 | 280,766 | 108.095 ms |
| Memory 6,000 | hierarchical | 0.9744 | 0.8077 | 284,782 | 110.360 ms |
| Email parent K=4 | hierarchical | 0.9487 | 0.8077 | 287,925 | 111.711 ms |
| Email parent K=16 | hierarchical | 0.9744 | 0.8077 | 287,925 | 112.040 ms |

Changing summary limits from 80 to 200 words or thread-parent fan-out from two
to eight did not change quality on this fixture. Email-parent K=4 lost one
aggregate fact; K=8 remains the safer default. Compared with repeated context,
the hierarchical baseline used 54.4% fewer indexed characters and 57.7% less
single-run retrieval time at the same measured quality. Timing is diagnostic,
not a production speed claim.

## Thread scale and storage

| Messages | Localized Top-K recall | Exhaustive source recall | 32-message pages | SQLite bytes |
|---:|---:|---:|---:|---:|
| 50 | 0.160 | 1.000 | 2 | 176,128 |
| 100 | 0.080 | 1.000 | 4 | 274,432 |
| 250 | 0.032 | 1.000 | 8 | 536,576 |
| 500 | 0.016 | 1.000 | 16 | 995,328 |

Top-K returned exactly eight facts, so its exhaustive recall necessarily fell
as the thread grew. Canonical paging retained every expected fact, scope, and
source span at every size. Storage remained below one MiB at 500 messages in
this synthetic fixture.

## Large-email mechanics

| Source | Route | Pages | Fact recall | Source-span validity |
|---|---|---:|---:|---:|
| 10,240 bytes | direct complete email | 1 | 1.000 | 1.000 |
| 256 KiB, 12K pages | complete source paging | 23 | 1.000 | 1.000 |
| 256 KiB, 20K pages | complete source paging | 14 | 1.000 | 1.000 |
| 256 KiB, 30K pages | complete source paging | 9 | 1.000 | 1.000 |

These measurements prove deterministic traversal, bounds, and provenance. They
are not repeated live-model quality measurements for the large sources.

## One-repeat live smoke results

| Model and placement | Retrieval recall | MRR | Answer fact recall | Answer correctness | Answer context | Answer latency |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3 8B repeated | 1.000 | 0.500 | 1.000 | 1.000 | 42,874 chars | 2.726 s |
| Qwen3 8B hierarchical | 1.000 | 1.000 | 1.000 | 1.000 | 12,009 chars | 0.848 s |
| Phi-4 14B Q8 repeated | 1.000 | 1.000 | 1.000 | 0.000 | 42,032 chars | 13.544 s |
| Phi-4 14B Q8 hierarchical | 1.000 | 1.000 | 1.000 | 1.000 | 11,987 chars | 2.079 s |

Both models extracted 4/4 messages and achieved 1.000 evidence-summary and
narrative-summary fact recall. Each stream rejected one invalid or
prior-derived field while retaining its valid fields. Both relation streams
scored 0.500 precision, recall, and F1.

Hierarchical placement reduced answer context by about 72%. Qwen's answer was
about 69% faster and Phi's about 85% faster in these single runs. Qwen returned
the correct M02 value but omitted its exact supporting citation; deterministic
repair attached an already offered source passage containing the same fact ID
and value. Phi's repeated lane included obsolete M01 and therefore failed exact
answer correctness. Its hierarchical lane returned only the requested current
fact and passed.

Qwen's smoke took 28.679 seconds, made 43 endpoint requests, and peaked at
6,455,432,314 Ollama VRAM bytes. Phi's original four-message extraction took
61.488 seconds and peaked at 16,972,072,876 Ollama VRAM bytes, below the 17-GiB
model-allocation cap. Confirmed unload polling fixed an initial partial-residency
failure when switching back from the embedding model. Whole-GPU peaks were
8,478,785,536 and 19,735,248,896 bytes respectively; whole-GPU telemetry is not
the model-allocation policy value.

## Decision

Advance this combination to the remaining live evaluation:

- whole-email extraction only when the effective prompt budget can contain the
  source plus instructions, prior memory, and output reserve;
- hierarchical thread-to-email-to-passage retrieval for localized questions;
- email-parent fan-out of at least eight for the tested shape;
- deterministic reply/reference edges as authoritative;
- model semantic relations as untrusted metadata until quality improves;
- canonical source paging for explicit exhaustive mode;
- original source spans as the only answer evidence.

Do not promote a model/configuration yet. Promotion requires three completed
live repeats, every hard and quality gate, no baseline regression, and live
validation of the non-dominated finalists.

## Reproduction and retained transient evidence

```sh
./scripts/build.sh
./scripts/test.sh
./scripts/run.sh thread-memory-evaluate --dry-run --repeats 3
./scripts/run.sh thread-memory-hardening-evaluate \
  --name thread-memory-hardening
```

The exact final deterministic report was written to
`/tmp/tb-ai-thread-memory-hardening-final2/deterministic-final.{json,md}`.
One-repeat live reports are
`/tmp/tb-ai-thread-memory-live-v8/qwen3-memory-smoke-v8.{json,md}` and
`/tmp/tb-ai-thread-memory-live-v9/phi4-memory-smoke-v9.{json,md}`. Temporary
paths are recorded for audit but are not represented as durable repository
artifacts.
