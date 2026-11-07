---
icon: gauge-simple-min
---

# FormosanBank: How it Works

FormosanBank is a corpus of Corpora. That is, like Pangloss or CHILDES, it is organized around the original data sources. Each of these is in its own folder in `FormosanBank/Corpora`. 

Within each corpus, there is an `XML` folder, which contains one or more XML files, potentially organized into subfolders. Each XML file has a header that contains critical information about the data in that file, including what the target language is, what the source is, what citation to use, and so on. 

Each file contains text in one or more target languages. It may also include translations and morphosyntactic glosses. If there is associated audio, the XML indicates which audio files go with which segments of the text. The XML format is explained [here](https://ai4commsci.gitbook.io/formosanbank/the-bank-architecture/formosanbank-xml-format).

Most audio is distributed through Hugging Face. Each corpus whose audio is hosted there has a `download_audio_data.sh` script. Some small corpora keep audio directly in the repository instead. In the root of FormosanBank, `run_audio_downloads.sh` runs every available corpus download script.

**Note**: XML filenames and audio filenames are *not* unique. Unless you really know what you are doing, we recommend keeping the same organization as in the FormosanBank repo. Simply delete any corpora you do not need. 

***

### Standardization

FormosanBank compiles corpora from many different sources. These vary in a number of ways.

* Orthography. Different individuals and groups have developed a wide range of orthographies for Taiwan's indigenous languages. The most widely used ones are one created by the Ministry of Education, two created by the Indigenous Languages Research and Development Foundation, and several developed for Bible translations. There are also orthographies developed by individual researchers for specific projects, as well as Japanese and Dutch orthographies. 

* Phonemes. Earlier sources do not necessarily record all phonemes. This is especially true of -- but not restricted to -- glottal stops. Some sources fail to distinguish different phonemes. Others distinguish phonemes that are in fact the same phoneme (the `o` vs. `u` distinction in many languages is the prime example).

* Clitics. Clitics are sometimes written as a separate word and sometimes not. This appears to have changed over time.

* Hyphens. Some orthographies and some individual writers make significant use of hyphens to segment out some (not all) morphemes.

Complicated the above, many sources are inconsistent, rendering the same text in multiple ways in the same document. 

The XMLs have two tiers: `original` and `standard` (see XML documentation). As much as is feasible, the original source is faithfully recorded in the `original` tier without correction. The primary exception is that if the original source segmented all words into morphemes, this segmentation is typically removed (this may vary by corpus).

The `standard` tier standardizes the text as much as possible. In the case of orthography, we convert the orthography to the current official orthography. Currently, this involves character substitutions (you can find the substitution tables [here](https://github.com/FormosanBank/FormosanBank/tree/main/Orthographies/ConversionTables)). Note that when the original orthography fails to distinguish phonemes that are distinguished in the modern orthography, we do not currently adjust. It would not be feasible to do so by hand, and automatic spelling- and grammar-checking is not yet good enough. Currently, we do not standardize clitics. We generally remove hyphens unless included in the modern orthography (we do not standardize their usage). Over time, we hope to improve on the standardization (help is very much welcome!).

***

### Note Well

Creating a large corpus of Taiwanese indigenous languages raises a number of complications. The most significant are:

* **Dialectal variation.** Several of the languages have multiple officially recognized dialects. These vary from one another to greater or lesser degrees. In some cases (most notably Amis), they use slightly different orthographies. Where we can identify the dialect, it is indicated in a `dialect` attribute in the XML header. When we cannot identify the dialect, the current convention is `dialect="unknown"`. The validator rejects a missing dialect attribute.

* **Untranscribed audio.** Untranscribed audio files are nonetheless associated with XML files. These XML files have headers (in order to contain the necessary meta-data) but no text.

* **Error suppression.** When it is clear that the audio is mismatched to the text, the audio filename is removed from the XML. The same goes for glosses or translations: when they mismatch the text, they are suppressed. This is often (not always) documented in the README in the corpus folder in the repo. Note that if there is an audio file, a gloss, or a translation, we do not assert that they are correct, only that we are not certain that they are incorrect. 

***

### Copyright and Licensing

Each resource in FormosanBank has its own **copyright and licensing terms**. There is no single blanket license for the corpus collection. Rights and usage restrictions are provided on the individual resource pages and in each XML, and stricter upstream or contributor notices control. See the [Terms of Use](../additional-resources/terms-of-use.md) and [AI Use and Commercial Licensing](../additional-resources/ai-use-and-commercial-licensing.md).

***

### Where Do I Find More Details?

Start with the [corpus pages](../the-bank-architecture/corpora/README.md) for source-specific notes and citations. The [XML format](../the-bank-architecture/formosanbank-xml-format.md) explains the data model. Contributors and developers can use the [developer documentation](../the-bank-architecture/developers/README.md) for folder layout, quality control, statistics, and porting workflows.

***

### Looking Ahead

The project is continually evolving, with plans to **expand the corpus**, **improve data quality**, and **incorporate new technologies** for linguistic research. Collaboration with **Indigenous communities, linguists, and technology experts** remains a key component of FormosanBank’s growth, ensuring that the project remains **community-oriented** and **culturally sensitive**.
