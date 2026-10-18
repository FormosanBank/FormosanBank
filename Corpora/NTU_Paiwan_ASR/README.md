# NTU Paiwan ASR Corpus

Paiwan (`pwn`) speech data collected by [Professor Li-May Sung](https://homepage.ntu.edu.tw/~gilntu/Faculty/Li-May_Sung.html)
at National Taiwan University, comprising **read text** (participants reading prepared passages) and
**spontaneous speech** (elicited narratives and topics). Collected over two field years and published
here in FormosanBank XML format.

## Languages and dialects

Every file is Paiwan, `xml:lang="pwn"`. The `dialect` attribute on each `TEXT`
records one of four Paiwan dialects, and each speaker's files all carry the same
dialect:

| `dialect` | files | speakers (folders under `XML/Paiwan/`) |
| --- | --- | --- |
| `Northern` | 115 | Calina, Edran, Kerris, Maron, Nira, Zendar |
| `Eastern` | 98 | Falin, Halmir, Ilvane, Loris, Sarnix, Tavora |
| `Southern` | 31 | Doriel, Orsen |
| `Central` | 16 | Belmira, Garven |

- **Four dialects:** Northern, Central, Eastern, and Southern (Southern enters with the Year-2 data).

The Year-1 speakers (the six listed in `CodeAndDocs/non_sp_data.json`) are Belmira,
Falin, Loris, Nira, Sarnix and Zendar; the other ten are Year-2 speakers. For Year 1
the dialect was set by `CodeAndDocs/add_dialect.py`, which takes the value as a
command-line flag, so the published scripts do not record which value was passed
for which speaker. For Year 2 and the spontaneous speech the dialect comes from the
private `speaker_key.csv` (see "Reproduction and processing").

## Source

#### Overview

The NTU Paiwan ASR Corpus contains Paiwan speech data collected by Professor Li-May Sung at National Taiwan University. It covers read text and spontaneous speech collected over two field years.

The current public corpus contains 260 XML files from 16 speakers across Northern, Central, Eastern, and Southern Paiwan. Speaker names are pseudonyms, and the two field years represent distinct participants.

#### Content Summary

* **Language Covered**: Paiwan
* **Corpus Content**:
  * Texts with aligned audio for read speech
  * Spontaneous speech recordings
* **Data Contributors**: Sixteen speakers (pseudonyms used to maintain anonymity)

#### Contents

- **260 XML files**, organised by speaker under `XML/Paiwan/<Speaker>/`.
- **3,101 transcribed sentences**, **58 untranscribed recording stubs**, and
  **3,156 audio references**.
- **16 speakers** across two years, all under pseudonyms (see *Privacy* below). The two years are
  **distinct individuals**.

(The 3,156 audio references are one per transcribed sentence, less the 3 sentences
that have no `AUDIO` element (see "Notes and caveats"), plus one per stub:
3,101 − 3 + 58 = 3,156.)

#### Two kinds of recording

1. **Read speech** — fully transcribed. Each `<S>` carries a `FORM` (original + standard tier),
   `PHON` (IPA), and an `<AUDIO start=… end=… file=…/>` clip.
2. **Spontaneous speech** — long recordings of which only a careful one-minute window was transcribed.
   These follow the FormosanBank **two-file partial-transcription** convention:
   - `<topic>_<Speaker>.xml` holds the transcribed window (`<S>` elements with audio clips), and
   - `<topic>_<Speaker>_untranscribed.xml` is a stub (`TEXT` + a single `AUDIO`) pointing at the full
     recording, marking that the remainder is present as audio but not transcribed.

There are no translations, no word or morpheme tiers, and no glosses.

#### Layout

```
NTU_Paiwan_ASR/
├── XML/Paiwan/<Speaker>/*.xml      # the published data
├── CodeAndDocs/                    # Year-1 reproduction scripts + metadata
├── download_audio_data.sh          # pulls audio from HuggingFace
└── README.md
```

`CodeAndDocs/` also holds the Year-2 and spontaneous-speech build scripts
(`build_y2_and_spontaneous.py`, `stage_audio.py`).

#### Audio

Audio is **not** committed; it is hosted on HuggingFace as the `FormosanBank/NTU_Paiwan_ASR_*`
datasets (full recordings only). To fetch it and regenerate the per-sentence clips that the XML
`AUDIO/@file` attributes reference:

```bash
./download_audio_data.sh
```

This downloads the two pinned `NTU_Paiwan_ASR_*` source datasets into `Audio/` and then runs
`CodeAndDocs/extract_audio_clips.py` to cut each `<S>`'s `[start, end)` segment client-side. Requires
`git` and `git-lfs`.

The two datasets are `FormosanBank/NTU_Paiwan_ASR_1` (98 recordings) and
`FormosanBank/NTU_Paiwan_ASR_Y2` (104 recordings); their pinned revisions are
recorded in the repository's `audio_sources.json`.

Audio is hosted on Hugging Face rather than committed to Git. Running the corpus's `download_audio_data.sh` downloads the full recordings and uses `CodeAndDocs/extract_audio_clips.py` to recreate the sentence-level clips referenced by the XML. Complete reconstruction also requires the private raw recordings and speaker key, which are intentionally not public.

#### Applications

The NTU Paiwan ASR Corpus is a crucial resource for advancing research and technology in several key areas:

* **Automated Speech Recognition (ASR)**: The aligned text and audio make this corpus particularly valuable for developing ASR systems tailored to Paiwan, enabling future tools like transcription software and voice interfaces in the language.
* **Language Revitalization**: Supports the creation of educational materials and language-learning resources for Paiwan speakers and learners.
* **Speech Technology Development**: Facilitates tools such as text-to-speech systems and pronunciation modeling.
* **Linguistic Analysis**: Enables studies on syntax, phonology, discourse structures, and other linguistic phenomena.
* **Comparative Studies**: Supports research on shared features and differences among Formosan languages.

#### Acknowledgments

This corpus was developed through a collaborative effort led by **Dr. Sung** at the NTU Graduate Institute of Linguistics. The project is part of the broader FormosanBank initiative and would not have been possible without the contributions of Paiwan-speaking participants. Special thanks to all collaborators and the broader Paiwan community for their support and engagement in this vital preservation effort.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/NTU_Paiwan_ASR_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

- Citation: Le Ferrand, É., Prud'hommeaux, E., Hartshorne, J. K., & Sung, L.-M. (2024). *NTU Paiwan
  ASR Corpus.* Electronic Resource.

This is the `citation` attribute of every `TEXT` element.

## License

**License:** CC BY 4.0
**Rights source:** FormosanBank, which owns this data (collected by Professor Li-May Sung); date not recorded in this repository; evidence: ask maintainer

#### License and AI Use

License: CC BY 4.0 (the `copyright` value of every `TEXT` element). The central FormosanBank terms and AI-use addendum also apply.

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

The `@copyright` value was recorded without a version (`CC-BY`) until
2026-10-16, when it was normalized to `CC BY 4.0` under POL-042 (a value that
names no version is 4.0).

## Notes and caveats

- The very end of the audio for `02SC105-1_Belmira.xml` is silent; its last two audio segments were
  removed from the XML for that reason.
- Spontaneous recordings whose only transcription is the one-minute window appear as the
  `*_untranscribed.xml` stubs described above — this is expected, not missing data.
- Three source lines that offered alternative wordings (in parentheses or with a
  slash) were each published as two sentences, one per alternative: `a1` / `a1-alt2`
  and `a3` / `a3-alt2` in `Paiwan/Nira/02JN106-3_Nira.xml`, and `a11` / `a11-alt2`
  in `Paiwan/Zendar/02SN106-2_Zendar.xml`. Both copies keep the full source line in
  the original `FORM`'s `notes` attribute ("source alternative notation expanded
  from …"). The `-alt2` copies have no `AUDIO` element (the recording is on the
  first copy), and the shared words are counted twice in word counts. The script
  that made this split is not among the published scripts.
