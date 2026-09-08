# Reproduction inputs

The canonical entry point is `CodeAndDocs/generate_xml.sh`. It runs with current
FormosanBank tools and records [provenance](../provenance.json); the former
historical-tools pin and combined download/build/QC wrappers are retired.

The 670 retained source IDs and locations come from `extraction_report.csv`
and `table_extraction_report.csv`. `source_data/text_metadata.json` preserves
the two existing TEXT headers. `manual_edits.xml` is the complete expert
transcription of those S records, including all W/M and alternative readings.
Every build reconstructs fresh S records before applying the shared manual
edits, the source-specific 23c expansion, cleaner, standardizer and standard
phonology tool. The baseline does not
read previous final XML. This transcription-based reconstruction implements
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
reading's IDs and adds a `_SHORT` reading without the optional object's W/M
or translation. This is POL-026 expansion, not an additional source occurrence;
the 670 retained occurrences produce 671 final S.

Summary rows remain source evidence, never build inputs. The source PDF and
OCR cache are required only for renewed source inspection. Older scripts are
historical source-research utilities, not alternate release entry points.
The current README states outstanding review and licence decisions.
