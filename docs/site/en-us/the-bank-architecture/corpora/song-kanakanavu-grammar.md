# Song Limei (2018), Introduction to Kanakanavu Grammar

This corpus is the Kanakanavu (`xnb`) material from Song Limei's 2018 *Kanakanafu yu yufa gailun* [Introduction to Kanakanavu Grammar] (Council of Indigenous Peoples), scraped from the official Alilin e-reader and reconciled page-by-page against the source page images. It comprises 699 grammar sentences — 650 of them with word- and morpheme-level interlinear glossing (3,477 words, 5,034 morphemes) — together with the book's Appendix 2A dictionary as a separate 870-entry lexicon. Text is in the Ortho113 orthography with Mandarin (`zho`) translations and glosses.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Kanakanavu |
| --- | --- |
| Word count | 5,256 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 5,256 |
| Morphologically segmented | 3,999 |
| Glossed words | 3,999 |

***

<!-- CORPUS STATS END -->


## **Corpus Processing**

The text was scraped from the official Alilin e-reader and reconciled page by page against the source page images. The book's own orthography discussion (reader pp. 31–44) describes the Ortho113 inventory — `ʉ` and `r`, no `l` — so no orthographic conversion is applied: the standard tier differs from the original tier only where the source's own apparatus does not belong in a standard surface.

Every departure from the printed text is recorded against a named record and a reader page; nothing is changed by a blanket rule. The full list is in the corpus [README](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Song-Kanakanavu-Grammar/README.md#recorded-per-record-corrections), and the reasoning behind the standard-tier decisions is in [`standard_surface_review.md`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Song-Kanakanavu-Grammar/CodeAndDocs/docs/standard_surface_review.md).

***

## **Corpus Notes**

* **Stress accents** (`á é í ó ú`) mark stress in the book, not distinct letters. They are kept in the original tier and folded out of the standard tier; PHON is accent-free on both tiers.

* **Interlinear conventions.** W forms keep the source's `-`, `=` and `<…>` notation. An infixed root keeps a gap hyphen and the infix is written `-X-` (`t<um>a-túturu` → `t-a`, `-um-`, `túturu`); each clitic morpheme keeps a leading `=` (`te=musu` → `te`, `=musu`).

* **Partial glossing is preserved, not invented.** On five page images the printed form and gloss lines do not align one-to-one. Those words are still segmented, but a morpheme the book does not gloss separately carries no gloss of its own; the word-level gloss is always present.

* **One repaired typesetting slip.** On reader p. 69 the aligned analysis line prints `takanaga` where the sentence line of the same example prints `takananga` (`takananga` occurs 22× in the corpus, `takanaga` twice — both inside that one analysis). It is repaired in the original tier as a recorded manual edit, so the standard tier and the phonetic tiers regenerate from the corrected form; the extraction ledgers still record exactly what the page prints.

* **Three examples come from the book's punctuation table (Appendix 1, p. 190), and its marks are not what they look like.**
  * *The song.* Row 10 of that table defines a hyphen used **in songs, to break lyrics to fit the musical score** — not morpheme boundaries. The one song example keeps those hyphens exactly as printed in the original tier. Its standard tier gives the running words, whose boundaries were recovered from an independent attestation of the same song: deleting the hyphens is not enough, since the last line would run together into a single word. This is the only place in the corpus where the standard tier is set from a source-checked decision rather than derived.
  * *The dash.* Row 8 defines `--`, written with two hyphens, as the Kanakanavu spelling of the **em dash** (破折號), whose Chinese equivalent is `―`. It is punctuation introducing an explanation or a list, not segmentation. The build renders it as a single `-` in the original tier, which the standard tier then inherits unchanged — so the two examples using it show a `-` that is a dash, not a morpheme boundary. They are the corpus's only two occurrences of a hyphen in a sentence-level standard form.

* **Dictionary variants are split, not concatenated.** Slash and semicolon alternatives and optional `(…)` material in Appendix 2A become separate single-form entries. Bound citation forms (a trailing hyphen, with no free-standing surface in the book) are excluded, and split variants that duplicate another record are dropped. Every exclusion is a recorded decision.

* **Repeated sentences are deliberate.** The book reuses example sentences to illustrate different points, so identical forms recur; each `S` carries its own `source` attribute naming the page and label it came from. Nothing is deduplicated.

***

## **Access Details**

* The repo containing this corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Song-Kanakanavu-Grammar).

***

## **Copyright**

CC BY-NC 4.0 (Creative Commons Attribution–NonCommercial), by permission of the author (Li-May Sung).

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

Song, Limei. (2018). *Kanakanafu yu yufa gailun* [Introduction to Kanakanavu Grammar]. *Taiwan nandao yuyan congshu*, 16. Council of Indigenous Peoples.
