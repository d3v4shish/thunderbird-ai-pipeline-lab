# Query-time Advanced-RAG Evaluation

Paired query-time ablation over one endpoint-embedded, structure-aware index. Generated hypotheses, rewrites, subqueries, step-back queries, relevance grades, and routes can change retrieval only; all reported evidence is unchanged source text.

Repeats: 3. Production ready: False. Safety pass: True.

## Compared methods

- Direct: original query with endpoint hybrid retrieval.
- HyDE: original lexical query plus the embedding of a hypothetical relevant passage.
- Fusion: original query plus three model rewrites, merged with reciprocal-rank fusion.
- Decomposition: original query plus independently searchable subquestions, merged with reciprocal-rank fusion.
- Step-back: original query plus one broader conceptual query, merged with reciprocal-rank fusion.
- Corrective: grade direct evidence, retry with local fusion when needed, then retain only graded-relevant source passages.
- Adaptive: the chat model routes each query to one of the five retrieval methods; it cannot choose no retrieval.

Generated text is retrieval control data only. Every cited passage is canonical source text.

## Stability across repeats

| Method | Document recall | Fact recall | Fact MRR | MRR | Negative rejection | Retrieval p50 ms | Est. uncached online p50 ms |
|---|---|---|---|---|---|---|---|
| direct | 1.000, 1.000, 1.000 | 0.857, 0.857, 0.857 | 0.410, 0.410, 0.410 | 0.950, 0.950, 0.950 | 0.000, 0.000, 0.000 | 8.402, 8.416, 8.416 | 8.402, 8.416, 8.416 |
| hyde | 1.000, 1.000, 1.000 | 0.786, 0.786, 0.786 | 0.403, 0.415, 0.415 | 0.950, 0.950, 0.950 | 0.000, 0.000, 0.000 | 8.308, 8.414, 8.371 | 1213.138, 1213.260, 1213.208 |
| fusion | 1.000, 1.000, 1.000 | 0.786, 0.786, 0.786 | 0.398, 0.398, 0.398 | 0.950, 0.950, 0.950 | 0.000, 0.000, 0.000 | 33.941, 34.466, 33.626 | 508.663, 508.728, 508.485 |
| decomposition | 1.000, 1.000, 1.000 | 0.857, 0.857, 0.857 | 0.416, 0.416, 0.416 | 1.000, 1.000, 1.000 | 0.000, 0.000, 0.000 | 25.053, 25.308, 25.092 | 417.765, 412.613, 418.108 |
| step_back | 1.000, 1.000, 1.000 | 0.857, 0.857, 0.857 | 0.410, 0.410, 0.410 | 0.950, 0.950, 0.950 | 0.000, 0.000, 0.000 | 16.829, 16.967, 16.789 | 290.932, 291.065, 290.825 |
| corrective | 0.900, 0.900, 0.900 | 0.810, 0.738, 0.738 | 0.387, 0.380, 0.380 | 0.900, 0.900, 0.900 | 1.000, 1.000, 1.000 | 8.702, 8.867, 9.062 | 536.914, 587.780, 1096.837 |
| adaptive | 1.000, 1.000, 1.000 | 0.857, 0.857, 0.857 | 0.410, 0.410, 0.410 | 0.950, 0.950, 0.950 | 0.000, 0.000, 0.000 | 8.417, 8.510, 8.545 | 370.065, 370.113, 370.079 |

## Promotion checks

| Method | No regression in every repeat | Any quality improvement | Broader-evaluation candidate |
|---|:---:|:---:|:---:|
| hyde | False | True | False |
| fusion | False | False | False |
| decomposition | True | True | True |
| step_back | True | False | False |
| corrective | False | True | False |
| adaptive | True | False | False |

## Repeat 1

Transform calls: 2; cache hits: 63; failures: 2.
Corrective grade calls: 8; cache hits: 9; verdict accuracy: 0.824; label precision/recall: 0.784/0.882.
Adaptive optimal-route rate: 0.923.

