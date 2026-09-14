# Host-Owned Slot Candidate Evaluation

- Fixture digest: `48dc90fd21a9a15dc4099e7de5cee97b12ff1b875fb8b60cd5bfbb17856b76d7`
- Documents: 8
- Deterministic contract: PASS
- Production ready: False

| Case | Candidates (eligible/rejected) | Expected | Selected | Span |
|---|---:|---|---|---|
| candidate-unique | 1/0 | $530.00 | $530.00 | PASS |
| candidate-repeated-identical | 2/0 | $540.00 | $540.00 | PASS |
| candidate-corrected | 2/0 | $560.00 | $560.00 | PASS |
| candidate-negated | 2/0 | $590.00 | $590.00 | PASS |
| candidate-total | 3/0 | $660.00 | $660.00 | PASS |
| candidate-injection | 1/1 | $710.00 | $710.00 | PASS |
| candidate-date | 2/0 | 2032-07-14 | 2032-07-14 | PASS |
| candidate-absent | 0/0 | none | none | PASS |

## Live selection screen

### qwen3:8b

- Complete: True
- Quality gate: True
- Successful: 8/8
- Fatal error: none
- family_accuracy: 1.000
- selection_accuracy: 1.000
- slot_precision: 1.000
- slot_recall: 1.000
- source_span_validity: 1.000
- poisoned_case_accuracy: 1.000

## Limits

- The typed extractor is bounded and can miss values outside configured patterns.
- Model selection quality is separate from candidate/source validity.
- No result changes Thunderbird or establishes production readiness.
