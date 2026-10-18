# Tang Recordings of Taroko

These audio files were collected by Prof. Apay Tang, a member of the Truku tribe and a prominent preservationist and revitalizationist in the community. While permanently archived at Paradisec, Prof. Tang graciously agreed to include the audio in FormosanBank. None of the audio are transcribed. There is slightly more meta-data at Paradisec, but not much.

## Languages and dialects

- **Language:** Seediq/Truku, ISO 639-3 `trv`
- **Dialect:** Truku

All 30 XML files under `XML/Truku/` declare the same values on `<TEXT>`: `xml:lang="trv"` and `dialect="Truku"`. (`trv` covers both Seediq and Truku; the `dialect="Truku"` attribute is what identifies these recordings as Truku.)

## Source

Thirty untranscribed recordings from PARADISEC items `AIT1-001` through `AIT1-004`, about 21.4 hours. Each file under `XML/Truku/` contains one stable `AIT1-*` TEXT and its AUDIO reference, with `xml:lang="trv"` and `dialect="Truku"`. No transcription, translation, gloss or pronunciation tier is invented.

The four PARADISEC items, as the committed metadata in `CodeAndDocs/Metadata/` describes them:

| Item | Title (as catalogued) | Recorded (`originatedOn`) | WAV recordings |
| --- | --- | --- | --- |
| `AIT1-001` | traditional Truku stories | 1997-10-01 | 1 |
| `AIT1-002` | daily stories | 1997-10-02 | 1 |
| `AIT1-003` | Daily and traditional stories | 1997-10-02 | 1 |
| `AIT1-004` | Tama visitation | 1998-01-02 | 27 |

- **Basecamp card:** [8253692022](https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/8253692022)

#### Audio

The published audio is pinned by identity: `CodeAndDocs/audio_manifest.json` records the byte size and SHA-256 of all 30 recordings against an immutable Hugging Face revision. `CodeAndDocs/verify_sources.py --live` checks the hosted identities without downloading 13.6 GB; `--local` hashes downloaded files. The downloader preserves the original 44.1 kHz stereo WAVs and verifies their bytes. It does not resample or upload audio.

```bash
./download_audio_data.sh --dry-run
./download_audio_data.sh
python3 CodeAndDocs/verify_sources.py --live
python3 CodeAndDocs/verify_sources.py --local
```

For a private checkout, keep `FORMOSANBANK_ROOT` set as above. Downloading needs the shared FormosanBank Python dependencies. The wrapper uses the shared audio contract and parity helpers with this repository's `Audio/` destination; the shared download CLI otherwise targets the published checkout. It preserves the original 44.1 kHz stereo WAVs and verifies their size and SHA-256. It does not resample or upload audio.

The default verifier checks the manifest against the committed metadata and the downloader's pin. `--live` compares the pinned remote WAV paths, sizes and LFS SHA-256 object IDs without downloading the recordings. `--local` hashes every named local WAV. Remote listing checks do not independently verify PARADISEC or read the full audio contents.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/TangRecordingsOfTaroko_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

> Tang, Apay. (1997). Traditional Truku stories. Paradisec. https://dx.doi.org/10.4225/72/56EC22110B85A

Each XML file carries its item-specific citation and BibTeX value from the committed `creditText`.

## License

**License:** CC BY-NC 4.0

**Rights source:** Prof. Apay Tang, 2025-05-04; evidence: ask maintainer

Prof. Tang granted FormosanBank permission to include these Truku recordings, permanently archived in the PARADISEC AIT1 collection. Prof. Apay Tang granted FormosanBank permission to publish these recordings on 4 May 2025.

The earlier XML value `CC BY-NC` means 4.0 under POL-042; spelling out the version retains the published licence. The value was written `CC BY-NC` until September 2026; an unversioned Creative Commons value means 4.0, so spelling out the version restates the same licence rather than changing it.

