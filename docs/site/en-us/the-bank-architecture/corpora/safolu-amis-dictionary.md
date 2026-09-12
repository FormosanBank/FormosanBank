# Safolu Amis Dictionary

The Safolu Amis Dictionary supplies Amis examples and Mandarin readings from the pinned g0v Amis Moedict source. The checked-in candidate XML retains 49,179 sentence records from the earlier build. It has no audio or W/M analysis.

This candidate remains under review. The statistics below describe the retained final XML, before the pending source repairs are regenerated.

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Amis<br>Coastal |
| --- | --- |
| Word count | 243,699 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 242,687 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 |
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->

## Notes and Issues

- The Safolu PHON profile and conversion table remain unmerged shared inputs.
  Current conversion checking reports an unresolved `u → o` mapping and `d`/`o`
  routing questions. Preserve the source's distinct vowel spellings and mixed
  `g`/`ng`; see [orthography evidence](https://github.com/FormosanBank/FormosanBank/blob/1da4a90f307630cec81fb7fe5d0cbdd70bef32cc/Corpora/Safolu-Amis-Dictionary/docs/orthography_evidence.md).
- Forty-two original-FORM parenthesis/slash cases still need source-specific
  interpretation. The revised parser resolves only directly supported cases,
  including the explicit pronunciation examples in the `e` and `i` entries.
- S37193's published Chinese correction was inferred from its sentence and
  definition; an authoritative reading is still needed. It is preserved pending
  review. Source field 35128 still contains unexplained `久` on the publisher's
  page and remains outside released XML.
- The source history includes both PDF-to-TXT and DOCX conversion. A clean JSON
  file does not establish that it is free of earlier extraction errors.

The [corpus PR #157](https://github.com/FormosanBank/FormosanBank/pull/157)
lists the remaining decisions. A successful build or XML check does not settle them.

## Access Details

The [candidate XML and reproduction package](https://github.com/FormosanBank/FormosanBank/tree/1da4a90f307630cec81fb7fe5d0cbdd70bef32cc/Corpora/Safolu-Amis-Dictionary/)
match the reviewed private development commit. This proposal has not been merged.

## Corpus Processing

The revised parser reads a committed public snapshot of 49,419 source fields, applies exact field corrections and stages 49,455 source records before shared deduplication. The complete build currently stops because the shared Safolu profile and conversion are unavailable. Its new source repairs are not yet in final XML. The retained provenance describes the old final build, not a new successful regeneration.

Run `bash Corpora/Safolu-Amis-Dictionary/CodeAndDocs/generate_xml.sh` in the candidate
FormosanBank checkout. The [README](https://github.com/FormosanBank/FormosanBank/blob/1da4a90f307630cec81fb7fe5d0cbdd70bef32cc/Corpora/Safolu-Amis-Dictionary/README.md) documents dependencies,
source coverage and any scoped pipeline deviations. The
[build provenance](https://github.com/FormosanBank/FormosanBank/blob/1da4a90f307630cec81fb7fe5d0cbdd70bef32cc/Corpora/Safolu-Amis-Dictionary/CodeAndDocs/provenance.json) records the actual
tools used for the retained output; it does not select or pin tools for later builds.

## Copyright

The retained XML copyright field is:

CC BY-NC according to the frozen amis-safolu README; current data source is g0v/amis-moedict docs/s.

**License:** unresolved; the existing XML copyright prose is retained.

**Rights source:** Safolu Kacaw Lalanges, date unconfirmed; evidence: ask maintainer.

The frozen upstream README says the author allowed g0v Amis Moedict to use the
dictionary under CC BY-NC, without a verified version/date. This does not justify
choosing a vocabulary value by assumption. The XML and companion GitBook rights
claim need an explicit maintainer review before publication (POL-042 through POL-045).

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

Tsai, Chung-Han (Safolu Kacaw Lalanges). (n.d.). *Amis dictionary*. Provided to the g0v Amis Moedict project. https://amis.moedict.tw/
