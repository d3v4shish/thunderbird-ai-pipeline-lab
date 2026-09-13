# Template-Aware Live Qualify Evaluation

| Model | Repeats | Recall | Unsupported | Contract pages | p50 ms | Hard gate |
|---|---:|---:|---:|---:|---:|---|
| granite3.1-moe:3b-instruct-fp16 | 3 | 1.000 | 0 | 1.000 | 100148.9 | PASS |
| qwen3:8b | 3 | 1.000 | 0 | 1.000 | 218282.5 | PASS |

## Embedding retrieval smoke

`qwen3-embedding:4b` achieved top-1 1.000 and MRR 1.000 over 8 family queries.

Passing order: granite3.1-moe:3b-instruct-fp16, qwen3:8b.

Every prompt, raw output, retry, and validated result is retained in the JSON companion.
