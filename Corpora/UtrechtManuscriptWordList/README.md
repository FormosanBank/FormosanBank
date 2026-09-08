# Utrecht Manuscript Word List

**Language:** Siraya (`fos`)

**Dialect:** Siraya

**Source:** Christopher Joby's corrected Utrecht Manuscript database

**Source orthography:** Historical Latin-script Utrecht Manuscript transcription, corrected by Joby

Christopher Joby's 75-page database provides corrected Siraya forms, historical Dutch translations, comparison data, and English translations for the seventeenth-century Utrecht Manuscript word list.

The canonical XML contains 1,061 source-row records. Each database row becomes one `S`, following the source-specific decision to use no `W` tier except where the source itself supplies a morphological analysis. Current FormosanBank authority has no Siraya standard orthography or phonology profile, so the corpus contains original `FORM` tiers and source translations without invented `standard` `FORM` or `PHON` tiers.

## Rights

**License:** CC BY-NC 4.0
**Rights source:** Christopher Joby, 2021-07-06; evidence: ask maintainer

Joby authorized use of his corrected transcriptions and translations under this licence. The permission is recorded against the project's source manifest; the maintainer holds the correspondence.

## License and AI use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

## Citation

Joby, C. (2021). Revisions to the Siraya lexicon based on the original Utrecht Manuscript: A case study in source data. *Historiographia Linguistica*, 48(2-3), 177-204.

The data itself is Joby's accompanying database, *Utrecht Manuscript, Siraya-Nederlands woordenlijst / UM database* (Neerlandistiek, 2021), pinned by SHA-256 in [`CodeAndDocs/source_manifest.json`](CodeAndDocs/source_manifest.json) and published at https://neerlandistiek.nl/wp-content/uploads/2021/07/UM-database.pdf — it is the file the build reads, but the article is what to cite.

## What the source columns become

The database is a ten-column comparative table. Five columns are published:

| # | column | becomes |
|---|---|---|
| 1 | `UM Formosana` — Joby's corrected reading | `FORM kindOf="original"` |
| 2 | `UM Belgica` — the manuscript's own Dutch | `TRANSL xml:lang="nld" ver="alt"`, **only where it differs from column 3** |
| 3 | `VdV Dutch` — van der Vlis 1842 | `TRANSL xml:lang="nld"` |
| 4 | `VdV Siraya` — van der Vlis 1842 | `FORM kindOf="alternate"`, where it differs from column 1 |
| 5 | `My English` — Joby's own English | `TRANSL xml:lang="eng"` |

Columns 6 (`Murakami`), 7 (`Gospel/Formulary equivalent`) and 8–10 (`Variation`, `etyma`, `Other sources`) are **not published**. Column 7 in particular was considered and ruled out: its 519 Gospel-dialect forms would have committed the corpus to a second orthography, to morpheme boundaries inside an S-level `FORM`, and to a dialect that `TEXT/@dialect` cannot express.

Editorial material is separated from translation by column, because the column decides its kind. Brackets in columns 2 and 3 are always apparatus about the manuscript — `[sic]`, `[recte …]`, `[… scored through]`, dictionary citations — and move to `TRANSL/@notes`. Brackets in column 5 are always Joby's own, and stay inline as parentheses where they elaborate. A comma in a translation that the Siraya form does not have separates alternative readings, which become `ver="alt"` translations. Every exception is recorded in `CodeAndDocs/source_decisions.json`.

## Reproducibility

The corpus rebuilds from a FormosanBank checkout alone. From the repository root:

```bash
python3 -m pip install -r Corpora/UtrechtManuscriptWordList/CodeAndDocs/requirements.txt
Corpora/UtrechtManuscriptWordList/CodeAndDocs/generate_xml.sh
```

Step 1 reads `CodeAndDocs/source/pdftotext.tsv`, the committed word-level extraction of the pinned PDF, so neither the PDF nor poppler is needed. To re-extract from the source instead, fetch the PDF and pass it:

