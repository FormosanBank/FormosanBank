# Source Coverage Audit

All target cells on printed pages 315–318 were manually transcribed
from the page images into `source_ledger.tsv`. Pages 314 and 319 were
visually checked and contain no target Formosan rows.

## Result

- Published Formosan cells: 40
- Included cells matching ledger, report, and XML: 40
- Cells excluded with the Sida column: 24
- Unresolved mismatches or extras: 0
- Exact independent spot checks: 12 in `source_checks.tsv`
- CSV detail: `CodeAndDocs/source_coverage_audit.csv`

## Page Decisions

| Page | Coverage decision |
| --- | --- |
| 314 | No target Formosan rows; Philippine, Dumagat, and Bashi data excluded. |
| 315 | Sideia comparison table: all 16 Formosan cells published (Klaproth Sideia 8, Vander Vlis Sideia 8). |
| 316 | Gabelentz table: 8 Favorlang cells published; the 8 Sida cells excluded (one a dash). |
| 317 | Gabelentz table: 8 Favorlang cells published; the 8 Sida cells excluded (one a dash). |
| 318 | Gabelentz table: 8 Favorlang cells published; the 8 Sida cells excluded. |
| 319 | Only non-Formosan continuation rows; excluded from target scope. |

## Review Notes

- The PDF is a six-page image-only excerpt; rendered pages 1–6 were
  visually reviewed.
- Historical diacritics are preserved in original FORM; standard is absent.
- Revised POL-028 splits six competing lexemes into separate S records
  and marks two spelling variants with original FORM ver="alt".
- The layout hyphen in `arribórri-` / `bon` is removed when the source
  word is reconstructed as `arribórribon`.
- Sida Forehead and Beard are dash cells and are not emitted.
- No PHON or W/M structure is inferred from the lexical table.
