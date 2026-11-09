# Tsukida (2014): Seediq correlative clauses

Seediq example sentences from Naomi Tsukida's chapter "Correlative clauses in
Seediq", with the author's word-by-word glosses and English translations.

## Languages and dialects

Seediq (ISO 639-3 `trv`), dialect DeluValley. The one TEXT file under
`XML/Seediq/` carries `xml:lang="trv"` and `dialect="DeluValley"`. The chapter
names the dialect Teruku.

## Source

Tsukida, Naomi. 2014. Correlative clauses in Seediq. In I Wayan Arka and
N. L. K. Mas Indrawati (eds.), *Papers from 12-ICAL, Volume 2: Argument
realisations and related constructions in Austronesian languages*, printed
pages 69–79 (PDF pages 74–84). Asia-Pacific Linguistics.
[Open Research repository](https://openresearch-repository.anu.edu.au/items/8bfb8bf0-2f58-4eae-947c-bf9af50faf9f).

The chapter has 39 numbered example units. The corpus contains the 26 Seediq
ones. It leaves out the seven examples in other languages (Hindi, Warlpiri,
Diyari, English), the five the chapter stars as ungrammatical, and example 28a,
which repeats example 7. Examples 6 and 9 print an optional phrase in
parentheses, so each is two S (the longer one has an `-opt` id).

`XML/Seediq/tsukida_2014_correlative_clauses_in_seediq.xml` contains 28 S,
201 W and 268 M, with 497 original and 497 standard FORM, 497 original and 497
standard PHON, and 33 English translations. There is no audio.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Naomi-Tsukida-Correlative-Clauses-Seediq_corpora_stats.csv` and
appears on this corpus's page on the
[FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

Tsukida, Naomi. 2014. Correlative clauses in Seediq. In I Wayan Arka and
N. L. K. Mas Indrawati (eds.), *Papers from 12-ICAL, Volume 2: Argument
realisations and related constructions in Austronesian languages*, 69–79.
Asia-Pacific Linguistics.

See the FormosanBank [Terms of Use](https://formosanbank.github.io/FormosanBank/additional-resources/terms-of-use/).

## License

**License:** CC BY 4.0

**Rights source:** the chapter's own licence statement (Tsukida 2014, published CC BY 4.0); evidence: ask maintainer

Creative Commons Attribution 4.0 International (CC BY 4.0).

## Notes and caveats

- **Glottal stop.** The source uses a glottal stop, written with an apostrophe
  (`'`). It is removed from the standard tier because the standard orthography
  lacks glottal stops.
- **Spelling of the standard tier.** The standard tier applies only ŋ → ng and
  deletes the apostrophe. Tsukida writes many vowels e that the DeluValley
  teaching materials do not (deha / dha ‘two’, sehiga / shiga ‘yesterday’), and
  these are kept, because which ones to drop is not a letter-for-letter rule.
- **Orthography.** Tsukida does not specify the orthography used. References to
  papers by her that we have not seen suggest some differences in phonemes
  assumed than the standard orthographies, but we cannot yet confirm.

## Reproduction and processing

### How to reproduce

From a FormosanBank checkout, with its Python dependencies installed:

```bash
source .venv/bin/activate
bash Corpora/Naomi-Tsukida-Correlative-Clauses-Seediq/CodeAndDocs/generate_xml.sh
python -m pytest -q Corpora/Naomi-Tsukida-Correlative-Clauses-Seediq/CodeAndDocs/tests
```

`generate_xml.sh` uses the checkout three levels above `CodeAndDocs/` and
`python3`; `FORMOSANBANK_ROOT` and `PYTHON` name others. The FormosanBank commit
the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

### What each step does

Everything is built in a temporary staging directory and installed into `XML/`
only when every step has succeeded.

1. `build_xml.py` builds the S, W and M records from the transcription tables
   in `CodeAndDocs/raw_data/`: `reviewed_examples.tsv` (all 39 units, as
   printed), `reviewed_variants.tsv` (the two readings of examples 6 and 9) and
   `reviewed_morpheme_alignments.tsv` (the morphemes of the 11 words with an
   infix). It removes the square brackets around relative clauses in examples
   18, 19 and the second 27, in the Seediq and in 19's translation; writes
   infixes in angle brackets on the word tier (`b<en>arig=na`); and makes each
   slash alternative in a translation (`s/he`, `a/the`) its own translation,
   the second with `ver="alt"`, from `raw_data/translation_alternatives.tsv`.
   It also writes the coverage ledgers in `CodeAndDocs/intermediate/`.
2. `QC/cleaning/clean_xml.py`, with its report kept out of `XML/` (POL-033).
3. `standardize_with_clitic_spaces.py` runs `QC/utilities/standardize.py` with
   the shared `Orthographies/ConversionTables/Seediq_Tsukida_113.tsv`
   (`ŋ` → `ng`, `'` deleted). Around it, the step writes each sentence's `=`
   as a space and restores the original afterwards, so clitics are separate
   words in the standard sentence (`hiyi su`) while the original tier, word
   FORMs and glosses keep `=` (`hiyi=su`).
4. `QC/utilities/add_phonology.py --orthography Tsukida` generates the PHON
   tiers; the original tier is read with the shared `Orthographies/Tsukida/`
   profile.
5. The staged XML replaces `XML/`, and `provenance.json` records the tools.

**POL-047 deviation:** step 3 edits the sentence-level original FORM for the
duration of standardization, then restores it; the step stops if any original
does not come back exactly.

`CodeAndDocs/check_source_alignment.py` (read-only) checks the published XML
against the transcription tables, and `CodeAndDocs/validate.sh` runs it with
the tests and the shared validators, writing reports outside the corpus. The
transcription tables and `intermediate/article_pages_074_084_*.txt` (the
chapter's text, for the source checks) are the source baseline (POL-035); the
source PDF (SHA-256
`fab9b60ce52e47530805204c1d5beed02e52e63972e8315d9a1996c8e79248f1`) is not
needed to rebuild.
