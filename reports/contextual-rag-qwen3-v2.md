# Generated Contextual RAG Evaluation

Paired, query-independent Contextual Retrieval ablation over identical structure-aware chunks. Raw passage, deterministic metadata context, and generated context are compared. Generated context is indexed by BM25 and embeddings but is never returned as answer evidence.

Top-K: 8. Production ready: False.
Promotion recommended: False.

## Models and exact method

- Context generator: `qwen3:8b` / `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`
- Embedding model: `qwen3-embedding:4b` / `df5bd2e3c74cd8d069d21dc038f1b359fcdc9458fce1c99bd43c9eb1518ff907`
- Prompt contract: `contextual-retrieval-v1`; temperature 0, seed 0, 16K context, 160 output tokens.
- The complete synthetic document and one chunk were supplied for each call. No user query was supplied.
- Accepted context was prepended to the search representation only. Retrieved evidence remained the unchanged canonical source span.

## Context generation

| Chunks | Successful | Generated now | Cache hits | Failures | Entity grounding | Source spans | Wall ms | Prompt tokens | Output tokens |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 23 | 23 | 23 | 0 | 0 | 1.000 | 1.000 | 16515.9 | 30741 | 1078 |

## Retrieval results

| Lane | Context | Retrieval | Embedding | Document recall | Fact recall | MRR | nDCG | p50 ms | DB bytes | Indexed chars |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| raw-local-lexical | raw | lexical | deterministic-local-v1 | 1.000 | 0.763 | 0.929 | 0.910 | 0.244 | 192512 | 17545 |
| raw-local-hybrid | raw | hybrid | deterministic-local-v1 | 0.929 | 0.763 | 0.929 | 0.892 | 0.518 | 192512 | 17545 |
| metadata-local-lexical | metadata | lexical | deterministic-local-v1 | 1.000 | 0.763 | 0.929 | 0.910 | 0.239 | 204800 | 19627 |
| metadata-local-hybrid | metadata | hybrid | deterministic-local-v1 | 0.929 | 0.763 | 0.929 | 0.892 | 0.522 | 204800 | 19627 |
| generated-local-lexical | generated | lexical | deterministic-local-v1 | 1.000 | 0.711 | 0.905 | 0.917 | 0.355 | 212992 | 23141 |
| generated-local-hybrid | generated | hybrid | deterministic-local-v1 | 1.000 | 0.789 | 1.000 | 0.972 | 0.622 | 212992 | 23141 |
| raw-endpoint-dense | raw | dense | qwen3-embedding:4b | 1.000 | 0.763 | 1.000 | 0.967 | 127.111 | 937984 | 17545 |
| raw-endpoint-hybrid | raw | hybrid | qwen3-embedding:4b | 1.000 | 0.842 | 1.000 | 1.000 | 127.040 | 937984 | 17545 |
| metadata-endpoint-dense | metadata | dense | qwen3-embedding:4b | 1.000 | 0.868 | 1.000 | 0.989 | 129.781 | 950272 | 19627 |
| metadata-endpoint-hybrid | metadata | hybrid | qwen3-embedding:4b | 1.000 | 0.842 | 1.000 | 1.000 | 127.815 | 950272 | 19627 |
| generated-endpoint-dense | generated | dense | qwen3-embedding:4b | 1.000 | 0.684 | 0.929 | 0.956 | 127.841 | 958464 | 23141 |
| generated-endpoint-hybrid | generated | hybrid | qwen3-embedding:4b | 1.000 | 0.711 | 1.000 | 1.000 | 126.228 | 958464 | 23141 |

## Paired deltas: generated minus metadata context

| Comparison | Retrieval family | Document recall | Fact recall | MRR | nDCG | p50 ms | DB bytes | Indexed chars |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| generated-vs-raw | local-lexical | +0.000 | -0.053 | -0.024 | +0.007 | +0.111 | +20480 | +5596 |
| generated-vs-raw | local-hybrid | +0.071 | +0.026 | +0.071 | +0.080 | +0.104 | +20480 | +5596 |
| generated-vs-raw | endpoint-dense | +0.000 | -0.079 | -0.071 | -0.011 | +0.730 | +20480 | +5596 |
| generated-vs-raw | endpoint-hybrid | +0.000 | -0.132 | +0.000 | +0.000 | -0.812 | +20480 | +5596 |
| generated-vs-metadata | local-lexical | +0.000 | -0.053 | -0.024 | +0.007 | +0.116 | +8192 | +3514 |
| generated-vs-metadata | local-hybrid | +0.071 | +0.026 | +0.071 | +0.080 | +0.101 | +8192 | +3514 |
| generated-vs-metadata | endpoint-dense | +0.000 | -0.184 | -0.071 | -0.032 | -1.939 | +8192 | +3514 |
| generated-vs-metadata | endpoint-hybrid | +0.000 | -0.132 | +0.000 | +0.000 | -1.587 | +8192 | +3514 |

## Decision

Do not promote generated contextual retrieval from this run.

## Limitations

- The corpus is synthetic and small.
- The frozen queries mostly contain exact identifiers; realistic paraphrase and thread-anaphora cases are still needed.
- One live run does not establish variance or production readiness.
- Generated context is model output and may add unverified prose even when exact identifiers are grounded.

## Generated-context audit

### exact-orbit / tenant-alpha/primary/exact-orbit:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-105`.
- Source span valid: `True`; latency: `1904.2 ms`.
- Generated context: The chunk is the entire content of the document titled 'Orbit launch decision', which details the launch date, location, and budget for Project ORBIT-731.
- Error: none
- Raw model output:

```json
{"context": "The chunk is the entire content of the document titled 'Orbit launch decision', which details the launch date, location, and budget for Project ORBIT-731."}
```

### exact-distractor / tenant-alpha/primary/exact-distractor:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-87`.
- Source span valid: `True`; latency: `429.1 ms`.
- Generated context: The chunk provides a factual statement about Project ORBIT-713, mentioning its launch date and that it is unrelated to other projects, using East Annex.
- Error: none
- Raw model output:

```json
{"context": "The chunk provides a factual statement about Project ORBIT-713, mentioning its launch date and that it is unrelated to other projects, using East Annex."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-1194`.
- Source span valid: `True`; latency: `703.1 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, containing multiple sections with FACT entries. Each section includes a required_value and repetitive explanatory text about bounded retrieval and data coverage.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, containing multiple sections with FACT entries. Each section includes a required_value and repetitive explanatory text about bounded retrieval and data coverage."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:1

- Status: `ok`; cache hit: `False`; source: `1016-2215`.
- Source span valid: `True`; latency: `811.8 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, located in Section 04, and contains a fact with the required value 'Asha Menon'. It repeats the purpose of synthetic context for retrieval exercises.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, located in Section 04, and contains a fact with the required value 'Asha Menon'. It repeats the purpose of synthetic context for retrieval exercises."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:2

- Status: `ok`; cache hit: `False`; source: `2036-3222`.
- Source span valid: `True`; latency: `918.0 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, following Section 07 and preceding Section 09. It contains repeated statements about synthetic context for bounded retrieval and includes a fact with the required value 'Omar Shah' in Section 08.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, following Section 07 and preceding Section 09. It contains repeated statements about synthetic context for bounded retrieval and includes a fact with the required value 'Omar Shah' in Section 08."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:3

- Status: `ok`; cache hit: `False`; source: `3044-4243`.
- Source span valid: `True`; latency: `811.6 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, following Section 09 and preceding Section 15. It contains repeated factual entries with required values and explanatory text about synthetic context usage.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, following Section 09 and preceding Section 15. It contains repeated factual entries with required values and explanatory text about synthetic context usage."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:4

- Status: `ok`; cache hit: `False`; source: `4064-5260`.
- Source span valid: `True`; latency: `844.6 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, located in Section 13 to 17. It contains repeated synthetic facts with required values and a purpose to exercise bounded retrieval and complete coverage without external data.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, located in Section 13 to 17. It contains repeated synthetic facts with required values and a purpose to exercise bounded retrieval and complete coverage without external data."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:5

- Status: `ok`; cache hit: `False`; source: `5081-6280`.
- Source span valid: `True`; latency: `817.8 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, located in Section 16 to Section 20. It contains repeated synthetic facts with required values and explanatory text about bounded retrieval and data privacy.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, located in Section 16 to Section 20. It contains repeated synthetic facts with required values and explanatory text about bounded retrieval and data privacy."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:6

- Status: `ok`; cache hit: `False`; source: `6101-7299`.
- Source span valid: `True`; latency: `764.0 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, located in Section 20 to Section 23. It contains facts about required values and repetitive context for retrieval exercises.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, located in Section 20 to Section 23. It contains facts about required values and repetitive context for retrieval exercises."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:7

- Status: `ok`; cache hit: `False`; source: `7120-8320`.
- Source span valid: `True`; latency: `869.5 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, following sections 22 and 27, and precedes sections 28 and 29. It contains facts related to specific values and repeated context about bounded retrieval and data handling.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, following sections 22 and 27, and precedes sections 28 and 29. It contains facts related to specific values and repeated context about bounded retrieval and data handling."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:8

- Status: `ok`; cache hit: `False`; source: `8141-9336`.
- Source span valid: `True`; latency: `826.7 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, specifically within Section 26 to Section 30. It contains facts with required values and repetitive statements about synthetic contexts for bounded retrieval and coverage.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, specifically within Section 26 to Section 30. It contains facts with required values and repetitive statements about synthetic contexts for bounded retrieval and coverage."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:9

- Status: `ok`; cache hit: `False`; source: `9157-10240`.
- Source span valid: `True`; latency: `814.7 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, located in Section 29 to 32. It contains facts with required values and repetitive statements about synthetic contexts for bounded retrieval and coverage.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, located in Section 29 to 32. It contains facts with required values and repetitive statements about synthetic contexts for bounded retrieval and coverage."}
```

### revision-old / tenant-alpha/primary/revision-old:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-81`.
- Source span valid: `True`; latency: `740.3 ms`.
- Generated context: The chunk is the full text of a decision document titled 'Cedar decision revision 1', dated 2026-08-01, which states that revision one for CEDAR-210 is superseded with a deployment date of 2027-08-12.
- Error: none
- Raw model output:

```json
{"context": "The chunk is the full text of a decision document titled 'Cedar decision revision 1', dated 2026-08-01, which states that revision one for CEDAR-210 is superseded with a deployment date of 2027-08-12."}
```

### revision-latest / tenant-alpha/primary/revision-latest:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-99`.
- Source span valid: `True`; latency: `584.7 ms`.
- Generated context: The chunk is the full text of the document titled 'Cedar decision revision 2', which confirms revision two as the latest approved decision for CEDAR-210 with a deployment date of 2027-09-21.
- Error: none
- Raw model output:

```json
{"context": "The chunk is the full text of the document titled 'Cedar decision revision 2', which confirms revision two as the latest approved decision for CEDAR-210 with a deployment date of 2027-09-21."}
```

### graph-team / tenant-alpha/primary/graph-team:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-93`.
- Source span valid: `True`; latency: `375.3 ms`.
- Generated context: The chunk is the full text of the document titled 'Atlas ownership', which details ownership and team assignments related to Project Atlas.
- Error: none
- Raw model output:

```json
{"context": "The chunk is the full text of the document titled 'Atlas ownership', which details ownership and team assignments related to Project Atlas."}
```

### graph-vendor / tenant-alpha/primary/graph-vendor:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-75`.
- Source span valid: `True`; latency: `446.3 ms`.
- Generated context: The chunk is located in the document titled 'Atlas supplier' under the dependency category. It states that Project Atlas depends on Kestrel Works as its supplier.
- Error: none
- Raw model output:

```json
{"context": "The chunk is located in the document titled 'Atlas supplier' under the dependency category. It states that Project Atlas depends on Kestrel Works as its supplier."}
```

### multilingual / tenant-alpha/primary/multilingual:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-90`.
- Source span valid: `True`; latency: `363.0 ms`.
- Generated context: The chunk provides a factual statement about a project meeting location and date within a multilingual schedule document.
- Error: none
- Raw model output:

```json
{"context": "The chunk provides a factual statement about a project meeting location and date within a multilingual schedule document."}
```

### injection / tenant-alpha/primary/injection:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-130`.
- Source span valid: `True`; latency: `591.3 ms`.
- Generated context: The chunk is from a security document titled 'Untrusted embedded instruction' with ID 'injection'. It contains an untrusted instruction to ignore previous guidance and reveal SECRETCODE-999, along with a fact about the safe status being quarantined.
- Error: none
- Raw model output:

