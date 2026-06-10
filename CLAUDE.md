# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

FormosanBank is a corpus collection for the 16 Formosan (indigenous Taiwanese) languages, plus the Python QC tooling that validates, cleans, and reports on it. The project is modeled after TalkBank. Code is small and procedural; the heart of the repo is the XML data under [Corpora/](Corpora/) and the conventions that make it consistent.

## Development workflow: corpus dev happens elsewhere

**New corpora are not developed in this repo.** Initial processing of a new corpus happens in a corpus-specific repo (most are siblings at `~/Documents/Projects/Formosan/Formosan-<CorpusName>/`). Only after a corpus passes QC and is approved for publication is it ported into `Corpora/` here.

Reasons:
1. Prevents users from depending on data that hasn't passed QC.
2. Original source data may include private content that can't be shared publicly.
3. Working-state organization during processing is messier than the published layout under `Corpora/<Name>/{XML,CodeAndDocs}/`.

If a task involves *creating* or *substantially reworking* a corpus rather than maintaining the published version, the work likely belongs in the corpus-specific dev repo, not here.

## Related repos

- **`../FormosanBankGitbook/`** — public-facing documentation site for both end-users of the corpora and FormosanBank contributors. Published at https://ai4commsci.gitbook.io/formosanbank. Available in multiple languages; **the English version is canonical**, others are typically out of date or incomplete. Ultimately should reflect what's in this repo.
- **`../Formosan-<CorpusName>/`** — per-corpus development repos. See "Development workflow" above.

## Environment

Python 3.10 (matches CI in [.github/workflows/](.github/workflows/)). A `.venv` exists in the repo root — activate it before running anything: `source .venv/bin/activate`. Deps are pinned in [requirements.txt](requirements.txt).

Audio files (`*.wav`, `*.mp3`) are gitignored and pulled per-corpus via [run_audio_downloads.sh](run_audio_downloads.sh), which iterates `Corpora/*/download_audio_data.sh`. Audio downloads require `git-lfs`, `jq`, and the `hf` (huggingface) CLI.

## Corpus layout and XML schema

Each corpus *should* contain (this is the standard, not always followed in older corpora):
- `README.md` — description of the corpus, where the source data came from, and how to run the scripts under `CodeAndDocs/`
- `download_audio_data.sh` — only if the corpus has audio
- `XML/` — the canonical, published data, often further split by language (e.g. [Corpora/Wikipedias/XML/Amis/](Corpora/Wikipedias/XML/Amis/)) or sub-corpus (e.g. [Corpora/ePark/XML/](Corpora/ePark/XML/))
- `CodeAndDocs/` — the scripts required to **reproduce** the contents of `XML/` from the original source data. This is reproducibility infrastructure, not just ingestion notes.

The XML schema is defined by [QC/validation/xml_template.xsd](QC/validation/xml_template.xsd) (migrated from DTD in Phase 4.5; [QC/validation/xml_template.dtd](QC/validation/xml_template.dtd) is retained on disk as a fallback only). The structure is:

```
TEXT (id, citation, BibTeX_citation, copyright, xml:lang, [source, audio, glottocode, dialect])
└── S (id)                                                ← sentence tier; usually at least "original" and "standard" FORMs
    ├── FORM* (kindOf="original"|"standard"|"alternate")
    ├── PHON* (kindOf="original"|"standard")
    ├── TRANSL* (xml:lang, [kindOf, ver])
    ├── AUDIO? (start, end, file, url)
    └── W* (id, [class, sclass])                          ← word tier (only when corpus is word-segmented)
        ├── FORM* (kindOf)
        ├── PHON* (kindOf)
        ├── TRANSL* (xml:lang, [kindOf, ver])
        ├── AUDIO?
        └── M* (id, [class, sclass])                      ← morpheme tier
            ├── FORM* (kindOf)
            ├── PHON* (kindOf)
            ├── TRANSL*
            └── AUDIO?
```

