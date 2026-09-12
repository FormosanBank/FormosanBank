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

- Current Ortho113 does not reproduce the reviewed conditioned standard PHON.
  Existing CLI flags can read the committed source profile and conversion;
  their location is not the phonology limitation. The standard-tier decision
  still needs separate review (POL-003/POL-049).
- The source parser resolves six spelling variants and the old V1/V2 IDs.
  Four parenthetical classifications still need resolution under POL-028.
  Clause brackets remain at S; the shared PHON step must handle them as
  analytical notation.
- Introduction lexical material uses several source orthographies. Its coverage
  and routing must be resolved without applying the narrative profile blindly.
  Footnote records preserve printed readings and omit unsupplied translations
  and W/M analysis; they remain source-stage output pending the full build.
- The earlier ten-page expert review and historical samples cover those records
  only. They do not establish a current visual review of every page or reading.

The [corpus PR #155](https://github.com/FormosanBank/FormosanBank/pull/155)
lists the remaining decisions. A successful build or XML check does not settle them.

## Access Details

The [candidate XML and reproduction package](https://github.com/FormosanBank/FormosanBank/tree/5f1c077dd0815b46841b8f50a91d9c50e401c51e/Corpora/ILCAA-Kanakanavu-Texts/)
match the reviewed private development commit. This proposal has not been merged.

## Corpus Processing

The revised parser uses the committed CC BY 4.0 PDF, source-specific decisions and current shared tools. Its numbered inventory covers 1,431 units and emits 1,449 S; 57 lexical records from explanatory footnotes bring source output to 1,506 S. Printed meanings, variants and note context are preserved without invented analysis. Source repairs include gloss columns, stacked infixes and four pseudo-clefts. These changes are not yet reflected in the retained final XML: canonical standard PHON does not reproduce the reviewed conditioned sounds. Existing CLI flags can load the committed source tables, but that alone does not resolve the standard-tier decision. Provenance continues to identify the actual earlier final build.

Run `bash Corpora/ILCAA-Kanakanavu-Texts/CodeAndDocs/generate_xml.sh` in the candidate
FormosanBank checkout. The [README](https://github.com/FormosanBank/FormosanBank/blob/5f1c077dd0815b46841b8f50a91d9c50e401c51e/Corpora/ILCAA-Kanakanavu-Texts/README.md) documents dependencies,
source coverage and any scoped pipeline deviations. The
[build provenance](https://github.com/FormosanBank/FormosanBank/blob/5f1c077dd0815b46841b8f50a91d9c50e401c51e/Corpora/ILCAA-Kanakanavu-Texts/CodeAndDocs/provenance.json) records the actual
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
