---
icon: screwdriver-wrench
---

# Miscellaneous utilities

> The one-off helper for uploading a corpus's audio to Hugging Face. (The dev-repo-era audio wranglers `add_durations.py`, `group_audios.py` and `organize_batches.py` were deleted in October 2026; `audio_durations.csv` is maintained by the [audio duration stats](audio-duration-stats.md) tooling.)

## What it's for

Not part of the routine QC pipeline: run once per corpus when its audio is first published, or after it changes. For keeping an already-published dataset in parity with the XML, use [sync_hf_audio.py](sync-hf-audio.md) instead.

## When to run it

Run by hand from the repo root after `source .venv/bin/activate`. Not wired into CI.

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

## Related

- [QC Pipeline overview](README.md)
- [Audio duration stats](audio-duration-stats.md) — `audio_durations.csv` seconds
- [sync_hf_audio.py](sync-hf-audio.md) — keep a published dataset in parity with the XML
- [Porting a Corpus In](../porting-a-corpus.md)
