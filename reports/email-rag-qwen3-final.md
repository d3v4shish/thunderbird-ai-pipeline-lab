# Selective Decomposition on Synthetic Email Threads

Paired direct endpoint-hybrid versus deterministic selective routing. Only multi-part queries receive model decomposition; exhaustive requests receive scope-locked canonical thread ranges. Both lanes run the same strict grounded-answer generator.

Repeats: 3. Production ready: False. Safety pass: True.

## Stability

| Method | Document recall | Retrieval fact recall | Fact MRR | Answer fact recall | Answer correctness | Citation precision | Abstention | Retrieval p50 ms | Answer p50 ms |
|---|---|---|---|---|---|---|---|---|---|
| direct | 0.970, 0.970, 0.970 | 0.846, 0.846, 0.846 | 0.547, 0.547, 0.547 | 0.846, 0.846, 0.846 | 0.923, 0.923, 0.923 | 1.000, 1.000, 1.000 | 1.000, 1.000, 1.000 | 63.826, 62.634, 61.819 | 1127.712, 1128.262, 1106.007 |
| selective | 1.000, 1.000, 1.000 | 1.000, 1.000, 1.000 | 0.562, 0.562, 0.562 | 1.000, 1.000, 1.000 | 1.000, 1.000, 1.000 | 1.000, 1.000, 1.000 | 1.000, 1.000, 1.000 | 64.693, 64.299, 64.229 | 1127.712, 1128.262, 1106.007 |

## Promotion check

- No quality regression in every repeat: True
- At least one quality improvement: True
- Broader-evaluation candidate: True

## Route attribution

| Route | Cases per repeat | No regression | Any improvement | Broader-evaluation candidate |
|---|---:|:---:|:---:|:---:|
| decomposition | 4 | True | False | False |
| thread_range | 1 | True | True | True |

## Repeat 1

Routes correct: 1.000. Decomposition calls/cache hits/failures: 0/4/0.
Unique final-answer calls: 18.

### Per-case comparison

| Case | Route | Direct retrieval facts | Selective retrieval facts | Direct answer facts | Selective answer facts | Direct correct | Selective correct |
|---|---|---:|---:|---:|---:|:---:|:---:|
| `email-exact-room` | direct | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-semantic-recovery` | direct | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-latest-revision` | direct | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-attachment` | direct | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-prompt-injection` | direct | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-multilingual` | direct | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-multipart-meridian` | decomposition | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-multipart-quartz` | decomposition | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-multipart-ember` | decomposition | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-multipart-polar` | decomposition | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-exhaustive-atlas` | thread_range | 0.6666666666666666 | 1.0 | 0.667 | 1.000 | False | True |
| `email-negative` | direct | - | - | 1.000 | 1.000 | True | True |
| `email-scope-isolation` | direct | - | - | 1.000 | 1.000 | True | True |

The JSON companion retains every route, decomposition prompt/output, embedding digest, ranking, canonical passage, answer prompt/output, validation result, metric, and runtime record.

## Repeat 2

Routes correct: 1.000. Decomposition calls/cache hits/failures: 0/4/0.
Unique final-answer calls: 18.

### Per-case comparison

| Case | Route | Direct retrieval facts | Selective retrieval facts | Direct answer facts | Selective answer facts | Direct correct | Selective correct |
|---|---|---:|---:|---:|---:|:---:|:---:|
| `email-exact-room` | direct | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-semantic-recovery` | direct | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-latest-revision` | direct | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-attachment` | direct | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-prompt-injection` | direct | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-multilingual` | direct | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-multipart-meridian` | decomposition | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-multipart-quartz` | decomposition | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-multipart-ember` | decomposition | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-multipart-polar` | decomposition | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-exhaustive-atlas` | thread_range | 0.6666666666666666 | 1.0 | 0.667 | 1.000 | False | True |
| `email-negative` | direct | - | - | 1.000 | 1.000 | True | True |
| `email-scope-isolation` | direct | - | - | 1.000 | 1.000 | True | True |

The JSON companion retains every route, decomposition prompt/output, embedding digest, ranking, canonical passage, answer prompt/output, validation result, metric, and runtime record.

## Repeat 3

Routes correct: 1.000. Decomposition calls/cache hits/failures: 0/4/0.
Unique final-answer calls: 18.

### Per-case comparison

| Case | Route | Direct retrieval facts | Selective retrieval facts | Direct answer facts | Selective answer facts | Direct correct | Selective correct |
|---|---|---:|---:|---:|---:|:---:|:---:|
| `email-exact-room` | direct | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-semantic-recovery` | direct | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-latest-revision` | direct | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-attachment` | direct | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-prompt-injection` | direct | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-multilingual` | direct | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-multipart-meridian` | decomposition | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-multipart-quartz` | decomposition | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-multipart-ember` | decomposition | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-multipart-polar` | decomposition | 1.0 | 1.0 | 1.000 | 1.000 | True | True |
| `email-exhaustive-atlas` | thread_range | 0.6666666666666666 | 1.0 | 0.667 | 1.000 | False | True |
| `email-negative` | direct | - | - | 1.000 | 1.000 | True | True |
| `email-scope-isolation` | direct | - | - | 1.000 | 1.000 | True | True |

The JSON companion retains every route, decomposition prompt/output, embedding digest, ranking, canonical passage, answer prompt/output, validation result, metric, and runtime record.

## Decision

Promote deterministic thread-range coverage to broader evaluation. Decomposition had no quality gain on the four exact-identifier multi-part cases and is not promoted by this experiment. This synthetic experiment cannot establish production readiness.
