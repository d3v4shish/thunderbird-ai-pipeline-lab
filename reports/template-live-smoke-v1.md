# Template-Aware Live Smoke Evaluation

| Model | Repeats | Recall | Unsupported | Contract pages | p50 ms | Hard gate |
|---|---:|---:|---:|---:|---:|---|
| granite3.1-moe:3b-instruct-fp16 | 1 | 1.000 | 0 | 1.000 | 15731.2 | PASS |
| deepseek-v2:16b | 1 | 0.031 | 0 | 0.000 | 42789.5 | FAIL |
| phi4:14b-q8_0 | 1 | 1.000 | 0 | 0.000 | 33141.6 | FAIL |
| qwen2.5:14b-instruct-q4_K_M | 1 | 1.000 | 0 | 0.000 | 17198.3 | FAIL |
| granite4.1:30b-q2_K | 1 | 1.000 | 0 | 1.000 | 23532.6 | PASS |
| qwen3:8b | 1 | 1.000 | 0 | 0.000 | 10543.5 | FAIL |

## Embedding retrieval smoke

`qwen3-embedding:4b` achieved top-1 1.000 and MRR 1.000 over 8 family queries.

Passing order: granite3.1-moe:3b-instruct-fp16, granite4.1:30b-q2_K.

Every prompt, raw output, retry, and validated result is retained in the JSON companion.
