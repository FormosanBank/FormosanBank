---
icon: broom
---

# remove_duplicate_sentences.py

> Deletes duplicate `<S>` elements (those found by `validate_duplicate_sentences.py`) from XML files, keeping the first occurrence — dry-run by default.

## What it's for

Some corpora contain the same sentence more than once — within a single file, or across files in the same corpus. [validate_duplicate_sentences.py](validate-duplicate-sentences.md) detects these; `remove_duplicate_sentences.py` removes them. It is the companion cleaner and shares the validator's exact equivalence logic so the two never drift apart.

Within each duplicate group it keeps the **first occurrence by `(file, S id)` sort order** and removes the rest. This deterministic rule (B9.5 plan, OQ4) makes results stable and reproducible regardless of filesystem walk order.

## How it works

Equivalence is imported directly from the validator: it calls `normalize_for_comparison` from `validate_duplicate_sentences.py`, so two sentences are "the same" when their whitespace-normalized `--tier`-selected `<FORM>` text matches. For each `<S>`, only the **first** direct-child `<FORM>` with the matching `kindOf` (the `--tier`) is used as the comparison key.

Planning (`plan_removals`) is deterministic:

- `--scope file` (default): duplicates are detected *within each file only*. For each file, sentences are grouped by normalized text; in any group of 2+, the first by S-id sort key is kept and the rest are scheduled for removal.
- `--scope corpus`: duplicates are detected *across all files* under the scan root. Occurrences are sorted by `(file path, S-id sort key)`, the first is kept, and the rest scheduled.

S-ids sort naturally (`S_2` before `S_10`) by parsing the trailing integer. The final removal list is sorted by `(file, S-id)` for a stable global order.

Apply (`apply_removals`) groups removals by file, parses each file once with `lxml`, removes every `<S>` whose id is scheduled, and writes back with `tree.write(..., pretty_print=False, encoding="utf-8", xml_declaration=True)`. (Note: unlike `clean_xml.py`, this writer uses `pretty_print=False`, so it does not re-indent surrounding content.)

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`. The script uses the standard `search_by` positional (`by_path`, `by_corpus`, `by_language`). Always dry-run first:

```bash
# Dry-run (default): plan removals, write nothing
python QC/cleaning/remove_duplicate_sentences.py by_path --path Corpora/ePark/XML

# Apply after reviewing the plan
python QC/cleaning/remove_duplicate_sentences.py by_path --path Corpora/ePark/XML --apply

# by_corpus
python QC/cleaning/remove_duplicate_sentences.py by_corpus \
    --corpora_path Corpora --corpus ePark --apply

# Include cross-file duplicates within the corpus
python QC/cleaning/remove_duplicate_sentences.py by_path --path Corpora/ePark/XML \
    --scope corpus --apply

# Compare on the original tier instead of standard
python QC/cleaning/remove_duplicate_sentences.py by_path --path Corpora/ePark/XML \
    --tier original
```

| Flag | Default | Purpose |
|------|---------|---------|
| `search_by` | *(required)* | `by_path`, `by_corpus`, or `by_language`. |
| `--path` | — | XML file or directory (for `by_path`). |
| `--corpora_path` | — | Corpora directory (for `by_corpus` / `by_language`). |
| `--corpus` | — | Corpus name (for `by_corpus`). |
| `--language` | — | Language name (for `by_language`; scans each corpus's `XML/<language>`). |
| `--scope` | `file` | `file` = within-file duplicates only (HARD); `corpus` = also cross-file within the root. |
| `--tier` | `standard` | Which `FORM @kindOf` to compare: `standard` or `original`. |
| `--apply` | off | Actually modify files. Default is dry-run. |

## Output & side effects

- **Modifies XML in place — but only with `--apply`.** **Dry-run is the default**: without `--apply` it prints `[dry-run] Would remove N duplicate <S> element(s)` followed by each `file#S_id`, and writes nothing.
- `--apply` deletes the scheduled `<S>` elements and rewrites the affected files (`pretty_print=False`).
- The kept sentence in each group is the first by `(file, S-id)` order — deterministic and reproducible.
- **Always `git diff` before committing.** Per repo convention, in-place XML mutators should be reviewed before staging.

## When to run it

Run after [validate_duplicate_sentences.py](validate-duplicate-sentences.md) has flagged duplicates and you've reviewed them. Use the **same `--tier`** the validator used so the equivalence matches. `--scope file` duplicates are HARD (a sentence repeated inside one file is almost always an error); `--scope corpus` cross-file duplicates may be legitimate (the same sentence appearing in two source documents), so review the dry-run carefully before applying corpus scope.

## Related

- [validate_duplicate_sentences.py](validate-duplicate-sentences.md) — detects the duplicates this script removes
- [find_duplicate_sentences.py](find-duplicate-sentences.md)
- [clean_xml.py](clean-xml.md)
- [QC Pipeline overview](README.md)
- [Running an Audit](../running-an-audit.md)
