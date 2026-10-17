# Wilang Yutas Videos

Wilang Yutas was an Atayal elder who, with his collaborator 劉宇陽, recorded
a large number of videos speaking in Atayal. The recordings are available on
his [YouTube channel](https://www.youtube.com/@wilangyutas9297). Some of the
audio is transcribed, and a smaller portion has been translated into Mandarin.
Permission to republish was generously provided by Wilang Yutas's
collaborator, 劉宇陽.

All audio is available. All text is Atayal (`tay`), Sekolik dialect. The
corpus has 82 XML files: 34 transcript files with 3,012 sentences and 48
audio-only files.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Atayal<br>Sekolik |
| --- | --- |
| Word count | 24,991 |
| Total audio | 11.8h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 6.8h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 5.1h |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 1,626 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 |
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


## Notes and Issues

* Many of the videos lack transcripts. These have XML files that point to the audio file, but there are no `<S>` elements.
* Many other videos have only partial transcripts. In these cases, the main XML contains only the transcribed part of the audio. A second XML with the postfix `_untranscribed` has no `<S>` elements and references the remaining audio.
* Segments that were not transcribable are marked as `<UNCLEAR/>`.
* A caption that is nothing but question marks is untranscribed audio, not a sentence: its clip is listed in the video's `_untranscribed` file and its sentence ID is retired, not reused. This applies to two captions, `Atayal_8` and `Atayal_9` of `20190407_Yutas_Wilang_di5duan_Lowsing_Watan_MVI_1703`.
* Many videos involve multiple speakers. The source captions put additional speakers in parentheses without separate timestamps. The corpus retains their text and records `notes="multiple speakers"`, but it cannot provide speaker-level timing.
* The transcriber wrote notes on Japanese loanwords in parentheses after the word, e.g. `cyolo(日: ちょっと)`. These notes are not speech: they are taken out of the sentence text and recorded in its FORM `notes`, naming the word (e.g. `transcriber's Japanese gloss: cyolo = ちょっと`; 17 notes in 13 sentences); the loanword stays.
* One Mandarin translation marks a missing stretch with `(???)`; the mark is removed and the translation's `notes` says it is uncertain, quoting the source.
* A few sentences quote Japanese song lyrics (kana/kanji) and one sentence contains a Bopomofo fragment (`ㄇ`) from the transcriber; these are faithful to the source subtitles and are intentionally kept.
* Timestamps come from the source captions and may not align perfectly with the audio.

***

## Corpus Processing

`CodeAndDocs/generate_xml.sh` rebuilds all 82 XML files from the committed transcripts and [video manifest](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/WilangYutasVideos/CodeAndDocs/video_manifest.tsv), without scraping YouTube. It uses the current FormosanBank cleaner, accent-removal standardization and Ortho94 phonology. The actual tool revision is recorded in [provenance.json](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/WilangYutasVideos/CodeAndDocs/provenance.json); it is not a required checkout pin. Source speaker notes remain attached to both FORM tiers.

The reviewed inputs preserve the published corrections and contain 3,014 timestamped captions, 237 translation lines and five wrapped caption continuations. All recording filenames, audio endpoints and TEXT/S IDs are preserved, except the two retired sentence IDs described under Notes; the captions become 3,012 sentences. Repeated utterances, code-switching and transcription gaps remain part of the corpus. Pure editorial recheck markers are retained in notes, and real translations retain their text.

Source checks and regression tests run separately from regeneration. Two unchanged-input builds must reproduce the same output, and final QC still requires source review. The [corpus README](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/WilangYutasVideos/README.md) gives the commands and processing caveats.

`download_audio_data.sh` retrieves the reviewed published audio revision from Hugging Face and checks the XML inventory. It does not resample or resegment the recordings; `--dry-run` checks the remote inventory without downloading audio.

`CodeAndDocs/refresh_source.sh` is the optional source refresh. It needs network access and never writes XML. `refresh_source.sh captions` re-fetches the channel's caption files into `CodeAndDocs/raw_scrape/`; `refresh_source.sh audio` downloads each video's audio from YouTube and cuts the per-sentence and untranscribed clips from the built XML's timings (needs `yt-dlp`, `ffmpeg` and `ffprobe`).

***

## **Access Details**

* The repo containing this corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/WilangYutasVideos).

***

## **Copyright**

CC BY-NC 4.0

Permission was provided by 劉宇陽 on 2024-12-26; evidence: ask maintainer.

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Wilang Yutas. (2019). *Wilang Yutas YouTube Channel*. YouTube. https://www.youtube.com/@wilangyutas9297
