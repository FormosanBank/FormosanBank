# Huteson (2003) Rukai survey

This corpus contains the 29 Appendix B imitation-test sentences in Greg
Huteson's 2003 survey: 14 Maga (`Maolin`) and 15 Tona (`Dona`) examples.
Each has a natural source FORM, analyzed W forms, English translations,
Ortho113 forms and generated phonology. Fifteen sentences have source
morpheme analysis; fourteen have word glosses without an invented M tier.
There are 103 W and 70 M. Eight word-gloss cells are blank in the source: seven
stay unglossed and one carries a gloss inferred from the corpus's own usage,
marked as inferred in the data. No audio is included.

## Languages and dialects

The Appendix B imitation tests contain 14 Maga (`Maolin`) and 15 Tona (`Dona`)
sentences in Rukai (`dru`), with English translations. Both files declare
`xml:lang="dru"`:

* `XML/Rukai/huteson_2003_rukai_maga_imitation_test.xml`: `dialect="Maolin"`
  (the source's label is Maga), 14 sentences.
* `XML/Rukai/huteson_2003_rukai_tona_imitation_test.xml`: `dialect="Dona"`
  (the source's label is Tona), 15 sentences.

## Source

Huteson, Greg. 2003. *Sociolinguistic Survey Report for the Tona and Maga
Dialects of the Rukai Language*. SIL International.
[Source archive](https://www.sil.org/resources/archives/9008).

[The source archive](https://www.sil.org/resources/archives/9008) identifies
Huteson's report. This corpus covers its Appendix B, with all 46 PDF pages
accounted for in the source inventory. All 46 pages are accounted for in
[the coverage inventory](CodeAndDocs/source_page_coverage.tsv). The corpus is
the 29 Appendix B examples on pages 38-44; the survey discussion,
questionnaire summaries and bibliographic titles are outside this scope.

The two files in `XML/Rukai/` contain 29 S, 103 W, 70 M and 34 sentence
translations. There is no audio in this corpus.

The XML and reproduction files are maintained in the
[FormosanBank repository](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Huteson-Rukai-Survey).

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Huteson-Rukai-Survey_corpora_stats.csv` and appears on this corpus's
page on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

Huteson, Greg. 2003. *Sociolinguistic Survey Report for the Tona and Maga
Dialects of the Rukai Language*. SIL International.

## License

**License:** CC BY-NC-SA 4.0
**Rights source:** SIL International, 2025-01-24; evidence: ask maintainer

SIL's terms of use state: "Unless stated otherwise in the file or item
description, all items are available under the Creative Commons
Attribution-Noncommercial-Share Alike 4.0 Unported License." Read 2025-01-24.
The version named is 4.0, which is the value recorded in `@copyright` and in
`rights_vocabulary.csv`; "Unported" is a Creative Commons 3.0-era word and is
taken to be a residue in SIL's own wording. Preserve attribution to Huteson and
SIL International, noncommercial use and ShareAlike terms. Attribution to
Greg Huteson and SIL International, noncommercial use and ShareAlike
distribution are therefore required. No different licence is stated in the
source PDF. The retained terms screenshot is recorded in
[the source manifest](CodeAndDocs/source_manifest.md).

The corpus is also subject to FormosanBank's
[Terms of Use](https://formosanbank.github.io/FormosanBank/additional-resources/terms-of-use/) and
[AI Use and Commercial Licensing](https://formosanbank.github.io/FormosanBank/additional-resources/ai-use-and-commercial-licensing/).

## Notes and caveats

#### Import decisions

**Tona 4 is two words, reversing an expert review.** Madeline Boese's August
2026 review corrected `ḍ` to `ɖ` and restored Tona 15's literal alternate
translation; both survive. That review also joined Tona 4's `saokwa mamitə`
into one word; **that join has been reversed** — page 42's gloss line prints two
columns, `very` and `fat`, and the gloss is the tie-breaker for word division.
The standardized gloss `very.fat` that the join required has gone with it, so
every gloss in the corpus is now the source's, with the single marked exception
noted below. The change to already-published identifiers this caused is listed
in the [processing notes](CodeAndDocs/README.md).

**Translation shorthands become alternatives.** Four source translation
shorthands (`S/he`, `ran/is running`) expand into same-S alternatives (POL-025).
Naturalistic `(how to)` and `(his)` remain, and the source gloss `ACT/REAL` is
preserved. No source sentence is removed.

#### Properties of the source

Four things a user should know before comparing this corpus with FormosanBank's
other Rukai data. All are properties of the 2003 source, not defects in the
port.

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
`NOM`, and none is glossed anything else, so `NOM` is supplied here. It is the only gloss in the
corpus that is not the source's, and it is marked in the data with a `notes`
attribute saying so.

**Case marking differs from the bank's other Rukai sources.** Huteson glosses
`ki` as `NOM`; ePark and NTUFormosanCorpus gloss it
`OBL` or `GEN`, never `NOM`. The source's own analysis is preserved.

## Reproduction and processing

### How to reproduce

```bash
bash Corpora/Huteson-Rukai-Survey/CodeAndDocs/generate_xml.sh
```

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

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

The corpus's `CodeAndDocs/generate_xml.sh` rebuilds from committed
transcription inputs and current shared cleaning, standardization and
phonology tools. No private repository, source download or historical Git
objects are needed. [Tool provenance](CodeAndDocs/provenance.json)
records the actual build, without pinning later runs.
[Reproduction and validation instructions](README.md)
include the source-specific gloss findings and correction history.

The build declares two XML files and `CodeAndDocs/extraction_report.tsv` as
outputs. Run it twice with unchanged inputs and compare those files; it is
idempotent. Cleaner and standardizer warning CSVs are per-run evidence, not
committed output (POL-033).

#### QC and source checks

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

The other sixteen checks are shared FormosanBank tools: `validate_xml.py`,
`validate_text.py` and `validate_glosses.py` (with `--no-exit-on-hard`),
`audit_gloss_scrape.py --no-source`, and for each of the original and standard
tiers `validate_duplicate_sentences.py`, `orthography_extract.py` (by dialect)
and `validate_orthography.py` against `QC/validation/reference` for Rukai; then
`validate_vocabulary.py` on the standard tier, `validate_conversion_table.py`
for each of Maolin and Dona, `validate_dialect.py`, `validate_registries.py`
and `validate_port_readiness.py`. Each check's log and exit code go to
`QC_REPORT_DIR` (which must be outside the corpus folder), and the script exits
1 if any check exited non-zero.

### What each step does

`generate_xml.sh` takes the FormosanBank root from `FORMOSANBANK_ROOT`
(default: three folders above `CodeAndDocs/`) and the interpreter from `PYTHON`
(default `python3`), stops unless `QC/cleaning/clean_xml.py` exists there, and
then runs four steps in this order.

**1. `CodeAndDocs/build_xml.py`** (no flags) writes the two XML files in
`XML/Rukai/` from scratch, plus `CodeAndDocs/extraction_report.tsv`.

The reviewed transcription preserves natural and analyzed lines separately,
with stable example/page identities. The PDF's legacy embedded fonts require
visual source review. The [reviewed transcription](CodeAndDocs/manual_source_review.tsv) records
natural lines separately from analyzed lines, source glosses, translations
and page locators. The PDF's legacy embedded fonts corrupt automatic text
extraction, so the transcription was checked against rendered pages.

What the script reads: the S `FORM kindOf="original"` comes from the
`source_natural_form` column of `manual_source_review.tsv`. The analyzed form,
the gloss line, the free translation, the page numbers and any alternate
translation of each of the 29 examples are typed into `build_xml.py` itself
(the `MAGA` and `TONA` tables); they repeat the TSV's `source_form`,
`source_gloss` and `source_translation` columns, and `audit_source_alignment.py`
(run by `validate.sh`, not by the build) checks the built XML against the TSV.

What it decides and writes, per example:

* `TEXT` carries `xml:lang="dru"`, `dialect` `Maolin` or `Dona`, the citation,
  a BibTeX citation, `copyright="CC BY-NC-SA 4.0"` and a `source` naming the
  appendix section. Each `S` has the id `S_maga_NNN` / `S_tona_NNN` and a
  `source` giving the test-list and translation pages.
* S uses the natural test-list line; W keeps the source's analyzed form, so the
  18 hyphens the interlinear prints appear at W and M but not at S. M occurs
  only in sentences with actual source parsing (POL-023); the 51
  single-morpheme mirrors that the unparsed sentences would otherwise carry are
  omitted. The sentence
  tier uses the natural test-list line and the word tier the analyzed one, so the
  interlinear's hyphens appear at word and morpheme level but not at the
  sentence. W forms are the analyzed form split on spaces with edge
  punctuation (`. , ! ? "` and curly quotes) stripped.
* Each word is paired with the next column of the gloss line, except the eight
  word positions listed in `UNGLOSSED_WORD_INDEXES`, which get no gloss. The
  script stops with an error if words and gloss columns do not line up.
* `INFERRED_GLOSSES` supplies the one gloss not taken from the source: page 43
  leaves the `ki` column of Tona 14 blank, and since every other `ki` in the corpus is glossed
  `NOM` and none is glossed anything else, `NOM` is supplied there and marked as
  inferred. The mark is a `notes` attribute stating that reasoning; the inferred
  gloss is not copied to any morpheme (Tona 14 has no M).
* A sentence counts as parsed when any of its words contains a hyphen;
  in a parsed sentence every word gets M elements, split on `-`, each paired
  with the matching piece of the word's gloss. Tona 9's `a-kakə` gets two M with
  no gloss, because the source gloss `1S.TOP` is one fused label. Tona 9
  retains printed `a-kakə` and the combined word gloss `1S.TOP`; no meanings are
  invented for its two individual morphemes.
* Free translations: four sentences (Maga 4 and 6, Tona 3 and 5) get their
  expanded alternatives instead of the shorthand, the second with `ver="alt"`.
  Four translation shorthands become same-sentence alternatives, and every gloss
  is the source's apart from the single inferred one noted above. Tona 15 also
  gets the literal translation as a `ver="alt"` TRANSL with
  `notes="literal translation"`. Expert corrections to `ɖ` and the literal
  alternate translation in Tona 15 remain.

**2. `QC/cleaning/clean_xml.py --corpora_path XML`** cleans the original tiers
in place: non-breaking spaces become spaces, S/W/M original FORMs are
Unicode-normalized (NFC), HTML entities decoded and punctuation and whitespace
tidied, and sentence-level TRANSL text is cleaned. It does not touch the
standard tier (none exists yet). No `--warnings_dir` is passed, so if the
cleaner has warnings its `cleaner_warnings.csv` is written into `XML/`.

**3. `QC/utilities/standardize.py --corpora_path XML --tsv_path
Orthographies/ConversionTables/Rukai_Huteson_113.tsv`** adds a
`FORM kindOf="standard"` beside every original FORM (S, W and M). Because
Rukai has several dialects, the file's `dialect` selects the table's `Maolin` or
`Dona` column; a cell reading `NA` is not a rule for that dialect. The rules are
applied in file order: `e`→`é` (Maolin only), `ɖ`→`dr`, `ŋ`→`ng`, `ʔ`→`'`
(Dona only), `ə`→`e`.

The source's writing system is registered as a scheme like any other:
`Orthographies/Huteson/Rukai.tsv` maps its letters to IPA for the original
phonology, and `Orthographies/ConversionTables/Rukai_Huteson_113.tsv` converts
it to Ortho113 for the standard tier. It is a mixed system rather than plain
IPA — `c` is [ʦ] and `y` is [j] — so the conversion table carries rules only
where those two systems disagree. The `e` row must come before the `ə` row, or
the schwa rule's output would be rewritten by the `e` rule; the
[processing notes](CodeAndDocs/README.md) explain this. Any
`standardize_warnings.csv` is written into `XML/`.

**4. `QC/utilities/add_phonology.py --corpora_path XML --orthography
Huteson`** writes a PHON after each base FORM: `PHON kindOf="original"` from
the original FORM using `Orthographies/Huteson/Rukai.tsv` (dialect column
`Maolin` or `Dona`), and `PHON kindOf="standard"` from the standard FORM using
Rukai's standard orthography table, `Orthographies/Ortho113/Rukai.tsv`.

The [processing notes](CodeAndDocs/README.md) record the reproduction pipeline
and the source-derived findings retained for review.
