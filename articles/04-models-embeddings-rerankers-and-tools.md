# Models, embeddings, rerankers, and tools

## Four different jobs

“The model” is too vague for this pipeline. Four components do different work:

1. a **chat model** transforms queries, calls bounded tools, and writes answers;
2. an **embedding model** converts text into vectors for dense retrieval;
3. a **reranker** scores query/passage pairs after retrieval;
4. a **deterministic controller/validator** enforces scope, budgets, schemas,
   citations, and completeness.

A better chat model cannot repair a source passage that retrieval never
provided. A reranker cannot recover an item absent from its candidate set. An
embedding model does not generate prose. The deterministic layer is what
prevents generated text from becoming an authority.

## The user-selected model set

The preparation allowlist contained exactly these six tags. Artifact size is
disk storage; it is **not** the 17-GiB limit. Eligibility used the sum of
Ollama-reported active model allocations during the configuration.

| Tag | Role | Family / parameters | Quantization | Artifact | Advertised context | Native tool template |
|---|---|---|---|---:|---:|:---:|
| `granite3.1-moe:3b-instruct-fp16` | chat | Granite MoE, 3.3B | F16 | 6.15 GiB | 131,072 | yes |
| `deepseek-v2:16b` | chat | DeepSeek2, 15.7B | Q4_0 | 8.29 GiB | 163,840 | no |
| `phi4:14b-q8_0` | chat | Phi3 family, 14.7B | Q8_0 | 14.51 GiB | 16,384 | no |
| `qwen3-embedding:4b` | embedding | Qwen3, 4.0B | Q4_K_M | 2.33 GiB | 40,960 | n/a |
| `qwen2.5:14b-instruct-q4_K_M` | chat | Qwen2, 14.8B | Q4_K_M | 8.37 GiB | 32,768 | yes |
| `granite4.1:30b-q2_K` | chat | Granite, 28.9B | Q2_K | 9.99 GiB | 131,072 | yes |

The exact digests and raw byte counts are retained in
[`prepared-models.json`](../reports/prepared-models.json). Model preparation was
explicit and sequential; build/test/benchmark never download models.

## Installed controls

Runtime discovery also found these existing controls:

- `llama3.2:latest` — 3.2B Q4_K_M chat/tools;
- `llama3.1:8b` — 8.0B Q4_K_M chat/tools;
- `qwen3:8b` — 8.2B Q4_K_M chat/tools/thinking;
- `qwen3.6:27b` — 27.8B Q4_K_M chat/vision/tools/thinking;
- `qwen3-embedding:0.6b` — 595.78M Q8_0 embedding;
- `bge-m3:latest` — 566.70M F16 embedding.

Discovery records capability and context from the runtime rather than guessing
from tag names. `bge-m3` was discovered, but the final sampled adaptive matrix
and hardening drift study centered on deterministic local embeddings and Qwen
embedding tags; this document does not manufacture an unrun BGE comparison.

## Chat-model observations

The adaptive calibration executed 48 sampled pipeline configurations. The
table reports each chat model's **best observed sampled configuration**, not a
pure one-factor model benchmark: embedding, reranker, and candidate strategy
also varied. Therefore it is useful for candidate screening, not a claim that
one family is intrinsically superior.

| Chat model | Best sampled quality | Answer correctness | Required-fact recall | JSON acceptance | p50 | Hard gate | Peak Ollama allocation |
|---|---:|---:|---:|---:|---:|:---:|---:|
| `qwen3:8b` | 0.9619 | 1.000 | 0.7714 | 1.000 | 853 ms | pass | 5.95 GiB |
| `phi4:14b-q8_0` | 0.8500 | 0.800 | 0.8000 | 0.833 | 1,573 ms | fail | 15.81 GiB |
| `llama3.1:8b` | 0.7925 | 0.400 | 0.7714 | 1.000 | 1,670 ms | fail | 5.61 GiB |
| `granite3.1-moe:3b-instruct-fp16` | 0.7167 | 0.800 | 0.0000 | 0.500 | 1,063 ms | pass | 6.75 GiB |
| `llama3.2:latest` | 0.7167 | 0.800 | 0.0000 | 0.333 | 820 ms | fail | 6.70 GiB |
| `qwen3.6:27b` | 0.6127 | 0.600 | 0.7429 | 1.000 | 3,386 ms | fail | 15.52 GiB |
| `deepseek-v2:16b` | 0.6222 | 0.400 | 0.0000 | 0.333 | 9,707 ms | fail | 14.30 GiB |
| `qwen2.5:14b-instruct-q4_K_M` | 0.5722 | 0.600 | 0.0000 | 0.833 | 3,335 ms | fail | 13.54 GiB |
| `granite4.1:30b-q2_K` | 0.4889 | 0.600 | 0.0000 | 1.000 | 2,503 ms | fail | 12.56 GiB |

