# Synthetic Large-Thread Scale Evaluation

Frozen synthetic 50-5000-message threads compare direct top-K, an unbounded control range, bounded paging, and deterministic hierarchical fact ledgers.

| Thread | Method | Fact recall | Peak stage chars | p50 ms | Pages |
|---:|---|---:|---:|---:|---:|
| 50 | direct-top-8 | 0.160 | 2417 | 1.574 | 1 |
| 50 | full-thread-range | 1.000 | 15141 | 0.500 | 1 |
| 50 | paged-thread-range | 1.000 | 9687 | 0.494 | 2 |
| 50 | hierarchical-ledger | 1.000 | 9687 | 2.720 | 2 |
| 100 | direct-top-8 | 0.080 | 2425 | 1.965 | 1 |
| 100 | full-thread-range | 1.000 | 30392 | 1.057 | 1 |
| 100 | paged-thread-range | 1.000 | 9728 | 1.060 | 4 |
| 100 | hierarchical-ledger | 1.000 | 9728 | 5.603 | 4 |
| 250 | direct-top-8 | 0.032 | 2429 | 3.591 | 1 |
| 250 | full-thread-range | 1.000 | 76142 | 2.551 | 1 |
| 250 | paged-thread-range | 1.000 | 9760 | 2.542 | 8 |
| 250 | hierarchical-ledger | 1.000 | 9760 | 13.674 | 8 |
| 500 | direct-top-8 | 0.016 | 2428 | 5.922 | 1 |
| 500 | full-thread-range | 1.000 | 152392 | 5.025 | 1 |
| 500 | paged-thread-range | 1.000 | 9760 | 5.062 | 16 |
| 500 | hierarchical-ledger | 1.000 | 13484 | 28.333 | 16 |
| 1000 | direct-top-8 | 0.008 | 2435 | 11.415 | 1 |
| 1000 | full-thread-range | 1.000 | 305896 | 10.784 | 1 |
| 1000 | paged-thread-range | 1.000 | 9792 | 10.255 | 32 |
| 1000 | hierarchical-ledger | 1.000 | 13808 | 54.554 | 32 |
| 2500 | direct-top-8 | 0.003 | 2433 | 30.628 | 1 |
| 2500 | full-thread-range | 1.000 | 770896 | 25.994 | 1 |
| 2500 | paged-thread-range | 1.000 | 9920 | 25.744 | 79 |
| 2500 | hierarchical-ledger | 1.000 | 14832 | 142.066 | 79 |
| 5000 | direct-top-8 | 0.002 | 2432 | 61.275 | 1 |
| 5000 | full-thread-range | 1.000 | 1545896 | 50.249 | 1 |
| 5000 | paged-thread-range | 1.000 | 9920 | 50.262 | 157 |
| 5000 | hierarchical-ledger | 1.000 | 14832 | 285.504 | 157 |

## Reduction batch sweep on the largest thread

| Batch size | Fact recall | Peak stage chars | Ledger chars | p50 ms |
|---:|---:|---:|---:|---:|
| 4 | 1.000 | 9920 | 143001 | 4.238 |
| 8 | 1.000 | 9920 | 143001 | 4.135 |
| 16 | 1.000 | 14832 | 143001 | 4.130 |
| 32 | 1.000 | 29664 | 143001 | 4.135 |
| 64 | 1.000 | 59328 | 143001 | 4.134 |

## Decision

Use ordered paging plus hierarchical reduction for exhaustive threads; never place a 50-500-message full range in one model prompt.
