# ePark

### Overview

Yedda Palemeq, a Paiwan-speaker and linguist, maintained a [blog](https://yeddapalemeq.blogspot.com/) for several years in which she recorded and glossed short Paiwan texts, usually just one or two sentences. In aggregate, this is a non-trivial amount of material. She drew many of the examples from texts that are already included in FormosanBank, so de-duplication of text will remove some. However, the recordings are all novel and do not appear elsewhere. 

***

<!-- CORPUS STATS START -->
### Corpus Statistics

| | Paiwan<br>Southern |
| --- | --- |
| Word count | 5,878 |
| Total audio | 1.2h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 1.2h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 5,863 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 0 |
| Morphologically segmented | 5,641 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


### **Access Details**

* The repo containing the ePark corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/YeddaPalemeqBlog).

***

### **Corpus Notes**

* The scrape was not completely successful and a few blog posts are not included.
* Sometimes the same word is spelled differently in the main text and the glosses. We have assumed that the main text is correct and the gloss is incorrect. In those cases, the gloss is ignored.
* Examples are not necessarily glossed word-by-word; repeated words and some common function words are not always listed. We did our best to automatically match glosses within that specific example; we do not reuse glosses from other examples, since we cannot be sure that they are contextually correct. If no gloss can be found, the <W> element's <FORM> is just a copy of the word in the example and no gloss is provided (there is no <TRANSL> element).
* Words are segmented in the glosses. These segments are preserved in the <M> elements. Note that the author did not provide morpheme-by-morpheme glosses, so no glossing is provided for individual morphemes. Not also that if we could not find a gloss for a word, it is assumed to be monomorphemic. This is almost certainly incorrect in some cases. 

***

### Copyright

CC BY-NC 4.0

***

### Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Palemeq, Y. (2021). Yedda Palemeq. Retrieved May 19, 2026, from https://yeddapalemeq.blogspot.com/
