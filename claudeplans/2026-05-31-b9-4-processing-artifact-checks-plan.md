# B9.4 — Text validation plan (rev. 2026-05-31)

**Date:** 2026-05-31
**Roadmap section:** B9.4
**Status:** [PARTIAL 2026-06-01] — W1, W2, W4–W9, W11 landed on `feature/claude-tooling-phase-0` (B9.4 subagent ran in main tree rather than its worktree branch; bundled into user's `5355d81cc added a number of tests and validators…` commit). W3 brainstorm signed off by user 2026-06-01 (decisions recorded inline in the W3 section below). W10 [NOT STARTED] — implements the now-finalized brainstorm-derived rules.

Per-W status:
- **W1** [DONE] — `QC/validation/rules/text.py` (new) + `QC/validation/validate_text.py` (new). V110 smart_quotes, V111 imbalanced_parens, V112 repeated_punct, V113 consecutive_dashes, V114 multiple_whitespace, V115 mismatched_quotes (all SOFT). `QC/validation/validate_punct.py` deleted.
- **W2** [DONE] — V116 non_ascii_in_form SOFT; aggregated per (file, character_group); CJK excluded. `QC/cleaning/non_ascii_counts.py` deleted.
- **W3** [DONE — brainstorm signed off 2026-06-01] — decisions inline below.
- **W4** [DONE] — TR1 / V120 HARD (∅ in S-standard FORM). V120 collision resolved 2026-06-01 by bumping B9.2's `flag_audio_suspicious` to V140.
- **W5** [DONE] — TR2 / V121 HARD (parens/`/` in W- or M-level FORM) + TR3 / V122 SOFT (parens/`/` in FORM/TRANSL).
- **W6** [DONE] — TR4 / V123 HARD (null in W/M standard FORM ⇒ sister original).
- **W7** [DONE] — TR5 / V124 HARD (null in M FORM ⇒ parent W FORM null AND S-original null).
- **W8** [DONE] — TR6 / V125 HARD (null in W FORM ⇒ some child M FORM null AND S-original null).
- **W9** [DONE] — TR7 / V126 SOFT (`=` in S-standard FORM).
- **W10** [NOT STARTED] — see W3 sign-off below for the finalized rule list and severities.
- **W11** [DONE] — `.github/workflows/xml-validation.yaml` extended (PR-changed and baseline jobs now also invoke `validate_text.py`; `text-soft.csv` artifact added). `QC/README.md`, `README.md`, `CLAUDE.md` updated. **Caveat (resolved 2026-06-01 in `06290ab1e`):** `.claude/skills/run-qc-pipeline.md` and `summary.template.md` updated by hand to point at `validate_text.py` (the subagent couldn't edit `.claude/` paths under the hook).

Test counts at landing: 28 pass on `tests/validators/test_validate_text.py`; 255 total in the full suite.

Followup landed 2026-06-01 in commit `06290ab1e`: `_s_id` loop variable in V110/V111/V112 renamed to `_` (rules aggregate file-level; per-S id not consumed).
**Supersedes:** earlier B9.4 draft on the same path. Major reframing per user 2026-05-31: `non_ascii_counts.py` + `validate_punct.py` consolidate into a new `validate_text.py` (under `QC/validation/`), following the staged-pipeline architecture established in B9.3. Adds seven specific FORM-content rules plus a work item to brainstorm additional checks, with cross-references to roadmap items C016, C023, C024, C025.

---

## Goal

Provide one always-on validator that checks the *textual content* of FORM and TRANSL elements — punctuation conventions, character set, leftover segmentation markers, null-morpheme propagation between tiers. Replaces the two existing single-purpose scripts with one unified validator that uses the shared Finding framework.

## Staged-pipeline placement

Per B9.3 architecture:

```
Stage 1: validate_xml.py    →  rules/xml.py (structural; must pass first)
Stage 2: validate_audio.py  →  rules/audio.py
Stage 2: validate_glosses.py → rules/gloss.py
Stage 2: validate_text.py   →  rules/text.py   ← this plan
Stage 2: …other artifact validators
```

Order between stage-2 validators is not strictly enforced; each can run independently against well-formed XML.

## Decisions locked in (2026-05-31)

| Question | Decision |
|---|---|
| Consolidation target | New `QC/validation/validate_text.py` |
| Rule module | New `QC/validation/rules/text.py` |
| Fate of `validate_punct.py` | Refactor logic into `rules/text.py`, then delete the standalone script |
| Fate of `non_ascii_counts.py` | Same — port logic into `rules/text.py`, delete the standalone |
| User-specified rules (7 below) | All in scope for this plan |
| Brainstorm step | Yes — W3 enumerates candidates and gets user sign-off before W4+ implements |
| TDD discipline | Yes — tests first per rule |

## User-specified rules (locked, severities as given)

| # | Severity | Rule |
|---|----------|------|
| TR1 | HARD | No null symbol in S-level standard-tier FORM |
| TR2 | HARD | No parentheses or forward slashes in W-level or M-level FORM |
| TR3 | SOFT | Parentheses or forward slashes in any FORM or TRANSL — may indicate meta-linguistic marking of alternative utterances. **Closes roadmap C023** (`/` = alternative forms) and **C024** (parens in free translations: too idiosyncratic to auto-normalize, flag only for manual review). |
| TR4 | HARD | Null symbol in W- or M-level FORM at standard tier ⇒ also in the corresponding sister original-tier FORM |
| TR5 | HARD | Null symbol in M-level FORM ⇒ also in parent W-level FORM AND in original tier of parent S-level FORM |
| TR6 | HARD | Null symbol in W-level FORM ⇒ also in some child M-level FORM AND in original tier of parent S-level FORM |
| TR7 | SOFT | `=` appears in S-level standard-tier FORM (probably leftover clitic marking) |

(I use TR-prefixed labels here for clarity; final V0xx codes assigned in W1.)

## Current state

### What already works
- [QC/validation/validate_punct.py](../../QC/validation/validate_punct.py) — checks **standard-tier S-level FORM** only for:
  - Smart quote counts (left/right single, left/right double)
  - Paired vs. orphan smart quotes
  - Extra/multiple consecutive whitespace
  - Imbalanced parentheses
  - Repeated punctuation (`??`, `!!`)
  - Mismatched smart-quote pairs
  - Consecutive dashes (`--`)
  - Non-ASCII character count (excluding Chinese CJK ranges)
- Output: stdout summary report + optional verbose log. No CSV, no Finding objects, no per-element output.
- [QC/cleaning/non_ascii_counts.py](../../QC/cleaning/non_ascii_counts.py) — walks XML, counts non-ASCII characters in **all** FORM elements (across tiers), excludes Chinese CJK ranges, prints tally sorted by frequency. No CSV, no Finding objects.

### What's missing
- Tests for either script.
- Finding-framework integration.
- Per-tier / per-level rule scoping (validate_punct.py is S-standard-only by hardcode; non_ascii_counts.py is all-FORMs by hardcode).
- Coverage of the seven user-specified rules.
- Coverage of structural FORM rules (asterisk, null propagation, segmentation leftover, HTML entities, control chars, etc. — full list in W3).

## Work items (TDD discipline)

Each item is a separable commit. Pattern per W*: write failing test → verify fail → implement → verify pass → commit.

### W1. Architecture: create `validate_text.py` + `rules/text.py`, port `validate_punct.py` checks

- **Files:**
  - Create: `QC/validation/rules/text.py`
  - Create: `QC/validation/validate_text.py`
  - Create: `tests/validators/test_validate_text.py`
  - Delete (after W2 lands): `QC/validation/validate_punct.py`
- **Test cases (W1.1):** one test per validate_punct.py check, mirroring its current detection but emitting `Finding` objects with rule IDs (proposed: V110 smart_quotes, V111 imbalanced_parens, V112 repeated_punct, V113 consecutive_dashes, V114 multiple_whitespace, V115 mismatched_quotes). Severities default to SOFT unless the existing script treats them as fatal (it doesn't — it's a tally).
- **Implementation notes:**
  - `validate_text.py` mirrors the orchestrator shape of `validate_glosses.py` (post-refactor): walks `<corpus>/XML/`, runs `rules/text.py` RULES list, collects Findings, exits HARD-fail / SOFT-warn / WARN-info.
  - Preserve existing stdout tally style as a side-output for users who want the aggregate view, but the canonical output is the Finding stream + a `text_issues.csv` artifact per corpus.
  - Standard tier vs. original tier vs. any tier — each rule knows which tier(s) it applies to.

### W2. Port `non_ascii_counts.py` logic

- **Files:**
  - Modify: `QC/validation/rules/text.py` (add V116 non_ascii_in_form)
  - Extend: `tests/validators/test_validate_text.py`
  - Delete: `QC/cleaning/non_ascii_counts.py`
- **Test cases (W2.1):** non-ASCII in FORM → emits one Finding per (file, character_group); Chinese characters (CJK ranges) excluded from findings; clean ASCII corpus → no findings.
- **Implementation notes:**
  - Default severity SOFT (preserves the original "tally for review" semantics; HARD-failing CI on every existing non-ASCII char would be too aggressive given current corpus state).
  - Aggregate output preserved as `non_ascii_tally.csv` artifact.
  - Tier scope: all FORM tiers (matches current behavior).
  - **Before deleting `non_ascii_counts.py`:** run `rg "non_ascii_counts" --type py --type sh --type md` to find any callers; update them to invoke `validate_text.py` instead.

### W3. Brainstorm: enumerate additional candidate rules and get user sign-off

**Status: SIGNED OFF 2026-06-01.** The user reviewed the seed list and locked the final rule set + severities below. Quoted user direction is from the 2026-06-01 conversation.

**This step partly fulfills roadmap C025** ("decide what validators we need") for the text-content category.

**Sign-off resolutions:**

1. **Null character: confirmed `∅` U+2205 EMPTY SET.** Used wherever a rule references "the null symbol" (TR1 / V120 and the W4–W8 propagation rules).
2. **TR12 / TR13 supersede the earlier "segmentation-removed invariant" idea.** The roadmap's B9.4 §Gaps bullet for "Segmentation-removed-from-S-FORM-standard invariant" is dropped — TR12 (`-`) and TR13 (`<`/`>`) cover this directly at the rule level.
3. **TR8 promoted to HARD, scope = both original AND standard tiers.** User: *"We should have ascii straight apostrophe and double quote only: `'` and `"`. And that should be HARD."* The only acceptable apostrophe and double-quote are ASCII U+0027 and U+0022; all smart-quote variants (U+2018/U+2019/U+201C/U+201D and friends) HARD-fail in both FORM tiers.
4. **TR10–TR21 approved as written, with the explicit caveat that "we can tighten later if it turns up too many false positives."**
5. **TR22 dropped.** User: *"Let's actually drop C016 entirely (and thus TR22)."* Out-of-language detection too costly for the value at this stage. Removed from the rule set and from the roadmap's B6-SUPERSEDED table.
6. **TR15 / TR16 promoted to HARD; TR17 folded into TR16.** User asked whether TR15–17 should be HARD with the deletions in `clean_xml.py`; resolution:
   - TR15 (leading/trailing whitespace in FORM) → HARD. `clean_xml.py` already strips via `normalize_whitespace`, so HARD just guarantees the cleaner ran.
   - TR16 (zero-width chars U+200B/U+200C/U+200D/U+FEFF anywhere in FORM/TRANSL) → HARD. ZWJ/ZWNJ have legitimate uses in Arabic/Indic but not in Formosan/English/Chinese; safe to require absent. Cleaner-side strip lands as a follow-up to B5.
   - TR17 (BOM at start of FORM/TRANSL) → **deleted as a separate rule** — subsumed by TR16's broader scope. If a more-pointed message for "BOM at position 0" is wanted later, it can be a separate finding within the same rule function.

**Finalized rule list (W10 scope, ready for implementation):**

**From OldQCPlan "verify punctuation, character set":**
- **TR8 HARD** [updated] — smart quotes (any of U+2018/U+2019/U+201C/U+201D + Chinese full-width variants) in **either** FORM tier (original AND standard). Standard convention is ASCII straight `'` U+0027 and `"` U+0022 only.
- TR9 SOFT — HTML entities in FORM/TRANSL (`&amp;`, `&apos;`, `&lt;`, `&gt;`, including double-encoded `&amp;amp;`). Captures YeddaPalemeqBlog-style scrape residue.
- TR10 HARD — control characters (codepoint < 0x20) other than `\t \n \r`.

**Structural FORM rules:**
- TR11 HARD — asterisk (`*`) in standard-tier FORM. Should never appear in published surface form.
- TR12 SOFT — `-` (segmentation marker) in S-level standard-tier FORM. Supersedes earlier "Segmentation-removed-from-S-FORM-standard invariant" idea.
- TR13 SOFT — `<` or `>` (infix delimiter) in S-level FORM at either tier.
- TR14 SOFT — trailing punctuation mismatch between original and standard tiers.
- **TR15 HARD** [updated] — leading or trailing whitespace in any FORM. Cleaner already handles via `normalize_whitespace`; validator HARD just guarantees the cleaner ran.

**Character-set / encoding rules:**
- **TR16 HARD** [updated, expanded] — zero-width / BOM characters (U+200B ZWSP, U+200C ZWNJ, U+200D ZWJ, U+FEFF BOM) **anywhere** in FORM/TRANSL. Subsumes the deleted TR17. Cleaner-side stripping queued for B5 follow-up.
- ~~TR17~~ **DELETED** — merged into TR16.
- TR18 SOFT — mixed-script confusables (Cyrillic 'а' vs Latin 'a', etc.) — heuristic: any character whose Unicode block doesn't match the dominant script of the FORM.

**Footnote / scrape residue (scope: FORM AND TRANSL — per Bril Amis Basecamp card Apr 3, 2026):**

Footnotes leak into both tiers. Real-world example from Bril Amis: `<M id="s13w4m2"><FORM>uwal</FORM><TRANSL>speak12</TRANSL></M>` — the `12` is a footnote leak in TRANSL, not FORM. Each rule below applies to FORM and TRANSL text.

- TR19 SOFT — trailing-decimal footnote (`word.1`, `word.2`) at end of S-level FORM or TRANSL.
- TR20 SOFT — superscript-digit footnote (`word¹`, `word²`, `¹` as standalone token) anywhere in FORM or TRANSL.
- TR21 SOFT — bracketed-digit footnote (`word[1]`, `[1]` as standalone token) anywhere in FORM or TRANSL.

Watch for false positives where genuine numerals belong in the text (years, page references in TRANSL, dates). Implementation should require the digit to be glued to a non-digit token (no whitespace between) to reduce noise; document the false-positive risk in each rule's docstring.

**Language-content rules:**
- ~~TR22~~ **DROPPED** per user direction 2026-06-01. Out-of-language detection out of scope for B9; closes roadmap C016 by deletion (not by validator).

**Cleaner-side follow-up (queued for B5):** TR15 (whitespace) is already handled by `clean_xml.py`'s `normalize_whitespace`. TR16 (zero-width / BOM) is a new mechanical strip that should land in `clean_text` / `clean_trans`. Add as a small follow-up task to the B5 plan so the HARD validator findings stay near zero in practice.

### W4–W10. Implement the rules (one per W, TDD)

**W4–W9 status: [DONE]** — see the per-W table in the Status header at the top of this document. V120–V126 landed in `feature/claude-tooling-phase-0`. The original implementation order is preserved below for reference:
- **W4: TR1 / V120** (no null symbol in S-standard FORM).
- **W5: TR2 / V121 + TR3 / V122** (parens/slashes at W/M HARD; parens/slashes elsewhere SOFT).
- **W6: TR4 / V123** (null propagation: W/M standard ⇒ sister original).
- **W7: TR5 / V124** (null propagation: M ⇒ W + S-original).
- **W8: TR6 / V125** (null propagation: W ⇒ some M child + S-original).
- **W9: TR7 / V126** (`=` in S-standard).

**W10 status: [NOT STARTED]** — implements the W3-signed-off brainstorm rules. **Suggested order, with HARD rules first** so the highest-value gates land before the SOFT noise:
1. **TR8 HARD** — smart quotes in either FORM tier. Cross-tier scope; requires per-tier iteration helpers.
2. **TR10 HARD** — control characters.
3. **TR11 HARD** — `*` in standard-tier FORM.
4. **TR15 HARD** — leading/trailing whitespace in any FORM. (Validator only; cleaner already strips.)
5. **TR16 HARD** — zero-width / BOM chars in FORM/TRANSL. (Cleaner-side strip lands as a B5 follow-up.)
6. **TR9 SOFT** — HTML entities.
7. **TR12 SOFT** — `-` in S-standard FORM.
8. **TR13 SOFT** — `<`/`>` in S-level FORM either tier.
9. **TR14 SOFT** — trailing-punctuation mismatch.
10. **TR18 SOFT** — mixed-script confusables.
11. **TR19/TR20/TR21 SOFT** — footnote-residue heuristics (FORM + TRANSL scope).

V-code assignment for W10: V127–V139 allocated to TR8/TR10/TR11/TR15/TR16/TR9/TR12/TR13/TR14/TR18/TR19/TR20/TR21 in that order. V140 is taken by B9.2's `flag_audio_suspicious` (bumped from V120 on 2026-06-01); V120 stays with B9.4's TR1.

For each rule: write failing test, verify fail, implement in `rules/text.py`, add to RULES list, verify pass, commit. Per the no-compound-bash memory, `.venv/bin/pytest` directly (no `source && pytest`).

### W11. CI integration + documentation

- **Files:**
  - Modify or add: `.github/workflows/xml-validation.yaml` (extend) or new `text-validation.yaml`. Decide based on PR-job runtime budget; text checks are cheap so extending xml-validation.yaml is reasonable.
  - Modify: [QC/README.md](../../QC/README.md)
- HARD findings fail the job; SOFT findings warn.
- Document `validate_text.py` in the staged pipeline (between `validate_xml.py` and `validate_orthography.py`).
- Note the consolidation: `validate_punct.py` and `non_ascii_counts.py` no longer exist; their checks moved to `validate_text.py`.

## Related roadmap items

These items in [`.claude/plans/2026-05-27-roadmap.md`](2026-05-27-roadmap.md) are addressed (in whole or part) by this plan, or belong elsewhere:

| C-item | Status in B9.4 |
|---|---|
| **C016** Out-of-language examples | Captured as TR22 WARN in W3 brainstorm. May be deferred per the open question above. |
| **C021** Multi-word glosses joined with `.` | **Belongs to B9.3** (gloss validation), not B9.4. Should be added to that plan's brainstorm. |
| **C023** `/` indicates alternative forms | Closed by TR3 SOFT. |
| **C024** Parentheses in free translations (flag-only, no auto-normalize) | Closed by TR3 SOFT. The "no auto-normalize" constraint is honored — TR3 only emits findings, doesn't modify text. |
| **C025** Decide what validators we need | Partly closed by W3 for the text-content category. The same brainstorm pattern should run for B9.3 (gloss), B9.5 (duplicates), and any future category. |
| **C026** `find_duplicate_sentences.py` cleaner | **Belongs to B9.5** (duplicate detection), not B9.4. Already captured in the B9.5 plan. |

## Out of scope for B9.4

- *Fixing* the artifacts. Detection only. Removal/repair belongs in per-corpus pipelines (see [corpus-cleanup-tasks.md](2026-05-31-corpus-cleanup-tasks.md)).
- HTML entity decoding (already addressed in B7 via `html.unescape` in `orthography_extract.py`). TR9 *detects* HTML entities; it does not decode them.
- Grammar-level / perplexity checks (the "automatic grammar check" box in OldQCPlan). Different problem, different toolchain.
- Translation BLEU / ASR transcription comparison (separate boxes in OldQCPlan; the ASR side maps to B9.2).
- Renaming `rules/hard.py` → `rules/xml.py` (deferred future cleanup, noted in B9.3 plan).

## Acceptance criteria

- `pytest tests/validators/test_validate_text.py` passes with ≥3 substantive cases per implemented rule.
- `validate_text.py` runs against a known-clean corpus and produces zero Findings and an empty `text_issues.csv` (header only).
- `validate_text.py` against `Corpora/YeddaPalemeqBlog` surfaces the known artifacts catalogued in [corpus-cleanup-tasks.md](2026-05-31-corpus-cleanup-tasks.md) (specifically: double-encoded HTML entities should trigger TR9 findings).
- `validate_punct.py` and `non_ascii_counts.py` are deleted; all callers migrated to `validate_text.py`.
- CI invokes `validate_text.py` on PRs and pushes; HARD findings fail, SOFT findings warn.
- QC/README.md documents `validate_text.py` in the canonical staged pipeline.
- W3 brainstorm has explicit user sign-off recorded in this doc (or its commit message) before W4+ proceeds.
- C021 has been moved into the B9.3 plan's brainstorm. (Tracking note, not a code change in B9.4.)
