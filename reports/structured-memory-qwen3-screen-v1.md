# Host-Built Structured Thread Memory Evaluation

- Version: `structured-memory-v1`
- Fixture digest: `2f8c1ac45545bc4515b44b2c045705263f0b4287f47fcf2f951428073061c7ae`
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

- Complete: False
- Quality gate: False
- Fatal error: StructuredMemoryError: multiple candidates selected for slot: amount
- Records: 1/8 successful; 2 attempted
- Prompt/output tokens: 541/117
- Summed latency: 4213.9 ms


## Limits

- The sentence miner is bounded and intentionally simple; broader unlabeled email needs separate recall evaluation.
- Closed-world IDs prevent fabricated memory records but do not prove that model selection is semantically correct.
- The one-repeat screen is a prerequisite, not the required three-repeat multi-model qualification.
- No result changes Thunderbird or establishes production readiness.
