# Huteson (2003) Rukai survey

The Appendix B imitation tests contain 14 Maga (`Maolin`) and 15 Tona
(`Dona`) sentences in Rukai (`dru`), with English translations. The two
files in `XML/Rukai/` contain 29 S, 102 W, 69 M and 34 sentence translations.
There is no audio in this corpus.

Huteson, Greg. 2003. *Sociolinguistic Survey Report for the Tona and Maga
Dialects of the Rukai Language*. SIL International.
[Source archive](https://www.sil.org/resources/archives/9008).

## Source and corrections

All 46 pages are accounted for in
[the coverage inventory](CodeAndDocs/source_page_coverage.tsv). The corpus is
the 29 Appendix B examples on pages 38-44; the survey discussion,
questionnaire summaries and bibliographic titles are outside this scope.
The [reviewed transcription](CodeAndDocs/manual_source_review.tsv) records
natural lines separately from analyzed lines, source glosses, translations
and page locators. The PDF's legacy embedded fonts corrupt automatic text
extraction, so the transcription was checked against rendered pages.

Madeline Boese's August 2026 review corrected `ḍ` to `ɖ`, joined
`saokwamamitə` in Tona 4, and restored Tona 15's literal alternate translation.
Those corrections remain. Tona 4 follows the analyzed line and reviewed join
rather than the extra space in the natural test list. Its W IDs 001/003 remain.

S uses the natural line; W keeps the source's analyzed form. M occurs in
sentences with actual source parsing (POL-023). Eight printed W gloss cells
are blank, and Tona 9's `a-kakə` has one combined W gloss `1S.TOP`, without
separate morpheme meanings. These absences remain blank. The two source
`very fat` glosses stay original; `very.fat` is added separately (POL-036).

Four source translation shorthands (`S/he`, `ran/is running`) expand into
same-S alternatives (POL-025). Naturalistic `(how to)` and `(his)` remain,
and the source gloss `ACT/REAL` is preserved. No source sentence is removed.
The [processing notes](CodeAndDocs/README.md) record the former proposal's
tier removals and identity mapping.

## Rights

**License:** CC BY-NC-SA 4.0

**Rights source:** SIL International, 2025-01-24; evidence: ask maintainer

The retained SIL terms screenshot identifies the licence, also recorded on
the source card. Preserve attribution to Huteson and SIL International,
noncommercial use and ShareAlike terms. No different licence was found in
the source PDF. Converting the earlier XML's permission prose to this exact
licence value requires ordinary rights-delta review before merging.

## Reproduce

[Tool provenance](CodeAndDocs/provenance.json) records the actual build's
FormosanBank commit. It does not select or require an older tool version.
Use the current checkout and its Python dependencies. From the corpus root
inside FormosanBank:

```bash
PYTHON=python3 ./CodeAndDocs/generate_xml.sh
```

For private development, set `FORMOSANBANK_ROOT` to the chosen current
FormosanBank checkout. The build reads only committed corpus inputs and
shared tools. It reconstructs fresh original XML from the reviewed
transcription, then runs shared cleaning, TSV standardization to Rukai
Ortho113, and phonology using the documented source profile. The source
profile and mapping distinguish Maolin and Dona; no private PDF, Git history,
network fetch or Basecamp snapshot is needed to generate XML. This new port
has no published predecessor or invented published baseline.

The build declares two XML files and `CodeAndDocs/extraction_report.tsv` as
outputs. Run it twice with unchanged inputs and compare those files and
any durable correction ledger. Cleaner/standardizer warning CSVs are
per-run evidence, not committed output.

## Validate

```bash
PYTHON=python3 QC_REPORT_DIR=/path/outside/the/corpus/qc \
  ./CodeAndDocs/validate.sh
```

This separate command checks existing output and retains findings for review;
it does not generate XML or automatically assert readiness. Set
`HUTESON_SOURCE_PDF` to the original PDF for the optional source identity and
scrape check. [Source access and hashes](CodeAndDocs/source_manifest.md).
The source tests preserve the independently reviewed readings, blank glosses,
parsing, expert corrections and stable IDs. Inspect raw CSVs, reference
coverage and final source differences even when commands succeed. Historical
August reports and Basecamp snapshots are retained as evidence, not current
policy or build requirements.