```bash
brew install poppler          # provides pdftotext; there is no `pdftotext` formula
mkdir -p Corpora/UtrechtManuscriptWordList/Private
curl -L https://neerlandistiek.nl/wp-content/uploads/2021/07/UM-database.pdf \
  -o Corpora/UtrechtManuscriptWordList/Private/JobyUtrechtManuscript.pdf
python3 Corpora/UtrechtManuscriptWordList/CodeAndDocs/extract_source.py
```

The build verifies the source ledger's hash, regenerates the source-to-predecessor reconciliation, builds the XML, and compares a second generation byte for byte.

**Deviation from POL-047.** `generate_xml.sh` runs steps 1 and 3 only. `apply_manual_edits.py` has nothing to apply; `clean_xml.py` is not run because the generator emits canonical text directly from a pinned ledger and has no scrape to clean; `standardize.py` and `add_phonology.py` are omitted because no Siraya standard orthography or phonology profile exists. QC lives in `CodeAndDocs/validate.sh`, separately, because a build that cannot finish when a validator fails cannot be used to investigate the failure.

**Build provenance:** [`CodeAndDocs/provenance.json`](CodeAndDocs/provenance.json).

**Stable ID scheme:** 1,044 predecessor records retain their published IDs. Seventeen source rows missing from the predecessor use `Utrecht_Manuscript-S-rNNNN`; four reused predecessor IDs use the same source-row scheme; numeric-only `725` is repaired to `W725`. Every exception and retirement is listed in `CodeAndDocs/source/source_reconciliation.csv` and `CodeAndDocs/source_decisions.json`.

**POL-035 baseline:** `CodeAndDocs/source/public_predecessor.xml` is the exact 285,055-byte public predecessor, retained by SHA-256 for content and identifier reconciliation.

**Recorded corrections:** The corpus is regenerated from the pinned source ledger through committed code and `source_decisions.json`. No `manual_edits.xml` is used.

## Known source anomalies

- **Rows 223–233** fill the two van der Vlis columns in the opposite order, a run that begins at manuscript page marker 12 and spans PDF pages 16–17. Confirmed against the source; the published predecessor reproduced the same anomaly, publishing the Siraya form as its own Dutch translation. The build swaps them back.
- Row 122's `pasagoualalingaua ng` carries a space that both other witnesses set solid; it is published as the source has it.

## QC status

- Last QC run: 2026-09-08 (`CodeAndDocs/validate.sh`)
- Result: **0 HARD findings** from `validate_xml`, `validate_text`, `validate_glosses` and `validate_port_readiness`
- Expected SOFT findings: `V014` missing standard tier (by design, one per record); `V148` partially segmented file (two records carry a source-supplied parse, the rest have no `W` tier — POL-041 treats no-W as normal); `V122` parentheses in translations (the fifteen deliberate elaborations); `V134` angle brackets in an S-level `FORM` (POL-014 permits the source's infix typography there); `V116` one `ü`, in a van der Vlis alternate form; `V062`, `V064`, `V065` no glosses on the `W`/`M` tiers, which the source does not supply
- Gloss audit: not applicable beyond the two parsed records

## Layout

- `XML/Siraya/Utrecht_Manuscript.xml`: canonical corpus XML.
- `CodeAndDocs/generate_xml.sh`: the build. `CodeAndDocs/validate.sh`: the QC run.
- `CodeAndDocs/source/`: the committed `pdftotext -tsv` extraction, the exact predecessor, the extracted source ledger, and the stable-ID reconciliation.
- `CodeAndDocs/source_decisions.json`: metadata, column mapping, editorial decisions, alternate translations, and repeated-attestation policy.

## Audio

The source and corpus contain no audio.

## Additional reference

C. J. van der Vlis. (1842). *Formosaansche woorden-lijst, volgens een Utrechtsch handschrift*. This public-domain edition is a comparison witness, not the authority for Joby's corrected Siraya forms.
