---
icon: text-height
---

# Formosan Dialects

The Taiwanese government officially recognizes 42 dialects belonging to 16 extant Formosan languages. Within this repository, where possible, we identify and label these dialects directly in the XML files (see the [FormosanBank XML format](formosanbank-xml-format.md) for more details). Although other authorities have proposed alternative sets of dialect groupings themselves, our approach here is to follow the official nomenclature as recognized by the Taiwanese government, without making any independent scientific judgments.

When a given source text or audio file is clearly aligned with one of the officially recognized dialects, we include that dialect's name directly in the XML. When the dialect cannot be firmly placed, the XML records `dialect="unknown"` rather than omitting the attribute — this preserves the distinction between "we don't know the dialect" and "we forgot to record it" (the latter is rejected by the validator). Any additional dialect-related context that doesn't fit on the `dialect` attribute is recorded in the accompanying corpus documentation.

For extant languages that have only one recognized dialect (Kanakanavu, Kavalan, Saaroa, Saisiyat, Sakizaya, Thao, Tsou, and Yami), the convention is to set `dialect` to the language name itself (e.g., `dialect="Tsou"` for an `xml:lang="tsu"` text). Siraya is supported with the same convention as a dormant language in FormosanBank, but it is not part of the official total of 42 dialects. Truku and Seediq share the ISO 639-3 code `trv`, so the validator uses the dialect value to distinguish Truku from the three official Seediq dialects.

***

### Language Registry: languages.csv

The main repository's [languages.csv](https://github.com/FormosanBank/FormosanBank/blob/main/languages.csv) (at the repo root, beside `dialects.csv` and `standards.csv`) is the canonical registry mapping ISO 639-3 codes to the language names used throughout FormosanBank. Every tool that resolves an `xml:lang` code — token counting, statistics, validators, orthography standardization — loads this one file, so adding or renaming a language happens in exactly one place. Its columns:

* **ISO639-3**: the lowercase ISO 639-3 code that appears in `xml:lang` (e.g., `ami`).
* **Language**: the display name used across the bank and in the other registries (e.g., `Amis`). These spellings are identical to the `language` values in `dialects.csv` and `standards.csv`; the registry validator checks the three files stay consistent.
* **Notes**: free-text caveats — most importantly that `trv` covers **both Seediq and Truku** (a text with `dialect="Truku"` resolves to Truku; anything else resolves to Seediq).

The registry also carries historical languages (Siraya, Babuza-Favorlang) and languages without published data yet (Pazeh), so their codes validate even though they sit outside the 16 officially recognized extant languages.

***

### CSV Mapping File

To help manage the complexity of multiple naming conventions, the main repository includes a [CSV file](https://github.com/FormosanBank/FormosanBank/blob/main/dialects.csv). This file serves as a “key” or reference point, enabling conversion between different dialect names that users may encounter. The CSV includes the following columns:

* **language**:\
  The name of the officially recognized Formosan language to which the dialect belongs. Since some languages encompass multiple dialects, this column helps group related dialects. An example would be 'Amis'
* **official**:\
  The official dialect name used by the FormosanBank repository. This is the name that will appear in the XML and other primary data files. An example would be 'Southern,' a dialect of the Amis language.
* **glottocode**:\
  The standardized [Glottocode identifier](https://glottolog.org/) corresponding to the dialect, if available. Glottocodes are unique identifiers used within the Glottolog database to reference languages and dialects, making it easier to connect data across different linguistic resources. An example would be 'cent2104,' referring to Coastal Amis
* **OtherNames**:\
  Any alternative dialect names that map onto the official dialect name. Because there may be multiple such names for a single dialect, the CSV may contain multiple rows for the same “official” dialect. Over time, as new names and variants become known, these entries will be updated or expanded.

***

### Ongoing Updates

This CSV file is a living document. We anticipate that ongoing research, consultation with linguists and native speakers, and the addition of new sources will lead to periodic updates. By maintaining a centralized and authoritative mapping of dialect names, we hope to make it easier for corpus users, researchers, and community members to identify, compare, and discuss Formosan dialects consistently and accurately.
