# Staged Advanced-RAG Evaluation

One-factor deterministic ablations run before final generation; no live model or external corpus is used.

Top-K: 8. Production ready: False.

## Technique coverage

| Technique | Status | Isolated stage | Note |
|---|---|---|---|
| Hybrid retrieval | tested | retrieval |  |
| Cross-encoder reranking | partial | reranking | Local deterministic and embedding rerankers are tested; a true cross-encoder remains an endpoint lane. |
| Contextual retrieval | partial | chunking | Deterministic metadata context is tested here; query-independent LLM-generated context has a separate live contextual-rag-evaluate lane. |
| HyDE | deferred | query transformation | Requires an extra live generation call and should be tested only after deterministic retrieval is stable. |
| Self-RAG | deferred | generation | Requires a reflection-trained model; current validation provides only a support gate. |
| CRAG | partial | quality gate | Local evidence validation exists; web fallback is intentionally excluded from the loopback-only lab. |
| Adaptive RAG | partial | query expansion | Deterministic intent rules are tested; no trained complexity router is used. |
| GraphRAG | partial | graph | Source-backed relation traversal is tested; Microsoft-style community summaries and global search are not implemented. |
| RAPTOR | deferred | hierarchical retrieval | Tree summaries need a larger long-document benchmark and extra indexing calls. |
| RAG Fusion | partial | query expansion | Deterministic query variants plus reciprocal-rank fusion are tested; LLM rewrites are not. |
| Sentence window / parent-child | tested | chunking |  |
| Modular RAG | tested | all | The report isolates swappable chunking, retrieval, reranking, graph, and generation stages. |

## Chunking

| Variant | Source coverage | Fact integrity | Redundancy | Chunks | Retrieval fact recall | Retrieval MRR |
|---|---:|---:|---:|---:|---:|---:|
| chunk-fixed | 1.000 | 1.000 | 0.128 | 19 | 0.838 | 1.000 |
| chunk-structure-aware | 1.000 | 1.000 | 0.127 | 19 | 0.838 | 1.000 |
| chunk-sentence-window | 1.000 | 1.000 | 0.938 | 173 | 0.892 | 1.000 |

## Chunk-size sweep

| Variant | Size | Overlap | Chunks | Fact recall | Packed chars/query | Redundancy |
|---|---:|---:|---:|---:|---:|---:|
| chunk-size-400 | 400 | 60 | 40 | 0.378 | 2195.1 | 0.137 |
| chunk-size-800 | 800 | 120 | 24 | 0.622 | 3988.5 | 0.130 |
| chunk-size-1200 | 1200 | 180 | 19 | 0.838 | 5117.1 | 0.127 |
| chunk-size-1800 | 1800 | 270 | 16 | 1.000 | 6561.6 | 0.127 |

## Retrieval

| Variant | K | Document recall | Fact recall | MRR | nDCG | Packed chars/query | Redundancy | p50 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| retrieval-exact | 8 | 0.500 | 0.081 | 0.500 | 0.500 | 196.1 | 0.000 | 0.014 |
| retrieval-lexical | 8 | 1.000 | 0.757 | 0.917 | 0.900 | 3204.8 | 0.032 | 0.288 |
| retrieval-dense | 8 | 0.583 | 0.676 | 0.583 | 0.564 | 5072.6 | 0.077 | 0.441 |
| retrieval-hybrid | 8 | 1.000 | 0.757 | 0.778 | 0.829 | 4998.1 | 0.065 | 0.694 |

## Retrieval Depth

| Variant | K | Document recall | Fact recall | MRR | nDCG | Packed chars/query | Redundancy | p50 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| top-k-4 | 4 | 0.917 | 0.514 | 1.000 | 0.936 | 1885.5 | 0.005 | 1.092 |
| top-k-8 | 8 | 1.000 | 0.838 | 1.000 | 0.970 | 5117.1 | 0.063 | 1.087 |
| top-k-16 | 16 | 1.000 | 1.000 | 1.000 | 0.970 | 9769.9 | 0.113 | 1.079 |

## Query Expansion

| Variant | K | Document recall | Fact recall | MRR | nDCG | Packed chars/query | Redundancy | p50 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| query-single | 8 | 1.000 | 0.757 | 0.778 | 0.829 | 4998.1 | 0.065 | 0.690 |
| query-adaptive | 8 | 1.000 | 0.784 | 0.889 | 0.911 | 4977.2 | 0.060 | 1.379 |

## Reranking

| Variant | K | Document recall | Fact recall | MRR | nDCG | Packed chars/query | Redundancy | p50 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| rerank-none | 8 | 1.000 | 0.757 | 0.778 | 0.829 | 4998.1 | 0.065 | 0.690 |
| rerank-deterministic | 8 | 1.000 | 0.838 | 1.000 | 0.970 | 5117.1 | 0.063 | 1.068 |
| rerank-embedding | 8 | 0.917 | 0.838 | 1.000 | 0.911 | 5940.9 | 0.067 | 0.827 |

## Graph retrieval

| Variant | Relation recall | Fact recall | Provenance validity |
|---|---:|---:|---:|
| graph-off | 0.000 | 1.000 | 1.000 |
| graph-keyword | 0.667 | 1.000 | 1.000 |
| graph-intent-multihop | 1.000 | 1.000 | 1.000 |

## Full deterministic pipeline

| Variant | Quality | Document recall | Fact recall | Answer | Graph | Hard gate | Quality gate |
|---|---:|---:|---:|---:|---:|:---:|:---:|
| full-current | 0.917 | 1.000 | 0.838 | 1.000 | 0.667 | pass | fail |
| full-advanced-structure | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | pass | pass |
| full-advanced-sentence-window | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | pass | pass |

## Stage recommendations

- Chunking: `chunk-structure-aware`
- Chunk Size: `chunk-size-1800`
- Retrieval: `retrieval-lexical`
- Retrieval Depth: `top-k-16`
- Query Expansion: `query-adaptive`
- Reranking: `rerank-deterministic`
- Graph: `graph-intent-multihop`
- Full Pipeline: `full-advanced-structure`

## Recommendation notes

- Sentence-window has the highest retrieval fact recall but is not the default while duplicated parent passages exceed 50% redundancy; normalize parent storage before promotion.
- Chunk-size and top-K winners optimize recall first, then packed context size. Re-run these sweeps on realistic thread-length and paraphrase cases before changing Thunderbird defaults.
- Lexical search wins this exact-term synthetic corpus. Keep hybrid as the production candidate until a semantic/paraphrase corpus and real embedding model are evaluated.
- HyDE, RAPTOR, Self-RAG, and a live cross-encoder remain separate future lanes. Generated contextual retrieval is evaluated by its own live command and is not mixed into this deterministic baseline.

## Per-case retrieval audit

Every evidence span below is preserved in full in the JSON companion.

### Chunking

