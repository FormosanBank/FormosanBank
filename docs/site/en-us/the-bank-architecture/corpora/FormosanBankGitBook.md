# FormosanBank GitBook

## **Overview**

This corpus contains translations of key FormosanBank GitBook pages into Formosan languages. The long-term goal is to provide at least the most critical pages in each Formosan language.

The current public corpus contains 105 aligned records from six GitBook sections in Eastern Paiwan, generously contributed by Xuan Ruan. Each entry also retains its English and Mandarin source text.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Paiwan<br>Eastern |
| --- | --- |
| Word count | 2,007 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 2,007 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 2,007 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 |
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


## Notes and Issues

These translations preserve historical manual text. Use current POLICIES.md and the committed English GitBook documentation for project guidance. Source names, language lists, repeated citations, and the literal English/Chinese licence-link labels remain part of the corpus. Generated PHON may contain uncertainty stars for unsupported borrowed letters, including where it is applied to non-Paiwan names. Two records carry known defects: in the Welcome roster the group heading `Advisory Board` sits inline among the personal names, because the source sets the two lists in one column; and the language-list record's Mandarin tier reproduces the source's untranslated Latin list rather than Mandarin. Records that are lists of names count toward this corpus's word totals. This written source supplies no audio.

***

## **Access Details**

* The corpus XML and retained processing code are available [in FormosanBank](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/FormosanBankGitBook).

***

## **Corpus Processing**

Run `./CodeAndDocs/generate_xml.sh` from the corpus directory using the current FormosanBank environment. It generates source tiers from the reviewed Paiwan, Mandarin, and English ledgers, then runs shared cleaning, standardization with `--remove_accents`, and Ortho113 phonology. The [corpus README](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/FormosanBankGitBook/README.md) gives reproduction and validation commands; [build provenance](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/FormosanBankGitBook/CodeAndDocs/provenance.json) records the shared tools used.

The source is a nine-page trilingual PDF rather than the GitBook pages it mirrors, because only the PDF aligns Paiwan, Mandarin and English record by record. Its Mandarin is a distinct translation, segmented to parallel the English; the Mandarin edition of this site words the same content differently, and has no counterpart page for one of the six sections. The public package retains that PDF, the reviewed ledgers, stable source keys, parser, source audit, and focused tests. All 315 source fields were checked in their original column order. The three recovered lists have new IDs; all 102 earlier sentence IDs still identify the same source passages. Two builds reproduced all six XML files from the public inputs alone. Validation and source review are separate from generation.

***

## **Copyright**

CC BY-NC 4.0. Xuan Ruan's permission was recorded on 2025-02-11. The corpus README records the rights statement; FormosanBank's [Terms of Use](../../additional-resources/terms-of-use.md) also apply, including the commercial AI restriction. Historical licensing text inside the translated manual does not replace the corpus rights statement.

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Ruan, X. (2025). *Paiwan translation of FormosanBank manual*.
