# Audit: Formosan-Kavalan-Zhang-Reference-Grammar (Chang 2000, Kavalan)

**Published:** 2026-11-09 as `Corpora/Kavalan-Chang-Reference-Grammar` (PR #338, merged; dev repo main `e2f9897`).
**Audit pages:** https://claude.ai/artifact/N5kVcxz8Fsphu9fbMSGauK (round 1, the code: 6 cards, all answered;
round 2, the data: 8 cards, 4 answered, nothing to change). Before the audit, the student review and orthography were
settled on https://claude.ai/artifact/ExkS9dS7oum5cjzGoxxSYY (rounds 1-10). Decision log: rounds 87-95.

## What the build does

`build_xml.py` turns Hunter's page-by-page transcription of the scan (`source_units.tsv`, 755 records; 14 examples
it missed added later) into the original tier, with the student's corrections (59 fields in 50 examples) applied as
the maintainer ruled. Then `clean_xml` (no change on this corpus), `standardize` with
`Kavalan_TaiwanNandao_113.tsv` (r -> l, l -> d), and `add_phonology --orthography TaiwanNandao`. The 20 steps, with
counts and the ruling behind each, are on the round-1 page.

## Findings by concern

- **(a) Letters.** Every letter of the 461 Kavalan lines is in the TaiwanNandao profile; no curly quotes; the three
  `o`s of 苗栗 are a README caveat. The 2026-08-10 gloss audit's two spelling departures (`nianiana`, `nizi-ita`) are
  fixed.
- **(b) Punctuation.** Final marks are added by the build (POL-063; 449 of 450 lines had none); brackets (6 examples)
  and optional parentheses (2) are deleted as ruled; 51 inner commas are kept; morphemes carry no punctuation (ruled).
- **(c) Conventions.** Infixes in angle brackets in the word tier and, after audit round 1, the sentence line too
  (79 lines, 82 infixes; V134 SOFT x164, expected). Validators: 0 HARD; SOFT V144 6, V134 164, V142 3, V061 10,
  V065 3, V153 13, each with a recorded reason (`CodeAndDocs/qc_summary.md`).
- **(d) Extraction.** No `*` anywhere; the starred `*iku` alternative excluded; the coverage record lists 11 starred
  examples on 8 pages as left out. The record missed 14 printed examples (found and added); the maintainer chose to
  port on the current record rather than recount every page.

## Build and rights (step 4b)

Remediated before the port, as ruled: decision tables moved out of the code into six `decisions_*.tsv` files
(POL-039; lint 54 -> none); `generate_xml.sh` (canonical order, clean_xml added) and `validate.sh` (checks moved out
of the build) replace `regenerate.sh`, `reproduce.sh` and `run_qc_pipeline.sh`; a source-accounting test added.
Licence `CC BY-NC 4.0`, Rights source Henry Chang, 2024-01-07. Rebuilds from a FormosanBank checkout alone (no
private file), byte-identical, idempotent.

## Left open

- The Kavalan attestation dictionary (5 words committed; 24 when rebuilt from today's corpora): refresh in its own
  shared PR, or leave. No effect on this corpus.
- The standard tier detects as Folk (0.76) rather than Ortho113 (0.72), as other Kavalan corpora do: accepted.
