# NTU Paiwan ASR Corpus

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

Paiwan (`pwn`) speech data collected by [Professor Li-May Sung](https://homepage.ntu.edu.tw/~gilntu/Faculty/Li-May_Sung.html)
at National Taiwan University, comprising **read text** (participants reading prepared passages) and
**spontaneous speech** (elicited narratives and topics). Collected over two field years and published
here in FormosanBank XML format.

## Contents

- **260 XML files**, organised by speaker under `XML/Paiwan/<Speaker>/`.
- **16 speakers** across two years, all under pseudonyms (see *Privacy* below). The two years are
  **distinct individuals**.
- **Four dialects:** Northern, Central, Eastern, and Southern (Southern enters with the Year-2 data).
- Citation: Le Ferrand, É., Prud'hommeaux, E., Hartshorne, J. K., & Sung, L.-M. (2024). *NTU Paiwan
  ASR Corpus.* Electronic Resource.

### Two kinds of recording

1. **Read speech** — fully transcribed. Each `<S>` carries a `FORM` (original + standard tier),
   `PHON` (IPA), and an `<AUDIO start=… end=… file=…/>` clip.
2. **Spontaneous speech** — long recordings of which only a careful one-minute window was transcribed.
   These follow the FormosanBank **two-file partial-transcription** convention:
   - `<topic>_<Speaker>.xml` holds the transcribed window (`<S>` elements with audio clips), and
   - `<topic>_<Speaker>_untranscribed.xml` is a stub (`TEXT` + a single `AUDIO`) pointing at the full
     recording, marking that the remainder is present as audio but not transcribed.

## Layout

```
NTU_Paiwan_ASR/
├── XML/Paiwan/<Speaker>/*.xml      # the published data
├── CodeAndDocs/                    # Year-1 reproduction scripts + metadata
├── download_audio_data.sh          # pulls audio from HuggingFace
└── README.md
```

## Audio

Audio is **not** committed; it is hosted on HuggingFace as the `FormosanBank/NTU_Paiwan_ASR_*`
datasets (full recordings only). To fetch it and regenerate the per-sentence clips that the XML
`AUDIO/@file` attributes reference:

```bash
./download_audio_data.sh
```

This clones every `NTU_Paiwan_ASR_*` dataset into `Audio/` and then runs
`CodeAndDocs/extract_audio_clips.py` to cut each `<S>`'s `[start, end)` segment client-side. Requires
`git-lfs`, `jq`, and the `hf` CLI (`pip install "huggingface_hub[cli]"`; `hf auth login`).

## Reproduction

The Year-1 read-speech XML is reproduced from ELAN (`.eaf`) sources by the scripts in `CodeAndDocs/`
(`main.py` → `add_dialect.py` → `add_citations.py` → standardize/`add_phonology` → `extract_audio_clips.py`).

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

## Privacy

Speaker names throughout (`Belmira`, `Loris`, … and the Year-2 names) are **pseudonyms**; no real
participant names, NTU subject codes, or source paths appear anywhere in the published XML, filenames,
or these docs. The real-name ↔ pseudonym mapping lives only in the private development repository.

## Notes

- The very end of the audio for `02SC105-1_Belmira.xml` is silent; its last two audio segments were
  removed from the XML for that reason.
- Spontaneous recordings whose only transcription is the one-minute window appear as the
  `*_untranscribed.xml` stubs described above — this is expected, not missing data.
