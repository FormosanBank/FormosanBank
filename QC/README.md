# FormosanBank QC

This folder contains lightweight scripts for checking FormosanBank XML corpora. The scripts are intentionally modular: run the checks that match the corpus state instead of treating every warning as an automatic data error.

## Expected XML Tiers

Most validation scripts inspect the standardized sentence tier:

```xml
<S id="...">
    <FORM kindOf="original">...</FORM>
    <FORM kindOf="standard">...</FORM>
</S>
```

If a corpus only has one sentence-level `FORM`, create the standard tier first:

```bash
python QC/utilities/standardize.py \
  --copy \
  --corpora_path /path/to/corpus-or-Final_XML
```

`--copy` does not normalize spelling. It preserves the source text as `kindOf="original"` and creates `kindOf="standard"` as an exact copy so the QC scripts have a consistent tier to inspect.

To actually normalize orthography, provide a TSV mapping:

```bash
python QC/utilities/standardize.py \
  --corpora_path /path/to/corpus-or-Final_XML \
  --tsv_path /path/to/orthography-map.tsv \
  --target_column standard
```

The TSV must include an `original` column and a target column such as `standard` or a dialect name. Replacements are applied globally and sequentially with Python string replacement, so review the diff after running it.

## Basic Flow

Run XML validation first:

```bash
python QC/validation/validate_xml.py by_path \
  --path /path/to/Final_XML
```

Run punctuation validation after `FORM kindOf="standard"` exists:

```bash
python QC/validation/validate_punct.py by_path \
  --path /path/to/Final_XML
```

Extract orthographic information from the standard tier:

```bash
python QC/orthography/orthography_extract.py \
  --corpora_path /path/to/Final_XML \
  --corpus all \
  --language All \
  --kindOf standard \
  --by_dialect true \
  --output_dir /path/to/qc-output/extract_logs
```

Compare orthography and vocabulary against the reference data:

```bash
python QC/validation/validate_orthography.py \
  --o_info /path/to/qc-output/extract_logs \
  --reference QC/validation/reference

python QC/validation/validate_vocabulary.py \
  --o_info /path/to/qc-output/extract_logs \
  --reference QC/validation/reference
```

Run gloss validation only when the corpus is expected to contain word-level `W` elements, and morpheme validation only when `M` elements are expected:

```bash
python QC/validation/validate_glosses.py /path/to/Final_XML \
  --output_dir /path/to/qc-output

python QC/validation/validate_glosses.py /path/to/Final_XML \
  --check_morpho \
  --output_dir /path/to/qc-output
```

For verse-level or sentence-only corpora with no `W`/`M` segmentation, `validate_glosses.py` will report sentence/W mismatches. Treat those as "not applicable" unless word segmentation is required for that corpus.

## Corpus Metrics

Generate corpus-wide facts, figures, and plots from XML files under `Corpora/`:

```bash
python QC/corpus_metrics.py Corpora \
  --output-dir corpus-metrics \
  --history
```

The script writes:

- `corpus_metrics.json`
- `corpus_metrics.md`
- `corpus_language_tokens.png`
- `corpus_source_tokens.png`
- `corpus_benchmark_comparison.png`
- `corpus_size_history.csv` and `corpus_size_over_time.png` when `--history` is used

By default, token counts use the first direct sentence-level `FORM` in each `S`, matching the legacy token counter. Use `--form-kind standard`, `--form-kind original`, or `--form-kind auto` when a different sentence tier is needed.

History mode samples recent first-parent commits where `Corpora/**/*.xml` was added, deleted, or modified, plus the current `HEAD` when it is not already in that sample.

## Token Delta Regression

Generate the same language/dialect token JSON used by the token delta workflow:

```bash
mkdir -p token-count-artifacts
python QC/count_tokens.py Corpora > token-count-artifacts/current_token_count.json
```

Compare the current checkout against another ref, such as `origin/main`, by counting that ref from a temporary worktree:

```bash
mkdir -p token-count-artifacts
git worktree add --detach /tmp/formosanbank-token-base origin/main
python QC/count_tokens.py /tmp/formosanbank-token-base/Corpora > token-count-artifacts/base_token_count.json
git worktree remove --force /tmp/formosanbank-token-base

python QC/tokens_delta.py \
  token-count-artifacts/base_token_count.json \
  token-count-artifacts/current_token_count.json \
  token-count-artifacts/token_delta.json
```

Optional plots can be generated from inside the artifact directory:

```bash
cd token-count-artifacts
python ../QC/plot_deltas.py token_delta.json
python ../QC/plot_counts.py current_token_count.json 0
mv plot.png language_dialect_counts.png
python ../QC/plot_counts.py current_token_count.json 1
mv plot.png language_counts.png
cd ..
```

The GitHub workflow runs this comparison automatically for PRs against the PR base SHA and for pushes to `main` against the previous push SHA.

## Output Locations

Use explicit output directories when you do not want logs or CSVs written beside the scripts or inside the corpus:

```bash
python QC/validation/validate_xml.py by_path \
  --path /path/to/Final_XML \
  --verbose \
  --log_dir /path/to/qc-output/logs

python QC/validation/validate_punct.py by_path \
  --path /path/to/Final_XML \
  --verbose \
  --log_dir /path/to/qc-output/logs
```

`orthography_extract.py --output_dir` writes extracted `orthographic_info` files and plots to that directory.

`validate_glosses.py --output_dir` writes:

- `validation_results.csv`
- `validation_m_mismatches.csv`

## Interpreting Common Warnings

- `No reference orthographic info found`: the extracted language/dialect folder does not match a folder under `QC/validation/reference`. Normalize dialect labels before treating this as an orthography failure.
- Punctuation `non_ascii_characters`: this excludes Chinese characters, but it still flags diacritics, IPA, smart quotes, and other non-ASCII symbols. Review whether these are expected for the source.
- Vocabulary overlap warnings: these are useful for review, but they can be noisy when comparing texts from different genres, such as Bibles against dictionaries or narratives.
