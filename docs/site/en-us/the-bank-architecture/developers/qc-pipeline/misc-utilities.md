---
icon: screwdriver-wrench
---

# Miscellaneous utilities

> Occasional, one-off helpers for preparing and uploading audio: stamping durations onto `AUDIO` elements, organizing audio into per-XML subdirs, batching large file collections, and uploading a corpus's audio to Hugging Face.

## What it's for

These are not part of the routine QC pipeline. They are audio-wrangling helpers reached for during corpus preparation or a publish — usually run once per corpus, often in a corpus's dev repo before porting. Several still assume the dev-repo `Final_XML/` + `Final_audio/` layout rather than the published `XML/` + `Audio/` layout.

## When to run it

Run by hand, occasionally, from the repo root after `source .venv/bin/activate` (or from a dev repo). None of these are wired into CI.

## add_durations.py — stamp start/end onto AUDIO elements

**How:** for a corpus with segmented audio, walks each XML file, measures each referenced audio file's duration (WAV via `wave`, MP3 via `mutagen`), and sets `start="0"` / `end="<seconds>"` on the matching `AUDIO` element. An `AUDIO` element whose audio file has no measurable duration is **removed** from the XML. Expects the dev-repo `Final_XML/` ↔ `Final_audio/<xml_stem>/` layout. Note: this edits the duration *attributes inside the XML*, distinct from [`audio_durations.csv`](audio-duration-stats.md), which stores aggregate seconds for statistics.

**Usage:**

```bash
python QC/utilities/add_durations.py --path path/to/Final_XML
```

## group_audios.py — organize audio into per-XML subdirs

**How:** for each XML marked `audio="segmented"`, reads the `AUDIO` file names and moves the corresponding files from `Final_audio/` into a per-XML subfolder `Final_audio/<xml_stem>/`, so each XML's clips are grouped together (the layout `add_durations.py` expects).

**Usage:**

```bash
python QC/utilities/group_audios.py --path path/to/Final_XML
```

## organize_batches.py — batch large file collections

**How:** recursively scans a parent folder; any subfolder holding more than the batch size (default 10,000) is split, its files distributed into `batch_1/`, `batch_2/`, … subfolders. Useful for keeping audio directories under per-folder file-count limits (e.g. for Hugging Face uploads). Skips `.cache`/`.git` paths. The batch size is fixed at the default in code (no CLI flag).

**Usage:**

```bash
python QC/utilities/organize_batches.py --path path/to/audio
```

## upload_to_hf.py — upload a corpus's audio to Hugging Face

**How:** uploads a corpus's audio folder to a Hugging Face dataset repo via `hf upload-large-folder`. The target is recorded in `.hf_dataset.yaml` at the corpus root so later runs don't re-prompt; supports either a single dataset (`repo: org/name`) or per-subdir datasets (`repo_template: …{group}…` + `split_by: subdir`, e.g. one repo per language). If `.hf_dataset.yaml` is missing you're prompted to select or create a FormosanBank dataset. **Default is an incremental upload** (new/changed files only, never deletes); `--sync` additionally deletes remote files not present locally so the remote mirrors the local folder exactly. Requires the `hf` CLI and authentication (`hf auth login`).

**Usage:**

```bash
python QC/utilities/upload_to_hf.py --path Corpora/YutasWilang
python QC/utilities/upload_to_hf.py --path Corpora/YutasWilang --sync
python QC/utilities/upload_to_hf.py --path . --audio-dir Final_audio --dry-run
```

| Flag | Default | Purpose |
| --- | --- | --- |
| `--path` | `.` | Corpus root containing the audio folder. |
| `--audio-dir` | `Audio` (or YAML `audio_dir`) | Audio folder name under `--path`. |
| `--sync` | off | Also delete remote files absent locally (full mirror). |
| `--dry-run` | off | Show actions; make no remote changes. |
| `--yes` | off | Skip confirmation prompts (unattended). |
| `--num-workers` | `1` | Upload parallelism. |

## Historical one-off migrations

Two audio-statistics migration scripts were run once and are documented with the audio-duration tooling rather than here: `migrate_audio_durations.py` and `port_audio_seconds_from_gitbook.py` (see [Audio duration stats](audio-duration-stats.md)). They are retained for provenance and should not need re-running.

## Related

- [QC Pipeline overview](README.md)
- [Audio duration stats](audio-duration-stats.md) — `audio_durations.csv` seconds (distinct from the in-XML start/end attributes)
- [Porting a Corpus In](../porting-a-corpus.md)
