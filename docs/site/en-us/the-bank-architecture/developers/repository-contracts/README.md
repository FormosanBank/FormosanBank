---
icon: file-contract
---

# Repository Contracts

> The invariants the FormosanBank repository enforces on itself — the manifests, registries, and generated files that CI checks, and the correct procedure for changing each one.

The [QC Pipeline](../qc-pipeline/README.md) section documents **scripts**: what each one does and how to run it. This section documents **contracts**: rules the repository holds itself to, each with a file that records the rule, a check that enforces it, and a right way to change it.

The difference matters because a contract fails differently from a script. You do not run `audio_extras.json`; you trip over it — in CI, in a pull request that looked unrelated, usually while doing something else. These pages exist so that the first time you meet one of these rules is not the first time it blocks you.

{% hint style="info" %}
**If CI has just failed on you and you want the fix, not the theory** — every page's *How to change it correctly* section is the procedure, and it is the last section on each page.
{% endhint %}

### The pages

<table data-header-hidden><thead><tr><th width="270"></th><th></th></tr></thead><tbody>
<tr><td><a href="hugging-face-audio-parity.md">Hugging Face audio parity</a></td><td>Exact parity between audio the XML references and audio hosted on the Hub, including <code>audio_extras.json</code>, the allowlist for deliberate orphans.</td></tr>
<tr><td><a href="audio-manifests.md">Audio manifests</a></td><td>The two hand-maintained JSON files behind every audio dataset: every field, who writes them, and which fields nothing checks.</td></tr>
<tr><td><a href="audio-publication-policy.md">Audio publication policy</a></td><td>Which audio may be public, under which license. Synced from <code>AUDIO-PERMISSIONS.md</code>.</td></tr>
<tr><td><a href="ci-workflows.md">CI workflows</a></td><td>All nine workflows: what runs when, and which ones can actually block a pull request.</td></tr>
<tr><td><a href="generated-files.md">Generated files</a></td><td>Files CI writes and you must not hand-edit — and the one that looks generated but is not.</td></tr>
<tr><td><a href="single-sources-of-truth.md">Single sources of truth</a></td><td>The registries every script reads for language, dialect, and orthography identity (POL-039).</td></tr>
<tr><td><a href="language-reference-data.md">Language reference data</a></td><td>Per-language attestation dictionaries and phonology rule sidecars — both change validator and phonology behaviour, and a missing one is silent.</td></tr>
<tr><td><a href="synced-pages.md">Synced pages</a></td><td>GitBook pages generated from canonical FormosanBank files, and the drift check that keeps them honest.</td></tr>
</tbody></table>

### How each page is organized

Every page answers the same five questions in the same order, so you can skim to the one you need:

1. **What it is** — the file, where it lives, its shape.
2. **Why it exists** — what breaks without it. Usually the reason it is a file rather than a looser check.
3. **Who reads it** — the scripts and workflows that consume it.
4. **How it's enforced** — which check, blocking or informational, and when it runs.
5. **How to change it correctly** — the procedure, and what to run before you push.

### What belongs here

A page belongs in this section when all three are true: there is a **file in the repository** that records the rule; there is an **automated check** that enforces it; and getting it wrong **fails somewhere other than where you made the mistake**. That last one is the real test — it is what makes a contract worth documenting separately from the tool that reads it.

Project-wide *rulings* — the questions that have been decided once and should not be re-litigated — live in [FormosanBank Policies](../../policies.md) as numbered POL entries. These pages cite POL entries; they do not restate them.
