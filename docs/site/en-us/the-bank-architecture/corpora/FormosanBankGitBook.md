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
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


## **Corpus Processing**

The published XML was produced from reviewed Paiwan, Mandarin, and English text ledgers with the corpus's `CodeAndDocs/process_raw.py` script. The source audit checks all 105 included records and every source-owned tier.

The reproduction wrapper builds into a temporary directory, runs the current cleaner, restores the reviewed source text, copies the standard form, derives Ortho113 phonology, runs the XML, text, and gloss validators, and compares all six outputs with the published XML byte-for-byte. The public repository retains the source PDF, reviewed ledgers, generator, source audit, unit tests, and resulting XML.

***

## **Corpus Notes**

This is a translation corpus, not a separate edition of the documentation. The English GitBook remains the canonical and most complete version.

***

## **Access Details**

* The corpus XML and retained processing code are available [in FormosanBank](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/FormosanBankGitBook).

***

## **Copyright**

CC-BY-NC

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Ruan, X. (2025). *Paiwan translation of FormosanBank manual*.
