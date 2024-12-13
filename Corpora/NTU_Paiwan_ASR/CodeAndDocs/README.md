
# NTU_Paiwan Data

This repository contains code and data for processing and structuring linguistic data collected in the Paiwan language. The data, collected by [Professor Sung](https://homepage.ntu.edu.tw/~gilntu/Faculty/Li-May_Sung.html) from National Taiwan University, includes both read text and spontaneous speach on various topics. 

## Notes

The names of the speakers are pseudonyms.

## Project Structure

- **Data**: Directory containing the raw source data in the Paiwan language, with audio recordings of scripted text read by participants. Each file is organized by topic and participant.

- **Final_XML/Paiwan**: Directory for the processed XML data in FormosanBank XML format, organized by the Paiwan language.

- **non_sp_data.json**: JSON file that describes the dataset, including details such as the number of topics read by each participant, file naming conventions, and other metadata.

- **main.py**: The main script that processes the raw data in the `Data` directory and converts it into the structured XML format defined by FormosanBank.

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
   Run `main.py` to process the raw data in the `Data` directory and structure it into XML format.

   ```bash
   python main.py
   ```

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
   python path/to/FormosanBankRepo/QC/cleaning/clean_xml.py --corpora_path path/to/FormosanePark/Final_XML
   ```

**Outputs**
   - This will update the XML files.

**Notes**
   - This removes empty XML elements
   - It also standardizes orthography (more-or-less), though a lot of this was done in previous steps (not documented above)
   - Unicode is flattened so that diacritics are merged with the characters they modify
   - HTML escape codes are replaced with the corresponding characters

4. **Standardize XML, Part 2**

   ```bash
   python path/to/FormosanBankRepo/QC/utilities/add_original.py --corpora_path path/to/FormosanWikipedias/Final_XML
   ```

**Outputs**
   - Updates XML files

**Notes**
   - Adds kindOf="original" attribute to all <FORM> elements. (This should normally be done in an earlier step, but wasn't for this corpus.)

5. **Standardize orthography**

   ```bash
   python path/to/FormosanBankRepo/QC/utilities/standardize.py --corpora_path path/to/FormosanWikipedias/Final_XML
   ```

**Outputs**
   - Updates XML files

**Notes**
   - Creates a copy of every <FORM> element with kindOf="standard" attribute
   - All u's are converted to o's.


## Code Breakdown

This section provides an in-depth code breakdown for the `main.py` script, which processes raw Paiwan language data and structures it into the FormosanBank XML format.

---

## Functions

### 1. `prettify(elem)`
   - Converts an XML element into a pretty-printed string format.
   - **Parameters**: `elem` (an XML element).
   - **Returns**: A formatted XML string with indentation for readability.

### 2. `create_root(p, id, audio)`
   - Creates the root XML element for a new document, setting attributes for the text.
   - **Parameters**:
     - `p`: The participant identifier.
     - `id`: The unique file identifier.
     - `audio`: The audio file path.
   - **Returns**: An XML `TEXT` element with specified attributes (e.g., ID, language, source).

### 3. `handle_participant(data_path, name, p_data, output_path)`
   - Processes each participant’s data, generating XML files and copying audio files.
   - **Parameters**:
     - `data_path`: Path to the raw data directory.
     - `name`: Participant’s name.
     - `p_data`: List of data entries for the participant, including file names and associated metadata.
     - `output_path`: Path to save the generated XML files.
   - **Functionality**:
     - Iterates over each entry in `p_data`, extracting information about the audio and annotation files.
     - Parses the ELAN (.eaf) file, creating XML sentence (`S`) elements with `FORM` (text) and `AUDIO` (timestamps).
     - Saves the generated XML to the output directory and copies the audio file if it doesn’t already exist.
     - Handles exceptions related to formatting XML or copying audio files.

### 4. `main(data_path, output_path)`
   - Main function to set up paths, read the JSON metadata, and call `handle_participant` for each participant.
   - **Parameters**:
     - `data_path`: Path to the raw data directory.
     - `output_path`: Path to save processed XML and audio files.
   - **Functionality**:
     - Loads participant metadata from `non_sp_data.json`.
     - Sets up directories for XML and audio output if they don’t exist.
     - Calls `handle_participant` for each participant, processing entries as described in the JSON file.

### 5. `__main__` Block
   - Sets up the environment for the script execution by defining paths and calling `main` with the appropriate directories.
   - Creates the `Final_XML/Paiwan` directory if it doesn’t exist.

---

## Key Components

- **Metadata Parsing**: The script loads metadata from `non_sp_data.json` to guide processing, determining the topics and file structures for each participant.
- **ELAN File Processing**: The script reads ELAN files (.eaf) for each data entry, parsing timestamps and aligning text with audio for structured storage.
- **Audio Management**: The audio files are copied into the XML output directory, ensuring local accessibility and consistency with the XML file paths.


## Output Explaination

All the output will be in the Final_XML folder. Since all the data is in Paiwan, all the output is in the subfolder Paiwan. The folder has subfolders for each participant; anonymized names were used. In the directory for each participant, there will be an XML file for each topic the participant read as well as an audio folder containing the audios associated with the participant.
