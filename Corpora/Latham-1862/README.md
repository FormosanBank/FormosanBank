# Latham 1862 comparative wordlist

The Formosan lexical tables in Robert Gordon Latham's *Elements of comparative
philology* (London: Walton and Maberly, 1862), printed pp. 315-318. This corpus
contains the Formosan lexical data from Robert Gordon Latham's 1862 _Elements of
Comparative Philology_ (printed pp. 315–318), a nineteenth-century comparative
wordlist. It comprises 45 lexical entries across two historically attested
Formosan languages — Siraya (`fos`) and Babuza-Favorlang (`bzg`) — each paired
with an English gloss.

## Languages and dialects

| Language | Source varieties | Records | XML |
| --- | --- | ---: | --- |
| Siraya (`fos`) | Klaproth Sideia, Vander Vlis Sideia | 16 | `XML/Siraya/latham_1862_sideia_sida.xml` |
| Babuza-Favorlang (`bzg`, dialect `Favorlang`) | Favorlang | 29 | `XML/Babuza-Favorlang/latham_1862_favorlang.xml` |

The Siraya file declares `xml:lang="fos"` and `dialect="Siraya"`; the
Babuza-Favorlang file declares `xml:lang="bzg"` and `dialect="Favorlang"`.

**The two Sideia readings are published as pronunciation variation within
Siraya**, not as distinct dialects. Latham's presentation suggests they may be
two dialects; the corpus records that here and does not encode it.

A third column in the printed tables, headed "Sida", is transcribed but **not
published**; see *Notes and caveats*.

## Source

The printed grid has 64 Formosan cells. **40 are published**; the 24 of the
Gabelentz "Sida" column are not — see *Notes and caveats*. Five published cells
supply two competing lexemes each, producing 45 records; two spelling variants
bring the source FORM count to 47. English headings supply the translations.
Neighbouring comparison languages are outside this corpus.

Because the source scan has no text layer, the table was transcribed by hand
from the page renders and independently checked against the source. The
historical spelling is preserved as-is; no modern orthographic standard or
phonology exists for these varieties, so none is inferred.

The six-page review excerpt covers printed pp. 314-319. SHA-256:
`e7b34a4063c5f552b288f2e97568d13387ffad471713e3191c644a2ec40ead7b`
(1,195,720 bytes). It can be reviewed against the public scan; it is not a build
dependency. The book's Addenda and Corrigenda, pp. 753-757, contain no correction
to these Formosan tables.

This written source supplies no audio.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Latham-1862_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

Latham, R. G. (1862). _Elements of comparative philology_. London: Walton and Maberly.

## License

**License:** public domain

**Rights source:** Internet Archive / Mark Graves (status confirmation), 2008-07-23; evidence: ask maintainer

