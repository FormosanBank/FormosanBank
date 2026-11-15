# Wild (kanakanavu.info) Kanakanavu Texts

Eleven interlinear Kanakanavu texts from the website kanakanavu.info, made by Ilka
Wild for the project *Dokumentation und Beschreibung der Sprache Kanakanavu* at the
Universität Erfurt (director Christian Lehmann), 2012–2015: eight narrations and
stories recorded on video in Namasia in 2013 and 2014, and three stories recorded by
Shigeru Tsuchida in 1969 and re-transcribed by the project.

## Languages and dialects

Kanakanavu (`xnb`). All 11 files in `XML/Kanakanavu/` declare `xml:lang="xnb"` and
`dialect="Kanakanavu"`. The source does not divide the texts by dialect.

The speakers code-switch occasionally. Three words or phrases the source labels as
Bunun, and one word the source glosses as Chinese (`meimei`, "CHIN: little.sister"),
stay in the text; the Bunun ones carry a note on the word.

## Source

The website kanakanavu.info (static site; pages carry "Copyright: Ilka Wild 2013").
The data is the 11 pages under *Language Documentation*. Each page is one HTML table
exported from Toolbox with these rows, as the pages label them: `rf` reference, `PT`
phonetic transcription, `NR` normalized representation (word by word), `GE` English
gloss, `FTE` / `FTC` English / Chinese free translation, and, for the three Tsuchida
stories, `OT` / `OG` / `OFTE` (Tsuchida 2003's original transcription, gloss and free
translation).

| Texts | Speaker | Recorded |
|---|---|---|
| Mo'o 2013 Narration 2, 3 | Mo'o Kangena | March 2013, Namasia village, by Ilka Wild with Elizabeth Zeitoun |
| Mo'o 2014 Narration 1, 2; Mo'o 2014 Story 1, 2, 3 | Mo'o Kangena | March 2014, Namasia village, by Ilka Wild with Elizabeth Zeitoun |
| Pa'icu 2014 Narration 1 | Pa'icu Kangena | March 2014, Namasia village, by Ilka Wild with Elizabeth Zeitoun |
| S. Tsuchida 2003 Story 1, 2 | Angaiana Paepuli | February 1969, by Shigeru Tsuchida |
| S. Tsuchida 2003 Story 3 | Angaiana Paa'u | February 1969, by Shigeru Tsuchida |

The site says the Tsuchida texts were re-transcribed from the original sound files
"in the orthography of the Council of Indiginous Peoples of Taiwan", with a new gloss
line and new Chinese and English translations, and that their original transcription
and analysis are published in Tsuchida, Shigeru (2003), *Kanakanavu Texts
(Austronesian Formosan)*, Osaka Gakuin University (ELPR A3-014). Of Tsuchida's own
lines, only his free translation (`OFTE`) is included, as a second English translation
marked with `notes`. Tsuchida's transcriptions and glosses will be handled when we
process the original Tsuchida book, should we get permission to do so.

**Audio.** Each text has one recording: three MP3s for the Tsuchida stories (15.0
minutes) and eight videos for the 2013–2014 texts (17.2 minutes). There are no
sentence timings, so each recording is attached to its whole text as untranscribed
audio (an `AUDIO` element directly under `TEXT`). For the videos, the file is the
video's audio track as `.wav`: copied out of the `.mp4` without re-encoding (`.m4a`),
then decoded to `.wav` (`for f in *.m4a; do ffmpeg -n -i "$f" "${f%.m4a}.wav"; done`).

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/<CorpusDir>_corpora_stats.csv` and appears on this corpus's page on the
[FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

Wild, Ilka 2018, Voice and transitivity in Kanakanavu. Unpubl. PhD dissertation University of Erfurt.

## License

**License:** CC BY-NC 4.0
**Rights source:** Christian Lehmann (the project's senior author), 2026-11-06; evidence: permission obtained by the maintainer

Permission to use the site's content, including the three Tsuchida stories, their
recordings and Tsuchida's 2003 translations, was given by Christian Lehmann and
obtained by the maintainer. The site itself says that the Tsuchida texts and sound
files are published "with the author's permission".

## Notes and caveats

- The source provides a transcription of the audio (its phonetic line, `PT`). However,
  because it does not have time stamps, it is currently included as files in
  [CodeAndDocs/PT/](CodeAndDocs/PT/), one per text. It is not fully processed or
  corrected.
- The site spells some frequent words differently from the other Kanakanavu
  corpora in FormosanBank, and its spelling is kept in both tiers. Most visibly,
  it writes `ei` where the ILRDF dictionary and ePark write `ai` or `ee`
  (`saronei`/`saronai` "male", `vunei`/`vunai` "snake", `ringei`/`ringai` "trap");
  no other Kanakanavu corpus here writes `ei`. Other differences are doubled
  vowels (`taamu`/`tamu`), the glottal stop (`ucangin`/`'ucangin` "spouse") and
  `u` for `o` (`pukarikari`/`pokarikari` "speak"), and
  the site itself writes some words both ways (`aranei`/`aranai`). A search
  across corpora should allow for both spellings.

## Reproduction and processing

### How to reproduce

