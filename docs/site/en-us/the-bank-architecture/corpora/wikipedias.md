# Wikipedias

### **Overview**

The **Formosan Wikipedias Corpus** is a collection of articles sourced from publicly available Formosan-language Wikipedias.ِ **Amis**, **Atayal**, **Sakizaya**, **Seediq**, and **Paiwan** have their own dedicated Wikipedia editions, making them publicly accessible for research and education. These articles provide a unique opportunity to document and analyze the linguistic characteristics of these languages in a contemporary, digital context. Even though the Wikipedias corpus doesn't have audio or translations associated with it, it still is highly valuable for computational and linguistic applications.

After scraping the articles, they have been preprocessed to remove elements like URLs, extraneous punctuation, and irrelevant text that is not relevant to the linguistic structure of Formosan while preserving linguistic integrity. Similar to the rest of the corpora in FormosanBank, the dataset is formatted in XML for easy use in computational applications.

***

<!-- CORPUS STATS START -->
### Corpus Statistics

| | Amis<br>unknown | Paiwan<br>unknown | Sakizaya | Atayal<br>unknown | Seediq<br>unknown |
| --- | --- | --- | --- | --- | --- |
| Word count | 850,500 | 116,685 | 1,567,968 | 529,757 | 736,080 |
| Total audio | 0 | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 | 0 | 0 | 0 | 0 |
| Translated words |  |  |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 0 | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 0 | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 | 0 | 0 | 0 | 0 |
| Morphologically segmented | 0 | 0 | 0 | 0 | 0 |
| Glossed words | 0 | 0 | 0 | 0 | 0 |

***

<!-- CORPUS STATS END -->


### The published corpus

The corpus has 12,748 articles, one XML file each: 1,892 Amis, 2,935 Atayal, 455 Paiwan, 5,498 Sakizaya and 1,968 Seediq. It is not re-scraped, because the live wikis have changed since the June 2026 scrape. Instead, `CodeAndDocs/generate_xml.sh` rebuilds `XML/` from that scrape, preserved in `CodeAndDocs/pre_correction_snapshot/` (13,278 files), plus the recorded corrections ([corpus README](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Wikipedias/README.md)). On the way it:

* drops 29 articles the scrape saved twice under the same id (`<name> (1).xml`; the copies were identical) and 11 articles with no Latin letter at all;
* sets `dialect="unknown"` on every article, because no Wikipedia article identifies its dialect;
* restores Seediq text that the historical citation cutter removed: 25 articles get their cut-off body text back (28 source sections) and 5 get their author credit back, in the FORM `notes` attribute. Each is listed, with the source revision it was read from, in [`citation_restorations.csv`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Wikipedias/CodeAndDocs/citation_restorations.csv);
* withdraws 490 articles that the scrape downloaded a second time under a title that redirects to them (108 Amis, 81 Atayal, 17 Paiwan, 194 Sakizaya, 90 Seediq; e.g. `Amis/Abraham_Lincoln.xml` was the article `Aparaham Linken`). No text is lost: each copy's text is published, character for character, under the article it redirects to. The withdrawn ids are listed in [`old_to_new_ids.csv`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Wikipedias/CodeAndDocs/old_to_new_ids.csv) and [`source_redirects.csv`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Wikipedias/CodeAndDocs/source_redirects.csv). Token counts fell by 1,311,509, because those copies had been counted twice; most of the Amis drop is one article, `Amis/Amilika.xml` ("America"), which 50 redirect titles led to;
* builds the standard tier as a copy of the original with accents removed (no spelling conversion, since the dialect is unknown), and PHON from the Ortho113 tables (see below).

### Processing and Quality Control (the original 2026-06 scrape)

The steps in this section describe how the June 2026 scrape was made and cleaned. They are kept for provenance and are not re-run.

