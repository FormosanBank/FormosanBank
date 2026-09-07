---
icon: gears
---

# QC Pipeline

FormosanBank ships a collection of small, modular Python scripts that **validate, clean, standardize, and measure** the XML corpora. This section documents every script that is part of the working pipeline: what each one is for, how it works, and exactly how to run it.

The tooling lives in the [main FormosanBank repository](https://github.com/FormosanBank/FormosanBank) under `QC/`. None of it is needed to *consume* the corpora — it exists to keep the published data consistent and to support the audit/port workflow by which new corpora enter the bank.

{% hint style="info" %}
The scripts are intentionally **modular**: you run the checks that match a corpus's state rather than treating every warning as a fatal error. Read this overview once to learn the shared conventions, then jump to the page for the tool you need.
{% endhint %}

## The two-tier text model

Almost every script cares about the distinction between two sentence-level `FORM` tiers:

- **`kindOf="original"`** — the text as it appeared in the source (book, website, recording transcript), after only light punctuation/HTML normalization. It preserves the source's orthographic choices and must stay faithful to the source.
- **`kindOf="standard"`** — the same content transliterated into FormosanBank's single common orthography, so material from different sources is comparable.

Many checks assume **both** tiers exist. If a corpus has only the original tier, create the standard tier with [standardize.py](standardize.md) `--copy` (an exact duplicate — no spelling change) before running the text/orthography stages. Orthography and metrics work generally targets `--kindOf standard`; anything that must represent the source faithfully targets `--kindOf original`. The full XML schema is described in [FormosanBank XML Format](../../formosanbank-xml-format.md).

## The Finding / Severity framework

The finding-based validators — [validate_xml.py](validate-xml.md), [validate_text.py](validate-text.md), and [validate_glosses.py](validate-glosses.md) — share a common framework (`QC/validation/_finding.py`, `_report.py`). Each rule has a mnemonic ID (e.g. `V013 S_must_have_original_FORM`) and a **severity**:

| Severity | Behaviour |
|----------|-----------|
| **HARD** | A real schema/structure violation. Drives the exit code — any HARD finding exits `1` (CI-gating). |
| **SOFT** | A candidate cleanup or review item. Reported and written to the findings CSV, but **never** changes the exit code. |
| **WARN** | Advisory only. Reserved; rarely used. |

These validators print a compact **per-rule summary** to the terminal and write **one findings CSV** whose path is announced as `Details: <path>` — per-finding detail lives in the CSV, not the terminal. To look up an id you saw in either, see [The rule catalogue](rule-catalogue.md), which lists all 83 rules and is generated from the code. Pass `--no-exit-on-hard` to inspect findings without failing your shell (useful during discovery; CI leaves it off so HARD findings gate).

{% hint style="warning" %}
Not every validator uses this framework. [validate_dialect.py](validate-dialect.md), [validate_orthography.py](validate-orthography.md), [validate_vocabulary.py](validate-vocabulary.md), and [validate_duplicate_sentences.py](validate-duplicate-sentences.md) print their own reports and **always exit 0** — they are informational. Each page says which kind it is.
{% endhint %}

### Pull request baseline behavior

The XML validation workflow runs `validate_xml.py`, `validate_text.py`, and `validate_glosses.py` on every added or modified file under `Corpora/*/XML/`. For a modified legacy file, `compare_findings.py` compares candidate and base findings by `rule_id`, `location`, `language`, and `character`; only newly introduced HARD findings block the pull request. An added file has an empty baseline and therefore must have no HARD findings. On pushes to `main`, the full-corpus run remains informational and uploads its findings as a longitudinal cleanup baseline.

## The `search_by` pattern

Most validators and several utilities share a `search_by` positional with three modes:

```bash
# A file or directory — the safest, most explicit target
python QC/validation/validate_xml.py by_path --path Corpora/ePark/XML

# A named corpus (walks <corpora_path>/<corpus>/XML/)
python QC/validation/validate_xml.py by_corpus --corpus ePark --corpora_path Corpora

# Every canonical file whose root xml:lang matches
python QC/validation/validate_xml.py by_language --language ami --corpora_path Corpora
```

When in doubt, `by_path` against a single corpus's `XML/` directory is the safest target. All commands in this section assume you run from the FormosanBank repo root after `source .venv/bin/activate`.

## Two pipelines: build vs. check

The QC tooling runs in two distinct passes, in this order. The first **transforms** the XML; the second **inspects** it.

- The **cleaning & standardization pipeline** takes a corpus's raw ingestion output and builds it into the canonical two-tier form. Its scripts **mutate the XML in place**. It runs in a corpus's `Formosan-<Name>/` dev repo as the corpus is developed.
- The **validation pipeline** runs afterward (and in CI). Its scripts are **read-only** — they report findings and never change the data.

The guided [`run-qc-pipeline` skill](../using-the-claude-skills.md) runs both in a single pass (cleaning & standardization first, then validation); the [`audit-dev-repo` skill](../using-the-claude-skills.md) drives the validation pipeline plus a source diff. See [Running an Audit](../running-an-audit.md) and [Porting a Corpus In](../porting-a-corpus.md) for the end-to-end workflows.

### The cleaning & standardization pipeline

Run in order; every step here writes to the XML, so `git diff` before committing.

1. [apply_manual_edits.py](manual-edits.md) — replay any recorded hand edits first (no-op if the corpus has none).
2. [clean_xml.py](clean-xml.md) — normalize unicode, punctuation, and HTML entities; language-aware segmentation handling.
3. **Orthography detection** *(human judgment)* — [orthography_detector.py](orthography-detector.md) analyzes the `original` tier; a human decides the corpus's source orthography, which determines the next step.
4. [standardize.py](standardize.md) — build the `standard` `FORM` tier: `--copy` for an exact duplicate (Ortho113 corpora), or a TSV mapping to transliterate.
5. [add_phonology.py](add-phonology.md) — add `PHON` tiers from the orthography→phoneme tables.

### The validation pipeline

Run after the XML is built (these are read-only). XML format must pass first; later stages assume structurally valid input.

1. [validate_xml.py](validate-xml.md) — XSD conformance and structure. **Must pass first.**
2. [validate_dialect.py](validate-dialect.md) — eyeball the `(xml:lang, dialect)` distribution.
3. [validate_text.py](validate-text.md) — punctuation, character set, processing artifacts. (Needs a `standard` tier; if a corpus skipped the build pipeline, create one with [standardize.py](standardize.md) `--copy` first.)
4. [orthography_extract.py](orthography-extract.md) `--kindOf standard --by_dialect true`, then [validate_orthography.py](validate-orthography.md) and [validate_vocabulary.py](validate-vocabulary.md) against the per-language reference data.
5. [validate_glosses.py](validate-glosses.md) — only for corpora with `W`/`M` segmentation.
6. [validate_audio.py](validate-audio.md) — only for corpora with audio.

(See [QC/README.md](https://github.com/FormosanBank/FormosanBank/blob/main/QC/README.md) for the authoritative version of both sequences.)

{% hint style="danger" %}
Everything in the **cleaning & standardization** pipeline — plus the [fix-up utilities](fix-up-utilities.md) — modifies XML *in place*. Some cleaners default to `--dry-run`, but several (e.g. `clean_xml.py`, `apply_manual_edits.py`, `standardize.py`) mutate immediately. Always `git diff` before committing. The **validation** pipeline never mutates data.
{% endhint %}

## Reference pages

### Validation

* [validate_xml.py](validate-xml.md) — schema & structure (stage 1 gate)
* [validate_dialect.py](validate-dialect.md) — dialect distribution summary
* [validate_text.py](validate-text.md) — punctuation, character set, processing artifacts
* [validate_glosses.py](validate-glosses.md) — word/morpheme gloss-tier checks
* [validate_orthography.py](validate-orthography.md) — orthography vs reference
* [validate_vocabulary.py](validate-vocabulary.md) — vocabulary vs reference
* [validate_duplicate_sentences.py](validate-duplicate-sentences.md) — within-corpus duplicates
* [validate_audio.py](validate-audio.md) — broken/silent/mis-ranged audio

### Cleaning

* [Manual edits](manual-edits.md) — capture & replay reproducible hand edits (runs first)
* [clean_xml.py](clean-xml.md): Unicode, entity, punctuation, and translation-metadata normalization
* [clean_audio.py](clean-audio.md) — remove broken `<AUDIO>` entries
* [clean_filepaths.py](clean-filepaths.md) — sanitize cross-platform filenames
* [remove_duplicate_sentences.py](remove-duplicate-sentences.md) — drop duplicate `<S>`
* [suppress_transl_annotations.py](suppress-transl-annotations.md) — strip annotator notes from `<TRANSL>`

### Orthography & tier building

* [orthography_extract.py](orthography-extract.md) — grapheme inventories & statistics
* [orthography_compare.py](orthography-compare.md) — compare two corpora
* [standardize.py](standardize.md) — build the `standard` `FORM` tier
* [add_phonology.py](add-phonology.md) — add `PHON` tiers
* [orthography_detector.py](orthography-detector.md) — guess a corpus's source orthography
* [dialect_detector](dialect-detector.md) — ML per-language dialect prediction

### Fix-ups & review

* [Fix-up utilities](fix-up-utilities.md) — `fix_dialects`, `fix_ids`, `fix_multiple_translations`
* [sample_sentences.py](sample-sentences.md) — random `<S>` sample for human review
* [find_duplicate_sentences.py](find-duplicate-sentences.md) — cross-corpus duplicate detection
* [OCR Review Tool](ocr-review-tool.md): guided, resumable human review of OCR-derived XML

### Audio quality & MT

* [Audio quality triage](audio-quality-triage.md) — score → flag → manually verify (MT data prep)
* [BLEU evaluation](bleu-evaluation.md) — `bleu_scores`, `bleu_long_texts`

### Statistics & CI

* [get_corpus_stats.py](get-corpus-stats.md) — per-corpus stats CSV the GitBook consumes
* [corpus_metrics.py](corpus-metrics.md) — aggregate metrics & growth history
* [Token counting](token-counting.md) — `count_tokens`, `tokens_delta`, `corpus_counts`, plots
* [Audio duration stats](audio-duration-stats.md) — `update`/`refresh_audio_stats`, `audio_durations.csv`

### Miscellaneous

* [Misc utilities](misc-utilities.md) — `add_durations`, `group_audios`, `organize_batches`, `upload_to_hf`
