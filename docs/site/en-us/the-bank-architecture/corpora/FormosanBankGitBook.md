# FormosanBank GitBook

## **Overview**

This corpus contains translations of key FormosanBank GitBook pages into Formosan languages. The long-term goal is to provide at least the most critical pages in each Formosan language.

The current public corpus contains six Eastern Paiwan pages, generously contributed by Ruan Xuan. Each entry also retains its English and Mandarin source text.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Paiwan<br>Eastern |
| --- | --- |
| Word count | 1,855 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 1,855 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 1,855 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 |
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


## **Corpus Processing**

The published XML was produced from aligned Paiwan, Mandarin, and English page text with the corpus's `CodeAndDocs/process_raw.py` script. The script creates one sentence per aligned entry and records the language, Eastern dialect, citation, and copyright metadata.

The post-conversion pipeline is wrapped by `CodeAndDocs/make_xml.sh`, which runs three steps over `XML/`: `clean_xml.py` (punctuation and Unicode cleanup; currently a content no-op for this corpus), `standardize.py --remove_accents` (creates the `kindOf="standard"` FORM tier — here identical to the original, whose transcription is already in the standard orthography), and `add_phonology.py --orthography Ortho113` (adds a `PHON` tier with IPA for each FORM). Characters outside the Paiwan orthography — digits and Latin loanwords such as `XML` — surface as `*` in PHON. The public repository retains the conversion script, the pipeline script, and the six resulting XML files.

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