| Variant | K | Case | Document recall | Fact recall | MRR | Source coverage | Evidence spans |
|---|---:|---|---:|---:|---:|---:|---|
| chunk-fixed | 8 | exact-identifier | 1.000 | 1.000 | 1.000 | 0.126 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://multilingual#0-90 |
| chunk-fixed | 8 | long-document-coverage | 1.000 | 0.812 | 1.000 | 0.819 | doc://long-10240#0-1194; doc://long-10240#9147-10235; doc://long-10240#5077-6277; doc://long-10240#3040-4238; doc://long-10240#6097-7295; doc://long-10240#4058-5257; doc://long-10240#2034-3220; doc://long-10240#1014-2214 |
| chunk-fixed | 8 | latest-revision | 1.000 | 1.000 | 1.000 | 1.000 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#3040-4238; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://multilingual#0-90 |
| chunk-fixed | 8 | graph-multihop | 1.000 | 1.000 | 1.000 | 1.000 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#9147-10235; doc://long-10240#8131-9327; doc://graph-vendor#0-75; doc://revision-old#0-81 |
| chunk-fixed | 8 | multilingual | 1.000 | 1.000 | 1.000 | 1.000 | doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#0-1194; doc://long-10240#6097-7295; doc://long-10240#7115-8310; doc://long-10240#3040-4238; doc://long-10240#2034-3220; doc://long-10240#1014-2214 |
| chunk-fixed | 8 | prompt-injection | 1.000 | 1.000 | 1.000 | 1.000 | doc://injection#0-130; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://long-10240#5077-6277; doc://long-10240#6097-7295; doc://long-10240#0-1194 |
| chunk-fixed | 8 | scope-isolation | not scored | not scored | not scored | not scored | doc://long-10240#6097-7295; doc://long-10240#5077-6277; doc://long-10240#3040-4238; doc://long-10240#0-1194; doc://long-10240#7115-8310; doc://injection#0-130; doc://long-10240#1014-2214; doc://long-10240#2034-3220 |
| chunk-fixed | 8 | no-answer | not scored | not scored | not scored | not scored | doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://revision-old#0-81; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://long-10240#8131-9327; doc://long-10240#9147-10235 |
| chunk-structure-aware | 8 | exact-identifier | 1.000 | 1.000 | 1.000 | 0.242 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://long-10240#7116-8316; doc://graph-vendor#0-75; doc://graph-team#0-93 |
| chunk-structure-aware | 8 | long-document-coverage | 1.000 | 0.812 | 1.000 | 0.818 | doc://long-10240#0-1194; doc://long-10240#9153-10235; doc://long-10240#5078-6277; doc://long-10240#3042-4241; doc://long-10240#6098-7295; doc://long-10240#2035-3220; doc://long-10240#4062-5257; doc://long-10240#1016-2214 |
| chunk-structure-aware | 8 | latest-revision | 1.000 | 1.000 | 1.000 | 1.000 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#3042-4241; doc://long-10240#7116-8316; doc://graph-vendor#0-75; doc://graph-team#0-93 |
| chunk-structure-aware | 8 | graph-multihop | 1.000 | 1.000 | 1.000 | 1.000 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#9153-10235; doc://long-10240#8137-9332; doc://graph-vendor#0-75; doc://revision-old#0-81 |
| chunk-structure-aware | 8 | multilingual | 1.000 | 1.000 | 1.000 | 1.000 | doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#0-1194; doc://long-10240#6098-7295; doc://long-10240#3042-4241; doc://long-10240#2035-3220; doc://long-10240#5078-6277; doc://long-10240#1016-2214 |
| chunk-structure-aware | 8 | prompt-injection | 1.000 | 1.000 | 1.000 | 1.000 | doc://injection#0-130; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://long-10240#6098-7295; doc://long-10240#5078-6277; doc://long-10240#0-1194 |
| chunk-structure-aware | 8 | scope-isolation | not scored | not scored | not scored | not scored | doc://long-10240#6098-7295; doc://long-10240#0-1194; doc://long-10240#5078-6277; doc://long-10240#3042-4241; doc://long-10240#1016-2214; doc://injection#0-130; doc://long-10240#2035-3220; doc://long-10240#4062-5257 |
| chunk-structure-aware | 8 | no-answer | not scored | not scored | not scored | not scored | doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://revision-old#0-81; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://long-10240#8137-9332; doc://long-10240#9153-10235 |
| chunk-sentence-window | 8 | exact-identifier | 1.000 | 1.000 | 1.000 | 0.473 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://long-10240#1194-2387; doc://long-10240#4782-5983; doc://long-10240#2387-3583 |
| chunk-sentence-window | 8 | long-document-coverage | 1.000 | 0.906 | 1.000 | 0.883 | doc://long-10240#0-1194; doc://long-10240#9572-10235; doc://long-10240#2387-3583; doc://long-10240#1194-2387; doc://long-10240#3583-4782; doc://long-10240#5983-7178; doc://long-10240#4782-5983; doc://long-10240#7178-8371 |
| chunk-sentence-window | 8 | latest-revision | 1.000 | 1.000 | 1.000 | 1.000 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#2387-3583; doc://long-10240#1194-2387; doc://long-10240#4782-5983; doc://long-10240#8371-9572 |
| chunk-sentence-window | 8 | graph-multihop | 0.500 | 0.000 | 1.000 | 0.554 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://long-10240#0-1194; doc://revision-old#0-81; doc://long-10240#3583-4782; doc://long-10240#8371-9572; doc://long-10240#9572-10235 |
| chunk-sentence-window | 8 | multilingual | 1.000 | 1.000 | 1.000 | 1.000 | doc://multilingual#0-90; doc://long-10240#7178-8371; doc://long-10240#5983-7178; doc://long-10240#2387-3583; doc://long-10240#3583-4782; doc://long-10240#4782-5983; doc://injection#0-130; doc://long-10240#8371-9572 |
| chunk-sentence-window | 8 | prompt-injection | 1.000 | 1.000 | 1.000 | 1.000 | doc://injection#0-130; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://long-10240#5983-7178; doc://long-10240#1194-2387; doc://long-10240#4782-5983; doc://long-10240#2387-3583 |
| chunk-sentence-window | 8 | scope-isolation | not scored | not scored | not scored | not scored | doc://long-10240#2387-3583; doc://long-10240#7178-8371; doc://long-10240#4782-5983; doc://long-10240#1194-2387; doc://long-10240#5983-7178; doc://long-10240#8371-9572; doc://injection#0-130; doc://long-10240#0-1194 |
| chunk-sentence-window | 8 | no-answer | not scored | not scored | not scored | not scored | doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://revision-old#0-81; doc://graph-team#0-93; doc://graph-vendor#0-75; doc://long-10240#7178-8371; doc://long-10240#0-1194 |

### Chunk Size

