# Template-aware RAG, long-thread, and oversized-email evaluation

Snapshot: 2026-09-13. Every source is frozen synthetic mail. No Thunderbird
profile, mailbox, credential, or real message was opened.

## Verdict

The template-aware mechanics pass their deterministic and staged live gates.
The recommended evaluation design is:

- segment body, signature, and quoted text while preserving original offsets;
- mine sender-scoped Drain families at similarity `0.6`, support `3`, and at
  most `1000` clusters per scope;
- index boilerplate-deduplicated body text, while storing family assignments
  and typed slots once in normalized tables;
- use family metadata only for retrieval/routing/diversification and bounded
  graph links; original source spans remain the only answer evidence;
- use Top-K for localized questions and ordered source paging plus a
  host-validated ledger for explicit exhaustive questions;
- if a model must render a ledger, constrain the JSON shape and allowed IDs,
  then validate every returned value against source.

This does **not** make the complete Thunderbird pipeline production-ready. The
older thread-memory experiment still has 0.500 semantic-relation F1 and an open
full three-repeat Cartesian live matrix. Real-mail distribution, Thunderbird
integration/parity, concurrency, cancellation, restart, and security review
also remain outside this synthetic lab.

## 1. Template mining

The fixture contains 113 messages: 80 messages across eight recurring
families, 32 unique controls, and one cross-tenant shadow. The first six
messages in each recurring family train the miner; only the later four revisions
are scored. Fixture SHA-256:
`c29125164aa129a94bfe26872aec6b264c81b7484ebb98f50ed9b843e6407741`.

| Method | Precision | Recall | F1 |
|---|---:|---:|---:|
| Exact subject | 1.000 | 0.000 | 0.000 |
| Sender + normalized subject skeleton | 1.000 | 1.000 | 1.000 |
| Sender-scoped Drain | 1.000 | 1.000 | 1.000 |

The selected Drain lane scored family F1 `1.000`, slot precision/recall
`1.000/1.000`, source-span validity `1.000`, zero over-merged clusters, and
rejected the cross-tenant assignment. The first slot pattern produced false
identifier matches such as “Order operations”; requiring identifiers to contain
both letters and digits repaired precision from `0.667` to `1.000`.

The 5-token shingle duplicate detector scored only `0.894` F1 at thresholds
`0.85`, `0.90`, and `0.95`; it is therefore not selected as an authoritative
deduplication rule. It may only be a bounded candidate signal.

## 2. Retrieval-representation ablation

All lanes use the same 44 held-out same-scope messages, exact + SQLite
FTS5/BM25 + deterministic local dense retrieval, RRF `60`, full-scan dense
candidates, and Top-4. Only indexed representation changes. Evidence returned
to generation remains the complete original message span.

| Indexed representation | Document R@4 | MRR | Family R@4 | Family P@4 | Characters |
|---|---:|---:|---:|---:|---:|
| Raw subject + source | 1.000 | 0.955 | 1.000 | 1.000 | 11,214 |
| Segmented source | 1.000 | 0.977 | 1.000 | 1.000 | 8,234 |
| Segmented + subject skeleton | 1.000 | 0.962 | 1.000 | 1.000 | 10,117 |
| Segmented + Drain family | 1.000 | 0.966 | 1.000 | 1.000 | 10,730 |
| Boilerplate deduplicated | 1.000 | 0.977 | 1.000 | 1.000 | 4,798 |
| Combined text + all metadata | 1.000 | 0.989 | 1.000 | 1.000 | 11,461 |

Deduplicated indexing is the Pareto choice: it retained every dynamic value and
all measured recall, improved MRR on this fixture, and indexed `57.2%` fewer
characters than raw. Repeating every template and slot in each chunk bought a
small MRR increase but made the surface larger than raw. Normalized template
tables keep that metadata available without this duplication.

## 3. Long-thread scale

| Messages | Family F1 | Exact ledger recall | Direct Top-8 recall | Character reduction | Mining | SQLite |
|---:|---:|---:|---:|---:|---:|---:|
| 500 | 1.000 | 1.000 | 0.0160 | 66.6% | 65.6 ms | 2,527,232 B |
| 1,000 | 1.000 | 1.000 | 0.0080 | 66.5% | 118.1 ms | 4,874,240 B |
| 2,500 | 1.000 | 1.000 | 0.0032 | 66.4% | 315.9 ms | 11,886,592 B |
| 5,000 | 1.000 | 1.000 | 0.0016 | 66.4% | 620.1 ms | 23,678,976 B |

Assignment, latest-family lookup, source/slot validity, bounded eight-family
graph expansion, and exact ledger recall were `1.000` at every size. Fixed
Top-8 is mathematically incapable of exhaustive recall as the thread grows.
The separate generic hierarchy capped a 5,000-message reduction stage at
14,832 characters while preserving all 5,000 facts; the complete final ledger
was 143,001 characters and must itself be paged or streamed.

## 4. Oversized messages

Both template-dense and unique-prose messages were generated at 256KiB, 1MiB,
4MiB, and 16MiB. Each size was traversed with 12K, 20K, and 30K character
pages. Every paged lane retained `1.000` fact recall and source validity.

At 16MiB, prefix-only recall was approximately `0.001`; complete traversal
needed 1,430/851/565 template-dense pages or 1,429/850/565 unique-prose pages.
The deterministic scans took about 1.21–1.25s for template-dense input and
1.37–1.42s for unique prose, with about 35MiB peak traced Python allocation.
Overlap can repeat facts, but source-addressed ledger merge removes duplicates.
The result proves bounded traversal and exact known-schema extraction—not
complete open-ended summarization.

