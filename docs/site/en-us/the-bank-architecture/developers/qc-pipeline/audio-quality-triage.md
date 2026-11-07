---
icon: waveform-lines
---

# Audio-quality triage (MT data prep)

> An optional three-step chain that scores `(audio, transcript)` pairs, ranks the worst as suspects, and lets a human verify them by ear — for preparing ASR/MT training data.

## What it's for

This chain is **outside the core text-QC loop**. The validators under [Running an Audit](../running-an-audit.md) and [Porting a Corpus In](../porting-a-corpus.md) never invoke it. Its job is to find audio clips whose transcript probably doesn't match what was actually said — the kind of noise that hurts when a corpus is used to train ASR or machine-translation models. It is a port of Jacob Ye's `data_validation/` tooling from `Formosan-ILRDF_Dicts/` into FormosanBank.

The workflow is three scripts in sequence: **score** every pair on acoustic/phonetic metrics, **flag** the statistical outliers into a ranked worklist, then **manually verify** the flagged clips by listening. Only run this if you are curating audio for MT/ASR; it carries heavy ML dependencies and is not part of normal publication QC.

## When to run it

Optional and on demand, after a corpus's text has passed QC and its audio is available locally (pulled via `run_audio_downloads.sh`). Prerequisites for the scoring step are heavy: `torch`, `torchaudio`, `torchcodec`, `allosaurus`, `Levenshtein`, `unidecode` (install via `pip install -r requirements-audio-mt.txt`), plus a sibling clone of Jacob's `data_quality_eval/` repo at the same parent directory as FormosanBank for the CTC-alignment helpers (see `QC/README.md` for the exact clone command). The metrics use an off-the-shelf **English** wav2vec2 model, so absolute scores are meaningless — only the *relative ranking within a language* is signal. Run steps 2 and 3 after step 1 produces its scores CSV.

## Step 1 — validate_audio_quality.py (score)

### How it works

Walks `<corpus_path>/XML/` and, for each `<S>` that has both a `<FORM>` and an `<AUDIO file="…">`, resolves the audio under `<corpus_path>/Audio/` (recursive search as a last resort) and computes up to four mismatch metrics:

| Metric      | Direction       | What it measures                                                                 |
| ----------- | --------------- | ------------------------------------------------------------------------------- |
| `ctc_score` | higher = better | Mean per-frame posterior of a forced CTC alignment (wav2vec2 `BASE_960H`).       |
| `wer`       | lower = better  | Word-error-rate between transcript and a greedy CTC decode of the same emissions. |
| `cer`       | lower = better  | Character-error-rate, same comparison.                                           |
| `pdm_score` | higher = better | Levenshtein ratio between the orthographic transcript and an Allosaurus universal-phoneme transcription. |

Heavy deps are imported lazily, so `--help` works before install. The run is **resumable**: re-running with the same `--out-csv` skips any `sentence_id` already in the file.

### Usage

```bash
source .venv/bin/activate
python QC/validation/validate_audio_quality.py \
    --corpus_path Corpora/ePark/ \
    --metrics ctc,wer,cer \
    --out-csv Corpora/ePark/results/Amis_scores.csv
```

| Flag                 | Default                              | Meaning                                                     |
| -------------------- | ------------------------------------ | ----------------------------------------------------------- |
| `--corpus_path`      | **required**                         | Corpus root; contains `XML/` and `Audio/`.                  |
| `--out-csv`          | **required**                         | Output scores CSV (resumable across runs).                  |
| `--metrics`          | `all`                                | Comma-separated subset of `{ctc,wer,cer,pdm}`, or `all`.    |
| `--sample`           | `0`                                  | Random sample of N entries (`0` = all).                     |
| `--seed`             | `42`                                 | Seed for `--sample`.                                        |
| `--word-map`         | `None`                               | Optional pickle: `audio_url → headword`.                    |
| `--pdm-cache`        | `None`                               | Optional pickle cache of Allosaurus outputs (one per language). |
| `--data-quality-eval`| sibling `data_quality_eval/`         | Path to Jacob's `data_quality_eval` clone (CTC helpers).    |

### Output