| Variant | K | Case | Document recall | Fact recall | MRR | Source coverage | Evidence spans |
|---|---:|---|---:|---:|---:|---:|---|
| chunk-size-400 | 8 | exact-identifier | 1.000 | 1.000 | 1.000 | 0.164 | doc://exact-orbit#0-105; doc://long-10240#0-400; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://long-10240#1355-1752; doc://long-10240#9467-9861; doc://long-10240#8457-8856 |
| chunk-size-400 | 8 | long-document-coverage | 1.000 | 0.312 | 1.000 | 0.298 | doc://long-10240#9803-10200; doc://long-10240#0-400; doc://long-10240#5753-6151; doc://long-10240#6092-6491; doc://long-10240#341-735; doc://long-10240#4738-5134; doc://long-10240#7112-7505; doc://long-10240#3726-4120 |
| chunk-size-400 | 8 | latest-revision | 1.000 | 1.000 | 1.000 | 1.000 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#3047-3446; doc://long-10240#1355-1752; doc://long-10240#9467-9861; doc://long-10240#8457-8856 |
| chunk-size-400 | 8 | graph-multihop | 0.500 | 0.000 | 1.000 | 0.554 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://long-10240#8798-9190; doc://long-10240#9131-9525; doc://exact-orbit#0-105; doc://long-10240#4403-4797; doc://long-10240#7446-7840 |
| chunk-size-400 | 8 | multilingual | 1.000 | 1.000 | 1.000 | 1.000 | doc://multilingual#0-90; doc://long-10240#0-400; doc://long-10240#7112-7505; doc://long-10240#3726-4120; doc://injection#0-130; doc://long-10240#341-735; doc://long-10240#6772-7170; doc://long-10240#2708-3106 |
| chunk-size-400 | 8 | prompt-injection | 1.000 | 1.000 | 1.000 | 1.000 | doc://injection#0-130; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://long-10240#6092-6491; doc://long-10240#5753-6151; doc://long-10240#0-400 |
| chunk-size-400 | 8 | scope-isolation | not scored | not scored | not scored | not scored | doc://long-10240#2368-2767; doc://long-10240#0-400; doc://long-10240#3047-3446; doc://long-10240#5753-6151; doc://long-10240#6092-6491; doc://long-10240#2708-3106; doc://long-10240#341-735; doc://long-10240#676-1074 |
| chunk-size-400 | 8 | no-answer | not scored | not scored | not scored | not scored | doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://revision-old#0-81; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://long-10240#10141-10235; doc://long-10240#7446-7840 |
| chunk-size-800 | 8 | exact-identifier | 1.000 | 1.000 | 1.000 | 0.318 | doc://exact-orbit#0-105; doc://long-10240#0-792; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://long-10240#1351-2145; doc://long-10240#7444-8242; doc://long-10240#6091-6885 |
| chunk-size-800 | 8 | long-document-coverage | 1.000 | 0.562 | 1.000 | 0.583 | doc://long-10240#0-792; doc://long-10240#9485-10235; doc://long-10240#5410-6210; doc://long-10240#4735-5529; doc://long-10240#4061-4854; doc://long-10240#6767-7563; doc://long-10240#8123-8922; doc://long-10240#3383-4180 |
| chunk-size-800 | 8 | latest-revision | 1.000 | 1.000 | 1.000 | 1.000 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#2707-3501; doc://long-10240#1351-2145; doc://long-10240#6091-6885; doc://long-10240#7444-8242 |
| chunk-size-800 | 8 | graph-multihop | 1.000 | 1.000 | 1.000 | 1.000 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://long-10240#9485-10235; doc://exact-orbit#0-105; doc://long-10240#8803-9603; doc://long-10240#2707-3501; doc://graph-vendor#0-75 |
| chunk-size-800 | 8 | multilingual | 1.000 | 1.000 | 1.000 | 1.000 | doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#0-792; doc://long-10240#6767-7563; doc://long-10240#3383-4180; doc://long-10240#2026-2826; doc://long-10240#4735-5529; doc://long-10240#673-1470 |
| chunk-size-800 | 8 | prompt-injection | 1.000 | 1.000 | 1.000 | 1.000 | doc://injection#0-130; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://long-10240#5410-6210; doc://long-10240#4061-4854; doc://long-10240#4735-5529 |
| chunk-size-800 | 8 | scope-isolation | not scored | not scored | not scored | not scored | doc://long-10240#6767-7563; doc://long-10240#673-1470; doc://long-10240#0-792; doc://long-10240#8123-8922; doc://long-10240#2026-2826; doc://long-10240#5410-6210; doc://injection#0-130; doc://long-10240#4061-4854 |
| chunk-size-800 | 8 | no-answer | not scored | not scored | not scored | not scored | doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://revision-old#0-81; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://long-10240#8803-9603; doc://long-10240#9485-10235 |
| chunk-size-1200 | 8 | exact-identifier | 1.000 | 1.000 | 1.000 | 0.242 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://long-10240#7116-8316; doc://graph-vendor#0-75; doc://graph-team#0-93 |
| chunk-size-1200 | 8 | long-document-coverage | 1.000 | 0.812 | 1.000 | 0.818 | doc://long-10240#0-1194; doc://long-10240#9153-10235; doc://long-10240#5078-6277; doc://long-10240#3042-4241; doc://long-10240#6098-7295; doc://long-10240#2035-3220; doc://long-10240#4062-5257; doc://long-10240#1016-2214 |
| chunk-size-1200 | 8 | latest-revision | 1.000 | 1.000 | 1.000 | 1.000 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#3042-4241; doc://long-10240#7116-8316; doc://graph-vendor#0-75; doc://graph-team#0-93 |
| chunk-size-1200 | 8 | graph-multihop | 1.000 | 1.000 | 1.000 | 1.000 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#9153-10235; doc://long-10240#8137-9332; doc://graph-vendor#0-75; doc://revision-old#0-81 |
| chunk-size-1200 | 8 | multilingual | 1.000 | 1.000 | 1.000 | 1.000 | doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#0-1194; doc://long-10240#6098-7295; doc://long-10240#3042-4241; doc://long-10240#2035-3220; doc://long-10240#5078-6277; doc://long-10240#1016-2214 |
| chunk-size-1200 | 8 | prompt-injection | 1.000 | 1.000 | 1.000 | 1.000 | doc://injection#0-130; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://long-10240#6098-7295; doc://long-10240#5078-6277; doc://long-10240#0-1194 |
| chunk-size-1200 | 8 | scope-isolation | not scored | not scored | not scored | not scored | doc://long-10240#6098-7295; doc://long-10240#0-1194; doc://long-10240#5078-6277; doc://long-10240#3042-4241; doc://long-10240#1016-2214; doc://injection#0-130; doc://long-10240#2035-3220; doc://long-10240#4062-5257 |
| chunk-size-1200 | 8 | no-answer | not scored | not scored | not scored | not scored | doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://revision-old#0-81; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://long-10240#8137-9332; doc://long-10240#9153-10235 |
| chunk-size-1800 | 8 | exact-identifier | 1.000 | 1.000 | 1.000 | 0.183 | doc://exact-orbit#0-105; doc://long-10240#0-1792; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://multilingual#0-90 |
| chunk-size-1800 | 8 | long-document-coverage | 1.000 | 1.000 | 1.000 | 1.000 | doc://long-10240#0-1792; doc://long-10240#9157-10235; doc://long-10240#1523-3321; doc://long-10240#6104-7896; doc://long-10240#3052-4849; doc://long-10240#4580-6373; doc://long-10240#7627-9426; doc://exact-orbit#0-105 |
| chunk-size-1800 | 8 | latest-revision | 1.000 | 1.000 | 1.000 | 1.000 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#1523-3321; doc://long-10240#3052-4849; doc://graph-vendor#0-75; doc://graph-team#0-93 |
| chunk-size-1800 | 8 | graph-multihop | 1.000 | 1.000 | 1.000 | 1.000 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#7627-9426; doc://long-10240#9157-10235; doc://graph-vendor#0-75; doc://revision-old#0-81 |
| chunk-size-1800 | 8 | multilingual | 1.000 | 1.000 | 1.000 | 1.000 | doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#6104-7896; doc://long-10240#0-1792; doc://long-10240#3052-4849; doc://long-10240#1523-3321; doc://long-10240#4580-6373; doc://graph-team#0-93 |
| chunk-size-1800 | 8 | prompt-injection | 1.000 | 1.000 | 1.000 | 1.000 | doc://injection#0-130; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://long-10240#6104-7896; doc://long-10240#4580-6373; doc://long-10240#3052-4849 |
| chunk-size-1800 | 8 | scope-isolation | not scored | not scored | not scored | not scored | doc://long-10240#6104-7896; doc://long-10240#0-1792; doc://long-10240#1523-3321; doc://long-10240#4580-6373; doc://injection#0-130; doc://long-10240#3052-4849; doc://long-10240#7627-9426; doc://long-10240#9157-10235 |
| chunk-size-1800 | 8 | no-answer | not scored | not scored | not scored | not scored | doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://revision-old#0-81; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://long-10240#7627-9426; doc://long-10240#9157-10235 |

