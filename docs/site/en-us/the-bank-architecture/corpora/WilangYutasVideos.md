# Wilang Yutas Videos

Wilang Yutas was an Atayal elder who, with his collaborator 劉宇陽, recorded
a large number of videos speaking in Atayal. The recordings are available on
his [YouTube channel](https://www.youtube.com/@wilangyutas9297). Some of the
audio is transcribed, and a smaller portion has been translated into Mandarin.
Permission to republish was generously provided by Wilang Yutas's
collaborator, 劉宇陽.

All audio is available. All text is Atayal (`tay`), Sekolik dialect. The
corpus has 82 XML files: 34 transcript files with 3,014 timestamped sentence
records and 48 audio-only files.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Atayal<br>Sekolik |
| --- | --- |
| Word count | 24,957 |
| Total audio | 11.8h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 6.8h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 5.1h |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 1,644 |
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


# Notes

* Many of the videos lack transcripts. These have XML files that point to the audio file, but there are no `<S>` elements.
* Many other videos have only partial transcripts. In these cases, the main XML contains only the transcribed part of the audio. A second XML with the postfix `_untranscribed` has no `<S>` elements and references the remaining audio.
* Segments that were not transcribable are marked as `<UNCLEAR/>`.
* Many videos involve multiple speakers. The source captions put additional speakers in parentheses without separate timestamps. The corpus retains their text and records `notes="multiple speakers"`, but it cannot provide speaker-level timing.
* A few sentences quote Japanese song lyrics (kana/kanji) and one sentence contains a Bopomofo fragment (`ㄇ`) from the transcriber; these are faithful to the source subtitles and are intentionally kept.
* Timestamps come from the source captions and may not align perfectly with the audio.

***

## Corpus Processing

The text rebuild is pinned and does not scrape the live YouTube channel:

1. `CodeAndDocs/video_manifest.tsv` pins all 34 public transcript inputs by path, byte count, and SHA-256. It also declares all 82 XML outputs and the 48 audio-only records.
2. `CodeAndDocs/make_xml.py` accounts for every source line, omits only explicitly blank timestamp rows, and generates the complete XML tree.
3. `CodeAndDocs/audit_source_alignment.py` compares every generated pre-clean element to the pinned sources and requires a complete disposition for the 21 prior MT-quality findings.
4. `CodeAndDocs/reproduce.sh` runs source verification, cleaning, standard-tier generation, Ortho94 phonology, and nine corpus regression tests twice. Both passes must be byte-identical to the committed XML.

The reviewed source accounting covers 6,455 timestamp rows: 3,014 non-empty
rows are included and 3,441 blank rows are omitted. All 237 source translation
lines and five wrapped source continuations are accounted for. Source-authentic
Mandarin, Japanese, and Bopomofo content is retained.

End users can run `download_audio_data.sh` to retrieve the reviewed audio from
Hugging Face. Audio is outside the text rebuild and is never committed to the
FormosanBank repository.

***

## **Access Details**

* The repo containing this corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/WilangYutasVideos).

***

## **Copyright**

CC BY-NC

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Wilang Yutas. (2019). *Wilang Yutas YouTube Channel*. YouTube. https://www.youtube.com/@wilangyutas9297
