# TODO

## Milestone 20: publish the complete current evaluation record

- [x] Reconcile every explanatory document with the structured-memory v4 run.
  Contract: the README, article index, test catalog, model comparison, result
  verdict, architecture, build, benchmark, hotspot, and next-plan documents
  distinguish historical free-prose memory from the qualified candidate-only
  design and retain every failed or deferred gate.
  Validation: documentation search finds no stale 156-test/current-memory
  claims; links resolve to retained reports; exact digests and measured values
  agree with machine-readable JSON.
  Result: the README and seven existing articles now distinguish the historical
  free-prose lane from v4; the 21-section inventory sums to 202 tests and all 18
  checked local-document sets resolve without a missing link.
- [x] Add a newcomer-readable structured-memory v4 test walkthrough.
  Contract: explain the input email, host candidate generation, exact prompt
  contract, expected result, accepted outputs, DeepSeek failure, long-thread
  behavior, security cases, performance, limitations, and reproduction commands
  without treating generated metadata as evidence.
  Validation: every result links to a retained raw or Markdown artifact and the
  article states that all fixtures are synthetic and Thunderbird was untouched.
  Result: `articles/09-structured-memory-v4-qualification.md` records the trust
  boundary, complete synthetic examples, exact prompt/output shape, v3/v4 and
  model comparisons, DeepSeek failure, performance, reproduction, and limits.
- [x] Validate and publish the current lab snapshot.
  Contract: never commit profiles, real mail, credentials, model caches, or
  transient checkpoints; publish only to the configured personal GitHub remote.
  Validation: build, 202-test suite, benchmark record, result-manifest verify,
  secret/private-artifact scan, Git diff check, commit, push, and remote commit
  verification all pass.
  Result: build digest
  `210743be72073bef2ff8ca287b2e79f03ae724c9acb067d993aa71d9281a31a8`,
  202/202 tests, 18-document-set link validation, report-manifest verification,
  and the staged privacy scan passed. Publication commit `58ea17e` was pushed
  to `d3v4shish/thunderbird-ai-pipeline-lab` on `main`; the follow-up commit
  records this completed gate.

## Milestone 19: structured-memory adversarial qualification

- [x] Freeze a broader synthetic-only qualification corpus and unchanged-v3 baseline.
  Contract: exercise 50/100/250/500-message threads, an event after the
  twenty-fourth sentence, ordinary unlabeled prose, an optional-slot template,
  forwarded/quoted history, noisy signatures, and paraphrased prompt
  injection without reading a profile or real mail.
  Validation: fixed fixture digest; exact source-span, scope, chronology,
  durable-event, quote-isolation, family/slot, and relation-candidate accounting;
  retain the original v3 result even when a hypothesis fails.
  Result: unchanged v3 passed 1/6 message cases and 0/4 long-thread cases. It
  lost the optional-slot family, retained quoted/signature/paraphrased hostile
  text, truncated the sentence-31 event, and omitted an old explicit reply
  target at every tested thread size. The failed report is retained.
- [x] Implement only the host-side corrections justified by that baseline.
  Contract: durable source events are not silently truncated by the smaller
  model-hint budget; quoted/signature material cannot become a new current-email
  event; relation choices remain bounded and target only justified earlier
  records; optional slots do not make a valid family impossible to select.
  Validation: candidate-cap sweep, hidden-ID rejection, stale-source rejection,
  long-thread scope/chronology tests, and no regression on the frozen v3 suite.
  Result: v4 passed 6/6 adversarial cases and 4/4 scale cases. It separates a
  512-event durable cap from 24 model hints, isolates quote/signature segments,
  filters paraphrased instructions, pins old explicit references into the
  24-record prompt, narrows relations, and accepts high-confidence families
  with absent optional slots. A 64/128/256 relation pressure sweep retained
  64/96/96 optional no-reference candidates; the selected 64 cap is explicitly
  non-exhaustive, while explicit reply relations remained exact.
- [x] Run the staged model qualification without skipping failed gates.
  Contract: first pass the expanded deterministic gate, then run three fresh
  temperature-zero Qwen repeats, then only installed alternate chat models that
  independently satisfy the advertised-context and 17-GiB Ollama-allocation
  gates. Stop downstream model qualification at the first hard failure.
  Validation: retain exact prompts, raw outputs, validation errors, model digest,
  context/VRAM telemetry, tokens, and latency for every attempted operation.
  Result: Qwen3, Granite 3.1 MoE, and Qwen 2.5 each passed 21/21 operations over
  three fresh repeats within the 17-GiB cap. DeepSeek passed five operations,
  then duplicated six event IDs on the long-message case; strict validation
  rejected it. Per the staged contract, Phi-4 and Granite 4.1 were not run.
- [x] Reconcile reproducibility, measurements, and the promotion verdict.
  Contract: historical v1-v3 artifacts remain unchanged and no Thunderbird or
  real-mail code is touched. Reports clearly separate deterministic mechanics
  from live semantic quality and never imply production readiness.
  Validation: baseline/profile/post-change benchmark, build, full deterministic
  suite, manifest verification, and README/BUILD/ARCHITECTURE/BENCHMARKS/
  HOTSPOTS/NEXT_PLAN updates with every unfinished item left visible.
  Result: build digest is
  `210743be72073bef2ff8ca287b2e79f03ae724c9acb067d993aa71d9281a31a8`;
  202 deterministic tests pass. Baseline/post 1K measurements are retained and
  no performance improvement is claimed. The failed DeepSeek gate prevents a
  production or Thunderbird-promotion claim.

## Milestone 18: host-built structured thread memory

- [x] Add source-bound event and semantic-relation candidates.
  Contract: host code extracts bounded current-email event spans and creates
  relation choices only for earlier same-scope/thread documents. Opaque IDs
  bind scope, document, source digest, predicate/kind, target, and source span;
  instruction-local records remain audit-only and are never model-visible.
  Validation: exact-span, stale-source, duplicate, invented, unsafe,
  future-target, cross-thread, and cross-scope selections fail closed.
  Result: the bounded body-sentence miner retains canonical source spans and
  hides instruction-like occurrences. Relation choices bind an allowed
  predicate and exact assertion event to only an earlier same-thread host
  record; structural `reply_to` edges remain fully deterministic.
