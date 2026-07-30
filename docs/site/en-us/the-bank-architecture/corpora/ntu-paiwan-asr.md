# NTU Paiwan ASR

### **Overview**

The NTU Paiwan ASR Corpus contains Paiwan speech data collected by Professor Li-May Sung at National Taiwan University. It covers read text and spontaneous speech collected over two field years.

The current public corpus contains 260 XML files from 16 speakers across Northern, Central, Eastern, and Southern Paiwan. Speaker names are pseudonyms, and the two field years represent distinct participants.

#### **Content Summary**

* **Language Covered**: Paiwan
* **Corpus Content**:
  * Read speech with sentence-level text and audio alignment
  * Spontaneous recordings with a transcribed window and a companion XML stub for the untranscribed remainder
* **Data Contributors**: Sixteen speakers across two field years, with pseudonyms used throughout the public data

***

<!-- CORPUS STATS START -->
### Corpus Statistics

| | Paiwan<br>Central | Paiwan<br>Eastern | Paiwan<br>Northern | Paiwan<br>Southern |
| --- | --- | --- | --- | --- |
| Word count | 3,632 | 20,512 | 27,735 | 5,554 |
| Total audio | 1.5h | 6.6h | 8.1h | 1.5h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0.9h | 4.8h | 6.3h | 0.9h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0.5h | 1.9h | 1.9h | 0.6h |
| Translated words |  |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 0 | 0 | 0 | 0 |
| Morphologically segmented | 0 | 0 | 0 | 0 |
| Glossed words | 0 | 0 | 0 | 0 |

***

<!-- CORPUS STATS END -->


### Corpus Processing

Read-speech XML was built from ELAN sources. The second field year and spontaneous-speech data were built with `CodeAndDocs/build_y2_and_spontaneous.py`, followed by the standard cleaning, orthography, phonology, and validation steps. The public scripts apply pseudonyms and contain no real participant names.

Audio is hosted on Hugging Face rather than committed to Git. Running the corpus's `download_audio_data.sh` downloads the full recordings and uses `CodeAndDocs/extract_audio_clips.py` to recreate the sentence-level clips referenced by the XML. Complete reconstruction also requires the private raw recordings and speaker key, which are intentionally not public.

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

* The XML, processing documentation, and audio download script are available [in FormosanBank](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/NTU_Paiwan_ASR).

***

### **Copyright**

The current public XML records this corpus as CC BY. The central FormosanBank terms and AI-use addendum also apply.

***

### **Acknowledgments**

This corpus was developed through a collaborative effort led by **Dr. Sung** at the NTU Graduate Institute of Linguistics. The project is part of the broader FormosanBank initiative and would not have been possible without the contributions of Paiwan-speaking participants. Special thanks to all collaborators and the broader Paiwan community for their support and engagement in this vital preservation effort.

***

### Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Le Ferrand, É., Prud'hommeaux, E., Hartshorne, J. K., & Sung, L.-M. (2024). _NTU Paiwan ASR Corpus_. _Electronic Resource_.
