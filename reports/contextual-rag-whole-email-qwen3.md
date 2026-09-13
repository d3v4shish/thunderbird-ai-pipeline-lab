# Contextual RAG Evaluation

Paired, query-independent Contextual Retrieval ablation over identical structure-aware chunks. Raw passage, deterministic metadata context, per-chunk generated context, and one shared whole-email context are compared. Generated context is indexed by BM25 and embeddings but is never returned as answer evidence.

Top-K: 8. Production ready: False.
Per-chunk promotion recommended: False.
Whole-email promotion recommended: False.

## Models and exact method

- Context generator: `qwen3:8b` / `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`
- Embedding model: `qwen3-embedding:4b` / `df5bd2e3c74cd8d069d21dc038f1b359fcdc9458fce1c99bd43c9eb1518ff907`
- Per-chunk prompt: `contextual-retrieval-v2`; one complete document plus one target chunk per call.
- Whole-email prompt: `whole-email-context-v1`; one complete document and no target chunk per call.
- Both use temperature 0, seed 0, 16K context, 160 output tokens, and no user query.
- Accepted context was prepended to the search representation only. Retrieved evidence remained the unchanged canonical source span.

## Per-chunk context generation

| Chunks | Successful | Generated now | Cache hits | Failures | Entity grounding | Source spans | Model latency ms | Prompt tokens | Output tokens |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 23 | 23 | 23 | 0 | 0 | 1.000 | 1.000 | 17081.2 | 31540 | 866 |

## Whole-email context generation

| Emails | Successful | Generated now | Cache hits | Failures | Entity grounding | Source spans | Model latency ms | Prompt tokens | Output tokens |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 11 | 11 | 11 | 0 | 0 | 1.000 | 1.000 | 5923.6 | 5391 | 479 |

## Retrieval results

| Lane | Context | Retrieval | Embedding | Document recall | Fact recall | Document MRR | Fact MRR | nDCG | p50 ms | DB bytes | Indexed chars |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| raw-local-lexical | raw | lexical | deterministic-local-v1 | 1.000 | 0.737 | 0.929 | 0.267 | 0.923 | 0.245 | 212992 | 17561 |
| raw-local-hybrid | raw | hybrid | deterministic-local-v1 | 1.000 | 0.763 | 0.929 | 0.326 | 0.920 | 0.637 | 212992 | 17561 |
| metadata-local-lexical | metadata | lexical | deterministic-local-v1 | 1.000 | 0.737 | 0.929 | 0.267 | 0.923 | 0.290 | 225280 | 19643 |
| metadata-local-hybrid | metadata | hybrid | deterministic-local-v1 | 0.929 | 0.737 | 0.929 | 0.311 | 0.892 | 0.557 | 225280 | 19643 |
| generated-local-lexical | generated | lexical | deterministic-local-v1 | 1.000 | 0.684 | 0.929 | 0.260 | 0.936 | 0.351 | 229376 | 22017 |
| generated-local-hybrid | generated | hybrid | deterministic-local-v1 | 0.929 | 0.737 | 1.000 | 0.354 | 0.945 | 0.647 | 229376 | 22017 |
| whole-email-local-lexical | whole-email | lexical | deterministic-local-v1 | 1.000 | 0.763 | 0.929 | 0.280 | 0.926 | 0.350 | 229376 | 22146 |
| whole-email-local-hybrid | whole-email | hybrid | deterministic-local-v1 | 0.929 | 0.763 | 0.929 | 0.335 | 0.892 | 0.642 | 229376 | 22146 |
| raw-endpoint-dense | raw | dense | qwen3-embedding:4b | 1.000 | 0.737 | 1.000 | 0.341 | 0.971 | 134.470 | 958464 | 17561 |
| raw-endpoint-hybrid | raw | hybrid | qwen3-embedding:4b | 1.000 | 0.816 | 1.000 | 0.348 | 1.000 | 130.664 | 958464 | 17561 |
| metadata-endpoint-dense | metadata | dense | qwen3-embedding:4b | 1.000 | 0.842 | 1.000 | 0.362 | 0.989 | 134.396 | 970752 | 19643 |
| metadata-endpoint-hybrid | metadata | hybrid | qwen3-embedding:4b | 1.000 | 0.816 | 1.000 | 0.349 | 1.000 | 133.774 | 970752 | 19643 |
| generated-endpoint-dense | generated | dense | qwen3-embedding:4b | 1.000 | 0.684 | 1.000 | 0.359 | 0.989 | 131.464 | 978944 | 22017 |
| generated-endpoint-hybrid | generated | hybrid | qwen3-embedding:4b | 1.000 | 0.711 | 1.000 | 0.342 | 1.000 | 136.096 | 978944 | 22017 |
| whole-email-endpoint-dense | whole-email | dense | qwen3-embedding:4b | 1.000 | 0.842 | 1.000 | 0.373 | 0.989 | 135.573 | 978944 | 22146 |
| whole-email-endpoint-hybrid | whole-email | hybrid | qwen3-embedding:4b | 1.000 | 0.763 | 1.000 | 0.348 | 1.000 | 135.197 | 978944 | 22146 |

## Paired deltas: candidate minus each baseline

| Comparison | Retrieval family | Document recall | Fact recall | Document MRR | Fact MRR | nDCG | p50 ms | DB bytes | Indexed chars |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| generated-vs-raw | local-lexical | +0.000 | -0.053 | +0.000 | -0.007 | +0.013 | +0.106 | +16384 | +4456 |
| generated-vs-raw | local-hybrid | -0.071 | -0.026 | +0.071 | +0.029 | +0.025 | +0.010 | +16384 | +4456 |
| generated-vs-raw | endpoint-dense | +0.000 | -0.053 | +0.000 | +0.018 | +0.018 | -3.006 | +20480 | +4456 |
| generated-vs-raw | endpoint-hybrid | +0.000 | -0.105 | +0.000 | -0.006 | +0.000 | +5.432 | +20480 | +4456 |
| generated-vs-metadata | local-lexical | +0.000 | -0.053 | +0.000 | -0.007 | +0.013 | +0.060 | +4096 | +2374 |
| generated-vs-metadata | local-hybrid | +0.000 | +0.000 | +0.071 | +0.044 | +0.053 | +0.091 | +4096 | +2374 |
| generated-vs-metadata | endpoint-dense | +0.000 | -0.158 | +0.000 | -0.003 | +0.000 | -2.932 | +8192 | +2374 |
| generated-vs-metadata | endpoint-hybrid | +0.000 | -0.105 | +0.000 | -0.007 | +0.000 | +2.322 | +8192 | +2374 |
| whole-email-vs-raw | local-lexical | +0.000 | +0.026 | +0.000 | +0.013 | +0.003 | +0.105 | +16384 | +4585 |
| whole-email-vs-raw | local-hybrid | -0.071 | +0.000 | +0.000 | +0.010 | -0.028 | +0.005 | +16384 | +4585 |
| whole-email-vs-raw | endpoint-dense | +0.000 | +0.105 | +0.000 | +0.032 | +0.018 | +1.103 | +20480 | +4585 |
| whole-email-vs-raw | endpoint-hybrid | +0.000 | -0.053 | +0.000 | -0.000 | +0.000 | +4.533 | +20480 | +4585 |
| whole-email-vs-metadata | local-lexical | +0.000 | +0.026 | +0.000 | +0.013 | +0.003 | +0.060 | +4096 | +2503 |
| whole-email-vs-metadata | local-hybrid | +0.000 | +0.026 | +0.000 | +0.025 | +0.000 | +0.085 | +4096 | +2503 |
| whole-email-vs-metadata | endpoint-dense | +0.000 | +0.000 | +0.000 | +0.011 | +0.000 | +1.177 | +8192 | +2503 |
| whole-email-vs-metadata | endpoint-hybrid | +0.000 | -0.053 | +0.000 | -0.001 | +0.000 | +1.423 | +8192 | +2503 |

## Decision

Do not promote whole-email shared context from this run.

## Limitations

- The corpus is synthetic and small.
- The frozen queries mostly contain exact identifiers; realistic paraphrase and thread-anaphora cases are still needed.
- One live run does not establish variance or production readiness.
- Generated context is model output and may add unverified prose even when exact identifiers are grounded.
- Whole-email context is duplicated across every source passage and may crowd unique passage terms in Top-K retrieval.

## Whole-email context audit

### exact-orbit

- Status: `ok`; cache hit: `False`; complete source: `0-105`.
- Source span valid: `True`; latency: `564.5 ms`.
- Generated context: Project ORBIT-731 launch decision from North Annex on 2027-01-14 with a budget of USD 18,450.00.
- Error: none
- Raw model output:

```json
{"context": "Project ORBIT-731 launch decision from North Annex on 2027-01-14 with a budget of USD 18,450.00."}
```

### exact-distractor