- [x] Add one candidate-only chronological model operation per email.
  Contract: the complete bounded current email and prior host-built structured
  memory may be read by the model, but output contains only event-hint,
  relation, family, and slot candidate IDs. The host persists every safe event
  span and constructs the record; model event choices are optional ranking
  hints, not completeness authority. No generated context, summary, event
  prose, relation target, value, anchor, or offset is requested or stored.
  Validation: a frozen clean/repeated/corrected/reply/injection/unique matrix,
  strict dynamic schema, poisoned source, chronological visibility, malformed
  output, cancellation, checkpoint/resume, and three-repeat fake-model tests.
  Result: v1 failed closed after 1/8 valid calls when Qwen selected both
  repeated `$540.00` occurrences for one slot. Schema slot cardinality fixed
  that. V2 completed 8/8 but missed 2/16 safe events, added one lookalike family,
  and selected two predicates for one assertion. V3 moved event completeness to
  the host, filtered typed-family offers lacking a source slot, and capped one
  relation predicate per assertion/target. It passed 8/8 with no errors.
- [x] Test the structured records as low-cost retrieval metadata.
  Contract: a deterministic renderer may decorate retrieval text, while every
  returned passage and answer remains an original canonical source span.
  Validation: compare raw and structured-memory retrieval on the frozen
  related-email cases; require unchanged scope/source validity, no localized
  regression, and exact Complete-mode host enumeration.
  Result: raw and structured localized fact recall were both 1.000. Explicit
  Complete union retained related recall 1.000, exact source/scope validity,
  and zero unrelated messages on the frozen eight-case fixture.
- [x] Run staged live validation and reconcile all project evidence.
  Contract: deterministic candidate/retrieval gates and the isolated one-repeat
  Qwen screen must pass before any three-repeat or alternate-model run. No
  Thunderbird changes or production claim are allowed.
  Validation: baseline/post-change fixed-seed benchmark, build, complete test
  suite, live prompt/raw-output report, result-manifest verification, and
  README/BUILD/ARCHITECTURE/BENCHMARKS/HOTSPOTS/NEXT_PLAN updates.
  Result: Qwen v3 used 5,577 prompt tokens, 704 output tokens, and 9,587.0 ms
  summed latency. Persisted event, relation, family, slot, source, chronology,
  poison, and retrieval gates all passed; model event-hint recall was 0.625 and
  is diagnostic only. Ollama allocation was 6,387,799,162 bytes under the
  17-GiB cap. Build digest is
  `c3183bf94dd4eb90d25ea3416a1fd25c1a3b45d37b6c4e9a908b07eb4c5320a1`;
  193 tests pass. No three-repeat, alternate-model, oversized-page, real-mail,
  or Thunderbird run followed, so the design remains experimental.

## Milestone 17: host-owned slot occurrence candidates

- [x] Add deterministic, source-backed slot occurrence candidates.
  Contract: host code extracts bounded typed candidates from the current
  canonical email, assigns opaque digest-bound IDs, and retains values and
  offsets. Models receive candidate IDs/value previews but never create values,
  anchors, offsets, family members, or scope.
  Validation: unique, repeated-identical, corrected, negated, subtotal/total,
  absent, stale-source, duplicate-ID, unoffered-ID, and cross-scope controls
  reject every unsupported selection.
  Result: bounded amount/date extraction creates source-digest-, document-, and
  scope-bound opaque IDs. Only ID/name/value/local-quote previews are exposed;
  offsets remain private. Stale, duplicated, invented, wrong-family,
  multiple-per-slot, and polluted cross-scope candidates fail closed.
- [x] Add an isolated semantic candidate-selection evaluation.
  Contract: a temperature-zero loopback model selects at most one offered
  candidate per slot or abstains, including corrected and negated amounts and
  a poisoned source. Host validation resolves only the selected ID.
  Validation: frozen fixture digest, exact candidate/value/span accuracy,
  abstention, malformed output, cancellation, resume, raw-output retention,
  and fail-closed reporting are covered before integration testing.
  Result: eight controls are frozen at digest
  `48dc90fd21a9a15dc4099e7de5cee97b12ff1b875fb8b60cd5bfbb17856b76d7`.
  Unfiltered Qwen completed 8/8 calls but followed a poisoned “select first”
  sentence, scoring 0.875 selection accuracy and 0.857 slot precision/recall.
  Sentence-local host filtering hid that unsafe candidate; the version-2 rerun
  passed 8/8 with every family/selection/slot/span/poison metric at 1.000.
- [x] Replace the related-email live anchor schema with candidate IDs.
  Contract: both combined and modular whole-email paths use the same candidate
  set; their validated artifacts preserve the existing `{name,value,start,end}`
  downstream contract. Historical v1/v2 reports remain unchanged.
  Validation: the prior repeated `$540.00` case no longer asks the model for an
  anchor; all existing family, memory, event, relation, expansion, scope, and
  evidence gates still pass.
  Result: combined and modular paths consume identical host candidates and
  preserve validated slot values/spans downstream. Qwen passed both paths for
  the formerly fatal repeated `$540.00` email. Least-privilege modular inputs
  also fixed template-metadata contamination discovered in the first
  integration attempt.
- [x] Run staged validation and reconcile reports/documentation.
  Contract: the isolated Qwen candidate screen must pass before rerunning the
  32-call combined/modular gate. A failed prerequisite stops later work; no
  Thunderbird change or production claim is allowed.
  Validation: build, complete tests, deterministic candidate report, live
  report if run, fixed-seed benchmark, result-manifest verification, and all
  required project documents are current.
  Result: build digest is
  `b0545029a9615a56115a6cdaa710e84214b18f993506369ed37ef21854ded6fa`;
  183 tests pass. The fixed-seed 1K regression report is
  `slot-candidate-postchange-1000`. The full integration advanced from 4/32
  valid operations with anchors to 8/32 with candidates and least-privilege
  inputs, then correctly rejected Qwen copying a hostile source instruction
  into generated context. No three-repeat, alternate-model, large-page, or
  Thunderbird run followed; the complete pipeline remains experimental.

