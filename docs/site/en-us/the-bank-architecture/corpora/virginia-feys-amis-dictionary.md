# Virginia Fey's Amis Dictionary

This candidate contains 2,042 Amis example records with English and Mandarin readings from Virginia Fey’s dictionary and its maintained digital edition. The source is routed to Xiuguluan. It preserves source spelling and multiple meanings; no audio or W/M analysis is supplied.

This candidate remains under review. The statistics below describe the checked-in candidate XML.

## Notes and Issues

- The digital source was checked against raw text, corrected Word files and
  conversion history. This is not a complete review of the printed dictionary.
- The digital edition writes the ng sound as `g` (printed guide, page 20), and its
  converter changed only lowercase `g`; a sentence-initial capital `G` is ng too,
  so S3846 reads `Nga'ayto` and S4934 `Nga'ayho`. This does not recover phonemic
  contrasts absent from the source.
- [Printed page 345](https://drive.google.com/file/d/1eNMbHjQfC-ZR77ha17S_441hx9ZcsDhm/view)
  confirms `O kalatolo / kalitolo konini.`; like every slash cell, it gives one
  sentence per option (S6717 and S6717-opt).
- Li, Joby and Zeitoun (2024) note that Fey misses some phonemic contrasts,
  including glottal versus pharyngealized stops. Wu Ming-yi modernized the
  digital spelling, but this does not establish that the distinction was
  recovered. Generated PHON must not be treated as source transcription.
- A sentence may have several English or Chinese translations. Where two source
  rows give the identical Amis sentence, they are one sentence and the second
  row's translations are alternates. No W/M analysis is supplied.

The [corpus PR #170](https://github.com/FormosanBank/FormosanBank/pull/170)
lists the remaining decisions. A successful build or XML check does not settle them.


<!-- CORPUS STATS START -->
## Corpus Statistics

| | Amis<br>Xiuguluan |
| --- | --- |
| Word count | 9,199 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 9,199 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 9,199 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 |
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->

## Access Details

The [candidate XML and reproduction package](https://github.com/FormosanBank/FormosanBank/tree/45578e57a9e1c768394df211f16aed14ab4c87b2/Corpora/Virginia_Fey_Dictionary/)
match the reviewed private development commit. This proposal has not been merged.

## Corpus Processing

The build starts from the preserved hand-corrected baseline and pinned digital source, applies source-located repairs, and runs the current shared tools. It accounts for 2,012 complete source rows while retaining 2,039 of the 2,040 published sentence IDs and adding three (S1900, S5142, S6717-opt). S6908 `ceco.`, the third option of a slash cell, is removed because it is not clear how it should be read. Spelling and sound use the shared Amis tables (Xiuguluan).

Run `bash Corpora/Virginia_Fey_Dictionary/CodeAndDocs/generate_xml.sh` in the candidate
FormosanBank checkout. The [README](https://github.com/FormosanBank/FormosanBank/blob/45578e57a9e1c768394df211f16aed14ab4c87b2/Corpora/Virginia_Fey_Dictionary/README.md) documents dependencies,
source coverage and any scoped pipeline deviations. The
[build provenance](https://github.com/FormosanBank/FormosanBank/blob/45578e57a9e1c768394df211f16aed14ab4c87b2/Corpora/Virginia_Fey_Dictionary/CodeAndDocs/provenance.json) records the actual
tools used for the retained output; it does not select or pin tools for later builds.

## Copyright

The retained XML copyright field is:

CC BY-NC 3.0

**License:** CC BY-NC 3.0

**Rights source:** Taiwan Bible Society, grant date not recorded; evidence: ask maintainer.

The pinned upstream README and licence state CC BY-NC 3.0. The publisher links
[Taiwan Bible Society correspondence dated 2008-10-07](https://drive.google.com/file/d/1s2_xzc_ZFbInk9wGXfVeUmvktJDZI5cb/view)
welcoming digitization, but that message does not specify a Creative Commons
licence or its grant date. Published XML said `CC BY-SA` until 2026-10-16; the
licence is now kept as granted, CC BY-NC 3.0 (maintainer ruling 2026-10-16).

The corpus is also subject to the central FormosanBank
[licence](https://github.com/FormosanBank/FormosanBank/blob/main/LICENSE.md) and
[AI use terms](https://github.com/FormosanBank/FormosanBank/blob/main/AI-USE-ADDENDUM.md).
Commercial AI use requires prior written permission.

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Fey, V. (1986). _Amis dictionary_. Taipei: The Bible Society.
* miaoski. (2023). _miaoski/amis-data_ \[Python]. GitHub. [https://github.com/miaoski/amis-data](https://github.com/miaoski/amis-data) (Original work published 2013)
* Wu, J. (2006). _Verb Classification, Case Marking, and Grammatical Relations in Amis_. University at Buffalo.
