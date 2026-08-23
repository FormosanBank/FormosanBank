# Presidential Apologies

### **Overview**

On **August 1, 2016**, President Tsai Ing-wen delivered a historic apology to Taiwan's indigenous peoples on behalf of the government during **Indigenous Peoples' Day**. The apology addressed the pain and mistreatment endured by indigenous communities over four centuries and marked the establishment of the **Presidential Office Indigenous Historical Justice and Transitional Justice Committee (Indigenous Justice Committee)**.&#x20;

This apology text, as part of the effort to promote **historical justice**, has been translated into the 16 officially recognized Formosan languages: **Amis**, **Atayal**, **Saisiyat**, **Thao**, **Seediq**, **Bunun**, **Paiwan**, **Rukai**, **Truku**, **Kavalan**, **Tsou**, **Kanakanavu**, **Saaroa**, **Puyuma**, **Yami**, and **Sakizaya**. The translated apologies are the main texts forming the corpus described here. This corpus consists exclusively of **text data.** The apology text is also available in **English** and **Chinese**.

The current release contains 16 texts and 524 aligned sentence sections. Every sentence has original and standard Formosan-language tiers, generated IPA tiers, and Mandarin and English translations. The source does not provide word or morpheme analysis, and the corpus has no audio.

***

<!-- CORPUS STATS START -->
### Corpus Statistics

| | Amis<br>Xiuguluan | Bunun<br>Junqun | Kavalan | Rukai<br>Wutai | Paiwan<br>Central | Puyuma<br>Nanwang | Thao | Saaroa | Sakizaya | Yami | Atayal<br>Sekolik | Seediq<br>Tegudaya | Truku | Tsou | Kanakanavu | Saisiyat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Word count | 1,929 | 1,548 | 2,209 | 1,948 | 2,378 | 2,091 | 1,854 | 1,114 | 1,735 | 1,640 | 2,445 | 1,508 | 1,853 | 2,070 | 1,543 | 1,639 |
| Total audio | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Translated words |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 1,929 | 1,548 | 2,209 | 1,948 | 2,378 | 2,091 | 1,854 | 1,114 | 1,735 | 1,640 | 2,445 | 1,508 | 1,853 | 2,070 | 1,543 | 1,639 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 1,929 | 1,548 | 2,209 | 1,948 | 2,378 | 2,091 | 1,854 | 1,114 | 1,735 | 1,640 | 2,445 | 1,508 | 1,853 | 2,070 | 1,543 | 1,639 |
| Morphologically segmented | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Glossed words | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

***

<!-- CORPUS STATS END -->


### **Corpus Processing**

The corpus uses the officially released translations in 16 Formosan languages, Mandarin, and English. Its public build follows these steps:

1. **Source inventory and PDF alignment**\
   The 36-file source manifest records 16 official bilingual PDFs and the corresponding transcript snapshots. Fifteen language texts contain 33 aligned sections; Kanakanavu contains 29. The source audit matches all 524 Formosan-language sections and all 524 Mandarin sections to the PDFs after only documented layout and typography equivalences. English is checked for file integrity, section count, and deterministic XML mapping because it is not printed in the bilingual PDFs.

   <figure><img src="../../.gitbook/assets/Screenshot 2024-12-08 at 9.41.01 PM.png" alt="Example of aligned Formosan-language and Mandarin apology sections"><figcaption>Example of the aligned source layout.</figcaption></figure>
2. **Reviewed source corrections**\
   The rebuild records three source decisions: Kavalan section 6 preserves public word boundaries after two Mandarin annotations; Saaroa section 0 corrects `mualiuhlʉ` to the PDF spelling `mualiuhlu`; and Truku section 25 replaces a semicolon with the apostrophe printed in the PDF. The repeated Saaroa sections 22 and 23 remain because the official PDF prints the same Formosan-language paragraph on both corresponding pages beside different Mandarin sections.
3. **Stable XML generation**\
   A single external mapping records source files, language codes, dialect labels, stable text IDs, and section counts. Generation preserves all 16 published text IDs and all 524 sentence IDs. Each sentence receives Formosan-language `FORM` tiers and Mandarin and English `TRANSL` elements.
4. **Cleaning, standardization, and IPA**\
   The XML is cleaned with the current FormosanBank tooling. The standard `FORM` tier is copied from the cleaned original tier, and both `PHON` tiers are generated from Ortho113 using the declared dialect. CJK-only parenthetical annotations in Tsou and Kavalan remain in the original tier but are removed from the standard tier and masked from IPA. Inline Mandarin content remains on both tiers.
5. **Reproduction and validation**\
   The [public pipeline and QC record](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Presidential_Apologies/CodeAndDocs) pin the FormosanBank tooling authority, rebuild all XML in a temporary directory, repeat the source audit, run the XML, text, gloss, duplicate, and port-readiness validators, and compare the result with the committed corpus. The release reproduces exactly and has no hard validation findings.

***

### **Corpus Notes**

* **Amis**: The presidential apology in Amis has several occurrences of the letter `b`, which is not part of the standard orthography. All occurrences are in the quoted Atayal words `Balay` and `Sbalay`.
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
