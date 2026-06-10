# B9.5 — Duplicate-sentence detection plan

**Date:** 2026-05-31
**Roadmap section:** B9.5 (Duplicates category of the six-category validator audit)
**Status:** [DONE 2026-06-01] — all work items W1–W4 landed on `feature/claude-tooling-phase-0` via merge of `worktree-agent-a9d15d445b16a8808` (merge commit `3c1d23187`). Per-W summary:
- **W1**: `QC/validation/validate_duplicate_sentences.py` (new) — within-corpus detector with `by_path` / `by_corpus` / `by_language` modes. HARD on within-file duplicates, SOFT on cross-file same-corpus.
- **W2**: tier choice (`--tier {standard,original}` default `standard`) + whitespace-normalized equivalence helper folded into W1.
- **W3**: `QC/cleaning/remove_duplicate_sentences.py` (new) — deterministic "keep first by (file, S id)" removal; `--dry-run` is the default, `--apply` required to mutate; `--scope file|corpus`.
- **W4**: `QC/README.md` pipeline + Cleaning section update; `.github/workflows/duplicate-sentences.yaml` runs detection per-corpus on PRs/pushes, uploads CSVs as 30-day artifacts; remover deliberately not in CI.

Open question resolutions: all defaults from the plan adopted as-is (OQ1=b, OQ2=b+d, OQ3=file→HARD/corpus→SOFT, OQ4=deterministic+dry-run).

Test counts at landing: 24 pass (13 validator + 11 remover) on `tests/{validators,cleaning}/test_*duplicate_sentences.py`.

Sanity-run finding (ePark): 3,963 HARD duplicate groups (8,394 occurrences) + 23,562 SOFT groups (78,474 occurrences). Heavy concentration in `qing_jing_zu_yu_contextual_indigenous_language/*` and `hui_ben_ping_tai_picture_book_platform/*` — likely a mix of intentional didactic repetition and ingestion bugs; curatorial review pending.

Followup landed 2026-06-01 in commit `06290ab1e`: drop dead `if text is None:` guard in `normalize_for_comparison`, remove unused `_filter_by_language` helper (by_language uses an inline directory walk in `main()`).

---

## Goal

Detect and (separately) remove duplicate `<S>` elements both *across* corpora and *within* a single corpus. Cross-corpus duplicates inflate the published token count and bias coverage statistics. Within-corpus duplicates usually indicate an ingestion bug (the same source segment captured twice) and are higher-confidence findings.

## Current state

**Exists:**
- [QC/utilities/find_duplicate_sentences.py](../../QC/utilities/find_duplicate_sentences.py) — cross-corpus duplicate finder. Reads multiple corpora, identifies S elements with identical FORM text.
- [tests/utilities/test_find_duplicate_sentences.py](../../tests/utilities/test_find_duplicate_sentences.py) — existing test coverage.

**Missing:**
- No within-corpus variant (or within-corpus flag on the existing tool).
- No `remove_duplicate_sentences.py` companion. Detection without removal means findings accumulate but nothing gets fixed.
- The tool lives in `utilities/`, not `validation/`. Probably correct — duplicate-finding is informational rather than a HARD-fail invariant — but worth confirming.

## Open questions to resolve before coding

1. **Within-corpus: flag on existing tool or separate script?** Two options:
   - (a) Add `--within-corpus` flag to `find_duplicate_sentences.py` that restricts comparison to S elements within the same TEXT or same XML file.
   - (b) Write a new `QC/validation/validate_duplicate_sentences.py` that focuses on within-corpus (with HARD severity for within-file duplicates) and consume the existing utility for cross-corpus.
   Recommend (a) **if** the existing tool's CLI accommodates the flag cleanly; (b) **if** within-corpus duplicates warrant being HARD findings in the validator pipeline (they likely do, given they signal ingestion bugs).

2. **What is the duplicate equivalence?** Options:
   - (a) Byte-equal FORM text (strict).
   - (b) Whitespace-normalized FORM text (permissive).
   - (c) Punctuation- and whitespace-normalized FORM text (most permissive).
   - (d) Comparison on `kindOf="standard"` only (avoids spurious original-tier near-duplicates).
   Recommend (b) + (d) for the first deployment. Document the choice in the tool's `--help`.

