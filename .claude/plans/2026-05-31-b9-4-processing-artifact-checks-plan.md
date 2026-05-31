# B9.4 — Processing-artifact validation plan

**Date:** 2026-05-31
**Roadmap section:** B9.4 (Processing-artifact category of the six-category validator audit)
**Status:** Plan; not yet started.

---

## Goal

Catch the residue of ingestion bugs — leftover footnote markers, stray punctuation, non-ASCII contamination, asterisks, segmentation hyphens that escaped a cleanup pass. These artifacts are usually invisible to the source-text reader but corrupt downstream NLP and cross-corpus comparisons.

Per the user (2026-05-30): this category is *validation after cleaning*. It runs after `clean_xml.py` and its siblings have done their work; anything it catches is a sign cleaning didn't go far enough or a new artifact type has appeared.

## Current state

**Exists:**
- [QC/validation/validate_punct.py](../../QC/validation/validate_punct.py) — punctuation validator. Hard-checks for specific punctuation invariants between `kindOf="original"` and `kindOf="standard"` tiers (exact rules TBD by reading the file).
- [QC/cleaning/non_ascii_counts.py](../../QC/cleaning/non_ascii_counts.py) — script that tallies non-ASCII characters per corpus. **Currently lives in `cleaning/` but per user direction belongs in the validation pipeline as a post-clean check.**

**Missing:**
- No test file `tests/validators/test_validate_punct.py`.
- `non_ascii_counts.py` is not wired into the validation pipeline (it's a cleaning-step artifact at present).
- No footnote-number detector. Footnotes in the source data often survive as `word.1`, `word.2`, `word¹`, `word²`, etc. — patterns easy to enumerate but not currently checked.
- No asterisk validator. Asterisks in linguistic data signal "ungrammatical example"; if they appear in `kindOf="standard"` and not `kindOf="original"`, that's likely a processing artifact.
- No "segmentation-removed" invariant check. After stripping segmentation markers (`-`, `=`, `<`, `>`) from a segmented tier, the result should equal the unsegmented tier modulo whitespace. Drift means the segmentation tier and the surface form disagree.

## Open questions to resolve before coding

1. **Where does `non_ascii_counts.py` belong on disk?** Options:
   - (a) Move it to `QC/validation/validate_non_ascii.py`. Cleanest from a "this is a validator" standpoint.
   - (b) Leave it in `QC/cleaning/` and have the pipeline simply call it. Pragmatic; preserves existing imports/scripts.
   Recommend (a) **if** no external scripts import from `QC/cleaning/non_ascii_counts`. Check with `rg "non_ascii_counts" --type py` first.

2. **Footnote-number detector: which patterns?** Reasonable starting set, sourced from real data:
   - Trailing decimal: `word.1`, `word.2`
   - Trailing superscript: `word¹`, `word²`, `word³`
   - Bracketed: `word[1]`, `word[2]`
   - Standalone superscript tokens: `¹`, `²`, etc. as their own tokens
   Confirm with a sample of YeddaPalemeqBlog (which is known to be scraped from web sources with footnotes) before fixing the heuristic. Plan to error toward over-flagging; reviewers can dismiss.

3. **Asterisk validator: is `*` ever legitimate in Formosan-language text?** Likely no in `kindOf="standard"`, but check before treating it as a hard finding. In `kindOf="original"` an asterisk may signal source-text annotation that's meant to be preserved.

4. **Segmentation-removed invariant: which characters constitute segmentation?** Standard set: `-` (suffix boundary), `=` (clitic boundary), `<`, `>` (infix delimiters). Confirm by spot-checking one segmented corpus's W-tier vs. S-tier.

## Concrete work items

### W1. Tests for `validate_punct.py`

- **File to create:** `tests/validators/test_validate_punct.py`
- Read the file first to know what it enforces; tests should mirror the existing invariants. Cover at minimum:
  - Clean corpus → zero findings.
  - Original tier has punctuation that's missing in standard tier → expected finding.
  - Both tiers consistent → zero findings.
- Pattern: same `tmp_path`-based corpus building as `test_validate_xml.py`.

### W2. Integrate non_ascii_counts into validation pipeline

- Resolve open question 1 (move vs. leave).
- If moving: create `QC/validation/validate_non_ascii.py`, port logic, delete `QC/cleaning/non_ascii_counts.py`, update any callers, add `tests/validators/test_validate_non_ascii.py`.
- Add to [QC/README.md](../../QC/README.md) pipeline order (after cleaning, before orthography extraction).
- Add to CI workflow.

### W3. Footnote detector

- **File to create:** `QC/validation/validate_footnotes.py` (or add as a rule to `rules/`-style infrastructure if validate_xml.py's rule registry is the natural home).
- Detect the patterns enumerated in open question 2. Default to SOFT severity for first deployment; promote to HARD per-pattern as false-positive rates settle.
- Test file: `tests/validators/test_validate_footnotes.py` with one test per pattern + a clean case.

### W4. Asterisk validator

- Per open question 3's resolution: either a HARD rule in `rules/` (if `*` is never legitimate in standard tier) or a SOFT check.
- Likely a one-rule addition rather than its own file. Mirror an existing V0xx code's structure.
- Add a test case in `tests/validators/test_validate_xml.py` (or wherever the rule lands).

### W5. Segmentation-removed invariant

- **File to create:** `QC/validation/validate_segmentation_invariant.py` OR add as a SOFT rule.
- Logic: for each `<S>`, concatenate the FORM text of its children (`<W>` and where present `<M>`), strip segmentation markers (`-=<>`), normalize whitespace, compare against `<FORM kindOf="standard">` text. Mismatch → SOFT finding.
- Only meaningful on segmented corpora — gracefully no-op on unsegmented ones.
- Test file: `tests/validators/test_validate_segmentation_invariant.py`.

## Out of scope for B9.4

- *Fixing* the artifacts. This phase only detects. Removal/repair belongs in per-corpus pipelines (i.e., the items captured in [`.claude/plans/2026-05-31-corpus-cleanup-tasks.md`](2026-05-31-corpus-cleanup-tasks.md)).
- HTML entity decoding. Already addressed in B7 ([QC/orthography/orthography_extract.py](../../QC/orthography/orthography_extract.py) calls `html.unescape`); the underlying XML still carries double-encoded entities by design until the per-corpus pipelines re-run.

## Acceptance criteria

- `pytest tests/validators/test_validate_punct.py` passes with ≥3 substantive cases.
- `non_ascii_counts` is reachable from the canonical pipeline (CI + QC/README.md ordering) under whatever filename W2 produces.
- Footnote, asterisk, and segmentation-invariant validators each have a test file and at least one finding-producing test case.
- Running the full validation suite against `Corpora/YeddaPalemeqBlog` surfaces (a) footnote-like patterns if any exist and (b) the known artifacts already catalogued in the cleanup-tasks doc. No silent false negatives.
