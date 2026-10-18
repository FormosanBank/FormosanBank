# Wilang Yutas Videos

Wilang Yutas was an Atayal elder who, with his collaborator 劉宇陽, recorded a large number of videos speaking in Atayal, which can be found on his [YouTube Channel](https://www.youtube.com/@wilangyutas9297). Some of the audio is transcribed, and a smaller portion has been translated into Mandarin. Permission to republish was generously provided by Wilang Yutas's collaborator, 劉宇陽.

All audio is available. All text is Atayal (`tay`), dialect Sekolik: 82 XML files, of which 34 carry transcripts.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Atayal<br>Sekolik |
| --- | --- |
| Word count | 25,001 |
| Total audio | 11.8h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 6.8h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 5.1h |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 1,594 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 |
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


# Notes

* Many of the videos lack transcripts. These have XMLs that point to the audio file, but there are no <S> elements.
* Many other videos have only partial transcripts. In these cases, the main XML contains only the transcribed part of the audio. A second XML with the postfix "_untranscribed" has no <S>s and a reference to a file that contains the remaining audio.
* Segments that were not transcribable are marked as `<UNCLEAR/>`.
* Many videos involve multiple speakers. The original transcriptions have the second speaker's text in parentheses. We replaced the parentheses with periods so that the text will be standard. People who want to do diarization can inspect `make_xml.py` to figure out how to mark text by speaker (note that we don't have timestamps for separate speakers).
* A few sentences quote Japanese song lyrics (kana/kanji) and one sentence contains a Bopomofo fragment (`ㄇ`) from the transcriber; these are faithful to the source subtitles and are intentionally kept.
* Time stamps are derived from the subtitles themselves. We do not guarantee that these align perfectly with the actual audio.

***

## **Corpus Processing**

The corpus is rebuilt in four steps, all committed under `CodeAndDocs/`:

1. `scripts/scrape.py` pulls the subtitle transcripts from the YouTube channel into `raw_scrape/`. These `.txt` files are committed, so the corpus text regenerates without network access.
2. `scripts/make_xml.py` converts the transcripts into FormosanBank XML (Chinese in filenames is converted to Pinyin).
3. The audio is downloaded: end users should run `./download_audio_data.sh` (requires `git-lfs`, `jq`, and the `hf` CLI) to pull the published audio from Hugging Face. Rebuilding from YouTube instead uses `scripts/download_audio.py` (requires `ffmpeg`), which downloads the audio, converts it to WAV, and segments it into units matching the subtitles (as accurately as the original time stamps allow).
4. `CodeAndDocs/make_xml.sh` runs the QC pipeline over `XML/`: `clean_xml.py` (character and punctuation canonicalization), `standardize.py --remove_accents` (creates the `kindOf="standard"` FORM tier; no spelling conversion table exists for this corpus, so the standard tier currently equals the original verbatim), and `add_phonology.py --orthography Ortho94` (IPA `PHON` tiers; Ortho94 is assumed for the original tier, as the transcripts predate Ortho113 and the two differ little for Atayal). Audio files are never touched by this pipeline.

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
