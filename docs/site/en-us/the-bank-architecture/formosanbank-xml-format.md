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

**When does the `<M>` level exist?** The unit of morphological analysis is the *sentence*, not the file. A sentence carries some analysis when either some word in it has two or more morphemes, or some `<M>`'s FORM differs from its parent `<W>`'s FORM (an infix split such as `l<em>angeda` → `l-angeda` / `-em-` carries an analysis even at one `<M>` per `<W>`). Within such a sentence, *every* `<W>` carries at least one `<M>` — a word with exactly one `<M>` reads as "analyzed as monomorphemic". A sentence the author simply never analyzed carries no `<M>` at all; demanding one there would fake an analysis it does not have. A file may therefore mix parsed and unparsed sentences freely. A corpus without any morpheme segmentation has no `<M>` level at all: a tier of words each wrapping a single identical morpheme adds no information. (Policy POL-023, scope amended 2026-08-12. The validator flags both violations as soft findings: V144 per sentence, V145 deliberately per file — one short sentence of genuinely monomorphemic words is indistinguishable from a mirror tier, so only a whole file with no multi-morphemic word anywhere is reliable evidence of a fake tier.)

***

### The `<FORM>` Element

`<FORM>` contains the linguistic form at sentence, word, or morpheme level. Its required `kindOf` attribute accepts:

* `original`: The source form, preserving the source's orthographic choices after limited punctuation, entity, and Unicode cleanup.
* `standard`: The same content converted as far as possible to FormosanBank's common standard orthography.
* `alternate`: A **spelling variant** of a sibling FORM on the same node — for example a second witness's reading, or a source cell offering two spellings. It must have a non-alternate sibling to vary from, and must either overlap it closely or be short along with it; neither form may be more than twice the length of the other. A competing *word* for the same meaning is not an alternate: per POL-027 that becomes its own `<S>` block. The variation may span the whole form — a one-letter word alternating `a`/`u` is a perfectly good alternate. (Policy POL-028; validator rules V149 HARD and V150 SOFT.)

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

PHON is **machine-generated and machine-owned**: `add_phonology.py` regenerates it from the FORM tiers on every pipeline run, so hand edits to PHON do not survive — to change a PHON, correct the FORM (or the orthography profile) and regenerate. Original PHON is derived through the source orthography's profile; standard PHON uses the orthography each language declares in the repository's `standards.csv` registry (a language with no declared standard simply has no standard PHON).

Conventions of the generated content:

