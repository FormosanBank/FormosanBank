---
icon: robot
---

# Generated files

> Some files in the repository are written by CI. Hand-editing them wastes your change — the next push overwrites it — and can corrupt a longitudinal record that is expensive to rebuild.

## What it is

Everything in `statistics/` **except one file**:

| Path | Written by | Contents |
|---|---|---|
| `statistics/*_corpora_stats.csv` | `corpus-metrics` (CI) | Per-corpus counts, one CSV per corpus. Read by the documentation site at build time. |
| `statistics/language_history.csv` | `corpus-metrics` (CI) | Per corpus, language and dialect, one row set per XML-changing commit (`QC/language_history.py`). The site's growth figures. |
| `statistics/corpus_size_history.csv` | `corpus-metrics` (CI) | One row per XML-changing commit — the longitudinal growth record. |
| `statistics/corpus_*_over_time.png` | `corpus-metrics` (CI) | Four growth graphs (size, transcribed audio, Mandarin words, glossed words). |
| `statistics/audio_durations.csv` | **a human, on demand** | Audio seconds per `(corpus, language, dialect)`. **Not** CI-written. |

That last row is the trap. `audio_durations.csv` sits among generated files, looks generated, and is not — it is a source of truth that CI only ever **reads**.

One generated file lives outside `statistics/`, and it is the well-behaved case: [`QC/validation/RULES.md`](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/RULES.md), the validation-rule catalogue. A developer regenerates it with `python QC/validation/rules_catalogue.py`, and unlike everything above it is **enforced** — a test runs `--check`, so a stale catalogue is a red check rather than a silent overwrite. See [The rule catalogue](../qc-pipeline/rule-catalogue.md).

## Why it exists

Audio seconds cannot be recomputed in CI, because the audio is gitignored and the full download is roughly 105 GiB. So the seconds are computed once, by hand, and committed alongside the audio-file count they were computed against. CI fills the seconds columns from this file and compares that stored `count_at_compute` against the corpus's current XML audio count; when they diverge it emits a `STALE AUDIO` warning rather than a wrong number.

The history CSV has a different reason to be protected: it is **append-mostly and expensive to restate**. `corpus_metrics.py --history-extend` adds one row per XML-changing commit since the last cached row, so a multi-commit push doesn't leave gaps. Restating it in full (`--history-rebuild`) is a first-parent walk over git blobs that takes a long time.

{% hint style="info" %}
History rows written before 2026-06 used different counting rules (first `FORM`, all whitespace chunks). The discontinuity is known and accepted — do not try to "fix" old rows by hand.
{% endhint %}

## Who reads it

`QC/corpus_counts.py` is the single source of truth for the counting *rules* behind all of it: tokens come from sentence-level `FORM` only (standard tier, original fallback) and are whitespace chunks containing at least one letter or digit. `get_corpus_stats.py`, `corpus_metrics.py` and `count_tokens.py` all import it, which is why the numbers agree.

Downstream, the documentation site reads the per-corpus CSVs and `language_history.csv` every time it is built (see [Generated pages](generated-pages.md)); nothing copies the numbers anywhere.

## How it's enforced

Weakly, and that is worth knowing: **nothing blocks a hand edit.** The `corpus-metrics` workflow simply regenerates the files on the next push to `main`, auto-commits them as `github-actions[bot]`, and your edit disappears. The failure mode is silent and delayed rather than a red check.

For `audio_durations.csv` the signal is the `STALE AUDIO` warning in the `get_corpus_stats.py` output — also non-blocking.

## How to change it correctly

**For the CI-generated files: don't.** Change the XML, or change the counting rules in `QC/corpus_counts.py`, and let the workflow regenerate. If a number looks wrong, the bug is upstream of the CSV.

**For `audio_durations.csv`**, refresh it deliberately — it is the one file here you are *supposed* to update:

```bash
source .venv/bin/activate

# What is stale, and why.
python QC/utilities/get_corpus_stats.py --report-stale-audio

# Pull one corpus's audio from Hugging Face, recompute, delete the audio.
# (Corpus name is positional; --keep-audio retains the download.)
python QC/utilities/refresh_audio_stats.py NTU_Paiwan_ASR

# Or, when the audio is already local (positional path, or --all).
python QC/utilities/update_audio_stats.py Corpora/ePark
```

The `refresh-audio-stats` Claude skill walks through this. It is never part of CI or a normal merge — see [Audio duration stats](../qc-pipeline/audio-duration-stats.md).

**To rebuild history** (rarely — a counting-rule change that must apply retroactively), use `QC/corpus_metrics.py --history-rebuild` in XML mode with no `--stats-dir`, and expect it to be slow.