## Milestone 16: whole-email related-message expansion

- [x] Add a frozen synthetic corpus and source-backed expansion primitives.
  Contract: chronological whole-email ingestion stores deterministic template
  assignments and prior-only thread memory; a qualified seed can expand one
  hop to its same-scope thread and template-family members without recursive
  fan-out. Generated metadata is never evidence.
  Validation: localized, complete, lookalike, multilingual, injection,
  repeated-slot, stale-source, and cross-scope fixtures have digest-stable
  expected seed/thread/family/union sets.
  Result: 18 documents and eight cases are frozen at digest
  `0cc1f3097a7d693aac05fc358169bbf6a997415984c9948f155dc6d57c5518ba`.
  Same-scope thread/family enumeration, one-hop union expansion, source-edit
  invalidation, and non-recursive/cross-tenant controls pass.
- [x] Replace model-computed slot offsets and add combined whole-email live
  extraction.
  Contract: the model can select only a host-offered family and returns exact
  slot values plus optional exact anchors; host code resolves unique canonical
  spans and rejects missing or ambiguous values. The combined prompt receives
  the bounded whole email, prior-only thread memory, and at most three offered
  families.
  Validation: original-offset regression, unique/repeated value resolution,
  malformed output, null/wrong family, injection, cancellation, and resume
  tests pass without weakening source validation.
  Result: model schemas now return `{name,value,anchor}` and host code derives
  canonical spans. Unique and uniquely anchored repeated values pass; absent,
  ambiguous, old-offset, and unoffered-family outputs fail closed. Combined
  and three-stage modular paths are checkpointed and covered by fake-client
  tests. The real Qwen3 v2 screen accepted four operations, then correctly
  rejected an anchor containing both repeated `$540.00` occurrences.
- [x] Evaluate ranking-only, bounded expansion, and explicit Complete mode.
  Contract: localized mode expands only one qualified top seed into bounded
  thread/family candidates before reranking; user-selected Complete mode pages
  the non-recursive union and validates an independent ID/source ledger.
  Validation: isolated arms report seed precision, expansion precision/recall,
  fact Recall@K/MRR, complete coverage, source/scope validity, calls, tokens,
  latency, storage, and failure reasons.
  Result: nine isolated deterministic arms were measured. Combined ranking
  raised seed accuracy from 0.750 to 0.875; bounded and Complete union both
  reached 1.000 related precision/recall on the frozen corpus. At
  50/500/5,000 family messages, bounded top-32 coverage was
  0.640/0.064/0.0064 while Complete ledger coverage remained 1.000. A 64-KiB
  source was covered by four ordered pages with no direct model call.
- [x] Run staged validation and reconcile all required documentation.
  Contract: one-repeat Qwen screening must pass before any three-repeat live
  matrix; incomplete live runs return failure and remain explicit in every
  report format. No Thunderbird code is changed and no production claim is
  made.
  Validation: build, full deterministic tests, deterministic report, paired
  benchmark, artifact-manifest verification, and documentation reconciliation
  complete; live results are recorded only if actually run.
  Result: build passed with implementation digest
  `7cf4498617e78a97a41df9104cb4902204bafca8c0d50ce45cc0e01c59e54095`;
  173 deterministic tests pass; the fixed-seed 1K benchmark is retained as
  `related-email-postchange-1000`. Qwen3 remained eligible at 6,387,799,162
  Ollama VRAM bytes but failed the v2 repeated-anchor screen after 4/32 valid
  operations. Therefore no three-repeat, alternate-model, large-page live, or
  Thunderbird run was started, and the feature remains experimental.

## Milestone 15: template, whole-email-context, and thread-memory ladder

- [x] Add one frozen synthetic ladder corpus and deterministic staged evaluator.
  Contract: the corpus covers recurring and drifting templates, forwards,
  multilingual text, injection, same-looking unique messages, cross-scope
  shadows, source revisions, source-linked relations, 10-KiB/256-KiB/1-MiB
  messages, and 50/500/5,000-message controls without profile or real-mail
  data. Every expected family, slot, span, relation, current revision, and
  fact is labeled and digest-stable.
  Validation: fixture, scope, source-span, long-source paging, and scale
  contracts pass in the standard-library test suite.
  Result: 17 synthetic documents, seven retrieval cases, 10-KiB/256-KiB/1-MiB
  controls, and 50/500/5,000-message controls are frozen in
  `context_ladder`; all paging and ledger contracts passed.
- [x] Evaluate raw, deterministic metadata, per-chunk context, whole-email
  context, detailed source-linked summaries, deterministic Drain templates,
  schema-validated offered-family confirmation, Markdown ledgers, relation
  graphs, and their bounded combination in staged isolation.
  Contract: generated text stays untrusted retrieval metadata; original
  canonical spans remain the sole answer evidence. Template confirmation can
  select only a host-offered same-scope family or null and can return only
  source-verifiable slot offsets.
  Validation: every individual arm, qualifying pair, and full package records
  retrieval/fact metrics, scope/span validity, unsupported output, and its
  promotion gate in JSON, Markdown, and HTML reports.
  Result: 23 deterministic source-indexed arms were measured; 22 passed the
  advance rule, exact-only retrieval failed at 0.667 localized fact recall,
  and the full package remained source/scope valid. A true cross-encoder is
  explicitly deferred to its separately configured evaluator.
