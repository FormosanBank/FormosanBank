# Chang (2000) Seediq Reference Grammar

This corpus is the Seediq (`trv`) material from Chang Yung-li's 張永利 2000 *賽德克語參考語法* [Seediq Reference Grammar] (Yuan-Liou Publishing), transcribed from scans of the book and proofread against the printed pages. It has two files: the interlinear example sentences of chapters 3–4 (351 sentences, word- and morpheme-glossed) and the chapter 5 narrative, a `sumuladuc` 祭祀 ritual account (37 sentences). Glosses and translations are in Mandarin (`zho`).

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Seediq<br>Tegudaya |
| --- | --- |
| Word count | 1,766 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 1,766 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 |
| Morphologically segmented | 1,766 |
| Glossed words | 1,766 |

***

<!-- CORPUS STATS END -->


## **Notes and Issues**

<!-- Known limitations, source defects, and caveats a user should know before using
     this corpus. Keep it user-facing (what affects the data), not process history.
     Write "None known." if there are none. -->

* **Dialect.** The book says it describes the 霧社方言 (Wushe dialect), spoken in 南豐 and 互助 villages, with consultants from 互助村 (printed p. 37: 本文研究的是霧社方言). FormosanBank tags this dialect `Tegudaya` (德固達雅; also called Tgdaya, Paran, 霧社). The book also thanks a speaker of the 春陽 dialect, Pastor 張秋雄 (walis ukan), for "許多寶貴的意見" (p. 38).
* **Orthography.** The major Seediq writing systems (Church, ILRDF 94, ILRDF 113) are identical. Chang (2000) predates even ILRDF 94, but we treat the original tier as 113 for convenience. Note that the writing here differs from our other Seediq sources in a few systematic ways: some words are written with vowels that the other corpora leave out (`munekan`, elsewhere `mnekan`), and pronouns are hyphenated onto the preceding word (`sapah-mu`, elsewhere `sapah mu`). The significance of this is not currently clear. The standard tier keeps the book's spelling; it removes the morpheme hyphens, so the pronoun is joined to the word before it (`sapahmu`).
* **Scope.** Chapters 3 and 4 (printed pp. 54–148) and the chapter 5 narrative (pp. 151–159). Chapter 6, the basic vocabulary list, is not included. Examples the book marks ungrammatical (`*`) or marginal (`?`) are left out.
* **One printed example can be several sentences.** Where the book prints optional material in parentheses or alternatives with a slash, each grammatical reading is its own sentence (ids `R275`, `R275-opt`, …), and its translation is adjusted where the printed one covers more than one reading. A reading identical to an earlier example is published once.
* **One word per printed gloss.** Where the book prints one gloss under two words (e.g. `ani naq` 雖然, `kiya ka` 所以), the two are a single word element. A pronoun printed inside such a pair (`ani-ku naq`) is written as an infix, `ani<ku>naq` 雖然<我>.
* **Infixes.** At the word tier, an infixed word is written with angle brackets, e.g. `b<n>eebu` glossed `打<完成貌>`. Sentences keep the book's hyphens (`b-n-eebu`). Where the book glosses each hyphen piece in a row (`m-un-ekan` AF-完成貌-吃), the morphemes follow the book.
* **Unglossed words.** A word the book leaves unglossed is glossed `?`, e.g. the question particle `yee`.
* **Where the published text corrects the book.** Everywhere else the original tier follows the printed page. These are the only places where the data departs from the print, and each carries a `notes` attribute:

| Book (printed page, example) | Book prints | Published | Why |
| --- | --- | --- | --- |
| p. 83, 2b | `mah-un` glossed 吃-PF | 喝-PF | the object is 水 'water' |
| pp. 119–120, 11b | 用-AF--我 | 用-AF-我 | the double hyphen is a typo |
| p. 140, 17a | `musa meepah` | `m-usa m-eepah` | hyphenated as in the book's other examples |
| p. 145, 25b | no translation | the translation of 23b/24b | the parallel examples |
| p. 147, 28a | `m-aha-ku` glossed AF-去-你 | AF-去-我 | `-ku` is first person, as in 29a–c |
| p. 147, 28a | `turima` glossed 洗 | 洗（AF） | to match 29a–c |
| pp. 147–148, 29a–c | `m-aha-ku` glossed AF-去-你 | AF-去-我 | `-ku` is first person |
| p. 108, 5 | one gloss, AF-在, under `m-enaq/gaga` | the `gaga` reading glossed 在 | the book glosses bare `gaga` 在 in 6b |

* **A printing error left as printed.** The translation of 1c (p. 78) reads 煮飯的的人是我自己, with 的 doubled; its `notes` says so.
* **Brackets and spacing.** Square and lenticular brackets (an embedded clause, or emphasis) are removed from the Seediq and the translations; the sentence's `notes` records what was bracketed. Parentheses are full-width in Chinese and ASCII in Seediq. Translations have no space beside a Latin-script name (`我相信pawan會打敗walis的。`).
* **`da/di`** is published as `da`, with `di` as a variant FORM (`ver="alt"`).
* **Review notes.** Notes from a 2026 proofreading of the whole corpus against the book are in `notes` attributes, attributed to the source the reviewer cited.

***

## **Access Details**

* The repo containing this corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Seediq-Chang-Reference-Grammar).

***

## **Copyright**

CC BY-NC 4.0 (Creative Commons Attribution–NonCommercial), by permission of the author (Chang Yung-li).

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

Chang, Y. (2000). *賽德克語參考語法* [Seediq reference grammar]. Yuan-Liou Publishing.
