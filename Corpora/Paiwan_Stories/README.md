# Paiwan Stories

Three Eastern Paiwan stories with Chinese translations: *Dingding*,
*Kavatjes ni vuvu* and *Maljialjian a qaciljay*. The corpus contains 46
bilingual passages, with whole-story audio and no word or morpheme analysis.

## Rights

**License:** CC BY-NC 4.0

**Rights source:** Gesi Giling (阮翠芳), 2024-04-13; evidence: ask maintainer

Joshua Hartshorne recorded permission directly from the Indigenous-text
author. The illustrated books also carry separate illustration, adaptation
and publisher rights. Full source documents are not redistributed here.
The central FormosanBank terms and AI-use addendum also apply.

## Sources and reproduction

The two illustrated PDFs credit Gesi Giling for the Indigenous text and
Tjaiwan Giling for illustrations; both colophons date their first printing
to November 2020. The third source is a bilingual Word document.

`CodeAndDocs/data/reviewed_records.tsv` is the committed transcription
baseline, with stable IDs, source locators and correction notes.
`texts.tsv` supplies TEXT metadata; `source_exclusions.tsv` identifies
paratext and illustration-only material. The source documents and original
recordings are identified by SHA-256 in `source_manifest.json`.

The build reconstructs XML from this transcription, without fetching or
re-extracting the restricted documents. With current FormosanBank dependencies:

```bash
FORMOSANBANK_ROOT=/path/to/FormosanBank PYTHON=python3 ./CodeAndDocs/generate_xml.sh
python3 -m unittest discover -s CodeAndDocs/tests -v
```

Inside `Corpora/Paiwan_Stories`, the shared checkout is found automatically.
The build generates fresh source tiers, runs shared cleaning, copies original
FORM to standard with `standardize.py --copy`, and derives PHON with Ortho94
for originals and the registered standard for standard FORM. Ortho94 and
Ortho113 Eastern values agree for this corpus's letters. Actual build tools
are recorded in [provenance.json](CodeAndDocs/provenance.json), without a tools pin.
QC is separate from generation. Set `QC_OUTPUT_DIR` to retain build warnings.

## Audio

`./download_audio_data.sh` retrieves the three published WAVs into ignored
`Audio/`, using the revision in FormosanBank's `audio_sources.json`.
Use `--dry-run` to check the remote inventory without downloading.
The recordings retain their published 16 kHz mono representation; no
resampling or channel conversion is performed. Each TEXT names its whole-story
recording. Sentence timings are not included.

## Notes and Issues

The restored Maljialjian passage uses `S6a`, between the existing S6 and S7;
all published TEXT and sentence IDs remain stable. Chinese translations
omitted or shifted in the earlier corpus are restored from the sources.
Published quotation corrections and comma/exclamation typography are retained
in the transcription; `repair_records.py` records the ID and locator repair.
The Word source has 15 table rows containing 16 passages; row 4 holds two units.
Historical alignment files are unavailable, so no sentence timings are inferred.
