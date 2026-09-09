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

### Two Seediq S IDs change (POL-037 exception)

Both published TEXT IDs are preserved. **Two published S IDs are not.** The
hand-built Seediq file had source rows 21 and 22 transposed, so published
Seediq S21 carried the Piuma Paiwan stress title while Saisiyat S21 carried
the Yami one — the two parallel files described different talks under the
same ID. The maintainer ruled on 2026-09-09 that matching content across the
two languages is worth breaking ID stability here:

| ID | Seediq, as published | Seediq, now | Saisiyat (unchanged) |
| --- | --- | --- | --- |
| S21 | Piuma Paiwan stress in directional evaluation | **Word stress in Yami** | Word stress in Yami |
| S22 | Word stress in Yami | **Piuma Paiwan stress in directional evaluation** | Piuma Paiwan stress in directional evaluation |

No other ID in either file moves, and every remaining ID equals its source-row
number. Anyone citing SEALS33 Seediq S21 or S22 from a release before this one
must remap. This is the only POL-037 break in the corpus; it supersedes the
earlier revision of this branch, which held both IDs in place with a
`published_id()` mapping and accepted the cross-language mismatch instead.

The Mandarin conference abbreviation, row-9 paragraph boundary and Saisiyat
word boundary follow the source. Row-9 Mandarin punctuation is restored after
an older pass processed that translation under an incorrect language code;
current Chinese quote normalization still applies. The two files now carry one
BibTeX string: the published Saisiyat value had a stray period after
`SEALS 33` that the Seediq value lacked.

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
is required. Original source labels remain intact **in both tiers**: S25's
`*-ʔ`, `*-h` and `*-∅` are Neogrammarian reconstruction labels, and shared
standardization no longer mistakes the `∅` of `*-∅` for a null morpheme — an
earlier build left `ma *`, a bare asterisk naming nothing. That exemption lives
in `QC/utilities/standardize.py`, not here (POL-046); this corpus's XML cannot
be reproduced against a FormosanBank checkout that predates it. The unknown
Seediq dialect uses the registered fallback. Source `ey` and standard `ey` have
different registered pronunciations. Saisiyat `:` remains vowel length in PHON.

**POL-047 deviation:** There is no manual-edits file, so that step is omitted.

`generate_xml.sh` reads `provenance.json` and notes to stderr when the
surrounding checkout is at a different commit. That is a note, never a gate: the
build runs with the tools it finds and never goes looking for another checkout
(POL-052).

## Review and validation

```bash
OUTPUT_DIR=/path/to/new/review ./CodeAndDocs/validate.sh
```

The source audit checks every original FORM and translation, including the
preserved IDs. The focused fixtures protect reconstruction notation, source
coverage and the two stress titles. The validator runs all applicable checks.
The four V129 findings on original/standard FORM in S25 of the two files are
waived in [`CodeAndDocs/qc_waivers.tsv`](CodeAndDocs/qc_waivers.tsv) (POL-054)
and reported as `WAIVED` rather than `HARD`; any other HARD finding fails the
run. A waiver whose finding has been fixed does not fail anything — tidy it
with `waivers.py prune` when convenient. Expect four V116 SOFT
findings too (non-ASCII in FORM): the two `∅` in the original tier and, since
the reconstruction labels now survive standardization, the two in the standard
tier. Review every SOFT finding,
orthography/vocabulary comparison and warning sidecar before a readiness
verdict. Warnings are retained for review rather than deleted by the build.

The comparison tools require exact directory names. Validation uses a temporary
view of the existing `Saisiyat/default` and `Seediq/Default` reference inventories
for the corpus's registered dialect labels. The Seediq comparison remains a
generic, low-quality reference because the source dialect is unknown; this
does not assign a named dialect or alter the shared reference files.

Source acquisition is a separate entry point from the build (POL-047), and
`generate_xml.sh` never invokes it — a rebuild must not depend on the page
still being up, or still being the page that was reviewed. To check the live
page against the committed snapshot without changing anything:

```bash
./CodeAndDocs/refresh_source.sh --check
```

Dropping `--check` overwrites `source_snapshot.json` from the live page. That
is a source change, not a build step: review the diff, then re-run
`generate_xml.sh` and `validate.sh` before committing anything.
Optional scraper/test dependencies are in `CodeAndDocs/requirements.txt`.
The complete public package is `README.md`, `CodeAndDocs/` and `XML/` from one
verified dev commit, exported with `git archive`; all XML is included unchanged.
