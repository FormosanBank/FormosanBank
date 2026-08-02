# Source Coverage Audit

All target cells on printed pages 315–318 were manually transcribed
from the page images into `source_ledger.tsv`. Pages 314 and 319 were
visually checked and contain no target Formosan rows.

## Result

- Expected included Formosan cells: 62
- Included cells matching ledger, report, and XML: 62
- Blank/dash Formosan cells intentionally omitted: 2
- Unresolved mismatches or extras: 0
- Exact independent spot checks: 12 in `source_checks.tsv`
- CSV detail: `CodeAndDocs/source_coverage_audit.csv`

## Page Decisions

| Page | Coverage decision |
| --- | --- |
| 314 | No target Formosan rows; Philippine, Dumagat, and Bashi data excluded. |
| 315 | Sideia comparison table: all 16 Formosan cells included. |
| 316 | Gabelentz table: 15 Formosan cells included; Sida Forehead dash omitted. |
| 317 | Gabelentz table: 15 Formosan cells included; Sida Beard dash omitted. |
| 318 | Gabelentz table: all 16 Formosan cells included. |
| 319 | Only non-Formosan continuation rows; excluded from target scope. |

## Review Notes

- The PDF is a six-page image-only excerpt; rendered pages 1–6 were
  visually reviewed.
- Historical diacritics are preserved exactly in original and standard
  FORM tiers.
- Comma-separated variants are separate original/alternate FORM tiers.
- The layout hyphen in `arribórri-` / `bon` is removed when the source
  word is reconstructed as `arribórribon`.
- Sida Forehead and Beard are dash cells and are not emitted.
- No PHON or W/M structure is inferred from the lexical table.
