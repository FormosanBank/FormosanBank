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

## Validation pipeline (staged)

The validator suite is a **staged pipeline** of separate executables that share a Finding/Severity framework but are run independently. XML format must pass before later stages produce meaningful output.

| Stage | Validator | Rule module | What it checks |
|---|---|---|---|
| 1 | `QC/validation/validate_xml.py` | `QC/validation/rules/hard.py` | XML format: schema, IDs, attributes, structural validity. |
| 2 | `QC/validation/validate_glosses.py` | `QC/validation/rules/gloss.py` | Gloss artifacts: V060–V065. SOFT rules emit warnings; HARD rules cause nonzero exit. |
| 2 | `QC/validation/validate_punct.py` | (legacy script) | Punctuation/processing artifacts. |

Gloss validation can be **run on any corpus**, including unsegmented ones — rules naturally no-op when iterating empty `W`/`M` lists. SOFT rules (V060/V061/V065) are review-not-gate: they surface candidate cleanups without blocking the build.

## Basic Flow

Run XML validation first:

```bash
python QC/validation/validate_xml.py by_path \
  --path /path/to/Final_XML
```

If the corpus has audio, validate audio next. `validate_audio.py` is an
always-on, lightweight check (no ML deps) that produces a single
`broken_audio.csv` with a `kind` column (`missing`, `unloadable`,
`silent`, `invalid_range`). HARD findings (V100-V103) cause non-zero
exit; SOFT findings (V104-V105, words-per-sec out of range) warn but
don't fail.

```bash
python QC/validation/validate_audio.py \
  --xml_path /path/to/corpus/XML \
  --path /path/to/corpus/Audio \
  --log_dir /path/to/qc-output/logs \
  [--check_silence]
```

Silence detection covers WAV (via RMS) and MP3 (via `ffprobe -af
silencedetect`). The MP3 path requires `ffmpeg`/`ffprobe` on `$PATH`.
Pass `--check_silence` to enable; otherwise silence is skipped to keep
the check fast for large corpora.

To remove broken entries afterward, run `clean_audio.py` against the
generated `broken_audio.csv`:

```bash
python QC/cleaning/clean_audio.py \
  --corpus_path /path/to/corpus \
  --broken_csv  /path/to/qc-output/logs/broken_audio.csv \
  --apply              # default is --dry-run
  [--also-delete-files]
```

`--apply` modifies the XML in place by removing each listed `<AUDIO>`
element. `--also-delete-files` also deletes the matching audio file
from `<corpus>/Audio/`. Default is `--dry-run`: print the intended
changes, modify nothing.

Run text-content validation after `FORM kindOf="standard"` exists:

```bash
python QC/validation/validate_text.py by_path \
  --path /path/to/Final_XML
```

`validate_text.py` (added in B9.4) consolidates the legacy
`validate_punct.py` and `non_ascii_counts.py` scripts under one
Finding-framework-aware validator. It checks the *textual content* of
`<FORM>` and `<TRANSL>`: smart quotes, imbalanced parentheses,
repeated punctuation, consecutive dashes, multiple whitespace,
mismatched smart quotes, non-ASCII characters (excluding CJK),
null-symbol propagation between W/M/S tiers, parens/slashes in W/M
FORM (HARD), parens/slashes anywhere (SOFT), and `=` leftovers in the
S-level standard tier. HARD findings exit 1; SOFT findings go to a
CSV artifact (`--soft-csv`) for review.

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

Run gloss validation on any corpus; rules naturally no-op on unsegmented ones. Six rules are registered (see `QC/validation/rules/gloss.py`):

| Rule | Severity | What it flags |
|---|---|---|
| V060 | SOFT | `<W>` count does not match the whitespace-delimited word count in S-level `FORM[@kindOf="original"]`. |
| V061 | SOFT | `<M>` count does not match the morpheme count implied by W's FORM segmentation markers (`-`, `=`, `<...>`). |
| V062 | HARD | `<M>` with infix-shaped FORM (`-X-`) requires an angle-bracket gloss (`<X>`) in the parent W's TRANSL. |
| V063 | HARD | When the S-level FORM has > 3 segmentation markers, the W children's FORMs must collectively retain at least N/2 markers in each tier. |
| V064 | HARD | Every `<M>` element must have at least one `<TRANSL>` child. |
| V065 | SOFT | Every `<W>` element should have at least one `<TRANSL>` child. |

Exit code: 1 if any HARD finding (V062/V063/V064); 0 otherwise. SOFT findings (V060/V061/V065) emit warnings to stderr but do not fail the run.

```bash
# Validate one XML file
python QC/validation/validate_glosses.py by_path --path /path/to/file.xml \
  --output_dir /path/to/qc-output

# Validate a directory tree
python QC/validation/validate_glosses.py by_path --path /path/to/Final_XML \
  --check_morpho \
  --output_dir /path/to/qc-output

# Validate one corpus by name (walks its canonical XML/)
python QC/validation/validate_glosses.py by_corpus \
  --corpus ePark --corpora_path Corpora \
  --output_dir /path/to/qc-output

# Validate every file across all corpora whose root xml:lang matches
python QC/validation/validate_glosses.py by_language \
  --language ami --corpora_path Corpora \
  --output_dir /path/to/qc-output
```

For verse-level or sentence-only corpora with no `W`/`M` segmentation, V060–V065 either no-op (no W/M to iterate) or surface SOFT findings that should be treated as "not applicable". The two legacy CSV artifacts (`validation_results.csv` for V060, `validation_m_mismatches.csv` for V061) are preserved for backward compatibility with prior callers.