- Status: `ok`; cache hit: `False`; complete source: `0-87`.
- Source span valid: `True`; latency: `546.1 ms`.
- Generated context: Project ORBIT-713, identified by ID exact-distractor, has a launch date of 2027-11-04 and is unrelated, using East Annex instead of the main facility.
- Error: none
- Raw model output:

```json
{"context": "Project ORBIT-713, identified by ID exact-distractor, has a launch date of 2027-11-04 and is unrelated, using East Annex instead of the main facility."}
```

### long-10240

- Status: `ok`; cache hit: `False`; complete source: `0-10240`.
- Source span valid: `True`; latency: `739.7 ms`.
- Generated context: A synthetic ledger document with multiple FACT entries, including values, dates, names, and identifiers, used for testing retrieval systems without real data.
- Error: none
- Raw model output:

```json
{"context": "A synthetic ledger document with multiple FACT entries, including values, dates, names, and identifiers, used for testing retrieval systems without real data."}
```

### revision-old

- Status: `ok`; cache hit: `False`; complete source: `0-81`.
- Source span valid: `True`; latency: `679.5 ms`.
- Generated context: Cedar decision revision 1, titled 'Cedar decision revision 1', with ID 'revision-old', supersedes Revision one for CEDAR-210, deployment date set for 2027-08-12.
- Error: none
- Raw model output:

```json
{"context": "Cedar decision revision 1, titled 'Cedar decision revision 1', with ID 'revision-old', supersedes Revision one for CEDAR-210, deployment date set for 2027-08-12."}
```

### revision-latest

- Status: `ok`; cache hit: `False`; complete source: `0-99`.
- Source span valid: `True`; latency: `537.8 ms`.
- Generated context: Cedar decision revision 2, titled 'Cedar decision revision 2', is the latest approved decision for CEDAR-210 with deployment date 2027-09-21.
- Error: none
- Raw model output:

```json
{"context": "Cedar decision revision 2, titled 'Cedar decision revision 2', is the latest approved decision for CEDAR-210 with deployment date 2027-09-21."}
```

### graph-team

- Status: `ok`; cache hit: `False`; complete source: `0-93`.
- Source span valid: `True`; latency: `366.5 ms`.
- Generated context: Project Atlas is led by Priya Das, who owns Team Aurora, as documented in the Atlas ownership fact.
- Error: none
- Raw model output:

```json
{"context": "Project Atlas is led by Priya Das, who owns Team Aurora, as documented in the Atlas ownership fact."}
```

### graph-vendor

- Status: `ok`; cache hit: `False`; complete source: `0-75`.
- Source span valid: `True`; latency: `399.3 ms`.
- Generated context: Project Atlas depends on Kestrel Works as its supplier, identified in the dependency graph under the id 'graph-vendor'.
- Error: none
- Raw model output:

```json
{"context": "Project Atlas depends on Kestrel Works as its supplier, identified in the dependency graph under the id 'graph-vendor'."}
```

### multilingual

- Status: `ok`; cache hit: `False`; complete source: `0-90`.
- Source span valid: `True`; latency: `487.0 ms`.
- Generated context: The project SOLAR-808 meeting is scheduled for October 6, 2027, in Madrid, as per the bilingüe decision document M01.
- Error: none
- Raw model output:

```json
{"context": "The project SOLAR-808 meeting is scheduled for October 6, 2027, in Madrid, as per the bilingüe decision document M01."}
```

### injection

- Status: `ok`; cache hit: `False`; complete source: `0-130`.
- Source span valid: `True`; latency: `448.4 ms`.
- Generated context: Untrusted embedded instruction document with ID 'injection' in the security category, mentioning SECRETCODE-999 and a quarantined safe_status.
- Error: none
- Raw model output:

```json
{"context": "Untrusted embedded instruction document with ID 'injection' in the security category, mentioning SECRETCODE-999 and a quarantined safe_status."}
```

### other-tenant-secret

- Status: `ok`; cache hit: `False`; complete source: `0-77`.
- Source span valid: `True`; latency: `499.8 ms`.
- Generated context: The email titled 'Isolation sentinel' contains a private document with the ID 'other-tenant-secret' and the isolated value 'VAULT-440' belonging exclusively to tenant-beta.
- Error: none
- Raw model output:

```json
{"context": "The email titled 'Isolation sentinel' contains a private document with the ID 'other-tenant-secret' and the isolated value 'VAULT-440' belonging exclusively to tenant-beta."}
```

### contextual-thread

- Status: `ok`; cache hit: `False`; complete source: `0-3976`.
- Source span valid: `True`; latency: `655.1 ms`.
- Generated context: The working group reviewed packaging, staffing, and transport checks for Project BOREALIS-204 without altering approved commercial terms, leading to a final approval of USD 6,400.00 settlement value.
- Error: none
- Raw model output:

```json
{"context": "The working group reviewed packaging, staffing, and transport checks for Project BOREALIS-204 without altering approved commercial terms, leading to a final approval of USD 6,400.00 settlement value."}
```

## Per-chunk generated-context audit

### exact-orbit / tenant-alpha/primary/exact-orbit:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-105`.
- Source span valid: `True`; latency: `2018.4 ms`.
- Generated context: Document details the launch decision for Project ORBIT-731, specifying its launch date, location, and budget from the Orbit launch decision record.
- Error: none
- Raw model output:

```json
{"context": "Document details the launch decision for Project ORBIT-731, specifying its launch date, location, and budget from the Orbit launch decision record."}
```

### exact-distractor / tenant-alpha/primary/exact-distractor:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-87`.
- Source span valid: `True`; latency: `527.2 ms`.
- Generated context: The document discusses Project ORBIT-713, a separate project from the main subject, using East Annex with a launch date of 2027-11-04.
- Error: none
- Raw model output:

```json
{"context": "The document discusses Project ORBIT-713, a separate project from the main subject, using East Annex with a launch date of 2027-11-04."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-1194`.
- Source span valid: `True`; latency: `737.5 ms`.
- Generated context: A synthetic operations ledger document containing factual entries with required values, used for testing retrieval systems without real data.
- Error: none
- Raw model output:

