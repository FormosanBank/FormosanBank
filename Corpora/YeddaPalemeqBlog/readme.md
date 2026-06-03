# Yedda Palemek's Blog 

This repository contains code and data for scraping and processing Formosan videos of the Paiwan Language (Southern Dialect); The blog can be found [here](https://yeddapalemeq.blogspot.com/). This scrape entails all of the 'Paiwan Every Day' posts, of which there are roughly 660

> [!WARNING]
> This script is not a good place to poke around if you are not an advanced Python user and aren't comfortable with complex web scraping! Yedda's blogspot has some tricky formatting issues that took a LONG time to figure out.

NOTE: Some of the glosses have the "em" infix. This causes a problem because enclosing "em" with <> results in a special phrase for XML and other markup languages. So whereever this occurs, we use HTML or XML escapes. 

## Project Structure

- **JSON/**: Contains a large JSON file of the first blog scrape with important fields like the english translation, the formosan sentence, and the gloss. 
- **Scripts/**: Python scripts for scraping and processing the blog posts 
  - `scrape.py`: Scrapes blog post data and throws it into a big JSON file 
  - `make_xml.py`: Converts JSON data to FormosanBank XML format
  - `analyze_xml.py`: Analyzes the generated XML files
- **Final_XML/**: Contains the final processed XML files

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/FormosanBank/formosan-yeddas-blog.git
   cd Formosan-Yeddas-Blog
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

### 1. Download the HTML
Run the scraping script to extract video information and metadata:

```bash
python Scripts/download_html.py
```

This will:
- Go through every blog post on Yedda's website 
- Extract the relevant information 
- Save it into a JSON file in the `JSON` directory

### 2. Generate XML Files
Scrape the downloaded HTMLs and create XML

```bash
python analyze_blog_structure.py
```

This will:
- Create XML files following the FormosanBank format
- Save the file into the `XML` 

### 3. Download audio

```bash
python Scripts/download_audio.py
```

### 4. Clean and Standardize XML, add IPA
Run the FormosanBank cleaning and standardization scripts.  Note we assume Ortho113. The only difference with Ortho94 is the addition of `o`, of which a tiny number appear in this text.

```bash
python path/to/FormosanBank/QC/cleaning/clean_xml.py --corpora_path path/to/Formosan-Yeddas-Blog/_XML
python path/to/FormosanBank/QC/utilities/standardize.py --corpora_path path/to/Formosan-Yeddas-Blog/XML --copy
python path/to/FormosanBank/QC/utilities/add_phonology.py --corpora_path XML --orthography Ortho113 
```

### 5. Fix XML ids
For some reason, we ended up with some repeated id attributes for some M elements. This will fix that.

```bash
python QC/validation/validate_xml.py by_path --path path/to/Formosan-Yeddas-Blog/_XML
```

## Contributing

Please feel free to submit issues and pull requests for any improvements.
