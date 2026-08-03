---
icon: file-lines
---

# FormosanBank XML Format

The **XML format** used in FormosanBank is a standardized structure based on the **Pangloss Collection**. It provides one consistent representation for source text, standardized text, translations, linguistic annotation, audio alignment, and source metadata across the corpora.

The canonical schema is [`QC/validation/xml_template.xsd`](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/xml_template.xsd). The Python validator adds rules that the XSD cannot express. New or changed XML should pass [`validate_xml.py`](developers/qc-pipeline/validate-xml.md) before any other quality-control step.

***

### Basic Structure

A minimal text file has a `<TEXT>` root, required source metadata, and at least one sentence:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<TEXT
    id="sample_amis_text"
    citation="Example source citation."
    BibTeX_citation="@misc{sample_amis_text}"
    copyright="CC BY-NC 4.0"
    xml:lang="ami"
    dialect="Coastal">
    <S id="sample_amis_text_S1">
        <FORM kindOf="original">O maan ko ngangan iso?</FORM>
        <FORM kindOf="standard">O maan ko ngangan iso?</FORM>
        <TRANSL xml:lang="eng">What is your name?</TRANSL>
    </S>
</TEXT>
```

`xml:lang` uses ISO 639-3 codes, so translations use values such as `eng` and `zho`, not two-letter codes such as `en` and `zh`.

The hierarchy is:

```text
TEXT
├── AUDIO*                 optional document-level audio
└── S*                     sentence or utterance
    ├── FORM*
    ├── PHON*
    ├── TRANSL*
    ├── AUDIO*
    └── W*                 word
        ├── FORM*
        ├── PHON*
        ├── TRANSL*
        ├── AUDIO*
        └── M*             morpheme
            ├── FORM*
            ├── PHON*
            ├── TRANSL*
            └── AUDIO*
```

Document-level `<AUDIO>` elements must appear before `<S>` elements. Within `<S>`, `<W>`, and `<M>`, the order of sibling FORM, PHON, TRANSL, AUDIO, W, or M elements is not enforced.

***

### The `<TEXT>` Element

`<TEXT>` represents one document. It has five attributes required by the XSD:

* `id`: A stable identifier for the text. It must not collide with a published `TEXT/@id`.
* `citation`: The human-readable citation for the original source. Users must cite this source along with FormosanBank where required.
* `BibTeX_citation`: The corresponding BibTeX citation.
* `copyright`: The copyright or license notice that applies to the file.
* `xml:lang`: The source language as an ISO 639-3 code.

The validator also requires:

* `dialect`: An official FormosanBank dialect value for the language, or `unknown` when the dialect cannot be identified. See [Formosan Dialects](formosan-dialects.md) and [`dialects.csv`](https://github.com/FormosanBank/FormosanBank/blob/main/dialects.csv). For `xml:lang="trv"`, this value distinguishes Truku from the three Seediq dialects.

Optional attributes are:

* `source`: A more specific source location, chapter, file, or other provenance note.
* `audio`: The document-level audio filename, or `segmented` when separate clips are used.
* `glottocode`: A Glottolog code when one is useful for the variety represented.

A text-only file normally contains one or more `<S>` elements. An audio-only file may instead contain document-level `<AUDIO>` elements and no sentences.

***

### The `<S>`, `<W>`, and `<M>` Elements

* `<S>` represents a sentence or utterance and is a direct child of `<TEXT>`.
* `<W>` represents a word and is a direct child of `<S>`.
* `<M>` represents a morpheme and is a direct child of `<W>`.

All three require an `id`. IDs for S, W, and M elements must be unique within the XML file.

`<S>` may also have:

* `audio_url`: A source URL for sentence-level audio.
* `source`: A sentence-specific provenance note.

`<W>` and `<M>` may also have:

* `class`: A grammatical class label.
* `sclass`: A grammatical subclass label.

The schema does not impose a controlled vocabulary on `class` or `sclass`.

An `<S>` may be empty when an utterance has not yet been transcribed, although the validator reports this as a soft finding. Every `<W>` and `<M>` must contain at least one `<FORM>`.

***

### The `<FORM>` Element

`<FORM>` contains the linguistic form at sentence, word, or morpheme level. Its required `kindOf` attribute accepts:

* `original`: The source form, preserving the source's orthographic choices after limited punctuation, entity, and Unicode cleanup.
* `standard`: The same content converted as far as possible to FormosanBank's common standard orthography.
* `alternate`: A genuine alternate form retained alongside the main tiers.

An optional `notes` attribute can record a transcription note, review status, or other human-readable qualification.

If an `<S>` has any FORM, exactly one must be `kindOf="original"`. A standard FORM is expected by much of the downstream tooling, but its absence is a soft validation finding. W and M elements also require a FORM, although their tier combinations can vary with the source annotation.

```xml
<S id="sample_S1">
    <FORM kindOf="original" notes="Source spelling retained.">...</FORM>
    <FORM kindOf="standard">...</FORM>
