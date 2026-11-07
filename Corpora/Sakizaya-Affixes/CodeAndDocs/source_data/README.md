# Source-derived build data

These files preserve source transcriptions, extraction decisions and mappings
from Akiw (2012). The final build reads `text_metadata.json`, the two main
inventories one directory above, `manual_edits.xml`, `supplemental_examples.json`,
`ruled_additions.json` (with `late_table_rows.csv`) and `ruled_corrections.tsv`. The other CSVs document the earlier extraction and remain source evidence.

- `text_metadata.json`: the two existing TEXT headers and output paths; both
  carry the licence `CC BY-NC 4.0` (maintainer, 2026-11-06).
- `supplemental_examples.json`: six scan-transcribed footnote/prose examples
  and four alternative Chinese readings, with stable IDs and page locators.
  These supplement the expert transcription without replacing its readings.

- `numbered_source_decisions.csv`: seeded examples, OCR corrections, reviewed gloss alignments, and numbered-example exclusions.
- `gloss_cell_replacements.csv`: verified recurrent OCR substitutions in interlinear gloss cells.
- `gloss_exceptions.csv`: exact G001 word IDs and readings from the independent
  August 14 expert submission. Joshua's August 10 corpus ruling (confirmed by the
  maintainer 2026-11-07) covers whole-word
  meanings beside affix/root columns and the thesis's unsegmented pronouns,
  case analyses and composite affixes. There are 413 table and 49 example cases
  (the twelve added with the 2026-11 ruled records are of the same two kinds);
  tests require those exact readings and reject any newly unreviewed G001 case.
  Physical scan pages 33, 37–39, 61, 73, 120, 128, 135 and 140–141 verify the
  distinct example conventions, including the restored null. This fixture does
  not waive other rules or establish complete source coverage. The supplemental
  footnote 15 composite prefix has its own scan-based regression fixture.
- `affix_analyses.csv`: source table ranges, affix forms, functions, and table numbers.
- `table_row_fixes.csv`: page-image-verified inventory-row corrections and the documented row 313 form mismatch.
- `late_table_rows.csv`: complete rows 435 through 547 with source pages, table numbers, forms, meanings, and unique linguistic fields where no earlier inventory row supplies them.
- `ruled_additions.json`: the records the maintainer ruled in that the expert
  transcription lacks (examples 75a, 87a, 88a, 88b, 90a; late rows 491–525), each
  checked against its inventory row by the build.
- `ruled_corrections.tsv`: the maintainer-ruled corrections to the expert
  transcription; each row names the value it expects, so a drifted input stops
  the build.

The late-table CSV and extraction report are retained as source evidence. The 2026-08-14 expert review excluded the whole dataset; the maintainer added back the 9 rows found nowhere else (2026-11-06: "B · Add the 9 unique rows"). The corrected release tiers are recorded in `CodeAndDocs/manual_edits.xml`.

The authoritative scan is `Private/source/akiw_2012_sakizaya_affixes_scan.pdf`, SHA-256 `fab787faf0e32cd087ba3dc222734132ad4213ca0804b8d5b32a318e66fbbbee`.