### Retrieval

| Variant | K | Case | Document recall | Fact recall | MRR | Source coverage | Evidence spans |
|---|---:|---|---:|---:|---:|---:|---|
| retrieval-exact | 8 | exact-identifier | 1.000 | 1.000 | 1.000 | 0.126 | doc://exact-orbit#0-105; doc://long-10240#0-1194 |
| retrieval-exact | 8 | long-document-coverage | 0.000 | 0.000 | 0.000 | 0.000 | none |
| retrieval-exact | 8 | latest-revision | 1.000 | 1.000 | 1.000 | 1.000 | doc://revision-latest#0-99; doc://revision-old#0-81 |
| retrieval-exact | 8 | graph-multihop | 0.000 | 0.000 | 0.000 | 0.000 | none |
| retrieval-exact | 8 | multilingual | 1.000 | 1.000 | 1.000 | 1.000 | doc://multilingual#0-90 |
| retrieval-exact | 8 | prompt-injection | 0.000 | 0.000 | 0.000 | 0.000 | none |
| retrieval-exact | 8 | scope-isolation | not scored | not scored | not scored | not scored | none |
| retrieval-exact | 8 | no-answer | not scored | not scored | not scored | not scored | none |
| retrieval-lexical | 8 | exact-identifier | 1.000 | 1.000 | 1.000 | 0.126 | doc://exact-orbit#0-105; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://long-10240#0-1194; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://multilingual#0-90 |
| retrieval-lexical | 8 | long-document-coverage | 1.000 | 0.719 | 0.500 | 0.736 | doc://exact-orbit#0-105; doc://long-10240#9153-10235; doc://long-10240#0-1194; doc://long-10240#4062-5257; doc://long-10240#8137-9332; doc://long-10240#3042-4241; doc://long-10240#5078-6277; doc://long-10240#2035-3220 |
| retrieval-lexical | 8 | latest-revision | 1.000 | 1.000 | 1.000 | 1.000 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#3042-4241; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://multilingual#0-90 |
| retrieval-lexical | 8 | graph-multihop | 1.000 | 1.000 | 1.000 | 1.000 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://graph-vendor#0-75; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://long-10240#1016-2214; doc://long-10240#0-1194 |
| retrieval-lexical | 8 | multilingual | 1.000 | 1.000 | 1.000 | 1.000 | doc://multilingual#0-90 |
| retrieval-lexical | 8 | prompt-injection | 1.000 | 1.000 | 1.000 | 1.000 | doc://injection#0-130; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://exact-orbit#0-105 |
| retrieval-lexical | 8 | scope-isolation | not scored | not scored | not scored | not scored | doc://long-10240#0-1194; doc://long-10240#6098-7295; doc://long-10240#8137-9332; doc://long-10240#3042-4241; doc://long-10240#5078-6277; doc://long-10240#1016-2214; doc://long-10240#2035-3220; doc://long-10240#7116-8316 |
| retrieval-lexical | 8 | no-answer | not scored | not scored | not scored | not scored | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://graph-vendor#0-75; doc://graph-team#0-93 |
| retrieval-dense | 8 | exact-identifier | 0.500 | 0.000 | 0.500 | 0.116 | doc://revision-old#0-81; doc://long-10240#7116-8316 |
| retrieval-dense | 8 | long-document-coverage | 1.000 | 0.719 | 1.000 | 0.713 | doc://long-10240#5078-6277; doc://long-10240#6098-7295; doc://long-10240#2035-3220; doc://long-10240#3042-4241; doc://long-10240#0-1194; doc://long-10240#1016-2214; doc://long-10240#4062-5257; doc://injection#0-130 |
| retrieval-dense | 8 | latest-revision | 0.000 | 0.000 | 0.000 | 0.000 | doc://revision-old#0-81; doc://long-10240#7116-8316 |
| retrieval-dense | 8 | graph-multihop | 0.000 | 0.000 | 0.000 | 0.000 | doc://exact-distractor#0-87; doc://long-10240#9153-10235; doc://long-10240#8137-9332; doc://revision-latest#0-99; doc://exact-orbit#0-105 |
| retrieval-dense | 8 | multilingual | 1.000 | 1.000 | 1.000 | 1.000 | doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#0-1194; doc://long-10240#6098-7295; doc://long-10240#3042-4241; doc://long-10240#2035-3220; doc://long-10240#5078-6277; doc://long-10240#1016-2214 |
| retrieval-dense | 8 | prompt-injection | 1.000 | 1.000 | 1.000 | 1.000 | doc://injection#0-130; doc://long-10240#6098-7295; doc://long-10240#5078-6277; doc://long-10240#0-1194; doc://long-10240#4062-5257; doc://long-10240#3042-4241; doc://long-10240#2035-3220; doc://long-10240#1016-2214 |
| retrieval-dense | 8 | scope-isolation | not scored | not scored | not scored | not scored | doc://injection#0-130; doc://long-10240#6098-7295; doc://long-10240#5078-6277; doc://long-10240#3042-4241; doc://long-10240#1016-2214; doc://long-10240#0-1194; doc://long-10240#4062-5257; doc://long-10240#2035-3220 |
| retrieval-dense | 8 | no-answer | not scored | not scored | not scored | not scored | doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://revision-latest#0-99; doc://long-10240#8137-9332; doc://long-10240#9153-10235 |
| retrieval-hybrid | 8 | exact-identifier | 1.000 | 1.000 | 1.000 | 0.242 | doc://exact-orbit#0-105; doc://revision-old#0-81; doc://long-10240#0-1194; doc://long-10240#7116-8316; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://graph-vendor#0-75; doc://graph-team#0-93 |
| retrieval-hybrid | 8 | long-document-coverage | 1.000 | 0.719 | 1.000 | 0.713 | doc://long-10240#5078-6277; doc://long-10240#0-1194; doc://long-10240#3042-4241; doc://long-10240#6098-7295; doc://long-10240#2035-3220; doc://long-10240#4062-5257; doc://long-10240#1016-2214; doc://injection#0-130 |
| retrieval-hybrid | 8 | latest-revision | 1.000 | 1.000 | 0.500 | 1.000 | doc://revision-old#0-81; doc://revision-latest#0-99; doc://long-10240#7116-8316; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#3042-4241; doc://graph-vendor#0-75; doc://graph-team#0-93 |
| retrieval-hybrid | 8 | graph-multihop | 1.000 | 1.000 | 0.167 | 1.000 | doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://exact-orbit#0-105; doc://long-10240#9153-10235; doc://long-10240#8137-9332; doc://graph-team#0-93; doc://graph-vendor#0-75; doc://revision-old#0-81 |
| retrieval-hybrid | 8 | multilingual | 1.000 | 1.000 | 1.000 | 1.000 | doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#0-1194; doc://long-10240#6098-7295; doc://long-10240#3042-4241; doc://long-10240#2035-3220; doc://long-10240#5078-6277; doc://long-10240#1016-2214 |
| retrieval-hybrid | 8 | prompt-injection | 1.000 | 1.000 | 1.000 | 1.000 | doc://injection#0-130; doc://long-10240#6098-7295; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://long-10240#5078-6277; doc://long-10240#0-1194; doc://revision-old#0-81; doc://exact-orbit#0-105 |
| retrieval-hybrid | 8 | scope-isolation | not scored | not scored | not scored | not scored | doc://long-10240#6098-7295; doc://long-10240#0-1194; doc://long-10240#5078-6277; doc://long-10240#3042-4241; doc://long-10240#1016-2214; doc://injection#0-130; doc://long-10240#2035-3220; doc://long-10240#4062-5257 |
| retrieval-hybrid | 8 | no-answer | not scored | not scored | not scored | not scored | doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://exact-orbit#0-105; doc://revision-old#0-81; doc://long-10240#8137-9332; doc://graph-vendor#0-75; doc://long-10240#9153-10235; doc://graph-team#0-93 |