Detect duplicate `<S>` sentences within a corpus (within-file matches are HARD findings; cross-file matches in the same corpus are SOFT):

```bash
python QC/validation/validate_duplicate_sentences.py by_path \
  --path /path/to/Final_XML \
  --output /path/to/qc-output/duplicate_sentences.csv
```

The validator compares whitespace-normalized FORM text on the `kindOf="standard"` tier by default; pass `--tier original` to compare the source tier. Cross-corpus duplicate detection (e.g. "is this Glosbe sentence also in ePark?") is a separate tool: see `QC/utilities/find_duplicate_sentences.py`.

## Cleaning

`QC/cleaning/clean_xml.py` normalizes unicode and HTML entities in place.

`QC/cleaning/remove_duplicate_sentences.py` removes duplicate `<S>` elements detected by the validator above. **It modifies XML in place** — the default is `--dry-run`; pass `--apply` to actually mutate files. Within each duplicate group it deterministically keeps the first occurrence by `(file, S id)` sort order.

```bash
# Plan only (default; nothing is written):
python QC/cleaning/remove_duplicate_sentences.py by_path \
  --path /path/to/Final_XML

# After reviewing the dry-run plan, actually remove:
python QC/cleaning/remove_duplicate_sentences.py by_path \
  --path /path/to/Final_XML --apply

# Include cross-file duplicates within the corpus (default scope is file-only):
python QC/cleaning/remove_duplicate_sentences.py by_path \
  --path /path/to/Final_XML --scope corpus --apply
```

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

History mode samples first-parent commits where XML files under `Corpora/**/XML/` were added, deleted, or modified. It uses the full XML-changing history by default; pass `--max-history-commits N` to sample only the most recent `N` XML-changing commits.

For routine updates, reuse the existing history CSV so the script only applies XML-changing commits after the last recorded commit:

```bash
python QC/corpus_metrics.py Corpora \
  --output-dir corpus-metrics \
  --history \
  --history-cache statistics/corpus_size_history.csv
```

During history runs, `corpus_metrics.py` prints progress to stderr for the current corpus and each sampled commit, so long runs show `[current/total]` status instead of appearing hung. The GitHub workflow uploads the full `corpus-metrics/` directory as a 30-day Actions artifact; on pushes to `main`, only `statistics/corpus_size_history.csv` and `statistics/corpus_size_over_time.png` are committed back for the README graph.

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

## MT Data Prep: On-Demand Audio Quality Scoring

For corpora destined for machine translation training, run the
on-demand audio quality pipeline ported from Jacob Ye's
`Formosan-ILRDF_Dicts/data_validation/`. This is NOT part of the
always-on QC suite (it has heavy ML dependencies and takes hours).

**Heavy dependencies** (not in `requirements.txt`; see
`requirements-audio-mt.txt`): `torch`, `torchaudio`, `torchcodec`,
`allosaurus`, `Levenshtein`, `unidecode`.

```bash
pip install -r requirements-audio-mt.txt
```

The CTC pipeline also requires a sibling clone of Jacob's
`data_quality_eval` repo (for the `utils_CTC.get_trellis` /
`backtrack` helpers):

```bash
# clone next to FormosanBank so the default path resolves
cd "$(dirname "$(pwd)")"
git clone https://github.com/AI4CommSci/data_quality_eval
```

Stage 1 — score each `(audio, transcript)` pair on four mismatch metrics
(`ctc`, `wer`, `cer`, `pdm`). Resumable: re-running skips
sentence_ids already in `--out-csv`.

```bash
python QC/validation/validate_audio_quality.py \
  --corpus_path Corpora/ePark \
  --out-csv     Corpora/ePark/results/scores.csv \
  --metrics     all
```

Stage 2 — turn the raw scores into a worklist by rank-normalizing each
metric per-language and flagging the worst K%%. Output is
`suspect_audio.csv`, sorted worst-first.

```bash
python QC/validation/flag_audio_suspicious.py \
  --scores  Corpora/ePark/results/scores.csv \
  --out     Corpora/ePark/results/suspect_audio.csv \
  --worst-pct 5 --min-agreement 1
```

Stage 3 — interactive human triage of the worklist. Plays each clip,
prompts for a single-key verdict (`c`/`w`/`u`/`s`/`p`/`n`/`b`/`q`),
writes to `{Lang}_verdicts.csv`. Resumes from the first unverified
row on re-run.

```bash
python QC/utilities/audio_manual_verify.py \
  --suspicious Corpora/ePark/results/suspect_audio.csv \
  --verdicts   Corpora/ePark/results/Amis_verdicts.csv
```

NOTE: the off-the-shelf wav2vec2 BASE_960H model is English-trained,
so the absolute CTC/WER/CER values are meaningless — only the
*relative* ranking within a language matters. A Formosan-tuned ASR
model would turn this into absolute quality scoring; that's deferred.

## Interpreting Common Warnings

- `No reference orthographic info found`: the extracted language/dialect folder does not match a folder under `QC/validation/reference`. Normalize dialect labels before treating this as an orthography failure.
- Punctuation `non_ascii_characters`: this excludes Chinese characters, but it still flags diacritics, IPA, smart quotes, and other non-ASCII symbols. Review whether these are expected for the source.
- Vocabulary overlap warnings: these are useful for review, but they can be noisy when comparing texts from different genres, such as Bibles against dictionaries or narratives.
