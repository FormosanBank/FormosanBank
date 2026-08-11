# Huteson (2003) Rukai Survey

This corpus contains the 29 Rukai imitation-test sentences in Appendix B of
Greg Huteson's 2003 sociolinguistic survey: 14 Maga examples published under
the canonical `Maolin` dialect label and 15 Tona examples under `Dona`.

## Source and rights

Huteson, Greg. 2003. *Sociolinguistic Survey Report for the Tona and Maga
Dialects of the Rukai Language*. SIL International.

The report was distributed through the
[SIL archive](https://www.sil.org/resources/archives/9008). The accompanying
rights evidence identifies the source as CC BY-NC-SA 4.0 unless otherwise
stated. Attribution to the contributor, SIL International, and named rights
holders is required.

Private source files and full page-review evidence remain in the
[development repository](https://github.com/FormosanBank/Formosan-Huteson-Rukai-Survey).
They are not copied into FormosanBank.

## Contents

- `XML/Rukai/`: two XML files with 29 S, 102 W, 119 M, and 34 sentence
  TRANSL elements.
- `CodeAndDocs/build_xml.py`: deterministic Appendix B XML builder.
- `CodeAndDocs/extraction_report.tsv`: 29 reviewed source records.
- `CodeAndDocs/huteson_source_to_ortho113.tsv`: source-to-Ortho113 mapping.
- `CodeAndDocs/source_orthography/Rukai.tsv`: corpus-scoped source profile
  used by the shared phonology generator.
- `CodeAndDocs/reproduce.sh`: current generation and QC gate.

TEXT IDs are stable source-based identifiers. S IDs use `S_maga_NNN` or
`S_tona_NNN`; W and M IDs extend their parent ID with fixed-width indexes.
The current port was generated and checked with FormosanBank tooling from
`ef1ebb62126337c3603e8b4f71359986b80d9494`.

All W elements have M analysis under POL-023. Eight source-blank gloss cells
use a reviewed standard `?` with notes. Tona 9 uses the source test-list W/M
form `akakə` and its fused original `1S.TOP` gloss while retaining analyzed
`a-kakə` at S level.

The source shorthands `S/he` and `ran/is running` are same-S alternate
translations under POL-025. The retained `(how to)` and `(his)` translation
parentheticals follow POL-024, and original gloss `ACT/REAL` follows POL-036.

## Reproduce

From this corpus directory:

```bash
./CodeAndDocs/reproduce.sh
```

The script rebuilds the XML, cleans once, validates both conversion-table
dialects, regenerates original and standard PHON with explicit profiles, and
runs the current XML, text, gloss, dialect, duplicate, orthography,
vocabulary, registry, and port-readiness checks. It also compares the rebuild
with the committed XML and stores per-run evidence outside the repository.

Expected results are 0 XML, gloss, generic gloss-audit, duplicate, and
port-readiness findings. Text validation has eight reviewed V122 SOFT
findings from source parentheticals and `ACT/REAL`; the adjudication step
fails if that exact set changes. There is no audio.
