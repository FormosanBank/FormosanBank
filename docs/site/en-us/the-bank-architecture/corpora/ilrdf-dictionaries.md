# ILRDF Dictionaries

### **Overview**

The [**Indigenous Languages Research and Development Foundation**](https://www.ilrdf.org.tw/) **(ILRDF)** dictionaries are a comprehensive digital resource designed to preserve and promote Taiwan’s indigenous languages. Built upon the foundational [writing systems ](https://yongfu.name/temp-data/pdf/writingsystemsdoc.pdf)announced in 2005 by the [Council of Indigenous Peoples](https://www.cip.gov.tw/en/index.html) and the Ministry of Education, these dictionaries represent the culmination of nearly seven years of collaborative effort involving hundreds of participants. The ILRDF dictionaries serve as an essential tool for language revitalization, education, and research, ensuring the cultural and linguistic heritage of Taiwan's indigenous peoples is preserved for future generations.&#x20;

The **ILRDF Dictionaries Corpus** is an integral part of the FormosanBank project, providing a rich and structured dataset of the 16 officially recognized Formosan languages: **Amis**, **Atayal**, **Saisiyat**, **Thao**, **Seediq**, **Bunun**, **Paiwan**, **Rukai**, **Truku**, **Kavalan**, **Tsou**, **Kanakanavu**, **Saaroa**, **Puyuma**, **Yami**, and **Sakizaya**. These dictionaries are invaluable for documenting and preserving linguistic diversity. They include text, audio recordings, and translations, making them a comprehensive resource for research, education, and language revitalization.

The corpus was rebuilt in 2026 from committed snapshots of the ILRDF dictionary API (retrieved 2026-05-04), keeping the sentence ids FormosanBank had already published from its 2024 scrape. It publishes two things per language:

| | Sentences | Headword entries |
| --- | ---: | ---: |
| Files | 16 | 16 |
| `S` records | 184,119 | 139,579 |
| Translations (`TRANSL`) | 187,314 | 164,849 |
| Recordings on a sentence (`AUDIO` in an `S`, at most one each) | 130,763 | — |
| Recordings without a transcription (`AUDIO` directly under `TEXT`) | 1,438 | — |
| Variant readings (`FORM kindOf="original" ver="alt"`) | 2,024 | 134 |

The **example sentences** (`XML/<Language>/<Language>.xml`) carry the source's Chinese translation and, where the source has one, a recording. The **headword entries** (`XML/<Language>/<Language>_dictionary.xml`) give one `<S>` per headword and one `<TRANSL>` per sense; each sense after the first is a `ver="alt"` TRANSL, and its part of speech is on that sense's `TRANSL/@notes`. Neither has a word or morpheme tier: the source carries no morphological analysis.

**Language and dialect** are as FormosanBank published them before the rebuild: Amis `Xiuguluan`, Atayal `Sekolik`, Bunun `Junqun`, Paiwan `Northern`, Puyuma `Nanwang`, Rukai `Wutai`, Seediq `Tegudaya`, Truku `Truku`; the other eight `unknown`. Seediq and Truku share `xml:lang="trv"`; `dialect="Truku"` is what makes the Truku files count as Truku.

***

<!-- CORPUS STATS START -->
### Corpus Statistics

| | Amis<br>Xiuguluan | Bunun<br>Junqun | Kavalan | Rukai<br>Wutai | Paiwan<br>Northern | Puyuma<br>Nanwang | Thao | Saaroa | Sakizaya | Yami | Atayal<br>Sekolik | Seediq<br>Tegudaya | Truku | Tsou | Kanakanavu | Saisiyat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Word count | 71,745 | 83,034 | 77,048 | 103,182 | 66,037 | 81,149 | 74,820 | 42,511 | 60,988 | 148,332 | 81,885 | 76,958 | 247,999 | 55,168 | 62,629 | 68,556 |
| Total audio | 8.4h | 12.3h | 10.9h | 14.7h | 9.2h | 10.6h | 9.2h | 6.9h | 8.2h | 6.3h | 10.5h | 8.5h | 7.1h | 4.3h | 12.5h | 9.2h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 8.4h | 12.3h | 10.9h | 14.7h | 9.2h | 10.6h | 9.2h | 6.9h | 8.2h | 6.3h | 10.5h | 8.5h | 7.1h | 4.3h | 12.5h | 9.2h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Translated words |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 0 | 18 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 71,745 | 83,016 | 77,035 | 103,176 | 66,012 | 81,142 | 74,817 | 42,511 | 60,988 | 148,332 | 81,885 | 76,949 | 247,999 | 55,168 | 62,593 | 68,556 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
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

The corpus is rebuilt from committed snapshots of the ILRDF API, with no network access and no environment variables:

```bash
Corpora/ILRDF_Dicts/CodeAndDocs/generate_xml.sh
```

Re-scraping the API is a separate, deliberate step ([`docs/reproduction.md`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/ILRDF_Dicts/CodeAndDocs/docs/reproduction.md)), because it can add, remove or reword source records. The FormosanBank commit the published XML was built against is recorded in [`provenance.json`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/ILRDF_Dicts/CodeAndDocs/provenance.json).

**Identifiers.** Sentences FormosanBank published before the rebuild keep their ids (`Amis_0` …). Sentences new in 2026 carry the source's GUID (`Amis_20a69646-e70a-f011-bd65-00155db40116`), and dictionary entries carry `d` + GUID. A record split into several `S` keeps its id on the first and adds `-opt`, `-opt3` … to the others. The matching of the 2024 sentences to the 2026 source was done once and frozen in [`main_id_ledger.csv`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/ILRDF_Dicts/CodeAndDocs/source_data/main_id_ledger.csv). Every previously published id that is no longer published, and why, is in [`old_to_new_ids.csv`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/ILRDF_Dicts/CodeAndDocs/old_to_new_ids.csv) (284 rows: 261 duplicates merged into the lowest id of their group, 4 sentences whose printed alternatives cannot be published as one sentence, 1 editor note, and 18 sentences printed twice with one recording).

**Sentences from the 2024 scrape — 1,251.** 1,251 sentences FormosanBank published in 2024 are no longer in ILRDF's current dictionary. They are kept as published then (same id, original text, translation and recording) and marked with `S/@source="ILRDF online dictionary, 2024 scrape …; no longer in ILRDF's current dictionary"`. Their standard tier and phonology are regenerated like every other record's.

**Derived tiers** come from the shared FormosanBank tools: the `standard` FORM from `standardize.py`, the IPA `PHON` from `add_phonology.py`. The original tier is assumed to be written in the 2005 official orthography (Ortho113) for all sixteen languages, so both PHON tiers are generated from the same table.

***

### Changes we make to the source

Everything below is reproducible from committed code and data; nothing was edited by hand.

**Source-fidelity repairs — 15 records.** The API sometimes returns material that is not Formosan text. These are corrected on the **original** tier through FormosanBank's manual-edits mechanism and listed in [`manual_edits.xml`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/ILRDF_Dicts/CodeAndDocs/manual_edits.xml), with a readable changelog beside it.

| What the source has | Records | Example |
| --- | ---: | --- |
| A part-of-speech label standing in for a word | 5 | `u數詞u paapuhla…` → `ʉnʉmʉ paapuhla…` (數詞 means "numeral") |
| Chinese editorial text welded onto a sentence | 8 | `…mawtu zau.這` → `…mawtu zau.` |
| A place name welded on without its parentheses | 1 | `…muntal mzai 水裏坑.` → `…muntal mzai (水裏坑).` |
| An editor note, 請刪除 ("please delete") | 1 | Puyuma_888 is not published; its recording is published without a transcription |

**Spaces next to punctuation at the edges of a form — 1,165 forms.** The source often leaves a space before sentence-final punctuation (`tukamia .`), or next to a quotation mark or bracket at the start or end of a sentence, and a few sentences open with a stray period (`. Aiza …`). The build removes exactly that space and nothing else (`… fafahiyan ako .` → `… fafahiyan ako.`). Every changed form, before and after, is in [`edge_space_report.csv`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/ILRDF_Dicts/CodeAndDocs/docs/edge_space_report.csv).

**Recovered `?` corruption — 61 tokens.** The source has lost the letter **ʉ** in places, leaving a literal `?`. Where the intended word can be confirmed it is restored automatically; where it cannot, the `?` is left visible rather than guessed at. The repair touches only Kanakanavu, Saaroa and Tsou, and only a `?` with a Formosan letter on *both* sides, so a sentence-final question mark is never affected. The candidate word must already occur, intact, elsewhere in the same language. Of 85 candidates, **61 were repaired — every one to ʉ** — and **24 were left unrepaired**.

**Source-side alternatives.** The source packs alternative wordings into one record three ways: `=` ("same as"), parentheses and slashes.

* a **spelling variant** stays one record, with the other spelling carried as a variant FORM (`kindOf="original" ver="alt"`); 2,006 in the sentence files.
* a **lexical alternative** becomes separate `<S>` records, named `-opt`, `-opt3` ….
* a parenthesis is kept as written when it is annotation: Chinese, a place or person name, a Japanese loanword in Romaji, or a number. Headword notation is left as the source writes it (`uculru(wa)` marks an optional ending).
* where the reading is not clear, the record is not published as text: 620 records, every one listed in [`split_report.csv`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/ILRDF_Dicts/CodeAndDocs/docs/split_report.csv).

For 73 previously published sentences the maintainer ruled on each one; those rulings, in [`alternative_rulings.json`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/ILRDF_Dicts/CodeAndDocs/source_data/alternative_rulings.json), replace the automatic resolution.

**Recordings.** Every recording was fingerprinted once and the result frozen, so the build never downloads anything.

* **One `S` per distinct recording; identical copies kept once.** The same sentence is often printed under several headwords, each copy with its own recording. Byte-identical copies are published once (98,529 copies). A sentence with *k* different recordings becomes *k* `S` with the same text and translations (15,599 added `S`).
* **FormosanBank's 2024 recording first.** Where the 2024 recording is byte-identical to a 2026 one, the file keeps its existing name. Where the 2026 source has a different usable recording, the 2026 one goes on the sentence under a new file name, and the 2024 recording is kept without a transcription (708 recordings).
* **File types are kept.** 2,162 recordings are WebM (`.webm`) and 16 MP4 (`.mp4`); they are not converted.
* **Yami: the village is in the file name.** The source records most Yami sentences in three villages. They are published as three `S` (朗島 first, then 野銀, then 漁人), with files named `<id>_<village>.<ext>`, e.g. `Yami_4596_野銀.mp3`.
* **Broken recordings are dropped.** 157 files from the 2026 source are empty, and 3 Paiwan files could not be downloaded. Where the sentence has another working recording, that one is used; 13 sentences are left with no recording.
* **One recording printed for several sentences.** In 285 cases the 2024 publication attached one recording to two to four different sentences. Where they were really one sentence printed twice (18 cases), they are merged into one `S`, the other reading kept as a variant. In the other 267 cases no member keeps the recording; the 244 that the 2026 source no longer has are published once without a transcription.
* **Recordings of alternatives.** When the source prints alternatives in one item, its recording is not attached to any of the resulting sentences; it is published without a transcription (486 recordings).

Every recording that is not published, and why, is in [`audio_not_published.csv`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/ILRDF_Dicts/CodeAndDocs/docs/audio_not_published.csv) (99,963 rows, 98,534 of them identical copies).

**Excluded content.** 820 all-zero audio ids found before the 2026 fingerprinting, two confirmed transcript mismatches, both uses of 40 audio ids assigned to different forms in different languages, three Kanakanavu lesson numbers that are not translations, and one Saisiyat headword sense that is an editor note.

***

### Notes and Issues

* **1,251 sentences are no longer in ILRDF's current dictionary.** They are kept as FormosanBank published them in 2024 and carry an `S/@source` saying so.
* **24 `?` are left where the source lost a letter** (Kanakanavu, Saaroa and Tsou), because the intended word could not be confirmed.
* **1,438 recordings are published without a transcription**, as `AUDIO` directly under `TEXT`, with `AUDIO/@source` naming the example it belongs to.
* **13 sentences have no recording**, because every recording the source has for them is broken or could not be downloaded.

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

FormosanBank publishes this corpus under **CC BY-NC 4.0** (the `copyright` value of every `TEXT` element).

The online dictionary's current [copyright statement](https://e-dictionary.ilrdf.org.tw/about?id=6c987092-47c7-ef11-bd58-00155db40116) says that ILRDF-authored works may be reproduced, publicly broadcast, or publicly transmitted within a reasonable scope when the source is identified. Other protected uses require permission unless an applicable fair-use provision applies. Users should consult the current statement and the source terms before reusing this corpus.

***

### Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and the dictionary/ies corresponding to the languages that were used:

* **Amis**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 阿美語_ \[Indigenous Languages Online Dictionary: Amis language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Atayal**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 泰雅語_ \[Indigenous Languages Online Dictionary: Atayal language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Bunun**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 布農語_ \[Indigenous Languages Online Dictionary: Bunun language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Kanakanavu**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 卡那卡那富語_ \[Indigenous Languages Online Dictionary: Kanakanavu language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Kavalan**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 噶瑪蘭語_ \[Indigenous Languages Online Dictionary: Kavalan language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Paiwan**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 排灣語_ \[Indigenous Languages Online Dictionary: Paiwan language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Puyuma**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 卑南語_ \[Indigenous Languages Online Dictionary: Puyuma language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Rukai**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 魯凱語_ \[Indigenous Languages Online Dictionary: Rukai language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Saaroa**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 拉阿魯哇語_ \[Indigenous Languages Online Dictionary: Saaroa language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Saisiyat**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 賽夏語_ \[Indigenous Languages Online Dictionary: Saisiyat language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Sakizaya**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 撒奇萊雅語_ \[Indigenous Languages Online Dictionary: Sakizaya language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Seediq**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 賽德克語_ \[Indigenous Languages Online Dictionary: Seediq language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Thao**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 邵語_ \[Indigenous Languages Online Dictionary: Thao language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Truku**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 太魯閣語_ \[Indigenous Languages Online Dictionary: Truku language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Tsou**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 鄒語_ \[Indigenous Languages Online Dictionary: Tsou language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Yami**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 雅美語_ \[Indigenous Languages Online Dictionary: Yami language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
