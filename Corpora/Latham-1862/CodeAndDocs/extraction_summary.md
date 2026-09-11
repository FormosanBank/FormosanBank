# Extraction Summary

The 64 target cells on printed pages 315–318 were visually
transcribed into `CodeAndDocs/source_ledger.tsv`. Sixty-two cells
contain Formosan data and two source dash cells are terminally
omitted.

## Outputs

- XML: `XML/Siraya/latham_1862_sideia_sida.xml`
- XML: `XML/Babuza-Favorlang/latham_1862_favorlang.xml`
- Row report: `CodeAndDocs/extraction_report.csv`
- Exact source checks: `CodeAndDocs/source_checks.tsv`

## Counts

- Lexical records emitted: 45
- Source FORM readings emitted: 47
- Source varieties represented: 3

## Counts By Source Variety

| Variety | Records |
| --- | --- |
| Favorlang | 29 |
| Klaproth Formosan Sideia | 8 |
| Vander Vlis Sideia | 8 |

## Counts By Language

| Language | Records |
| --- | --- |
| Babuza-Favorlang | 29 |
| Siraya | 16 |

## Representation Decisions

- Five published cells contain competing lexemes, split into separate `S` records
  under revised POL-028; added records use the source ID plus `-opt`
  (a third reading would take `-opt3`).
- Two spelling pairs stay together as original FORM plus `ver="alt"`.
- Historical spelling and all source readings are preserved.
  No standard tier is generated under the corpus's August 12 ruling.
- No W/M segmentation or PHON is inferred from this comparative table.
- Sideia/Sida maps to Siraya (`fos`); Favorlang maps to Babuza-Favorlang (`bzg`).
