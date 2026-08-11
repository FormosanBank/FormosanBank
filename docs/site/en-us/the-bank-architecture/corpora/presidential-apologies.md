# Presidential Apologies

### **Overview**

On **August 1, 2016**, President Tsai Ing-wen delivered a historic apology to Taiwan's indigenous peoples on behalf of the government during **Indigenous Peoples' Day**. The apology addressed the pain and mistreatment endured by indigenous communities over four centuries and marked the establishment of the **Presidential Office Indigenous Historical Justice and Transitional Justice Committee (Indigenous Justice Committee)**.&#x20;

This apology text, as part of the effort to promote **historical justice**, has been translated into the 16 officially recognized Formosan languages: **Amis**, **Atayal**, **Saisiyat**, **Thao**, **Seediq**, **Bunun**, **Paiwan**, **Rukai**, **Truku**, **Kavalan**, **Tsou**, **Kanakanavu**, **Saaroa**, **Puyuma**, **Yami**, and **Sakizaya**. The translated apologies are the main texts forming the corpus described here. This corpus consists exclusively of **text data.** The apology text is also available in **English** and **Chinese**.

***

<!-- CORPUS STATS START -->
### Corpus Statistics

| | Amis<br>Xiuguluan | Bunun<br>Junqun | Kavalan | Rukai<br>Wutai | Paiwan<br>Central | Puyuma<br>Nanwang | Thao | Saaroa | Sakizaya | Yami | Atayal<br>Sekolik | Seediq<br>Tegudaya | Truku | Tsou | Kanakanavu | Saisiyat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Word count | 1,929 | 1,548 | 2,209 | 1,948 | 2,378 | 2,091 | 1,854 | 1,114 | 1,735 | 1,640 | 2,445 | 1,508 | 1,853 | 2,072 | 1,543 | 1,639 |
| Total audio | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Translated words |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 1,929 | 1,548 | 2,209 | 1,948 | 2,378 | 2,091 | 1,854 | 1,114 | 1,735 | 1,640 | 2,445 | 1,508 | 1,853 | 2,072 | 1,543 | 1,639 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 1,929 | 1,548 | 2,209 | 1,948 | 2,378 | 2,091 | 1,854 | 1,114 | 1,735 | 1,640 | 2,445 | 1,508 | 1,853 | 2,072 | 1,543 | 1,639 |
| Morphologically segmented | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Glossed words | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

***

<!-- CORPUS STATS END -->


### **Corpus Processing**

The Presidential Apology corpus was developed using officially released translations of the apology by the President of Taiwan. These translations were provided in 16 official Formosan languages, as well as in Chinese and English. The corpus was processed following these steps:

1.  **Alignment of Sentences Across Translations**\
    Each paragraph in the Formosan languages was aligned with its corresponding translations in English and Chinese. This was accomplished by segmenting the apology into 33 consistent sections across all languages. An example image is shown below. The only exception to this was Kanakanavu where I did it separately with only 29 sections because the sectioning was quite different from the rest.

    <figure><img src="../../.gitbook/assets/Screenshot 2024-12-08 at 9.41.01 PM.png" alt=""><figcaption></figcaption></figure>
2. **XML Generation Following FormosanBank Standards**\
   The aligned data was then structured into XML files adhering to the FormosanBank standard. Each XML file contained:
   * Sentence-level (`S`) elements for each section, with sub-elements `FORM` for the Formosan language text and `TRANSL` for English and Chinese translations.
   * Metadata and language codes specific to each Formosan language.
