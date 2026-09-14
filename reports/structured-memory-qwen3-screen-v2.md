# Host-Built Structured Thread Memory Evaluation

- Version: `structured-memory-v2`
- Fixture digest: `237a195e3dc9b4fad23e6ab0e01b45319d7a1e05d739af4dc1ac3503b28e3fc1`
- Deterministic hard contract: PASS
- Production ready: False

The host mines source occurrences and persists validated records. The model returns IDs only; this lane makes no generated context or summary calls.

## Deterministic candidate and memory quality

- Event precision/recall: 1.000/1.000
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

### qwen3:8b

- Complete: True
- Quality gate: False
- Fatal error: none
- Records: 8/8 successful; 8 attempted
- Prompt/output tokens: 5588/835
- Summed latency: 10962.4 ms

- Repeat 1: events P/R 1.000/0.875; relations F1 0.667; family F1 0.923; slots P/R 1.000/1.000; poison 1.000.

## Limits

- The sentence miner is bounded and intentionally simple; broader unlabeled email needs separate recall evaluation.
- Closed-world IDs prevent fabricated memory records but do not prove that model selection is semantically correct.
- The one-repeat screen is a prerequisite, not the required three-repeat multi-model qualification.
- No result changes Thunderbird or establishes production readiness.
