# Virginia Fey Amis Dictionary

Example sentences and phrases from Virginia Fey's (1986) *Amis Dictionary*
(阿美語字典), with English and Chinese translations. This candidate contains
2,042 Amis example records with English and Mandarin readings from Virginia
Fey’s dictionary and its maintained digital edition. The current development
output contains 2,042 S records from 2,012 source examples, in
`XML/Amis/Amis.xml`. It preserves source spelling and multiple meanings; no
audio or W/M analysis is supplied. This candidate remains under review. The
statistics below describe the checked-in candidate XML. On the old
documentation site this corpus was called Virginia Fey's Amis Dictionary. Two
points users ask about first: in the digital edition a sentence-initial capital
`G` is ng too, so S3846 reads `Nga'ayto` and S4934 `Nga'ayho`. This does not
recover phonemic contrasts absent from the source. Printed page 345 confirms
`O kalatolo / kalitolo konini.`; like every slash cell, it gives one sentence
per option (S6717 and S6717-opt). Both are explained under "Notes and caveats".

## Languages and dialects

The language is Amis (`ami`), dialect Xiuguluan. The corpus is one file,
`XML/Amis/Amis.xml`, whose `TEXT` element carries `xml:lang="ami"` and
`dialect="Xiuguluan"`. The source is routed to Xiuguluan: the dictionary's
introduction (printed page 13) identifies the main text as Central Amis; the
FormosanBank registry calls this dialect Xiuguluan.

## Source

