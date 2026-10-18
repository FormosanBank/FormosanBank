# Glosbe

## **Overview**

This corpus contains dictionary and translation-memory entries collected from the crowdsourced online dictionary Glosbe, for Amis, Atayal, Saisiyat and Truku: seven XML files with 5,670 sentences. Amis has one translation-memory file, `XML/Amis/Amis.xml` (4,508 sentences): 2,358 with an English translation only, 1,791 with English and Traditional Chinese, and 359 with Chinese only. The other files are the Amis, Atayal, Saisiyat and Truku dictionary entries and two small Atayal and Saisiyat translation memories, all translated into English. Religious (JW) material predominates in the translation memories.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Amis<br>unknown | Atayal<br>unknown | Truku | Saisiyat |
| --- | --- | --- | --- | --- |
| Word count | 62,679 | 585 | 115 | 622 |
| Total audio | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 | 0 | 0 | 0 |
| Translated words |  |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 59,315 | 585 | 115 | 622 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 28,133 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 | 0 | 0 | 0 |
| Morphologically segmented | 0 | 0 | 0 | 0 |
| Glossed words | 0 | 0 | 0 | 0 |

***

<!-- CORPUS STATS END -->


## **Corpus Processing**

The source is a frozen Glosbe crawl (captured 2026-05-14) recorded in `CodeAndDocs/source_records.jsonl`; the Traditional Chinese translations come from Joseph Lin's reviewed copy of the Amis–Chinese translation memory. `CodeAndDocs/generate_xml.sh` rebuilds every XML file from those records with the current FormosanBank tools and no network access: it applies the recorded hand edits, runs the shared cleaner, removes within-file duplicates, moves editorial material to notes, joins the Amis files, standardizes to Ortho113 and generates both pronunciation (`PHON`) tiers.

* **One Amis file.** An Amis sentence that appeared in both the Amis–English and the Amis–Chinese translation memory is one sentence carrying both translations. Sentences join when their Amis text is identical, or identical apart from spaces, commas, periods and dashes; texts that differ by a word, a letter, an apostrophe or a quotation mark are kept apart.
* **Editorial material goes to notes.** Scripture references, paragraph cross-references, list labels, captions and journal-citation tails are in the `notes` attribute of the FORM or translation, not in the text; bare list enumerators such as `(b)` are removed.
* **Search-highlight spaces removed.** The Chinese copy was scraped from Glosbe search pages that pad the searched word with spaces (`" o wacay`); the build removes that padding.
* **Withdrawn identifiers.** Every sentence id no longer published (joined Amis–Chinese sentences, grouped copies, three duplicate dictionary entries) is listed with the id that replaces it in `CodeAndDocs/withdrawn_ids.csv`.

Where one source form has several distinct translations, the additional ones are kept as separate `TRANSL` elements marked `ver="alt"`.

***

## **Corpus Notes**

Because this is a crowdsourced dictionary and translation memory, the linguistic accuracy and the rights attached to individual entries can vary. Treat entries as leads for review rather than as expert-verified dictionary records.

* Glosbe's own pages write the Amis glottal stop as `ˈ` and quotation marks as `‘ ’`; FormosanBank writes the glottal stop as `'` and quotations with `"`. Quotation repairs are recorded hand edits (`CodeAndDocs/manual_edits.xml`, logged in `CodeAndDocs/quote_corrections.csv`) checked against those Glosbe pages; the XML as it stood before any correction is preserved in `CodeAndDocs/pre_correction_snapshot/`.
* Glosbe entries generally do not identify a dialect, and a single file likely mixes dialects; the standardization assumptions per language are documented in the corpus README.

***

## **Access Details**

* The repo containing the Glosbe corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Glosbe).

***

## **Copyright**

**License:** CC BY-NC-SA 4.0, the licence under which Glosbe's terms of use make user-uploaded content available to other users. Every `TEXT` element records `copyright="CC BY-NC-SA 4.0"`. Glosbe content can include third-party translation-memory sources, so users must also follow those sources' rights, as well as the central FormosanBank [Terms of Use](../../additional-resources/terms-of-use.md).

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Glosbe. (2026). *Glosbe [language]-[translation language] dictionary and translation memory*. Cite the language pair, URL, and retrieval date recorded in the XML file used.
