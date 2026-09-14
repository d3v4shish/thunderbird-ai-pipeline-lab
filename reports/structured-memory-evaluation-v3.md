# Host-Built Structured Thread Memory Evaluation

- Version: `structured-memory-v3`
- Fixture digest: `4933c53c3743a4557183f8da817abe32c912fa5b687c9a870d5ed7bbadfd48fb`
- Deterministic hard contract: PASS
- Production ready: False

The host mines source occurrences and persists validated records. The model returns IDs only; this lane makes no generated context or summary calls.

## Deterministic candidate and memory quality

- Event precision/recall: 1.000/1.000
- Model event-hint precision/recall: 1.000/1.000
- Relation F1: 1.000
- Family F1: 1.000
- Slot precision/recall: 1.000/1.000
- Source/chronology/poison validity: 1.000/1.000/1.000

## Retrieval contract

- Raw localized fact recall: 1.000
- Structured localized fact recall: 1.000
- Localized no regression: True
- Complete related recall: 1.000
- Unrelated documents: 0

## Live whole-email screen

Not run. The report contains the exact one-call-per-email plan.

## Limits

- The sentence miner is bounded and intentionally simple; broader unlabeled email needs separate recall evaluation.
- Closed-world IDs prevent fabricated memory records but do not prove that model selection is semantically correct.
- The one-repeat screen is a prerequisite, not the required three-repeat multi-model qualification.
- No result changes Thunderbird or establishes production readiness.