- [x] Add resumable loopback-only live screening and blinded review artifacts.
  Contract: a live run is temperature-zero, cache/digest keyed, source bounded,
  serial, and stays within the configured 17-GiB Ollama allocation cap. Whole
  emails above 48,000 characters are structure-paged and never truncated into
  a direct model call. The review pack uses neutral IDs and stores its key
  separately.
  Validation: dry-run, malformed model output, cache resume, cancellation,
  invalid offsets, cross-scope offers, and report/review-pack tests pass.
  Result: the command writes JSON/JSONL/Markdown/HTML plus a neutral 20-case
  review pack and separate key. The one-repeat Qwen3 screen was attempted with
  eligible 6,387,799,162-byte Ollama residency, then failed closed after its
  third operation: it selected the offered family and correct values but gave
  invalid source offsets. The three-repeat and large-page live lanes remain
  blocked pending a separately evaluated offset-representation repair.
- [x] Record deterministic measurements and the explicit live-qualification
  status in all required project documents.
  Contract: no live or Thunderbird-promotion result is inferred from a
  deterministic stand-in; deferred model work remains visible.
  Validation: build, full tests, deterministic ladder report, benchmark, and
  documentation reconciliation complete.
  Result: build passed; 163/163 deterministic tests passed in 18.390 seconds;
  `context-ladder-evaluation` is retained; the post-change 1K benchmark is in
  `reports/context-ladder-postchange-1000.*`. No live or Thunderbird-promotion
  claim is made.

## Milestone 14: reproducible public evaluation archive

- [x] Turn `README.md` into the beginner-oriented primary evaluation article.
  Contract: one document explains the actual source-to-answer pipeline, test
  inputs, prompts, metrics, model and RAG comparisons, failures, decisions,
  limits, and exact reproduction commands without implying production
  readiness.
  Validation: every headline value is traceable to a retained report and all
  Markdown links resolve.
- [x] Add deterministic integrity metadata for retained evaluation artifacts.
  Contract: local model caches, resumable checkpoints, dry-run plans, and
  temporary files are excluded; synthetic fixtures and non-transient reports,
  including failed attempts and raw model output, remain reviewable.
  Validation: regenerating and verifying `RESULTS_MANIFEST.sha256` succeeds and
  no retained file exceeds GitHub's 100-MB per-file limit.
- [x] Validate and publish this directory as the public
  `d3v4shish/thunderbird-ai-pipeline-lab` Git repository.
  Contract: the default branch is `main`, no profile/mail/credential data is
  present, and the first push preserves the exact validated tree.
  Validation: clean build, full deterministic tests, benchmark, link check,
  secret/profile-data scan, clean Git status, and remote branch verification.
  Result: published `main` to
  `https://github.com/d3v4shish/thunderbird-ai-pipeline-lab` after the build,
  156-test suite, 1,000-document benchmark, 248-artifact digest verification,
  zero-broken-link check, staged-file audit, and per-file size gate passed.
- [x] Refresh and incrementally publish the existing ThunderbirdAI source
  export without editing the active Thunderbird source tree.
  Contract: export artifacts represent all current Gecko/comm changes while
  ordinary Git history records only the delta from the previous export; no
  force push is used.
  Validation: export verification, source-tree status count comparison, clean
  export repository, and remote branch verification.
  Result: the refreshed bundle passed integrity verification and the 46-test AI
  xpcshell manifest, then commit `47f7504` was fast-forwarded to the existing
  ThunderbirdAI `main` branch without modifying the Mercurial source tree.

## Milestone 13: template-aware RAG and extended-scale qualification

- [x] Add a frozen, source-addressable template evaluation corpus and a
  deterministic mirror of Thunderbird's mail segmentation, Drain-style
  template mining, typed-slot extraction, and bounded duplicate detection.
  Contract: training and evaluation use a chronological 60/40 split; mined
  artifacts are scope/source-digest keyed retrieval metadata and original mail
  spans remain the only answer evidence.
  Validation: parity, fixture-digest, source-offset, template drift, poisoning,
  over-merge, slot-quality, cross-scope, and invalidation tests pass.
  Result: 113 synthetic messages, 60/40 chronological family split, family F1
  1.000, slot precision/recall 1.000/1.000, zero over-merge, and exact source
  invalidation passed.
- [x] Compare raw, segmented, skeleton, Drain, deduplicated, and combined
  template-aware retrieval/ledger lanes one factor at a time.
  Contract: automatic templates may affect retrieval, diversification, bounded
  graph traversal, and source-validated ledgers only; they cannot change user
  intent, classification, security policy, or mailbox actions.
  Validation: isolated reports retain every parameter, assignment, expected
  family/slot, actual family/slot, source span, and quality/cost metric.
  Result: all six paired lanes retained 1.000 Recall@4. Deduplicated indexing
  used 4,798 versus 11,214 raw characters and is selected; template metadata
  remains normalized instead of repeated in every chunk.
- [x] Extend deterministic scale coverage to 1,000/2,500/5,000-message threads
  and 1/4/16-MiB messages, retaining the existing 500-message and 256-KiB
  controls.
  Contract: localized, latest-state, historical, multi-message, exhaustive,
  anomaly, and cross-scope cases remain complete, ordered, bounded, and
  reproducible without profile or endpoint state.
  Validation: complete source traversal, exact fact/slot ledgers, stable fixture
  digests, storage/CPU/memory measurements, and baseline comparisons pass.
  Result: exact ledgers and source validity passed through 5,000 messages;
  template-dense and unique-prose messages passed 256KiB/1MiB/4MiB/16MiB at
  all three page sizes. Fixed Top-8 remained explicitly incomplete.
- [x] Add resumable staged live qualification for the approved model set.
  Contract: qwen3-embedding:4b is the embedding model; approved chat models and
  the qwen3:8b control run serially, loopback-only, temperature-zero, and only
  while measured Ollama allocation is at most 17 GiB.
  Validation: one-repeat smoke, at most two three-repeat Pareto finalists, and
  one selected stress candidate retain exact prompts, raw outputs, validation,
  model digests, residency, and failure reasons.
  Result: the v1 prompt-only lane failed qualification. The v2 schema-bound
  lane advanced Granite 3.1 and Qwen3 through three 1,000-record repeats;
  Granite then recovered 15,000/15,000 values across three 5,000-record repeats
  with no retry or unsupported output under the measured cap.