| Method | Doc recall | Fact recall | Fact MRR | MRR | nDCG | Negative rejection | Source spans | Retrieval p50 ms | Est. uncached online p50 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | 1.000 | 0.857 | 0.410 | 0.950 | 0.963 | 0.000 | 1.000 | 8.402 | 8.402 |
| hyde | 1.000 | 0.786 | 0.403 | 0.950 | 0.963 | 0.000 | 1.000 | 8.308 | 1213.138 |
| fusion | 1.000 | 0.786 | 0.398 | 0.950 | 0.963 | 0.000 | 1.000 | 33.941 | 508.663 |
| decomposition | 1.000 | 0.857 | 0.416 | 1.000 | 0.988 | 0.000 | 1.000 | 25.053 | 417.765 |
| step_back | 1.000 | 0.857 | 0.410 | 0.950 | 0.963 | 0.000 | 1.000 | 16.829 | 290.932 |
| corrective | 0.900 | 0.810 | 0.387 | 0.900 | 0.900 | 1.000 | 1.000 | 8.702 | 536.914 |
| adaptive | 1.000 | 0.857 | 0.410 | 0.950 | 0.963 | 0.000 | 1.000 | 8.417 | 370.065 |

### Per-case retrieval audit

#### direct

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "multilingual"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 5, "F16": 5, "F17": 5, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 6, "F25": 6, "F26": 6, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "long-10240", "meridian-finance", "long-10240", "semantic-access"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "long-10240", "long-10240", "semantic-recovery", "semantic-access", "meridian-schedule", "exact-distractor"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "exact-distractor", "long-10240", "meridian-schedule", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "semantic-distractor", "semantic-access", "exact-distractor", "semantic-retention", "revision-old"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["long-10240", "long-10240", "long-10240", "semantic-retention", "injection", "long-10240", "long-10240", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "revision-old", "revision-latest", "meridian-schedule", "exact-orbit", "graph-vendor", "semantic-distractor"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "exact-distractor", "meridian-finance"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "injection", "exact-distractor", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "exact-distractor", "revision-latest", "revision-old", "long-10240", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "meridian-finance", "semantic-recovery", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-access", "meridian-finance", "semantic-distractor", "revision-latest", "semantic-retention", "exact-distractor"]`.
#### hyde

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "multilingual"]`.
- `long-document-coverage`: facts 0.71875, fact ranks `{"F01": 2, "F02": 2, "F03": 2, "F04": 2, "F05": 4, "F06": 4, "F07": 4, "F11": 6, "F12": 6, "F13": 6, "F14": 5, "F15": 5, "F16": 5, "F17": 5, "F21": 8, "F22": 8, "F23": 8, "F27": 3, "F28": 3, "F29": 3, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "exact-orbit", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "long-10240", "exact-orbit", "meridian-finance", "multilingual"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "semantic-recovery", "semantic-distractor", "long-10240", "long-10240", "meridian-finance", "semantic-access"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "meridian-schedule", "long-10240", "long-10240", "exact-distractor", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "revision-old", "semantic-distractor", "semantic-access", "semantic-retention", "exact-distractor"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["semantic-distractor", "long-10240", "long-10240", "semantic-retention", "long-10240", "long-10240", "injection", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "revision-old", "revision-latest", "meridian-finance", "exact-orbit", "meridian-schedule", "semantic-distractor", "graph-vendor"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "semantic-retention", "revision-old", "exact-distractor", "revision-latest", "meridian-finance"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "long-10240", "exact-distractor", "injection", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "revision-latest", "exact-distractor", "revision-old", "long-10240", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "meridian-finance", "semantic-recovery", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-distractor", "semantic-access", "meridian-finance", "revision-latest", "semantic-retention", "exact-distractor"]`.
#### fusion

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "revision-old", "graph-vendor", "revision-latest", "meridian-schedule", "semantic-distractor"]`.
- `long-document-coverage`: facts 0.71875, fact ranks `{"F01": 2, "F02": 2, "F03": 2, "F04": 2, "F05": 8, "F06": 8, "F07": 8, "F11": 7, "F12": 7, "F13": 7, "F14": 6, "F15": 6, "F16": 6, "F17": 6, "F24": 4, "F25": 4, "F26": 4, "F27": 3, "F28": 3, "F29": 3, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "injection", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "meridian-finance", "long-10240", "exact-distractor", "semantic-access", "long-10240"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "semantic-recovery", "meridian-schedule", "semantic-access", "long-10240", "long-10240", "meridian-finance"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "exact-distractor", "long-10240", "meridian-schedule", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "semantic-access", "semantic-distractor", "exact-distractor", "revision-old", "semantic-retention"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["semantic-retention", "long-10240", "long-10240", "long-10240", "injection", "semantic-distractor", "meridian-schedule", "semantic-access"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "exact-orbit", "revision-latest", "graph-vendor", "revision-old", "semantic-distractor", "meridian-schedule"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "exact-distractor", "meridian-finance"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "exact-distractor", "long-10240", "injection", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "revision-latest", "exact-distractor", "long-10240", "long-10240", "semantic-distractor"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "semantic-recovery", "meridian-finance", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-access", "meridian-finance", "revision-latest", "semantic-distractor", "exact-distractor", "semantic-retention"]`.
#### decomposition

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "multilingual"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 6, "F16": 6, "F17": 6, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 5, "F25": 5, "F26": 5, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "meridian-finance", "long-10240", "semantic-access", "long-10240"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 4}`, documents `["graph-team", "semantic-recovery", "long-10240", "graph-vendor", "exact-distractor", "long-10240", "semantic-access", "meridian-finance"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "exact-distractor", "long-10240", "meridian-schedule", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "semantic-distractor", "revision-latest", "semantic-access", "exact-distractor", "revision-old", "semantic-retention"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["semantic-retention", "long-10240", "long-10240", "long-10240", "injection", "semantic-distractor", "long-10240", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "revision-old", "graph-vendor", "exact-orbit", "revision-latest", "graph-team", "semantic-access"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "meridian-finance", "injection"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "exact-distractor", "injection", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "revision-latest", "exact-orbit", "revision-old", "exact-distractor", "long-10240", "semantic-distractor"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 1}`, documents `["semantic-retention", "graph-vendor", "meridian-finance", "long-10240", "semantic-recovery", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "exact-distractor", "semantic-access", "semantic-distractor", "revision-latest", "semantic-recovery", "meridian-finance", "long-10240"]`.
#### step_back

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "multilingual"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 5, "F16": 5, "F17": 5, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 6, "F25": 6, "F26": 6, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "long-10240", "meridian-finance", "long-10240", "semantic-access"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "long-10240", "long-10240", "semantic-recovery", "semantic-access", "meridian-schedule", "exact-distractor"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "exact-distractor", "long-10240", "meridian-schedule", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "semantic-distractor", "semantic-access", "exact-distractor", "semantic-retention", "revision-old"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["long-10240", "long-10240", "long-10240", "semantic-retention", "injection", "long-10240", "long-10240", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "revision-old", "revision-latest", "meridian-schedule", "exact-orbit", "graph-vendor", "semantic-distractor"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "exact-distractor", "meridian-finance"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "injection", "exact-distractor", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "exact-distractor", "revision-latest", "revision-old", "long-10240", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "meridian-finance", "semantic-recovery", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-access", "meridian-finance", "semantic-distractor", "revision-latest", "semantic-retention", "exact-distractor"]`.
#### corrective

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 5, "F16": 5, "F17": 5, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 6, "F25": 6, "F26": 6, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `[]`.
- `no-answer`: facts None, fact ranks `{}`, documents `[]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 0.0, fact ranks `{}`, documents `[]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 1}`, documents `["semantic-retention"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `[]`.
#### adaptive

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "multilingual"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 6, "F16": 6, "F17": 6, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 5, "F25": 5, "F26": 5, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "long-10240", "meridian-finance", "long-10240", "semantic-access"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "long-10240", "long-10240", "semantic-recovery", "semantic-access", "meridian-schedule", "exact-distractor"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "exact-distractor", "long-10240", "meridian-schedule", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "semantic-distractor", "semantic-access", "exact-distractor", "semantic-retention", "revision-old"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["long-10240", "long-10240", "long-10240", "semantic-retention", "injection", "long-10240", "long-10240", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "revision-old", "revision-latest", "meridian-schedule", "exact-orbit", "graph-vendor", "semantic-distractor"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "meridian-finance", "injection"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "injection", "exact-distractor", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "exact-distractor", "revision-latest", "revision-old", "long-10240", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "meridian-finance", "semantic-recovery", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-access", "meridian-finance", "semantic-distractor", "revision-latest", "semantic-retention", "exact-distractor"]`.

The JSON companion retains every transformation prompt, original model output, validated rewrite, corrective grade, query/document vector digest, ranking, metric, and canonical evidence span for this repeat.

## Repeat 2

Transform calls: 2; cache hits: 63; failures: 2.
Corrective grade calls: 7; cache hits: 11; verdict accuracy: 0.778; label precision/recall: 0.736/0.833.
Adaptive optimal-route rate: 0.923.

| Method | Doc recall | Fact recall | Fact MRR | MRR | nDCG | Negative rejection | Source spans | Retrieval p50 ms | Est. uncached online p50 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | 1.000 | 0.857 | 0.410 | 0.950 | 0.963 | 0.000 | 1.000 | 8.416 | 8.416 |
| hyde | 1.000 | 0.786 | 0.415 | 0.950 | 0.963 | 0.000 | 1.000 | 8.414 | 1213.260 |
| fusion | 1.000 | 0.786 | 0.398 | 0.950 | 0.963 | 0.000 | 1.000 | 34.466 | 508.728 |
| decomposition | 1.000 | 0.857 | 0.416 | 1.000 | 0.988 | 0.000 | 1.000 | 25.308 | 412.613 |
| step_back | 1.000 | 0.857 | 0.410 | 0.950 | 0.963 | 0.000 | 1.000 | 16.967 | 291.065 |
| corrective | 0.900 | 0.738 | 0.380 | 0.900 | 0.900 | 1.000 | 1.000 | 8.867 | 587.780 |
| adaptive | 1.000 | 0.857 | 0.410 | 0.950 | 0.963 | 0.000 | 1.000 | 8.510 | 370.113 |

### Per-case retrieval audit

#### direct

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "long-10240"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 5, "F16": 5, "F17": 5, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 6, "F25": 6, "F26": 6, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "meridian-finance", "long-10240", "long-10240", "semantic-access"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "long-10240", "long-10240", "semantic-recovery", "semantic-access", "meridian-schedule", "exact-distractor"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "exact-distractor", "long-10240", "meridian-schedule", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "exact-distractor", "semantic-distractor", "semantic-access", "semantic-retention", "revision-old"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["long-10240", "long-10240", "long-10240", "semantic-retention", "injection", "long-10240", "long-10240", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "revision-old", "revision-latest", "meridian-schedule", "exact-orbit", "graph-vendor", "semantic-distractor"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "exact-distractor", "meridian-finance"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "injection", "exact-distractor", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "exact-distractor", "revision-latest", "revision-old", "long-10240", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "meridian-finance", "semantic-recovery", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-access", "meridian-finance", "revision-latest", "semantic-distractor", "semantic-retention", "exact-distractor"]`.
#### hyde

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "multilingual"]`.
- `long-document-coverage`: facts 0.71875, fact ranks `{"F01": 1, "F02": 1, "F03": 1, "F04": 1, "F05": 4, "F06": 4, "F07": 4, "F11": 6, "F12": 6, "F13": 6, "F14": 5, "F15": 5, "F16": 5, "F17": 5, "F21": 8, "F22": 8, "F23": 8, "F27": 3, "F28": 3, "F29": 3, "F30": 2, "F31": 2, "F32": 2}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "exact-orbit", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "long-10240", "exact-orbit", "meridian-finance", "long-10240"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "semantic-recovery", "semantic-distractor", "long-10240", "long-10240", "meridian-finance", "semantic-access"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "meridian-schedule", "long-10240", "long-10240", "long-10240", "exact-distractor", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "revision-old", "semantic-distractor", "semantic-access", "meridian-schedule", "semantic-retention"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["semantic-distractor", "long-10240", "long-10240", "semantic-retention", "long-10240", "long-10240", "injection", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "revision-old", "revision-latest", "meridian-finance", "exact-orbit", "meridian-schedule", "semantic-distractor", "graph-vendor"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "semantic-retention", "revision-old", "exact-distractor", "revision-latest", "meridian-finance"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "long-10240", "exact-distractor", "injection", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "revision-latest", "exact-distractor", "revision-old", "long-10240", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "meridian-finance", "semantic-recovery", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-distractor", "semantic-access", "meridian-finance", "revision-latest", "semantic-retention", "exact-distractor"]`.
#### fusion

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "revision-old", "graph-vendor", "meridian-schedule", "revision-latest", "semantic-distractor"]`.
- `long-document-coverage`: facts 0.71875, fact ranks `{"F01": 2, "F02": 2, "F03": 2, "F04": 2, "F05": 8, "F06": 8, "F07": 8, "F11": 6, "F12": 6, "F13": 6, "F14": 6, "F15": 7, "F16": 7, "F17": 7, "F24": 4, "F25": 4, "F26": 4, "F27": 3, "F28": 3, "F29": 3, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "injection", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "meridian-finance", "long-10240", "exact-distractor", "long-10240", "semantic-access"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "semantic-recovery", "meridian-schedule", "semantic-access", "long-10240", "long-10240", "meridian-finance"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "exact-distractor", "long-10240", "long-10240", "meridian-schedule", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "semantic-distractor", "semantic-access", "exact-distractor", "revision-old", "semantic-retention"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["semantic-retention", "long-10240", "long-10240", "long-10240", "injection", "semantic-distractor", "meridian-schedule", "semantic-access"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "exact-orbit", "revision-latest", "graph-vendor", "revision-old", "semantic-distractor", "meridian-schedule"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "exact-distractor", "meridian-finance"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "exact-distractor", "long-10240", "long-10240", "injection", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "revision-latest", "exact-distractor", "long-10240", "long-10240", "semantic-distractor"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "semantic-recovery", "meridian-finance", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-access", "revision-latest", "meridian-finance", "exact-distractor", "semantic-distractor", "semantic-retention"]`.
#### decomposition

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "long-10240"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 6, "F16": 6, "F17": 6, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 5, "F25": 5, "F26": 5, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "meridian-finance", "exact-distractor", "long-10240", "semantic-access", "long-10240"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 4}`, documents `["graph-team", "semantic-recovery", "long-10240", "graph-vendor", "exact-distractor", "long-10240", "semantic-access", "meridian-finance"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "exact-distractor", "long-10240", "meridian-schedule", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "semantic-distractor", "semantic-access", "exact-distractor", "revision-old", "semantic-retention"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["semantic-retention", "long-10240", "long-10240", "long-10240", "injection", "semantic-distractor", "long-10240", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "revision-old", "graph-vendor", "exact-orbit", "revision-latest", "graph-team", "semantic-access"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "meridian-finance", "injection"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "exact-distractor", "injection", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "revision-latest", "exact-orbit", "revision-old", "exact-distractor", "semantic-distractor", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 1}`, documents `["semantic-retention", "graph-vendor", "meridian-finance", "long-10240", "semantic-recovery", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "exact-distractor", "semantic-access", "semantic-distractor", "revision-latest", "semantic-recovery", "meridian-finance", "long-10240"]`.
#### step_back

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "long-10240"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 5, "F16": 5, "F17": 5, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 6, "F25": 6, "F26": 6, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "meridian-finance", "long-10240", "long-10240", "semantic-access"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "long-10240", "long-10240", "semantic-recovery", "semantic-access", "meridian-schedule", "exact-distractor"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "exact-distractor", "long-10240", "meridian-schedule", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "exact-distractor", "semantic-distractor", "semantic-access", "semantic-retention", "revision-old"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["long-10240", "long-10240", "long-10240", "semantic-retention", "injection", "long-10240", "long-10240", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "revision-old", "revision-latest", "meridian-schedule", "exact-orbit", "graph-vendor", "semantic-distractor"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "exact-distractor", "meridian-finance"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "injection", "exact-distractor", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "exact-distractor", "revision-latest", "revision-old", "long-10240", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "meridian-finance", "semantic-recovery", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-access", "meridian-finance", "revision-latest", "semantic-distractor", "semantic-retention", "exact-distractor"]`.
#### corrective

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240"]`.
- `long-document-coverage`: facts 0.71875, fact ranks `{"F01": 2, "F02": 2, "F03": 2, "F04": 2, "F05": 7, "F06": 7, "F07": 7, "F11": 5, "F12": 5, "F13": 5, "F14": 5, "F15": 6, "F16": 6, "F17": 6, "F24": 4, "F25": 4, "F26": 4, "F27": 3, "F28": 3, "F29": 3, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `[]`.
- `no-answer`: facts None, fact ranks `{}`, documents `[]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 0.0, fact ranks `{}`, documents `[]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 1}`, documents `["semantic-retention"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `[]`.
#### adaptive

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "long-10240"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 6, "F16": 6, "F17": 6, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 5, "F25": 5, "F26": 5, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "meridian-finance", "long-10240", "long-10240", "semantic-access"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "long-10240", "long-10240", "semantic-recovery", "semantic-access", "meridian-schedule", "exact-distractor"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "exact-distractor", "long-10240", "meridian-schedule", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "exact-distractor", "semantic-distractor", "semantic-access", "semantic-retention", "revision-old"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["long-10240", "long-10240", "long-10240", "semantic-retention", "injection", "long-10240", "long-10240", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "revision-old", "revision-latest", "meridian-schedule", "exact-orbit", "graph-vendor", "semantic-distractor"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "meridian-finance", "injection"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "injection", "exact-distractor", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "exact-distractor", "revision-latest", "revision-old", "long-10240", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "meridian-finance", "semantic-recovery", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-access", "meridian-finance", "revision-latest", "semantic-distractor", "semantic-retention", "exact-distractor"]`.

The JSON companion retains every transformation prompt, original model output, validated rewrite, corrective grade, query/document vector digest, ranking, metric, and canonical evidence span for this repeat.

## Repeat 3

Transform calls: 2; cache hits: 63; failures: 2.
Corrective grade calls: 4; cache hits: 14; verdict accuracy: 0.778; label precision/recall: 0.741/0.833.
Adaptive optimal-route rate: 0.923.

| Method | Doc recall | Fact recall | Fact MRR | MRR | nDCG | Negative rejection | Source spans | Retrieval p50 ms | Est. uncached online p50 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | 1.000 | 0.857 | 0.410 | 0.950 | 0.963 | 0.000 | 1.000 | 8.416 | 8.416 |
| hyde | 1.000 | 0.786 | 0.415 | 0.950 | 0.963 | 0.000 | 1.000 | 8.371 | 1213.208 |
| fusion | 1.000 | 0.786 | 0.398 | 0.950 | 0.963 | 0.000 | 1.000 | 33.626 | 508.485 |
| decomposition | 1.000 | 0.857 | 0.416 | 1.000 | 0.988 | 0.000 | 1.000 | 25.092 | 418.108 |
| step_back | 1.000 | 0.857 | 0.410 | 0.950 | 0.963 | 0.000 | 1.000 | 16.789 | 290.825 |
| corrective | 0.900 | 0.738 | 0.380 | 0.900 | 0.900 | 1.000 | 1.000 | 9.062 | 1096.837 |
| adaptive | 1.000 | 0.857 | 0.410 | 0.950 | 0.963 | 0.000 | 1.000 | 8.545 | 370.079 |

### Per-case retrieval audit

#### direct

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "long-10240"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 5, "F16": 5, "F17": 5, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 6, "F25": 6, "F26": 6, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "meridian-finance", "long-10240", "long-10240", "semantic-access"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "long-10240", "long-10240", "semantic-recovery", "semantic-access", "meridian-schedule", "exact-distractor"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "long-10240", "exact-distractor", "meridian-schedule", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "exact-distractor", "semantic-distractor", "semantic-access", "semantic-retention", "revision-old"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["long-10240", "long-10240", "long-10240", "semantic-retention", "injection", "long-10240", "long-10240", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "revision-old", "revision-latest", "meridian-schedule", "exact-orbit", "graph-vendor", "semantic-distractor"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "exact-distractor", "meridian-finance"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "injection", "exact-distractor", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "exact-distractor", "revision-latest", "revision-old", "long-10240", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "meridian-finance", "semantic-recovery", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-access", "meridian-finance", "semantic-distractor", "revision-latest", "semantic-retention", "exact-distractor"]`.
#### hyde

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "multilingual"]`.
- `long-document-coverage`: facts 0.71875, fact ranks `{"F01": 1, "F02": 1, "F03": 1, "F04": 1, "F05": 4, "F06": 4, "F07": 4, "F11": 6, "F12": 6, "F13": 6, "F14": 5, "F15": 5, "F16": 5, "F17": 5, "F21": 8, "F22": 8, "F23": 8, "F27": 3, "F28": 3, "F29": 3, "F30": 2, "F31": 2, "F32": 2}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "exact-orbit", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "long-10240", "exact-orbit", "meridian-finance", "long-10240"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "semantic-recovery", "semantic-distractor", "long-10240", "long-10240", "meridian-finance", "semantic-access"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "meridian-schedule", "long-10240", "long-10240", "exact-distractor", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "revision-old", "semantic-distractor", "semantic-access", "meridian-schedule", "semantic-retention"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["semantic-distractor", "long-10240", "long-10240", "semantic-retention", "long-10240", "long-10240", "injection", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "revision-old", "revision-latest", "meridian-finance", "exact-orbit", "meridian-schedule", "semantic-distractor", "graph-vendor"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "semantic-retention", "revision-old", "exact-distractor", "revision-latest", "meridian-finance"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "long-10240", "exact-distractor", "injection", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "revision-latest", "exact-distractor", "revision-old", "long-10240", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "meridian-finance", "semantic-recovery", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-distractor", "semantic-access", "revision-latest", "meridian-finance", "semantic-retention", "exact-distractor"]`.
#### fusion

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "revision-old", "graph-vendor", "meridian-schedule", "long-10240", "revision-latest"]`.
- `long-document-coverage`: facts 0.71875, fact ranks `{"F01": 2, "F02": 2, "F03": 2, "F04": 2, "F05": 8, "F06": 8, "F07": 8, "F11": 6, "F12": 6, "F13": 6, "F14": 6, "F15": 7, "F16": 7, "F17": 7, "F24": 4, "F25": 4, "F26": 4, "F27": 3, "F28": 3, "F29": 3, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "injection", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "meridian-finance", "long-10240", "exact-distractor", "long-10240", "semantic-access"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "semantic-recovery", "meridian-schedule", "semantic-access", "long-10240", "long-10240", "meridian-finance"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "long-10240", "exact-distractor", "long-10240", "meridian-schedule", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "semantic-distractor", "exact-distractor", "semantic-access", "revision-old", "semantic-retention"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["semantic-retention", "long-10240", "long-10240", "long-10240", "injection", "semantic-distractor", "meridian-schedule", "semantic-access"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "exact-orbit", "revision-latest", "graph-vendor", "revision-old", "semantic-distractor", "meridian-schedule"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "exact-distractor", "meridian-finance"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "exact-distractor", "long-10240", "long-10240", "injection", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "revision-latest", "exact-distractor", "long-10240", "long-10240", "semantic-distractor"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "semantic-recovery", "meridian-finance", "long-10240", "long-10240", "long-10240", "revision-old"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-access", "meridian-finance", "revision-latest", "semantic-distractor", "exact-distractor", "semantic-retention"]`.
#### decomposition

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "long-10240"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 6, "F16": 6, "F17": 6, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 5, "F25": 5, "F26": 5, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "meridian-finance", "exact-distractor", "long-10240", "semantic-access", "long-10240"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 4}`, documents `["graph-team", "semantic-recovery", "long-10240", "graph-vendor", "exact-distractor", "long-10240", "semantic-access", "meridian-finance"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "exact-distractor", "long-10240", "meridian-schedule", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "semantic-distractor", "semantic-access", "exact-distractor", "revision-old", "semantic-retention"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["semantic-retention", "long-10240", "long-10240", "long-10240", "injection", "semantic-distractor", "long-10240", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "revision-old", "graph-vendor", "exact-orbit", "revision-latest", "graph-team", "semantic-access"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "meridian-finance", "injection"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "exact-distractor", "injection", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "revision-latest", "exact-orbit", "revision-old", "exact-distractor", "semantic-distractor", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 1}`, documents `["semantic-retention", "graph-vendor", "long-10240", "meridian-finance", "semantic-recovery", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "exact-distractor", "semantic-access", "semantic-distractor", "revision-latest", "semantic-recovery", "meridian-finance", "long-10240"]`.
#### step_back

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "long-10240"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 5, "F16": 5, "F17": 5, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 6, "F25": 6, "F26": 6, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "meridian-finance", "long-10240", "long-10240", "semantic-access"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "long-10240", "long-10240", "semantic-recovery", "semantic-access", "meridian-schedule", "exact-distractor"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "long-10240", "exact-distractor", "meridian-schedule", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "exact-distractor", "semantic-distractor", "semantic-access", "semantic-retention", "revision-old"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["long-10240", "long-10240", "long-10240", "semantic-retention", "injection", "long-10240", "long-10240", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "revision-old", "revision-latest", "meridian-schedule", "exact-orbit", "graph-vendor", "semantic-distractor"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "exact-distractor", "meridian-finance"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "injection", "exact-distractor", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "exact-distractor", "revision-latest", "revision-old", "long-10240", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "meridian-finance", "semantic-recovery", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-access", "meridian-finance", "semantic-distractor", "revision-latest", "semantic-retention", "exact-distractor"]`.
#### corrective

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240"]`.
- `long-document-coverage`: facts 0.71875, fact ranks `{"F01": 2, "F02": 2, "F03": 2, "F04": 2, "F05": 7, "F06": 7, "F07": 7, "F11": 5, "F12": 5, "F13": 5, "F14": 5, "F15": 6, "F16": 6, "F17": 6, "F24": 4, "F25": 4, "F26": 4, "F27": 3, "F28": 3, "F29": 3, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `[]`.
- `no-answer`: facts None, fact ranks `{}`, documents `[]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 0.0, fact ranks `{}`, documents `[]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 1}`, documents `["semantic-retention"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `[]`.
#### adaptive

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "long-10240"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 6, "F16": 6, "F17": 6, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 5, "F25": 5, "F26": 5, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "meridian-finance", "long-10240", "long-10240", "semantic-access"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "long-10240", "long-10240", "semantic-recovery", "semantic-access", "meridian-schedule", "exact-distractor"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "long-10240", "exact-distractor", "meridian-schedule", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "exact-distractor", "semantic-distractor", "semantic-access", "semantic-retention", "revision-old"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["long-10240", "long-10240", "long-10240", "semantic-retention", "injection", "long-10240", "long-10240", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "revision-old", "revision-latest", "meridian-schedule", "exact-orbit", "graph-vendor", "semantic-distractor"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "meridian-finance", "injection"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "injection", "exact-distractor", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "exact-distractor", "revision-latest", "revision-old", "long-10240", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "meridian-finance", "semantic-recovery", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-access", "meridian-finance", "semantic-distractor", "revision-latest", "semantic-retention", "exact-distractor"]`.

The JSON companion retains every transformation prompt, original model output, validated rewrite, corrective grade, query/document vector digest, ranking, metric, and canonical evidence span for this repeat.

## Decision

Retain direct hybrid as the default; route only methods that show a stable, case-specific benefit. No query-time method is production-ready from this synthetic suite.
