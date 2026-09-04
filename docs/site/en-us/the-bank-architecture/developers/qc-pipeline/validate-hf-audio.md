---
icon: cloud-check
---

# validate_hf_audio.py

> Anonymous check that the FormosanBank Hugging Face organization matches what the repository says it should be: published audio public, development audio private, and exact file-level parity between the XML's `<AUDIO>` references and the hosted datasets.

## What it's for

Unlike [validate_audio.py](validate-audio.md), which inspects audio files you have *locally* for decodability and silence, this validator checks the **contract between the repository and the Hub**. It answers three questions no local check can:

1. Is every dataset that should be public actually public, anonymously?
2. Is anything public that shouldn't be?
3. Does the set of hosted files match the set the XML references, exactly?

It is the only validator in the repository that is unconditionally blocking in CI. The conceptual background — why parity is enforced in both directions, and what `audio_extras.json` is for — is on the [Hugging Face audio parity](../repository-contracts/hugging-face-audio-parity.md) contract page; this page is the tool reference.

## How it works

Everything starts from `audio_sources.json`, the manifest, which points at `audio_permissions.json` (`permissions`) and `audio_extras.json` (`declared_extras`). Loading is strict: an unknown `schema_version`, a declared repository absent from the manifest, a non-string path, or a duplicate path is a contract error, not a finding.

**Inventory checks** (online mode only) enumerate the organization anonymously via `HfApi(token=False)` and report:

| Failure class | Meaning |
|---|---|
| unapproved public Hugging Face datasets | Public in the org, but not a published source and not a declared non-audio dataset. |
| published audio datasets not anonymously public | `audio_permissions.json` says published; the Hub disagrees. |
| canonical audio datasets missing publication records | In the manifest, but no `published_public` record. |
| declared non-audio but contains audio | A dataset — or a public model or Space — asserted to hold no audio, that does. |

**Parity checks** compare three sets per dataset group: `expected` (files the XML references), `actual` (files hosted, or downloaded under `--local`), and `declared` (`audio_extras.json`).

| Comparison | Reported as |
|---|---|
| `expected - actual` | missing |
| `actual - expected - declared` | undeclared extras |
| `declared - actual` | stale declarations |

Any non-empty delta is a failure. Online mode lists remote files with a blobless, depth-1 `git ls-tree` rather than downloading anything.

Exit codes: **0** pass · **1** parity or inventory failures · **2** contract error (unparseable JSON, unknown schema version, unmanifested repository).

## Usage

Run from the repo root after `source .venv/bin/activate`. No Hugging Face token is needed or wanted — CI runs it with `HF_TOKEN: ''` so it sees exactly what the public sees.

```bash
# Everything, against the Hub — exactly what CI runs.
python QC/validation/validate_hf_audio.py

# One corpus.
python QC/validation/validate_hf_audio.py --corpus ePark

# Against audio already downloaded locally, skipping the org inventory.
python QC/validation/validate_hf_audio.py --local --corpus ePark
```

| Flag | Required | Default | Meaning |
|---|---|---|---|
| `--manifest` | no | `audio_sources.json` | Path to the manifest that anchors the whole contract. |
| `--corpus` | no | all datasets | Restrict to one corpus's datasets. |
| `--local` | no | off | Validate downloaded `Audio/` directories instead of the Hub. Skips the org inventory checks. |

{% hint style="info" %}
`QC/utilities/download_audio.py` runs the same online parity check before transferring anything, so `--dry-run` verifies the contract without moving ~105 GiB. See [Misc utilities](misc-utilities.md).
{% endhint %}

## When it fails

- **missing** — the XML references audio that isn't hosted. Usually a filename or path-mode mistake in the XML, or an upload that didn't complete.
- **undeclared extras** — something is hosted that nothing references. Decide whether the *reference* is wrong (fix the XML) or the *orphan is intentional* (declare it in `audio_extras.json`, with the reason in the commit message).
- **stale declarations** — a declared file no longer exists. Remove its entry.
- **inventory failures** — a dataset's visibility on the Hub and its record in `audio_permissions.json` disagree. Fix whichever is wrong; if the *permission* is in question, that is a publication decision, not a bookkeeping one — see [Audio publication policy](../repository-contracts/audio-publication-policy.md).

Because the workflow also runs **nightly at 08:17 UTC**, a failure can appear with no commit behind it. That means something changed on the Hugging Face side.