* **Phonemic variants** are written `[x|y]` — two or more pipe-separated alternatives in square brackets, e.g. `ta[b|v]aki` for a letter realized as either /b/ or /v/, or `[ɬ|ɮ]` for a three-way `[ɬ|ɮ|l]` style alternation. Multi-character alternatives are fine (`[l|ll]`). Some variants are resolved by context rules (e.g. Bunun's `c` resolving to `ʦ` before *a/u* but `ʨ` before *i*), in which case the resolved phone appears instead of a variant group.
* **Punctuation is not represented**: characters with no sound value are dropped from PHON rather than copied.
* **Unmapped letters** — characters the orthography profile cannot transcribe — surface as `*` so they can be found and reviewed, never silently guessed.
* **Null morphemes are silent**: a null marker (`∅`) inside a FORM contributes nothing to PHON, but a FORM that *is* a null morpheme gets `<PHON>∅</PHON>` so the tier is never empty.

***

### The `<TRANSL>` Element

`<TRANSL>` provides a translation at sentence, word, or morpheme level. Every translation requires `xml:lang` using an ISO 639-3 code.

Optional attributes are:

* `kindOf`: `original` or `standard`, and **only meaningful at word and morpheme level**, where a `TRANSL` carries a gloss: `original` is the source's own gloss, `standard` a standardized one. It is **forbidden on a sentence-level `TRANSL`** — a free translation has no original-vs-standard axis, so the attribute would carry no information. The validator reports S-level uses (V151) and the schema restricts the value at every level.
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

#### Optional material and alternatives

A source sentence with optional words — *x y (z)* — becomes **two** `<S>` blocks, one for *x y* and one for *x y z*, each with glosses and translations matching its own variant (the *x y* block must not carry *z*'s gloss). A source sentence offering alternatives — *Sally likes x / y / z* — becomes **one `<S>` block per option**, never a single block with the slashes retained. (Policies POL-026/POL-027; leftover parentheses or slashes in published FORMs are what the V121/V122 validator findings point at.)

#### Ungrammatical and marginal examples

Examples a source marks as ungrammatical (`*`) or questionable/marginal (`?`) are **not ingested** — neither with the marker inline nor with it stripped (policy POL-016). A `*` in any published FORM is a hard validator finding.

***

### Validation

Run the structural validator from the public FormosanBank repository before using the other QC tools:

```bash
source .venv/bin/activate
python QC/validation/validate_xml.py by_path --path Corpora/<CorpusName>/XML
```

The validator checks the XSD, required dialect and language metadata, FORM and TRANSL rules, audio modes, ID uniqueness, and other cross-file constraints. See the [`validate_xml.py` documentation](developers/qc-pipeline/validate-xml.md) for the complete rule list and output format.

***

### Every attribute, in one place

The attribute set is **closed**: the schema declares no `anyAttribute`, so an attribute not listed here fails validation. Adding one requires a schema declaration, documentation, a regenerated catalogue, and a policy entry (POL-053) — never ad hoc.

This table is generated from `QC/validation/xml_template.xsd` in the FormosanBank repo, where it is also published as `QC/validation/ATTRIBUTES.md`.

#### `<TEXT>`

| Attribute | Use | Allowed values | Meaning |
| --- | --- | --- | --- |
| `BibTeX_citation` | required | `xs:string` | The same source as a BibTeX entry, for machine reuse. Required on every published TEXT. |
| `audio` | optional | `xs:string` | Name or identifier of the audio collection this text's recordings belong to. Present only for corpora with audio. |
| `citation` | required | `xs:string` | Human-readable bibliographic citation for the source. Required on every published TEXT (POL-042). |
| `copyright` | required | `xs:string` | The rights statement under which this text is published. Required on every published TEXT; POL-042 through POL-045 govern what may go here. |
| `dialect` | optional | `xs:string` | Dialect label, from the canonical list in `dialects.csv` (V036). Together with `xml:lang` this determines language identity and which reference materials apply. |
| `glottocode` | optional | `xs:string` | Glottolog code for the variety, where one is useful alongside the ISO 639-3 code. |
| `id` | required | `xs:string` | Stable public identifier for this text, unique across the published bank (V081). Renaming one breaks external references — see POL-037. |
| `source` | optional | `xs:string` | Free-text provenance for the whole text — the publication, page, URL or collection it came from. |
| `xml:lang` | required | — | ISO 639-3 code for the language of the Formosan-text tiers, validated against `QC/validation/iso-639-3.txt` (V035). Note `trv` covers the whole Seediq family: `trv` plus `dialect="Truku"` is Truku, anything else is Seediq. |

#### `<S>`

| Attribute | Use | Allowed values | Meaning |
| --- | --- | --- | --- |
| `audio_url` | optional | `xs:string` | Source URL for this sentence's audio, where the recording is addressed by URL rather than by file. |
| `id` | required | `xs:string` | Sentence identifier, unique across all S, W and M within the file (V039). Part of the public identifier surface (POL-037). A sentence split from another for optional material takes the original's id plus `-opt` (POL-028). |
| `source` | optional | `xs:string` | Sentence-specific provenance — page, column, or editorial note about where this particular sentence came from. |

#### `<W>`

| Attribute | Use | Allowed values | Meaning |
| --- | --- | --- | --- |
| `class` | optional | `xs:string` | Grammatical class label for the word. The schema imposes no controlled vocabulary. |
| `id` | required | `xs:string` | Word identifier, unique across all S, W and M within the file (V039). |
| `sclass` | optional | `xs:string` | Grammatical subclass label for the word. The schema imposes no controlled vocabulary. |

#### `<M>`

| Attribute | Use | Allowed values | Meaning |
| --- | --- | --- | --- |
| `class` | optional | `xs:string` | Grammatical class label for the morpheme. The schema imposes no controlled vocabulary. |
| `id` | required | `xs:string` | Morpheme identifier, unique across all S, W and M within the file (V039). |
| `sclass` | optional | `xs:string` | Grammatical subclass label for the morpheme. The schema imposes no controlled vocabulary. |

#### `<FORM>`

| Attribute | Use | Allowed values | Meaning |
| --- | --- | --- | --- |
| `kindOf` | required | `original \| standard \| alternate` | Which tier this FORM belongs to. `original` is the text as the actual source prints it, preserving the source's orthographic choices. `standard` is that content transliterated into FormosanBank's common standard orthography. `alternate` is a spelling variant of a sibling FORM on the same node (POL-028); it requires a non-alternate sibling (V149) and must overlap it and stay in proportion to it (V150). |
| `notes` | optional | `xs:string` | Human-readable qualification of this FORM — a transcription note, a review status, or what the source actually printed where the tier departs from it. |

#### `<PHON>`

| Attribute | Use | Allowed values | Meaning |
| --- | --- | --- | --- |
| `kindOf` | optional | `original \| standard` | Which FORM tier this IPA representation was derived from, `original` or `standard` (V071). A parent may carry at most one PHON per value (V072). |

#### `<TRANSL>`

| Attribute | Use | Allowed values | Meaning |
| --- | --- | --- | --- |
| `kindOf` | optional | `original \| standard` | Only meaningful at W and M level, where a TRANSL carries a gloss: `original` is the source's own gloss, `standard` a standardized one. Forbidden on an S-level TRANSL, which is a free translation with no such axis (V151). |
| `notes` | optional | `xs:string` | Human-readable qualification of this translation — translator, review status, or a literal reading kept out of the translation text itself (POL-024). |
| `ver` | optional | `xs:string` | Discriminates multiple translations into the same language on one parent (POL-025). When a parent has two or more same-language TRANSLs, all but one must carry this (V085). The allowed values are owned by V084's allowlist — currently `{"alt"}` — deliberately not duplicated as an XSD enumeration, so there is one place to update. |
| `xml:lang` | optional | — | ISO 639-3 code for the language this translation is *into* — not the language of the text (V023, V035). |

#### `<AUDIO>`

| Attribute | Use | Allowed values | Meaning |
| --- | --- | --- | --- |
| `end` | optional | `xs:double` | End offset in seconds within the referenced audio file. Must be greater than `start` (V054). |
| `file` | optional | `xs:string` | Name of the audio file this element refers to. Audio files are gitignored and fetched per corpus by `download_audio_data.sh`. |
| `source` | optional | `xs:string` | Provenance of the recording — for example the video or broadcast a clip was extracted from. |
| `start` | optional | `xs:double` | Start offset in seconds within the referenced audio file. Typed `xs:double`, so non-numeric values fail at schema time. |
| `url` | optional | `xs:string` | URL the audio can be fetched from, where it is addressed remotely rather than by filename. |

30 attributes across 8 elements.