“Hard gate pass” means scope/contract safety passed for that sampled lane; it
does not mean quality passed. **Zero of the 48 calibration records passed every
quality threshold.** Eight hard-gate survivors entered the three-repeat full
phase. The best final combined record remained `qwen3:8b` with deterministic
local embeddings and embedding reranking: quality 0.9550, answer correctness
1.000, required-fact recall 0.7297, schema acceptance 1.000, p50 782 ms, and
peak Ollama allocation 5.95 GiB. It still failed the complete quality gate.

This explains why `qwen3:8b` became the focused test model: it was the strongest
sampled controller/answer candidate under the measured cap, not because every
Qwen behavior was reliable.

### Source-linked memory smoke

A later one-repeat smoke isolated whole-email context extraction and thread
memory on the same four-message final-versus-obsolete fact test. These are
diagnostics, not stable model rankings:

| Model and placement | Answer correct | Context | Answer latency | Peak Ollama allocation |
|---|---:|---:|---:|---:|
| Qwen3 repeated | 1.000 | 42,874 chars | 2.726 s | 6,455,432,314 B |
| Qwen3 hierarchical | 1.000 | 12,009 chars | 0.848 s | 6,455,432,314 B |
| Phi-4 repeated | 0.000 | 42,032 chars | 13.544 s | 16,972,072,876 B |
| Phi-4 hierarchical | 1.000 | 11,987 chars | 2.079 s | 16,972,072,876 B |

Both models extracted 4/4 messages and recovered every labeled summary fact,
but both scored 0.500 relation F1. Qwen omitted the exact M02-bearing citation
and received an audited deterministic citation attachment. Phi's repeated lane
included obsolete M01; hierarchy removed that error. Phi fit under the 17-GiB
Ollama-allocation cap, but required confirmed model unload polling to avoid
partial residency when switching from embeddings.

### Candidate-only structured-memory qualification

The later v4 test is not comparable to the adaptive matrix or free-prose smoke:
it asks a narrower schema-bound question. Each model sees one complete bounded
email plus host-generated candidate IDs and may select only those IDs. Seven
operations were repeated three times at temperature zero, 16,384 context, and
a 1,024-token output cap.

| Model | Valid operations | Prompt/output tokens | Summed latency | Ollama allocation | Outcome |
|---|---:|---:|---:|---:|---|
| `granite3.1-moe:3b-instruct-fp16` | 21/21 | 21,942/2,853 | 16.181 s | 7,325,289,020 B | pass |
| `qwen3:8b` | 21/21 | 20,169/2,766 | 34.358 s | 6,387,799,162 B | pass |
| `qwen2.5:14b-instruct-q4_K_M` | 21/21 | 20,001/2,877 | 52.484 s | 10,521,914,899 B | pass |
| `deepseek-v2:16b` | 5/6 attempted | 2,326/410 accepted-call tokens | 36.762 s | 11,340,947,127 B | fail |

Granite was the fastest passing model in this task; Qwen3 used the smallest
measured allocation. Qwen 2.5 passed but was slowest among the passers.
DeepSeek's sixth response repeated six event IDs, violating `uniqueItems`.
Validation rejected the record and the staged protocol stopped, so Phi-4 and
Granite 4.1 have no v4 result. This is evidence about this exact ID-selection
contract, not a universal ranking of model families. See the
[complete qualification walkthrough](09-structured-memory-v4-qualification.md).

