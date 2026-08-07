---
icon: layer-group
---

# add_phonology.py

> Adds `PHON` (phonemic transcription) tiers by mapping a corpus's text through orthography→phoneme tables under `Orthographies/`.

## What it's for

`add_phonology.py` derives an IPA-ish phonemic transcription from already-spelled text and stores it as a sister `PHON` element next to each `FORM`. It always processes the **standard** tier (using the `Orthographies/Ortho113` tables); with `--orthography <Name>` it can additionally transcribe the **original** tier through a second, source-specific orthography table.

## How it works

For each file it reads `TEXT/@xml:lang` (mapped to a language name) and `TEXT/@dialect`, then loads `Orthographies/Ortho113/<Language>.tsv`. That TSV has a `letter` column plus value columns; the column actually used is chosen by whether the language is multi-dialect (per `dialects.csv`):

- **Explicit override**: `--target_column` selects that value column for the standard Ortho113 table and takes precedence over dialect detection.
- **Multi-dialect**: without an override, the `dialect` attribute selects the column, falling back to a `default` column.
- **Single-dialect**: the sole value column, else `IPA`, else `default`.

It builds an ordered list of `(letter → phoneme)` pairs (rows whose value is the literal `NA` are skipped), then for every `FORM[@kindOf="standard"]`:

1. Ensures a sibling `PHON[@kindOf="standard"]` exists (creating one right after the `FORM` if not).
2. Strips morphological segmentation markers from the `FORM` text so `PHON` stays clean IPA even when the FORM tier carries them: `=` (clitic) and the `<...>` infix brackets are always removed — the infix content is kept, since it is pronounced — while `-` is removed only when it is **not** a letter in the language's orthography (Bunun/Thao keep `-`).
3. Applies the mappings as ordered string replacements over the text, with light capitalization handling.
4. Replaces any leftover character that is not a known phoneme, punctuation, or whitespace with `*`.

The resulting string becomes the `PHON` element's text. With `--orthography <Name>`, the same procedure runs over `FORM[@kindOf="original"]` using `Orthographies/<Name>/<Language>.tsv`, writing `PHON[@kindOf="original"]`.

## Schema note (PHON is fully supported)

A `PHON` tier is **valid under the current schema**. [`QC/validation/xml_template.xsd`](validate-xml.md) defines a `PHON_Type` (mixed content; optional `kindOf` enumerated `original`/`standard`) and allows `PHON` in any order within `S`, `W`, and `M`. The retained fallback DTD also permits `PHON*`. So the older caveat that adding `PHON` could trip XSD/DTD validation **no longer applies** — files with `PHON` tiers pass `validate_xml.py`. (Still re-run [validate_xml.py](validate-xml.md) after this step as a matter of course.)

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`.

```bash
# Standard tier only (uses Orthographies/Ortho113)
python QC/utilities/add_phonology.py \
  --corpora_path /path/to/corpus-or-Final_XML

# Also transcribe the original tier through a source orthography
python QC/utilities/add_phonology.py \
  --corpora_path /path/to/corpus-or-Final_XML \
  --orthography Church \
  --language Amis
```

| Flag | Default | Notes |
| --- | --- | --- |
| `--corpora_path` | (required) | Corpora root (iterated entry-by-entry), a corpus dir, or a single `.xml` file. |
| `--orthography` | none | Folder name under `Orthographies/` used to also transcribe the **original** tier. Must exist. |
| `--language` | none | Restrict to files whose path matches this language name. |
| `--target_column` | none | Force a specific Ortho113 value column for the standard tier; otherwise auto-detect from dialect/language. |

### Single-file wrapper

`add_phonology.py --corpora_path <file.xml>` can operate on one XML file directly. `QC/utilities/add_phonology_single_file.py` is still available as a wrapper for workflows that prefer an explicit `--xml_path`; it runs `add_phonology.py` on one file via a temp directory, copying the result back. Flags: `--xml_path`, `--orthography`, `--target_column`, `--language`.

## Output & side effects

**Modifies XML in place.** A `PHON` element is inserted after each processed `FORM`, and each file is re-serialized and overwritten. The serializer preserves inline mixed content without inserting formatting whitespace inside it. Inspect the diff before committing. Confirm the phonemic strings look right and that stray `*` markers (unmapped characters) are not hiding orthography problems. The standard tier's `Ortho113/<Language>.tsv` must exist for the language, or the file is skipped with a warning.

## When to run it

After the standard tier exists (see [standardize.py](standardize.md)) and after orthography has been validated, so the input spelling is trustworthy. It is an optional enrichment step rather than a gate. See [Running an Audit](../running-an-audit.md) and [Porting a Corpus In](../porting-a-corpus.md).

## Related

- [QC Pipeline overview](README.md)
- [standardize.py](standardize.md)
- [orthography_detector.py](orthography-detector.md)
- [validate_xml.py](validate-xml.md)
