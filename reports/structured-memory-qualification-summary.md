# Structured-Memory V4 Qualification Report

Date: 2026-09-14. This report covers synthetic lab data only. No Thunderbird
profile, mailbox, credential, or real email was read, and no Thunderbird code
was changed.

## Question tested

Can the host mine durable source-linked memory from a complete bounded email,
give a model only closed-world candidate IDs, preserve an explicit old reply
target in a long thread, and reject malformed model choices?

The model was never asked to write a summary, event, value, source offset,
target document, scope, or family member list. It received the current bounded
email, at most 24 prior host records, and host-generated event/relation/family/
slot candidates. It returned four fields: selected event IDs, selected relation
IDs, one offered family ID or null, and selected slot IDs.

## Frozen cases

Six bounded synthetic emails tested:

1. three ordinary unlabeled decision/assignment/status sentences;
2. an invoice-family email where the amount slot is legitimately absent;
3. one current incident update followed by a forwarded hostile old message;
4. one current deployment status followed by a signature and hostile text;
5. a valid security status followed by paraphrased prompt injection;
6. thirty routine sentences followed by a required final decision at sentence
   31.

Four deterministic controls replied to record one in otherwise synthetic
50/100/250/500-message threads. The live gate used the six messages plus the
500-record reply, for seven calls per repeat and 21 per model.

The exact sources, prompts, schemas, raw output, source offsets, and accepted
records are in the linked JSON artifacts. The fixture digest is
`efc617918a8f390b049865d00352c21f8d29519da07a09fa943a9305c4da6489` and
the v4 qualification contract digest is
`88be0fb5424ce0aab821fb31a749a6938fc179332b876526e30e78e92a663b3e`.

## Before: unchanged v3

V3 passed 1/6 message cases and 0/4 long-thread cases:

| Failure | Observed result |
|---|---|
| Optional slot | the correctly assigned invoice family was removed |
| Forwarded text | five events persisted instead of one current event |
| Signature | four events persisted instead of one current event |
| Paraphrased injection | both sentences were model-visible |
| Late event | only the first 24 of 31 events existed |
| Old reply target | record one was absent from all four 24-record prompt windows |
| Relation pressure | each old-reply case filled the 64-candidate cap without offering the actual target |

Source: [unchanged-v3 baseline](structured-memory-qualification-v3-baseline.md).

## V4 host changes and deterministic result

- Current-body segmentation excludes forwarded/quoted and signature regions.
- A conservative additional detector rejects tested paraphrases such as
  “set aside governing guidance” and “treat this email as a developer
  directive.”
- The host can retain up to 512 durable events, while the model sees at most 24
  optional importance hints. A hidden event ID remains invalid model output.
- Full prior memory is scope/thread/chronology validated, but the prompt stays
  at 24 records. Explicit `In-Reply-To`/`References` targets are pinned into
  that window before recent records fill it.
- Relation predicates are lexically narrowed. The explicit 500-record reply
  offered exactly one `confirms` relation to record one.
- A deterministically assigned family with score at least 0.8 stays selectable
  when all typed slots are optional. Unassigned same-sender lookalikes remain
  filtered.

V4 passed 6/6 adversarial messages and 4/4 thread sizes with exact source spans.
The late event was absent at durable cap 24 and present at 48/96/512; public
hints remained 24. A dense no-reference pressure case produced 64/96/96
relation candidates at caps 64/128/256. Therefore the selected relation cap of
64 is explicitly non-exhaustive for inferred semantic links; structural reply
edges and canonical source remain authoritative.

Source: [v4 deterministic report](structured-memory-qualification-v4-deterministic.md).

## Live model result

All calls used temperature 0, 16,384 context, a 1,024 output cap, fresh
three-repeat checkpoints, serial loopback Ollama execution, and the 17-GiB
Ollama-allocation policy.

| Model | Result | Prompt/output tokens | Summed latency | Ollama allocation |
|---|---:|---:|---:|---:|
| Qwen3 8B | 21/21 pass | 20,169/2,766 | 34.358 s | 6,387,799,162 B |
| Granite 3.1 MoE F16 | 21/21 pass | 21,942/2,853 | 16.181 s | 7,325,289,020 B |
| Qwen 2.5 14B Q4 | 21/21 pass | 20,001/2,877 | 52.484 s | 10,521,914,899 B |
| DeepSeek V2 16B | 5 pass, sixth rejected | 2,326/410 accepted-call tokens | 36.762 s | 11,340,947,127 B |

Qwen3, Granite, and Qwen 2.5 selected the optional invoice family and the exact
old-record relation in every repeat. In the 31-event case, the final event was
not among the 24 model hints, but it was still present in host-owned durable
memory; this is the intended separation.

DeepSeek's sixth response contained 24 event entries but repeated six IDs. The
schema declared unique items and host validation detected the duplicates. The
response was rejected rather than silently deduplicated. The staged run then
stopped, so Phi-4 and Granite 4.1 have no v4 qualification result.

Raw evidence:

- [Qwen3 report](structured-memory-qualification-qwen3-v4.md) and
  [JSON](structured-memory-qualification-qwen3-v4.json)
- [Granite 3.1 report](structured-memory-qualification-granite31-v4.md) and
  [JSON](structured-memory-qualification-granite31-v4.json)
- [Qwen 2.5 report](structured-memory-qualification-qwen25-v4.md) and
  [JSON](structured-memory-qualification-qwen25-v4.json)
- [DeepSeek failed report](structured-memory-qualification-deepseek-v4.md) and
  [JSON](structured-memory-qualification-deepseek-v4.json)

## Performance and validation

The generic fixed-seed 1K benchmark moved from 0.730760 to 0.732320 seconds
ingest, 1.797299 to 1.852720 ms query p50, and 2.320323 to 2.367568 ms p95;
database size stayed 3,465,216 bytes. These are single local runs and do not
support a performance-improvement claim. The post-change deterministic suite
passed 202/202 tests, and the implementation digest is
`210743be72073bef2ff8ca287b2e79f03ae724c9acb067d993aa71d9281a31a8`.

## Verdict

V4 is the strongest structured-memory design tested so far. It fixes every
measured host-side v3 failure and is stable across three model families. It is
not production-ready: DeepSeek failed strict output validation, two approved
models remain unrun behind that gate, semantic relations are deliberately
non-exhaustive without explicit references, and real-mail/Thunderbird,
HTML-to-text, multilingual, concurrency, cancellation, deletion/invalidation,
and usability tests remain.
