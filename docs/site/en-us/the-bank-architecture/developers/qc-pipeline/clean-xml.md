---
icon: broom
---

# clean_xml.py

> Normalizes Unicode, punctuation, and HTML entities in `<FORM>` and `<TRANSL>` text **in place**, emitting a warnings CSV and a transformation summary.

## What it's for

`clean_xml.py` is the first mechanical cleaning pass over a corpus's XML. It standardizes the *text content* of sentence-level `<FORM>` and `<TRANSL>` elements: NFC-normalizing Unicode, unescaping HTML entities, swapping full-width and typographic punctuation for ASCII, collapsing whitespace, stripping zero-width/BOM residue, and canonicalizing caret-like glottal-stop glyphs. It also handles segmentation markers (hyphens, clitic `=`, null-morpheme `Ø`) in the standard sentence tier according to each language's orthography.

Some fixes are unconditional and silent (e.g. NFC, zero-width stripping). Others are *flagged but not changed* — the script writes a `cleaner_warnings.csv` row so a human can decide (e.g. stray `*`, IPA stress marks, Bopomofo characters, ambiguous Chinese single quotes). It is a workhorse cleaner, not a validator: it mutates files directly and there is no dry-run.

## How it works

It walks `--corpora_path` recursively for `*.xml`. For each file:

1. **Raw text pass (byte level):** the file is read as a string, every non-breaking space (`U+00A0`) is replaced with a regular space, and the result is written straight back. This happens before any XML parsing.
2. **Parsed pass (lxml):** the file is re-parsed with `lxml`. For every `<S>`:
   - **Sentence-level `<FORM>`** text is: scanned for Bopomofo (warning `c007`); NFC-normalized; HTML-unescaped (logged to `html_entities.log`); run through `clean_text` (caret normalization → `swap_punctuation` → whitespace collapse → repeated-punctuation trim); and scanned for `*` (warning `c022`, text left intact). A `<S>` whose FORM text contains the literal `456otca` is **removed entirely**.
   - **`FORM[@kindOf="standard"]` only** is then run through hyphen handling (rule `c012`): the null-morpheme `Ø` (and its bridging hyphen) and the clitic `=` are always stripped; `-` is stripped unless it is a letter in the language's canonical orthography (empirically only **Bunun** and **Thao**), in which case it is preserved and a `c012` warning is emitted per occurrence. `--hard-remove-segmentation` forces stripping even there. Only direct `<FORM>` children of `<S>` are touched, so word/morpheme segmentation is preserved.
   - **`<TRANSL>`** text is run through `clean_trans`, which branches on `xml:lang`: non-Chinese TRANSL gets the same ASCII punctuation swap as FORM, while Chinese TRANSL collapses double-quote variants and corner brackets to `U+FF02` and only *warns* (`c002`) on single quotes/apostrophes, leaving them in place. Chinese title marks `《》` / `〈〉` are deliberately left untouched.

The XML is re-serialized with `tree.write(..., xml_declaration=True, pretty_print=True, encoding="utf-8")` **only if something changed** — so this is a full reparse-and-reserialize, not a byte-level edit, and lxml's `pretty_print` may re-indent. Diff before committing.

### Sidecar files written (under `--corpora_path`)

| File | Content |
|------|---------|
| `cleaner_warnings.csv` | One row per flagged occurrence: `rule_id, file, s_id, character, position`. Appended; not written when there are no warnings. |
| `html_entities.log` | Appended before/after text for each HTML-entity unescape. |

A transformation summary (input char → output char : count) is printed to stdout at the end.

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`. The script takes a single `--corpora_path` (no `search_by` positional):

```bash
# Clean one corpus's XML tree in place
python QC/cleaning/clean_xml.py --corpora_path Corpora/ePark/XML

# Force-strip standard-tier hyphens even for Bunun/Thao
python QC/cleaning/clean_xml.py --corpora_path Corpora/SomeCorpus/XML \
    --hard-remove-segmentation

# Point C012 at a non-default orthography directory
python QC/cleaning/clean_xml.py --corpora_path Corpora/SomeCorpus/XML \
    --ortho-path Orthographies/Ortho113
```

| Flag | Default | Purpose |
|------|---------|---------|
| `--corpora_path` | *(required)* | Root directory to walk recursively for `*.xml`. Mutated in place. |
| `--hard-remove-segmentation` | `False` | Strip `-` from `FORM[@kindOf="standard"]` even when it is an orthographic letter (Bunun, Thao); suppresses the `c012` warning. |
| `--ortho-path` | `Orthographies/Ortho113/` | Directory of `<Language>.tsv` orthography tables consulted by C012 to decide whether `-` is a letter. |

There is **no `--dry-run` and no `--apply`** — invoking the script writes changes.

## Output & side effects

- **Modifies XML in place.** Every `*.xml` under `--corpora_path` that changes is overwritten via a full lxml reparse-and-reserialize (`pretty_print=True`), which can re-indent the file even where text was unchanged.
- It can **delete `<S>` elements** (the `456otca` sentinel).
- It writes `cleaner_warnings.csv` and `html_entities.log` into `--corpora_path`.
- Most punctuation/zero-width fixes are silent; only the warning rules (`c002`, `c002b`, `c007`, `c012`, `c022`) surface in the CSV — and those generally leave the text *unchanged* by design.
- **Always `git diff` before committing.** Per repo convention, `clean_xml.py` modifies XML in place — review the diff (and the warnings CSV) before staging.

## When to run it

This is typically the **first cleaning step** when QC'ing a corpus in its dev repo, before standardization and validation. The pipeline order is roughly: `clean_xml.py` → orthography detection (human input) → `standardize.py` → `add_phonology.py` → validators.

Prerequisites: XSD-valid XML (run [validate_xml.py](validate-xml.md) first). The `kindOf="original"` vs `kindOf="standard"` distinction matters here — C012 hyphen handling only touches the standard tier, preserving the source's orthographic choices in the original tier.

## Related

- [validate_xml.py](validate-xml.md)
- [validate_text.py](validate-text.md) — flags many of the same characters HARD
- [standardize.py](standardize.md)
- [orthography_detector.py](orthography-detector.md)
- [QC Pipeline overview](README.md)
- [Running an Audit](../running-an-audit.md)