</S>
```

***

### The `<PHON>` Element

`<PHON>` contains an IPA representation of a FORM. In most corpora this is an automatic transliteration, not a phonetic transcription. It is marker-free: morphological segmentation markers carried by a W/M FORM (`-`, `=`, and the `<...>` infix brackets) are not represented in `PHON`, though an infix's content is retained since it is pronounced.

Its optional `kindOf` attribute may be `original` or `standard`, identifying the FORM tier from which it was derived. A parent may have at most one PHON for each `kindOf` value.

```xml
<PHON kindOf="standard">o maan ko ŋaŋan iso</PHON>
```

***

### The `<TRANSL>` Element

`<TRANSL>` provides a translation at sentence, word, or morpheme level. Every translation requires `xml:lang` using an ISO 639-3 code.

Optional attributes are:

* `kindOf`: The translation type, method, or provenance. At morpheme level, the validator limits this to `original` or `standard`.
* `ver`: Distinguishes multiple translations into the same language on the same parent. The current allowed value is `alt`.
* `notes`: A translator, review status, caveat, or other human-readable note.

When a parent contains more than one translation with the same `xml:lang`, at least one must have a `ver` value:

```xml
<TRANSL xml:lang="eng">What is your name?</TRANSL>
<TRANSL xml:lang="eng" ver="alt">What are you called?</TRANSL>
<TRANSL xml:lang="zho">你叫什麼名字？</TRANSL>
```

Morpheme glosses are represented as translations within `<M>`:

```xml
<M id="sample_S1_W1_M1" class="pronoun">
    <FORM kindOf="original">ako</FORM>
    <TRANSL xml:lang="eng" kindOf="original">1SG.GEN</TRANSL>
</M>
```

Original source glosses should be preserved. A standardized gloss can be added as a separate `kindOf="standard"` translation.

***

### The `<AUDIO>` Element

`<AUDIO>` links a document, sentence, word, or morpheme to audio. It accepts:

* `start` and `end`: Numeric offsets in seconds.
* `file`: A non-empty audio filename.
* `url`: A web location for the audio.
* `source`: Additional audio provenance.

For a segment within one document-level recording, set `TEXT/@audio` and provide `start` and `end`:

```xml
<TEXT
    id="sample_recording"
    citation="Example source citation."
    BibTeX_citation="@misc{sample_recording}"
    copyright="CC BY-NC 4.0"
    xml:lang="ami"
    dialect="Coastal"
    audio="recording.wav">
    <S id="sample_recording_S1">
        <FORM kindOf="original">...</FORM>
        <AUDIO start="10.5" end="12.8"/>
    </S>
</TEXT>
```

For separate clips, use `file`. Start and end may describe the used region of that clip:

```xml
<AUDIO start="0" end="4.23" file="sentence1.wav"/>
```

The validator requires `start < end`. An AUDIO without its own `file` must have both offsets and a document-level `TEXT/@audio`. A `url` supplements the local or document-level reference; it does not replace these structural requirements.

***

### The `<UNCLEAR>` Element

`<UNCLEAR/>` marks audio or text that was actively reviewed but could not be transcribed or translated. It can replace the whole content of a FORM, PHON, or TRANSL, or appear inline:

```xml
<FORM kindOf="original"><UNCLEAR/></FORM>
<FORM kindOf="original">misa <UNCLEAR/> kako</FORM>
```

This is different from a missing FORM. A missing FORM means that no transcription is available; `<UNCLEAR/>` records that transcription was attempted but the content could not be recovered. Token-counting tools do not count it as a token.

***

### Special Rules

#### Infixes and circumfixes

When creating M levels for a word with an infix, the infix FORM should begin and end with `-`. The FORM for the surrounding morpheme should use `-` where the infix occurred. For example, `a-b-c` is represented by morpheme FORMs `a-c` and `-b-`.

Circumfixes can be handled in an analogous way, although some source glossing conventions treat their two parts as a prefix and a suffix.

#### Clitics

Formosan sources do not use one consistent convention for writing clitics as attached or separate words. In an M-level FORM for a clitic, retain the `=` marker whether or not the source wrote the clitic together with its host.

***

### Validation

Run the structural validator from the public FormosanBank repository before using the other QC tools:

```bash
source .venv/bin/activate
python QC/validation/validate_xml.py by_path --path Corpora/<CorpusName>/XML
```

The validator checks the XSD, required dialect and language metadata, FORM and TRANSL rules, audio modes, ID uniqueness, and other cross-file constraints. See the [`validate_xml.py` documentation](developers/qc-pipeline/validate-xml.md) for the complete rule list and output format.
