# Utrecht Manuscript Word List

This corpus contains 1,061 Siraya lexical records from Christopher Joby's corrected database of the seventeenth-century Utrecht Manuscript word list. Each row of Joby's source table becomes one sentence-level record.

## Languages and dialects

**Language:** Siraya (`fos`)

**Dialect:** Siraya

The corpus is one file, `XML/Siraya/Utrecht_Manuscript.xml`, whose `<TEXT>` declares `xml:lang="fos"` and `dialect="Siraya"`. The Siraya forms are the sentence-level `FORM`s; the translations are Dutch (`TRANSL xml:lang="nld"`) and English (`TRANSL xml:lang="eng"`).

## Source

**Source:** Christopher Joby's corrected Utrecht Manuscript database

**Source orthography:** Historical Latin-script Utrecht Manuscript transcription, corrected by Joby

Christopher Joby's 75-page database provides corrected Siraya forms, historical Dutch translations, comparison data, and English translations for the seventeenth-century Utrecht Manuscript word list. Joby's corrected source database is published by [Neerlandistiek](https://neerlandistiek.nl/wp-content/uploads/2021/07/UM-database.pdf).

The canonical XML contains 1,061 source-row records. Each database row becomes one `S`, following the source-specific decision to use no `W` tier except where the source itself supplies a morphological analysis. Current FormosanBank authority has no Siraya standard orthography or phonology profile, so the corpus contains original `FORM` tiers and source translations without invented `standard` `FORM` or `PHON` tiers.

The table sets several witnesses side by side, and the corpus keeps the ones that are Siraya or a translation of it. Joby's own corrected reading is the original `FORM`. Where van der Vlis's 1842 edition reads differently, his form is kept as a **variant** `FORM` — `kindOf="original" ver="alt"`, a second reading of the original tier — so the two readings can be compared without either being lost. There are 79 such variants. Two further variant `FORM`s carry the source's own analysis of a headword (source rows 105 and 233), so the corpus has 81 variant `FORM`s in all. Van der Vlis's Dutch is the primary translation and the manuscript's own Dutch is kept alongside it as a variant `TRANSL`, also marked `ver="alt"`, wherever the two differ; the marker means the same thing in both places — one of several readings of the same thing — and the element it sits on says whether that thing is a form or a translation. Joby's English is the English translation.

The source supplies a morphological analysis for two entries, and those carry `W` and `M` tiers. The remaining 1,059 have none, which is the normal state for a word list. There is no audio. FormosanBank currently has no Siraya standard-orthography target or phonology profile, so the corpus preserves the original forms without adding standard `FORM` or `PHON` tiers.

#### What the source columns become

The database is a ten-column comparative table. Five columns are published:

| # | column | becomes |
|---|---|---|
| 1 | `UM Formosana` — Joby's corrected reading | `FORM kindOf="original"` |
| 2 | `UM Belgica` — the manuscript's own Dutch | `TRANSL xml:lang="nld" ver="alt"`, **only where it differs from column 3** |
| 3 | `VdV Dutch` — van der Vlis 1842 | `TRANSL xml:lang="nld"` |
| 4 | `VdV Siraya` — van der Vlis 1842 | `FORM kindOf="original" ver="alt"`, where it differs from column 1 |
| 5 | `My English` — Joby's own English | `TRANSL xml:lang="eng"` |

Columns 6 (`Murakami`), 7 (`Gospel/Formulary equivalent`) and 8–10 (`Variation`, `etyma`, `Other sources`) are **not published**. Column 7 in particular was considered and ruled out: its 519 Gospel-dialect forms would have committed the corpus to a second orthography, to morpheme boundaries inside an S-level `FORM`, and to a dialect that `TEXT/@dialect` cannot express.

Editorial material is separated from translation by column, because the column decides its kind. Brackets in columns 2 and 3 are always apparatus about the manuscript — `[sic]`, `[recte …]`, `[… scored through]`, dictionary citations — and move to `TRANSL/@notes`. Brackets in column 5 are always Joby's own, and stay inline as parentheses where they elaborate. A comma in a translation that the Siraya form does not have separates alternative readings, which become `ver="alt"` translations. Every exception is recorded in `CodeAndDocs/source_decisions.json`.

Editorial material is separated from translation by which column it appears in. Joby's database marks scholarly apparatus in square brackets, and the column decides what a bracket means: in the two Dutch columns it is always a remark about the manuscript — `[sic]`, a corrected reading, a note that a word was struck through, a dictionary citation — and moves to a `notes` attribute rather than being published as part of the translation. In Joby's own English column a bracket is his own elaboration, and stays inline. Where a translation carries a comma the Siraya form does not, the readings are separated into `ver="alt"` translations.

Two of the source's own conventions are preserved rather than normalized away. Where Joby supplies a letter the manuscript lacks, the supplied reading is published and the manuscript reading recorded in a note. Where he gives an uncertain alternative, it is recorded as a note on the form rather than presented as a second headword.

#### Audio

The source and corpus contain no audio.

#### Additional reference

C. J. van der Vlis. (1842). *Formosaansche woorden-lijst, volgens een Utrechtsch handschrift*. This public-domain edition is a comparison witness, not the authority for Joby's corrected Siraya forms.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/UtrechtManuscriptWordList_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

Joby, C. (2021). Revisions to the Siraya lexicon based on the original Utrecht Manuscript: A case study in source data. *Historiographia Linguistica*, 48(2-3), 177-204.

The data itself is Joby's accompanying database, *Utrecht Manuscript, Siraya-Nederlands woordenlijst / UM database* (Neerlandistiek, 2021), pinned by SHA-256 in [`CodeAndDocs/source_manifest.json`](CodeAndDocs/source_manifest.json) and published at https://neerlandistiek.nl/wp-content/uploads/2021/07/UM-database.pdf — it is the file the build reads, but the article is what to cite.

## License

**License:** CC BY-NC 4.0
**Rights source:** Christopher Joby, 2021-07-06; evidence: ask maintainer

Joby authorized use of his corrected transcriptions and translations under this licence. The permission is recorded against the project's source manifest; the maintainer holds the correspondence.

Christopher Joby's corrected transcriptions and translations are licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). Commercial AI use requires prior written permission under the FormosanBank terms.

#### License and AI use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission. See also the FormosanBank [Terms of Use](https://formosanbank.github.io/FormosanBank/additional-resources/terms-of-use/).

## Notes and caveats

#### Known source anomalies

- **Rows 223–233** fill the two van der Vlis columns in the opposite order, a run that begins at manuscript page marker 12 and spans PDF pages 16–17. Confirmed against the source; the published predecessor reproduced the same anomaly, publishing the Siraya form as its own Dutch translation. The build swaps them back. For eleven consecutive entries, beginning at the manuscript's own page 12, the source table fills its two van der Vlis columns in the opposite order to the rest of the table. The build restores the intended order. This is worth recording because the earlier published version of this corpus reproduced the anomaly, printing the Siraya form as its own Dutch translation.
- Row 122 is published as one word, `pasagoualalingauang`. Joby's table cell wraps it across two lines (`pasagoualalingaua` / `ng`, PDF p. 9), which the text layer reads as a space; van der Vlis sets it solid, so there is no variant (maintainer, 2026-10-15). The FORM's `notes` says so. One entry, `pasagoualalingauang` 'mirror', is published as one word: Joby's table cell wraps it across two lines, which reads as a space in the text layer, and van der Vlis sets it solid.
- Row 1060's van der Vlis cell has two lines, `vougot` and `vuxot` (PDF p. 75). Only `vuxot`, the second spelling, is published as the variant (maintainer, 2026-10-15). For `vougot` 'to bind', van der Vlis gives a second spelling, `vuxot`, published as its variant.
#### Import decisions

- There are no `standard` `FORM` or `PHON` tiers, because FormosanBank has no Siraya standard orthography or phonology profile (see Source).
- Van der Vlis's own infix parses in column 4 are not published; the corpus follows Joby, so text after the headword in that column is dropped, except at row 1060 (`CodeAndDocs/source_decisions.json`, `alternate_form_rules`).
- Joby describes the manuscript as containing 1,072 lemmas, but the database has 1,061 detectable table rows; the build takes the database row as the unit and does not split any row to make up the difference (`CodeAndDocs/source_decisions.json`, `unit_model`).
- Fifteen forms occur in two separate source rows each; both rows are kept as separate records (`CodeAndDocs/source_decisions.json`, `repeat_policy`).

## Reproduction and processing

### How to reproduce

The XML, the source ledger, the reconciliation table, and the deterministic build code are available in the [FormosanBank repository](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/UtrechtManuscriptWordList).

The corpus rebuilds from a FormosanBank checkout alone. From the repository root:

```bash
python3 -m pip install -r Corpora/UtrechtManuscriptWordList/CodeAndDocs/requirements.txt
Corpora/UtrechtManuscriptWordList/CodeAndDocs/generate_xml.sh
```

The only requirement is `lxml` (pinned in `CodeAndDocs/requirements.txt`). Set `PYTHON` to use an interpreter other than `python3`. The quality checks run separately:

```bash
Corpora/UtrechtManuscriptWordList/CodeAndDocs/validate.sh
```

`validate.sh` calls the shared validators under `QC/validation/`, so it needs the repository's own Python environment.

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

**Build provenance:** [`CodeAndDocs/provenance.json`](CodeAndDocs/provenance.json).

The corpus is generated from the source table by `CodeAndDocs/generate_xml.sh`, which rebuilds it from a committed word-level extraction of the pinned database rather than from the PDF, so the build needs no external file. The commit the published XML was built against is recorded in [`CodeAndDocs/provenance.json`](CodeAndDocs/provenance.json). Quality checks live in a separate `CodeAndDocs/validate.sh`, so a failing check never blocks a rebuild.

Step 1 reads `CodeAndDocs/source/pdftotext.tsv`, the committed word-level extraction of the pinned PDF, so neither the PDF nor poppler is needed. To re-extract from the source instead, fetch the PDF and pass it:

```bash
brew install poppler          # provides pdftotext; there is no `pdftotext` formula
mkdir -p Corpora/UtrechtManuscriptWordList/Private
curl -L https://neerlandistiek.nl/wp-content/uploads/2021/07/UM-database.pdf \
  -o Corpora/UtrechtManuscriptWordList/Private/JobyUtrechtManuscript.pdf
python3 Corpora/UtrechtManuscriptWordList/CodeAndDocs/extract_source.py
```

The build verifies the source ledger's hash, regenerates the source-to-predecessor reconciliation, builds the XML, and compares a second generation byte for byte.

**POL-047 deviation:** `generate_xml.sh` runs steps 1 and 3 only. `apply_manual_edits.py` has nothing to apply; `clean_xml.py` is not run because the generator emits canonical text directly from a pinned ledger and has no scrape to clean; `standardize.py` and `add_phonology.py` are omitted because no Siraya standard orthography or phonology profile exists. QC lives in `CodeAndDocs/validate.sh`, separately, because a build that cannot finish when a validator fails cannot be used to investigate the failure.

#### Layout

- `XML/Siraya/Utrecht_Manuscript.xml`: canonical corpus XML.
- `CodeAndDocs/generate_xml.sh`: the build. `CodeAndDocs/validate.sh`: the QC run.
- `CodeAndDocs/source/`: the committed `pdftotext -tsv` extraction, the exact predecessor, the extracted source ledger, and the stable-ID reconciliation.
- `CodeAndDocs/source_decisions.json`: metadata, column mapping, editorial decisions, alternate translations, and repeated-attestation policy.
- `CodeAndDocs/tests/test_page_top_orphans.py`: a test of step 1's handling of lines that spill onto the top of the next page. It is not run by `generate_xml.sh`.

### What each step does

`generate_xml.sh` runs these in order and stops at the first failure.

**0. Provenance note.** It compares the current git commit with the one recorded in `CodeAndDocs/provenance.json` and, if they differ, prints a note. It never fails on this and never writes the file.

**1. `extract_source.py --tsv CodeAndDocs/source/pdftotext.tsv`** turns the extraction into the source ledger.
- Reads the word-level rows of the TSV and keeps only words whose top edge lies between 145 and 550 points (the table body).
- Words whose left edge lies between 50 and 70 points are the manuscript's own page markers, kept as `um_page_marker`. Every other word is assigned to one of the ten columns by fixed left-edge bands.
- A row starts at a column-1 line that begins at the same height as, or just above, the first line of cells in columns 2–5; starts closer than 20 points are merged. A row runs down to the next start. The last row on a page also takes any lines at the top of the next page that come before that page's first row start, so a cell that spills across a page break is not lost.
- The words of each cell are joined with single spaces, which is why a cell that wraps mid-word (row 122) arrives with a space in it.
- It fails unless exactly 1,061 rows are found, then writes `CodeAndDocs/source/source_records.json`: the rows with their PDF page and position, the row count, and a SHA-256 of the rows.
- Run without `--tsv` and with the PDF at `Private/JobyUtrechtManuscript.pdf`, it first checks the PDF's size (1,096,429 bytes) and SHA-256, then runs `pdftotext -tsv` itself.

**2. `reconcile_predecessor.py`** maps each source row to a stable `S` ID.
- Checks the ledger's row count and row SHA-256 against `CodeAndDocs/source_decisions.json`, and the predecessor file's size and SHA-256, failing on any drift.
- Reads the 1,052 `W` entries of `CodeAndDocs/source/public_predecessor.xml` (the pinned file has no closing `</TEXT>` tag, so one is appended before parsing).
- Retires 8 predecessor entries listed in `source_decisions.json`: `W11` (`Deus samma`, an exact duplicate of `W2`) and seven `samma` entries that are page-flow artifacts absent from Joby's table. It checks that each retired entry's ID and form still match.
- Pairs the remaining 1,044 predecessor entries, in order, with the 1,044 source rows that are not among the 17 rows new in Joby's table; then applies 4 pairing overrides where the predecessor has two neighbours in reversed order (`tagaraos`/`tagatimog`, source rows 38–39; `loudock`/`mala`, rows 101–102).
- Assigns IDs: the predecessor's ID by default; `Utrecht_Manuscript-S-rNNNN` for the 17 new rows; 5 ID overrides (rows 11, 480, 481 and 482 get `Utrecht_Manuscript-S-rNNNN` because the predecessor reused `W2`, `W474`, `W475` and `W476` for them; row 732 gets `W725`).
- Fails on any duplicate or invalid XML ID, then writes `CodeAndDocs/source/source_reconciliation.csv`. Its current status counts are 999 `retained_exact`, 40 `retained_source_corrected` (the predecessor's form differs from Joby's), 17 `new_source` and 5 `repaired_predecessor_id`.

**Stable ID scheme:** 1,044 predecessor records are carried over, and 1,039 of them keep their published IDs. Seventeen source rows missing from the predecessor use `Utrecht_Manuscript-S-rNNNN`; four reused predecessor IDs use the same source-row scheme; numeric-only `725` is repaired to `W725`. Every exception and retirement is listed in `CodeAndDocs/source/source_reconciliation.csv` and `CodeAndDocs/source_decisions.json`.

**POL-035 baseline:** `CodeAndDocs/source/public_predecessor.xml` is the exact 285,055-byte public predecessor, retained by SHA-256 for content and identifier reconciliation.

**3. `generate_xml.py`** writes `XML/Siraya/Utrecht_Manuscript.xml`.
- Reloads the ledger and predecessor with the same checks, rebuilds the reconciliation and fails if it differs from the committed CSV.
- Swaps the two van der Vlis columns back for source rows 223–233.
- `<TEXT>` gets exactly the attributes in `source_decisions.json` (`xml.attributes`): ID, `xml:lang`, source URL, copyright, citation, BibTeX citation and dialect.
- For each row, one `S` with the reconciled ID, then:
  - `FORM kindOf="original"`: column 1 as extracted, or, for the 13 rows in `form_decisions`, the decided form with a `notes` attribute (a deleted-transcription marker, an uncertain reading or an editorial remark moved out of the form, the row 122 join, and the two parsed rows).
  - For rows 105 and 233, a `FORM kindOf="original" ver="alt"` holding the source's own analysis, with a note.
  - Column 4 (van der Vlis's form): square-bracketed text removed, text after the headword dropped (row 1060 keeps only that text), row 599 dropped entirely (a Tsuchida citation). If what remains differs from the headword, it becomes `FORM kindOf="original" ver="alt" notes="van der Vlis 1842."`. For the two parsed rows the comparison ignores `<`, `>` and `-`.
  - Translations, in this order: column 3 (`nld`), column 2 (`nld`, skipped when identical to column 3), column 5 (`eng`). The 39 cells in `translation_decisions` use their recorded output. Otherwise, in the Dutch columns all bracketed text (outermost brackets, so nested ones stay together) moves to `notes`; in the English column `[ ]` become `( )`. The cell is then split on commas outside brackets and parentheses, unless the raw Siraya form contains a comma or the row is one of the 9 in `comma_split.do_not_split`. A reading already emitted for that language is skipped; every reading after the first in a language, and every column 2 reading, gets `ver="alt"`.
  - For the two rows with a parse (164 `t<m>atoutou`, 165 `va-va-rigbig`), one `W` with its `M`s.
- Result: 1,061 `S`; 81 variant `FORM`s; 1,047 `nld` + 115 `nld ver="alt"` and 1,050 `eng` + 183 `eng ver="alt"` `TRANSL`s; 2 `S` with `W`/`M` tiers.

**Recorded corrections:** The corpus is regenerated from the pinned source ledger through committed code and `source_decisions.json`. No `manual_edits.xml` is used.

**4. Determinism check.** `generate_xml.py` runs a second time into a temporary file, and `cmp` requires it to be byte-identical to the published XML.

#### Quality checks (`validate.sh`)

1. `audit_source_alignment.py` fails unless: `<TEXT>` has exactly the attributes in `source_decisions.json`; the `S` IDs and order equal the reconciliation; there is no `PHON`, no standard `FORM` and no `W`/`M` directly under `<TEXT>`; the XML is exactly what the decisions produce; `W` tiers sit on exactly the parsed rows; no translation repeats its form (the symptom of the rows 223–233 column swap); and no square brackets survive in any `FORM` or `TRANSL`.
2. `QC/validation/validate_xml.py`, `validate_text.py` and `validate_glosses.py`, each `by_path --path XML`.
3. `QC/validation/validate_port_readiness.py --corpus_path` on the corpus folder.

#### QC status

- Last QC run: 2026-09-08 (`CodeAndDocs/validate.sh`)
- Result: **0 HARD findings** from `validate_xml`, `validate_text`, `validate_glosses` and `validate_port_readiness`
- Expected SOFT findings: `V014` missing standard tier (by design, one per record); `V148` partially segmented file (two records carry a source-supplied parse, the rest have no `W` tier — POL-041 treats no-W as normal); `V122` parentheses in translations (the fifteen deliberate elaborations); `V134` angle brackets in an S-level `FORM` (POL-014 permits the source's infix typography there); `V116` one `ü`, in a van der Vlis alternate form; `V062`, `V064`, `V065` no glosses on the `W`/`M` tiers, which the source does not supply
- Gloss audit: not applicable beyond the two parsed records
