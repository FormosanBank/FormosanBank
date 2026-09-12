# Tang Recordings of Taroko

**Basecamp card:** [8253692022](https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/8253692022)

## Rights

**License:** CC BY-NC 4.0

**Rights source:** Prof. Apay Tang, 2025-05-04; evidence: ask maintainer

Prof. Tang granted FormosanBank permission to include these Truku recordings, permanently archived in the PARADISEC AIT1 collection. The earlier XML value `CC BY-NC` means 4.0 under POL-042; spelling out the version retains the published licence.

The central [FormosanBank terms](https://github.com/FormosanBank/FormosanBank/blob/main/LICENSE.md) and [AI Use Addendum](https://github.com/FormosanBank/FormosanBank/blob/main/AI-USE-ADDENDUM.md) also apply.

## Contents

Thirty untranscribed recordings from PARADISEC items `AIT1-001` through `AIT1-004`, about 21.4 hours. Each file under `XML/Truku/` contains one stable `AIT1-*` TEXT and its AUDIO reference, with `xml:lang="trv"` and `dialect="Truku"`. No transcription, translation, gloss or pronunciation tier is invented.

- `CodeAndDocs/Metadata/`: four unchanged source metadata extracts.
- `CodeAndDocs/generate_xml.sh`: the XML build entry point.
- `CodeAndDocs/audio_manifest.json`: sizes and SHA-256 hashes of all 30 original WAVs at an immutable Hugging Face revision.
- `CodeAndDocs/verify_sources.py`: separate metadata, remote-identity and local-byte checks.

## Reproduction

Python 3.9 or later is sufficient for the build. From a FormosanBank checkout:

```bash
Corpora/TangRecordingsOfTaroko/CodeAndDocs/generate_xml.sh
```

From this private repository, select the current FormosanBank checkout explicitly:

```bash
export FORMOSANBANK_ROOT=/path/to/FormosanBank
./CodeAndDocs/generate_xml.sh
```

The build reads only the four committed metadata extracts and writes all 30 XML files. Audio, credentials and source downloads are not inputs. A second build must reproduce the same XML. The actual tools commit is recorded in [CodeAndDocs/provenance.json](CodeAndDocs/provenance.json); it records the build and never selects or requires an older checkout. A Git-free export retains that provenance record.

**POL-047 deviation:** Only source-to-XML generation runs. These recordings have no text tiers or recorded manual edits, so manual-edit application, cleaning, standardization and phonology have nothing to act on. Verification stays outside the build.

The four metadata files are flattened extracts wrapped as `{"metadata": {...}}`, not complete RO-Crates. They contain 61 source parts and archival fields absent from our XML, and have been unchanged since the corpus's first commit. The XML follows from those extracts plus the separately granted licence. Unresolved graph references, including the extract's licence pointer, do not supply additional rights evidence.

Joshua accepted two source limits on 2026-09-07 in [#197](https://github.com/FormosanBank/FormosanBank/pull/197): the 30 matching MP3s are treated as delivery copies of the WAV masters, and no metadata refresh mechanism is required for this closed archival deposit. Reproduction does not independently verify the extract against PARADISEC. The remaining source part, `AIT1-001-2df.pdf`, has not been inspected or included.

## Audio

```bash
./download_audio_data.sh --dry-run
./download_audio_data.sh
python3 CodeAndDocs/verify_sources.py --live
python3 CodeAndDocs/verify_sources.py --local
```

For a private checkout, keep `FORMOSANBANK_ROOT` set as above. Downloading needs the shared FormosanBank Python dependencies. The wrapper uses the shared audio contract and parity helpers with this repository's `Audio/` destination; the shared download CLI otherwise targets the published checkout. It preserves the original 44.1 kHz stereo WAVs and verifies their size and SHA-256. It does not resample or upload audio.

The default verifier checks the manifest against the committed metadata and the downloader's pin. `--live` compares the pinned remote WAV paths, sizes and LFS SHA-256 object IDs without downloading the recordings. `--local` hashes every named local WAV. Remote listing checks do not independently verify PARADISEC or read the full audio contents.

If local verification fails, move the differing copies aside before downloading and checking again. Earlier private builds produced 16 kHz mono derivatives; those must not be mistaken for the originals. Any future ASR derivative needs its own reviewed output, as Joshua specified in [#168](https://github.com/FormosanBank/FormosanBank/pull/168#issuecomment-5565082860). Authorized uploads use the shared `QC/utilities/upload_to_hf.py`, after source-byte verification.

## Notes and Issues

The recordings are untranscribed. Metadata provenance and MP3/WAV equivalence retain the accepted limits described above; the source PDF remains uninspected. The source verifier is corpus-specific, and its remote listing is suitable for this 30-WAV inventory rather than a general large-dataset audit.

## Validation

```bash
python3 -m unittest discover -s CodeAndDocs/tests -v
python3 CodeAndDocs/verify_sources.py --live
```

Run the current FormosanBank XML, text, dialect, registry, audio-parity and port-readiness checks separately from generation. Text orthography and gloss checks are inapplicable because there are no text tiers. Local acoustic validation requires the original WAVs.

## Citation

Cite FormosanBank and:

> Tang, Apay. (1997). Traditional Truku stories. Paradisec. https://dx.doi.org/10.4225/72/56EC22110B85A

Each XML file carries its item-specific citation and BibTeX value from the committed `creditText`.
