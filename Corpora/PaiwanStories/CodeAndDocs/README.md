# Formosan-PaiwanStories

This repository contains code and data for processing and structuring the Paiwan Stories dataset into the [FormosanBank XML format](https://app.gitbook.com/o/tZF822XPLvjWkTiqbQyF/s/VETgkt5DVZWXBIolTyjW/the-bank-architecture/xml-standardize-format). The dataset includes various Formosan dialects and is organized to assist in linguistic research and language preservation.

## Project Structure

- **Final_XML**: Directory containing the processed data structured into FormosanBank XML format.
- **Original**: Original files received by source.
- **requirements.txt**: Lists the Python libraries required to run the processing scripts.

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

The XMLs were created by hand from the PDF. No automatic processing.

1. **Clean XML and standardize punctuation**

This isn't necessary because everything was already standardized. It is listed just to make it clear that we didn't forget to do it.

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

2. **Standardize XML, Part 2**

   ```bash
   python path/to/FormosanBankRepo/QC/utilities/add_original.py --corpora_path path/to/Formosan-ePark/Final_XML
   ```

3. **Standardize orthography**

   ```bash
   python path/to/FormosanBankRepo/QC/utilities/standardize.py --corpora_path path/to/FormosanWikipedias/Final_XML
   ```

**Outputs**
   - Updates XML files

**Notes**
   - Creates a copy of every <FORM> element with kindOf="standard" attribute
   - All u's are converted to o's.
