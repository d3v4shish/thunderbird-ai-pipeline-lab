# Whole-Email Thread and Template Expansion Evaluation

- Fixture digest: `37b586643dcf9cf1863cbf8ebcfdca032cba8de0d7edc8fd1df3ece956c5f8b6`
- Documents/cases: 18/8
- Deterministic hard contract: PASS
- Production ready: False

A direct source result is the only seed. Host code follows its scoped thread and template assignment once; generated metadata never becomes evidence.

## Deterministic arms

| Arm | Seed accuracy | Answer recall | Related P/R | Fact recall | Span/scope | Gate |
|---|---:|---:|---:|---:|---:|---|
| raw-hybrid | 0.750 | 0.925 | 0.500/0.286 | 1.000 | 1.000/1.000 | PASS |
| whole-email-context | 0.875 | 1.000 | 0.500/0.286 | 1.000 | 1.000/1.000 | PASS |
| thread-memory | 0.875 | 0.961 | 0.500/0.286 | 1.000 | 1.000/1.000 | PASS |
| template-metadata | 0.750 | 0.975 | 0.500/0.286 | 1.000 | 1.000/1.000 | PASS |
| combined-ranking | 0.875 | 1.000 | 0.500/0.286 | 1.000 | 1.000/1.000 | PASS |
| bounded-thread-expansion | 0.875 | 0.638 | 1.000/0.459 | 1.000 | 1.000/1.000 | PASS |
| bounded-family-expansion | 0.875 | 1.000 | 1.000/0.982 | 1.000 | 1.000/1.000 | PASS |
| bounded-union-expansion | 0.875 | 1.000 | 1.000/1.000 | 1.000 | 1.000/1.000 | PASS |
| complete-union-expansion | 0.875 | 1.000 | 1.000/1.000 | 1.000 | 1.000/1.000 | PASS |

## Scale controls

| Family messages | Bounded candidate recall | Complete pages | Ledger recall |
|---:|---:|---:|---:|
| 50 | 0.6400 | 2 | 1.000 |
| 500 | 0.0640 | 16 | 1.000 |
| 5000 | 0.0064 | 157 | 1.000 |

## Live whole-email screen

Not run. The report contains the exact combined-versus-modular call plan.

## Limits

- Deterministic whole-email context and memory are source-derived stand-ins, not model quality results.
- The 50/500/5000 family controls validate bounded-versus-paged accounting; live generation is staged separately.
- Template and thread expansion are one hop and generated metadata is never answer evidence.
- No result promotes this design to Thunderbird or labels it production-ready.
