# Scope: updating the pipeline (and data) to match the new policies

Written after the quote-classifier merge into `proposal/qc-improvements`
(947 tests green). Policy-by-policy survey of what is DONE in tooling,
what tooling still needs building, and what is data work belonging to the
regeneration sweep. The sweep plan at the bottom is the actionable core.

## Where each policy stands

| Policy | Tooling | Data |
| --- | --- | --- |
| POL-010/018 quotes/apostrophes | DONE for detection+correction (classifier, c030–c032, Amis dictionary) | Correction runs at sweep; **only Amis has an attestation dictionary** |
| POL-011 dashes | DONE (swap_punctuation) | Applies at sweep |
| POL-012 nulls | DONE (clean_xml, V069/V120 family) | Applies at sweep |
| POL-013 tilde + PHON variants | DONE (C029; `[x\|y]` profiles, V146/V147/V154) | PHON regen at sweep (V147 counts what's left) |
| POL-014 infixes | DONE (G004 dual-spelling) | none |
| POL-016 exclude `*`/`?` examples | DONE (V129/V142 as detectors) | Worklist: 4 published `? ` sentences; Lin dev repo 17+3 |
| POL-017 starred parens | DONE (NTU parser fixed) | **NTU XML regen still pending** (deferred to sweep) |
| POL-022 duplicates by corpus type | **GAP — see item 1** | after tooling |
| POL-023 M-tier | DONE (V144/V145) | Worklist: Li-Thao 140, NTU 477, Wakelin 428, Song 7 |
| POL-024–027 TRANSL/options/alternatives | mostly intake conventions; V121/V122/G011/G012 already flag the symptoms | per-corpus at audit time |
| POL-030 manual edits | DONE (hook, CI check, --prune) | **Capture backlog before sweep** |
| POL-033 warnings sidecars | DONE | none |
| POL-034 registries | Validator DONE; **not wired into CI — item 2** | Seediq/Truku modeling review |
| POL-035 pre-correction baselines | DONE (policy + durable quote_corrections.csv) | Snapshot step per non-regenerable corpus at sweep |

## Tooling gaps to close before the sweep

1. **`validate_duplicate_sentences` corpus-type scoping (POL-022).**
   Needs a *source of truth for corpus type* (narrative vs reference).
   Recommendation: a `corpus_types.csv` registry at repo root (corpus →
   `narrative | reference`), consumed by the validator (duplicates in
   reference corpora stay actionable; in narratives they stop being
   findings; provenance-distinct attestations exempt via the existing
   source-attribute check) and echoed by `find_duplicate_sentences`
   messaging. Registry gets a V15x consistency rule (every corpus in
   `Corpora/` has a row). ~Half-day including tests. *Maintainer input:
   the initial classification of the 26 corpora.*
2. **Wire `validate_registries.py` into CI** — a small non-blocking job
   (or a step in the conversion-tables workflow, same
   `Orthographies/**`+registries path filter). ~Minutes.
3. **Attestation dictionaries beyond Amis (POL-010/018).**
   `build_attestation_dict.py` exists; generating per-language
   dictionaries is mechanical, but *enabling correction for a language is
   a judgment call* (dictionary quality gates correction quality — the
   Amis one was hand-reviewed via `quote_review_nonwiki_amis.md`).
   Recommendation: sweep runs with Amis only; other languages get
   dictionaries + review as separate follow-ups.
4. **POL-016 intake enforcement** is prose-only (skills/briefing).
   Optional hardening: dev-repo build scripts get audited for exclusion
   at `audit-gloss-scrape` time (already in the skill). No pipeline code
   needed — exclusion is an intake decision, not an automatic deletion.

## The regeneration sweep (per corpus, in order)

Prereqs all in place: idempotence tests, prune-safe apply, durable
correction log, V147/V154 progress tracking.

0. **Classify**: regenerable (working reproduction pipeline in
   `CodeAndDocs/`) vs non-regenerable — one pass over the 26 READMEs,
   recorded in the sweep tracking doc.
1. **POL-035 snapshot** (non-regenerable only): copy pristine `XML/` into
   `CodeAndDocs/` (naming: `pre_correction_snapshot/` + README note).
2. **POL-030 capture**: `capture_manual_edits.py` against the appropriate
   baseline for corpora with known uncaptured hand edits.
3. **Run**: `apply_manual_edits → clean_xml → standardize →
   add_phonology`. Expected diff classes per corpus: null glyphs `ø/Ø→∅`,
   dash look-alikes, curly apostrophes, tildes (U+223C→`~`), decoded
   entity residue (C028), Amis quote corrections (c031/c032 rows in
   `quote_corrections.csv` — commit it), PHON regenerated (variants to
   `[x|y]`, V147→0), NTU starred-parens regen (POL-017).
4. **Review + commit**: diff per corpus; token-comparison CI will flag
   count shifts (expected — announce the discontinuity as in 2026-06);
   README updates dropping the old double-clean_xml pipeline description
   ride along per corpus.
5. **Verify**: re-run the baseline sweeps (V142/V144/V147/port gate);
   V147 and the null-family vacuities should go to zero.

Sequencing note: three corpora were already regenerated on the feature
branch with the new pipeline (HundredPaiwanStories, Presidential_Apologies,
NTU partially) — the sweep should diff-check rather than blindly rerun
those.

## Explicitly out of sweep scope

- Linguistic review worklists (V144 segmentation, V070 impostors,
  phoneme-level conversion-table reviews, Latham/Wikipedias port-gate
  HARDs) — tracked in `2026-08-10-new-rule-baselines.md`.
- Conversion-table validator case-awareness (inherited deferral).
- POLICIES.md DRAFT-banner removal (maintainer read-through).
