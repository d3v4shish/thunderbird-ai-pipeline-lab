# Normalized Sentence-Window Parent Storage Evaluation

Paired fresh SQLite indexes store identical sentence children either with duplicated parent text or one canonical parent row referenced by each child.

| Layout | DB bytes | Passage chars | Ingest p50 ms | Fact recall | MRR |
|---|---|---|---:|---|---|
| duplicated-parent | [569344, 569344, 569344] | [179594, 179594, 179594] | 13.613 | [0.8918918918918919, 0.8918918918918919, 0.8918918918918919] | [1.0, 1.0, 1.0] |
| normalized-parent | [356352, 356352, 356352] | [11072, 11072, 11072] | 13.129 | [0.8918918918918919, 0.8918918918918919, 0.8918918918918919] | [1.0, 1.0, 1.0] |

Behavioral parity: True. Candidate: True.
Database change: -37.41%.

Promote normalized parent storage only if source/ranking parity is exact and the measured database is no larger.
