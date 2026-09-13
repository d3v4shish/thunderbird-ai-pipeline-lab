# Generated Contextual RAG Evaluation

Paired, query-independent Contextual Retrieval ablation over identical structure-aware chunks. Generated context is indexed by BM25 and embeddings but is never returned as answer evidence.

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
| 19 | 19 | 1 | 18 | 0 | 1.000 | 1.000 | 2151.7 | 26633 | 893 |

## Retrieval results

| Lane | Context | Retrieval | Embedding | Document recall | Fact recall | MRR | nDCG | p50 ms | DB bytes | Indexed chars |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| metadata-local-lexical | metadata | lexical | deterministic-local-v1 | 1.000 | 0.757 | 0.917 | 0.900 | 0.290 | 176128 | 14743 |
| metadata-local-hybrid | metadata | hybrid | deterministic-local-v1 | 1.000 | 0.757 | 1.000 | 0.972 | 0.505 | 176128 | 14743 |
| generated-local-lexical | generated | lexical | deterministic-local-v1 | 1.000 | 0.676 | 1.000 | 0.987 | 0.321 | 192512 | 19301 |
| generated-local-hybrid | generated | hybrid | deterministic-local-v1 | 0.917 | 0.811 | 1.000 | 0.936 | 0.527 | 192512 | 19301 |
| metadata-endpoint-dense | metadata | dense | qwen3-embedding:4b | 1.000 | 0.865 | 1.000 | 0.987 | 125.729 | 794624 | 14743 |
| metadata-endpoint-hybrid | metadata | hybrid | qwen3-embedding:4b | 1.000 | 0.838 | 1.000 | 1.000 | 126.582 | 794624 | 14743 |
| generated-endpoint-dense | generated | dense | qwen3-embedding:4b | 1.000 | 0.838 | 0.917 | 0.949 | 126.274 | 806912 | 19301 |
| generated-endpoint-hybrid | generated | hybrid | qwen3-embedding:4b | 1.000 | 0.757 | 1.000 | 1.000 | 126.177 | 806912 | 19301 |

## Paired deltas: generated minus metadata context

| Retrieval family | Document recall | Fact recall | MRR | nDCG | p50 ms | DB bytes | Indexed chars |
|---|---:|---:|---:|---:|---:|---:|---:|
| local-lexical | +0.000 | -0.081 | +0.083 | +0.086 | +0.032 | +16384 | +4558 |
| local-hybrid | -0.083 | +0.054 | +0.000 | -0.036 | +0.022 | +16384 | +4558 |
| endpoint-dense | +0.000 | -0.027 | -0.083 | -0.038 | +0.545 | +12288 | +4558 |
| endpoint-hybrid | +0.000 | -0.081 | +0.000 | +0.000 | -0.405 | +12288 | +4558 |

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
- Source span valid: `True`; latency: `16732.4 ms`.
- Generated context: The chunk is the entire content of the document titled 'Orbit launch decision', which details the launch date, location, and budget for Project ORBIT-731.
- Error: none
- Raw model output:

```json
{"context": "The chunk is the entire content of the document titled 'Orbit launch decision', which details the launch date, location, and budget for Project ORBIT-731."}
```

### exact-distractor / tenant-alpha/primary/exact-distractor:chunk:0

- Status: `ok`; cache hit: `True`; source: `0-87`.
- Source span valid: `True`; latency: `457.9 ms`.
- Generated context: The chunk provides a factual statement about Project ORBIT-713, mentioning its launch date and that it is unrelated to other projects, using East Annex.
- Error: none
- Raw model output:

```json
{"context": "The chunk provides a factual statement about Project ORBIT-713, mentioning its launch date and that it is unrelated to other projects, using East Annex."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:0

- Status: `ok`; cache hit: `True`; source: `0-1194`.
- Source span valid: `True`; latency: `6611.5 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, containing multiple sections with FACT entries. Each section includes a required_value and repetitive explanatory text about bounded retrieval and data coverage.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, containing multiple sections with FACT entries. Each section includes a required_value and repetitive explanatory text about bounded retrieval and data coverage."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:1