- The published Year-1 scripts do not reproduce the published Year-1 XML exactly:
  `CodeAndDocs/main.py` writes `TEXT/@id` as `Li-May_Pwn<Speaker>_<file>` and
  `@source` as `Li-May Paiwan Data, …`, while the published files carry
  `NTU_Pwn_<Speaker>_<file>` and `NTU Paiwan Data, …`. The step that made that
  change, and the Belmira hand edit above, are not recorded in `CodeAndDocs/`.

#### Privacy

Speaker names throughout (`Belmira`, `Loris`, … and the Year-2 names) are **pseudonyms**; no real
participant names, NTU subject codes, or source paths appear anywhere in the published XML, filenames,
or these docs. The real-name ↔ pseudonym mapping lives only in the private development repository.

## Reproduction and processing

### How to reproduce

This corpus predates POL-047 and POL-052 (it is listed in `generate_xml_pending.txt`
and `provenance_pending.txt` at the repository root): it has no
`CodeAndDocs/generate_xml.sh` build script and no `CodeAndDocs/provenance.json`.
The published XML cannot be rebuilt from this repository alone.

The Year-1 read-speech XML is reproduced from ELAN (`.eaf`) sources by the scripts in `CodeAndDocs/`
(`main.py` → `add_dialect.py` → `add_citations.py` → standardize/`add_phonology` → `extract_audio_clips.py`).
The ELAN builders emit `FORM kindOf="original"`; the standardization step then creates the
`kindOf="standard"` comparison tier.