## What the 17-GiB cap measured

The cap is 18,253,611,008 bytes of **Ollama-reported model allocation**, summed
for the active configuration. It is not model file size and not total GPU use.
Whole-GPU telemetry includes desktop/display and other allocations and was
recorded separately. For example, the best sampled `phi4` lane used 15.81 GiB
of Ollama model allocation while whole-GPU telemetry reached 17.61 GiB; the
eligibility decision used the former.

Every ranked chat model also had to be fully GPU-resident and advertise at
least a 16K model capacity. A later answer-limit experiment could deliberately
select a smaller runtime window only after discovery had separately verified
the model's advertised capacity.

## Embedding implementations

### Deterministic local embedding

`deterministic-local-v1` is a standard-library, hash-derived embedding used to
make offline tests reproducible. It is not claimed to have state-of-the-art
semantic quality. Its purpose is to isolate retrieval, storage, graph, and
validation code from endpoint variation.

### `qwen3-embedding:4b`

This was the primary live embedding model, pinned to digest
`df5bd2e3c74cd8d069d21dc038f1b359fcdc9458fce1c99bd43c9eb1518ff907`.
It indexed 180 synthetic emails and 13 queries in the dedicated drift study.

The harness asked separate questions:

- are repeated vectors byte-equal?
- are they at least nearly collinear by cosine?
- does batch size or order change them?
- do duplicate texts in one request match?
- are standalone singleton requests equal?
- do three fresh model loads preserve vectors, ranks, overlap, and recall?

#### Normal batching: 24 texts/request

| Property | Result |
|---|---|
| Equal on repeated same-load passes | no |
| Equal after warm-up/steady-state | no |
| Batch/order invariant | no |
| Duplicates within one request equal | no |
| Repeated standalone singleton equal | yes |
| Fresh-load vectors exactly equal | no |
| Ranking/quality tolerance | pass |

Minimum measured cosine was 0.997264 within the broader comparisons. Relative
to load one, fresh loads two and three had exact ranking rates 0.5385 and
0.7692, but mean overlap@8 0.9712 and 0.9808. Fact recall stayed 0.8462 and mean
document recall stayed 0.9697, so aggregate quality delta was zero. One normal
document pass took about 6.85–6.95 seconds.

This is ranking-stable enough for the explicit tolerance used in the lab, but
it is not a reproducible vector build.

#### Singleton batching: 1 text/request

The first same-load pass still differed from the second (minimum cosine
0.999101), showing a cold/warm effect. The second and third passes became exact.
The complete singleton request sequence was exact across three fresh loads,
with identical rankings and zero quality drift. One pass took 25.99–26.70
seconds—roughly four times the batch-24 path.

The resulting policy is:

- persist document embeddings instead of rebuilding casually;
- use one warm pass plus singleton indexing only when exact rebuild
  reproducibility is required;
- otherwise permit batching only behind overlap@8 >= 0.95 and aggregate quality
  drift <= 0.01, while surfacing byte nondeterminism separately.

Peak Ollama allocation in both drift reports was 6,455,432,314 bytes.

## Reranking methods

Reranking starts from one frozen candidate set. It must not add, delete, or
rewrite candidates; it only changes order.

### No reranker

This is the original fused order and provides the control.

### Deterministic reranker

This combines explicit signals such as identifier match, exact terms, source
metadata, revision/fact coverage, and stable tie-breaking. In the staged suite,
fact recall@8 rose from 0.757 to 0.838 and first-result MRR rose to 1.000.

### Embedding reranker

This reorders candidates by stored query/chunk vector similarity. In the staged
suite it also reached 0.838 fact recall but reduced document recall to 0.917 on
that exact corpus. In the adaptive matrix, the best Qwen chat candidate used an
embedding reranker with deterministic local vectors.

### True cross-encoder

A cross-encoder jointly reads the query and one passage, making it more
expressive than comparing independently created vectors.

