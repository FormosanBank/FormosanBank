# Asai et al. (2026) Kanakanavu Texts

This proposed collection covers the grammatical introduction and 44 narratives in Asai et al.’s 2026 Kanakanavu Texts. The checked-in candidate retains 45 XML files and 1,455 sentence records from the earlier build, with English translations and W/M analysis. It has no audio.

This candidate remains under review. The statistics below describe the retained final XML, before the pending source repairs are regenerated.

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Kanakanavu |
| --- | --- |
| Word count | 9,998 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 9,998 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 |
| Morphologically segmented | 9,983 |
| Glossed words | 9,983 |

***

<!-- CORPUS STATS END -->

## Notes and Issues

- Standard PHON follows Ortho113 (POL-003). The source's conditioned c/s
  pronunciation stays in original PHON; the former private standard override
  is retired. The two tiers therefore differ in those environments.
- The source parser resolves eight spelling/pronunciation variants and the old
  V1/V2 IDs. Tsuchida's notation key resolves ha/sua in two passages;
  two parenthetical classifications still need resolution under POL-028.
  Clause grouping stays at S; shared cleaning normalizes its brackets to
  parentheses and PHON omits them. These clauses are not optional material.
- Introduction lexical material has seven transcription groups, including Saaroa
  and the explicit phonemic/phonetic pair. Szakos ö still needs a supported sound
  mapping. Table 2's 16 pronouns have a
  verified segmental route; their stress marks remain in original FORM.
  The Saaroa comparison has a
  source-backed `ɫ` -> `hl` conversion and the corrected Saaroa code `sxr`,
  separate from the narrative profile.
  The village-labelled phonetic comparison remains open in the ledger.
  Supplemental records preserve printed readings; only three analyzed prose
  examples supply W/M tiers. They remain source-stage output pending the full build.
- The earlier ten-page expert review and historical samples cover those records
  only. They do not establish a current visual review of every page or reading.

The [corpus PR #155](https://github.com/FormosanBank/FormosanBank/pull/155)
lists the remaining decisions. A successful build or XML check does not settle them.

## Access Details

The [candidate XML and reproduction package](https://github.com/FormosanBank/FormosanBank/tree/c8362f07b3de5cbb0dade0c6a93bde3859a21f80/Corpora/ILCAA-Kanakanavu-Texts/)
match the reviewed private development commit. This proposal has not been merged.

## Corpus Processing

The parser reads the committed CC BY 4.0 PDF and source decisions. It emits 1,447 numbered-example S, 57 footnote S and 101 introduction/title S, totalling 1,605 source records. Historical columns stay separate. Repairs preserve prior corrections and narrative repetition while fixing gloss alignment, infixes, pseudo-clefts and reading variants. Table 1's Tsuchida 1969 and 2007 vocabulary columns use a separate source route; Table 2's 16 pronouns use the reviewed narrative-profile subset. Saaroa has its own conversion. The explicit /kaɨnɨ/[kɅɨnɨ] pair preserves source FORM and PHON separately. Shared tools derive other original PHON from source profiles and standard PHON from Ortho113 (POL-003). Szakos ö, one village phonetic comparison and two narrative classifications remain unresolved. These repairs have not reached retained final XML; provenance identifies its actual earlier build.

Run `bash Corpora/ILCAA-Kanakanavu-Texts/CodeAndDocs/generate_xml.sh` in the candidate
FormosanBank checkout. The [README](https://github.com/FormosanBank/FormosanBank/blob/c8362f07b3de5cbb0dade0c6a93bde3859a21f80/Corpora/ILCAA-Kanakanavu-Texts/README.md) documents dependencies,
source coverage and any scoped pipeline deviations. The
[build provenance](https://github.com/FormosanBank/FormosanBank/blob/c8362f07b3de5cbb0dade0c6a93bde3859a21f80/Corpora/ILCAA-Kanakanavu-Texts/CodeAndDocs/provenance.json) records the actual
tools used for the retained output; it does not select or pin tools for later builds.

## Copyright

The retained XML copyright field is:

Copyright © 2026 Paul Jen-kuei Li, Yi-Chun Chen, Hsiu-min Huang, and Amy Ming-luan Chen. Licensed under CC BY 4.0.

**License:** CC BY 4.0, stated on source PDF physical page 3.

**Rights source:** Paul Jen-kuei Li, Yi-Chun Chen, Hsiu-min Huang and Amy
Ming-luan Chen, 2026; exact grant date not stated; evidence: ask maintainer.

The source PDF may be redistributed under that licence with attribution.
Source generation writes the canonical licence value `CC BY 4.0` (POL-042),
with attribution retained here. The retained XML still carries its old
copyright prose and awaits final regeneration.

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

Asai, E., Mei, K., Li, P. J.-k., & Tsuchida, S. 2026. *Kanakanavu Texts*
(P. J.-k. Li, Ed.). Research Institute for Languages and Cultures of Asia and
Africa, Tokyo University of Foreign Studies.
