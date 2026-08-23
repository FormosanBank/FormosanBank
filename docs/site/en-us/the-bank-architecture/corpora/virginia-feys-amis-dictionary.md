# Virginia Fey's Amis Dictionary

### Overview

Virginia Fey’s Amis Dictionary represents a significant effort to document the Amis language. Originally compiled in the mid-1980s and later updated with revised orthography, the dictionary provides a valuable linguistic resource for researchers, educators, and community members interested in Amis language study and revitalization.

FormosanBank publishes 2,041 deduplicated Amis example sentences and phrases from the dictionary, with English and Mandarin translations. The source is routed to the Xiuguluan dialect and retains alternative readings as separate translation elements.

***

<!-- CORPUS STATS START -->
### Corpus Statistics

| | Amis<br>Xiuguluan |
| --- | --- |
| Word count | 9,051 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 9,051 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 9,051 |
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


### Background

First compiled by Virginia Fey in 1986, this dictionary has undergone several stages of transformation:

1. **Original Documentation:** Initially published with older Catholic-style orthography, the dictionary aimed to be a reference guide for speakers and learners of Amis.
2. **Orthographic Revisions:** Thanks to the work of linguists, most notably Wu Ming-yi, this corpus was later converted into the newer orthography aligned with the Indigenous language writing systems recognized by the Council of Indigenous Peoples and other linguistic authorities.
3. **Digital Adaptation:** The digitized version comes from the publicly accessible [miaoski/amis-data](https://github.com/miaoski/amis-data) repository. The source is licensed CC BY-NC 3.0 and was adapted to FormosanBank’s standardized XML format.

***

### Features of the Dictionary

* **Example Inventory:** Includes 2,041 deduplicated sentence and phrase records drawn from dictionary entries covering everyday objects, actions, cultural concepts, flora, fauna, and more.
* **Multilingual Translations:** Records include English and Mandarin translations, with distinct alternatives retained separately.
* **Source Provenance:** Transformed source fields are preserved in notes, and the complete example inventory is checked against a pinned maintenance sheet.
* **Revised Orthography:** The dictionary data has been updated from older Catholic orthographic conventions to a standardized orthography used in current Indigenous language education and revitalization efforts.

***

### **Corpus Processing**

The processing pipeline for converting the dictionary data into FormosanBank’s standardized XML format included several stages:

1. **Pinned source:** The pipeline uses a 6,899-row maintenance sheet with 2,012 complete Amis, English, and Mandarin example rows. It also pins the relevant upstream files and commit from [miaoski/amis-data](https://github.com/miaoski/amis-data/tree/494e5e4bc276c4d2b8b7b827a2c737597239a73b), with exact hashes.
2. **Reconstruction baseline:** The original converter and history of hand cleaning are unavailable. Under POL-035, the preserved pre-correction XML is the immutable baseline for reproducible repairs.
3. **Source reconciliation:** Reviewed source decisions expand every form alternative, repair documented form and translation defects, correct the license metadata to CC BY-NC 3.0, and preserve exact transformed source fields in notes. A fail-closed audit accounts for 2,012 source rows and 2,051 pre-dedup source units.
4. **Canonical generation:** The pipeline cleans the original tier, creates machine-owned standard FORM tiers with `standardize.py --remove_accents`, regenerates original and standard PHON with the Xiuguluan Ortho113 profile, and removes exactly ten declared duplicate attestations. Distinct translations from removed duplicates are merged into the surviving records with `ver="alt"`.
5. **Quality control:** The final corpus has 2,041 sentence records, zero XML issues, zero duplicate groups, zero unresolved PHON markers, complete source accounting, and zero HARD or WARN port-readiness findings.

***

### **Corpus Notes**

* Wu (2006, Table 1.4) identifies Fey 1986 as a dictionary of Standard Central Amis from Fuyuan to Fuli and Fengbin to Yiwan. FormosanBank’s registry maps Central to Xiuguluan, which controls the XML dialect value.
* The pinned upstream README states that Wu Ming-yi rewrote the old Catholic spelling into the newer Council of Indigenous Peoples spelling. The current orthography detector ranks Xiuguluan Ortho113 first. Li et al. (2024) nevertheless caution that Fey’s dictionary misses some phonemic contrasts, so users should not infer distinctions absent from the source.
* A sentence may contain multiple translations in the same target language, including alternatives carried over from removed duplicate entries. Later alternatives are marked `ver="alt"`.

***

### Significance

* **Language Preservation:** By documenting a wide range of lexical items and their meanings, this dictionary contributes to the preservation and revitalization of the Amis language.
* **Linguistic Research:** Researchers gain access to a standardized, machine-readable corpus that facilitates lexicographic analysis, comparative studies, and the development of natural language processing tools.
* **Educational Resource:** Educators and community members can draw on the dictionary to create learning materials, support classroom teaching, and develop language applications.

***

### Access Details

* The pinned upstream revision used by the corpus is available at [miaoski/amis-data commit 494e5e4](https://github.com/miaoski/amis-data/tree/494e5e4bc276c4d2b8b7b827a2c737597239a73b).
* The corpus XML and retained processing materials are available [in FormosanBank](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Virginia_Fey_Dictionary).

***

### Copyrights

According to the pinned [upstream repository](https://github.com/miaoski/amis-data/tree/494e5e4bc276c4d2b8b7b827a2c737597239a73b), the Taiwan Bible Society authorized digitization and the source data is CC BY-NC 3.0:

> 謹感謝 台灣聖經公會 授權電子化。商業使用之授權，請洽\[台灣聖經公會]。

> 感謝吳明義老師將天主教的舊式拼法，改寫成原民會版本的新式拼法。

> This work is licensed under the Creative Commons 姓名標示-非商業性 3.0 Unported License. To view a copy of this license, visit [http://creativecommons.org/licenses/by-nc/3.0/deed.zh\_TW](http://creativecommons.org/licenses/by-nc/3.0/deed.zh_TW).

The public XML records the same CC BY-NC 3.0 license.

***

### Acknowledgments

This dictionary is the product of the dedication and collaborative spirit of numerous individuals and organizations:

* **Virginia Fey:** For the original compilation of the dictionary.
* **Wu Ming-yi (吳明義老師):** For converting old Catholic orthography to a new, standardized version.
* **Taiwan Bible Society (台灣聖經公會):** For permission to digitize and adapt the dictionary.
* **GitHub Contributors:** For making the data accessible and easily integrable into FormosanBank.

***

### Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Fey, V. (1986). _Amis dictionary_. Taipei: The Bible Society.
* miaoski. (2023). _miaoski/amis-data_ \[Python]. GitHub. [https://github.com/miaoski/amis-data](https://github.com/miaoski/amis-data) (Original work published 2013)
* Wu, J. (2006). _Verb Classification, Case Marking, and Grammatical Relations in Amis_. University at Buffalo.
