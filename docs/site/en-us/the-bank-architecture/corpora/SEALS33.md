# SEALS 33

## **Overview**

This corpus contains source-faithful text from the [SEALS 33 national-languages page](https://sites.google.com/view/seals33/national-languages?authuser=0), used with permission from the organizers.

The 2024 South East Asian Linguistic Society meeting took place in Taipei. The page presents parallel Saisiyat, Seediq, and Mandarin text, with English translations for program titles. The corpus retains 28 source rows per Formosan language.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Seediq<br>unknown | Saisiyat |
| --- | --- | --- |
| Word count | 550 | 597 |
| Total audio | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 | 0 |
| Translated words |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 126 | 168 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 550 | 597 |
| Morphologically segmented | 0 | 0 |
| Glossed words | 0 | 0 |

***

<!-- CORPUS STATS END -->


## **Corpus Processing**

The public reproduction package includes a structure-aware live-page scraper, a committed 29-row source snapshot, a deterministic XML generator, a complete coverage audit, and focused tests. `CodeAndDocs/reproduce.sh` rebuilds source tiers, verifies source alignment, runs the current XML cleaner, copies Ortho94 FORM into the machine-owned standard tier, generates original and standard PHON, and repeats the source audit. The Ortho94-to-Ortho113 tables contain no spelling rules for this material, so copy mode preserves the source's lexical hyphens.

***

## **Corpus Notes**

* The Seediq file does not identify a dialect, so its dialect is reported as unknown.
* The source contains 29 parallel rows. Row 25 is recorded in the public source snapshot but excluded from both language XML files under POL-016 because its Formosan titles contain reconstruction asterisks.
* TEXT IDs remain stable, and S IDs are the source row numbers. The deliberate row-25 exclusion leaves a gap between S24 and S26.
* The corpus has no audio and no word or morpheme analysis.

***

## **Access Details**

* The repo containing the SEALS 33 corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/SEALS33).

***

## **Copyright**

© 2023-2024 SEALS 33 organizing committee. Used by FormosanBank with permission.

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* SEALS 33 Organizing Committee. (2024). 國家語言專區. SEALS 33. https://sites.google.com/view/seals33/national-languages