- [x] Reconcile the measured decision and all required project documentation.
  Contract: promotion requires all existing hard gates, template-family F1 at
  least 0.95, slot precision 1.0/recall at least 0.98, no material retrieval or
  answer regression, three safe live repeats, and a deterministic cost gain.
  Validation: build, full tests, benchmark, staged reports, README, BUILD,
  ARCHITECTURE, BENCHMARKS, HOTSPOTS, and this TODO agree; unfinished or failed
  gates remain explicit.
  Result: template-aware mechanics advance to broader integration testing, not
  production. The separate thread-memory relation F1/full-live work, real-mail
  validation, Thunderbird port/parity, and operational/security testing remain
  open and visible below.

## Milestone 12: source-linked email and thread memory

- [x] Synchronize maintained result documentation with the final implementation
  and measured thread-memory evidence.
  Contract: documentation distinguishes deterministic mechanics from one-repeat
  live diagnostics, retains exact metrics, and does not imply promotion.
  Validation: stale suite counts are removed, result tables agree with retained
  reports, all required documents remain present, and the canonical tests pass.
- [x] Add versioned email-artifact, summary, ledger, relation, and rollup
  contracts with normalized SQLite storage and derived Markdown/graph views.
  Contract: each artifact is scope locked, source-digest keyed, and backed by
  exact source spans; per-email extraction can see only earlier thread state.
  Validation: deterministic contract, provenance, chronology, rendering, and
  append/edit/delete invalidation tests pass.
- [x] Add the complete focused contextual-memory matrix and hierarchical
  thread-to-email-to-passage retrieval.
  Contract: all 1,152 planned cells are explicit; generated context, summaries,
  and relations remain retrieval metadata while original email spans remain the
  only answer evidence.
  Validation: matrix cardinality/isolation, repeated-chunk versus parent-index,
  relation-policy, memory-mode, retrieval, and security tests pass.
- [ ] Add resumable live evaluation for Qwen3 8B and Phi-4 14B plus scale and
  oversized validation of safe Pareto candidates.
  Contract: endpoint work is loopback-only, serial, digest-keyed, and constrained
  by the measured 17-GiB Ollama VRAM cap; every prompt and raw output is retained.
  Validation: dry-run preflight, three-repeat focused runs, and winner validation
  over the 180-message, 50-500-message, 10-KB, and 256-KiB fixtures complete.
  Current status: the 1,152-cell/144-stream preflight, per-artifact/answer/repeat
  resume tests, one-repeat Qwen3 and Phi-4 smoke runs, and deterministic 180,
  50-500, 10-KB, and 256-KiB hardening pass are complete. The full three-repeat
  focused live matrix and live validation of its Pareto finalists remain open.
- [ ] Measure and document quality, safety, stability, storage, and performance.
  Contract: no Thunderbird promotion or performance claim is made without hard
  gates, paired baselines, and a non-dominated quality/cost result.
  Validation: build, full tests, benchmark, reports, and all required project
  documents agree with the measured outcome; unfinished live work remains open.
  Current status: implementation measurements and one-repeat smoke results are
  documented in `reports/thread-memory-evaluation-summary.md`; build and
  136/136 deterministic tests passed at that snapshot; the current complete
  suite is 156/156. Promotion remains blocked on the open
  three-repeat live work and 0.500 semantic-relation F1.

## Milestone 1: standalone pipeline lab

- [x] Create deterministic build, run, test, and benchmark entry points.
  Contract: commands are independent of the caller's working directory and do
  not access mutable profile or mail data.
  Validation: run all four scripts from outside the project directory.
- [x] Implement versioned document, case, variant, trace, and report contracts.
  Contract: malformed and unknown-version records fail before pipeline work.
  Validation: contract unit tests cover valid and invalid records.
- [x] Implement the generic ingestion, RAG, GraphRAG, tool, generation, and
  validation pipeline with a `tb-current` baseline.
  Contract: scope is locked end to end, source spans remain verifiable, and
  tool execution is bounded and read-only.
  Validation: deterministic unit and integration tests cover each stage.
- [x] Add a frozen synthetic corpus, including an exact 10,240-byte document.
  Contract: 32 required facts are distributed through the document and no
  fixture contains profile data or credentials.
  Validation: corpus digest and byte/fact-count tests pass.
- [x] Add Ollama capability discovery, approved model preparation, live tool
  calling, and the measured full-GPU/17-GiB eligibility gate.
  Contract: no unapproved model is pulled and ineligible runs are recorded.
  Validation: mock endpoint and VRAM-policy tests pass.
- [x] Add adaptive calibration, hard-gate pruning, three-repeat full runs,
  resumable checkpoints, and JSON/JSONL/Markdown/HTML reports.
  Contract: incompatible and rejected combinations are retained with reasons.
  Validation: offline matrix and report tests pass.
- [x] Record the measured deterministic baseline and known hotspots.
  Contract: no performance claim is made without before/after measurements.
  Validation: `scripts/benchmark.sh` updates reproducible artifacts.

## Deferred integration

- [x] Prepare and warm-probe the six approved model downloads.
  Contract: downloads are explicit and sequential; no existing model is
  deleted; runtime eligibility uses measured Ollama allocation.
  Validation: exact digest manifest and residency report are retained.
- [x] Complete the full live GPU matrix with atomic per-step checkpoints.
  Contract: only measured eligible configurations enter ranking; every step
  remains independently reviewable in the checkpoint and final reports.
  Validation: 48/48 calibration variants and all 24 planned survivor repeat
  slots were attempted; one runtime failure remains explicit in the combined
  result and the Pareto report is retained.
- [ ] Port a selected passing configuration back into Thunderbird.
  Contract: this is a separate reviewed change after all quality and safety
  gates pass.
  Validation: Thunderbird parity, xpcshell, browser, and benchmark coverage.

## Milestone 11: whole-email context extraction ablation

