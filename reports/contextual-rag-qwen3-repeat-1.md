# Generated Contextual RAG Evaluation

Paired, query-independent Contextual Retrieval ablation over identical structure-aware chunks. Raw passage, deterministic metadata context, and generated context are compared. Generated context is indexed by BM25 and embeddings but is never returned as answer evidence.

Top-K: 8. Production ready: False.
Promotion recommended: False.

## Models and exact method

- Context generator: `qwen3:8b` / `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`
- Embedding model: `qwen3-embedding:4b` / `df5bd2e3c74cd8d069d21dc038f1b359fcdc9458fce1c99bd43c9eb1518ff907`
- Prompt contract: `contextual-retrieval-v2`; temperature 0, seed 0, 16K context, 160 output tokens.
- The complete synthetic document and one chunk were supplied for each call. No user query was supplied.
- Accepted context was prepended to the search representation only. Retrieved evidence remained the unchanged canonical source span.

## Context generation

| Chunks | Successful | Generated now | Cache hits | Failures | Entity grounding | Source spans | Model latency ms | Prompt tokens | Output tokens |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 23 | 23 | 0 | 23 | 0 | 1.000 | 1.000 | 14810.5 | 31540 | 866 |

## Retrieval results

| Lane | Context | Retrieval | Embedding | Document recall | Fact recall | Document MRR | Fact MRR | nDCG | p50 ms | DB bytes | Indexed chars |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| raw-local-lexical | raw | lexical | deterministic-local-v1 | 1.000 | 0.737 | 0.929 | 0.267 | 0.923 | 0.355 | 192512 | 17561 |
| raw-local-hybrid | raw | hybrid | deterministic-local-v1 | 1.000 | 0.763 | 0.929 | 0.326 | 0.920 | 0.873 | 192512 | 17561 |
| metadata-local-lexical | metadata | lexical | deterministic-local-v1 | 1.000 | 0.737 | 0.929 | 0.267 | 0.923 | 0.333 | 204800 | 19643 |
| metadata-local-hybrid | metadata | hybrid | deterministic-local-v1 | 0.929 | 0.737 | 0.929 | 0.311 | 0.892 | 0.822 | 204800 | 19643 |
| generated-local-lexical | generated | lexical | deterministic-local-v1 | 1.000 | 0.684 | 0.929 | 0.260 | 0.936 | 0.755 | 208896 | 22017 |
| generated-local-hybrid | generated | hybrid | deterministic-local-v1 | 0.929 | 0.737 | 1.000 | 0.354 | 0.945 | 0.876 | 208896 | 22017 |
| raw-endpoint-dense | raw | dense | qwen3-embedding:4b | 1.000 | 0.737 | 1.000 | 0.341 | 0.971 | 395.039 | 937984 | 17561 |
| raw-endpoint-hybrid | raw | hybrid | qwen3-embedding:4b | 1.000 | 0.816 | 1.000 | 0.348 | 1.000 | 377.155 | 937984 | 17561 |
| metadata-endpoint-dense | metadata | dense | qwen3-embedding:4b | 1.000 | 0.842 | 1.000 | 0.362 | 0.989 | 380.242 | 950272 | 19643 |
| metadata-endpoint-hybrid | metadata | hybrid | qwen3-embedding:4b | 1.000 | 0.816 | 1.000 | 0.349 | 1.000 | 343.680 | 950272 | 19643 |
| generated-endpoint-dense | generated | dense | qwen3-embedding:4b | 1.000 | 0.684 | 1.000 | 0.365 | 0.989 | 303.947 | 966656 | 22017 |
| generated-endpoint-hybrid | generated | hybrid | qwen3-embedding:4b | 1.000 | 0.789 | 1.000 | 0.360 | 1.000 | 353.083 | 966656 | 22017 |

## Paired deltas: generated minus each baseline

