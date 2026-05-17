---
icon: language
---

# Formosan MT Toolkit

The Formosan MT Toolkit is the repository used to turn FormosanBank XML into machine-translation corpora and experiments. It is not a separate source corpus. Instead, it is a derived-data and modeling repository built on top of FormosanBank.

The repository is available here: [FormosanBank/Formosan-MT-Toolkit](https://github.com/FormosanBank/Formosan-MT-Toolkit).

### What the Toolkit Contains

The released corpus files live in `processed_corpora/`. The current release contains 30 processed pairwise corpora: 15 Formosan-English corpora and 15 Formosan-Traditional Chinese corpora. These files are the training-ready CSVs used by the FormosanMT work.

Each processed CSV keeps the Formosan text, the target translation, and metadata needed for downstream experiments:

* `source`: the original FormosanBank source file or text.
* `kindOf`: the translation type or origin, when known.
* `dialect`: the Formosan dialect label.
* `row_type`: whether the row is a sentence-level pair or a lexical entry.
* `split`: the released train, validate, or test split.
* `group_id`: the shared grouping used to reduce train/evaluation leakage.

Lexical rows are routed to training only. Sentence splits are assigned with shared source or target strings in mind, which helps avoid evaluating on examples that are nearly duplicated in training.

### Rebuilding Corpora from FormosanBank

The main corpus pipeline is:

```text
FormosanBank XML -> fetch_xml.py -> clean_xml.py -> make_corpus.py -> filter_split_corpus.py -> processed CSV
```

The pipeline downloads XML from FormosanBank, runs the standard XML cleaning utilities, extracts parallel pairs, filters noisy rows, labels lexical entries and sentence pairs, deduplicates examples, and writes the released CSV format.

To rebuild all released corpora:

```bash
./build_corpora.sh
```

To rebuild a single language pair, run the local scripts in sequence. For example, the Amis-Chinese pipeline fetches Amis XML, cleans it, extracts Chinese translations, then filters and splits the result.

### Machine Translation Experiments

The repository also contains the NLLB and OpenNMT experiment code used for FormosanMT. The older scripts under `scripts/mt/` support bilingual and multilingual NLLB-200 runs, multilingual tokenizer setup, evaluation, and OpenNMT baselines.

The newer experiment stack lives in `formosan_mt_experiments/`. It adds leakage-resistant split generation, tiered evaluation sets, SentencePiece tokenizer sweeps, directional NLLB training, denoising autoencoder pre-adaptation, LoRA experiments, evaluation reports, and Andromeda Slurm templates.

The headline workflow uses tiered splits such as:

* `lexical`: lexeme and template evaluation.
* `in_domain_hard`: the main benchmark.
* `hard_global`: a harder domain-transfer stress test.

Generated split files, tokenizer sweeps, model checkpoints, prediction files, and reports should stay in ignored output directories such as `formosan_mt_experiments/data/`, `formosan_mt_experiments/reports/`, or cluster scratch space.

### Pivot Corpora

The toolkit can also build DeepL pivot corpora, which add synthetic English or Traditional Chinese targets where only one target language is available. These outputs are expensive generated artifacts and are not ordinary source data.

The canonical working location is:

```text
pivot_corpora_final/
```

Protected checksum copies and manifests live under:

```text
protected_corpora/deepl_pivots/
```

Before copying or using the protected pivot data, verify the checksums:

```bash
cd protected_corpora/deepl_pivots
shasum -a 256 -c SHA256SUMS
```

Do not commit generated model artifacts, DeepL cache payloads, Slurm logs, prediction dumps, or regenerated pivot CSVs. Keep source scripts, configuration files, small manifests, checksums, and released processed corpora in git.

### Citation

If you use the processed corpora or models derived from them, cite FormosanBank and the underlying corpora. For the FormosanMT corpus and machine translation experiments, also cite:

* Scheppat, H., Le Ferrand, É., Hartshorne, J., & Prud’hommeaux, E. (2025). [Integrating diverse corpora for training endangered language machine translation systems](https://aclanthology.org/2025.computel-main.19/). In _Proceedings of the Eighth Workshop on the Use of Computational Methods in the Study of Endangered Languages (ComputEL-8)_.
