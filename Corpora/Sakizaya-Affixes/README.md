# Akiw (2012) Sakizaya Affixes

**Languages:** Sakizaya (`szy`)
**Dialects:** Sakizaya
**Source:** Akiw, Chung-Wen Hsu's 2012 master's thesis, *The Study of Affixes in Sakizaya*
**License:** Included with the author's permission, recorded on Basecamp card `8176965975` on 2026-04-01
**Source orthography:** Ortho113
**FormosanBank tooling commit:** `3a3c47c220520113f747e6a2d441494000e13c4b`

This corpus contains the thesis's numbered examples and affix-inventory rows. It
has 670 sentence records with source-aligned word and morpheme analyses. All 113
late summary-table units remain in the extraction ledger but are excluded from
release XML after expert review. Nine source-starred examples and two additional
expert-identified ungrammatical examples are also excluded.

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

**Stable ID scheme:** The two `TEXT` IDs identify numbered examples and
affix-inventory rows. Sentence, word, and morpheme IDs derive from stable source
example or table-row identifiers and remain fixed across regeneration.

**POL-035 baseline evidence:** The regenerable pipeline verifies the 174-page
source scan at SHA-256
`fab787faf0e32cd087ba3dc222734132ad4213ca0804b8d5b32a318e66fbbbee` and
accounts for all 808 reviewed source units.

**POL-030 correction mechanism:** Source decisions are committed under
`CodeAndDocs/source_data/`, and Madeline Boese's 2026-08-14 reviewed tier
corrections are recorded in `CodeAndDocs/manual_edits.xml`.

## QC status

- Last QC run: 2026-08-22
- Status: ready to port
- Development source: `Formosan-Sakizaya-Affixes` commit
  `42585ef108a916a1c9f3226129fbb21c766deae7`
- Development audit: complete source review and current-authority refresh passed with verdict `ready to port`
- Gloss audit: 57 focused and 36 seeded checks passed
- Residual warning dispositions: source-attested partial morphology, composite
  table analyses, one expert-reviewed unglossed affix M, one standard-tier
  convergence group, and source-provenanced overlap with existing Sakizaya corpora
- Audio: none
