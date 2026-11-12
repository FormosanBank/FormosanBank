---
icon: tags
---

# apply\_gloss\_standard.py

> Writes the `TRANSL kindOf="standard"` gloss tier beside every original gloss, converting each gloss code according to the corpus's conversion table and rules file. Additive per POL-036: the original tier is never changed.

## What it's for

Each glossed corpus keeps its source's own gloss codes in the original tier. `QC/glossing/apply_gloss_standard.py` adds a standard tier in FormosanBank's single gloss vocabulary (Leipzig Glossing Rules plus the registry in `Glossing/supplementary_codes.tsv`), so glosses are comparable across corpora. Codes without a ruled mapping are copied verbatim — the standard tier is always complete, and what remains undecided is visible in the corpus's conversion table.

## How it works

For every `W` and `M` gloss (`TRANSL` whose `xml:lang` is a gloss language):

- The gloss is segmented by the corpus's **rules file** (`Glossing/ConversionTables/<Corpus>.rules.tsv`): separators (`.`, `-`, `=`), infix brackets, and any corpus-specific conventions (for example prose separators for a corpus that glosses in sentences).
- Each atom is looked up in the corpus's **conversion table** (`Glossing/ConversionTables/<Corpus>.tsv`): `CONVERT` rows map to their standard code, `KEEP` and `UNDECIDED` rows copy the atom unchanged. `language_overrides` apply per language (`trv` resolves to Seediq or Truku by the `dialect` attribute); an override to the code itself means "unmapped for this language".
- **Context rules** (`CONTEXT-CONVERT→X` lines in the rules file) convert an atom only on words whose morphemes include a diagnostic affix; unsegmented words may satisfy an affix pattern by their own shape.
- Glosses containing characters the rules flag (for example parentheses) are copied verbatim and listed in the **residue report**. Glosses with `<UNCLEAR/>` children convert their text segments and keep the children; `TRANSL`s with `ver=` (variant readings) are left entirely untouched.
- A bare original gloss is stamped `kindOf="original"`; pre-existing standard glosses are never overwritten.

## Usage

```bash
python QC/glossing/apply_gloss_standard.py --corpus <CorpusName> [--write]
# or explicitly:
python QC/glossing/apply_gloss_standard.py --path <XML dir> \
    --table Glossing/ConversionTables/<Corpus>.tsv \
    --rules Glossing/ConversionTables/<Corpus>.rules.tsv --write
```

Without `--write` it is a dry run that prints the conversion statistics (converted / copied / residue / standard\_added). Every glossed corpus's `CodeAndDocs/generate_xml.sh` runs this as its final step.

## Tests

`tests/glossing/test_apply_gloss_standard.py` covers conversion and tier insertion, infix brackets, KEEP/UNDECIDED copying, language overrides, kindOf stamping, residue, pre-existing standard tiers, dry runs, context rules (segmented and unsegmented words), `<UNCLEAR/>` children, and `ver=` variants. `tests/glossing/test_gloss_dictionaries.py` enforces that every code the tables map onto is defined in the per-language gloss dictionaries (`Glossing/GlossDictionaries/`).

## Related

- [QC Pipeline overview](README.md)
- [Gloss standardization](../../../standardization/glossing.md)
- [validate_glosses.py](validate-glosses.md)
- [standardize.py](standardize.md)
