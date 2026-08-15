# Asai et al. (2026) Kanakanavu Texts

**Languages:** Kanakanavu (`xnb`)
**Dialects:** Kanakanavu
**Source:** Asai, Mei, Li, and Tsuchida's 2026 *Kanakanavu Texts*
**License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
**Source orthography:** Asai 2026, standardized to Ortho113
**FormosanBank tooling commit:** `3a3c47c220520113f747e6a2d441494000e13c4b`

This corpus contains the grammatical introduction examples and 44 narratives
from the source volume. Its 1,455 sentence records preserve English
translations and source-aligned word and morpheme analyses. Twenty-four
reviewed optional or alternative constructions are represented as complete,
aligned variants. Four square-bracket source-analysis constructions remain
sentence-only to avoid inventing an analysis.

## Citation

Asai, E., Mei, K., Li, P. J.-k., & Tsuchida, S. 2026. *Kanakanavu Texts*
(P. J.-k. Li, Ed.). Research Institute for Languages and Cultures of Asia and
Africa, Tokyo University of Foreign Studies.

## Reproducibility

`CodeAndDocs/` contains the CC BY 4.0 source PDF, extraction pipeline, reviewed
orthography and conversion files, source-audit tools, tests, and deterministic
two-pass reproduction wrapper. The wrapper regenerates a working XML tree under
`CodeAndDocs/XML/` and verifies that it is byte-identical to the published
corpus-level `XML/` tree.

To rebuild from source:

1. Prepare a separate clean FormosanBank checkout at commit
   `3a3c47c220520113f747e6a2d441494000e13c4b`.
2. From `CodeAndDocs/`, create a Python environment and install
   `requirements.txt`.
3. Run:

   ```bash
   FORMOSANBANK_PATH=/path/to/pinned/FormosanBank \
   make reproduce PYTHON=.venv/bin/python
   ```

**Stable ID scheme:** Each `TEXT` ID is derived from the fixed source text
number and title. Sentence IDs derive from stable source-unit identifiers, with
deterministic suffixes for expanded variants. Word and morpheme IDs derive from
their parent sentence and aligned position.

**POL-035 baseline evidence:** The regenerable pipeline verifies the tracked
252-page source PDF at SHA-256
`785058bad6a8495f8b5fb51ed3d0eaf7da1736e791b308611d9442c010d93c03` and
accounts for all 45 texts and 1,431 extracted source units.

**POL-030 correction mechanism:** Reviewed extraction, source-notation,
variant, standardization, and phonology decisions are enforced by committed
pipeline code and generated audit ledgers. No manual-edit file is required.

## QC status

- Last QC run: 2026-08-13
- Status: ready to port
- Development source: `Formosan-Kanakanavu-Texts` commit
  `a5a514d3dac2e362739121d7c9d1af5992a10faf`
- Development audit: post-remediation audit passed with verdict `ready for QC`
- Gloss audit: 673 source-assisted findings fully reconciled, with 0 unresolved
- Residual warning dispositions: four intentional sentence-only analyses, 17
  source-required duplicate groups, 77 visible foreign-loan PHON markers, and
  three expert-reviewed conversion mismatches
- Audio: none
