# QC Summary

## Publication input

- Private development commit: `74d6a196b956097fa701bda9e723decefeac71a7`
- Source-tier snapshot SHA-256: `25bacdc8721ba3b8321ad6838eb4b5e7caa9f360328463175e54387cca7a0fac`
- Published XML SHA-256: `2a9f0c0d32adde1be3c2fd48178b19d8a9780afc52369d493b6860734e7460aa`
- XML shape: 276 S, 1,131 W, 1,311 M
- Parsed source candidates: 335 resolved, 0 unresolved

The development workflow was rebuilt twice from the protected source PDF with identical output before this snapshot was copied. The public `make_xml.sh` also reproduces the published XML byte for byte from the source-tier snapshot.

## Current shared QC

- Update-mode `validate_xml.py`: 0 findings.
- `validate_text.py`: 0 hard, 45 soft.
- `validate_glosses.py`: 0 hard, 87 soft.
- Duplicate sentences, original tier: 0 groups.
- Duplicate sentences, standard tier: 0 groups.
- Dialect: `trv` / `Truku`.
- Orthography detector: Ortho94 is the best match.
- Conversion-table validation: pass; see `conversion_table_report.md`.
- Port readiness: 0 hard, 1 expected P006 reminder because `make_xml.sh` references the conversion table. The required table audit is committed and passes.

The raw all-published-corpora XML check reports the expected TEXT-ID collision with the copy this update replaces. Excluding only that target corpus produces the clean update-mode result above.

## Published-ID reconciliation

The live public comparison covered 2,832 published S/W/M units and 2,718 replacement units.

- Hard findings: 0.
- Documented duplicate sentence retirements: 3.
- Legacy unglossed M retirements: 115.
- Reused identifiers with different lexical content: 0.
- Newly recovered sentences: 1, with a new non-conflicting ID.

The 115 retired M elements had no TRANSL in the public XML. They were unsupported segmentation shells rather than source-backed morpheme analyses. Their parent S and W identifiers remain stable.

## Specialized gloss audit

The source-aware specialized gloss audit emits conservative raw signals that are not equivalent to unresolved publication defects. Its current source-backed run reports 178 hard heuristic signals, 334 soft signals, and 1 warning; its structural run reports 133 hard heuristic signals and 39 soft signals. These are fully adjudicated in the private development evidence:

- Marker-skeleton signals arise where source notation and the supported XML tier have different ownership or segmentation scope.
- Source-missing and XML-unmatched signals cover reviewed manual variants, explicit duplicate dispositions, and the recovered source sentence.
- No central gloss validator hard findings remain.

## Privacy

The public package excludes both source PDFs, page images, page-text extraction, PDF inventory, and private permission correspondence. The author permission record remains in the private project workflow.
