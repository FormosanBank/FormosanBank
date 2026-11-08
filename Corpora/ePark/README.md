# ePark Data

ePark (族語E樂園) is the online language-learning platform for the Indigenous
languages of Taiwan, built by the Indigenous Languages Research and Development
Foundation (ILRDF). This corpus holds its learning materials, sentences, word lists
and short texts, with Mandarin (and for some subcorpora English) translations and audio,
in 42 dialects of 16 Formosan languages.

This repository contains code and data for processing and structuring the ePark dataset into the [FormosanBank XML format](https://ai4commsci.gitbook.io/formosanbank/the-bank-architecture/formosanbank-xml-format). The dataset includes various Formosan dialects and is organized to assist in linguistic research and language preservation.

## Languages and dialects

The published XML has 436 files: one file per dialect in each of 11 subcorpora
(42 files in each of 10 subcorpora, and 16 in `hui_ben_ping_tai_picture_book_platform`,
which covers one dialect of each language). Files sit at
`XML/<subcorpus>/<Language>/<Dialect>_<Language>.xml`, or
`XML/<subcorpus>/<Language>/<Language>.xml` for languages with a single dialect.
Every `<TEXT>` carries `xml:lang` (ISO 639-3) and a `dialect` attribute:

| Language | `xml:lang` | `dialect` values |
| --- | --- | --- |
| Amis | `ami` | Coastal, Hengchun, Malan, Southern, Xiuguluan |
| Atayal | `tay` | FourSeasons, Sekolik, Wanda, Wenshui, YilanZeaol, Zeaol |
| Bunun | `bnn` | Junqun, Kaqun, Luanqun, Tanqun, Zhuoqun |
| Kanakanavu | `xnb` | Kanakanavu |
| Kavalan | `ckv` | Kavalan |
| Paiwan | `pwn` | Central, Eastern, Northern, Southern |
| Puyuma | `pyu` | Jianhe, Nanwang, Xiqun, Zhiben |
| Rukai | `dru` | Dawu, Dona, Eastern, Maolin, Wanshan, Wutai |
| Saaroa | `sxr` | Saaroa |
| Saisiyat | `xsy` | Saisiyat |
| Sakizaya | `szy` | Sakizaya |
| Seediq | `trv` | DeluValley, Duda, Tegudaya |
| Thao | `ssf` | Thao |
| Truku | `trv` | Truku |
| Tsou | `tsu` | Tsou |
| Yami | `tao` | Yami |

Seediq and Truku share the ISO code `trv`; `dialect="Truku"` marks the Truku files,
and the other `trv` dialects are Seediq. For single-dialect languages the `dialect`
value is the language name. The dialect names come from the numbered source files
through [CodeAndDocs/dialects.csv](CodeAndDocs/dialects.csv).

## Source

#### Overview

[The ePark corpus](https://web.klokah.tw/) is a comprehensive and interactive resource for the preservation, learning, and revitalization of Indigenous languages of Taiwan. Developed by the Indigenous Languages Research and Development Foundation ([ILRDF](https://www.ilrdf.org.tw/)), this digital platform caters to a wide audience, including preschoolers, students, adults, and language teachers, with resources and tools designed to support various learning levels and linguistic goals. The corpus is available in all recognized 42 official dialects across the 16 different Formosan languages. The corpus is invaluable for documenting and preserving linguistic diversity, and it includes text, audio recordings, and translations, making it a comprehensive resource for research, education, and language revitalization.

Visit the ePark corpus online platform at [https://web.klokah.tw/](https://web.klokah.tw/).

Please note that ePark is a collection of educational material that is split into topics. The Final_XML folder will have subfolders and their names would start with the ePark version (e.g. ep1) followed by the topic name in Chinese (e.g. 九階教材). These topics could be something like "9th Period Teaching Materials" or "Cultural Topics." Unless you are interested in differentiating between the specific type of the educational materials in your research, the topic names shouldn't be relevant.

In the published `XML/` folder the topics (subcorpora) carry romanized names:
`hui_ben_ping_tai_picture_book_platform`, `jiu_jie_jiao_cai_nine_level_materials`,
`ju_xing_pian_gao_zhong_sentence_patterns_senior_high`,
`ju_xing_pian_guo_zhong_sentence_patterns_junior_high`,
`qing_jing_zu_yu_contextual_indigenous_language`,
`sheng_huo_hui_hua_pian_daily_conversation`, `tu_hua_gu_shi_pian_picture_story`,
`wen_hua_pian_cultural_section`, `xue_xi_ci_biao_learning_vocabulary`,
`yue_du_shu_xie_pian_reading_writing` and `zu_yu_duan_wen_indigenous_language_essays`.

Data was originally received in three packages, here named ePark 1, 2, and 3. This has no significance outside how it was mailed to us. But based on what was in which archive, the code varies a little.

#### Acknowledgments

The ePark corpus was developed through collaboration between ILRDF, educators, linguists, and Indigenous communities. Without the tremendous effort and collaborations of these entities, it wouldn't have been possible to have such a valuable resource in FormosanBank.

#### Downloading published audio

Most sentences (and, in `jiu_jie_jiao_cai_nine_level_materials`, many words) have
an `AUDIO` element. To download the published audio, from the FormosanBank repository root, run:

```bash
Corpora/ePark/download_audio_data.sh
```

This downloads the pinned public audio archives from Hugging Face. The XML
`AUDIO/@url` values are source references and are not the bulk-download path.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/ePark_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

* Indigenous Languages Research and Development Foundation. (2020). _族語E樂園_. https://web.klokah.tw/

## License

**License:** CC BY-NC-SA 4.0
**Rights source:** the ePark source site, which publishes these materials under this licence; date not recorded in this repository; evidence: ask maintainer

The content of the ePark corpus is released under the Creative Commons CC BY-NC-SA 4.0 license. Further information is available at [https://web.klokah.tw/creativeCommons/](https://web.klokah.tw/creativeCommons/).

#### License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

The `@copyright` value was recorded without a version (`CC-BY-NC-SA`) until
2026-10-16, when it was normalized to `CC BY-NC-SA 4.0` under POL-042 (a value
that names no version is 4.0).

## Notes and caveats

- There are some cases where the audio does not entirely match the text. For instance, the text describes a conversation, and the speaker only reads what is said. So `Pawang, "iyat bbengan pazih pi?"` gets rendered as `iyat bbengan pazih pi?`. These do not seem to be very common, so they have not been dealt with.

- The sound files corresponding to individual words in `jiu_jie_jiao_cai_nine_level_materials` are iffy. The original datasource had some errors in it. We cleaned it up quite a bit, but it is likely some inaccuracies remain. Use with caution.

- The corpus appears to use the standard orthography ("Ortho113" in FormosanBank nomenclature), with some exceptions:

  * Ortho113 specifies that only the Nanshi dialect uses `u`, while the other dialects use `o`. However, there are a fair number of `o`s and `u`s throughout the dialect, irrespective of dialect. The `standard` tier normalizes these to match the standard orthography. For the IPA transcriptions of the `original` tier, we recognize either `o` or `u` as referring to the same phoneme.
  * Different subcorpora appear to use different orthographies; the determination
    for each subcorpus is listed under step 8 of "What each step does" below.

- The ePark source frequently runs a word straight into a following parenthetical
  (e.g. `manokos(manakboz)`). A space is added in sentences without word segmentation,
  but in word-segmented sentences (all in `jiu_jie_jiao_cai_nine_level_materials`)
  the parenthetical is left attached on purpose (step 10 below).

- Some `TEXT` elements carry an empty `glottocode=""` attribute: `add_dialects.py`
  writes the `glottocode` column of `dialects.csv` even when it is blank (step 4 below).

- Reproduction is incomplete. The XML cannot be fully rebuilt from this folder
  alone: there is no single build script, some steps were done by hand, the
  source audio for the sentence-pattern subcorpora was not retained, and some
  properties of the published XML are produced by no script here (listed at the
  end of "What each step does").

## Reproduction and processing

### How to reproduce

ePark predates POL-047: it has no `CodeAndDocs/generate_xml.sh` (it is listed in
`generate_xml_pending.txt`) and no `CodeAndDocs/provenance.json` (it is listed in
`provenance_pending.txt`). The build is the sequence of manual steps below, run
by hand in the order given under "What each step does".

The scripts and the received source data (`ePark_1/`, `ePark_2/`, `ePark_3/`) are
in [CodeAndDocs/](CodeAndDocs/). Run the scripts from inside `CodeAndDocs/`:
several open relative paths (`dialects.csv`, `Final_XML`, `Final_audio`) and
`update_xml_ids.py` only accepts paths that begin with `Final_XML`.

#### Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/FormosanBank/Formosan-ePark
   cd ePark
   ```

   (That is the corpus's original development repository; the same scripts are
   now in `CodeAndDocs/` of this folder.)

2. Set up a virtual environment (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   `requirements.txt` lists only `requests` and `tqdm`; several scripts also
   import `lxml`, which the FormosanBank `.venv` provides. The shared steps need
   a FormosanBank checkout (`QC/`, `Orthographies/`). The audio steps need `sox`
   and `ffmpeg`.

#### Project Structure

- **ePark_1**, **ePark_2**, **ePark_3**: Directories containing the source data files from the ePark dataset, organized by different parts. eParks 2 and 3 contain multiple topics. Data in the different ePark folders are structured differently, and so the code is in this repo is catered to deal with these different structures to process the code.
- **XML**: Canonical published data in FormosanBank XML format. The older build scripts use `Final_XML` as their local output directory before the result is ported here.
- **dialects.csv**: A mapping file between numerical codes and the corresponding Formosan dialects used in the ePark dataset.
- **ePark1and2.py**: Script to process and convert the data in `ePark_1` and `ePark_2` directories into the FormosanBank XML format.
- **ePark3.py**: Script to process and convert the data in the `ePark_3` directory into the FormosanBank XML format.
- **failed_audio.csv**: A record of audio files that could not be downloaded during the data collection process. There is a failed_audio.csv file in each of the ePark topics in the FinalXML Folder
- **requirements.txt**: Lists the Python libraries required to run the processing scripts.
- **add_dialects**: script to add the dialect information to the XML files
- **update_audio.py**: script to update the XML files and remove the <AUDIO> tags associated with audio files that weren't downloaded successfully
- **update_xml_ids.py**: update the id attribute in the <TEXT> tags in XML files to ensure the ids are unique
- **learning_vocabulary_audio_urls.py**: normalizes the learning-vocabulary provider's former audio route during generation and reproducibly migrates published XML links.

Other files in `CodeAndDocs/` that no step below runs: `check_word_count_mismatches.py`
and `fix_word_segmentation.py` (find and fix sentences whose `W` count does not
match their word count), `check_missing_symlinks.py` and `check_missing_audio.sh`
(diagnostics for missing audio), `convert_mp3_to_wav_efficient.sh` (an alternative
to `convert_mp3_to_wav_fast.sh`), and the logs/reports `conversion.log` and
`missing_audio_files.txt`.

#### Output Explaination

All the output will be in the Final_XML folder. in the folder, there will be subfolder, coming from different ePark data. Each subfolder will start with ep[ver] followed by the topic name. in each folder, there will be a folder for each of the languages, and inside each of these folders, an XML file for each dialect and an audio folder for the audio files associated with the XML files.

(The scripts write audio to a parallel `Final_audio/` tree, at
`Final_audio/<topic>/<Language>/<Dialect>_<Language>/`.)

### What each step does

#### Usage

The steps in the order they were run. Paths are relative to `CodeAndDocs/`;
`../FormosanBank` and `path/to/FormosanBankRepo` stand for a FormosanBank checkout.

#### 1. Process ePark 1 and 2 Data

Run `ePark1and2.py` to process the source data in `ePark_1` and `ePark_2` directories:
```bash
python ePark1and2.py
```

**_Output_**
The processed data in XML format will be saved in the `Final_XML` directory.

The received learning-vocabulary CSVs retain the provider's historical
`ilrdc.tw/tow/2022` URLs as source evidence. `ePark1and2.py` normalizes those
values to the current `web.klokah.tw/vocabulary` route when it builds XML, so
the raw snapshot remains unchanged while regenerated XML stays usable.

For each topic folder it reads every CSV whose name starts with a number, looks
the number up in `dialects.csv` to get the dialect and language, and writes
`Final_XML/ep<1|2>_<topic>/<Language>/<Dialect>_<Language>.xml`. Each row becomes an
`S` with an original `FORM`, a `zho` `TRANSL` (and an `eng` `TRANSL` when the row has
more than three columns) and an `AUDIO` element with the file name and source URL.
In ePark 1, rows whose audio file name contains `C` are words of the preceding
sentence and become `W` elements inside it. It downloads each audio file into
`Final_audio/` (500 threads), skipping files already present, and appends each
failed download to `failed_audio.csv` in the topic folder.

#### 2. Process ePark 3 Data

Run `ePark3.py` to process the source data in the `ePark_3` directory:

```bash
python ePark3.py
```

**_Output_**
The processed data in XML format will be saved in the `Final_XML` directory.

Some ePark picture-book records are illustration-only pages: the source row has an
ID and page order, but no Formosan text (the Chinese translation is blank or a
placeholder such as `(無文字)`). `ePark3.py` skips these rows so they do not become empty `<S />` elements in `Final_XML`. Skipped rows are recorded in `skipped_blank_rows.csv` in the generated topic directory.

`main()` processes four ePark 3 topics: 句型篇國中 and 句型篇高中 (the
sentence-pattern subcorpora, read from the source XML files and with audio copied
from the source `sound/` folder), and 圖畫故事篇 and 繪本平台 (read from CSV, with
audio downloaded from `https://web.klokah.tw/text/sound/`). Topics 4 to 8 are not
generated here: the code comment says their published subcorpora come from the
equivalent ePark 2 topics, and the ePark 3 source for them was not retained.
`clean_text()` normalizes whitespace and sentence-punctuation spacing, and strips
the instructional boilerplate 如果會話只有兩句本欄位請勿更動 from translations.
Failed downloads are written to `failed_audio_download.csv`, and an `S` whose audio
failed to download gets no `AUDIO` element.

#### 3. Remove audio tags associated with failed downloads

This could have been done in the previous steps but the conventions hadn't been decided yet. So it is done as a separate step.

```bash
python update_audio.py
```

**_Output_**
This edits the XML in the `Final_XML` directory to remove audio tags with failed downloads.

It reads `failed_audio.csv` in each topic folder (written only by `ePark1and2.py`)
and removes the `AUDIO` element of each listed `S` or `W`.

#### 4. Adding dialect information

This could have been done in the previous steps but the conventions hadn't been decided yet. So it is done as a separate step.

```bash
python add_dialects.py --dialects_csv dialects.csv --final_xml_dir Final_XML
```

**_Output_**

- This edits the XML in the `Final_XML` directory.
- The name of the of the dialect (if any) is read from the filename and stored in XML root as the `dialect` attribute.
- The corresponding glottocode in `dialects.csv`, if any, is stored in the XML root as the `glottocode` attribute.

For a file named `<Dialect>_<Language>.xml` the `dialect` value is the part before
the underscore; for a single-dialect file (`<Language>.xml`) it is the language
name. When `dialects.csv` has no glottocode the script still writes the attribute,
as `glottocode=""`.

#### 5. Updating the XML files ids

```bash
python update_xml_ids.py
```

**_Output_**
This edits the XML in the `Final_XML` directory to update the id attribute for <TEXT> tags.

The new id is `<topic folder>_<file name>`, for example
`hui_ben_ping_tai_picture_book_platform_Coastal_Amis`. The script takes no
arguments; it always processes `Final_XML` under the current directory.

#### 6. Re-apply recorded hand edits

One-off source corrections that no rule should make are recorded in
`CodeAndDocs/manual_edits.xml` (changelog: `CodeAndDocs/manual_edits.md`) and
re-applied here, before any cleaning:

   ```bash
   python path/to/FormosanBankRepo/QC/cleaning/apply_manual_edits.py --corpora_path Final_XML --manual_file path/to/FormosanBankRepo/Corpora/ePark/CodeAndDocs/manual_edits.xml
   ```

Currently one record: `wen_hua_pian_cultural_section/Puyuma/Jianhe_Puyuma.xml`
S 246, where the source typed two of its four quotation marks as `''`
(`vavayan''`, `''imu''`); the next sentence, S 247, is the same template typed
with `"` throughout (maintainer, 2026-10-14: "a one-off that should not have a
rule").

#### 7. Clean XML and standardize punctuation

   ```bash
   python path/to/FormosanBankRepo/QC/cleaning/clean_xml.py --corpora_path path/to/FormosanePark/Final_XML
   ```

There were some problems with the CSVs for jiu_jie_jiao_cai_nine_level_materials, where sometimes there are entries for words that consist only of punctuation. The following will, for any <W /> element where the text does not include any alphanumeric characters AND there is no value for `file` in the corresponding <AUDIO /> element, remove that <W /> element:

   ```bash
   python cleanup_empty_words.py
   ```

This will also address some known issues:


   ```bash
   python fix_question_mark_spacing.py
   ```

(`fix_question_mark_spacing.py` works on every `FORM` and `PHON` in `Final_XML`:
it removes whitespace before `?`, `!`, `,` and `.`, adds a space after them, and
adds a space between one of them and a following word that begins with a glottal
stop.)

**Outputs**

- This will update the XML files.

**Notes**

- This removes empty XML elements
- It also standardizes orthography (more-or-less), though a lot of this was done in previous steps (not documented above)
- Unicode is flattened so that diacritics are merged with the characters they modify
- HTML escape codes are replaced with the corresponding characters

#### 8. Standardize XML, Part 2; Also add IPA

Different subcorpora appear to use different orthographies, so they need to be standardized one at a time, using `standardize.py`. This involves a lot of commands, so we don't write them here. Here is our determination of which subcorpora use which orthographies (note that when an earlier orthography matches better but standardization wouldn't change anything, we use Ortho113; this is usually because Ortho113 has additional letteres that aren't used in the corpus):

* hui_ben_ping_tai_picture_book_platform: Ortho113, except Amis, which uses Ortho113Liberal. Note that the Puyuma text appears to have a large number of loanwords resulting in unexpected letters. 
* jiu_jie_jiao_cai_nine_level_materials: Amis (Ortho113Liberal), Atayal (Ortho94), Puyuma (Ortho94), Rukai (Ortho94), and the rest are Ortho113. 
* ju_xing_pian_guo_zhong_sentence_patterns_junior_high: Seems to all be Ortho113, though Wanshan Rukai is missing a number of expected letters (dr, r, u, w, y)
* ju_xing_pian_gao_zhong_sentence_patterns_senior_high: Some dialects of Amis (not Southern) might be Church (there are a small number of `g`s, but no `u`s.) Rukai is probably Ortho113, though some dialects (esp. Dona) are plausibly Ortho94. Otherwise, everything seems to be Ortho113.
* qing_jing_zu_yu_contextual_indigenous_language: The orthographies are pretty irregular for this one, with an unusual number of (low-frequency) unexpected characters. The most striking is Jianhe Puyuma, which may be using an unknown orthography or including a lot of loan words. Amis is probably Ortho113Liberal.
* tu_hua_gu_shi_pian_picture_story: All Ortho113
* sheng_huo_hui_hua_pian_daily_conversation: All Ortho113
* wen_hua_pian_cultural_section: All Ortho113
* xue_xi_ci_biao_learning_vocabulary: All Ortho113
* yue_du_shu_xie_pian_reading_writing: All Ortho113
* zu_yu_duan_wen_indigenous_language_essays: All Ortho113

```bash
   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/hui_ben_ping_tai_picture_book_platform --copy
   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/hui_ben_ping_tai_picture_book_platform/Amis --tsv_path ../FormosanBank/Orthographies/ConversionTables/Amis_113lib_113.tsv
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/hui_ben_ping_tai_picture_book_platform --orthography Ortho113
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/hui_ben_ping_tai_picture_book_platform/Amis --orthography Ortho113Liberal

   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/jiu_jie_jiao_cai_nine_level_materials --copy
   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/jiu_jie_jiao_cai_nine_level_materials/Amis --tsv_path ../FormosanBank/Orthographies/ConversionTables/Amis_113lib_113.tsv
   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/jiu_jie_jiao_cai_nine_level_materials/Atayal --tsv_path ../FormosanBank/Orthographies/ConversionTables/Atayal_94_113.tsv
   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/jiu_jie_jiao_cai_nine_level_materials/Puyuma --tsv_path ../FormosanBank/Orthographies/ConversionTables/Puyuma_94_113.tsv
   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/jiu_jie_jiao_cai_nine_level_materials/Rukai --tsv_path ../FormosanBank/Orthographies/ConversionTables/Rukai_94_113.tsv
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/jiu_jie_jiao_cai_nine_level_materials --orthography Ortho113
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/jiu_jie_jiao_cai_nine_level_materials/Rukai --orthography Ortho94
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/jiu_jie_jiao_cai_nine_level_materials/Atayal --orthography Ortho94
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/jiu_jie_jiao_cai_nine_level_materials/Puyuma --orthography Ortho94

   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/ju_xing_pian_gao_zhong_sentence_patterns_senior_high --copy
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/ju_xing_pian_gao_zhong_sentence_patterns_senior_high --orthography Ortho113

   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/ju_xing_pian_guo_zhong_sentence_patterns_junior_high --copy
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/ju_xing_pian_guo_zhong_sentence_patterns_junior_high --orthography Ortho113

   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/qing_jing_zu_yu_contextual_indigenous_language --copy
   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/qing_jing_zu_yu_contextual_indigenous_language/Amis
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/qing_jing_zu_yu_contextual_indigenous_language/Amis --orthography Ortho113Liberal
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/qing_jing_zu_yu_contextual_indigenous_language --orthography Ortho113

   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/tu_hua_gu_shi_pian_picture_story --copy
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/tu_hua_gu_shi_pian_picture_story --orthography Ortho113

   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/wen_hua_pian_cultural_section --copy
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/wen_hua_pian_cultural_section --orthography Ortho113

   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/xue_xi_ci_biao_learning_vocabulary --copy
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/xue_xi_ci_biao_learning_vocabulary --orthography Ortho113

   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/yue_du_shu_xie_pian_reading_writing --copy
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/yue_du_shu_xie_pian_reading_writing --orthography Ortho113

   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/zu_yu_duan_wen_indigenous_language_essays --copy
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/zu_yu_duan_wen_indigenous_language_essays --orthography Ortho113
```

Two gaps in this list, as recorded: the `qing_jing_zu_yu_contextual_indigenous_language/Amis`
`standardize.py` line names no `--copy` or `--tsv_path` (the current `standardize.py`
refuses that; which conversion table was used is not recorded), and there are no
commands for `sheng_huo_hui_hua_pian_daily_conversation`, although its XML has
standard `FORM` and `PHON` tiers.

#### 9. Drop fully unmapped original-tier PHON

After `add_phonology`, drop the original-tier PHON elements that came out fully
unmapped. Some dialect/orthography combinations have no letter→IPA mapping (most
notably YilanZeaol Atayal in `jiu_jie_jiao_cai`, phonologized with Ortho94 whose
YilanZeaol column is entirely `NA`), so `add_phonology` emits placeholder strings
like `"**** ****"`. This removes any `PHON[@kindOf="original"]` whose content is
only `*` placeholders (the standard-tier PHON, built from the mappable
standardized text, is kept):

```bash
   python drop_unmapped_phon.py --final_xml_dir Final_XML
```

#### 10. Add the missing space around inline parentheticals

Next, **add the missing space around inline parentheticals**. The ePark source
frequently runs a word straight into a following parenthetical gloss/alternate
with no separating space (e.g. `manokos(manakboz)`, `madagdag(apnezak)`,
`saleman(100)`). This is present verbatim in the source CSVs — it is *not*
introduced by our processing — so it is corrected here as a reproducible step.
`fix_parenthetical_spacing.py` inserts a space before `(` and after `)` at word
boundaries in `FORM` and `PHON` only. `TRANSL` is deliberately left untouched:
the `zho` translations use CJK parenthetical conventions (e.g. `Dahu(拉荷)`) where
a space is not wanted. It also **skips word-segmented sentences** (those with
`<W>` children, all in `jiu_jie_jiao_cai_nine_level_materials`): there the
parenthetical is a single word token aligned across the sentence `FORM` and the
`W` tier (e.g. one `<W>` `apnezak(pepnezak)`), so spacing the sentence `FORM`
would split it into two whitespace tokens while the `W` tier keeps one, breaking
`FORM`↔`W` alignment (`validate_glosses` V060). Those ~100 glossed cases are left
as-is on purpose. The script defaults to a dry run that previews every change;
pass `--apply` to write. It serializes with lxml (matching `clean_xml.py`) so the
diff contains only the text edits, not a whole-file reserialization:

```bash
   python fix_parenthetical_spacing.py --final_xml_dir Final_XML --apply
```

#### 11. Re-run clean_xml.py

Finally, **re-run `clean_xml.py` now that the standard tier exists**. The earlier
`clean_xml` pass (step "Clean XML and standardize punctuation" above) ran *before*
`standardize.py` created the `kindOf="standard"` FORM tier, so its standard-tier
cleanups never touched it: `standardize --copy` produces the standard tier as a
verbatim copy of the original, inheriting its hyphens and curly apostrophes. A
second `clean_xml` pass strips `-` from the standard tier where the orthography
doesn't use it as a letter (kept for Bunun/Thao per C012) and normalizes smart
quotes `’→'` in both FORM tiers (otherwise validate_text flags V110/V127/V133):

```bash
   python ../FormosanBank/QC/cleaning/clean_xml.py --corpora_path Final_XML
```

#### 12. More

So ePark is a very complex datasource. It contains repeated names. It also contains a lot of Chinese in filenames, which are problems for some computers. We have a series of scripts that clean this up. It would be better to do this much earlier in the process. Feel free to submit a pull request!

  ```bash
   python add_audio_saisiyat.py
   python clean_source_prefixes.py
   python clean_audio_filenames.py
   python update_xml_ids.py
   ```

What these do: `add_audio_saisiyat.py` adds an `AUDIO` element (file name only) to
S 0 to 85 of `sheng_huo_hui_hua_pian_daily_conversation/Saisiyat/Saisiyat.xml`
where one is missing; `clean_source_prefixes.py` removes the leading `ePark1 `,
`ePark2 ` or `ePark3 ` from each `TEXT/@source`; `clean_audio_filenames.py`
replaces a Chinese prefix in each `AUDIO/@file` with the topic folder name (and
turns `<topic>/` into `<topic>_`); `update_xml_ids.py` recomputes the `TEXT` ids
from the now-romanized folder names.

You will then need to edit the top-level folders for the audio files so that the names match. That is, they come with some Chinese. You need to replace with Romanizations. But be careful because some of these top-level folders have the same names once the "ep1", "ep2", etc., are removed. You should be able to figure this out. 

Then run:

  ```bash
   python rename_audio_files.py
   ```

(`rename_audio_files.py` renames each audio file under `Final_audio/` whose name
begins with Chinese characters, replacing that prefix with the topic folder name.)

At this point, run:
  ```bash
   python verify_audio_files.py
   ```

This will check to make sure all the audio files exist and are where they are supposed to be. However, if any are missing, they will end up in `missing_audio_files.txt`. 

As the script now stands it reads XML from `XML/` and looks for audio under
`Audio/` (both relative to where it is run), not `Final_XML/` and `Final_audio/`
as its docstring says.

For the published corpus, restore missing audio with `../download_audio_data.sh`,
which uses the pinned Hugging Face archives. `download_missing_audio.py` is a
legacy reproduction helper for local build outputs; it now normalizes former
learning-vocabulary URLs before requesting the source file.

Now, we need to convert the mp3s to wav files. Run

```bash
   ./convert_mp3_to_wav_fast.sh
   ./update_xml_mp3_to_wav_fast.sh
```

(`convert_mp3_to_wav_fast.sh` converts every `.mp3` under `Final_audio/` to a 16 kHz
mono `.wav` beside it with `sox`, skipping existing `.wav` files, and logs to
`conversion.log`; `update_xml_mp3_to_wav_fast.sh` rewrites `file="….mp3"` to
`file="….wav"` in every XML file under `Final_XML/`. It calls `sed -i ''`, the
macOS/BSD form; GNU `sed` reads the `''` as a file name.)

Confirm that this ran correctly and that all files have been updated by running:

  ```bash
   python verify_audio_files.py
   ```

When I ran this, there were 8 missing files. 6 of the mp3s were actually m4a files, which sox can't convert. I solved with the following (it specifies the files specifically, so it may not work for you if you have different problems):

  ```bash
   ./convert_missing_m4a.sh
   ```

(It converts those six files with `ffmpeg`, 16 kHz mono.)

The 2 remaining missing files appear not to exist in the original source, so I deleted their audio tags from the corresponding XML.

#### 13. Migrate published learning-vocabulary audio URLs

`learning_vocabulary_audio_urls.py` also works on the published XML: by default it
scans `XML/xue_xi_ci_biao_learning_vocabulary`, reports how many `AUDIO/@url`
values still use the retired `https://ilrdc.tw/tow/2022/audio/word/` route, and
with `--apply` rewrites them to `https://web.klokah.tw/vocabulary/audio/word/`
(`--check` exits 1 if any retired URL remains). It refuses any vocabulary URL of an
unexpected shape.

#### Not produced by any script here

These properties of the published XML are made by no script in `CodeAndDocs/`:

- the rename of the `Final_XML` topic folders from `ep<N>_<Chinese topic name>` to
  the romanized names; `apply_manual_edits.py` (step 6) and `cleanup_empty_words.py`
  (step 7) already use the romanized paths, so this happened before step 6;
- the `start` and `end` attributes on `AUDIO` elements;
- the "later dedup step" that the `ePark3.py` code comment says removed duplicate
  subcorpora.

#### Code breakdown

This breakdown provides an in-depth look at the functionality of two main Python scripts in the ePark project, explaining each section's purpose and the functions implemented.

##### Part 1: ePark1and2.py

This script processes the data files in `ePark_1` and `ePark_2` directories, downloads associated audio files (when available), and organizes the data into structured XML format.

**Imports**

- **csv**: For reading and writing CSV files.
- **xml.etree.ElementTree**: For creating and modifying XML elements.
- **xml.dom.minidom**: For pretty-printing XML.
- **os**: For file and directory operations.
- **requests**: For downloading audio files from URLs.
- **ThreadPoolExecutor, as_completed**: For concurrent downloading of audio files.
- **tqdm**: For displaying progress bars.
- **normalize_audio_url** (from `learning_vocabulary_audio_urls.py`): For rewriting retired learning-vocabulary audio URLs.

**Functions**

1. **prettify(elem)**: Converts an XML element into a pretty-printed string for better readability.

2. **download_audio(url, save_path, file_name, lang, dialect, failed_audio)**: Downloads audio files. If download fails, it records the failure details in `failed_audio.csv`.

3. **download_all_audios(audio_urls, save_path, lang, dialect, failed_audio)**: Uses a thread pool to download multiple audio files concurrently. It returns nothing; failures are recorded in `failed_audio.csv` by `download_audio`.

4. **create_xml(curr_ePark, out_ePark, file, dialect, lang, lang_code, dir, ePark, failed_audio)**: Reads data from a CSV file, constructs XML elements, downloads audio files, and saves the resulting XML.

5. **ePark1_2(curr_dir, dialects, lang_codes, ePark_ver)**: Processes ePark versions 1 and 2, iterating over directories and files to create XML files for each dialect.

6. **main()**: Initializes variables, reads dialect mappings from `dialects.csv`, and initiates processing of ePark versions 1 and 2.

---

##### Part 2: ePark3.py

This script processes the data files in `ePark_3` directory for various ePark topics, including “句型篇國中” and “句型篇高中”. It handles different data structures in XML and audio files, organizes them into structured XML, and performs concurrent downloading.

**Imports**

- **os, shutil**: For file and directory operations.
- **xml.etree.ElementTree, xml.dom.minidom**: For XML creation, manipulation, and pretty-printing.
- **csv, requests, tqdm, ThreadPoolExecutor, as_completed, defaultdict, threading**: For handling CSV files, downloading files, concurrent processing, progress display, and thread-safe operations.

**Functions**

1. **prettify(elem)**: Converts an XML element into a pretty-printed string.

2. **create_root(ePark, dialect, lang)**: Creates the root XML element with metadata attributes for an ePark topic.

3. **process_match_items(item, types, audio_path, type_id, class_num)**: Handles "match" type items where pairs of sentences and translations are stored.

4. **process_multiple_sentences_single_audio(item, types, audio_path, type_id, class_num)**: Processes items where multiple sentences share a single audio file.

5. **process_multiple_sentences_multiple_audio(item, types, audio_path, type_id, class_num)**: Processes items where each sentence has its own audio file.

6. **process_single_sentence_item(item, types, audio_path, type_id, class_num)**: Processes items containing a single sentence and translation.

7. **process_item_by_type(ePark, item, types, audio_path)**: Determines the correct function to process an item based on type and ePark topic.

8. **process_epark_sentence_patterns(ePark, path, output_path, dialects, lang_codes)**: Processes the ePark sentence patterns for topics like “句型篇國中” and “句型篇高中”.

9. **download_audio(save_path, url, file_name)**: Downloads audio from a URL to a specified path.

10. **process_data_point(data_point, dialects, audio_output_dict, download_url, ePark, failed_audio_entries, s_elements_dict)**: Processes a single data point, appends failed audio entries for reprocessing, and stores “S” elements. (In the current code it also takes `skipped_blank_entries` and `entries_lock`, and skips rows with no Formosan text.)

11. **process_epark_topics_with_csv(ePark, path, output_path, dialects, lang_codes, data_file, download_url)**: Processes ePark topics where data is stored in CSV files, downloading audio files concurrently.

12. **process_topics4and5_items(item, tag_org, tag_zh, root, path, idx, audio_output, ePark, lang, dialect, failed_audio)**: Processes items for specific ePark topics like "生活會話篇" and "閱讀書寫篇".

13. **process_epark_conversation_reading(ePark, path, output_path, dialects, lang_codes, xml_file)**: Processes the “生活會話篇” and “閱讀書寫篇” topics by creating XML and managing audio downloads.

14. **main()**: Reads dialect mappings, processes each ePark topic, and organizes XML and audio files.

Functions 12 and 13 are no longer called by `main()` (see step 2).

---

##### Key Processing Steps

1. **Audio Downloads**: Concurrently downloads audio files for each sentence or item, managing failures and retries.
2. **XML Generation**: Constructs well-structured XML files that encapsulate the dialect, sentence, translation, and audio details.
3. **Multi-threaded Processing**: Implements concurrent processing for downloading audio and processing large files.

There is no automatic retry: a failed download is recorded, and a re-run skips
files already downloaded, so re-running retries only the failures.
