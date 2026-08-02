# Extraction Summary

The 64 target cells on printed pages 315–318 were visually
transcribed into `CodeAndDocs/source_ledger.tsv`. Sixty-two cells
contain Formosan data and two source dash cells are terminally
omitted.

## Outputs

- XML: `Final_XML/Siraya/latham_1862_sideia_sida.xml`
- XML: `Final_XML/Babuza-Favorlang/latham_1862_favorlang.xml`
- Row report: `CodeAndDocs/extraction_report.csv`
- Exact source checks: `CodeAndDocs/source_checks.tsv`

## Counts

- Lexical records emitted: 62
- Source FORM variants emitted: 70
- Source varieties represented: 4

## Counts By Source Variety

| Variety | Records |
| --- | --- |
| Favorlang | 24 |
| Klaproth Formosan Sideia | 8 |
| Sida | 22 |
| Vander Vlis Sideia | 8 |

## Counts By Language

| Language | Records |
| --- | --- |
| Babuza-Favorlang | 24 |
| Siraya | 38 |

## Representation Decisions

- Every source cell is one lexical `S` record.
- Comma-separated source variants are separate `FORM` elements;
  punctuation is not embedded in a FORM value.
- Historical spelling is preserved in original and standard FORM
  because the source supplies no supported modern normalization.
- No W/M segmentation or PHON is inferred from this comparative table.
- Sideia/Sida maps to Siraya (`fos`); Favorlang maps to Babuza-Favorlang (`bzg`).
