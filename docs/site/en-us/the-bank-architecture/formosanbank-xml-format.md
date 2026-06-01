---
icon: file-lines
---

# FormosanBank XML Format

The **XML format** used in FormosanBank is a standardized structure based on the **Pangloss Collection**, designed to ensure consistency and facilitate computational processing across the entire corpus. This format enables detailed linguistic annotation and metadata management, allowing researchers, language enthusiasts, and developers to easily navigate, analyze, and integrate the data. By adopting a uniform format, FormosanBank supports transparency, proper attribution, and interoperability with other linguistic tools and resources, making it an essential component of the project's technical architecture.

***

### Basic Structure

The XML format follows a hierarchical structure, with the primary elements organized as follows:

```xml
<TEXT xml:lang="fr" source="" audio="">
    <S>
        <W>
            <M>
            </M>
        </W>
    </S>
</TEXT>
```

***

### Example with ID Attributes

Each element includes unique identifiers (`id`), enabling easy reference:

```xml
<TEXT xml:lang="ami" id="story1">
    <S id="S1">
        <W id="S1W1">
            <M id="S1W1M1">
            </M>
        </W>
    </S>
</TEXT>
```

***

### The `<TEXT>` Element&#x20;

The `<TEXT>` represents the entire document. It is the root element, and it can only have \<S> tag as a sub-element. `<TEXT>` element must include these attributes:

* `id:`The unique identifier of the text; unique across resources
* `citation`: An APA-style citation of the original source. Users of the text in this XML are required to include this citation _along with_ a citation to FormosanBank. In case there are more than one citation associated with the corpus (the XML file), the citations will be seperated by a `|` delimter.
* `BibTeX_citation`: BibTeX citation of the original source. In case there are more than one citation associated with the corpus (the XML file), the citations will be seperated by a `,` delimter.
* `copyright`: The copyright or license information (e.g., CC BY).
* `xml:lang`: The language code using the ISO 639-3 standard.

Optional attributes may include:

