---
icon: rotate
---

# Synced pages

> A few pages in this GitBook are generated copies of files that are canonical in the FormosanBank repository. Edit them here and your change is silently reverted by the next sync.

## What it is

`sync_upstream_docs.py` in the GitBook repository regenerates one page per entry in its `DOCS` table:

| Canonical file (FormosanBank) | Generated page (GitBook) |
|---|---|
| `POLICIES.md` | [FormosanBank Policies](../../policies.md) |
| `AUDIO-PERMISSIONS.md` | [Audio publication policy](audio-publication-policy.md) |

Each generated page carries GitBook front-matter, a **"Synced copy — do not edit here"** banner naming its source, and then the upstream file verbatim.

## Why it exists

These documents version with *code*, not with prose. `POLICIES.md` entries cite rule IDs and script names, so a ruling and the validator that implements it must move in the same commit. `AUDIO-PERMISSIONS.md` states license and publication facts that `audio_permissions.json` and the [parity checks](hugging-face-audio-parity.md) enforce mechanically.

Keeping the canonical copy in FormosanBank means a policy change and its implementation are reviewed together. Publishing a rendered copy here means readers of the documentation site see it. Generating rather than transcribing means the two cannot quietly disagree — which, for license statements, is the difference between documentation and misinformation.

## Who reads it

`sync_upstream_docs.py` expects a FormosanBank checkout as a **sibling directory** by default; `--formosanbank PATH` overrides it. `--check` verifies without rewriting, `--only NAME` limits the run to one document.

## How it's enforced

`tests/test_upstream_doc_sync.py` byte-compares each generated page against a fresh render of its source, in the GitBook's `tests` workflow, which checks out FormosanBank at `main` alongside this repository.

The coupling is deliberate and cross-repo: **an upstream edit that is not synced here turns this repository red**, including on pull requests that have nothing to do with it. That is the intended signal — the fix is one command — and it matches how `corpus-page-lint` already checks out FormosanBank to lint corpus pages against `Corpora/`.

The drift tests **skip** rather than fail when no FormosanBank checkout is present, so `pytest` still passes against a standalone clone.

{% hint style="info" %}
This check ran for the first time in the change that generalized it, and immediately caught real drift: the policies page on `main` was missing POL-041 and POL-013 clause 3, both merged upstream weeks earlier. The check had existed but was never wired into CI.
{% endhint %}

Two structural guards run alongside the comparison: document names and target pages must be unique, and **a source may not contain relative Markdown links**. Sources are copied verbatim, so a link written for the FormosanBank tree resolves somewhere else entirely once rendered inside the GitBook. Use absolute `https://` links in a synced document.

## How to change it correctly

**To change the content**, edit the canonical file in FormosanBank, then in the GitBook repository:

```bash
python sync_upstream_docs.py          # regenerate every page
python sync_upstream_docs.py --check  # verify only; exits 1 on drift
pytest -q
```

Commit the regenerated page. Because the two repositories are checked separately, **merge the FormosanBank change first** — otherwise the GitBook's drift check compares against upstream `main`, which does not yet have your edit.

**To add a document to the sync**, append a `SyncedDoc` to `DOCS` with its `name`, `source`, target `page`, GitBook `icon` and a one-clause `rationale` for the banner; run the script; then wire the new page into `en-us/SUMMARY.md`. The drift test picks it up automatically — `DOCS` is what it parametrizes over.

**Never** edit a generated page directly. If you find yourself wanting to add GitBook-specific framing, that framing belongs in a neighbouring hand-written page that links to the synced one — which is exactly the relationship between [Hugging Face audio parity](hugging-face-audio-parity.md) and [Audio publication policy](audio-publication-policy.md).
