# Paiwan Stories

### Overview

The Paiwan Stories corpus is a small collection of children’s stories told in Eastern Paiwan. Drawn from three storybooks, these narratives provide valuable cultural and linguistic insights into the Paiwan language as it is used in accessible, community-oriented contexts. Their inclusion in FormosanBank broadens the range of available materials, offering a glimpse into traditional knowledge, everyday life, and childhood learning in a Paiwan-speaking environment.&#x20;

Three whole-story WAV recordings are available through FormosanBank’s public Hugging Face audio contract and can be retrieved with the corpus download script. Each XML root links to its recording. Corpus statistics count sentence-level `AUDIO` elements, so these recordings without sentence timing do not contribute to the audio-duration metric.

#### Source Materials

* giling, gesi & giling tjaiwan (2020) _vuvu 的寶物 / kavatjes ni vuvu_
* giling, gesi & giling tjaiwan (2021) _dingding蝸牛_
* giling, gesi & giling tjaiwan (2022) _maljialjian a qaciljay_

***

### **Corpus Processing**

The reviewed release contains 46 bilingual sentence records across three XML files. All 66 pages of the two illustrated PDFs and bilingual Word source were reviewed, with four paratext or illustration-only exclusions recorded in the source ledger.

#### Processing Notes

* **Source-aligned generation:** The public builder regenerates the XML deterministically from 46 reviewed, page-addressed records and a complete inclusion/exclusion ledger.
* **Reviewed corrections:** One complete bilingual sentence omitted from the legacy `Maljialjian` XML was restored. Omitted or shifted Chinese translations in `Kavatjes` and `Maljialjian` were also repaired from the source.
* **Tier ownership:** The generator emits source-owned original Paiwan forms and Chinese translations. The shared FormosanBank pipeline alone creates standard forms and original and standard phonology.
* **Validation:** The 2026-08-22 release has no unresolved source-audit findings, no XML or text findings, live hosted-audio parity, and 0 hard findings and 0 warnings for port readiness.

***

### Access Details

* The [FormosanBank corpus directory](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Paiwan_Stories) contains the XML, reviewed source transcription and ledger, deterministic build script, and audio download script. The illustrated source documents are not redistributed because they contain separate rights notices.

***

### Copyrights

The Indigenous-language text is published with direct author permission under CC BY-NC. The central FormosanBank terms and AI-use addendum also apply.

***

### Citation

In accordance with our [Terms of Use](../../additional-resources/tja-kipapawlingaven-a-cekaw-tua-ziriu-imaza.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Juan, T. F., & Ruan, X. (2024). _Corpus of Paiwan stories_ \[Electronic resource].
