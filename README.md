# Corpora

---

# Quality Control

This directory contains a set of Python scripts and resources for quality control (QC) and data processing for Formosan Bank, focusing on things orthography chceks, validation, cleaning data, etc. The intended use of each script and its functionality is outlined below.

---

## Table of Contents

1. [Repository Structure](#repository-structure)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Usage](#usage)
    - [Cleaning Scripts](#cleaning-scripts)
    - [Orthography Scripts](#orthography-scripts)
    - [Validation Scripts](#validation-scripts)
5. [Logs](#logs)

---

## Repository Structure

```plaintext

Corpora/
...

QC/
├── cleaning/
│   ├── clean_xml.py
│   ├── replace_non_ascii.py
│   └── validate_punct.py
├── orthography/
│   ├── logs/
│   │   ├── Amis_ePark
│   │   └── Amis_ILRDF_Dicts
│   ├── orthography_compare.py
│   └── orthography_extract.py
├── validation/
│   ├── logs/
│   ├── iso-639-3.txt
│   ├── validate_xml.py
│   └── xml_template.dtd
├── count_tokens.py
```

Each subfolder and script serves a specific purpose related to the quality control and processing of FormosanBank data.

---

## Prerequisites

- Python 3.6+
- Required libraries can be installed using `pip install -r requirements.txt` (see the [Installation](#installation) section for more details).
---

## Installation

Clone the repository and install dependencies.

```bash
git clone <repository-url>
cd FormosanBank
pip install -r requirements.txt
```

---

## Usage

### Cleaning Scripts

1. **`clean_xml.py`**
   - **Purpose**: Cleans XML files by removing unnecessary elements.
   - **Usage**: `python3 QC/cleaning/clean_xml.py [arguments]`
   - **Arguments**: _(Placeholder for specific arguments and examples)_

2. **`replace_non_ascii.py`**
   - **Purpose**: Replaces non-ASCII characters in text data to maintain consistency.
   - **Usage**: `python3 QC/cleaning/replace_non_ascii.py [arguments]`
   - **Arguments**: _(Placeholder for specific arguments and examples)_

3. **`validate_punct.py`**
   - **Purpose**: Validates and standardizes punctuation in text data.
   - **Usage**: `python3 QC/cleaning/validate_punct.py [arguments]`
   - **Arguments**: _(Placeholder for specific arguments and examples)_

### Orthography Scripts

1. **`orthography_compare.py`**
   - **Purpose**: Compares orthography variations within datasets.
   - **Usage**: `python3 QC/orthography/orthography_compare.py [arguments]`
   - **Arguments**: _(Placeholder for specific arguments and examples)_

2. **`orthography_extract.py`**
   - **Purpose**: Extracts orthographic features from text data for analysis.
   - **Usage**: `python3 QC/orthography/orthography_extract.py --language <language> --corpus <corpus>`
   - **Arguments**:
     - `--language`: Specifies the language to process (e.g., `Amis`).
     - `--corpus`: Specifies the corpus to use (e.g., `ePark`).

### Validation Scripts

1. **`validate_xml.py`**
   - **Purpose**: Validates XML files by ensuring they conform to a predefined structure, checking ISO language codes, and reformatting XML content.
   - **Usage**:
     ```bash
     python3 QC/validation/validate_xml.py <search_method> --language <language_code> --corpus <corpus_name> --path <file_path>
     ```
   - **Arguments**:
     - `--search_by`: Defines the method to search for validation (`by_language`, `by_corpus`, or `by_path`). Always required
     - `--language`: Specifies the language to be validated (required when searching `by_language`).
     - `--corpus`: Specifies the corpus name for validation (required when using `by_corpus`).
     - `--path`: Path to the XML file (or directory; if directory is provided, all XML files within will be checked) to be validated (required when using `by_path`).
     - `--corpora_path` Path to the directory containing all the corpora. (required when using `by_language` and `by_corpus`)
     - `--verbose` when used, Detailed logs will be saved in a log file. Log will include which files have been checked and a detailed record if whether there has been any issues or not. The search mood is indicated by the log file name. A summary of issues can be found the buttom of the log file

   - **Examples**:
     - Validate by language:
       ```bash
       python3 QC/validation/validate_xml.py by_language --language "Amis" --corpora_path "./Corpora"
       ```
     - Validate by corpus and use verbose:
       ```bash
       python3 QC/validation/validate_xml.py by_corpus --corpus "ePark" --corpora_path "./Corpora" --verbose
       ```
     - Validate by path:
       ```bash
       python3 QC/validation/validate_xml.py by_path --path "./Corpora/ePark/ep1_九階教材"
       ```
   - **Associated Files**:
     - `iso-639-3.txt`: A text file containing ISO 639-3 language codes used to verify that the `xml:lang` attribute in XML files contains a valid code.
     - `xml_template.dtd`: A Document Type Definition (DTD) file specifying the required structure of the XML files. The script validates XML files against this template to ensure consistency.

### Aditional Scripts

1. **`count_tokens.py`**
   - **Purpose**: Counts the current number of tokens in the corpora both by language and by source
   - **Usage**: `python3 QC/validation/count_tokens.py <corpora_path>`
   - **Example**: `python3 QC/validation/count_tokens.py ./Corpora`
   - **Output** The code will output the count for each language as well as the count per resource then will print the total token count across the corpora

---

## Logs

Each subdirectory contains a `logs` folder for storing log files generated by the scripts.

- **Orthography Logs**: Located in `QC/orthography/logs/`
- **Validation Logs**: Located in `QC/validation/logs/`

---