# ILRDF Dictionaries

Example sentences and headword entries for all sixteen Formosan languages,
drawn from the Council of Indigenous Peoples / Indigenous Languages Research
and Development Foundation (ILRDF) online dictionary,
<https://e-dictionary.ilrdf.org.tw/>.

## Languages and dialects

One folder per language, `XML/<Language>/`, each holding a sentence file
`<Language>.xml` and a headword file `<Language>_dictionary.xml`. Both files of
a language carry the same values on `<TEXT>`:

| Language | `xml:lang` | `dialect` | `glottocode` |
|---|---|---|---|
| Amis | `ami` | `Xiuguluan` | `cent2104` |
| Atayal | `tay` | `Sekolik` | none |
| Bunun | `bnn` | `Junqun` | `sout2930` |
| Kanakanavu | `xnb` | `unknown` | none |
| Kavalan | `ckv` | `unknown` | none |
| Paiwan | `pwn` | `Northern` | none |
| Puyuma | `pyu` | `Nanwang` | `nanw1237` |
| Rukai | `dru` | `Wutai` | `buda1252` |
| Saaroa | `sxr` | `unknown` | none |
| Saisiyat | `xsy` | `unknown` | none |
| Sakizaya | `szy` | `unknown` | none |
| Seediq | `trv` | `Tegudaya` | `teke1282` |
| Thao | `ssf` | `unknown` | none |
| Truku | `trv` | `Truku` | none |
| Tsou | `tsu` | `unknown` | none |
| Yami | `tao` | `unknown` | none |

**Language and dialect** are as FormosanBank published them before the rebuild: Amis `Xiuguluan`, Atayal `Sekolik`, Bunun `Junqun`, Paiwan `Northern`, Puyuma `Nanwang`, Rukai `Wutai`, Seediq `Tegudaya`, Truku `Truku`; the other eight `unknown`. Seediq and Truku share `xml:lang="trv"`; `dialect="Truku"` is what makes the Truku files count as Truku.

**Language and dialect.** `xml:lang`, `dialect` and `glottocode` are as
FormosanBank published them before the rebuild: Amis `Xiuguluan`
(`cent2104`), Atayal `Sekolik`, Bunun `Junqun` (`sout2930`), Paiwan
`Northern`, Puyuma `Nanwang` (`nanw1237`), Rukai `Wutai` (`buda1252`),
Seediq `Tegudaya` (`teke1282`), Truku `Truku`; the other eight `unknown`.
Seediq and Truku share `xml:lang="trv"`; `dialect="Truku"` is what makes the
Truku files count as Truku.

The build takes these values from FormosanBank's 2024 publication of the corpus
(`generate_xml.py`, `text_attributes`); where that publication had none, the
dialect is `unknown`. The rebuild does not read a dialect from the ILRDF
source; whether the source distinguishes dialects for these eight languages is
not documented in this repository.

## Source

#### Overview

