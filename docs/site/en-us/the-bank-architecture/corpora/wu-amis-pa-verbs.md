# Wu (2006), The Analysis of Pa-Verbs in Amis

This corpus contains 29 Coastal Amis sentence variants from Joy Wu's 2006 paper, [The Analysis of Pa-Verbs in Amis](https://sil-philippines-languages.org/ical/papers/wu_joy-pa%20verbs.pdf). The paper identifies Haian/Coastal Amis from Changpin, Taitung. The XML has 154 W and 265 M, 33 sentence translations, and no audio.

All 13 source pages were reviewed. The corpus covers the sentence examples on pages 6–10; lexical tables and theory discussion are outside this sentence-example scope. The recorded exclusions cover repeated earlier examples, ungrammatical and questionable examples, forbidden alternatives and one starred translation. Person/car readings in 20c and both case forms of 36a remain separate, fully aligned variants. `TEXT/@source` carries the paper's URL and the SHA-256 of the transcribed PDF.

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

## Notes and Issues

The source segments `Pa-fli` but gives only the whole-word gloss `give`; its two morphemes therefore have no individual glosses. Source form/gloss mismatches and analytic nulls are preserved. Original and standard PHON use different vowel and lateral inventories, so the tiers do not imply strict phonemic equivalence — in particular the standard tier merges Wu's `u`/`o` distinction, because Ortho113 Coastal writes one `o` for /o~u/. The source paper supplies no audio.

Wu prints example 36a in two case forms. They are two sentences, `s36a` and `s36a-opt`, because the alternation is a competing lexeme with a different gloss (`t-u`/DAT-NCM against `i`/PREP) rather than a spelling variant.

The corpus carries its own build test suite under `CodeAndDocs/tests/`, which pins the reviewed source decisions — exact sentence and morpheme IDs, counts, the unglossed `Pa-fli` boundary and the retained exclusions — so neither a shared-tool change nor a transcription edit can move them silently. It runs as the `source-tests` check of `CodeAndDocs/validate.sh`, and is not part of the repository-wide test run.

## Access Details

XML and reproducible build inputs are in the [Amis-Pa-Verbs directory](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Amis-Pa-Verbs). Language is Amis (`ami`), dialect `Coastal`.

## Corpus Processing

The committed transcription tables preserve source spelling, W glosses, translations, exclusions and stable source IDs. The current source review restores obligatory `i/PREP` in example 32c (`*(i)`), 22 printed sentence endings and the two printed parts of `Pa-fli`. The latter retains W gloss `give`; its M parts have no individually supplied gloss and remain unglossed. No sentence or free translation is removed. Source `payau`, `ni/GEN-NCM`, `ku/NOM-NCM` and source `CaU` with additive standard `CAU` remain.

Seven analytic nulls are retained as `∅` in original S/W/M tiers; shared standardization removes them from S standard. Nulls are silent in PHON, except a whole-null FORM receives PHON `∅`. The six earlier reviewed correction records have been pruned: the transcription tables encode the same decisions, so each was re-applied as a no-op on every build. The decisions and their source locators remain in the corpus package.

Run `CodeAndDocs/generate_xml.sh` from the corpus package. It builds from committed inputs, applies corrections, cleans, standardizes and generates PHON with current shared tools, without a private PDF, network fetch or historical Git checkout. [provenance.json](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Amis-Pa-Verbs/CodeAndDocs/provenance.json) records the tools used for the committed output and does not pin future builds. Validation and source refresh are separate.

Original PHON uses [`Orthographies/Ortho94/Amis.tsv`](https://github.com/FormosanBank/FormosanBank/blob/main/Orthographies/Ortho94/Amis.tsv), the bank's existing Coastal Ortho94 profile, and converts through the existing [`Amis_94_113.tsv`](https://github.com/FormosanBank/FormosanBank/blob/main/Orthographies/ConversionTables/Amis_94_113.tsv); standard PHON uses Ortho113. Wu's letter inventory is Coastal Ortho94, so no corpus-specific orthography or conversion table is registered. The `u→o` spelling conversion merges Wu's `u`/`o` into Ortho113 Coastal's single `o`, which is the one reviewed phoneme-level difference.

The apostrophe is **not** converted. An earlier pass read Wu's `'` as the glottal stop /ʔ/ and mapped it to Ortho113's `^`; that was reverted in review. Ortho94 and Ortho113 agree that `'` is /ʡ/ and `^` is /ʔ/, so the claim departed from both standards rather than from one of them; the corpus carries the apostrophe in two tokens of a single word type and no `q` or `^` at all, so there is no contrast in it to record; and the bank spells this very lexeme with an apostrophe — `(ma)na'ay` 'not want' appears 81 times in standard tiers across the Amis corpora with `'` and never with `^`. [Source and conversion notes](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Amis-Pa-Verbs/CodeAndDocs/README.md) document these limitations and the exact source-inherent findings protected by tests.

## Copyright

**CC BY-NC-SA 4.0.** SIL International's published archive terms apply unless an item states otherwise; this paper has no conflicting terms. The maintainer verified the grant in January 2025. Credit Joy Wu and SIL International, retain the noncommercial/share-alike conditions, and identify the transcription and normalization changes. Rights evidence is available from the maintainer.

The corpus is also subject to the central FormosanBank [Terms of Use](../../additional-resources/terms-of-use.md) and [AI Use and Commercial Licensing](../../additional-resources/ai-use-and-commercial-licensing.md).

## Citation

In accordance with the Terms of Use, cite FormosanBank and:

Wu, Joy. 2006. The analysis of pa- verbs in Amis. Paper presented at the Tenth International Conference on Austronesian Linguistics, 17–20 January 2006, Puerto Princesa City, Palawan, Philippines.
