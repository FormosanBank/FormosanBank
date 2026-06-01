# B9.4 — Text validation plan (rev. 2026-05-31)

**Date:** 2026-05-31
**Roadmap section:** B9.4
**Status:** Plan; not yet started.
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

This is a discussion artifact, not a code commit. **Output:** an updated section of this plan listing every candidate rule with proposed severity, awaiting user OK before W4+ implements them.

**This step partly fulfills roadmap C025** ("decide what validators we need") for the text-content category.

Seed list (drawn from the [OldQCPlan flowchart](../../temp/OldQCPlan.png), validate_punct.py current checks, [corpus-cleanup-tasks.md](2026-05-31-corpus-cleanup-tasks.md), the roadmap C-items below, and common sense). User adds / removes / rebalances as desired:

**From OldQCPlan "verify punctuation, character set":**
- TR8 SOFT: smart quotes in standard-tier FORM (left/right single, left/right double). Standard convention is ASCII apostrophe.
- TR9 SOFT: HTML entities in FORM/TRANSL (`&amp;`, `&apos;`, `&lt;`, `&gt;`, including double-encoded `&amp;amp;`). Captures YeddaPalemeqBlog-style scrape residue.
- TR10 HARD: control characters (codepoint < 0x20) other than `\t \n \r`.

**Structural FORM rules:**
- TR11 HARD: asterisk (`*`) in standard-tier FORM. Asterisk is linguistics convention for "ungrammatical example"; should never appear in published surface form.
- TR12 SOFT: `-` (segmentation marker) in S-level standard-tier FORM. Parallel to TR7 (`=`) — leftover morpheme boundary.
- TR13 SOFT: `<` or `>` (infix delimiter) in S-level FORM at either tier. Surface form shouldn't carry segmentation markup.
- TR14 SOFT: trailing punctuation mismatch between original and standard tiers (e.g., original ends with `.` but standard doesn't, or vice versa).
- TR15 SOFT: leading or trailing whitespace in any FORM.

**Character-set / encoding rules:**
- TR16 SOFT: zero-width characters (U+200B, U+200C, U+200D, U+FEFF) in FORM/TRANSL. Common copy-paste / scrape artifact, invisible to humans, breaks downstream tokenization.
- TR17 SOFT: byte-order mark (U+FEFF) at start of any FORM or TRANSL.
- TR18 SOFT: mixed-script confusables (Cyrillic 'а' vs Latin 'a', etc.) — heuristic: any character whose Unicode block doesn't match the dominant script of the FORM.

**Footnote / scrape residue:**
- TR19 SOFT: trailing-decimal footnote (`word.1`, `word.2`) at end of S-level FORM.
- TR20 SOFT: superscript-digit footnote (`word¹`, `word²`, `¹` as standalone token) anywhere in FORM.
- TR21 SOFT: bracketed-digit footnote (`word[1]`, `[1]` as standalone token) anywhere in FORM.

**Language-content rules (advanced):**
- TR22 WARN: out-of-language examples (e.g. Japanese/Fongbe/Tagalog tokens in an Amis or Bunun file). **Closes roadmap C016**. Roadmap explicitly notes "hard problem; likely WARN-level if attempted" — needs a language-ID model (langid / fasttext-lid / whatever the project standardizes on). Possibly deferred to a B9.4-followup round rather than landed in this plan; flag as scoped-out unless cheap to add.

**Open questions for W3 (user to resolve before W4 begins):**
- What exact character is "the null symbol"? Assumption: `∅` U+2205 EMPTY SET. Confirm or specify alternative.
- Do TR12 / TR13 supersede the earlier "segmentation-removed invariant" idea in the original draft? Or do we want both (one detects markers in S-FORM directly; the other verifies the W/M tier reconstructs to S-FORM)?
- Severity of TR8 (smart quotes in standard tier) — SOFT now, but candidate for HARD eventually if standardization conventions are firm.
- Footnote heuristics (TR19–TR21) — should they require additional context (e.g., the digit is unattached / standalone) to reduce false positives on legitimate numerals?
- TR22 — implement in this plan or defer? Depends on whether the user wants a language-ID dep added now.

### W4–W10. Implement the rules (one per W, TDD)

Order of implementation is by rule independence + simplicity:
- **W4: TR1** (no null symbol in S-standard FORM). Simplest character search.
- **W5: TR2 + TR3** (parens/slashes at W/M HARD; parens/slashes elsewhere SOFT). Two related rules, share helper.
- **W6: TR4** (null propagation: W/M standard ⇒ sister original).
- **W7: TR5** (null propagation: M ⇒ W + S-original).
- **W8: TR6** (null propagation: W ⇒ some M child + S-original).
- **W9: TR7** (`=` in S-standard).
- **W10: TR8 onward** — the brainstorm-derived rules, batched by category (smart-quote/HTML-entity batch; structural batch; encoding batch; footnote batch). Each batch one commit.

For each W4–W10: write failing test, verify fail, implement rule in `rules/text.py`, add to RULES list, verify pass, commit. Per the no-compound-bash memory, `.venv/bin/pytest` directly (no `source && pytest`).

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