The **Formosan Wikipedias Corpus** was created by sourcing articles from publicly available Formosan-language Wikipedias, Amis, Atayal, Sakizaya, Seediq, and Paiwan. Considering that the quality control pipeline of Wikipedias isn't as rigorous as other resources in the Bank, extra effort went into processing, cleaning, and QCing the Wikipedias articles. Below, we outline the detailed processing steps and quality control measures applied to ensure the corpus is both reliable and linguistically accurate.

***

### **Processing Steps**

1. **Scraping Wikipedia Articles**
   * Articles were retrieved using the Wikipedia API for each language.
   * Titles of available articles were collected and stored in the `Titles` directory as pickle files for each language.
   * Using these titles, the articles were downloaded, saved as text files, and stored in the `Articles` directory.
   * Articles were initially saved in their raw, unprocessed format.
2. **Preprocessing and Cleaning**
   * Articles were cleaned to remove URLs, extraneous punctuation, and citation markers. Irrelevant content (e.g., non-Formosan text) was also removed.
   * The following logs were generated for quality assurance:
     * [**`link_removal.log`**](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Wikipedias/CodeAndDocs/link_removal.log): Lists URLs removed from the text.
     * [**`citations_remove.log`**](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Wikipedias/CodeAndDocs/citations_remove.log): Tracks removed citation sections.
     * [**`remove_possible_citations.log`**](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Wikipedias/CodeAndDocs/remove_possible_citations.log): Records sequence numbers and periods (common citation markers) that were removed.
     * [**`encoding_detection.log`**](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Wikipedias/CodeAndDocs/encoding_detection.log): Notes encoding issues and fixes for articles.
     * [**`citation_marker_removal.log`**](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Wikipedias/CodeAndDocs/citation_marker_removal.log): Tracks citation markers removed from within the text.
3. **Removing Non-Formosan Text**
   * Text in non-Formosan languages, such as English, Chinese, or other non-Latin scripts, was identified and removed.
   * Specific logs were generated for this step:
     * [**`remove_Annotations.log`**](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Wikipedias/CodeAndDocs/remove_Annotations.log): Tracks removal of non-Formosan commentary in parentheses.
     * [**`remove_large_blocks.log`**](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Wikipedias/CodeAndDocs/remove_large_blocks.log): Logs large non-Latin text blocks removed.
     * [**`remove_character_strings.log`**](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Wikipedias/CodeAndDocs/remove_character_strings.log): Notes removal of continuous segments of non-Latin text.
     * [**`remove_empty_parentheses.log`**](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Wikipedias/CodeAndDocs/remove_empty_parentheses.log): Tracks removal of empty parentheses.
4. **XML Structuring**
   * The cleaned articles were converted into the FormosanBank XML format, where each article was structured with a `<FORM>` element for the main text.
   * Metadata, including the article title and language code, was added to the XML files for organizational purposes.
   * These XML files were saved in the `XML` directory for further analysis and applications.
5. **Standardization and Punctuation Cleaning**
   * HTML escape codes were replaced with the corresponding characters, and a `kindOf="standard"` attribute was added to `<FORM>` elements. The original text would be `<FORM kindOf="original">`  and any text that will be standardized from this point will be in `<FORM kindOf="standard">`
   * XML files underwent additional cleaning to remove empty elements, standardize orthography, and merge Unicode diacritics with their base characters.

***

### **Quality Control**

In addition to the thorough work done during processing to ensure the resulting corpus is of high quality, further QC steps were conducted to validate and enhance the dataset's reliability and usability. Some of these QC steps are listed below:

1. **Cross-Linguistic Character Frequency Analysis**
   * A character frequency comparison was conducted between the Formosan Wikipedias and the [ILRDF corpus](ilrdf-dictionaries.md) (Indigenous Languages Research and Development Foundation). This ensures that expected Formosan characters dominate and non-Formosan characters (e.g., English characters used incidentally) appear at low frequencies.
   *   Below are the character-frequency graphs for the 5 languages compared to the ILRDF corpus:

{% tabs %}
{% tab title="Amis" %}
<figure><img src="../../.gitbook/assets/Amis_frequency_comparison.png" alt=""><figcaption></figcaption></figure>
{% endtab %}

{% tab title="Atayal" %}
<figure><img src="../../.gitbook/assets/Atayal_frequency_comparison.png" alt=""><figcaption></figcaption></figure>
{% endtab %}

{% tab title="Paiwan" %}
<figure><img src="../../.gitbook/assets/Paiwan_frequency_comparison.png" alt=""><figcaption></figcaption></figure>
{% endtab %}

{% tab title="Sakizaya" %}
<figure><img src="../../.gitbook/assets/Sakizaya_frequency_comparison.png" alt=""><figcaption></figcaption></figure>
{% endtab %}

{% tab title="Seediq" %}
<figure><img src="../../.gitbook/assets/Seediq_frequency_comparison.png" alt=""><figcaption></figcaption></figure>
{% endtab %}
{% endtabs %}

2. **Annotation Verification**
   * Logs of removed annotations and non-Formosan text were reviewed to ensure edits were appropriate and did not inadvertently remove valuable linguistic data. Cases flagged for ambiguity were manually resolved.
3. **Consistency Checks on XML Structure**
   * The XML files were subjected to automated checks to ensure compliance with the FormosanBank schema. This included verifying the presence of required attributes (e.g., `kindOf="original"` and `kindOf="standard"`) and the absence of empty or malformed elements.
4. **Manual Spot Checks**
   * Random samples of the XML files were manually inspected to confirm proper segmentation, alignment, and the integrity of the linguistic content. These checks ensured the processed corpus accurately reflected the original articles' linguistic structures.

***

### **Processing Notes**

* Given the multilingual nature of Wikipedia articles, users should note the presence of occasional non-Formosan text (e.g., English characters or Chinese text). While these have been minimized, they may still appear at low frequencies.
* Every article records `dialect="unknown"`, because Wikipedia articles do not identify a dialect. The Seediq articles (`xml:lang="trv"`) therefore count as Seediq, not Truku.

***

### **Applications**

Although the data doesn't have associated audio or translations, it still can be relavant to a number of practical applications:

* The corpus provides authentic text data for training models in **natural language processing (NLP)** tasks, such as language modeling and text classification, .
* Useful for developing tools like spell checkers and predictive text.
* Could be used for building surprisal and preplexity models, which would facilitate Quality Assurance of further collected data
* A stepping stone for creating digital resources and applications, such as dictionaries, and grammar-check tools, tailored to these languages.

***

### **Limitations**

Please beware that due to the nature of the wikipedias corpus (being collected from public online article and heavily containing non-Formosan text), there are some limitations in the corpus that should be pointed out.

* The standard tier (`<FORM kindOf="standard">`) is a copy of the original with accents removed. It does not convert spelling, so any English or other non-Formosan words are left as they are.
* The historical citation cutter sometimes stopped at an early reference heading and removed the article text after it. The 30 Seediq cases identified so far are repaired (see "The published corpus" above), including Nakahara, Kobah, Pratan and Bubun (body text) and Smangus (author credit). `Tausa`, which this page used to list as an example, is not among the 30. Other articles cut the same way, if any, have not been looked for.

***

### The orthography behind `PHON`

**Short version.** The `PHON` tiers in this corpus are generated by mapping each letter of the `FORM` text to IPA through **one** orthography table — `Ortho113`, dialect-agnostic column — for all five languages and all articles. (The figures in this section were computed on the 13,238 articles published before the 490 redirect copies were withdrawn on 2026-10-18, and were not recomputed.) Wikipedia articles do not state which orthography their author used, so this is an assumption, not a fact recovered from the source. This section gives the evidence for it and the size of the residual error, so you can decide whether `PHON` is usable for your purpose.

