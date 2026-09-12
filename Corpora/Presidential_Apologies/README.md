# Presidential Apologies

**Basecamp card:** [6991940238](https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/6991940238)

The official 2016 presidential apology in 16 Indigenous languages, aligned with Mandarin and English. The corpus contains 16 TEXT records and 524 paragraph-sized S records; it has no word or morpheme analysis. The [Presidential Office Indigenous Historical Justice project](https://indigenous-justice.president.gov.tw/) provided the bilingual publications.

## Rights

**License:** public domain

**Rights source:** Wael Mohamed (recorded source status), 2024-10-16; evidence: ask maintainer

This retains the published corpus's public-domain status. The dated source coordination record confirms that status; it is not a new licence grant by the compiler. The committed PDFs and transcript snapshots are the recorded public build inputs.

## Source and alignment

`CodeAndDocs/Apologies/` contains one bilingual PDF and one native transcript per language, shared Mandarin and English transcripts, and separate Kanakanavu translations. The 36 files are checksummed in `CodeAndDocs/data/source_manifest.csv`. Fifteen texts have 33 aligned sections; Kanakanavu has 29. Sections can combine source paragraphs to align the translations.

The source audit compares all 524 native and 524 Mandarin sections with their PDF pages. It checks native body coverage and embedded word spaces, excluding synthetic layout spacing. Alignment allows documented typography differences and an added terminal period in titles or closings, without folding case, letters or diacritics. English is absent from the bilingual PDFs: its committed snapshots are checked for integrity, section counts and mapping, without claiming PDF verification.

Earlier corrections in `CodeAndDocs/data/source_corrections.csv` preserve Kavalan S6 word boundaries, Saaroa S0 `mualiuhlu`, and the Truku S25 text-layer apostrophe. The Truku PDF font displays a missing glyph, while its embedded text identifies U+FF07. Nine further paragraph repairs have PDF locators in the same correction ledger and are applied from `manual_edits.xml`. Shared tooling regenerates [manual_edits.md](CodeAndDocs/manual_edits.md) as the readable correction changelog.

## Language, dialect and IDs

`CodeAndDocs/data/dialect_authority.tsv` records source files, section counts, language codes, dialects, TEXT IDs and the Seediq glottocode. Dialects come from the cited published baseline, not from labels in the PDFs. That baseline is historical evidence, not a tools version pin.

Published TEXT IDs `PA_<Language>` and zero-based S IDs remain unchanged: `0` through `32`, or `0` through `28` for Kanakanavu. The tests compare source tiers, translations and IDs with a supplied published baseline.

The [published orthography decision](https://github.com/FormosanBank/FormosanBank/commit/9608caee5) uses `standardize.py --copy` and original PHON profile `Ortho113`, including the previously reviewed Thao choice. PHON follows the declared dialect column. Kanakanavu `h`/`f`, Puyuma `ē`, and Sakizaya loan `f` remain in source FORM. Current shared tools own accent handling in derived PHON; unavailable dialect sound values remain `*` without borrowing another dialect's values.

## Reproduce

Use a current FormosanBank checkout with its dependencies installed. From this repository root:

```bash
FORMOSANBANK_ROOT=/path/to/FormosanBank PYTHON=python3 \
  CodeAndDocs/generate_xml.sh
```

The build generates fresh source XML, applies recorded edits, cleans, copies standard FORM, generates PHON with `Ortho113`, then applies the scoped annotation handling below. It replaces only `XML/`; it does not fetch sources or run validators. Optional `QC_OUTPUT_DIR` selects an external warning directory. [provenance.json](CodeAndDocs/provenance.json) records the actual FormosanBank tools commit and never selects or pins the tools checkout. A Git-free export retains this provenance record.

**POL-047 deviation:** The [published annotation handling](https://github.com/FormosanBank/FormosanBank/commit/f73f24a78) runs `remove_standard_cjk_annotations.py` after phonology. It removes only CJK-only parenthetical annotations from standard FORM and regenerates PHON with those annotations masked. Original FORM, bare inline Mandarin and Latin parentheticals remain intact. This retains the corpus-specific ruling while shared tools supply the sound values.

Source auditing and tests are separate from generation:

```bash
python3 -m pip install -r CodeAndDocs/requirements.txt
python3 CodeAndDocs/scripts/audit_source_alignment.py \
  --xml-dir XML --report /path/outside/repository/source_alignment.csv
PRESIDENTIAL_PUBLIC_XML_ROOT=/path/to/FormosanBank/Corpora/Presidential_Apologies/XML \
  python3 -m pytest CodeAndDocs/tests
```

Run current FormosanBank QC separately and review its findings. Compare two fresh builds byte-for-byte; source-audit scores and unchanged record counts alone do not establish correctness. Keep audit/QC reports outside the repository. `XML/<Language>/` is the sole final-output tree.

## Audio

None.

## Notes and Issues

- The source repeats Saaroa S22/S23 on physical PDF pages 22/23 beside different translations. Both records are intentional and retained.
- Some source notation still needs interpretation under POL-027/POL-028: Puyuma S28 `parubalruk(pasenkin)` and Tsou S2/S9 `taa’uzva(taa’uiva)`, `esmiza(esmia)`, `mahiz’o(mahi’o)`. The PDFs provide no legend distinguishing lexical alternatives, spelling variants or explanatory notation. These existing readings remain intact pending that decision; the corpus is not yet ready to port.
- Mandarin code-switching, explanatory quotations and numbers are source content. CJK-only parenthetical annotations follow the scoped handling above. Do not treat every parenthesis as optional spoken material.
- English has no bilingual-PDF witness, and the PDFs do not establish the inherited dialect labels.