The central [FormosanBank terms](https://github.com/FormosanBank/FormosanBank/blob/main/LICENSE.md) and [AI Use Addendum](https://github.com/FormosanBank/FormosanBank/blob/main/AI-USE-ADDENDUM.md) also apply.

## Notes and caveats

The committed metadata extracts are not independently checked against Paradisec. Joshua accepted this limit for the closed AIT1 deposit, recorded in 1997 and 1998 and published in 2016, in [FormosanBank #197](https://github.com/FormosanBank/FormosanBank/pull/197). The extracts enumerate 61 source files and archival fields absent from our XML, and have been unchanged since the corpus's first commit. The 30 matching MP3s are treated as delivery copies of the WAV masters; the remaining file, `AIT1-001-2df.pdf`, has not been inspected or included.

Joshua accepted two source limits on 2026-09-07 in [#197](https://github.com/FormosanBank/FormosanBank/pull/197): the 30 matching MP3s are treated as delivery copies of the WAV masters, and no metadata refresh mechanism is required for this closed archival deposit. Reproduction does not independently verify the extract against PARADISEC. The remaining source part, `AIT1-001-2df.pdf`, has not been inspected or included.

The recordings are untranscribed. Metadata provenance and MP3/WAV equivalence retain the accepted limits described above; the source PDF remains uninspected. The source verifier is corpus-specific, and its remote listing is suitable for this 30-WAV inventory rather than a general large-dataset audit.

The four metadata files are flattened extracts wrapped as `{"metadata": {...}}`, not complete RO-Crates. They contain 61 source parts and archival fields absent from our XML, and have been unchanged since the corpus's first commit. The XML follows from those extracts plus the separately granted licence. Unresolved graph references, including the extract's licence pointer, do not supply additional rights evidence.

Remote audio verification compares paths, sizes and hosted SHA-256 object IDs. It does not listen to the recordings or independently verify Paradisec. The verifier covers this 30-WAV inventory; it is not a general audit tool for larger datasets. If local hashes differ, move those copies aside before downloading and checking again.

If local verification fails, move the differing copies aside before downloading and checking again. Earlier private builds produced 16 kHz mono derivatives; those must not be mistaken for the originals. Any future ASR derivative needs its own reviewed output, as Joshua specified in [#168](https://github.com/FormosanBank/FormosanBank/pull/168#issuecomment-5565082860). Authorized uploads use the shared `QC/utilities/upload_to_hf.py`, after source-byte verification.

## Reproduction and processing

### How to reproduce

Python 3.9 or later is sufficient for the build. From a FormosanBank checkout, run:

```bash
Corpora/TangRecordingsOfTaroko/CodeAndDocs/generate_xml.sh
```

From this private repository, select the current FormosanBank checkout explicitly:

```bash
export FORMOSANBANK_ROOT=/path/to/FormosanBank
./CodeAndDocs/generate_xml.sh
```

This rebuilds all 30 XML files from the four committed metadata extracts without downloading audio. The build reads only the four committed metadata extracts and writes all 30 XML files. Audio, credentials and source downloads are not inputs. A second build must reproduce the same XML.

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools). The actual tools commit is recorded in [CodeAndDocs/provenance.json](CodeAndDocs/provenance.json); it records the build and never selects or requires an older checkout. The build's FormosanBank commit is recorded in [`CodeAndDocs/provenance.json`](CodeAndDocs/provenance.json); it does not select an older checkout. A Git-free export retains that provenance record. A Git-free export retains that record.

**POL-047 deviation:** Only source-to-XML generation runs. These recordings have no text tiers or recorded manual edits, so manual-edit application, cleaning, standardization and phonology have nothing to act on. Verification stays outside the build. These untranscribed recordings have no text tiers or manual edits, so only source-to-XML generation applies. Audio verification runs separately from the build.

#### Files in `CodeAndDocs/`

- `CodeAndDocs/Metadata/`: four unchanged source metadata extracts.
- `CodeAndDocs/generate_xml.sh`: the XML build entry point.
- `CodeAndDocs/make_xml.py`: writes the XML (called by `generate_xml.sh`).
- `CodeAndDocs/audio_manifest.json`: sizes and SHA-256 hashes of all 30 original WAVs at an immutable Hugging Face revision.
- `CodeAndDocs/verify_sources.py`: separate metadata, remote-identity and local-byte checks.
- `CodeAndDocs/tests/test_audio_manifest.py`: unit tests for the manifest and verifier checks.

#### Checks (run separately; not part of the build)

```bash
python3 -m unittest discover -s CodeAndDocs/tests -v
python3 CodeAndDocs/verify_sources.py --live
```

Run the current FormosanBank XML, text, dialect, registry, audio-parity and port-readiness checks separately from generation. Text orthography and gloss checks are inapplicable because there are no text tiers. Local acoustic validation requires the original WAVs.

### What each step does

`generate_xml.sh` runs two steps, in this order. Neither downloads audio or reads the network.

0. **Setup.** The script finds its own folder (`CodeAndDocs/`), takes the FormosanBank root from `FORMOSANBANK_ROOT` if set and otherwise from three levels up (the repository root), uses `$PYTHON` if set and otherwise `python3`, and sets `PYTHONDONTWRITEBYTECODE=1` so no `__pycache__` is left behind. It stops at the first failing command (`set -euo pipefail`).

1. **`make_xml.py` (no flags).**
   - *Reads* the four files `CodeAndDocs/Metadata/*-ro-crate-metadata.json`. Each is a flattened extract wrapped as `{"metadata": {...}}`; the item id (`AIT1-001` …) is taken from the first two dash-separated parts of the file name.
   - *Decides which recordings exist:* every `hasPart` entry whose `@id` ends in `.wav` is a recording. That gives 30 (1 + 1 + 1 + 27). The 30 MP3s and the one PDF in `hasPart` are not used. If no recording is found, the script stops.
   - *Refuses stale output:* if `XML/Truku/` already holds an `.xml` file whose name does not match one of the 30 WAVs, the script stops and names it rather than deleting anything.
   - *Writes* one file per WAV, `XML/Truku/<WAV name without .wav>.xml`, overwriting any previous copy. Each contains a single `<TEXT>` with `id` (the WAV stem, e.g. `AIT1-004-10A`), `xml:lang="trv"`, `dialect="Truku"`, `audio` (the WAV file name), `source` (the item's PARADISEC catalogue URL, e.g. `https://catalog.paradisec.org.au/repository/AIT1/004`), `copyright="CC BY-NC 4.0"` (a constant in the script, because the extract's `license` field only points at a node the extract does not include), and `citation` and `BibTeX_citation`. Inside the TEXT is one `<AUDIO file="<WAV name>"/>` with no start or end times. There are no `S`, `FORM`, `TRANSL` or `W` elements.
   - *Citation formatting:* from the item's `creditText` (e.g. `Apay Tang (collector), Apay Tang (recorder), 1997. traditional Truku stories. MPEG/WAV/PDF. AIT1-001 at catalog.paradisec.org.au. https://dx.doi.org/10.4225/72/56EC22110B85A`) it takes the distinct names marked with a role, inverted to "Last, First"; the first four-digit year; the text between the year and the next full stop, with its first letter capitalised; and the URL. The result is `Tang, Apay. (1997). Traditional Truku stories. Paradisec. https://dx.doi.org/10.4225/72/56EC22110B85A`. The BibTeX entry is an `@misc` built from the same parts, with key = first author's surname + year + first title word (e.g. `tang1997traditional`).

2. **Provenance record (inline Python in `generate_xml.sh`).** If the FormosanBank root is a git checkout, it writes that checkout's current commit (`git rev-parse HEAD`) to [CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) as `{"formosanbank_commit": ...}`. If it is not a git checkout (a Git-free export), it keeps the existing `provenance.json` and stops with an error if that file is missing.

Not run by the build: `verify_sources.py`, the unit tests and `download_audio_data.sh`. When run, `download_audio_data.sh` first checks the manifest against the committed metadata, checks that it pins the same Hugging Face repository, revision and file count (30) as the `TangRecordingsOfTaroko` entry in the shared `audio_sources.json`, and compares the remote sizes and SHA-256 IDs (`verify_sources.py --live` logic); then runs the shared `QC/validation/validate_hf_audio.py` online parity check. With `--dry-run` it stops there. Otherwise it downloads the pinned revision into `Audio/`, runs the shared local parity check, and hashes every WAV in `Audio/Truku/` against the manifest.
