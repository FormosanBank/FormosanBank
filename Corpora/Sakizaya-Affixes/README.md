# Akiw (2012): Sakizaya affixes

Akiw, Chung-Wen Hsu. 2012. *The Study of Affixes in Sakizaya*. Master's thesis,
National Dong Hwa University. The corpus contains Sakizaya forms, Chinese
translations and source analyses from the numbered examples and affix tables.

## Languages and dialects

Sakizaya (ISO 639-3 `szy`, glottocode `saki1247`). Both TEXT files under
`XML/Sakizaya/` carry `xml:lang="szy"` and `dialect="Sakizaya"`.

## Source

The thesis's numbered examples, footnote and prose examples, and affix inventory
tables. The Chinese translations, alternative meanings, notes and morpheme
analyses follow an expert transcription of the thesis by Madeline Boese
(`CodeAndDocs/manual_edits.xml`). The source PDF is not distributed here.

Two TEXT files under `XML/Sakizaya/` contain 691 S: 244 numbered-example
readings, six footnote/prose examples and 441 affix entries (432 main-table rows
and 9 rows of the late summary tables), with 1,802 W, 2,605 M, 5,098 original
and 5,098 standard FORM, 5,098 standard PHON, 744 S translations and 4,496
untiered W/M source glosses. No source-supplied phonetic transcription is
included.

Of the thesis's 814 example and table units (261 numbered occurrences, 434
main-table rows, 113 late summary rows and six footnote/prose examples), the
corpus leaves out eleven exact repeats, the nine examples the source stars as
ungrammatical, and the 104 late summary rows that repeat a main-table row.
Phonology demonstrations, paradigms, lexical discussion and quoted analyses of
other languages are not included; this is not a transcription of every
linguistic item in the thesis. Example 23c prints an optional phrase, so it is
two S: `ha-min han mu-kan` and `ha-min han mu-kan kiya hemay` (scan p. 55,
POL-026).

Audio: none in the source.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Sakizaya-Affixes_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

Akiw, Chung-Wen Hsu. 2012. *The Study of Affixes in Sakizaya*. Master's thesis,
National Dong Hwa University.

See the FormosanBank [Terms of Use](https://formosanbank.github.io/FormosanBank/additional-resources/terms-of-use/).

## License

**License:** CC BY-NC 4.0

**Rights source:** Akiw Chung-Wen Hsu (the author), 2026-04-01; evidence: ask maintainer

Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0).

## Notes and caveats

- **Table-row translations are whole-word meanings, not glosses.** In the affix
  tables, a word's translation is its meaning as a whole word; its morphemes
  carry the table's affix and root columns. In the examples, the source
  sometimes glosses an unsegmented word as a complex form (`maku` ↔
  `m-我.屬格`); such words keep that gloss and have no M.
- **Examples printed twice are two S.** 27a/88a, 27b/88b, 49a/75a and 69a/82a
  are each kept twice because their printed glosses or analyses differ, so
  their sentences count twice.

## Reproduction and processing

### How to reproduce

From a FormosanBank checkout, with its Python dependencies installed:

```bash
source .venv/bin/activate
./Corpora/Sakizaya-Affixes/CodeAndDocs/generate_xml.sh
python -m unittest discover -s Corpora/Sakizaya-Affixes/CodeAndDocs -p test_source.py
```

`generate_xml.sh` uses the checkout three levels above `CodeAndDocs/` and
`python3`; `FORMOSANBANK_ROOT` and `PYTHON` name others. The FormosanBank commit
the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

### What each step does

Everything is built in a temporary staging directory and installed into `XML/`
only when every step has succeeded.

1. `generate_xml.py` builds the S records (original FORM and Chinese
   translation) from the two inventories in `CodeAndDocs/` and the TEXT
   metadata. It stops if the inventory and the transcription disagree.
2. `QC/cleaning/apply_manual_edits.py` applies the 670 transcription records
   (`manual_edits.xml`), which add every W and M and the alternative readings
   (POL-030).
3. `generate_xml.py --complete-transcription`, in order: expands 23c into its
   two readings (the shorter one has `-opt` IDs and only its own W, M and
   translation); adds the footnote and prose examples and four alternative
   translations in `source_data/supplemental_examples.json`; adds the records in
   `source_data/ruled_additions.json` (examples 75a, 87a, 88a, 88b, 90a and the
   9 late rows, each checked against its inventory row); applies the corrections
   in `source_data/ruled_corrections.tsv` (each row names the value it expects,
   so a changed input stops the build); and puts the table-row morphemes in word
   order with circumfixes written `X-Y`.
4. `QC/cleaning/clean_xml.py`, with its report kept out of `XML/` (POL-033).
5. `QC/utilities/standardize.py --remove_accents --segmented-without-m-tier`:
   the source already spells in the standard orthography, so no conversion
   table is used. The shared tool copies each original FORM and removes
   segmentation marks and null morphemes from the sentence-level standard FORM;
   `--segmented-without-m-tier` also removes the morpheme hyphen from footnote
   10's sentence, which has no M.
6. `QC/utilities/add_phonology.py` generates standard PHON.
7. The staged XML replaces `XML/`, and `provenance.json` records the tools.

The inventories and the transcription are the source baseline (POL-035); no
private scan, OCR cache or download is needed.

**POL-047 deviation:** original PHON is omitted because the source supplies no
phonetic transcription, and the source-specific completion step (step 3)
follows the manual transcription and precedes cleaning.
