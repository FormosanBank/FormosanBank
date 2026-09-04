# Presidential Apologies

This FormosanBank corpus builds the Presidential Apologies collection from the official 2016 apology translations. It contains 16 Indigenous-language texts aligned with Mandarin and English translations.

| Field | Value |
| --- | --- |
| Source | [Presidential Office Indigenous Historical Justice and Transitional Justice Committee](https://indigenous-justice.president.gov.tw/) |
| Source type | Official bilingual PDF translations and transcript snapshots |
| Rights | Public domain in the recorded FormosanBank source authority |
| Languages | 16 Formosan languages |
| Canonical output | `XML/` |
| TEXT elements | 16 |
| Sentence elements | 524 |
| Audio | None |
| FormosanBank tooling commit | `3a3c47c220520113f747e6a2d441494000e13c4b` |

## License and AI Use

The source is recorded as public domain. This corpus is also subject to the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

## Source and alignment

`CodeAndDocs/Apologies/` contains one official PDF and one native transcript for each language. The PDFs place the Indigenous-language translation beside Mandarin. Fifteen texts have 33 aligned sections. Kanakanavu has 29 sections and its own Mandarin and English transcript files.

The source audit matches all 524 native sections and all 524 Mandarin sections to the official PDFs. It removes layout whitespace and treats typographic width variants, quote styles, and ellipsis styles as equivalent. The title and closing section may differ only by an added terminal period in the transcript. No letters or words are normalized for alignment. See `CodeAndDocs/SOURCE_AUDIT.md`, `CodeAndDocs/data/source_alignment.csv`, and `CodeAndDocs/QC_SUMMARY.md`.

The shared English file and Kanakanavu English file are preserved official transcript snapshots. English is not printed in the bilingual PDFs, so it is checked for file integrity, section count, and deterministic XML mapping rather than PDF alignment.

Two source-content corrections and one published word-boundary reconciliation are recorded in `CodeAndDocs/data/source_corrections.csv`:

- Kavalan section `6`: spaces after two CJK annotations preserve the published lexical boundaries.
- Saaroa section `0`: `mualiuhlʉ` was corrected to the PDF's `mualiuhlu`.
- Truku section `25`: a semicolon was corrected to the PDF's fullwidth apostrophe after `tnpusu`.

## Language and dialect authority

`CodeAndDocs/data/dialect_authority.tsv` is the single mapping for language codes, source files, section counts, stable TEXT IDs, dialects, and the published Seediq glottocode. The PDFs do not identify dialects. The dialect labels are carried forward from the current published FormosanBank corpus at the pinned tooling commit so this rebuild does not introduce an unsupported reinterpretation.

The source orthography is processed as Ortho113. The standard FORM tier is copied from the cleaned original FORM tier. PHON is generated with each TEXT element's declared dialect column.

## Stable IDs

Published identifiers are preserved:

- TEXT IDs are `PA_<Language>`.
- Sentence IDs are zero-based decimal strings in source order.
- The 15 full translations use sentence IDs `0` through `32`.
- Kanakanavu uses sentence IDs `0` through `28`.

The tests compare every identifier with the pinned published baseline. Regeneration does not renumber the corpus.

## Reproduce and verify

Create an isolated environment and install both the corpus audit dependencies and the FormosanBank dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -r Corpora/Presidential_Apologies/CodeAndDocs/requirements.txt
```

Rebuild the canonical XML and run the complete audit and QC sequence:

```bash
PRESIDENTIAL_PYTHON=.venv/bin/python \
  Corpora/Presidential_Apologies/CodeAndDocs/scripts/reproduce.sh --write \
  --formosanbank-root .
```

Use `--check` to rebuild in a temporary directory and compare the result with committed `XML/` and source-alignment evidence:

```bash
PRESIDENTIAL_PYTHON=.venv/bin/python \
  Corpora/Presidential_Apologies/CodeAndDocs/scripts/reproduce.sh --check \
  --formosanbank-root .
```

The script verifies the pinned FormosanBank commit and object hashes before it runs:

1. Source manifest and native/Mandarin PDF alignment audit.
2. Deterministic source-tier XML generation.
3. `clean_xml.py`.
4. `standardize.py --copy`.
5. `add_phonology.py --orthography Ortho113` with declared dialects.
6. Reproducible removal of CJK-only parenthetical annotations from the standard tier.
7. XML, text, gloss, duplicate, and port-readiness validation.
8. Corpus tests and comparison with published stable IDs.

`CodeAndDocs/data/provenance.json` records the FormosanBank commit this corpus was built against. It is documentation: nothing in the build reads it. The build runs against the current state of the bank, so a rebuild picks up later tooling improvements rather than pinning them — if a rebuild changes the XML, review the diff against the prior published baseline.

## Corpus-specific processing

Tsou and Kavalan include Mandarin annotations in parentheses. These remain in `FORM kindOf="original"` for source fidelity. `remove_standard_cjk_annotations.py` removes only CJK-only parenthetical groups from the standard tier and masks them from generated PHON. Bare inline Mandarin and parenthetical Latin alternatives remain untouched.

The declared dialect tables contain `NA` entries for some letters found mainly in loans. Those letters remain `*` in PHON. This preserves the current maintainer ruling and does not borrow values from another dialect column.

The existing orthographic notes remain applicable:

- Kanakanavu `h` and `f` are retained.
- Puyuma `ē` is retained, including `yēncumin` and `sēhu`.
- Sakizaya `f` in apparent loans is retained.

## Layout

- `XML/`: final generated FormosanBank XML.
- `CodeAndDocs/Apologies/`: approved public source PDFs and transcripts.
- `CodeAndDocs/main.py`: deterministic source-tier generator.
- `CodeAndDocs/data/`: source, dialect, authority, correction, and alignment evidence.
- `CodeAndDocs/scripts/`: source audit and full reproduction scripts.
- `CodeAndDocs/tests/`: pipeline, stable-ID, source, and tier checks.

Run all commands from the FormosanBank repository root. `XML/` is the canonical corpus output; do not use a legacy `Final_XML/` path.
