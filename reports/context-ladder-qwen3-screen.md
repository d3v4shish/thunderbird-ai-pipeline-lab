# Template, Whole-Email Context, and Thread-Memory Evaluation Ladder

- Fixture digest: `59ed2640097f2fb788f72649c8d103afebf0ba387d16ce9fd330b6e264d40af9`
- Synthetic documents: 17 (14 used for retrieval)
- Cases: 7
- Hard long-source/scale contracts: PASS
- Production ready: False

Generated context, summaries, template labels, ledgers, and graph records are untrusted retrieval metadata. Every answerable value remains in an unchanged, verified source span.

## Staged arms

| Arm | Status | Local fact recall | Complete fact recall | Span/scope | Advance |
|---|---|---:|---:|---:|---|
| control-raw-hybrid | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| context-metadata | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| context-per-chunk | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| context-whole-email | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| context-summary | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| template-drain | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| template-confirmed | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| memory-markdown | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| memory-graph | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| memory-ledger-graph | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| retrieval-exact | measured | 0.667 | 1.000 | 1.000/1.000 | source/scope/unsupported/localized-recall gate failed |
| retrieval-lexical | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| retrieval-dense | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| rerank-deterministic | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| query-transform-canonical | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| graphrag-relation | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| bounded-tools-range | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| hierarchy-complete-range | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| pair-metadata-drain | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| pair-whole-email-markdown | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| pair-summary-graph | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| pair-confirmed-ledger | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| full-context-template-memory-package | measured | 1.000 | 1.000 | 1.000/1.000 | PASS |
| cross-encoder-controlled-external | deferred-external-control | 0.000 | 0.000 | 0.000/0.000 | A true cross-encoder requires the separately configured loopback /rerank service; run cross-encoder-evaluate before combining it. |

## Long-email controls

| Source | Characters | Direct allowed | Pages | Fact recall | Complete |
|---|---:|---|---:|---:|---|
| LARGE-10K | 10240 | True | 1 | 1.000 | True |
| LARGE-256K | 262144 | False | 14 | 1.000 | True |
| LARGE-1M | 1048576 | False | 53 | 1.000 | True |

## Thread-scale controls

| Messages | Top-8 fact recall | Pages | Ledger fact recall | Ordered complete |
|---:|---:|---:|---:|---|
| 50 | 0.1600 | 2 | 1.000 | True |
| 500 | 0.0160 | 16 | 1.000 | True |
| 5000 | 0.0016 | 157 | 1.000 | True |

## Live qualification

Use `context-ladder-evaluate --dry-run` to retain the exact bounded screen plan. Use `--live --chat-model qwen3:8b --repeats 1` only with the configured loopback endpoint, then run three fresh repeats for qualified candidates. Raw output and validated records are kept in the live checkpoint, not merged into deterministic quality metrics.
