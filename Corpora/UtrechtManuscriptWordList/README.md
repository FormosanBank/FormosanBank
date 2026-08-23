# Utrecht Manuscript Word List

**Language:** Siraya (`fos`)

**Dialect:** Siraya

**Source:** Christopher Joby's corrected Utrecht Manuscript database

**License:** CC BY-NC 4.0

**Source orthography:** Historical Latin-script Utrecht Manuscript transcription, corrected by Joby
**FormosanBank tooling commit:** `3a3c47c220520113f747e6a2d441494000e13c4b`

## License and AI use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

Christopher Joby's 75-page database provides corrected Siraya forms, historical Dutch translations, comparison data, and English translations for the seventeenth-century Utrecht Manuscript word list. The recorded source permission authorizes Joby's corrected transcriptions and translations under CC BY-NC 4.0.

The canonical XML contains 1,061 source-row records. Each database row becomes one `S`, following the source-specific decision to use no `W` tier. Current FormosanBank authority has no Siraya standard or phonology profile, so the corpus contains original FORM tiers and source translations without invented standard FORM or PHON tiers.

## Citation

Joby, Christopher. (2021). *Utrecht Manuscript, Siraya-Nederlands woordenlijst / UM database*. Neerlandistiek. https://neerlandistiek.nl/wp-content/uploads/2021/07/UM-database.pdf

## Reproducibility

The corrected PDF is public but is not stored in this repository. From the FormosanBank repository root:

```bash
python3 -m pip install -r Corpora/UtrechtManuscriptWordList/CodeAndDocs/requirements.txt
mkdir -p Corpora/UtrechtManuscriptWordList/Private
curl -L https://neerlandistiek.nl/wp-content/uploads/2021/07/UM-database.pdf \
  -o Corpora/UtrechtManuscriptWordList/Private/JobyUtrechtManuscript.pdf
PYTHON=python3 Corpora/UtrechtManuscriptWordList/CodeAndDocs/make_xml.sh
```

The build verifies the PDF's byte size and SHA-256, extracts all ten source columns, regenerates the source-to-predecessor reconciliation, builds XML, runs a fail-closed source audit, and compares a second generation byte for byte.

**Stable ID scheme:** 1,044 predecessor records retain their published IDs. Seventeen source rows missing from the predecessor use `Utrecht_Manuscript-S-rNNNN`; four reused predecessor IDs use the same source-row scheme; numeric-only `725` is repaired to `W725`. Every exception and retirement is listed in `CodeAndDocs/source/source_reconciliation.csv` and `CodeAndDocs/source_decisions.json`.

**POL-035 baseline:** `CodeAndDocs/source/public_predecessor.xml` is the exact 285,055-byte public predecessor at the tooling commit above. It is retained by SHA-256 for content and identifier reconciliation.

**Recorded corrections:** The corpus is regenerated from the pinned source ledger through committed code and `source_decisions.json`. No `manual_edits.xml` is used.

## QC status

- Last QC run: 2026-08-23
- Status: `ready to port`
- Development source: private repository `FormosanBank/Formosan-UtrechtManuscriptWordList`; the verified commit is recorded in the publication PR
- Development audit: `ready for QC`, with complete source and predecessor accounting
- Gloss audit: not applicable because the source and XML contain no W/M analysis
- Residual warnings: missing-standard and missing-W soft findings are expected; balanced source parentheticals and 15 page-distinct repeated forms are explicitly dispositioned

## Layout

- `XML/Siraya/Utrecht_Manuscript.xml`: canonical corpus XML.
- `CodeAndDocs/source/`: exact predecessor, extracted source ledger, and stable-ID reconciliation.
- `CodeAndDocs/source_decisions.json`: metadata, editorial decisions, alternate translations, and repeated-attestation policy.
- `CodeAndDocs/make_xml.sh`: complete deterministic build and source audit.

## Audio

The source and corpus contain no audio.

## Additional reference

C. J. van der Vlis. (1842). *Formosaansche woorden-lijst, volgens een Utrechtsch handschrift*. This public-domain edition is a comparison witness, not the authority for Joby's corrected Siraya forms.