```bash
bash CodeAndDocs/refresh_source.sh    # optional: re-fetch the site (pages, recordings, gloss-index image)
bash CodeAndDocs/generate_xml.sh      # build XML/ and CodeAndDocs/PT/ from the committed scrape
```

`generate_xml.sh` needs only a FormosanBank checkout (found as `../../` when installed
under `Corpora/`, or a sibling `../FormosanBank/`; override with `FORMOSANBANK_ROOT`)
and its `.venv`. `refresh_source.sh` needs network access to kanakanavu.info.

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

### What each step does

1. **`generate_xml.py`** reads the committed HTML (`CodeAndDocs/source/html/`), one
   XML file per text page. Each inner table is one sentence, named by its `rf` row
   (apostrophes removed). A table with no `NR` row is rejected with its reason in
   `CodeAndDocs/rejected.tsv` (one: ST03_01_70a, which has only an `rf` row). It
   applies [CodeAndDocs/source_corrections.tsv](CodeAndDocs/source_corrections.tsv),
   one row per changed cell with its reason (the build stops if any row's expected
   text is not found), writes the IPA tap `ɾ` as `r` in the text, and builds: sentence
   text = the `NR` cells joined by spaces; one word per `NR` cell with the `GE` cell as
   its gloss; morphemes where `NR` splits a word (hyphen or `<infix>`) and the gloss
   splits the same way (an infixed root is written with a hyphen where the infix goes,
   followed by the infix, e.g. `s-asʉrʉcʉ` + `-um-`), and one morpheme, the word itself,
   for an unsplit word whose gloss is one piece; `FTE`/`FTC` as English/Chinese
   translations and `OFTE` as an alternative English translation; the page's
   recording as the text's `AUDIO`. The site's sentences have no punctuation, so
   each sentence ends in the final mark of its English translation (a period if
   there is none), and each translation ends in its script's final mark
   (`.` `?` `!`, `。` `？` `！`; POL-063). TEXT attributes come from `corpus_metadata.json`
   (citation, licence, the extension of the videos' extracted audio) and from each
   page (title, URL, recorder, date, speaker).
2. **`apply_manual_edits.py`**: no `manual_edits.xml` exists, so nothing happens.
3. **`clean_xml.py`**: the shared cleaner (typographic apostrophes and dashes to ASCII).
4. **`standardize.py --remove_accents`**: the standard tier is the original, which
   is already written in Ortho113, without the segmentation marks: the sentence's
   hyphens and infix brackets are removed (`ni-kamanʉngu` → `nikamanʉngu`).
5. **`add_phonology.py --orthography Ortho113`**: pronunciation lines for both tiers.
6. **`generate_pt.py`** writes the `PT` line into `CodeAndDocs/PT/`, one XML file per
   text with a `PT` row, applying
   [CodeAndDocs/pt_corrections.tsv](CodeAndDocs/pt_corrections.tsv) and writing `ts`,
   `tʃ` as `ʦ`, `ʧ`.

The build writes into a temporary directory and replaces `XML/` and `CodeAndDocs/PT/`
wholesale, so a rebuild on a clean checkout leaves `git status` empty.

**Standard gloss tier** (final step): `QC/glossing/apply_gloss_standard.py` adds `TRANSL kindOf="standard"` glosses beside every original gloss (POL-036 — the original tier is never changed), converting each gloss code according to this corpus's standardization list, [Glossing/ConversionTables/Wild-Lehmann-Kanakanavu.tsv](https://github.com/FormosanBank/FormosanBank/blob/main/Glossing/ConversionTables/Wild-Lehmann-Kanakanavu.tsv) (segmentation conventions in [Wild-Lehmann-Kanakanavu.rules.tsv](https://github.com/FormosanBank/FormosanBank/blob/main/Glossing/ConversionTables/Wild-Lehmann-Kanakanavu.rules.tsv)). Codes without a ruled mapping are copied verbatim, so the standard tier is always complete; the project-wide approach, vocabulary and per-language gloss dictionaries are documented in [Glossing/README.md](https://github.com/FormosanBank/FormosanBank/blob/main/Glossing/README.md).
### Audio on Hugging Face

The 11 recordings the XML names are hosted as one Hugging Face dataset,
`FormosanBank/Wild-Lehmann-Kanakanavu` ([.hf_dataset.yaml](.hf_dataset.yaml)), with
the files at `Kanakanavu/<file>`. [download_audio_data.sh](download_audio_data.sh)
downloads them. To upload or update the dataset, from the corpus root:

```bash
bash CodeAndDocs/upload_audio_to_hf.sh --dry-run   # what would happen
bash CodeAndDocs/upload_audio_to_hf.sh             # do it
```

[CodeAndDocs/upload_audio_to_hf.sh](CodeAndDocs/upload_audio_to_hf.sh) stages exactly
the files the XML names into `Audio_hf/Kanakanavu/`, uploads them with FormosanBank's
`QC/utilities/upload_to_hf.py`, and checks that the dataset holds exactly those
files. It needs a FormosanBank checkout, the `hf` command from `huggingface_hub` 1.x
(2.x no longer has the `upload-large-folder` command the bank's tool runs), and a
Hugging Face login with write access to FormosanBank.
