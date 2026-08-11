# 100 Paiwan Texts

### **Overview**

[The 100 Paiwan Texts](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/HundredPaiwanStories) corpus contains 100 morphologically parsed and glossed texts from Early and Whitehorn (2003).


<!-- CORPUS STATS START -->
### Corpus Statistics

| | Paiwan<br>Central | Paiwan<br>Eastern | Paiwan<br>Northern | Paiwan<br>Southern | Paiwan<br>unknown |
| --- | --- | --- | --- | --- | --- |
| Word count | 3,714 | 1,198 | 9,017 | 9,444 | 1,105 |
| Total audio | 0 | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 | 0 | 0 | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 | 0 | 0 | 0 | 0 |
| Translated words |  |  |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 3,714 | 1,198 | 9,017 | 9,444 | 1,105 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 0 | 0 | 0 | 0 | 0 |
| Morphologically segmented | 3,714 | 1,198 | 9,017 | 9,444 | 1,105 |
| Glossed words | 3,714 | 1,198 | 9,017 | 9,444 | 1,105 |

***

<!-- CORPUS STATS END -->

### **Corpus Processing**

This corpus was originally published as a book. Prof. Early graciously provided the original Word document, which we scraped. The initial conversion involved the following steps:

1. The free translation was not always on its own line in the docx file. This was fixed manually, the result being `Paiwan Ch2.docx`. 

2. The scripts in the Jupyter notebook `script.ipynb` was then used to create the XMLs.

3. The character encodings from the original Word document did not transfer correctly, and no automatic solution was found. These were fixed using regular expressions (probably; unfortunately, the exact process was not recorded).

4. The following lines were fixed by hand, following the authors' errata notes:

story 061, sentence 034<br>
story 062, sentence 022<br>
story 071, sentence 064<br>
story 072, sentence 045<br>
story 074, sentence 070<br>
story 075, sentence 075<br>
story 095, sentence 008<br>
story 096, sentence 049<br>
story 097, sentence 022<br>

5. The FormosanBank cleaning and orthography tools were run. This normalized punctuation and created a standard orthography tier.

6. Because the original used a slightly different orthography than the modern orthography, the local script `convert.py` was used to convert the orthography to the standard. A table showing the conversion of the original orthography to IPA is available in the book itself. We used a similar conversion table provided by ILRDF for the standard modern orthography we are using. Note that Early and Whitehorn describe a few of the phonemes slightly differently from ILRDF, perhaps reflecting dialectal differences.

The published corpus has since received additional repairs (language tags for morpheme glosses, infix and reduplication segmentation, duplicate ID fixes, and several hand-corrected word and morpheme alignment errors) and was fully regenerated in August 2026 with FormosanBank's current cleaning, standardization, and phonology tools. Highlights of the regenerated version:

* The PHON tiers contain IPA only: punctuation and morpheme-segmentation hyphens are excluded, and the orthography-to-IPA conversion no longer re-maps its own output (e.g. standard `tj` is now consistently IPA `c`).
* In the source orthography the character `?` is both the glottal-stop letter and question-mark punctuation, and `'` appears only as a nested quotation mark. A corpus-specific step (`fix_ferrell.py`) disambiguates every occurrence from context — the English translation's question marks, quote adjacency, sentence position, and corpus-wide attestation — so question marks are restored on the standard tier and no spurious glottal stops appear in the IPA. The source's `word(?)` uncertainty annotations are likewise treated as punctuation, not glottals.
* All four texts whose dialect is unknown (`090`, `091`, `097`, `099`) now carry complete phonological tiers (see Corpus Notes).

The [source README](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/HundredPaiwanStories) records the exact current pipeline, which can be re-run end-to-end, and the manual corrections.

### **Corpus Notes**

The published PDF remains the reference for checking the XML. IPA in four texts whose dialect is currently unknown (`090`, `091`, `097`, and `099`) was generated with the default mapping and is provisional. Please report any errors to the FormosanBank maintainers.

### **Access Details**

Users of this corpus are encouraged to obtain a copy of the original text. A PDF is currently available for [free from the Australian National University](https://openresearch-repository.anu.edu.au/server/api/core/bitstreams/5f377c02-9051-40b3-b839-7108229b3f84/content). This book has extensive information about the texts and the language, including a sketch grammar. 

### **Citation**

Early, R. J., and Whitehorn, J. (2003). One hundred Paiwan texts. Pacific Linguistics, Research School of Pacific and Asian Studies, The Australian National University.

The corpus README states that the corpus is available CC BY-NC with permission from R. J. Early. The current XML files are labeled public domain. Until those notices are reconciled, users should follow the stricter CC BY-NC terms. The text itself is also freely available online from several sources.
