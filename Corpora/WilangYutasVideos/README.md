# Wilang Yutas Videos

Wilang Yutas and his collaborator 劉宇陽 recorded these [Atayal videos](https://www.youtube.com/@wilangyutas9297). The corpus contains Sekolik Atayal (`tay`), with some Mandarin translations: 83 XML files, 34 transcripts, 49 audio-only files and 3,012 sentences.

## Languages and dialects

All text is Atayal (`tay`), Sekolik dialect.

All 83 XML files under `XML/Atayal/` carry `xml:lang="tay"` and `dialect="Sekolik"` on their `TEXT` element. The translations are Mandarin: 235 `TRANSL` elements, all `xml:lang="zho"`. Some sentences contain code-switched Japanese and Mandarin speech, Japanese song lyrics and a Bopomofo fragment, all kept as source content (see "Notes and caveats"). Neither the earlier README nor the earlier GitBook page says how the Sekolik dialect label was determined.

## Source

Wilang Yutas was an Atayal elder who, with his collaborator 劉宇陽, recorded a large number of videos speaking in Atayal. The recordings are available on his [YouTube channel](https://www.youtube.com/@wilangyutas9297). Some of the audio is transcribed, and a smaller portion has been translated into Mandarin. Permission to republish was generously provided by Wilang Yutas's collaborator, 劉宇陽.

The transcripts are the channel's captions. The corpus has 83 XML files: 34 transcript files with 3,012 sentences and 49 audio-only files. Of the 49 audio-only files, 24 are `_untranscribed` companions that hold the untranscribed part of a partly transcribed video; the other 25 are videos with no transcript at all.

**Audio.** All audio is available. Every sentence has an `AUDIO` element with its start time (seconds) in the video, the name of its clip and, except for 16 sentences that are the last of their video, an end time. `download_audio_data.sh` downloads the published audio revision selected by FormosanBank's shared manifest and checks its XML inventory. It preserves the published files without resampling or segmentation. It is optional for text regeneration; `--dry-run` checks the remote inventory without downloading. Set `PYTHON` the same way from a private development checkout; `download_audio_data.sh` does not read `FORMOSANBANK_ROOT`: it always runs `QC/utilities/download_audio.py` from the FormosanBank checkout two folders above the corpus folder. `download_audio_data.sh` retrieves the reviewed published audio revision from Hugging Face and checks the XML inventory. It does not resample or resegment the recordings; `--dry-run` checks the remote inventory without downloading audio. (The shared manifest, `audio_sources.json` at the repository root, names the Hugging Face dataset `FormosanBank/YutasWilang` at a pinned revision and expects 3,103 audio files.)

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/WilangYutasVideos_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

Wilang Yutas. (2019). *Wilang Yutas YouTube Channel*. YouTube. https://www.youtube.com/@wilangyutas9297

The earlier README wrote the same citation without parentheses: Wilang Yutas. 2019. *Wilang Yutas YouTube Channel*. YouTube. https://www.youtube.com/@wilangyutas9297.

The XML's `citation` attribute is shorter and gives no title: `Wilang Yutas. (2019). YouTube channel. YouTube. https://www.youtube.com/@wilangyutas9297` (its `BibTeX_citation` has the title `Wilang Yutas YouTube Channel`).

## License

**License:** CC BY-NC 4.0

**Rights source:** 劉宇陽, 2024-12-26; evidence: ask maintainer

Permission was provided by 劉宇陽 on 2024-12-26; evidence: ask maintainer. The grant specifies CC By-NC; POL-042 supplies the canonical 4.0 spelling. The licence was recorded unversioned (`CC-BY-NC`) until 2026-10-17. The corpus remains subject to FormosanBank's [central terms](https://github.com/FormosanBank/FormosanBank/blob/main/LICENSE.md) and [AI use addendum](https://github.com/FormosanBank/FormosanBank/blob/main/AI-USE-ADDENDUM.md).

All 83 XML files carry `copyright="CC BY-NC 4.0"`.

## Notes and caveats

- **Untranscribed and partly transcribed videos.** Many videos have no transcript. Their XML points to audio without inventing S records. Partly transcribed recordings retain their `_untranscribed` companions. Many of the videos lack transcripts. These have XML files that point to the audio file, but there are no `<S>` elements. Many other videos have only partial transcripts. In these cases, the main XML contains only the transcribed part of the audio. A second XML with the postfix `_untranscribed` has no `<S>` elements and references the remaining audio.
- **Timestamps and multiple speakers.** Subtitle timestamps are not guaranteed to align perfectly with the recording. Multi-speaker passages have no separate speaker timestamps. Timestamps come from the source captions and may not align perfectly with the audio. A sentence ends where the next caption begins, including a caption with no text: so a video's last sentence ends with its caption rather than running to the end of the video, and stretches covered by no caption are untranscribed audio, listed in the video's `_untranscribed` file.
- **Multiple speakers.** Many videos involve multiple speakers. The source captions put additional speakers in parentheses without separate timestamps. The corpus retains their text and records `notes="multiple speakers"`, but it cannot provide speaker-level timing.
- **Unclear stretches.** Source question-mark runs inside a caption mark attempted but unrecoverable transcription and become `UNCLEAR`. There is no word or morpheme analysis. Segments that were not transcribable are marked as `<UNCLEAR/>`.
- **Question-mark-only captions.** A caption that is nothing but question marks is untranscribed audio, not a sentence. Its clip is listed in the video's `_untranscribed` companion and its sentence ID is retired, not reused (POL-037). This applies to two captions, `…MVI_1703.xml` `Atayal_8` (39.74–40.78 s) and `Atayal_9` (40.78–42.0 s); their clips `…MVI_1703_Atayal_8.wav` and `…_Atayal_9.wav` are now in `…MVI_1703_untranscribed.xml`. `scripts/download_audio.py` cuts clips only from sentence timings, so a future audio refresh would cut that stretch as an untranscribed gap clip instead. A caption that is nothing but question marks is untranscribed audio, not a sentence: its clip is listed in the video's `_untranscribed` file and its sentence ID is retired, not reused. This applies to two captions, `Atayal_8` and `Atayal_9` of `20190407_Yutas_Wilang_di5duan_Lowsing_Watan_MVI_1703`.
- **Transcriber's Japanese notes.** The transcriber wrote notes on Japanese loanwords in parentheses after the word, e.g. `cyolo(日: ちょっと)`. These notes are not speech: they are taken out of the sentence text and recorded in its FORM `notes`, naming the word (e.g. `transcriber's Japanese gloss: cyolo = ちょっと`; 17 notes in 13 sentences); the loanword stays. Details are under "What each step does".
- **Uncertain translation.** One translation marks a missing stretch with `(???)` (`所以他們取名為(???)`, Yagu_04 `Atayal_85`). The mark is removed and the TRANSL `notes` says the translation is uncertain, quoting the source. One Mandarin translation marks a missing stretch with `(???)`; the mark is removed and the translation's `notes` says it is uncertain, quoting the source.
- **Non-Atayal content.** Japanese songs, Mandarin speech and annotations, and the Bopomofo fragment `ㄇ` are intentional source content. Orthography, vocabulary and phonology warnings involving them need source-aware review. A few sentences quote Japanese song lyrics (kana/kanji) and one sentence contains a Bopomofo fragment (`ㄇ`) from the transcriber; these are faithful to the source subtitles and are intentionally kept. Code-switched Japanese and Mandarin are retained; the Atayal phonology profile does not transcribe those languages correctly.
- **Repeated utterances.** Repeated utterances are narrative evidence. Do not deduplicate them for corpus publication.

## Reproduction and processing

### How to reproduce

Required inputs, source hashes, build code and tests are under `CodeAndDocs/`. The canonical output is `XML/Atayal/`. Install the current FormosanBank requirements and `CodeAndDocs/requirements.txt`, then run (from the corpus folder):

```bash
./CodeAndDocs/generate_xml.sh
```

or, from the repository root:

```bash
bash Corpora/WilangYutasVideos/CodeAndDocs/generate_xml.sh
```

From a separate development checkout, select the current tools explicitly:

```bash
FORMOSANBANK_ROOT=/path/to/FormosanBank PYTHON=python3 \
  QC_OUTPUT_DIR=/path/to/external/reports ./CodeAndDocs/generate_xml.sh
```

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

`CodeAndDocs/generate_xml.sh` rebuilds all 83 XML files from the committed transcripts and [video manifest](CodeAndDocs/video_manifest.tsv), without scraping YouTube. It uses the current FormosanBank cleaner, accent-removal standardization and Ortho94 phonology. The actual tool revision is recorded in [provenance.json](CodeAndDocs/provenance.json); it is not a required checkout pin. Source speaker notes remain attached to both FORM tiers.

The build uses the selected checkout's tools and records their actual revision in [provenance.json](CodeAndDocs/provenance.json). That record is informational, not a tool pin. A Git-free export retains its supplied provenance. Warnings are saved outside the corpus; the printed directory must be reviewed. Source refresh, validators and audio acquisition are separate from the XML build.

**Source refresh.** `CodeAndDocs/refresh_source.sh` is the optional source refresh (POL-047). It needs network access and never writes XML. `refresh_source.sh captions` re-fetches the channel's caption files into `CodeAndDocs/raw_scrape/` (`scripts/scrape.py`; needs `yt-dlp` and `youtube-transcript-api`). `refresh_source.sh audio` downloads each video's audio and cuts the per-sentence and untranscribed clips from the built XML's timings (`scripts/download_audio.py`; needs `yt-dlp`, `lxml`, `ffmpeg` and `ffprobe`). After new captions: review every change to `raw_scrape/`, update the hashes in `video_manifest.tsv`, rebuild, then run `audio`. If the untranscribed clips it reports differ from `video_manifest.tsv`, update the manifest and rebuild. `CodeAndDocs/refresh_source.sh` is the optional source refresh. It needs network access and never writes XML. `refresh_source.sh captions` re-fetches the channel's caption files into `CodeAndDocs/raw_scrape/`; `refresh_source.sh audio` downloads each video's audio from YouTube and cuts the per-sentence and untranscribed clips from the built XML's timings (needs `yt-dlp`, `ffmpeg` and `ffprobe`). The clips are written to `Audio/Atayal/`; untranscribed gaps shorter than 1 s are not cut (`MIN_GAP = 1.0` in `scripts/download_audio.py`).

**Checks.** Source checks and regression tests run separately from regeneration. Run the corpus regression checks separately:

```bash
python3 -m unittest discover -s CodeAndDocs/tests -v
```

`CodeAndDocs/audit_source_alignment.py --xml-root /path/to/pre-clean/XML` checks a separate pre-clean build from `CodeAndDocs/make_xml.py --output-dir /path/to/empty/XML`. This checks parser coverage, not independent source fidelity or final QC. Current FormosanBank validators and source review are still required; historical test counts are not a readiness gate. Two unchanged-input builds must reproduce the same output, and final QC still requires source review. The corpus README gives the commands and processing caveats: this page, under "How to reproduce" and "Notes and caveats".

### What each step does

The build starts from the committed transcripts in a fresh staging directory, then runs the shared cleaner, `standardize.py --remove_accents`, and `add_phonology.py --orthography Ortho94`. Ortho94 and accent removal retain the published processing decision. The standard tier follows current `standards.csv`.

`generate_xml.sh` takes the FormosanBank checkout from `FORMOSANBANK_ROOT` (default: three folders above `CodeAndDocs/`), the interpreter from `PYTHON` (default `python3`) and the warnings folder from `QC_OUTPUT_DIR` (default: a new temporary folder `wilang-build-reports.XXXXXX`). It creates a staging folder `CodeAndDocs/.build.XXXXXX`, deleted on exit, checks that `QC/cleaning/clean_xml.py` exists in the checkout, then runs, in order:

1. **`make_xml.py --output-dir <staging>/XML`** builds all 83 files from the 34 transcripts in `CodeAndDocs/raw_scrape/`, as described under "Source processing" below. It refuses a non-empty output folder.
2. **`QC/cleaning/clean_xml.py --corpora_path <staging>/XML --warnings_dir <warnings folder>`**, the shared FormosanBank cleaner, cleans text and punctuation in place and writes its warnings CSV to the warnings folder, outside the corpus.
3. **`QC/utilities/standardize.py --corpora_path <staging>/XML --remove_accents`** creates the `kindOf="standard"` FORM for every sentence: a copy of the original FORM with accents deleted, and no letter conversion. Its `standardize_warnings.csv`, if any, is written inside the staging folder and deleted with it.
4. **`make_xml.py --copy-form-notes <staging>/XML`** is the corpus's one post-standardization step (the POL-047 deviation below). For every sentence it copies the original FORM's `notes` onto the standard FORM, and fails if a sentence lacks either FORM.

   **POL-047 deviation:** After standardization, copy source FORM notes onto standard FORM to preserve the published speaker qualifications. This changes notes only; shared tools still generate all standard text and PHON.

5. **`QC/utilities/add_phonology.py --corpora_path <staging>/XML --orthography Ortho94`** writes a `PHON` for each FORM tier: the original PHON from the `Orthographies/Ortho94` Atayal table, the standard PHON from Ortho113 (3,012 of each in the published XML).
6. The staged `XML/Atayal/*.xml` files are copied over `XML/Atayal/` (files already there that the build does not produce are not deleted).
7. **`make_xml.py --record-provenance <checkout>`** writes the checkout's `git rev-parse HEAD` to `CodeAndDocs/provenance.json`; without Git metadata it keeps the existing record and fails if there is none. The script finally prints the warnings folder.

#### Source processing (`make_xml.py`)

[video_manifest.tsv](CodeAndDocs/video_manifest.tsv) lists every output, video ID and source hash. The 34 committed transcripts preserve Joshua Hartshorne's published corrections from [the June source repair](https://github.com/FormosanBank/FormosanBank/commit/5dbd832e245ff1f34078aa2c8e8bb314957556b8). `CodeAndDocs/import_reviewed_sources.py` performed this one-time import and updated the hashes. It is not called by regeneration.

`make_xml.py` checks that the manifest has 83 unique output paths, 34 transcript sources and 49 audio-only outputs, and that each transcript's byte count and SHA-256 match the manifest; any mismatch stops the build.

The reviewed inputs preserve the published corrections and contain 3,014 timestamped captions, 237 translation lines and five wrapped caption continuations. The reviewed inputs contain 3,014 non-empty timestamp rows, 237 translation lines and five wrapped caption continuations. The earlier development scrape's 3,441 empty timestamps (captions with no text) are absent from the reviewed inputs.

Each timestamped caption becomes one S. An indented continuation, or a continuation of an open speaker parenthesis, belongs to that caption. Unindented translation lines stay translations, including two instances of the name `Wilang`. Parentheses identify a second speaker in this source; their content is retained and the speaker boundary becomes punctuation. They do not indicate optional words. A sentence whose caption had parentheses gets the FORM note `multiple speakers`.

The exception is the transcriber's notes on Japanese loanwords, written `(日: …)` after the word, e.g. `cyolo(日: ちょっと)`. They are notes, not speech: they leave the sentence text and are recorded in the sentence's FORM `notes`, naming the word annotated, e.g. `transcriber's Japanese gloss: cyolo = ちょっと` (17 notes in 13 captions, all in `20190209_YutasWilang_ki_Yagu_04_disiduan_Sayun.xml`; one, `gako no kyuzi(日: 学校のきゅうじ)`, glosses a three-word phrase; an empty note is recorded as `(left blank)`). The loanword itself stays.

A run of three or more question marks inside a caption becomes an `<UNCLEAR/>` element. Transcription gaps retain the published word boundary after `UNCLEAR`, so regeneration cannot join the words on either side. The gap supplies no invented text or phonemes.

Sentence IDs are `Atayal_<n>`, numbered over the captions in order; each sentence's clip is `<file name>_Atayal_<n>.wav`. A sentence's audio starts at its caption's timestamp and ends at the next caption's timestamp; a video's last sentence gets no end time (it runs to the end of the video) unless the table below gives one, which leaves 16 sentences in the published XML without an end time. Where a sentence's next caption was empty, its end is that empty caption's start, as in the caption track and the corpus's first version: 22 sentences, recorded with their source line in [caption_end_times.tsv](CodeAndDocs/caption_end_times.tsv) (maintainer ruling 2026-10-17). 18 are a video's last sentence, which otherwise ran to the end of the video and contained the untranscribed tail; 4 are mid-video, followed by uncaptioned stretches of 8.6, 22.34, 27.36 and 0.5 s. Audio covered by no caption is untranscribed audio and belongs in the video's `_untranscribed` companion: [untranscribed_clips.tsv](CodeAndDocs/untranscribed_clips.tsv) lists the 7 clips this added (the 4 mid-video stretches, and the tail of the 3 videos whose companion held only the stretch before the first caption), and `…Yagu_05_diwuduan_untranscribed.xml` is a new companion. The build fails if any row of `caption_end_times.tsv` is not applied. 22 audio end times return to the caption track's own (see Notes). Each audio-only file is a `TEXT` with one `AUDIO` element for its manifest file, followed by any retired question-mark-only caption clips of that video and the clips `untranscribed_clips.tsv` lists for it. All published TEXT/S IDs, recording filenames and audio-only entries are retained, except the two retired sentence IDs described below; endpoints are retained except the 22 above. All recording filenames and TEXT/S IDs are preserved, except the two retired sentence IDs described under Notes; the captions become 3,012 sentences. The two retired IDs are described under "Question-mark-only captions" in "Notes and caveats".

The [issue #1 source review](CodeAndDocs/issue_1_review.tsv) records all 20 flagged instances of Japanese/Mandarin content: Japanese and Mandarin speech, code-switches and song lyrics are retained; the 13 captions whose flagged content is the transcriber's `(日: …)` notes have those notes moved to FORM notes. Two pure `(再確認)` recheck markers are recorded in FORM notes rather than emitted as translations. Two similar annotations attached to real translations move to translation notes. No spoken text is deleted. Repeated utterances, code-switching and transcription gaps remain part of the corpus. Pure editorial recheck markers are retained in notes, and real translations retain their text. The complete earlier acquisition and processing versions remain in Git history; the development-only scripts under `scripts/` are not reproduction entrypoints.

Every `TEXT` gets `id` (the file name), `xml:lang="tay"`, `dialect="Sekolik"`, `audio` (the video's YouTube URL), `source="Wilang Yutas Atayal Videos"`, `copyright="CC BY-NC 4.0"`, `citation` and `BibTeX_citation`. Translations get `xml:lang="zho"`.
