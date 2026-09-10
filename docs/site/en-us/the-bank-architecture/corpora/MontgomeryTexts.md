# The Montgomery Texts

This corpus contains three Amis texts with word-level segmentation, English word glosses and English sentence translations, digitized from [this publication](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/MontgomeryTexts/CodeAndDocs/Original.pdf):

> Tamih and Montgomery, Robert L. (1962) Amis text. Work Papers of the Summer Institute of Linguistics, University of North Dakota Session: Vol. 6, Article 6. 10.31356/silwp.vol06.06

The article uses a 1962 SIL field transcription that it never names; it was identified afterwards (see Notes). Each file's first sentence is the text's **printed title**, which the article sets over its own word-aligned English gloss line, so the titles are published as sentences like any other.

The texts are segmented into words but **not into morphemes**: the hyphens in the forms mark morpheme boundaries, but the article gives no morpheme-by-morpheme gloss line, so no morpheme tier is invented.

The `standard` tier is a real transliteration of the original through Akiw's letter correspondences below, not a copy of it: 185 of the 391 sentence- and word-level forms differ, including every sentence-level form.

> **The `PHON` (IPA) tier was regenerated in September 2026, and 568 of its
> 788 values changed.** If you took a copy before then, refresh it. Three
> things moved: the retired bare-tilde variant notation (`o~u`) became the
> current `[o|u]` form; segmentation hyphens were stripped, as a PHON should
> not carry them; and a wrong cell in the orthography profile was corrected —
> it had given the letter `l` the sound /d/, where Akiw's own example
> (`tamlaw` → `tamdaw` "people", /tamɬaw/) shows it writes /ɬ~ɮ/. Before the
> fix, the same word was transcribed /dafak/ from the original tier and
> /ɬafak/ from the standard. They now agree on every element, and no value
> carries an uncertainty marker.

***

<!-- CORPUS STATS START -->
### Corpus Statistics

| | Amis<br>unknown |
| --- | --- |
| Word count | 358 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 358 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 |
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


### Notes

Many thanks are owed to Hsu Cheng-Wen "Akiw", who helped identify the orthography. Her notes follow.

1. Letter Correspondences

These are some identified differences between the original orthography and the current standard.

|Original | Ortho113 | |
| ts	| c |	|
| ?	| '	| glottal stop |
| ř	 | r | |	
| r	| l	| |
| l	| d	| e.g., tamlaw → tamdaw (“people”) |

The status of the diacritic on `f` (which is rare — one word, `ma-sasi?af̆a?ařaw`) is uncertain, and remains so. The published XML writes it as `f` with a combining breve. A high-resolution reading of the scan suggests the mark is a caron, matching the `ř` elsewhere on the same line, but a single glyph on a 1962 mimeograph is not enough evidence to change a published letter, so it stands. The reasoning is recorded in the corpus's [`CodeAndDocs/source_discrepancies.md`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/MontgomeryTexts/CodeAndDocs/source_discrepancies.md).

The import of hyphens, which are used sporadically, has not been ascertained. In the published data they are treated as morpheme boundaries: kept on the word tier, and removed from sentence-level `standard` forms so that tier reads as running text.

The correspondence table audits cleanly through IPA — all five rows confirmed, no information loss. The `dialect` attribute is left as `unknown`: the article does not say, and nothing in the orthography narrows it. (Southern Amis in particular is ruled out rather than suggested — Ortho113 marks `f` and `o` as unused in Southern, and these texts are full of both.)

4. Two English equivalents for one word

The article's gloss line sometimes gives two English readings separated by a slash — `good/holy`, `noon/lunch`, `trip/walk`, `whole/all`, `and/with`. The Amis word does not vary, only its English rendering, so these are not published as separate sentences. Each is a primary translation plus a second one marked `ver="alt"` on the same word. No published translation keeps a slash.

2. Omission of the central vowel “e”

It appears that the central vowel is missing in many places:

mahřek	-> maherek	("finish")
tstsay	-> cecay	("one")
pafri	-> pafeli	("give")

3. Glides are used inconsistently. 

soar → sowal (“words”)
tsiwro → ciwlo(“elders” / 長老— loanword  ) 

***

# Copyright

**License:** CC BY-NC-ND 4.0

The individual authors cannot be located. The publisher — the Summer Institute of Linguistics / University of North Dakota — released the article as **CC-BY-ND**, and FormosanBank has **interpreted that licence liberally** in order to publish the texts with their glosses and translations. Publication rights were confirmed by the FormosanBank maintainer on 23 August 2026. If you are a copyright owner, please reach out to us.

***

### Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Tamih and Montgomery, Robert L. (1962) Amis text. Work Papers of the Summer Institute of Linguistics, University of North Dakota Session: Vol. 6, Article 6. 10.31356/silwp.vol06.06
