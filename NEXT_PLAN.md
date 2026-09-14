# Next Evaluation Plan

This file records the implemented lab experiment and the gates that remain.
It is deliberately not implemented in Thunderbird.

## Current status

The deterministic experiment is implemented in `related_email_rag`. On the
frozen 18-message/eight-case corpus, bounded and Complete one-hop
thread-plus-template union reached related precision/recall 1.000/1.000 with
valid source spans, valid scope, and zero unrelated messages. Complete mode
retained ledger coverage 1.000 at 50, 500, and 5,000-message accounting scales;
bounded top-32 coverage necessarily fell to 0.640, 0.064, and 0.0064.

The anchor failure has now been isolated and repaired with host-owned candidate
IDs. An eight-case Qwen candidate screen initially failed prompt injection at
0.875 selection accuracy; sentence-local host filtering then passed 8/8 with
all quality metrics 1.000. Integrated candidate selection passed the formerly
fatal repeated-value email in both combined and modular forms.

The previous complete live prerequisite did not pass. Least-privilege modular
inputs fixed template metadata being emitted as email events, but the latest
full run stopped after 8/32 valid operations when Qwen copied a hostile source
instruction into generated context.

The candidate-only structured-memory successor therefore removed generated
context and summaries. V1 exposed duplicate slot selection; V2 completed 8/8
but exposed two event omissions, one template-family false positive, and a
double semantic predicate. V3 passed its eight-email one-repeat Qwen screen.

The v4 qualification is now complete through its first failed model gate.
Unchanged v3 passed 1/6 adversarial message cases and 0/4 old-reference scale
cases. V4 separates 512 durable events from 24 model hints, excludes quote and
signature segments plus paraphrased instructions, preserves explicit old reply
targets inside a 24-record prompt, narrows relation candidates, and permits a
high-confidence assigned family with no optional slot occurrence. It passed
all six message cases and 50/100/250/500-message controls deterministically.
Qwen3, Granite 3.1 MoE, and Qwen 2.5 then passed 21/21 operations over three
fresh repeats. DeepSeek passed five operations and failed closed on the sixth
after emitting duplicate event IDs. Phi-4 and Granite 4.1 were not run because
the staged plan stops at the first failure.

## Goal

Test whether template families can improve complete email retrieval without
allowing a language model to decide scope, evidence, or completeness.

## Proposed pipeline

1. Mine sender-scoped template families deterministically and store normalized
   family, assignment, and typed-slot rows.
2. For a selected email, retrieve only candidate template families permitted by
   the fixed tenant, account, folder, and user-selected time range.
3. Host code extracts bounded typed occurrences and creates opaque IDs bound to
   scope, document, source digest, name, value, and span. Sentence-local
   instruction-like candidates remain audited but are excluded from the model
   schema.
4. Mine bounded current-email event spans in host code and persist every safe
   occurrence. Models may mark event IDs as ranking hints, but cannot remove
   events from durable memory. Keep deterministic header relations separate.
5. Give the candidate-only operation prior validated thread records plus
   bounded event, relation, template, and slot IDs. Reject invented, duplicate,
   stale/cross-scope IDs, unsafe candidate contexts, non-prior relation targets,
   and multiple predicates for one assertion/target. Keep an assigned family
   without a slot only when deterministic assignment confidence is at least
   0.8; same-sender unassigned lookalikes remain filtered.
6. Let host code enumerate every canonical email assigned to the accepted
   family. The model never supplies that list and therefore cannot silently omit
   family members.
7. Route localized questions to bounded hybrid retrieval. Route an explicit
   user-selected Complete mode to paged family enumeration plus a deterministic
   completion ledger.
8. Use the original email spans as answer evidence. Template skeletons,
   generated summaries, and model-confirmed family labels remain search or
   routing metadata only.

## Completed in v4

- Freeze and retain the failed v3 adversarial baseline before host changes.
- Test unlabeled boundaries, optional-slot families, forwarded/quoted bodies,
  noisy signatures, paraphrased prompt injection, a sentence-31 event, and an
  explicit old reply target at 50/100/250/500 messages.
- Sweep 24/48/96/512 durable-event caps and 64/128/256 relation caps. The dense
  no-reference diagnostic produced 64/96/96 relation candidates, so the
  selected 64 cap is bounded but not an exhaustive relation claim.
- Exercise malformed output, hidden/duplicate/stale IDs, scope, chronology,
  cancellation inherited from the v3 gate, and checkpoint resume.
- Run three fresh repeats with Qwen3, Granite 3.1 MoE, Qwen 2.5, and DeepSeek
  until DeepSeek's strict duplicate-ID failure stops the model ladder.

## Remaining experiments

- Decide whether to leave DeepSeek incompatible, reduce the event-hint schema,
  or add a separately versioned exact-duplicate normalization experiment. Do
  not silently deduplicate output in the qualified contract.
- Only after that gate passes, run Phi-4 and Granite 4.1 under the same three
  fresh-repeat and residency checks.
- Test HTML-to-text artifacts, legitimate body lines beginning with `From:`,
  broader languages, empty/MIME-damaged bodies, append/edit/delete invalidation,
  and realistic sender/template cardinality.
- Re-run retrieval Recall/MRR and Complete expansion on a larger unlabeled v4
  memory corpus; the current qualification isolates memory construction and
  schema compliance, not end-to-end answer improvement.
- Add a human-reviewed, unlabeled-summary evaluation before claiming that
  family retrieval improves open-ended summaries.

## Promotion gates

- Family F1 at least 0.95 and slot precision 1.0/recall at least 0.98.
- Exact complete-mode family enumeration in every repeat with zero scope leaks,
  unsupported facts, invalid citations, or unvalidated source spans.
- No regression for direct localized questions or negative abstention.
- A non-dominated quality/cost result under the 17-GiB Ollama model-allocation
  cap.
- Thunderbird parity, UI, cancellation, concurrency, profile deletion, and
  security tests in a separate reviewed implementation phase.

Failure of any gate keeps the feature experimental. A model may help classify
or extract metadata; it never becomes the authority for which emails exist or
whether every email was processed.
