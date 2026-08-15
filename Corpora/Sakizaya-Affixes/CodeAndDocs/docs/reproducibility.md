# Reproducibility

`CodeAndDocs/reproduce.sh` requires both checksum-verified private PDFs and a clean FormosanBank checkout at commit `3a3c47c220520113f747e6a2d441494000e13c4b`.

The workflow loads source-derived mappings from `CodeAndDocs/source_data/`, rebuilds the numbered-example and affix-inventory XML files twice, and never regenerates the expert-rejected summary XML. It applies `manual_edits.xml`, cleans the output, derives standard FORM with `sakizaya_affixes_standardization.tsv`, and generates standard PHON without claiming source phonetics. It then compares hashes and runs the source, XML, privacy, and port-readiness gates.

The workflow does not install packages, modify the shared checkout, or write to Basecamp.
