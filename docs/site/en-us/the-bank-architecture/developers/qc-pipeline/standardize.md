---
icon: layer-group
---

# standardize.py

> Creates the `FORM kindOf="standard"` sentence tier that the rest of the QC pipeline assumes — either as an exact copy of the original, or by applying a TSV transliteration mapping.

## What it's for

Most QC scripts expect every `<S>` to carry two sentence-level `FORM`s: `kindOf="original"` (the source spelling) and `kindOf="standard"` (FormosanBank's common orthography). Many corpora arrive with only the original tier. `standardize.py` builds the standard tier so orthography, punctuation, and metrics checks have a consistent target.

It has three modes:

- **`--copy`** — duplicate the original text verbatim into a new standard tier. This does **not** normalize spelling; it just guarantees the tier exists.
- **`--ortho113`** — like `--copy`, but **deletes accents** from the standard tier (no TSV, no dialectal letter conversion). Use this when the dialect is unknown or mixed so a dialect-specific conversion table can't be chosen, but you still want an Ortho113-compatible, accent-free standard tier. (No Formosan orthography uses accents phonemically, so accent removal is the one normalization that is safe regardless of dialect.)
- **`--tsv_path`** — create the standard tier *and* apply a find-and-replace transliteration map, producing genuinely standardized spelling.

## How it works

For every `<S>` (matched as any element containing a `FORM` child) the script calls `create_standard`:

- If the element has no `FORM[@kindOf='original']`, it errors out and exits — there must be an original tier to standardize from.
- If a `FORM[@kindOf='standard']` already exists, its content is replaced; otherwise a new `FORM kindOf="standard"` element is inserted. Mixed content (notably inline `<UNCLEAR/>` markers) is deep-copied so it is not dropped.

In `--copy` mode that is the whole operation. In `--ortho113` mode it additionally runs `apply_standard` with an **empty** mapping, which deletes accents but converts no letters. In TSV mode it runs `apply_standard` with the loaded map, doing ordered, global Python `str.replace` for each `(original → replacement)` pair on the standard tier's text (an empty replacement deletes the matched string).

**Accents are stripped before any mapping is applied** (in both `--ortho113` and TSV modes). No Formosan orthography uses accents phonemically, so an accented vowel in a source text (for example Glosbe marks stress: `máduk`, `dálix`) is just the plain vowel wearing a diacritic. `apply_standard` strips these accents from the **standard** tier — decomposing to NFD, removing the accent marks (currently the combining acute and breve; the set is easy to extend), then recomposing. In TSV mode this guarantees a mapping entry keyed on the bare vowel still matches: without it, a rule such as `us → os` would silently skip `ús`. The **original** tier is never touched — it keeps the source's exact spelling, accents and all. (`--copy` runs no `apply_standard`, so it preserves accents verbatim; use `--ortho113` when you want a copy *with* accents removed.)

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

# Ortho113 mode: create the standard tier as a copy with accents deleted
# (no TSV; for unknown/mixed-dialect corpora)
python QC/utilities/standardize.py \
  --ortho113 \
  --corpora_path /path/to/corpus-or-Final_XML

# Transliteration mode: create + standardize via a TSV map
python QC/utilities/standardize.py \
  --corpora_path /path/to/corpus-or-Final_XML \
  --tsv_path /path/to/orthography-map.tsv \
  --target_column standard
```

| Flag | Default | Notes |
| --- | --- | --- |
| `--copy` | off | Duplicate original → standard with no transformation. |
| `--ortho113` | off | Duplicate original → standard, then delete accents (no TSV, no letter conversion). For unknown/mixed-dialect corpora. |
| `--tsv_path` | none | TSV with an `original` column and target column(s). |
| _(mode)_ | — | Exactly one of `--copy`, `--ortho113`, or `--tsv_path` is required. |
| `--target_column` | auto | Force a specific TSV column; otherwise auto-detected from dialect/language. |
| `--corpora_path` | (required) | Corpora root, a single corpus dir, or a single `.xml` file. |
| `--corpus` | none | Restrict to one corpus under `--corpora_path`. |
| `--language` | none | Restrict to files whose path matches this language name. |

### Single-file wrapper

`standardize.py --corpora_path <file.xml>` can operate on one XML file directly. `QC/utilities/standardize_single_file.py` is still available as a wrapper for workflows that prefer an explicit `--xml_path`; it copies the file into a temp directory, invokes `standardize.py --corpora_path <tempdir> --tsv_path …`, then writes the result back. Flags: `--xml_path`, `--tsv_path`, `--target_column`. (It has no `--copy` mode.)

## Output & side effects

**Modifies XML in place.** Each processed file is re-serialized (pretty-printed, blank lines stripped) and overwritten, with a new `FORM kindOf="standard"` element added to every element that has an original FORM (S/W/M, not just sentence level). The serializer preserves inline mixed content, including text around `<UNCLEAR/>`, without inserting formatting whitespace into the tier. Always `git diff` before committing. In TSV mode especially, confirm the transliteration did what you expected.

## When to run it

Early in the pipeline, immediately after [validate_xml.py](validate-xml.md) and **before** text/orthography checks. Run `--copy` whenever a corpus has only one sentence-level `FORM` and its source spelling should be preserved as-is; run `--ortho113` when the dialect is unknown or mixed and you just want an accent-free standard tier; run the TSV mode when an actual per-dialect transliteration map is available. See [Running an Audit](../running-an-audit.md) and [Porting a Corpus In](../porting-a-corpus.md).

## Related

- [QC Pipeline overview](README.md)
- [add_phonology.py](add-phonology.md)
- [orthography_extract.py](orthography-extract.md)
- [validate_text.py](validate-text.md)
- [validate_orthography.py](validate-orthography.md)
