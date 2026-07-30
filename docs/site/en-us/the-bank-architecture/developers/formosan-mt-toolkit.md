---
icon: language
---

# Formosan MT Toolkit

The Formosan MT Toolkit turns FormosanBank XML into reproducible machine-translation corpora and NLLB-200 experiments. It is a derived-data and modeling repository, not a separate source corpus.

The implementation is maintained in the private `FormosanBank/Formosan-MT-Toolkit` repository. The workflow below reflects its current `main` branch; repository access requires authorization from the FormosanBank organization.

### Current Production Workflow

Corpus pipeline v2 is the first supported release path. It:

```text
FormosanBank XML
  -> immutable source repository and commit inventory
  -> pinned FormosanBank QC
  -> standard-tier parallel-pair extraction
  -> conservative cleaning and rejection logging
  -> English and Traditional Chinese aggregates
  -> validated DeepL pivot completion
  -> document- and group-aware in_domain_hard split
  -> independent validation and TAME-MT exposure audit
  -> checksummed training bundle
  -> SPM8k NLLB setup
  -> four directional training and evaluation runs
```

The July 2026 v1 manifests remain in `formosan_mt_experiments/manifests/` as historical experiment records. Their corpora are not current v2 training inputs.

### Repository Layout

* `build_corpora.sh`: Stable wrapper for the end-to-end corpus builder.
* `scripts/local/`: Source acquisition, QC, XML extraction, filtering, pivoting, aggregation, and orchestration.
* `formosan_mt_experiments/`: Current splitting, validation, SPM8k setup, training, evaluation, and Slurm tooling.
* `corpus_builds/<name>/`: Ignored, self-contained generated builds.
* `protected_corpora/`: Paid-pivot snapshots and tracked checksums. This is retained for protection and provenance, not used as the current build namespace.

There is no current top-level release of 30 pairwise CSV files. Intermediate `processed_corpora/` directories and final training files live inside named, ignored builds under `corpus_builds/`.

### Building Corpora

The normal release procedure creates separate public and private/all-repository variants, adds cached or newly generated English-Chinese pivots, and excludes the exact Taiwan Bible Society repository:

```bash
./build_corpora.sh --build-public-private --with-pivot --exclude-bible
```

The active orchestrator is `scripts/local/build_mt_corpus.py`. Named builds do not overwrite one another. Each build records the exact repository commits and blobs used, the pinned QC revision, row-level provenance, rejected rows, pivot outcomes, split decisions, validation reports, exposure audits, configuration, and checksums.

The builder requires a clean checkout and stops when acquisition, parsing, QC, row conservation, pivot completion, split validation, exposure auditing, or provenance packaging is incomplete.

DeepL-generated targets are transactional. Successful translations are cached with provenance. Provider errors, missing cache entries, exhausted quota, or deferred requests prevent final outputs from being promoted. Responses that fail script, identity, markup, or fertility checks are excluded and recorded in a quarantine ledger.

### Model-Facing Corpora

The supported model-facing files are:

```text
corpus_builds/<name>/pivot_corpora_final/big_corpus_en_in_domain_hard.csv
corpus_builds/<name>/pivot_corpora_final/big_corpus_zh_in_domain_hard.csv
```

The split contract includes:

* source text extracted from `FORM kindOf="standard"`
* raw source, cleaned text, XML locator, source commit, QC commit, tier origin, and hashes retained for each row
* XML lexemes and morphemes routed to training only
* at least 7.5% test and 2.5% validation per language
* DeepL-generated rows kept in training, with human references required for evaluation
* source documents held out where enough eligible documents exist
* exact and near-duplicate leakage checks across split boundaries
* exact TAME-MT source, target, pair, and high-similarity exposure required to be zero
* connected one-to-many and many-to-one groups kept in one split

Each completed build includes `mt_build_manifest.json` and a portable `pivot_corpora_final/provenance/` bundle.

### Machine Translation Experiments

The current experiment stack lives in `formosan_mt_experiments/`. It validates the English and Chinese corpora, creates or reuses the pinned train-only SPM8k tokenizer and NLLB base, then trains and evaluates four unidirectional models per corpus variant:

* `f2en`: Formosan to English
* `en2f`: English to Formosan
* `f2zh`: Formosan to Traditional Chinese
* `zh2f`: Traditional Chinese to Formosan

Generated corpora, caches, tokenizer artifacts, model checkpoints, predictions, reports, and Slurm logs remain in ignored output or cluster storage. Source code, small manifests, checksums, and historical records are the items retained in Git.

### Further Documentation

For authorized contributors, the toolkit's `README.md` is the current operational reference. `docs/ARCHITECTURE.md` describes component ownership, `docs/NO_BIBLE_CORPUS_REBUILD.md` gives the release procedure, and `docs/CURRENT_EXPERIMENT.md` documents the superseded v1 flight.

### Citation

If you use a derived corpus or model, cite FormosanBank and the underlying source corpora. For the FormosanMT corpus and experiments, also cite:

* Scheppat, H., Hartshorne, J., Leddy, D., Le Ferrand, E., & Prudhommeaux, E. (2025). [Integrating diverse corpora for training an endangered language machine translation system](https://aclanthology.org/2025.computel-main.19/). In _Proceedings of the Eight Workshop on the Use of Computational Methods in the Study of Endangered Languages (ComputEL-8)_, 162–169.