- [x] Add one bounded, query-independent whole-email context call per document.
  Contract: the chat model receives the complete synthetic email without a
  target chunk or user query; accepted output is grounded, length/schema
  checked, and used only as untrusted retrieval metadata.
  Validation: focused tests cover prompt contents, malformed or hallucinated
  output, cache reuse, and preservation of every canonical passage span.
- [x] Compare shared whole-email context with raw, deterministic-metadata, and
  per-chunk generated-context retrieval under identical chunking and Top-K.
  Contract: source passages, queries, embedding model, scope, and ranking stay
  fixed; the report retains exact prompts, raw outputs, retrieval evidence,
  quality, endpoint cost, storage, and latency.
  Validation: build and full deterministic tests pass, followed by one live
  Qwen3 context/embedding run under the measured 17-GiB VRAM cap.
- [x] Record the measured result and keep the production decision explicit.
  Contract: distinguish one-call-per-email cost from duplicated shared-context
  index cost and do not promote the lane when primary hybrid quality regresses.
  Validation: update README, BUILD, ARCHITECTURE, BENCHMARKS, and HOTSPOTS from
  the generated JSON/Markdown report.

## Milestone 9: oversized single-email evaluation

- [x] Add a frozen synthetic email that exceeds the selected model context.
  Contract: facts span the beginning, middle, end, and chunk boundaries; the
  fixture is exact-size, source-verifiable, injection-bearing, and contains no
  profile or real-mail data.
  Validation: digest, byte count, fact distribution, scope, and chunk coverage
  tests pass for the default 256-KiB email and a 1-MiB deterministic stress case.
- [x] Compare truncation, targeted top-K retrieval, exhaustive top-K, bounded
  page mapping, validated ledger reduction, and paged result delivery.
  Contract: every method records offered source spans, omissions, duplicates,
  prompt/output bounds, grounding, latency, and whether completeness can be
  proven without using synthetic labels at runtime.
  Validation: deterministic tests expose truncation/top-K loss and prove bounded
  page/ledger coverage; a live qwen3:8b run retains prompts and raw outputs.
- [x] Record the measured decision and keep production limits explicit.
  Contract: distinguish targeted questions from exhaustive extraction and from
  open-ended summarization; do not claim arbitrary-summary completeness.
  Validation: build, full tests, report reconciliation, and documentation updates
  complete without changing the existing standard benchmark claim.

## Milestone 10: oversized-email design matrix

- [x] Define and freeze the practical design taxonomy and objectives.
  Contract: separately score localized question answering, exhaustive
  known-schema extraction, and open-ended summary coverage across direct,
  sampling, retrieval, compression, paging, hierarchy, and agent-controlled
  alternatives; inapplicable designs remain explicit rather than receiving a
  synthetic score.
  Validation: deterministic tests assert lane identity, fixed inputs, source
  coverage, grounding, and objective-specific completeness semantics.
- [x] Implement a deterministic one-factor design matrix.
  Contract: compare prefix/suffix/head-tail/uniform sampling, capped and
  uncapped chunking, exact/lexical/dense/hybrid retrieval and K, deterministic
  schema extraction, page size/overlap, rolling accumulation, hierarchical
  reduction, and bounded result delivery without profile or endpoint state.
  Validation: every lane records source offered, fact recall, context/output
  bounds, source-span validity, duplication, latency, and expected failure mode.
- [x] Run live finalists and adversarial controls with `qwen3:8b`.
  Contract: direct, compressed, bounded-map, hierarchical/rolling, targeted QA,
  and page-order/adversarial lanes retain exact prompts, raw outputs, accepted
  and rejected facts, token counts, latency, model digest, and VRAM telemetry.
  Validation: three repeats for promoted candidates; cheaper one-repeat
  diagnostic lanes are labelled and never treated as stability evidence.
- [x] Publish one reconciled design report and update project documentation.
  Contract: recommend a design per objective, explain cost and failure modes,
  and preserve production gaps including real unlabeled summary evaluation,
  cancellation, concurrency, and crash recovery.
  Validation: clean build, full tests, report assertions, relative-link check,
  and accurate README/BUILD/ARCHITECTURE/BENCHMARKS/HOTSPOTS updates.

## Milestone 3: staged advanced-RAG evaluation

- [x] Add source-verifiable sentence-window/parent-child chunking.
  Contract: retrieval indexes the child sentence while generation receives its
  bounded parent passage; every returned character span maps to canonical text.
  Validation: deterministic boundary, fact-integrity, and duplicate-span tests.
- [x] Evaluate chunking independently from retrieval and generation.
  Contract: report source coverage, fact integrity, truncation, context size,
  and overlap/redundancy for each supported chunker.
  Validation: the frozen 10,240-byte document and all labeled facts are scored.
- [x] Evaluate retrieval, reranking, query expansion, and GraphRAG as separate
  ablation stages before running generation.
  Contract: each lane changes one named factor and reports document recall,
  fact recall, reciprocal rank, evidence redundancy, scope integrity, graph
  relation recall, provenance validity, and latency where applicable.
  Validation: deterministic tests assert lane isolation and known graph-depth
  and long-document behavior.
- [x] Add a deterministic CLI/report for the staged suite and run it.
  Contract: one command writes atomic JSON and Markdown artifacts containing
  per-case evidence and an explicit technique recommendation; no endpoint,
  mailbox, or mutable external data is required.
  Validation: build, full tests, staged evaluation, and benchmark all pass;
  measured results are recorded in project documentation.

## Deferred advanced-RAG lanes

- [x] Add realistic semantic/paraphrase/thread cases and rerun hybrid retrieval
  with the approved live embedding model before selecting a production
  retriever.
- [x] Diagnose endpoint-embedding variation across model reloads.
  Contract: identical model digest, input text, and batching must produce either
  reproducible vectors/rankings or an explicitly bounded quality tolerance.
  Validation: compare stored vector digests and retrieval metrics over three
  fresh model loads before selecting an endpoint embedding configuration.
- [x] Normalize sentence-window parent storage, then remeasure ingestion,
  database size, retrieval quality, and context redundancy.
