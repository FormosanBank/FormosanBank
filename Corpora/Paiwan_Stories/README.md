# Paiwan Stories

Three Eastern Paiwan stories with Chinese translations and whole-story audio:

- `Dingding`
- `Kavatjes ni vuvu`
- `Maljialjian a qaciljay`

## License and AI use

The author granted FormosanBank direct CC BY-NC permission for the Indigenous-language text. The corpus is also subject to the central terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI use is prohibited without prior written permission.

The illustrated source documents contain separate rights notices for illustrations, adaptation, and publication. Those documents and their redundant MP3 files were used for a private source audit but are not distributed here.

## Contents

- 3 XML files
- 46 reviewed sentence records
- 46 source-owned original Paiwan forms
- 46 source-owned original Chinese translations
- 3 whole-story WAV recordings available through the public audio contract

The reviewed data restore one complete bilingual sentence omitted from the legacy `Maljialjian` XML. They also repair omitted or shifted Chinese translations in `Kavatjes` and `Maljialjian`.

## Source authority and scope

The published XML comes from reviewed private development revision `9a7eafb186de`. All 66 pages in the two illustrated PDFs and bilingual Word source were reviewed. The source ledger retains 46 bilingual records and documents four paratext or illustration-only exclusions.

`CodeAndDocs/data/reviewed_records.tsv` is the public, page-addressed source transcription used by the generator. `source_ledger.csv` records every retained and excluded item. `source_manifest.json` pins the six private audit inputs and the three published recordings by filename, size, and SHA-256 without distributing the restricted source files.

## Reproduce

From this corpus directory, use a current FormosanBank Python environment:

```bash
PYTHON=/path/to/FormosanBank/.venv/bin/python ./CodeAndDocs/make_xml.sh
```

The build regenerates the three original-tier XML files from the reviewed records, applies the shared cleaner, creates standard forms with `standardize.py --copy`, generates original and standard phonology with the reviewed Paiwan Ortho94 profile, and runs structural validation. Repeated builds are byte-identical.

## Audio

Audio is not committed to Git. Download the three pinned public recordings with:

```bash
./download_audio_data.sh
```

The XML roots reference `DingDing.wav`, `kavatjes_ni_vuvu.wav`, and `maljialjian_a_qaciljay.wav`. The public Hugging Face copies are byte-identical to the reviewed development WAV files.

## Validation status

The 2026-08-22 current-authority review passed source coverage, 8 repository tests, XML, text, gloss, duplicate, audio, dialect, orthography, vocabulary, registry, and port-readiness checks. It adjudicated 51 expected soft findings with none unresolved and reported 0 hard findings and 0 warnings for port readiness.

The 46 V060 gloss findings are expected because these narrative sources contain no source-supported word or morpheme analysis.

## Citation

Juan, T. F., and X. Ruan. 2024. *Corpus of Paiwan Stories*. Electronic resource.
