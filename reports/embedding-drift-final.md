# Endpoint Embedding Drift Investigation

Model: `qwen3-embedding:4b` / `df5bd2e3c74cd8d069d21dc038f1b359fcdc9458fce1c99bd43c9eb1518ff907`.

| Repeat | Document digest | Query digest | First/second exact | Second/third exact | Batch/order exact | Fact recall@8 |
|---:|---|---|---|---|---|---:|
| 1 | `2812292678c697b8123e0a470b439fc3b750ac29ea2d3652ead62af41e2c8dac` | `5063fca664de827f3173f31354d63ba987c68c3bd10de832687f4b80787ccbfc` | False | False | False | 0.846 |
| 2 | `f2405d4c28fcd11d430ce2c1e30e33b4062e167757cb68a405579fa4481d8f68` | `5063fca664de827f3173f31354d63ba987c68c3bd10de832687f4b80787ccbfc` | False | False | False | 0.846 |
| 3 | `57356d635519c17919a821c6053b239b75eda1bf863ea9ba766b084f1a1252d0` | `5063fca664de827f3173f31354d63ba987c68c3bd10de832687f4b80787ccbfc` | False | False | False | 0.846 |

Cross-load exact: False.
Steady-state exact: False.
Batch/order effect isolatable: False.
Rank/quality tolerance pass (95% top-8 overlap, 1% quality): True.

Persist document embeddings and permit this endpoint only if steady-state calls are exact and cross-load ranking remains at least 95% overlapping with no more than 1% aggregate quality drift; byte-level nondeterminism remains separately visible.
