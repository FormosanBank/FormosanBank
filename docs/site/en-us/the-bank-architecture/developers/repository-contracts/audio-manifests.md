---
icon: list-tree
---

# Audio manifests

> `audio_sources.json` and `audio_permissions.json` are the two hand-maintained files that describe every FormosanBank audio dataset. Nothing generates them. If you publish audio, you write these entries yourself.

## What they are

Three JSON files at the repository root form one contract, and `audio_sources.json` is its entry point — it names the other two, so every tool loads the manifest and follows the pointers:

```
audio_sources.json                    ← the manifest: what exists, where, pinned to what
├── "permissions":     audio_permissions.json   ← may it be public, under what license
└── "declared_extras": audio_extras.json        ← orphans deliberately kept
```

`audio_extras.json` has its own page: [Hugging Face audio parity](hugging-face-audio-parity.md). This page covers the other two.

{% hint style="warning" %}
**No script writes these files.** There is no generator, no scaffold, no `--init`. `QC/utilities/download_audio.py` and `QC/validation/validate_hf_audio.py` are the only code that touches them, and both are strictly read-only. Every field is typed by a human and reviewed like code — which is the point: publishing audio is a decision, and a decision should not be inferable by a script from the state of a bucket.
{% endhint %}

## Why they exist

They separate two questions that are easy to conflate and expensive to get wrong:

- **`audio_permissions.json` — may this be public?** A licensing and consent record. Its entries cite an approval on a Basecamp corpus card and the license the XML carries. Getting this wrong publishes material someone did not agree to publish.
- **`audio_sources.json` — what exactly is published, and how do you get it back?** A reproducibility record. Every dataset is pinned to a 40-character commit SHA, so a download today and a download in three years produce the same bytes.

Keeping them apart means a permission change and an inventory change are separate reviews. Merging them would make "we re-uploaded the files" and "we changed who may use them" look the same in a diff.

## `audio_sources.json`

Top-level:

| Field | Read by code? | Meaning |
|---|---|---|
| `schema_version` | ✅ | Currently `1`. |
| `permissions` | ✅ | Path to `audio_permissions.json`. |
| `declared_extras` | ✅ | Path to `audio_extras.json`. |
| `datasets` | ✅ | The 21 canonical public datasets. |
| `public_source_commit` | ❌ | The FormosanBank commit the inventory was reconciled against. Provenance for humans. |
| `collection` | ❌ | The Hugging Face collection the datasets belong to. |

Each entry in `datasets` — **eight fields are required on all 21**, plus `xml_root` on every entry that derives paths from XML:

| Field | Required | Read? | Meaning |
|---|---|---|---|
| `corpus` | ✅ | ✅ | Corpus name, matching `Corpora/<name>/`. |
| `permission_id` | ✅ | ✅ | **The join key** into `audio_permissions.json`. |
| `repo_id` | ✅ | ✅ | Hugging Face dataset, e.g. `FormosanBank/ILRDF_Dicts`. |
| `revision` | ✅ | ✅ | Pinned 40-char commit SHA. Downloads resolve to this, not to `main`. |
| `destination` | ✅ | ✅ | Where it unpacks locally, e.g. `Corpora/ILRDF_Dicts/Audio`. |
| `path_mode` | ✅ | ✅ | How expected filenames are derived — see below. |
| `expected_audio_files` | ✅ | ✅ | Asserted file count. A mismatch fails. |
| `source_type` | ✅ | ❌ | `source` (hosted originals) or `generated` (derived). Documentation. |
| `xml_root` | 20/21 | ✅ | XML tree whose `<AUDIO>` elements define the expected set. |
| `validation_group` | 2 | ✅ | Validates several datasets as one combined set (both NTU Paiwan ASR sources). |
| `post_download` | 2 | ✅ | Command run after download; `{python}` is templated. |
| `files` | 1 | ✅ | Literal file list, for `path_mode: explicit`. |
| `rukai_batch_2_files` | 1 | ✅ | Which Rukai files live under `batch_2` rather than `batch_1`. |
| `generated_from` | 1 | ❌ | Prose describing how a `generated` dataset was derived. |

### `path_mode`

The heart of the manifest: it says how a filename in the XML maps to a path in the dataset. Six values, all derived from the XML rather than stored:

