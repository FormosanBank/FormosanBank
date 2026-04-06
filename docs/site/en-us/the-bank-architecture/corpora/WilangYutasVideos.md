# Wilang Yutas Videos

Wilang Yutas was an Atayal elder who, with his collaborator 劉宇陽, recorded a large number of videos speaking in Atayal, which can be found on his [YouTube Channel](https://www.youtube.com/@wilangyutas9297). Some of the audio is transcribed, and a smaller portion has been translated into Mandarin. Permission to republish was generously provided by Wilang Yutas's collaborator, 劉宇陽.

All audio is available. If it is transcribed, it is also diarized.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Atayal<br>Sekolik |
| --- | --- |
| Word count | 25,096 |
| Total audio | 4.1h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 4.1h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 1,649 |
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


# Notes

* Many of the videos lack transcripts. These have XMLs that point to the audio file, but there are no <S> elements.
* Many other videos have only partial transcripts. In these cases, the main XML contains only the transcribed part of the audio. A second XML with the postfix "_untranscribed" has no <S>s and a reference to a file that contains the remaining audio.
* Segments that were not transcribable are marked as <UNCLEAR>. 
* Many videos involve multiple speakers. The original transcriptions have the second speaker's text in parentheses. We replaced the parentheses with periods so that the text will be standard. People who want to do diarization can inspect `make_xml.py` to figure out how to mark text by speaker (note that we don't have timestamps for seprate speakers).
* Time stamps are derived from the subtitles themselves. We do not guarantee that these align perfectly with the actual audio.

***

## **Access Details**

* The repo containing this corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/WilangYutasVideos).

***

## **Copyright**

CC BY-NC

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Glosbe. (n.d.). Glosbe dictionary. https://glosbe.com. Accessed 2025.