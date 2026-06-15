---
icon: circle-check
---

# validate_audio.py

> Always-on, lightweight broken-audio check that walks a corpus's XML plus its audio directory and reports missing, unloadable, silent, and invalid-range audio (V100–V103), with a SOFT words/sec sanity signal (V105).

## What it's for

Corpora that carry audio reference `*.wav`/`*.mp3` files from their `<AUDIO>` elements. This validator confirms those references actually resolve to decodable, non-empty, sensibly-clipped audio, and — optionally — that the clips aren't end-to-end silence. It produces a single `broken_audio.csv` with a `kind` column that downstream cleanup ([clean_audio.py](clean-audio.md)) consumes to act on the breakages.

It is built on the Finding framework (`QC/validation/_finding.py`): broken-audio classes are HARD findings and fail the run; the words/sec range check is a SOFT signal that warns but never fails.

## How it works

It collects two kinds of audio references from the XML:

- **Sentence/word level** — `<S>` and `<W>` elements that have a child `<AUDIO @file>` and a `FORM[@kindOf='original']`. The original-tier FORM text (collected via `itertext()`, so trailing text after inline children like `<UNCLEAR/>` is counted) is used for the words/sec check.
- **TEXT level** — `<AUDIO @file>` children of the root `TEXT`. These get existence/unloadable/silence checks but no words/sec check.

Only files ending in `.mp3`, `.wav`, `.flac`, `.ogg`, `.m4a` are considered. Each referenced filename is resolved against `--path` (the audio root) by mirroring the XML's relative directory, then falling back to dropping the leading path component, then the audio-root top level, then a recursive search for the filename.

Rule IDs (each broken-audio class is a HARD finding, written to `broken_audio.csv` with the matching `kind`):

| Rule | kind | Meaning |
|---|---|---|
| `V100` | `missing` | File referenced by `<AUDIO @file>` could not be resolved/found. |
| `V101` | `unloadable` | File present but mutagen (MP3) / `wave` (WAV) can't decode it (or it has zero frames/framerate). |
| `V102` | `silent` | Appears silent — only checked when `--check_silence` is passed. |
| `V103` | `invalid_range` | `AUDIO @start >= @end` (both parsed as floats). |
| `V105` | — (SOFT) | words/sec or chars/sec outside the expected range (written to `audio_duration_issues.csv`). |

Per file, checks run in order: invalid-range and missing are independent; for resolved files, `unloadable` short-circuits (a broken file is not further checked), otherwise `silent` (if enabled) and then the SOFT words/sec check run. `V104` (declared-vs-actual duration) is reserved in the module docstring but not currently emitted — it is "absorbed by V105."

**Silence detection** (`--check_silence` only): WAV files are judged by RMS amplitude below a threshold; MP3 files are probed with `ffmpeg`'s `silencedetect` filter and called silent when ≥95% of the duration is reported as silence. If the probe can't run, the result is `None` and the file is not flagged silent.

**Words/sec SOFT range** (`V105`): for sentence/word audio with non-empty stripped FORM text and positive duration, it flags when `words_per_sec < 0.1` **or** `chars_per_sec > 17` **or** (`word_count < 5` and `duration > 10`) **or** (`word_count > 12` and `duration < 7`). FORMs with no transcribed text (e.g. only `<UNCLEAR/>`) are skipped to avoid a false "too slow" signal.

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`. Audio files are gitignored — pull them first (see [run_audio_downloads.sh](../porting-a-corpus.md)) or the check will report everything as `missing`. Unlike the other validators, this script takes explicit `--xml_path` and `--path` rather than a `search_by` positional.

```bash
# Basic broken-audio check for one corpus.
python QC/validation/validate_audio.py \
    --xml_path Corpora/ePark/XML \
    --path Corpora/ePark/Audio \
    --log_dir logs/audio_ePark

# Also run silence detection (WAV RMS + MP3 ffprobe silencedetect).
python QC/validation/validate_audio.py \
    --xml_path Corpora/ePark/XML \
    --path Corpora/ePark/Audio \
    --check_silence \
    --log_dir logs/audio_ePark
```

| Flag | Required | Default | Meaning |
|---|---|---|---|
| `--xml_path` | yes | — | Root dir of the corpus's XML. |
| `--path` | yes | — | Root dir of the corpus's audio files (the `Audio/` dir). |
| `--check_silence` | no | off | Enable silence detection (WAV via RMS, MP3 via ffprobe). |
| `--log_dir` | no | `./logs/` | Output dir for `broken_audio.csv` and `audio_duration_issues.csv`. |
| `--no-exit-on-hard` | no | off | Always exit 0 even with HARD findings (back-compat). |

## Output & exit codes

Two CSVs are written under `--log_dir`:

- **`broken_audio.csv`** — columns `xml_file, audio_file, kind, rule_id, message`; one row per HARD finding (`kind` ∈ `missing`/`unloadable`/`silent`/`invalid_range`). This is the file [clean_audio.py](clean-audio.md) consumes.
- **`audio_duration_issues.csv`** — columns `xml_file, audio_file, words_per_sec, chars_per_sec`; the SOFT `V105` rows.

A compact per-rule summary (HARD then SOFT) prints to stderr, mirroring the other validators. Legacy CSVs (`non_working_audio.csv`, `missing_audio.csv`, `silent_audio.csv`) are no longer written — `broken_audio.csv` with its `kind` column subsumes them.

Exit code: **1** if any HARD finding (V100–V103) is present, else **0**. SOFT `V105` findings warn but never fail. Pass `--no-exit-on-hard` to force exit 0 regardless.

## When to run it

Run it after the XML validates and after the corpus's audio has been downloaded locally, as part of QC for any audio-bearing corpus — both during a [Running an Audit](../running-an-audit.md) pass and when [Porting a Corpus In](../porting-a-corpus.md). Feed the resulting `broken_audio.csv` to [clean_audio.py](clean-audio.md) to strip or repair the broken references. `--check_silence` requires `ffmpeg`/`ffprobe` on `PATH` for MP3s.

## Related

- [clean_audio.py](clean-audio.md) — consumes `broken_audio.csv` to remove/repair broken audio references.
- [audio_quality_triage](audio-quality-triage.md) — deeper, human-in-the-loop audio review.
- [audio_duration_stats](audio-duration-stats.md) — duration statistics for reporting.
- [Porting a Corpus In](../porting-a-corpus.md)
- [QC Pipeline overview](README.md)