Appends rows to the scores CSV with columns `lang, sentence_id, word, audio_path, transcript, asr_hypothesis, ctc_score, wer, cer, pdm_score` (the `pdm_score` column is omitted when `pdm` is not requested). Exit `2` on an invalid `--metrics` value.

## Step 2 — flag_audio_suspicious.py (rank)

### How it works

Reads the scores CSV and, **independently per language**, rank-normalizes each metric's distribution. An entry is flagged if it falls in the worst K% of any single metric (default 5%), unless `--min-agreement` requires several metrics to agree. Absolute cutoffs (`--ctc-max`, `--pdm-max`, `--wer-min`, `--cer-min`) override the percentile logic for that metric. Each flagged row gets:

```
suspicion = (100 - worst_pct_rank) + 10 * (n_triggers - 1)
```

so worse outliers and multi-metric agreement rank higher. Each suspect also emits a SOFT `V140` Finding so the rest of the QC suite has visibility.

### Usage

```bash
python QC/validation/flag_audio_suspicious.py \
    --scores Corpora/ePark/results/Amis_scores.csv \
    --out    Corpora/ePark/results/suspect_audio.csv
```

| Flag              | Default                       | Meaning                                                  |
| ----------------- | ----------------------------- | -------------------------------------------------------- |
| `--scores`        | **required**                  | Scores CSV from step 1.                                  |
| `--out`           | `suspect_audio.csv` beside scores | Output worklist CSV.                                 |
| `--worst-pct`     | `5.0`                         | Flag entries in the worst K% of any single metric.       |
| `--min-agreement` | `1`                           | Require this many metrics to agree.                      |
| `--ctc-max`       | `None`                        | Absolute cutoff: flag if `ctc_score <` this.             |
| `--pdm-max`       | `None`                        | Absolute cutoff: flag if `pdm_score <` this.             |
| `--wer-min`       | `None`                        | Absolute cutoff: flag if `wer >` this.                   |
| `--cer-min`       | `None`                        | Absolute cutoff: flag if `cer >` this.                   |
| `--limit`         | `0`                           | Cap the worklist size (`0` = no cap).                    |

### Output

Writes a `suspect_audio.csv` carrying the original columns plus `triggers, n_triggers, worst_pct_rank, suspicion`, sorted worst-first (an empty file if nothing is flagged). Per-metric medians print to stderr. Exit `2` if the scores file is missing.

## Step 3 — audio_manual_verify.py (verify by ear)

### How it works

An **interactive** terminal tool. For each row of `suspect_audio.csv` it plays the clip and prints the transcript, ASR hypothesis, scores, and triggers, then prompts for a verdict. It picks an audio player automatically (`ffplay`/`afplay`/`aplay`/`mpg123`/`mpv`) or you can override with `--player`. With `readchar` installed, controls are single-keypress (no Enter); otherwise it falls back to line input. Verdicts are written to a CSV; re-running **resumes from the first unverified row**.

Keys: `c` correct · `w` wrong · `u` unclear · `s` skip (advance, no verdict) · `p` replay · `n` add a free-text note · `b` back one entry · `q` quit and save.

### Usage

```bash
python QC/utilities/audio_manual_verify.py \
    --suspicious Corpora/ePark/results/suspect_audio.csv \
    --verdicts   Corpora/ePark/results/Amis_verdicts.csv \
    [--player afplay]
```

| Flag           | Default                              | Meaning                                              |
| -------------- | ------------------------------------ | ---------------------------------------------------- |
| `--suspicious` | **required**                         | `suspect_audio.csv` from step 2.                     |
| `--verdicts`   | `<suspicious stem>_verdicts.csv`     | Output verdicts CSV.                                 |
| `--player`     | auto-detect                          | Override the audio-player command.                   |
| `--auto-play`  | `yes`                                | Play audio automatically when an entry is shown (`yes`/`no`). |

### Output & side effects

Writes/updates the verdicts CSV (the suspect columns plus `verdict` and `notes`); written on every advance and again on quit, so progress is never lost. A correct/wrong/unclear tally prints on exit. Exit `2` if the suspicious file is missing.

## Related

- [validate_audio.py](validate-audio.md) — structural audio validation (part of core QC)
- [clean_audio.py](clean-audio.md)
- [Running an Audit](../running-an-audit.md)
- [QC Pipeline overview](README.md)