If you need phonemic precision, treat `PHON` here as a **broad, deliberately under-specified** transcription and go back to `FORM`. If you need a rough phone inventory, a searchable phonemic index, or a segment-level baseline, `PHON` is sound to within the error described below.

#### What the evidence says

FormosanBank's orthography detector scores a text's letter inventory against every reference orthography table available for its language. Run over this corpus, combined per language (original tier):

| language | top-scoring table | score | where Ortho113 lands |
| --- | --- | --- | --- |
| Amis | Ortho94 (all five dialect columns tie) | 88.4% | below the top 7 |
| Atayal | Church (Sekolik) / Ortho94 (Sekolik), tied | 86.1% | 5th, 84.3% |
| Paiwan | **Ortho113** (four dialect columns tie) | 82.1% | 1st |
| Sakizaya | **Ortho113** | 73.2% | 1st (Ortho94 2nd, 65.0%) |
| Seediq | **Ortho113** | 87.9% | 1st (Ortho94 4th, 87.9%) |

So Ortho113 is the best-supported table for Paiwan, Sakizaya and Seediq. For Amis and Atayal another table scores higher — and the reason is *not* that those wikis spell differently; see "Where the tables disagree" below.

#### Is the orthography uniform across articles?

Effectively yes, as far as anything measurable shows. All 13,238 articles were also scored individually:

| language | articles | best = Ortho113 | median score gap to the per-article winner |
| --- | --- | --- | --- |
| Amis | 2,000 | 225 (11.2%) | 0.018 |
| Atayal | 3,016 | 292 (9.7%) | 0.018 |
| Paiwan | 472 | 157 (33.3%) | 0.012 |
| Sakizaya | 5,692 | 5,209 (91.5%) | 0.000 |
| Seediq | 2,058 | 824 (40.0%) | 0.002 |

The per-article "winner" flips constantly, but the margins are within noise (median gaps 0.000–0.018 on a 0–1 scale). The detector scores *inventory coverage*, so a short article that happens not to use one letter of a larger inventory hands the win to the smaller table. **These flips are scoring noise, not evidence that different articles follow different spelling conventions.** Nothing in the data supports phonologizing article by article, which is why a single table is applied corpus-wide.

#### Where the tables disagree — and why it mostly costs ambiguity, not accuracy

For nearly every letter where Ortho113 and a rival table differ, Ortho113's value is a **variant group** rather than a competing single value: it records "this letter is `o` *or* `u`" where Ortho94 commits to one. Those disagreements therefore surface in `PHON` as explicit `[x|y]` groups you can see and handle, not as silently wrong segments:

| language | PHON tokens containing a `[x\|y]` group | commonest groups |
| --- | --- | --- |
| Amis | 51.4% | `[o\|u]`, `[ɬ\|ɮ]`, `[b\|v]` |
| Atayal | 24.8% | `[s\|ɕ]`, `[ʦ\|ʨ]` |
| Sakizaya | 19.0% | `[r\|ɾ]`, `[ʔ\|ʡ]` |
| Paiwan | 0% | — |
| Seediq | 0% | — |

Genuinely *conflicting* single values — where Ortho113 commits to one IPA value and a plausible rival table commits to a different one — are few and enumerable:

| language | letter | Ortho113 | rival | occurrences |
| --- | --- | --- | --- | --- |
| Atayal | `e` | `e` | Church `ə` | 35,336 |
| Seediq | `j` | `ɟ` | Church (Tegudaya) `ɖʐ` | 18,777 |
| Sakizaya | `f` | `f` | Ortho94 `b` | 6,507 |
| Paiwan | `o` | `u` | (not listed by Ortho94/Church) | 2,031 |

Together these are **under 0.4% of the corpus's letter occurrences**. The largest single item is Atayal `e`: Church, the corpus-wide top-scoring table for Atayal, reads it as `ə` where this corpus writes `e`, 35,336 times. If you work on Atayal vowels, that is the one substitution to apply yourself.

