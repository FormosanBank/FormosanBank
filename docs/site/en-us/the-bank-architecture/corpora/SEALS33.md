# SEALS 33

## **Overview**

These are the translated sections of the [2024 SEALS conference](https://sites.google.com/view/seals33/national-languages?authuser=0) (SEALS 33), graciously provided by the authors. 

The 2024 South East Asian Linguistic Society meeting took place in Taipei. The corpus contains all 29 parallel source rows per Formosan language, with Mandarin translations and English translations for 16 program titles per language.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Seediq<br>unknown | Saisiyat |
| --- | --- | --- |
| Word count | 560 | 612 |
| Total audio | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 | 0 |
| Translated words |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 136 | 183 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 560 | 612 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 | 0 |
| Morphologically segmented | 0 | 0 |
| Glossed words | 0 | 0 |

***

<!-- CORPUS STATS END -->


## **Corpus Processing**

The original hand transcription is preserved in `CodeAndDocs/pre_correction_snapshot/`. The final build uses a committed structured snapshot of all 29 parallel source rows, checked against the complete official page. `CodeAndDocs/generate_xml.sh` rebuilds the XML, then runs current `clean_xml.py`, `standardize.py --remove_accents`, and `add_phonology.py --orthography Ortho94`. Original and standard FORM, PHON, and all source translations are retained. Source refresh is separate from generation; all required build inputs are committed. The [build provenance](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/SEALS33/CodeAndDocs/provenance.json) records the tools used without pinning future builds.

The source audit checks every original FORM and translation. Focused tests protect source coverage, reconstructed forms, published identities and the scoped validation exception.

***

## **Corpus Notes**

* The Seediq file does not identify a dialect, so its dialect is reported as unknown.
* S25 is a title containing reconstructed proto-forms (`*-ʔ, *-h, *-∅`), not an ungrammatical example. Both titles remain included under the merged corpus ruling. The Saisiyat FORM now follows the actual Saisiyat source title instead of the earlier English copy. The four source-inherent V129 HARD findings remain visible and are checked by a corpus-owned exception test.
* The Saisiyat file uses `:` for vowel length; it is retained in PHON for Saisiyat but treated as punctuation for Seediq.
* Published TEXT identities are preserved, and so is every sentence identity except two. The Seediq file previously had source rows 21 and 22 transposed, so Seediq S21 and Saisiyat S21 named different talks. The two languages are now aligned on content: **Seediq S21 is “Word stress in Yami” (previously S22), and Seediq S22 is “Piuma Paiwan stress in directional evaluation” (previously S21).** If you have cited Seediq S21 or S22 from an earlier release, remap those two references; no other identity in either file has changed.
* The source conference abbreviation and paragraph boundaries are retained. Mandarin punctuation follows the source with current Chinese quote normalization.
* There is no audio or word/morpheme analysis.

***

## **Access Details**

* The repo containing the SEALS 33 corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/SEALS33).

***

## **Copyright**

CC BY-NC 4.0

Rights source: Hsiu-chuan Liao, 2025-04-16; evidence: ask maintainer. This preserves the published license under POL-042/043; the spelling change requires maintainer merge review.

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* SEALS 33 Organizing Committee. (2024). 國家語言專區. SEALS 33. https://sites.google.com/view/seals33/national-languages
