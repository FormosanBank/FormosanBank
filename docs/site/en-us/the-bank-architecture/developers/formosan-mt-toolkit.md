---
icon: language
---

# Formosan MT Toolkit

The [Formosan MT Toolkit](https://github.com/FormosanBank/Formosan-MT-Toolkit) builds Formosan-English and Formosan-Traditional Chinese corpora from FormosanBank XML. It also provides reproducible training and evaluation for NLLB-200 and MADLAD-400 3B.

## Build a public corpus

```bash
git clone https://github.com/FormosanBank/Formosan-MT-Toolkit.git
cd Formosan-MT-Toolkit
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Build from public XML without paid pivot translation:

```bash
./build_corpora.sh \
  --corpus-name public_no_bible \
  --public \
  --exclude-bible
```

Add validated English-Chinese pivot translations with DeepL:

```bash
./build_corpora.sh \
  --corpus-name public_no_bible \
  --public \
  --with-pivot \
  --exclude-bible
```

A GitHub token is optional for public data. DeepL keys are needed only for new pivot translations, and completed translations are cached for later builds. Put credentials in the ignored `.env` file.

## Outputs

Final model-facing corpora are written to:

```text
corpus_builds/public_no_bible/pivot_corpora_final/
  big_corpus_en_in_domain_hard.csv
  big_corpus_zh_in_domain_hard.csv
  provenance/
```

Each build is isolated by corpus name and includes source revisions, cleaning decisions, rejected rows, pivot status, split diagnostics, TAME-MT exposure reports, and checksums.

## Data quality

The v3 pipeline:

* preserves nonempty XML `FORM kindOf="standard"` tiers and derives model text from a separate, versioned standardization;
* keeps lexemes, morphemes, and synthetic translations in training only;
* reserves at least 7.5% test and 2.5% validation data per language;
* uses human sentence references for evaluation;
* blocks exact, punctuation-skeleton, one-edit, and high character n-gram leakage across train and evaluation splits;
* fails incomplete acquisition, pivoting, validation, provenance, or checksum gates.

## Training and models

The toolkit trains four directions: Formosan to English, English to Formosan, Formosan to Traditional Chinese, and Traditional Chinese to Formosan. The NLLB setup uses an 8k Formosan SentencePiece extension. MADLAD uses its native tokenizer with Formosan target and metadata tokens.

Current NLLB models are available on Hugging Face:

* [Formosan to English](https://huggingface.co/FormosanBank/nllb200-formosan-en-spm8k)
* [English to Formosan](https://huggingface.co/FormosanBank/nllb200-en-formosan-spm8k)
* [Formosan to Traditional Chinese](https://huggingface.co/FormosanBank/nllb200-formosan-zh-spm8k)
* [Traditional Chinese to Formosan](https://huggingface.co/FormosanBank/nllb200-zh-formosan-spm8k)

See the toolkit [README](https://github.com/FormosanBank/Formosan-MT-Toolkit#readme) for cache-only rebuilds, configuration, cluster training, and development checks.

## Citation

If you use a generated corpus or model, cite FormosanBank, the source corpora, and:

* Scheppat, H., Hartshorne, J., Leddy, D., Le Ferrand, E., & Prudhommeaux, E. (2025). [Integrating diverse corpora for training an endangered language machine translation system](https://aclanthology.org/2025.computel-main.19/). In _Proceedings of the Eight Workshop on the Use of Computational Methods in the Study of Endangered Languages (ComputEL-8)_, 162–169.