| Comparison | Retrieval family | Document recall | Fact recall | Document MRR | Fact MRR | nDCG | p50 ms | DB bytes | Indexed chars |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| generated-vs-raw | local-lexical | +0.000 | -0.053 | +0.000 | -0.007 | +0.013 | +0.400 | +16384 | +4456 |
| generated-vs-raw | local-hybrid | -0.071 | -0.026 | +0.071 | +0.029 | +0.025 | +0.003 | +16384 | +4456 |
| generated-vs-raw | endpoint-dense | +0.000 | -0.053 | +0.000 | +0.024 | +0.018 | -91.092 | +28672 | +4456 |
| generated-vs-raw | endpoint-hybrid | +0.000 | -0.026 | +0.000 | +0.012 | +0.000 | -24.071 | +28672 | +4456 |
| generated-vs-metadata | local-lexical | +0.000 | -0.053 | +0.000 | -0.007 | +0.013 | +0.422 | +4096 | +2374 |
| generated-vs-metadata | local-hybrid | +0.000 | +0.000 | +0.071 | +0.044 | +0.053 | +0.054 | +4096 | +2374 |
| generated-vs-metadata | endpoint-dense | +0.000 | -0.158 | +0.000 | +0.002 | +0.000 | -76.295 | +16384 | +2374 |
| generated-vs-metadata | endpoint-hybrid | +0.000 | -0.026 | +0.000 | +0.011 | +0.000 | +9.403 | +16384 | +2374 |

## Decision

Do not promote generated contextual retrieval from this run.

## Limitations

- The corpus is synthetic and small.
- The frozen queries mostly contain exact identifiers; realistic paraphrase and thread-anaphora cases are still needed.
- One live run does not establish variance or production readiness.
- Generated context is model output and may add unverified prose even when exact identifiers are grounded.

## Generated-context audit

### exact-orbit / tenant-alpha/primary/exact-orbit:chunk:0

- Status: `ok`; cache hit: `True`; source: `0-105`.
- Source span valid: `True`; latency: `1884.5 ms`.
- Generated context: Document details the launch decision for Project ORBIT-731, specifying its launch date, location, and budget from the Orbit launch decision record.
- Error: none
- Raw model output:

```json
{"context": "Document details the launch decision for Project ORBIT-731, specifying its launch date, location, and budget from the Orbit launch decision record."}
```

### exact-distractor / tenant-alpha/primary/exact-distractor:chunk:0

- Status: `ok`; cache hit: `True`; source: `0-87`.
- Source span valid: `True`; latency: `491.4 ms`.
- Generated context: The document discusses Project ORBIT-713, a separate project from the main subject, using East Annex with a launch date of 2027-11-04.
- Error: none
- Raw model output:

