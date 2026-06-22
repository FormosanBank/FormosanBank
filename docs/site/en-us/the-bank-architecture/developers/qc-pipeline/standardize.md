---
icon: layer-group
---

# standardize.py

> Creates the `FORM kindOf="standard"` sentence tier that the rest of the QC pipeline assumes — either as an exact copy of the original, or by applying a TSV transliteration mapping.

## What it's for

Most QC scripts expect every `<S>` to carry two sentence-level `FORM`s: `kindOf="original"` (the source spelling) and `kindOf="standard"` (FormosanBank's common orthography). Many corpora arrive with only the original tier. `standardize.py` builds the standard tier so orthography, punctuation, and metrics checks have a consistent target.

It has two modes:

- **`--copy`** — duplicate the original text verbatim into a new standard tier. This does **not** normalize spelling; it just guarantees the tier exists.
- **`--tsv_path`** — create the standard tier *and* apply a find-and-replace transliteration map, producing genuinely standardized spelling.

## How it works

For every `<S>` (matched as any element containing a `FORM` child) the script calls `create_standard`:

- If the element has no `FORM[@kindOf='original']`, it errors out and exits — there must be an original tier to standardize from.
- If a `FORM[@kindOf='standard']` already exists, its content is replaced; otherwise a new `FORM kindOf="standard"` element is inserted. Mixed content (notably inline `<UNCLEAR/>` markers) is deep-copied so it is not dropped.

In `--copy` mode that is the whole operation. In TSV mode it additionally runs `apply_standard`, doing ordered, global Python `str.replace` for each `(original → replacement)` pair on the standard tier's text. An empty replacement deletes the matched string.

**Choosing the TSV column.** The mapping TSV has an `original` column plus one or more value columns. The target column is resolved as follows:

- `--target_column` overrides everything.
- Otherwise, for **multi-dialect** languages (per `dialects.csv`), the file's `TEXT/@dialect` selects the column, falling back to a `standard` column (with a warning) or erroring if neither exists.
- For **single-dialect** languages, a `dialect`-named column is used if present, else the sole non-`original` column, else `standard`.

Replacements are literal and sequential, so order in the TSV matters — review the diff.

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`.

```bash
# Copy mode: just create the standard tier (no spelling changes)
python QC/utilities/standardize.py \
  --copy \
  --corpora_path /path/to/corpus-or-Final_XML

# Transliteration mode: create + standardize via a TSV map
python QC/utilities/standardize.py \
  --corpora_path /path/to/corpus-or-Final_XML \
  --tsv_path /path/to/orthography-map.tsv \
  --target_column standard
```

| Flag | Default | Notes |
| --- | --- | --- |
| `--copy` | off | Duplicate original → standard with no transformation. Mutually exclusive in intent with `--tsv_path`. |
| `--tsv_path` | none | TSV with an `original` column and target column(s). Required unless `--copy`. |
| `--target_column` | auto | Force a specific TSV column; otherwise auto-detected from dialect/language. |
| `--corpora_path` | (required) | Corpora root, a single corpus dir, or a single `.xml` file. |
| `--corpus` | none | Restrict to one corpus under `--corpora_path`. |
| `--language` | none | Restrict to files whose path matches this language name. |

### Single-file wrapper

`standardize.py --corpora_path <file.xml>` can operate on one XML file directly. `QC/utilities/standardize_single_file.py` is still available as a wrapper for workflows that prefer an explicit `--xml_path`; it copies the file into a temp directory, invokes `standardize.py --corpora_path <tempdir> --tsv_path …`, then writes the result back. Flags: `--xml_path`, `--tsv_path`, `--target_column`. (It has no `--copy` mode.)

## Output & side effects

**Modifies XML in place.** Each processed file is re-serialized (pretty-printed, blank lines stripped) and overwritten, with a new `FORM kindOf="standard"` element added to every element that has an original FORM (S/W/M, not just sentence level). Always `git diff` before committing — in TSV mode especially, confirm the transliteration did what you expected.

## When to run it

Early in the pipeline, immediately after [validate_xml.py](validate-xml.md) and **before** text/orthography checks. Run `--copy` whenever a corpus has only one sentence-level `FORM`; run the TSV mode when an actual transliteration map is available. See [Running an Audit](../running-an-audit.md) and [Porting a Corpus In](../porting-a-corpus.md).

## Related

- [QC Pipeline overview](README.md)
- [add_phonology.py](add-phonology.md)
- [orthography_extract.py](orthography-extract.md)
- [validate_text.py](validate-text.md)
- [validate_orthography.py](validate-orthography.md)
