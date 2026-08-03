---
icon: circle-check
---

# validate_text.py

> The text-content validator: checks the actual characters inside `FORM` and `TRANSL` elements — smart quotes, stray punctuation, non-ASCII, leftover segmentation markers, and null-symbol propagation — using the `V1xx` rule family.

## What it's for

Where [validate_xml.py](validate-xml.md) checks that a file is *shaped* correctly, `validate_text.py` checks that the *text inside* the elements is clean. It catches the residue that survives ingestion and cleaning: curly smart quotes, doubled punctuation, footnote leaks from scraped sources, parentheses and slashes that need review, leftover `=` clitic markers, and inconsistent use of the null symbol `∅` across tiers.

It is **stage 2** of the QC pipeline and consolidates two retired single-purpose scripts: the legacy `validate_punct.py` (punctuation checks, now `V110`–`V115`) and `non_ascii_counts.py` (non-ASCII counting, now `V116`). It assumes its input is already well-formed XML — run [validate_xml.py](validate-xml.md) first.

## How it works

The runner uses the same shape as `validate_xml.py`: walk a target (path/corpus/language), parse each `.xml` once with `lxml`, and apply the rules in [QC/validation/rules/text.py](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/rules/text.py). All `text.py` rules are per-file (there are no cross-file text rules). A parse failure is itself a HARD `V000` finding.

