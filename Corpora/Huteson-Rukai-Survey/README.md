# Huteson (2003) Rukai survey

The Appendix B imitation tests contain 14 Maga (`Maolin`) and 15 Tona (`Dona`)
sentences in Rukai (`dru`), with English translations. The two files in
`XML/Rukai/` contain 29 S, 103 W, 70 M and 34 sentence translations. There is no
audio in this corpus.

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

S uses the natural test-list line; W keeps the source's analyzed form, so the
18 hyphens the interlinear prints appear at W and M but not at S. M occurs only
in sentences with actual source parsing (POL-023); the 51 single-morpheme
mirrors that the unparsed sentences would otherwise carry are omitted.

Madeline Boese's August 2026 review corrected `ḍ` to `ɖ` and restored Tona 15's
literal alternate translation; both survive. That review also joined Tona 4's
`saokwa mamitə` into one word; **that join has been reversed** — page 42's gloss
line prints two columns, `very` and `fat`, and the gloss is the tie-breaker for
word division. The standardized gloss `very.fat` that the join required has gone
with it, so every gloss in the corpus is now the source's, with the single marked
exception noted below.

Four source translation shorthands (`S/he`, `ran/is running`) expand into
same-S alternatives (POL-025). Naturalistic `(how to)` and `(his)` remain,
and the source gloss `ACT/REAL` is preserved. No source sentence is removed.
The [processing notes](CodeAndDocs/README.md) record the reproduction pipeline
and the source-derived findings retained for review.

## Notes and Issues

**Maga (Maolin) does not distinguish schwa.** Ortho113 gives Maolin a
seven-vowel system, writing [e] as `é` and [ə] as `e`. Huteson's Maga
transcription uses six vowel symbols and never writes `ə` at all, though he
writes it 60 times in the Tona chapter. His `e` is therefore read as [e]
throughout and standardizes to `é`. Where the modern orthography has [ə] in
these words — `isierkɨ` 'sleep', spelled `sierkɨ` in ePark, is the clear case —
the distinction is simply not recorded in this source, and the standard tier
follows the author rather than reconciling him.

**Word-final vowels are written double.** All eleven doubled vowels in the Maga
data are word-final (`ikee`, `knee`, `mamaa`, `broo` …); the Tona data has none
in that position. The doubling is preserved as the author's, so the standard
tier writes `ikéé` where the bank's other Maolin corpus writes `iké`. Users
comparing Maolin across corpora should expect this: of 41 Maolin word types, 23
match the bank's spelling directly and a further 7 match once word-final
doubling is collapsed. Whether the doubling is phonemic length or predictable
final lengthening is unresolved.

**The particle `na` is never glossed.** All seven occurrences are blank in the
source's aligned display and no meaning has been coined for them: the word, and
its morpheme where the sentence is parsed, carry a FORM and no translation.
Standardizing these glosses is left for a future pass. Seven further word-gloss
cells are blank for the same reason, and Tona 9's `a-kakə` carries one fused
source gloss `1S.TOP` for two morphemes without either being given an invented
meaning.

**One gloss is inferred, not from the source.** Page 43 leaves the `ki` column
of Tona 14 blank. Every other `ki` in the corpus — six of them — is glossed
`NOM`, and none is glossed anything else, so `NOM` is supplied here. It is the
only gloss in the corpus that is not the source's, and it is marked in the data
with a `notes` attribute saying so.

**Case marking differs from the bank's other Rukai sources.** Huteson glosses
`ki` as `NOM`; ePark and NTUFormosanCorpus gloss it `OBL` or `GEN`, never `NOM`.
The source's own analysis is preserved.

## Rights

**License:** CC BY-NC-SA 4.0

**Rights source:** SIL International, 2025-01-24; evidence: ask maintainer

SIL's terms of use state: "Unless stated otherwise in the file or item
description, all items are available under the Creative Commons
Attribution-Noncommercial-Share Alike 4.0 Unported License." Read 2025-01-24.
The version named is 4.0, which is the value recorded in `@copyright` and in
`rights_vocabulary.csv`; "Unported" is a Creative Commons 3.0-era word and is
taken to be a residue in SIL's own wording. Preserve attribution to Huteson and
SIL International, noncommercial use and ShareAlike terms. No different licence
is stated in the source PDF. The retained terms screenshot is recorded in
[the source manifest](CodeAndDocs/source_manifest.md).

## Reproduce

[Tool provenance](CodeAndDocs/provenance.json) records the FormosanBank commit
the published XML was built against. It does not select or require an older tool
version. Use the current checkout and its Python dependencies. From the corpus
root inside FormosanBank:

```bash
PYTHON=python3 ./CodeAndDocs/generate_xml.sh
```

For private development, set `FORMOSANBANK_ROOT` to the chosen current
FormosanBank checkout. The build reads only committed corpus inputs and shared
tools. It reconstructs fresh original XML from the reviewed transcription, then
runs shared cleaning, TSV standardization to Rukai Ortho113 via
[`Orthographies/ConversionTables/Rukai_Huteson_113.tsv`](../../Orthographies/ConversionTables/Rukai_Huteson_113.tsv),
and phonology from the source profile
[`Orthographies/Huteson/Rukai.tsv`](../../Orthographies/Huteson/Rukai.tsv). The
profile and the conversion table both distinguish Maolin and Dona. No private
PDF, Git history, network fetch or issue-tracker access is needed to generate
XML. This new port has no published predecessor.

The build declares two XML files and `CodeAndDocs/extraction_report.tsv` as
outputs. Run it twice with unchanged inputs and compare those files; it is
idempotent. Cleaner and standardizer warning CSVs are per-run evidence, not
committed output (POL-033).

## QC and source checks

`CodeAndDocs/validate.sh` runs eighteen checks over the published XML and keeps
their output for review. It is separate from the build and asserts nothing about
readiness — inspect the findings.

```bash
PYTHON=python3 QC_REPORT_DIR=/path/outside/the/corpus/qc \
  ./CodeAndDocs/validate.sh
```

Two of those checks are specific to this corpus and worth running after any
change to the transcription:

* `audit_source_alignment.py` compares the published XML against
  `manual_source_review.tsv` field by field — natural line, analyzed words,
  source gloss columns, free translations and their alternate metadata. It also
  rejects a gloss on a column the source leaves blank unless that gloss is
  marked `@notes` as inferred.
* `CodeAndDocs/tests/` holds fourteen regression tests pinning the reviewed
  readings, the blank gloss cells, the source parsing, the inferred `ki` gloss
  and the stable ids.

Run them through `validate.sh` rather than directly: one test needs
`FORMOSANBANK_ROOT`, which `validate.sh` exports.

Set `HUTESON_SOURCE_PDF` to a local copy of the report to add the optional
source-identity and gloss-scrape comparisons; see
[the source manifest](CodeAndDocs/source_manifest.md) for where to get it and
the SHA-256 to check it against.
