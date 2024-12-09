
# Wikipedias Project

This repository contains code and data for retrieving, processing and structuring Wikipedia articles in various Formosan languages (namely Amis, Atayal, Paiwan, Sakizaya, and Seediq) into the FormosanBank XML format. The data collected from Wikipedia in these languages is organized to assist in linguistic research and cultural preservation.

## Project Structure

- **Articles**: Directory containing subdirectories for each Formosan language with available Wikipedia articles. Each language folder includes:
  - TXT files representing individual articles in that language.

- **XML**: Directory for storing the processed XML files, structured according to the FormosanBank XML format.

- **Titles**: Directory containing pickle files. Each pickle file corresponds to a language and contains a list of articles available in that language's Wikipedia.

- **citations_to_remove**: A pickle file containing section titles for citation sections, which are to be excluded during scraping as they do not contain useful content.

- **main.py**: The main script that:
  - Uses the Wikipedia API to retrieve a list of articles for each language and stores this data in the `Titles` folder.
  - Scrapes the articles from Wikipedia, saves them as text files in the `Articles` folder.
  - Processes the articles into XML format for the `XML` directory.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/Wikipedias_Project.git
   cd Wikipedias_Project
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

1. **Retrieve Wikipedia Articles**:
   Run `download.py` to use the Wikipedia API to scrape articles.
   
   ```bash
   python download.py
   ```

   **Outputs**:
      - The unmodified scraped article text files are saved in the `Articles` directory.
      - The list of article titles (per language) is saved as pickles in the `Titles` directory.

2. **Basic cleaning and creation of XML files**:
   Run `clean_articles.py` to use the Wikipedia API to scrape articles.
   
   ```bash
   python clean_articles.py
   ```

   **Outputs**:
      - The processed XML files are stored in the `XML` directory.
      - There are several log files that are useful for ensuring proper functioning
         - *link_removal.log*: Logs details of URLs removed from the text, including file path, line number, original line, and modified line.
         - *citations_remove.log*: Code automatically detects (mostly accurately) reference sections of wikipedia articles and removes them. This lists every file that had something removed and what was removed. 
         - *remove_possible_citations.log*: Some citations squeak through the above. The code finds sequences consisting of a new line that starts with a number, followed by a period. These are almost always citations. The log lists every file that had something removed and what was removed. 
         - *encoding_detection.log*: Logs the detected encoding of each file that couldn't be opened, including the file path and detected encoding.
         - *citation_marker_removal.log*: Logs details of citation markers removed from the text, including file path, line number, original line, and modified line.

3. **Delete non-Formosan Text**:
   Run `remove_other_langs.py` to use the Wikipedia API to scrape articles.
   
   ```bash
   python remove_other_langs.py
   ```

   **Outputs**:
      - This will update the XML files.

   **Notes**:
      - Everything that is removed is recorded in a log file.
         - *remove_Annotations.log*: There is a lot of commentary in non-Formosan languages, enclosed on parentheses. Often these are translations. Parentheses that contain mostly suspected non-Formosan text are removed. Every edit is logged with the file path and the section of text modified, with the part that was removed set aside within |||triple lines|||.
         - *remove_large_blocks.log*: Lines that contain mostly non-latin text are removed. The log lists the file path and the entire line that was removed. Note that this text sometimes contains a small amount of Formosan text, usually names of individuals.
         - *remove_character_strings.log*: Longish continuous segments of non-latin text are removed. Every edit is logged with the file path and the section of text modified, with the part that was removed set aside within |||triple lines|||.
         - *remove_empty_parentheses.log*: Does what is sounds like.

4. **Clean XML and standardize punctuation**

   ```bash
   python path/to/FormosanBankRepo/QC/cleaning/clean_xml.py --corpora_path path/to/FormosanWikipedias/XML
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
   python path/to/FormosanBankRepo/QC/utilities/standardize.py --corpora_path path/to/FormosanWikipedias/XML
   ```
   
   **Outputs**
      - Updates XML files

   **Notes**
      - Creates a copy of every <FORM> element with kindOf="standard" attribute
      - All u's are converted to o's.

## Developer Notes and Tools

### MakeListOfMarkers.py
   - Convenience code for adding lines of text that indicate all following are citations.
   - Result is saved in `citations_to_remove.pkl`
   - This can't be run from the command line. It's meant to be copied-and-pasted into the console.

### download.py

#### `retry(retries=3, delay=2, backoff=2)`
   - **Purpose**: A decorator function to retry a function execution with exponential backoff in case of failure.
   - **Parameters**:
     - `retries`: Number of retry attempts (default: 3).
     - `delay`: Initial delay between retries in seconds (default: 2).
     - `backoff`: Multiplicative factor for delay after each retry (default: 2).
   - **Usage**: Used to handle API request failures gracefully.

### `get_titles(lang_code, titles_path)`
   - **Purpose**: Retrieves Wikipedia article titles for a specific language using the language code.
   - **Parameters**:
     - `lang_code`: ISO code of the language.
     - `titles_path`: Path to save or retrieve the cached titles list.
   - **Functionality**:
     - Checks if the titles are already cached in a pickle file. If not, it retrieves titles from the Wikipedia API, saves them, and returns the list of titles.

### `read_article(title, wiki_wiki, citations_to_remove, lang_path)`
   - **Purpose**: Reads a Wikipedia article, cleans the text, and saves it.
   - **Parameters**:
     - `title`: Title of the article.
     - `wiki_wiki`: Wikipedia API instance.
     - `citations_to_remove`: List of unwanted sections.
     - `lang_path`: Path to save the cleaned article.
   - **Functionality**:
     - Retrieves and cleans the article, removing citations and links.

### `download_articles(titles, lang_path, lang_code, citations_to_remove)`
   - **Purpose**: Downloads and saves multiple articles for a language.
   - **Parameters**:
     - `titles`: List of article titles.
     - `lang_path`: Path to save the articles.
     - `lang_code`: Language code for Wikipedia.
     - `citations_to_remove`: List of citations to remove. Should come from citations_to_remove.pkl
   - **Usage**: Executes `read_article` in parallel using threading.

