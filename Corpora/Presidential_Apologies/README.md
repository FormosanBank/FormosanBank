# Presidential Apologies Data

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.


This repository contains code and data for processing and structuring translations of the Presidential Apology issued by the President of Taiwan towards Indigenous communities. The apology is available in the 16 official Formosan languages, as well as in Chinese and English translations. The data is organized to facilitate linguistic analysis and cultural preservation.

## Notes

*Kanakanavu* This corpus uses a small number of h's and f's, which are controversial. None of the words involving h's or f's appear in the reference ILRDF Dictionary corpus, with or without the h's and f's. Thus, we have chosen to leave them in.

*Puyuma* This corpus has a number of appearances of ē. Almost all of these are due to yēncumin (which is marked as a foreign word) and sēhu. Thus, this has not been homogenized.

*Sakizaya* A small number of f's appear to be foreign words.

Tsou and Kavalan both had a lot of annotations in Mandarin in parentheses (e.g. `zipun( 日 本 )`, `senfa(憲法)`). These are kept in the `original` tier (source fidelity) but removed from the `standard` tier, since they aren't actually part of the utterance and aren't in the translation; they are likewise masked out of the IPA. This removal is step 5 of the pipeline (`remove_standard_cjk_annotations.py`), so it survives a rerun of `standardize.py --copy`. Bare inline Mandarin terms (code-switched utterance content such as Tsou `'e 行政院 ho`) are *not* annotations and stay in both tiers; they surface as `*` in the IPA.

The PHON (IPA) tiers are generated from each file's declared `dialect` column of the Ortho113 orthography tables (Amis: Xiuguluan, Bunun: Junqun, Puyuma: Nanwang, ...). Some of these dialect columns mark letters as `NA` that nevertheless occur in these texts — mostly in Mandarin/Japanese loanwords (Puyuma `sēhu`, `yēncumincu`; Amis `Balay`) — and those letters surface as `*` in the IPA (e.g. Puyuma `yēncumincu` → `j*n*umin*u`). **This is intentional** (maintainer decision, 2026-08): the `*` faithfully marks a letter the declared dialect's orthography cannot transcribe, rather than borrowing a pronunciation from another dialect's column. (An earlier build used the `default` column for every file, which transcribed these letters but ignored the declared dialect.)

## Project Structure

- **Apologies**: Directory containing subdirectories for each Formosan language. Each language folder includes:
  - A PDF file of the apology in the specific language.
  - A TXT file of the apology, divided into 33 sections that correspond across all languages.

- **Chinese.txt** and **English.txt**: TXT files containing the apology in Chinese and English, respectively. Like the other languages, these are also divided into 33 sections.

- **Final_XML**: Directory for storing the processed XML files, structured according to the FormosanBank XML format.

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

***Output***

The processed XML files will be saved in the `Final_XML` directory.

2. **Clean XML and standardize punctuation**

   ```bash
   python QC/cleaning/clean_xml.py --corpora_path Corpora/Presidential_Apologies/XML
   ```

**Notes**
   - Normalizes punctuation and whitespace on the original tier and the translations. Chinese translations get the canonical full-width double quote (C002 Branch B: `「」`/curly quotes → `＂`).
   - Unicode is flattened so that diacritics are merged with the characters they modify; HTML escape codes are replaced with the corresponding characters.
   - (An earlier pipeline version needed `add_original.py` to tag FORM elements with `kindOf="original"`; that is baked into the XML now and the script has been retired.)

3. **Create the standard tier**

The files use the 113 Orthography (except possibly Thao, but nothing else matches better).

   ```bash
   python QC/utilities/standardize.py --corpora_path Corpora/Presidential_Apologies/XML --copy
   ```

**Notes**
   - `--copy` is a pure duplication: every `FORM kindOf="original"` gets a `kindOf="standard"` copy. The Mandarin-annotation removal happens in step 5, after the copy.

4. **Add IPA**

   ```bash
   python QC/utilities/add_phonology.py --corpora_path Corpora/Presidential_Apologies/XML --orthography Ortho113
   ```

**Notes**
   - Generates original and standard PHON from the Ortho113 tables, selecting each file's declared `dialect` column (see the Notes section above about `NA` letters).

5. **Remove Mandarin annotations from the standard tier**

   ```bash
   python Corpora/Presidential_Apologies/CodeAndDocs/remove_standard_cjk_annotations.py
   ```

**Notes**
   - Removes CJK parenthetical annotations from the standard FORM (original untouched) and regenerates PHON with the annotations masked. See the script docstring for exactly what counts as an annotation. Idempotent; safe to re-run.
   - Steps 2–5 are safe to re-run over the published `XML/` — each fully re-derives its outputs.



---

## Code Breakdown: `main.py`

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
   - Ensures the `Final_XML` directory exists for storing processed XML files.

---

## Key Components

- **Apology Text Mapping**: The script reads apology texts from different languages, including English and Chinese translations, and organizes them into a dictionary for processing.
- **XML Structure**: Each language's apology is structured into XML format with a root `TEXT` element containing `S` elements for each section. Each `S` element includes the apology text and translations.
- **Special Handling for Kanakanavu**: For Kanakanavu, the script uses unique English and Chinese translations (`_en` and `_zh`), instead of the main translation files.

## Output Explaination

All the output will be in the Final_XML folder. There will be a file for each of the languages in the FormosanBank XML format.