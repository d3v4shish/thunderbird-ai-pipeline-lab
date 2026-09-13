# Deterministic One-Factor RAG Parameter Sweep

Each lane changes one retrieval, chunking, or evidence-budget parameter from the documented structure-aware baseline.

| Factor | Value | Fact recall | MRR | Packed chars | p50 ms | Truncated cases |
|---|---:|---:|---:|---:|---:|---:|
| chunk_chars | 400 | 0.405 | 1.000 | 2050.1 | 1.645 | 0 |
| chunk_chars | 800 | 0.622 | 1.000 | 3641.6 | 1.474 | 0 |
| chunk_chars | 1200 | 0.838 | 1.000 | 5132.8 | 1.532 | 0 |
| chunk_chars | 1800 | 1.000 | 1.000 | 6912.6 | 1.236 | 0 |
| chunk_overlap | 0 | 0.919 | 1.000 | 4904.9 | 1.231 | 0 |
| chunk_overlap | 120 | 0.838 | 1.000 | 4850.2 | 1.285 | 0 |
| chunk_overlap | 180 | 0.838 | 1.000 | 5132.8 | 1.329 | 0 |
| chunk_overlap | 300 | 0.757 | 1.000 | 4692.2 | 1.665 | 0 |
| retrieval_candidates | 8 | 0.838 | 1.000 | 5132.4 | 0.993 | 0 |
| retrieval_candidates | 16 | 0.838 | 1.000 | 5132.8 | 1.289 | 0 |
| retrieval_candidates | 24 | 0.838 | 1.000 | 5132.8 | 1.292 | 0 |
| retrieval_candidates | 32 | 0.838 | 1.000 | 5132.8 | 1.286 | 0 |
| retrieval_candidates | 64 | 0.838 | 1.000 | 5132.8 | 1.319 | 0 |
| top_k | 4 | 0.514 | 1.000 | 1744.2 | 1.361 | 0 |
| top_k | 8 | 0.838 | 1.000 | 5132.8 | 1.308 | 0 |
| top_k | 12 | 1.000 | 1.000 | 8901.5 | 1.514 | 0 |
| top_k | 16 | 1.000 | 1.000 | 11728.1 | 1.350 | 0 |
| context_records | 4 | 0.514 | 1.000 | 1744.2 | 1.483 | 0 |
| context_records | 8 | 0.838 | 1.000 | 5132.8 | 1.596 | 0 |
| context_records | 12 | 1.000 | 1.000 | 8901.5 | 1.387 | 0 |
| context_records | 16 | 1.000 | 1.000 | 11728.1 | 1.361 | 0 |
| context_chars | 600 | 0.541 | 1.000 | 2790.6 | 1.333 | 8 |
| context_chars | 1200 | 0.838 | 1.000 | 5132.8 | 1.318 | 0 |
| context_chars | 1800 | 0.838 | 1.000 | 5132.8 | 1.303 | 0 |
| context_chars | 2400 | 0.838 | 1.000 | 5132.8 | 1.323 | 0 |
| context_total_chars | 4096 | 0.459 | 1.000 | 3517.9 | 1.337 | 4 |
| context_total_chars | 8192 | 0.757 | 1.000 | 4936.0 | 1.501 | 2 |
| context_total_chars | 14400 | 0.838 | 1.000 | 5132.8 | 1.513 | 0 |
| context_total_chars | 32768 | 0.838 | 1.000 | 5132.8 | 1.393 | 0 |
| rrf_k | 10 | 0.838 | 1.000 | 5132.1 | 1.356 | 0 |
| rrf_k | 30 | 0.838 | 1.000 | 5132.1 | 1.306 | 0 |
| rrf_k | 60 | 0.838 | 1.000 | 5132.8 | 1.308 | 0 |
| rrf_k | 120 | 0.838 | 1.000 | 5132.4 | 1.322 | 0 |

## Provisional winners

- `chunk_chars`: `1800` (fact recall 1.000, MRR 1.000).
- `chunk_overlap`: `0` (fact recall 0.919, MRR 1.000).
- `retrieval_candidates`: `8` (fact recall 0.838, MRR 1.000).
- `top_k`: `12` (fact recall 1.000, MRR 1.000).
- `context_records`: `12` (fact recall 1.000, MRR 1.000).
- `context_chars`: `1800` (fact recall 0.838, MRR 1.000).
- `context_total_chars`: `32768` (fact recall 0.838, MRR 1.000).
- `rrf_k`: `30` (fact recall 0.838, MRR 1.000).
