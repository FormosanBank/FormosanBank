---
icon: broom
---

# clean_audio.py

> Removes broken `<AUDIO>` elements (listed in `broken_audio.csv`) from their XML files, and optionally deletes the audio files from disk — dry-run by default.

## What it's for

`clean_audio.py` is the cleanup half of the audio-validation loop. [validate_audio.py](validate-audio.md) inspects a corpus's `<AUDIO>` references and writes a `broken_audio.csv` of entries that are missing, unreadable, or otherwise unusable. This script consumes that CSV and surgically removes each listed `<AUDIO>` element from its containing XML file, so the published corpus no longer points at audio that does not work.

It replaces the legacy `remove_non_working_audio.py`, which hardcoded ePark's `Final_audio`/`Final_XML` paths, had no CLI, and silently failed to delete audio files on disk.

## How it works

The script reads `--broken_csv` (expected columns: `xml_file`, `audio_file`, `kind`; extra columns are preserved). Rows are grouped by `xml_file` so each XML is opened at most once. The `xml_file` column is trusted as an absolute path and used directly.

For each XML file, it parses with `lxml`, collects every `<AUDIO>` element whose `file` attribute matches one of the broken `audio_file` names for that file, and removes those elements from their parents. The tree is then written back with `tree.write(..., encoding="utf-8", xml_declaration=True)`. Any target audio filename that was *not* found in the XML is reported as a warning (so an operator can investigate) rather than silently ignored.

If `--also-delete-files` is set, the script searches recursively under `<corpus_path>/Audio/` (via `rglob`, because corpora often nest by sub-corpus/language) for each broken filename and deletes every match. Missing files and `OSError`s are reported as warnings.

The expected layout (per the B9.2 plan) is canonical XML under `<corpus_path>/XML/` and audio under `<corpus_path>/Audio/`.

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`. Always do the dry-run first, then re-run with `--apply`:

```bash
# 1. Dry-run (default): print what would be removed, change nothing
python QC/cleaning/clean_audio.py \
    --corpus_path Corpora/ePark \
    --broken_csv  logs/broken_audio.csv

# 2. Apply: remove the <AUDIO> elements from the XML
python QC/cleaning/clean_audio.py \
    --corpus_path Corpora/ePark \
    --broken_csv  logs/broken_audio.csv \
    --apply

# 3. Apply AND delete the audio files from <corpus_path>/Audio/
python QC/cleaning/clean_audio.py \
    --corpus_path Corpora/ePark \
    --broken_csv  logs/broken_audio.csv \
    --apply --also-delete-files
```

| Flag | Default | Purpose |
|------|---------|---------|
| `--corpus_path` | *(required)* | Corpus root containing `XML/` and `Audio/`. Used to locate audio files for `--also-delete-files`. |
| `--broken_csv` | *(required)* | Path to `broken_audio.csv` from [validate_audio.py](validate-audio.md). |
| `--dry-run` | **on** | Print intended changes without modifying anything. Mutually exclusive with `--apply`. |
| `--apply` | off | Actually modify XML (and, with the next flag, disk). |
| `--also-delete-files` | `False` | Also delete each broken audio file from under `<corpus_path>/Audio/` (only takes effect with `--apply`). |

An empty `broken_audio.csv` (header only) is a no-op. A missing CSV exits with code 2.

## Output & side effects

- **Modifies XML in place** — but only with `--apply`. **Dry-run is the default**; without `--apply` nothing is written, the script just prints the planned removals (`[DRY-RUN] re-run with --apply to make changes.`).
- `--apply` reparses and rewrites each affected XML, removing the matched `<AUDIO>` elements.
- `--also-delete-files` (with `--apply`) **permanently deletes audio files from disk** under `<corpus_path>/Audio/`. This is irreversible — be sure the `broken_audio.csv` is correct first.
- Warns on broken targets not found in the XML, and on audio files not found / undeletable.
- **Always `git diff` before committing** the XML changes.

## When to run it

Run after [validate_audio.py](validate-audio.md) has produced a `broken_audio.csv` and you've reviewed it. It belongs in the audio-QC loop, typically when auditing or maintaining a corpus that has audio. Prerequisite: a current `broken_audio.csv`; the `<AUDIO>` elements and the on-disk audio layout (`XML/` + `Audio/`) must match the validator's assumptions.

## Related

- [validate_audio.py](validate-audio.md) — produces the `broken_audio.csv` this script consumes
- [audio-quality-triage.py](audio-quality-triage.md)
- [audio_duration_stats](audio-duration-stats.md)
- [QC Pipeline overview](README.md)
- [Running an Audit](../running-an-audit.md)
