# Presidential Apologies

### **Overview**

On **August 1, 2016**, President Tsai Ing-wen delivered a historic apology to Taiwan's indigenous peoples on behalf of the government during **Indigenous Peoples' Day**. The apology addressed the pain and mistreatment endured by indigenous communities over four centuries and marked the establishment of the **Presidential Office Indigenous Historical Justice and Transitional Justice Committee (Indigenous Justice Committee)**.&#x20;

This apology text, as part of the effort to promote **historical justice**, has been translated into the 16 officially recognized Formosan languages: **Amis**, **Atayal**, **Saisiyat**, **Thao**, **Seediq**, **Bunun**, **Paiwan**, **Rukai**, **Truku**, **Kavalan**, **Tsou**, **Kanakanavu**, **Saaroa**, **Puyuma**, **Yami**, and **Sakizaya**. The translated apology are the main text forming this corpus described here. This corpus consists exclusively of **text data.** The apology text is also available in **English** and **Chinese**.

***

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
   Once the XML files were created, they underwent multiple cleaning and standardization processes, as outlined below:
   * **XML Cleaning**: Punctuation was standardized and unicode characters were flattened to merge diacritics with their base characters.
   * **Orthography Standardization**: A secondary pass added standardized versions of Formosan text while retaining the original versions. This ensured consistency, such as converting all "u" to "o" where applicable.
   * **Final Adjustments**: HTML escape codes were replaced with corresponding characters, and attributes like `kindOf="original"` and `kindOf="standard"` were added to ensure compliance with the [XML schema.](../formosanbank-xml-format.md#the-less-than-form-greater-than-element)
4. **Output Organization**\
   The processed XML files were stored in the `XML` directory, each named after its corresponding Formosan language. The files were formatted to ensure readability and ease of analysis.

***

### **Corpus Notes**

This section will be used to describe any notes regarding the corpus (e.g. explaining the presence of characters that aren't part of the standard orthography)

* **Amis**: The presidential apology in Amis has a couple of occurances of the letter 'b' which isn't part of the standard orthography of the language. all the occurances can be found in two words: Balay and Sbalay. Both of these words are Atayal words that are quoted in the original apology, and they were used in the same form in the Amis translation. This is an example from the English translation: "In the Atayal language, truth is called 'Balay', and reconciliation is called 'Sbalay'"
* **Kanakanavu**: This corpus uses a small number of h's and f's, which are controversial. None of the words involving h's or f's appear in the reference ILRDF Dictionary corpus, with or without the h's and f's. Thus, we have chosen to leave them in.
* **Puyuma**: This corpus has a number of appearances of ē. Almost all of these are due to yēncumin (which is marked as a foreign word) and sēhu. Thus, this has not been homogenized.
* **Sakizaya**: A small number of f's appear to be foreign words.

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

* Information about the apology, the apology text in English and Chinese as well as the 16 Formosan languages are all publicly available [here](https://indigenous-justice.president.gov.tw/).
* The repo containing the ePark corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Presidential_Apologies).

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

In accordance with our [Terms of Use](../../additional-resources/tja-kipapawlingaven-a-cekaw-tua-ziriu-imaza.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* **Citing the apology in general**: Tsai, I. W. (2016, August 1). _President Tsai Ing-wen's apology to the Indigenous Peoples on behalf of the government_ \[Speech transcript]. [https://indigenous-justice.president.gov.tw/](https://indigenous-justice.president.gov.tw/)
* **Language specific**: Tsai, I. W. (2016, August 1). _President Tsai Ing-wen's apology to the Indigenous Peoples on behalf of the government_ \[Speech transcript, Amis translation]. [https://indigenous-justice.president.gov.tw/](https://indigenous-justice.president.gov.tw/)
