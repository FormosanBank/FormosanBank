# SEALS conference website

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

## Contents

This corpus contains the translated sections of the [2024 SEALS conference](https://sites.google.com/view/seals33/national-languages?authuser=0) website, graciously provided by the authors.

The 2024 South East Asian Linguistic Society meeting took place in Taipei. The main pages of the website were available in Seediq and Saisiyat (as well as Mandarin and English, which serve as the translation tiers here).

- `XML/Seediq/seediq_SEALS.xml` — 29 sentences, `xml:lang="trv"`, `dialect="unknown"`
- `XML/Saisiyat/saisiyat_seals.xml` — 29 sentences, `xml:lang="xsy"`

There is no audio and no word/morpheme segmentation.

## Project structure

- **`XML/`** — the published FormosanBank XML, one directory per language.
- **`CodeAndDocs/`** — reproduction infrastructure:
  - `pre_correction_snapshot/XML/` — pristine pre-cleaning snapshot (see below);
  - `make_xml.sh` — regenerates `XML/` from the snapshot (see below).

## Provenance and the pre-correction snapshot (POL-035)

The XML files were created **by hand**, by copy-and-paste from the conference website; there is no scraper and no raw source data committed, so the corpus is **not regenerable from source**. Per POL-035, before the automated cleaning pipeline first touched the published XML (2026-08-11), the pristine XML was snapshotted to `CodeAndDocs/pre_correction_snapshot/XML/`. That snapshot is the reproduction baseline: the published `XML/` is derived from it by the pipeline below, and (per POL-038) neither the snapshot nor the published XML is ever edited by hand.

## Processing pipeline

The entire post-scrape pipeline is wrapped by an executable script:

```bash
./CodeAndDocs/make_xml.sh [FORMOSANBANK_ROOT]
```

It first restores `XML/` from the pre-correction snapshot — the pipeline's starting point, since the corpus has no other source data — and then runs the three steps below, using the QC scripts of the FormosanBank checkout the corpus lives in (pass a path or set `FORMOSANBANK_ROOT` to use another checkout; set `PYTHON` to override the interpreter, which defaults to the root's `.venv`). The script is idempotent — it always rebuilds from the snapshot.

The steps, in order:

1. **Clean XML**

   ```bash
   python QC/cleaning/clean_xml.py --corpora_path Corpora/SEALS33/XML
   ```

   - Removes empty XML elements.
   - Flattens Unicode so that diacritics are merged with the characters they modify (NFC).
   - Replaces HTML escape codes with the corresponding characters and canonicalizes punctuation look-alikes (dashes, curly apostrophes) and null glyphs (`ø/Ø` → `∅`).
   - Quote-glottal correction makes no rewrites in this corpus: no quote evaluation runs for Seediq (no attestation dictionary), so the loan-autonym apostrophes in `'Tayal` (S16, S26) are preserved, and the Saisiyat pass changes nothing (it only emits audit flags). Warning sidecars (`cleaner_warnings.csv`) are per-run reports: review, then delete; never commit.

2. **Create the standard tier**

   ```bash
   python QC/utilities/standardize.py --corpora_path Corpora/SEALS33/XML --remove_accents
   ```

   - Copies every original `<FORM>` to a `kindOf="standard"` `<FORM>`, then deletes accents/stress diacritics and removes S-level null-morpheme units (`∅` plus any bridging hyphen).
   - No spelling conversion is applied (no TSV): the transcription is already the 94 Orthography, which for our purposes is the same as the 113 Orthography. In this corpus the originals carry no accents, so the only textual effect beyond the copy is the removal of the `∅` unit in S25 of each file.

3. **Add IPA**

   ```bash
   python QC/utilities/add_phonology.py --corpora_path Corpora/SEALS33/XML --orthography Ortho94
   ```

   - Adds a `<PHON>` element for each sentence-level `<FORM>`, containing IPA.
   - Ortho94 is used for the "original" tier because the text lacks the distinguishing features of Ortho113.
   - Note the tier semantics for Seediq `ey`: the original-tier profile voices `y` (→ `əj`), while the standard-tier profile treats `ey` as a digraph (→ `e`).

## Known caveats

- **S25** (both files) is a talk title containing reconstructed proto-forms (`*-ʔ, *-h, *-∅`). The asterisks are faithful to the source; the Saisiyat S25 is actually the English title, so its PHON is English-rendered-through-the-Saisiyat-profile.
- The Saisiyat file uses `:` for vowel length; it is retained in PHON for Saisiyat but treated as punctuation for Seediq.
