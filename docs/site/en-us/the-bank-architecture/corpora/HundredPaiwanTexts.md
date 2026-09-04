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

The corpus was rebuilt in August 2026 from two checksum-pinned Word documents supplied by the author. All 268 rendered source pages were reviewed. Both Word documents are published with the corpus under `CodeAndDocs/`, so the XML rebuilds from a FormosanBank checkout alone; only the private correspondence recording the author's permission is withheld.

The rebuild preserves the natural Paiwan line at the sentence tier and the separate source analysis and gloss lines at the word and morpheme tiers. It also:

* restores the first sentence of story 091, nine omitted final words, and four XML files missing from the earlier development output;
* expands five optional tokens into complete sentence variants;
* records two word-alignment decisions, three translation-note extractions, one punctuation repair, four text-metadata corrections, and 16 exact sentence-surface decisions;
* preserves all 64,198 identifiers from the previous public version while assigning unique identifiers to restored material; and
* leaves the one source morpheme without a gloss, final `-i` in sentence `078S4`, genuinely unglossed rather than inventing a meaning for it.

The deterministic pipeline rebuilds the original tiers, runs the shared cleaner, creates standard forms, generates phonology, resolves the source orthography's question-mark and glottal-stop ambiguity, applies the reviewed sentence decisions, and runs structural, text, gloss, and source-scrape validation. One row was removed from the shared Ferrell conversion table: `Ḍ → dr`, which mapped the uppercase retroflex to a lowercase output. The row was not redundant — it overrode the standardizer's case-variant derivation, so proper names lost their capital in the standard tier (`Ḍiququ → driququ`). Without it the derivation produces case-preserving `Ḍ → Dr`, giving `Driququ`. The change affects standard-tier capitalization only: it leaves every one of the corpus's 128,830 phonology elements byte-identical, because `add_phonology.py` matches orthography letters case-insensitively and already read `Ḍ` as `ɖ`. The corrected table passes its standalone audit.

The final audit reports one hard finding, accepted and documented below, and no others across the four validator families. The remaining soft findings are fully classified as source notation or canonical infix and reduplication structures. The [corpus README](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/HundredPaiwanStories) documents the reproducible workflow, and the [audit report](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/HundredPaiwanStories/CodeAndDocs/reports/audit-report.md) records the evidence.

### **Corpus Notes**

#### The one unglossed morpheme, and the three findings it causes

The source's analysis of sentence `078S4`, word 19 (`t<al>e-talem-i`) prints
four form units but only three gloss units (`al=te-talem-i` against
`qal=do-plant`), leaving the final `-i` without a gloss.

Morpheme `078S4W19M0c` is therefore published with **no `TRANSL` element at
all**. An absent gloss is the honest record of an absent source gloss. It is
deliberately not filled with a `?`: this source writes `?` itself, as a real
gloss, for morphemes its authors could not identify — 337 times — so a `?`
supplied by FormosanBank would be indistinguishable from the authors' own. The
`notes` attribute on the word's `TRANSL` records that the gap is intentional.

Three validator findings follow directly from that decision, and are accepted:

| Rule | Severity | What it reports |
| --- | --- | --- |
| `V064` `every_M_has_TRANSL` | Soft | `078S4W19M0c` has no gloss |
| `G002` `M_count_matches_gloss_units` | Soft | the word has 4 morphemes but its gloss implies 3 |
| `G001` `marker_skeleton_parity` | **Hard** | `t<al>e-talem-i` and `do<qal>-plant` differ by that one unit |

There is no way to publish an unglossed morpheme without them, and the
alternative — inventing a gloss — is worse. The build does not simply ignore
hard findings: `review_qc_findings.py` pins all three to this exact word and
morpheme and fails if a fourth appears, if one moves, or if any other morpheme
in the corpus loses its gloss.

#### How sentence-level corrections are recorded

A handful of sentences need a correction the blanket pipeline cannot make on its
own. These are **not** recorded as FormosanBank manual edits
(`capture_manual_edits.py` / `manual_edits.xml`). They live in a reviewed
decision table,
[`standard_surface_decisions.tsv`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/HundredPaiwanStories/CodeAndDocs/standard_surface_decisions.tsv),
which `normalize_sentence_standards.py` applies at the end of the build. Every
decision is listed there in full, so readers can check each one against the
source. All 16 rows concern parenthesised material:

* **11 remove parenthesised uncertainty.** Where the source prints a bracketed
  query on a form — `paqeteleng(?)` — the original tier keeps it and the
  standard tier resolves it out.
* **5 publish a parenthesised optional token as two complete sentences.** Where
  the source prints `kemljang (aken) tu …`, both complete readings are published
  as separate `S` elements rather than leaving a parenthesis inside a sentence.

The table is preferred to a recorded diff because each row carries the source
form, what the blanket pipeline produced, the corrected form, the decision and
its evidence. The build re-derives the change every time, re-checks each row's
original form against the source first, and asserts the pass is idempotent.

#### Hyphens are not part of the standard orthography

Ferrell's §1.6 gives three interlinear levels. The plain-text first line — the
one that becomes the sentence `FORM` — legitimately contains hyphens, while the
second line carries the morpheme analysis. The **original** tier keeps every one
of them: 153 sentences contain hyphens, and the `G010` warnings report exactly
those.

The **standard** tier carries none. A hyphen is a segmentation marker rather
than a letter of the standard orthography, so the pipeline strips it and the
decision table does not put it back. `V133` (`dash_in_S_standard_FORM`) does not
fire at all.

#### Dialect coverage

The source does not identify a supported dialect for texts `090`, `091`, `097`, and `099`. Their dialect remains `unknown`, and their generated phonology uses the default Paiwan profile. These tiers should be revisited if source-supported dialect metadata becomes available.

### **Rights and Access**

R. J. Early granted FormosanBank permission to publish these texts and supplied the source document. We are grateful for that permission, without which the corpus could not be distributed.

On that basis the corpus is published under **CC BY-NC**: attributed non-commercial use and redistribution are permitted, and commercial use requires prior written permission. Every `TEXT` element records `copyright="CC BY-NC"`. The corpus is also subject to FormosanBank's central license and AI-use terms.

Users are encouraged to consult the published source. A PDF is available from the [Australian National University repository](https://openresearch-repository.anu.edu.au/server/api/core/bitstreams/5f377c02-9051-40b3-b839-7108229b3f84/content), which also provides the grammatical and cultural context for the texts.

### **Citation**

Early, R. J., and Whitehorn, J. (2003). *One Hundred Paiwan Texts*. Pacific Linguistics, Research School of Pacific and Asian Studies, Australian National University.
