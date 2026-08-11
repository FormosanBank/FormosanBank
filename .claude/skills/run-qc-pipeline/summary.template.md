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
| `validate_xml.py` (XSD) | {{XML_RESULT}} | {{XML_NOTES}} |
| `validate_text.py` (punct + character set) | {{TEXT_RESULT}} | {{TEXT_NOTES}} |
| `validate_duplicate_sentences.py` (same-file dupes) | {{DUPES_RESULT}} | {{DUPES_NOTES}} |
| `validate_glosses.py` | {{GLOSSES_RESULT_OR_NA}} | {{GLOSSES_NOTES}} |
| `validate_audio.py` | {{AUDIO_RESULT_OR_NA}} | {{AUDIO_NOTES}} <!-- "skipped — audio not local" if applicable --> |

## Soft checks (info-only)

| Check | Number | Note |
|---|---|---|
| Orthography similarity vs reference | {{ORTHO_SIM}} | Thresholds uncalibrated (B Phase B4 work) |
| Vocabulary overlap vs reference | {{VOCAB_OVERLAP}} | Cross-genre comparisons may be noisy |
| Cross-file duplicate sentences (within corpus) | {{DUPES_SOFT_COUNT}} | May be legitimate (repeated proverbs etc.) |

## Dialect distribution

<!-- Paste the (xml:lang, dialect) -> count table from 05f_validate_dialect.log.
     Flag anything odd (missing dialects, leakage across languages) under
     "Unusual things surfaced". -->

## Unusual things surfaced

<!-- Anything the validators flagged that doesn't fit a category above, or that needs human judgment. -->

## Known limitations of this summary

- `validate_xml.py` may fail after Phase 4 (`add_phonology.py`) purely because the DTD currently has no `<PHON>` element. This is schema/code drift, not a corpus error. Resolving belongs to B's reconciliation work.

## Ready to port?

<!-- One-line verdict + reasoning. NOT a guarantee — the operator decides. -->
