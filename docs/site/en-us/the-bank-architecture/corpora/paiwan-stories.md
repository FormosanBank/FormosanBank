# Paiwan Stories

## Overview

Three children's stories in Eastern Paiwan with Chinese translations:
*Dingding*, *Kavatjes ni vuvu* and *Maljialjian a qaciljay*.

### Source Materials

* Gesi Giling (2020), *Dingding* and *Kavatjes ni vuvu*, illustrated by
  Tjaiwan Giling. Both PDF colophons date the first printing to November 2020.
* *Maljialjian a qaciljay*, an undated bilingual Word document.

Three whole-story WAV recordings are available through the corpus download
script and FormosanBank's published Hugging Face audio contract. Each XML root
names its recording. The duration metric below counts `AUDIO` elements;
these whole-story references have no sentence timings and therefore report zero.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Paiwan<br>Eastern |
| --- | --- |
| Word count | 574 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 574 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 |
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


## Corpus Processing

The corpus contains 46 bilingual passages reconstructed from the committed,
reviewed transcription and source metadata. Source locators cover the text in
the two PDFs and all 15 Word-table rows; one row contains two passages.
Paratext and illustration-only material are identified separately.

The [build entrypoint](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Paiwan_Stories/CodeAndDocs/generate_xml.sh)
generates source tiers, then runs shared cleaning, copy standardization and
phonology. It uses current FormosanBank tools; the actual build revision is
recorded in [provenance.json](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Paiwan_Stories/CodeAndDocs/provenance.json).
Source documents are not fetched during reproduction.

## Notes and Issues

The recovered Maljialjian passage uses `S6a`, preserving every published TEXT
and sentence ID. Omitted or shifted Chinese translations are restored from
the sources. Published quotation corrections and documented typography are
retained. There is no source word or morpheme analysis.

Historical sentence-alignment files are unavailable. The three published WAVs
are preserved without resampling or inferred timings. Full illustrated sources
are not redistributed because they contain separate illustration and publisher rights.

## Access Details

The [corpus directory](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Paiwan_Stories)
contains the XML, reviewed transcription, metadata, build code and audio downloader.

## Copyright

CC BY-NC 4.0. Joshua Hartshorne recorded direct permission from the
Indigenous-text author, Gesi Giling (阮翠芳), on 2024-04-13; evidence: ask maintainer.
The central FormosanBank terms and AI-use addendum also apply.

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md),
if you use this corpus or a derived product in a publication, cite FormosanBank and:

* Juan, T. F., & Ruan, X. (2024). *Corpus of Paiwan stories* [Electronic resource].