The Year-2 read-speech and all spontaneous-speech XML are built from the raw ELAN sources by
`CodeAndDocs/build_y2_and_spontaneous.py` (ELAN → FormosanBank XML, applying pseudonyms and the two-file
partial-transcription model), followed by the standard FormosanBank pipeline
(`clean_xml` → `standardize --copy` → `add_phonology`); audio is staged for HuggingFace by
`CodeAndDocs/stage_audio.py`. These scripts are name-free and published here, but **running them
requires two private inputs that are not part of this corpus**:

1. `speaker_key.csv` — the real-name ↔ pseudonym mapping (and the per-speaker filename patterns the
   build script loads). It lives only in the private development repository.
2. the raw ELAN/audio sources, which contain participants' real names and are likewise private.

So the scripts document and reproduce the exact process, but full reproduction is only possible from the
private development repo. The XML published here is the QC-passing output of that process.

Read-speech XML was built from ELAN sources. The second field year and spontaneous-speech data were built with `CodeAndDocs/build_y2_and_spontaneous.py`, followed by the standard cleaning, orthography, phonology, and validation steps. The public scripts apply pseudonyms and contain no real participant names.

The audio clips, by contrast, can be recreated by anyone with
`bash Corpora/NTU_Paiwan_ASR/download_audio_data.sh` (see "Audio" above).

The exact flags with which the shared QC steps (`clean_xml`, `standardize`,
`add_phonology`) were run for this corpus are not recorded.

#### Publication authority

The published XML is the reviewed output of private development commit
`8fb7eff4c51daed73ca0950259a67c4f5dd9d559`. The private source inventory
contains 202 ELAN files and is not published because it includes participant
identities. The public output contains pseudonyms only.

### What each step does

#### Year 1 read speech

1. **`CodeAndDocs/main.py`** (no flags; run from inside `CodeAndDocs/`, because
   it opens `non_sp_data.json` by a relative path). Reads
   `CodeAndDocs/non_sp_data.json`, which lists, per Year-1 speaker, each
   recording's WAV name, ELAN file name, TextGrid name and topic (98 recordings
   across six speakers). For each recording it opens
   `CodeAndDocs/Data/<Speaker>/<file>.eaf` (if that name does not exist, it retries
   with underscores removed), and writes one `TEXT` with `xml:lang="pwn"`,
   `copyright="CC BY 4.0"`, `@audio` = the WAV name, and placeholder
   `citation="origianl"` / `BibTeX_citation="TBD"`. Every ELAN
   `ALIGNABLE_ANNOTATION` becomes an `S` (id = the ELAN annotation id) holding a
   `FORM kindOf="original"` (the annotation text with newlines removed) and an
   `AUDIO` with `start`/`end` in seconds. Output:
   `CodeAndDocs/Final_XML/Paiwan/<Speaker>/<file>_<Speaker>.xml`; it also copies
   each WAV to `Final_XML/Paiwan/<Speaker>/audio/`.
2. **`CodeAndDocs/add_dialect.py --dialect <value> --path <dir>`** sets
   `TEXT/@dialect` to the given value on every `.xml` file directly inside
   `<dir>` (not in subfolders), rewriting each file.
3. **`CodeAndDocs/add_citations.py`** (no flags) walks `Final_XML/` and sets
   `TEXT/@citation` and `TEXT/@BibTeX_citation` to the corpus citation (the one
   under "How to cite") and its BibTeX entry, replacing `main.py`'s placeholders.
