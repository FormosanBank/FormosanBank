# ILRDF Dictionaries

### **Overview**

The [**Indigenous Languages Research and Development Foundation**](https://www.ilrdf.org.tw/en/) **(ILRDF)** dictionaries are a comprehensive digital resource designed to preserve and promote Taiwan’s indigenous languages. Built upon the foundational [writing systems ](https://yongfu.name/temp-data/pdf/writingsystemsdoc.pdf)announced in 2005 by the [Council of Indigenous Peoples](https://www.cip.gov.tw/en/index.html) and the Ministry of Education, these dictionaries represent the culmination of nearly seven years of collaborative effort involving hundreds of participants. The ILRDF dictionaries serve as an essential tool for language revitalization, education, and research, ensuring the cultural and linguistic heritage of Taiwan's indigenous peoples is preserved for future generations.&#x20;

The **ILRDF Dictionaries Corpus** is an integral part of the FormosanBank project, providing a rich and structured dataset of the 16 officially recognized Formosan languages: **Amis**, **Atayal**, **Saisiyat**, **Thao**, **Seediq**, **Bunun**, **Paiwan**, **Rukai**, **Truku**, **Kavalan**, **Tsou**, **Kanakanavu**, **Saaroa**, **Puyuma**, **Yami**, and **Sakizaya**. These dictionaries are invaluable for documenting and preserving linguistic diversity. They include text, audio recordings, and translations, making them a comprehensive resource for research, education, and language revitalization.

***

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

Below, we outline the processing pipeline and quality control (QC) measures that were implemented to structure the data into a machine-readable format while ensuring its accuracy and usability.

1. **Data Extraction from PDFs**
   * The process began by extracting dictionary entries from PDF files provided by the ILRDF for each language. The entries were identified using specific markers (e.g., the symbol ★) to distinguish dictionary content from other text.
   * Extracted entries were stored as word lists in the `words_list` directory for further processing.
2. **API Integration for Word Data**
   * The extracted words were used to query the ILRDF API, retrieving:
     * **Definitions** of the words.
     * **Example sentences** demonstrating their use in context.
     * **Audio links** for pronunciation.
   * The results of these API calls were saved in `.PickleScrapes` for each language, enabling streamlined access and reuse.
3. **XML Conversion**
   * The scraped data was structured into XML format following the FormosanBank XML standard, ensuring compatibility with other corpora in FormosanBank.
   * Each dictionary entry was represented as an XML `<S>` element, containing:
     * `<FORM>`: The original word or phrase.
     * `<TRANSL>`: Chinese translations of the word or examples.
     * `<AUDIO>`: Links to or paths for audio files.
4. **Audio Download and Integration**
   * Audio files were downloaded using the API links and stored in language-specific subfolders under `XML/audio`.
   * The corresponding XML files were updated to include local paths to the audio files for seamless integration.
5. **Cleaning and Standardization**
   * XML files underwent further cleaning to remove empty elements and standardize punctuation and orthography.
   * HTML escape codes were replaced with the corresponding characters, and a `kindOf="standard"` attribute was added to `<FORM>` elements. The original text would be `<FORM kindOf="original">`  and any text that will be standardized from this point will be in `<FORM kindOf="standard">`
6. **Quality Control**
   * Several QC steps were performed, including:
     * **Cross-referencing word lists and API results** to ensure all entries were successfully processed.
     * **Validation of XML structure** to confirm compliance with the FormosanBank schema.
     * **Manual checks of random samples** to verify data integrity.
     * **Character Frequency Analysis** to spot any abnormalities in the orthography with [the official orthography](https://yongfu.name/temp-data/pdf/writingsystemsdoc.pdf) as reference.

***

### Key Features of the Corpus

1. **Comprehensive Data**
   * The corpus contains a total of **659295 tokens** and over **135 hours of audio**, offering a rich and comprehensive resource for the study of Formosan languages. Its quality is ensured by the extensive effort and meticulous processes involved in its creation. Below is a breakdown of the token count and audio duration for each language:
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
* The repo containing the ePark corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/ILRDF_Dicts).

***

### **Acknowledgments**

This project is made possible through the collaboration of native speakers, linguists, and researchers. Special thanks to the **Indigenous Languages Research and Development Foundation** ([ILRDF](https://www.ilrdf.org.tw/en/)) for their invaluable contributions and to the broader Formosan communities for their support and engagement.

***

### **Copyright**

According to the [copyrights page](https://e-dictionary.ilrdf.org.tw/copyright.htm) of the online dictionaries, work produced by the ILRDF, such as the dictionaries, is under "fair use" and can be reproduced:

> \[Translated] The works published on this website and published in the name of the Association, that is, if the author is the Association, may be reproduced, publicly broadcast or publicly transmitted within a reasonable scope; When using, please indicate the source.

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
