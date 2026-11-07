---
icon: cloud-arrow-up
---

# sync_hf_audio.py

> Brings one Hugging Face audio dataset back into parity with the XML: slices and uploads the clips the XML references but the Hub lacks, deletes the Hub files nothing references any more, in a single Hub commit. Dry run by default.

## What it's for

[validate_hf_audio.py](validate-hf-audio.md) *reports* drift between a corpus's `<AUDIO file=…>` references and the dataset that hosts them, and CI fails on it. This script *repairs* it. Drift appears whenever a rebuild changes sentence boundaries (new clip names, stale old ones) or adds sentences with audio.

## How it works

1. Reads every `AUDIO` element under `--xml` (working tree, or a git revision with `--from-ref` so a branch can be synced without checking it out) and keys each clip as `<language dir>/<file>`; the first `start`/`end` seen for a name wins, elements missing `url`, `start` or `end` are ignored.
2. Lists the dataset's `.mp3` files anonymously.
3. Prints the two differences: **missing** (to slice from the whole-story recording named by `AUDIO/@url` and upload) and **extras** (to delete).
4. Without `--apply` it stops there. With `--apply` it checks write access first, slices with `ffmpeg`, and sends one commit; it then prints the revision SHA and file count to record in `audio_sources.json`.

## Usage

```bash
source .venv/bin/activate

# Report only (no token, no ffmpeg, no downloads):
python QC/utilities/sync_hf_audio.py --repo FormosanBank/NTUFormosanCorpus_Stories \
    --xml Corpora/NTUFormosanCorpus/XML/Stories

# Against a branch that is not checked out:
python QC/utilities/sync_hf_audio.py --repo FormosanBank/<Dataset> \
    --xml Corpora/<Corpus>/XML --from-ref origin/<branch>

# Do it:
export HF_TOKEN=hf_xxxxxxxx      # write access to the dataset
python QC/utilities/sync_hf_audio.py --repo FormosanBank/<Dataset> \
    --xml Corpora/<Corpus>/XML --apply
```

| Flag | Default | Purpose |
| --- | --- | --- |
| `--repo` | required | Dataset id, e.g. `FormosanBank/NTUFormosanCorpus_Stories`. |
| `--xml` | required | XML directory whose `AUDIO` elements are the contract. |
| `--from-ref` | off | Read the XML from this git revision instead of the working tree. |
| `--apply` | off | Slice, upload and delete. Without it nothing is written anywhere. |
| `--no-slice` | off | Report only; refuses to combine with `--apply` when clips are missing. |
| `--work-dir` | temp dir | Where recordings are cached and clips written. |
| `--token` | `$HF_TOKEN`, then the stored `huggingface-cli login` | Hub token. |
| `--message` | generated | Hub commit message. |

## Output & side effects

Prints counts (referenced by the XML, present on the Hub, to upload, to delete) and the first ten names of each list. **Dry run changes nothing.** With `--apply`: one commit on the dataset, which deletes files from a public dataset irreversibly from here; the whole-story recordings are downloaded to the work dir for slicing.

## When to run it

After any rebuild that changes sentence boundaries or adds audio, before the PR is merged, and again whenever `validate_hf_audio.py` reports missing or extra files. The dry run is part of the port skill's audio step; `--apply` is the maintainer's call.

## Related

- [validate_hf_audio.py](validate-hf-audio.md) — the check this repairs
- [Hugging Face audio parity](../repository-contracts/hugging-face-audio-parity.md) — why parity is enforced both ways
- [Audio duration stats](audio-duration-stats.md)
- [QC Pipeline overview](README.md)
