---
icon: scale-unbalanced
---

# Hugging Face audio parity

> The repository enforces **exact** parity between the audio files its XML references and the audio files hosted on the FormosanBank Hugging Face datasets. `audio_extras.json` is the allowlist that makes deliberate exceptions possible — one path at a time.

## What it is

Four files at the repository root describe the audio contract. Two govern *permission*, two govern *inventory*, and it is worth keeping the pair straight:

<table><thead><tr><th width="230">File</th><th>Governs</th></tr></thead><tbody>
<tr><td><code>AUDIO-PERMISSIONS.md</code></td><td>The publication <em>rule</em> — prose. See <a href="audio-publication-policy.md">Audio publication policy</a>.</td></tr>
<tr><td><code>audio_permissions.json</code></td><td>Publication status and license, per audio source.</td></tr>
<tr><td><code>audio_sources.json</code></td><td>The manifest: which datasets are canonical, pinned to a revision, and where each unpacks locally.</td></tr>
<tr><td><code>audio_extras.json</code></td><td>The allowlist of <strong>orphaned audio</strong> — files on the Hub that no <code>&#x3C;AUDIO></code> element points at.</td></tr>
</tbody></table>

The first two answer *may this audio be public*. The last two answer *is the inventory reconciled*. This page is about the second question.

`audio_extras.json` has a deliberately small shape:

```json
{
  "schema_version": 1,
  "description": "Public audio present on Hugging Face but not referenced by the current public XML. These files remain covered by the published corpus license and are intentionally retained and downloaded.",
  "repositories": {
    "FormosanBank/YeddaPalemeqBlog_Paiwan": ["S24_1.wav", "S535_1.wav"]
  }
}
```

It currently declares **767 files across 13 repositories**, overwhelmingly ePark — `xue_xi_ci_biao` alone accounts for 433 — plus 34 in `YutasWilang` and 2 each in `Whitehorn_Collection` and `YeddaPalemeqBlog_Paiwan`.

## Why it exists

Parity is enforced in **both** directions, which is the whole point: a missing file means the XML promises audio that isn't there, and an unexpected file means something is published that nothing accounts for. Without an escape hatch, every legitimately unreferenced file on the Hub would fail CI forever.

The alternative to an allowlist is loosening the check — and a check that tolerates unexplained files stops being able to tell you when audio goes missing. So the file is how you say *yes, that one is supposed to be there*, deliberately and individually, instead of turning the check down.

### The typical reason a file lands here

The Yedda Palemeq entries are the clean example. `S24_1.wav`, `S483_1.wav` and `S535_1.wav` each record a sentence the source printed with two alternatives. When those sentences were split into `S24_1` / `S24_1b`, the recording — which speaks *both* options — represented neither variant, so the `<AUDIO>` reference was dropped from the XML. The file is still legitimately published under the corpus license. Deleting it from the Hub would destroy a real recording to satisfy a bookkeeping check; declaring it says the loss of the reference was intentional.

That is the shape to look for: **the audio is fine, the reference is correctly absent.** If instead the reference is missing *by mistake*, the fix is the XML, not this file.

## Who reads it

[`QC/validation/validate_hf_audio.py`](../qc-pipeline/validate-hf-audio.md) loads it — not directly, but through `audio_sources.json`'s `declared_extras` pointer, so the manifest stays the single entry point to the contract. Both manifests are hand-maintained and documented field by field in [Audio manifests](audio-manifests.md). It then does three-way set arithmetic per dataset group:

| Comparison | Meaning | Result |
|---|---|---|
| `expected - actual` | XML references a file that isn't hosted | **missing** — failure |
| `actual - expected - declared` | Hosted, unreferenced, and not declared here | **undeclared extra** — failure |
| `declared - actual` | Declared here, but the file no longer exists | **stale declaration** — failure |

The third row is the one people forget. A declaration is not a permanent exemption: when the file goes away, the entry must go too, or CI fails on the leftover.

The same arithmetic runs against both the Hub (`validate_online`) and a local download (`--local`). [`QC/utilities/download_audio.py`](../qc-pipeline/misc-utilities.md) also runs the online half before it transfers anything, so `--dry-run` checks the contract without moving 105 GiB.

The loader is strict on purpose: it rejects an unknown `schema_version`, a repository not present in `audio_sources.json`, a non-string path, and duplicate paths within a repository. A typo'd repo name fails loudly rather than silently declaring nothing.

## How it's enforced

The **`hf-audio-parity`** workflow, which is the only unconditionally blocking check in the repository — it passes no `--no-exit-on-hard` and swallows no exit code. It runs:

- on pull requests touching `Corpora/**/*.xml`, any of the four manifests, the validator, or the workflow itself;
- on pushes to `main` with the same paths;
- nightly at **08:17 UTC**, which is what catches drift caused from the Hugging Face side rather than by a commit.

It runs anonymously (`HF_TOKEN: ''`), so it verifies what the public actually sees, not what a privileged token can reach.

Exit codes: `0` pass, `1` parity failures, `2` a contract error such as unparseable JSON or an unknown schema version.

{% hint style="warning" %}
The same job also enforces the **org-level inventory**, which is easy to trip without touching audio at all: no unapproved public dataset in the organization, every published dataset genuinely anonymously public, every canonical dataset carrying a publication record, and no audio hiding in a repository declared non-audio (including public models and Spaces). Making a dataset public on the Hub without adding it to `audio_permissions.json` fails the nightly run.
{% endhint %}

## How to change it correctly

**To declare an orphan.** First confirm the reference is *correctly* absent — that the audio is legitimate and the XML is right to not point at it. Then add the path under its repository in `audio_extras.json`, keeping paths relative to the dataset root and the list sorted. Say why in the commit message; the file itself has no per-entry comment field, so the commit is the only place the reason survives.

**To remove one.** When a file is deleted from the Hub, delete its entry in the same change. Leaving it behind is a stale declaration and fails CI.

**To re-reference a file.** If XML gains an `<AUDIO>` element pointing at a declared file, remove the declaration — it is now `expected`, and leaving it declared is harmless to the arithmetic but misleading to the next reader.

Verify before pushing:

```bash
source .venv/bin/activate

# The full contract, anonymously, exactly as CI runs it.
python QC/validation/validate_hf_audio.py

# One corpus, when you know what you touched.
python QC/validation/validate_hf_audio.py --corpus ePark

# Against audio you have already downloaded, instead of the Hub.
python QC/validation/validate_hf_audio.py --local --corpus ePark
```

{% hint style="danger" %}
`audio_extras.json` reconciles **inventory only**. It never grants permission to publish anything. A file being declared here asserts that it is already covered by its corpus's published license — if that is not true, the problem is a publication decision, and it belongs in [audio publication policy](audio-publication-policy.md) and `audio_permissions.json`, not here.
{% endhint %}
