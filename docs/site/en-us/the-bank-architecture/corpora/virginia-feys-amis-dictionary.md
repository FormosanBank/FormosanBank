# Virginia Fey's Amis Dictionary

This candidate contains 2,051 Amis example records with English and Mandarin readings from Virginia Fey’s dictionary and its maintained digital edition. The source is routed to Xiuguluan. It preserves source spelling and multiple meanings; no audio or W/M analysis is supplied.

This candidate remains under review. The statistics below describe the checked-in candidate XML.

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Amis<br>Xiuguluan |
| --- | --- |
| Word count | 9,228 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 9,228 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 9,228 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 |
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->

## Notes and Issues

- The digital source was checked against raw text, corrected Word files and
  conversion history. This is not a complete review of the printed dictionary.
- S3846 retains the published source spelling `Ga'ayto`. The printed guide
  identifies g as the ng sound, but G is absent from the selected profile and
  its generated PHON contains `*`. Source-profile treatment remains unresolved;
  do not change the original spelling merely to clear that result.
- The proposed `kalatolo` / `kalitolo` reading still needs classification as
  competing words or pronunciation variants.
- Li, Joby and Zeitoun (2024) note that Fey misses some phonemic contrasts,
  including glottal versus pharyngealized stops. Wu Ming-yi modernized the
  digital spelling, but this does not establish that the distinction was
  recovered. Generated PHON must not be treated as source transcription.
- A sentence may have several English or Chinese translations. No W/M analysis
  is supplied.

The [corpus PR #170](https://github.com/FormosanBank/FormosanBank/pull/170)
lists the remaining decisions. A successful build or XML check does not settle them.

## Access Details

The [candidate XML and reproduction package](https://github.com/FormosanBank/FormosanBank/tree/449e42384fa5b0be9454a071026dc53e1bd95bd3/Corpora/Virginia_Fey_Dictionary/)
match the reviewed private development commit. This proposal has not been merged.

## Corpus Processing

The build starts from the preserved hand-corrected baseline and pinned digital source, applies source-located repairs, and runs the current shared tools. It accounts for 2,012 complete source rows while retaining all 2,040 published sentence IDs. Distinct source readings are preserved. The remaining G and kalatolo/kalitolo decisions are not resolved by a deterministic build.

Run `bash Corpora/Virginia_Fey_Dictionary/CodeAndDocs/generate_xml.sh` in the candidate
FormosanBank checkout. The [README](https://github.com/FormosanBank/FormosanBank/blob/449e42384fa5b0be9454a071026dc53e1bd95bd3/Corpora/Virginia_Fey_Dictionary/README.md) documents dependencies,
source coverage and any scoped pipeline deviations. The
[build provenance](https://github.com/FormosanBank/FormosanBank/blob/449e42384fa5b0be9454a071026dc53e1bd95bd3/Corpora/Virginia_Fey_Dictionary/CodeAndDocs/provenance.json) records the actual
tools used for the retained output; it does not select or pin tools for later builds.

## Copyright

The retained XML copyright field is:

CC BY-NC 3.0

**License:** CC BY-NC 3.0

**Rights source:** Taiwan Bible Society, grant date not recorded; evidence: ask maintainer.

The pinned upstream README and licence state this licence and acknowledge the
Taiwan Bible Society's permission to digitize the dictionary. The exact grant
date still needs confirmation. Published XML previously said CC BY-SA, so the
change requires explicit maintainer rights review before publication.

The corpus is also subject to the central FormosanBank
[licence](https://github.com/FormosanBank/FormosanBank/blob/main/LICENSE.md) and
[AI use terms](https://github.com/FormosanBank/FormosanBank/blob/main/AI-USE-ADDENDUM.md).
Commercial AI use requires prior written permission.

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Fey, V. (1986). _Amis dictionary_. Taipei: The Bible Society.
* miaoski. (2023). _miaoski/amis-data_ \[Python]. GitHub. [https://github.com/miaoski/amis-data](https://github.com/miaoski/amis-data) (Original work published 2013)
* Wu, J. (2006). _Verb Classification, Case Marking, and Grammatical Relations in Amis_. University at Buffalo.
