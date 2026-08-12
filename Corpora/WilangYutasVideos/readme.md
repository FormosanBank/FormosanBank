# Wilang Yutas Videos

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

Wilang Yutas was an Atayal elder who, with his collaborator 劉宇陽, recorded a large number of videos speaking in Atayal, which can be found on his [YouTube Channel](https://www.youtube.com/@wilangyutas9297). Some of the audio is transcribed, and a smaller portion has been translated into Mandarin. Permission to republish was generously provided by Wilang Yutas's collaborator, 劉宇陽.

All text is Atayal (`tay`), dialect Sekolik. 82 XML files; 34 carry transcripts (3,014 sentences), the rest are no-transcript stubs and `*_untranscribed` audio companions.

***

# Notes

* Many of the videos lack transcripts. These have XMLs that point to the audio file, but there are no `<S>` elements.
* Many other videos have only partial transcripts. In these cases, the main XML contains only the transcribed part of the audio. A second XML with the postfix `_untranscribed` has no `<S>`s and a reference to a file that contains the remaining audio.
* Segments that were not transcribable are marked as `<UNCLEAR/>`.
* Many videos involve multiple speakers. The original transcriptions have the second speaker's text in parentheses. We replaced the parentheses with periods so that the text will be standard. People who want to do diarization can inspect `make_xml.py` to figure out how to mark text by speaker (note that we don't have timestamps for separate speakers).
* A few sentences quote Japanese song lyrics (kana/kanji) and one sentence contains a Bopomofo fragment (`ㄇ`) from the transcriber; these are faithful to the source subtitles and are intentionally kept.
* Time stamps are derived from the subtitles themselves. We do not guarantee that these align perfectly with the actual audio.

***

## Project Structure

- **XML/Atayal/**: the published FormosanBank XML files (canonical data)
- **CodeAndDocs/raw_scrape/**: the raw `.txt` transcript files scraped from the YouTube channel using the YouTube API (committed — the corpus text regenerates from these without network access)
- **CodeAndDocs/scripts/**: Python scripts for scraping and processing
  - `scrape.py`: scrapes video transcript data from YouTube into `.txt` files
  - `make_xml.py`: converts the `.txt` transcripts to FormosanBank XML (Chinese in filenames is converted to Pinyin)
  - `download_audio.py`: downloads and segments the audio (dev-repo use; end users should use `download_audio_data.sh`)
  - `issues.py`: ad-hoc analysis helper
- **CodeAndDocs/make_xml.sh**: one-command wrapper for the post-scrape QC pipeline (see below)
- **download_audio_data.sh**: pulls the published audio from Hugging Face

## Reproducibility

Everything a text correction could touch regenerates deterministically from the **committed** `CodeAndDocs/raw_scrape/` transcripts via `make_xml.py` + the pipeline below; only the no-transcript stubs and the audio segmentation require live YouTube access.

## Usage

### 1. Scrape video data (network; only to refresh the corpus from YouTube)

```bash
python CodeAndDocs/scripts/scrape.py
```

This calls the YouTube transcripts API on all videos on the channel, extracts the transcripts, and saves them as `.txt` files in `raw_scrape/`.

### 2. Generate XML files

```bash
python CodeAndDocs/scripts/make_xml.py
```

This processes all `.txt` files, creates XML files following the FormosanBank format (organized by language and dialect; in the dev-repo layout the output directory is `Final_XML/`, published here as `XML/`), and converts Chinese in filenames to Pinyin.

### 3. Download the audio

End users: run `./download_audio_data.sh` (requires `git-lfs`, `jq`, and the `hf` CLI). Rebuilding from YouTube instead uses `CodeAndDocs/scripts/download_audio.py` (requires `ffmpeg`), which downloads the audio, converts it to WAV, and segments it into units matching the subtitles (as accurately as the original time stamps allow).

### 4. Clean and standardize XML, add IPA

One command (from anywhere; pass the FormosanBank root if this corpus is checked out elsewhere):

```bash
CodeAndDocs/make_xml.sh [path/to/FormosanBank]
```

which runs, in order, over `XML/`:

```bash
python QC/cleaning/clean_xml.py --corpora_path Corpora/WilangYutasVideos/XML
python QC/utilities/standardize.py --remove_accents --corpora_path Corpora/WilangYutasVideos/XML
python QC/utilities/add_phonology.py --corpora_path Corpora/WilangYutasVideos/XML --orthography Ortho94
```

Step by step:

1. **`clean_xml.py`** canonicalizes characters and punctuation (e.g. wave-dash `〜` → `~`) and writes a per-run `cleaner_warnings.csv` sidecar, which is reviewed and deleted, never committed.
2. **`standardize.py --remove_accents`** rebuilds the standard tier as a copy of the original with accents (combining acute/breve) deleted and null units removed. No conversion table exists for this corpus, so no orthographic letter conversion is applied; the Sekolik transcripts contain no such accents, so the standard tier currently equals the original tier verbatim (the Japanese kana dakuten are not accents and are untouched). Source hyphens in Japanese loanwords (e.g. `Karen-ko`, `Tay-To`) therefore remain on the standard tier until a conversion table exists.
3. **`add_phonology.py --orthography Ortho94`** regenerates the PHON tiers. The original-tier PHON assumes the **Ortho94** orthography — an assumption: the transcripts predate Ortho113, and the two differ little for Atayal.

Audio files are never touched by this pipeline.
