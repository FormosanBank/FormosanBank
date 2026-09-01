# SEALS 33

## **Overview**

These are the translated sections of the [2024 SEALS conference](https://sites.google.com/view/seals33/national-languages?authuser=0) (SEALS 33), graciously provided by the authors. 

The 2024 South East Asian Linguistic Society meeting took place in Taipei. The national-languages page was available in Seediq and Saisiyat, as well as Mandarin and English.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Seediq<br>unknown | Saisiyat |
| --- | --- | --- |
| Word count | 560 | 604 |
| Total audio | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 | 0 |
| Translated words |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 136 | 176 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 560 | 604 |
| Morphologically segmented | 0 | 0 |
| Glossed words | 0 | 0 |

***

<!-- CORPUS STATS END -->


## **Corpus Processing**

The short Seediq and Saisiyat translations were aligned with the corresponding Mandarin and English text and copied by hand into two FormosanBank XML files; there is no scraper, so the hand-built XML (preserved as a pristine snapshot in `CodeAndDocs/pre_correction_snapshot/`) is the reproduction baseline. From that baseline, `CodeAndDocs/make_xml.sh` regenerates the published `XML/` in three steps: `clean_xml.py` (punctuation and Unicode cleanup), `standardize.py --remove_accents` (creates the `kindOf="standard"` FORM tier; no spelling conversion is applied, as the transcription is already in the standard orthography), and `add_phonology.py --orthography Ortho94` (adds IPA `PHON` tiers). The published XML thus includes original and standard FORM tiers, IPA, and both translations.

***

## **Corpus Notes**

* The Seediq file does not identify a dialect, so its dialect is reported as unknown.
* S25 in both files is a talk title containing reconstructed proto-forms (`*-ʔ, *-h, *-∅`). The asterisks are faithful to the source; the Saisiyat S25 is actually the English title, so its PHON is English rendered through the Saisiyat profile.
* The Saisiyat file uses `:` for vowel length; it is retained in PHON for Saisiyat but treated as punctuation for Seediq.

***

## **Access Details**

* The repo containing the SEALS 33 corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/SEALS33).

***

## **Copyright**

CC-BY-NC

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* SEALS 33 Organizing Committee. (2024). 國家語言專區. SEALS 33. https://sites.google.com/view/seals33/national-languages
