# B9.3 — Gloss validation plan (rev. 2026-05-31)

**Date:** 2026-05-31
**Roadmap section:** B9.3
**Status:** Plan; not yet started.
**Supersedes:** earlier draft on the same path. Architecture revised after user feedback (2026-05-31): the rule registry framework is shared across validators, but the orchestrators stay split by concern (XML format first; artifact validators after). V062 moves out of `rules/hard.py`; `validate_glosses.py` is refactored to consume the shared framework rather than being deleted.

---

## Goal

Bring gloss validation into the rule-registry framework while preserving the staged-pipeline architecture: XML format is checked first (and must pass) before artifact validators run. Gloss checks are inherently SOFT — spelling rules and normalization can legitimately produce W/M-count mismatches that don't indicate corruption.

## Staged-pipeline architecture (user direction, 2026-05-31)

The validator suite is *not* a single orchestrator. It's a staged pipeline of separate executables, all sharing the same `Finding`/`Severity` framework:

| Stage | Validator | Rule module | What it checks |
|---|---|---|---|
| 1 | `validate_xml.py` | `rules/hard.py` (could later be renamed `rules/xml.py`) | XML format: schema, IDs, attributes, structure. **Must pass before later stages run meaningfully.** |
| 2 | `validate_audio.py` (B9.2) | `rules/audio.py` (new in B9.2) | Audio artifacts |
| 2 | `validate_glosses.py` (this plan) | `rules/gloss.py` (new) | Gloss artifacts |
| 2 | `validate_punct.py` (B9.4) | `rules/punct.py` (eventual) | Punctuation/processing artifacts |

Each stage-2 validator can be run independently. They share the framework (Finding objects, severity semantics, CorpusIndex) but not the orchestration.

## Decisions locked in (2026-05-31)

| Question | Decision |
|---|---|
| V062 placement | Move from `rules/hard.py` to new `rules/gloss.py` |
| Validators-per-rule-module | One rule module per artifact concern; one validator per module |
| `validate_glosses.py` fate | Refactor to consume `rules/gloss.py` via shared framework; keep as separate executable |
| V060 (new, W-count vs word-count) | SOFT |
| V061 (new, M-count vs implied-morpheme-count) | SOFT |
| V062 severity | Stays HARD (per-corpus downgrade tracked in corpus-cleanup-tasks.md) |
| CSV artifacts | Preserve `validation_results.csv` and `validation_m_mismatches.csv` as artifacts alongside Findings |
| Unsegmented-corpus handling | No special check needed; rules naturally no-op when iterating empty W/M lists |

## Current state

