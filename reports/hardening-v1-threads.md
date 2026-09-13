# Synthetic Large-Thread Scale Evaluation

Frozen synthetic 50-500-message threads compare direct top-K, an unbounded control range, bounded paging, and deterministic hierarchical fact ledgers.

| Thread | Method | Fact recall | Peak stage chars | p50 ms | Pages |
|---:|---|---:|---:|---:|---:|
| 50 | direct-top-8 | 0.160 | 2417 | 1.629 | 1 |
| 50 | full-thread-range | 1.000 | 15141 | 0.542 | 1 |
| 50 | paged-thread-range | 1.000 | 9687 | 0.000 | 2 |
| 50 | hierarchical-ledger | 1.000 | 9687 | 0.261 | 2 |
| 100 | direct-top-8 | 0.080 | 2425 | 1.951 | 1 |
| 100 | full-thread-range | 1.000 | 30392 | 1.072 | 1 |
| 100 | paged-thread-range | 1.000 | 9728 | 0.001 | 4 |
| 100 | hierarchical-ledger | 1.000 | 9728 | 0.512 | 4 |
| 250 | direct-top-8 | 0.032 | 2429 | 3.684 | 1 |
| 250 | full-thread-range | 1.000 | 76142 | 2.535 | 1 |
| 250 | paged-thread-range | 1.000 | 9760 | 0.001 | 8 |
| 250 | hierarchical-ledger | 1.000 | 9760 | 1.261 | 8 |
| 500 | direct-top-8 | 0.016 | 2428 | 5.928 | 1 |
| 500 | full-thread-range | 1.000 | 152392 | 4.972 | 1 |
| 500 | paged-thread-range | 1.000 | 9760 | 0.002 | 16 |
| 500 | hierarchical-ledger | 1.000 | 13484 | 2.527 | 16 |

## Decision

Use ordered paging plus hierarchical reduction for exhaustive threads; never place a 50-500-message full range in one model prompt.
