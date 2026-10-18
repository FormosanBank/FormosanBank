---
icon: table-list
---

# Single sources of truth

> Language, dialect, and orthography identity each come from exactly one file, loaded through exactly one loader. POL-039: data that critical steps depend on is never hardcoded inside a Python file.

## What it is

Four repo-root registries and three reference trees:

| File | Answers |
|---|---|
| `languages.csv` | ISO 639-3 code → language name. |
| `dialects.csv` | Which dialects a language has, with Chinese names and glottocodes. |
| `standards.csv` | Which standard orthography each language uses. |
| `QC/validation/iso-639-3.txt` | Which codes are valid ISO 639-3 at all. |
| `QC/validation/xml_template.xsd` | The XML schema (the `.dtd` is a retained fallback only). |
| `QC/validation/reference/<Language>/` | Reference orthographies and vocabularies the validators consume. |
| `Orthographies/ConversionTables/` | Per-scheme transliteration tables. |

`languages.csv`, `dialects.csv` and `standards.csv` name languages **identically** — that shared spelling is what lets the three join.

## Why it exists

POL-039 was raised by a concrete failure: four separate hardcoded copies of the code→language table had drifted apart, one containing `bzg` and another `pzh`. The rule that came out of it is that lookup tables live in prominent human-readable files and are loaded through one function, so drift becomes impossible rather than merely unlikely.

{% hint style="danger" %}
**`trv` means Seediq-or-Truku, never just Truku.** ISO 639-3 has a single code for the whole Seediq family, so every Seediq *and* Truku text is tagged `xml:lang="trv"`. Language identity comes from the `dialect` attribute: `trv` + `dialect="Truku"` → Truku; anything else, including no dialect, → Seediq.

This is not a nicety. It selects which reference materials apply (`reference/Truku/` vs `reference/Seediq/`), which conversion-table column is used, and which attestation dictionary. Reading `trv` as "Truku" from the code alone produces confidently wrong output — `Corpora/Wikipedias/XML/Seediq/` is `trv`, and it is the *Seediq* Wikipedia. There is no Truku Wikipedia.
{% endhint %}

## Who reads it

`QC/corpus_counts.load_language_codes()` is the one loader for `languages.csv`; every other consumer imports it rather than reading the file. The same `corpus_counts` module resolves the `trv` + dialect rule, which is why token counts, statistics, and the documentation site all agree on what a language is.

## How it's enforced

`validate_registries.py`, in the `conversion-tables` workflow:

- **V150** — every language in `languages.csv` has a `standards.csv` row.
- **V155** — `dialects.csv` ↔ `languages.csv` naming agrees; ISO codes are unique and lowercase.

Both are **SOFT** per POL-034: registries may be legitimately out of sync mid-migration, so they report rather than block.

{% hint style="info" %}
Per POL-034 these content findings never fail the build. The job *does* gate on a structurally broken registry — one that is missing, or not readable as UTF-8 — which is a separate `return 1` in the script. Read the step summary for the findings; trust the red/green only for the structural case.
{% endhint %}

`xml:lang` values are validated against `iso-639-3.txt` by `validate_xml.py`, which *is* blocking.

## How to change it correctly

**Adding a language** is three rows, not one:

1. A `languages.csv` row (ISO code + name).
2. A `standards.csv` row — leave the scheme blank until a standard is designated.
3. `dialects.csv` rows, if the language is multi-dialect.

Then add `QC/validation/reference/<Language>/` if validators should check its orthography or vocabulary, and keep it in step with `Orthographies/` — see [Language reference data](language-reference-data.md) for the attestation dictionary and phonology sidecar that live there. The end-user-facing description lives on the [Formosan Dialects](../../formosan-dialects.md) page.

**Never** add a fourth copy of a lookup table to a Python file. If a script needs a mapping these registries don't carry, the answer is a new column or a new registry — not a dict literal.

```bash
source .venv/bin/activate
python QC/validation/validate_registries.py --csv logs/registry_findings.csv
```
