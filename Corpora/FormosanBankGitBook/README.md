
# GitBook Translations

These are translations of the FormosanBank GitBook into Formosan languages. So far, there is only Eastern Paiwan, generously contributed by Ruan Xuan.

This repository contains code and data for recreating the XMLs.

## Project Structure

- **raw_data**: Directory containing the raw source data in text format. For Paiwan, there is also a helpful table showing what corresponds to what.

- **Final_XML**: Directories for the processed XML data in FormosanBank XML format, organized by language.

- **process_raw.py**: The main script that processes the raw data in the `raw_data` directory and converts it into the structured XML format defined by FormosanBank.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/NTU_Paiwan.git
   cd NTU_Paiwan
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

1. **Process Raw Data to XML**:
   Run `process_raw.py` to process the raw data in the `raw_data` directory and structure it into XML format.

   ```bash
   python main.py
   ```

Currently, this only works for Eastern Paiwan.

**Output**
The processed XML files will be saved in `Final_XML/Paiwan`.

2. **Add dialect information**
Use `add_dialect.py` to add dialect information for the speakers.

```bash
python add_dialect.py --path Final_XML/Paiwan/speaker-name --dialect dialect
```

**Output**
- The XML roots will now have a `dialect` attribute. Since there are no glottocodes for Paiwan dialects, no glottocode attribute is created.

3. **Clean XML and standardize punctuation**

This isn't necessary because everything was already standardized. It is listed just to make it clear that we didn't forget to do it.

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

4. **Standardize orthography**

   ```bash
   python path/to/FormosanBankRepo/QC/utilities/standardize.py --corpora_path path/to/FormosanWikipedias/Final_XML --copy
   ```

**Outputs**
   - Updates XML files

**Notes**
   - Creates a copy of every <FORM> element with kindOf="standard" attribute
   - Makes no changes, since the transcription is already the 113 Orthography.

5. **Add IPA**

   ```bash
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML --orthography Ortho113
   ```

**Outputs**
   - Updates XML files

**Notes**
   - Adds <PHON /> elements corresponding to each <FORM />, containing IPA.