```json
{"context": "The document discusses Project ORBIT-713, a separate project from the main subject, using East Annex with a launch date of 2027-11-04."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:0

- Status: `ok`; cache hit: `True`; source: `0-1194`.
- Source span valid: `True`; latency: `604.5 ms`.
- Generated context: A synthetic operations ledger document containing factual entries with required values, used for testing retrieval systems without real data.
- Error: none
- Raw model output:

```json
{"context": "A synthetic operations ledger document containing factual entries with required values, used for testing retrieval systems without real data."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:1

- Status: `ok`; cache hit: `True`; source: `1016-2215`.
- Source span valid: `True`; latency: `713.3 ms`.
- Generated context: The document is a synthetic operations ledger, and this chunk contains a fact about the North Annex as a required value in a synthetic context exercise.
- Error: none
- Raw model output:

```json
{"context": "The document is a synthetic operations ledger, and this chunk contains a fact about the North Annex as a required value in a synthetic context exercise."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:2

- Status: `ok`; cache hit: `True`; source: `2036-3222`.
- Source span valid: `True`; latency: `700.1 ms`.
- Generated context: The document is a synthetic operations ledger, and this chunk contains a fact about Omar Shah as part of the ledger's structured data.
- Error: none
- Raw model output:

```json
{"context": "The document is a synthetic operations ledger, and this chunk contains a fact about Omar Shah as part of the ledger's structured data."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:3

- Status: `ok`; cache hit: `True`; source: `3044-4243`.
- Source span valid: `True`; latency: `739.9 ms`.
- Generated context: The document is a synthetic operations ledger, and this chunk contains FACT F10 to F14 with specific required values and repetitive context about bounded retrieval.
- Error: none
- Raw model output:

```json
{"context": "The document is a synthetic operations ledger, and this chunk contains FACT F10 to F14 with specific required values and repetitive context about bounded retrieval."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:4

- Status: `ok`; cache hit: `True`; source: `4064-5260`.
- Source span valid: `True`; latency: `774.4 ms`.
- Generated context: The document is a synthetic operations ledger, and this chunk contains FACT F13 with the required value Mira Chen, part of the ledger's structured data entries.
- Error: none
- Raw model output:

```json
{"context": "The document is a synthetic operations ledger, and this chunk contains FACT F13 with the required value Mira Chen, part of the ledger's structured data entries."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:5

- Status: `ok`; cache hit: `True`; source: `5081-6280`.
- Source span valid: `True`; latency: `786.8 ms`.
- Generated context: The document is a synthetic operations ledger detailing various facts with required values, and this chunk contains entries from Section 16 to Section 20, including financial figures and identifiers.
- Error: none
- Raw model output:

```json
{"context": "The document is a synthetic operations ledger detailing various facts with required values, and this chunk contains entries from Section 16 to Section 20, including financial figures and identifiers."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:6

- Status: `ok`; cache hit: `True`; source: `6101-7299`.
- Source span valid: `True`; latency: `732.8 ms`.
- Generated context: The document is a synthetic operations ledger, and this chunk contains factual entries related to financial values, dates, and personnel names within the ledger's structured format.
- Error: none
- Raw model output:

```json
{"context": "The document is a synthetic operations ledger, and this chunk contains factual entries related to financial values, dates, and personnel names within the ledger's structured format."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:7

- Status: `ok`; cache hit: `True`; source: `7120-8320`.
- Source span valid: `True`; latency: `683.0 ms`.
- Generated context: The document is a synthetic operations ledger, and this chunk contains facts about financial values and locations used for testing retrieval systems.
- Error: none
- Raw model output:

```json
{"context": "The document is a synthetic operations ledger, and this chunk contains facts about financial values and locations used for testing retrieval systems."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:8

- Status: `ok`; cache hit: `True`; source: `8141-9336`.
- Source span valid: `True`; latency: `745.7 ms`.
- Generated context: The parent document is a synthetic operations ledger, and this chunk contains FACT F30 with the required value 'Silver Pine' as part of the ledger's structured data.
- Error: none
- Raw model output:

```json
{"context": "The parent document is a synthetic operations ledger, and this chunk contains FACT F30 with the required value 'Silver Pine' as part of the ledger's structured data."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:9

- Status: `ok`; cache hit: `True`; source: `9157-10240`.
- Source span valid: `True`; latency: `798.8 ms`.
- Generated context: The document is a synthetic operations ledger, and this chunk contains facts about synthetic contexts used for bounded retrieval exercises, including entries like VECTOR-963, Silver Pine, and Keiko Tanaka.
- Error: none
- Raw model output:

```json
{"context": "The document is a synthetic operations ledger, and this chunk contains facts about synthetic contexts used for bounded retrieval exercises, including entries like VECTOR-963, Silver Pine, and Keiko Tanaka."}
```

### revision-old / tenant-alpha/primary/revision-old:chunk:0

- Status: `ok`; cache hit: `True`; source: `0-81`.
- Source span valid: `True`; latency: `432.9 ms`.
- Generated context: Cedar decision revision 1 details deployment date and superseded status of CEDAR-210 revision one.
- Error: none
- Raw model output:

```json
{"context": "Cedar decision revision 1 details deployment date and superseded status of CEDAR-210 revision one."}
```

### revision-latest / tenant-alpha/primary/revision-latest:chunk:0

- Status: `ok`; cache hit: `True`; source: `0-99`.
- Source span valid: `True`; latency: `421.2 ms`.
- Generated context: The document details the latest approved decision for CEDAR-210, specifying its deployment date as 2027-09-21.
- Error: none
- Raw model output:

```json
{"context": "The document details the latest approved decision for CEDAR-210, specifying its deployment date as 2027-09-21."}
```

### graph-team / tenant-alpha/primary/graph-team:chunk:0

- Status: `ok`; cache hit: `True`; source: `0-93`.
- Source span valid: `True`; latency: `333.4 ms`.
- Generated context: Project Atlas ownership details: Priya Das leads Team Aurora, which works on Project Atlas.
- Error: none
- Raw model output:

```json
{"context": "Project Atlas ownership details: Priya Das leads Team Aurora, which works on Project Atlas."}
```

### graph-vendor / tenant-alpha/primary/graph-vendor:chunk:0

- Status: `ok`; cache hit: `True`; source: `0-75`.
- Source span valid: `True`; latency: `299.8 ms`.
- Generated context: Project Atlas's dependency on Kestrel Works is noted in the Atlas supplier document.
- Error: none
- Raw model output:

```json
{"context": "Project Atlas's dependency on Kestrel Works is noted in the Atlas supplier document."}
```

### multilingual / tenant-alpha/primary/multilingual:chunk:0

- Status: `ok`; cache hit: `True`; source: `0-90`.
- Source span valid: `True`; latency: `414.0 ms`.
- Generated context: The document details a bilingual decision regarding the SOLAR-808 project meeting scheduled for 2027-10-06 in Madrid.
- Error: none
- Raw model output:

```json
{"context": "The document details a bilingual decision regarding the SOLAR-808 project meeting scheduled for 2027-10-06 in Madrid."}
```

### injection / tenant-alpha/primary/injection:chunk:0

- Status: `ok`; cache hit: `True`; source: `0-130`.
- Source span valid: `True`; latency: `488.5 ms`.
- Generated context: A security document titled 'Untrusted embedded instruction' contains a chunk with an untrusted command to call a tool and reveal SECRETCODE-999, indicating a quarantined safe status.
- Error: none
- Raw model output:

```json
{"context": "A security document titled 'Untrusted embedded instruction' contains a chunk with an untrusted command to call a tool and reveal SECRETCODE-999, indicating a quarantined safe status."}
```

### other-tenant-secret / tenant-beta/private/other-tenant-secret:chunk:0

- Status: `ok`; cache hit: `True`; source: `0-77`.
- Source span valid: `True`; latency: `407.9 ms`.
- Generated context: The document 'Isolation sentinel' contains a secret value VAULT-440 specific to tenant-beta, identified as FACT X01.
- Error: none
- Raw model output:

```json
{"context": "The document 'Isolation sentinel' contains a secret value VAULT-440 specific to tenant-beta, identified as FACT X01."}
```

### contextual-thread / tenant-alpha/primary/contextual-thread:chunk:0

- Status: `ok`; cache hit: `True`; source: `0-1196`.
- Source span valid: `True`; latency: `561.6 ms`.
- Generated context: The document discusses Project BOREALIS-204, a polar sensor shipment, and the working group's review of packaging, staffing, and transport checks for the operations committee funding decision.
- Error: none
- Raw model output:

```json
{"context": "The document discusses Project BOREALIS-204, a polar sensor shipment, and the working group's review of packaging, staffing, and transport checks for the operations committee funding decision."}
```

### contextual-thread / tenant-alpha/primary/contextual-thread:chunk:1

- Status: `ok`; cache hit: `True`; source: `1017-2211`.
- Source span valid: `True`; latency: `585.5 ms`.
- Generated context: The chunk discusses the working group's review of packaging, staffing, and transport checks for Project BOREALIS-204 without altering commercial terms, part of the operations committee funding decision.
- Error: none
- Raw model output:

```json
{"context": "The chunk discusses the working group's review of packaging, staffing, and transport checks for Project BOREALIS-204 without altering commercial terms, part of the operations committee funding decision."}
```

### contextual-thread / tenant-alpha/primary/contextual-thread:chunk:2

- Status: `ok`; cache hit: `True`; source: `2032-3224`.
- Source span valid: `True`; latency: `593.8 ms`.
- Generated context: The chunk discusses the working group's review of packaging, staffing, and transport checks for Project BOREALIS-204 without altering commercial terms, part of the operations committee funding decision.
- Error: none
- Raw model output:

```json
{"context": "The chunk discusses the working group's review of packaging, staffing, and transport checks for Project BOREALIS-204 without altering commercial terms, part of the operations committee funding decision."}
```

### contextual-thread / tenant-alpha/primary/contextual-thread:chunk:3

- Status: `ok`; cache hit: `True`; source: `3045-3976`.
- Source span valid: `True`; latency: `616.8 ms`.
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
| metadata-endpoint-dense | exact-identifier | exact-orbit, exact-distractor, long-10240, revision-old, graph-vendor | 1/1 | doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://long-10240#0-1194; doc://revision-old#0-81; doc://graph-vendor#0-75; doc://long-10240#5081-6280; doc://long-10240#1016-2215; doc://long-10240#9157-10240 |
| metadata-endpoint-dense | long-document-coverage | long-10240 | 27/32 | doc://long-10240#8141-9336; doc://long-10240#9157-10240; doc://long-10240#7120-8320; doc://long-10240#3044-4243; doc://long-10240#0-1194; doc://long-10240#5081-6280; doc://long-10240#2036-3222; doc://long-10240#1016-2215 |
| metadata-endpoint-dense | latest-revision | revision-latest, revision-old, exact-distractor, long-10240, contextual-thread | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://long-10240#1016-2215; doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://contextual-thread#0-1196 |
| metadata-endpoint-dense | graph-multihop | graph-team, graph-vendor, long-10240, contextual-thread | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#9157-10240; doc://contextual-thread#3045-3976; doc://long-10240#5081-6280; doc://long-10240#8141-9336 |
| metadata-endpoint-dense | multilingual | multilingual, long-10240, exact-distractor | 1/1 | doc://multilingual#0-90; doc://long-10240#2036-3222; doc://long-10240#9157-10240; doc://long-10240#5081-6280; doc://exact-distractor#0-87; doc://long-10240#0-1194; doc://long-10240#8141-9336; doc://long-10240#6101-7299 |
| metadata-endpoint-dense | prompt-injection | injection, contextual-thread, long-10240 | 1/1 | doc://injection#0-130; doc://contextual-thread#3045-3976; doc://contextual-thread#1017-2211; doc://long-10240#7120-8320; doc://long-10240#8141-9336; doc://contextual-thread#2032-3224; doc://long-10240#1016-2215; doc://long-10240#5081-6280 |
| metadata-endpoint-dense | scope-isolation | injection, long-10240, exact-distractor | 0/0 | doc://injection#0-130; doc://long-10240#7120-8320; doc://long-10240#1016-2215; doc://long-10240#8141-9336; doc://long-10240#4064-5260; doc://exact-distractor#0-87; doc://long-10240#5081-6280; doc://long-10240#3044-4243 |
| metadata-endpoint-dense | no-answer | injection, exact-distractor, long-10240 | 0/0 | doc://injection#0-130; doc://exact-distractor#0-87; doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://long-10240#1016-2215; doc://long-10240#7120-8320; doc://long-10240#0-1194 |
| metadata-endpoint-dense | contextual-late-reference | contextual-thread, exact-distractor, long-10240, exact-orbit | 0/1 | doc://contextual-thread#0-1196; doc://exact-distractor#0-87; doc://long-10240#7120-8320; doc://long-10240#6101-7299; doc://long-10240#4064-5260; doc://long-10240#2036-3222; doc://exact-orbit#0-105; doc://long-10240#1016-2215 |
| metadata-endpoint-hybrid | exact-identifier | exact-orbit, long-10240, exact-distractor, revision-old, revision-latest, graph-vendor | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://revision-latest#0-99; doc://graph-vendor#0-75; doc://long-10240#1016-2215; doc://long-10240#9157-10240 |
| metadata-endpoint-hybrid | long-document-coverage | long-10240 | 26/32 | doc://long-10240#9157-10240; doc://long-10240#8141-9336; doc://long-10240#0-1194; doc://long-10240#3044-4243; doc://long-10240#7120-8320; doc://long-10240#5081-6280; doc://long-10240#6101-7299; doc://long-10240#4064-5260 |
| metadata-endpoint-hybrid | latest-revision | revision-latest, revision-old, exact-distractor, contextual-thread, long-10240 | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://contextual-thread#0-1196; doc://long-10240#3044-4243; doc://contextual-thread#3045-3976; doc://long-10240#1016-2215; doc://contextual-thread#2032-3224 |
| metadata-endpoint-hybrid | graph-multihop | graph-team, graph-vendor, contextual-thread, long-10240 | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://contextual-thread#3045-3976; doc://long-10240#0-1194; doc://contextual-thread#1017-2211; doc://long-10240#6101-7299; doc://contextual-thread#2032-3224; doc://contextual-thread#0-1196 |
| metadata-endpoint-hybrid | multilingual | multilingual, long-10240, exact-distractor | 1/1 | doc://multilingual#0-90; doc://long-10240#2036-3222; doc://long-10240#9157-10240; doc://long-10240#5081-6280; doc://exact-distractor#0-87; doc://long-10240#0-1194; doc://long-10240#8141-9336; doc://long-10240#6101-7299 |
| metadata-endpoint-hybrid | prompt-injection | injection, contextual-thread, revision-latest, exact-distractor, revision-old | 1/1 | doc://injection#0-130; doc://contextual-thread#3045-3976; doc://contextual-thread#1017-2211; doc://contextual-thread#2032-3224; doc://contextual-thread#0-1196; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81 |
| metadata-endpoint-hybrid | scope-isolation | long-10240, injection | 0/0 | doc://long-10240#8141-9336; doc://long-10240#1016-2215; doc://long-10240#7120-8320; doc://injection#0-130; doc://long-10240#3044-4243; doc://long-10240#5081-6280; doc://long-10240#0-1194; doc://long-10240#4064-5260 |
| metadata-endpoint-hybrid | no-answer | exact-distractor, contextual-thread, revision-old, revision-latest, graph-vendor | 0/0 | doc://exact-distractor#0-87; doc://contextual-thread#3045-3976; doc://contextual-thread#0-1196; doc://revision-old#0-81; doc://revision-latest#0-99; doc://contextual-thread#1017-2211; doc://contextual-thread#2032-3224; doc://graph-vendor#0-75 |
| metadata-endpoint-hybrid | contextual-late-reference | contextual-thread, exact-distractor, long-10240, graph-vendor, exact-orbit, graph-team | 0/1 | doc://contextual-thread#0-1196; doc://exact-distractor#0-87; doc://long-10240#1016-2215; doc://graph-vendor#0-75; doc://exact-orbit#0-105; doc://graph-team#0-93; doc://long-10240#7120-8320; doc://long-10240#6101-7299 |
| generated-endpoint-dense | exact-identifier | exact-orbit, exact-distractor, long-10240, revision-latest, revision-old | 1/1 | doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://long-10240#0-1194; doc://revision-latest#0-99; doc://long-10240#9157-10240; doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://revision-old#0-81 |
| generated-endpoint-dense | long-document-coverage | long-10240, contextual-thread, exact-orbit | 20/32 | doc://long-10240#8141-9336; doc://long-10240#3044-4243; doc://long-10240#0-1194; doc://long-10240#9157-10240; doc://long-10240#1016-2215; doc://contextual-thread#3045-3976; doc://long-10240#7120-8320; doc://exact-orbit#0-105 |
| generated-endpoint-dense | latest-revision | revision-latest, revision-old, long-10240, contextual-thread, exact-orbit | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://long-10240#3044-4243; doc://long-10240#1016-2215; doc://contextual-thread#3045-3976; doc://long-10240#8141-9336; doc://exact-orbit#0-105; doc://long-10240#9157-10240 |
| generated-endpoint-dense | graph-multihop | graph-team, graph-vendor, long-10240, contextual-thread | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://long-10240#8141-9336; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://contextual-thread#3045-3976; doc://long-10240#3044-4243; doc://long-10240#5081-6280 |
| generated-endpoint-dense | multilingual | multilingual, long-10240, exact-orbit, contextual-thread | 1/1 | doc://multilingual#0-90; doc://long-10240#8141-9336; doc://long-10240#2036-3222; doc://long-10240#0-1194; doc://exact-orbit#0-105; doc://long-10240#5081-6280; doc://long-10240#9157-10240; doc://contextual-thread#3045-3976 |
| generated-endpoint-dense | prompt-injection | injection, contextual-thread, revision-latest, long-10240, exact-orbit | 1/1 | doc://injection#0-130; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://revision-latest#0-99; doc://long-10240#8141-9336; doc://exact-orbit#0-105; doc://long-10240#9157-10240 |
| generated-endpoint-dense | scope-isolation | long-10240, contextual-thread, injection, graph-vendor, exact-orbit | 0/0 | doc://long-10240#7120-8320; doc://long-10240#1016-2215; doc://contextual-thread#3045-3976; doc://long-10240#8141-9336; doc://injection#0-130; doc://long-10240#3044-4243; doc://graph-vendor#0-75; doc://exact-orbit#0-105 |
| generated-endpoint-dense | no-answer | contextual-thread, exact-orbit, injection, long-10240, graph-vendor, revision-latest | 0/0 | doc://contextual-thread#3045-3976; doc://exact-orbit#0-105; doc://injection#0-130; doc://long-10240#8141-9336; doc://graph-vendor#0-75; doc://contextual-thread#2032-3224; doc://revision-latest#0-99; doc://long-10240#6101-7299 |
| generated-endpoint-dense | contextual-late-reference | contextual-thread, exact-orbit, multilingual, long-10240 | 1/1 | doc://contextual-thread#0-1196; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://exact-orbit#0-105; doc://multilingual#0-90; doc://long-10240#7120-8320; doc://long-10240#1016-2215 |
| generated-endpoint-hybrid | exact-identifier | exact-orbit, long-10240, exact-distractor, revision-latest, revision-old, multilingual, contextual-thread | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://revision-old#0-81; doc://long-10240#9157-10240; doc://multilingual#0-90; doc://contextual-thread#3045-3976 |
| generated-endpoint-hybrid | long-document-coverage | long-10240, exact-orbit | 24/32 | doc://long-10240#0-1194; doc://long-10240#9157-10240; doc://long-10240#3044-4243; doc://exact-orbit#0-105; doc://long-10240#8141-9336; doc://long-10240#1016-2215; doc://long-10240#7120-8320; doc://long-10240#5081-6280 |
| generated-endpoint-hybrid | latest-revision | revision-latest, revision-old, exact-orbit, long-10240, contextual-thread | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://long-10240#3044-4243; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://long-10240#9157-10240 |
| generated-endpoint-hybrid | graph-multihop | graph-team, graph-vendor, long-10240 | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://long-10240#8141-9336; doc://long-10240#6101-7299; doc://long-10240#4064-5260; doc://long-10240#3044-4243; doc://long-10240#9157-10240; doc://long-10240#5081-6280 |
| generated-endpoint-hybrid | multilingual | multilingual, long-10240, exact-orbit, contextual-thread | 1/1 | doc://multilingual#0-90; doc://long-10240#8141-9336; doc://long-10240#2036-3222; doc://long-10240#0-1194; doc://exact-orbit#0-105; doc://long-10240#5081-6280; doc://long-10240#9157-10240; doc://contextual-thread#3045-3976 |
| generated-endpoint-hybrid | prompt-injection | injection, contextual-thread, revision-latest, long-10240, revision-old, exact-orbit | 1/1 | doc://injection#0-130; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224; doc://contextual-thread#1017-2211; doc://revision-latest#0-99; doc://long-10240#8141-9336; doc://revision-old#0-81; doc://exact-orbit#0-105 |
| generated-endpoint-hybrid | scope-isolation | long-10240, graph-vendor, multilingual, injection | 0/0 | doc://long-10240#1016-2215; doc://graph-vendor#0-75; doc://long-10240#7120-8320; doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#5081-6280 |
| generated-endpoint-hybrid | no-answer | contextual-thread, exact-orbit, revision-latest, graph-vendor, long-10240 | 0/0 | doc://contextual-thread#3045-3976; doc://exact-orbit#0-105; doc://contextual-thread#2032-3224; doc://revision-latest#0-99; doc://contextual-thread#1017-2211; doc://graph-vendor#0-75; doc://long-10240#8141-9336; doc://contextual-thread#0-1196 |
| generated-endpoint-hybrid | contextual-late-reference | contextual-thread, long-10240, exact-orbit, multilingual, graph-vendor | 1/1 | doc://contextual-thread#0-1196; doc://contextual-thread#1017-2211; doc://contextual-thread#3045-3976; doc://contextual-thread#2032-3224; doc://long-10240#1016-2215; doc://exact-orbit#0-105; doc://multilingual#0-90; doc://graph-vendor#0-75 |

The JSON companion retains every prompt, raw model output, generated context, per-case metric, and complete source-backed evidence span.
