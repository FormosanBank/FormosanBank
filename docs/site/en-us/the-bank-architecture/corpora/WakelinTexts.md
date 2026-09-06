# The Wakelin Texts

This corpus contains the 6 glossed Yami texts [found here](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/WakelinTexts/CodeAndDocs/Original.pdf) in

> Indosan, S., Wakelin, G., Dararyaw, S., and Kalaku, S. (1958). Yami texts. Work Papers of the Summer Institute of Linguistics, University of North Dakota Session: Vol. 2, Article 7. 10.31356/silwp.vol02.07

They were collected on Orchid Island between 1955 and 1957. Every sentence has an English free translation, and the texts are segmented into words and morphemes with English glosses on both tiers. There is no audio.

**Before you use this corpus: it has an `original` tier and nothing else.** Every `FORM` is `kindOf="original"` — the text as the 1958 article prints it. There is **no `standard` tier and no `PHON` (IPA) tier** at any level. The article states no writing system and its transcription matches no orthography profiled in FormosanBank, so the corpus asserts neither a transliteration nor a pronunciation. Tooling that expects a standard tier will find none; read the original tier, and treat its spelling as the article's own.

***

<!-- CORPUS STATS START -->
### Corpus Statistics

| | Yami |
| --- | --- |
| Word count | 852 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 852 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 0 |
| Morphologically segmented | 840 |
| Glossed words | 840 |

***

<!-- CORPUS STATS END -->


### Notes

* **`?` is a letter, not punctuation.** It occurs 47 times, word-internally and word-finally, on all three tiers — `tau?` 'person', `uvi?` 'potato', `kayu?` 'tree' — and in plainly declarative sentences. It most plausibly writes a glottal stop that modern Yami spelling leaves unwritten, but that is **not confirmed**, and it is the single largest reason the writing system cannot be pinned down. Do not strip it as punctuation, and do not read a sentence containing it as a question.
* **`( )` marks a probable discrepancy** in the data, per the article's own key: `(n)aku`, `puken-(en)`, `(u)m-lavi`. This notation is preserved.
* **Hyphens mark morpheme boundaries** and are kept exactly as printed, at every level.
* An earlier release shipped a `standard` tier produced by `Yami_Wakelin_113.tsv`, a "conversion table" whose only rule deleted hyphens and which mapped no letters at all. That tier asserted nothing; both it and the table have been removed.

### Corpus Processing

The texts were transferred from the printed article to XML **by hand**, so the hand-typed XML is the corpus's source of record and is preserved in `CodeAndDocs/pre_correction_snapshot/`. The published XML is rebuilt from it by `CodeAndDocs/generate_xml.sh`, which runs a corpus-local parser and then the shared cleaner. There is deliberately no standardization and no phonology step.

The article prints 18 alternations with a slash — `nipi/niripi`, `varit/yaked`, `akak-aep-an/(mangday su aep)`. These record **the transcriber's uncertainty**, not alternatives the speaker offered, so they are not automatically split into one sentence per option. Each is classified by hand in `CodeAndDocs/alternative_decisions.json`: a clear spelling variant (overlapping letters, same gloss) becomes an `alternate` FORM sibling on the node that varies and on its ancestors; anything else — different lexemes, different glosses, a word against a phrase — becomes separate sentences, the first keeping the printed sentence number and the rest taking `b`, `c`, …. **No published FORM keeps a slash.**

A checked comparison of the snapshot against the article and its errata is published at [`CodeAndDocs/source_discrepancies.md`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/WakelinTexts/CodeAndDocs/source_discrepancies.md); six findings there are still open. The FormosanBank commit this corpus was built against is recorded in [`CodeAndDocs/provenance.json`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/WakelinTexts/CodeAndDocs/provenance.json).

***

# Copyright

**License:** CC BY-NC-ND 4.0

The individual authors could not be located. The publisher released the article as **CC-BY-ND**, and FormosanBank has **interpreted that licence liberally** in order to publish the texts with their glosses and translations; publication rights were confirmed by the FormosanBank maintainer on 23 August 2026. If you are a copyright owner, please reach out to us.

***

### Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Indosan, S., Wakelin, G., Dararyaw, S., and Kalaku, S. (1958). Yami texts. Work Papers of the Summer Institute of Linguistics, University of North Dakota Session: Vol. 2, Article 7. 10.31356/silwp.vol02.07
