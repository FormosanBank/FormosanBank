# ILRDF Dictionaries

### **Overview**

The [**Indigenous Languages Research and Development Foundation**](https://www.ilrdf.org.tw/) **(ILRDF)** dictionaries are a comprehensive digital resource designed to preserve and promote Taiwan’s indigenous languages. Built upon the foundational [writing systems ](https://yongfu.name/temp-data/pdf/writingsystemsdoc.pdf)announced in 2005 by the [Council of Indigenous Peoples](https://www.cip.gov.tw/en/index.html) and the Ministry of Education, these dictionaries represent the culmination of nearly seven years of collaborative effort involving hundreds of participants. The ILRDF dictionaries serve as an essential tool for language revitalization, education, and research, ensuring the cultural and linguistic heritage of Taiwan's indigenous peoples is preserved for future generations.&#x20;

The **ILRDF Dictionaries Corpus** is an integral part of the FormosanBank project, providing a rich and structured dataset of the 16 officially recognized Formosan languages: **Amis**, **Atayal**, **Saisiyat**, **Thao**, **Seediq**, **Bunun**, **Paiwan**, **Rukai**, **Truku**, **Kavalan**, **Tsou**, **Kanakanavu**, **Saaroa**, **Puyuma**, **Yami**, and **Sakizaya**. These dictionaries are invaluable for documenting and preserving linguistic diversity. They include text, audio recordings, and translations, making them a comprehensive resource for research, education, and language revitalization.

The corpus publishes two things per language:

| | Sentences | Headword entries |
| --- | ---: | ---: |
| Files | 16 | 16 |
| `S` records | 167,241 | 139,097 |
| Translations | 169,364 | 164,359 |
| Audio links | 132,281 | — |

The **example sentences** carry the source's Chinese translation and, where the source has one, a link to its audio recording. The **headword entries**, in `XML/<Language>/<Language>_dictionary.xml`, give one `<S>` per headword and one `<TRANSL>` per sense, with each sense's part of speech on its own `TRANSL/@notes`. Neither has a word or morpheme tier: the source carries no morphological analysis.

***

<!-- CORPUS STATS START -->
### Corpus Statistics

| | Amis<br>Xiuguluan | Bunun<br>Junqun | Kavalan | Rukai<br>Wutai | Paiwan<br>Northern | Puyuma<br>Nanwang | Thao | Saaroa | Sakizaya | Yami | Atayal<br>Sekolik | Seediq<br>Tegudaya | Truku | Tsou | Kanakanavu | Saisiyat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Word count | 37,140 | 53,541 | 53,088 | 60,572 | 38,316 | 51,590 | 44,889 | 19,149 | 32,233 | 39,790 | 53,688 | 51,673 | 27,973 | 19,184 | 38,130 | 37,491 |
| Total audio | 8.4h | 12.3h | 10.9h | 14.7h | 9.2h | 10.6h | 9.2h | 6.9h | 8.2h | 6.3h | 10.5h | 8.5h | 7.1h | 4.3h | 12.5h | 9.2h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 8.4h | 12.3h | 10.9h | 14.7h | 9.2h | 10.6h | 9.2h | 6.9h | 8.2h | 6.3h | 10.5h | 8.5h | 7.1h | 4.3h | 12.5h | 9.2h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Translated words |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 37,140 | 53,541 | 53,088 | 60,572 | 38,316 | 51,590 | 44,886 | 19,149 | 32,233 | 39,790 | 53,688 | 51,664 | 27,973 | 19,184 | 38,130 | 37,491 |
| Morphologically segmented | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Glossed words | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

***

<!-- CORPUS STATS END -->


### **Background**

The project began in 2007 with the systematic compilation of dictionaries for  the **16 indigenous languages**. Each dictionary took two years to complete, involving the dedication of language teachers, experts, and scholars. By 2014, all dictionaries had been completed, marking a significant milestone in the documentation of Taiwan's indigenous languages.

Recognizing the importance of sustainability, the ILRDF digitized these dictionaries and launched the **Indigenous Languages Online Dictionary** platform. This digital transformation allows the dictionaries to remain dynamic, expandable, and maintainable, becoming a vital resource for language promotion, teaching, research, and learning.

***

### **Features of the ILRDF Online Dictionaries**

1. **Online Access and Search**
   * Users can search for words, view their definitions, listen to pronunciations, and explore examples in real-time.
2. **Downloadable Resources**
   * The platform offers downloadable content for offline learning, including:
     * Word cards
     * Full dictionary text
     * Chinese-indexed versions
3. **Interactive Learning Tools**
   * Features include:
     * **Online Quizzes:** Test your knowledge of the languages.
     * **Word Suggestions:** Contribute or recommend new words.
     * **Examples and Applications:** Practical sentences for immediate learning and use.
4. **Community Engagement**
   * Users can share feedback or discuss usage questions in the **discussion area**, fostering a collaborative environment.
   * Periodic expert consultations ensure updates and accuracy, with the final decisions on word usage returned to the respective indigenous communities
5. **API for Data Collection**
   * The ILRDF provides an **API** that facilitates streamlined data collection and integration into FormosanBank, ensuring efficient access to the full range of dictionary content.

***

### Processing the ILRDF Corpus

The corpus is rebuilt from committed snapshots of the ILRDF API, so anyone can reproduce it without network access:

```bash
export FORMOSANBANK_AUTHORITY=/path/to/a/clean/FormosanBank/checkout
CodeAndDocs/make_xml.sh
```

Re-scraping the API is a separate, deliberate step (`refresh_source.sh`), because it can add, remove or reword source records — and each of those moves a published identifier.

**Identifiers.** Every sentence and entry id carries the source's own GUID: `Amis_20a69646-e70a-f011-bd65-00155db40116`, with a `d` before the GUID for dictionary entries. A published id therefore survives our later corrections to the text, which an id derived from the text itself would not. `CodeAndDocs/source_data/published_ids.csv` is a lockfile of all 306,338 of them, and the build fails if one disappears or changes meaning without being declared.

**Derived tiers** come from the shared FormosanBank tools and nothing else: the `standard` FORM from `standardize.py`, the IPA `PHON` from `add_phonology.py`. The corpus's own scripts emit source tiers only.

***

### Changes we make to the source

Everything below is reproducible from committed code and data; nothing was edited by hand.

**Source-fidelity repairs — 15 records.** The API sometimes returns material that is not Formosan text: a part-of-speech label standing in for a word (`u數詞u paapuhla…` → `ʉnʉmʉ paapuhla…`, where 數詞 means "numeral"), or Chinese editorial text welded onto a sentence (`…mawtu zau.這` → `…mawtu zau.`). These are corrected on the **original** tier through FormosanBank's manual-edits mechanism, and each one is listed in [`CodeAndDocs/manual_edits.xml`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/ILRDF_Dicts/CodeAndDocs/manual_edits.xml) with a readable changelog beside it.

**Recovered `?` corruption — 61 tokens.** The source has lost the letter **ʉ** in places, leaving a literal `?`. Where the intended word can be confirmed it is restored automatically; where it cannot, the `?` is left visible rather than guessed at. The repair touches only Kanakanavu, Saaroa and Tsou, and only a `?` with a Formosan letter on *both* sides — so a sentence-final question mark is never affected (1,128 of those survive untouched). The candidate must already appear, intact, elsewhere in the same language, in a sentence containing no `?`, so a corruption cannot vouch for itself. Of 85 candidates, **61 were repaired — every one to ʉ** — with supporting evidence ranging from 2 to 54 other occurrences. **24 were left unrepaired** for want of an attested candidate.

**Source-side alternatives.** The source packs alternative wordings into a single record using `=`, parentheses and slashes. Two different things hide under that, and they are treated differently:

* a **spelling variant** — the same utterance written differently, `hiya` / `hiyaʼ` — stays one record, with the other spellings carried as `FORM[@kindOf="alternate"]`. There are **1,998** of these.
* a **lexical alternative** — different wording, `tanux` / `(mnaw tay tanux)` — becomes separate `<S>` records.

A parenthesis is kept as the source wrote it when it holds Chinese, a Japanese loanword in Romaji, a proper noun or a number: those are annotation, not alternation. Headword notation is left alone entirely — `uculru(wa)` marks an optional ending, not an annotation.

**2,049 records were resolved into 2,146.** Where the reading was not clear we delete rather than guess: a phrase alternative that shares no word with the term it replaces could substitute for any span, and two options too dissimilar to be one word spelled two ways might be either. **718 fragments were dropped on those grounds, and every one is listed in [`CodeAndDocs/docs/split_report.csv`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/ILRDF_Dicts/CodeAndDocs/docs/split_report.csv).**

Every rewritten record keeps its source string in `FORM/@notes`, and a record split into several takes a letter suffix on its id (`…_a`, `…_b`).

**Excluded content.** 820 all-zero audio ids, two confirmed transcript mismatches, both uses of 40 audio ids assigned to different forms in different languages, and three Kanakanavu lesson numbers that are not translations.

***

### Key Features of the Corpus

1. **Comprehensive Data**
   * The corpus offers a rich resource for the study of Formosan languages: example sentences with audio for most of them, plus the full headword inventory of all sixteen dictionaries. The generated statistics table above gives the current breakdown by language.
2. **Audio Integration**
   * High-quality audio files accompany most example sentences, providing an invaluable resource for analyzing pronunciation, phonology, and spoken language contexts.
3. **Translation Availability**
   * Example sentences are translated into **Chinese**, ensuring accessibility for researchers and learners.

***

### **Significance**

1. **Language Preservation**
   * The dictionaries support the documentation and revitalization of endangered indigenous languages, ensuring they remain a living cultural asset.
2. **Accessibility**
   * The online platform makes these resources available to a global audience, transcending geographical boundaries.
3. **Education and Research**
   * With rich examples and structured content, the dictionaries are invaluable for both language learners and researchers.

***

### **Access Details**

* Visit the **Indigenous Languages Online Dictionary** at [https://e-dictionary.ilrdf.org.tw](https://e-dictionary.ilrdf.org.tw) to explore the 16 indigenous language dictionaries.
* The corpus XML, retained processing materials, and audio download script are available [in FormosanBank](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/ILRDF_Dicts).

***

### **Acknowledgments**

This project is made possible through the collaboration of native speakers, linguists, and researchers. Special thanks to the **Indigenous Languages Research and Development Foundation** ([ILRDF](https://www.ilrdf.org.tw/)) for their invaluable contributions and to the broader Formosan communities for their support and engagement.

***

### **Copyright**

FormosanBank publishes this corpus under **CC BY-NC 4.0**.

The online dictionary's [copyright statement](https://e-dictionary.ilrdf.org.tw/about?id=6c987092-47c7-ef11-bd58-00155db40116) allows quotation for research and teaching within a reasonable scope when the source is identified, and requires permission beyond that. This corpus is made available under those terms, with attribution to the Council of Indigenous Peoples and to ILRDF. Downstream users remain responsible for the source's attribution requirements and for applicable law; see `CodeAndDocs/source_data/RIGHTS.md` in the repository.

***

### Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and the dictionary/ies corresponding to the languages that were used:

* **Amis**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). _原住民族語言線上辭典: 阿美語_ \[Indigenous languages online dictionary: Amis language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Atayal**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). _原住民族語言線上辭典: 泰雅語_ \[Indigenous languages online dictionary: Atayal language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Bunun**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). _原住民族語言線上辭典: 布農語_ \[Indigenous languages online dictionary: Bunun language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Kanakanavu**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). _原住民族語言線上辭典: 卡那卡那富語_ \[Indigenous languages online dictionary: Kanakanavu language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Kavalan**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). _原住民族語言線上辭典: 噶瑪蘭語_ \[Indigenous languages online dictionary: Kavalan language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Paiwan**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). _原住民族語言線上辭典: 排灣語_ \[Indigenous languages online dictionary: Paiwan language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Puyuma**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). _原住民族語言線上辭典: 卑南語_ \[Indigenous languages online dictionary: Puyuma language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Rukai**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). _原住民族語言線上辭典: 魯凱語_ \[Indigenous languages online dictionary: Rukai language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Saaroa**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). _原住民族語言線上辭典: 拉阿魯哇語_ \[Indigenous languages online dictionary: Saaroa language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Saisiyat**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). _原住民族語言線上辭典: 賽夏語_ \[Indigenous languages online dictionary: Saisiyat language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Sakizaya**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). _原住民族語言線上辭典: 撒奇萊雅語_ \[Indigenous languages online dictionary: Sakizaya language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Seediq**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). _原住民族語言線上辭典: 賽德克語_ \[Indigenous languages online dictionary: Seediq language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Thao**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). _原住民族語言線上辭典: 邵語_ \[Indigenous languages online dictionary: Thao language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Truku**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). _原住民族語言線上辭典: 太魯閣語_ \[Indigenous languages online dictionary: Truku language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Tsou**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). _原住民族語言線上辭典: 鄒語_ \[Indigenous languages online dictionary: Tsou language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Yami**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). _原住民族語言線上辭典: 雅美語_ \[Indigenous languages online dictionary: Yami language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
