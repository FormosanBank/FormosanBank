# Source-derived build data

These CSV files contain page-image-verified transcriptions and extraction decisions from Akiw (2012). The build scripts load them directly so linguistic mappings and source corrections remain reviewable data rather than Python constants.

- `numbered_source_decisions.csv`: seeded examples, narrow OCR corrections, gloss alignments, null-prefix handling, and POL-016 exclusions.
- `gloss_cell_replacements.csv`: verified recurrent OCR substitutions in interlinear gloss cells.
- `affix_analyses.csv`: source table ranges, affix forms, functions, and table numbers.
- `table_row_fixes.csv`: page-image-verified inventory-row corrections and the documented row 313 form mismatch.
- `late_table_rows.csv`: complete rows 435 through 547 with source pages, table numbers, forms, meanings, and unique linguistic fields where no earlier inventory row supplies them.

The authoritative scan is `Private/source/akiw_2012_sakizaya_affixes_scan.pdf`, SHA-256 `fab787faf0e32cd087ba3dc222734132ad4213ca0804b8d5b32a318e66fbbbee`.
