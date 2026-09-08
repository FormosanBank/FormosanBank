# Source-derived build data

These files preserve source transcriptions, extraction decisions and mappings
from Akiw (2012). The final build reads `text_metadata.json`, the two main
inventories one directory above, `manual_edits.xml`, and the standardization
TSV. The other CSVs document the earlier extraction and remain source evidence.

- `text_metadata.json`: the two existing TEXT headers and output paths; the
  permission prose remains unresolved under POL-042.

- `numbered_source_decisions.csv`: seeded examples, OCR corrections, reviewed gloss alignments, and numbered-example exclusions.
- `gloss_cell_replacements.csv`: verified recurrent OCR substitutions in interlinear gloss cells.
- `gloss_exceptions.csv`: exact G001 word IDs and readings from the independent
  August 14 expert submission. Joshua's August 10 corpus ruling covers whole-word
  meanings beside affix/root columns and the thesis's unsegmented pronouns,
  case analyses and composite affixes. There are 403 table and 47 example cases;
  tests require those exact readings and reject any newly unreviewed G001 case.
  Physical scan pages 33, 37–39, 61, 73, 120, 128, 135 and 140–141 verify the
  distinct example conventions, including the restored null. This fixture does
  not waive other rules or establish complete source coverage.
- `affix_analyses.csv`: source table ranges, affix forms, functions, and table numbers.
- `table_row_fixes.csv`: page-image-verified inventory-row corrections and the documented row 313 form mismatch.
- `late_table_rows.csv`: complete rows 435 through 547 with source pages, table numbers, forms, meanings, and unique linguistic fields where no earlier inventory row supplies them.
- `sakizaya_affixes_standardization.tsv`: corpus-local derived-tier rules that remove circumfix ellipses from standard M forms.

The late-table CSV and extraction report are retained as source evidence, but the full dataset is excluded from release XML by the 2026-08-14 expert review. The corrected release tiers are recorded in `CodeAndDocs/manual_edits.xml`.

The authoritative scan is `Private/source/akiw_2012_sakizaya_affixes_scan.pdf`, SHA-256 `fab787faf0e32cd087ba3dc222734132ad4213ca0804b8d5b32a318e66fbbbee`.