* `source`: Description of the original file, chapter, or other relevant details. If this file contains everything in the original source, then this attribute is redundant with `citation` and won't be used. There is no specific format for `source`; it would contain enough information that the user can match what is in the XML against the original source.
* `audio`: Name of the associated audio file. If the audio is already segmented and there is no single audio file corresponding to the entire XML, this will be set to "segmented"
* `glottocode`: The [Glottolog](https://glottolog.org/) code if specifying a specific dialect.
* `dialect`: The name of the dialect of the Formosan language in use. Will only be used if the dialect name corresponds to one of the 42 official dialects. For more information, see [Formosan Dialects](formosan-dialects.md).

***

### The `<S>, <W>, and <M>` Elemenets

* `<S>`: Represents a sentence or utterance. It can only be a sub-element of the `<TEXT>` element.
* `<W>`: Represents a word. It can only be a sub-element of the `<S>` element.
* `<M>`: Represents a morpheme. It can only be a sub-element of the `<W>` element

The only attribute these three elements take (and require) is the `id` attribute.

***

### The `<FORM>` Element

At the lowest level of `<S>,` `<W>,` and `<M>`, a `<FORM>` element must be used to represent the text content.  `<FORM>` element can only be a sub-element of `<S>, <W>, and <M>` elements. `<FORM>` must be included at the lowest level of the hierarchy, but it could exist on multiple levels:

```xml
<S id="S14">
    <FORM>tɐrú kə mənaŋorɐ nə...</FORM>
    <W>
        <FORM>tɐrú</FORM>
    </W>
    <W>
        <FORM>kə</FORM>
    </W>
    <W>
        <FORM>mənaŋorɐ</FORM>
    </W>
</S>
```

The `<FORM>` element has one attribute, `kindOf`, which has two use cases:

**original** This is the text as it appeared in the original source. The only differences should be punctuation standardization. If there were listed errata, the `original` text should be updated to address those errata. Otherwise, this should be left as-is. In most cases, the `original` FORMs exist as a historical record and for reproducibility. They are not used in analysis and can be safely ignored by most end-users.

**standard** This is text that has been normalized as much as possible, including standardizing the orthography and spelling. For `S`-level FORMs only, this includes removing any morphological segmentation (other than morphological segmentation that may be indicated by the orthography rules themselves). For `W`-level forms, morphological segmentation should be retained.

### The `<PHON>` Element

This is an analog to `<FORM>` and contains IPA transliterations of the text. Note that these are almost always transliterations rather than actual transcriptions, being derived from the content of `<FORM>`.

Like `<FORM>`, `<PHON>` should have a `kindOf` attribute set to `original` or `standard`, indicating which text it is transliterated from. If this is a transcription not a transliteration, use `standard`.

***

### The `<AUDIO>` Element

The `<AUDIO>` element links specific audio segments to linguistic elements in the XML, such as sentences, words, or morphemes. It ensures that users can align the textual data with the corresponding audio.

Attributes:

* **`start`** and **`end`**: Must always be set when there is a single, large audio file associated with the entire XML document. These attributes indicate the start and end times of the audio segment in seconds, measured from the beginning of the file. When audio files are segmented, start would be 0 and end would be the length of the audio file associated with the element.
* **`file`** and **`url`**: Used when the audio is **segmented**—that is, there are separate audio files for individual elements (e.g., each sentence or word). The `file` attribute specifies the audio file for the segment, and the `url` attribute (optional) provides a web link for accessing the file.

Usage Scenarios:

1.  **Single Large Audio File**: When a single audio file covers the entire XML document (referenced in the `audio` attribute of the `<TEXT>` tag), the `<AUDIO>` element would include the `start` and `end` attributes to indicate the relevant segment's time range.

    Example:

    ```xml
    <AUDIO start="10.5" end="12.8"/>
    ```
2.  **Segmented Audio Files**: If individual audio files are provided for each element (sentence, word, etc.), the `audio` attribute of the `<TEXT>` tag would be set to "segmented." In this case, the `<AUDIO>` element would use the `file` attribute to indicate the corresponding audio file, and the `url` attribute can be included if the file is available online; this is in addition to start and end.&#x20;

    Example:

    ```xml
    <AUDIO start="0" end="4.23" file="sentence1_audio.mp3" url="https://example.com/audio/sentence1_audio.mp3"/>
    ```

***

### The `<TRANSL>` Element

The `<TRANSL>` element is used to provide translations of linguistic elements, such as sentences, words, or morphemes. It can be placed within different levels of the XML structure to specify translations at the appropriate granularity.

Attributes:

* **`xml:lang`**: The language code for the translation, using the ISO 639-3 standard.
* **`kindOf`** (optional): Specifies the method or tool used to generate the translation, such as a pivot language or translation software (e.g., `kindOf="DeepL"`). Including the software version, if applicable, is encouraged for more detailed documentation.

Usage Guidelines:

1.  **Sentence-Level Translation**: When placed within the `<S>` element, the `<TRANSL>` tag provides a translation for the entire sentence or utterance.

    Example:

    ```xml
    <S id="S1">
        <FORM>This is a sentence.</FORM>
        <TRANSL xml:lang="en">This is a sentence.</TRANSL>
        <TRANSL xml:lang="fr" kindOf="manual">Ceci est une phrase.</TRANSL>
    </S>
    ```
2.  **Word-Level Translation**: When placed within the `<W>` element, it provides a translation for that specific word.

    Example:

    ```xml
    <W id="W1">
        <FORM>ʕa</FORM>
        <TRANSL xml:lang="en">I</TRANSL>
    </W>
    ```
3.  **Morpheme-Level Translation (glosses)**: For linguistic glosses following the Leipzig Glossing Rules, use the `<TRANSL>` element within the `<M>` element to provide morpheme-level glosses.

    Example:

    ```xml
    <W>
        <M>
            <FORM>ʕa</FORM>
            <TRANSL xml:lang="en">1SG</TRANSL>
        </M>
    </W>
    ```

Importantly, the `M`-level `TRANSL` can have a `kindOf` attribute. Many of the older texts uses non-standard glosses, and even those that use Leipzig format may use different abbreviations for the same constructs. The original glosses should be left as is and indicated as `original` if necessary. Updated glosses should be `kidof="standard"`.

Note: didn't include class or subclss attrs for W and M and didn't include ver attr for TRANSL.

***

### Special Rules

#### Infixes and circumfixes

When creating the `M` levels for words that have infixes, the `FORM` for the infix should start and stop with a `-`, indicating that it is in an infix. The `FORM` for the morpheme that surrounded the infix should have a `-` where the infix went. So: `a-b-c` would result in `M`s of `a-c` and `-b-`. 

Circumfixes can be handled in an analogous way, though many glossing conventions treat the two parts of a circumfix as a prefix and a suffix. This should be standardized at some point. 

#### Clitics

Formosan languages have not standardized whether clitics are written as the same word or different, and probabilistic conventions have changed over time. When writing the `M` FORM for a clitic, include the `=` whether or not it was actually attached to the head word.