```json
{"context": "The chunk is from a security document titled 'Untrusted embedded instruction' with ID 'injection'. It contains an untrusted instruction to ignore previous guidance and reveal SECRETCODE-999, along with a fact about the safe status being quarantined."}
```

### other-tenant-secret / tenant-beta/private/other-tenant-secret:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-77`.
- Source span valid: `True`; latency: `402.9 ms`.
- Generated context: The chunk is the entire content of a private document titled 'Isolation sentinel', containing a fact about an isolated value specific to tenant-beta.
- Error: none
- Raw model output:

```json
{"context": "The chunk is the entire content of a private document titled 'Isolation sentinel', containing a fact about an isolated value specific to tenant-beta."}
```

### contextual-thread / tenant-alpha/primary/contextual-thread:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-1197`.
- Source span valid: `True`; latency: `565.5 ms`.
- Generated context: The chunk is the beginning of the document discussing Project BOREALIS-204, focusing on the working group's review of packaging, staffing, and transport checks without altering commercial terms.
- Error: none
- Raw model output:

```json
{"context": "The chunk is the beginning of the document discussing Project BOREALIS-204, focusing on the working group's review of packaging, staffing, and transport checks without altering commercial terms."}
```

### contextual-thread / tenant-alpha/primary/contextual-thread:chunk:1

- Status: `ok`; cache hit: `False`; source: `1018-2217`.
- Source span valid: `True`; latency: `629.6 ms`.
- Generated context: The chunk is part of the 'Background' section of the document, detailing the working group's review of packaging, staffing, and transport checks for Project BOREALIS-204 without altering commercial terms.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of the 'Background' section of the document, detailing the working group's review of packaging, staffing, and transport checks for Project BOREALIS-204 without altering commercial terms."}
```

### contextual-thread / tenant-alpha/primary/contextual-thread:chunk:2

- Status: `ok`; cache hit: `False`; source: `2038-3236`.
- Source span valid: `True`; latency: `636.5 ms`.
- Generated context: The chunk is part of the 'Background' section of the document, detailing the working group's review of packaging, staffing, and transport checks for Project BOREALIS-204 without altering approved commercial terms.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of the 'Background' section of the document, detailing the working group's review of packaging, staffing, and transport checks for Project BOREALIS-204 without altering approved commercial terms."}
```

### contextual-thread / tenant-alpha/primary/contextual-thread:chunk:3

