# Template-Aware RAG Isolated Evaluation

Chronologically train on the first six messages in each recurring family and evaluate only later revisions and unique controls. Template output is derived metadata; slot offsets are checked against immutable source text.

## Corpus

- Documents: 113 synthetic messages.
- Recurring families: 8.
- Chronological train/test split: 60%/40%.
- Fixture digest: `c29125164aa129a94bfe26872aec6b264c81b7484ebb98f50ed9b843e6407741`.

## Family controls

| Method | Precision | Recall | F1 |
|---|---:|---:|---:|
| exact-subject | 1.000 | 0.000 | 0.000 |
| subject-skeleton | 1.000 | 1.000 | 1.000 |
| sender-scoped-drain | 1.000 | 1.000 | 1.000 |

## Selected isolated candidate

- Settings: `{"max_clusters": 1000, "min_support": 3, "sender_scoped": true, "similarity_threshold": 0.6}`.
- Family F1: 1.000.
- Slot precision/recall: 1.000/1.000.
- Over-merged clusters: 0.
- Source-span validity: 1.000.
- Boilerplate character reduction: 66.6%.
- Dynamic-value recall after reduction: 1.000.

## Retrieval representation ablation

| Lane | Document R@4 | Document MRR | Family R@4 | Family P@4 | Indexed chars |
|---|---:|---:|---:|---:|---:|
| raw | 1.000 | 0.955 | 1.000 | 1.000 | 11214 |
| segmented | 1.000 | 0.977 | 1.000 | 1.000 | 8234 |
| subject-skeleton | 1.000 | 0.962 | 1.000 | 1.000 | 10117 |
| drain-family | 1.000 | 0.966 | 1.000 | 1.000 | 10730 |
| deduplicated | 1.000 | 0.977 | 1.000 | 1.000 | 4798 |
| combined | 1.000 | 0.989 | 1.000 | 1.000 | 11461 |

Selected retrieval surface: `deduplicated` (57.2% fewer indexed characters than `raw`).

The deduplicated lane preserved document/family recall and exact dynamic values with a smaller index. Keep Drain families and typed slots in normalized routing tables instead of repeating them in every chunk.

## Gates

- PASS: `family_f1`
- PASS: `no_overmerge`
- PASS: `slot_precision`
- PASS: `slot_recall`
- PASS: `source_span_validity`
- PASS: `cross_scope_rejected`
- PASS: `dynamic_value_recall`
- PASS: `retrieval_no_recall_regression`
- PASS: `retrieval_source_and_scope`
- PASS: `deterministic_cost_gain`

Overall isolated hard gate: PASS.

This is an isolated deterministic result, not a production-readiness decision.
