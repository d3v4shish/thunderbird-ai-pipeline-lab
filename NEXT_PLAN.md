# Next Evaluation Plan

This file records the next experiment. It is deliberately not implemented in
Thunderbird or in the current lab snapshot.

## Goal

Test whether template families can improve complete email retrieval without
allowing a language model to decide scope, evidence, or completeness.

## Proposed pipeline

1. Mine sender-scoped template families deterministically and store normalized
   family, assignment, and typed-slot rows.
2. For a selected email, retrieve only candidate template families permitted by
   the fixed tenant, account, folder, and user-selected time range.
3. Give the model the selected email, bounded template skeletons, and an exact
   schema. Ask it only to confirm a candidate family and extract candidate slot
   values with source offsets.
4. Reject family IDs not offered by the host, invalid JSON, unsupported values,
   offsets that do not map to source text, and any cross-scope reference.
5. Let host code enumerate every canonical email assigned to the accepted
   family. The model never supplies that list and therefore cannot silently omit
   family members.
6. Route localized questions to bounded hybrid retrieval. Route an explicit
   user-selected Complete mode to paged family enumeration plus a deterministic
   completion ledger.
7. Use the original email spans as answer evidence. Template skeletons,
   generated summaries, and model-confirmed family labels remain search or
   routing metadata only.

## Required experiments

- Compare no-template, mined-template, and model-confirmed-template routing on
  near-duplicate, drifting, multilingual, forwarded, adversarial, and unique
  synthetic emails.
- Measure family precision/recall/F1, slot precision/recall, email-level
  retrieval recall/MRR, exhaustive family coverage, unsupported-value rate,
  cross-scope leakage, indexed characters, latency, calls, tokens, RAM, and
  Ollama model VRAM.
- Test 50, 500, and 5,000-message families, append/edit/delete invalidation,
  cancellation, crash-safe resume, model failure, malformed output, and a
  poisoned email that asks the model to select another family or scope.
- Compare deterministic selection with Granite 3.1 MoE, Qwen3 8B, and the best
  eligible alternate family from the retained model matrix for three fresh-load
  repeats.
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