### What exists
- [QC/validation/validate_glosses.py](../../QC/validation/validate_glosses.py) — 289 lines. Two checks:
  - **W-count vs. word-count** ([validate_xml_file()](../../QC/validation/validate_glosses.py#L137-L191)): counts whitespace-split words in `<FORM kindOf="original">` vs. direct `<W>` children. Optional `--check_morpho` flag adds "W with no M children" as a column. Writes `validation_results.csv`.
  - **M-count vs. implied-morpheme-count** ([validate_morpheme_counts_file()](../../QC/validation/validate_glosses.py#L96-L134)): per W, counts morphemes implied by FORM (`<infix>` groups + `-`/`=` segments) vs. actual `<M>` children. Monomorphemic-with-zero-M is acceptable. Writes `validation_m_mismatches.csv`.
- Architecture issues to fix: uses `xml.etree.ElementTree` (not lxml), no `Finding` integration, no rule_ids, no severity model, no CorpusIndex awareness.
- [V062 in rules/hard.py:722-768](../../QC/validation/rules/hard.py#L722-L768) — already in the modern framework. Currently lives under "Category 5: W/M segmentation" in hard.py but conceptually belongs in `rules/gloss.py`.

### What's missing
- No `tests/validators/test_validate_glosses.py`.
- No `rules/gloss.py` rule module.
- No V060 or V061 implementations.
- V062 lives in the wrong rule module.
- CI workflow does not invoke `validate_glosses.py`.

## Open questions

1. **CI severity policy for SOFT.** `validate_xml.py` already runs in `.github/workflows/xml-validation.yaml`. When `validate_glosses.py` joins, SOFT findings (V060/V061) should emit warnings without failing the job; HARD findings (V062) fail. Confirm during W5 implementation.

2. **`rules/hard.py` rename (deferred).** "hard.py" is a historical name — the file already contains rules of mixed severities (e.g., V010 is SOFT inside hard.py). A rename to `rules/xml.py` or `rules/structural.py` would align with the new per-domain rule modules. Out of scope for B9.3; capture as a future cleanup task.

## Work items (TDD discipline)

Each item is a separable commit. Pattern per W*: write failing test → run to verify fail → implement → run to verify pass → commit.

### W1. Move V062 from `rules/hard.py` to new `rules/gloss.py`

- **Files:**
  - Create: `QC/validation/rules/gloss.py`
  - Modify: `QC/validation/rules/hard.py` (remove V062 + its RULES list entry + the `_re` import if V062 is its only user)
  - Modify: existing test file that covers V062 — update import path; tests should otherwise stay green
  - Modify: `QC/validation/validate_xml.py` if it imports V062 directly (not via the RULES list)
- **Test cases (W1.1):**
  - V062's existing test cases still pass after the move
  - `validate_xml.py` no longer emits V062 findings (since V062 left its RULES list)
- **Implementation notes:**
  - Create `rules/gloss.py` with the same module-level scaffolding as `rules/hard.py` (imports of `Finding`, `Severity`, `etree`, `Path`, `CorpusIndex`)
  - Add a `RULES = [v062_infix_M_needs_angle_gloss]` list at the bottom
  - Move `_INFIX_PATTERN` constant alongside the function

### W2. Add V060 (W-count vs. word-count) to `rules/gloss.py` — SOFT

- **Files:**
  - Modify: `QC/validation/rules/gloss.py` (add `v060_W_count_matches_word_count`)
  - Create: `tests/validators/test_validate_glosses.py` (start of the new test file)
- **Test cases (W2.1):**
  - Clean S (3 words in FORM, 3 W children) → no finding
  - Mismatch (3 words in FORM, 2 W children) → SOFT V060 finding citing S id, word_count, w_count
  - S with `<FORM kindOf="original">` and `<FORM kindOf="standard">` → uses original (matches validate_glosses.py's preference)
  - S with no FORM at all → no finding (V013/V011 will catch that elsewhere)
  - Nested W (descendant rather than direct child) → warning logged but doesn't double-count (preserves current behavior at validate_glosses.py:166-169)
- **Implementation notes:**
  - Port `count_words` + `extract_s_direct_text` from validate_glosses.py — same logic, lxml instead of xml.etree
  - Severity SOFT (per user direction); message should make clear this is informational ("expected and actual W counts differ; may be due to normalization/spelling")
  - Add `v060_W_count_matches_word_count` to RULES list

### W3. Add V061 (M-count vs. implied-morpheme-count) to `rules/gloss.py` — SOFT

- **Files:**
  - Modify: `QC/validation/rules/gloss.py` (add `v061_M_count_matches_form_segmentation`)
  - Extend: `tests/validators/test_validate_glosses.py`
- **Test cases (W3.1):**
  - W with FORM `'ka'` and 0 M → no finding (monomorphemic-with-no-M exception)
  - W with FORM `'ika-doa'` and 2 M → no finding (matches expected)
  - W with FORM `'k<um>ita'` and 2 M (infix + root) → no finding
  - W with FORM `'k<um>ita'` and 1 M → SOFT V061 with expected=2, actual=1
  - W with FORM `'ma=luhay'` and 2 M (clitic boundary) → no finding
  - W with no FORM → no finding (V011/V012 catch FORM-missing)
- **Implementation notes:**
  - Port `count_morphemes_from_form` and `get_w_form` from validate_glosses.py unchanged (same logic; just call sites change tree type)
  - Severity SOFT
  - Preserve the monomorphemic-with-no-M acceptable case (validate_glosses.py:128)
  - Add `v061_M_count_matches_form_segmentation` to RULES list

### W4. Refactor `validate_glosses.py` to consume `rules/gloss.py`

- **Files:**
  - Modify: `QC/validation/validate_glosses.py`
  - Extend: `tests/validators/test_validate_glosses.py`
- **Test cases (W4.1):**
  - `validate_glosses.py` against a clean fixture produces zero Finding objects and empty CSVs (header only)
  - Same fixture with W-count mismatch produces one SOFT V060 Finding **and** one row in `validation_results.csv`
  - Same fixture with M-count mismatch produces one SOFT V061 Finding **and** one row in `validation_m_mismatches.csv`
  - HARD V062 finding causes nonzero exit; SOFT findings warn but don't fail (mirrors `validate_xml.py` exit semantics)
  - `--check_morpho` flag still works (legacy column in `validation_results.csv`)
  - `--output_dir` flag still works
- **Implementation notes:**
  - Replace the xml.etree.ElementTree code with lxml; use the same orchestration shape as `validate_xml.py` (walk files, run RULES from `rules/gloss.py`, collect Findings)
  - Continue writing the two legacy CSVs so any external workflows that consume them keep working — CSV rows derive from the corresponding Finding objects
  - CLI surface preserved: `xml_folder`, `--check_morpho`, `--debug`, `--output_dir`
  - Drop the standalone `count_words`, `extract_s_direct_text`, `count_morphemes_from_form`, `get_w_form` helpers from validate_glosses.py (they now live in `rules/gloss.py`)

### W5. CI integration + documentation

- **Files:**
  - Modify: `.github/workflows/xml-validation.yaml` (or new `gloss-validation.yaml` — decide per CI maintenance preference)
  - Modify: [QC/README.md](../../QC/README.md)
- **Steps:**
  - Add a CI job that runs `validate_glosses.py` against changed `.xml` files (PR track) and the baseline (push track)
  - HARD V062 fails the job; SOFT V060/V061 emit warnings without failing
  - Update QC/README.md to:
    - Document the staged pipeline (XML format → artifact validators)
    - Note that gloss checks are SOFT (review-not-gate)
    - Reference `rules/gloss.py` as the rule source
    - Add a sentence: "Run on any corpus; rules naturally no-op on unsegmented corpora."

## Out of scope for B9.3

- Adding NEW gloss rules beyond V060/V061/V062.
- Cross-corpus gloss-consistency comparison (does "AV" mean the same thing in NTU vs. ePark glosses?). Research question, not a validator.
- Renaming `rules/hard.py` → `rules/xml.py` (deferred future cleanup; affects every validator import).
- Per-corpus V062 severity downgrade (already tracked in [corpus-cleanup-tasks.md](2026-05-31-corpus-cleanup-tasks.md) for YeddaPalemeqBlog's 285 V062 findings).
- A unified `--rule-prefix` or `--rule-category` filter on `validate_xml.py` (orthogonal feature; not needed because validators stay split).

## Acceptance criteria

- `pytest tests/validators/test_validate_glosses.py` passes with ≥6 substantive cases covering V060, V061, V062, and the validate_glosses.py orchestrator.
- V062 is no longer in `rules/hard.py`'s RULES list; `validate_xml.py` no longer emits V062 findings.
- `validate_glosses.py` against a known-clean corpus produces zero Findings and empty CSVs (header only).
- `validate_glosses.py` against a known-bad corpus (or fixture) produces SOFT V060/V061 Findings + the corresponding CSV rows.
- The staged-pipeline architecture is documented in QC/README.md.
- `xml-validation.yaml` (or gloss-validation.yaml) invokes `validate_glosses.py` in CI; HARD V062 fails the job, SOFT V060/V061 warn.
