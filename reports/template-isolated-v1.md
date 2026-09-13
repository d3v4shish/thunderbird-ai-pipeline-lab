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

## Gates

- PASS: `family_f1`
- PASS: `no_overmerge`
- PASS: `slot_precision`
- PASS: `slot_recall`
- PASS: `source_span_validity`
- PASS: `cross_scope_rejected`
- PASS: `dynamic_value_recall`

Overall isolated hard gate: PASS.

This is an isolated deterministic result, not a production-readiness decision.