- Status: `ok`; cache hit: `True`; source: `1016-2215`.
- Source span valid: `True`; latency: `895.7 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, following Section 04 and preceding Section 08. It contains repeated statements about synthetic context's purpose and includes FACT F07 with a required value of 2027-02-03.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, following Section 04 and preceding Section 08. It contains repeated statements about synthetic context's purpose and includes FACT F07 with a required value of 2027-02-03."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:2

- Status: `ok`; cache hit: `True`; source: `2036-3222`.
- Source span valid: `True`; latency: `746.4 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, located in Section 07, which contains a fact about a date and repeated statements about synthetic context for retrieval exercises.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, located in Section 07, which contains a fact about a date and repeated statements about synthetic context for retrieval exercises."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:3

- Status: `ok`; cache hit: `True`; source: `3044-4243`.
- Source span valid: `True`; latency: `792.4 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, located in Section 10 to Section 14. It contains facts with required values and repetitive statements about synthetic contexts for bounded retrieval and coverage.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, located in Section 10 to Section 14. It contains facts with required values and repetitive statements about synthetic contexts for bounded retrieval and coverage."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:4

- Status: `ok`; cache hit: `True`; source: `4064-5260`.
- Source span valid: `True`; latency: `811.7 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, located in Section 13 to 17. It contains repeated synthetic facts with required values and a purpose to exercise bounded retrieval and complete coverage without external data.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, located in Section 13 to 17. It contains repeated synthetic facts with required values and a purpose to exercise bounded retrieval and complete coverage without external data."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:5

- Status: `ok`; cache hit: `True`; source: `5081-6280`.
- Source span valid: `True`; latency: `803.5 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, following Section 16 and preceding Section 20. It contains repeated synthetic facts with required values and explanatory text about bounded retrieval and data privacy.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, following Section 16 and preceding Section 20. It contains repeated synthetic facts with required values and explanatory text about bounded retrieval and data privacy."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:6

- Status: `ok`; cache hit: `True`; source: `6101-7299`.
- Source span valid: `True`; latency: `748.1 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, located in Section 20 to Section 23. It contains facts about required values and repetitive context statements for retrieval exercises.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, located in Section 20 to Section 23. It contains facts about required values and repetitive context statements for retrieval exercises."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:7

