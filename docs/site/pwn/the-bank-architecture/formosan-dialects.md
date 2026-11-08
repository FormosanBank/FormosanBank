---
icon: text-height
---

# Formosan Dialects

The Taiwanese government officially recognizes 42 dialects belonging to 16 extant Formosan languages. Within this repository, where possible, we identify and label these dialects directly in the XML files (see the [FormosanBank XML format](formosanbank-xml-format.md) for more details). Although other authorities have proposed alternative sets of dialect groupings themselves, our approach here is to follow the official nomenclature as recognized by the Taiwanese government, without making any independent scientific judgments.

When a given source text or audio file is clearly aligned with one of the officially recognized dialects, we include that dialect’s name directly in the XML. However, if it cannot be firmly placed within these recognized dialect divisions, any dialect information would be recorded only in the accompanying corpus documentation. This ensures the highest possible accuracy and transparency, while making it easier for users of the corpus to understand the scope and provenance of each resource.

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
