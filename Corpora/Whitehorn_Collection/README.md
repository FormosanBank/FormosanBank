# Whitehorn Collection

Audio recordings, many of them songs, that John Whitehorn contributed to the World
Oral Literature project, published here as 87 untranscribed records: one XML
file per recording, holding its metadata and a link to its audio, with no text.

## Languages and dialects

They are mostly Paiwan but also some Atayal, Seediq, and Amis.

The XML declares these languages and dialects (`xml:lang` and `dialect` on each
file's `TEXT`):

| Folder | `xml:lang` | `dialect` | Files |
| --- | --- | --- | --- |
| `XML/Paiwan/` | `pwn` (Paiwan) | `unknown` | 80 |
| `XML/Paiwan/` | `pwn` (Paiwan) | `Southern` | 2 (`Whitehorn_Paiwan_01A_4.xml`, `Whitehorn_Paiwan_02A_2.xml`) |
| `XML/Atayal/` | `tay` (Atayal) | `unknown` | 3 |
| `XML/Amis/` | `ami` (Amis) | `unknown` | 1 |
| `XML/Seediq/` | `trv` (Seediq) | `unknown` | 1 |

For all but the two Southern Paiwan recordings, the source does not record a
dialect FormosanBank recognises. See "Notes and caveats" for the 46 Paiwan
recordings Whitehorn labels "north-west". The one `trv` file has `dialect="unknown"`, which FormosanBank reads as
Seediq, not Truku.

## Source

These are audio recordings contributed by John Whitehorn to the World Oral
Literature project: https://www.repository.cam.ac.uk/collections/1240188b-2f4c-401e-9372-58177440d9c6.

The recordings are not transcribed, and many are songs.

Each XML file's `source` attribute quotes the repository's description of the
recording, and every one of those descriptions gives a recording date as free
text (for example "Recorded in Dec 1965", "Recorded in 1950s"): 35 of the 87
records say 1954 or the 1950s, 27 a year from 1964 to 1969, 16 say 1970, and 9
give both 1967 and 1970. Dates are also available in the PDFs (found in the
repository); there is no separate date field in the XML.

`CodeAndDocs/` holds 71 PDFs of the repository's accession forms (Whitehorn's
notes), one folder per tape side.

