# Chunking, context, and every parameter sweep

## How the parameters fit together

Several limits that sound similar control different stages:

```text
source document
  --chunk_chars / chunk_overlap--> indexed chunks
query
  --retrieval_candidates--> preliminary candidate pool
  --reranker--> reordered pool
  --top_k / context_records--> evidence records selected
  --context_chars--> maximum characters from one record
  --context_total_chars--> maximum characters across all records
  --model context_window--> prompt + evidence + generated tokens that fit
  --max_output_tokens--> maximum generated response
```

For exhaustive threads, `page_size` limits messages per map page and
`reduction_batch_size` limits ledgers combined at one hierarchy stage.

The hardening sweep changed one factor at a time from this deterministic
baseline:

```text
chunking=structure-aware
chunk_chars=1200
chunk_overlap=180
retrieval=hybrid
retrieval_candidates=full scan
reranking=deterministic
top_k=8
context_records=8
context_chars=1800
context_total_chars=unlimited by an extra hard cap
rrf_k=60
```

The suite contained exact identifiers, a 10,240-byte document, a latest
revision, a graph question, multilingual text, prompt injection, no-answer,
and cross-tenant scope isolation. Quality was selected before packed size;
single-run millisecond differences were not treated as speed evidence.

## How chunking quality was evaluated

A chunker is not good because its text “looks natural.” The test measured:

- source coverage: every source character that should be indexable is covered;
- fact integrity: labeled facts remain inside verifiable spans;
- source-span validity: returned text equals the canonical source range;
- retrieval fact recall: expected facts present in top-K evidence;
- document recall and rank;
- overlap/redundancy;
- chunk count and packed characters;
- truncation under per-record and total budgets.

The exact 10,240-byte fixture is important because its 32 facts are distributed
through the full source. It reveals boundary and top-K losses that short emails
cannot.

## Fixed versus structure-aware versus sentence-window

Initial staged results at K=8:

| Chunker | Source coverage | Fact integrity | Chunks | Fact recall | Redundancy |
|---|---:|---:|---:|---:|---:|
| Fixed | 1.000 | 1.000 | 19 | 0.838 | 0.128 |
| Structure-aware | 1.000 | 1.000 | 19 | 0.838 | 0.127 |
| Sentence-window | 1.000 | 1.000 | 173 | 0.892 | 0.938 |

Structure-aware keeps boundaries readable without sacrificing the fixed lane's
quality. Sentence-window indexes precise child sentences and returns parent
passages, raising retrieval recall but initially repeating the same parents in
many rows.

After storage normalization, each child referenced one canonical parent. Over
three paired runs, both legacy and normalized layouts retained document recall
1.000, fact recall 0.8919, MRR 1.000, scope integrity 1.000, and byte-identical
rankings/evidence. The database fell from 569,344 to 356,352 bytes (-37.410%),
and represented parent-passage characters fell from 179,594 to 11,072. Median
ingest moved from 12.702 to 13.116 ms; that small local increase is not treated
as a portable performance claim.

## Chunk size

`chunk_chars` is the target maximum search passage size. Smaller chunks are
precise but a fixed K covers less of a long source; larger chunks carry more
context but consume more prompt space.

| Characters | Fact recall@8 | Fact MRR | Mean packed chars | Redundancy | p50 |
|---:|---:|---:|---:|---:|---:|
| 400 | 0.4054 | 0.2244 | 2,050 | 0.0202 | 1.618 ms |
| 800 | 0.6216 | 0.2978 | 3,642 | 0.0320 | 1.409 ms |
| 1,200 | 0.8378 | 0.3699 | 5,133 | 0.0393 | 1.356 ms |
| 1,800 | 1.0000 | 0.4569 | 6,913 | 0.0694 | 1.276 ms |

`1,800` is the provisional quality candidate for this fixture. It is not a
universal email chunk size: longer chunks increased packed text and should be
revalidated on real email structure before integration.

## Chunk overlap

