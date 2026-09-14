# Host-Owned Slot Candidate Evaluation

- Fixture digest: `84f54b353abf3d4bcc174120c90333b3b057e309de388ad359153a20d30a73c9`
- Documents: 8
- Deterministic contract: PASS
- Production ready: False

| Case | Candidates | Expected | Selected | Span |
|---|---:|---|---|---|
| candidate-unique | 1 | $530.00 | $530.00 | PASS |
| candidate-repeated-identical | 2 | $540.00 | $540.00 | PASS |
| candidate-corrected | 2 | $560.00 | $560.00 | PASS |
| candidate-negated | 2 | $590.00 | $590.00 | PASS |
| candidate-total | 3 | $660.00 | $660.00 | PASS |
| candidate-injection | 2 | $710.00 | $710.00 | PASS |
| candidate-date | 2 | 2032-07-14 | 2032-07-14 | PASS |
| candidate-absent | 0 | none | none | PASS |

## Live selection screen

Not run. The exact live call plan is retained in the JSON report.

## Limits

- The typed extractor is bounded and can miss values outside configured patterns.
- Model selection quality is separate from candidate/source validity.
- No result changes Thunderbird or establishes production readiness.
