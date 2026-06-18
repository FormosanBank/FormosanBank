# Glosbe Amis-Chinese Dictionary Scraper

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

This repository contains code for scraping and processing Amis-Chinese translations from the Glosbe online dictionary into the [FormosanBank XML format](https://app.gitbook.com/o/tZF822XPLvjWkTiqbQyF/s/VETgkt5DVZWXBIolTyjW/the-bank-architecture/xml-standardize-format).

⚠️ **Important Note**: This project currently only handles Amis-to-Chinese translations from Glosbe. Other language pairs (including Amis-English) are not supported due to data quality and reliability concerns.

## Project Structure

- **work/**
  - **json/**: Directory containing processed JSON data files
    - `cleaned_amis_chinese_translations.json`: Cleaned and deduplicated translation pairs
  - **reference_amis/**: Directory containing reference Amis corpus
    - `Amis.xml`: Source XML corpus from ILRDF
  - **scripts/**: Python scripts for scraping and processing
    - `dedupe_zh.py`: Deduplicates collected translations
    - `make_xml.py`: Converts JSON to FormosanBank XML format
    - `scrape_zh.py`: Main scraping script for Amis-Chinese translations
    - `validate.py`: Validates XML output
    - `clean_xml.py`: Standardizes punctuation and cleans XML (optional)
- **Final_XML/**: Directory containing final XML output
  - `amis_glosbe.xml`: Final Amis-Chinese dataset
  - `example.xml`: Example XML file for reference

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/glosbe-scraper.git
cd glosbe-scraper
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

The process involves several steps to extract, scrape, clean and format the data:

1. **Extract Common Words**:
```bash
python work/scripts/extract_words.py
```

**Output**: Generates list of most frequent Amis words from reference corpus

2. **Scrape Translations**:
```bash
python work/scripts/scrape_zh.py
```

**Output**: Raw translation pairs saved to JSON

3. **Deduplicate Translations**:
```bash
python work/scripts/dedupe_zh.py
```

**Output**: Cleaned JSON file with unique translation pairs

4. **Convert to XML Format**:
```bash
python work/scripts/make_xml.py
```

**Output**: FormosanBank XML format in `Final_XML/amis_glosbe.xml`

5. **Validate XML** (Optional):
```bash
python work/scripts/validate.py
```

**Output**: Validation report of XML structure

6. **Clean XML** (Optional):
```bash
   python work/scripts/clean_xml.py
```

**Output**: Standardized punctuation and cleaned XML

7. **Update XML**

Replace-all: <FORM> -> <FORM kindOf="original">

8. **Add Traditional Chinese**

This was done semi-automatically. It's not easily reproducible.

9. **Standardize**

It looks like it's Ortho94 (mostly). But conversion won't change anything relevant.

```bash
   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML --copy
```

9. **Remove some colons**

Colons are used for introducing quotes in this text. However, colons have a specific meaning in the standard orthography, so replace with commas. 

```bash
   python work/scripts/fix_colon_quote.py
```

10. **Add IPA**

The IPA for Ortho94 is different from Ortho113, so go ahead and use it for the "original" tier.

```bash
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML --orthography Ortho94
```

## Code Breakdown

### scrape_zh.py
Main scraping script that:
- Extracts common Amis words from reference corpus
- Handles web scraping with rotating User-Agent headers
- Manages rate limiting and error handling

### make_xml.py
Converts JSON data to FormosanBank XML format with:
- Proper XML structure and metadata
- Language tags and IDs
- Translation pair organization

## Limitations & Ethical Considerations

- **Website Access**: Glosbe has implemented anti-scraping measures. Permission should be obtained before scraping.
- **Data Quality**: Only Amis-Chinese translations are included due to quality concerns with other language pairs.
- **Terms of Service**: While collected for academic research, scraping may violate Glosbe's terms of service.

## License

The data is provided under the **CC-BY-SA 4.0 (Attribution-ShareAlike)** license, as per Glosbe's terms of use.

## Acknowledgments

- Initial Amis XML corpus provided by ILRDF (Indigenous Language Research Development Foundation)
- Glosbe dictionary used as source for Amis-Chinese translations