The [**Indigenous Languages Research and Development Foundation**](https://www.ilrdf.org.tw/) **(ILRDF)** dictionaries are a comprehensive digital resource designed to preserve and promote Taiwan’s indigenous languages. Built upon the foundational [writing systems ](https://yongfu.name/temp-data/pdf/writingsystemsdoc.pdf)announced in 2005 by the [Council of Indigenous Peoples](https://www.cip.gov.tw/en/index.html) and the Ministry of Education, these dictionaries represent the culmination of nearly seven years of collaborative effort involving hundreds of participants. The ILRDF dictionaries serve as an essential tool for language revitalization, education, and research, ensuring the cultural and linguistic heritage of Taiwan's indigenous peoples is preserved for future generations.&#x20;

The **ILRDF Dictionaries Corpus** is an integral part of the FormosanBank project, providing a rich and structured dataset of the 16 officially recognized Formosan languages: **Amis**, **Atayal**, **Saisiyat**, **Thao**, **Seediq**, **Bunun**, **Paiwan**, **Rukai**, **Truku**, **Kavalan**, **Tsou**, **Kanakanavu**, **Saaroa**, **Puyuma**, **Yami**, and **Sakizaya**. These dictionaries are invaluable for documenting and preserving linguistic diversity. They include text, audio recordings, and translations, making them a comprehensive resource for research, education, and language revitalization.

Visit the **Indigenous Languages Online Dictionary** at [https://e-dictionary.ilrdf.org.tw](https://e-dictionary.ilrdf.org.tw) to explore the 16 indigenous language dictionaries.

#### What is in it

The corpus was rebuilt in 2026 from committed snapshots of the ILRDF dictionary API (retrieved 2026-05-04), keeping the sentence ids FormosanBank had already published from its 2024 scrape. It publishes two things per language: sentences and headword entries.

Rebuilt in 2026 from committed snapshots of the ILRDF dictionary API
(retrieved 2026-05-04), keeping the sentence ids FormosanBank had already
published from its 2024 scrape.

| | Sentences | Dictionaries |
|---|---:|---:|
| Files | 16 | 16 |
| `S` records | 184,119 | 139,579 |
| Translations (`TRANSL`) | 187,314 | 164,849 |
| `AUDIO` in an `S` (at most one per `S`) | 130,763 | — |
| untranscribed `AUDIO` (direct child of `TEXT`) | 1,438 | — |
| Variant readings (`FORM kindOf="original" ver="alt"`) | 2,024 | 134 |

| Language | `S` (sentences) | under a main id | new (GUID id) | of which 2024-only | `AUDIO` in an `S` | untranscribed `AUDIO` | headword entries |
|---|---:|---:|---:|---:|---:|---:|---:|
| Amis | 9,037 | 5,615 | 3,422 | 4 | 6,560 | 32 | 8,444 |
| Atayal | 9,191 | 6,410 | 2,781 | 89 | 6,885 | 172 | 6,496 |
| Bunun | 12,368 | 9,022 | 3,346 | 6 | 10,444 | 59 | 7,564 |
| Kanakanavu | 8,837 | 5,647 | 3,190 | 537 | 6,609 | 160 | 4,415 |
| Kavalan | 10,647 | 8,384 | 2,263 | 138 | 9,287 | 62 | 7,291 |
| Paiwan | 7,837 | 5,424 | 2,413 | 3 | 5,812 | 81 | 6,625 |
| Puyuma | 9,631 | 7,279 | 2,352 | 36 | 8,208 | 134 | 8,636 |
| Rukai | 15,236 | 10,474 | 4,762 | 2 | 12,958 | 13 | 12,997 |
| Saaroa | 7,161 | 4,156 | 3,005 | 209 | 4,837 | 130 | 6,092 |
| Saisiyat | 9,339 | 6,211 | 3,128 | 38 | 7,600 | 93 | 6,268 |
| Sakizaya | 8,495 | 5,565 | 2,930 | 1 | 6,766 | 118 | 7,078 |
| Seediq | 7,660 | 5,495 | 2,165 | 29 | 6,115 | 43 | 5,977 |
| Thao | 9,860 | 6,660 | 3,200 | 22 | 7,658 | 127 | 5,165 |
| Truku | 29,718 | 4,762 | 24,956 | 6 | 5,810 | 24 | 32,892 |
| Tsou | 7,186 | 2,956 | 4,230 | 116 | 4,885 | 149 | 5,768 |
| Yami | 21,916 | 19,158 | 2,758 | 15 | 20,329 | 41 | 7,871 |
| **Total** | **184,119** | **113,218** | **70,901** | **1,251** | **130,763** | **1,438** | **139,579** |

"Under a main id" includes the `-opt` records split from a main sentence
(alternatives, and one `S` per recording); "2024-only" sentences are
explained below, under "Notes and caveats".

The **example sentences** (`XML/<Language>/<Language>.xml`) carry the source's Chinese translation and, where the source has one, a recording. The **headword entries** (`XML/<Language>/<Language>_dictionary.xml`) give one `<S>` per headword and one `<TRANSL>` per sense; each sense after the first is a `ver="alt"` TRANSL, and its part of speech is on that sense's `TRANSL/@notes`. Neither has a word or morpheme tier: the source carries no morphological analysis.

**Sentences** — `XML/<Language>/<Language>.xml`, one `<S>` per example
sentence, with the source's Chinese translation and its recordings.

**Dictionaries** — `XML/<Language>/<Language>_dictionary.xml`, one `<S>` per
headword and one `<TRANSL>` per sense; each sense after the first is a
`ver="alt"` TRANSL (POL-025). A sense's part of speech rides on that sense's
`TRANSL/@notes`. There is no `W` or `M` tier: the source carries no
morphological analysis.

#### Audio

Most example sentences have a recording from the source (`AUDIO` with `url`
and `file`; `TEXT/@audio="segmented"`). The headword files have no audio. The
audio files are not in git: `download_audio_data.sh` fetches them from
FormosanBank's Hugging Face audio store (it runs
`QC/utilities/download_audio.py --corpus ILRDF_Dicts`). How recordings were
chosen, named and dropped is under "Notes and caveats".

Hugging Face allows at most 10,000 files in one folder, so the three
largest languages (Bunun, Rukai, Yami; `sharded_languages` in the repo-root
`audio_sources.json`) are stored in 16 subfolders each, `<Lang>/<Lang>/0/`
to `<Lang>/<Lang>/f/`, chosen by the first hex digit of the SHA-256 of the
file name (`name_shard` in `QC/validation/validate_hf_audio.py`). This
replaces Rukai's earlier `batch_1/` and `batch_2/` folders ("Shard big
languages by name (Recommended)", maintainer, 2026-10-18). Files the XML
references that are not yet at their Hugging Face path are listed by
`audio_upload_manifest.py` in
[CodeAndDocs/docs/audio_upload_manifest.csv](CodeAndDocs/docs/audio_upload_manifest.csv)
(59,407 rows: 33,817 new files to upload, 4.0 GB, and 25,590 Bunun, Rukai
and Yami files already on Hugging Face under the old layout, column
`hf_old_path`, which move into the subfolders by a copy on Hugging Face).

#### Background

The project began in 2007 with the systematic compilation of dictionaries for  the **16 indigenous languages**. Each dictionary took two years to complete, involving the dedication of language teachers, experts, and scholars. By 2014, all dictionaries had been completed, marking a significant milestone in the documentation of Taiwan's indigenous languages.

Recognizing the importance of sustainability, the ILRDF digitized these dictionaries and launched the **Indigenous Languages Online Dictionary** platform. This digital transformation allows the dictionaries to remain dynamic, expandable, and maintainable, becoming a vital resource for language promotion, teaching, research, and learning.

#### Features of the ILRDF Online Dictionaries

1. **Online Access and Search**
   * Users can search for words, view their definitions, listen to pronunciations, and explore examples in real-time.
2. **Downloadable Resources**
   * The platform offers downloadable content for offline learning, including:
     * Word cards
     * Full dictionary text
     * Chinese-indexed versions
3. **Interactive Learning Tools**
   * Features include:
     * **Online Quizzes:** Test your knowledge of the languages.
     * **Word Suggestions:** Contribute or recommend new words.
     * **Examples and Applications:** Practical sentences for immediate learning and use.
4. **Community Engagement**
   * Users can share feedback or discuss usage questions in the **discussion area**, fostering a collaborative environment.
   * Periodic expert consultations ensure updates and accuracy, with the final decisions on word usage returned to the respective indigenous communities
5. **API for Data Collection**
   * The ILRDF provides an **API** that facilitates streamlined data collection and integration into FormosanBank, ensuring efficient access to the full range of dictionary content.

#### Key Features of the Corpus

1. **Comprehensive Data**
   * The corpus offers a rich resource for the study of Formosan languages: example sentences with audio for most of them, plus the full headword inventory of all sixteen dictionaries. The generated statistics table (under "Statistics", below) gives the current breakdown by language.
2. **Audio Integration**
   * High-quality audio files accompany most example sentences, providing an invaluable resource for analyzing pronunciation, phonology, and spoken language contexts.
3. **Translation Availability**
   * Example sentences are translated into **Chinese**, ensuring accessibility for researchers and learners.

#### Significance

1. **Language Preservation**
   * The dictionaries support the documentation and revitalization of endangered indigenous languages, ensuring they remain a living cultural asset.
2. **Accessibility**
   * The online platform makes these resources available to a global audience, transcending geographical boundaries.
3. **Education and Research**
   * With rich examples and structured content, the dictionaries are invaluable for both language learners and researchers.

#### Acknowledgments

This project is made possible through the collaboration of native speakers, linguists, and researchers. Special thanks to the **Indigenous Languages Research and Development Foundation** ([ILRDF](https://www.ilrdf.org.tw/)) for their invaluable contributions and to the broader Formosan communities for their support and engagement.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/ILRDF_Dicts_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

the dictionary/ies corresponding to the languages that were used.

* **Amis**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 阿美語_ \[Indigenous Languages Online Dictionary: Amis language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Atayal**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 泰雅語_ \[Indigenous Languages Online Dictionary: Atayal language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Bunun**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 布農語_ \[Indigenous Languages Online Dictionary: Bunun language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Kanakanavu**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 卡那卡那富語_ \[Indigenous Languages Online Dictionary: Kanakanavu language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Kavalan**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 噶瑪蘭語_ \[Indigenous Languages Online Dictionary: Kavalan language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Paiwan**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 排灣語_ \[Indigenous Languages Online Dictionary: Paiwan language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Puyuma**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 卑南語_ \[Indigenous Languages Online Dictionary: Puyuma language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Rukai**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 魯凱語_ \[Indigenous Languages Online Dictionary: Rukai language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Saaroa**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 拉阿魯哇語_ \[Indigenous Languages Online Dictionary: Saaroa language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Saisiyat**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 賽夏語_ \[Indigenous Languages Online Dictionary: Saisiyat language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Sakizaya**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 撒奇萊雅語_ \[Indigenous Languages Online Dictionary: Sakizaya language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Seediq**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 賽德克語_ \[Indigenous Languages Online Dictionary: Seediq language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Thao**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 邵語_ \[Indigenous Languages Online Dictionary: Thao language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Truku**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 太魯閣語_ \[Indigenous Languages Online Dictionary: Truku language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Tsou**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 鄒語_ \[Indigenous Languages Online Dictionary: Tsou language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* **Yami**: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (n.d.). _原住民族語言線上辭典: 雅美語_ \[Indigenous Languages Online Dictionary: Yami language]. Retrieved 2026-05-04, from [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)

Each citation is the `citation` attribute of that language's `<TEXT>` (the
same in its sentence file and its headword file).

## License

**License:** CC BY-NC 4.0
**Rights source:** the Indigenous Languages Research and Development Foundation (ILRDF), which publishes these dictionaries under this licence; date not recorded in this repository; evidence: ask maintainer

The `@copyright` value was recorded without a version (`CC-BY-NC`) until
2026-10-16, when it was normalized to `CC BY-NC 4.0` under POL-042 (a value
that names no version is 4.0).

Every `TEXT` carries `copyright="CC BY-NC 4.0"`. See also
[CodeAndDocs/source_data/RIGHTS.md](CodeAndDocs/source_data/RIGHTS.md).

FormosanBank publishes this corpus under **CC BY-NC 4.0** (the `copyright` value of every `TEXT` element).

The online dictionary's current [copyright statement](https://e-dictionary.ilrdf.org.tw/about?id=6c987092-47c7-ef11-bd58-00155db40116) says that ILRDF-authored works may be reproduced, publicly broadcast, or publicly transmitted within a reasonable scope when the source is identified. Other protected uses require permission unless an applicable fair-use provision applies. Users should consult the current statement and the source terms before reusing this corpus.

## Notes and caveats

#### Summary

Each item is described in full in the section named in brackets.

- **1,251 sentences are no longer in ILRDF's current dictionary.** They are
  kept as FormosanBank published them from its 2024 scrape and carry an
  `S/@source` saying so. ["Sentences from the 2024 scrape — 1,251"]
- **24 `?` are left where the source lost a letter.** In Kanakanavu, Saaroa
  and Tsou the source sometimes has a literal `?` where **ʉ** was lost; 61
  were restored, but these 24 could not be confirmed and are left visible
  rather than guessed. ["Recovered `?` corruption — 61 tokens"]
- **1,438 recordings are published without a transcription** (as `AUDIO`
  directly under `TEXT`), including the 244 that FormosanBank's 2024
  publication had attached to several different sentences. ["Recordings"]
- **99,963 recordings are not published**; every one, and why, is in
  [CodeAndDocs/docs/audio_not_published.csv](CodeAndDocs/docs/audio_not_published.csv).
  ["Recordings", "Excluded content"]

The same points in brief, with one more:

* **1,251 sentences are no longer in ILRDF's current dictionary.** They are kept as FormosanBank published them in 2024 and carry an `S/@source` saying so.
* **24 `?` are left where the source lost a letter** (Kanakanavu, Saaroa and Tsou), because the intended word could not be confirmed.
* **1,438 recordings are published without a transcription**, as `AUDIO` directly under `TEXT`, with `AUDIO/@source` naming the example it belongs to.
* **13 sentences have no recording**, because every recording the source has for them is broken or could not be downloaded.

#### Ids

**Identifiers.** Sentences FormosanBank published before the rebuild keep their ids (`Amis_0` …). Sentences new in 2026 carry the source's GUID (`Amis_20a69646-e70a-f011-bd65-00155db40116`), and dictionary entries carry `d` + GUID. A record split into several `S` keeps its id on the first and adds `-opt`, `-opt3` … to the others. The matching of the 2024 sentences to the 2026 source was done once and frozen in [`main_id_ledger.csv`](CodeAndDocs/source_data/main_id_ledger.csv). Every previously published id that is no longer published, and why, is in [`old_to_new_ids.csv`](CodeAndDocs/old_to_new_ids.csv) (284 rows: 261 duplicates merged into the lowest id of their group, 4 sentences whose printed alternatives cannot be published as one sentence, 1 editor note, and 18 sentences printed twice with one recording).

Sentences FormosanBank published before the rebuild keep their ids
(`Amis_0` …); sentences new in 2026 carry the source's GUID
(`Amis_20a69646-e70a-f011-bd65-00155db40116`); dictionary entries carry
`d` + GUID. A record split into several `S` keeps its id on the first and
adds `-opt`, `-opt3` … to the others (POL-028). A sentence with several
different recordings is also split this way, one `S` per recording (see
"Recordings" below); those 15,599 added ids are listed in
[CodeAndDocs/docs/recording_split_ids.csv](CodeAndDocs/docs/recording_split_ids.csv). The matching of old sentences
to the 2026 source was done once and frozen in
[CodeAndDocs/source_data/main_id_ledger.csv](CodeAndDocs/source_data/main_id_ledger.csv);
see [CodeAndDocs/docs/id_scheme.md](CodeAndDocs/docs/id_scheme.md).

Every previously published id that is no longer published, and why, is in
[CodeAndDocs/old_to_new_ids.csv](CodeAndDocs/old_to_new_ids.csv) (284 rows):
261 duplicates merged into the lowest id of their group, 4 sentences whose
printed alternatives cannot be published as one sentence, Puyuma_888
(source repair #3), and 18 sentences printed twice with one recording
(see "One recording printed for several sentences" below).

#### Sentences from the 2024 scrape — 1,251

**Sentences from the 2024 scrape — 1,251.** 1,251 sentences FormosanBank published in 2024 are no longer in ILRDF's current dictionary. They are kept as published then (same id, original text, translation and recording) and marked with `S/@source="ILRDF online dictionary, 2024 scrape …; no longer in ILRDF's current dictionary"`. Their standard tier and phonology are regenerated like every other record's.

1,251 sentences FormosanBank published from its 2024 scrape are no longer in
ILRDF's current dictionary. They are kept as published then — same id,
original text, translation and recording — from a committed snapshot of that
XML ([CodeAndDocs/source_data/main_2024/](CodeAndDocs/source_data/main_2024/),
POL-035), and marked with `S/@source="ILRDF online dictionary, 2024 scrape …;
no longer in ILRDF's current dictionary"`. Their standard tier and phonology
are regenerated like every other record's.

| Amis | Atayal | Bunun | Kanakanavu | Kavalan | Paiwan | Puyuma | Rukai | Saaroa | Saisiyat | Sakizaya | Seediq | Thao | Truku | Tsou | Yami |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 89 | 6 | 537 | 138 | 3 | 36 | 2 | 209 | 38 | 1 | 29 | 22 | 6 | 116 | 15 |

#### Phonology and the standard tier

**Derived tiers** come from the shared FormosanBank tools: the `standard` FORM from `standardize.py`, the IPA `PHON` from `add_phonology.py`. The original tier is assumed to be written in the 2005 official orthography (Ortho113) for all sixteen languages, so both PHON tiers are generated from the same table.

Both PHON tiers are generated, never hand-edited. **The original tier is
assumed to be written in Ortho113** for all sixteen languages (maintainer,
2026-10-16), so original and standard PHON are generated from the same
Ortho113 table, with the column chosen by each file's `dialect`.

The standard tier is the original with accents removed (`standardize.py
--remove_accents`): no conversion table is applied, so the standard tier keeps
the source's spelling.

#### Changes we make to the source

Everything below is reproducible from committed code and data; nothing was edited by hand.

Everything below is reproducible from committed code and data. Nothing was
edited by hand.

#### Source-fidelity repairs — 15 records

**Source-fidelity repairs — 15 records.** The API sometimes returns material that is not Formosan text. These are corrected on the **original** tier through FormosanBank's manual-edits mechanism and listed in [`manual_edits.xml`](CodeAndDocs/manual_edits.xml), with a readable changelog beside it.

The ILRDF API sometimes returns material that is not Formosan text. 14 are
corrected on the **original** tier through the manual-edits mechanism
(POL-030), recorded in [CodeAndDocs/manual_edits.xml](CodeAndDocs/manual_edits.xml)
with a changelog in [CodeAndDocs/manual_edits.md](CodeAndDocs/manual_edits.md);
the reviewed table is
[CodeAndDocs/source_data/source_repairs.json](CodeAndDocs/source_data/source_repairs.json).

| Class | Records | Example |
|---|---:|---|
| A part-of-speech label standing in for a word | 5 | `u數詞u paapuhla…` → `ʉnʉmʉ paapuhla…` (數詞 means "numeral") |
| Chinese editorial text welded onto a sentence | 8 | `…mawtu zau.這` → `…mawtu zau.` |
| A place name welded on without its parentheses | 1 | `…muntal mzai 水裏坑.` → `…muntal mzai (水裏坑).` |
| Editor note "請刪除" ("please delete") | 1 | Puyuma_888: not published; its recording is published as untranscribed audio |

**The 數詞 repairs (Saaroa).** In five Saaroa sentences the API replaced a
word containing the numeral root `nʉm` with the part-of-speech label 數詞
("numeral"), and turned the `ʉ` on either side into `u`: `u數詞u paapuhla…`.
Four repairs undo exactly that, restoring `ʉnʉmʉ`
(`ʉnʉmʉ paapuhla ualuia laihla upatu.`, `apuaʉnʉmʉ …`, `aʉnʉmʉ …`,
`tʉnʉmʉa …`). The fifth, Saaroa_3575 `kapita數詞ia`, is read as `nʉ`:
`hlaʼalua maci kapitanʉia …` (`kapitanʉ` is a Saaroa headword and appears in
16 sentences).

#### Spaces next to punctuation at the edges of a form — 1,165 forms

**Spaces next to punctuation at the edges of a form — 1,165 forms.** The source often leaves a space before sentence-final punctuation (`tukamia .`), or next to a quotation mark or bracket at the start or end of a sentence, and a few sentences open with a stray period (`. Aiza …`). The build removes exactly that space and nothing else (`… fafahiyan ako .` → `… fafahiyan ako.`). Every changed form, before and after, is in [`edge_space_report.csv`](CodeAndDocs/docs/edge_space_report.csv).

The source often leaves a space before sentence-final punctuation
(`tukamia .`) or next to a quotation mark or bracket at the start or end of
a sentence, and a few sentences open with a stray period (`. Aiza …`).
Phonology drops punctuation, so these spaces ended up at the edge of the
PHON tier. On the original tier (the standard tier follows), the build
removes exactly that space and nothing else (maintainer, 2026-10-18:
"Revert; fix ILRDF text (Recommended)" and "Same treatment
(Recommended)"), in `CodeAndDocs/tidy_edge_spaces.py`:

| Pattern | Forms | Example |
|---|---:|---|
| space before final `.` `?` `!` | 1,136 | `… fafahiyan ako .` → `… fafahiyan ako.` |
| stray leading period | 12 | `. Aiza bunun masuaz …` → `Aiza bunun masuaz …` |
| space after an opening `"` | 7 | `" Dopohen a matayal!" …` → `"Dopohen a matayal!" …` |
| space before a closing `"` `,` `…` `-` at the end | 9 | `… mas ismut ,` → `… mas ismut,`; headword `caca -` → `caca-` |
| spaces inside a final bracket | 1 | `… a zaljum ( vava ).` → `… a zaljum (vava).` |

Every changed form, before and after, is in
[CodeAndDocs/docs/edge_space_report.csv](CodeAndDocs/docs/edge_space_report.csv)
(3 of them are headwords). No PHON value has a space at either edge.

#### Recovered `?` corruption — 61 tokens

**Recovered `?` corruption — 61 tokens.** The source has lost the letter **ʉ** in places, leaving a literal `?`. Where the intended word can be confirmed it is restored automatically; where it cannot, the `?` is left visible rather than guessed at. The repair touches only Kanakanavu, Saaroa and Tsou, and only a `?` with a Formosan letter on *both* sides, so a sentence-final question mark is never affected. The candidate word must already occur, intact, elsewhere in the same language. Of 85 candidates, **61 were repaired — every one to ʉ** — and **24 were left unrepaired**.

The source has lost the letter **ʉ** in places, leaving a literal `?`. Where
the intended word can be confirmed, it is restored automatically; where it
cannot, the `?` is left visible rather than guessed at. The repair applies
only to Kanakanavu, Saaroa and Tsou, and only to a `?` with a Formosan letter
on **both** sides. The candidate must already occur, intact, elsewhere in the
same language's snapshot. Of 85 candidates, **61 were repaired — every one to
ʉ** — and **24 were left unrepaired**.

#### Source-side alternatives

**Source-side alternatives.** The source packs alternative wordings into one record three ways: `=` ("same as"), parentheses and slashes.

* a **spelling variant** stays one record, with the other spelling carried as a variant FORM (`kindOf="original" ver="alt"`); 2,006 in the sentence files.
* a **lexical alternative** becomes separate `<S>` records, named `-opt`, `-opt3` ….
* a parenthesis is kept as written when it is annotation: Chinese, a place or person name, a Japanese loanword in Romaji, or a number. Headword notation is not always left as the source writes it: `uculru(wa)` (an attached bracket marking an optional ending) is dropped by the build, see below.
* where the reading is not clear, the record is not published as text: 620 records, every one listed in [`split_report.csv`](CodeAndDocs/docs/split_report.csv).

For 73 previously published sentences the maintainer ruled on each one; those rulings, in [`alternative_rulings.json`](CodeAndDocs/source_data/alternative_rulings.json), replace the automatic resolution.

The source packs alternative wordings into one record three ways: `=` ("same
as"), parentheses, and slashes.

- a **spelling variant** stays one record, the other spelling carried as a
  variant FORM, `kindOf="original" ver="alt"` (POL-028); `standardize.py`
  derives the matching standard variant. 2,006 in the sentence files.
- a **lexical alternative** becomes separate `<S>` records, named `-opt`,
  `-opt3` ….
- a parenthesis is kept as written when it is annotation: Chinese, a place or
  person name, a Japanese loanword in Romaji (listed in
  [CodeAndDocs/source_data/bracket_annotations.csv](CodeAndDocs/source_data/bracket_annotations.csv)),
  or a number.
- where the reading is not clear the record is not published as text; 620
  records, every one listed in
  [CodeAndDocs/docs/split_report.csv](CodeAndDocs/docs/split_report.csv).

For 73 previously published sentences the maintainer ruled on each one
(2026-10-15/16), and those rulings replace the automatic resolution:
[CodeAndDocs/source_data/alternative_rulings.json](CodeAndDocs/source_data/alternative_rulings.json).
9 are kept as printed, parentheses included (where the source prints the
alternative in both the sentence and its translation, POL-028 allows this for
ILRDF_Dicts); 35 lose the parenthesised alternative; 7 become two sentences
with the same translation; 1 becomes two sentences with their own
translations; 3 keep one sentence with a `ver="alt"` variant; 2 are published
without a translation; 4 are not published as text; and 12 Thao records are
resolved as listed there.

**Recordings of alternatives.** When the source prints alternatives in one
item, its recording is not attached to any of the resulting sentences: it is
published as untranscribed audio, an `AUDIO` that is a direct child of
`TEXT`, with `AUDIO/@source` naming the example it belongs to (maintainer
ruling 2026-10-16, ILRDF only). 486 recordings are published this way;
with the 708 replaced 2024 recordings and the 244 recordings printed for
several sentences (below), 1,438 untranscribed recordings in all.

**Headwords with an attached bracket.** Headword notation such as
`uculru(wa)` (an attached bracket marking an optional ending) is not left as
the source writes it: the build cannot classify the bracket, so the headword
is not published. `uculru(wa)` (Rukai) is listed as `dropped` in
[CodeAndDocs/docs/split_report.csv](CodeAndDocs/docs/split_report.csv), and
so is `aono(mamcino)`.

#### Recordings

**Recordings.** Every recording was fingerprinted once and the result frozen, so the build never downloads anything.

* **One `S` per distinct recording; identical copies kept once.** The same sentence is often printed under several headwords, each copy with its own recording. Byte-identical copies are published once (98,529 copies). A sentence with *k* different recordings becomes *k* `S` with the same text and translations (15,599 added `S`).
* **FormosanBank's 2024 recording first.** Where the 2024 recording is byte-identical to a 2026 one, the file keeps its existing name. Where the 2026 source has a different usable recording, the 2026 one goes on the sentence under a new file name, and the 2024 recording is kept without a transcription (708 recordings).
* **File types are kept.** 2,162 recordings are WebM (`.webm`) and 16 MP4 (`.mp4`); they are not converted.
* **Yami: the village is in the file name.** The source records most Yami sentences in three villages. They are published as three `S` (朗島 first, then 野銀, then 漁人), with files named `<id>_<village>.<ext>`, e.g. `Yami_4596_野銀.mp3`.
* **Broken recordings are dropped.** 157 files from the 2026 source are empty, and 3 Paiwan files could not be downloaded. Where the sentence has another working recording, that one is used; 13 sentences are left with no recording.
* **One recording printed for several sentences.** In 285 cases the 2024 publication attached one recording to two to four different sentences. Where they were really one sentence printed twice (18 cases), they are merged into one `S`, the other reading kept as a variant. In the other 267 cases no member keeps the recording; the 244 that the 2026 source no longer has are published once without a transcription.
* **Recordings of alternatives.** When the source prints alternatives in one item, its recording is not attached to any of the resulting sentences; it is published without a transcription (486 recordings).

Every recording that is not published, and why, is in [`audio_not_published.csv`](CodeAndDocs/docs/audio_not_published.csv) (99,963 rows, 98,534 of them identical copies).

Every recording was fingerprinted once (SHA-256 and real file type, read from
the file's first bytes) and the result is frozen in
[CodeAndDocs/source_data/audio_fingerprints.tsv](CodeAndDocs/source_data/audio_fingerprints.tsv);
the build never downloads anything. The rules (maintainer rulings
2026-10-17; code in `CodeAndDocs/audio_recordings.py`):

- **One `S` per distinct recording; identical copies kept once.** The same
  sentence is often printed under several headwords, each copy with its own
  recording; byte-identical copies are published once (98,529 copies). A
  sentence with *k* different recordings becomes *k* `S` with the same text
  and translations: the first keeps the id, the others take `-opt`, `-opt3`
  … (15,599 added `S`: 8,808 `-opt`, 6,326 `-opt3`, 465 `-opt4` or higher).
- **Main's recording first.** Where FormosanBank's 2024 recording is
  byte-identical to a 2026 one, the file keeps its existing name
  (`<Language>_<n>.mp3`, with its `start`/`end`) and the `AUDIO` carries the
  2026 source URL (maintainer, 2026-10-18: "Use the 2026 URL"). Where the
  2026 source has a different usable recording, the 2026 one goes on the
  `S` under a new file name, and the 2024 recording is kept as untranscribed
  audio (maintainer, 2026-10-18: "Give replacements new names" and "add the
  recordings as untranscribed audio"): 708 recordings, with
  `AUDIO/@source` "ILRDF example <id>; FormosanBank's 2024 recording,
  replaced by a different recording in the 2026 source" (5 more were
  byte-identical copies of those and are kept once). Where the 2026 source
  has no usable recording, main's is kept. For
  Kanakanavu_2310 and Kanakanavu_5468 both are published (main's on the main
  id, the 2026 one on `-opt`; [source_data/audio_rulings.json](CodeAndDocs/source_data/audio_rulings.json)).
- **File names.** A 2026 recording is named after its `S`
  (`Bunun_1995-opt.mp3`), with the extension of its real type: 2,162 are
  WebM (`.webm`) and 16 MP4 (`.mp4`); they are not converted. A name that a
  2024 file with different content already has is never reused: the new
  recording takes `_2` (`Amis_137_2.mp3`), as the Yami same-village names
  do.
- **Yami: the village is in the file name.** The source records most Yami
  sentences in three villages. They are published as three `S`, 朗島 first
  (it keeps the id; main's recording is the 朗島 one), then 野銀, then 漁人,
  with files `<id>_<village>.<ext>` (`Yami_4596_野銀.mp3` on `Yami_4596-opt`).
  Where one sentence has two *different* recordings from the same village
  (267 files), the second is named `<id>_<village>_2.<ext>`; Yami recordings
  with no village in the source (652 files, 644 sentences) are named after
  their `S`, like the other languages (both "OK as built", maintainer,
  2026-10-18).
- **Broken recordings are dropped.** 157 2026 files are empty (all zero
  bytes, or no recognisable audio header) and 3 Paiwan files could not be
  downloaded. Where the sentence has another working recording (2026 or
  main's) that one is used; **13 sentences are left with no recording**
  (Paiwan 1, Puyuma 1, Saaroa 5, Tsou 5, Yami 1).
- **Recordings dropped by ruling.** Kanakanavu_2270, Saisiyat_1174,
  Saisiyat_4707, Saisiyat_5198 and Tsou_2810 are published with the 2026
  text and no recording ("Use only 2026 version. Drop the audio.",
  maintainer, 2026-10-16;
  [source_data/audio_rulings.json](CodeAndDocs/source_data/audio_rulings.json)).

**One recording printed for several sentences.** In 285 cases
FormosanBank's 2024 publication attached one recording (byte-identical
files, the same 2024 URL and segment) to two to four different sentences
(validate_xml.py V162). Maintainer ruling 2026-10-18 ("2026 source decides;
merge the 18"), frozen with every member in
[source_data/shared_clips.json](CodeAndDocs/source_data/shared_clips.json):

| Case | Groups | What is published |
|---|---:|---|
| near-identical or same wording (one sentence printed twice) | 18 | merged into the first id, the other reading as a `ver="alt"` FORM, translations merged, recording kept; the 18 retired ids are in `old_to_new_ids.csv` |
| different sentences; the 2026 source attaches the recording to another sentence, which already carries it | 23 | no member keeps it |
| different sentences; the 2026 source has no copy of the recording | 244 | no member keeps it; published once as untranscribed audio |

The 2026 source attaches none of these recordings to any of their members.
Where a removed recording was a sentence's second recording, its `-opt`
`S` is no longer published (10 ids; one, Kanakanavu_4483, keeps its other
recording on the base id).

Every recording that is not published, and why, is listed in
[CodeAndDocs/docs/audio_not_published.csv](CodeAndDocs/docs/audio_not_published.csv)
(99,963 rows: 98,534 identical copies, 708 2024 recordings moved to
untranscribed audio, 555 removed from sentences that shared one recording,
157 broken, 3 unreachable, 5 dropped by ruling, and 1 note where main's
recording replaced broken 2026 ones).

#### Excluded content

**Excluded content.** 820 all-zero audio ids found before the 2026 fingerprinting, two confirmed transcript mismatches, both uses of 40 audio ids assigned to different forms in different languages, three Kanakanavu lesson numbers that are not translations, and one Saisiyat headword sense that is an editor note.

- 820 all-zero audio ids (found before the 2026 fingerprinting; the 157
  found by it are under "Recordings" above), two confirmed transcript mismatches, and both uses
  of 40 audio ids assigned to different forms in different languages
  ([source_data/audio_exclusions.json](CodeAndDocs/source_data/audio_exclusions.json)).
- Three Kanakanavu lesson numbers that are not translations, and one Saisiyat
  headword sense that is an editor note (`不小心按到，請刪除！…`)
  ([source_data/source_content_exclusions.json](CodeAndDocs/source_data/source_content_exclusions.json)).

## Reproduction and processing

### How to reproduce

The corpus is rebuilt from committed snapshots of the ILRDF API, with no network access and no environment variables:

```bash
bash Corpora/ILRDF_Dicts/CodeAndDocs/generate_xml.sh
```

This rebuilds everything from committed files and needs no network access and
no environment variables (`PYTHON` optionally selects the interpreter). The
shared QC tools come from the FormosanBank checkout the script sits in. The
FormosanBank commit the published XML was built against is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).
`CodeAndDocs/validate.sh` runs the published-id audit and the corpus tests.

What the build needs: a Python with the repository's `requirements.txt`
installed (the corpus scripts use `lxml` and `rapidfuzz`). It reads only
files under `Corpora/ILRDF_Dicts/CodeAndDocs/` and the shared tools and
`Orthographies/Ortho113` of the same checkout; it writes the 32 XML files under
`XML/`, `manual_edits.xml/.md`, `old_to_new_ids.csv`,
`docs/split_report.csv`, `docs/audio_not_published.csv`,
`docs/recording_split_ids.csv`, `docs/edge_space_report.csv` and
`provenance.json`, and prints a digest of the XML (see
[CodeAndDocs/docs/reproduction.md](CodeAndDocs/docs/reproduction.md)).

To check the result:

```bash
bash Corpora/ILRDF_Dicts/CodeAndDocs/validate.sh
```

It runs `generate_xml.py audit` (every id in the XML must be declared in
`source_data/published_ids.csv`, no declared id may silently disappear, and
no id may come to point at different source GUIDs) and then the corpus's own
tests (`python -m pytest CodeAndDocs/tests`).

The audio is not needed for the build. To fetch it, run
`Corpora/ILRDF_Dicts/download_audio_data.sh`. The corpus XML, retained processing materials, and audio download script are available in FormosanBank.

To add phonology to these files yourself, from the repository root:

```bash
python QC/utilities/standardize.py --corpora_path Corpora/ILRDF_Dicts/XML \
    --remove_accents --ortho-path Orthographies/Ortho113
python QC/utilities/add_phonology.py --corpora_path Corpora/ILRDF_Dicts/XML \
    --orthography Ortho113
```

Re-scraping the API is a separate, deliberate step ([`docs/reproduction.md`](CodeAndDocs/docs/reproduction.md)), because it can add, remove or reword source records. The FormosanBank commit the published XML was built against is recorded in [`provenance.json`](CodeAndDocs/provenance.json).

**Full regeneration** re-scrapes the ILRDF API first; see
[CodeAndDocs/docs/reproduction.md](CodeAndDocs/docs/reproduction.md).

**POL-047 deviation:** besides the canonical steps, the build runs five
corpus-local steps — `generate_dictionary.py` (headword files),
`build_manual_edits.py` (renders `manual_edits.xml` from the reviewed repair
table), `split_alternatives.py` (source-side alternatives, after the
manual edits and before `clean_xml.py`, because the repairs must match the
unsplit text), `one_recording_per_s.py` (after the split, so that only
sentences that keep their recordings are split by recording) and
`tidy_edge_spaces.py` (after `clean_xml.py`, which turns full-width
`？！．` into ASCII and so exposes some of these spaces).

The steps, in order:

1. `generate_xml.py generate` — sentences from the snapshots; main's ids from
   the frozen ledger; main's withdrawn sentences from the 2024 snapshot;
   recordings (below); dialects from main.
2. `generate_dictionary.py` — headword entries.
3. `build_manual_edits.py`, then the shared `QC/cleaning/apply_manual_edits.py`.
4. `split_alternatives.py --apply`.
5. `one_recording_per_s.py` — one `S` per distinct recording.
6. `QC/cleaning/clean_xml.py`.
7. `tidy_edge_spaces.py` — spaces next to punctuation at the edges of a form.
8. `QC/utilities/standardize.py --remove_accents --ortho-path Orthographies/Ortho113`.
9. `QC/utilities/add_phonology.py --orthography Ortho113`.

`generate_xml.sh` itself prints these as ten steps ("1/10" to "10/10"),
because it counts rendering `manual_edits.xml` and applying it separately.
The next section follows the script's ten steps.

### What each step does

Before step 1, `generate_xml.sh` compares the FormosanBank commit it is run
from with the one recorded in `provenance.json` and prints a note if they
differ; nothing stops on it (POL-052). It makes an empty temporary folder for
step 7 and deletes it on exit. Every corpus script is run from
`CodeAndDocs/`.

#### Step 1/10: `generate_xml.py generate` (sentence files)

- Reads `source_data/source_manifest.json` and, for each of the 16 languages,
  its gzipped API snapshot under `source_data/snapshots/`; it stops if the
  SHA-256 of the compressed or uncompressed snapshot differs from the
  manifest.
- Loads the exclusion and override tables: `audio_exclusions.json`
  (recordings never used), `source_content_exclusions.json` (translations
  that are not translations) and `translation_language_overrides.json`.
- Walks every published headword of the snapshot (one with a frequency above
  0 or a source) and every example sentence under it. Each sentence's text is
  Unicode-normalized (NFC, zero-width spaces removed), curly and CJK quotation
  marks (`‘’“”「」『』《》`) become straight `'` and `"`, and runs of spaces
  are collapsed. A sentence with no letter or digit, or whose text is a
  placeholder (`-`, `---`), is skipped. A sentence whose translation is a
  placeholder is set aside and published only if the frozen id ledger claims
  it.
- In Kanakanavu, Saaroa and Tsou, a `?` between two letters is replaced only
  when the repaired word (with `ʉ`, or `ɨ`) already occurs intact in that
  language's snapshot; the most frequent attested candidate wins.
- Sentences with identical text are merged into one record, which takes the
  lowest of their source GUIDs as its id. A translation is tagged `zho`,
  unless an override names another language or the "translation" is the
  sentence itself (then the language's own ISO code). Recordings whose storage
  id is in `audio_exclusions.json` are left out.
- Maps the records onto FormosanBank's 2024 publication: reads the
  hash-checked 2024 snapshot (`source_data/main_2024/`) and
  `source_data/main_id_ledger.csv` (it stops unless the ledger covers every
  2024 id exactly). A record the ledger matches keeps the 2024 id; 2024
  duplicates merged into it add their distinct translations; a ledger row
  `withdrawn` is published from the 2024 snapshot with the `S/@source` above.
- Chooses each sentence's recordings by the rules in `audio_recordings.py`
  (see "Recordings" above), using the frozen `audio_fingerprints.tsv` and
  `audio_rulings.json`. A 2024 recording replaced by a different 2026 one
  becomes untranscribed audio.
- Leaves out the record `source_repairs.json` marks `withdraw` (Puyuma_888),
  publishing its recording as untranscribed audio, and applies
  `shared_clips.json` (merge the 18 pairs; take the shared recording off the
  other groups' sentences, and publish 244 of them once as untranscribed
  audio).
- Writes `XML/<Language>/<Language>.xml`: `TEXT` with `id`
  (`ILRDF_Dicts_<Language>`), `xml:lang`, `source`, `audio="segmented"`,
  `dialect` and `glottocode` from the 2024 publication (else
  `dialect="unknown"`), `copyright`, `citation` and `BibTeX_citation`; then
  the untranscribed `AUDIO`; then one `S` per record, sorted by text, holding
  the original `FORM`, any `ver="alt"` FORMs, the `TRANSL`s (a second one in
  the same language gets `ver="alt"`) and the `AUDIO`s.
- After all 16 languages, writes `old_to_new_ids.csv` (adding a row for each
  ruled sentence that publishes nothing) and `docs/audio_not_published.csv`.
  It stops if an override or exclusion was never used, or if one recording
  URL belongs to sentences with different texts.

#### Step 2/10: `generate_dictionary.py` (headword files)

For each language, takes every published headword of the snapshot, normalized
as above, merges headwords with identical text (id `<Language>_d` + the lowest
word GUID), and gives it one `TRANSL xml:lang="zho"` per distinct sense
(the source's Chinese explanation; empty or placeholder senses skipped).
Senses after the first get `ver="alt"`; the source's parts of speech, joined
with `; `, go in that sense's `TRANSL/@notes`. Headword senses listed in
`source_content_exclusions.json` are left out (it stops if one is never used),
and a headword left with no sense is not published. The `TEXT` attributes are
the sentence file's, with `_dictionary` added to the `id`. Writes
`XML/<Language>/<Language>_dictionary.xml`.

#### Step 3/10: `build_manual_edits.py --xml-dir XML`

Reads `source_data/source_repairs.json`, ignores the `withdraw` repair
(handled in step 1), finds every `S` whose original FORM is exactly a repair's
"before" text, and writes `manual_edits.xml` with the "after" text. It exits
with an error if a repair finds no target. It runs before the split (step 5)
because the split rewrites the text a repair matches on (one Thao record is
both repaired and split).

#### Step 4/10: `QC/cleaning/apply_manual_edits.py --corpora_path XML`

The shared tool re-applies the records in `manual_edits.xml` to the original
tier (POL-030) and regenerates the changelog `manual_edits.md`.

#### Step 5/10: `split_alternatives.py --apply --xml-dir XML --report docs/split_report.csv`

Runs over the sentence and headword files. A sentence with `S/@source` (a
2024-only sentence) is left untouched. A sentence named in
`source_data/alternative_rulings.json` is replaced by exactly the `S`
records the ruling lists (it stops if a ruling finds no record). Every other
original FORM goes through the automatic resolution:

1. `=`: an inline `(= x)` or a trailing `= x` yields two readings.
2. A record holding several sentences is cut into fragments: numbered
   examples `1.` `2.`…, a slash after sentence-final punctuation, or
   `(a) / (b)`.
3. In each fragment, every slash site is classified. Options with different
   word counts are a **lexical alternative** (only if the longer option
   shares a word, at Levenshtein similarity 0.60 or more, with the shorter
   one); options with the same word count and similarity 0.50 or more are a
   **spelling variant**; anything else is not confident, and the fragment is
   dropped. More than 4 lexical readings also drops the fragment.
4. A bracket is kept as written if it holds Chinese or Japanese characters,
   a word listed in `source_data/bracket_annotations.csv`, a capitalized
   word (a proper noun) or a number; otherwise it is classified like a slash
   option against the word before it, or the fragment is dropped.

A headword differs in one respect: a slash between whole headwords is two
entries (or one entry with a spelling variant), never "not confident", and a
spaced trailing bracket that is not annotation is read as a second form.

Lexical alternatives become separate `S` (the first keeps the id, then `-opt`,
`-opt3` …); spelling variants become `FORM kindOf="original" ver="alt"`.
A rewritten original FORM gets `notes="source: <the source text>"`. Whenever
a record is rewritten, split, deleted, or replaced by a ruling that does not
keep its audio, its `AUDIO` moves to the top of `TEXT` as untranscribed
audio, with `AUDIO/@source` "ILRDF example <id>; its source text prints
alternatives". A record with no readable fragment is deleted. Every rewritten,
dropped and ruled record is written to `docs/split_report.csv`.

#### Step 6/10: `one_recording_per_s.py --xml-dir XML --report docs/recording_split_ids.csv`

In the sentence files only, replaces each `S` that still holds more than one
`AUDIO` by one copy per recording (same FORMs and TRANSLs, one `AUDIO` each),
ids `<id>`, `<id>-opt`, `<id>-opt3` …; it stops if such an id already exists.
The added ids are written to `docs/recording_split_ids.csv`.

#### Step 7/10: `QC/cleaning/clean_xml.py --corpora_path XML --reference_dir <empty folder>`

The shared cleaner: replaces non-breaking spaces, NFC-normalizes, unescapes
HTML entities and normalizes punctuation and spacing in every non-standard
FORM (this is where full-width `？！．` become ASCII), and cleans the
`TRANSL` text. Because `--reference_dir` points at an empty folder, no
`attestation.txt` is found, so the cleaner's attestation-based apostrophe
(glottal) correction of the original tier does not run for this corpus. Its
warnings file is deleted at the end of the build.

#### Step 8/10: `tidy_edge_spaces.py --xml-dir XML --report docs/edge_space_report.csv`

On every original FORM (base and `ver="alt"`, sentence and headword files)
applies, in this order: remove a stray leading period; remove the space after
opening punctuation at the start; remove the spaces inside a bracket group
that ends the text; remove the space before sentence-final `.` `?` `!`;
remove the space before closing punctuation at the end. Writes every changed
form, with the rules that fired, to `docs/edge_space_report.csv`.

#### Step 9/10: `QC/utilities/standardize.py --corpora_path XML --remove_accents --ortho-path Orthographies/Ortho113`

Creates the `standard` FORM of every sentence and headword by copying the
original (variant FORMs get matching standard variants), removes null units
from `S`, and strips accents except those the language's reference
orthography attests. No letter conversion is applied. `--ortho-path` is used
only for the check of whether a hyphen is a letter. Its warnings file is
deleted at the end of the build.

#### Step 10/10: `QC/utilities/add_phonology.py --corpora_path XML --orthography Ortho113`

Generates the original and standard `PHON` from the Ortho113 tables, the IPA
column chosen by each file's `dialect`.

#### After step 10

Deletes `cleaner_warnings.csv`, `html_entities.log` and
`standardize_warnings.csv` from `XML/` (POL-033: review output, not corpus
data), writes `provenance.json` with the current FormosanBank commit, and
prints the commit and the XML digest.

#### Files in `CodeAndDocs/`

| | |
|---|---|
| `generate_xml.sh` | the reproduction entry point (build only) |
| `validate.sh` | id audit + corpus tests |
| `generate_xml.py` | sentences; also the `ledger` and `audit` modes |
| `generate_dictionary.py` | headword entries |
| `split_alternatives.py` | source-side alternatives and the per-sentence rulings |
| `build_manual_edits.py` | renders `manual_edits.xml` from the repair table |
| `match_main_ids.py` | one-off: matched main's sentences to the 2026 source; wrote `main_id_ledger.csv` |
| `snapshot_main_xml.py` | one-off: wrote the POL-035 snapshot in `source_data/main_2024/` |
| `audio_recordings.py` | which recordings each sentence carries, and their file names |
| `one_recording_per_s.py` | build step: one `S` per distinct recording |
| `tidy_edge_spaces.py` | build step: the space next to punctuation at the start/end of an original FORM |
| `freeze_audio_fingerprints.py` | one-off: wrote `source_data/audio_fingerprints.tsv` from the fingerprinting run |
| `audio_upload_manifest.py` | lists referenced audio not yet at its Hugging Face path (`docs/audio_upload_manifest.csv`: new files, and files that only move into the sharded folders), offline, from the frozen listing; uploads nothing |
| `refresh_source.py` / `.sh` | re-scrape the API into snapshots (not part of reproduction) |
| `tests/` | `python -m pytest CodeAndDocs/tests` |
