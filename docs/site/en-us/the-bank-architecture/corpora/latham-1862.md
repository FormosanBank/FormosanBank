# Latham 1862 Comparative Philology

This corpus contains the Formosan lexical data from Robert Gordon Latham's 1862 _Elements of Comparative Philology_ (printed pp. 315–318), a nineteenth-century comparative wordlist. It comprises 45 lexical entries across two historically attested Formosan languages — Siraya (`fos`) and Babuza-Favorlang (`bzg`) — each paired with an English gloss. A third column in the printed tables, headed "Sida", is transcribed but **not published**; see _Notes and Issues_. Because the source scan has no text layer, the table was transcribed by hand from the page renders and independently checked against the source. The historical spelling is preserved as-is; no modern orthographic standard or phonology exists for these varieties, so none is inferred.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Babuza-Favorlang<br>Favorlang | Siraya |
| --- | --- | --- |
| Word count | 31 | 16 |
| Total audio | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 | 0 |
| Translated words |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 31 | 16 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 | 0 |
| Morphologically segmented | 0 | 0 |
| Glossed words | 0 | 0 |

***

<!-- CORPUS STATS END -->


## **Corpus Processing**

The hand transcription lives in a reviewed, page-addressed source ledger (`CodeAndDocs/source_ledger.tsv`), from which `CodeAndDocs/build_lexical_xml.py` rebuilds the XML; every emitted field is independently verified against the ledger. The entry point is `CodeAndDocs/generate_xml.sh`, which builds from the ledger and then runs the shared `clean_xml.py` (a verified no-op — the transcription is already clean).

Each published source cell becomes one lexical `S` record. Where a cell gives two readings, the ledger's `reading_type` column decides how they are represented: two competing **lexemes** become two `S` records, the second taking the first's id plus `-opt`, while two spellings of one word stay in a single record as an original `FORM` plus a `FORM ver="alt"`. Latham's historical diacritics (`â á ó é à`) are preserved exactly.

**There is no `standard` tier and no `PHON` tier**, by design. Neither variety has an approved standard orthography — `standards.csv` leaves both blank — so there is nothing to transliterate into and nothing to compare an orthography profile against; no orthography check is run for them at all. Query the original `FORM`.

***

## Notes and Issues

**The Gabelentz "Sida" column is not published.** Latham's tables on printed pp. 316–318 carry a third Formosan column headed "Sida". Publishing it as Siraya would assert that Sida is the "Sideia" of the Klaproth/Vander Vlis table on p. 315, and FormosanBank does not make that identification. Its 24 cells are transcribed in the source ledger and marked excluded, so the decision is reversible without redoing the work, but no `S` record is emitted for them and 22 previously published records were withdrawn.

**The two Sideia readings are published as pronunciation variation within Siraya**, not as distinct dialects. Where Klaproth and Vander Vlis give different readings of the same entry, the second is a `FORM ver="alt"` on the same record. Latham's presentation suggests these may be two dialects; the corpus records that here rather than encoding it.

**The file name says more than the file contains.** The Siraya file is `latham_1862_sideia_sida.xml` and its `TEXT` id is `latham_1862_sideia_sida`, from when the Sida column was published in it. Published identifiers are never renamed, so both keep the old name.

Historical spellings have no approved standardization or pronunciation profile; query the original `FORM`. English headings are lexical glosses, not sentence translations. This written source supplies no audio.

***

## **Access Details**

* The repo containing this corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Latham-1862).

***

## **Copyright**

public domain. The source, Latham (1862), is in the public domain.

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

Latham, R. G. (1862). _Elements of comparative philology_. London: Walton and Maberly.
