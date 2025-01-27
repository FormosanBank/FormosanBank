
# ePark Data

This repository contains code and data for processing and structuring the ePark dataset into the [FormosanBank XML format](https://app.gitbook.com/o/tZF822XPLvjWkTiqbQyF/s/VETgkt5DVZWXBIolTyjW/the-bank-architecture/xml-standardize-format). The dataset includes various Formosan dialects and is organized to assist in linguistic research and language preservation.

## Project Structure

- **ePark_1**, **ePark_2**, **ePark_3**: Directories containing the source data files from the ePark dataset, organized by different parts. eParks 2 and 3 contain multiple topics. Data in the different ePark folders are structured differently, and so the code is in this repo is catered to deal with these different structures to process the code.
- **Final_XML**: Directory containing the processed data structured into FormosanBank XML format.
- **dialects.csv**: A mapping file between numerical codes and the corresponding Formosan dialects used in the ePark dataset.
- **ePark1and2.py**: Script to process and convert the data in `ePark_1` and `ePark_2` directories into the FormosanBank XML format.
- **ePark3.py**: Script to process and convert the data in the `ePark_3` directory into the FormosanBank XML format.
- **failed_audio.csv**: A record of audio files that could not be downloaded during the data collection process.
- **requirements.txt**: Lists the Python libraries required to run the processing scripts.

Please note that ePark is a collection of educational material that is split into topics. The Final_XML folder will have subfolders and their names would start with the ePark version (e.g. ep1) followed by the topic name in Chinese (e.g. 九階教材). These topics could be something like "9th Period Teaching Materials" or "Cultural Topics." Unless you are interested in differentiating between the specific type of the educational materials in your research, the topic names shouldn't be relevant.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/ePark.git
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

***Output***
The processed data in XML format will be saved in the `Final_XML` directory.

2. **Process ePark 3 Data**:
   Run `ePark3.py` to process the source data in the `ePark_3` directory:
   ```bash
   python ePark3.py
   ```
***Output***
The processed data in XML format will be saved in the `Final_XML` directory.

3. **Adding dialect information**

This could have been done in the previous steps but the conventions hadn't been decided yet. So it is done as a separate step.

   ```bash
   python add_dialects.py --dialects_csv dialects.csv --final_xml_dir Final_XML
   ```

***Output***
- This edits the XML in the `Final_XML` directory.
- The name of the of the dialect (if any) is read from the filename and stored in XML root as the `dialect` attribute.
- The corresponding glottocode in `dialects.csv`, if any, is  stored in the XML root as the `glottocode` attribute.

4. **Clean XML and standardize punctuation**

   ```bash
   python path/to/FormosanBankRepo/QC/cleaning/clean_xml.py --corpora_path path/to/FormosanePark/Final_XML
   ```

**Outputs**
   - This will update the XML files.

**Notes**
   - This removes empty XML elements
   - It also standardizes orthography (more-or-less), though a lot of this was done in previous steps (not documented above)
   - Unicode is flattened so that diacritics are merged with the characters they modify
   - HTML escape codes are replaced with the corresponding characters

5. **Standardize XML, Part 2**

   ```bash
   python path/to/FormosanBankRepo/QC/utilities/add_original.py --corpora_path path/to/Formosan-ePark/Final_XML
   ```



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
