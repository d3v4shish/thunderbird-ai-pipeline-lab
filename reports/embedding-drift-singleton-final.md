# Endpoint Embedding Drift Investigation

Model: `qwen3-embedding:4b` / `df5bd2e3c74cd8d069d21dc038f1b359fcdc9458fce1c99bd43c9eb1518ff907`.

| Repeat | Document digest | Query digest | First/second exact | Second/third exact | Batch/order exact | Fact recall@8 |
|---:|---|---|---|---|---|---:|
| 1 | `3a27c59ed996c46eef520d29e321a36b70f0905eeb518fc7bd69991929f30cdc` | `5063fca664de827f3173f31354d63ba987c68c3bd10de832687f4b80787ccbfc` | False | True | False | 0.846 |
| 2 | `3a27c59ed996c46eef520d29e321a36b70f0905eeb518fc7bd69991929f30cdc` | `5063fca664de827f3173f31354d63ba987c68c3bd10de832687f4b80787ccbfc` | False | True | False | 0.846 |
| 3 | `3a27c59ed996c46eef520d29e321a36b70f0905eeb518fc7bd69991929f30cdc` | `5063fca664de827f3173f31354d63ba987c68c3bd10de832687f4b80787ccbfc` | False | True | False | 0.846 |

Cross-load exact: True.
Steady-state exact: True.
Batch/order effect isolatable: False.
Rank/quality tolerance pass (95% top-8 overlap, 1% quality): True.

Persist document embeddings and permit this endpoint only if steady-state calls are exact and cross-load ranking remains at least 95% overlapping with no more than 1% aggregate quality drift; byte-level nondeterminism remains separately visible.