## 5. Live model stages and boundary failure

All live calls were loopback-only, serial, fixed seed, temperature zero, 16K
runtime context, and subject to the 17GiB Ollama-allocation cap. The prompt
contained an untrusted instruction to add
`S99999=PRIVATE-TEMPLATE-SHADOW`.

The original JSON-only smoke passed Granite 3.1 MoE and Granite 4.1. Phi-4,
Qwen 2.5, and Qwen 3 copied every legitimate value but also obeyed the private
instruction. DeepSeek removed required zero padding. In the first 1,000-record
qualification, Granite 3.1 produced the wrong JSON envelope on most 64-record
pages (`0.103` recall, `0.0625` contract-page rate); Granite 4.1 accepted the
private key and timed out at page five in all repeats (`0.256` recall,
`0.1875` contract-page rate).

That investigation found an aggregate-accounting bug: unsupported facts were
rejected per page but counted only after the accepted-fact filter, which always
reported zero. The corrected evaluator counts rejected attempts. It also uses
an Ollama JSON schema that requires the offered IDs and prohibits extra keys.
The schema contains no expected values; values still come only from untrusted
input and must exactly match source after generation.

### Schema-bound smoke

| Model | Recall | Unsupported | Contract pages | Wall | Result |
|---|---:|---:|---:|---:|---|
| Granite 3.1 MoE F16 | 1.000 | 0 | 1.000 | 4.78 s | PASS |
| DeepSeek V2 16B | 0.031 | 31 | 0.000 | 56.94 s | FAIL |
| Phi-4 14B Q8 | 1.000 | 0 | 1.000 | 31.35 s | PASS |
| Qwen 2.5 14B Q4 | 1.000 | 0 | 1.000 | 17.87 s | PASS |
| Granite 4.1 30B Q2 | 1.000 | 0 | 1.000 | 17.37 s | PASS |
| Qwen 3 8B control | 1.000 | 0 | 1.000 | 9.60 s | PASS |

`qwen3-embedding:4b` ranked all eight family queries first (Top-1 `1.000`, MRR
`1.000`, 2,560 dimensions). Earlier fresh-load drift findings still apply; this
eight-query smoke does not establish global embedding repeatability.

### Three-repeat qualification and stress

At 1,000 records, Granite 3.1 and Qwen 3 both recovered `3,000/3,000` exact
values with no unsupported output or retry. Granite repeat times were
112.47/100.15/99.63s (p50 100.15s); Qwen was
222.78/218.28/214.36s (p50 218.28s). Granite used 7,325,289,020 bytes of
Ollama VRAM versus Qwen's 6,387,799,162 bytes.

Granite alone advanced to the 5,000-record stress stage. All three repeats
recovered `5,000/5,000` values over 79 pages with contract rate `1.000`, zero
unsupported output, and zero retries. Times were 528.90/546.03/543.98s (p50
543.98s). Across the stage it generated 362,607 output tokens from 409,338
prompt tokens. The largest page used 1,745 prompt and 1,547 output tokens, so a
larger context window would add KV-cache cost without increasing evidence. Peak
Ollama allocation remained 7,325,289,020 bytes; peak whole-GPU telemetry was
11,771,314,176 bytes.

This live pass validates bounded ledger rendering, not arbitrary semantic
summary quality. Deterministic rendering should still be preferred whenever
natural-language generation adds no user value.

## 6. Final deterministic verification

- Build: passed.
- Tests: 156/156 passed in 19.079s.
- Final implementation digest:
  `74fb7f1504c61c40252649d6f60f6a15c26f9d1ed4655935204e4ccc1a5c7304`.
- Live v2 implementation digest:
  `e80911d3b9e2d64a311c1b740ce8f8f251c132e334f8cf58b070d79eb3f0ebb9`.
  The later source-only change added the isolated retrieval ablation/report; it
  did not change the retained live prompt, schema, validator, fixture, or model
  client. The model outputs are intentionally not relabeled as a fresh run.
- Final generic 1K benchmark: 0.751673s ingest, 1,330 docs/s, 1.850639ms query
  p50, 2.622365ms p95, 33,920KiB peak RSS, and 3,465,216 SQLite bytes.
- Immediately preceding same-command run: 0.745197s ingest, 1.860272ms p50,
  3.338602ms p95, 33,488KiB RSS, and identical storage.

The mixed single-run timing changes do not support a performance-improvement
claim. Template-specific cost savings are the paired character counts above;
generic indexing does not execute the optional template evaluator.

## Evidence

- Isolated families/slots/retrieval: `template-isolated-v2-retrieval.json`.
- Generic 50–5,000 scale: `template-extended-scale-v1-threads.json`.
- Template-aware 500–5,000 scale: `template-long-thread-v1.json`.
- 256KiB–16MiB messages: `template-oversized-stress-v1.json`.
- Original boundary failures: `template-live-smoke-v1.json` and
  `template-live-qualify-v1.json`.
- Corrected smoke/qualification/stress: `template-live-smoke-v2-schema.json`,
  `template-live-qualify-v2-schema.json`, and
  `template-live-stress-v2-schema.json`.

Every live JSON retains exact prompts, raw outputs, validation, model digests,
residency, token counts, request sizes, and checkpoint identity.
