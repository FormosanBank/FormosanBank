# Utrecht Manuscript Word List

This corpus contains 1,061 Siraya lexical records from Christopher Joby's corrected database of the seventeenth-century Utrecht Manuscript word list. Each row of Joby's source table becomes one sentence-level record.

The table sets several witnesses side by side, and the corpus keeps the ones that are Siraya or a translation of it. Joby's own corrected reading is the original `FORM`. Where van der Vlis's 1842 edition reads differently, his form is kept as an `alternate` `FORM`, so the two readings can be compared without either being lost — there are 82 such alternates. Van der Vlis's Dutch is the primary translation and the manuscript's own Dutch is kept alongside it, marked `ver="alt"`, wherever the two differ; Joby's English is the English translation.

The source supplies a morphological analysis for two entries, and those carry `W` and `M` tiers. The remaining 1,059 have none, which is the normal state for a word list. There is no audio. FormosanBank currently has no Siraya standard-orthography target or phonology profile, so the corpus preserves the original forms without adding standard `FORM` or `PHON` tiers.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Siraya |
| --- | --- |
| Word count | 1,205 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 1,193 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 0 |
| Morphologically segmented | 2 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


## **Access Details**

The XML, the source ledger, the reconciliation table, and the deterministic build code are available in the [FormosanBank repository](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/UtrechtManuscriptWordList). Joby's corrected source database is published by [Neerlandistiek](https://neerlandistiek.nl/wp-content/uploads/2021/07/UM-database.pdf).

***

## **Corpus Processing**

The corpus is generated from the source table by `CodeAndDocs/generate_xml.sh`, which rebuilds it from a committed word-level extraction of the pinned database rather than from the PDF, so the build needs no external file. The commit the published XML was built against is recorded in [`CodeAndDocs/provenance.json`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/UtrechtManuscriptWordList/CodeAndDocs/provenance.json). Quality checks live in a separate `CodeAndDocs/validate.sh`, so a failing check never blocks a rebuild.

Editorial material is separated from translation by which column it appears in. Joby's database marks scholarly apparatus in square brackets, and the column decides what a bracket means: in the two Dutch columns it is always a remark about the manuscript — `[sic]`, a corrected reading, a note that a word was struck through, a dictionary citation — and moves to a `notes` attribute rather than being published as part of the translation. In Joby's own English column a bracket is his own elaboration, and stays inline. Where a translation carries a comma the Siraya form does not, the readings are separated into `ver="alt"` translations.

Two of the source's own conventions are preserved rather than normalized away. Where Joby supplies a letter the manuscript lacks, the supplied reading is published and the manuscript reading recorded in a note. Where he gives an uncertain alternative, it is recorded as a note on the form rather than presented as a second headword.

***

## **Corpus Notes**

For eleven consecutive entries, beginning at the manuscript's own page 12, the source table fills its two van der Vlis columns in the opposite order to the rest of the table. The build restores the intended order. This is worth recording because the earlier published version of this corpus reproduced the anomaly, printing the Siraya form as its own Dutch translation.

One entry, `pasagoualalingaua ng` 'mirror', carries a space that both other witnesses set solid. It is published as the source has it.

***

## **Copyright**

Christopher Joby's corrected transcriptions and translations are licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). Commercial AI use requires prior written permission under the FormosanBank terms.

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

Joby, C. (2021). Revisions to the Siraya lexicon based on the original Utrecht Manuscript: A case study in source data. *Historiographia Linguistica*, 48(2-3), 177-204.
