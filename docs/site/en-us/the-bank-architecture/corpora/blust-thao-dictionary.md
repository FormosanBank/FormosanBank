# Blust (2003) Thao Dictionary

### Overview

Robert Blust's *Thao Dictionary* (2003) is the standard reference work for Thao, a Formosan language of central Taiwan spoken around Sun-Moon Lake. Published by the Institute of Linguistics (Preparatory Office), Academia Sinica, it runs to over a thousand pages and records the language in far more depth than any other source: headwords and the forms derived from them, grammatical labels, definitions, etymologies reaching back to Proto-Austronesian, and thousands of example sentences collected from speakers.

This corpus is the whole of that linguistic material. It contains the dictionary itself — 7,248 entries and derived forms, each with its English definition — alongside 8,591 example sentences, and the five interlinear texts printed on pages 244–274, which are narrative rather than lexical and carry word-by-word glosses. Every sentence records the printed page it came from, the entry it belongs to, and its sense number, so anything here can be traced back to the book.

Thao is severely endangered, with very few remaining first-language speakers. Blust's dictionary is the most substantial record of it that exists, and this is the first time it has been available as structured, searchable data.

***

<!-- CORPUS STATS START -->
### Corpus Statistics

| | Thao |
| --- | --- |
| Word count | 63,319 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 63,311 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 |
| Morphologically segmented | 56,445 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


## **Notes and Issues**

<!-- Known limitations, source defects, and caveats a user should know before using
     this corpus. Keep it user-facing (what affects the data), not process history.
     Write "None known." if there are none. -->

**Morpheme boundaries are part of the text.** Blust prints morpheme boundaries in the dictionary examples but not in the interlinear texts, and those hyphens are carried through into the standardized tier. This corpus therefore tokenizes differently from the other Thao material in FormosanBank, and word counts are not directly comparable. The sentences are also segmented into word and morpheme tiers.

**Glosses are at the sentence level, except in the texts.** The dictionary's examples are translated as wholes, because that is how the book translates them — there is no word-by-word gloss to extract. The five interlinear texts are the exception: 2,517 of their 2,542 words carry their own gloss. Note that the "Glossed words" figure above counts *morpheme*-level glosses, of which this corpus has none, so it reads 0 despite those word-level glosses.

**Notation that is not translation has been left out.** Blust writes glosses like "(don't) give it" to signal that a bound form can be used either positively or negatively. That is notation about the form rather than a translation of it, so the 395 entries whose entire gloss was of that shape are not published, nor are the 34 entries that are themselves a bound root rather than a word.

**Sixty-two pairs of sentences share a spelling but not a meaning.** Each has been read individually and confirmed as a genuine homophone — Thao *a* the future marker beside *a* the linking particle, for instance. They are deliberately kept as separate entries.

**A small number of source defects survive.** Eight sentences carry an unpaired quotation mark, because a quotation in the book runs past the point the text was divided into sentences; 22 English translations begin mid-quotation because the opening mark is missing from the PDF's text layer. One translation, on printed page 399, is spliced with a few words from a later page. The Sinitic place name *Tongpú* is mis-standardized as *Tonngpu* in four sentences, an artifact of a spelling conversion rule meeting a loanword.

Full detail, including the readings that were judgement calls rather than facts, is in the corpus README and in `CodeAndDocs/uncertain-decisions.md`.

***

## **Access Details**

* The repo containing this corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Blust-Thao-Dictionary).

***

## **Copyright**

CC BY-NC 4.0.

The Institute of Linguistics (Preparatory Office), Academia Sinica — the publisher and economic rights holder of the *Thao Dictionary* — authorized FormosanBank to reprint, reproduce and adapt the linguistic material in the book under this licence.

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

Blust, R. (2003). *Thao dictionary*. Institute of Linguistics (Preparatory Office), Academia Sinica.
