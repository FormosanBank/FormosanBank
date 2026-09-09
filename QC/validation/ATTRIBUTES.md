# XML attributes

Every attribute a FormosanBank XML file may carry, generated from
`QC/validation/xml_template.xsd` by
`QC/validation/attributes_catalogue.py`. **Do not edit by hand** —
annotate the attribute in the XSD and regenerate.

The schema declares no `anyAttribute`, so this list is exhaustive:
an attribute not named here fails `validate_xml.py`. Adding one
requires an XSD declaration, an `xs:documentation` annotation, a
regenerated catalogue, and a policy entry (POL-053).

## `<TEXT>`

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

## `<S>`

| Attribute | Use | Allowed values | Meaning |
| --- | --- | --- | --- |
| `audio_url` | optional | `xs:string` | Source URL for this sentence's audio, where the recording is addressed by URL rather than by file. |
| `id` | required | `xs:string` | Sentence identifier, unique across all S, W and M within the file (V039). Part of the public identifier surface (POL-037). A sentence split from another for optional material takes the original's id plus `-opt` (POL-028). |
| `source` | optional | `xs:string` | Sentence-specific provenance — page, column, or editorial note about where this particular sentence came from. |

## `<W>`

| Attribute | Use | Allowed values | Meaning |
| --- | --- | --- | --- |
| `class` | optional | `xs:string` | Grammatical class label for the word. The schema imposes no controlled vocabulary. |
| `id` | required | `xs:string` | Word identifier, unique across all S, W and M within the file (V039). |
| `sclass` | optional | `xs:string` | Grammatical subclass label for the word. The schema imposes no controlled vocabulary. |

## `<M>`

| Attribute | Use | Allowed values | Meaning |
| --- | --- | --- | --- |
| `class` | optional | `xs:string` | Grammatical class label for the morpheme. The schema imposes no controlled vocabulary. |
| `id` | required | `xs:string` | Morpheme identifier, unique across all S, W and M within the file (V039). |
| `sclass` | optional | `xs:string` | Grammatical subclass label for the morpheme. The schema imposes no controlled vocabulary. |

## `<FORM>`

| Attribute | Use | Allowed values | Meaning |
| --- | --- | --- | --- |
| `kindOf` | required | `original \| standard \| alternate` | Which tier this FORM belongs to. `original` is the text as the actual source prints it, preserving the source's orthographic choices. `standard` is that content transliterated into FormosanBank's common standard orthography. `alternate` is a spelling variant of a sibling FORM on the same node (POL-028); it requires a non-alternate sibling (V149) and must overlap it and stay in proportion to it (V150). |
| `notes` | optional | `xs:string` | Human-readable qualification of this FORM — a transcription note, a review status, or what the source actually printed where the tier departs from it. |

## `<PHON>`

| Attribute | Use | Allowed values | Meaning |
| --- | --- | --- | --- |
| `kindOf` | optional | `original \| standard` | Which FORM tier this IPA representation was derived from, `original` or `standard` (V071). A parent may carry at most one PHON per value (V072). |

## `<TRANSL>`

| Attribute | Use | Allowed values | Meaning |
| --- | --- | --- | --- |
| `kindOf` | optional | `original \| standard` | Only meaningful at W and M level, where a TRANSL carries a gloss: `original` is the source's own gloss, `standard` a standardized one. Forbidden on an S-level TRANSL, which is a free translation with no such axis (V151). |
| `notes` | optional | `xs:string` | Human-readable qualification of this translation — translator, review status, or a literal reading kept out of the translation text itself (POL-024). |
| `ver` | optional | `xs:string` | Discriminates multiple translations into the same language on one parent (POL-025). When a parent has two or more same-language TRANSLs, all but one must carry this (V085). The allowed values are owned by V084's allowlist — currently `{"alt"}` — deliberately not duplicated as an XSD enumeration, so there is one place to update. |
| `xml:lang` | optional | — | ISO 639-3 code for the language this translation is *into* — not the language of the text (V023, V035). |

## `<AUDIO>`

| Attribute | Use | Allowed values | Meaning |
| --- | --- | --- | --- |
| `end` | optional | `xs:double` | End offset in seconds within the referenced audio file. Must be greater than `start` (V054). |
| `file` | optional | `xs:string` | Name of the audio file this element refers to. Audio files are gitignored and fetched per corpus by `download_audio_data.sh`. |
| `source` | optional | `xs:string` | Provenance of the recording — for example the video or broadcast a clip was extracted from. |
| `start` | optional | `xs:double` | Start offset in seconds within the referenced audio file. Typed `xs:double`, so non-numeric values fail at schema time. |
| `url` | optional | `xs:string` | URL the audio can be fetched from, where it is addressed remotely rather than by filename. |

30 attributes across 8 elements.