#### Unmapped characters (`*`)

Any character with no IPA value in the table is written as `*` in `PHON`:

| language | `*` share of PHON characters | of the characters producing a `*`: digits |
| --- | --- | --- |
| Amis | 1.39% | 89.3% |
| Atayal | 2.17% | 68.8% |
| Paiwan | 2.57% | 50.3% |
| Sakizaya | 2.28% | 60.4% |
| Seediq | 2.80% | 85.6% |

**None of this is attributable to Ortho113.** Between 50% and 89% of the stars come from digits (dates, population figures, footnote numbers); most of the rest are CJK quotations and loanword letters (`f`, `v`, `g`, `q`, `z`, `x`, `J`, `R`) that no Formosan orthography table maps. Choosing Ortho94 or Church instead would not change them — those tables have the same or smaller letter inventories.

#### Summary for users of `PHON`

* One table (Ortho113, dialect-agnostic) for the whole corpus; the source does not state an orthography, and per-article detection shows no real variation.
* Best-supported table for Paiwan, Sakizaya and Seediq; for Amis and Atayal a rival scores higher because it is *less* cautious, not because the wiki spells differently.
* The dominant cost is **ambiguity**: 19–51% of Amis/Atayal/Sakizaya `PHON` tokens carry a `[x|y]` variant group (0% for Paiwan and Seediq).
* Outright disputable segments are bounded by four letters, under 0.4% of letter occurrences, the largest being Atayal `e` (35,336).
* 1.4–2.8% of `PHON` characters are `*` (no IPA value), mostly digits.

#### Decision

Ortho113 is used corpus-wide, for the reasons set out above. The one material divergence — Atayal `e` (Ortho113 `e` vs Church `ə`, 35,336 occurrences) — is known, quantified above, and accepted as **unadjudicable**: the articles state no orthography and carry no translations, so there is no evidence that could settle which value their authors intended. Users who need `ə` for Atayal should apply that substitution themselves.

***

### **Access Details**

* Blow is a list of the wikipedias available in Formosan languages:
  * Amis: [https://ami.wikipedia.org](https://ami.wikipedia.org/)
  * Atayal: [https://tay.wikipedia.org](https://tay.wikipedia.org)
  * Sakizaya: [https://szy.wikipedia.org](https://szy.wikipedia.org)
  * Seediq: [https://trv.wikipedia.org](https://trv.wikipedia.org)
  * Paiwan: [https://pwn.wikipedia.org](https://pwn.wikipedia.org)
* The corpus XML and retained processing materials are available [in FormosanBank](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Wikipedias).

***

### **Copyright**

According to [Wikipedia:Copyrights](https://en.wikipedia.org/wiki/Wikipedia:Copyrights) page, Wikipedias can be used under the Creative Commons license CC BY-SA. FormosanBank publishes this corpus under **CC BY-SA 4.0** (the `copyright` value of every `TEXT` element).

> Most of Wikipedia's text and many of its images are co-licensed under the [Creative Commons Attribution-ShareAlike 4.0 International License](https://en.wikipedia.org/wiki/Wikipedia:Text_of_the_Creative_Commons_Attribution-ShareAlike_4.0_International_License) (CC BY-SA) and the [GNU Free Documentation License](https://en.wikipedia.org/wiki/Wikipedia:Text_of_the_GNU_Free_Documentation_License) (GFDL) (unversioned, with no invariant sections, front-cover texts, or back-cover texts). Some text has been imported only under CC BY-SA and CC BY-SA-compatible license and cannot be reused under GFDL; such text will be identified on the page footer, in the page history, or on the discussion page of the article that utilizes the text.

***

### Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from it, cite FormosanBank and each Wikipedia language edition used. The current XML records a per-language citation in this form:

* Wikipedia contributors. (2026). *[Language] Wikipedia*. Wikimedia Foundation. Retrieved June 9, 2026, from the corresponding language-edition URL.
