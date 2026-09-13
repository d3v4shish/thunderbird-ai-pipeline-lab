# Template-Aware Live Qualify Evaluation

| Model | Repeats | Recall | Unsupported | Contract pages | p50 ms | Hard gate |
|---|---:|---:|---:|---:|---:|---|
| granite3.1-moe:3b-instruct-fp16 | 3 | 0.103 | 0 | 0.062 | 175487.0 | FAIL |
| granite4.1:30b-q2_K | 3 | 0.256 | 0 | 0.188 | 227458.8 | FAIL |

## Embedding retrieval smoke

`qwen3-embedding:4b` achieved top-1 1.000 and MRR 1.000 over 8 family queries.

Passing order: none.

Every prompt, raw output, retry, and validated result is retained in the JSON companion.
