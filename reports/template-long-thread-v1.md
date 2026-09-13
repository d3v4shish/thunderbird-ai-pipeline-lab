# Template-Aware Long-Thread Scale Evaluation

| Messages | Family F1 | Assignments | Fact recall | Top-8 recall | Latest | Reduction | Mining ms | Ingest ms | DB bytes | Peak bytes |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 500 | 1.000 | 1.000 | 1.000 | 0.0160 | 1.000 | 66.6% | 65.6 | 1304.5 | 2527232 | 38789 |
| 1000 | 1.000 | 1.000 | 1.000 | 0.0080 | 1.000 | 66.5% | 118.1 | 2568.1 | 4874240 | 39002 |
| 2500 | 1.000 | 1.000 | 1.000 | 0.0032 | 1.000 | 66.4% | 315.9 | 6513.2 | 11886592 | 46094 |
| 5000 | 1.000 | 1.000 | 1.000 | 0.0016 | 1.000 | 66.4% | 620.1 | 12782.3 | 23678976 | 39271 |

Hard gate: PASS.

## Decision

Use sender-scoped template families as bounded retrieval metadata, retain source-validated slots and facts in deterministic ledgers, and cap family graph expansion. Top-K remains unsuitable for exhaustive thread requests.