### Retrieval Depth

| Variant | K | Case | Document recall | Fact recall | MRR | Source coverage | Evidence spans |
|---|---:|---|---:|---:|---:|---:|---|
| top-k-4 | 4 | exact-identifier | 1.000 | 1.000 | 1.000 | 0.126 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://revision-latest#0-99; doc://exact-distractor#0-87 |
| top-k-4 | 4 | long-document-coverage | 1.000 | 0.469 | 1.000 | 0.457 | doc://long-10240#0-1194; doc://long-10240#9153-10235; doc://long-10240#5078-6277; doc://long-10240#3042-4241 |
| top-k-4 | 4 | latest-revision | 1.000 | 1.000 | 1.000 | 1.000 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105 |
| top-k-4 | 4 | graph-multihop | 0.500 | 0.000 | 1.000 | 0.554 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105 |
| top-k-4 | 4 | multilingual | 1.000 | 1.000 | 1.000 | 1.000 | doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#0-1194; doc://long-10240#6098-7295 |
| top-k-4 | 4 | prompt-injection | 1.000 | 1.000 | 1.000 | 1.000 | doc://injection#0-130; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81 |
| top-k-4 | 4 | scope-isolation | not scored | not scored | not scored | not scored | doc://long-10240#6098-7295; doc://long-10240#0-1194; doc://long-10240#5078-6277; doc://long-10240#3042-4241 |
| top-k-4 | 4 | no-answer | not scored | not scored | not scored | not scored | doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://revision-old#0-81 |
| top-k-8 | 8 | exact-identifier | 1.000 | 1.000 | 1.000 | 0.242 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://long-10240#7116-8316; doc://graph-vendor#0-75; doc://graph-team#0-93 |
| top-k-8 | 8 | long-document-coverage | 1.000 | 0.812 | 1.000 | 0.818 | doc://long-10240#0-1194; doc://long-10240#9153-10235; doc://long-10240#5078-6277; doc://long-10240#3042-4241; doc://long-10240#6098-7295; doc://long-10240#2035-3220; doc://long-10240#4062-5257; doc://long-10240#1016-2214 |
| top-k-8 | 8 | latest-revision | 1.000 | 1.000 | 1.000 | 1.000 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#3042-4241; doc://long-10240#7116-8316; doc://graph-vendor#0-75; doc://graph-team#0-93 |
| top-k-8 | 8 | graph-multihop | 1.000 | 1.000 | 1.000 | 1.000 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#9153-10235; doc://long-10240#8137-9332; doc://graph-vendor#0-75; doc://revision-old#0-81 |
| top-k-8 | 8 | multilingual | 1.000 | 1.000 | 1.000 | 1.000 | doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#0-1194; doc://long-10240#6098-7295; doc://long-10240#3042-4241; doc://long-10240#2035-3220; doc://long-10240#5078-6277; doc://long-10240#1016-2214 |
| top-k-8 | 8 | prompt-injection | 1.000 | 1.000 | 1.000 | 1.000 | doc://injection#0-130; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://long-10240#6098-7295; doc://long-10240#5078-6277; doc://long-10240#0-1194 |
| top-k-8 | 8 | scope-isolation | not scored | not scored | not scored | not scored | doc://long-10240#6098-7295; doc://long-10240#0-1194; doc://long-10240#5078-6277; doc://long-10240#3042-4241; doc://long-10240#1016-2214; doc://injection#0-130; doc://long-10240#2035-3220; doc://long-10240#4062-5257 |
| top-k-8 | 8 | no-answer | not scored | not scored | not scored | not scored | doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://revision-old#0-81; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://long-10240#8137-9332; doc://long-10240#9153-10235 |
| top-k-16 | 16 | exact-identifier | 1.000 | 1.000 | 1.000 | 0.820 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://long-10240#7116-8316; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#9153-10235; doc://long-10240#1016-2214; doc://long-10240#2035-3220; doc://long-10240#6098-7295; doc://long-10240#8137-9332; doc://long-10240#3042-4241 |
| top-k-16 | 16 | long-document-coverage | 1.000 | 1.000 | 1.000 | 1.000 | doc://long-10240#0-1194; doc://long-10240#9153-10235; doc://long-10240#5078-6277; doc://long-10240#3042-4241; doc://long-10240#6098-7295; doc://long-10240#2035-3220; doc://long-10240#4062-5257; doc://long-10240#1016-2214; doc://long-10240#8137-9332; doc://long-10240#7116-8316; doc://exact-orbit#0-105; doc://injection#0-130; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://multilingual#0-90; doc://exact-distractor#0-87 |
| top-k-16 | 16 | latest-revision | 1.000 | 1.000 | 1.000 | 1.000 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#3042-4241; doc://long-10240#7116-8316; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#9153-10235; doc://long-10240#1016-2214; doc://long-10240#0-1194; doc://long-10240#2035-3220; doc://long-10240#6098-7295; doc://long-10240#8137-9332 |
| top-k-16 | 16 | graph-multihop | 1.000 | 1.000 | 1.000 | 1.000 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#9153-10235; doc://long-10240#8137-9332; doc://graph-vendor#0-75; doc://revision-old#0-81; doc://long-10240#1016-2214; doc://long-10240#0-1194; doc://long-10240#6098-7295; doc://long-10240#7116-8316; doc://long-10240#3042-4241; doc://long-10240#2035-3220; doc://long-10240#4062-5257; doc://long-10240#5078-6277 |
| top-k-16 | 16 | multilingual | 1.000 | 1.000 | 1.000 | 1.000 | doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#0-1194; doc://long-10240#6098-7295; doc://long-10240#3042-4241; doc://long-10240#2035-3220; doc://long-10240#5078-6277; doc://long-10240#1016-2214; doc://long-10240#4062-5257; doc://graph-team#0-93; doc://graph-vendor#0-75 |
| top-k-16 | 16 | prompt-injection | 1.000 | 1.000 | 1.000 | 1.000 | doc://injection#0-130; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://long-10240#6098-7295; doc://long-10240#5078-6277; doc://long-10240#0-1194; doc://long-10240#4062-5257; doc://long-10240#3042-4241; doc://long-10240#2035-3220; doc://long-10240#1016-2214; doc://graph-vendor#0-75; doc://multilingual#0-90; doc://graph-team#0-93 |
| top-k-16 | 16 | scope-isolation | not scored | not scored | not scored | not scored | doc://long-10240#6098-7295; doc://long-10240#0-1194; doc://long-10240#5078-6277; doc://long-10240#3042-4241; doc://long-10240#1016-2214; doc://injection#0-130; doc://long-10240#2035-3220; doc://long-10240#4062-5257; doc://long-10240#8137-9332; doc://long-10240#7116-8316; doc://long-10240#9153-10235; doc://graph-vendor#0-75; doc://multilingual#0-90; doc://graph-team#0-93 |
| top-k-16 | 16 | no-answer | not scored | not scored | not scored | not scored | doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://revision-old#0-81; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://long-10240#8137-9332; doc://long-10240#9153-10235 |