```json
{"context": "A synthetic operations ledger document containing factual entries with required values, used for testing retrieval systems without real data."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:1

- Status: `ok`; cache hit: `False`; source: `1016-2215`.
- Source span valid: `True`; latency: `806.1 ms`.
- Generated context: The document is a synthetic operations ledger, and this chunk contains a fact about the North Annex as a required value in a synthetic context exercise.
- Error: none
- Raw model output:

```json
{"context": "The document is a synthetic operations ledger, and this chunk contains a fact about the North Annex as a required value in a synthetic context exercise."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:2

- Status: `ok`; cache hit: `False`; source: `2036-3222`.
- Source span valid: `True`; latency: `812.4 ms`.
- Generated context: The document is a synthetic operations ledger, and this chunk contains a fact about Omar Shah as part of the ledger's structured data.
- Error: none
- Raw model output:

```json
{"context": "The document is a synthetic operations ledger, and this chunk contains a fact about Omar Shah as part of the ledger's structured data."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:3

- Status: `ok`; cache hit: `False`; source: `3044-4243`.
- Source span valid: `True`; latency: `874.9 ms`.
- Generated context: The document is a synthetic operations ledger, and this chunk contains FACT F10 to F14 with specific required values and repetitive context about bounded retrieval.
- Error: none
- Raw model output:

```json
{"context": "The document is a synthetic operations ledger, and this chunk contains FACT F10 to F14 with specific required values and repetitive context about bounded retrieval."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:4

- Status: `ok`; cache hit: `False`; source: `4064-5260`.
- Source span valid: `True`; latency: `1021.6 ms`.
- Generated context: The document is a synthetic operations ledger, and this chunk contains FACT F13 with the required value Mira Chen, part of the ledger's structured data entries.
- Error: none
- Raw model output:

```json
{"context": "The document is a synthetic operations ledger, and this chunk contains FACT F13 with the required value Mira Chen, part of the ledger's structured data entries."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:5

- Status: `ok`; cache hit: `False`; source: `5081-6280`.
- Source span valid: `True`; latency: `1068.0 ms`.
- Generated context: The document is a synthetic operations ledger detailing various facts with required values, and this chunk contains entries from Section 16 to Section 20, including financial figures and identifiers.
- Error: none
- Raw model output:

```json
{"context": "The document is a synthetic operations ledger detailing various facts with required values, and this chunk contains entries from Section 16 to Section 20, including financial figures and identifiers."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:6

- Status: `ok`; cache hit: `False`; source: `6101-7299`.
- Source span valid: `True`; latency: `866.7 ms`.
- Generated context: The document is a synthetic operations ledger, and this chunk contains factual entries related to financial values, dates, and personnel names within the ledger's structured format.
- Error: none
- Raw model output:

```json
{"context": "The document is a synthetic operations ledger, and this chunk contains factual entries related to financial values, dates, and personnel names within the ledger's structured format."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:7

- Status: `ok`; cache hit: `False`; source: `7120-8320`.
- Source span valid: `True`; latency: `778.5 ms`.
- Generated context: The document is a synthetic operations ledger, and this chunk contains facts about financial values and locations used for testing retrieval systems.
- Error: none
- Raw model output:

```json
{"context": "The document is a synthetic operations ledger, and this chunk contains facts about financial values and locations used for testing retrieval systems."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:8

- Status: `ok`; cache hit: `False`; source: `8141-9336`.
- Source span valid: `True`; latency: `898.0 ms`.
- Generated context: The parent document is a synthetic operations ledger, and this chunk contains FACT F30 with the required value 'Silver Pine' as part of the ledger's structured data.
- Error: none
- Raw model output:

```json
{"context": "The parent document is a synthetic operations ledger, and this chunk contains FACT F30 with the required value 'Silver Pine' as part of the ledger's structured data."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:9

- Status: `ok`; cache hit: `False`; source: `9157-10240`.
- Source span valid: `True`; latency: `955.2 ms`.
- Generated context: The document is a synthetic operations ledger, and this chunk contains facts about synthetic contexts used for bounded retrieval exercises, including entries like VECTOR-963, Silver Pine, and Keiko Tanaka.
- Error: none
- Raw model output:

```json
{"context": "The document is a synthetic operations ledger, and this chunk contains facts about synthetic contexts used for bounded retrieval exercises, including entries like VECTOR-963, Silver Pine, and Keiko Tanaka."}
```

### revision-old / tenant-alpha/primary/revision-old:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-81`.
- Source span valid: `True`; latency: `466.0 ms`.
- Generated context: Cedar decision revision 1 details deployment date and superseded status of CEDAR-210 revision one.
- Error: none
- Raw model output:

```json
{"context": "Cedar decision revision 1 details deployment date and superseded status of CEDAR-210 revision one."}
```

### revision-latest / tenant-alpha/primary/revision-latest:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-99`.
- Source span valid: `True`; latency: `469.1 ms`.
- Generated context: The document details the latest approved decision for CEDAR-210, specifying its deployment date as 2027-09-21.
- Error: none
- Raw model output:

```json
{"context": "The document details the latest approved decision for CEDAR-210, specifying its deployment date as 2027-09-21."}
```

### graph-team / tenant-alpha/primary/graph-team:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-93`.
- Source span valid: `True`; latency: `354.9 ms`.
- Generated context: Project Atlas ownership details: Priya Das leads Team Aurora, which works on Project Atlas.
- Error: none
- Raw model output:

```json
{"context": "Project Atlas ownership details: Priya Das leads Team Aurora, which works on Project Atlas."}
```

### graph-vendor / tenant-alpha/primary/graph-vendor:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-75`.
- Source span valid: `True`; latency: `319.9 ms`.
- Generated context: Project Atlas's dependency on Kestrel Works is noted in the Atlas supplier document.
- Error: none
- Raw model output:

```json
{"context": "Project Atlas's dependency on Kestrel Works is noted in the Atlas supplier document."}
```

### multilingual / tenant-alpha/primary/multilingual:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-90`.
- Source span valid: `True`; latency: `466.4 ms`.
- Generated context: The document details a bilingual decision regarding the SOLAR-808 project meeting scheduled for 2027-10-06 in Madrid.
- Error: none
- Raw model output:

```json
{"context": "The document details a bilingual decision regarding the SOLAR-808 project meeting scheduled for 2027-10-06 in Madrid."}
```

### injection / tenant-alpha/primary/injection:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-130`.
- Source span valid: `True`; latency: `533.5 ms`.
- Generated context: A security document titled 'Untrusted embedded instruction' contains a chunk with an untrusted command to call a tool and reveal SECRETCODE-999, indicating a quarantined safe status.
- Error: none
- Raw model output:

```json
{"context": "A security document titled 'Untrusted embedded instruction' contains a chunk with an untrusted command to call a tool and reveal SECRETCODE-999, indicating a quarantined safe status."}
```

### other-tenant-secret / tenant-beta/private/other-tenant-secret:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-77`.
- Source span valid: `True`; latency: `454.5 ms`.
- Generated context: The document 'Isolation sentinel' contains a secret value VAULT-440 specific to tenant-beta, identified as FACT X01.
- Error: none
- Raw model output:

```json
{"context": "The document 'Isolation sentinel' contains a secret value VAULT-440 specific to tenant-beta, identified as FACT X01."}
```

### contextual-thread / tenant-alpha/primary/contextual-thread:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-1196`.
- Source span valid: `True`; latency: `655.4 ms`.
- Generated context: The document discusses Project BOREALIS-204, a polar sensor shipment, and the working group's review of packaging, staffing, and transport checks for the operations committee funding decision.
- Error: none
- Raw model output:

```json
{"context": "The document discusses Project BOREALIS-204, a polar sensor shipment, and the working group's review of packaging, staffing, and transport checks for the operations committee funding decision."}
```

### contextual-thread / tenant-alpha/primary/contextual-thread:chunk:1

- Status: `ok`; cache hit: `False`; source: `1017-2211`.
- Source span valid: `True`; latency: `677.7 ms`.
- Generated context: The chunk discusses the working group's review of packaging, staffing, and transport checks for Project BOREALIS-204 without altering commercial terms, part of the operations committee funding decision.
- Error: none
- Raw model output:

```json
{"context": "The chunk discusses the working group's review of packaging, staffing, and transport checks for Project BOREALIS-204 without altering commercial terms, part of the operations committee funding decision."}
```

### contextual-thread / tenant-alpha/primary/contextual-thread:chunk:2

- Status: `ok`; cache hit: `False`; source: `2032-3224`.
- Source span valid: `True`; latency: `638.3 ms`.
- Generated context: The chunk discusses the working group's review of packaging, staffing, and transport checks for Project BOREALIS-204 without altering commercial terms, part of the operations committee funding decision.
- Error: none
- Raw model output:

```json
{"context": "The chunk discusses the working group's review of packaging, staffing, and transport checks for Project BOREALIS-204 without altering commercial terms, part of the operations committee funding decision."}
```

### contextual-thread / tenant-alpha/primary/contextual-thread:chunk:3

- Status: `ok`; cache hit: `False`; source: `3045-3976`.
- Source span valid: `True`; latency: `681.2 ms`.
- Generated context: The chunk details the working group's review of packaging, staffing, and transport checks for Project BOREALIS-204, with final approval of a USD 6,400.00 settlement.
- Error: none
- Raw model output:

```json
{"context": "The chunk details the working group's review of packaging, staffing, and transport checks for Project BOREALIS-204, with final approval of a USD 6,400.00 settlement."}
```

## Per-case retrieval audit

| Lane | Case | Retrieved documents | Matched facts | Evidence spans |
|---|---|---|---|---|
| raw-local-lexical | exact-identifier | exact-orbit, exact-distractor, revision-latest, revision-old, contextual-thread, long-10240 | 1/1 | doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#0-1196; doc://long-10240#0-1194; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211 |
| raw-local-lexical | long-document-coverage | exact-orbit, long-10240 | 23/32 | doc://exact-orbit#0-105; doc://long-10240#9157-10240; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#4064-5260; doc://long-10240#3044-4243; doc://long-10240#5081-6280 |
| raw-local-lexical | latest-revision | revision-latest, revision-old, contextual-thread, exact-distractor, exact-orbit | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#0-1196; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://contextual-thread#3045-3976; doc://exact-distractor#0-87; doc://exact-orbit#0-105 |
| raw-local-lexical | graph-multihop | graph-team, graph-vendor, contextual-thread, revision-latest, revision-old | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://contextual-thread#0-1196; doc://revision-latest#0-99; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://contextual-thread#3045-3976; doc://revision-old#0-81 |
| raw-local-lexical | multilingual | multilingual | 1/1 | doc://multilingual#0-90 |
| raw-local-lexical | prompt-injection | injection, contextual-thread, revision-latest, revision-old, exact-distractor | 1/1 | doc://injection#0-130; doc://contextual-thread#0-1196; doc://revision-latest#0-99; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://contextual-thread#3045-3976; doc://revision-old#0-81; doc://exact-distractor#0-87 |
| raw-local-lexical | scope-isolation | long-10240 | 0/0 | doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#0-1194; doc://long-10240#3044-4243; doc://long-10240#5081-6280; doc://long-10240#1016-2215; doc://long-10240#2036-3222; doc://long-10240#7120-8320 |
| raw-local-lexical | no-answer | revision-latest, contextual-thread, revision-old, exact-distractor, exact-orbit | 0/0 | doc://revision-latest#0-99; doc://contextual-thread#0-1196; doc://revision-old#0-81; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://contextual-thread#3045-3976; doc://exact-distractor#0-87; doc://exact-orbit#0-105 |
| raw-local-lexical | contextual-late-reference | contextual-thread, graph-vendor, exact-distractor, graph-team, exact-orbit, long-10240 | 0/1 | doc://contextual-thread#0-1196; doc://graph-vendor#0-75; doc://exact-distractor#0-87; doc://graph-team#0-93; doc://exact-orbit#0-105; doc://long-10240#1016-2215 |
| raw-local-hybrid | exact-identifier | exact-orbit, long-10240, revision-latest, revision-old, contextual-thread, exact-distractor | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#0-1196; doc://exact-distractor#0-87; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224 |
| raw-local-hybrid | long-document-coverage | long-10240, exact-orbit | 24/32 | doc://long-10240#0-1194; doc://long-10240#9157-10240; doc://long-10240#6101-7299; doc://exact-orbit#0-105; doc://long-10240#5081-6280; doc://long-10240#8141-9336; doc://long-10240#3044-4243; doc://long-10240#2036-3222 |
| raw-local-hybrid | latest-revision | revision-latest, revision-old, contextual-thread, exact-distractor, long-10240 | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#0-1196; doc://contextual-thread#2032-3224; doc://contextual-thread#3045-3976; doc://contextual-thread#1017-2211; doc://exact-distractor#0-87; doc://long-10240#3044-4243 |
| raw-local-hybrid | graph-multihop | graph-team, revision-latest, contextual-thread, long-10240, graph-vendor | 1/1 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://contextual-thread#0-1196; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://long-10240#9157-10240; doc://graph-vendor#0-75 |
| raw-local-hybrid | multilingual | multilingual, exact-orbit, long-10240, injection | 1/1 | doc://multilingual#0-90; doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://injection#0-130; doc://long-10240#6101-7299; doc://long-10240#7120-8320; doc://long-10240#3044-4243; doc://long-10240#2036-3222 |
| raw-local-hybrid | prompt-injection | contextual-thread, injection, revision-latest, exact-distractor, revision-old | 1/1 | doc://contextual-thread#0-1196; doc://injection#0-130; doc://contextual-thread#2032-3224; doc://contextual-thread#3045-3976; doc://revision-latest#0-99; doc://contextual-thread#1017-2211; doc://exact-distractor#0-87; doc://revision-old#0-81 |
| raw-local-hybrid | scope-isolation | long-10240, injection | 0/0 | doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://long-10240#0-1194; doc://injection#0-130; doc://long-10240#3044-4243; doc://long-10240#7120-8320; doc://long-10240#1016-2215 |
| raw-local-hybrid | no-answer | contextual-thread, revision-latest, revision-old, exact-distractor, exact-orbit | 0/0 | doc://contextual-thread#0-1196; doc://contextual-thread#2032-3224; doc://revision-latest#0-99; doc://contextual-thread#3045-3976; doc://contextual-thread#1017-2211; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105 |
| raw-local-hybrid | contextual-late-reference | contextual-thread, graph-team, exact-distractor, long-10240, exact-orbit, graph-vendor, multilingual | 0/1 | doc://contextual-thread#0-1196; doc://graph-team#0-93; doc://exact-distractor#0-87; doc://long-10240#1016-2215; doc://exact-orbit#0-105; doc://graph-vendor#0-75; doc://multilingual#0-90; doc://long-10240#9157-10240 |
| metadata-local-lexical | exact-identifier | exact-orbit, exact-distractor, revision-latest, revision-old, contextual-thread, long-10240 | 1/1 | doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#0-1196; doc://long-10240#0-1194; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211 |
| metadata-local-lexical | long-document-coverage | exact-orbit, long-10240 | 23/32 | doc://exact-orbit#0-105; doc://long-10240#9157-10240; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#4064-5260; doc://long-10240#3044-4243; doc://long-10240#5081-6280 |
| metadata-local-lexical | latest-revision | revision-latest, revision-old, contextual-thread, exact-distractor, exact-orbit | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#0-1196; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://contextual-thread#3045-3976; doc://exact-distractor#0-87; doc://exact-orbit#0-105 |
| metadata-local-lexical | graph-multihop | graph-team, graph-vendor, contextual-thread, revision-latest, exact-distractor | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://contextual-thread#0-1196; doc://revision-latest#0-99; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://contextual-thread#3045-3976; doc://exact-distractor#0-87 |
| metadata-local-lexical | multilingual | multilingual | 1/1 | doc://multilingual#0-90 |
| metadata-local-lexical | prompt-injection | injection, contextual-thread, revision-latest, exact-distractor, revision-old | 1/1 | doc://injection#0-130; doc://contextual-thread#0-1196; doc://revision-latest#0-99; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://contextual-thread#3045-3976; doc://exact-distractor#0-87; doc://revision-old#0-81 |
| metadata-local-lexical | scope-isolation | long-10240 | 0/0 | doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#3044-4243; doc://long-10240#5081-6280; doc://long-10240#1016-2215; doc://long-10240#2036-3222; doc://long-10240#7120-8320 |
| metadata-local-lexical | no-answer | revision-latest, contextual-thread, revision-old, exact-distractor, exact-orbit | 0/0 | doc://revision-latest#0-99; doc://contextual-thread#0-1196; doc://revision-old#0-81; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://contextual-thread#3045-3976; doc://exact-distractor#0-87; doc://exact-orbit#0-105 |
| metadata-local-lexical | contextual-late-reference | contextual-thread, graph-vendor, long-10240, exact-distractor, graph-team, exact-orbit | 0/1 | doc://contextual-thread#0-1196; doc://graph-vendor#0-75; doc://long-10240#1016-2215; doc://exact-distractor#0-87; doc://graph-team#0-93; doc://exact-orbit#0-105 |
| metadata-local-hybrid | exact-identifier | exact-orbit, long-10240, exact-distractor, revision-latest, contextual-thread, revision-old | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://contextual-thread#0-1196; doc://contextual-thread#3045-3976; doc://revision-old#0-81; doc://contextual-thread#2032-3224 |
| metadata-local-hybrid | long-document-coverage | long-10240, exact-orbit | 24/32 | doc://long-10240#9157-10240; doc://long-10240#6101-7299; doc://long-10240#0-1194; doc://long-10240#5081-6280; doc://exact-orbit#0-105; doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://long-10240#2036-3222 |
| metadata-local-hybrid | latest-revision | revision-latest, revision-old, contextual-thread, exact-distractor, exact-orbit | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#0-1196; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://exact-distractor#0-87; doc://exact-orbit#0-105 |
| metadata-local-hybrid | graph-multihop | graph-team, contextual-thread, exact-distractor, revision-latest, long-10240 | 0/1 | doc://graph-team#0-93; doc://contextual-thread#0-1196; doc://contextual-thread#3045-3976; doc://contextual-thread#1017-2211; doc://exact-distractor#0-87; doc://contextual-thread#2032-3224; doc://revision-latest#0-99; doc://long-10240#0-1194 |
| metadata-local-hybrid | multilingual | multilingual, exact-orbit, injection, long-10240 | 1/1 | doc://multilingual#0-90; doc://exact-orbit#0-105; doc://injection#0-130; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#7120-8320; doc://long-10240#3044-4243; doc://long-10240#2036-3222 |
| metadata-local-hybrid | prompt-injection | contextual-thread, injection, revision-latest, exact-distractor, revision-old | 1/1 | doc://contextual-thread#0-1196; doc://injection#0-130; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224; doc://revision-latest#0-99; doc://contextual-thread#1017-2211; doc://exact-distractor#0-87; doc://revision-old#0-81 |
| metadata-local-hybrid | scope-isolation | long-10240, injection | 0/0 | doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://long-10240#0-1194; doc://long-10240#3044-4243; doc://injection#0-130; doc://long-10240#1016-2215; doc://long-10240#7120-8320 |
| metadata-local-hybrid | no-answer | contextual-thread, revision-latest, exact-distractor, exact-orbit, revision-old | 0/0 | doc://contextual-thread#0-1196; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224; doc://revision-latest#0-99; doc://contextual-thread#1017-2211; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://revision-old#0-81 |
| metadata-local-hybrid | contextual-late-reference | contextual-thread, long-10240, graph-team, exact-distractor, graph-vendor, exact-orbit, multilingual | 0/1 | doc://contextual-thread#0-1196; doc://long-10240#1016-2215; doc://graph-team#0-93; doc://exact-distractor#0-87; doc://graph-vendor#0-75; doc://exact-orbit#0-105; doc://multilingual#0-90; doc://long-10240#9157-10240 |
| generated-local-lexical | exact-identifier | exact-orbit, exact-distractor, long-10240, revision-old, revision-latest, multilingual, contextual-thread | 1/1 | doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://long-10240#0-1194; doc://revision-old#0-81; doc://revision-latest#0-99; doc://multilingual#0-90; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224 |
| generated-local-lexical | long-document-coverage | exact-orbit, long-10240, exact-distractor | 20/32 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://long-10240#9157-10240; doc://exact-distractor#0-87; doc://long-10240#5081-6280; doc://long-10240#3044-4243; doc://long-10240#4064-5260; doc://long-10240#8141-9336 |
| generated-local-lexical | latest-revision | revision-latest, revision-old, exact-orbit, exact-distractor, contextual-thread | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://contextual-thread#3045-3976; doc://contextual-thread#0-1196 |
| generated-local-lexical | graph-multihop | graph-team, graph-vendor, long-10240 | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://long-10240#4064-5260; doc://long-10240#8141-9336; doc://long-10240#6101-7299; doc://long-10240#1016-2215; doc://long-10240#2036-3222; doc://long-10240#3044-4243 |
| generated-local-lexical | multilingual | multilingual | 1/1 | doc://multilingual#0-90 |
| generated-local-lexical | prompt-injection | injection, revision-old, exact-distractor, contextual-thread, long-10240 | 1/1 | doc://injection#0-130; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://contextual-thread#0-1196; doc://long-10240#2036-3222 |
| generated-local-lexical | scope-isolation | graph-vendor, multilingual, long-10240 | 0/0 | doc://graph-vendor#0-75; doc://multilingual#0-90; doc://long-10240#1016-2215; doc://long-10240#3044-4243; doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://long-10240#0-1194 |
| generated-local-lexical | no-answer | contextual-thread, revision-latest, exact-orbit, graph-team, exact-distractor | 0/0 | doc://contextual-thread#0-1196; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://revision-latest#0-99; doc://exact-orbit#0-105; doc://graph-team#0-93; doc://exact-distractor#0-87 |
| generated-local-lexical | contextual-late-reference | contextual-thread, long-10240, graph-team, exact-distractor, graph-vendor | 1/1 | doc://contextual-thread#0-1196; doc://contextual-thread#1017-2211; doc://contextual-thread#2032-3224; doc://contextual-thread#3045-3976; doc://long-10240#1016-2215; doc://graph-team#0-93; doc://exact-distractor#0-87; doc://graph-vendor#0-75 |
| generated-local-hybrid | exact-identifier | exact-orbit, long-10240, exact-distractor, revision-latest, revision-old, contextual-thread | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#2032-3224; doc://contextual-thread#3045-3976; doc://contextual-thread#0-1196 |
| generated-local-hybrid | long-document-coverage | long-10240, exact-orbit | 23/32 | doc://long-10240#0-1194; doc://long-10240#5081-6280; doc://long-10240#9157-10240; doc://long-10240#3044-4243; doc://long-10240#1016-2215; doc://exact-orbit#0-105; doc://long-10240#4064-5260; doc://long-10240#8141-9336 |
| generated-local-hybrid | latest-revision | revision-latest, revision-old, contextual-thread, exact-orbit, exact-distractor | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#2032-3224; doc://contextual-thread#0-1196; doc://contextual-thread#1017-2211; doc://exact-orbit#0-105; doc://contextual-thread#3045-3976; doc://exact-distractor#0-87 |
| generated-local-hybrid | graph-multihop | graph-team, long-10240, contextual-thread | 0/1 | doc://graph-team#0-93; doc://long-10240#4064-5260; doc://long-10240#8141-9336; doc://long-10240#9157-10240; doc://contextual-thread#0-1196; doc://long-10240#6101-7299; doc://long-10240#3044-4243; doc://long-10240#2036-3222 |
| generated-local-hybrid | multilingual | multilingual, exact-orbit, long-10240 | 1/1 | doc://multilingual#0-90; doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#3044-4243; doc://long-10240#7120-8320; doc://long-10240#1016-2215; doc://long-10240#5081-6280 |
| generated-local-hybrid | prompt-injection | injection, contextual-thread, revision-old, exact-distractor, revision-latest | 1/1 | doc://injection#0-130; doc://contextual-thread#2032-3224; doc://contextual-thread#3045-3976; doc://contextual-thread#0-1196; doc://revision-old#0-81; doc://contextual-thread#1017-2211; doc://exact-distractor#0-87; doc://revision-latest#0-99 |
| generated-local-hybrid | scope-isolation | graph-vendor, long-10240, injection | 0/0 | doc://graph-vendor#0-75; doc://long-10240#1016-2215; doc://long-10240#5081-6280; doc://long-10240#6101-7299; doc://injection#0-130; doc://long-10240#3044-4243; doc://long-10240#7120-8320; doc://long-10240#8141-9336 |
| generated-local-hybrid | no-answer | contextual-thread, revision-latest, exact-orbit, exact-distractor, multilingual | 0/0 | doc://contextual-thread#0-1196; doc://contextual-thread#2032-3224; doc://contextual-thread#3045-3976; doc://contextual-thread#1017-2211; doc://revision-latest#0-99; doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://multilingual#0-90 |
| generated-local-hybrid | contextual-late-reference | contextual-thread, graph-team, multilingual, exact-distractor, long-10240 | 1/1 | doc://contextual-thread#0-1196; doc://graph-team#0-93; doc://multilingual#0-90; doc://exact-distractor#0-87; doc://contextual-thread#3045-3976; doc://long-10240#1016-2215; doc://contextual-thread#1017-2211; doc://contextual-thread#2032-3224 |
| whole-email-local-lexical | exact-identifier | exact-orbit, exact-distractor, revision-latest, revision-old, long-10240, multilingual, graph-team, contextual-thread | 1/1 | doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://revision-old#0-81; doc://long-10240#0-1194; doc://multilingual#0-90; doc://graph-team#0-93; doc://contextual-thread#0-1196 |
| whole-email-local-lexical | long-document-coverage | exact-orbit, long-10240 | 23/32 | doc://exact-orbit#0-105; doc://long-10240#9157-10240; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#4064-5260; doc://long-10240#3044-4243; doc://long-10240#5081-6280 |
| whole-email-local-lexical | latest-revision | revision-latest, revision-old, exact-distractor, contextual-thread, exact-orbit | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://contextual-thread#0-1196; doc://exact-orbit#0-105; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://contextual-thread#3045-3976 |
| whole-email-local-lexical | graph-multihop | graph-team, graph-vendor, exact-distractor, revision-latest, multilingual, contextual-thread, exact-orbit, revision-old | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://multilingual#0-90; doc://contextual-thread#0-1196; doc://exact-orbit#0-105; doc://revision-old#0-81 |
| whole-email-local-lexical | multilingual | multilingual | 1/1 | doc://multilingual#0-90 |
| whole-email-local-lexical | prompt-injection | injection, exact-distractor, exact-orbit, contextual-thread, revision-latest, multilingual, graph-team | 1/1 | doc://injection#0-130; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://contextual-thread#0-1196; doc://revision-latest#0-99; doc://multilingual#0-90; doc://graph-team#0-93; doc://contextual-thread#3045-3976 |
| whole-email-local-lexical | scope-isolation | graph-vendor, graph-team, multilingual, injection, long-10240 | 0/0 | doc://graph-vendor#0-75; doc://graph-team#0-93; doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#0-1194; doc://long-10240#3044-4243 |
| whole-email-local-lexical | no-answer | contextual-thread, revision-latest, exact-distractor, graph-team, multilingual | 0/0 | doc://contextual-thread#0-1196; doc://revision-latest#0-99; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://exact-distractor#0-87; doc://graph-team#0-93; doc://multilingual#0-90 |
| whole-email-local-lexical | contextual-late-reference | contextual-thread, long-10240, graph-vendor, graph-team, exact-orbit | 1/1 | doc://contextual-thread#0-1196; doc://contextual-thread#3045-3976; doc://contextual-thread#1017-2211; doc://contextual-thread#2032-3224; doc://long-10240#1016-2215; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://exact-orbit#0-105 |
| whole-email-local-hybrid | exact-identifier | exact-orbit, long-10240, revision-latest, exact-distractor, contextual-thread, revision-old | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://contextual-thread#0-1196; doc://revision-old#0-81; doc://contextual-thread#2032-3224; doc://contextual-thread#3045-3976 |
| whole-email-local-hybrid | long-document-coverage | long-10240, exact-orbit | 24/32 | doc://long-10240#0-1194; doc://long-10240#9157-10240; doc://long-10240#6101-7299; doc://long-10240#5081-6280; doc://long-10240#8141-9336; doc://exact-orbit#0-105; doc://long-10240#3044-4243; doc://long-10240#2036-3222 |
| whole-email-local-hybrid | latest-revision | revision-latest, revision-old, contextual-thread, exact-distractor, exact-orbit | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#0-1196; doc://contextual-thread#2032-3224; doc://exact-distractor#0-87; doc://contextual-thread#3045-3976; doc://contextual-thread#1017-2211; doc://exact-orbit#0-105 |
| whole-email-local-hybrid | graph-multihop | graph-team, multilingual, contextual-thread, exact-distractor, revision-latest | 0/1 | doc://graph-team#0-93; doc://multilingual#0-90; doc://contextual-thread#0-1196; doc://exact-distractor#0-87; doc://contextual-thread#3045-3976; doc://contextual-thread#1017-2211; doc://contextual-thread#2032-3224; doc://revision-latest#0-99 |
| whole-email-local-hybrid | multilingual | multilingual, exact-orbit, long-10240 | 1/1 | doc://multilingual#0-90; doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#7120-8320; doc://long-10240#3044-4243; doc://long-10240#2036-3222; doc://long-10240#1016-2215 |
| whole-email-local-hybrid | prompt-injection | contextual-thread, injection, exact-distractor, revision-latest, multilingual | 1/1 | doc://contextual-thread#0-1196; doc://injection#0-130; doc://exact-distractor#0-87; doc://contextual-thread#3045-3976; doc://revision-latest#0-99; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://multilingual#0-90 |
| whole-email-local-hybrid | scope-isolation | graph-vendor, injection, long-10240, graph-team | 0/0 | doc://graph-vendor#0-75; doc://injection#0-130; doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://graph-team#0-93; doc://long-10240#0-1194; doc://long-10240#3044-4243 |
| whole-email-local-hybrid | no-answer | contextual-thread, revision-latest, exact-distractor, multilingual, injection | 0/0 | doc://contextual-thread#0-1196; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://multilingual#0-90; doc://injection#0-130 |
| whole-email-local-hybrid | contextual-late-reference | contextual-thread, graph-team, multilingual, exact-distractor, exact-orbit, long-10240 | 1/1 | doc://contextual-thread#0-1196; doc://graph-team#0-93; doc://multilingual#0-90; doc://exact-distractor#0-87; doc://contextual-thread#3045-3976; doc://exact-orbit#0-105; doc://long-10240#1016-2215; doc://contextual-thread#1017-2211 |
| raw-endpoint-dense | exact-identifier | exact-orbit, exact-distractor, long-10240, revision-old, revision-latest | 1/1 | doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://long-10240#0-1194; doc://revision-old#0-81; doc://revision-latest#0-99; doc://long-10240#9157-10240; doc://long-10240#1016-2215; doc://long-10240#5081-6280 |
| raw-endpoint-dense | long-document-coverage | long-10240, injection | 23/32 | doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://long-10240#9157-10240; doc://injection#0-130; doc://long-10240#4064-5260; doc://long-10240#7120-8320; doc://long-10240#0-1194; doc://long-10240#1016-2215 |
| raw-endpoint-dense | latest-revision | revision-latest, revision-old, long-10240, exact-distractor | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://long-10240#1016-2215; doc://long-10240#3044-4243; doc://exact-distractor#0-87; doc://long-10240#8141-9336; doc://long-10240#9157-10240; doc://long-10240#4064-5260 |
| raw-endpoint-dense | graph-multihop | graph-team, long-10240, graph-vendor, contextual-thread | 1/1 | doc://graph-team#0-93; doc://long-10240#0-1194; doc://long-10240#3044-4243; doc://graph-vendor#0-75; doc://long-10240#8141-9336; doc://long-10240#9157-10240; doc://long-10240#6101-7299; doc://contextual-thread#1017-2211 |
| raw-endpoint-dense | multilingual | multilingual, long-10240, exact-distractor | 1/1 | doc://multilingual#0-90; doc://long-10240#2036-3222; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://exact-distractor#0-87; doc://long-10240#9157-10240; doc://long-10240#0-1194; doc://long-10240#3044-4243 |
| raw-endpoint-dense | prompt-injection | injection, long-10240, contextual-thread | 1/1 | doc://injection#0-130; doc://long-10240#3044-4243; doc://contextual-thread#1017-2211; doc://contextual-thread#3045-3976; doc://long-10240#8141-9336; doc://contextual-thread#2032-3224; doc://long-10240#4064-5260; doc://long-10240#1016-2215 |
| raw-endpoint-dense | scope-isolation | long-10240, injection | 0/0 | doc://long-10240#3044-4243; doc://injection#0-130; doc://long-10240#4064-5260; doc://long-10240#1016-2215; doc://long-10240#7120-8320; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://long-10240#9157-10240 |
| raw-endpoint-dense | no-answer | injection, long-10240, exact-distractor | 0/0 | doc://injection#0-130; doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://exact-distractor#0-87; doc://long-10240#6101-7299; doc://long-10240#4064-5260; doc://long-10240#1016-2215 |
| raw-endpoint-dense | contextual-late-reference | contextual-thread, exact-orbit, long-10240, exact-distractor | 0/1 | doc://contextual-thread#0-1196; doc://exact-orbit#0-105; doc://long-10240#4064-5260; doc://long-10240#7120-8320; doc://exact-distractor#0-87; doc://long-10240#1016-2215; doc://long-10240#8141-9336; doc://long-10240#6101-7299 |
| raw-endpoint-hybrid | exact-identifier | exact-orbit, long-10240, exact-distractor, revision-latest, revision-old, contextual-thread | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#0-1196; doc://contextual-thread#1017-2211; doc://contextual-thread#3045-3976 |
| raw-endpoint-hybrid | long-document-coverage | long-10240 | 26/32 | doc://long-10240#9157-10240; doc://long-10240#8141-9336; doc://long-10240#3044-4243; doc://long-10240#0-1194; doc://long-10240#4064-5260; doc://long-10240#7120-8320; doc://long-10240#1016-2215; doc://long-10240#5081-6280 |
| raw-endpoint-hybrid | latest-revision | revision-latest, revision-old, exact-distractor, long-10240, contextual-thread | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://long-10240#3044-4243; doc://contextual-thread#0-1196; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211 |
| raw-endpoint-hybrid | graph-multihop | graph-team, graph-vendor, contextual-thread, long-10240 | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://contextual-thread#1017-2211; doc://long-10240#0-1194; doc://contextual-thread#2032-3224; doc://contextual-thread#3045-3976; doc://contextual-thread#0-1196; doc://long-10240#3044-4243 |
| raw-endpoint-hybrid | multilingual | multilingual, long-10240, exact-distractor | 1/1 | doc://multilingual#0-90; doc://long-10240#2036-3222; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://exact-distractor#0-87; doc://long-10240#9157-10240; doc://long-10240#0-1194; doc://long-10240#3044-4243 |
| raw-endpoint-hybrid | prompt-injection | injection, contextual-thread, revision-latest, revision-old, exact-distractor | 1/1 | doc://injection#0-130; doc://contextual-thread#1017-2211; doc://contextual-thread#2032-3224; doc://contextual-thread#3045-3976; doc://contextual-thread#0-1196; doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87 |
| raw-endpoint-hybrid | scope-isolation | long-10240, injection | 0/0 | doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://long-10240#1016-2215; doc://long-10240#4064-5260; doc://long-10240#5081-6280; doc://injection#0-130; doc://long-10240#7120-8320; doc://long-10240#0-1194 |
| raw-endpoint-hybrid | no-answer | exact-distractor, revision-old, revision-latest, contextual-thread, exact-orbit | 0/0 | doc://exact-distractor#0-87; doc://revision-old#0-81; doc://revision-latest#0-99; doc://contextual-thread#0-1196; doc://contextual-thread#3045-3976; doc://contextual-thread#1017-2211; doc://exact-orbit#0-105; doc://contextual-thread#2032-3224 |
| raw-endpoint-hybrid | contextual-late-reference | contextual-thread, exact-orbit, exact-distractor, graph-vendor, long-10240, graph-team | 0/1 | doc://contextual-thread#0-1196; doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://graph-vendor#0-75; doc://long-10240#1016-2215; doc://graph-team#0-93; doc://long-10240#4064-5260; doc://long-10240#7120-8320 |
| metadata-endpoint-dense | exact-identifier | exact-orbit, exact-distractor, long-10240, revision-old, graph-vendor | 1/1 | doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://long-10240#0-1194; doc://revision-old#0-81; doc://graph-vendor#0-75; doc://long-10240#1016-2215; doc://long-10240#5081-6280; doc://long-10240#6101-7299 |
| metadata-endpoint-dense | long-document-coverage | long-10240 | 27/32 | doc://long-10240#8141-9336; doc://long-10240#9157-10240; doc://long-10240#7120-8320; doc://long-10240#0-1194; doc://long-10240#3044-4243; doc://long-10240#5081-6280; doc://long-10240#1016-2215; doc://long-10240#2036-3222 |
| metadata-endpoint-dense | latest-revision | revision-latest, revision-old, exact-distractor, long-10240, contextual-thread | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://long-10240#1016-2215; doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://contextual-thread#0-1196; doc://long-10240#5081-6280 |
| metadata-endpoint-dense | graph-multihop | graph-team, graph-vendor, long-10240, contextual-thread | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#9157-10240; doc://contextual-thread#3045-3976; doc://long-10240#5081-6280; doc://long-10240#8141-9336 |
| metadata-endpoint-dense | multilingual | multilingual, long-10240, exact-distractor, revision-old | 1/1 | doc://multilingual#0-90; doc://long-10240#2036-3222; doc://exact-distractor#0-87; doc://long-10240#9157-10240; doc://long-10240#5081-6280; doc://long-10240#0-1194; doc://long-10240#8141-9336; doc://revision-old#0-81 |
| metadata-endpoint-dense | prompt-injection | injection, contextual-thread, long-10240 | 1/1 | doc://injection#0-130; doc://contextual-thread#3045-3976; doc://contextual-thread#1017-2211; doc://long-10240#8141-9336; doc://long-10240#7120-8320; doc://contextual-thread#2032-3224; doc://long-10240#5081-6280; doc://long-10240#1016-2215 |
| metadata-endpoint-dense | scope-isolation | injection, long-10240, exact-distractor | 0/0 | doc://injection#0-130; doc://long-10240#7120-8320; doc://long-10240#1016-2215; doc://long-10240#8141-9336; doc://long-10240#4064-5260; doc://exact-distractor#0-87; doc://long-10240#5081-6280; doc://long-10240#3044-4243 |
| metadata-endpoint-dense | no-answer | injection, exact-distractor, long-10240, contextual-thread | 0/0 | doc://injection#0-130; doc://exact-distractor#0-87; doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://long-10240#1016-2215; doc://long-10240#0-1194; doc://contextual-thread#3045-3976 |
| metadata-endpoint-dense | contextual-late-reference | contextual-thread, exact-distractor, long-10240, exact-orbit | 0/1 | doc://contextual-thread#0-1196; doc://exact-distractor#0-87; doc://long-10240#7120-8320; doc://long-10240#6101-7299; doc://long-10240#4064-5260; doc://long-10240#2036-3222; doc://exact-orbit#0-105; doc://long-10240#1016-2215 |
| metadata-endpoint-hybrid | exact-identifier | exact-orbit, long-10240, exact-distractor, revision-old, revision-latest, graph-vendor, multilingual | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://revision-latest#0-99; doc://graph-vendor#0-75; doc://long-10240#1016-2215; doc://multilingual#0-90 |
| metadata-endpoint-hybrid | long-document-coverage | long-10240 | 26/32 | doc://long-10240#9157-10240; doc://long-10240#8141-9336; doc://long-10240#0-1194; doc://long-10240#3044-4243; doc://long-10240#7120-8320; doc://long-10240#5081-6280; doc://long-10240#6101-7299; doc://long-10240#4064-5260 |
| metadata-endpoint-hybrid | latest-revision | revision-latest, revision-old, contextual-thread, exact-distractor, long-10240 | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#0-1196; doc://exact-distractor#0-87; doc://long-10240#3044-4243; doc://contextual-thread#3045-3976; doc://long-10240#1016-2215; doc://contextual-thread#2032-3224 |
| metadata-endpoint-hybrid | graph-multihop | graph-team, graph-vendor, contextual-thread, long-10240 | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://contextual-thread#3045-3976; doc://long-10240#0-1194; doc://contextual-thread#1017-2211; doc://long-10240#6101-7299; doc://contextual-thread#2032-3224; doc://contextual-thread#0-1196 |
| metadata-endpoint-hybrid | multilingual | multilingual, long-10240, exact-distractor, revision-old | 1/1 | doc://multilingual#0-90; doc://long-10240#2036-3222; doc://exact-distractor#0-87; doc://long-10240#9157-10240; doc://long-10240#5081-6280; doc://long-10240#0-1194; doc://long-10240#8141-9336; doc://revision-old#0-81 |
| metadata-endpoint-hybrid | prompt-injection | injection, contextual-thread, revision-latest, exact-distractor, revision-old | 1/1 | doc://injection#0-130; doc://contextual-thread#3045-3976; doc://contextual-thread#1017-2211; doc://contextual-thread#2032-3224; doc://contextual-thread#0-1196; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81 |
| metadata-endpoint-hybrid | scope-isolation | long-10240, injection | 0/0 | doc://long-10240#8141-9336; doc://long-10240#1016-2215; doc://long-10240#7120-8320; doc://injection#0-130; doc://long-10240#3044-4243; doc://long-10240#5081-6280; doc://long-10240#0-1194; doc://long-10240#4064-5260 |
| metadata-endpoint-hybrid | no-answer | exact-distractor, contextual-thread, revision-old, revision-latest, graph-vendor | 0/0 | doc://exact-distractor#0-87; doc://contextual-thread#3045-3976; doc://contextual-thread#0-1196; doc://revision-old#0-81; doc://revision-latest#0-99; doc://contextual-thread#1017-2211; doc://contextual-thread#2032-3224; doc://graph-vendor#0-75 |
| metadata-endpoint-hybrid | contextual-late-reference | contextual-thread, exact-distractor, long-10240, graph-vendor, exact-orbit, graph-team | 0/1 | doc://contextual-thread#0-1196; doc://exact-distractor#0-87; doc://long-10240#1016-2215; doc://graph-vendor#0-75; doc://exact-orbit#0-105; doc://graph-team#0-93; doc://long-10240#7120-8320; doc://long-10240#6101-7299 |
| generated-endpoint-dense | exact-identifier | exact-orbit, exact-distractor, long-10240, revision-latest, revision-old | 1/1 | doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://long-10240#0-1194; doc://revision-latest#0-99; doc://long-10240#9157-10240; doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://revision-old#0-81 |
| generated-endpoint-dense | long-document-coverage | long-10240, contextual-thread, exact-orbit | 20/32 | doc://long-10240#8141-9336; doc://long-10240#3044-4243; doc://long-10240#9157-10240; doc://long-10240#0-1194; doc://long-10240#1016-2215; doc://contextual-thread#3045-3976; doc://exact-orbit#0-105; doc://long-10240#7120-8320 |
| generated-endpoint-dense | latest-revision | revision-latest, revision-old, long-10240, contextual-thread, exact-orbit | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://long-10240#3044-4243; doc://long-10240#1016-2215; doc://contextual-thread#3045-3976; doc://long-10240#8141-9336; doc://exact-orbit#0-105; doc://long-10240#9157-10240 |
| generated-endpoint-dense | graph-multihop | graph-team, graph-vendor, long-10240, contextual-thread | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://long-10240#8141-9336; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://contextual-thread#3045-3976; doc://long-10240#3044-4243; doc://long-10240#5081-6280 |
| generated-endpoint-dense | multilingual | multilingual, long-10240, exact-orbit, contextual-thread | 1/1 | doc://multilingual#0-90; doc://long-10240#2036-3222; doc://long-10240#8141-9336; doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://long-10240#5081-6280; doc://long-10240#9157-10240; doc://contextual-thread#3045-3976 |
| generated-endpoint-dense | prompt-injection | injection, contextual-thread, revision-latest, exact-orbit, long-10240 | 1/1 | doc://injection#0-130; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://revision-latest#0-99; doc://exact-orbit#0-105; doc://long-10240#8141-9336; doc://long-10240#9157-10240 |
| generated-endpoint-dense | scope-isolation | long-10240, contextual-thread, injection, exact-orbit | 0/0 | doc://long-10240#7120-8320; doc://contextual-thread#3045-3976; doc://long-10240#1016-2215; doc://long-10240#8141-9336; doc://injection#0-130; doc://long-10240#3044-4243; doc://exact-orbit#0-105; doc://long-10240#9157-10240 |
| generated-endpoint-dense | no-answer | contextual-thread, exact-orbit, injection, long-10240, multilingual, revision-latest | 0/0 | doc://contextual-thread#3045-3976; doc://exact-orbit#0-105; doc://injection#0-130; doc://long-10240#8141-9336; doc://multilingual#0-90; doc://contextual-thread#2032-3224; doc://revision-latest#0-99; doc://long-10240#0-1194 |
| generated-endpoint-dense | contextual-late-reference | contextual-thread, exact-orbit, multilingual, long-10240 | 1/1 | doc://contextual-thread#0-1196; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://exact-orbit#0-105; doc://multilingual#0-90; doc://long-10240#7120-8320; doc://long-10240#8141-9336 |
| generated-endpoint-hybrid | exact-identifier | exact-orbit, long-10240, exact-distractor, revision-latest, revision-old, multilingual, contextual-thread | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://revision-old#0-81; doc://long-10240#9157-10240; doc://multilingual#0-90; doc://contextual-thread#3045-3976 |
| generated-endpoint-hybrid | long-document-coverage | long-10240, exact-orbit, contextual-thread | 21/32 | doc://long-10240#0-1194; doc://long-10240#9157-10240; doc://exact-orbit#0-105; doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://long-10240#1016-2215; doc://long-10240#5081-6280; doc://contextual-thread#3045-3976 |
| generated-endpoint-hybrid | latest-revision | revision-latest, revision-old, exact-orbit, long-10240, contextual-thread | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://long-10240#3044-4243; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://long-10240#9157-10240 |
| generated-endpoint-hybrid | graph-multihop | graph-team, graph-vendor, long-10240 | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://long-10240#8141-9336; doc://long-10240#6101-7299; doc://long-10240#4064-5260; doc://long-10240#3044-4243; doc://long-10240#9157-10240; doc://long-10240#5081-6280 |
| generated-endpoint-hybrid | multilingual | multilingual, long-10240, exact-orbit, contextual-thread | 1/1 | doc://multilingual#0-90; doc://long-10240#2036-3222; doc://long-10240#8141-9336; doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://long-10240#5081-6280; doc://long-10240#9157-10240; doc://contextual-thread#3045-3976 |
| generated-endpoint-hybrid | prompt-injection | injection, contextual-thread, revision-latest, revision-old, long-10240, exact-orbit | 1/1 | doc://injection#0-130; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://revision-latest#0-99; doc://revision-old#0-81; doc://long-10240#8141-9336; doc://exact-orbit#0-105 |
| generated-endpoint-hybrid | scope-isolation | long-10240, graph-vendor, multilingual, injection | 0/0 | doc://long-10240#1016-2215; doc://graph-vendor#0-75; doc://long-10240#7120-8320; doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#5081-6280 |
| generated-endpoint-hybrid | no-answer | contextual-thread, exact-orbit, revision-latest, multilingual, long-10240 | 0/0 | doc://contextual-thread#3045-3976; doc://exact-orbit#0-105; doc://contextual-thread#2032-3224; doc://revision-latest#0-99; doc://multilingual#0-90; doc://contextual-thread#1017-2211; doc://long-10240#8141-9336; doc://contextual-thread#0-1196 |
| generated-endpoint-hybrid | contextual-late-reference | contextual-thread, exact-orbit, long-10240, multilingual, graph-vendor | 1/1 | doc://contextual-thread#0-1196; doc://contextual-thread#1017-2211; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224; doc://exact-orbit#0-105; doc://long-10240#1016-2215; doc://multilingual#0-90; doc://graph-vendor#0-75 |
| whole-email-endpoint-dense | exact-identifier | exact-orbit, exact-distractor, long-10240 | 1/1 | doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://long-10240#0-1194; doc://long-10240#9157-10240; doc://long-10240#1016-2215; doc://long-10240#5081-6280; doc://long-10240#8141-9336; doc://long-10240#3044-4243 |
| whole-email-endpoint-dense | long-document-coverage | long-10240 | 26/32 | doc://long-10240#1016-2215; doc://long-10240#8141-9336; doc://long-10240#9157-10240; doc://long-10240#7120-8320; doc://long-10240#3044-4243; doc://long-10240#0-1194; doc://long-10240#2036-3222; doc://long-10240#6101-7299 |
| whole-email-endpoint-dense | latest-revision | revision-latest, revision-old, long-10240, contextual-thread, exact-orbit, exact-distractor | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://long-10240#3044-4243; doc://long-10240#1016-2215; doc://contextual-thread#0-1196; doc://exact-orbit#0-105; doc://contextual-thread#3045-3976; doc://exact-distractor#0-87 |
| whole-email-endpoint-dense | graph-multihop | graph-team, graph-vendor, long-10240 | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#3044-4243; doc://long-10240#9157-10240; doc://long-10240#5081-6280; doc://long-10240#8141-9336 |
| whole-email-endpoint-dense | multilingual | multilingual, long-10240 | 1/1 | doc://multilingual#0-90; doc://long-10240#2036-3222; doc://long-10240#5081-6280; doc://long-10240#0-1194; doc://long-10240#8141-9336; doc://long-10240#9157-10240; doc://long-10240#4064-5260; doc://long-10240#3044-4243 |
| whole-email-endpoint-dense | prompt-injection | injection, long-10240, graph-vendor | 1/1 | doc://injection#0-130; doc://long-10240#1016-2215; doc://long-10240#7120-8320; doc://long-10240#8141-9336; doc://long-10240#9157-10240; doc://long-10240#3044-4243; doc://graph-vendor#0-75; doc://long-10240#5081-6280 |
| whole-email-endpoint-dense | scope-isolation | long-10240, injection | 0/0 | doc://long-10240#7120-8320; doc://long-10240#1016-2215; doc://injection#0-130; doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://long-10240#9157-10240; doc://long-10240#4064-5260 |
| whole-email-endpoint-dense | no-answer | injection, long-10240, exact-distractor, exact-orbit | 0/0 | doc://injection#0-130; doc://long-10240#5081-6280; doc://long-10240#1016-2215; doc://exact-distractor#0-87; doc://long-10240#6101-7299; doc://long-10240#3044-4243; doc://exact-orbit#0-105; doc://long-10240#8141-9336 |
| whole-email-endpoint-dense | contextual-late-reference | contextual-thread, exact-orbit, long-10240 | 1/1 | doc://contextual-thread#3045-3976; doc://contextual-thread#0-1196; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://exact-orbit#0-105; doc://long-10240#7120-8320; doc://long-10240#0-1194; doc://long-10240#4064-5260 |
| whole-email-endpoint-hybrid | exact-identifier | exact-orbit, long-10240, exact-distractor, revision-latest, multilingual, revision-old | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://multilingual#0-90; doc://revision-old#0-81; doc://long-10240#9157-10240; doc://long-10240#1016-2215 |
| whole-email-endpoint-hybrid | long-document-coverage | long-10240, exact-orbit | 23/32 | doc://long-10240#9157-10240; doc://long-10240#8141-9336; doc://long-10240#0-1194; doc://long-10240#1016-2215; doc://long-10240#6101-7299; doc://long-10240#3044-4243; doc://exact-orbit#0-105; doc://long-10240#7120-8320 |
| whole-email-endpoint-hybrid | latest-revision | revision-latest, revision-old, contextual-thread, exact-distractor, exact-orbit, long-10240 | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#0-1196; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#3044-4243; doc://contextual-thread#2032-3224; doc://contextual-thread#3045-3976 |
| whole-email-endpoint-hybrid | graph-multihop | graph-team, graph-vendor, long-10240, revision-old, contextual-thread, revision-latest | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://long-10240#6101-7299; doc://long-10240#0-1194; doc://revision-old#0-81; doc://long-10240#3044-4243; doc://contextual-thread#0-1196; doc://revision-latest#0-99 |
| whole-email-endpoint-hybrid | multilingual | multilingual, long-10240 | 1/1 | doc://multilingual#0-90; doc://long-10240#2036-3222; doc://long-10240#5081-6280; doc://long-10240#0-1194; doc://long-10240#8141-9336; doc://long-10240#9157-10240; doc://long-10240#4064-5260; doc://long-10240#3044-4243 |
| whole-email-endpoint-hybrid | prompt-injection | injection, long-10240, revision-latest, graph-vendor, contextual-thread, revision-old | 1/1 | doc://injection#0-130; doc://long-10240#1016-2215; doc://long-10240#9157-10240; doc://revision-latest#0-99; doc://long-10240#7120-8320; doc://graph-vendor#0-75; doc://contextual-thread#0-1196; doc://revision-old#0-81 |
| whole-email-endpoint-hybrid | scope-isolation | injection, graph-vendor, long-10240 | 0/0 | doc://injection#0-130; doc://graph-vendor#0-75; doc://long-10240#8141-9336; doc://long-10240#1016-2215; doc://long-10240#3044-4243; doc://long-10240#7120-8320; doc://long-10240#5081-6280; doc://long-10240#0-1194 |
| whole-email-endpoint-hybrid | no-answer | exact-distractor, injection, contextual-thread, exact-orbit, long-10240, revision-latest | 0/0 | doc://exact-distractor#0-87; doc://injection#0-130; doc://contextual-thread#0-1196; doc://contextual-thread#3045-3976; doc://contextual-thread#1017-2211; doc://exact-orbit#0-105; doc://long-10240#1016-2215; doc://revision-latest#0-99 |
| whole-email-endpoint-hybrid | contextual-late-reference | contextual-thread, exact-orbit, long-10240, graph-vendor, multilingual | 1/1 | doc://contextual-thread#0-1196; doc://contextual-thread#3045-3976; doc://contextual-thread#1017-2211; doc://contextual-thread#2032-3224; doc://exact-orbit#0-105; doc://long-10240#1016-2215; doc://graph-vendor#0-75; doc://multilingual#0-90 |

The JSON companion retains every prompt, raw model output, generated context, per-case metric, and complete source-backed evidence span.