Overlap repeats the end of one chunk at the beginning of the next. It can save
a fact split by a hard boundary, but it can also consume K with duplicate text.

| Overlap | Fact recall@8 | Fact MRR | Mean packed chars | Redundancy |
|---:|---:|---:|---:|---:|
| 0 | 0.9189 | 0.3772 | 4,905 | 0.0000 |
| 120 | 0.8378 | 0.3564 | 4,850 | 0.0325 |
| 180 | 0.8378 | 0.3699 | 5,133 | 0.0393 |
| 300 | 0.7568 | 0.3285 | 4,692 | 0.0466 |

Zero overlap unexpectedly won this structured synthetic corpus. The result is
plausible because paragraph-aware boundaries already protected facts and
overlap displaced unique chunks. It remains provisional rather than proof that
all email corpora should use zero overlap.

## Retrieval candidate depth

Candidate depth is the pool available *before* final top-K packing. A reranker
cannot reorder a passage it never receives.

| Candidates | Fact recall@8 | Fact MRR | Mean packed chars | p50 |
|---:|---:|---:|---:|---:|
| 8 | 0.8378 | 0.3722 | 5,132 | 1.342 ms |
| 16 | 0.8378 | 0.3699 | 5,133 | 1.569 ms |
| 24 | 0.8378 | 0.3699 | 5,133 | 1.470 ms |
| 32 | 0.8378 | 0.3699 | 5,133 | 1.302 ms |
| 64 | 0.8378 | 0.3699 | 5,133 | 1.338 ms |

Eight was the smallest tested pool with baseline quality. The independent live
cross-encoder sweep agreed: depths 8/16/32/64 had identical recall and MRR,
while CPU reranking cost rose almost linearly. Candidate depth 8 is therefore a
measured budget-reduction candidate for this suite.

## Top-K and evidence-record count

`top_k` controls final retrieval depth. `context_records` controls how many
records can actually enter the prompt. They matched in this one-record-per-rank
experiment, but remain separate controls in the architecture.

| K or records | Fact recall | Fact MRR | Mean packed chars | Redundancy |
|---:|---:|---:|---:|---:|
| 4 | 0.5135 | 0.3176 | 1,744 | 0.0095 |
| 8 | 0.8378 | 0.3699 | 5,133 | 0.0393 |
| 12 | 1.0000 | 0.3870 | 8,902 | 0.0805 |
| 16 | 1.0000 | 0.3870 | 11,728 | 0.1189 |

Twelve is the smallest quality-maximizing value in this sweep. It is not a
solution for unbounded “every message” queries; those use range/paging instead.

## Per-record context characters

This limit truncates each selected evidence record independently.

| Characters/record | Fact recall | Mean packed chars | Truncated cases |
|---:|---:|---:|---:|
| 600 | 0.5405 | 2,791 | 8 |
| 1,200 | 0.8378 | 5,133 | 0 |
| 1,800 | 0.8378 | 5,133 | 0 |
| 2,400 | 0.8378 | 5,133 | 0 |

The underlying chunks were at most 1,200 characters, so larger record limits
could not add information. `1,200` is the measured budget-reduction candidate.

## Total evidence characters

This is a hard cap across all selected records. It is different from the model
context window because the final prompt also contains instructions, query,
JSON syntax, and output space.

| Total cap | Fact recall | Mean packed chars | Truncated cases |
|---:|---:|---:|---:|
| 4,096 | 0.4595 | 3,518 | 4 |
| 8,192 | 0.7568 | 4,936 | 2 |
| 14,400 | 0.8378 | 5,133 | 0 |
| 32,768 | 0.8378 | 5,133 | 0 |

`14,400` was the first hard cap preserving baseline quality. It is deliberately
larger than mean packed characters because the worst case, not the mean, must
fit.

## RRF constant

