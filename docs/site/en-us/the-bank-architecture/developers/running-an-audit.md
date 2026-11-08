---
icon: magnifying-glass
---

# Running an Audit

Before a new corpus is QC'd and published into FormosanBank, its **preprocessing is audited**: every transformation the corpus's ingestion code applies to the data is checked for correctness against FormosanBank's conventions. This page describes the audit as a manual procedure — the steps, the tools to run, and the judgments to make. FormosanBank also ships a guided [`audit-dev-repo` Claude skill](using-the-claude-skills.md) that walks you through exactly this sequence; the steps below are what that skill automates.

{% hint style="info" %}
**Why audit at all?** New corpora are developed in separate per-corpus dev repos (`Formosan-<Name>/`), often by contributors who write strong ingestion code but do not read the Formosan languages. Before the bank trusts that output, we verify that the preprocessing didn't silently distort the data.
{% endhint %}

## What you need

- A local clone of [FormosanBank](https://github.com/FormosanBank/FormosanBank) with its `.venv` active (`source .venv/bin/activate`).
- The corpus **dev repo** as a sibling directory (e.g. `../Formosan-<Name>/`) containing the built XML (commonly under `XML/`, sometimes `Final_XML/`) and the ingestion scripts that produced it.
- The corpus's language, so you can find the right reference data under [`QC/validation/reference/<Language>/`](https://github.com/FormosanBank/FormosanBank/tree/main/QC/validation/reference) and `Orthographies/Ortho113/<Language>.tsv`.

Read [FormosanBank's `CLAUDE.md`](https://github.com/FormosanBank/FormosanBank/blob/main/CLAUDE.md) and the [QC Pipeline overview](qc-pipeline/README.md) first — they define the conventions an audit checks against.

## The scope: anything that touches the data

The general goal is to check **every transformation** the preprocessing applies — each one should make sense and look correct. Four concerns are highlighted priorities (not an exhaustive checklist):

| | Concern | What to look for |
|---|---------|------------------|
| **(a)** | Eliminated orthography characters | Real letters dropped — glottal-stop apostrophe, `ŋ`, `ə`, `ɬ`, barred/stroked letters. Curly apostrophes (`’`, U+2019) silently lost are a classic case. |
| **(b)** | Suppressed punctuation | Punctuation or segmentation stripped from the tier that must stay faithful (the **original** tier), or segmentation markers (`-`, `=`, `<…>`) removed from the `W` tier. |
| **(c)** | Other convention breaks | Schema, `kindOf`, `TRANSL/@ver`, dialects, segmentation markers, id rules. |
| **(d)** | Source-extraction artifacts | Leftovers like sentences the source marked ungrammatical (sentence-initial `*`), footnote-digit leaks, out-of-language examples. |

The **original tier is the faithfulness anchor**: most of (a), (b), and (d) reduce to "did the original tier lose something the source had?"

## The procedure

### 1. Read the preprocessing

Read the dev repo's `README` and every scrape/parse/build script. Produce a plain-language summary of the transformations it applies and in what order — flag every step that **deletes or substitutes characters** or **drops/normalizes punctuation**. Confirm your reading is correct before going further.

### 2. Map each transformation to our pipeline

For each step, classify it: (i) our pipeline already does this (and how it differs), (ii) it's a no-op for us, or (iii) it conflicts with a convention (cite which). Pay special attention to anything touching the **original** tier and to `W`-tier segmentation markers, which must survive. As a reference, FormosanBank's own tooling runs in two passes — a cleaning & standardization build (`apply_manual_edits` → `clean_xml` → orthography detection (human) → `standardize` → `add_phonology`) followed by a read-only validation pass — both laid out in the [QC Pipeline overview](qc-pipeline/README.md).

### 3. Run the validators on the built XML

Run the finding-based validators against the dev repo's XML output and read each per-rule summary plus its findings CSV. Use `--no-exit-on-hard` so a HARD finding doesn't abort your run — at this stage you are gathering information, not gating.

```bash
# Structure & schema
python QC/validation/validate_xml.py by_path --path ../Formosan-<Name>/XML --no-exit-on-hard

# Text content: punctuation, character set, processing artifacts
python QC/validation/validate_text.py by_path --path ../Formosan-<Name>/XML --no-exit-on-hard

# Orthography: extract from the ORIGINAL tier, then compare to reference
python QC/orthography/orthography_extract.py \
  --corpus all --language All --kindOf original --by_dialect true \
  --corpora_path ../Formosan-<Name>/XML --output_dir logs/audit-extract
python QC/validation/validate_orthography.py \
  --o_info logs/audit-extract --reference QC/validation/reference

# Gloss tiers — only if the corpus has <W>/<M> segmentation
python QC/validation/validate_glosses.py by_path --path ../Formosan-<Name>/XML
```

{% hint style="info" %}
The guided [`run-qc-pipeline` skill](using-the-claude-skills.md) runs this whole sequence for you (cleaning, standardize, add-phonology, then every validator) and writes timestamped logs plus a summary. The audit only needs the validators, but the full pipeline is a convenient superset.
{% endhint %}

Organize the hits by concern using the map below.

### 4. Diff the output against the source

Automated rules don't catch everything. Pull a sample of sentences with [sample_sentences.py](qc-pipeline/sample-sentences.md) (or pick representative ids) and, for each, compare the `FORM[@kindOf="original"]` against the raw source:

```bash
python QC/utilities/sample_sentences.py --corpus_path ../Formosan-<Name> --n 20 --seed 42 \
  --output logs/audit-sample.md
```

- **(a)** Did any orthographic letter disappear? Compare the original-tier character inventory against both the source and `reference/<Language>/`.
- **(b)** Did punctuation or segmentation in the original tier vanish relative to the source?
- **(d)** Are there sentence-initial `*` (should have been excluded), footnote-digit leaks, or out-of-language runs?

### 5. Flag and decide

Group findings by concern (a–d) with concrete evidence — file, id, and a source-vs-XML sample for each. **This is a human-judgment step**: every finding needs a maintainer's call (real bug / acceptable / needs a source check) before it becomes a remediation item. An audit *surfaces* problems; it does not fix them.

### 6. Record the report

Write a per-repo report (the skill saves it at `claudeplans/audit-<Repo>.md`): what the preprocessing did, findings by concern with evidence, the pipeline mapping, and which conflicts must be fixed in the reproduction scripts *before* the corpus is ported.

## Concern → tool map

| Concern | Run / check |
|---------|-------------|
| (a) dropped orthography chars | [orthography_extract.py](qc-pipeline/orthography-extract.md) `--kindOf original` → [validate_orthography.py](qc-pipeline/validate-orthography.md) vs `reference/<Language>/`; diff the original-tier inventory against the **source**; watch curly-apostrophe loss |
| (b) suppressed punctuation | [validate_text.py](qc-pipeline/validate-text.md); confirm the **original** tier still has source punctuation/segmentation and the `W` tier kept `-`/`=`/`<>` |
| (c) convention breaks | [validate_xml.py](qc-pipeline/validate-xml.md) (schema/`kindOf`/`ver`/dialects) + [validate_glosses.py](qc-pipeline/validate-glosses.md) (segmentation & reconstruction rules) |
| (d) extraction artifacts | [validate_text.py](qc-pipeline/validate-text.md) (`*`-in-FORM, footnote leaks); grep source + XML for sentence-initial `*`, stray digits, out-of-language runs |

## Important boundaries

- An audit is **not a fix-it pass**. Do not modify the dev repo or `Corpora/` while auditing. Remediation happens in the dev repo's reproduction scripts, then the corpus is re-QC'd.
- **Evidence over assertion**: every finding should cite a file, an id, and a source/XML sample.
- Once the audit is clean (or its findings are remediated and re-QC'd), the corpus is ready to [port in](porting-a-corpus.md).

## Related

- [QC Pipeline overview](qc-pipeline/README.md)
- [Porting a Corpus In](porting-a-corpus.md)
- [Using the Claude Skills](using-the-claude-skills.md)
