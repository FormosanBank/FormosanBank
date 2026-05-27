# QC Summary: {{CORPUS_NAME}}

**Dev repo:** {{DEV_REPO_PATH}}
**Run timestamp:** {{TIMESTAMP_UTC}}
**XML location:** {{XML_PATH}}

## Orthography

- Original (determined in Phase 2): **{{ORIGINAL_ORTHOGRAPHY}}**
- Detector output that informed the decision: see `<output_dir>/orthography_detector.log`
- Standardize args used: `{{STANDARDIZE_ARGS}}`

## Counts

| Metric | Value |
|---|---|
| Texts | {{N_TEXTS}} |
| Sentences | {{N_SENTENCES}} |
| Words (W-tier) | {{N_WORDS_OR_NA}} |
| Morphemes (M-tier) | {{N_MORPHEMES_OR_NA}} |
| Languages | {{LANGUAGES_LIST}} |
| Dialects | {{DIALECTS_LIST}} |

## Hard-gate findings

| Check | Result | Notes |
|---|---|---|
| `validate_xml.py` (DTD) | {{XML_RESULT}} | {{XML_NOTES}} |
| `validate_punct.py` | {{PUNCT_RESULT}} | {{PUNCT_NOTES}} |
| `validate_glosses.py` | {{GLOSSES_RESULT_OR_NA}} | {{GLOSSES_NOTES}} |

## Soft checks (info-only)

| Check | Number | Note |
|---|---|---|
| Orthography similarity vs reference | {{ORTHO_SIM}} | Thresholds uncalibrated (B Phase B4 work) |
| Vocabulary overlap vs reference | {{VOCAB_OVERLAP}} | Cross-genre comparisons may be noisy |

## Unusual things surfaced

<!-- Anything the validators flagged that doesn't fit a category above, or that needs human judgment. -->

## Known limitations of this summary

- `validate_xml.py` may fail after Phase 4 (`add_phonology.py`) purely because the DTD currently has no `<PHON>` element. This is schema/code drift, not a corpus error. Resolving belongs to B's reconciliation work.

## Ready to port?

<!-- One-line verdict + reasoning. NOT a guarantee — the operator decides. -->