Tiers read: `FORM` (distinguishing `kindOf="original"` vs `kindOf="standard"`) and `TRANSL`. Many rules are scoped deliberately — for example several only inspect the `S`-level **standard** FORM (the project's canonical surface text), while the non-ASCII check skips the `original` tier entirely because that tier is source-faithful by policy and legitimately carries annotation characters. Results flow through the shared `Finding`/`Severity` framework ([_finding.py](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/_finding.py)) and reporter ([_report.py](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/_report.py)): **HARD** drives exit 1, **SOFT** is informational only. SOFT rows pin each occurrence to its `S`/`W`/`M` id and source line in the CSV. See the [QC Pipeline overview](README.md) for the severity framework.

### HARD rules (drive exit code)

| Rule | Meaning |
|------|---------|
| `V120` | Null symbol `∅` in an `S`-level standard FORM (unresolved elision marker). |
| `V123` | Null in a `W`/`M` standard FORM must also appear in that element's sister `original` FORM. |
| `V124` | Null in an `M` FORM must propagate up to the parent `W` FORM **and** the `S`-level original FORM. |
| `V125` | Null in a `W` FORM must appear in some child `M` FORM **and** the `S`-level original FORM. |
| `V127` | Smart-quote characters (curly quotes, Chinese corner/angle brackets) in any FORM, either tier. |
| `V128` | C0 control characters (`<0x20` except tab/newline/CR) in FORM or TRANSL. |
| `V129` | `*` (asterisk) in any FORM, either tier. |
| `V130` | Leading/trailing whitespace in a FORM (carve-out for `UNCLEAR` mixed content). |
| `V131` | Zero-width or BOM characters (`U+200B`/`U+200C`/`U+200D`/`U+FEFF`) in FORM or TRANSL. |
| `V140` | Null in an `S`-level original FORM must propagate down to a child `W` (and that `W` to a child `M`). |

### SOFT rules (informational; never change exit code)

| Rule | Meaning |
|------|---------|
| `V110` | Smart quotes in `S`-standard FORM. |
| `V111` | Imbalanced ASCII parentheses in `S`-standard FORM. |
| `V112` | Repeated terminal punctuation (`??`, `!!`) in `S`-standard FORM. |
| `V113` | Two or more consecutive dashes in `S`-standard FORM. |
| `V114` | Two or more consecutive spaces in `S`-standard FORM. |
| `V115` | Mismatched smart-quote pairs in `S`-standard FORM. |
| `V116` | Non-ASCII characters in FORM (excluding CJK and the language's orthography letters; skips `original` tier). |
| `V122` | Parentheses or `/` anywhere in FORM or TRANSL. This is review-only so source records are not rejected solely for these characters. |
| `V126` | `=` (leftover clitic marker) in `S`-standard FORM. |
| `V132` | HTML entity-like residue (`&amp;`, `&lt;`, …) in FORM or TRANSL — likely double-encoded source. |
| `V133` | `-` (leftover segmentation marker) in `S`-standard FORM. |
| `V134` | `<` or `>` in an `S`-level FORM, either tier. |
| `V135` | Trailing-punctuation mismatch between the `S` original and standard tiers. |
| `V136` | Mixed Latin/Cyrillic/Greek scripts (confusables) in a FORM. |
| `V137` | Footnote-like substrings (`.<digits>`, `<letter><digits>`) in FORM/TRANSL (skips `W`/`M`-level TRANSL gloss codes). |
| `V138` | Superscript-digit footnote (`¹²³…`) in FORM or TRANSL. |
| `V139` | Bracketed-digit footnote (`[1]`) in FORM or TRANSL. |
| `V141` | The child `W` FORMs of an `S` should reconstruct (spell) the `S` original FORM — flags likely word-tier misalignment. |

Files consumed: per-language orthography tables under `Orthographies/**/<Lang>.tsv` (so `V116` can exempt legitimate orthographic letters). Produces: one findings CSV plus the terminal summary.

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`. The validator uses the shared `search_by` positional — `by_path`, `by_corpus`, `by_language` — and common flags may appear before or after the subcommand.

```bash
# Validate one corpus's published XML by path (safest target)
python QC/validation/validate_text.py by_path --path Corpora/ePark/XML

# A single file
python QC/validation/validate_text.py by_path --path Corpora/ePark/XML/some_file.xml

# By corpus name (walks <corpora_path>/<corpus>/XML/)
python QC/validation/validate_text.py by_corpus --corpus ePark --corpora_path Corpora

# By language code (every canonical file whose TEXT/@xml:lang matches)
python QC/validation/validate_text.py by_language --language ami --corpora_path Corpora

# Custom CSV path; don't fail the shell on HARD findings
python QC/validation/validate_text.py by_path --path Corpora/ePark/XML \
    --csv logs/epark_text.csv --no-exit-on-hard
```

| Flag | Default | Purpose |
|------|---------|---------|
| `--csv` (alias `--soft-csv`) | `logs/validate_text_findings.csv` | Path for the single findings CSV (all severities). `--soft-csv` is deprecated. |
| `--no-exit-on-hard` | off | Always exit 0, even with HARD findings. |
| `--verbose` | off | Accepted but currently ignored (prints a note). |
| `--log_dir` | none | Accepted but currently ignored (prints a note). |

## Output & exit codes

The terminal (stderr) prints the summary header followed by a per-severity, per-rule count summary with mnemonic titles (e.g. `V120 null_in_S_standard: 2`). Per-finding detail goes to the findings CSV, announced as `Details: <path>`. The CSV (UTF-8 with BOM) carries `file, line, severity, rule_id, title, location, language, character, count, message`; SOFT rows include the offending `location` and source `line`. It is always written, header-only when clean.

- **HARD** findings cause exit code **1**.
- **SOFT** findings are reported and written to the CSV but never affect the exit code.
- **WARN** is unused by this validator.

`--no-exit-on-hard` forces exit 0 regardless.

## When to run it

Run `validate_text.py` **after** [validate_xml.py](validate-xml.md) passes — it assumes well-formed XML. It works best once a `standard` tier exists, because most of the HARD and many SOFT rules target the standard tier specifically; if a corpus has only an `original` tier, create the standard tier first with [standardize.py](standardize.md) `--copy` (note that `--copy` does not transliterate — it just duplicates so the standard-tier rules have something to inspect). For word/morpheme-segmented corpora, follow with [validate_glosses.py](validate-glosses.md).

## Related

- [QC Pipeline overview](README.md)
- [validate_xml.py](validate-xml.md)
- [validate_glosses.py](validate-glosses.md)
- [standardize.py](standardize.md)
- [orthography_extract.py](orthography-extract.md)
- [Running an Audit](../running-an-audit.md)