**Audio.** Every XML file has one `AUDIO` element naming its audio file. The
audio is not in this repository: it is on Hugging Face
(`FormosanBank/Whitehorn_Collection`) and is downloaded by
[download_audio_data.sh](download_audio_data.sh) (see "Reproduction and
processing"). That dataset holds 89 audio files: the 87 the XML names, plus two
declared extras listed in [audio_extras.json](../../audio_extras.json)
(`Paiwan/Whitehorn_Paiwan_03A_01.mp3` and
`Paiwan/hymns_of_praise_side_b_whitehorn.wav`).

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Whitehorn_Collection_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

* Whitehorn, J. (n.d.). The Whitehorn Collections. World Oral Literature Project. Retrieved February 24, 2025, from https://www.repository.cam.ac.uk/collections/1240188b-2f4c-401e-9372-58177440d9c6 and https://www.repository.cam.ac.uk/collections/dc1f2cd8-36da-48e1-979b-fe478eff6a91

## License

CC BY-NC 4.0

This is the `copyright` value on all 87 XML files. The audio carries the same
licence (the `whitehorn-cambridge` entry in
[audio_permissions.json](../../audio_permissions.json)).

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

## Notes and caveats

* Recording quality is about what you would expect, given the age.
* The recordings are not transcribed, so each XML file carries record-level metadata and an audio link, with no sentence tiers.
* Whitehorn labels 46 of the Paiwan recordings "north-west", written variously as `(NW)`, `(? NW)`, `(north-west)` and `(north-west dialect)`. Northwest is not one of FormosanBank's Paiwan dialects, so those records carry `dialect="unknown"` rather than being mapped onto Northern. Only two recordings state a dialect FormosanBank recognises, and both are Southern Paiwan.
* One tape has no XML record. The accession form for `Whitehorn_Paiwan_03A_01` describes a BBC Radio 3 broadcast from February 1993, *Songs to help the crops grow* — eight chants assigned by item number to Bunun (nos. 1, 2, 3, 5, 6), Amis (nos. 4, 8) and Atayal (no. 7) — but gives times for the tape side only as a whole, `00.00` to `c.19.00`. Without per-track times it cannot be split into one record per language, so the released master is published as an audio extra only. Those Bunun chants are the only Bunun material in the collection.

#### One tape has no XML record

The accession form `Whitehorn_Paiwan_03A_01` (tape 2010.3, side 1) describes a
BBC Radio 3 broadcast from February 1993, *Songs to help the crops grow*: eight
chants from Taiwan with English commentaries. The form assigns the chants to
three languages by item number — Bunun (nos. 1, 2, 3, 5, 6), Amis (nos. 4, 8)
and Atayal (no. 7) — but gives times for the tape side only as a whole,
`00.00` to `c.19.00`. Every other tape side in the collection carries per-track
start and stop times, which is what allows it to be split into separate `TEXT`
records, one language each. This one gives no times for the individual chants,
so it cannot be split without listening to the recording.

There is therefore no XML record for this tape, and the Bunun chants on it are
the only Bunun material anywhere in the collection. The released master audio
remains available as a declared extra
(`Paiwan/Whitehorn_Paiwan_03A_01.mp3` in [audio_extras.json](../../audio_extras.json)).

## Reproduction and processing

### How to reproduce

The XMLs were compiled by hand, so aren't entirely reproducible. However, since they just contain the names of the audio files and the associated language, there's not much to reproduce.

There is no `CodeAndDocs/generate_xml.sh` and no build script of any kind
(`CodeAndDocs/` holds only the accession-form PDFs and an empty
`requirements.txt`). This corpus is listed in `generate_xml_pending.txt` and in
`provenance_pending.txt` at the repository root, so it has no
`CodeAndDocs/provenance.json` either.

The one script is the audio download:

```bash
bash Corpora/Whitehorn_Collection/download_audio_data.sh
```

It needs `git` and `git-lfs` and network access to Hugging Face, and writes the
audio to `Corpora/Whitehorn_Collection/Audio/` (`.wav` and `.mp3` files are gitignored).

### What each step does

**The XML (by hand).** Each of the 87 files is a single `TEXT` element with the
attributes `id`, `xml:lang`, `dialect`, `source` (the repository's handle URL
and its description of the recording), `audio` (the repository's download URL),
`copyright`, `citation` and `BibTeX_citation`, and one child, an `AUDIO` element
whose `file` attribute names the audio file. There are no `S` elements. Files
sit in a folder named after their language (`XML/Paiwan/`, `XML/Atayal/`,
`XML/Amis/`, `XML/Seediq/`). Where a tape side holds more than one language
(for example the hymns on `10 Hymns of Praise B`, published as one Atayal and
one Seediq record) or more than one track, it is split into one record per
track or language, using the per-track times on the accession form.

**`download_audio_data.sh`.** Runs
`python3 QC/utilities/download_audio.py --corpus Whitehorn_Collection` (any
further arguments are passed on; `--dry-run` checks without downloading). That
script:

1. reads this corpus's entry in `audio_sources.json`: Hugging Face dataset
   `FormosanBank/Whitehorn_Collection` at a pinned revision, destination
   `Corpora/Whitehorn_Collection/Audio`, 89 audio files expected, and path
   mode `language_file` (each file is expected at
   `<language folder>/<AUDIO file>`, e.g. `Paiwan/…`);
2. lists the dataset's files at that revision and fails if there are not
   exactly 89 audio files, if a file the XML names is missing, if there is an
   audio file that is neither named by the XML nor declared in
   `audio_extras.json`, or if a declared extra is absent;
3. checks that `git-lfs` is installed, fetches that revision (depth 1) into a
   temporary `.audio-download-cache/` checkout, pulls the audio with Git LFS,
   and moves the audio files into `Corpora/Whitehorn_Collection/Audio/`,
   then deletes the temporary checkout;
4. checks the local `Audio/` folder the same way (nothing missing, no
   undeclared extras, no declared extra absent) and prints
   `Audio ready for Whitehorn_Collection: present=…, downloaded=…, generated=…, missing=0`.
