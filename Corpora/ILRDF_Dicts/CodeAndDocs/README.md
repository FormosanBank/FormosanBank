
# ILRDF Data

This repository contains code and data for processing and structuring Formosan language dictionaries provided by the Indigenous Languages Research and Development Foundation ([ILRDF](https://www.ilrdf.org.tw/)). The project includes handling dictionary data, downloading audio for words, and organizing the data into structured XML format.

## Project Structure

- **dicts**: Contains PDF dictionaries for 16 Formosan languages provided by the ILRDF.

- **.PickleScrapes**: Stores results from API calls on the words within the dictionaries. Each API call returns the definition, example sentences, and audio links.

- **words_list**: Contains pickled lists of words extracted from the `dicts` PDFs. These lists were processed using `scrape.py`.

- **Final_XML**: Directory containing the processed XML data, similar to the ePark repository. This data is structured into XML format using `xmlify.py`.

- **audioDL.py**: Script used to download audio files linked to words in the dictionaries.

- **scrape.py**: Script to process words from the dictionaries and store them in `words_list`. It them make the API calls to retrieve definitions, example sentences, and audio links.

- **xmlify.py**: Script to convert data into XML format, structured in the FormosanBank XML format.

- **requirements.txt**: Lists the Python libraries required to run the scripts in this repository.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/ILRDF.git
   cd ILRDF
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

1. **Scrape Definitions and Examples**:
   Run `scrape.py` to retrieve lists of words from the pdf dictionaries then make the API calls to retrieve definitions, example sentences, and audio links via API calls, and store results in `.PickleScrapes`.

   ```bash
   python scrape.py
   ```

2. **Convert Data to XML**:
   Run `xmlify.py` to process the scraped data and convert it into structured XML format saved in the `Final_XML` directory.

   ```bash
   python xmlify.py
   ```

3. **Download Audio**:
   Run `audioDL.py` to download audio files linked to words in the dictionaries. The audio will be stored in the audio directory in the folder of the language it belongs to in Final_XML.

   ```bash
   python audioDL.py
   ```

3. **Download Audio**:
   Run `audioDL.py` to download audio files linked to words in the dictionaries. The audio will be stored in the audio directory in the folder of the language it belongs to in Final_XML.

   ```bash
   python audioDL.py
   ```

4. **Clean XML and standardize punctuation**

   ```bash
   python path/to/FormosanBankRepo/QC/cleaning/clean_xml.py --corpora_path path/to/FormosanWikipedias/Final_XML
   ```

**Outputs**
   - This will update the XML files.

**Notes**
   - This removes empty XML elements
   - It also standardizes orthography (more-or-less), though a lot of this was done in previous steps (not documented above)
   - Unicode is flattened so that diacritics are merged with the characters they modify
   - HTML escape codes are replaced with the corresponding characters

5. **Standardize orthography**

   ```bash
   python path/to/FormosanBankRepo/QC/utilities/add_original.py --corpora_path path/to/FormosanWikipedias/Final_XML
   ```

**Outputs**
   - Updates XML files

**Notes**
   - Adds kindOf="original" attribute to all <FORM> elements. (This should normally be done in an earlier step, but wasn't for this corpus.)

6. **Standardize orthography**

   ```bash
   python path/to/FormosanBankRepo/QC/utilities/standardize.py --corpora_path path/to/FormosanWikipedias/Final_XML
   ```

**Outputs**
   - Updates XML files

**Notes**
   - Creates a copy of every <FORM> element with kindOf="standard" attribute
   - All u's are converted to o's.

## Code Breakdown

This document provides an in-depth code breakdown for three main Python scripts in the ILRDF project: **scrape.py**, **xmlify.py**, and **audioDL.py**.

---

## Script 1: scrape.py

This script extracts words from PDF dictionaries, makes API requests to retrieve definitions and example sentences, and organizes the results in pickle files.

### Functions

1. **getWords(lang)**: Extracts words from a PDF dictionary for a specified language.
   - Reads the PDF content page by page and extracts text containing a specific symbol (★) to identify dictionary entries.
   - Returns a list of words after filtering and processing the text.

2. **getData(lang, qw, TRIBES, URL)**: Sends an API request to retrieve definitions and example sentences for a given word.
   - Constructs a payload with language and word parameters, then sends a POST request to the specified API.
   - Returns the data received or logs errors if the request fails.

3. **processWords(lang, words, TRIBES, URL)**: Processes a list of words by making concurrent API requests.
   - Uses a ThreadPoolExecutor to handle multiple requests in parallel.
   - Organizes successful responses and failed queries into separate lists.

4. **main()**: Main function to set up the environment, process each language, and save results.
   - Reads or generates word lists, organizes directory structure, and initiates API requests.
   - Saves processed data as pickles for later use.

---

## Script 2: xmlify.py

This script structures the processed data into XML format following the FormosanBank XML standard.

### Functions

1. **prettify(elem)**: Converts an XML element into a pretty-printed string for readability.

2. **getPickles(lang)**: Loads processed data for a specified language from pickle files.
   - Returns the data for words that succeeded and failed API requests.

3. **handleHelper(sent)**: Checks if a sentence contains the required keys and extracts necessary components.
   - Returns the sentence text, translation, and audio link if valid.

4. **createElemHelp(lang, count, r)**: Creates XML elements for a sentence entry.
   - Sets attributes for the sentence ID, original text, translation, and audio link.

5. **wrapperXML(sent, root, count, seen, lang)**: Processes a sentence and adds it to the XML root if it’s not a duplicate.

6. **handleExplanation(expl, root, lang, count, seen)**: Handles sentence explanations and manages single or multiple sentence entries.

7. **makeLists(lang)**: Categorizes sentences based on pickle data for easier processing.

8. **xmlify_main()**: Main function to generate XML files for each language.
   - Initializes XML structure, processes sentences, and saves the XML file to the `Final_XML` directory.

---

## Script 3: audioDL.py

This script manages audio file downloads for each language, including retry mechanisms for failed downloads.

### Functions

1. **dlAudio(url, audioPath, dlRate, maxRetries, retryDelay)**: Downloads an audio file with a retry mechanism.
   - Handles network issues by retrying a maximum number of times with a specified delay between attempts.

2. **dlHelper(urls)**: Manages parallel downloading of multiple audio files.
   - Uses a ThreadPoolExecutor to handle concurrent downloads, logging errors if any occur.

3. **download_audios(xml_path, toDo)**: Parses XML files and initiates audio downloads for each sentence.
   - Updates XML files with the local paths of downloaded audio files.

4. **main()**: Main function to set up directories and initiate the download process for each language.
   - Ensures necessary directories exist, then calls `download_audios` to process each language’s XML.

---

### Key Components

- **PDF Extraction**: The `scrape.py` script uses PyPDF2 to extract text from PDFs, filtering dictionary entries by a symbol (★).
- **API Requests**: Concurrent API requests are managed in `scrape.py` to retrieve definitions, examples, and audio links.
- **XML Conversion**: Processed data is structured into XML in `xmlify.py`, following a specific format for consistency.
- **Audio Download**: `audioDL.py` handles downloading and updating XML files with local audio paths, utilizing retry mechanisms for robustness.


## Output Explaination

All the output will be in the Final_XML folder. in the folder, there will be a subfolder for each of the Formosan languages. Inside each of these folders, there will be an XML file for the language content and an audio folder for the audio files associated with the XML files.