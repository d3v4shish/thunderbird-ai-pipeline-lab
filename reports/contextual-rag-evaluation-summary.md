# Contextual RAG Evaluation Summary

Date: 2026-09-12. Production ready: no. Global promotion recommended: no.

## Objective

Test query-independent generated Contextual Retrieval separately from raw
passages and the existing deterministic title/date/category/section metadata.
Generated text may influence search, but the unchanged canonical chunk remains
the only answer and citation evidence.

## Configuration

- Context generator: `qwen3:8b`, digest
  `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.
- Embedding model: `qwen3-embedding:4b`, digest
  `df5bd2e3c74cd8d069d21dc038f1b359fcdc9458fce1c99bd43c9eb1518ff907`.
- Chunking: structure-aware, 1,200 characters, 180-character overlap.
- Retrieval: lexical, dense, and hybrid; K=8; no reranker or graph expansion.
- Prompt: `contextual-retrieval-v2`, query-independent, temperature 0, seed 0,
  16K context, 160 maximum output tokens, 50-word accepted context.
- Corpus: ten frozen documents/eight cases plus one fixed multi-chunk
  cross-reference document/case.
- Safety: loopback only; 17-GiB measured Ollama allocation cap; exact generated
  identifiers/dates/amounts must occur in the source; generated prose is never
  returned as evidence.

Exact command:

```sh
./scripts/run.sh contextual-rag-evaluate \
  --name contextual-rag-qwen3-focused \
  --chat-model qwen3:8b \
  --embedding-model qwen3-embedding:4b \
  --top-k 8 \
  --no-resume
```

The three retrieval repeats reused that immutable context cache with different
report names and `--cache-name contextual-rag-qwen3-focused`.

## Context-generation result

Qwen generated 23/23 contexts successfully. Exact-entity grounding and source
span validity were both 1.000. Mean context length was 151.7 characters.
Generation used 31,540 prompt tokens, 866 output tokens, and 14.811 seconds of
summed model latency. Peak combined active Ollama allocation during the full
run was 12,843,231,476 bytes, below the cap.

One security-document context repeated source-backed hostile instruction
language. This was recorded, remained tenant-scoped untrusted retrieval
metadata, and never became executable input or answer evidence.

## Targeted cross-chunk test

Query: `How much funding did Project BOREALIS-204 receive?`

Expected evidence: the late source chunk containing
`[FACT C01] settlement_value: USD 6,400.00.` That chunk intentionally contains
neither `BOREALIS-204` nor `funding`; the project identity appears more than
3,000 characters earlier.

| Retrieval lane | Raw/metadata result | Generated-context result |
|---|---|---|
| Local lexical | Fact absent from K=8 | Fact at rank 4 |
| Local hybrid | Fact absent from K=8 | Fact at rank 5 |
| Qwen dense | Fact absent from K=8 | Fact at rank 2 |
| Qwen hybrid | Fact absent from K=8 | Fact at rank 3 in all three repeats |

This is the intended Contextual RAG win: the generated context restored the
missing project-to-late-fact relationship.

## Full-suite and stability result

| Repeat | Metadata hybrid fact recall | Generated hybrid fact recall | Metadata fact MRR | Generated fact MRR | Generated challenge rank |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.8158 | 0.7895 | 0.3494 | 0.3604 | 3 |
| 2 | 0.8158 | 0.7105 | 0.3483 | 0.3422 | 3 |
| 3 | 0.8158 | 0.7105 | 0.3494 | 0.3291 | 3 |

Generated context added common descriptions to several repetitive 10KB-ledger
chunks. Those descriptions diluted top-K ordering and displaced required facts,
so overall coverage was worse despite the cross-chunk win.

Full endpoint vector digests differed after model reloads even though model,
inputs, batch order, and cached contexts were unchanged. A focused probe found
identical vectors for repeated calls within one load. The exact runtime cause
is not yet established; this remains an explicit open stability issue.

## Decision

Do not replace normal retrieval with generated Contextual RAG. Retain it as a
candidate only for semantic or cross-chunk-reference queries. Continue routing
explicit “all/every/complete” requests through deterministic document-range
coverage, where top-K semantic ranking is the wrong mechanism.

Before Thunderbird integration, add realistic email-thread/anaphora cases,
diagnose cross-load embedding variance, repeat context generation itself, and
test whether a shorter contextual BM25-only path gives the targeted benefit
without endpoint-vector instability.

Detailed artifacts:

- `contextual-rag-qwen3-focused.md` and `.json`: prompts, raw outputs, all
  contexts, evidence, model/VRAM telemetry, and the focused run.
- `contextual-rag-qwen3-repeat-1.*`, `repeat-2.*`, and `repeat-3.*`: independent
  cached-context embedding and retrieval repeats with vector digests.
- `contextual-rag-qwen3-v2.*`: the earlier generic prompt, retained as a failed
  comparison rather than overwritten.