The first selected model,
`Alibaba-NLP/gte-multilingual-reranker-base`, did not produce a quality result:

1. GPU TEI failed because Docker had no NVIDIA-capable device driver.
2. CPU TEI 1.7 found no ONNX export, downloaded safetensors, then crashed in
   the GTE Candle CPU path with Intel MKL SGEMM errors.

The successful fallback was
`Alibaba-NLP/gte-reranker-modernbert-base` under TEI 1.9.3, float32, CPU,
8,192 maximum input tokens, and runtime batch 8. A smoke query
`approved cutover date` scored the relevant passage 5.3479 and unrelated lunch
text -1.7130.

All reranking lanes received identical candidates. Results over three repeats:

| Method | Fact recall@8 | Fact MRR | Mean p50 at candidate depth 8 |
|---|---:|---:|---:|
| None | 0.9697 | 0.7933 | approximately 0.001 ms |
| Deterministic | 0.9697 | 0.7933 | approximately 0.127 ms |
| Embedding | 0.9697 | 0.7933 | approximately 2.69 ms |
| Cross-encoder | 0.9697 | 0.8388 | 281 ms |

The cross-encoder improved ordering in every repeat but could not recover the
one fact absent from the candidate/top-8 control. Candidate depths 8, 16, 32,
and 64 had mean p50 about 281, 557, 1,086, and 2,159 ms with no quality change,
so depth 8 is the measured CPU candidate. The CPU model recorded zero VRAM but
the idle container used 9.327 GiB host RAM. GPU latency remains untested.

## Tool calling

The bounded tool surface is:

- `search_passages` — scoped retrieval;
- `fetch_passage` — exact scoped source fetch;
- `range_coverage` — ordered document/thread range;
- `document_outline` — structure without consuming the text-evidence budget;
- `graph_neighborhood` and `graph_path` — scoped source-backed relations;
- `document_aggregate` — bounded deterministic aggregation.

Tool availability is discovered separately from chat capability. The model can
request only names allowed by the current case, while trusted code supplies
scope and enforces call/round/evidence/character limits. Native tool templates
were advertised by Granite 3.1 MoE, Granite 4.1, Qwen 2.5, Qwen 3, Llama 3.1,
and Llama 3.2 tags; Phi4 and DeepSeek V2 did not advertise them in the retained
runtime manifest. The lab can still test strict JSON-style orchestration, but
it does not relabel a missing runtime template as native support.

The deterministic suite tests allowlists, empty allowlists, unknown tools,
strict arguments, cross-scope fetch rejection, hard budgets, and validation of
tool-derived evidence. It does not grant a model arbitrary system or mailbox
access.

## Bottom line

- `qwen3:8b` was the strongest sampled chat/controller candidate, but no full
  configuration passed every quality gate.
- Qwen3 and Phi-4 both passed the source-linked hierarchical answer smoke, but
  one repeat and 0.500 semantic-relation F1 are insufficient for promotion.
- `qwen3-embedding:4b` gave useful retrieval quality but normal batching is not
  byte-deterministic; persistence and an explicit tolerance are required.
- deterministic reranking is cheap and useful; the CPU cross-encoder improves
  order but adds hundreds of milliseconds and substantial host RAM.
- tools are safe only because a deterministic layer constrains them.

Primary artifacts:
[`prepared-models.json`](../reports/prepared-models.json),
[`model-probe.json`](../reports/model-probe.json),
[`adaptive-live-evaluation-v2-calibration.json`](../reports/adaptive-live-evaluation-v2-calibration.json),
[`adaptive-live-evaluation-v2.json`](../reports/adaptive-live-evaluation-v2.json),
[`embedding-drift-final.json`](../reports/embedding-drift-final.json),
[`embedding-drift-singleton-final.json`](../reports/embedding-drift-singleton-final.json), and
[`cross-encoder-candidates-8-final.json`](../reports/cross-encoder-candidates-8-final.json).
The newer focused comparison is in the
[`thread-memory evaluation summary`](../reports/thread-memory-evaluation-summary.md).
