---
icon: list-ol
---

# The rule catalogue

> Every validation rule in one place — id, mnemonic, severity, and what it checks. Generated from the code that runs, so it cannot drift from it.

## What it's for

A validator run tells you `V135 trailing_punct_mismatch: 2` and points at a findings CSV. That names the rule but does not explain it, and until September 2026 there was nowhere to look it up: the rules lived in five Python modules, and the pages in this section each described their own family in prose.

[**`QC/validation/RULES.md`**](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/RULES.md) is the missing index. It lists **every** rule the validators run — 95 as of October 2026 — with:

| Column | Meaning |
|---|---|
| **Rule** | The id you saw in the summary or the findings CSV (`V135`, `G012`). |
| **Mnemonic** | The short name printed beside it (`trailing_punct_mismatch`). |
| **Severity** | `HARD` gates the exit code; `SOFT` and `WARN` are reported and do not. |
| **Scope** | `file` — one XML file at a time. `corpus` — needs the whole collection, so it only runs on a full-corpus target. |
| **Checks** | One line on what the rule actually looks for. |

The tables are grouped by the validator that runs the rule, so you can also read it the other way: *what does `validate_glosses.py` check?*

## How it relates to the pages in this section

They answer different questions, and the catalogue is the authority on the first one.

- **"What is V135?"** → the catalogue. It is complete by construction, and a rule cannot exist without appearing in it.
- **"Why does this validator exist, when do I run it, what do the findings mean in practice?"** → the per-validator page — [validate_xml.py](validate-xml.md), [validate_text.py](validate-text.md), [validate_glosses.py](validate-glosses.md). These carry the reasoning, the worked examples, and the CLI.

The rule tables on those pages are written by hand and are illustrative, not exhaustive. Where one disagrees with the catalogue, the catalogue is right.

## How it stays honest

It is generated, never written:

```bash
python QC/validation/rules_catalogue.py           # regenerate RULES.md
python QC/validation/rules_catalogue.py --check   # exit 1 if it is stale
```

The generator imports each rule module and walks its `RULES` and `CROSS_FILE_RULES` lists — the same lists the validators execute — taking the id and mnemonic from each function's name and the description from the first line of its docstring. Severity comes from the module for `hard.py` / `soft.py` / `warn.py`, and from the docstring for `text.py`, `gloss.py` and `gloss_scrape.py`, which mix severities.

`tests/validators/test_rules_catalogue.py` runs `--check`, so **adding a rule without regenerating the catalogue fails CI**. That is the whole point: a hand-maintained list of rule ids goes stale the first time someone forgets it, which is exactly the failure that made the list worth having.

{% hint style="warning" %}
`RULES.md` is a generated file. Editing it by hand is wasted work — the next regeneration overwrites you, and in the meantime the test fails. To change what it says, change the rule's docstring or its `RULES` entry, then regenerate.
{% endhint %}

## Duplicate ids

The generator does not deduplicate. Two rules sharing an id makes every finding under it ambiguous in the findings CSV, which is a defect to surface rather than tidy away, so the catalogue carries a callout at the top listing any id claimed more than once, and the generator prints a warning.

There is one today: **`V070`** is claimed by both `validate_xml.py`'s `phon_placement` and `validate_glosses.py`'s `gloss_code_as_FORM`. They are different checks in different validators, and one of them needs renumbering. Rule ids appear in corpus READMEs and issue threads, so that has not been done unilaterally.

## Where the rules live

| Module | Runs in | Family |
|---|---|---|
| [`rules/hard.py`](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/rules/hard.py) | `validate_xml.py` | Schema and structure violations that gate CI |
| [`rules/soft.py`](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/rules/soft.py) | `validate_xml.py` | Structural review items |
| [`rules/warn.py`](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/rules/warn.py) | `validate_xml.py` | Advisory; reserved, currently empty |
| [`rules/text.py`](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/rules/text.py) | `validate_text.py` | Characters inside `FORM` and `TRANSL` |
| [`rules/gloss.py`](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/rules/gloss.py) | `validate_glosses.py` | Word- and morpheme-tier glossing |
| [`rules/gloss_scrape.py`](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/rules/gloss_scrape.py) | `audit_gloss_scrape.py` | Scrape-against-source audit (`G` ids) |

Adding a rule means adding the function to its module's `RULES` list and regenerating the catalogue. The [QC Pipeline overview](README.md) explains, under *The Finding / Severity framework*, what a rule returns.