4. **`CodeAndDocs/normalize_audio_filenames.py [--xml_root Final_XML]`** replaces
   spaces with underscores in every `TEXT/@audio` (for example
   `02SE105-1 Loris.wav` → `02SE105-1_Loris.wav`). Its place in the order is not
   recorded; it must run before `extract_audio_clips.py`, which looks the WAV up
   by that name.
5. **Shared standardize and phonology steps** (flags not recorded): add the
   `FORM kindOf="standard"` tier and the two `PHON` tiers (every `S` in the
   published XML has original and standard `FORM` and original and standard
   `PHON`).
6. **`CodeAndDocs/extract_audio_clips.py`** (see step 3 of the Year-2 list).

#### Year 2 read speech and all spontaneous speech

1. **`CodeAndDocs/build_y2_and_spontaneous.py [--key <speaker_key.csv>]
   [--new-download <dir>] [--out <dir>]`**. Defaults: `--key` =
   `CodeAndDocs/speaker_key.csv`, `--new-download` = `NTU_NewDownload/` and
   `--out` = `new_xml/`, both beside `CodeAndDocs/`. It stops with an error if
   the private speaker key is missing. It reads three source folders:
   - `NTU_NewDownload/NTU_Y2/` (searched recursively): Year-2 read speech, built
     as fully transcribed files;
   - `NTU_NewDownload/Y1 ELAN 1 min perfect transcription/` and
     `NTU_NewDownload/Y2 ELAN 1 min perfect transcription/` (top level only):
     spontaneous speech, built as two files each.

   For each `.eaf` it drops a trailing ` 1 min` from the file name and matches
   the name against the key's filename patterns to find the speaker's pseudonym,
   which replaces the real name in the file name. Files that match no pattern
   (`UNRESOLVED`) or contain no usable annotation (`EMPTY`) are skipped and listed
   in the printed summary. It keeps every time-aligned ELAN annotation that
   contains at least one letter (this drops the numbering tier, `001`, `002`, …,
   whatever the tier is called), collapses runs of whitespace, keeps the
   apostrophe as written, and sorts the annotations by start time. Each becomes an
   `S` (id = the ELAN annotation id) with a `FORM kindOf="original"` and an
   `AUDIO` with `start`/`end` in seconds (three decimals) and
   `file="<file>_<id>.wav"`. The `TEXT` gets `id="NTU_Pwn_<Pseudonym>_<file>"`,
   `xml:lang="pwn"`, `source="NTU Paiwan Data, Participant <Pseudonym>, file <file>"`,
   `@audio` = the file name with spaces as underscores plus `.wav`,
   `copyright="CC BY 4.0"`, the corpus citation and BibTeX entry, and the
   speaker's `dialect` from the key. For spontaneous speech it also writes
   `<file>_untranscribed.xml`: a `TEXT` with no `S` and one `AUDIO` whose `file` is
   the full recording. Output: `new_xml/Paiwan/<Pseudonym>/`.
2. **Shared QC steps** `clean_xml` → `standardize --copy` → `add_phonology`
   (flags not recorded). `standardize --copy` copies the original `FORM` into a
   `FORM kindOf="standard"` without changing spelling; `add_phonology` adds the
   `PHON` tiers.
3. **`CodeAndDocs/extract_audio_clips.py [--xml_root Final_XML] [--audio_root <dir>]`**
   (also run by `download_audio_data.sh`, with `--xml_root
   Corpora/NTU_Paiwan_ASR/XML --audio_root Corpora/NTU_Paiwan_ASR/Audio`). For
   each XML file it finds the WAV named in `TEXT/@audio` in the matching speaker
   folder under the audio root. For each `S` with an `AUDIO start/end` it cuts that
   `[start, end)` stretch into `<XML file name>_<S id>.wav` beside the full
   recording, writes that name into `AUDIO/@file`, and rewrites the XML file in
   place. Stubs have no `S` and are left alone. A missing WAV, a bad time or an
   empty stretch is reported and skipped.

#### Audio staging (for the Hugging Face upload)

**`CodeAndDocs/stage_audio.py [--out Audio] [--sources <dir> …]`** copies every
full WAV found under the private source folders (defaults `Temp/` and
`NTU_NewDownload/NTU_Y2/`, beside `CodeAndDocs/`) to
`Audio/Paiwan/<Pseudonym>/<file>.wav`, using the same speaker key to replace real
names with pseudonyms (the first copy of a name wins), and prints any file it
could not match. Per-sentence clips are not staged; they are cut at download time
by `extract_audio_clips.py`.
