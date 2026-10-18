# SEALS 33 national-languages page

Parallel Saisiyat and Seediq text from the organizing committee's
[national-languages page](https://sites.google.com/view/seals33/national-languages)
for the 2024 Southeast Asian Linguistics Society meeting in Taipei.

## Languages and dialects

| Language | Dialect | Records | XML |
| --- | --- | ---: | --- |
| Saisiyat (`xsy`) | Saisiyat | 29 | `XML/Saisiyat/saisiyat_seals.xml` |
| Seediq (`trv`) | unknown | 29 | `XML/Seediq/seediq_SEALS.xml` |

The Seediq file does not identify a dialect, so its dialect is reported as
unknown. Its `<TEXT>` carries `xml:lang="trv"` with `dialect="unknown"`; in
FormosanBank `trv` without `dialect="Truku"` is Seediq, so this is Seediq text,
not Truku. The Saisiyat file carries `xml:lang="xsy"` with `dialect="Saisiyat"`.

## Source

These are the translated sections of the
[2024 SEALS conference](https://sites.google.com/view/seals33/national-languages?authuser=0)
(SEALS 33), graciously provided by the authors.

The 2024 South East Asian Linguistic Society meeting took place in Taipei. The
corpus contains all 29 parallel source rows per Formosan language, with Mandarin
translations and English translations for 16 program titles per language.

Each record has a Mandarin translation; 16 program titles per language also
have English translations. There is no audio or source W/M analysis.

[The structured source snapshot](CodeAndDocs/source_snapshot.json) contains all
29 parallel page rows and accounts for 16 untranslated presenter blocks.
Navigation, the language legend, untranslated presenter/organizer names,
contact information and the site footer are outside the established corpus
scope. The snapshot matches the live page; builds do not refresh it.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/SEALS33_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

* SEALS 33 Organizing Committee. (2024). 國家語言專區. SEALS 33. https://sites.google.com/view/seals33/national-languages

The two files now carry one BibTeX string: the published Saisiyat value had a
stray period after `SEALS 33` that the Seediq value lacked.

## License

**License:** CC BY-NC 4.0

**Rights source:** Hsiu-chuan Liao, 2025-04-16; evidence: ask maintainer

The organizers permitted inclusion of the page in FormosanBank. This retains
the existing published `CC-BY-NC` claim; POL-042 treats a versionless value as
4.0. Missing local correspondence does not justify replacing that claim with
permission prose (POL-043). The spelling normalization requires maintainer
merge review. This preserves the published license under POL-042/043; the
spelling change requires maintainer merge review. Commercial AI Use requires
prior written permission under the
[FormosanBank terms](https://github.com/FormosanBank/FormosanBank/blob/main/LICENSE.md)
and [AI Use Addendum](https://github.com/FormosanBank/FormosanBank/blob/main/AI-USE-ADDENDUM.md).

## Notes and caveats

* The Seediq dialect is unknown (see "Languages and dialects" above).
* S25 is a title containing reconstructed proto-forms (`*-ʔ, *-h, *-∅`), not an
  ungrammatical example. Both titles remain included under the merged corpus
  ruling. The Saisiyat FORM now follows the actual Saisiyat source title instead
  of the earlier English copy. The four source-inherent V129 HARD findings
  remain visible and are checked by a corpus-owned exception test. (They are
  waived in [`CodeAndDocs/qc_waivers.tsv`](CodeAndDocs/qc_waivers.tsv), so the
  validators report them as `WAIVED`; the corpus-owned test is
  `test_waivers_cover_the_reconstruction_title_only` in
  `CodeAndDocs/tests/test_pipeline.py`, which checks that the waivers cover
  S25 of the two files and nothing else.)
* The source supplies the Saisiyat reconstruction title in row 25; an earlier
  copy had put its English title in the Saisiyat FORM. Preserve the translated
  title and its three reconstructed labels `*-ʔ`, `*-h`, `*-∅`. These are
  linguistic reconstructions, not ungrammaticality judgments. The
  [merged corpus ruling](https://github.com/FormosanBank/FormosanBank/commit/b0f882702e52a9d9aa7eafe0197f4570743810f1)
  explicitly retained the title and its source-inherent validation exception.
* The Saisiyat file uses `:` for vowel length; it is retained in PHON for
  Saisiyat but treated as punctuation for Seediq.
* The source conference abbreviation and paragraph boundaries are retained.
  Mandarin punctuation follows the source with current Chinese quote
  normalization.
* The Mandarin conference abbreviation, row-9 paragraph boundary and Saisiyat
  word boundary follow the source. Row-9 Mandarin punctuation is restored after
  an older pass processed that translation under an incorrect language code;
  current Chinese quote normalization still applies.
* There is no audio or word/morpheme analysis.

#### Two Seediq S IDs change (POL-037 exception)

Published TEXT identities are preserved, and so is every sentence identity
except two. The Seediq file previously had source rows 21 and 22 transposed, so
Seediq S21 and Saisiyat S21 named different talks. The two languages are now
aligned on content: **Seediq S21 is “Word stress in Yami” (previously S22), and
Seediq S22 is “Piuma Paiwan stress in directional evaluation” (previously
S21).** If you have cited Seediq S21 or S22 from an earlier release, remap those
two references; no other identity in either file has changed.

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

## Reproduction and processing

### How to reproduce

Use the current FormosanBank Python environment, then run from the corpus:

```bash
./CodeAndDocs/generate_xml.sh
```

In a standalone dev clone, set `FORMOSANBANK_ROOT` to the current FormosanBank
checkout and `PYTHON` to its Python executable. In the public layout the
surrounding checkout supplies the tools. The build needs only committed inputs.
[Provenance](CodeAndDocs/provenance.json) records the reviewed build's tools;
it never selects an old checkout.

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

**POL-047 deviation:** There is no manual-edits file, so that step is omitted.

To run the checks (writes reports to a new directory outside the corpus):

```bash
OUTPUT_DIR=/path/to/new/review ./CodeAndDocs/validate.sh
```

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

### What each step does

The original hand transcription is preserved in
`CodeAndDocs/pre_correction_snapshot/`. The final build uses a committed
structured snapshot of all 29 parallel source rows, checked against the complete
official page. `CodeAndDocs/generate_xml.sh` rebuilds the XML, then runs current
`clean_xml.py`, `standardize.py --remove_accents`, and
`add_phonology.py --orthography Ortho94`. Original and standard FORM, PHON, and
all source translations are retained. Source refresh is separate from
generation; all required build inputs are committed. The
[build provenance](CodeAndDocs/provenance.json) records the tools used without
pinning future builds.

[The pre-correction XML snapshot](CodeAndDocs/pre_correction_snapshot/) is
preserved byte-for-byte as historical evidence. It sits outside any `XML/`
directory. Final generation reads the reviewed structured snapshot.

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

`generate_xml.sh` runs these steps in order; any failing step stops the build
(`set -euo pipefail`):

1. **Locate the tools.** The FormosanBank checkout is the first argument, else
   `FORMOSANBANK_ROOT`, else the checkout three levels above `CodeAndDocs/`;
   Python is `PYTHON`, else `python3`. The script stops unless
   `QC/cleaning/clean_xml.py` exists there.
2. **Provenance note.** `generate_xml.sh` reads `provenance.json` and notes to
   stderr when the surrounding checkout is at a different commit. That is a
   note, never a gate: the build runs with the tools it finds and never goes
   looking for another checkout (POL-052).
3. **`CodeAndDocs/scripts/build_xml.py`** (no flags). Reads
   `CodeAndDocs/source_snapshot.json` and refuses it unless it has
   `schema_version` 1, exactly 29 rows numbered 1 to 29, non-empty Mandarin
   (`zho`), Saisiyat (`xsy`) and Seediq (`trv`) text in every row, and English
   (`eng`) in exactly rows 11-14, 16-22 and 24-28 (16 rows). It then deletes
   and recreates `XML/` and writes one file per language. Each `<TEXT>` gets
   the IDs, `xml:lang` and `dialect` shown under "Languages and dialects", the
   citation and BibTeX string, `copyright="CC BY-NC 4.0"`, and a `source`
   attribute naming the page URL, the snapshot's retrieval time and
   `source_orthography=Ortho94`. Each source row becomes one `<S>` whose `id`
   is the source-row number, holding the row's text as the original FORM, a
   Mandarin TRANSL, and an English TRANSL where the row has one. Nothing is
   excluded; it prints "source rows included per language: 29; source
   exclusions: 0".
4. **`QC/cleaning/clean_xml.py --corpora_path XML`** — shared cleaning, no
   corpus-specific flags, rewrites the files in place. For example, the
   snapshot's curly apostrophe (row 25 Saisiyat `ka:i’`) is `ka:i'` in the
   published FORM, and Chinese quotes in Mandarin translations are normalized.
5. **`QC/utilities/standardize.py --remove_accents --corpora_path XML`** —
   copies each original FORM to a standard FORM, removes null-morpheme units
   from sentence-level standard FORMs (but keeps asterisked reconstruction
   labels such as `*-∅`), and strips accents other than those the language's
   reference orthography attests. No conversion table is used, so the
   standard tier has the source's spelling.
6. **`QC/utilities/add_phonology.py --corpora_path XML --orthography Ortho94`**
   — writes original PHON from `Orthographies/Ortho94/` and standard PHON from
   `Orthographies/Ortho113/`. The IPA column is chosen from `dialect`; Seediq
   `dialect="unknown"` uses the `default` column. Unmapped punctuation is
   dropped from PHON, and any other character with no mapping is written as
   `*`.

#### Review and validation (`validate.sh`)

`validate.sh` requires `OUTPUT_DIR` to be a new absolute directory outside the
corpus. It writes one log per check there, prints each log, and exits non-zero
if any check failed. In order it runs: the corpus tests
(`CodeAndDocs/tests/`); `scripts/source_audit.py --json`; `validate_xml.py`
(against a view of the other published corpora); `validate_text.py`;
`validate_dialect.py`; `validate_duplicate_sentences.py --tier standard`;
`orthography_extract.py` and `validate_orthography.py` for the original and
the standard tier; `validate_vocabulary.py` on the standard tier;
`validate_registries.py`; and `validate_port_readiness.py`.

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

The source audit checks every original FORM and translation. Focused tests
protect source coverage, reconstructed forms, published identities and the
scoped validation exception.

The comparison tools require exact directory names. Validation uses a temporary
view of the existing `Saisiyat/default` and `Seediq/Default` reference inventories
for the corpus's registered dialect labels. The Seediq comparison remains a
generic, low-quality reference because the source dialect is unknown; this
does not assign a named dialect or alter the shared reference files.
