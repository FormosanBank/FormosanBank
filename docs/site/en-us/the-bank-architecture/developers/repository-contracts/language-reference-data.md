---
icon: book-font
---

# Language reference data

> Two families of per-language files silently change what the validators find and what phonology gets written: the attestation dictionaries under `QC/validation/reference/<Language>/`, and the phonology rule sidecars under `Orthographies/<Scheme>/<Language>.rules.tsv`. One is generated, one is hand-written, and neither announces itself when it is missing.

## What they are

### Attestation dictionaries

`QC/validation/reference/<Language>/attestation.txt` — a newline-delimited, sorted, casefolded word list, one per language, **16 languages, ~4,000 entries total**. They range from 56 lines (Tsou) to well over a thousand (Amis).

They exist to answer one question: *is this string a real word in this language?* That is what lets the quote/glottal classifier decide whether a `'` is the glottal letter or a stray quotation mark — the distinction POL-013 turns on, and one that cannot be made from the character alone.

### Phonology rule sidecars

`Orthographies/<Scheme>/<Language>.rules.tsv` — **15 files** across seven schemes (Ortho113, Ortho94, TaiwanNandao, MinEd, Huang, Cauquelin, Tsuchida, Zhang). Each sits beside its conversion table and holds ordered, context-sensitive rewrite rules applied *after* the table's flat character mapping:

```tsv
pattern	replacement	description
ts(?=i)	tɕ	c is palatalized before i
s(?=i)	ɕ	s is palatalized before i
ʡ(?=$|[^\w])	ʡħ	word-final glottal is released with a fricative
```

A flat table cannot express "palatalized *before i*". The sidecar is where conditioned allophony lives.

## Why they exist

Both files encode knowledge that is **linguistic, not mechanical** — the kind that cannot be derived from the XML and would otherwise end up hardcoded in a Python file, which POL-039 forbids. Keeping them as data means a linguist can review and correct them without touching code, and a diff shows exactly which phonological claim changed.

The sidecar split matters especially: conversion tables are per-scheme *orthography* (which letters map to which), while rules are per-scheme *phonology* (how those sounds behave in context). Merging them would force every table row to carry conditioning it does not need.

## Who reads them

| File | Read by |
|---|---|
| `attestation.txt` | `QC/cleaning/clean_xml.py`, `QC/utilities/classify_quotes.py` |
| `<Language>.rules.tsv` | `QC/utilities/add_phonology.py`, validated by `QC/validation/validate_registries.py` |

`add_phonology.py` loads a sidecar by **path convention** — `tsv_path.with_suffix(".rules.tsv")` next to the conversion table — and, critically, **returns silently when the file does not exist**. A missing sidecar is not an error; it means "no conditioned rules for this scheme," which is correct for most of them and indistinguishable from a typo'd filename.

### Dialect scoping

A sidecar may carry an optional fourth `dialect` column, currently used by `Ortho113/Seediq.rules.tsv` and `Ortho113/Bunun.rules.tsv`. Its semantics mirror the conversion tables':

- **blank cell, or no `dialect` column** — universal; applies to every dialect;
- **a named dialect** (comma-separated for several) — applies only to those;
- **the literal `default`** — a fallback, applied only to dialects that no rule names explicitly, so a named dialect uses its own rules *instead of* the fallback, never in addition.

{% hint style="danger" %}
Remember that `trv` is Seediq-or-Truku ([single sources of truth](single-sources-of-truth.md)). `Ortho113/Seediq.rules.tsv` is dialect-scoped, so which rules fire depends on resolving the `dialect` attribute correctly, not on the ISO code.
{% endhint %}

## How they're enforced

**Attestation dictionaries: not enforced at all.** Nothing validates that a language has one, that it is current, or that it is free of pollution. A stale or missing dictionary degrades the classifier quietly — it simply attests fewer words, so more `'` characters fall through to the default reading. The safeguard is procedural, not automated: the builder's own default is deliberately conservative, taking **only single-word sentence-level S-FORMs** (dictionary entries), because interior tokens harvested from running text can carry unresolved quote-`'` and poison the very guard the file exists to provide.

**Sidecars: partly.** `validate_registries.py` emits **V153 (SOFT)** when a sidecar scopes a rule to a dialect that is not canonical per `dialects.csv`. `add_phonology.py` additionally raises on structural problems at load: missing `pattern`/`replacement`/`description` columns, an empty pattern, or a replacement containing a backslash (replacements must be literal, not regex backreferences). Those are errors, not findings — they stop the run.

Nothing checks that a rule is *phonologically correct*. That is a linguist's review, and the `description` column exists so the review is possible.

## How to change them correctly

**Regenerate an attestation dictionary** whenever a corpus is ported — the `port-corpus-in` skill does this for you, but it can be run standalone at any time:

```bash
source .venv/bin/activate
python QC/utilities/build_attestation_dict.py --language Amis
```

It scans every `Corpora/*/XML` file whose `TEXT` `xml:lang` resolves to that language, across both the original and standard tiers, and writes the sorted result. `--include-interior` additionally unions in interior tokens above `--min-freq`; the docstring warns to use it with care, and that warning is the whole design — a polluted dictionary is worse than a small one, because it makes the classifier confidently wrong rather than merely cautious.

**Adding or editing a rule sidecar** is a linguistic change and should be reviewed as one:

- Rules are **ordered** and applied in sequence — a later rule sees the output of an earlier one, so inserting a row in the middle can change results downstream of it.
- Replacements are **literal**; backslashes are rejected at load.
- Always fill `description`. It is the only record of *why* a rule exists, and the only thing a reviewing linguist can check.
- Name the file to match its table exactly. A misnamed sidecar is silently ignored rather than reported.

```bash
python QC/validation/validate_registries.py --csv logs/registry_findings.csv
```

Then re-run `add_phonology.py` for an affected corpus and diff the PHON tiers before committing — see [add_phonology.py](../qc-pipeline/add-phonology.md).
