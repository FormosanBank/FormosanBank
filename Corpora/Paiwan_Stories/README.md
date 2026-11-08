# Paiwan Stories

Three Eastern Paiwan stories with Chinese translations: *Dingding*,
*Kavatjes ni vuvu* and *Maljialjian a qaciljay*. The corpus contains 46
bilingual passages, with whole-story audio and no word or morpheme analysis.

## Languages and dialects

Paiwan (ISO 639-3 `pwn`), Eastern dialect. All three XML files
(`XML/Paiwan/DingDing.xml`, `XML/Paiwan/kavatjes_ni_vuvu.xml` and
`XML/Paiwan/maljialjian_a_qaciljay.xml`) declare `xml:lang="pwn"` and
`dialect="Eastern"` on `<TEXT>`. Every sentence carries one Mandarin Chinese
translation (`TRANSL xml:lang="zho"`).

## Source

#### Overview

Three children's stories in Eastern Paiwan with Chinese translations:
*Dingding*, *Kavatjes ni vuvu* and *Maljialjian a qaciljay*.

#### Source materials

* Gesi Giling (2020), *Dingding* and *Kavatjes ni vuvu*, illustrated by Tjaiwan Giling. Both PDF colophons date the first printing to November 2020.
* *Maljialjian a qaciljay*, an undated bilingual Word document.

The two illustrated PDFs credit Gesi Giling for the Indigenous text and
Tjaiwan Giling for illustrations; both colophons date their first printing
to November 2020. The third source is a bilingual Word document.

#### Audio

Three whole-story WAV recordings are available through the corpus download
script and FormosanBank's published Hugging Face audio contract. Each XML root
names its recording. The duration metric below counts `AUDIO` elements;
these whole-story references have no sentence timings and therefore report zero.

`./download_audio_data.sh` retrieves the three published WAVs into ignored
`Audio/`, using the revision in FormosanBank's `audio_sources.json`.
Use `--dry-run` to check the remote inventory without downloading.
The recordings retain their published 16 kHz mono representation; no
resampling or channel conversion is performed. Each TEXT names its whole-story
recording. Sentence timings are not included.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Paiwan_Stories_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

* Juan, T. F., & Ruan, X. (2024). *Corpus of Paiwan stories* [Electronic resource].

## License

**License:** CC BY-NC 4.0

**Rights source:** Gesi Giling (阮翠芳), 2024-04-13; evidence: ask maintainer

CC BY-NC 4.0. Joshua Hartshorne recorded direct permission from the
Indigenous-text author, Gesi Giling (阮翠芳), on 2024-04-13; evidence: ask maintainer.
The central FormosanBank terms and AI-use addendum also apply.

The author granted republication under CC BY-NC. The licence was recorded unversioned (`CC-BY-NC`) until 2026-10-17; POL-042 normalises an unversioned grant to 4.0.

Joshua Hartshorne recorded permission directly from the Indigenous-text
author. The illustrated books also carry separate illustration, adaptation
and publisher rights. Full source documents are not redistributed here.
Full illustrated sources are not redistributed because they contain separate
illustration and publisher rights.

## Notes and caveats

The restored Maljialjian passage uses `S6a`, between the existing S6 and S7;
all published TEXT and sentence IDs remain stable. The recovered Maljialjian
passage uses `S6a`, preserving every published TEXT and sentence ID.

Chinese translations omitted or shifted in the earlier corpus are restored
from the sources. Omitted or shifted Chinese translations are restored from
the sources.

Published quotation corrections and comma/exclamation typography are retained
in the transcription; `repair_records.py` records the ID and locator repair.
Published quotation corrections and documented typography are retained.

The Word source has 15 table rows containing 16 passages; row 4 holds two units.

There is no source word or morpheme analysis.

Historical alignment files are unavailable, so no sentence timings are inferred.
Historical sentence-alignment files are unavailable. The three published WAVs
are preserved without resampling or inferred timings.

## Reproduction and processing

### How to reproduce

```bash
bash Corpora/Paiwan_Stories/CodeAndDocs/generate_xml.sh
```

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

The corpus directory contains the XML, reviewed transcription, metadata, build
code and audio downloader.

The build reconstructs XML from this transcription, without fetching or
re-extracting the restricted documents. Source documents are not fetched during
reproduction. With current FormosanBank dependencies:

```bash
FORMOSANBANK_ROOT=/path/to/FormosanBank PYTHON=python3 ./CodeAndDocs/generate_xml.sh
python3 -m unittest discover -s CodeAndDocs/tests -v
```

Inside `Corpora/Paiwan_Stories`, the shared checkout is found automatically.
The build generates fresh source tiers, runs shared cleaning, copies original
FORM to standard with `standardize.py --copy`, and derives PHON with Ortho94
for originals and the registered standard for standard FORM. Ortho94 and
Ortho113 Eastern values agree for this corpus's letters.

