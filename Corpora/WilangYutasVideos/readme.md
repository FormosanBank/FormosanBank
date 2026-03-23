# Wilang Yutas Videos

Wilang Yutas was an Atayal elder who, with his collaborator 劉宇陽, recorded a large number of videos speaking in Atayal, which can be found on his [YouTube Channel](https://www.youtube.com/@wilangyutas9297). Some of the audio is transcribed, and a smaller portion has been translated into Mandarin. Permission to republish was generously provided by Wilang Yutas's collaborator, 劉宇陽.



***

# Notes

* Many of the videos lack transcripts. These have XMLs that point to the audio file, but there are no <S> elements.
* Many other videos have only partial transcripts. In these cases, the main XML contains only the transcribed part of the audio. A second XML with the postfix "_untranscribed" has no <S>s and a reference to a file that contains the remaining audio.
* Segments that were not transcribable are marked as <UNCLEAR>. 
* Many videos involve multiple speakers. The original transcriptions have the second speaker's text in parentheses. We replaced the parentheses with periods so that the text will be standard. People who want to do diarization can inspect `make_xml.py` to figure out how to mark text by speaker (note that we don't have timestamps for seprate speakers).
* Time stamps are derived from the subtitles themselves. We do not guarantee that these align perfectly with the actual audio.

***

## Project Structure

- **raw_scrape/**: Contains raw .txt files scraped from the YouTube channel using the YouTube API
- **scripts/**: Python scripts for scraping and processing
  - `scrape_videos.py`: Scrapes video transcript data from YouTube into .txt files 
  - `make_xml.py`: Converts JSON data to FormosanBank XML format
  - `analyze_xml.py`: Analyzes the generated XML files
- **Final_XML/**: Contains the final processed XML files

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/FormosanBank/formosan-wilang-yutas-videos.git
   cd Formosan-Wilang-Yutas-videos
   ```

2. Install required Python packages(best done in a virtually environment):
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Scrape Video Data
Run the scraping script to extract video information and metadata:

```bash
python scripts/scrape_videos.py
```

This will:
- Call the YouTube transcripts API on all videos on the channel
- Extract the transcripts
- Save them into a .txt file in the `raw_scrape` directory
### 3. Generate XML Files
Convert the JSON data to FormosanBank XML format:

```bash
python scripts/make_xml.py
```

This will:
- Process all .txt files
- Create XML files following the FormosanBank format
- Organize files by language and dialect in the `Final_XML` directory
- Chinese in filenames will be changed to Pinyin.

### 4. Download the audio

Make sure fmpeg is installed (on Mac, use `brew install ffmpeg`).

```bash
   python scripts/download_audio.py
```

This will download the audio, convert to WAV, and then segment into units matching the subtitles (depending on how accurate the original time stamps were).

### 4. Clean and Standardize XML, add IPA
Run the FormosanBank cleaning and standardization scripts:

First, authors appear to have used strings of question marks to indicate unclear audio. We replace these with "<UNCLEAR>" because otherwise our clean_xml.py script removes them.

```bash
   find Final_XML -type f -name "*.xml" -exec sed -i '' -E 's/[?？]{3,}/ <UNCLEAR> /g' {} +
```

Now standard cleaning scripts:

```bash
   python path/to/FormosanBank/QC/cleaning/clean_xml.py --corpora_path path/to/Formosan-Wilang-Yutas-Videos/Final_XML
   python path/to/FormosanBank/QC/utilities/standardize.py --corpora_path path/to/Formosan-Wilang-Yutas-Videos/Final_XML --copy
   python path/to/FormosanBank/QC/utilities/add_phonology.py --corpora_path path/to/Formosan-Wilang-Yutas-Videos/Final_XML --orthography Ortho94
```

I'm just assuming it is Ortho94. They aren't much different, and it was done too long ago to reasonably be Ortho113.