The [source repository](https://github.com/miaoski/amis-data) and its maintained
spreadsheet provide the digital edition. Source versions, checksums, exact
corrections and dialect evidence are in
[source_decisions.json](CodeAndDocs/source_decisions.json).

Calista extensively corrected the original XML by hand. Joshua confirmed on
Basecamp card [7112943798](https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/7112943798)
that the lost converter need not be recreated. The immutable
`CodeAndDocs/pre_correction_snapshot/` is the POL-035 baseline. The build
preserves those translation readings and applies recorded source repairs,
rather than replacing the baseline with a new scrape.

[source_field_repairs.tsv](CodeAndDocs/source_field_repairs.tsv) records missing
source text with its exact witness and locator. It covers 503 unsplit examples;
16 affected slash rows and one corrected-Word reading are in the decision file.
An additional repeated translation was matched using the full source sentence.
The old upstream stemmer dropped prefixes and entire short words. Replaying it
reproduces 512 of the 519 sheet losses; the other seven have direct source
evidence. Its
[2016 fix](https://github.com/miaoski/amis-data/commit/23b6efd42fe3e73c0d3cd249c14587ca6349af9f)
preserves those pieces.

A sentence may have several English or Chinese translations. No W/M analysis
is supplied. No audio is supplied.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Virginia_Fey_Dictionary_corpora_stats.csv` and appears on this
corpus's page on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

* Fey, V. (1986). _Amis dictionary_. Taipei: The Bible Society.
* miaoski. (2023). _miaoski/amis-data_ \[Python]. GitHub. [https://github.com/miaoski/amis-data](https://github.com/miaoski/amis-data) (Original work published 2013)
* Wu, J. (2006). _Verb Classification, Case Marking, and Grammatical Relations in Amis_. University at Buffalo.

## License

**License:** CC BY-NC 3.0

**Rights source:** Taiwan Bible Society, grant date not recorded; evidence: ask maintainer.

The retained XML copyright field is: `CC BY-NC 3.0`

The pinned upstream README and licence state CC BY-NC 3.0. The publisher links
[Taiwan Bible Society correspondence dated 2008-10-07](https://drive.google.com/file/d/1s2_xzc_ZFbInk9wGXfVeUmvktJDZI5cb/view)
welcoming digitization, but that message does not specify a Creative Commons
licence or its grant date. Published XML said `CC BY-SA` until
2026-10-16, which matched neither the version nor the NonCommercial term of the
grant; the licence is now kept as granted, CC BY-NC 3.0 (maintainer ruling
2026-10-16). The licence is kept as granted, CC BY-NC 3.0, by maintainer ruling
2026-10-16 (*"CC BY-NC 3.0 (as granted; add to vocabulary)"*) rather than mapped
to 4.0 (POL-042).

The corpus is also subject to the central FormosanBank
[licence](https://github.com/FormosanBank/FormosanBank/blob/main/LICENSE.md) and
[AI use terms](https://github.com/FormosanBank/FormosanBank/blob/main/AI-USE-ADDENDUM.md).
Commercial AI use requires prior written permission.

## Notes and caveats

Source review remains incomplete; this output is not ready to port. The
[corpus PR #170](https://github.com/FormosanBank/FormosanBank/pull/170) lists the
remaining decisions. A successful build or XML check does not settle them.

- The digital source was checked against raw text, corrected Word files and
  conversion history. This is not a complete review of the printed dictionary.
- The digital edition writes the ng sound as `g` (printed guide, page 20), and its
  converter changed only lowercase `g`. A sentence-initial capital `G` is ng too,
  so S3846 reads `Nga'ayto` and S4934 `Nga'ayho` in both tiers (maintainer ruling
  2026-10-17). This narrow mapping does not recover phonemic contrasts absent
  from the source.
- [Printed page 345](https://drive.google.com/file/d/1eNMbHjQfC-ZR77ha17S_441hx9ZcsDhm/view)
  confirms `O kalatolo / kalitolo konini.` The page does not classify the pair
  as competing words or pronunciation variants; that decision remains open. The
  build gives one sentence per option (S6717 and S6717-opt).
- Li, Joby and Zeitoun (2024) note that Fey misses some phonemic contrasts,
  including glottal versus pharyngealized stops. Wu Ming-yi modernized the
  digital spelling, but this does not establish that the distinction was
  recovered. Generated PHON must not be treated as source transcription.
- A sentence may have several English or Chinese translations. Where two source
  rows give the identical Amis sentence, they are one sentence and the second
  row's translations are alternates. No W/M analysis is supplied.
- Source translations that were split or cleaned remain recoverable in TRANSL
  notes. Later readings use `ver="alt"`. A FORM `notes` attribute keeps the
  source cell only where it carries content beyond the corrected text: the full
  cell of a split slash cell, and S1193's stray English `Literally`. The sheet's
  converter-damaged text is not repeated in notes; it remains in the frozen
  sheet copy (maintainer ruling 2026-10-17).
- Sentences whose original FORM is identical are one sentence (POL-025,
  maintainer ruling 2026-10-17): the later record merges into the earliest and
  its translations become `ver="alt"`. Eight such pairs exist; the merged-away
  ids S2843, S3026, S5023, S5280, S5703, S6241 and S6916 are retired (main had
  already retired them), and S5991-opt, which the build creates from the slash
  cell `talakal / tilo ni Idek.`, is merged into S1945 in the same step, so it
  never appears in the published XML. Records that the source repair made
  different (S1899/S1900, S5141/S5142) stay separate. Historical published IDs
  stay stable. New S readings use `-opt`.
- One published sentence is removed: S6908 `ceco.`, the third option of the
  slash cell `sasoken a kowa' / cacoscosen a kowa' / ceco.` (Pith Paper Plant),
  because it is not clear how it should be read (maintainer ruling 2026-10-17);
  its id is retired, and the full cell remains in the FORM notes of S2761 and
  S6907.

#### References

Fey, V. (1986). *Amis dictionary*. Taipei: The Bible Society.

Li, P. J. K., Joby, C., & Zeitoun, E. (2024). Word Lists and Dictionaries of
Formosan Languages. In *Handbook on Formosan Languages*. Brill.

## Reproduction and processing

### How to reproduce

```bash
bash Corpora/Virginia_Fey_Dictionary/CodeAndDocs/generate_xml.sh
```

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

Run `bash Corpora/Virginia_Fey_Dictionary/CodeAndDocs/generate_xml.sh` in the candidate
FormosanBank checkout. The [README](https://github.com/FormosanBank/FormosanBank/blob/45578e57a9e1c768394df211f16aed14ab4c87b2/Corpora/Virginia_Fey_Dictionary/README.md)
documents dependencies, source coverage and any scoped pipeline deviations. The
[build provenance](https://github.com/FormosanBank/FormosanBank/blob/45578e57a9e1c768394df211f16aed14ab4c87b2/Corpora/Virginia_Fey_Dictionary/CodeAndDocs/provenance.json)
records the actual tools used for the retained output; it does not select or pin
tools for later builds. The candidate XML and reproduction package match the reviewed private
development commit
([commit 45578e57](https://github.com/FormosanBank/FormosanBank/tree/45578e57a9e1c768394df211f16aed14ab4c87b2/Corpora/Virginia_Fey_Dictionary/)). This proposal has since been
merged: commit 45578e57 is on `main`.

Use the current FormosanBank tools and their Python dependencies. From the
corpus folder, build and then check:

```bash
./CodeAndDocs/generate_xml.sh /path/to/FormosanBank
python3 CodeAndDocs/audit_source_alignment.py --path XML/Amis/Amis.xml
python3 -m pytest CodeAndDocs/tests
```

An embedded `Corpora/Virginia_Fey_Dictionary` checkout is detected automatically.
`FORMOSANBANK_ROOT` selects another tools checkout and `PYTHON` selects its
interpreter. The build uses committed inputs and performs no source download.

The build starts from the preserved hand-corrected baseline and pinned digital
source, applies source-located repairs, and runs the current shared tools. It
accounts for 2,012 complete source rows while retaining 2,039 of the 2,040
published sentence IDs and adding three (S1900, S5142, S6717-opt). S6908
`ceco.`, the third option of a slash cell, is removed because it is not clear
how it should be read. Spelling and sound use the shared Amis tables
(Xiuguluan).

The entry point restores the snapshot, checks historical duplicate IDs,
reconciles source fields, runs shared cleaning, then standardizes and generates
PHON with the shared tables (`Orthographies/ConversionTables/Amis_Church_113.tsv`,
Xiuguluan column, and the Ortho113 profile) before shared deduplication.
Validation runs separately. The source audit checks the recorded inventory and
corrections; passing it does not resolve the remaining source questions. Run
the full FormosanBank audit and QC workflow separately.

**POL-047 deviation:** The historical ID guard and recorded source repairs
precede cleaning; reference-resource deduplication follows derived tiers.

The actual tools commit is recorded in
[provenance.json](CodeAndDocs/provenance.json), never used to select or pin a
future tools checkout. A Git-free export retains that record and requires
independent verification of its tools revision. Rebuild twice to verify all
declared outputs. Per-run cleaner and standardization warnings are disposable;
any `CodeAndDocs/quote_corrections.csv` is durable correction evidence.

### What each step does

[CodeAndDocs/generate_xml.sh](CodeAndDocs/generate_xml.sh) runs these steps in
order and stops at the first failure (`set -euo pipefail`).

1. **Find the tools.** The FormosanBank checkout is `FORMOSANBANK_ROOT`, else the
   script's first argument, else the repository the corpus sits in (when
   `../../QC` exists), else a sibling `../FormosanBank`. `PYTHON` picks the
   interpreter (default `python3`). The script stops unless
   `QC/cleaning/clean_xml.py` and `CodeAndDocs/pre_correction_snapshot/Amis/Amis.xml`
   both exist.
2. **Restore the baseline.** `XML/` is deleted and recreated, and the snapshot
   `CodeAndDocs/pre_correction_snapshot/` (Calista's hand-corrected XML) is
   copied into it.
3. **[fix_duplicate_ids.py](CodeAndDocs/fix_duplicate_ids.py) `--path XML`.**
   Gives the second and later copies of a repeated `S` id a letter suffix
   (`S3797` → `S3797b`), editing only the `id` attribute text. The snapshot
   already carries that fix, so in this build the script is a guard that
   changes nothing ("No duplicate S ids found"). It must change nothing: the
   next step refuses any file whose hash differs from the recorded baseline.
4. **[reconcile_source.py](CodeAndDocs/reconcile_source.py) `--path XML/Amis/Amis.xml`.**
   Reads [source_decisions.json](CodeAndDocs/source_decisions.json) and
   [source_field_repairs.tsv](CodeAndDocs/source_field_repairs.tsv), then:
   - **Checks its inputs** and stops on any mismatch: the SHA-256 of the
     baseline, of the frozen spreadsheet `CodeAndDocs/source/virginia_fey_source.csv`
     (6,899 data rows, the expected seven-column Chinese header, 2,012 rows with
     an Amis example and both translations) and of each vendored upstream file
     in `CodeAndDocs/source/upstream/`; that the XML file is byte-identical to
     the baseline and has 2,049 `S`; and, for each of the 503 repair rows, that
     the recorded `raw_form` with lowercase `g` turned into `ng` equals the
     repaired `form` (a check only; that conversion is never applied to the XML).
   - **Sets `TEXT` attributes** `source` (the amis-data tree at commit
     `494e5e4b…`) and `copyright` (`CC BY-NC 3.0`).
   - **Slash cells** (37 rows in `form_variants`): the first option keeps the
     row's id, each further option becomes a copy of that `S` with its own id;
     each gets its own original `FORM`, and the full source cell goes in the
     `FORM` `notes`.
   - **Single-form repairs** (3 decisions in the JSON plus the 503 TSV rows):
     the original `FORM` text is replaced by the repaired text; `notes` keeps
     the sheet text only where `keep_source_form_note` is set (S1193), and is
     removed otherwise. Every `S` touched here or by the slash step loses its
     standard `FORM` and `PHON`, which later steps regenerate.
   - **Removes** S6908 (`ceco.`), after checking it still reads `ceco.`.
   - **Structural repair:** removes the stray `、` between S1117's two Mandarin
     translations.
   - **Translation repairs** (8 recorded old → new texts, such as S277
     `spiritualityh` → `spirituality`); then drops repeated translations
     within an `S` (exactly 1 expected) and marks every translation after the
     first in each language `ver="alt"`.
   - **Translation splits** (2): one translation becomes several, later ones
     `ver="alt"` (S413 → "He saved me (physically)" / "He saved me (spiritually)").
   - **Keeps the source translation:** where an `S`'s English or Chinese
     translations no longer equal the sheet cell, the full sheet cell is stored
     in the first translation's `notes`.
   - **Merges sentences with the same original `FORM`** into the earliest one,
     moving the later ones' translations over as `ver="alt"` and dropping
     repeats; the result must equal the 8 merges recorded in the JSON.
   It then writes the file and prints a one-line summary of the counts.
5. **`QC/cleaning/clean_xml.py --corpora_path XML`** (shared cleaning:
   punctuation, whitespace, quote and character normalization). No
   `--warnings_dir` is passed, so the per-run `cleaner_warnings.csv` is written
   into `XML/` when there are warnings and removed when there are none; actual
   quote rewrites are appended to `CodeAndDocs/quote_corrections.csv`.
6. **`QC/utilities/standardize.py --corpora_path XML --tsv_path Orthographies/ConversionTables/Amis_Church_113.tsv --target_column Xiuguluan`**
   writes the standard `FORM` from the original `FORM` using the Xiuguluan
   column of the shared Amis table, deriving capital-letter rules from the
   table's source profile. Warnings go to `XML/standardize_warnings.csv`.
7. **`QC/utilities/add_phonology.py --corpora_path XML --orthography Ortho113`**
   writes `PHON` for the original and the standard tier from the shared
   Ortho113 tables (the IPA column is chosen from the dialect).
8. **`QC/cleaning/remove_duplicate_sentences.py by_path --path XML --apply`**
   (defaults: within the file, standard tier). Two `S` count as duplicates only
   if their standard `FORM` and their full set of translations both match; the
   first by `S` id is kept, and any translation of a removed `S` the survivor
   lacks is added to it as `ver="alt"`.
9. **Provenance.** If the tools checkout is a Git repository, its `HEAD` commit
   is written to [CodeAndDocs/provenance.json](CodeAndDocs/provenance.json);
   otherwise the existing file must be present and the script says to verify
   the export's tools revision separately.

The checks are run by hand, not by `generate_xml.sh`:
[audit_source_alignment.py](CodeAndDocs/audit_source_alignment.py) re-reads the
same pinned inputs and fails on any finding: `TEXT` language, dialect and the
two header values; duplicate or missing/extra `S` ids against the expected
inventory; stray character content; each original `FORM` and its `notes`
against the recorded source; any remaining `/` in an original `FORM`; both
`eng` and `zho` translations present, no repeats, `ver="alt"` on later ones,
every sheet translation present as a translation or a note, and no English
word or Chinese character in the output that the sheet lacks (except the
recorded `translation_token_exceptions`).
[tests/test_source_reconciliation.py](CodeAndDocs/tests/test_source_reconciliation.py)
runs `reconcile_source.py` on a copy of the baseline and checks restored words,
the capital-`G` rule, ids, merges, notes, translation repairs and that a
changed baseline is refused.
