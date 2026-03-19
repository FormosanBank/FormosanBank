# Virginia Fey's Amis Dictionary

### Overview

Virginia Fey’s Amis Dictionary represents a significant effort to document the Amis language. Originally compiled in the mid-1980s and later updated with revised orthography, the dictionary provides a valuable linguistic resource for researchers, educators, and community members interested in Amis language study and revitalization.

This dictionary is a critical addition to FormosanBank, complementing other corpora and offering unique insights into the lexical richness and semantic nuances of Amis. It includes a wide range of entries, along with English and Chinese definitions, and in some cases, example sentences in Amis.

***

<!-- CORPUS STATS START -->
### Corpus Statistics

| | ami<br>Xiuguluan |
| --- | --- |
| Word count | 9,078 |
| Audio length | 0 |
| Translated sentences |  |
| &nbsp;&nbsp;&nbsp;&nbsp;English | 2,307 |
| &nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 2,478 |
| Morphologically segmented | 0 |
| Proportion glossed | 0% |

***

<!-- CORPUS STATS END -->


### Background

First compiled by Virginia Fey in 1986, this dictionary has undergone several stages of transformation:

1. **Original Documentation:** Initially published with older Catholic-style orthography, the dictionary aimed to be a reference guide for speakers and learners of Amis.
2. **Orthographic Revisions:** Thanks to the work of linguists—most notably Wu Ming-yi—this corpus was later converted into the newer orthography aligned with the Indigenous language writing systems recognized by the Council of Indigenous Peoples and other linguistic authorities.
3. **Digital Adaptation:** The digitized version comes from community-driven efforts as documented in repositories like [GitHub: miaoski/amis-data](https://github.com/miaoski/amis-data). This open-source collaboration made it possible to incorporate the dictionary into FormosanBank’s standardized XML format.

***

### Features of the Dictionary

* **Lexical Entries:** Includes a broad array of lexical items covering everyday objects, actions, cultural concepts, flora, fauna, and more.
* **Multilingual Definitions:** Each entry typically provides English and Chinese definitions, making the dictionary accessible to a wider audience, and allows broader research extents.
* **Example Sentences:** Select entries include Amis example sentences, offering context and illustrating usage.
* **Revised Orthography:** The dictionary data has been updated from older Catholic orthographic conventions to a standardized orthography used in current Indigenous language education and revitalization efforts.

***

### **Corpus Processing**

The processing pipeline for converting the dictionary data into FormosanBank’s standardized XML format included several stages:

1. **Data Acquisition:** The source data was obtained from the [miaoski/amis-data](https://github.com/miaoski/amis-data) GitHub repository. A CSV file provided lexical entries, English and Chinese definitions, and sometimes example sentences in Amis.
2. **Data Extraction and XML Conversion:**
   * Each entery in the CSV file consisted of a word in Amis, its English definition as well as the Chinese defintion. Some of the enteries would have example sentences and associated translations with them.
   * The CSV data was scraped and structured into XML format following the FormosanBank XML standard, ensuring compatibility with other corpora in FormosanBank.
   * Each dictionary entry was represented as an XML `<S>` element, containing
     * `<FORM>`: The original word or sentence.
     * `<TRANSL>`: For English and Chinese translations when available.
3. **Cleaning and Standardization:**
   * XML files underwent further cleaning to remove empty elements and standardize punctuation and orthography.
   * HTML escape codes were replaced with the corresponding characters, and a `kindOf="standard"` attribute was added to `<FORM>` elements. The original text would be `<FORM kindOf="original">`  and any text that will be standardized from this point will be in `<FORM kindOf="standard">`
4. **Quality Control:**
   * Several QC steps were performed, including:
     * **Cross-referencing word lists and API results** to ensure all entries were successfully processed.
     * **Validation of XML structure** to confirm compliance with the FormosanBank schema.
     * **Manual checks of random samples** to verify data integrity.
     * **Character Frequency Analysis** to spot any abnormalities in the orthography with [the official orthography](https://yongfu.name/temp-data/pdf/writingsystemsdoc.pdf) as well as [the ILRDF Dictionaries Corpus](ilrdf-dictionaries.md) as references.

***

### **Corpus Notes**

This section will be used to describe any notes regarding the corpus (e.g. explaining the presence of characters that aren't part of the standard orthography)

* According to Li et al. (2024), "Fey’s (1986) dictionary ... misses certain phonemic contrasts, such as the distinction between the glottal stop and the pharyngealized stop, for example, e.g., Central Amis ’op’op ‘frog’ vs. qopo ‘assemble’." However, the repo from which this corpus is derived states that "Thanks to Mr. Wu Ming-yi for rewriting the old Catholic spelling into the newer spelling of the original Minzu Kung Hui version." It is not clear whether this addressed the concerns raised by Li and colleagues, but the orthography seems to be a good match for our reference corpus.
* There are often multiple translations into the same non-Formosan language for a particular sentence. Thus do not assume there is only one element per target language.

***

### Significance

* **Language Preservation:** By documenting a wide range of lexical items and their meanings, this dictionary contributes to the preservation and revitalization of the Amis language.
* **Linguistic Research:** Researchers gain access to a standardized, machine-readable corpus that facilitates lexicographic analysis, comparative studies, and the development of natural language processing tools.
* **Educational Resource:** Educators and community members can draw on the dictionary to create learning materials, support classroom teaching, and develop language applications.

***

### Access Details

* The original digital online dictionary that was used to generate the corpus in FormosanBank can be found here: [https://github.com/miaoski/amis-data](https://github.com/miaoski/amis-data)
* The repo containing the ePark corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Virginia_Fey_Dictionary).

***

### Copyrights

According to [https://github.com/miaoski/amis-data](https://github.com/miaoski/amis-data) (the github repo we sourced this from), permission for a CC-BY-NC license was provided by the Taipei Bible Society:

> 謹感謝 台灣聖經公會 授權電子化。商業使用之授權，請洽\[台灣聖經公會]。

> 感謝吳明義老師將天主教的舊式拼法，改寫成原民會版本的新式拼法。

> This work is licensed under the Creative Commons 姓名標示-非商業性 3.0 Unported License. To view a copy of this license, visit [http://creativecommons.org/licenses/by-nc/3.0/deed.zh\_TW](http://creativecommons.org/licenses/by-nc/3.0/deed.zh_TW).

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
