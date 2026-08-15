# Reproducibility

`CodeAndDocs/reproduce.sh` requires both checksum-verified private PDFs and a clean FormosanBank checkout at commit `3a3c47c220520113f747e6a2d441494000e13c4b`.

The workflow loads source-derived mappings from `CodeAndDocs/source_data/`, rebuilds all three XML files and review ledgers twice, compares hashes, runs source and XML audits, applies recorded edits and cleaning, regenerates standard FORM with `--remove_accents`, generates original and standard PHON with explicit source `Ortho113`, verifies Main-aligned TRANSL ownership, and executes the complete current QC suite. Evidence defaults to an untracked temporary directory.

The workflow does not install packages, modify the shared checkout, or write to Basecamp.
