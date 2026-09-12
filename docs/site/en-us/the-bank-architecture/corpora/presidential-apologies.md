# Presidential Apologies

This corpus contains 524 aligned sentence sections in 16 Formosan languages from the official presidential apology translations. It preserves the government PDFs, transcript snapshots, source corrections and Mandarin readings. No audio is included.

This candidate remains under review. The statistics below describe the checked-in candidate XML.

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Amis<br>Xiuguluan | Bunun<br>Junqun | Kavalan | Rukai<br>Wutai | Paiwan<br>Central | Puyuma<br>Nanwang | Thao | Saaroa | Sakizaya | Yami | Atayal<br>Sekolik | Seediq<br>Tegudaya | Truku | Tsou | Kanakanavu | Saisiyat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Word count | 1,936 | 1,554 | 2,209 | 1,948 | 2,378 | 2,091 | 1,854 | 1,117 | 1,735 | 1,640 | 2,449 | 1,508 | 1,853 | 2,084 | 1,544 | 1,640 |
| Total audio | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Translated words |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 1,936 | 1,554 | 2,209 | 1,948 | 2,378 | 2,091 | 1,854 | 1,117 | 1,735 | 1,640 | 2,449 | 1,508 | 1,853 | 2,084 | 1,544 | 1,640 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 1,936 | 1,554 | 2,209 | 1,948 | 2,378 | 2,091 | 1,854 | 1,117 | 1,735 | 1,640 | 2,449 | 1,508 | 1,853 | 2,084 | 1,544 | 1,640 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Morphologically segmented | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Glossed words | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

***

<!-- CORPUS STATS END -->

## Notes and Issues

- The source repeats Saaroa S22/S23 on physical PDF pages 22/23 beside different translations. Both records are intentional and retained.
- Some source notation still needs interpretation under POL-027/POL-028: Puyuma S28 `parubalruk(pasenkin)` and Tsou S2/S9 `taa’uzva(taa’uiva)`, `esmiza(esmia)`, `mahiz’o(mahi’o)`. The PDFs provide no legend distinguishing lexical alternatives, spelling variants or explanatory notation. These existing readings remain intact pending that decision; the corpus is not yet ready to port.
- Mandarin code-switching, explanatory quotations and numbers are source content. CJK-only parenthetical annotations follow the scoped handling in the corpus README. Do not treat every parenthesis as optional spoken material.
- English has no bilingual-PDF witness, and the PDFs do not establish the inherited dialect labels.
- Existing source caveats are retained: Amis quotes Atayal Balay/Sbalay; Kanakanavu keeps its controversial h/f spellings; Puyuma keeps ē in yēncumin and sēhu; some Sakizaya f spellings may be loans. Letters unsupported by the declared dialect profile remain marked with `*` in generated PHON. These markers are not source transcriptions.

The [corpus PR #171](https://github.com/FormosanBank/FormosanBank/pull/171)
lists the remaining decisions. A successful build or XML check does not settle them.

## Access Details

The [candidate XML and reproduction package](https://github.com/FormosanBank/FormosanBank/tree/fa63bbf8dd7bb4d889d07332db853c3292e9b23a/Corpora/Presidential_Apologies/)
match the reviewed private development commit. This proposal has not been merged.

## Corpus Processing

The build reconstructs the source tiers from the committed transcripts and correction records, then uses current shared cleaning, standardization and phonology. The 36-file source inventory and alignment checks retain intentional repetition and identify the limits of the available PDF witnesses.

Run `bash Corpora/Presidential_Apologies/CodeAndDocs/generate_xml.sh` in the candidate
FormosanBank checkout. The [README](https://github.com/FormosanBank/FormosanBank/blob/fa63bbf8dd7bb4d889d07332db853c3292e9b23a/Corpora/Presidential_Apologies/README.md) documents dependencies,
source coverage and any scoped pipeline deviations. The
[build provenance](https://github.com/FormosanBank/FormosanBank/blob/fa63bbf8dd7bb4d889d07332db853c3292e9b23a/Corpora/Presidential_Apologies/CodeAndDocs/provenance.json) records the actual
tools used for the retained output; it does not select or pin tools for later builds.

## Copyright

The retained XML copyright field is:

public domain

**License:** public domain

**Rights source:** Wael Mohamed (recorded source status), 2024-10-16; evidence: ask maintainer

This retains the published corpus's public-domain status. The dated source coordination record confirms that status; it is not a new licence grant by the compiler. The committed PDFs and transcript snapshots are the recorded public build inputs.

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* **Citing the apology in general**: Tsai, I. W. (2016, August 1). _President Tsai Ing-wen's apology to the Indigenous Peoples on behalf of the government_ \[Speech transcript]. [Office of the President](https://english.president.gov.tw/NEWS/4950).
* **Language specific**: Tsai, I. W. (2016, August 1). _President Tsai Ing-wen's apology to the Indigenous Peoples on behalf of the government_ \[Speech transcript, Amis translation]. [Council of Indigenous Peoples](https://www.cip.gov.tw/zh-tw/news/data-list/01F6453A792735EC/index.html?cumid=01F6453A792735EC).