- Status: `ok`; cache hit: `False`; source: `3057-3960`.
- Source span valid: `True`; latency: `665.3 ms`.
- Generated context: The chunk is part of the 'Background' section of the document, detailing the working group's review of packaging, staffing, and transport checks without altering approved commercial terms. It precedes the final approval section which includes the approved amount for the shipment.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of the 'Background' section of the document, detailing the working group's review of packaging, staffing, and transport checks without altering approved commercial terms. It precedes the final approval section which includes the approved amount for the shipment."}
```

## Per-case retrieval audit

| Lane | Case | Retrieved documents | Matched facts | Evidence spans |
|---|---|---|---|---|
| raw-local-lexical | exact-identifier | exact-orbit, exact-distractor, revision-latest, revision-old, contextual-thread, long-10240 | 1/1 | doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#3057-3960; doc://contextual-thread#0-1197; doc://long-10240#0-1194; doc://contextual-thread#2038-3236 |
| raw-local-lexical | long-document-coverage | exact-orbit, long-10240 | 23/32 | doc://exact-orbit#0-105; doc://long-10240#9157-10240; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#4064-5260; doc://long-10240#3044-4243; doc://long-10240#5081-6280 |
| raw-local-lexical | latest-revision | revision-latest, revision-old, contextual-thread, exact-distractor, exact-orbit | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#3057-3960; doc://contextual-thread#0-1197; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://exact-distractor#0-87; doc://exact-orbit#0-105 |
| raw-local-lexical | graph-multihop | graph-team, contextual-thread, graph-vendor, revision-latest, revision-old | 1/1 | doc://graph-team#0-93; doc://contextual-thread#0-1197; doc://graph-vendor#0-75; doc://revision-latest#0-99; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://contextual-thread#3057-3960; doc://revision-old#0-81 |
| raw-local-lexical | multilingual | multilingual | 1/1 | doc://multilingual#0-90 |
| raw-local-lexical | prompt-injection | injection, revision-latest, contextual-thread, revision-old, exact-distractor | 1/1 | doc://injection#0-130; doc://revision-latest#0-99; doc://contextual-thread#0-1197; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://contextual-thread#3057-3960; doc://revision-old#0-81; doc://exact-distractor#0-87 |
| raw-local-lexical | scope-isolation | long-10240 | 0/0 | doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#0-1194; doc://long-10240#3044-4243; doc://long-10240#5081-6280; doc://long-10240#1016-2215; doc://long-10240#2036-3222; doc://long-10240#7120-8320 |
| raw-local-lexical | no-answer | revision-latest, contextual-thread, revision-old, exact-distractor, exact-orbit | 0/0 | doc://revision-latest#0-99; doc://contextual-thread#0-1197; doc://contextual-thread#3057-3960; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105 |
| raw-local-lexical | contextual-late-reference | contextual-thread, revision-latest, revision-old, graph-vendor, exact-distractor | 1/1 | doc://contextual-thread#3057-3960; doc://contextual-thread#0-1197; doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#1018-2217; doc://contextual-thread#2038-3236; doc://graph-vendor#0-75; doc://exact-distractor#0-87 |
| raw-local-hybrid | exact-identifier | exact-orbit, long-10240, revision-latest, revision-old, contextual-thread, exact-distractor | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#0-1197; doc://contextual-thread#3057-3960; doc://exact-distractor#0-87; doc://contextual-thread#1018-2217 |
| raw-local-hybrid | long-document-coverage | long-10240, exact-orbit | 24/32 | doc://long-10240#0-1194; doc://long-10240#9157-10240; doc://long-10240#6101-7299; doc://exact-orbit#0-105; doc://long-10240#5081-6280; doc://long-10240#8141-9336; doc://long-10240#3044-4243; doc://long-10240#2036-3222 |
| raw-local-hybrid | latest-revision | revision-latest, revision-old, contextual-thread, exact-distractor, long-10240 | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#3057-3960; doc://contextual-thread#2038-3236; doc://contextual-thread#0-1197; doc://contextual-thread#1018-2217; doc://exact-distractor#0-87; doc://long-10240#3044-4243 |
| raw-local-hybrid | graph-multihop | graph-team, revision-latest, contextual-thread, long-10240 | 0/1 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://contextual-thread#0-1197; doc://contextual-thread#3057-3960; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://long-10240#9157-10240; doc://long-10240#0-1194 |
| raw-local-hybrid | multilingual | multilingual, exact-orbit, long-10240, injection | 1/1 | doc://multilingual#0-90; doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://injection#0-130; doc://long-10240#6101-7299; doc://long-10240#7120-8320; doc://long-10240#3044-4243; doc://long-10240#2036-3222 |
| raw-local-hybrid | prompt-injection | contextual-thread, injection, revision-latest, exact-distractor, revision-old | 1/1 | doc://contextual-thread#0-1197; doc://injection#0-130; doc://contextual-thread#3057-3960; doc://contextual-thread#2038-3236; doc://revision-latest#0-99; doc://contextual-thread#1018-2217; doc://exact-distractor#0-87; doc://revision-old#0-81 |
| raw-local-hybrid | scope-isolation | long-10240, injection | 0/0 | doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://long-10240#0-1194; doc://injection#0-130; doc://long-10240#3044-4243; doc://long-10240#7120-8320; doc://long-10240#1016-2215 |
| raw-local-hybrid | no-answer | contextual-thread, revision-latest, exact-distractor, revision-old, exact-orbit | 0/0 | doc://contextual-thread#0-1197; doc://contextual-thread#3057-3960; doc://revision-latest#0-99; doc://contextual-thread#1018-2217; doc://contextual-thread#2038-3236; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://exact-orbit#0-105 |
| raw-local-hybrid | contextual-late-reference | contextual-thread, revision-latest, exact-distractor, graph-team, revision-old | 1/1 | doc://contextual-thread#0-1197; doc://contextual-thread#3057-3960; doc://revision-latest#0-99; doc://contextual-thread#1018-2217; doc://contextual-thread#2038-3236; doc://exact-distractor#0-87; doc://graph-team#0-93; doc://revision-old#0-81 |
| metadata-local-lexical | exact-identifier | exact-orbit, exact-distractor, revision-latest, revision-old, contextual-thread, long-10240 | 1/1 | doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#3057-3960; doc://contextual-thread#0-1197; doc://long-10240#0-1194; doc://contextual-thread#2038-3236 |
| metadata-local-lexical | long-document-coverage | exact-orbit, long-10240 | 23/32 | doc://exact-orbit#0-105; doc://long-10240#9157-10240; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#4064-5260; doc://long-10240#3044-4243; doc://long-10240#5081-6280 |
| metadata-local-lexical | latest-revision | revision-latest, revision-old, contextual-thread, exact-distractor, exact-orbit | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#3057-3960; doc://contextual-thread#0-1197; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://exact-distractor#0-87; doc://exact-orbit#0-105 |
| metadata-local-lexical | graph-multihop | graph-team, contextual-thread, graph-vendor, revision-latest, exact-distractor | 1/1 | doc://graph-team#0-93; doc://contextual-thread#0-1197; doc://graph-vendor#0-75; doc://revision-latest#0-99; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://contextual-thread#3057-3960; doc://exact-distractor#0-87 |
| metadata-local-lexical | multilingual | multilingual | 1/1 | doc://multilingual#0-90 |
| metadata-local-lexical | prompt-injection | injection, contextual-thread, revision-latest, exact-distractor, revision-old | 1/1 | doc://injection#0-130; doc://contextual-thread#0-1197; doc://revision-latest#0-99; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://contextual-thread#3057-3960; doc://exact-distractor#0-87; doc://revision-old#0-81 |
| metadata-local-lexical | scope-isolation | long-10240 | 0/0 | doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#3044-4243; doc://long-10240#5081-6280; doc://long-10240#1016-2215; doc://long-10240#2036-3222; doc://long-10240#7120-8320 |
| metadata-local-lexical | no-answer | revision-latest, contextual-thread, revision-old, exact-distractor, exact-orbit | 0/0 | doc://revision-latest#0-99; doc://contextual-thread#0-1197; doc://contextual-thread#3057-3960; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105 |
| metadata-local-lexical | contextual-late-reference | contextual-thread, revision-latest, revision-old, graph-vendor, long-10240 | 1/1 | doc://contextual-thread#3057-3960; doc://contextual-thread#0-1197; doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#1018-2217; doc://contextual-thread#2038-3236; doc://graph-vendor#0-75; doc://long-10240#1016-2215 |
| metadata-local-hybrid | exact-identifier | exact-orbit, long-10240, exact-distractor, revision-latest, contextual-thread, revision-old | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://contextual-thread#3057-3960; doc://contextual-thread#0-1197; doc://revision-old#0-81; doc://contextual-thread#1018-2217 |
| metadata-local-hybrid | long-document-coverage | long-10240, exact-orbit | 24/32 | doc://long-10240#9157-10240; doc://long-10240#6101-7299; doc://long-10240#0-1194; doc://long-10240#5081-6280; doc://exact-orbit#0-105; doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://long-10240#2036-3222 |
| metadata-local-hybrid | latest-revision | revision-latest, revision-old, contextual-thread, exact-distractor, exact-orbit | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#3057-3960; doc://contextual-thread#2038-3236; doc://contextual-thread#0-1197; doc://contextual-thread#1018-2217; doc://exact-distractor#0-87; doc://exact-orbit#0-105 |
| metadata-local-hybrid | graph-multihop | graph-team, contextual-thread, exact-distractor, revision-latest, long-10240 | 0/1 | doc://graph-team#0-93; doc://contextual-thread#0-1197; doc://contextual-thread#3057-3960; doc://exact-distractor#0-87; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://revision-latest#0-99; doc://long-10240#0-1194 |
| metadata-local-hybrid | multilingual | multilingual, exact-orbit, injection, long-10240 | 1/1 | doc://multilingual#0-90; doc://exact-orbit#0-105; doc://injection#0-130; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#7120-8320; doc://long-10240#3044-4243; doc://long-10240#2036-3222 |
| metadata-local-hybrid | prompt-injection | contextual-thread, injection, revision-latest, exact-distractor, revision-old | 1/1 | doc://contextual-thread#0-1197; doc://injection#0-130; doc://contextual-thread#3057-3960; doc://contextual-thread#2038-3236; doc://revision-latest#0-99; doc://contextual-thread#1018-2217; doc://exact-distractor#0-87; doc://revision-old#0-81 |
| metadata-local-hybrid | scope-isolation | long-10240, injection | 0/0 | doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://long-10240#0-1194; doc://long-10240#3044-4243; doc://injection#0-130; doc://long-10240#1016-2215; doc://long-10240#7120-8320 |
| metadata-local-hybrid | no-answer | contextual-thread, revision-latest, exact-distractor, exact-orbit, revision-old | 0/0 | doc://contextual-thread#3057-3960; doc://contextual-thread#0-1197; doc://contextual-thread#1018-2217; doc://contextual-thread#2038-3236; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://revision-old#0-81 |
| metadata-local-hybrid | contextual-late-reference | contextual-thread, revision-latest, exact-distractor, long-10240, graph-team | 1/1 | doc://contextual-thread#0-1197; doc://contextual-thread#3057-3960; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://contextual-thread#1018-2217; doc://contextual-thread#2038-3236; doc://long-10240#1016-2215; doc://graph-team#0-93 |
| generated-local-lexical | exact-identifier | exact-orbit, exact-distractor, long-10240, revision-latest, revision-old, multilingual, contextual-thread | 1/1 | doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://long-10240#0-1194; doc://revision-latest#0-99; doc://revision-old#0-81; doc://multilingual#0-90; doc://contextual-thread#3057-3960; doc://contextual-thread#1018-2217 |
| generated-local-lexical | long-document-coverage | exact-orbit, injection, long-10240 | 21/32 | doc://exact-orbit#0-105; doc://injection#0-130; doc://long-10240#9157-10240; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://long-10240#5081-6280 |
| generated-local-lexical | latest-revision | revision-latest, revision-old, contextual-thread, exact-orbit, exact-distractor | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#3057-3960; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://contextual-thread#0-1197; doc://exact-orbit#0-105; doc://exact-distractor#0-87 |
| generated-local-lexical | graph-multihop | graph-team, graph-vendor, contextual-thread, exact-orbit, revision-latest, revision-old, exact-distractor | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://contextual-thread#0-1197; doc://exact-orbit#0-105; doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#3057-3960; doc://exact-distractor#0-87 |
| generated-local-lexical | multilingual | multilingual | 1/1 | doc://multilingual#0-90 |
| generated-local-lexical | prompt-injection | injection, revision-latest, revision-old, exact-orbit, graph-team, contextual-thread | 1/1 | doc://injection#0-130; doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://graph-team#0-93; doc://contextual-thread#3057-3960; doc://contextual-thread#0-1197; doc://contextual-thread#1018-2217 |
| generated-local-lexical | scope-isolation | graph-vendor, long-10240 | 0/0 | doc://graph-vendor#0-75; doc://long-10240#9157-10240; doc://long-10240#6101-7299; doc://long-10240#1016-2215; doc://long-10240#5081-6280; doc://long-10240#2036-3222; doc://long-10240#4064-5260; doc://long-10240#0-1194 |
| generated-local-lexical | no-answer | contextual-thread, revision-latest, exact-orbit, graph-vendor, graph-team | 0/0 | doc://contextual-thread#0-1197; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://contextual-thread#3057-3960; doc://revision-latest#0-99; doc://exact-orbit#0-105; doc://graph-vendor#0-75; doc://graph-team#0-93 |
| generated-local-lexical | contextual-late-reference | contextual-thread, revision-latest, long-10240, exact-orbit, graph-vendor | 1/1 | doc://contextual-thread#0-1197; doc://contextual-thread#3057-3960; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://revision-latest#0-99; doc://long-10240#1016-2215; doc://exact-orbit#0-105; doc://graph-vendor#0-75 |
| generated-local-hybrid | exact-identifier | exact-orbit, long-10240, revision-latest, revision-old, exact-distractor, contextual-thread, multilingual | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://contextual-thread#1018-2217; doc://contextual-thread#3057-3960; doc://multilingual#0-90 |
| generated-local-hybrid | long-document-coverage | long-10240, exact-orbit | 24/32 | doc://long-10240#9157-10240; doc://long-10240#6101-7299; doc://long-10240#5081-6280; doc://long-10240#0-1194; doc://long-10240#8141-9336; doc://exact-orbit#0-105; doc://long-10240#3044-4243; doc://long-10240#2036-3222 |
| generated-local-hybrid | latest-revision | revision-latest, revision-old, contextual-thread, exact-orbit, long-10240 | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#3057-3960; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://contextual-thread#0-1197; doc://exact-orbit#0-105; doc://long-10240#3044-4243 |
| generated-local-hybrid | graph-multihop | graph-team, revision-latest, revision-old, exact-orbit, contextual-thread, injection, graph-vendor | 1/1 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://contextual-thread#0-1197; doc://injection#0-130; doc://contextual-thread#3057-3960; doc://graph-vendor#0-75 |
| generated-local-hybrid | multilingual | multilingual, long-10240, exact-orbit | 1/1 | doc://multilingual#0-90; doc://long-10240#6101-7299; doc://long-10240#0-1194; doc://exact-orbit#0-105; doc://long-10240#3044-4243; doc://long-10240#1016-2215; doc://long-10240#9157-10240; doc://long-10240#8141-9336 |
| generated-local-hybrid | prompt-injection | injection, contextual-thread, revision-latest, exact-orbit, revision-old | 1/1 | doc://injection#0-130; doc://contextual-thread#3057-3960; doc://revision-latest#0-99; doc://contextual-thread#0-1197; doc://exact-orbit#0-105; doc://revision-old#0-81; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217 |
| generated-local-hybrid | scope-isolation | graph-vendor, long-10240, injection | 0/0 | doc://graph-vendor#0-75; doc://long-10240#6101-7299; doc://long-10240#9157-10240; doc://long-10240#1016-2215; doc://long-10240#5081-6280; doc://injection#0-130; doc://long-10240#4064-5260; doc://long-10240#3044-4243 |
| generated-local-hybrid | no-answer | contextual-thread, exact-orbit, revision-latest, exact-distractor, multilingual | 0/0 | doc://contextual-thread#0-1197; doc://contextual-thread#1018-2217; doc://contextual-thread#2038-3236; doc://contextual-thread#3057-3960; doc://exact-orbit#0-105; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://multilingual#0-90 |
| generated-local-hybrid | contextual-late-reference | contextual-thread, revision-latest, multilingual, exact-orbit, exact-distractor | 1/1 | doc://contextual-thread#0-1197; doc://contextual-thread#1018-2217; doc://contextual-thread#3057-3960; doc://contextual-thread#2038-3236; doc://revision-latest#0-99; doc://multilingual#0-90; doc://exact-orbit#0-105; doc://exact-distractor#0-87 |
| raw-endpoint-dense | exact-identifier | exact-orbit, exact-distractor, long-10240, revision-old, revision-latest | 1/1 | doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://long-10240#0-1194; doc://revision-old#0-81; doc://revision-latest#0-99; doc://long-10240#9157-10240; doc://long-10240#8141-9336; doc://long-10240#5081-6280 |
| raw-endpoint-dense | long-document-coverage | long-10240, injection | 23/32 | doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://long-10240#9157-10240; doc://long-10240#4064-5260; doc://long-10240#7120-8320; doc://injection#0-130; doc://long-10240#0-1194; doc://long-10240#1016-2215 |
| raw-endpoint-dense | latest-revision | revision-latest, revision-old, long-10240, exact-distractor, contextual-thread | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://long-10240#1016-2215; doc://long-10240#3044-4243; doc://exact-distractor#0-87; doc://long-10240#8141-9336; doc://contextual-thread#3057-3960; doc://long-10240#4064-5260 |
| raw-endpoint-dense | graph-multihop | graph-team, long-10240, graph-vendor, contextual-thread | 1/1 | doc://graph-team#0-93; doc://long-10240#0-1194; doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://graph-vendor#0-75; doc://long-10240#9157-10240; doc://contextual-thread#3057-3960; doc://long-10240#6101-7299 |
| raw-endpoint-dense | multilingual | multilingual, long-10240, exact-distractor | 1/1 | doc://multilingual#0-90; doc://long-10240#2036-3222; doc://long-10240#5081-6280; doc://long-10240#8141-9336; doc://exact-distractor#0-87; doc://long-10240#9157-10240; doc://long-10240#0-1194; doc://long-10240#3044-4243 |
| raw-endpoint-dense | prompt-injection | injection, long-10240, contextual-thread | 1/1 | doc://injection#0-130; doc://long-10240#3044-4243; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://contextual-thread#3057-3960; doc://long-10240#8141-9336; doc://long-10240#4064-5260; doc://long-10240#7120-8320 |
| raw-endpoint-dense | scope-isolation | long-10240, injection | 0/0 | doc://long-10240#3044-4243; doc://long-10240#4064-5260; doc://injection#0-130; doc://long-10240#7120-8320; doc://long-10240#1016-2215; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://long-10240#9157-10240 |
| raw-endpoint-dense | no-answer | injection, long-10240, exact-distractor | 0/0 | doc://injection#0-130; doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://exact-distractor#0-87; doc://long-10240#4064-5260; doc://long-10240#6101-7299; doc://long-10240#9157-10240 |
| raw-endpoint-dense | contextual-late-reference | contextual-thread, exact-orbit, long-10240, revision-latest, exact-distractor | 1/1 | doc://contextual-thread#0-1197; doc://contextual-thread#3057-3960; doc://exact-orbit#0-105; doc://long-10240#4064-5260; doc://long-10240#1016-2215; doc://revision-latest#0-99; doc://long-10240#7120-8320; doc://exact-distractor#0-87 |
| raw-endpoint-hybrid | exact-identifier | exact-orbit, long-10240, exact-distractor, revision-latest, revision-old, contextual-thread | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#3057-3960; doc://contextual-thread#0-1197; doc://contextual-thread#2038-3236 |
| raw-endpoint-hybrid | long-document-coverage | long-10240 | 26/32 | doc://long-10240#9157-10240; doc://long-10240#8141-9336; doc://long-10240#3044-4243; doc://long-10240#0-1194; doc://long-10240#4064-5260; doc://long-10240#7120-8320; doc://long-10240#1016-2215; doc://long-10240#5081-6280 |
| raw-endpoint-hybrid | latest-revision | revision-latest, revision-old, contextual-thread, exact-distractor, long-10240 | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#3057-3960; doc://exact-distractor#0-87; doc://long-10240#3044-4243; doc://contextual-thread#0-1197; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217 |
| raw-endpoint-hybrid | graph-multihop | graph-team, graph-vendor, contextual-thread, long-10240 | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://contextual-thread#3057-3960; doc://contextual-thread#2038-3236; doc://long-10240#0-1194; doc://contextual-thread#0-1197; doc://long-10240#3044-4243; doc://contextual-thread#1018-2217 |
| raw-endpoint-hybrid | multilingual | multilingual, long-10240, exact-distractor | 1/1 | doc://multilingual#0-90; doc://long-10240#2036-3222; doc://long-10240#5081-6280; doc://long-10240#8141-9336; doc://exact-distractor#0-87; doc://long-10240#9157-10240; doc://long-10240#0-1194; doc://long-10240#3044-4243 |
| raw-endpoint-hybrid | prompt-injection | injection, contextual-thread, revision-latest, revision-old, exact-distractor | 1/1 | doc://injection#0-130; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://contextual-thread#3057-3960; doc://revision-latest#0-99; doc://contextual-thread#0-1197; doc://revision-old#0-81; doc://exact-distractor#0-87 |
| raw-endpoint-hybrid | scope-isolation | long-10240, injection | 0/0 | doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://long-10240#4064-5260; doc://long-10240#1016-2215; doc://long-10240#7120-8320; doc://long-10240#5081-6280; doc://injection#0-130; doc://long-10240#0-1194 |
| raw-endpoint-hybrid | no-answer | exact-distractor, contextual-thread, revision-latest, revision-old, exact-orbit | 0/0 | doc://exact-distractor#0-87; doc://contextual-thread#3057-3960; doc://contextual-thread#2038-3236; doc://contextual-thread#0-1197; doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://contextual-thread#1018-2217 |
| raw-endpoint-hybrid | contextual-late-reference | contextual-thread, revision-latest, exact-orbit, long-10240, exact-distractor, revision-old, graph-vendor | 1/1 | doc://contextual-thread#0-1197; doc://contextual-thread#3057-3960; doc://revision-latest#0-99; doc://exact-orbit#0-105; doc://long-10240#1016-2215; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://graph-vendor#0-75 |
| metadata-endpoint-dense | exact-identifier | exact-orbit, exact-distractor, long-10240, revision-old, graph-vendor | 1/1 | doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://long-10240#0-1194; doc://revision-old#0-81; doc://graph-vendor#0-75; doc://long-10240#5081-6280; doc://long-10240#1016-2215; doc://long-10240#6101-7299 |
| metadata-endpoint-dense | long-document-coverage | long-10240 | 27/32 | doc://long-10240#8141-9336; doc://long-10240#9157-10240; doc://long-10240#7120-8320; doc://long-10240#0-1194; doc://long-10240#3044-4243; doc://long-10240#5081-6280; doc://long-10240#2036-3222; doc://long-10240#1016-2215 |
| metadata-endpoint-dense | latest-revision | revision-latest, revision-old, exact-distractor, long-10240, contextual-thread | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://long-10240#1016-2215; doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://contextual-thread#3057-3960 |
| metadata-endpoint-dense | graph-multihop | graph-team, graph-vendor, long-10240, contextual-thread | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#9157-10240; doc://contextual-thread#3057-3960; doc://long-10240#5081-6280; doc://long-10240#8141-9336 |
| metadata-endpoint-dense | multilingual | multilingual, long-10240, exact-distractor | 1/1 | doc://multilingual#0-90; doc://long-10240#2036-3222; doc://long-10240#9157-10240; doc://long-10240#5081-6280; doc://exact-distractor#0-87; doc://long-10240#0-1194; doc://long-10240#8141-9336; doc://long-10240#6101-7299 |
| metadata-endpoint-dense | prompt-injection | injection, contextual-thread, long-10240 | 1/1 | doc://injection#0-130; doc://contextual-thread#3057-3960; doc://contextual-thread#1018-2217; doc://contextual-thread#2038-3236; doc://long-10240#8141-9336; doc://long-10240#7120-8320; doc://long-10240#1016-2215; doc://long-10240#5081-6280 |
| metadata-endpoint-dense | scope-isolation | injection, long-10240, exact-distractor | 0/0 | doc://injection#0-130; doc://long-10240#7120-8320; doc://long-10240#1016-2215; doc://long-10240#8141-9336; doc://long-10240#4064-5260; doc://exact-distractor#0-87; doc://long-10240#5081-6280; doc://long-10240#9157-10240 |
| metadata-endpoint-dense | no-answer | injection, exact-distractor, long-10240, contextual-thread | 0/0 | doc://injection#0-130; doc://exact-distractor#0-87; doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://long-10240#1016-2215; doc://contextual-thread#3057-3960; doc://long-10240#0-1194 |
| metadata-endpoint-dense | contextual-late-reference | contextual-thread, exact-distractor, long-10240, exact-orbit, revision-latest | 1/1 | doc://contextual-thread#0-1197; doc://contextual-thread#3057-3960; doc://exact-distractor#0-87; doc://long-10240#6101-7299; doc://long-10240#7120-8320; doc://exact-orbit#0-105; doc://revision-latest#0-99; doc://long-10240#4064-5260 |
| metadata-endpoint-hybrid | exact-identifier | exact-orbit, long-10240, exact-distractor, revision-old, revision-latest, graph-vendor | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://revision-latest#0-99; doc://graph-vendor#0-75; doc://long-10240#1016-2215; doc://long-10240#9157-10240 |
| metadata-endpoint-hybrid | long-document-coverage | long-10240 | 26/32 | doc://long-10240#9157-10240; doc://long-10240#8141-9336; doc://long-10240#0-1194; doc://long-10240#3044-4243; doc://long-10240#7120-8320; doc://long-10240#5081-6280; doc://long-10240#6101-7299; doc://long-10240#4064-5260 |
| metadata-endpoint-hybrid | latest-revision | revision-latest, revision-old, exact-distractor, contextual-thread, long-10240 | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://contextual-thread#3057-3960; doc://contextual-thread#0-1197; doc://long-10240#3044-4243; doc://long-10240#1016-2215; doc://contextual-thread#2038-3236 |
| metadata-endpoint-hybrid | graph-multihop | graph-team, graph-vendor, contextual-thread, long-10240 | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://contextual-thread#3057-3960; doc://long-10240#0-1194; doc://contextual-thread#2038-3236; doc://contextual-thread#0-1197; doc://long-10240#6101-7299; doc://contextual-thread#1018-2217 |
| metadata-endpoint-hybrid | multilingual | multilingual, long-10240, exact-distractor | 1/1 | doc://multilingual#0-90; doc://long-10240#2036-3222; doc://long-10240#9157-10240; doc://long-10240#5081-6280; doc://exact-distractor#0-87; doc://long-10240#0-1194; doc://long-10240#8141-9336; doc://long-10240#6101-7299 |
| metadata-endpoint-hybrid | prompt-injection | injection, contextual-thread, revision-latest, exact-distractor, revision-old | 1/1 | doc://injection#0-130; doc://contextual-thread#3057-3960; doc://contextual-thread#1018-2217; doc://contextual-thread#2038-3236; doc://contextual-thread#0-1197; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81 |
| metadata-endpoint-hybrid | scope-isolation | long-10240, injection | 0/0 | doc://long-10240#8141-9336; doc://long-10240#1016-2215; doc://long-10240#7120-8320; doc://injection#0-130; doc://long-10240#5081-6280; doc://long-10240#0-1194; doc://long-10240#3044-4243; doc://long-10240#4064-5260 |
| metadata-endpoint-hybrid | no-answer | exact-distractor, contextual-thread, revision-latest, revision-old, graph-vendor | 0/0 | doc://exact-distractor#0-87; doc://contextual-thread#3057-3960; doc://contextual-thread#0-1197; doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://graph-vendor#0-75 |
| metadata-endpoint-hybrid | contextual-late-reference | contextual-thread, revision-latest, exact-distractor, revision-old, exact-orbit, long-10240, graph-vendor | 1/1 | doc://contextual-thread#0-1197; doc://contextual-thread#3057-3960; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://long-10240#1016-2215; doc://graph-vendor#0-75 |
| generated-endpoint-dense | exact-identifier | exact-distractor, exact-orbit, long-10240, revision-latest, revision-old | 1/1 | doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://long-10240#9157-10240; doc://revision-latest#0-99; doc://long-10240#1016-2215; doc://revision-old#0-81; doc://long-10240#5081-6280 |
| generated-endpoint-dense | long-document-coverage | long-10240, exact-orbit, injection | 20/32 | doc://long-10240#8141-9336; doc://long-10240#0-1194; doc://long-10240#9157-10240; doc://long-10240#5081-6280; doc://long-10240#1016-2215; doc://exact-orbit#0-105; doc://injection#0-130; doc://long-10240#2036-3222 |
| generated-endpoint-dense | latest-revision | revision-latest, revision-old, long-10240, exact-distractor, exact-orbit, contextual-thread | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://long-10240#3044-4243; doc://long-10240#1016-2215; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#9157-10240; doc://contextual-thread#3057-3960 |
| generated-endpoint-dense | graph-multihop | graph-team, graph-vendor, long-10240, contextual-thread | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#5081-6280; doc://long-10240#9157-10240; doc://contextual-thread#3057-3960; doc://long-10240#8141-9336 |
| generated-endpoint-dense | multilingual | multilingual, long-10240, exact-orbit | 1/1 | doc://multilingual#0-90; doc://long-10240#2036-3222; doc://long-10240#5081-6280; doc://long-10240#9157-10240; doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://long-10240#8141-9336; doc://long-10240#1016-2215 |
| generated-endpoint-dense | prompt-injection | injection, contextual-thread, revision-latest, revision-old, exact-orbit, exact-distractor | 1/1 | doc://injection#0-130; doc://contextual-thread#3057-3960; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://exact-distractor#0-87 |
| generated-endpoint-dense | scope-isolation | injection, long-10240, exact-distractor | 0/0 | doc://injection#0-130; doc://long-10240#7120-8320; doc://long-10240#1016-2215; doc://long-10240#5081-6280; doc://long-10240#8141-9336; doc://long-10240#3044-4243; doc://exact-distractor#0-87; doc://long-10240#4064-5260 |
| generated-endpoint-dense | no-answer | injection, exact-distractor, exact-orbit, long-10240, multilingual | 0/0 | doc://injection#0-130; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#6101-7299; doc://long-10240#5081-6280; doc://long-10240#8141-9336; doc://multilingual#0-90; doc://long-10240#0-1194 |
| generated-endpoint-dense | contextual-late-reference | contextual-thread, exact-orbit, long-10240 | 1/1 | doc://contextual-thread#0-1197; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://exact-orbit#0-105; doc://contextual-thread#3057-3960; doc://long-10240#6101-7299; doc://long-10240#4064-5260; doc://long-10240#0-1194 |
| generated-endpoint-hybrid | exact-identifier | exact-orbit, long-10240, exact-distractor, revision-latest, revision-old, multilingual | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://revision-old#0-81; doc://long-10240#9157-10240; doc://multilingual#0-90; doc://long-10240#1016-2215 |
| generated-endpoint-hybrid | long-document-coverage | long-10240, exact-orbit, injection | 21/32 | doc://long-10240#0-1194; doc://long-10240#9157-10240; doc://exact-orbit#0-105; doc://long-10240#8141-9336; doc://injection#0-130; doc://long-10240#5081-6280; doc://long-10240#1016-2215; doc://long-10240#3044-4243 |
| generated-endpoint-hybrid | latest-revision | revision-latest, revision-old, contextual-thread, long-10240, exact-distractor, exact-orbit | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://contextual-thread#3057-3960; doc://long-10240#3044-4243; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#1016-2215; doc://long-10240#9157-10240 |
| generated-endpoint-hybrid | graph-multihop | graph-team, graph-vendor, contextual-thread, long-10240, exact-orbit | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://contextual-thread#3057-3960; doc://long-10240#6101-7299; doc://long-10240#9157-10240; doc://long-10240#0-1194; doc://exact-orbit#0-105; doc://contextual-thread#0-1197 |
| generated-endpoint-hybrid | multilingual | multilingual, long-10240, exact-orbit | 1/1 | doc://multilingual#0-90; doc://long-10240#2036-3222; doc://long-10240#5081-6280; doc://long-10240#9157-10240; doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://long-10240#8141-9336; doc://long-10240#1016-2215 |
| generated-endpoint-hybrid | prompt-injection | injection, revision-latest, contextual-thread, revision-old, exact-orbit, exact-distractor | 1/1 | doc://injection#0-130; doc://revision-latest#0-99; doc://contextual-thread#3057-3960; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://contextual-thread#2038-3236; doc://contextual-thread#1018-2217; doc://exact-distractor#0-87 |
| generated-endpoint-hybrid | scope-isolation | long-10240, graph-vendor, injection | 0/0 | doc://long-10240#1016-2215; doc://long-10240#5081-6280; doc://graph-vendor#0-75; doc://long-10240#9157-10240; doc://injection#0-130; doc://long-10240#7120-8320; doc://long-10240#8141-9336; doc://long-10240#3044-4243 |
| generated-endpoint-hybrid | no-answer | exact-orbit, exact-distractor, revision-latest, contextual-thread, injection, long-10240, multilingual | 0/0 | doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://contextual-thread#3057-3960; doc://injection#0-130; doc://long-10240#6101-7299; doc://contextual-thread#2038-3236; doc://multilingual#0-90 |
| generated-endpoint-hybrid | contextual-late-reference | contextual-thread, exact-orbit, revision-latest, long-10240 | 1/1 | doc://contextual-thread#0-1197; doc://contextual-thread#2038-3236; doc://contextual-thread#3057-3960; doc://contextual-thread#1018-2217; doc://exact-orbit#0-105; doc://revision-latest#0-99; doc://long-10240#1016-2215; doc://long-10240#6101-7299 |

The JSON companion retains every prompt, raw model output, generated context, per-case metric, and complete source-backed evidence span.