- [x] Add an independently gated live lane for a true cross-encoder. Diverse
  query rewrites and HyDE are covered by Milestone 5.
- [ ] Add RAPTOR only with a larger long-document corpus; consider Self-RAG only
  if a compatible reflection-trained model fits the measured 17-GiB VRAM cap.

## Milestone 7: scale, stability, reranking, and parameter evaluation

- [x] Add frozen 50, 100, 250, and 500-message thread fixtures and compare
  fixed top-K, full thread ranges, paged ranges, and hierarchical reduction.
  Contract: retrieval stays tenant/thread scoped, source ordered, deduplicated,
  and bounded; answer synthesis exposes omissions rather than truncating them.
  Validation: deterministic scale tests plus measured recall, context bytes,
  latency, memory, and database growth for every thread size.
- [x] Diagnose endpoint embedding drift within one load and across three fresh
  loads using exact, near-tie, paraphrase, and multilingual probes.
  Contract: record vector digests, maximum/mean component deltas, cosine
  similarity, ranking overlap, rank correlation, and quality tolerance without
  treating stable aggregate recall as proof of vector determinism.
  Validation: an atomic live report identifies whether document, query,
  batching, reload, or ordering changes the result.
- [x] Normalize sentence-window parent storage and compare it with the existing
  duplicated schema.
  Contract: child retrieval records reference one canonical parent passage;
  returned evidence remains byte-for-byte source verifiable and behaviorally
  equivalent to the legacy representation.
  Validation: migration/schema tests and paired ingestion, database-size,
  retrieval-quality, and context-redundancy benchmarks pass.
- [x] Evaluate a genuine query-document cross-encoder behind the existing
  loopback-only reranker boundary.
  Contract: the reranker scores query/passage pairs jointly, cannot alter
  evidence, fails closed on malformed output, and is independently constrained
  by the 17-GiB measured allocation cap.
  Validation: compare no reranker, deterministic, embedding, and cross-encoder
  lanes over identical candidates in three repeats with quality and latency.
- [x] Sweep remaining high-impact parameters one factor at a time: chunk size
  and overlap, candidate depth, top-K, context record/character budget, model
  context window, output-token budget, and exhaustive reduction batch size.
  Contract: every lane records the changed factor, effective packed prompt,
  truncation/completeness state, quality, latency, token counts, and resource
  use; unsafe or over-cap settings are retained as rejected results.
  Validation: deterministic preflight and three-repeat live finalists produce
  an explicit keep/change/defer recommendation per parameter.
- [x] Run build, full tests, baseline/post benchmark, and write a review report.
  Contract: no performance or production claim is made without paired results;
  unavailable optional infrastructure remains visible as a blocked lane.
  Validation: required project documents and raw JSON/Markdown artifacts match
  the final implementation and measured runs.

## Milestone 8: evaluation article series

- [x] Add a ground-up, one-email RAG dry-run covering every stored
  representation and retrieval stage.
  Contract: show the complete synthetic email, actual fixed/structure-aware/
  sentence-window chunk output, SQLite tables, FTS5/BM25, exact and dense
  retrieval, RRF, every reranker, evidence packing, prompt, output, and
  validation without confusing generated search metadata with evidence.
  Validation: rerun the example through the implemented functions, reconcile
  all displayed scores/offsets, check local links, build, and run all tests.

- [x] Create a linked article index and terminology map.
  Contract: a newcomer can choose a concept, procedure, or result article
  without reading raw JSON first.
  Validation: every article and primary raw artifact is linked from the index.
- [x] Explain the baseline pipeline and every evaluated RAG family.
  Contract: distinguish retrieval, generated retrieval metadata, routing,
  GraphRAG, agentic control, reranking, and generation without claiming that
  deferred Self-RAG/RAPTOR lanes were executed.
  Validation: descriptions map to implemented stages and retained reports.
- [x] Document the frozen emails, prompts, expected outputs, and complete
  representative dry-runs.
  Contract: copied examples come from synthetic fixtures and actual reports;
  excerpts are clearly distinguished from complete raw artifacts.
  Validation: independently parse source reports and verify quoted values.
- [x] Document all models, embedding behavior, rerankers, and parameter lanes.
  Contract: capability, VRAM/RAM, stability, quality, and latency are separated;
  unavailable or failed runtimes remain visible.
  Validation: tables reconcile with model, drift, cross-encoder, and parameter
  JSON artifacts.
- [x] Write a results/failures article with expected-versus-actual evidence.
  Contract: include prompts, outputs, retrieval orders, omissions, safety gates,
  and benchmark regressions without turning synthetic results into a production
  claim.
  Validation: build, test, and report digests/counts remain accurately stated.
- [x] Link the series from README and validate the documentation set.
  Contract: required project documents stay concise and accurate.
  Validation: links resolve locally and no Milestone 8 work remains hidden.

## Milestone 5: query-time advanced-RAG experiments

- [x] Add a frozen semantic/paraphrase/compositional challenge set and bounded,
  cacheable query-transformation contracts for HyDE, multi-query RAG Fusion,
  decomposition, and step-back retrieval.
  Contract: generated text may influence retrieval only, every returned passage
  remains an unchanged source span, and malformed or over-broad transformations
  fail closed without changing tenant or collection scope.
  Validation: deterministic tests cover prompt isolation, strict output parsing,
  cache identity, rank fusion, source provenance, and challenge labels.
- [x] Evaluate direct endpoint hybrid retrieval and each generated-query method
  as paired one-factor lanes over identical chunks, embeddings, queries, and K.
  Contract: reports retain exact prompts, raw model output, accepted transforms,
  rankings, fact/document metrics, request cost, latency, and failures.
  Validation: run the complete synthetic suite with `qwen3:8b` and
  `qwen3-embedding:4b` under the measured 17-GiB allocation cap.
