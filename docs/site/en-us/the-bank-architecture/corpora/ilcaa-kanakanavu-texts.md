# Asai et al. (2026) Kanakanavu Texts

This corpus is the Kanakanavu (`xnb`) text of Asai, Mei, Li and Tsuchida's 2026 *Kanakanavu Texts* (Research Institute for Languages and Cultures of Asia and Africa, Tokyo University of Foreign Studies): 44 narratives and the example sentences of the book's grammatical introduction, with the book's own English translations and, for the narratives and the introduction's numbered examples, its word and morpheme glossing. The introduction's word lists and the book's explanatory footnotes add single-word entries. The source is a born-digital PDF, so nothing was OCR'd. There is no audio.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Kanakanavu |
| --- | --- |
| Word count | 10,071 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 10,036 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 4 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 |
| Morphologically segmented | 9,942 |
| Glossed words | 9,942 |

***

<!-- CORPUS STATS END -->


## **Notes and Issues**

* **The standard tier is a transliteration into Ortho113.** The book writes Kanakanavu with IPA-style letters (`ʔ`, `ŋ`, `ə`). The standard tier writes `ʔ` as `'`, `ŋ` as `ng` and `ə` as `e`. It also writes `l` as `r`, as Ortho113 has a single `r`. Two distinctions are therefore lost in the standard tier: `ə` versus the rarer native `e`, and `l` versus `r`. The original tier keeps both.
* **The capital glottal stop `Ɂ` is written `ʔ`.** Four of the narratives print the glottal stop with this glyph. The original tier writes it as the ordinary `ʔ`, so a search for `ʔ` finds all of them.
* **Infix brackets stay in the original sentence form, not the standard one.** The original tier keeps the book's `<um>`; the standard sentence form drops the brackets. Word and morpheme forms keep their segmentation marks (`-`, `=`, `<...>`) as printed, and the morpheme tier carries the infix as `-um-`.
* **Spelling variants the book prints in parentheses are kept as alternatives.** For example `mu-usa (= mu-kusa)` is one sentence whose word carries `mu-kusa` as an alternative reading. Nine pairs are handled this way. Where the two readings would be glossed differently, or the book prints whole optional words, the second reading is its own sentence, with the same ID plus `-opt`.
* **The example-23 clauses.** The book prints square brackets around the pseudo-cleft clause in examples 23a to 23d. The original sentence form shows them as parentheses; the standard form and the word and morpheme forms have none.
* **`əhə kai` is one word.** In Naparamaci example 68 the book prints a single gloss, "interjection", under the two words, so they are published as one word and one morpheme.
* **Not every sentence has word-level analysis.** The introduction's word lists and the footnote entries are single words that the book does not segment; they carry a translation and no word or morpheme tier. Only three of the introduction's lexical examples come with the book's own morpheme analysis.
* **Not included.** The introduction's Table 1 (historical transcriptions by Tsuchida 1969, Szakos 1999 and the 2007 Basic Vocabulary) and two prose examples next to it are left out by decision. The village-labelled phonetic comparison on page 15 is also left out, because the book gives no written form for it.
* **Printed translation parentheses are kept.** The book's own clarifications, for example `Thereupon, (the girl) left`, stay in the English translations. One translation prints an em dash that the shared cleaning step writes as a hyphen.
* **Repeated passages are kept.** Repetition within a story is source data and is not removed.

***

## **Access Details**

* The repo containing this corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/ILCAA-Kanakanavu-Texts).

***

## **Corpus Processing**

Run `bash Corpora/ILCAA-Kanakanavu-Texts/CodeAndDocs/generate_xml.sh` in a FormosanBank checkout. It extracts the text from the committed source PDF, builds the XML, then runs FormosanBank's shared cleaning, standardization and phonology steps. The [README](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/ILCAA-Kanakanavu-Texts/README.md) documents the dependencies, the source coverage and every decision about the book's notation. The [build provenance](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/ILCAA-Kanakanavu-Texts/CodeAndDocs/provenance.json) records the FormosanBank commit the published XML was built against.

***

## **Copyright**

CC BY 4.0 (Creative Commons Attribution 4.0 International). The licence is stated on the source PDF itself (physical page 3); the rights holders are Paul Jen-kuei Li, Yi-Chun Chen, Hsiu-min Huang and Amy Ming-luan Chen (2026).

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

Asai, E., Mei, K., Li, P. J.-k., & Tsuchida, S. (2026). *Kanakanavu Texts* (P. J.-k. Li, Ed.). Research Institute for Languages and Cultures of Asia and Africa, Tokyo University of Foreign Studies.