The [build entrypoint](CodeAndDocs/generate_xml.sh)
generates source tiers, then runs shared cleaning, copy standardization and
phonology. It uses current FormosanBank tools; the actual build revision is
recorded in [provenance.json](CodeAndDocs/provenance.json).
Actual build tools are recorded in [provenance.json](CodeAndDocs/provenance.json), without a tools pin.
QC is separate from generation. Set `QC_OUTPUT_DIR` to retain build warnings.

### What each step does

#### Inputs

The corpus contains 46 bilingual passages reconstructed from the committed,
reviewed transcription and source metadata. Source locators cover the text in
the two PDFs and all 15 Word-table rows; one row contains two passages.
Paratext and illustration-only material are identified separately.

`CodeAndDocs/data/reviewed_records.tsv` is the committed transcription
baseline, with stable IDs, source locators and correction notes.
`texts.tsv` supplies TEXT metadata; `source_exclusions.tsv` identifies
paratext and illustration-only material. The source documents and original
recordings are identified by SHA-256 in `source_manifest.json`.

`reviewed_records.tsv` has 46 rows (15 for *Dingding*, 15 for *Kavatjes ni
vuvu*, 16 for *Maljialjian a qaciljay*). `source_exclusions.tsv` lists four
exclusions, two per PDF: the cover and the illustration-only odd pages 3-31
("contain no target-language prose"), and the page-32 paratext (title,
credits, publication metadata, rights notice and English legal text; all 15
Chinese story paragraphs are included). It is documentation: no build script
reads it.

`CodeAndDocs/repair_records.py` is a one-off migration that rewrote
`reviewed_records.tsv` (IDs, Word-table locators, the `S6a` ID and the
correction notes); it is not a build step and `generate_xml.sh` does not run it.

#### Steps, in the order `generate_xml.sh` runs them

1. **Set-up.** Locates the FormosanBank checkout (`FORMOSANBANK_ROOT`, default
   three folders above `CodeAndDocs/`), the Python interpreter (`PYTHON`,
   default `python3`) and a warnings folder (`QC_OUTPUT_DIR`, default a new
   temporary folder under `$TMPDIR` or `/tmp`). Makes a staging folder
   `CodeAndDocs/.build.XXXXXX`, deleted when the script exits, and stops if
   `QC/cleaning/clean_xml.py` is not found in the checkout.
2. **`CodeAndDocs/build_xml.py --output-dir <stage>/XML`.** Reads
   `data/reviewed_records.tsv` and stops if a (story, ID) pair repeats, if an
   ID differs from its `legacy_id`, if a Paiwan or Chinese cell is empty, if
   the stories in the transcription and in `data/texts.tsv` differ, or if a
   story has a repeated `sequence`. For each row of `texts.tsv` it writes one
   `<stage>/XML/Paiwan/<filename>` whose `TEXT` carries the id, `xml:lang`,
   `dialect`, citation, BibTeX citation, copyright, source and audio from that
   row. Sentences are written in `sequence` order; each `S` gets its ID, a
   `source` attribute (`<source file>: <Paiwan locator> (Paiwan); <Chinese
   locator> (Chinese)`), one `FORM kindOf="original"` and one
   `TRANSL xml:lang="zho"`. It writes no standard tier and no PHON.
3. **`QC/cleaning/clean_xml.py --corpora_path <stage>/XML --warnings_dir
   <QC_OUTPUT_DIR>`.** Shared cleaning of the original FORM and the TRANSL:
   non-breaking spaces to spaces, Unicode NFC, HTML-entity decoding, caret
   variants to `^`, full-width and typographic punctuation to ASCII in FORM,
   double-quote variants to the full-width `＂` in Chinese TRANSL, whitespace
   collapsing and repeated-punctuation trimming; it may also correct `'`
   versus `"` in the original FORM against the language's reference
   vocabulary (`QC/validation/reference/Paiwan/attestation.txt`). Warnings go
   to `<QC_OUTPUT_DIR>/cleaner_warnings.csv`. The log of any such quote
   corrections (`quote_corrections.csv`) is written inside the staging folder
   (`<stage>/CodeAndDocs/`), so it is deleted when the script exits.
4. **`QC/utilities/standardize.py --corpora_path <stage>/XML --copy`.** Adds
   `FORM kindOf="standard"` as an unchanged copy of the original FORM (no
   spelling conversion).
5. **`QC/utilities/add_phonology.py --corpora_path <stage>/XML --orthography
   Ortho94`.** Writes `PHON kindOf="original"` from the original FORM with the
   Ortho94 Paiwan table, and `PHON kindOf="standard"` from the standard FORM
   with Paiwan's registered standard orthography (Ortho113, per
   `standards.csv`), both using the Eastern column.
6. **Publish.** Copies the staged `XML/` over `Corpora/Paiwan_Stories/XML/`
   with `rsync -a --delete`, so files no longer generated are removed.
7. **Provenance.** If the FormosanBank checkout is a git checkout, writes its
   current commit to `CodeAndDocs/provenance.json`; otherwise it requires that
   file to exist already. Prints the warnings folder and exits.