3. **Cleaning and Standardization**\
   Once the XML files were created, they underwent multiple cleaning and standardization processes (fully re-runnable; the [source README](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Presidential_Apologies) records the exact pipeline):
   * **XML Cleaning**: Punctuation was standardized and unicode characters were flattened to merge diacritics with their base characters. Chinese translations use the canonical full-width double quote (`＂`); HTML escape codes were replaced with the corresponding characters.
   * **Standard tier**: Every original `FORM` gets a `kindOf="standard"` copy (the source texts already use the standard orthography), per the [XML schema](../formosanbank-xml-format.md#the-less-than-form-greater-than-element).
   * **Mandarin annotations**: The Tsou and Kavalan translations gloss many terms with a Mandarin parenthetical (e.g. `zipun( 日 本 )`). These annotations are kept on the original tier but removed from the standard tier and masked out of the IPA, since they are not part of the utterance. Bare in-line Mandarin terms (code-switched utterance content, e.g. Tsou `'e 行政院 ho`) are kept in both tiers.
   * **IPA (`PHON`) tiers**: Generated from the Ortho113 orthography tables using each file's declared dialect column (Amis: Xiuguluan, Bunun: Junqun, Puyuma: Nanwang, ...). A letter the declared dialect's orthography does not use — mostly in Mandarin/Japanese loanwords — surfaces as `*` in the IPA rather than borrowing a pronunciation from another dialect (see Corpus Notes).
4. **Output Organization**\
   The processed XML files were stored in the `XML` directory, each named after its corresponding Formosan language. The files were formatted to ensure readability and ease of analysis.

***

### **Corpus Notes**

* **Amis**: The presidential apology in Amis has a couple of occurances of the letter 'b' which isn't part of the standard orthography of the language. all the occurances can be found in two words: Balay and Sbalay. Both of these words are Atayal words that are quoted in the original apology, and they were used in the same form in the Amis translation. This is an example from the English translation: "In the Atayal language, truth is called 'Balay', and reconciliation is called 'Sbalay'"
* **Kanakanavu**: This corpus uses a small number of h's and f's, which are controversial. None of the words involving h's or f's appear in the reference ILRDF Dictionary corpus, with or without the h's and f's. Thus, we have chosen to leave them in.
* **Puyuma**: This corpus has a number of appearances of ē. Almost all of these are due to yēncumin (which is marked as a foreign word) and sēhu. Thus, this has not been homogenized.
* **Sakizaya**: A small number of f's appear to be foreign words.
* **Starred IPA**: Letters outside the declared dialect's orthography — the Amis 'b' and Puyuma ē/loanword letters above, and bare Mandarin terms — appear as `*` in the `PHON` tiers. This is intentional: `*` marks a letter the dialect's orthography tables cannot transcribe.

***

### **Significance of the Apology Corpus**

1. **Preserving Indigenous Languages**\
   Translating the apology into these languages ensures that it remains accessible to all indigenous groups, contributing to the preservation and revitalization of their languages.
2. **Uniform Text for Linguistic Comparison**\
   Having the same text available across multiple languages provides a unique opportunity to study and compare linguistic structures, vocabulary, and syntax across Formosan languages.
3. **Cultural and Linguistic Identity**\
   This corpus demonstrates the importance of indigenous languages in addressing historical events and acknowledging their role in Taiwan's cultural heritage.

This corpus represents a critical step in preserving linguistic diversity and making significant historical events accessible in the native languages of Taiwan’s indigenous communities.

***

### **Access Details**

* The Office of the President provides the [official English apology](https://english.president.gov.tw/NEWS/4950), and the Council of Indigenous Peoples provides the [16 Formosan-language versions](https://www.cip.gov.tw/zh-tw/news/data-list/01F6453A792735EC/index.html?cumid=01F6453A792735EC).
* The corpus XML and retained processing code are available [in FormosanBank](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Presidential_Apologies).

***

### **Copyright**

According to [Copyright rules by territory/Taiwan](https://commons.wikimedia.org/wiki/Commons:Copyright_rules_by_territory/Taiwan), transcriptions of presidential speeches are not copyrighted as they are listed under public domain.

> ### Not protected <a href="#not_protected" id="not_protected"></a>
>
> See also: [Commons:Unprotected works](https://commons.wikimedia.org/wiki/Commons:Unprotected_works)
>
> According to the _Copyright Act as amended on 15 June 2022_, The following items shall not be the subject matter of copyright, to which [\{{PD-ROC-exempt\}}](https://commons.wikimedia.org/wiki/Template:PD-ROC-exempt) applied:\[2022 Art.9]
>
> 1. The constitution, acts, regulations, or official documents.
> 2. Translations or compilations by central or local government agencies of works referred to in the preceding subparagraph.
> 3. Slogans and common symbols, terms, formulas, numerical charts, forms, notebooks, or almanacs.
> 4. Oral and literary works for news reports that are intended strictly to communicate facts.
> 5. Test questions and alternative test questions from all kinds of examinations held pursuant to acts or regulations.
>
> The term "official documents" in the first subparagraph of the preceding paragraph includes proclamations, text of speeches, news releases, and other documents prepared by civil servants in the course of carrying out their duties.\[2022 Art.9]

***

### Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* **Citing the apology in general**: Tsai, I. W. (2016, August 1). _President Tsai Ing-wen's apology to the Indigenous Peoples on behalf of the government_ \[Speech transcript]. [Office of the President](https://english.president.gov.tw/NEWS/4950).
* **Language specific**: Tsai, I. W. (2016, August 1). _President Tsai Ing-wen's apology to the Indigenous Peoples on behalf of the government_ \[Speech transcript, Amis translation]. [Council of Indigenous Peoples](https://www.cip.gov.tw/zh-tw/news/data-list/01F6453A792735EC/index.html?cumid=01F6453A792735EC).
