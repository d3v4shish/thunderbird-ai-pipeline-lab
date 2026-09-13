# Deterministic One-Factor RAG Parameter Sweep

Each lane changes one retrieval, chunking, or evidence-budget parameter from the documented structure-aware baseline.

| Factor | Value | Fact recall | MRR | Packed chars | p50 ms | Truncated cases |
|---|---:|---:|---:|---:|---:|---:|
| chunk_chars | 400 | 0.405 | 1.000 | 2050.1 | 1.652 | 0 |
| chunk_chars | 800 | 0.622 | 1.000 | 3641.6 | 1.733 | 0 |
| chunk_chars | 1200 | 0.838 | 1.000 | 5132.8 | 1.297 | 0 |
| chunk_chars | 1800 | 1.000 | 1.000 | 6912.6 | 1.241 | 0 |
| chunk_overlap | 0 | 0.919 | 1.000 | 4904.9 | 1.277 | 0 |
| chunk_overlap | 120 | 0.838 | 1.000 | 4850.2 | 1.578 | 0 |
| chunk_overlap | 180 | 0.838 | 1.000 | 5132.8 | 1.358 | 0 |
| chunk_overlap | 300 | 0.757 | 1.000 | 4692.2 | 1.381 | 0 |
| retrieval_candidates | 8 | 0.838 | 1.000 | 5132.4 | 0.977 | 0 |
| retrieval_candidates | 16 | 0.838 | 1.000 | 5132.8 | 1.259 | 0 |
| retrieval_candidates | 24 | 0.838 | 1.000 | 5132.8 | 1.321 | 0 |
| retrieval_candidates | 32 | 0.838 | 1.000 | 5132.8 | 1.302 | 0 |
| retrieval_candidates | 64 | 0.838 | 1.000 | 5132.8 | 1.289 | 0 |
| top_k | 4 | 0.514 | 1.000 | 1744.2 | 1.314 | 0 |
| top_k | 8 | 0.838 | 1.000 | 5132.8 | 1.463 | 0 |
| top_k | 12 | 1.000 | 1.000 | 8901.5 | 1.606 | 0 |
| top_k | 16 | 1.000 | 1.000 | 11728.1 | 1.332 | 0 |
| context_records | 4 | 0.514 | 1.000 | 1744.2 | 1.343 | 0 |
| context_records | 8 | 0.838 | 1.000 | 5132.8 | 1.298 | 0 |
| context_records | 12 | 1.000 | 1.000 | 8901.5 | 1.623 | 0 |
| context_records | 16 | 1.000 | 1.000 | 11728.1 | 1.400 | 0 |
| context_chars | 600 | 0.541 | 1.000 | 2790.6 | 1.544 | 8 |
| context_chars | 1200 | 0.838 | 1.000 | 5132.8 | 1.413 | 0 |
| context_chars | 1800 | 0.838 | 1.000 | 5132.8 | 1.375 | 0 |
| context_chars | 2400 | 0.838 | 1.000 | 5132.8 | 1.309 | 0 |
| context_total_chars | 4096 | 0.459 | 1.000 | 3517.9 | 1.294 | 4 |
| context_total_chars | 8192 | 0.757 | 1.000 | 4936.0 | 1.310 | 2 |
| context_total_chars | 14400 | 0.838 | 1.000 | 5132.8 | 1.413 | 0 |
| context_total_chars | 32768 | 0.838 | 1.000 | 5132.8 | 1.368 | 0 |
| rrf_k | 10 | 0.838 | 1.000 | 5132.1 | 1.357 | 0 |
| rrf_k | 30 | 0.838 | 1.000 | 5132.1 | 1.518 | 0 |
| rrf_k | 60 | 0.838 | 1.000 | 5132.8 | 1.365 | 0 |
| rrf_k | 120 | 0.838 | 1.000 | 5132.4 | 1.416 | 0 |

## Provisional winners

- `chunk_chars`: `1800` (fact recall 1.000, MRR 1.000).
- `chunk_overlap`: `0` (fact recall 0.919, MRR 1.000).
- `retrieval_candidates`: `8` (fact recall 0.838, MRR 1.000).
- `top_k`: `12` (fact recall 1.000, MRR 1.000).
- `context_records`: `12` (fact recall 1.000, MRR 1.000).
- `context_chars`: `1200` (fact recall 0.838, MRR 1.000).
- `context_total_chars`: `14400` (fact recall 0.838, MRR 1.000).
- `rrf_k`: `60` (fact recall 0.838, MRR 1.000).
