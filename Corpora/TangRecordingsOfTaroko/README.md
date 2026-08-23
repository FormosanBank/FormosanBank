# Tang Recordings of Taroko

## License and AI use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI use is prohibited without prior written permission.

The published source license is CC BY-NC 4.0. Prof. Apay Tang gave FormosanBank permission to use these PARADISEC recordings.

## Source and contents

The source is the [PARADISEC AIT1 collection](https://catalog.paradisec.org.au/collections/AIT1), items `AIT1-001` through `AIT1-004`. The corpus contains 30 untranscribed Truku recordings totaling 76,976.624 seconds, or 21.382396 hours.

Use the project-approved corpus citation:

> Apay Tang (collector), Apay Tang (recorder), 1997. traditional Truku stories. MPEG/WAV/PDF. AIT1-001 at catalog.paradisec.org.au. https://dx.doi.org/10.4225/72/56EC22110B85A

Each XML file also contains its PARADISEC item-specific citation and DOI.

## Audio and identifiers

The source dataset is pinned to an immutable Hugging Face revision recorded in the manifest. Its 30 source WAV files are signed 16-bit PCM, 44.1 kHz, stereo. The recorded preparation decision converts each file to signed 16-bit PCM, 16 kHz, mono with ffmpeg 8.0.1. `CodeAndDocs/audio_manifest.json` pins the source and prepared byte sizes, SHA-256 values, frames, durations, and exact ffmpeg arguments.

The downloader performs this verified conversion automatically:

```bash
Corpora/TangRecordingsOfTaroko/download_audio_data.sh
```

The 30 stable `AIT1-*` TEXT IDs and matching AUDIO filenames are preserved under POL-037. No FORM, TRANSL, PHON, W, or M tier is invented for these untranscribed recordings.

## Reproduction and QC

The four source metadata records, complete audio manifest, generator, verifier, and tests are under `CodeAndDocs/`. Reproduce all 30 XML files with:

```bash
PYTHON=python3 Corpora/TangRecordingsOfTaroko/CodeAndDocs/reproduce.sh
```

Verify the source inventory against the pinned public revision with:

```bash
python3 Corpora/TangRecordingsOfTaroko/CodeAndDocs/verify_sources.py --live
```

Run the focused pipeline tests with:

```bash
python3 -m unittest discover \
  -s Corpora/TangRecordingsOfTaroko/CodeAndDocs/tests -v
```

The private reconciliation completed audit and canonical QC on 2026-08-23 using FormosanBank tooling commit `3a3c47c220520113f747e6a2d441494000e13c4b`. Two complete source downloads and conversions produced identical prepared identities. XML regeneration is deterministic and byte-identical to the published identifiers and metadata. All applicable corpus validators report zero HARD findings, and all 30 prepared files pass silence-aware audio validation.
