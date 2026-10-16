# Tang Recordings of Taroko

## Rights

**License:** CC BY-NC 4.0

**Rights source:** Prof. Apay Tang, 2025-05-04; evidence: ask maintainer

These audio files were collected by Prof. Apay Tang, a member of the Truku tribe and a prominent preservationist and revitalizationist in the community. While permanently archived at Paradisec, Prof. Tang graciously agreed to include the audio in FormosanBank.

The published `TEXT/@copyright` read `CC BY-NC` until 2026-09. POL-042 reads an unversioned Creative Commons value as 4.0 and requires the exact `rights_vocabulary.csv` spelling, so writing out the version restates the same licence rather than changing it.

This corpus is also subject to the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

***

## Contents

None of the audio are transcribed. There is slightly more meta-data at Paradisec, but not much.

30 recordings from Paradisec items `AIT1-001` through `AIT1-004`, all Truku (`xml:lang="trv"`, `dialect="Truku"`). Each XML file is a single `TEXT` carrying the recording's identifier, Paradisec source URL, citation and `AUDIO` reference — and nothing else. The source has no transcription, so no `FORM`, `PHON`, `TRANSL`, `W` or `M` tier is invented for it.

- `XML/Truku/` — the published XML, one file per recording
- `Audio/Truku/` — the WAV recordings (gitignored; fetched by `download_audio_data.sh`)
- `CodeAndDocs/Metadata/` — an extract of the Paradisec item metadata, one file per collection item (see Reproduction)
- `CodeAndDocs/generate_xml.sh` — the build entry point
- `CodeAndDocs/make_xml.py` — writes the XML from that metadata
- `CodeAndDocs/provenance.json` — the FormosanBank commit the published XML was built against
- `CodeAndDocs/upload_hf_datasets.sh` — uploads `Audio/` to the Hugging Face dataset repo
- `download_audio_data.sh` — downloads `Audio/` from the Hugging Face dataset repo

***

## Reproduction

```bash
Corpora/TangRecordingsOfTaroko/CodeAndDocs/generate_xml.sh
```

Rewrites all 30 files in `XML/Truku/` and leaves `git status` empty.

**The audio is not an input.** Every recording is enumerated by the Paradisec item metadata committed under `CodeAndDocs/Metadata/`, so the corpus rebuilds from a FormosanBank checkout alone (POL-048) without downloading a single WAV.

**What that metadata is.** The four files are an *extract*, not the archive's own RO-Crate. Each is a single flattened entity wrapped as `{"metadata": {…}}`, with no `@context` and no `@graph`, so every reference inside — `license`, `publisher`, `collector`, `root` — points at a node that was not kept. One consequence matters for rights: the corpus's licence is **not** derivable from its committed source (`license` is `{"@id": "#license-3-a6e13b67"}`, which resolves to nothing), which is why the licence is stated in the Rights block above and set as a constant in `make_xml.py` rather than read from the extract.

**It is upstream material, not our own output fed back in.** A committed extract that the build treats as source invites the question of whether the published XML was quietly laundered into it. It was not, and the check is easy to repeat. The extract enumerates **61 parts — 30 MP3, 30 WAV and one PDF** — where this corpus publishes only the 30 WAVs (see *What the item holds that we do not* below); it carries a dozen fields the XML has no slot for (`dateCreated 2008-09-20`, `datePublished 2016-03-19`, `originatedOn 1997-10-01`, `originalMedia "audio casssette"` — the archive's own typo, `contentLocation "Siyu-Lin, Hualien"`, `languageGenre "narrative"`); and it holds RO-Crate graph fragments such as `#license-3-a6e13b67` and `#place-Siyu-Lin, Hualien` that mean nothing outside a crate. The information runs one way only: everything in the XML is derivable from the extract plus the licence constant, and nothing in the extract is derivable from the XML. The four files have also been byte-identical since the corpus's first commit (2026-03-23) and no script in this repository writes them — `make_xml.py` only reads.

### What the item holds that we do not

The AIT1 items contain 61 files; FormosanBank publishes 30. The 30 MP3s pair **exactly one-to-one** with the 30 WAVs — every stem has one of each, with no MP3 that lacks a WAV — which is Paradisec's usual deposit shape: an archival master plus a delivery copy. Nothing committed here proves it — the extract's `hasPart` entries are bare `@id` strings carrying no format, size or duration — and it is accepted as the working assumption rather than left open (maintainer, 2026-09-07). The circumstantial case is strong: `originalMedia` is `"audio casssette"`, the stems run `1A`/`1B`, `2A`/`2B` — cassette sides — and `AIT1-001-1.wav` is 658,178,448 bytes, about 62 minutes at 44.1 kHz/16-bit/stereo, which is one full side. **FormosanBank holds the masters, not the derivatives**, which is the right way round.

The one non-audio part, `AIT1-001-2df.pdf`, is held in no form here. It may be what the corpus description means by *"slightly more meta-data at Paradisec, but not much"*; nobody has checked.

***

### Known deviation: the source cannot be verified from this repository

There is **no `refresh_source.sh`**, no committed hash of the extract, and nothing that checks it against the Paradisec catalogue. The extract is the only witness to Paradisec that FormosanBank holds, and a reader cannot confirm from here that it faithfully represents the archive's records.

This is accepted deliberately (maintainer, 2026-09-07). The AIT1 deposit is a **closed archival item** — recorded in 1997, deposited and published in 2016, and not going to change — so a refresh path would add fetching machinery without adding assurance: re-downloading an immutable record only tells you it is still the record you already have. POL-047 makes `refresh_source.sh` optional, *"only where the source can be re-fetched"* to useful effect; this is a case where it cannot.

What this does mean, stated plainly so it is not discovered later: the reproduction guarantee here is **"the published XML follows from the committed extract"**, not **"the committed extract follows from Paradisec."** The second link rests on the 2026-03 deposit and on the archive's permanence, not on anything mechanical.

**POL-047 deviation, deliberate.** `generate_xml.sh` runs step 1 only. Steps 2–5 — `apply_manual_edits.py`, `clean_xml.py`, `standardize.py`, `add_phonology.py` — have nothing to act on, because the XML carries no text tier to clean, standardize or phonologize, and the corpus has no recorded manual edits.

The commit the published XML was built against is recorded in [CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052). Rebuild with the current tools: the recorded commit exists to make an unexpected diff readable, not to pin the build. Here it should never matter — the build calls no shared QC utility.

***

## Audio

```bash
Corpora/TangRecordingsOfTaroko/download_audio_data.sh
```

Fetches the 30 recordings from the Hugging Face revision pinned in [audio_sources.json](../../audio_sources.json). Strict reproduction from Paradisec itself is possible but requires the collection's access paperwork, which would put unnecessary work on everyone downstream; the Hugging Face copy is the same audio.

***

## Citation

If you use this corpus, cite FormosanBank and:

> Tang, Apay. (1997). Traditional Truku stories. Paradisec. https://dx.doi.org/10.4225/72/56EC22110B85A

Each XML file also carries its own item-specific `citation` and `BibTeX_citation`.