3. **Within-corpus scope: same file or same corpus?** A duplicate `<S>` in the same `<TEXT>` is almost certainly a bug. A duplicate `<S>` in a different `<TEXT>` in the same corpus might be legitimate (same proverb in two stories) but more often is a bug. Decision affects severity:
   - Same file → HARD.
   - Same corpus, different files → SOFT.

4. **`remove_duplicate_sentences.py`: deterministic or interactive?** Deterministic = "keep the first occurrence by file/id sort order, remove the rest." Interactive = "show each duplicate group, prompt for action." Recommend deterministic with `--dry-run` flag for first deployment; the user can always run `--dry-run` and inspect before letting it modify.

## Concrete work items

### W1. Within-corpus duplicate detection

- Per open question 1, resolve placement.
- If (a): modify `QC/utilities/find_duplicate_sentences.py` to add `--within-corpus` flag with file-scope and corpus-scope sub-modes.
- If (b): create `QC/validation/validate_duplicate_sentences.py` that emits HARD findings for within-file duplicates and SOFT for within-corpus duplicates.
- Add tests: extend `tests/utilities/test_find_duplicate_sentences.py` OR create `tests/validators/test_validate_duplicate_sentences.py`. Cover:
  - Within-file duplicate → expected finding (HARD).
  - Within-corpus, different file → expected finding (SOFT).
  - Cross-corpus (existing behavior) → unchanged.
  - Whitespace-only differences → treated as duplicates (per equivalence decision).

### W2. Equivalence and tier choice

- Implement open question 2's resolution as helper functions: `normalize_for_comparison(text)` and a `--tier` flag (`original` | `standard`, default `standard`).
- Document in `--help`.

### W3. `remove_duplicate_sentences.py`

- **File to create:** `QC/cleaning/remove_duplicate_sentences.py`
- CLI:
  - `--corpus_path <path>` (or by_corpus/by_path subcommand consistent with other QC scripts)
  - `--dry-run` (default? recommend yes)
  - `--scope file|corpus` (matches W1's scope decision)
  - `--tier original|standard` (matches W2)
- Behavior: identify duplicate groups, keep the first by (file, S id) sort order, remove the rest, write modified XML back.
- Test file: `tests/cleaning/test_remove_duplicate_sentences.py` (creating new `tests/cleaning/` subdirectory if it doesn't exist — verify with `ls tests/`).
- **Reversibility:** the script modifies XML in place. Per repo conventions ([CLAUDE.md](../../CLAUDE.md): "`clean_xml.py` modify XML in place — diff before committing."), mention this in the script docstring and in the commit message that lands the script.

### W4. Pipeline integration

- Update [QC/README.md](../../QC/README.md) pipeline order to include the validator (within-corpus detection) — likely between gloss validation and orthography extraction.
- The remover (`remove_duplicate_sentences.py`) goes in the cleaning section of the README, alongside `clean_xml.py`.
- Add a CI entry only for the detection side (not the removal — removers should not run in CI).

## Out of scope for B9.5

- Near-duplicate detection (edit-distance-based fuzzy matching). Useful but high false-positive rate; defer.
- Cross-corpus deduplication (i.e., picking a canonical version when the same sentence appears in multiple corpora). That's a curatorial decision, not a validator's call.
- Removal driven directly by CI. Removal touches data; should be opt-in only.

## Acceptance criteria

- Within-file duplicates produce HARD findings; within-corpus-cross-file produce SOFT findings (or per open question 3's resolution).
- Cross-corpus detection works as before; new tests cover the within-corpus variant.
- `remove_duplicate_sentences.py` has `--dry-run` and produces sensible deterministic output verified against a known-duplicate corpus (probably ePark, which has repeated example sentences across sub-corpora — confirm).
- Running the new detection validator against current `Corpora/` surfaces findings that are quoted in the resulting PR description, not just "exited 0".