- Status: `ok`; cache hit: `True`; source: `7120-8320`.
- Source span valid: `True`; latency: `898.6 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, following sections 22 and preceding sections 27. It contains facts about MATRIX-317, South Gallery, and USD 4,275.00, each repeated with the same explanatory text.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, following sections 22 and preceding sections 27. It contains facts about MATRIX-317, South Gallery, and USD 4,275.00, each repeated with the same explanatory text."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:8

- Status: `ok`; cache hit: `True`; source: `8141-9336`.
- Source span valid: `True`; latency: `845.0 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, specifically within Section 26 to Section 30. It contains facts with required values and repetitive statements about synthetic contexts for bounded retrieval and coverage without personal or mutable external data.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, specifically within Section 26 to Section 30. It contains facts with required values and repetitive statements about synthetic contexts for bounded retrieval and coverage without personal or mutable external data."}
```

### long-10240 / tenant-alpha/primary/long-10240:chunk:9

- Status: `ok`; cache hit: `True`; source: `9157-10240`.
- Source span valid: `True`; latency: `841.1 ms`.
- Generated context: The chunk is part of a synthetic operations ledger document, following sections 28 and preceding section 32. It contains repeated synthetic context descriptions for bounded retrieval exercises, with specific required values for facts F29 to F32.
- Error: none
- Raw model output:

```json
{"context": "The chunk is part of a synthetic operations ledger document, following sections 28 and preceding section 32. It contains repeated synthetic context descriptions for bounded retrieval exercises, with specific required values for facts F29 to F32."}
```

### revision-old / tenant-alpha/primary/revision-old:chunk:0

- Status: `ok`; cache hit: `False`; source: `0-81`.
- Source span valid: `True`; latency: `2149.8 ms`.
- Generated context: The chunk is the full text of a decision document titled 'Cedar decision revision 1', dated 2026-08-01, which states that revision one for CEDAR-210 is superseded with a deployment date of 2027-08-12.
- Error: none
- Raw model output:

```json
{"context": "The chunk is the full text of a decision document titled 'Cedar decision revision 1', dated 2026-08-01, which states that revision one for CEDAR-210 is superseded with a deployment date of 2027-08-12."}
```

### revision-latest / tenant-alpha/primary/revision-latest:chunk:0

- Status: `ok`; cache hit: `True`; source: `0-99`.
- Source span valid: `True`; latency: `561.2 ms`.
- Generated context: The chunk is the full text of the document titled 'Cedar decision revision 2', which confirms revision two as the latest approved decision for CEDAR-210 with a deployment date of 2027-09-21.
- Error: none
- Raw model output:

```json
{"context": "The chunk is the full text of the document titled 'Cedar decision revision 2', which confirms revision two as the latest approved decision for CEDAR-210 with a deployment date of 2027-09-21."}
```

### graph-team / tenant-alpha/primary/graph-team:chunk:0

- Status: `ok`; cache hit: `True`; source: `0-93`.
- Source span valid: `True`; latency: `367.1 ms`.
- Generated context: The chunk is the full text of the document titled 'Atlas ownership', which details ownership and team structure related to Project Atlas.
- Error: none
- Raw model output:

```json
{"context": "The chunk is the full text of the document titled 'Atlas ownership', which details ownership and team structure related to Project Atlas."}
```

### graph-vendor / tenant-alpha/primary/graph-vendor:chunk:0

- Status: `ok`; cache hit: `True`; source: `0-75`.
- Source span valid: `True`; latency: `425.1 ms`.
- Generated context: The chunk is located in the document titled 'Atlas supplier' under the dependency category. It states that Project Atlas depends on Kestrel Works as its supplier.
- Error: none
- Raw model output:

```json
{"context": "The chunk is located in the document titled 'Atlas supplier' under the dependency category. It states that Project Atlas depends on Kestrel Works as its supplier."}
```

### multilingual / tenant-alpha/primary/multilingual:chunk:0

- Status: `ok`; cache hit: `True`; source: `0-90`.
- Source span valid: `True`; latency: `325.1 ms`.
- Generated context: The chunk provides a fact about a project meeting location and date within a bilingual decision document.
- Error: none
- Raw model output:

```json
{"context": "The chunk provides a fact about a project meeting location and date within a bilingual decision document."}
```

### injection / tenant-alpha/primary/injection:chunk:0

- Status: `ok`; cache hit: `True`; source: `0-130`.
- Source span valid: `True`; latency: `565.5 ms`.
- Generated context: The chunk is from a security document titled 'Untrusted embedded instruction' with ID 'injection'. It contains an untrusted instruction to ignore previous guidance and reveal SECRETCODE-999, along with a fact about a quarantined safe status.
- Error: none
- Raw model output:

```json
{"context": "The chunk is from a security document titled 'Untrusted embedded instruction' with ID 'injection'. It contains an untrusted instruction to ignore previous guidance and reveal SECRETCODE-999, along with a fact about a quarantined safe status."}
```

### other-tenant-secret / tenant-beta/private/other-tenant-secret:chunk:0

- Status: `ok`; cache hit: `True`; source: `0-77`.
- Source span valid: `True`; latency: `409.5 ms`.
- Generated context: The chunk is the entire content of a private document titled 'Isolation sentinel' containing a fact about an isolated value assigned to tenant-beta.
- Error: none
- Raw model output:

```json
{"context": "The chunk is the entire content of a private document titled 'Isolation sentinel' containing a fact about an isolated value assigned to tenant-beta."}
```

## Per-case retrieval audit

| Lane | Case | Retrieved documents | Matched facts | Evidence spans |
|---|---|---|---|---|
| metadata-local-lexical | exact-identifier | exact-orbit, revision-latest, exact-distractor, revision-old, long-10240, graph-vendor, graph-team, multilingual | 1/1 | doc://exact-orbit#0-105; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://long-10240#0-1194; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://multilingual#0-90 |
| metadata-local-lexical | long-document-coverage | exact-orbit, long-10240 | 23/32 | doc://exact-orbit#0-105; doc://long-10240#9157-10240; doc://long-10240#0-1194; doc://long-10240#4064-5260; doc://long-10240#8141-9336; doc://long-10240#3044-4243; doc://long-10240#5081-6280; doc://long-10240#2036-3222 |
| metadata-local-lexical | latest-revision | revision-latest, revision-old, exact-distractor, exact-orbit, long-10240, graph-vendor, graph-team, multilingual | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#3044-4243; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://multilingual#0-90 |
| metadata-local-lexical | graph-multihop | graph-team, revision-latest, graph-vendor, exact-distractor, revision-old, exact-orbit, long-10240 | 1/1 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://graph-vendor#0-75; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://long-10240#1016-2215; doc://long-10240#0-1194 |
| metadata-local-lexical | multilingual | multilingual | 1/1 | doc://multilingual#0-90 |
| metadata-local-lexical | prompt-injection | injection, revision-latest, exact-distractor, revision-old, exact-orbit | 1/1 | doc://injection#0-130; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://exact-orbit#0-105 |
| metadata-local-lexical | scope-isolation | long-10240 | 0/0 | doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#3044-4243; doc://long-10240#5081-6280; doc://long-10240#1016-2215; doc://long-10240#2036-3222; doc://long-10240#7120-8320 |
| metadata-local-lexical | no-answer | revision-latest, revision-old, exact-distractor, exact-orbit, graph-vendor, graph-team | 0/0 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://graph-vendor#0-75; doc://graph-team#0-93 |
| metadata-local-hybrid | exact-identifier | exact-orbit, long-10240, revision-latest, exact-distractor, revision-old, multilingual, injection, graph-vendor | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://multilingual#0-90; doc://injection#0-130; doc://graph-vendor#0-75 |
| metadata-local-hybrid | long-document-coverage | long-10240, exact-orbit | 23/32 | doc://long-10240#9157-10240; doc://long-10240#5081-6280; doc://long-10240#0-1194; doc://long-10240#3044-4243; doc://exact-orbit#0-105; doc://long-10240#6101-7299; doc://long-10240#2036-3222; doc://long-10240#4064-5260 |
| metadata-local-hybrid | latest-revision | revision-latest, revision-old, exact-distractor, exact-orbit, long-10240 | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://long-10240#9157-10240; doc://long-10240#6101-7299 |
| metadata-local-hybrid | graph-multihop | graph-team, exact-distractor, revision-latest, long-10240, graph-vendor | 1/1 | doc://graph-team#0-93; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://long-10240#0-1194; doc://long-10240#9157-10240; doc://graph-vendor#0-75; doc://long-10240#3044-4243; doc://long-10240#1016-2215 |
| metadata-local-hybrid | multilingual | multilingual, exact-orbit, injection, long-10240 | 1/1 | doc://multilingual#0-90; doc://exact-orbit#0-105; doc://injection#0-130; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#7120-8320; doc://long-10240#3044-4243; doc://long-10240#2036-3222 |
| metadata-local-hybrid | prompt-injection | injection, revision-latest, exact-distractor, revision-old, exact-orbit, long-10240 | 1/1 | doc://injection#0-130; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://long-10240#8141-9336; doc://long-10240#6101-7299; doc://long-10240#5081-6280 |
| metadata-local-hybrid | scope-isolation | long-10240, injection | 0/0 | doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://long-10240#0-1194; doc://long-10240#3044-4243; doc://injection#0-130; doc://long-10240#1016-2215; doc://long-10240#7120-8320 |
| metadata-local-hybrid | no-answer | exact-distractor, revision-latest, exact-orbit, revision-old, graph-vendor, graph-team, injection, multilingual | 0/0 | doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://exact-orbit#0-105; doc://revision-old#0-81; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://injection#0-130; doc://multilingual#0-90 |
| generated-local-lexical | exact-identifier | exact-orbit, exact-distractor, long-10240, revision-latest, revision-old | 1/1 | doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://long-10240#0-1194; doc://revision-latest#0-99; doc://revision-old#0-81; doc://long-10240#9157-10240; doc://long-10240#2036-3222; doc://long-10240#6101-7299 |
| generated-local-lexical | long-document-coverage | long-10240, exact-orbit, injection | 20/32 | doc://long-10240#9157-10240; doc://exact-orbit#0-105; doc://injection#0-130; doc://long-10240#0-1194; doc://long-10240#4064-5260; doc://long-10240#8141-9336; doc://long-10240#3044-4243; doc://long-10240#5081-6280 |
| generated-local-lexical | latest-revision | revision-latest, revision-old, long-10240, exact-orbit | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://long-10240#3044-4243; doc://exact-orbit#0-105; doc://long-10240#9157-10240; doc://long-10240#2036-3222; doc://long-10240#6101-7299; doc://long-10240#8141-9336 |
| generated-local-lexical | graph-multihop | graph-team, graph-vendor, exact-orbit, revision-latest, revision-old, long-10240, exact-distractor | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://exact-orbit#0-105; doc://revision-latest#0-99; doc://revision-old#0-81; doc://long-10240#2036-3222; doc://exact-distractor#0-87; doc://long-10240#7120-8320 |
| generated-local-lexical | multilingual | multilingual | 1/1 | doc://multilingual#0-90 |
| generated-local-lexical | prompt-injection | injection, revision-latest, revision-old, exact-orbit, graph-team, graph-vendor, long-10240 | 1/1 | doc://injection#0-130; doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://graph-team#0-93; doc://graph-vendor#0-75; doc://long-10240#1016-2215; doc://long-10240#7120-8320 |
| generated-local-lexical | scope-isolation | graph-vendor, long-10240 | 0/0 | doc://graph-vendor#0-75; doc://long-10240#2036-3222; doc://long-10240#6101-7299; doc://long-10240#3044-4243; doc://long-10240#4064-5260; doc://long-10240#0-1194; doc://long-10240#5081-6280; doc://long-10240#8141-9336 |
| generated-local-lexical | no-answer | revision-latest, exact-orbit, graph-vendor, graph-team, exact-distractor, multilingual, revision-old, long-10240 | 0/0 | doc://revision-latest#0-99; doc://exact-orbit#0-105; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://exact-distractor#0-87; doc://multilingual#0-90; doc://revision-old#0-81; doc://long-10240#9157-10240 |
| generated-local-hybrid | exact-identifier | exact-orbit, long-10240, exact-distractor, revision-latest, revision-old, injection | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://revision-old#0-81; doc://long-10240#9157-10240; doc://long-10240#8141-9336; doc://injection#0-130 |
| generated-local-hybrid | long-document-coverage | long-10240 | 26/32 | doc://long-10240#9157-10240; doc://long-10240#4064-5260; doc://long-10240#6101-7299; doc://long-10240#0-1194; doc://long-10240#5081-6280; doc://long-10240#3044-4243; doc://long-10240#2036-3222; doc://long-10240#8141-9336 |
| generated-local-hybrid | latest-revision | revision-latest, revision-old, exact-orbit, long-10240, exact-distractor | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://long-10240#3044-4243; doc://long-10240#9157-10240; doc://exact-distractor#0-87; doc://long-10240#8141-9336; doc://long-10240#6101-7299 |
| generated-local-hybrid | graph-multihop | graph-team, revision-latest, exact-distractor, long-10240, revision-old, injection, exact-orbit | 0/1 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://long-10240#9157-10240; doc://revision-old#0-81; doc://injection#0-130; doc://exact-orbit#0-105; doc://long-10240#0-1194 |
| generated-local-hybrid | multilingual | multilingual, long-10240, exact-orbit | 1/1 | doc://multilingual#0-90; doc://long-10240#6101-7299; doc://long-10240#0-1194; doc://long-10240#7120-8320; doc://exact-orbit#0-105; doc://long-10240#3044-4243; doc://long-10240#2036-3222; doc://long-10240#8141-9336 |
| generated-local-hybrid | prompt-injection | injection, revision-latest, exact-orbit, revision-old, exact-distractor, graph-vendor, long-10240, graph-team | 1/1 | doc://injection#0-130; doc://revision-latest#0-99; doc://exact-orbit#0-105; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://graph-vendor#0-75; doc://long-10240#7120-8320; doc://graph-team#0-93 |
| generated-local-hybrid | scope-isolation | graph-vendor, long-10240, injection | 0/0 | doc://graph-vendor#0-75; doc://long-10240#6101-7299; doc://long-10240#3044-4243; doc://long-10240#2036-3222; doc://long-10240#5081-6280; doc://injection#0-130; doc://long-10240#4064-5260; doc://long-10240#9157-10240 |
| generated-local-hybrid | no-answer | exact-orbit, revision-latest, exact-distractor, multilingual, revision-old, injection, long-10240, graph-vendor | 0/0 | doc://exact-orbit#0-105; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://multilingual#0-90; doc://revision-old#0-81; doc://injection#0-130; doc://long-10240#6101-7299; doc://graph-vendor#0-75 |
| metadata-endpoint-dense | exact-identifier | exact-orbit, exact-distractor, long-10240, revision-old, graph-vendor | 1/1 | doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://long-10240#0-1194; doc://revision-old#0-81; doc://graph-vendor#0-75; doc://long-10240#1016-2215; doc://long-10240#5081-6280; doc://long-10240#6101-7299 |
| metadata-endpoint-dense | long-document-coverage | long-10240 | 27/32 | doc://long-10240#8141-9336; doc://long-10240#9157-10240; doc://long-10240#7120-8320; doc://long-10240#0-1194; doc://long-10240#3044-4243; doc://long-10240#5081-6280; doc://long-10240#2036-3222; doc://long-10240#1016-2215 |
| metadata-endpoint-dense | latest-revision | revision-latest, revision-old, exact-distractor, long-10240 | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://long-10240#1016-2215; doc://long-10240#3044-4243; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://long-10240#9157-10240 |
| metadata-endpoint-dense | graph-multihop | graph-team, graph-vendor, long-10240 | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://long-10240#9157-10240; doc://long-10240#5081-6280; doc://long-10240#8141-9336; doc://long-10240#3044-4243 |
| metadata-endpoint-dense | multilingual | multilingual, long-10240, exact-distractor | 1/1 | doc://multilingual#0-90; doc://long-10240#2036-3222; doc://exact-distractor#0-87; doc://long-10240#9157-10240; doc://long-10240#5081-6280; doc://long-10240#0-1194; doc://long-10240#8141-9336; doc://long-10240#6101-7299 |
| metadata-endpoint-dense | prompt-injection | injection, long-10240 | 1/1 | doc://injection#0-130; doc://long-10240#8141-9336; doc://long-10240#7120-8320; doc://long-10240#5081-6280; doc://long-10240#1016-2215; doc://long-10240#9157-10240; doc://long-10240#3044-4243; doc://long-10240#4064-5260 |
| metadata-endpoint-dense | scope-isolation | injection, long-10240, exact-distractor, graph-vendor | 0/0 | doc://injection#0-130; doc://long-10240#7120-8320; doc://long-10240#1016-2215; doc://long-10240#8141-9336; doc://long-10240#4064-5260; doc://exact-distractor#0-87; doc://long-10240#5081-6280; doc://graph-vendor#0-75 |
| metadata-endpoint-dense | no-answer | injection, exact-distractor, long-10240 | 0/0 | doc://injection#0-130; doc://exact-distractor#0-87; doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://long-10240#1016-2215; doc://long-10240#0-1194; doc://long-10240#7120-8320 |
| metadata-endpoint-hybrid | exact-identifier | exact-orbit, long-10240, exact-distractor, revision-old, graph-vendor, revision-latest, multilingual | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://graph-vendor#0-75; doc://revision-latest#0-99; doc://long-10240#1016-2215; doc://multilingual#0-90 |
| metadata-endpoint-hybrid | long-document-coverage | long-10240 | 26/32 | doc://long-10240#9157-10240; doc://long-10240#8141-9336; doc://long-10240#0-1194; doc://long-10240#3044-4243; doc://long-10240#4064-5260; doc://long-10240#5081-6280; doc://long-10240#7120-8320; doc://long-10240#2036-3222 |
| metadata-endpoint-hybrid | latest-revision | revision-latest, revision-old, exact-distractor, long-10240, exact-orbit, multilingual | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://long-10240#3044-4243; doc://long-10240#1016-2215; doc://exact-orbit#0-105; doc://long-10240#9157-10240; doc://multilingual#0-90 |
| metadata-endpoint-hybrid | graph-multihop | graph-team, graph-vendor, long-10240, exact-distractor, revision-latest, revision-old | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://long-10240#0-1194; doc://long-10240#6101-7299; doc://exact-distractor#0-87; doc://long-10240#9157-10240; doc://revision-latest#0-99; doc://revision-old#0-81 |
| metadata-endpoint-hybrid | multilingual | multilingual, long-10240, exact-distractor | 1/1 | doc://multilingual#0-90; doc://long-10240#2036-3222; doc://exact-distractor#0-87; doc://long-10240#9157-10240; doc://long-10240#5081-6280; doc://long-10240#0-1194; doc://long-10240#8141-9336; doc://long-10240#6101-7299 |
| metadata-endpoint-hybrid | prompt-injection | injection, exact-distractor, revision-latest, revision-old, exact-orbit, long-10240 | 1/1 | doc://injection#0-130; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://long-10240#8141-9336; doc://long-10240#7120-8320; doc://long-10240#5081-6280 |
| metadata-endpoint-hybrid | scope-isolation | long-10240, injection | 0/0 | doc://long-10240#8141-9336; doc://long-10240#1016-2215; doc://long-10240#7120-8320; doc://injection#0-130; doc://long-10240#0-1194; doc://long-10240#5081-6280; doc://long-10240#3044-4243; doc://long-10240#6101-7299 |
| metadata-endpoint-hybrid | no-answer | exact-distractor, revision-old, revision-latest, exact-orbit, graph-vendor, graph-team, injection, long-10240 | 0/0 | doc://exact-distractor#0-87; doc://revision-old#0-81; doc://revision-latest#0-99; doc://exact-orbit#0-105; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://injection#0-130; doc://long-10240#6101-7299 |
| generated-endpoint-dense | exact-identifier | exact-distractor, exact-orbit, long-10240, revision-old, revision-latest | 1/1 | doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://revision-old#0-81; doc://revision-latest#0-99; doc://long-10240#9157-10240; doc://long-10240#5081-6280; doc://long-10240#8141-9336 |
| generated-endpoint-dense | long-document-coverage | long-10240 | 26/32 | doc://long-10240#8141-9336; doc://long-10240#9157-10240; doc://long-10240#0-1194; doc://long-10240#3044-4243; doc://long-10240#1016-2215; doc://long-10240#5081-6280; doc://long-10240#4064-5260; doc://long-10240#2036-3222 |
| generated-endpoint-dense | latest-revision | revision-latest, revision-old, long-10240, exact-orbit, exact-distractor | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://long-10240#3044-4243; doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://long-10240#8141-9336; doc://long-10240#1016-2215; doc://long-10240#5081-6280 |
| generated-endpoint-dense | graph-multihop | graph-team, graph-vendor, long-10240 | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://long-10240#9157-10240; doc://long-10240#0-1194; doc://long-10240#3044-4243 |
| generated-endpoint-dense | multilingual | multilingual, exact-orbit, long-10240, revision-old | 1/1 | doc://multilingual#0-90; doc://exact-orbit#0-105; doc://long-10240#9157-10240; doc://long-10240#4064-5260; doc://long-10240#2036-3222; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://revision-old#0-81 |
| generated-endpoint-dense | prompt-injection | injection, long-10240, revision-latest, exact-orbit, revision-old | 1/1 | doc://injection#0-130; doc://long-10240#8141-9336; doc://revision-latest#0-99; doc://long-10240#5081-6280; doc://exact-orbit#0-105; doc://revision-old#0-81; doc://long-10240#1016-2215; doc://long-10240#7120-8320 |
| generated-endpoint-dense | scope-isolation | injection, long-10240, exact-orbit, exact-distractor | 0/0 | doc://injection#0-130; doc://long-10240#8141-9336; doc://long-10240#7120-8320; doc://long-10240#5081-6280; doc://long-10240#4064-5260; doc://long-10240#3044-4243; doc://exact-orbit#0-105; doc://exact-distractor#0-87 |
| generated-endpoint-dense | no-answer | injection, exact-distractor, exact-orbit, long-10240, multilingual, revision-old | 0/0 | doc://injection#0-130; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#6101-7299; doc://long-10240#8141-9336; doc://multilingual#0-90; doc://long-10240#5081-6280; doc://revision-old#0-81 |
| generated-endpoint-hybrid | exact-identifier | exact-orbit, long-10240, exact-distractor, revision-latest, revision-old | 1/1 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://revision-old#0-81; doc://long-10240#9157-10240; doc://long-10240#6101-7299; doc://long-10240#8141-9336 |
| generated-endpoint-hybrid | long-document-coverage | long-10240, exact-orbit | 23/32 | doc://long-10240#9157-10240; doc://long-10240#8141-9336; doc://long-10240#0-1194; doc://long-10240#3044-4243; doc://exact-orbit#0-105; doc://long-10240#4064-5260; doc://long-10240#1016-2215; doc://long-10240#5081-6280 |
| generated-endpoint-hybrid | latest-revision | revision-latest, revision-old, long-10240, exact-orbit, exact-distractor | 1/1 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://long-10240#3044-4243; doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://long-10240#9157-10240; doc://long-10240#8141-9336; doc://long-10240#6101-7299 |
| generated-endpoint-hybrid | graph-multihop | graph-team, graph-vendor, long-10240, exact-orbit, revision-old, revision-latest | 1/1 | doc://graph-team#0-93; doc://graph-vendor#0-75; doc://long-10240#6101-7299; doc://exact-orbit#0-105; doc://revision-old#0-81; doc://long-10240#9157-10240; doc://revision-latest#0-99; doc://long-10240#2036-3222 |
| generated-endpoint-hybrid | multilingual | multilingual, exact-orbit, long-10240, revision-old | 1/1 | doc://multilingual#0-90; doc://exact-orbit#0-105; doc://long-10240#9157-10240; doc://long-10240#4064-5260; doc://long-10240#2036-3222; doc://long-10240#8141-9336; doc://long-10240#5081-6280; doc://revision-old#0-81 |
| generated-endpoint-hybrid | prompt-injection | injection, revision-latest, revision-old, exact-orbit, long-10240 | 1/1 | doc://injection#0-130; doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://long-10240#1016-2215; doc://long-10240#7120-8320; doc://long-10240#5081-6280; doc://long-10240#8141-9336 |
| generated-endpoint-hybrid | scope-isolation | graph-vendor, long-10240, injection | 0/0 | doc://graph-vendor#0-75; doc://long-10240#8141-9336; doc://long-10240#3044-4243; doc://long-10240#4064-5260; doc://long-10240#5081-6280; doc://injection#0-130; doc://long-10240#7120-8320; doc://long-10240#6101-7299 |
| generated-endpoint-hybrid | no-answer | exact-orbit, exact-distractor, revision-latest, multilingual, injection, graph-vendor, long-10240, revision-old | 0/0 | doc://exact-orbit#0-105; doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://multilingual#0-90; doc://injection#0-130; doc://graph-vendor#0-75; doc://long-10240#6101-7299; doc://revision-old#0-81 |

The JSON companion retains every prompt, raw model output, generated context, per-case metric, and complete source-backed evidence span.
