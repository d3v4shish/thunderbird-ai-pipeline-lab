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
| direct | 1.000, 1.000, 1.000 | 0.857, 0.857, 0.857 | 0.410, 0.410, 0.414 | 0.950, 0.950, 0.950 | 0.000, 0.000, 0.000 | 8.288, 8.369, 8.393 | 8.288, 8.369, 8.393 |
| hyde | 1.000, 1.000, 1.000 | 0.786, 0.786, 0.786 | 0.411, 0.399, 0.411 | 0.933, 0.933, 0.933 | 0.000, 0.000, 0.000 | 8.199, 8.353, 8.450 | 1786.560, 1786.752, 1786.740 |
| fusion | 1.000, 1.000, 1.000 | 0.786, 0.786, 0.786 | 0.398, 0.400, 0.398 | 0.950, 0.950, 0.950 | 0.000, 0.000, 0.000 | 33.006, 33.494, 33.741 | 915.098, 914.763, 915.184 |
| decomposition | 1.000, 1.000, 1.000 | 0.857, 0.857, 0.857 | 0.416, 0.416, 0.420 | 1.000, 1.000, 1.000 | 0.000, 0.000, 0.000 | 24.327, 25.086, 25.317 | 760.485, 761.176, 761.481 |
| step_back | 1.000, 1.000, 1.000 | 0.857, 0.857, 0.857 | 0.410, 0.410, 0.414 | 0.950, 0.950, 0.950 | 0.000, 0.000, 0.000 | 16.361, 16.790, 16.976 | 603.442, 603.841, 604.138 |
| corrective | 0.700, 0.700, 0.700 | 0.214, 0.214, 0.762 | 0.214, 0.214, 0.355 | 0.800, 0.800, 0.800 | 1.000, 1.000, 1.000 | 8.633, 8.798, 8.745 | 815.248, 481.275, 733.188 |
| adaptive | 1.000, 1.000, 1.000 | 0.857, 0.857, 0.857 | 0.410, 0.410, 0.414 | 0.950, 0.950, 0.950 | 0.000, 0.000, 0.000 | 8.365, 8.484, 8.529 | 755.105, 755.030, 755.099 |

## Promotion checks

| Method | No regression in every repeat | Any quality improvement | Broader-evaluation candidate |
|---|:---:|:---:|:---:|
| hyde | False | False | False |
| fusion | False | False | False |
| decomposition | True | False | False |
| step_back | True | False | False |
| corrective | False | True | False |
| adaptive | True | False | False |

## Repeat 1

Transform calls: 1; cache hits: 64; failures: 1.
Corrective grade calls: 11; cache hits: 6; verdict accuracy: 0.588; label precision/recall: 0.529/0.713.
Adaptive optimal-route rate: 0.923.

| Method | Doc recall | Fact recall | Fact MRR | MRR | nDCG | Negative rejection | Source spans | Retrieval p50 ms | Est. uncached online p50 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | 1.000 | 0.857 | 0.410 | 0.950 | 0.963 | 0.000 | 1.000 | 8.288 | 8.288 |
| hyde | 1.000 | 0.786 | 0.411 | 0.933 | 0.950 | 0.000 | 1.000 | 8.199 | 1786.560 |
| fusion | 1.000 | 0.786 | 0.398 | 0.950 | 0.963 | 0.000 | 1.000 | 33.006 | 915.098 |
| decomposition | 1.000 | 0.857 | 0.416 | 1.000 | 0.988 | 0.000 | 1.000 | 24.327 | 760.485 |
| step_back | 1.000 | 0.857 | 0.410 | 0.950 | 0.963 | 0.000 | 1.000 | 16.361 | 603.442 |
| corrective | 0.700 | 0.214 | 0.214 | 0.800 | 0.723 | 1.000 | 1.000 | 8.633 | 815.248 |
| adaptive | 1.000 | 0.857 | 0.410 | 0.950 | 0.963 | 0.000 | 1.000 | 8.365 | 755.105 |

### Per-case retrieval audit

