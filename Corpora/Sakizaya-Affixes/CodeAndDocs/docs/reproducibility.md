# Reproduction inputs

The canonical entry point is `CodeAndDocs/generate_xml.sh`. It runs with current
FormosanBank tools and records [provenance](../provenance.json); the former
historical-tools pin and combined download/build/QC wrappers are retired.

The 670 retained source IDs and locations come from `extraction_report.csv`
and `table_extraction_report.csv`. `source_data/text_metadata.json` preserves
the two existing TEXT headers. `manual_edits.xml` is the complete expert
transcription of those S records, including all W/M and alternative readings.
Every build reconstructs fresh S records before applying the shared manual
edits, the source-specific 23c expansion and supplement, the maintainer's ruled
additions and corrections (`source_data/ruled_additions.json`,
`source_data/ruled_corrections.tsv`) and the table-row morpheme order, then the
cleaner, standardizer and standard phonology tool, all in a staging directory. The baseline does not read previous final XML.
This transcription-based reconstruction implements
POL-035/POL-047/POL-048 without redistributing the private scan.

The transcription originated in Madeline's expert submission at commit
`45d58b084295a9800a809502976c23a0f400e93a`, integrated by `85abf3b`.
The integration repaired two malformed XML tags but also removed 17d W1's
source-backed null prefix. The current manual record restores that prefix
from physical scan pages 37–38 and adds null/root M under POL-012. Original S
also retains the printed prefix, correcting the expert file's omission and
satisfying null propagation (V124/V125). Standard S omits the silent prefix.
The null M receives no invented translation.

Physical page 55 places `kiya hemay` in parentheses in example 23c and 飯 in
parentheses in its Chinese translation. The earlier extraction lost those
parentheses and emitted only the longer reading. The build now preserves that
reading's IDs and adds a `-opt` reading without the optional object's W/M
or translation. This is POL-026 expansion, not an additional source occurrence;
the 670 retained occurrences produce 671 S before the source supplement.

`source_data/supplemental_examples.json` adds six complete footnote/prose
examples and four alternative translations from physical pages 33, 37, 39,
130 and 131. It runs after manual transcription and before the shared cleaner.
The four unglossed examples remain W-free; the two glossed examples retain
their printed alignment. All primary translations and 670 manual records stay
intact. Manual FILE and metadata paths now use `Sakizaya/`, matching final XML.

The 9 late summary rows found nowhere else in the thesis are build inputs
(`source_data/late_table_rows.csv`, by maintainer ruling 2026-11-06); the other
104 summary rows remain source evidence. The source PDF and
OCR cache are required only for renewed source inspection. Older scripts are
historical source-research utilities, not alternate release entry points.
The licence is CC BY-NC 4.0, chosen by the maintainer on 2026-11-06 for the
author's 2026-04-01 permission.