### Query Expansion

| Variant | K | Case | Document recall | Fact recall | MRR | Source coverage | Evidence spans |
|---|---:|---|---:|---:|---:|---:|---|
| query-single | 8 | exact-identifier | 1.000 | 1.000 | 1.000 | 0.242 | doc://exact-orbit#0-105; doc://revision-old#0-81; doc://long-10240#0-1194; doc://long-10240#7116-8316; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://graph-vendor#0-75; doc://graph-team#0-93 |
| query-single | 8 | long-document-coverage | 1.000 | 0.719 | 1.000 | 0.713 | doc://long-10240#5078-6277; doc://long-10240#0-1194; doc://long-10240#3042-4241; doc://long-10240#6098-7295; doc://long-10240#2035-3220; doc://long-10240#4062-5257; doc://long-10240#1016-2214; doc://injection#0-130 |
| query-single | 8 | latest-revision | 1.000 | 1.000 | 0.500 | 1.000 | doc://revision-old#0-81; doc://revision-latest#0-99; doc://long-10240#7116-8316; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#3042-4241; doc://graph-vendor#0-75; doc://graph-team#0-93 |
| query-single | 8 | graph-multihop | 1.000 | 1.000 | 0.167 | 1.000 | doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://exact-orbit#0-105; doc://long-10240#9153-10235; doc://long-10240#8137-9332; doc://graph-team#0-93; doc://graph-vendor#0-75; doc://revision-old#0-81 |
| query-single | 8 | multilingual | 1.000 | 1.000 | 1.000 | 1.000 | doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#0-1194; doc://long-10240#6098-7295; doc://long-10240#3042-4241; doc://long-10240#2035-3220; doc://long-10240#5078-6277; doc://long-10240#1016-2214 |
| query-single | 8 | prompt-injection | 1.000 | 1.000 | 1.000 | 1.000 | doc://injection#0-130; doc://long-10240#6098-7295; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://long-10240#5078-6277; doc://long-10240#0-1194; doc://revision-old#0-81; doc://exact-orbit#0-105 |
| query-single | 8 | scope-isolation | not scored | not scored | not scored | not scored | doc://long-10240#6098-7295; doc://long-10240#0-1194; doc://long-10240#5078-6277; doc://long-10240#3042-4241; doc://long-10240#1016-2214; doc://injection#0-130; doc://long-10240#2035-3220; doc://long-10240#4062-5257 |
| query-single | 8 | no-answer | not scored | not scored | not scored | not scored | doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://exact-orbit#0-105; doc://revision-old#0-81; doc://long-10240#8137-9332; doc://graph-vendor#0-75; doc://long-10240#9153-10235; doc://graph-team#0-93 |
| query-adaptive | 8 | exact-identifier | 1.000 | 1.000 | 1.000 | 0.242 | doc://exact-orbit#0-105; doc://revision-old#0-81; doc://long-10240#0-1194; doc://long-10240#7116-8316; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://graph-vendor#0-75; doc://graph-team#0-93 |
| query-adaptive | 8 | long-document-coverage | 1.000 | 0.750 | 1.000 | 0.748 | doc://long-10240#0-1194; doc://long-10240#3042-4241; doc://long-10240#5078-6277; doc://long-10240#7116-8316; doc://long-10240#4062-5257; doc://revision-old#0-81; doc://long-10240#2035-3220; doc://long-10240#8137-9332 |
| query-adaptive | 8 | latest-revision | 1.000 | 1.000 | 1.000 | 1.000 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#3042-4241; doc://graph-vendor#0-75; doc://long-10240#9153-10235; doc://graph-team#0-93 |
| query-adaptive | 8 | graph-multihop | 1.000 | 1.000 | 0.333 | 1.000 | doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://graph-team#0-93; doc://long-10240#9153-10235; doc://graph-vendor#0-75; doc://long-10240#8137-9332; doc://revision-latest#0-99; doc://revision-old#0-81 |
| query-adaptive | 8 | multilingual | 1.000 | 1.000 | 1.000 | 1.000 | doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#0-1194; doc://long-10240#6098-7295; doc://long-10240#3042-4241; doc://long-10240#2035-3220; doc://long-10240#5078-6277; doc://long-10240#1016-2214 |
| query-adaptive | 8 | prompt-injection | 1.000 | 1.000 | 1.000 | 1.000 | doc://injection#0-130; doc://long-10240#6098-7295; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://long-10240#5078-6277; doc://long-10240#0-1194; doc://revision-old#0-81; doc://exact-orbit#0-105 |
| query-adaptive | 8 | scope-isolation | not scored | not scored | not scored | not scored | doc://long-10240#6098-7295; doc://long-10240#0-1194; doc://long-10240#5078-6277; doc://long-10240#3042-4241; doc://long-10240#1016-2214; doc://injection#0-130; doc://long-10240#2035-3220; doc://long-10240#4062-5257 |
| query-adaptive | 8 | no-answer | not scored | not scored | not scored | not scored | doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://exact-orbit#0-105; doc://revision-old#0-81; doc://long-10240#8137-9332; doc://long-10240#9153-10235; doc://graph-vendor#0-75; doc://graph-team#0-93 |

### Reranking

