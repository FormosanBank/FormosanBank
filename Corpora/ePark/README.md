# ePark Data

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

This repository contains code and data for processing and structuring the ePark dataset into the [FormosanBank XML format](https://ai4commsci.gitbook.io/formosanbank/the-bank-architecture/formosanbank-xml-format). The dataset includes various Formosan dialects and is organized to assist in linguistic research and language preservation.

## Project Structure

- **ePark_1**, **ePark_2**, **ePark_3**: Directories containing the source data files from the ePark dataset, organized by different parts. eParks 2 and 3 contain multiple topics. Data in the different ePark folders are structured differently, and so the code is in this repo is catered to deal with these different structures to process the code.
- **Final_XML**: Directory containing the processed data structured into FormosanBank XML format.
- **dialects.csv**: A mapping file between numerical codes and the corresponding Formosan dialects used in the ePark dataset.
- **ePark1and2.py**: Script to process and convert the data in `ePark_1` and `ePark_2` directories into the FormosanBank XML format.
- **ePark3.py**: Script to process and convert the data in the `ePark_3` directory into the FormosanBank XML format.
- **failed_audio.csv**: A record of audio files that could not be downloaded during the data collection process. There is a failed_audio.csv file in each of the ePark topics in the FinalXML Folder
- **requirements.txt**: Lists the Python libraries required to run the processing scripts.
- **add_dialects**: script to add the dialect information to the XML files
- **update_audio.py**: script to update the XML files and remove the <AUDIO> tags associated with audio files that weren't downloaded successfully -**update_xml_ids.py**: update the id attribute in the <TEXT> tags in XML files to ensure the ids are unique

Please note that ePark is a collection of educational material that is split into topics. The Final_XML folder will have subfolders and their names would start with the ePark version (e.g. ep1) followed by the topic name in Chinese (e.g. 九階教材). These topics could be something like "9th Period Teaching Materials" or "Cultural Topics." Unless you are interested in differentiating between the specific type of the educational materials in your research, the topic names shouldn't be relevant
.

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/FormosanBank/Formosan-ePark
   cd ePark
   ```

2. Set up a virtual environment (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Data was originally received in three packages, here named ePark 1, 2, and 3. This has no significance outside how it was mailed to us. But based on what was in which archive, the code varies a little.

1. **Process ePark 1 and 2 Data**:
   Run `ePark1and2.py` to process the source data in `ePark_1` and `ePark_2` directories:
   ```bash
   python ePark1and2.py
   ```

**_Output_**
The processed data in XML format will be saved in the `Final_XML` directory.

2. **Process ePark 3 Data**:
   Run `ePark3.py` to process the source data in the `ePark_3` directory:

   ```bash
   python ePark3.py
   ```

   **_Output_**
   The processed data in XML format will be saved in the `Final_XML` directory.

   Some ePark picture-book records are illustration-only pages: the source row has an ID and page order, but both the Formosan text and Chinese translation are blank. `ePark3.py` skips these rows so they do not become empty `<S />` elements in `Final_XML`. Skipped rows are recorded in `skipped_blank_rows.csv` in the generated topic directory.

3. **remove audio tags associated with failed downloads**

This could have been done in the previous steps but the conventions hadn't been decided yet. So it is done as a separate step.

```bash
python update_audio.py
```

**_Output_**
This edits the XML in the `Final_XML` directory to remove audio tags with failed downloads.

4. **Adding dialect information**

This could have been done in the previous steps but the conventions hadn't been decided yet. So it is done as a separate step.

```bash
python add_dialects.py --dialects_csv dialects.csv --final_xml_dir Final_XML
```

**_Output_**

- This edits the XML in the `Final_XML` directory.
- The name of the of the dialect (if any) is read from the filename and stored in XML root as the `dialect` attribute.
- The corresponding glottocode in `dialects.csv`, if any, is stored in the XML root as the `glottocode` attribute.

5. **updating the XML files ids**

   ```bash
   python update_xml_ids.py --directory Final_XML
   ```

**_Output_**
This edits the XML in the `Final_XML` directory to update the id attribute for <TEXT> tags.

6. **Clean XML and standardize punctuation**

   ```bash
   python path/to/FormosanBankRepo/QC/cleaning/clean_xml.py --corpora_path path/to/FormosanePark/Final_XML
   ```

There were some problems with the CSVs for jiu_jie_jaio_cai_nine_levels_materials, where sometimes there are entries for words that consist only of punctuation. The following will, for any <W /> element where the text does not include any alphanumeric characters AND there is no value for `file` in the corresponding <AUDIO /> element, remove that <W /> element:

   ```bash
   python cleanup_empty_words.py
   ```

This will also address some known issues:


   ```bash
   python fix_question_mark_spacing.py
   ```


**Outputs**

- This will update the XML files.

**Notes**

- This removes empty XML elements
- It also standardizes orthography (more-or-less), though a lot of this was done in previous steps (not documented above)
- Unicode is flattened so that diacritics are merged with the characters they modify
- HTML escape codes are replaced with the corresponding characters

5. **Standardize XML, Part 2; Also add IPA**

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
   ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/jiu_jie_jiao_cai_nine_level_materials --orthography Ortho113
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/jiu_jie_jiao_cai_nine_level_materials/Rukai --orthography Ortho94
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/jiu_jie_jiao_cai_nine_level_materials/Atayal --orthography Ortho94
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/jiu_jie_jiao_cai_nine_level_materials/Puyuma --orthography Ortho94

   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/ju_xing_pian_gao_zhong_sentence_patterns_senior_high --copy
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/ju_xing_pian_gao_zhong_sentence_patterns_senior_high --orthography Ortho113

   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/ju_xing_pian_guo_zhong_sentence_patterns_junior_high --copy
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/ju_xing_pian_guo_zhong_sentence_patterns_junior_high --orthography Ortho113

   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/qing_jing_zu_yu_contextual_indigenous_language --copy
   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML/qing_jing_zu_yu_contextual_indigenous_language/Amis python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML/qing_jing_zu_yu_contextual_indigenous_language/Amis --orthography Ortho113Liberal
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

6. **More**

So ePark is a very complex datasource. It contains repeated names. It also contains a lot of Chinese in filenames, which are problems for some computers. We have a series of scripts that clean this up. It would be better to do this much earlier in the process. Feel free to submit a pull request!

  ```bash
   python add_audio_saisiyat.py
   python clean_source_prefixes.py
   python clean_audio_filenames.py
   python update_xml_ids.py
   ```

You will then need to edit the top-level folders for the audio files so that the names match. That is, they come with some Chinese. You need to replace with Romanizations. But be careful because some of these top-level folders have the same names once the "ep1", "ep2", etc., are removed. You should be able to figure this out. 

Then run:

  ```bash
   python rename_audio_files.py
   ```

At this point, run:
  ```bash
   python verify_audio_files.py
   ```

This will check to make sure all the audio files exist and are where they are supposed to be. However, if any are missing, they will end up in `missing_audio_files.txt`. 

When I ran this, we had a number of broken symlinks. This was verified by running `check_missing_symlinks.py`. At that point, running `python download_missing_audio.py` replaced all the missing audio files for me. Hopefully this won't come up, and if it does, hopefully the steps above will address the issue for you.

Now, we need to convert the mp3s to wav files. Run

```bash
   ./convert_mp3_to_wav_fast.sh
   ./update_xml_mp3_to_wav_fast.sh
```

Confirm that this ran correctly and that all files have been updated by running:

  ```bash
   python verify_audio_files.py
   ```

When I ran this, there were 8 missing files. 6 of the mp3s were actually m4a files, which sox can't convert. I solved with the following (it specifies the files specifically, so it may not work for you if you have different problems):

  ```bash
   ./convert_missing_m4a.sh
   ```

The 2 remaining missing files appear not to exist in the original source, so I deleted their audio tags from the corresponding XML.

## code breakdown

This breakdown provides an in-depth look at the functionality of two main Python scripts in the ePark project, explaining each section's purpose and the functions implemented.

### Part 1: ePark1and2.py

This script processes the data files in `ePark_1` and `ePark_2` directories, downloads associated audio files (when available), and organizes the data into structured XML format.

#### Imports

- **csv**: For reading and writing CSV files.
- **xml.etree.ElementTree**: For creating and modifying XML elements.
- **xml.dom.minidom**: For pretty-printing XML.
- **os**: For file and directory operations.
- **requests**: For downloading audio files from URLs.
- **ThreadPoolExecutor, as_completed**: For concurrent downloading of audio files.
- **Lock, tqdm**: For thread-safe operations and displaying progress bars.

#### Functions

1. **prettify(elem)**: Converts an XML element into a pretty-printed string for better readability.

2. **download_audio(url, save_path, file_name, lang, dialect, failed_ids, lock)**: Downloads audio files. If download fails, it records the failure details in `failed_audio.csv`.

3. **download_all_audios(audio_urls, save_path, lang, dialect)**: Uses a thread pool to download multiple audio files concurrently. Returns a list of IDs for which downloads failed.

4. **create_xml(curr_ePark, out_ePark, file, dialect, lang, lang_code, dir, ePark)**: Reads data from a CSV file, constructs XML elements, downloads audio files, and saves the resulting XML.

5. **ePark1_2(curr_dir, dialects, lang_codes, ePark_ver)**: Processes ePark versions 1 and 2, iterating over directories and files to create XML files for each dialect.

6. **main()**: Initializes variables, reads dialect mappings from `dialects.csv`, and initiates processing of ePark versions 1 and 2.

---

### Part 2: ePark3.py

This script processes the data files in `ePark_3` directory for various ePark topics, including “句型篇國中” and “句型篇高中”. It handles different data structures in XML and audio files, organizes them into structured XML, and performs concurrent downloading.

#### Imports

- **os, shutil**: For file and directory operations.
- **xml.etree.ElementTree, xml.dom.minidom**: For XML creation, manipulation, and pretty-printing.
- **csv, requests, tqdm, ThreadPoolExecutor, as_completed, defaultdict, threading**: For handling CSV files, downloading files, concurrent processing, progress display, and thread-safe operations.

#### Functions

1. **prettify(elem)**: Converts an XML element into a pretty-printed string.

2. **create_root(ePark, dialect, lang)**: Creates the root XML element with metadata attributes for an ePark topic.

3. **process_match_items(item, types, audio_path, type_id, class_num)**: Handles "match" type items where pairs of sentences and translations are stored.

4. **process_multiple_sentences_single_audio(item, types, audio_path, type_id, class_num)**: Processes items where multiple sentences share a single audio file.

5. **process_multiple_sentences_multiple_audio(item, types, audio_path, type_id, class_num)**: Processes items where each sentence has its own audio file.

6. **process_single_sentence_item(item, types, audio_path, type_id, class_num)**: Processes items containing a single sentence and translation.

7. **process_item_by_type(ePark, item, types, audio_path)**: Determines the correct function to process an item based on type and ePark topic.

8. **process_epark_sentence_patterns(ePark, path, output_path, dialects, lang_codes)**: Processes the ePark sentence patterns for topics like “句型篇國中” and “句型篇高中”.

9. **download_audio(save_path, url, file_name)**: Downloads audio from a URL to a specified path.

10. **process_data_point(data_point, dialects, audio_output_dict, download_url, ePark, failed_audio_entries, s_elements_dict)**: Processes a single data point, appends failed audio entries for reprocessing, and stores “S” elements.

11. **process_epark_topics_with_csv(ePark, path, output_path, dialects, lang_codes, data_file, download_url)**: Processes ePark topics where data is stored in CSV files, downloading audio files concurrently.

12. **process_topics4and5_items(item, tag_org, tag_zh, root, path, idx, audio_output, ePark, lang, dialect, failed_audio)**: Processes items for specific ePark topics like "生活會話篇" and "閱讀書寫篇".

13. **process_epark_conversation_reading(ePark, path, output_path, dialects, lang_codes, xml_file)**: Processes the “生活會話篇” and “閱讀書寫篇” topics by creating XML and managing audio downloads.

14. **main()**: Reads dialect mappings, processes each ePark topic, and organizes XML and audio files.

---

### Key Processing Steps

1. **Audio Downloads**: Concurrently downloads audio files for each sentence or item, managing failures and retries.
2. **XML Generation**: Constructs well-structured XML files that encapsulate the dialect, sentence, translation, and audio details.
3. **Multi-threaded Processing**: Implements concurrent processing for downloading audio and processing large files.

## Output Explaination

All the output will be in the Final_XML folder. in the folder, there will be subfolder, coming from different ePark data. Each subfolder will start with ep[ver] followed by the topic name. in each folder, there will be a folder for each of the languages, and inside each of these folders, an XML file for each dialect and an audio folder for the audio files associated with the XML files.

## Notes

- There are some cases where the audio does not entirely match the text. For instance, the text describes a conversation, and the speaker only reads what is said. So `Pawang, "iyat bbengan pazih pi?"` gets rendered as `iyat bbengan pazih pi?`. These do not seem to be very common, so they have not been dealt with. 

- The sound files corresponding to individual words in `jiu_jie_jaio_cai_nine_levels_materials` are iffy. The original datasource had some errors in it. We cleaned it up quite a bit, but it is likely some inaccuracies remain. Use with caution.