Per the XSD (via `xs:choice maxOccurs="unbounded"`), sibling order of FORM/PHON/TRANSL/AUDIO/W within S — and FORM/PHON/TRANSL/AUDIO/M within W — is **not enforced**. The diagram shows a typical order, not a required one. (Prior to 2026-06-01 the XSD forced W to the end of S and M to the end of W; this was relaxed because AUDIO needs to be positionable anywhere within S and W, and XSD 1.0 can't express "AUDIO flexible, W/M trailing" without UPA violations. W/M-at-end is now a soft documentation convention.)

The `kindOf="original"` vs `kindOf="standard"` distinction is **critical** and not just cosmetic:
- **`original`**: the text as it appeared in the original source (book, website, etc.), possibly after minor normalization of punctuation and HTML escape codes. Preserves the source's orthographic choices.
- **`standard`**: the same content transliterated into FormosanBank's single common standard orthography. This exists because Formosan language orthographies are not highly standardized in the wild — different sources spell the same word different ways. The `standard` tier is the project's attempt to put everything in a single comparable form.

QC scripts that compare across corpora or compute orthographic statistics generally want `--kindOf standard`. Anything claiming to represent the source faithfully should use `--kindOf original`.

Two conventions that most QC code assumes:
1. **Two sentence-tier `FORM` elements** (original and standard). If a corpus only has one, create the standard tier with `python QC/utilities/standardize.py --copy --corpora_path <path>` *before* running punctuation/orthography checks. `--copy` does not normalize spelling — it just duplicates the original so QC scripts have a consistent tier to inspect; actual transliteration requires a TSV mapping.
2. **`--kindOf standard`** is the default for orthography extraction; legacy token counting uses the first sentence-level `FORM`.

`xml:lang` uses ISO 639-3 codes (validated against [QC/validation/iso-639-3.txt](QC/validation/iso-639-3.txt)). Dialect labels come from the `dialect` attribute; the canonical list is in [dialects.csv](dialects.csv).

## QC script conventions

Most validation/extraction scripts share a `search_by` positional with three modes:
- `by_language --language <Name> --corpora_path <path>`
- `by_corpus --corpus <Name> --corpora_path <path>`
- `by_path --path <file-or-dir>`

When in doubt, `by_path` against a single corpus's `XML/` directory is the safest target. Many scripts accept `--verbose` and `--log_dir <path>` so logs don't get scattered next to scripts or inside corpora.

The full pipeline is documented in [QC/README.md](QC/README.md). The typical order is:
1. `QC/validation/validate_xml.py` (XSD conformance)
2. `QC/utilities/standardize.py --copy` (only if standard tier is missing)
3. `QC/validation/validate_text.py` (B9.4 consolidation of `validate_punct.py` + `non_ascii_counts.py`)
4. `QC/orthography/orthography_extract.py --kindOf standard --by_dialect true`
5. `QC/validation/validate_orthography.py` and `validate_vocabulary.py` against [QC/validation/reference/](QC/validation/reference/) (per-language reference orthographies and vocabularies)
6. `QC/validation/validate_glosses.py` only for corpora with `W`/`M` segmentation

`clean_xml.py` modify XML in place — diff before committing.

## Corpus metrics and token deltas (CI-coupled)

[QC/corpus_metrics.py](QC/corpus_metrics.py) and [QC/count_tokens.py](QC/count_tokens.py) feed two GitHub Actions:

- **[.github/workflows/corpus-metrics.yaml](.github/workflows/corpus-metrics.yaml)** runs on push to `main` and auto-commits [statistics/corpus_size_history.csv](statistics/corpus_size_history.csv) and [statistics/corpus_size_over_time.png](statistics/corpus_size_over_time.png) back to the repo. **Do not hand-edit those two files** — let the workflow regenerate them. Full JSON/Markdown/plot output is a 30-day Actions artifact, not committed.
- **[.github/workflows/token-comparison.yaml](.github/workflows/token-comparison.yaml)** runs on PRs and pushes, comparing token counts against the PR base or previous push.

For local runs of `corpus_metrics.py --history`, pass `--history-cache statistics/corpus_size_history.csv` to reuse the cache — otherwise a full first-parent walk of XML-changing commits will take a long time.

## Conventions worth preserving

- Per-corpus logs land in `logs/` subdirs that are gitignored; prefer `--log_dir`/`--output_dir` flags to keep output out of the tree entirely.
- `Orthographies/` holds reference orthography PDFs and tables (e.g. [Orthographies/Ortho113.pdf](Orthographies/Ortho113.pdf), [Orthographies/ConversionTables/](Orthographies/ConversionTables/)). `QC/validation/reference/<Language>/` is what the validators actually consume — keep them in sync if you add a language.
- When **porting** a corpus from its dev repo into `Corpora/`, move everything necessary for reproducing the XMLs to the `<CorpusName>/CodeAndDocs` folder and explain in the `README.md` how to reproduce. Include `download_audio_data.sh` only if the corpus has audio. (Reminder: don't develop new corpora directly here — see "Development workflow" above.)
