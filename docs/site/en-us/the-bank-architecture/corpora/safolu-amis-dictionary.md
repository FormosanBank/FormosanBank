# Safolu Amis Dictionary

The Safolu Amis Dictionary is a collection of 49,406 Amis example sentences with Mandarin (Chinese) translations, drawn from the dictionary compiled by Safolu Kacaw Lalanges / Tsai Chung-Han (蔡中涵). The data comes from the generated JSON of the [g0v Amis Moedict](https://github.com/g0v/amis-moedict) project (`docs/s`; see [amis.moedict.tw](https://amis.moedict.tw/)), checked against the dictionary's printed text.

Each sentence carries the source text (`original` tier), a copy in the FormosanBank standard orthography (`standard` tier, Ortho113), and an IPA transcription of each. The corpus stops at the sentence level: it has no audio and no word or morpheme segmentation, because the dictionary's examples carry none.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Amis<br>Coastal |
| --- | --- |
| Word count | 244,756 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 243,775 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 |
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


## Access Details

* The corpus and the code that rebuilds it are [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Safolu-Amis-Dictionary).

***

## Corpus Processing

The build reads a committed snapshot of the source (49,419 example fields at `g0v/amis-moedict` commit `e7c6976`, 2026-05-08) and never fetches anything. Its steps, all in the repository:

* **Parsing** into one sentence per example. Where a source field holds two readings (a parenthesised or slashed alternative), it becomes either one sentence with an alternative form or two sentences, as decided example by example in a maintainer review.
* **Per-sentence decisions** from that review (2026-10-16/17), each recorded with its reason: full translations from the printed text where the digitised source cut them short, and decisions on 48 parenthesis and slash examples.
* **The dictionary editors' later corrections.** The editors have kept revising the dictionary upstream since our snapshot. 204 of their edits are adopted (pinned at `g0v/amis-moedict` commit `4cb82539d`, 2026-10-16), so **these 204 sentences follow the editors' revision, not the printed book**. Four examples printed in the book but missing from the source are added.
* **Spacing:** no space before `?` or `!`, and a space after them before the next word.
* **Standard tier** via the Church-to-Ortho113 conversion table (Coastal), and **pronunciation** from the Church orthography table.
* **Duplicates** are removed only when both the standard text and the translations are identical (120 sentences).

The [README](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Safolu-Amis-Dictionary/README.md) gives the details, the full list of decisions, and how to reproduce the corpus.

***

## Copyright

**CC BY-NC-SA 3.0 TW**, the licence as granted by Tsai Chung-Han; the grant is held in FormosanBank's records.

The frozen upstream README says CC BY-NC without a version. The
[publisher README](https://github.com/g0v/amis-moedict-new/blob/20d9718b362e046c8a79454d3710efa4fe404afe/README.md#license-授權)
identifies Tsai Chung-Han's dictionary as CC BY-NC-SA 3.0 TW and links his
[signed licence deed](https://drive.google.com/file/d/1IQykXGWtaWAL0pH0xlE0pi5My0Onlji2/view),
which names that licence. Its printed footer says 2015/4/9; this does not establish
the signature or grant date.

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

Tsai, Chung-Han (Safolu Kacaw Lalanges). (n.d.). *Amis dictionary*. Provided to the g0v Amis Moedict project. https://amis.moedict.tw/
