# Rau and Dong

### **Overview**

[The Rau-Dong Corpus](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/RauDong/XML) contains 20 morphologically parsed and glossed texts in Yami from Rau and Dong (2006).

***

<!-- CORPUS STATS START -->
### Corpus Statistics

| | Yami |
| --- | --- |
| Word count | 13,295 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 13,285 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 13,285 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 |
| Morphologically segmented | 13,295 |
| Glossed words | 13,295 |

***

<!-- CORPUS STATS END -->


### **Corpus Processing**

This corpus was originally published as a book. The version included in FormosanBank was scraped from a website prepared by the original authors. We have not checked whether there are differences between that source and the original book.

Since October 2026 the published XML is rebuilt reproducibly: `CodeAndDocs/generate_xml.sh` starts from a frozen snapshot of the XML as it was published (`CodeAndDocs/pre_correction_snapshot/`) and re-runs the shared cleaning, standardization and phonology tools; `CodeAndDocs/provenance.json` records the FormosanBank commit of the published build. The snapshot is not the original delivery: earlier in-place edits (quotation marks, one split sentence in text 10, translation fixes) are part of it.

***

### **Corpus Notes**

* The original text has morphemes marked with hyphens. This is retained in the "original" tier and removed from the "standard" tier. 

* Lexical accent is marked in the original tier but removed in the standard tier. 
* The pronunciation (PHON) tiers were regenerated with the current tools in October 2026: variant vowels are written `[o|u]`, morpheme hyphens and punctuation are not part of PHON, accented vowels map to their plain vowel, and the standard tier's `z` is `r` (a bug had made it `ɻ`, merging z and r).
* Glosses the book marks `?` are published as `<UNCLEAR/>`, as are the few word glosses left empty inside glossed sentences; one sentence whose translation the book marks as not clear (text 9, S23) carries no translation.

* There are differences relative to the reference text in terms of the frequency of glottal stops.

* Translations frequently have explanatory parantheticals. A few of these have been removed, but most remain.

![Yami Frequency Comparison](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/RauDong/CodeAndDocs/Yami_frequency_comparison.png)

***

### Citation

Rau, D. V., and Dong, M. N. (2006). Yami texts with reference grammar and dictionary. Institute of Linguistics, Academia Sinica. 

This corpus is available under CC BY-NC 4.0, with permission of the publisher and authors.