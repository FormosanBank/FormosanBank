# 100 Paiwan Texts

### **Overview**

[The 100 Paiwan Texts](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/HundredPaiwanStories) corpus contains 100 morphologically analyzed and glossed Paiwan texts from Early and Whitehorn (2003). The published XML has 2,921 sentence elements, including 2,916 source sentences and 5 complete variants for optional source tokens.

<!-- CORPUS STATS START -->
### Corpus Statistics

| | Paiwan<br>Central | Paiwan<br>Eastern | Paiwan<br>Northern | Paiwan<br>Southern | Paiwan<br>unknown |
| --- | --- | --- | --- | --- | --- |
| Word count | 3,719 | 1,198 | 9,021 | 9,496 | 1,122 |
| Total audio | 0 | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 | 0 | 0 | 0 | 0 |
| Translated words |  |  |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 3,719 | 1,198 | 9,021 | 9,496 | 1,122 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 0 | 0 | 0 | 0 | 0 |
| Morphologically segmented | 3,719 | 1,198 | 9,021 | 9,496 | 1,122 |
| Glossed words | 3,719 | 1,198 | 9,021 | 9,496 | 1,122 |

***

<!-- CORPUS STATS END -->

### **Corpus Processing**

The corpus was rebuilt in August 2026 from two checksum-pinned Word documents supplied by the author. All 268 rendered source pages were reviewed. The public repository contains the derivative XML and reproducibility code, but not the Word files or private permission evidence.

The rebuild preserves the natural Paiwan line at the sentence tier and the separate source analysis and gloss lines at the word and morpheme tiers. It also:

* restores the first sentence of story 091, nine omitted final words, and four XML files missing from the earlier development output;
* expands five optional tokens into complete sentence variants;
* records two word-alignment decisions, three translation-note extractions, one punctuation repair, four text-metadata corrections, and 166 exact sentence-surface decisions;
* preserves all 64,198 identifiers from the previous public version while assigning unique identifiers to restored material; and
* marks the one source morpheme without a gloss, final `-i` in sentence `078S4`, as editorially unknown instead of inventing a meaning.

The deterministic pipeline rebuilds the original tiers, runs the shared cleaner, creates standard forms, generates phonology, resolves the source orthography's question-mark and glottal-stop ambiguity, applies the reviewed sentence decisions, and runs structural, text, gloss, and source-scrape validation. A redundant Ferrell conversion row was removed so uppercase `Ḍ` now maps to case-preserving standard `Dr`. The corrected conversion table passes its standalone audit.

The final audit reports zero hard findings across all four validator families. The remaining soft findings are fully classified as source notation or canonical infix and reduplication structures. The [corpus README](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/HundredPaiwanStories) documents the reproducible workflow, and the [audit report](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/HundredPaiwanStories/CodeAndDocs/reports/audit-report.md) records the evidence.

### **Corpus Notes**

The source does not identify a supported dialect for texts `090`, `091`, `097`, and `099`. Their dialect remains `unknown`, and their generated phonology uses the default Paiwan profile. These tiers should be revisited if source-supported dialect metadata becomes available.

### **Rights and Access**

The author granted permission for attributed, non-profit derivative publication. For-profit republication of the source as-is is not permitted. This permission is not represented as a Creative Commons license. The corpus is also subject to FormosanBank's central license and AI-use terms.

Users are encouraged to consult the published source. A PDF is available from the [Australian National University repository](https://openresearch-repository.anu.edu.au/server/api/core/bitstreams/5f377c02-9051-40b3-b839-7108229b3f84/content), which also provides the grammatical and cultural context for the texts.

### **Citation**

Early, R. J., and Whitehorn, J. (2003). *One Hundred Paiwan Texts*. Pacific Linguistics, Research School of Pacific and Asian Studies, Australian National University.