| `rrf_k` | Fact recall | Fact MRR | nDCG |
|---:|---:|---:|---:|
| 10 | 0.8378 | 0.3722 | 0.9866 |
| 30 | 0.8378 | 0.3699 | 0.9795 |
| 60 | 0.8378 | 0.3699 | 0.9795 |
| 120 | 0.8378 | 0.3722 | 0.9795 |

Differences were too small and fixture-specific to justify changing the
existing value. Recommendation: keep `60`.

## Model context, output, evidence, and temperature

This live test used `qwen3:8b` and the first 32 messages of the frozen
50-message scale thread. The complete evidence was 9,687 characters. Expected
output was one valid JSON object containing exact T001–T032 values and all
supporting citations. Every setting ran three times, seed 0, thinking disabled.

The baseline 16,384 context / 4,096 output used 4,410 prompt tokens and produced
1,932 output tokens.

### Context-window sweep

| Runtime context | Fact recall in 3 repeats | Structured output | Result |
|---:|---|---|---|
| 4,096 | 0, 0, 0 | invalid | fail |
| 8,192 | 1, 1, 1 | valid | pass |
| 16,384 baseline | 1, 1, 1 | valid | pass |
| 32,768 | 1, 1, 1 | valid | pass |

The model itself advertised 40,960 tokens. A bug initially confused the chosen
runtime window with advertised capacity and falsely returned
`CONTEXT_INCOMPATIBLE`; the guard was corrected and covered by pass/fail tests
before the final run.

### Output-token sweep

| Output cap | Fact recall in 3 repeats | Result |
|---:|---|---|
| 256 | 0, 0, 0 | truncated/invalid JSON |
| 512 | 0, 0, 0 | truncated/invalid JSON |
| 1,024 | 0, 0, 0 | truncated/invalid JSON |
| 2,048 | 1, 1, 1 | complete valid JSON |
| 4,096 baseline | 1, 1, 1 | complete valid JSON |

Although 32 facts sound small, values plus 32 citations consumed 1,932 tokens.
`2,048` is only a measured minimum for this map page, not a safe global maximum.

### Evidence-budget sweep

| Evidence characters | Facts available/returned | Recall |
|---:|---:|---:|
| 4,096 | 13/32 | 0.40625 |
| 8,192 | 27/32 | 0.84375 |
| 9,687 full source page | 32/32 | 1.00000 |
| 16,384 cap | all available evidence | 1.00000 |

This demonstrates that the model cannot infer omitted source values. Evidence
budget should be reduced by paging or better selection, not by pretending
truncation is summarization.

### Temperature and combined finalists

Temperature 0.2 happened to return all facts in all repeats, but temperature
0 remains preferred for deterministic extraction.

| Context/output | Recall | Structured | Decision |
|---|---:|:---:|---|
| 6,144 / 2,048 | 0 in all repeats | no | reject |
| 7,168 / 2,048 | 1 in all repeats | yes | smallest measured finalist |
| 8,192 / 2,048 | 1 in all repeats | yes | operational-margin candidate |

Successful calls took about 20–23 seconds because emitting 32 fact values and
citations dominated. Peak Ollama allocation was 7,704,810,618 bytes and peak
whole-GPU telemetry was 9,345,957,888 bytes.

## Thread page and reduction parameters

The scale test fixed `page_size=32`. Full, paged, and hierarchical methods all
returned every fact at 50/100/250/500 messages. Direct K=8 returned exactly
eight.

| Messages | Direct recall | Full evidence | Paged peak stage | Hierarchy peak stage | Hierarchy p50 | Traced hierarchy peak |
|---:|---:|---:|---:|---:|---:|---:|
| 50 | 0.160 | 15,141 chars | 9,687 | 9,687 | 3.012 ms | 54,035 B |
| 100 | 0.080 | 30,392 chars | 9,728 | 9,728 | 5.882 ms | 101,884 B |
| 250 | 0.032 | 76,142 chars | 9,760 | 9,760 | 15.488 ms | 272,464 B |
| 500 | 0.016 | 152,392 chars | 9,760 | 13,484 | 30.752 ms | 529,356 B |