#### direct

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "long-10240"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 5, "F16": 5, "F17": 5, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 6, "F25": 6, "F26": 6, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "meridian-finance", "long-10240", "long-10240", "semantic-access"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "long-10240", "long-10240", "semantic-recovery", "semantic-access", "meridian-schedule", "exact-distractor"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "long-10240", "exact-distractor", "meridian-schedule", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "semantic-distractor", "semantic-access", "exact-distractor", "semantic-retention", "revision-old"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["long-10240", "long-10240", "long-10240", "semantic-retention", "long-10240", "injection", "long-10240", "long-10240"]`.
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
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "revision-latest", "meridian-finance", "revision-old", "semantic-distractor", "semantic-access", "semantic-retention", "exact-distractor"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["semantic-distractor", "long-10240", "long-10240", "semantic-retention", "long-10240", "long-10240", "injection", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "revision-old", "revision-latest", "meridian-finance", "exact-orbit", "meridian-schedule", "semantic-distractor", "graph-vendor"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "semantic-retention", "revision-old", "exact-distractor", "revision-latest", "meridian-finance"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "long-10240", "exact-distractor", "injection", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "revision-latest", "exact-distractor", "revision-old", "long-10240", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 3}`, documents `["meridian-finance", "graph-vendor", "semantic-retention", "semantic-recovery", "injection", "revision-old", "long-10240", "semantic-distractor"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-distractor", "semantic-access", "meridian-finance", "revision-latest", "semantic-retention", "exact-distractor"]`.
#### fusion

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "revision-old", "graph-vendor", "meridian-schedule", "revision-latest", "long-10240"]`.
- `long-document-coverage`: facts 0.71875, fact ranks `{"F01": 2, "F02": 2, "F03": 2, "F04": 2, "F05": 8, "F06": 8, "F07": 8, "F11": 6, "F12": 6, "F13": 6, "F14": 6, "F15": 7, "F16": 7, "F17": 7, "F24": 4, "F25": 4, "F26": 4, "F27": 3, "F28": 3, "F29": 3, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "injection", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "meridian-finance", "long-10240", "exact-distractor", "long-10240", "semantic-access"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "semantic-recovery", "meridian-schedule", "semantic-access", "long-10240", "long-10240", "meridian-finance"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "long-10240", "exact-distractor", "long-10240", "meridian-schedule", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "semantic-distractor", "semantic-access", "exact-distractor", "revision-old", "semantic-retention"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["semantic-retention", "long-10240", "long-10240", "long-10240", "semantic-distractor", "injection", "meridian-schedule", "semantic-access"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "exact-orbit", "revision-latest", "graph-vendor", "revision-old", "semantic-distractor", "meridian-schedule"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "exact-distractor", "meridian-finance"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "exact-distractor", "long-10240", "long-10240", "injection", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "revision-latest", "exact-distractor", "long-10240", "long-10240", "semantic-distractor"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "semantic-recovery", "meridian-finance", "long-10240", "long-10240", "revision-old", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-access", "meridian-finance", "revision-latest", "semantic-distractor", "exact-distractor", "semantic-retention"]`.
#### decomposition

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "long-10240"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 6, "F16": 6, "F17": 6, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 5, "F25": 5, "F26": 5, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "meridian-finance", "exact-distractor", "long-10240", "semantic-access", "long-10240"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 4}`, documents `["graph-team", "semantic-recovery", "long-10240", "graph-vendor", "exact-distractor", "long-10240", "semantic-access", "meridian-finance"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "long-10240", "exact-distractor", "meridian-schedule", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "semantic-distractor", "revision-latest", "semantic-access", "exact-distractor", "revision-old", "semantic-retention"]`.
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
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "long-10240", "exact-distractor", "meridian-schedule", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "semantic-distractor", "semantic-access", "exact-distractor", "semantic-retention", "revision-old"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["long-10240", "long-10240", "long-10240", "semantic-retention", "injection", "long-10240", "long-10240", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "revision-old", "revision-latest", "meridian-schedule", "exact-orbit", "graph-vendor", "semantic-distractor"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "exact-distractor", "meridian-finance"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "injection", "exact-distractor", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "exact-distractor", "revision-latest", "revision-old", "long-10240", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "meridian-finance", "semantic-recovery", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-access", "meridian-finance", "semantic-distractor", "revision-latest", "semantic-retention", "exact-distractor"]`.
#### corrective

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit"]`.
- `long-document-coverage`: facts 0.09375, fact ranks `{"F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest"]`.
- `graph-multihop`: facts 0.0, fact ranks `{}`, documents `["graph-team"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `[]`.
- `no-answer`: facts None, fact ranks `{}`, documents `[]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access"]`.
- `compositional-meridian`: facts 0.0, fact ranks `{}`, documents `[]`.
- `step-back-retention`: facts 0.0, fact ranks `{}`, documents `["graph-vendor"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `[]`.
#### adaptive

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "long-10240"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 6, "F16": 6, "F17": 6, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 5, "F25": 5, "F26": 5, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "meridian-finance", "long-10240", "long-10240", "semantic-access"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "long-10240", "long-10240", "semantic-recovery", "semantic-access", "meridian-schedule", "exact-distractor"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "long-10240", "exact-distractor", "meridian-schedule", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "semantic-distractor", "semantic-access", "exact-distractor", "semantic-retention", "revision-old"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["long-10240", "long-10240", "long-10240", "semantic-retention", "long-10240", "injection", "long-10240", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "revision-old", "revision-latest", "meridian-schedule", "exact-orbit", "graph-vendor", "semantic-distractor"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "meridian-finance", "injection"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "injection", "exact-distractor", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "exact-distractor", "revision-latest", "revision-old", "long-10240", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "meridian-finance", "semantic-recovery", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-access", "meridian-finance", "semantic-distractor", "revision-latest", "semantic-retention", "exact-distractor"]`.

The JSON companion retains every transformation prompt, original model output, validated rewrite, corrective grade, query/document vector digest, ranking, metric, and canonical evidence span for this repeat.

## Repeat 2

Transform calls: 1; cache hits: 64; failures: 1.
Corrective grade calls: 14; cache hits: 4; verdict accuracy: 0.500; label precision/recall: 0.500/0.674.
Adaptive optimal-route rate: 0.923.

| Method | Doc recall | Fact recall | Fact MRR | MRR | nDCG | Negative rejection | Source spans | Retrieval p50 ms | Est. uncached online p50 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | 1.000 | 0.857 | 0.410 | 0.950 | 0.963 | 0.000 | 1.000 | 8.369 | 8.369 |
| hyde | 1.000 | 0.786 | 0.399 | 0.933 | 0.950 | 0.000 | 1.000 | 8.353 | 1786.752 |
| fusion | 1.000 | 0.786 | 0.400 | 0.950 | 0.963 | 0.000 | 1.000 | 33.494 | 914.763 |
| decomposition | 1.000 | 0.857 | 0.416 | 1.000 | 0.988 | 0.000 | 1.000 | 25.086 | 761.176 |
| step_back | 1.000 | 0.857 | 0.410 | 0.950 | 0.963 | 0.000 | 1.000 | 16.790 | 603.841 |
| corrective | 0.700 | 0.214 | 0.214 | 0.800 | 0.723 | 1.000 | 1.000 | 8.798 | 481.275 |
| adaptive | 1.000 | 0.857 | 0.410 | 0.950 | 0.963 | 0.000 | 1.000 | 8.484 | 755.030 |

### Per-case retrieval audit

#### direct

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "multilingual"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F05": 7, "F06": 7, "F07": 7, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 5, "F16": 5, "F17": 5, "F18": 8, "F19": 8, "F20": 8, "F24": 6, "F25": 6, "F26": 6, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "long-10240", "meridian-finance", "long-10240", "semantic-access"]`.
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
- `long-document-coverage`: facts 0.71875, fact ranks `{"F01": 2, "F02": 2, "F03": 2, "F04": 2, "F05": 4, "F06": 4, "F07": 4, "F11": 6, "F12": 6, "F13": 6, "F14": 5, "F15": 5, "F16": 5, "F17": 5, "F21": 8, "F22": 8, "F23": 8, "F27": 3, "F28": 3, "F29": 3, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "exact-orbit", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "long-10240", "exact-orbit", "meridian-finance", "multilingual"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "semantic-recovery", "semantic-distractor", "long-10240", "long-10240", "meridian-finance", "semantic-access"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "meridian-schedule", "long-10240", "long-10240", "exact-distractor", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "revision-latest", "meridian-finance", "revision-old", "semantic-distractor", "semantic-access", "meridian-schedule", "semantic-retention"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["semantic-distractor", "long-10240", "long-10240", "semantic-retention", "long-10240", "injection", "long-10240", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "revision-old", "revision-latest", "meridian-finance", "exact-orbit", "semantic-distractor", "meridian-schedule", "graph-vendor"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "semantic-retention", "revision-old", "exact-distractor", "revision-latest", "meridian-finance"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "exact-distractor", "long-10240", "injection", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "revision-latest", "exact-distractor", "revision-old", "long-10240", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 3}`, documents `["meridian-finance", "graph-vendor", "semantic-retention", "semantic-recovery", "injection", "revision-old", "semantic-distractor", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-distractor", "semantic-access", "meridian-finance", "revision-latest", "semantic-retention", "exact-distractor"]`.
#### fusion

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "revision-old", "graph-vendor", "revision-latest", "meridian-schedule", "semantic-distractor"]`.
- `long-document-coverage`: facts 0.71875, fact ranks `{"F01": 2, "F02": 2, "F03": 2, "F04": 2, "F05": 5, "F06": 5, "F07": 5, "F11": 8, "F12": 8, "F13": 8, "F14": 7, "F15": 7, "F16": 7, "F17": 7, "F24": 4, "F25": 4, "F26": 4, "F27": 3, "F28": 3, "F29": 3, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "injection", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "meridian-finance", "long-10240", "exact-distractor", "long-10240", "semantic-access"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "semantic-recovery", "meridian-schedule", "semantic-access", "long-10240", "long-10240", "meridian-finance"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "exact-distractor", "long-10240", "meridian-schedule", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "exact-distractor", "semantic-access", "semantic-distractor", "revision-old", "semantic-retention"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["semantic-retention", "long-10240", "long-10240", "long-10240", "injection", "semantic-distractor", "meridian-schedule", "semantic-access"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "exact-orbit", "revision-latest", "graph-vendor", "revision-old", "semantic-distractor", "meridian-schedule"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "exact-distractor", "meridian-finance"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "exact-distractor", "long-10240", "long-10240", "injection", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "revision-latest", "exact-distractor", "long-10240", "long-10240", "semantic-distractor"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "semantic-recovery", "meridian-finance", "long-10240", "long-10240", "revision-old", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-access", "revision-latest", "meridian-finance", "exact-distractor", "semantic-distractor", "semantic-retention"]`.
#### decomposition

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "multilingual"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F05": 5, "F06": 5, "F07": 5, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 7, "F16": 7, "F17": 7, "F18": 8, "F19": 8, "F20": 8, "F24": 6, "F25": 6, "F26": 6, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "meridian-finance", "long-10240", "semantic-access", "long-10240"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 4}`, documents `["graph-team", "semantic-recovery", "long-10240", "graph-vendor", "exact-distractor", "long-10240", "semantic-access", "meridian-finance"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "exact-distractor", "long-10240", "meridian-schedule", "long-10240", "long-10240"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "semantic-distractor", "semantic-access", "exact-distractor", "revision-old", "semantic-retention"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["semantic-retention", "long-10240", "long-10240", "long-10240", "injection", "semantic-distractor", "long-10240", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "revision-old", "graph-vendor", "exact-orbit", "revision-latest", "graph-team", "semantic-access"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "meridian-finance", "injection"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "exact-distractor", "injection", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "revision-latest", "exact-orbit", "revision-old", "exact-distractor", "long-10240", "semantic-distractor"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 1}`, documents `["semantic-retention", "graph-vendor", "meridian-finance", "long-10240", "semantic-recovery", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "exact-distractor", "semantic-access", "revision-latest", "semantic-distractor", "semantic-recovery", "meridian-finance", "long-10240"]`.
#### step_back

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "multilingual"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F05": 7, "F06": 7, "F07": 7, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 5, "F16": 5, "F17": 5, "F18": 8, "F19": 8, "F20": 8, "F24": 6, "F25": 6, "F26": 6, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "long-10240", "meridian-finance", "long-10240", "semantic-access"]`.
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

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit"]`.
- `long-document-coverage`: facts 0.09375, fact ranks `{"F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest"]`.
- `graph-multihop`: facts 0.0, fact ranks `{}`, documents `["graph-team"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `[]`.
- `no-answer`: facts None, fact ranks `{}`, documents `[]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access"]`.
- `compositional-meridian`: facts 0.0, fact ranks `{}`, documents `[]`.
- `step-back-retention`: facts 0.0, fact ranks `{}`, documents `[]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `[]`.
#### adaptive

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "multilingual"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 3, "F02": 3, "F03": 3, "F04": 3, "F05": 5, "F06": 5, "F07": 5, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 7, "F16": 7, "F17": 7, "F18": 8, "F19": 8, "F20": 8, "F24": 6, "F25": 6, "F26": 6, "F27": 2, "F28": 2, "F29": 2, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "long-10240", "meridian-finance", "long-10240", "semantic-access"]`.
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

Transform calls: 1; cache hits: 64; failures: 1.
Corrective grade calls: 8; cache hits: 9; verdict accuracy: 0.588; label precision/recall: 0.529/0.765.
Adaptive optimal-route rate: 0.923.

| Method | Doc recall | Fact recall | Fact MRR | MRR | nDCG | Negative rejection | Source spans | Retrieval p50 ms | Est. uncached online p50 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | 1.000 | 0.857 | 0.414 | 0.950 | 0.963 | 0.000 | 1.000 | 8.393 | 8.393 |
| hyde | 1.000 | 0.786 | 0.411 | 0.933 | 0.950 | 0.000 | 1.000 | 8.450 | 1786.740 |
| fusion | 1.000 | 0.786 | 0.398 | 0.950 | 0.963 | 0.000 | 1.000 | 33.741 | 915.184 |
| decomposition | 1.000 | 0.857 | 0.420 | 1.000 | 0.988 | 0.000 | 1.000 | 25.317 | 761.481 |
| step_back | 1.000 | 0.857 | 0.414 | 0.950 | 0.963 | 0.000 | 1.000 | 16.976 | 604.138 |
| corrective | 0.700 | 0.762 | 0.355 | 0.800 | 0.723 | 1.000 | 1.000 | 8.745 | 733.188 |
| adaptive | 1.000 | 0.857 | 0.414 | 0.950 | 0.963 | 0.000 | 1.000 | 8.529 | 755.099 |

### Per-case retrieval audit

#### direct

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "multilingual"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 2, "F02": 2, "F03": 2, "F04": 2, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 5, "F16": 5, "F17": 5, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 6, "F25": 6, "F26": 6, "F27": 3, "F28": 3, "F29": 3, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "meridian-finance", "long-10240", "long-10240", "semantic-access"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "long-10240", "long-10240", "semantic-recovery", "semantic-access", "meridian-schedule", "exact-distractor"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "exact-distractor", "long-10240", "meridian-schedule", "long-10240", "revision-old"]`.
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
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "revision-latest", "meridian-finance", "revision-old", "semantic-distractor", "semantic-access", "meridian-schedule", "semantic-retention"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["semantic-distractor", "long-10240", "semantic-retention", "long-10240", "long-10240", "long-10240", "injection", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "revision-old", "revision-latest", "meridian-finance", "exact-orbit", "meridian-schedule", "semantic-distractor", "graph-vendor"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "semantic-retention", "revision-old", "exact-distractor", "revision-latest", "meridian-finance"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "long-10240", "exact-distractor", "injection", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "revision-latest", "exact-distractor", "revision-old", "long-10240", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 3}`, documents `["meridian-finance", "graph-vendor", "semantic-retention", "semantic-recovery", "injection", "revision-old", "semantic-distractor", "long-10240"]`.
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

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "multilingual"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 2, "F02": 2, "F03": 2, "F04": 2, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 6, "F16": 6, "F17": 6, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 5, "F25": 5, "F26": 5, "F27": 3, "F28": 3, "F29": 3, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
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

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "multilingual"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 2, "F02": 2, "F03": 2, "F04": 2, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 5, "F16": 5, "F17": 5, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 6, "F25": 6, "F26": 6, "F27": 3, "F28": 3, "F29": 3, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "meridian-finance", "long-10240", "long-10240", "semantic-access"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "long-10240", "long-10240", "semantic-recovery", "semantic-access", "meridian-schedule", "exact-distractor"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "exact-distractor", "long-10240", "meridian-schedule", "long-10240", "revision-old"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "exact-distractor", "semantic-distractor", "semantic-access", "semantic-retention", "revision-old"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["long-10240", "long-10240", "long-10240", "semantic-retention", "injection", "long-10240", "long-10240", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "revision-old", "revision-latest", "meridian-schedule", "exact-orbit", "graph-vendor", "semantic-distractor"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "exact-distractor", "meridian-finance"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "injection", "exact-distractor", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "exact-distractor", "revision-latest", "revision-old", "long-10240", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "meridian-finance", "semantic-recovery", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-access", "meridian-finance", "revision-latest", "semantic-distractor", "semantic-retention", "exact-distractor"]`.
#### corrective

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 2, "F02": 2, "F03": 2, "F04": 2, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 5, "F16": 5, "F17": 5, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 6, "F25": 6, "F26": 6, "F27": 3, "F28": 3, "F29": 3, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest"]`.
- `graph-multihop`: facts 0.0, fact ranks `{}`, documents `["graph-team"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `[]`.
- `no-answer`: facts None, fact ranks `{}`, documents `[]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access"]`.
- `compositional-meridian`: facts 0.0, fact ranks `{}`, documents `[]`.
- `step-back-retention`: facts 0.0, fact ranks `{}`, documents `["graph-vendor"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `[]`.
#### adaptive

- `exact-identifier`: facts 1.0, fact ranks `{"E01": 1}`, documents `["exact-orbit", "long-10240", "exact-distractor", "meridian-schedule", "revision-old", "revision-latest", "graph-vendor", "multilingual"]`.
- `long-document-coverage`: facts 0.8125, fact ranks `{"F01": 2, "F02": 2, "F03": 2, "F04": 2, "F11": 4, "F12": 4, "F13": 4, "F14": 4, "F15": 6, "F16": 6, "F17": 6, "F18": 7, "F19": 7, "F20": 7, "F21": 8, "F22": 8, "F23": 8, "F24": 5, "F25": 5, "F26": 5, "F27": 3, "F28": 3, "F29": 3, "F30": 1, "F31": 1, "F32": 1}`, documents `["long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `latest-revision`: facts 1.0, fact ranks `{"R02": 1}`, documents `["revision-latest", "revision-old", "meridian-schedule", "exact-distractor", "meridian-finance", "long-10240", "long-10240", "semantic-access"]`.
- `graph-multihop`: facts 1.0, fact ranks `{"G02": 2}`, documents `["graph-team", "graph-vendor", "long-10240", "long-10240", "semantic-recovery", "semantic-access", "meridian-schedule", "exact-distractor"]`.
- `multilingual`: facts 1.0, fact ranks `{"M01": 1}`, documents `["multilingual", "long-10240", "long-10240", "exact-distractor", "long-10240", "meridian-schedule", "long-10240", "revision-old"]`.
- `prompt-injection`: facts 1.0, fact ranks `{"S01": 1}`, documents `["injection", "meridian-finance", "revision-latest", "exact-distractor", "semantic-distractor", "semantic-access", "semantic-retention", "revision-old"]`.
- `scope-isolation`: facts None, fact ranks `{}`, documents `["long-10240", "long-10240", "long-10240", "semantic-retention", "injection", "long-10240", "long-10240", "long-10240"]`.
- `no-answer`: facts None, fact ranks `{}`, documents `["exact-distractor", "meridian-finance", "revision-old", "revision-latest", "meridian-schedule", "exact-orbit", "graph-vendor", "semantic-distractor"]`.
- `semantic-recovery-owner`: facts 1.0, fact ranks `{"Q01": 1}`, documents `["semantic-recovery", "semantic-distractor", "semantic-access", "revision-old", "semantic-retention", "revision-latest", "meridian-finance", "injection"]`.
- `semantic-badge-location`: facts 1.0, fact ranks `{"Q02": 1}`, documents `["semantic-access", "semantic-distractor", "injection", "exact-distractor", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `compositional-meridian`: facts 1.0, fact ranks `{"Q03": 2, "Q04": 1}`, documents `["meridian-finance", "meridian-schedule", "exact-orbit", "exact-distractor", "revision-latest", "revision-old", "long-10240", "long-10240"]`.
- `step-back-retention`: facts 1.0, fact ranks `{"Q05": 2}`, documents `["graph-vendor", "semantic-retention", "meridian-finance", "semantic-recovery", "long-10240", "long-10240", "long-10240", "long-10240"]`.
- `semantic-negative`: facts None, fact ranks `{}`, documents `["meridian-schedule", "semantic-recovery", "semantic-access", "meridian-finance", "revision-latest", "semantic-distractor", "semantic-retention", "exact-distractor"]`.

The JSON companion retains every transformation prompt, original model output, validated rewrite, corrective grade, query/document vector digest, ranking, metric, and canonical evidence span for this repeat.

## Decision

Retain direct hybrid as the default; route only methods that show a stable, case-specific benefit. No query-time method is production-ready from this synthetic suite.