| Mode | Expected remote path |
|---|---|
| `root_file` | `<file>` — flat at the dataset root. |
| `language_file` | `<first XML directory>/<file>` |
| `xml_stem` | `<XML directory>/<XML basename>/<file>` |
| `ilrdf` | Like `xml_stem`, plus a `batch_1`/`batch_2` split for Rukai driven by `rukai_batch_2_files`. |
| `ntu_paiwan_sources` | Document-level `TEXT/@audio` rather than child `<AUDIO @file>`. Local validation additionally expects the extracted per-clip files. |
| `explicit` | The literal `files` list. No XML is walked. |

If you add a corpus whose audio layout matches none of these, the honest options are to reshape the upload to fit an existing mode or to add a new mode to `expected_remote_paths()`. Do not use `explicit` to paper over a layout — it disables the XML-derived check entirely, which is the check you actually want.

## `audio_permissions.json`

{% hint style="info" %}
This file is `schema_version` **2**, while `audio_sources.json` and `audio_extras.json` are `1`. The three version independently; the numbers are not meant to match.
{% endhint %}

Top-level carries the policy context: `hf_organization`, `policy` (pointing at `AUDIO-PERMISSIONS.md`), `audit_date`, `publication_rule`, `license_version_rule`, and `public_non_audio_datasets` — public datasets in the organization that legitimately hold no audio, which the validator confirms by listing their files.

Then 22 `sources`: **20 `published_public`, 2 `development_private`.**

| Field | Meaning |
|---|---|
| `permission_id` | Unique; the join key `audio_sources.json` refers to. |
| `corpus`, `source` | The corpus, and a prose description of where the recordings came from. |
| `status` | `published_public` or `development_private`. |
| `license` / `hf_license` | Human form (`CC BY-NC 4.0`) and Hub form (`cc-by-nc-4.0`). Both are recorded because the dataset card must carry the second. |
| `basis` | Why this license applies — the reasoning, in prose. |
| `hf_repositories` | `{repo_id, access}` pairs. `access` is checked against the Hub anonymously. |
| `version_basis`, `xml_path`, `approval_record` | On the 20 published sources: which license-version rule applied, the XML the license comes from, and where approval is recorded (a Basecamp corpus card). |

## How they're enforced

`load_contract()` validates the join **before any network call**, and these are contract errors (exit `2`), not findings:

- every `permission_id` in `audio_permissions.json` is unique;
- every dataset's `permission_id` exists there;
- that source's `status` is `published_public`;
- the dataset's `repo_id` is listed under it with `access: public`.

So a dataset cannot be added to the manifest without a matching, approved, public permission record. The remaining checks — org inventory and file-level parity — are on the [validate_hf_audio.py](../qc-pipeline/validate-hf-audio.md) page, and run in the blocking `hf-audio-parity` workflow.

{% hint style="danger" %}
Fields marked "read by code? ❌" — `public_source_commit`, `collection`, `source_type`, `generated_from` — are **not verified by anything**. They are provenance notes for humans and can silently go stale. Treat them as comments, and do not build tooling that trusts them without adding a check first.
{% endhint %}

## How to change them correctly

Publishing a new corpus's audio, in order — this is the checklist from [Audio publication policy](audio-publication-policy.md), with the manifest detail filled in:

1. **Confirm approval** on the corpus's Basecamp card. Nothing below is valid without it.
2. **Add the `audio_permissions.json` source** — a new unique `permission_id`, `status: published_public`, the license in both forms, the `basis` prose, and each `hf_repositories` entry.
3. **Flip the Hugging Face dataset to public** and set its dataset-card license to match `hf_license`.
4. **Add the `audio_sources.json` dataset** — `permission_id` matching step 2, the `repo_id`, the `revision` pinned to the current dataset commit SHA, the local `destination`, a `path_mode` that actually describes the upload, and `expected_audio_files` as the true count.
5. **Verify anonymously**, exactly as CI does:

```bash
source .venv/bin/activate
python QC/validation/validate_hf_audio.py --corpus <Name>
```

**To re-pin after re-uploading audio**, update `revision` to the new SHA *and* `expected_audio_files` if the count moved. A stale `revision` is not caught as an error — downloads simply keep fetching the old bytes, which is exactly what pinning is for and exactly why forgetting to update it is silent.

**To retire a dataset**, remove it from `datasets`, set its source `status` appropriately, and make the Hub repository private in the same change — the org inventory check fails on a public dataset with no publication record.
