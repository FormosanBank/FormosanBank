# Lin (2015) Amis and Kavalan Interrogative Verbs

**Languages:** Amis (`ami`) and Kavalan (`ckv`)
**Dialects:** Xiuguluan Amis and Kavalan
**Source:** Dong-yi Lin's 2015 chapter, “The syntactic derivations of interrogative verbs in Amis and Kavalan”
**License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
**Source orthography:** LinAmis for Amis and Ortho113 for Kavalan
**FormosanBank tooling commit:** `3a3c47c220520113f747e6a2d441494000e13c4b`

The corpus contains 76 sentence records, evenly divided between Amis and
Kavalan. It preserves source-aligned word and morpheme analyses, source glosses,
alternate translations, and eight fully aligned optional-form expansions.
Starred and marginal source examples remain in the exclusion ledger and are not
included in the published XML.

## Citation

Lin, Dong-yi. 2015. The syntactic derivations of interrogative verbs in Amis
and Kavalan. In Elizabeth Zeitoun, Stacy F. Teng, and Joy J. Wu (eds.), *New
Advances in Formosan Linguistics*, 253–289. Asia-Pacific Linguistics.

## Reproducibility

`CodeAndDocs/` contains the extraction model, source-review ledgers, custom Amis
orthography profile and conversion table, builders, audits, regression tests,
and deterministic reproduction wrapper used to produce `XML/`.

The complete source-assisted gate requires the source PDF, license screenshot,
and `pdftotext -layout` cache at the paths declared in
`CodeAndDocs/run_qc_pipeline.sh`. The chapter is available from
[ANU Open Research](https://openresearch-repository.anu.edu.au/items/249b6de8-c40b-4e66-8198-dfeedfc380bf).

To rebuild from source, prepare a separate clean FormosanBank checkout at the
tooling commit above, install the three source-evidence files under the declared
ignored `Private/` paths, and run:

```bash
FORMOSANBANK_QC_ROOT=/path/to/pinned/FormosanBank \
FORMOSANBANK_QC_PYTHON=/path/to/pinned/FormosanBank/.venv/bin/python \
./CodeAndDocs/reproduce.sh
```

**Stable ID scheme:** The two `TEXT` IDs identify the Amis and Kavalan source
sets. Sentence IDs derive from the source language and numbered example, with
deterministic suffixes for optional variants. Word and morpheme IDs derive from
their parent sentence and aligned position.

**POL-035 baseline evidence:** The regenerable pipeline verifies the 38-page
source PDF at SHA-256
`fb39fca379012a953ed21bc82d39c2545adc0227aa870a009841ed318aece28d` and
accounts for 95 Formosan source occurrences plus 18 theory or comparison units.

**POL-030 correction mechanism:** Source decisions and exclusions are committed
in the extraction and review ledgers. No manual-edit file is required.

## QC status

- Last QC run: 2026-08-22
- Status: ready to port
- Development source: `Formosan-Amis-Kavalan-Lin-Interrogative-Verbs` commit
  `19f7d557f66c9476ffc90f5a9785fbda443c3af6`
- Development audit: source-assisted current-authority refresh passed with verdict `ready to port`
- Gloss audit: 56 source-assisted findings fully reconciled, with 0 unresolved
- Residual warning dispositions: eight permitted translation parentheticals,
  one source-required optional-variant duplicate group, and the reviewed Amis
  conversion-table reminder
- Audio: none
