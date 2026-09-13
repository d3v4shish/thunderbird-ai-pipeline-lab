# Template mining and extreme-scale mail: what changed and what passed

Most inboxes contain repeated machine-generated mail: invoices, shipment
updates, receipts, security alerts, support notices, and newsletters. Ordinary
chunking treats each repeated footer and signature as fresh content. A template
miner instead learns which words are stable and which positions vary.

For example, these subjects:

```text
Invoice INV-0007 review
Invoice INV-0008 review
Invoice INV-0009 review
```

become a family resembling:

```text
invoice <*> review
```

The wildcard is not an answer and the template is not evidence. It is only a
compact search/routing hint. `INV-0009` remains a typed slot linked to the exact
character range in the original message. If the message changes, its
source-digest-keyed assignment is invalidated.

## The tested flow

1. Split canonical mail into body, signature, and quoted regions without
   changing source offsets.
2. Train sender-scoped Drain clusters only on earlier messages.
3. Match later messages against mature families.
4. Extract bounded identifier/date/amount/email/URL slots and verify every
   value against its source range.
5. Remove learned boilerplate only from the retrieval representation.
6. Store source, family, assignment, and slots in normalized SQLite tables.
7. Use Top-K for localized questions. Use ordered source pages and a host-owned
   ledger when the user explicitly asks for every item.
8. If an LLM renders that ledger, constrain allowed output IDs and validate
   every value against source before accepting it.

The original source is never replaced by a template, summary, graph edge, or
model response.

## What the paired ablation showed

On 44 held-out synthetic messages, raw, segmented, skeleton, Drain,
deduplicated, and combined representations all retained 1.000 document and
family Recall@4. Boilerplate-deduplicated text indexed 4,798 characters instead
of raw's 11,214 and improved document MRR from 0.955 to 0.977. Concatenating all
template metadata reached 0.989 MRR but grew beyond raw to 11,461 characters.

The practical choice is therefore not “put the template everywhere.” Index the
smaller deduplicated source representation, and keep family/slot records once
in normalized tables for routing and diversification.

## What happened at large scale

The deterministic template-aware test passed at 500, 1,000, 2,500, and 5,000
messages. At 5,000 messages it achieved 1.000 family F1 and exact-ledger recall,
mined families in 620.1ms, reduced retrieval text by 66.4%, and used a
23,678,976-byte SQLite database. Direct Top-8 exhaustive recall was only
0.0016, which is expected: eight retrieved records cannot enumerate 5,000
records.

For single emails, both repetitive template mail and unique prose passed
complete deterministic traversal at 256KiB, 1MiB, 4MiB, and 16MiB. A 16MiB
source needed 565 pages at 30K characters or about 850 pages at 20K. This is why
increasing an LLM context window is not the general solution. Keep each call
bounded and keep accumulated state outside the model.

## Why structured output mattered

The first live prompt asked models to return `{"facts": {...}}` while an
untrusted field told them to add a private key. Phi-4, Qwen 2.5, and Qwen 3
copied that key. Granite 3.1 later changed output shape on most 64-record pages;
Granite 4.1 timed out repeatedly. Prompt wording alone was not a sufficient
boundary.

The corrected route gave Ollama a JSON schema that requires exactly the offered
IDs and prohibits additional keys. Crucially, the schema did not contain the
expected values. Models still had to copy values from input, and host code still
rejected any value not found in source. Five of six models then passed smoke;
DeepSeek continued to corrupt zero padding and failed.

Granite 3.1 MoE and Qwen 3 both passed three 1,000-record repeats. Granite was
about twice as fast and advanced to 5,000 records, where it returned all 15,000
expected values across three runs, 237 total pages, with no retry or unsupported
output. Its largest prompt used only 1,745 tokens, so increasing context would
not help this design.

## What this does and does not prove

It proves the mechanics on frozen synthetic input: source preservation,
template/slot quality, scope isolation, bounded storage and graph expansion,
complete page traversal, strict model-output validation, and three-repeat
ledger rendering for the selected model.

It does not prove that arbitrary summaries contain every important thought, or
that template frequencies and language patterns match real inboxes. It also
does not close older thread-memory relation-quality, Thunderbird integration,
concurrency, cancellation, restart, and full security-review gaps. The result
is a strong broader-integration candidate, not a production certificate.

The complete tables and exact artifact list are in the
[template-aware evaluation summary](../reports/template-aware-evaluation-summary.md).
Raw JSON remains the source of truth.
