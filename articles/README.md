# Thunderbird AI pipeline evaluation: article index

This series explains the evaluation lab from first principles and ties every
important statement to a retained report. It is written for readers who do not
want to reverse-engineer several megabytes of JSON.

The short conclusion is: the original adaptive and advanced-RAG experiments
are complete, and the candidate-only structured-memory v4 successor has passed
three fresh repeats with Qwen3, Granite 3.1 MoE, and Qwen 2.5. DeepSeek failed
closed on duplicate IDs, which stopped the staged ladder before Phi-4 and
Granite 4.1. The evaluated Thunderbird AI pipeline is **not certified as
production-ready**. Several components are good candidates for integration,
especially structure-aware chunks, hybrid retrieval, deterministic thread-range
coverage, normalized parent storage, host-owned source events, and strict
source/citation validation. Generated query expansion is not a global win and
endpoint embeddings are not byte-stable in normal batches.

## Reading order

1. [What RAG actually does: one email from source to answer](00-rag-one-email-from-source-to-answer.md)
   is the ground-up walkthrough: complete email, every chunk representation,
   SQLite/FTS5/BM25, exact search, embeddings, RRF, reranking, evidence packing,
   prompt, output, and validation.
2. [How the pipeline and RAG methods work](01-pipeline-and-rag-methods.md)
   explains ordinary RAG, Contextual RAG, HyDE, Fusion, decomposition,
   Corrective RAG, Adaptive/Agentic RAG, GraphRAG, sentence-window retrieval,
   and hierarchical thread coverage.
3. [Complete test catalog and reproduction](02-test-catalog-and-reproduction.md)
   inventories the 202 deterministic tests and every measured evaluation lane.
4. [Actual emails, prompts, outputs, and dry-runs](03-emails-prompts-and-dry-runs.md)
   follows retained ORCHID, MERIDIAN, ATLAS, GUARDIAN, BOREALIS, and 10,240-byte
   cases through the real experimental pipeline.
5. [Models, embeddings, rerankers, and tools](04-models-embeddings-rerankers-and-tools.md)
   separates model quality, model artifact size, measured VRAM, embedding
   behavior, reranking behavior, and tool-calling support.
6. [Chunking and every parameter sweep](05-chunking-context-and-parameters.md)
   contains the one-factor tables for chunk size, overlap, candidate depth,
   top-K, evidence packing, model context, output tokens, and reduction batches.
7. [Results, failures, and decisions](06-results-failures-and-decisions.md)
   is the outcome-oriented report: expected versus actual, what won, what
   failed, what remains provisional, and why this is not production-ready.
8. [When one email is larger than the AI context window](07-emails-larger-than-the-context-window.md)
   compares truncation, top-K retrieval, bounded source mapping, validated
   ledger reduction, context/page parameters, and output pagination using one
   exact 256-KiB email and a 1-MiB stress control. Its follow-up
   [complete design matrix](../reports/oversized-design-evaluation-summary.md)
   adds sampling, retrieval/K, reranking, rolling state, hierarchy, and agents.
9. [Template mining and extreme-scale mail](08-template-mining-and-extreme-scale.md)
   explains sender-scoped Drain families, typed slots, boilerplate reduction,
   5,000-message/16MiB tests, schema-constrained model output, and the final
   staged Granite/Qwen result.
10. [Structured memory v4: complete qualification walkthrough](09-structured-memory-v4-qualification.md)
    explains why the model no longer creates anchors, the exact host/LLM
    boundary, every adversarial and scale case, expected versus actual output,
    all live model results, performance, limitations, and reproduction.

## Terminology map

| Term | Meaning in this lab |
|---|---|
| Document | One immutable synthetic source record, often shaped like an email. |
| Chunk | A source-verifiable character range indexed for retrieval. |
| Parent passage | The larger canonical source span returned after a smaller child match. |
| Evidence | An unchanged source span offered to the answer model. |
| Generated retrieval metadata | Model text that may help search but can never be cited as evidence. |
| Exact retrieval | Identifier/metadata matching. |
| Lexical retrieval | SQLite FTS5 term matching. |
| Dense retrieval | Vector similarity between query and chunk embeddings. |
| Hybrid retrieval | Reciprocal-rank fusion of exact, lexical, and dense rankings. |
| Reranking | Reordering an already retrieved candidate set; it cannot recover an absent item. |
| Fact recall@K | Fraction of labeled answer facts present in the first K evidence records. |
| MRR | Reciprocal-rank metric favoring an early first relevant result. |
| Fact MRR | The reciprocal-rank score calculated for every expected fact. |
| Scope integrity | Whether tenant and collection boundaries stayed intact. |
| Source-span validity | Whether returned text is exactly traceable to the canonical source. |
| Hard gate | Safety/contract condition; failure rejects a run regardless of quality score. |
| Quality gate | Required usefulness threshold; passing safety alone is insufficient. |
| Production-ready | Not established by this project; all reports deliberately record `false`. |

## Evidence hierarchy

The articles are explanatory. The source of truth is, in descending order:

1. frozen corpus and case contracts in
   [`data/generated/`](../data/generated/);
2. raw JSON reports in [`reports/`](../reports/);
3. compact generated Markdown reports in [`reports/`](../reports/);
4. review summaries such as
   [`hardening-evaluation-summary.md`](../reports/hardening-evaluation-summary.md);
5. these articles.

All examples are synthetic. Every email address uses `example.invalid`, and no
Thunderbird profile, real mailbox, credentials, or mutable external corpus was
opened.

## Exact evaluated build

The hardening report set records implementation digest
`5335a3c71f247cdec434e48eca674d2538870decd3b5c60d06c507056fb8b2a2`.
The oversized-email report set records implementation digest
`8787d97c5ee556d56a5f639f7e7c0e21649b4bf88cf9e1415ad45420dbee1f14`.
The complete design-matrix report records implementation digest
`06a3f6c2b5d46c75ed5f0cde4965ab6c869622a1724196f416ddd9030de90aba`.
The latest deterministic validation completed 202/202 tests against
implementation digest
`210743be72073bef2ff8ca287b2e79f03ae724c9acb067d993aa71d9281a31a8`.
Retained live reports also pin model digests, so future code or tag changes
cannot silently be mistaken for the versions tested here.

The newest source-linked memory result is consolidated in the
[thread-memory evaluation summary](../reports/thread-memory-evaluation-summary.md).
It records the 1,152-cell preflight, 180-message parameter sweep, 50–500-message
and 10KB/256KiB deterministic hardening, and one-repeat Qwen3/Phi-4 diagnostics.
That free-prose relation stream remains historical and unqualified. Its
candidate-only v4 successor is documented in the
[structured-memory qualification](09-structured-memory-v4-qualification.md):
three models passed 21/21 operations each, DeepSeek failed the sixth operation,
and the remaining model ladder stopped by design.

The newest template-aware result is consolidated in the
[template-aware evaluation summary](../reports/template-aware-evaluation-summary.md).
Its own staged live ledger-rendering gate passed, but it does not close the
separate thread-memory semantic-relation or complete live-matrix gaps.
