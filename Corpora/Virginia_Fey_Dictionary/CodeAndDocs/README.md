# Formosan-VirginiaFey

This repository contains code and data for processing and structuring the Virginia Fey's Amis Dictionary dataset into the [FormosanBank XML format](https://app.gitbook.com/o/tZF822XPLvjWkTiqbQyF/s/VETgkt5DVZWXBIolTyjW/the-bank-architecture/xml-standardize-format).

## Notes

1. According to Li et al. (2024), "Fey’s (1986) dictionary ... misses certain phonemic contrasts, such as the distinction between the glottal stop and the pharyngealized stop, for example, e.g., Central Amis ’op’op ‘frog’ vs. qopo ‘assemble’."

However, the repo from which this corpus is derived states:

> Thanks to Mr. Wu Ming-yi for rewriting the old Catholic spelling into the newer spelling of the original Minzu Kung Hui version.

It is not clear whether this addressed the concerns raised by Li and colleagues, but the orthography seems to be a good match for our reference corpus. 

2. There are often multiple translations into the same non-Formosan language for a particular sentence. Thus do not assume there is only one <TRANSL> element per target language.

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

The XML was created using a CSV provided by https://github.com/miaoski/amis-data. It was then cleaned by hand to address parantheticals and other annotations.

1. **Clean XML and standardize punctuation**


   ```bash
   python path/to/FormosanBankRepo/QC/cleaning/clean_xml.py --corpora_path path/to/repo/Final_XML
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
   python path/to/FormosanBankRepo/QC/utilities/add_original.py --corpora_path path/to/repo/Final_XML
   ```

3. **Standardize orthography**

This doesn't actually do anything other than create a `kindof="standard"` tier, since the orthography matches what we expect.


   ```bash
   python path/to/FormosanBankRepo/QC/utilities/standardize.py --corpora_path path/to/repo/Final_XML
   ```

**Outputs**
   - Updates XML files

**Notes**
   - Creates a copy of every <FORM> element with kindOf="standard" attribute
   - All u's are converted to o's.


## References

Li, P. J. K., Joby, C., & Zeitoun, E. (2024). Word Lists and Dictionaries of Formosan Languages. Handbook on Formosan languages: The indigenous languages of Taiwan. Leiden: Brill.

## License

According to [https://github.com/miaoski/amis-data](https://github.com/miaoski/amis-data)(the github repo we sourced this from), permission for a CC-BY-NC license was provided by the Taipei Bible Society:

>謹感謝 台灣聖經公會 授權電子化。商業使用之授權，請洽[台灣聖經公會]。

>感謝吳明義老師將天主教的舊式拼法，改寫成原民會版本的新式拼法。

>This work is licensed under the Creative Commons 姓名標示-非商業性 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-nc/3.0/deed.zh_TW.
