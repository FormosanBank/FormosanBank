# B9.3 — Gloss validation plan

**Date:** 2026-05-31
**Roadmap section:** B9.3 (Gloss category of the six-category validator audit)
**Status:** Plan; not yet started.

---

## Goal

Make the gloss-validation pipeline first-class: tested, CI-integrated, and consolidated so V062 and any gloss-related rules live in one place rather than scattered across `validate_xml.py` and `validate_glosses.py`.

## Current state

**Exists:**
- [QC/validation/validate_glosses.py](../../QC/validation/validate_glosses.py) — gloss-specific validator. Checks things like W-TRANSL ↔ M-TRANSL gloss agreement, angle-bracket convention for infix glosses, etc.
- V062 (infix-without-angle-bracket-gloss) currently lives in [QC/validation/rules/hard.py](../../QC/validation/rules/hard.py) and runs through `validate_xml.py`.

**Missing:**
- No test file `tests/validators/test_validate_glosses.py`.
- V062 lives in the XML validator's ruleset, not the gloss validator. This is a categorization bug; gloss-rule findings belong with gloss findings.
- `validate_glosses.py` is not in the CI workflow ([`.github/workflows/xml-validation.yaml`](../../.github/workflows/xml-validation.yaml)).
- Not invoked from [`QC/README.md`](../../QC/README.md)'s documented pipeline order.

## Open questions to resolve before coding

1. **Move V062 or alias it?** Three options:
   - (a) Move V062 from `rules/hard.py` to a new `QC/validation/rules/gloss.py` and have `validate_glosses.py` consume the same rule infrastructure (`Finding`, `Severity`, `RULES` list). Cleanest if `validate_glosses.py` is rewritten on top of the rule infrastructure.
   - (b) Leave V062 in `validate_xml.py` and add a cross-reference comment. Pragmatic if `validate_glosses.py` uses a different architecture.
   - (c) Run V062 in *both* validators by importing the rule function. Risk of double-counting in aggregate reports.
   Recommend (a) **if** `validate_glosses.py` can be migrated to the rule registry without major churn. Otherwise (b).

2. **What rules does `validate_glosses.py` currently enforce that aren't in `rules/`?** Read the file first; some checks may already be re-implementations of rules that exist as V0xx codes. Consolidate.

3. **Which corpora does this need to run on?** Only corpora with `<W>` / `<M>` segmentation. Per [QC/README.md](../../QC/README.md): "validate_glosses.py only for corpora with W/M segmentation." Need a programmatic "is this corpus segmented?" check before invoking — or accept that the validator no-ops gracefully on unsegmented corpora.

## Concrete work items

### W1. Read `validate_glosses.py` and inventory its checks

- Catalogue each distinct check the file performs.
- For each check: does it have a V0xx code? Is it duplicated in `rules/`?
- Output: a short inline comment block at the top of the file (or a one-paragraph addendum to this plan) listing the checks.

### W2. Decide V062 placement (per open question 1)

- Document the decision in the commit message that lands the move (or no-move).
- If moving: create `QC/validation/rules/gloss.py`, transfer V062 + its tests, register in a new `GLOSS_RULES` list, update `validate_glosses.py` to consume it.

### W3. Tests for `validate_glosses.py`

- **File to create:** `tests/validators/test_validate_glosses.py`
- Cover at minimum:
  - Clean segmented corpus → zero findings.
  - W-TRANSL ↔ M-TRANSL disagreement → expected finding.
  - Infix morpheme without angle-bracket gloss in W-TRANSL → V062 finding (or whatever code V062 ends up under post-W2).
  - Unsegmented corpus (no `<W>`/`<M>`) → validator no-ops cleanly (no findings, no crashes).
- Pattern: same `tmp_path`-based corpus building used in `test_validate_xml.py`.

### W4. CI integration

- **File to edit:** [`.github/workflows/xml-validation.yaml`](../../.github/workflows/xml-validation.yaml)
- Add a step that runs `validate_glosses.py` against changed `.xml` files (PR track) and the baseline (push track), filtered to corpora that have at least one `<W>` element.
- Treat HARD findings as failures, SOFT as warnings (mirror the XML track).

### W5. Documentation

- **File to edit:** [QC/README.md](../../QC/README.md)
- Add `validate_glosses.py` to the documented pipeline order (currently item 6 in QC/README.md but verify; the README says "only for corpora with W/M segmentation" which should stay).
- Reference this plan or its outcome in the commit message.

## Out of scope for B9.3

- Adding NEW gloss rules. This work is consolidation + test coverage. New rule design is a separate item — when a new gloss check is needed, add it under the consolidated infrastructure W2 produces.
- Cross-corpus gloss-consistency comparison (e.g., does "AV" mean the same thing in NTU vs. ePark glosses?). That's a research question, not a validator.

## Acceptance criteria

- `pytest tests/validators/test_validate_glosses.py` passes with ≥4 substantive cases.
- V062 has a single home (per W2 decision) — no double-counting in aggregate reports.
- `validate_glosses.py` runs in CI on PR + push and surfaces findings.
- `QC/README.md` lists `validate_glosses.py` in the canonical pipeline order with a one-line description of what it checks.
