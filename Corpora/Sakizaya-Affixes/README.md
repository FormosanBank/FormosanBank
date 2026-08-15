# Akiw (2012) Sakizaya Affixes

**Languages:** Sakizaya (`szy`)
**Dialects:** Sakizaya
**Source:** Akiw, Chung-Wen Hsu's 2012 master's thesis, *The Study of Affixes in Sakizaya*
**License:** Included with the author's permission, recorded on Basecamp card `8176965975` on 2026-04-01
**Source orthography:** Ortho113
**FormosanBank tooling commit:** `3a3c47c220520113f747e6a2d441494000e13c4b`

This corpus contains the thesis's numbered examples, affix-inventory rows, and
late summary or comparison-table rows. It has 681 sentence records with source
aligned word and morpheme analyses. Source glosses are preserved as original
gloss tiers. Nine source-starred examples are retained in the extraction ledger
but excluded from the published XML under POL-016.

## Citation

Akiw, Chung-Wen Hsu. 2012. *The Study of Affixes in Sakizaya*. Master's thesis,
National Dong Hwa University.

## Reproducibility

`CodeAndDocs/` contains the generators, reviewed source-decision tables, audit
scripts, and deterministic reproduction wrapper used to produce `XML/`. The
source scan and OCR comparison copy are not published. They are installed into
an ignored `Private/source/` directory from authenticated Basecamp access or an
exact local copy.

To rebuild from source:

1. Prepare a clean FormosanBank checkout at commit
   `3a3c47c220520113f747e6a2d441494000e13c4b`.
2. Set `SOURCE_DIR` to a directory containing the two checksum-verified source
   files, or authenticate the Basecamp CLI.
3. Run:

   ```bash
   SOURCE_DIR=/path/to/source-files \
   FORMOSANBANK_QC_ROOT=/path/to/pinned/FormosanBank \
   FORMOSANBANK_QC_PYTHON=/path/to/pinned/FormosanBank/.venv/bin/python \
   ./CodeAndDocs/reproduce.sh
   ```

**Stable ID scheme:** The three `TEXT` IDs identify numbered examples,
affix-inventory rows, and summary rows. Sentence, word, and morpheme IDs are
derived from stable source example or table-row identifiers and remain fixed
across regeneration.

**POL-035 baseline evidence:** The regenerable pipeline verifies the 174-page
source scan at SHA-256
`fab787faf0e32cd087ba3dc222734132ad4213ca0804b8d5b32a318e66fbbbee` and
accounts for all 808 reviewed source units.

**POL-030 correction mechanism:** Source corrections, mappings, and exclusions
are committed as CSV data under `CodeAndDocs/source_data/`. No manual-edit file
is required.

## QC status

- Last QC run: 2026-08-13
- Status: ready to port
- Development source: `Formosan-Sakizaya-Affixes` commit
  `e5fbe20c07789050b6ce369815427b60bd74194c`
- Development audit: post-remediation audit passed with verdict `ready for QC`
- Gloss audit: passed after complete source-backed adjudication
- Residual warning dispositions: source-attested partial morphology, composite
  table analyses, one unglossed null morpheme, two standard-tier convergences,
  and source-provenanced lexical overlap with existing Sakizaya corpora
- Audio: none
