# Source-derived build data

Data from Akiw (2012). The build reads `manual_edits.xml` and the two main
inventories one directory up, and these files:

- `text_metadata.json`: the two TEXT headers and their output paths.
- `supplemental_examples.json`: six footnote and prose examples and four
  alternative Chinese translations, with stable IDs and page locators.
- `ruled_additions.json`: records the transcription lacks (examples 75a, 87a,
  88a, 88b, 90a and late table rows 506, 517, 523 and 525), each checked against its inventory
  row.
- `late_table_rows.csv`: rows 435–547 of the late summary tables, with pages,
  table numbers, forms and meanings; the corpus includes the four rows of
  table 109 found nowhere else in the thesis.
- `ruled_corrections.tsv`: corrections to the transcription; each row names the
  value it expects, so a changed input stops the build.

The corpus test reads:

- `gloss_exceptions.csv`: the words whose gloss is segmented differently from
  their form, as printed: whole-word meanings beside a table's affix and root
  columns (409 table rows), and the thesis's unsegmented pronouns, case-marked
  nouns and composite affixes (49 examples). The test requires exactly these
  readings and fails on any other G001 finding. Footnote 15's composite prefix
  has its own test.

Extraction evidence, not read by the build:

- `numbered_source_decisions.csv`: seeded examples, OCR corrections, reviewed
  gloss alignments and numbered-example exclusions.
- `gloss_cell_replacements.csv`: recurrent OCR substitutions in interlinear
  gloss cells.
- `affix_analyses.csv`: source table ranges, affix forms, functions and table
  numbers.
- `table_row_fixes.csv`: inventory-row corrections checked against the page
  images, and the row 313 form mismatch.

The source scan is not distributed (SHA-256
`fab787faf0e32cd087ba3dc222734132ad4213ca0804b8d5b32a318e66fbbbee`).
