# Oversized Email Architecture Design Matrix

## Deterministic overview

Fixture: 262144 bytes, 64 facts.

| Input design | Model-input chars | Fact recall | Complete? |
|---|---:|---:|---|
| prefix | 24576 | 0.094 | False |
| suffix | 24576 | 0.094 | False |
| head-tail | 24577 | 0.094 | False |
| middle | 24576 | 0.094 | False |
| uniform-eight-windows | 24583 | 0.125 | False |
| known-schema-source-compaction | 3391 | 1.000 | True |

| Chunk design | Coverage | Facts | Chunks | Passage chars |
|---|---:|---:|---:|---:|
| fixed-capped-current | 0.076 | 5 | 13 | 22159 |
| fixed-uncapped | 1.000 | 64 | 163 | 291296 |
| structure-aware | 1.000 | 64 | 163 | 291104 |
| sentence-window | 1.000 | 63 | 2485 | 4463067 |

## Objective result

- Best tested retrieval-only exhaustive recall: 1.000 (lexical, K=128).
- Validated host ledger recall: 1.000.
- Bounded tool-agent maximum deterministic source coverage: 0.092.

## Live Qwen3 8B result

| Design | Repeats | Recall/result | Wall time |
|---|---:|---:|---:|
| Direct giant prompt | 3 | {'8192': [0.0, 0.0, 0.0], '40960': [0.0, 0.0, 0.0]} | recorded per call |
| 20K bounded map + host ledger | 3 | [1.0, 1.0, 1.0] | 32463 ms mean |
| Known-schema compaction | 3 | [1.0, 1.0, 1.0] | recorded per call |
| Targeted hybrid RAG | 3 x 3 probes | 1.000 pass rate | recorded per call |
| 8K-character page map | 1 diagnostic | 1.000 | 30333 ms |
| 30K-character page map | 1 diagnostic | 1.000 | 29344 ms |
| Rolling model state | 1 diagnostic | 0.469 | 80402 ms |
| Model hierarchical reduce | 1 diagnostic | 1.000 | 30254 ms |
| Bounded tool agent | 1 diagnostic | 0.000 | 6 tool calls |

One-repeat diagnostics measure failure mode and cost, not stability.

## Decision

- Localized question: structure-aware full ingestion plus hybrid top-K and validation.
- Exhaustive known schema: bounded structure-aware page map, exact source validation, deterministic ledger merge, and paged/streamed delivery.
- Open-ended summary: hierarchical cited summaries with an explicit non-exhaustive label.

Every prompt and raw live output is retained in the JSON companion.