This is the existing public-domain work, not a new permission grant. The
[public scan record](https://archive.org/details/elementsofcompar00lathrich)
records the 1862 publication and its public-domain status. The normalized XML
value `public domain` preserves the prior `Public domain.` claim; the exact
spelling change remains subject to maintainer merge review.

public domain. The source, Latham (1862), is in the public domain.

## Notes and caveats

**The Gabelentz "Sida" column is not published.** Its 24 cells on printed
pp. 316–318 are transcribed in `source_ledger.tsv` with status
`excluded_unidentified_variety`, and are emitted to no XML. Gabelentz heads the
column "Sida"; publishing it under `fos` would assert that Sida is the "Sideia"
of the Klaproth/Vander Vlis table on p. 315, and FormosanBank does not make that
identification. The transcription is kept so the decision can be revisited
without redoing the work — if the identification is ever settled, flipping 24
ledger rows republishes them under their original IDs.

**The Gabelentz "Sida" column is not published.** Latham's tables on printed pp. 316–318 carry a third Formosan column headed "Sida". Publishing it as Siraya would assert that Sida is the "Sideia" of the Klaproth/Vander Vlis table on p. 315, and FormosanBank does not make that identification. Its 24 cells are transcribed in the source ledger and marked excluded, so the decision is reversible without redoing the work, but no `S` record is emitted for them and 22 previously published records were withdrawn.

**The two Sideia readings are published as pronunciation variation within Siraya**, not as distinct dialects. Klaproth and Vander Vlis readings of the same entry are separate `S` records (for example `S_klaproth_formosan_sideia_two` `ranka` and `S_vander_vlis_sideia_two` `so`); the only Siraya `FORM ver="alt"` is `soa`, the second reading in the Vander Vlis cell for Two. Latham's presentation suggests these may be two dialects; the corpus records that here rather than encoding it.

**The file name says more than the file contains.** `latham_1862_sideia_sida.xml`
and its `TEXT/@id` both carry "sida", from when the Sida column was published in
it. POL-037 forbids renaming a published `TEXT/@id`, so both stay.

**The file name says more than the file contains.** The Siraya file is `latham_1862_sideia_sida.xml` and its `TEXT` id is `latham_1862_sideia_sida`, from when the Sida column was published in it. Published identifiers are never renamed, so both keep the old name.

**There is no `standard` tier and no `PHON` tier**, by design. Historical
spellings have no approved standardization or pronunciation profile; use
original FORM (POL-058). Query the original `FORM`. English headings are lexical
glosses, not sentence translations. `rahpal` and `rima` no longer repeat across
records: both former duplicate pairs needed a Sida record.

## Reproduction and processing

### How to reproduce

Use the Python environment installed for the current FormosanBank checkout:

```bash
./CodeAndDocs/generate_xml.sh
```

(from `Corpora/Latham-1862/`; from the repository root the same script runs as
`bash Corpora/Latham-1862/CodeAndDocs/generate_xml.sh`).

For a standalone development clone, set `FORMOSANBANK_ROOT` to the current
FormosanBank checkout and, if needed, `PYTHON` to its Python executable. In the
public corpus layout the surrounding checkout is used automatically. No
network fetch, private source, or historical tool checkout is required.

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

The build regenerates XML from the ledger and runs shared `clean_xml.py`.
[Build provenance](CodeAndDocs/provenance.json) records the tools used for the
reviewed output; it does not select or constrain future tools. Repeating a
build with unchanged inputs must leave the XML and extraction summaries
unchanged.

After building, write checks to a new directory outside the corpus:

```bash
OUTPUT_DIR=/path/to/new/review ./CodeAndDocs/validate.sh
```

**POL-047 deviation:** No manual-edits file exists. Standard FORM and PHON are
omitted under the [August 12 corpus ruling](https://github.com/FormosanBank/FormosanBank/commit/be579c6b0fb4818ae90bedbbf7c0dc4d58145ac6): neither historical variety has an
approved standardization or pronunciation profile. No W/M analysis is
inferred. Query original FORM; token counting falls back to that tier.

**POL-058:** No orthography profile is extracted and none is compared.
`standards.csv` leaves `standard_orthography` blank for both Babuza-Favorlang
and Siraya, and neither has a reference inventory, so there is nothing to check
against.

### What each step does

`CodeAndDocs/generate_xml.sh` (bash, `set -euo pipefail`) locates the corpus
folder, the FormosanBank checkout (`FORMOSANBANK_ROOT`, default three levels up
from `CodeAndDocs/`) and the Python executable (`PYTHON`, default `python3`),
checks that `QC/cleaning/clean_xml.py` exists, then runs two steps.

#### 1. `CodeAndDocs/build_lexical_xml.py`

The hand transcription lives in a reviewed, page-addressed source ledger
(`CodeAndDocs/source_ledger.tsv`), from which `CodeAndDocs/build_lexical_xml.py`
rebuilds the XML; every emitted field is independently verified against the
ledger. The entry point is `CodeAndDocs/generate_xml.sh`, which builds from the
ledger and then runs the shared `clean_xml.py` (a verified no-op — the
transcription is already clean).

[The source ledger](CodeAndDocs/source_ledger.tsv) is the reviewed manual
transcription and build input. It preserves historical spelling, including
`â á ó é à`, source-variety and page locators, and distinct repeated
attestations of `rahpal` and `rima`. Its `reading_type` column distinguishes
competing lexemes from spelling variants under revised POL-028.

What the script does, in order:

- **Reads the ledger** (64 rows, one per printed cell). It refuses to build if
  the ledger is empty, if any `status` is not `included`,
  `omitted_blank_or_dash` or `excluded_unidentified_variety`, if an included
  cell has no FORM, if an omitted cell has FORM data, if an included cell with a
  second reading has a `reading_type` other than `lexeme` or `variant` (or a
  `reading_type` without a second reading), or if two included cells would get
  the same XML id. In the current ledger 40 rows are `included` and 24 are
  `excluded_unidentified_variety`.
- **Keeps only `included` rows.** The 24 Sida rows are dropped here.
- **Splits competing lexemes.** Each published source cell becomes one lexical
  `S` record. Where a cell gives two readings, the ledger's `reading_type`
  column decides how they are represented: two competing **lexemes** become two
  `S` records, the second taking the first's id plus `-opt`, while two
  spellings of one word stay in a single record as an original `FORM` plus a
  `FORM ver="alt"`. Favorlang Man, Hair, Mouth, Neck and Breast each have two S
  records: the first keeps its published ID, the second adds `-opt` (POL-028; a
  third reading would take `-opt3`). The pairs `so`/`soa` and `totto`/`tutta`
  stay in one record as an original FORM plus `ver="alt"`. Latham's historical
  diacritics (`â á ó é à`) are preserved exactly.
- **Builds ids** as `S_<source variety>_<English heading>` (lower-cased,
  non-alphanumerics to `_`), e.g. `S_favorlang_man`, `S_favorlang_man-opt`,
  `S_vander_vlis_sideia_two`. Because the source variety is part of the id,
  Klaproth and Vander Vlis readings are always separate records.
- **Writes the two XML files**: `fos` rows to
  `XML/Siraya/latham_1862_sideia_sida.xml` (`TEXT` id `latham_1862_sideia_sida`,
  glottocode `sira1267`) and `bzg` rows to
  `XML/Babuza-Favorlang/latham_1862_favorlang.xml` (`TEXT` id
  `latham_1862_favorlang`, glottocode `favo1235`). Each `TEXT` gets the fixed
  citation, BibTeX citation, `copyright="public domain"`, the ledger's dialect
  and a `source` naming the Basecamp card, the manual transcription and the
  public scan. Each `S` gets a `source` attribute with printed page, PDF page,
  table, source variety and English heading; one `FORM kindOf="original"`, one
  `FORM kindOf="original" ver="alt"` per spelling variant, and a
  `TRANSL xml:lang="eng"` holding the lower-cased English heading. No standard
  FORM, PHON, W or M is written.
- **Writes the row report** `CodeAndDocs/extraction_report.csv` (one row per
  included ledger cell) and the summary `CodeAndDocs/extraction_summary.md`
  (record and FORM counts by variety and language).

**There is no `standard` tier and no `PHON` tier**, by design. Neither variety
has an approved standard orthography — `standards.csv` leaves both blank — so
there is nothing to transliterate into and nothing to compare an orthography
profile against; no orthography check is run for them at all. Query the
original `FORM`.

#### 2. Shared `QC/cleaning/clean_xml.py --corpora_path XML`

Runs the shared cleaner over both XML files in place.

#### Source readings and the review record

**Whether a second reading is a competing lexeme or a variant is a judgement
about the source, not a similarity test** (POL-028). The two kept together are
not kept because they look alike: Latham presents the Klaproth and Vander Vlis
Sideia columns as readings of the same material, and FormosanBank takes no
position on whether its two Siraya sources are distinct dialects. They are
published as **pronunciation variation within Siraya**, with the source's own
suggestion that they may be two dialects recorded here rather than asserted in
the XML. (In the ledger, `so`/`soa` are both in the Vander Vlis Sideia cell for
Two, and `totto`/`tutta` are both in the Favorlang cell for Heart.)

This supersedes the former all-FORM grouping and `kindOf="alternate"` spelling
(POL-050), preserving every published source reading.

[The review record](CodeAndDocs/reviewer_feedback.tsv) preserves Madeline
Boese's July 25 and 27 corrections. Some concern the Sida column, which is
no longer published; the rows stay, because what a reviewer found in the source
does not stop being true when a column is withdrawn. For published cells:
corrected accents, the wrapped word `arribórribon`, and `(so)` corrected to
`so` with alternate `soa`. [Independent fixtures](CodeAndDocs/source_checks.tsv)
and [tests](CodeAndDocs/tests/test_source_ledger.py) protect these readings.
The published [pre-correction snapshot](CodeAndDocs/pre_correction_snapshot/)
is retained unchanged as historical evidence; current generation reads the
ledger, not the final XML.

#### Validation (`CodeAndDocs/validate.sh`)

`validate.sh` requires `OUTPUT_DIR` to be a new absolute directory outside the
corpus. It builds a view of the other published corpora (for cross-corpus id
checks), then runs, logging each to `OUTPUT_DIR`: the corpus tests
(`CodeAndDocs/tests/`); `CodeAndDocs/audit_source_coverage.py`; the shared
`validate_xml.py`, `validate_text.py` and `validate_glosses.py` (each with a
findings CSV); `validate_dialect.py`; `validate_duplicate_sentences.py` on the
original tier; `validate_registries.py`; `validate_port_readiness.py`; and
finally `CodeAndDocs/scripts/adjudicate_qc.py`, which checks the run against
the ledger, the duplicate-group review and the XML. It exits non-zero if any
step failed.

The source audit is read-only by default. After an authorized ledger change,
`python CodeAndDocs/audit_source_coverage.py --write-reports` refreshes its
committed summaries. The validator runs every applicable check and rejects
unreviewed findings; [QC notes](CodeAndDocs/qc_summary.md) explain accepted
findings and unavailable comparisons.

No orthography extraction wrapper exists in `CodeAndDocs/`, and `validate.sh`
runs no orthography extraction (POL-058; see the comment in `validate.sh`).
Neither historical variety has a reference inventory for automatic comparison.
No shared code is changed here.

#### Publication packaging

The complete public file set is `README.md`, `CodeAndDocs/` and `XML/` from one
verified private commit. Export those paths with `git archive` and install them
at `Corpora/Latham-1862/`; paths inside the corpus and all file bytes remain
unchanged. Replace superseded build files rather than overlaying competing
entry points. Both XML files are included; there are no private-only XML
exclusions. The preserved snapshot is a build-history input, not published XML.