| Variant | K | Case | Document recall | Fact recall | MRR | Source coverage | Evidence spans |
|---|---:|---|---:|---:|---:|---:|---|
| rerank-none | 8 | exact-identifier | 1.000 | 1.000 | 1.000 | 0.242 | doc://exact-orbit#0-105; doc://revision-old#0-81; doc://long-10240#0-1194; doc://long-10240#7116-8316; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://graph-vendor#0-75; doc://graph-team#0-93 |
| rerank-none | 8 | long-document-coverage | 1.000 | 0.719 | 1.000 | 0.713 | doc://long-10240#5078-6277; doc://long-10240#0-1194; doc://long-10240#3042-4241; doc://long-10240#6098-7295; doc://long-10240#2035-3220; doc://long-10240#4062-5257; doc://long-10240#1016-2214; doc://injection#0-130 |
| rerank-none | 8 | latest-revision | 1.000 | 1.000 | 0.500 | 1.000 | doc://revision-old#0-81; doc://revision-latest#0-99; doc://long-10240#7116-8316; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#3042-4241; doc://graph-vendor#0-75; doc://graph-team#0-93 |
| rerank-none | 8 | graph-multihop | 1.000 | 1.000 | 0.167 | 1.000 | doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://exact-orbit#0-105; doc://long-10240#9153-10235; doc://long-10240#8137-9332; doc://graph-team#0-93; doc://graph-vendor#0-75; doc://revision-old#0-81 |
| rerank-none | 8 | multilingual | 1.000 | 1.000 | 1.000 | 1.000 | doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#0-1194; doc://long-10240#6098-7295; doc://long-10240#3042-4241; doc://long-10240#2035-3220; doc://long-10240#5078-6277; doc://long-10240#1016-2214 |
| rerank-none | 8 | prompt-injection | 1.000 | 1.000 | 1.000 | 1.000 | doc://injection#0-130; doc://long-10240#6098-7295; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://long-10240#5078-6277; doc://long-10240#0-1194; doc://revision-old#0-81; doc://exact-orbit#0-105 |
| rerank-none | 8 | scope-isolation | not scored | not scored | not scored | not scored | doc://long-10240#6098-7295; doc://long-10240#0-1194; doc://long-10240#5078-6277; doc://long-10240#3042-4241; doc://long-10240#1016-2214; doc://injection#0-130; doc://long-10240#2035-3220; doc://long-10240#4062-5257 |
| rerank-none | 8 | no-answer | not scored | not scored | not scored | not scored | doc://exact-distractor#0-87; doc://revision-latest#0-99; doc://exact-orbit#0-105; doc://revision-old#0-81; doc://long-10240#8137-9332; doc://graph-vendor#0-75; doc://long-10240#9153-10235; doc://graph-team#0-93 |
| rerank-deterministic | 8 | exact-identifier | 1.000 | 1.000 | 1.000 | 0.242 | doc://exact-orbit#0-105; doc://long-10240#0-1194; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://long-10240#7116-8316; doc://graph-vendor#0-75; doc://graph-team#0-93 |
| rerank-deterministic | 8 | long-document-coverage | 1.000 | 0.812 | 1.000 | 0.818 | doc://long-10240#0-1194; doc://long-10240#9153-10235; doc://long-10240#5078-6277; doc://long-10240#3042-4241; doc://long-10240#6098-7295; doc://long-10240#2035-3220; doc://long-10240#4062-5257; doc://long-10240#1016-2214 |
| rerank-deterministic | 8 | latest-revision | 1.000 | 1.000 | 1.000 | 1.000 | doc://revision-latest#0-99; doc://revision-old#0-81; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#3042-4241; doc://long-10240#7116-8316; doc://graph-vendor#0-75; doc://graph-team#0-93 |
| rerank-deterministic | 8 | graph-multihop | 1.000 | 1.000 | 1.000 | 1.000 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#9153-10235; doc://long-10240#8137-9332; doc://graph-vendor#0-75; doc://revision-old#0-81 |
| rerank-deterministic | 8 | multilingual | 1.000 | 1.000 | 1.000 | 1.000 | doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#0-1194; doc://long-10240#6098-7295; doc://long-10240#3042-4241; doc://long-10240#2035-3220; doc://long-10240#5078-6277; doc://long-10240#1016-2214 |
| rerank-deterministic | 8 | prompt-injection | 1.000 | 1.000 | 1.000 | 1.000 | doc://injection#0-130; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://exact-orbit#0-105; doc://long-10240#6098-7295; doc://long-10240#5078-6277; doc://long-10240#0-1194 |
| rerank-deterministic | 8 | scope-isolation | not scored | not scored | not scored | not scored | doc://long-10240#6098-7295; doc://long-10240#0-1194; doc://long-10240#5078-6277; doc://long-10240#3042-4241; doc://long-10240#1016-2214; doc://injection#0-130; doc://long-10240#2035-3220; doc://long-10240#4062-5257 |
| rerank-deterministic | 8 | no-answer | not scored | not scored | not scored | not scored | doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://revision-old#0-81; doc://graph-vendor#0-75; doc://graph-team#0-93; doc://long-10240#8137-9332; doc://long-10240#9153-10235 |
| rerank-embedding | 8 | exact-identifier | 1.000 | 1.000 | 1.000 | 0.242 | doc://exact-orbit#0-105; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://long-10240#0-1194; doc://multilingual#0-90; doc://long-10240#5078-6277; doc://injection#0-130 |
| rerank-embedding | 8 | long-document-coverage | 1.000 | 0.844 | 1.000 | 0.836 | doc://long-10240#9153-10235; doc://long-10240#5078-6277; doc://long-10240#6098-7295; doc://long-10240#2035-3220; doc://long-10240#3042-4241; doc://long-10240#0-1194; doc://long-10240#1016-2214; doc://long-10240#8137-9332 |
| rerank-embedding | 8 | latest-revision | 1.000 | 1.000 | 1.000 | 1.000 | doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#8137-9332; doc://long-10240#5078-6277; doc://long-10240#6098-7295; doc://long-10240#4062-5257; doc://revision-old#0-81 |
| rerank-embedding | 8 | graph-multihop | 0.500 | 0.000 | 1.000 | 0.554 | doc://graph-team#0-93; doc://exact-distractor#0-87; doc://long-10240#0-1194; doc://long-10240#9153-10235; doc://long-10240#4062-5257; doc://long-10240#8137-9332; doc://long-10240#3042-4241; doc://revision-latest#0-99 |
| rerank-embedding | 8 | multilingual | 1.000 | 1.000 | 1.000 | 1.000 | doc://multilingual#0-90; doc://injection#0-130; doc://long-10240#0-1194; doc://long-10240#6098-7295; doc://long-10240#3042-4241; doc://long-10240#2035-3220; doc://long-10240#5078-6277; doc://long-10240#1016-2214 |
| rerank-embedding | 8 | prompt-injection | 1.000 | 1.000 | 1.000 | 1.000 | doc://injection#0-130; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://revision-old#0-81; doc://long-10240#6098-7295; doc://long-10240#5078-6277; doc://long-10240#0-1194; doc://long-10240#4062-5257 |
| rerank-embedding | 8 | scope-isolation | not scored | not scored | not scored | not scored | doc://injection#0-130; doc://long-10240#6098-7295; doc://long-10240#5078-6277; doc://long-10240#8137-9332; doc://long-10240#9153-10235; doc://long-10240#7116-8316; doc://long-10240#3042-4241; doc://long-10240#1016-2214 |
| rerank-embedding | 8 | no-answer | not scored | not scored | not scored | not scored | doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://revision-latest#0-99; doc://revision-old#0-81; doc://long-10240#8137-9332; doc://long-10240#9153-10235; doc://graph-vendor#0-75; doc://graph-team#0-93 |

