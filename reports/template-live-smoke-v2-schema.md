# Template-Aware Live Smoke Evaluation

| Model | Repeats | Recall | Unsupported | Contract pages | p50 ms | Hard gate |
|---|---:|---:|---:|---:|---:|---|
| granite3.1-moe:3b-instruct-fp16 | 1 | 1.000 | 0 | 1.000 | 4778.4 | PASS |
| deepseek-v2:16b | 1 | 0.031 | 31 | 0.000 | 56944.8 | FAIL |
| phi4:14b-q8_0 | 1 | 1.000 | 0 | 1.000 | 31352.1 | PASS |
| qwen2.5:14b-instruct-q4_K_M | 1 | 1.000 | 0 | 1.000 | 17874.7 | PASS |
| granite4.1:30b-q2_K | 1 | 1.000 | 0 | 1.000 | 17371.1 | PASS |
| qwen3:8b | 1 | 1.000 | 0 | 1.000 | 9604.8 | PASS |

## Embedding retrieval smoke

`qwen3-embedding:4b` achieved top-1 1.000 and MRR 1.000 over 8 family queries.

Passing order: granite3.1-moe:3b-instruct-fp16, qwen3:8b, granite4.1:30b-q2_K, qwen2.5:14b-instruct-q4_K_M, phi4:14b-q8_0.

Every prompt, raw output, retry, and validated result is retained in the JSON companion.
