# Yedda Palemeq Blog

### Overview

Yedda Palemeq, a Paiwan speaker and linguist, maintained a [blog](https://yeddapalemeq.blogspot.com/) with short Southern Paiwan examples, English translations, prose word explanations, and recordings. The corpus contains 668 source records represented as 671 sentences after three source-defined alternative splits. Some examples also occur in independently sourced FormosanBank collections; they are retained here with their blog provenance.

***

<!-- CORPUS STATS START -->
### Corpus Statistics

| | Paiwan<br>Southern |
| --- | --- |
| Word count | 5,877 |
| Total audio | 1.2h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 1.2h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 5,877 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 0 |
| Morphologically segmented | 4,475 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


### **Access Details**

* The corpus XML and retained processing code are available [in FormosanBank](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/YeddaPalemeqBlog).
* `CodeAndDocs/scripts/` rebuilds the published XML from a frozen snapshot of the scrape, with no network access. `CodeAndDocs/scrape/` holds the code that read the blog in the first place; the build does not run it, and a fresh scrape of a live blog will not reproduce the snapshot byte-for-byte.

***

### **Corpus Notes**

**Coverage**

* The corpus covers the author's numbered "Paiwan Every Day" series, not the whole blog. The live Blogger feed holds 846 posts; the other posts are essays, announcements, and other non-series material that was never in scope.
* The corpus holds 668 source records drawn from 641 post URLs, and the 2026-08-23 live-source audit matched every one of them against the feed. Six numbers in the series are nevertheless absent — 66, 183, 197, 480, 519, and 543. They have been missing since the corpus was first added and the reason is not recorded, so treat this as very nearly, but not quite, a complete run of the series.
* The audit restored 24 incomplete or omitted sentence translations and 41 exact word glosses. Phrase-level definitions were not assigned to individual words.

**Glossing**

* Examples are not necessarily glossed word by word; repeated words and common function words are often unglossed in the source. Glosses were matched within a single example only — a gloss is never reused from another example, since it may not be contextually correct. Where no gloss can be found, the `<W>` element's `<FORM>` is just a copy of the word in the example and no `<TRANSL>` is provided.
* Sometimes the same word is spelled differently in the main text and in the glosses. We have assumed the main text is correct and the gloss is incorrect; in those cases the gloss is ignored.
* The author did not provide morpheme-by-morpheme glosses, so no glossing is provided for individual morphemes.

**Morpheme (`<M>`) elements**

* Where the author parsed words into segments, those segments are preserved in `<M>` elements. Within such a sentence, a word we could not find a parse for is assumed to be monomorphemic and gets a single `<M>` — which is almost certainly incorrect in some cases.
* Where the author parsed *nothing* in a sentence, that sentence carries **no `<M>` elements at all**. An earlier version of this corpus gave every word a single `<M>` mirroring the word, which asserted a monomorphemic analysis the author never made. Those mirror morphemes have been removed, so 1,165 of the 5,643 `<W>` elements now have no `<M>` child. This is why "Morphologically segmented" above counts 4,475 rather than the full word count.
* In short: the presence of an `<M>` tier is itself information — it tells you the author analysed that sentence.

**Notation**

* Infixes are written with angle brackets inside the word, as the source writes them: `s<em>eljec-an`, `p<in>a-cun-an`. These are XML-escaped in the file (`s&lt;em&gt;eljec-an`), so any XML parser returns them as text. They are source notation, not markup — stripping tags naively will corrupt these words.

**Alternatives, audio, and duplicates**

* Where the source offers alternative wordings of one sentence — `qali/drava`, `tjangtjang / siyak`, `abar (yasi)` — each alternative becomes its own sentence record. The recordings for those three are excluded from the corpus: the author pronounces both alternatives in turn, which is not a recording of either single sentence and would be an ungrammatical utterance of the combined one. The files remain available as declared extras of the public audio dataset.
* Two duplicate sentence groups come from separate blog posts with distinct source URLs and audio, so both attestations are retained.

***

### Copyright

CC BY-NC 4.0, by permission of the author.

Yedda Palemeq gave FormosanBank permission to license this material. The blog
itself carries no public licence notice, so the licence rests on the author's
grant rather than on anything stated on the site.

***

### Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Palemeq, Y. (2021). Yedda Palemeq. Retrieved May 19, 2026, from https://yeddapalemeq.blogspot.com/
