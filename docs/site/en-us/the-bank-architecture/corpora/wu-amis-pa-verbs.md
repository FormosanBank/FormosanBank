# Wu (2006), The Analysis of Pa-Verbs in Amis

This corpus contains 29 Coastal Amis sentence variants from Joy Wu's 2006 paper, [The Analysis of Pa-Verbs in Amis](https://sil-philippines-languages.org/ical/papers/wu_joy-pa%20verbs.pdf). The paper identifies Haian/Coastal Amis from Changpin, Taitung. The XML has 154 W and 265 M, 33 sentence translations, and no audio.

All 13 source pages were reviewed. The corpus covers the sentence examples on pages 6–10; lexical tables and theory discussion are outside this sentence-example scope. The recorded exclusions cover repeated earlier examples, ungrammatical and questionable examples, forbidden alternatives and one starred translation. Person/car readings in 20c and both case forms of 36a remain separate, fully aligned variants.

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Amis<br>Coastal |
| --- | --- |
| Word count | 154 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 154 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 0 |
| Morphologically segmented | 154 |
| Glossed words | 154 |

***

<!-- CORPUS STATS END -->

## Access Details

XML and reproducible build inputs are in the [Amis-Pa-Verbs directory](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Amis-Pa-Verbs). Language is Amis (`ami`), dialect `Coastal`.

## Corpus Processing

The committed transcription tables preserve source spelling, W glosses, translations, exclusions and stable source IDs. The current source review restores obligatory `i/PREP` in example 32c (`*(i)`), 22 printed sentence endings and the two printed parts of `Pa-fli`. The latter retains W gloss `give`; its M parts have no individually supplied gloss and remain unglossed. No sentence or free translation is removed. Source `payau`, `ni/GEN-NCM`, `ku/NOM-NCM` and source `CaU` with additive standard `CAU` remain.

Seven analytic nulls are retained as `∅` in original S/W/M tiers; shared standardization removes them from S standard. Nulls are silent in PHON, except a whole-null FORM receives PHON `∅`. The six earlier reviewed correction records are retained and their file path now reaches the generated XML.

Run `CodeAndDocs/generate_xml.sh` from the corpus package. It builds from committed inputs, applies corrections, cleans, standardizes and generates PHON with current shared tools, without a private PDF, network fetch or historical Git checkout. [provenance.json](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Amis-Pa-Verbs/CodeAndDocs/provenance.json) records the tools used for the committed output and does not pin future builds. Validation and source refresh are separate.

Original PHON uses Coastal Ortho94 values with Wu's explicit apostrophe /ʔ/ and q /ʡ/ spellings; standard PHON uses Ortho113. Wu's dissertation phonetic key and its repeated version of example 36a establish the distinction in `Ma-na’ay`. The source form is preserved, standard apostrophe becomes `^`, and both PHON tiers give /ʔ/. The existing `u→o` spelling conversion retains its reviewed phoneme-level difference. [Source and conversion notes](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Amis-Pa-Verbs/CodeAndDocs/README.md) document these limitations and the exact source-inherent findings protected by tests.

## Copyright

**CC BY-NC-SA 4.0.** SIL International's published archive terms apply unless an item states otherwise; this paper has no conflicting terms. The maintainer verified the grant in January 2025. Credit Joy Wu and SIL International, retain the noncommercial/share-alike conditions, and identify the transcription and normalization changes. Rights evidence is available from the maintainer.

The corpus is also subject to the central FormosanBank [Terms of Use](../../additional-resources/terms-of-use.md) and [AI Use and Commercial Licensing](../../additional-resources/ai-use-and-commercial-licensing.md).

## Citation

In accordance with the Terms of Use, cite FormosanBank and:

Wu, Joy. 2006. The analysis of pa- verbs in Amis. Paper presented at the Tenth International Conference on Austronesian Linguistics, 17–20 January 2006, Puerto Princesa City, Palawan, Philippines.
