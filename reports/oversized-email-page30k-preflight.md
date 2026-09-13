# Oversized Single-Email Evaluation

This synthetic experiment tests one email whose input is larger than the selected model context.

## Deterministic controls

- Email: 262144 bytes, 64 facts.
- Estimated input: 65536 tokens at four characters/token.

| Method | Fact recall | Notes |
|---|---:|---|
| prefix-only | 0.094 | 24576 source characters offered |
| head-tail | 0.094 | 24576 source characters offered |
| exhaustive top-8 | 0.016 | fixed K cannot enumerate every record |
| bounded source map + ledger | 1.000 | 9 pages; 2 result pages |

Targeted top-8 retrieval passed beginning, middle, and end probes: True.

## Chunking coverage

| Chunker | Source coverage | Facts | Last source offset |
|---|---:|---:|---:|
| fixed | 0.076 | 5 | 20000 |
| structure-aware | 1.000 | 64 | 262144 |

## Output-too-large stress

The 1048576-byte, 512-fact control retained 1.000 recall and required 10 bounded result pages.

## Decision

Use top-K retrieval for localized questions. Use structure-aware bounded page maps plus a validated source ledger for exhaustive extraction. If the ledger itself exceeds the output budget, return or stream result pages rather than asking one model response to contain everything.
