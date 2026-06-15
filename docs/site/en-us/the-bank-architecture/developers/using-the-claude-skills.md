---
icon: robot
---

# Using the Claude Skills

The QC and corpus-lifecycle work described in [Running an Audit](running-an-audit.md) and [Porting a Corpus In](porting-a-corpus.md) is also packaged as a set of **Claude Code skills** that live in the FormosanBank repo under [`.claude/skills/`](https://github.com/FormosanBank/FormosanBank/tree/main/.claude/skills). They are checked into version control, so anyone with [Claude Code](https://claude.com/claude-code) and a clone of the repo can use them — you don't need to be the original maintainer.

Each skill is a guided recipe: it gathers the inputs it needs, runs the QC scripts in the right order, and — crucially — **pauses for human judgment** at the points where a decision can't be automated (which orthography a corpus uses, whether a finding is a real bug, which files to port). The skills don't replace the underlying scripts documented in the [QC Pipeline](qc-pipeline/README.md) section; they orchestrate them.

## How to invoke a skill

From a Claude Code session opened in your FormosanBank clone, either:

- **Type the skill name as a slash command**, e.g. `/run-qc-pipeline`, or
- **Describe the task** — the skills are written to trigger on the matching intent (e.g. "QC this dev repo" or "port this corpus in").

{% hint style="info" %}
Several skills operate across **two repositories at once** — a sibling `Formosan-<Name>/` dev repo and FormosanBank, or FormosanBank and this GitBook repo. Start Claude Code in FormosanBank and grant access to the other directory (Claude Code's `--add-dir` / additional-directories setting) so the scripts and the data are both in scope.
{% endhint %}

The skills make **working-tree changes only** — they do not commit or push. You review the diffs and open the pull requests yourself.

## The corpus lifecycle

The skills line up with the stages a corpus passes through, from creation to publication:

```
setup-new-dev-repo  →  (ingest source, develop XML)  →  run-qc-pipeline
        →  audit-dev-repo  →  port-corpus-in  →  (published in Corpora/ + GitBook)
```

With two supporting skills used on demand: `sample-sentences-for-expert-review` (manual content review) and `refresh-audio-stats` (recompute audio durations).

## The skills

### `setup-new-dev-repo`

Bootstraps a fresh `Formosan-<Name>/` dev repo with the standard layout (`XML/`, `CodeAndDocs/`, `Private/`), a Python `.venv` installed from FormosanBank's `requirements.txt`, a `.gitignore` (audio is gitignored), a README scaffold, and a SessionStart venv-check safety hook. Surfaces decisions like whether to set up a git remote and whether to include audio scaffolding. Use it when starting a corpus that doesn't yet have its own repo.

### `run-qc-pipeline`

Runs the full QC sequence on a **dev repo**: [clean_xml](qc-pipeline/clean-xml.md) → [orthography_detector](qc-pipeline/orthography-detector.md) (**pauses for your answer** about the source orthography) → [standardize](qc-pipeline/standardize.md) → [add_phonology](qc-pipeline/add-phonology.md) → the validators ([validate_xml](qc-pipeline/validate-xml.md), [validate_text](qc-pipeline/validate-text.md), [orthography_extract](qc-pipeline/orthography-extract.md) + [validate_orthography](qc-pipeline/validate-orthography.md)/[validate_vocabulary](qc-pipeline/validate-vocabulary.md), and [validate_glosses](qc-pipeline/validate-glosses.md) if the corpus is segmented). It writes timestamped logs and a README-style `qc-summary.md` with a heuristic "ready to port?" verdict. It reports findings; it does not fix them.

### `audit-dev-repo`

The guided version of [Running an Audit](running-an-audit.md). Reads a dev repo's preprocessing, maps each transformation onto FormosanBank's pipeline, runs the validators on its output, and diffs the `original` tier against the source for dropped characters/punctuation and extraction artifacts — **pausing for the maintainer's judgment on each concern** before writing the report. Use it when reviewing a new dev repo's preprocessing prior to QC and porting.

### `port-corpus-in`

The guided version of [Porting a Corpus In](porting-a-corpus.md). Moves a QC'd corpus from its dev repo into `Corpora/<Name>/` with the standard layout, enforces the `Private/` no-leak invariant (including a content-hash check after the copy), re-validates the published XML, and wires the corpus into this GitBook (page, nav, corpus list, stats tables). It **surfaces decisions rather than guessing** — corpus name, which XML to copy, README handling, the GitBook publish branch, how to populate audio seconds — and never commits.

### `sample-sentences-for-expert-review`

Wraps [sample_sentences.py](qc-pipeline/sample-sentences.md) to pull N random `<S>` from a **published** corpus and format them as a print/email-ready report for a native speaker or linguist to spot-check — catching bad translations, unnatural phrasing, and wrong-content sentences that no automated validator can. It also drafts a cover note for the reviewer. Read-only.

### `refresh-audio-stats`

Wraps [refresh_audio_stats.py](qc-pipeline/audio-duration-stats.md) to recompute one corpus's audio durations by pulling its audio from Hugging Face, updating `statistics/audio_durations.csv`, and deleting the download. Use when a corpus's audio changed or `get_corpus_stats.py --report-stale-audio` flags it. It is **never** part of CI — one corpus at a time, on demand.

## What the skills are not

- **Not committers.** They edit the working tree; you commit and open PRs.
- **Not fix-it tools.** `run-qc-pipeline` and `audit-dev-repo` *report*; you decide what to fix, and fixes happen in the dev repo's reproduction scripts so regeneration preserves them.
- **Not a substitute for understanding the scripts.** When a skill does something surprising, the per-script pages in the [QC Pipeline](qc-pipeline/README.md) section are the ground truth.

## Related

- [QC Pipeline overview](qc-pipeline/README.md)
- [Running an Audit](running-an-audit.md)
- [Porting a Corpus In](porting-a-corpus.md)
