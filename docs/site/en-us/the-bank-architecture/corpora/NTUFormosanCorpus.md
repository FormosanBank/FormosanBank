# NTU Corpus of Formosan Languages

[The NTU Corpus of Formosan Languages](https://corpus.linguistics.ntu.edu.tw/#/) is the first large open corpus of Formosan languages. The NTU Corpus is a comprehensive and meticulously curated dataset representing 10 Indigenous Formosan languages: Kanakanavu, Rukai, Saisiyat, Tsou, Kavalan, Amis, Seediq, Atayal, Sakizaya, and Bunun. This corpus includes texts, audio recordings, elicited sentences, and example sentences from various sources such as grammar books and narrative collections. Designed to support linguistic research and revitalization efforts, the NTU Corpus provides a unique window into the diversity and complexity of Formosan languages.

It consists of three main sections:

* Grammar (examples derived from grammar textbooks)

* Sentences (individual sentences recorded during fieldwork and transcribed and glossed).

* Stories (narratives recorded during fieldwork and transcribed and glossed.)

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Amis<br>Coastal | Bunun<br>Junqun | Kavalan | Rukai<br>Wutai | Sakizaya | Atayal<br>Wenshui | Seediq<br>Tegudaya | Tsou | Kanakanavu | Saisiyat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Word count | 7,531 | 23,486 | 16,290 | 17,978 | 14,038 | 5,864 | 25,298 | 10,206 | 20,354 | 10,853 |
| Total audio | 1.2h | 1.6h | 2.9h | 1.6h | 2.3h | 1.1h | 3.3h | 1.0h | 4.0h | 1.8h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 1.2h | 1.6h | 2.9h | 1.6h | 2.3h | 1.1h | 3.3h | 1.0h | 4.0h | 1.8h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Translated words |  |  |  |  |  |  |  |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 7,486 | 23,404 | 16,225 | 17,963 | 8,993 | 5,859 | 20,369 | 10,206 | 15,169 | 10,837 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 7,531 | 23,396 | 16,288 | 17,961 | 14,036 | 5,859 | 25,298 | 10,206 | 20,334 | 10,837 |
| Morphologically segmented | 7,528 | 23,463 | 16,286 | 17,292 | 12,968 | 5,861 | 22,803 | 10,200 | 18,854 | 10,849 |
| Glossed words | 7,528 | 23,463 | 16,286 | 17,292 | 12,968 | 5,861 | 22,803 | 10,195 | 18,847 | 10,848 |

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

* The corpus is fully regenerable from the archived source data. The JSONs under `CodeAndDocs/{grammar,sentence,story}` are the source — nothing is scraped, so there is no refresh step — and `CodeAndDocs/pipeline/build.sh` takes them to the published XML: a per-subcorpus builder, a chain of repair scripts, then tier construction (alternate readings, morpheme pruning, id alignment, and the standard and phonemic tiers against Ortho94). Each subcorpus is built from scratch in a temporary directory and installed only on success, so a rebuild reproduces the same bytes. `CodeAndDocs/make.sh` wraps that build with the source-coverage audit, re-application of recorded hand edits, validation and a regression check against the recorded QA baseline. The one-off hand-verified corrections are stored as data tables rather than in code, so they survive regeneration. The source JSONs used are the ones this corpus has always published; an alternative revision of 207 of them exists on a feature branch but is not produced by any script in the repository, so it is neither auditable nor reproducible and is not used. Step-by-step documentation is in [CodeAndDocs/pipeline/README.md](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/NTUFormosanCorpus/CodeAndDocs/pipeline/README.md) and the corpus [README](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/NTUFormosanCorpus/readme.md).

***

## Notes

### Major issues, user beware

* It is known that the audio does not always match the text. It is not clear how common this is. A list of audio clips that are suspiciously long or short given how many words in the utterance can be found in [audio_duration_issues.csv](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/NTUFormosanCorpus/audio_duration_issues.csv)

* There are sentences (current list: 54) where the glosses are clearly wrong. Most, but not all, of these cases involve a missing gloss, resulting in glosses being out of sync with the words. See [sentences_with_bad_glosses_removed.csv](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/NTUFormosanCorpus/sentences_with_bad_glosses_removed.csv).

* At the time the NTU Formosan Corpus was created, there were no clear conventions as to whether to write a clitic as a stand-alone word. However, the glosses almost always treat the clitic as attached to another word. This results in sometimes two words corresponding to a single W element. A list of such cases is found in [clitics.csv](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/NTUFormosanCorpus/clitics.csv) (currently 819 cases).

* There are some translated but unglossed wordlists. These lack W elements on account of not having any segmentation or glossing.

* Even after accounting for the two issues above, the number of W elements does not always match the number of words in the sentence. These cases are listed in [validation_results.csv](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/NTUFormosanCorpus/validation_results.csv) (current count: 361).

* There are a number of cases where, in the glosses, the wordform and syntactic glosses differ in the number of segments. Many of these cases appear to be due to failing to segment the wordform. Others may be due to the wordforms and syntactic glosses being out of alignment. Known examples are recorded in [validation_m_mismatches.csv](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/NTUFormosanCorpus/validation_m_mismatches.csv) (current count: 1,476).

* The original data often contains transcriber notes or translation notes inline, in parentheses. These are removed from the text and preserved in a `notes` attribute: commentary inside a free translation goes to `TRANSL/@notes` (5,911 sentences), and commentary in the sentence text itself goes to `FORM/@notes` (5,542 sentences, plus 1,298 at the word level). Every parenthetical span is extracted, whether the source wrote ASCII `(...)` or fullwidth `（...）` and wherever in the string it sits; the `notes` attribute holds the source string as written, so nothing is lost. Word- and morpheme-level glosses are left exactly as the source wrote them, since those are glosses rather than commentary. A small residue survives: 28 free translations still carry a parenthetical inline (23 of them with no `notes` attribute, so those are not recorded anywhere else), and 16 have unbalanced parentheses that cannot be resolved automatically. The online version of the NTU Formosan Corpus is meant to be read by a human and remains the better place to browse the annotations: the `id` of the XML file (check the `TEXT` header element) tells you what the file is there, and the `id` of the `S` element tells you which line.

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

* The Kanakanavu sentence subcorpus writes "∅" inside some words (31 occurrences), and the Sakizaya grammar writes a null prefix slot "ø". These are the linguists' null-morpheme annotation: a morpheme that is present in the analysis but has no phonological content (e.g. a phonologically empty relativizer, glossed REL). FormosanBank's convention (per the 2026-08 null-morpheme specification) canonicalizes the marker glyph to `∅` (U+2205) and keeps it in the original tier and on the word/morpheme tiers — where the morphological analysis lives — while removing it from sentence-level standard FORMs; in the PHON tier null morphemes are silent (a wholly-null morpheme carries PHON `∅` so the tier is never empty). The currently published XML predates parts of this convention (e.g. Sakizaya still shows `ø`); it is applied fully at the next regeneration. See the corpus [README](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/NTUFormosanCorpus/readme.md) for details.

***

## Orthography

The NTU source is written in **Ortho94**, the orthography released in ROC year 94 which Ortho113 later revised. The corpus is processed as Ortho94 throughout: the original phonemic tier is generated from Ortho94's letter-to-sound rules, and the standard tier is produced by converting 94 → 113 per language, since Ortho113 is FormosanBank's common orthography.

This is a change from earlier processing, which declared the original tier to be Ortho113 and produced the standard tier by stripping accents without any letter conversion — describing the source as an orthography it was not written in.

Three of the corpus's ten languages carry an empty conversion table. Bunun and Tsou need no letter conversion, their Ortho94 and Ortho113 spellings agreeing; Kanakanavu genuinely differs but cannot be converted in this direction, because Ortho113 introduced letters Ortho94 did not have. Accents are removed and capital variants derived in all cases regardless.

***

## Quality checks

FormosanBank's validators decide whether a corpus's XML is *legal*. This corpus additionally carries a suite that measures how well it holds together as a **glossed** corpus — whether the word tier accounts for the sentence, whether every morpheme a word's form implies actually has a morpheme element, and whether the glosses sit in the right language slots. A file can be perfectly valid and still score poorly on these.

Almost none of those tests can honestly reach 100%: the source contains sentences nobody segmented and words nobody glossed, and suppressing that fact would be worse than reporting it. So the recorded score is the specification — a baseline file holds what each test achieves on the corpus as published, and any rebuild is compared against it, with drops reported as regressions and rises reported so the baseline can be moved deliberately.

The suite and its baseline live in the corpus's `CodeAndDocs/qa/` directory in the [FormosanBank repository](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/NTUFormosanCorpus/CodeAndDocs/qa).

***

## Copyright

CC BY-NC

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Sung, L. M., Lily, I., Hsieh, F., &amp; Lin, Z. (2008). Developing an online corpus of Formosan languages. Taiwan Journal of Linguistics, 6(2).