- [x] Add and separately score a loopback-only corrective retrieval lane and an
  adaptive method router.
  Contract: corrective grading treats passages as untrusted data and can only
  retain or broaden local retrieval; adaptive routing selects only measured
  methods and never permits a no-retrieval answer for corpus-backed questions.
  Validation: deterministic routing/security tests plus three cached-transform
  live repeats preserve scope and source-span integrity.
- [x] Record the paired quality, generation/index/query cost, stability, and
  promotion decision for every new lane.
  Contract: no method is promoted from a single synthetic win, and unsupported
  Self-RAG/RAPTOR claims remain clearly deferred.
  Validation: build, full deterministic tests, live report, and before/after
  standard benchmark complete with reviewable JSON/Markdown artifacts.

## Milestone 6: routed decomposition on email-like threads

- [x] Add a larger frozen synthetic email/thread corpus with realistic
  paraphrases, revisions, attachments, cross-message facts, distractors,
  prompt injection, negative questions, and exhaustive thread requests.
  Contract: fixtures contain no profile or real-mail data, use stable IDs and
  timestamps, and label every expected fact and route.
  Validation: deterministic tests assert corpus size/digest, route balance,
  exact source spans, scope isolation, and fixture contracts.
- [x] Compare direct endpoint hybrid retrieval with a deterministic selective
  router that uses decomposition only for multi-part questions and canonical
  thread-range retrieval for all/every requests.
  Contract: generated subqueries are corpus-blind and fail back to direct;
  range retrieval is scope locked and returns canonical messages in stable
  timestamp/ID order.
  Validation: paired retrieval metrics retain prompts, outputs, rankings,
  route decisions, query cost, and embedding digests over fresh model loads.
- [x] Generate and validate final grounded answers for both retrieval lanes.
  Contract: final JSON must use exact fact IDs/values and citations from the
  offered evidence; unsupported facts and out-of-evidence citations are
  rejected, and negative cases must abstain.
  Validation: score answer correctness, exact fact recall, citation precision,
  structured-output acceptance, abstention, and per-case failures.
- [x] Run three live repeats under the measured 17-GiB allocation cap and
  record the promotion decision, baseline/post benchmark, architecture, and
  hotspots.
  Contract: no production claim is made from synthetic results or one repeat.
  Validation: clean build, full deterministic tests, live JSON/Markdown report,
  and review summary all complete.

## Milestone 4: generated Contextual RAG experiment

- [x] Add a bounded, query-independent context-generation contract and cache.
  Contract: a loopback model receives only the frozen synthetic document and
  one source-verifiable chunk; output is length/schema checked, stored as
  untrusted retrieval metadata, and never used as answer evidence.
  Validation: deterministic tests cover prompt bounds, malformed output,
  source-span preservation, cache reuse, and hallucinated exact entities.
- [x] Compare metadata context with generated context one factor at a time.
  Contract: the same documents, chunks, queries, top-K, and ranking settings
  are used for paired lexical, embedding, and hybrid lanes; reports retain all
  generated contexts, raw model outputs, retrieved evidence, resource usage,
  and failures.
  Validation: run the frozen eight-case suite with an approved chat model and
  embedding model under the measured 17-GiB combined residency limit.
- [x] Record measured quality, indexing cost, retrieval latency, storage cost,
  grounding checks, and the promotion decision.
  Contract: no quality or performance claim is made without paired results,
  and failure/regression remains visible.
  Validation: build, full deterministic tests, live Contextual RAG command,
  and the standard benchmark complete with reviewable JSON/Markdown reports.

## Milestone 2: evaluation-lab hardening

- [x] Enforce composite tenant/collection/document identity in storage and
  graph records.
  Contract: duplicate document IDs in different scopes cannot overwrite or
  expose one another.
  Validation: cross-scope storage and retrieval regression tests pass.
- [x] Make tool policy and tool-derived evidence auditable end to end.
  Contract: an empty allowlist permits no tools; rejected calls are retained;
  fetched source spans are available to citation/fact validation.
  Validation: denied-tool and live fetch/validate tests pass.
- [x] Replace placeholder embedding reranking with measured-vector reranking.
  Contract: the candidate order is computed from stored and query vectors.
  Validation: controlled vectors deterministically reverse the source order.
- [x] Bound ingestion telemetry and remeasure its resource impact.
  Contract: ingestion records per-stage aggregates without retaining records
  proportional to corpus size.
  Validation: unit tests and comparable before/after profile results pass.
- [x] Complete strict contract/output validation and index reset behavior.
  Contract: malformed metadata/config/model output fails closed and clearing
  an index removes graph state as well as documents and retrieval records.
  Validation: focused malformed-input, citation-support, and clear tests pass.
- [x] Finish approved model preparation, warm residency probing, and a live
  matrix preflight.
  Contract: the 17-GiB limit applies to measured Ollama VRAM required by the
  tested configuration; whole-GPU usage is telemetry only.
  Validation: digest manifest, probe report, and exact dry-run plan are saved.
- [x] Reject over-cap chat/embedding pairs before adaptive calibration.
  Contract: the dry-run plan distinguishes all enumerated variants from the
  measured-VRAM-eligible subset and records every rejected variant and reason.
  Validation: matrix-selection regression tests cover exact-cap and over-cap
  pairs, and a fresh live plan contains no over-cap calibration variants.
- [x] Make evaluation fact-ID-aware and score answer correctness separately
  from graph-context availability.
  Contract: a correct value under the wrong fact key does not receive full
  contract credit, and graph edges alone cannot make a wrong answer look right.
  Validation: regression cases cover wrong keys and wrong answers with correct
  graph context before one reviewed live case is rerun.
  - [x] Add explicit expected answer values to applicable frozen cases.
  - [x] Require exact expected key/value pairs for fact recall.
  - [x] Add answer correctness to case, aggregate, repeat, and report metrics.
  - [x] Propagate empty failed repeats into combined hard and quality gates.
  - [x] Run build and the complete deterministic test suite.
  - [x] Rerun the 48-candidate live calibration from a fresh checkpoint.
  - [x] Run three full-corpus repeats for selected hard-gate survivors.
  - [x] Record final results and remaining limitations in project documents.
