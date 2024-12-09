
# Presidential Apologies Data

This repository contains code and data for processing and structuring translations of the Presidential Apology issued by the President of Taiwan towards Indigenous communities. The apology is available in the 16 official Formosan languages, as well as in Chinese and English translations. To ensure consistent alignment, the corpus was divided into 33 sections, with each section corresponding to paragraph divisions in the official release. While sentence-level alignment was considered, it was impractical due to differing sentence counts across languages. Instead, paragraphs were used as the unit of alignment, with some sections merged or split manually to match across all languages. This approach ensured that English and Chinese translations could be reliably mapped to Formosan languages, even when structural discrepancies existed. The exception to this is Kanakanavu as the apology for this language was divided to only 29 sections and the sections were aligned manually because it was too different from the other apologies in terms of the sectionining. The final dataset enables accurate cross-linguistic comparison and preserves the cultural integrity of the apologies. 

## Notes

*Amis* The presidential apology in Amis has a couple of occurances of the letter 'b' which isn't part of the standard orthography of the language. all the occurances can be found in two words: Balay and Sbalay. Both of these words are Atayal words that are quoted in the original apology, and they were used in the same form in the Amis translation. 

*Kanakanavu* This corpus uses a small number of h's and f's, which are controversial. None of the words involving h's or f's appear in the reference ILRDF Dictionary corpus, with or without the h's and f's. Thus, we have chosen to leave them in.

*Puyuma* This corpus has a number of appearances of ē. Almost all of these are due to yēncumin (which is marked as a foreign word) and sēhu. Thus, this has not been homogenized.

*Sakizaya* A small number of f's appear to be foreign words.



## Project Structure

- **Apologies**: Directory containing subdirectories for each Formosan language. Each language folder includes:
  - A PDF file of the apology in the specific language.
  - A TXT file of the apology, divided into 33 sections that correspond across all languages.

- **Chinese.txt** and **English.txt**: TXT files containing the apology in Chinese and English, respectively. Like the other languages, these are also divided into 33 sections.

- **XML**: Directory for storing the processed XML files, structured according to the FormosanBank XML format.

- **main.py**: The main script that processes the text files in each language folder and converts them into XML format, organizing sections to match across translations.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/Presidential_Apologies.git
   cd Presidential_Apologies
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

1. **Process Text Files to XML**:
   Run `main.py` to process the text files in each language folder and convert them into XML format.
   
   ```bash
   python main.py
   ```

   **Output**

   The processed XML files will be saved in the `XML` directory.


2. **Clean XML and standardize punctuation**

   ```bash
   python path/to/FormosanBankRepo/QC/cleaning/clean_xml.py --corpora_path path/to/Apologies/XML
   ```

   **Outputs**
   - This will update the XML files.

   **Notes**
      - This removes empty XML elements
      - It also standardizes orthography (more-or-less), though a lot of this was done in previous steps (not documented above)
      - Unicode is flattened so that diacritics are merged with the characters they modify
      - HTML escape codes are replaced with the corresponding characters

3. **Standardize XML**

   ```bash
   python path/to/FormosanBankRepo/QC/utilities/add_original.py --corpora_path path/to/FormosanWikipedias/XML
   ```

   **Outputs**
      - Updates XML files

   **Notes**
      - Adds kindOf="original" attribute to all <FORM> elements. (This should normally be done in an earlier step, but wasn't for this corpus.)


4. **Standardize orthography**

   ```bash
   python path/to/FormosanBankRepo/QC/utilities/standardize.py --corpora_path path/to/FormosanWikipedias/XML
   ```

   **Outputs**
      - Updates XML files

   **Notes**
      - Creates a copy of every <FORM> element with kindOf="standard" attribute
      - All u's are converted to o's.

## Code Breakdown

This document provides an in-depth code breakdown for the `main.py` script, which processes the Presidential Apology translations and structures them into the FormosanBank XML format.

---

## Functions

### 1. `read_apologies(path, langs)`
   - Reads the apology text files for each language and returns a dictionary with the text data for each language.
   - **Parameters**:
     - `path`: The path to the `Apologies` directory containing language subfolders and translation text files.
     - `langs`: A list of language names, each corresponding to a subfolder in `Apologies`.
   - **Returns**: A dictionary where each key is a language and each value is a list of sections (lines) in the apology text.
   - **Functionality**:
     - Reads English and Chinese translations from `English.txt` and `Chinese.txt`.
     - Reads each language's apology text from `lang.txt` in the corresponding subfolder.
     - For Kanakanavu, also reads special English and Chinese translations (`_en.txt` and `_zh.txt`).

### 2. `prettify(elem)`
   - Converts an XML element into a pretty-printed string format for readability.
   - **Parameters**: `elem` (an XML element).
   - **Returns**: A formatted XML string with indentation.

### 3. `generate_apology_xml(lang, lang_code, apologies, out_path)`
   - Generates an XML file for a specific language’s apology, structuring the data to include translations in English and Chinese.
   - **Parameters**:
     - `lang`: The name of the language being processed.
     - `lang_code`: The language code (ISO code) for the language.
     - `apologies`: Dictionary of apologies for each language, including translations.
     - `out_path`: Path to save the generated XML files.
   - **Functionality**:
     - Creates a root XML element with metadata for the specific language.
     - Iterates over each section of the apology, adding XML sentence (`S`) elements with `FORM` (text) and `TRANSL` (translations in Chinese and English).
     - For Kanakanavu, uses language-specific translations (`_en` and `_zh` files) instead of the main English and Chinese files.
     - Saves the formatted XML to the output path.

### 4. `main()`
   - Main function to set up paths, read apology texts, and generate XML files for each language.
   - **Functionality**:
     - Defines the language codes for each language.
     - Reads the apology texts for each language using `read_apologies()`.
     - Calls `generate_apology_xml()` for each language, creating XML files with mapped translations.

### 5. `__main__` Block
   - Sets up the environment for script execution by defining paths and calling `main`.
   - Ensures the `XML` directory exists for storing processed XML files.

---

## Key Components

- **Apology Text Mapping**: The script reads apology texts from different languages, including English and Chinese translations, and organizes them into a dictionary for processing.
- **XML Structure**: Each language's apology is structured into XML format with a root `TEXT` element containing `S` elements for each section. Each `S` element includes the apology text and translations.
- **Special Handling for Kanakanavu**: For Kanakanavu, the script uses unique English and Chinese translations (`_en` and `_zh`), instead of the main translation files.

## Output Explaination

All the output will be in the XML folder. There will be a file for each of the languages in the FormosanBank XML format.