Reduction batch sweep on 500 facts:

| Batch | Recall | Final ledger chars | Peak stage chars | Reduction p50 |
|---:|---:|---:|---:|---:|
| 4 | 1.000 | 13,499 | 9,760 | 0.423 ms |
| 8 | 1.000 | 13,499 | 9,760 | 0.422 ms |
| 16 | 1.000 | 13,499 | 13,484 | 0.414 ms |
| 32 | 1.000 | 13,499 | 13,484 | 0.415 ms |
| 64 | 1.000 | 13,499 | 13,484 | 0.415 ms |

Batch 8 minimized the measured working stage. Batch 16 remains the current
throughput test default. Because extraction was deterministic, sub-millisecond
timing differences are not used as a speed claim.

### Source-linked memory parameters

The later thread-memory hardening run changed one parameter at a time on 180
messages and compared repeated context with thread→email→passage hierarchy.

| Parameter | Hierarchical fact recall | Indexed characters | Retrieval |
|---|---:|---:|---:|
| Baseline | 0.9744 | 287,925 | 124.951 ms |
| Memory 2,000 chars | 0.9744 | 280,766 | 108.095 ms |
| Memory 6,000 chars | 0.9744 | 284,782 | 110.360 ms |
| Summary 80 words | 0.9744 | 287,925 | 111.417 ms |
| Summary 200 words | 0.9744 | 287,925 | 113.297 ms |
| Thread parent K=2 | 0.9744 | 287,925 | 106.433 ms |
| Thread parent K=8 | 0.9744 | 287,925 | 116.542 ms |
| Email parent K=4 | 0.9487 | 287,925 | 111.711 ms |
| Email parent K=16 | 0.9744 | 287,925 | 112.040 ms |

Memory and summary limits did not change quality on this fixture, so larger
budgets have no demonstrated quality benefit yet. Email-parent K=4 did lose one
aggregate fact; K=8 remains the safer evaluated default. The repeated baseline
had the same 0.9744 recall and 0.8077 MRR as hierarchy but indexed 631,854
characters and took 295.249 ms in the final deterministic run. These timings
were not repeated and are used only as cost diagnostics.

The direct-email threshold is also not the advertised context window. The
implementation reserves prompt, prior-memory, and output space; with the
default 48,000-character ceiling, the effective direct source threshold is
33,936 characters. Larger messages take independent canonical pages. A
256-KiB source required 23, 14, or 9 pages at 12K, 20K, or 30K page budgets and
retained complete deterministic fact/source coverage in each lane.

## Provisional configuration produced by these sweeps

These are candidates for the next integrated evaluation, not production
defaults:

```text
chunking              structure-aware
chunk_chars           1800 (quality candidate)
chunk_overlap         0 (fixture-specific candidate)
retrieval             hybrid
retrieval_candidates  8
top_k                 12 for bounded relevance queries
context_records       12
context_chars         1200
context_total_chars   14400
rrf_k                 60
exhaustive routing    ordered range -> page 32 -> hierarchical ledger
reduction_batch       8 or 16
answer temperature    0
answer context        at least 7168 measured; 8192 with margin
answer output         at least 2048 for a 32-fact page
```

Some values conflict intentionally: 1,800-character retrieval chunks with a
1,200-character per-record pack limit need a further combined test because the
one-factor winners were selected independently. The articles do not hide that
integration work behind a synthetic “optimal” label.

Primary artifacts:
[`staged-rag-evaluation.json`](../reports/staged-rag-evaluation.json),
[`hardening-final-parameters.json`](../reports/hardening-final-parameters.json),
[`answer-parameters-final.json`](../reports/answer-parameters-final.json),
[`hardening-final-threads.json`](../reports/hardening-final-threads.json), and
[`hardening-final-storage.json`](../reports/hardening-final-storage.json).
The source-linked follow-up is consolidated in
[`thread-memory-evaluation-summary.md`](../reports/thread-memory-evaluation-summary.md).
