# Synthetic Large-Thread Scale Evaluation

Frozen synthetic 50-500-message threads compare direct top-K, an unbounded control range, bounded paging, and deterministic hierarchical fact ledgers.

| Thread | Method | Fact recall | Peak stage chars | p50 ms | Pages |
|---:|---|---:|---:|---:|---:|
| 50 | direct-top-8 | 0.160 | 2417 | 1.608 | 1 |
| 50 | full-thread-range | 1.000 | 15141 | 0.519 | 1 |
| 50 | paged-thread-range | 1.000 | 9687 | 0.506 | 2 |
| 50 | hierarchical-ledger | 1.000 | 9687 | 3.012 | 2 |
| 100 | direct-top-8 | 0.080 | 2425 | 2.065 | 1 |
| 100 | full-thread-range | 1.000 | 30392 | 1.036 | 1 |
| 100 | paged-thread-range | 1.000 | 9728 | 1.091 | 4 |
| 100 | hierarchical-ledger | 1.000 | 9728 | 5.882 | 4 |
| 250 | direct-top-8 | 0.032 | 2429 | 3.655 | 1 |
| 250 | full-thread-range | 1.000 | 76142 | 2.594 | 1 |
| 250 | paged-thread-range | 1.000 | 9760 | 2.569 | 8 |
| 250 | hierarchical-ledger | 1.000 | 9760 | 15.488 | 8 |
| 500 | direct-top-8 | 0.016 | 2428 | 6.105 | 1 |
| 500 | full-thread-range | 1.000 | 152392 | 5.202 | 1 |
| 500 | paged-thread-range | 1.000 | 9760 | 5.072 | 16 |
| 500 | hierarchical-ledger | 1.000 | 13484 | 30.752 | 16 |

## Reduction batch sweep on the largest thread

| Batch size | Fact recall | Peak stage chars | Ledger chars | p50 ms |
|---:|---:|---:|---:|---:|
| 4 | 1.000 | 9760 | 13499 | 0.423 |
| 8 | 1.000 | 9760 | 13499 | 0.422 |
| 16 | 1.000 | 13484 | 13499 | 0.414 |
| 32 | 1.000 | 13484 | 13499 | 0.415 |
| 64 | 1.000 | 13484 | 13499 | 0.415 |

## Decision

Use ordered paging plus hierarchical reduction for exhaustive threads; never place a 50-500-message full range in one model prompt.
