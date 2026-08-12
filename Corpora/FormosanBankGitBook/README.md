# GitBook Translations

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.


These are translations of the FormosanBank GitBook into Formosan languages. So far, there is only Eastern Paiwan, generously contributed by Ruan Xuan.

This corpus contains code and data for recreating the XMLs.

## Project Structure

- **XML/**: The published, canonical FormosanBank XML, organized by language (currently `XML/Paiwan/`).

- **CodeAndDocs/raw_data**: Directory containing the raw source data in text format. For Paiwan, there is also a helpful table showing what corresponds to what.

- **CodeAndDocs/process_raw.py**: The script that converts the raw data in `raw_data/` into FormosanBank XML (the scrape/conversion step).

- **CodeAndDocs/make_xml.sh**: Executable script that runs **all post-scrape pipeline steps in order** (see "Post-scrape pipeline" below). The per-step notes below remain the reference for what each step does; `make_xml.sh` is their executable form.

## Installation

Run everything with the FormosanBank repository's Python environment (`.venv` in the repo root), which has all dependencies installed:

```bash
source path/to/FormosanBank/.venv/bin/activate
```

(`CodeAndDocs/requirements.txt` lists the minimal dependencies of `process_raw.py` if you want a standalone environment for the scrape step only.)

## Reproducing the XML

### Step 0 — Raw data to XML (scrape/conversion)

```bash
cd CodeAndDocs
python process_raw.py
```

**Output**
- Writes fresh XML to `CodeAndDocs/Final_XML/Paiwan/` (currently Eastern Paiwan only).
- The `dialect="Eastern"` attribute is set by `process_raw.py` itself. Since there are no glottocodes for Paiwan dialects, no glottocode attribute is created.
- To republish, replace the files in `XML/Paiwan/` with the fresh output, then run the post-scrape pipeline below.

### Post-scrape pipeline — `make_xml.sh`

All remaining steps run over the published `XML/` directory and are wrapped by one executable script:

```bash
./CodeAndDocs/make_xml.sh [path/to/FormosanBank]
```

The FormosanBank repo root argument is optional and defaults to the repository enclosing this corpus; set the `PYTHON` environment variable to pick an interpreter (defaults to the FormosanBank root's `.venv` python when present). The script runs steps 1–3 below in order. Their individual explanations follow.

#### 1. Clean XML and standardize punctuation

```bash
python path/to/FormosanBank/QC/cleaning/clean_xml.py --corpora_path XML
```

**Notes**
- Currently a content no-op for this corpus — the text is already clean.
- This removes empty XML elements.
- It also standardizes punctuation and canonicalizes look-alike characters (dashes, quotes, tildes).
- Unicode is flattened so that diacritics are merged with the characters they modify.
- HTML escape codes are replaced with the corresponding characters.
- Paiwan has an attestation dictionary, so quote/glottal correction is armed: any `'`→`"` corrections would be logged to `CodeAndDocs/quote_corrections.csv`. This corpus's single apostrophe (`pu'ui`) is a word-internal glottal and is untouched (0 corrections).

#### 2. Standardize orthography

```bash
python path/to/FormosanBank/QC/utilities/standardize.py --corpora_path XML --remove_accents
```

**Notes**
- Creates (or overwrites) a copy of every sentence-level `<FORM>` element with the `kindOf="standard"` attribute, then deletes accent/stress diacritics and removes null-morpheme units from the standard tier. No conversion table is applied.
- For this corpus the result equals a pure copy of the original tier: the transcription is already the 113 Orthography and contains no accents and no null units.

#### 3. Add IPA

```bash
python path/to/FormosanBank/QC/utilities/add_phonology.py --corpora_path XML --orthography Ortho113
```

**Notes**
- Adds `<PHON>` elements corresponding to each `<FORM>`, containing IPA (Ortho113 Paiwan profile, Eastern column).
- Punctuation is not carried into PHON.
- Characters outside the orthography surface as `*` in PHON: here these are digits, `%`, and Latin loanwords/proper nouns (e.g. `FormosanBank`, `NSF`, `XML`, `CC-BY-4.0`).
