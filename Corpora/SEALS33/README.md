# SEALS33 national-languages page

Parallel Saisiyat and Seediq text from the organizing committee's
[national-languages page](https://sites.google.com/view/seals33/national-languages)
for the 2024 Southeast Asian Linguistics Society meeting in Taipei.

| Language | Dialect | Records | XML |
| --- | --- | ---: | --- |
| Saisiyat (`xsy`) | Saisiyat | 29 | `XML/Saisiyat/saisiyat_seals.xml` |
| Seediq (`trv`) | unknown | 29 | `XML/Seediq/seediq_SEALS.xml` |

Each record has a Mandarin translation; 16 program titles per language also
have English translations. There is no audio or source W/M analysis.

## Rights

**License:** CC BY-NC 4.0

**Rights source:** Hsiu-chuan Liao, 2025-04-16; evidence: ask maintainer

The organizers permitted inclusion of the page in FormosanBank. This retains
the existing published `CC-BY-NC` claim; POL-042 treats a versionless value as
4.0. Missing local correspondence does not justify replacing that claim with
permission prose (POL-043). The spelling normalization requires maintainer
merge review. Commercial AI Use requires prior written permission under the
[FormosanBank terms](https://github.com/FormosanBank/FormosanBank/blob/main/LICENSE.md)
and [AI Use Addendum](https://github.com/FormosanBank/FormosanBank/blob/main/AI-USE-ADDENDUM.md).

## Source and corrections

[The structured source snapshot](CodeAndDocs/source_snapshot.json) contains all
29 parallel page rows and accounts for 16 untranslated presenter blocks.
Navigation, the language legend, untranslated presenter/organizer names,
contact information and the site footer are outside the established corpus
scope. The snapshot matches the live page; builds do not refresh it.

The source supplies the Saisiyat reconstruction title in row 25; an earlier
copy had put its English title in the Saisiyat FORM. Preserve the translated
title and its three reconstructed labels `*-ʔ`, `*-h`, `*-∅`. These are linguistic
reconstructions, not ungrammaticality judgments. The
[merged corpus ruling](https://github.com/FormosanBank/FormosanBank/commit/b0f882702e52a9d9aa7eafe0197f4570743810f1)
explicitly retained the title and its source-inherent validation exception.

Both published TEXT IDs and all S identities are preserved. Seediq source row
21 (Yami stress) retains published S ID 22; source row 22 (Piuma Paiwan stress)
retains ID 21. Their output order follows the page. The remaining IDs equal
the source-row numbers. The Mandarin conference abbreviation, row-9 paragraph
boundary and Saisiyat word boundary follow the source. Row-9 Mandarin
punctuation is restored after an older pass processed that translation under
an incorrect language code; current Chinese quote normalization still applies.

[The pre-correction XML snapshot](CodeAndDocs/pre_correction_snapshot/) is
preserved byte-for-byte as historical evidence. It sits outside any `XML/`
directory. Final generation reads the reviewed structured snapshot.

## Reproduction

Use the current FormosanBank Python environment, then run from the corpus:

```bash
./CodeAndDocs/generate_xml.sh
```

In a standalone dev clone, set `FORMOSANBANK_ROOT` to the current FormosanBank
checkout and `PYTHON` to its Python executable. In the public layout the
surrounding checkout supplies the tools. The build needs only committed inputs.
[Provenance](CodeAndDocs/provenance.json) records the reviewed build's tools;
it never selects an old checkout.

The build writes source XML, runs shared cleaning, standardizes with
`--remove_accents`, then generates PHON with source orthography `Ortho94`.
These are the merged corpus's processing choices. No spelling conversion table
is required; shared standardization removes the S25 null unit only from the
standard tier. Original source labels remain intact. The unknown Seediq dialect
uses the registered fallback. Source `ey` and standard `ey` have different
registered pronunciations. Saisiyat `:` remains vowel length in PHON.

**POL-047 deviation:** There is no manual-edits file, so that step is omitted.

## Review and validation

```bash
OUTPUT_DIR=/path/to/new/review ./CodeAndDocs/validate.sh
```

The source audit checks every original FORM and translation, including the
preserved IDs. The focused fixtures protect reconstruction notation, source
coverage and the two stress titles. The validator runs all applicable checks
and verifies that the only HARD exception is the four recorded V129 findings
on original/standard FORM in S25 of the two files. Review every SOFT finding,
orthography/vocabulary comparison and warning sidecar before a readiness
verdict. Warnings are retained for review rather than deleted by the build.

The comparison tools require exact directory names. Validation uses a temporary
view of the existing `Saisiyat/default` and `Seediq/Default` reference inventories
for the corpus's registered dialect labels. The Seediq comparison remains a
generic, low-quality reference because the source dialect is unknown; this
does not assign a named dialect or alter the shared reference files.

To check the source without changing the snapshot:

```bash
python CodeAndDocs/scripts/scrape_source.py --check
```

A deliberate source refresh omits `--check` and requires a new source review.
Optional scraper/test dependencies are in `CodeAndDocs/requirements.txt`.
The complete public package is `README.md`, `CodeAndDocs/` and `XML/` from one
verified dev commit, exported with `git archive`; all XML is included unchanged.
