# NTU Paiwan ASR

### **Overview**

The NTU Paiwan ASR Corpus is a linguistically rich dataset created as part of the efforts to enrich **FormosanBank**. The corpus was developed through a collaborative effort with one of the main collaborators of FormosanBank, [**Dr. Sung**](https://drive.google.com/file/d/1pkqbvFYHUydbiGRhPIgkBigkh2hpSCYi/view) from National Taiwan University and represents a pioneering contribution.

This corpus includes mostly read speech aligned with its corresponding text in addition to a small collection of spontaneous speech recordings. It is designed to support language preservation, linguistic research, and, notably, the development of automated speech recognition (ASR) tools tailored specifically for Paiwan.

#### **Content Summary**

* **Language Covered**: Paiwan
* **Corpus Content**:
  * Texts with aligned audio for read speech
  * Spontaneous speech recordings
* **Data Contributors**: Six speakers (pseudonyms used to maintain anonymity)

#### **Data Summary**

| Metric         | Read Speech | Spontaneous Speech | Total    |
| -------------- | ----------- | ------------------ | -------- |
| **Topics**     | 11          | 51                 | 62       |
| **Recordings** | 16          | 98                 | 114      |
| **Duration**   | 1:24:10     | 9:10:33            | 10:34:43 |

#### Data Breakdown by Participant

Below is a detailed description of the data outlying for each speaker how many recordings are available of them and the duration they have spoken for. As mentioned above, participants' names are pseudonyms for privacy.

| Speaker | Number of Recordings (N)	 | Total Duration |
| ------- | ------------------------- | -------------- |
| Loris   | 23                        | 2:05:16        |
| Zendar  | 35                        | 3:01:01        |
| Nira    | 30                        | 2:29:31        |
| Belmira | 8                         | 1:00:57        |
| Falin   | 7                         | 0:51:48        |
| Sarnix  | 11                        | 1:06:10        |

***

<!-- CORPUS STATS START -->
### Corpus Statistics

| | Paiwan<br>Central | Paiwan<br>Eastern | Paiwan<br>Northern |
| --- | --- | --- | --- |
| Word count | 3,136 | 10,688 | 20,672 |
| Total audio | 0.8h | 2.7h | 4.6h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0.8h | 2.7h | 4.6h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 | 0 | 0 |
| Translated words |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 0 | 0 | 0 |
| Morphologically segmented | 0 | 0 | 0 |
| Glossed words | 0 | 0 | 0 |

***

<!-- CORPUS STATS END -->


### Corpus Processing

The data was processed thoroughly to ensure compatibility with FormosanBank standards while ensuring accuracy and usability. The corpus collected by Dr. Sung was structured by associating each topic with its corresponding audio recordings and transcriptions (for read speech) for each speaker.  This data was then processed to transform the data into [FormosanBank XML Format](../formosanbank-xml-format.md). Below is a detailed description of the process.

1. **XML Conversion**
   * the transcribed text files were processed to create the XML files out of, ensuring compatibility with other corpora in FormosanBank.
   * Each topic for each of the participant represent on file, and each file contained the following elements:
     * `<FORM>`: Containing the original sentence in Paiwan
     * `<AUDIO>`: Name of the audio file associated with the sentence
2. **Cleaning and Standardization**
   * XML files underwent further cleaning to remove empty elements and standardize punctuation and orthography.
   * HTML escape codes were replaced with the corresponding characters, and a `kindOf="standard"` attribute was added to `<FORM>` elements. The original text would be `<FORM kindOf="original">`  and any text that will be standardized from this point will be in `<FORM kindOf="standard">`
3. **Quality Control**
   * Several QC steps were performed, including:
     * **Cross-referencing word lists and API results** to ensure all entries were successfully processed.
     * **Validation of XML structure** to confirm compliance with the FormosanBank schema.
     * **Manual checks of random samples** to verify data integrity.
     * **Character Frequency Analysis** to spot any abnormalities in the orthography with [the official orthography](https://yongfu.name/temp-data/pdf/writingsystemsdoc.pdf) as well as [the ILRDF Dictionaries Corpus](ilrdf-dictionaries.md) as references.

***

### **Applications**

The NTU Paiwan ASR Corpus is a crucial resource for advancing research and technology in several key areas:

* **Automated Speech Recognition (ASR)**: The aligned text and audio make this corpus particularly valuable for developing ASR systems tailored to Paiwan, enabling future tools like transcription software and voice interfaces in the language.
* **Language Revitalization**: Supports the creation of educational materials and language-learning resources for Paiwan speakers and learners.
* **Speech Technology Development**: Facilitates tools such as text-to-speech systems and pronunciation modeling.
* **Linguistic Analysis**: Enables studies on syntax, phonology, discourse structures, and other linguistic phenomena.
* **Comparative Studies**: Supports research on shared features and differences among Formosan languages.

***

### **Access Details**

* The corpus as part of FormosanBank can be accessed from [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/NTU_Paiwan_ASR/XML).
* The repo containing the ePark corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/NTU_Paiwan_ASR/CodeAndDocs).

***

### **Copyright**

Since this corpus was collected as part of Formosan Bank in the first place, the copyright restrictions applied to it are the ones governing FormosanBank (see below).

***

### **Acknowledgments**

This corpus was developed through a collaborative effort led by **Dr. Sung** at the NTU Graduate Institute of Linguistics. The project is part of the broader FormosanBank initiative and would not have been possible without the contributions of Paiwan-speaking participants. Special thanks to all collaborators and the broader Paiwan community for their support and engagement in this vital preservation effort.

***

### Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Le Ferrand, É., Prud'hommeaux, E., Hartshorne, J. K., & Sung, L.-M. (2024). _NTU Paiwan ASR Corpus_. _Electronic Resource_.

