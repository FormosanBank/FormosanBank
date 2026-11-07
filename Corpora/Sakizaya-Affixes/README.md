# Akiw (2012): Sakizaya affixes

Akiw, Chung-Wen Hsu. 2012. *The Study of Affixes in Sakizaya*. Master's thesis,
National Dong Hwa University. The corpus contains Sakizaya forms, Chinese
translations and source analyses from the numbered examples and affix tables.

## Languages and dialects

Sakizaya (ISO 639-3 `szy`, glottocode `saki1247`). Both TEXT files under
`XML/Sakizaya/` carry `xml:lang="szy"` and `dialect="Sakizaya"`.

## Source

The thesis's numbered examples and affix inventory tables. Madeline Boese's
August 14 review supplies the corrected Chinese, alternative meanings, notes,
morpheme analyses and exclusions. Regeneration preserves that complete
transcription; a new OCR pass does not replace it. Source and output review
preserves the expert transcription, restores missed footnote/prose examples and
translation readings, and verifies repeatable standalone builds. Example 17d
keeps its source null prefix; 23c has two aligned optional readings. The source
PDF is not distributed here.

Two TEXT files under `XML/Sakizaya/` contain 691 S: 244 numbered-example
readings, six footnote/prose examples and 441 affix entries (432 main-table rows
and 9 rows of the late summary tables), with 1,802 W, 2,605 M, 5,098 original
and 5,098 standard FORM, 5,098 standard PHON, 744 S translations and 4,496
untiered W/M source glosses. No source-supplied phonetic transcription is
included.

The committed inventories account for 814 units: 261 numbered occurrences,
434 main-table rows, 113 late summary rows and six footnote/prose examples.
Eleven exact repeats, nine source-starred examples and the 104 late summary rows
that repeat a main-table row are excluded. The collection covers sentence
examples and the affix inventory; phonology demonstrations, paradigms, lexical
discussion and quoted analyses of other languages remain source context. This is
not a transcription of every linguistic item in the thesis.
The 243 included numbered occurrences produce 244 S because 23c permits both
`ha-min han mu-kan` and `ha-min han mu-kan kiya hemay` (scan p. 55, POL-026).

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

The author's permission (2026-04-01) reads: "I'm happy to have the data from my
thesis included in FormosanBank to support the project and its research
applications." It names no licence; the maintainer chose CC BY-NC 4.0 for it on
2026-11-06.

## Notes and caveats

- **Whole-word meanings and complex glosses.** The source uses whole-word Chinese
  meanings beside separate affix/root analyses in the inventory, and sometimes
  glosses an unsegmented word as a complex form (`maku` ↔ `m-我.屬格`). These are
  kept as printed; such words have no M. The scoped list of these words is
  `CodeAndDocs/source_data/gloss_exceptions.csv` (the maintainer's August 10
  sign-off, confirmed 2026-11-07).
- **Incomplete analysis.** Some analyzed sentences have incomplete M coverage;
  four footnote examples have no word glosses. No missing analysis or gloss has
  been invented. Two morphemes the source leaves unglossed inside a glossed
  record (17d's null prefix `∅` and the affix of table row 20) are glossed
  `<UNCLEAR/>` (POL-061).
- **Repeated examples.** The thesis prints some examples twice. 27a/88a, 27b/88b,
  49a/75a and 69a/82a are each kept as two S because their printed glosses
  differ; 49a and 75a carry a note naming the difference. Example 104a repeats 2
  and is not kept separately.
- **Examples 87a and 90a** are printed unstarred, glossed and translated. The
  expert review removed them as ungrammatical; the maintainer restored them.
- **Corrections to the expert transcription.** Twelve Chinese OCR look-alikes
  that survived the expert review are corrected to the printed text (e.g. 探 →
  採 in five table rows and example 40b, `吹囗琴` → `吹口琴`); two table meanings
  wrongly split at a character inside one phrase (rows 152, 368; 368 had also
  lost 繩) are one translation again, as printed; a stray comma is removed from
  the word `duba'` (29a).
  Example 105a's translation keeps the evident 捕 where the source prints 補,
  with a note.
- **Late summary tables.** Of their 113 rows, the 9 found nowhere else in the
  thesis are included as table rows 491–525. Where the late table has no
  function column (table 108), the affix morpheme carries the table's title as
  printed, as the main-table rows carry their tables' function cells.
- **Morpheme notation in the inventory.** Table-row morphemes are in word order
  (a suffix follows its root), and their hyphens are dropped except as
  circumfix notation: the source's `ka-...-an` is written `ka-an`, and
  `ka-si-...-an` is written `kasi-an`. A composite prefix such as `ma-la-` is one
  morpheme, `mala`. The examples file already wrote affixes this way.
- **Repeated analyses.** Examples 69a/82a retain their different source analyses
  even though their standard forms agree.
- **Orthography and phonology.** The source uses Lin (2011)'s dictionary spelling
  (scan pp. 29–31); its retained letters align with Ortho113, so the standard
  tier is the original tier with segmentation marks and null morphemes removed.
  Only standard PHON is supplied, following the expert review; it represents the
  designated standard, not the source's narrower phonetic descriptions.

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
only, a rebuild always runs the current tools). A Gitless export retains its
record and reports that its tools revision needs separate verification. Source
acquisition and validation run separately from generation.

### What each step does

Everything is built in a temporary staging directory and installed into `XML/`
only when every step has succeeded.

1. `generate_xml.py` builds fresh pre-manual S records (original FORM and Chinese
   translation) from the two committed inventories and the TEXT metadata. It
   stops if the inventory and the expert transcription disagree.
2. `QC/cleaning/apply_manual_edits.py` applies all 670 expert correction records
   (`manual_edits.xml`), which add every W and M and the alternative readings.
   All manual records are retained, including no-ops (POL-030).
3. `generate_xml.py --complete-transcription`, in order:
   expands 23c into its two readings (preserving the longer reading's IDs and
   giving the shorter reading stable `-opt` IDs, with only its own W/M and
   Chinese translation); adds the scan-located supplement
   (`source_data/supplemental_examples.json`: footnotes 9, 10, 14 and 15, a
   prose example spanning PDF pages 130-131, and four source translation
   alternatives alongside the retained primary readings); adds the records the
   maintainer ruled in (`source_data/ruled_additions.json`: examples 75a, 87a,
   88a, 88b, 90a and the 9 late rows, each checked against its inventory row);
   applies the ruled corrections (`source_data/ruled_corrections.tsv`, each row
   naming the value it expects and the maintainer's words); and puts the
   table-row morphemes in word order with circumfixes written `X-Y`.
4. `QC/cleaning/clean_xml.py`, with its per-run report kept out of `XML/`
   (POL-033).
5. `QC/utilities/standardize.py --remove_accents --segmented-without-m-tier`:
   the source already spells in the standard orthography, so no conversion table
   is used; the shared tool copies each original FORM and removes segmentation
   marks and null morphemes from the sentence-level standard FORM. The shared
   `--segmented-without-m-tier` option removes the explicit morphology hyphen
   from the standard sentence in footnote 10 without inventing M analysis.
6. `QC/utilities/add_phonology.py` generates standard PHON.
7. The staged XML replaces `XML/`, and `provenance.json` records the tools.

The inventories plus complete manual transcription are the documented source
baseline (POL-035); no private scan, OCR cache, download or historical Git object
is needed.

**POL-047 deviation:** Original PHON is omitted under Madeline's August 13–14
decision because the source supplies no phonetic transcription. The
source-specific completion step (23c expansion, supplement, ruled records and
corrections, table-row morpheme order and circumfix notation) follows manual
transcription and precedes cleaning.
