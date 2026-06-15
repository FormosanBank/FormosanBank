# NTU Corpus of Formosan Languages

[The NTU Corpus of Formosan Languages](https://corpus.linguistics.ntu.edu.tw/#/) is the first large open corpus of Formosan languages. The NTU Corpus is a comprehensive and meticulously curated dataset representing 10 Indigenous Formosan languages: Kanakanavu, Rukai, Saisiyat, Tsou, Kavalan, Amis, Seediq, Atayal, Sakizaya, and Bunun. This corpus includes texts, audio recordings, elicited sentences, and example sentences from various sources such as grammar books and narrative collections. Designed to support linguistic research and revitalization efforts, the NTU Corpus provides a unique window into the diversity and complexity of Formosan languages.

It consists of three main sections:

* Grammar (examples derived from grammar textbooks)

* Sentences (individual sentences recorded during fieldwork and transcribed and glossed).

* Stories (narratives recorded during fieldwork and transcribed and glossed.)

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Amis<br>Coastal | Bunun<br>Junqun | Kavalan | Rukai<br>Wutai | Sakizaya | Atayal<br>Wenshui | Seediq<br>Tegudaya | Tsou | Kanakanabu | Saisiyat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Word count | 7,561 | 22,922 | 16,244 | 17,931 | 13,985 | 5,856 | 23,341 | 10,107 | 20,074 | 10,816 |
| Total audio | 1.2h | 1.6h | 2.9h | 1.6h | 2.3h | 1.1h | 3.3h | 1.0h | 4.0h | 1.8h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 1.2h | 1.6h | 2.9h | 1.6h | 2.3h | 1.1h | 3.3h | 1.0h | 4.0h | 1.8h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Translated words |  |  |  |  |  |  |  |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 7,516 | 22,843 | 16,179 | 17,915 | 8,949 | 5,851 | 18,427 | 10,107 | 14,968 | 10,800 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 7,561 | 22,832 | 16,242 | 17,914 | 13,983 | 5,851 | 23,341 | 10,107 | 20,062 | 10,800 |
| Morphologically segmented | 7,561 | 22,853 | 16,244 | 17,890 | 12,987 | 5,855 | 21,931 | 10,107 | 18,678 | 10,816 |
| Glossed words | 7,561 | 22,853 | 16,244 | 17,890 | 12,987 | 5,855 | 21,931 | 10,107 | 18,678 | 10,816 |

***

<!-- CORPUS STATS END -->


***

## **Glossing Conventions**

The glossing conventions for the NTU Corpus primarily follow the [**Leipzig Glossing Rules**](https://www.eva.mpg.de/lingua/resources/glossing-rules.php), with modifications to better capture the linguistic specificity of Formosan languages. Below are the alternative treatments for Leipzig Rules 6, 7, and 10, as well as other adopted coding conventions.

### **Modifications to Leipzig Glossing Rules**

1. **Rule 6 - Non-Overt Elements**
   * The symbol `[ ]` or `Ø` is not used for glossing non-overt elements.
   * Example:
     * **akoy** (Saisiyat) is glossed as `AF.many`.
     * In Tsou, the non-overt element in **bonu** ('to eat') is glossed as `eat.AF`.
2. **Rule 7 - Inherent Categories**
   * Coding for inherent categories is **not used**.
3. **Rule 10 - Reduplication**
   * Reduplication is not marked by the tilde `~`. Instead, the following conventions are adopted:
     * **Ca Reduplication:** Marked as `Ca-`.
       * Example: **ha-hila** (Saisiyat) is glossed as `Ca-sun`.
     * **Prefix-Type Reduplication:** Marked as `red-` if the reduplicated portion is at the beginning of the word.
       * Example: **m-li-lizaq** (Kavalan) is glossed as `af-red-happy`.
     * **Infix-Type Reduplication:** Marked as `<red>` if the reduplicated portion occurs in the medial position of the word.
       * Example: **sa-ru\<mi'a>mi'ad** (Amis) is glossed as `sa-<red>day`.

### **Glossing Focus Markers**

The following focus markers are **new abbreviations** introduced in the NTU Corpus to represent the specific focus morphology of Formosan languages:

* **AF:** Agent Focus
* **PF:** Patient Focus
* **RF (IF):** Referential Focus (Instrumental Focus)
* **LF:** Locative Focus

### **Focus Morphology in Tsou**

The Tsou language has a unique focus system compared to other Formosan languages:

* **Agent Focus (AF):** Glossed after the verb stem.
* **Patient Focus (PF):** Glossed similarly.
* Example:
  * **bonU/ana** ('to eat') → `eat.AF/eat.PF`.
  * **boacU/eoeca** ('to bite') → `bite.AF/bite.PF`.
  * Verbs with -m- or m- forms for AF:
    * **tmoecU/teoca** ('to hack') → `hack.AF/hack.PF`.
    * **matvo'ho/patvo'ha** ('to dare to say') → `dare.to.say.AF/dare.to.say.PF`.
    * **mooteo/totea** ('to wait') → `wait.AF/wait.PF`.

### **Replaced Abbreviations**

The NTU Corpus uses alternative abbreviations to standard Leipzig Glossing Rules to better fit Formosan languages:

| **Leipzig Abbreviation** | **NTU Corpus Abbreviation** |
| ------------------------ | --------------------------- |
| `caus`                   | `cau`                       |
| `dem`                    | `'this'` and `'that'`       |
| `nmlz`                   | `nmz`                       |
| `recp`                   | `rec`                       |

### **Discourse Coding**

The original corpus has a great deal of discourse coding for Sentences and Stories. For purposes of FormosanBank, this has been removed. Interested parties should consult the original.

***

## Access Details

* The repo containing this corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/NTUFormosanCorpus).

***

## Notes

### Major issues, user beware

* It is known that the audio does not always match the text. It is not clear how common this is. A list of audio clips that are suspiciously long or short given how many words in the utterance can be found in [audio_duration_issues.csv](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/NTUFormosanCorpus/audio_duration_issues.csv)

* There are sentences (last count, 56) where the glosses are clearly wrong. Most, but not all, of these cases involve a missing gloss, resulting in glosses being out of sync with the words. See [sentences_with_bad_glosses_removed.csv](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/NTUFormosanCorpus/sentences_with_bad_glosses_removed.csv).

* At the time the NTU Formosan Corpus was created, there were no clear conventions as to whether to write a clitic as a stand-alone word. However, the glosses almost always treat the clitic as attached to another word. This results in sometimes two words corresponding to a single W element. A list of such cases is found in [clitics.csv](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/NTUFormosanCorpus/clitics.csv) (currently 819 cases).

* There are some translated but unglossed wordlists. These lack W elements on account of not having any segmentation or glossing.

* Even after accounting for the two issues above, the number of W elements does not always match the number of words in the sentence. These cases are listed in [validation_results.csv](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/NTUFormosanCorpus/validation_results.csv) (current count: 366).

* There are a number of cases where, in the glosses, the wordform and syntactic glosses differ in the number of segments. Many of these cases appear to be due to failing to segment the wordform. Others may be due to the wordforms and syntactic glosses being out of alignment. Known examples are recorded in [validation_m_results.csv](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/NTUFormosanCorpus/validation_m_mismatches.csv) (current count: 1,415).

* The original data often contains transcriber notes or translation notes in the text. These have been removed from the text and placed in a `notes` attribute in the corresponding `FORM`. However, such information may not always be included (it was complicated to extract), so users who are interested in the notes and parentheticals should consult the online version of the NTU Formosan Corpus, which is meant to be read by a human. The `id` of the XML file (check the `TEXT` header element) tells you what the file is on NTU Formosan Corpus. The `id` of the `S` element tells you which line in the NTU Formosan Corpus.

* The original data also has notes written below the free translation. Many of these simply state the source of the information, but others are useful and relevant. These are NOT included in FormosanBank. (Not because they aren't interesting, but because it's harder than you'd think to extract them and figure out where to put them.)

## Minor notes

* The Amis text does not use the `^` glottal stop. `^` does appear in the original, but as a discourse marker. 

* The Rukai marker `_` is not used in the text.

* A small subset of sentences in the Grammar subcorpus have no word-by-word glosses (the original data does not include them).

* The original data has a lot of prosodic markup and other dialog markup. This has all been removed.

* Item 323 in sentence/Kanakanavu_Kanakanavu/1.json is excluded because it involves two sentence fragments that are hard to deal with.

* Item 12 from sentence/Bunun_Isbukun/59.json is misaligned in the original, but the alignment is straightforward and was corrected by hand.

* In the Sakizaya texts, "i tina" and "i tiza" are sometimes written as "itina" and "itiza". However, the glosses treat them as separate words. We have edited the text to write them as separate words.

* In the Sakizaya texts, "paza'ci" was written as a single word, but based on glossing and other examples, it appears to be "paza' ci". This was corrected as part of parse_grammar.py

* In the Kanakanavu texts, "tia'apacangcangarʉʉn" was often written as one word, whereas it appears that "tia 'apacangcangarʉʉn" is more likely based on glossing. We made this change in parse_grammar.py.

* In the Kanakanavu sentence subcorpus, "∅" appears 31 times. Its interpretation is unclear. 

***

## Copyright

CC BY-NC

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Sung, L. M., Lily, I., Hsieh, F., &amp; Lin, Z. (2008). Developing an online corpus of Formosan languages. Taiwan Journal of Linguistics, 6(2).