# Deterministic One-Factor RAG Parameter Sweep

Each lane changes one retrieval, chunking, or evidence-budget parameter from the documented structure-aware baseline.

| Factor | Value | Fact recall | MRR | Packed chars | p50 ms | Truncated cases |
|---|---:|---:|---:|---:|---:|---:|
| chunk_chars | 400 | 0.405 | 1.000 | 2050.1 | 1.618 | 0 |
| chunk_chars | 800 | 0.622 | 1.000 | 3641.6 | 1.409 | 0 |
| chunk_chars | 1200 | 0.838 | 1.000 | 5132.8 | 1.356 | 0 |
| chunk_chars | 1800 | 1.000 | 1.000 | 6912.6 | 1.276 | 0 |
| chunk_overlap | 0 | 0.919 | 1.000 | 4904.9 | 1.306 | 0 |
| chunk_overlap | 120 | 0.838 | 1.000 | 4850.2 | 1.320 | 0 |
| chunk_overlap | 180 | 0.838 | 1.000 | 5132.8 | 1.354 | 0 |
| chunk_overlap | 300 | 0.757 | 1.000 | 4692.2 | 1.397 | 0 |
| retrieval_candidates | 8 | 0.838 | 1.000 | 5132.4 | 1.342 | 0 |
| retrieval_candidates | 16 | 0.838 | 1.000 | 5132.8 | 1.569 | 0 |
| retrieval_candidates | 24 | 0.838 | 1.000 | 5132.8 | 1.470 | 0 |
| retrieval_candidates | 32 | 0.838 | 1.000 | 5132.8 | 1.302 | 0 |
| retrieval_candidates | 64 | 0.838 | 1.000 | 5132.8 | 1.338 | 0 |
| top_k | 4 | 0.514 | 1.000 | 1744.2 | 1.367 | 0 |
| top_k | 8 | 0.838 | 1.000 | 5132.8 | 1.554 | 0 |
| top_k | 12 | 1.000 | 1.000 | 8901.5 | 1.325 | 0 |
| top_k | 16 | 1.000 | 1.000 | 11728.1 | 1.308 | 0 |
| context_records | 4 | 0.514 | 1.000 | 1744.2 | 1.265 | 0 |
| context_records | 8 | 0.838 | 1.000 | 5132.8 | 1.585 | 0 |
| context_records | 12 | 1.000 | 1.000 | 8901.5 | 1.360 | 0 |
| context_records | 16 | 1.000 | 1.000 | 11728.1 | 1.427 | 0 |
| context_chars | 600 | 0.541 | 1.000 | 2790.6 | 1.366 | 8 |
| context_chars | 1200 | 0.838 | 1.000 | 5132.8 | 1.540 | 0 |
| context_chars | 1800 | 0.838 | 1.000 | 5132.8 | 1.290 | 0 |
| context_chars | 2400 | 0.838 | 1.000 | 5132.8 | 1.383 | 0 |
| context_total_chars | 4096 | 0.459 | 1.000 | 3517.9 | 1.321 | 4 |
| context_total_chars | 8192 | 0.757 | 1.000 | 4936.0 | 1.307 | 2 |
| context_total_chars | 14400 | 0.838 | 1.000 | 5132.8 | 1.326 | 0 |
| context_total_chars | 32768 | 0.838 | 1.000 | 5132.8 | 1.324 | 0 |
| rrf_k | 10 | 0.838 | 1.000 | 5132.1 | 1.316 | 0 |
| rrf_k | 30 | 0.838 | 1.000 | 5132.1 | 1.354 | 0 |
| rrf_k | 60 | 0.838 | 1.000 | 5132.8 | 1.399 | 0 |
| rrf_k | 120 | 0.838 | 1.000 | 5132.4 | 1.325 | 0 |

## Provisional winners

- `chunk_chars`: `1800` (fact recall 1.000, MRR 1.000).
- `chunk_overlap`: `0` (fact recall 0.919, MRR 1.000).
- `retrieval_candidates`: `8` (fact recall 0.838, MRR 1.000).
- `top_k`: `12` (fact recall 1.000, MRR 1.000).
- `context_records`: `12` (fact recall 1.000, MRR 1.000).
- `context_chars`: `1200` (fact recall 0.838, MRR 1.000).
- `context_total_chars`: `14400` (fact recall 0.838, MRR 1.000).
- `rrf_k`: `60` (fact recall 0.838, MRR 1.000).
