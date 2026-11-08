---
icon: broom
---

# suppress_transl_annotations.py

> Strips a curated, exact-match list of annotator-note parentheticals (e.g. `(人名)`, `(祈使)`, `(imperatives)`) from **sentence-level** `<TRANSL>` text — dry-run by default.

## What it's for

Some FormosanBank translations carry parenthetical editorial notes that are not part of the translation itself — grammatical labels and markers such as `(人名)` ("[this is a] personal name"), `(祈使)` (imperative), `(各族用語)`, or the English `(imperatives)` / `(collectively)`. These notes are noise in a sentence translation. This script removes them, using a **curated exact-match list** so it only strips known annotation strings and never guesses.

**Critical scope:** only S-level `<TRANSL>` (a `TRANSL` that is a *direct child* of an `<S>`) is touched. Word-level and morpheme-level `<TRANSL>` are never modified — there these same strings (e.g. `人名`) are legitimate word/morpheme glosses, and stripping them would destroy real data. `<FORM>` and `<PHON>` are never touched.

## How it works

The suppression list is read from a **sidecar data file**, by default `transl_annotation_suppress_list.txt` next to the script (override with `--list`). Each non-comment line is one exact parenthetical content to strip; `#` starts a comment. Edit that file to extend the list — no code change needed. (The shipped list includes entries such as `人名`, `東西`, `祈使`, `女子全名`, `各族用語`, `imperatives`, `collectively`.)

For each XML file, `process_file` parses with `lxml`, iterates `root.findall('S')`, and for each S-level `TRANSL`:

- A regex matches one parenthetical pair, **half- or full-width** (`( )` or `（ ）`), capturing inner content. A match is removed only if its whitespace-stripped inner content is in the suppression set.
- Whitespace is cleaned **only at each removal site**: a note between two spaces collapses to one space; an edge note's adjacent space is consumed. Text with no suppressed note is left **byte-for-byte untouched**.

When stripping leaves a `TRANSL` empty (the "translation" was only the note), `--empty-policy` decides:

| `--empty-policy` | Behavior |
|------------------|----------|
| `remove` (default) | Delete the now-empty `<TRANSL>` element. |
| `empty` | Keep an empty `<TRANSL></TRANSL>`. |
| `keep` | Do not suppress when the note is the entire translation (leave it in place). |

Changed files are written with `tree.write(..., xml_declaration=True, pretty_print=True, encoding='utf-8')` — lxml, exactly like `clean_xml.py`, so the diff shows only the text/element changes.

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`. Dry-run first, then `--apply`:

```bash
# Dry-run (default): preview before/after examples + summary, write nothing
python QC/cleaning/suppress_transl_annotations.py --corpora_path Corpora/ePark/XML

# Apply
python QC/cleaning/suppress_transl_annotations.py --corpora_path Corpora/ePark/XML --apply

# Keep empty TRANSL elements instead of removing them
python QC/cleaning/suppress_transl_annotations.py --corpora_path Corpora/ePark/XML \
    --empty-policy empty --apply

# Use a custom suppression list
python QC/cleaning/suppress_transl_annotations.py --corpora_path Corpora/ePark/XML \
    --list path/to/my_suppress_list.txt
```

| Flag | Default | Purpose |
|------|---------|---------|
| `--corpora_path` | *(required)* | Directory of XML files, processed recursively (`rglob('*.xml')`). |
| `--list` | sidecar `transl_annotation_suppress_list.txt` | Suppression list file (one exact parenthetical content per line; `#` comments). |
| `--empty-policy` | `remove` | What to do when a note was the entire translation: `remove`, `empty`, or `keep`. |
| `--apply` | off | Write changes. Without it, preview only. |
| `--show` | `25` | Max before/after examples to print. |

## Output & side effects

- **Modifies XML in place — but only with `--apply`.** **Dry-run is the default** (`DRY RUN: ...`), printing before/after examples and a summary (`files changed`, `notes removed`, `TRANSL left empty`) and writing nothing.
- With `--apply`, it edits S-level `<TRANSL>` text and, under `--empty-policy remove`, deletes emptied `<TRANSL>` elements. W/M-level TRANSL, FORM, and PHON are never altered.
- Translations with no suppressed note are left byte-for-byte unchanged.
- **Always `git diff` before committing.**

## When to run it

Run during corpus QC/cleaning, after the bulk text cleaning, when a corpus's sentence translations are known to contain annotator notes. It only acts on the curated list, so it is safe to run broadly — but review the dry-run output and confirm the suppression list matches what you actually want stripped, and that `--empty-policy` is the right choice for translations that are *only* a note.

## Related

- [clean_xml.py](clean-xml.md)
- [validate_text.py](validate-text.md)
- [validate_glosses.py](validate-glosses.md) — W/M-level glosses, which this script deliberately leaves alone
- [QC Pipeline overview](README.md)
- [Running an Audit](../running-an-audit.md)
