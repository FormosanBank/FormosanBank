# SEALS conference website

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

This repository contains the translated sections of the [2024 SEALS conference](https://sites.google.com/view/seals33/national-languages?authuser=0), graciously provided by the authors. 

The 2024 South East Asian Linguistic Society meeting took place in Taipei. The main page of the website were available in Seediq and Saisiyat, as well as Mandarin and English. 

This repo is relatively simple because the XMLs were created by copy-and-paste, being relatively short.

## Project Structure

- **raw_data**: Directory containing the raw source data in text format. For Paiwan, there is also a helpful table showing what corresponds to what.

- **Final_XML**: Directories for the processed XML data in FormosanBank XML format, organized by language.

## Installation

1. Clone this repository:
   ```bash
   git clone git@github.com:FormosanBank/Formosan-SEALS.git
   cd Formosan-SEALS
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

1. **Clean XML and standardize punctuation**

   ```bash
   python path/to/FormosanBankRepo/QC/cleaning/clean_xml.py --corpora_path Final_XML
   ```

**Outputs**
   - This will update the XML files.

**Notes**
   - This removes empty XML elements
   - It also standardizes orthography (more-or-less), though a lot of this was done in previous steps (not documented above)
   - Unicode is flattened so that diacritics are merged with the characters they modify
   - HTML escape codes are replaced with the corresponding characters

2. **Standardize orthography**

   ```bash
   python path/to/FormosanBankRepo/QC/utilities/standardize.py --corpora_path path/to/FormosanWikipedias/Final_XML --copy
   ```

**Outputs**
   - Updates XML files

**Notes**
   - Creates a copy of every <FORM> element with kindOf="standard" attribute
   - Makes no changes, since the transcription is already the 94 Orthography, which for our purposes is the same as the 113 Orthography.

5. **Add IPA**

   ```bash
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML --orthography Ortho94
   ```

Ortho94 is used here for the "original" tier because the text lacks the distinguishing features of Ortho113.

**Outputs**
   - Updates XML files

**Notes**
   - Adds <PHON /> elements corresponding to each <FORM />, containing IPA.