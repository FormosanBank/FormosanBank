# Wilang Yutas Videos

Wilang Yutas and his collaborator 劉宇陽 recorded these [Atayal videos](https://www.youtube.com/@wilangyutas9297). The corpus contains Sekolik Atayal (`tay`), with some Mandarin translations: 83 XML files, 34 transcripts, 49 audio-only files and 3,012 sentences.

## Rights

**License:** CC BY-NC 4.0

**Rights source:** 劉宇陽, 2024-12-26; evidence: ask maintainer

The grant specifies CC By-NC; POL-042 supplies the canonical 4.0 spelling. The licence was recorded unversioned (`CC-BY-NC`) until 2026-10-17. The corpus remains subject to FormosanBank's [central terms](https://github.com/FormosanBank/FormosanBank/blob/main/LICENSE.md) and [AI use addendum](https://github.com/FormosanBank/FormosanBank/blob/main/AI-USE-ADDENDUM.md).

## Reproduction

Required inputs, source hashes, build code and tests are under `CodeAndDocs/`. The canonical output is `XML/Atayal/`. Install the current FormosanBank requirements and `CodeAndDocs/requirements.txt`, then run:

```bash
./CodeAndDocs/generate_xml.sh
```

From a separate development checkout, select the current tools explicitly:

```bash
FORMOSANBANK_ROOT=/path/to/FormosanBank PYTHON=python3 \
  QC_OUTPUT_DIR=/path/to/external/reports ./CodeAndDocs/generate_xml.sh
```

The build starts from the committed transcripts in a fresh staging directory, then runs the shared cleaner, `standardize.py --remove_accents`, and `add_phonology.py --orthography Ortho94`. Ortho94 and accent removal retain the published processing decision. The standard tier follows current `standards.csv`. Code-switched Japanese and Mandarin are retained; the Atayal phonology profile does not transcribe those languages correctly.

**POL-047 deviation:** After standardization, copy source FORM notes onto standard FORM to preserve the published speaker qualifications. This changes notes only; shared tools still generate all standard text and PHON.

The build uses the selected checkout's tools and records their actual revision in [provenance.json](CodeAndDocs/provenance.json). That record is informational, not a tool pin. A Git-free export retains its supplied provenance. Warnings are saved outside the corpus; the printed directory must be reviewed. Source refresh, validators and audio acquisition are separate from the XML build.

`CodeAndDocs/refresh_source.sh` is the optional source refresh (POL-047). It needs network access and never writes XML. `refresh_source.sh captions` re-fetches the channel's caption files into `CodeAndDocs/raw_scrape/` (`scripts/scrape.py`; needs `yt-dlp` and `youtube-transcript-api`). `refresh_source.sh audio` downloads each video's audio and cuts the per-sentence and untranscribed clips from the built XML's timings (`scripts/download_audio.py`; needs `yt-dlp`, `lxml`, `ffmpeg` and `ffprobe`). After new captions: review every change to `raw_scrape/`, update the hashes in `video_manifest.tsv`, rebuild, then run `audio`. If the untranscribed clips it reports differ from `video_manifest.tsv`, update the manifest and rebuild.

Run the corpus regression checks separately:

```bash
python3 -m unittest discover -s CodeAndDocs/tests -v
```

`CodeAndDocs/audit_source_alignment.py --xml-root /path/to/pre-clean/XML` checks a separate pre-clean build from `CodeAndDocs/make_xml.py --output-dir /path/to/empty/XML`. This checks parser coverage, not independent source fidelity or final QC. Current FormosanBank validators and source review are still required; historical test counts are not a readiness gate.

## Source processing

[video_manifest.tsv](CodeAndDocs/video_manifest.tsv) lists every output, video ID and source hash. The 34 committed transcripts preserve Joshua Hartshorne's published corrections from [the June source repair](https://github.com/FormosanBank/FormosanBank/commit/5dbd832e245ff1f34078aa2c8e8bb314957556b8). `CodeAndDocs/import_reviewed_sources.py` performed this one-time import and updated the hashes. It is not called by regeneration.

The reviewed inputs contain 3,014 non-empty timestamp rows, 237 translation lines and five wrapped caption continuations. The earlier development scrape's 3,441 empty timestamps (captions with no text) are absent from the reviewed inputs. Where a sentence's next caption was empty, its end is that empty caption's start, as in the caption track and the corpus's first version: 22 sentences, recorded with their source line in [caption_end_times.tsv](CodeAndDocs/caption_end_times.tsv) (maintainer ruling 2026-10-17). 18 are a video's last sentence, which otherwise ran to the end of the video and contained the untranscribed tail; 4 are mid-video, followed by uncaptioned stretches of 8.6, 22.34, 27.36 and 0.5 s. Audio covered by no caption is untranscribed audio and belongs in the video's `_untranscribed` companion: [untranscribed_clips.tsv](CodeAndDocs/untranscribed_clips.tsv) lists the 7 clips this added (the 4 mid-video stretches, and the tail of the 3 videos whose companion held only the stretch before the first caption), and `…Yagu_05_diwuduan_untranscribed.xml` is a new companion. All published TEXT/S IDs, recording filenames and audio-only entries are retained, except the two retired sentence IDs described below; endpoints are retained except the 22 above.

Each timestamped caption becomes one S. An indented continuation, or a continuation of an open speaker parenthesis, belongs to that caption. Unindented translation lines stay translations, including two instances of the name `Wilang`. Parentheses identify a second speaker in this source; their content is retained and the speaker boundary becomes punctuation. They do not indicate optional words.

The exception is the transcriber's notes on Japanese loanwords, written `(日: …)` after the word, e.g. `cyolo(日: ちょっと)`. They are notes, not speech: they leave the sentence text and are recorded in the sentence's FORM `notes`, naming the word annotated, e.g. `transcriber's Japanese gloss: cyolo = ちょっと` (17 notes in 13 captions, all in `20190209_YutasWilang_ki_Yagu_04_disiduan_Sayun.xml`; one, `gako no kyuzi(日: 学校のきゅうじ)`, glosses a three-word phrase; an empty note is recorded as `(left blank)`). The loanword itself stays.

Transcription gaps retain the published word boundary after `UNCLEAR`, so regeneration cannot join the words on either side. The gap supplies no invented text or phonemes.

The [issue #1 source review](CodeAndDocs/issue_1_review.tsv) records all 20 flagged instances of Japanese/Mandarin content: Japanese and Mandarin speech, code-switches and song lyrics are retained; the 13 captions whose flagged content is the transcriber's `(日: …)` notes have those notes moved to FORM notes. Two pure `(再確認)` recheck markers are recorded in FORM notes rather than emitted as translations. Two similar annotations attached to real translations move to translation notes. No spoken text is deleted. The complete earlier acquisition and processing versions remain in Git history; the development-only scripts under `scripts/` are not reproduction entrypoints.

## Audio

`download_audio_data.sh` downloads the published audio revision selected by FormosanBank's shared manifest and checks its XML inventory. It preserves the published files without resampling or segmentation. It is optional for text regeneration; `--dry-run` checks the remote inventory without downloading. Use the same `FORMOSANBANK_ROOT` and `PYTHON` settings from a private development checkout.

## Notes and Issues

- Many videos have no transcript. Their XML points to audio without inventing S records. Partly transcribed recordings retain their `_untranscribed` companions.
- Subtitle timestamps are not guaranteed to align perfectly with the recording. Multi-speaker passages have no separate speaker timestamps.
- Source question-mark runs inside a caption mark attempted but unrecoverable transcription and become `UNCLEAR`. There is no word or morpheme analysis.
- One translation marks a missing stretch with `(???)` (`所以他們取名為(???)`, Yagu_04 `Atayal_85`). The mark is removed and the TRANSL `notes` says the translation is uncertain, quoting the source.
- A caption that is nothing but question marks is untranscribed audio, not a sentence. Its clip is listed in the video's `_untranscribed` companion and its sentence ID is retired, not reused (POL-037). This applies to two captions, `…MVI_1703.xml` `Atayal_8` (39.74–40.78 s) and `Atayal_9` (40.78–42.0 s); their clips `…MVI_1703_Atayal_8.wav` and `…_Atayal_9.wav` are now in `…MVI_1703_untranscribed.xml`. `scripts/download_audio.py` cuts clips only from sentence timings, so a future audio refresh would cut that stretch as an untranscribed gap clip instead.
- Japanese songs, Mandarin speech and annotations, and the Bopomofo fragment `ㄇ` are intentional source content. Orthography, vocabulary and phonology warnings involving them need source-aware review.
- Repeated utterances are narrative evidence. Do not deduplicate them for corpus publication.

## Citation

Wilang Yutas. 2019. *Wilang Yutas YouTube Channel*. YouTube. https://www.youtube.com/@wilangyutas9297.
