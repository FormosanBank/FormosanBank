# Latham 1862 Comparative Philology

This corpus contains the Formosan lexical data from Robert Gordon Latham's 1862 _Elements of Comparative Philology_ (printed pp. 315–318), a nineteenth-century comparative wordlist. It comprises 62 lexical entries across two historically attested Formosan languages — Siraya (`fos`) and Babuza-Favorlang (`bzg`) — each paired with an English gloss. Because the source scan has no text layer, the table was transcribed by hand from the page renders and independently checked against the source. The historical spelling is preserved as-is; no modern orthographic standard or phonology exists for these varieties, so none is inferred.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | bzg<br>Favorlang | Siraya |
| --- | --- | --- |
| Word count | 26 | 38 |
| Total audio | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 | 0 |
| Translated words |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 26 | 38 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 0 | 0 |
| Morphologically segmented | 0 | 0 |
| Glossed words | 0 | 0 |

***

<!-- CORPUS STATS END -->


## **Corpus Processing**

The hand transcription lives in a reviewed, page-addressed source ledger (`CodeAndDocs/source_ledger.tsv`), from which `CodeAndDocs/build_lexical_xml.py` rebuilds the XML; every emitted field is independently verified against the ledger. Each source cell becomes one lexical `S` record, and comma-separated source variants become separate `FORM kindOf="alternate"` entries. The maintenance pipeline (`CodeAndDocs/make_xml.sh`) then runs `clean_xml.py` (a verified no-op — the transcription is already clean) and `standardize.py --copy`, so the `kindOf="standard"` tier is a faithful, letter-for-letter copy of the original, with Latham's historical diacritics (`â á ó é à`) preserved. There is no `PHON` tier, by design: a historical lexical table with no living pronunciation reference gets no phonology.

***

## **Access Details**

* The repo containing this corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Latham-1862).

***

## **Copyright**

Public domain. The source, Latham (1862), is in the public domain.

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

Latham, R. G. (1862). _Elements of comparative philology_. London: Walton and Maberly.
