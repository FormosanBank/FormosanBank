---
name: sample-sentences-for-expert-review
description: Pull N random <S> elements from a published FormosanBank corpus and format them as a print/email-ready markdown report for a human expert to spot-check (translation quality, naturalness, content accuracy — things no automated validator can catch). Wraps QC/utilities/sample_sentences.py and walks the maintainer through generating + sending the sample. Use when you want a manual expert review of a corpus's contents.
---

# sample-sentences-for-expert-review

Generate a small random sample of sentences from a corpus so a native-speaker or linguist reviewer can eyeball them. This is the **B9.7** manual-review step: it surfaces issues the automated validators (`validate_xml`, `validate_text`, `validate_glosses`, …) structurally cannot — bad translations, unnatural phrasing, wrong-content sentences.

**Operates on published `FormosanBank/Corpora/<Name>/` trees** (not `Formosan-<CORPUS>/` dev repos — that is `run-qc-pipeline`'s territory). It is read-only: it never mutates XML.

The underlying tool is [QC/utilities/sample_sentences.py](../../../QC/utilities/sample_sentences.py). Each sampled `<S>` is rendered with its id, language, source file, every FORM (by `kindOf`), PHON, every TRANSL (by `xml:lang`), AUDIO references, and the full W/M tier when present.

## Inputs (gather via `AskUserQuestion` if missing)

- `corpus_path` — the corpus to sample, e.g. `Corpora/ePark`. **Required.** If `<corpus_path>/XML/` exists, only that subdir is walked (the canonical-walk convention). If the user names a language rather than a corpus, point them at the corpus dir that contains it (or sample the whole corpus and note the language in the cover note).
- `n` — sample size. Default **20** (the tool's default; B9.7's proposed size). Offer 20 unless the reviewer asked for more/fewer. Capped at the corpus's total `<S>` count.
- `seed` — pass an explicit integer (e.g. `42`) **whenever the sample needs to be reproducible** — i.e. so you or the reviewer can regenerate the exact same 20 sentences later. Omit only for a genuinely throwaway look. Record the seed you used in the cover note.
- `output` — a file path to save the report. Default: save it (don't just dump to stdout) so it can be attached/pasted. Suggest `logs/sample-<corpus>-seed<seed>.md` or a user-chosen path; `logs/` is gitignored.

## Pre-checks

1. Verify `corpus_path` exists and is a directory. If not, stop and ask.
2. Confirm the repo `.venv` is active (`source .venv/bin/activate`) — the SessionStart hook normally ensures this. All invocations use the repo `.venv` python.
3. If the corpus has **no standard tier**, the report still works (it shows whatever FORMs exist), but say so in the cover note — reviewers should know whether they're looking at original-orthography text.

## Recipe

Run the sampler with the chosen inputs:

```bash
source .venv/bin/activate
python QC/utilities/sample_sentences.py \
    --corpus_path <corpus_path> \
    --n <n> \
    --seed <seed> \
    --output <output_path>
```

- Omit `--seed` only for a throwaway sample.
- Omit `--output` only if the user explicitly wants it on stdout.

Then:

1. **Read the report back** and sanity-check it rendered (right number of sentences, FORM/TRANSL populated, no obviously empty records). If many records are sparse, mention it — it may itself be a finding.
2. **Show the user a short preview** (the first 2–3 sentences) plus the saved path.

## Cover note for the reviewer

Draft a short, paste-ready cover note to accompany the report so the expert knows what to do. Include:

- Which corpus + language(s), and roughly how big it is.
- That this is a random spot-check of **N** sentences (and the **seed**, so it can be regenerated).
- Which tiers are present (original / standard / translations / audio).
- A concrete ask: *"For each sentence, flag anything that looks wrong — bad or unnatural translation, mis-transcription, wrong-language content, or a sentence that doesn't belong. No need to fix; just mark and comment."*
- Where to send comments back.

Keep it short enough to paste into an email body, with the markdown report attached or pasted below it.

## After the review

When the reviewer returns findings, each confirmed problem is a candidate for:
- a corpus data fix (in the corpus's dev repo if it has one, so regeneration preserves it; otherwise a documented published-corpus remediation), and/or
- a new automated check if the problem is a detectable class (turn it into a `validate_text`/`validate_glosses` rule + fixture per the "saw a problem → regression test" workflow).

## What this skill is NOT

- Not a validator. It surfaces nothing automatically; a human reads the output.
- Not a fix-it tool. Read-only; the maintainer decides what to do with the findings.
- Not for dev repos. Use `run-qc-pipeline` for `Formosan-<CORPUS>/` QC.