## Per-case graph audit

| Variant | Case | Relations matched | Relations expected | Fact recall | Provenance | Evidence spans |
|---|---|---:|---:|---:|---:|---|
| graph-off | graph-multihop | 0 | 3 | 1.000 | 1.000 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#9153-10235; doc://graph-vendor#0-75; doc://long-10240#8137-9332; doc://revision-old#0-81 |
| graph-keyword | graph-multihop | 2 | 3 | 1.000 | 1.000 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://graph-vendor#0-75; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#9153-10235; doc://long-10240#8137-9332; doc://revision-old#0-81 |
| graph-intent-multihop | graph-multihop | 3 | 3 | 1.000 | 1.000 | doc://graph-team#0-93; doc://revision-latest#0-99; doc://graph-vendor#0-75; doc://exact-distractor#0-87; doc://exact-orbit#0-105; doc://long-10240#9153-10235; doc://long-10240#8137-9332; doc://revision-old#0-81 |

## Per-case full-pipeline audit

| Variant | Case | Facts matched | Facts expected | Answer score | Graph score | Hard failures | Validated answer |
|---|---|---:|---:|---:|---:|---|---|
| full-current | exact-identifier | 1 | 1 | 1.000 | 1.000 | none | E01: 2027-01-14; F01: ORBIT-731; F02: 2027-01-14; F03: USD 18,450.00; F04: Asha Menon |
| full-current | long-document-coverage | 26 | 32 | 1.000 | 1.000 | none | F01: ORBIT-731; F02: 2027-01-14; F03: USD 18,450.00; F04: Asha Menon; F08: Omar Shah; F09: LANTERN-882; F10: EUR 7,920.00; F11: Blue Cedar; F12: 2027-03-19; F13: Mira Chen; F14: SIGNAL-446; F15: West Atrium; F16: GBP 2,315.00; F17: 2027-04-08; F18: Diego Ruiz; F19: HARBOR-590; F20: Amber Route; F21: INR 84,600.00; F22: 2027-05-22; F23: Noor Ibrahim; F27: 2027-06-11; F28: Elena Petrova; F29: VECTOR-963; F30: Silver Pine; F31: 2027-07-30; F32: Keiko Tanaka |
| full-current | latest-revision | 1 | 1 | 1.000 | 1.000 | none | R02: 2027-09-21 |
| full-current | graph-multihop | 1 | 1 | 1.000 | 0.667 | none | G01: Priya Das; G02: Kestrel Works |
| full-current | multilingual | 1 | 1 | 1.000 | 1.000 | none | M01: Madrid |
| full-current | prompt-injection | 1 | 1 | 1.000 | 1.000 | none | R02: 2027-09-21; S01: quarantined |
| full-current | scope-isolation | 0 | 0 | 1.000 | 1.000 | none | Insufficient source-backed evidence. |
| full-current | no-answer | 0 | 0 | 1.000 | 1.000 | none | Insufficient source-backed evidence. |
| full-advanced-structure | exact-identifier | 1 | 1 | 1.000 | 1.000 | none | E01: 2027-01-14; F01: ORBIT-731; F02: 2027-01-14; F03: USD 18,450.00; F04: Asha Menon |
| full-advanced-structure | long-document-coverage | 32 | 32 | 1.000 | 1.000 | none | F01: ORBIT-731; F02: 2027-01-14; F03: USD 18,450.00; F04: Asha Menon; F05: North Annex; F06: CHECKPOINT-204; F07: 2027-02-03; F08: Omar Shah; F09: LANTERN-882; F10: EUR 7,920.00; F11: Blue Cedar; F12: 2027-03-19; F13: Mira Chen; F14: SIGNAL-446; F15: West Atrium; F16: GBP 2,315.00; F17: 2027-04-08; F18: Diego Ruiz; F19: HARBOR-590; F20: Amber Route; F21: INR 84,600.00; F22: 2027-05-22; F23: Noor Ibrahim; F24: MATRIX-317; F25: South Gallery; F26: USD 4,275.00; F27: 2027-06-11; F28: Elena Petrova; F29: VECTOR-963; F30: Silver Pine; F31: 2027-07-30; F32: Keiko Tanaka |
| full-advanced-structure | latest-revision | 1 | 1 | 1.000 | 1.000 | none | R02: 2027-09-21 |
| full-advanced-structure | graph-multihop | 1 | 1 | 1.000 | 1.000 | none | G01: Priya Das; G02: Kestrel Works |
| full-advanced-structure | multilingual | 1 | 1 | 1.000 | 1.000 | none | M01: Madrid |
| full-advanced-structure | prompt-injection | 1 | 1 | 1.000 | 1.000 | none | R02: 2027-09-21; S01: quarantined |
| full-advanced-structure | scope-isolation | 0 | 0 | 1.000 | 1.000 | none | Insufficient source-backed evidence. |
| full-advanced-structure | no-answer | 0 | 0 | 1.000 | 1.000 | none | Insufficient source-backed evidence. |
| full-advanced-sentence-window | exact-identifier | 1 | 1 | 1.000 | 1.000 | none | E01: 2027-01-14; F01: ORBIT-731; F02: 2027-01-14; F03: USD 18,450.00; F04: Asha Menon |
| full-advanced-sentence-window | long-document-coverage | 32 | 32 | 1.000 | 1.000 | none | F01: ORBIT-731; F02: 2027-01-14; F03: USD 18,450.00; F04: Asha Menon; F05: North Annex; F06: CHECKPOINT-204; F07: 2027-02-03; F08: Omar Shah; F09: LANTERN-882; F10: EUR 7,920.00; F11: Blue Cedar; F12: 2027-03-19; F13: Mira Chen; F14: SIGNAL-446; F15: West Atrium; F16: GBP 2,315.00; F17: 2027-04-08; F18: Diego Ruiz; F19: HARBOR-590; F20: Amber Route; F21: INR 84,600.00; F22: 2027-05-22; F23: Noor Ibrahim; F24: MATRIX-317; F25: South Gallery; F26: USD 4,275.00; F27: 2027-06-11; F28: Elena Petrova; F29: VECTOR-963; F30: Silver Pine; F31: 2027-07-30; F32: Keiko Tanaka |
| full-advanced-sentence-window | latest-revision | 1 | 1 | 1.000 | 1.000 | none | R02: 2027-09-21 |
| full-advanced-sentence-window | graph-multihop | 1 | 1 | 1.000 | 1.000 | none | G01: Priya Das; G02: Kestrel Works |
| full-advanced-sentence-window | multilingual | 1 | 1 | 1.000 | 1.000 | none | M01: Madrid |
| full-advanced-sentence-window | prompt-injection | 1 | 1 | 1.000 | 1.000 | none | R02: 2027-09-21; S01: quarantined |
| full-advanced-sentence-window | scope-isolation | 0 | 0 | 1.000 | 1.000 | none | Insufficient source-backed evidence. |
| full-advanced-sentence-window | no-answer | 0 | 0 | 1.000 | 1.000 | none | Insufficient source-backed evidence. |

These winners are corpus-specific deterministic measurements, not a production-readiness claim.
The JSON companion contains every case metric, evidence span, graph edge, prompt, and validated output.
