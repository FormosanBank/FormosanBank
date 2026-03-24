# NTU Corpus of Formosan Languages


***

## Notes

### Major issues, user beware

* It is known that the audio does not always match the text. It is not clear how common this is. 

* There are sentences (last count, 56) where the glosses are clearly wrong. Most, but not all, of these cases involve a missing gloss, resulting in glosses being out of sync with the words. See `sentences_with_bad_glosses_removed.csv`

* At the time the NTU Formosan Corpus was created, there were no clear conventions as to whether to write a clitic as a stand-alone word. However, the glosses almost always treat the clitic as attached to another word. This results in sometimes two words corresponding to a single W element. A list of such cases is found in `clitics.csv` (currently 819 cases).

* There are some translated but unglossed wordlists. These lack W elements on account of not having any segmentation or glossing.

* Even after accounting for the two issues above, the number of W elements does not always match the number of words in the sentence. These cases are listed in `validation_results.csv` (current count: 366).

* There are a number of cases where, in the glosses, the wordform and syntactic glosses differ in the number of segments. Many of these cases appear to be due to failing to segment the wordform. Others may be due to the wordforms and syntactic glosses being out of alignment. Known examples are recorded in `validation_m_results.csv` (current count: 1,415).

* The original data often contains transcriber notes or translation notes in the text. These have been removed from the text and placed in a `notes` attribute in the corresponding <FORM />. However, such information may not always be included (it was complicated to extract), so users who are interested in the notes and parentheticals should consult the online version of the NTU Formosan Corpus, which is meant to be read by a human. The `id` of the XML file (check the <TEXT> header element) tells you what the file is on NTU Formosan Corpus. The `id` of the <S> element tells you which line in the NTU Formosan Corpus.

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

## Processing

* **1. Parse original files**

```bash
    python scripts/run_parsers.py
```

These scripts do *a lot* of cleaning. The JSONs used in the backend of the NTU Formosan corpus are meant to result in something human-readable, not machine readable.

These scripts produce many error logs and warning logs, which are described in the "Notes" above. However, the `validation_results.csv` and `validation_m_mismatches.csv` are produced by running `validate_glossing.py` from FormosanBank QC/validation scripts library.

* **2. Download the audio**

```bash
    python scripts/download_grammar_audio.py
    python scripts/download_stories_audio.py
```

Note that there is no audio associated with sentences. 

Note also that utterances in grammar and stories lack audio, and some of the audio that is supposed to exist does not. An error log reports missing audio.

* **3. Standardize orthography

First, some more punctuation cleaning:

```bash
    python ../FormosanBank/QC/cleaning/clean_xml.py --corpora_path Final_XM
```

According to the documentation, all data use Ortho94. In practice, though, we found that where there are differences between Ortho94 and Ortho113, the latter fit the data better. The only exception is Amis, which appears to have been influenced by Church. 

* Amis - Church
* Atayal - Ortho113 <-- though with an unexpected number of `v`s. Could be Ortho94.
* Bunun - Ortho113 <-- though a lot of `g`s (mainly not Ortho94 because Junqun in Orth94 didn't have glottal stops).
* Kanakanavu - Ortho113 <-- with a bunch of á and ú and ó
* Kavalan - Ortho113
* Rukai - Ortho113
* Saisiyat - Ortho113 (could be Ortho94, but no important differences)
* Sakizaya - Ortho113
* Seediq - Ortho113 (could be Ortho94)
* Tsou - Ortho113 (could be Ortho94)

```bash
    python scripts/remove_no_audio_elements.py
    python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML --copy 
    python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML --orthography Ortho113
