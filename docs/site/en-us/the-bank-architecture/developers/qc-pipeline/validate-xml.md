---
icon: circle-check
---

# validate_xml.py

> The structural gatekeeper: validates each XML file against the canonical XSD plus a battery of Python `V0xx` schema/structure rules, and is the first stage every corpus must clear.

## What it's for

`validate_xml.py` answers one question: *is this file shaped like a FormosanBank corpus file?* It checks that the document root is `<TEXT>`, that required attributes (`xml:lang`, `dialect`) are present and well-formed, that the `FORM`/`PHON`/`TRANSL`/`AUDIO`/`W`/`M` tiers obey the constraints the XSD cannot express on its own, and that `id`s are unique within a file and across published corpora.

It is **stage 1** of the QC pipeline. Nothing downstream (text checks, orthography extraction, gloss checks) is meaningful on a file that is not structurally valid, so this runs first. It is the only validator that loads the XSD ([QC/validation/xml_template.xsd](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/xml_template.xsd)) directly.

## How it works

The runner walks a target (a path, a corpus, or a language), parses each `.xml` once with `lxml`, and applies the rules registered in [QC/validation/rules/hard.py](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/rules/hard.py) and [rules/soft.py](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/rules/soft.py). (`rules/warn.py` is registered but currently empty.) It runs in two passes: pass 1 applies per-file rules; pass 2 builds a `CorpusIndex` (collecting every `TEXT/@id` and `xml:lang` in the target plus every `TEXT/@id` in published `Corpora/`) and then applies the cross-file rules. A file that fails to parse is itself a HARD finding (`V000`, "XML parse error").

Every rule returns `Finding` objects (see [QC/validation/_finding.py](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/_finding.py)) carrying a severity. The shared reporter ([QC/validation/_report.py](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/_report.py)) turns them into a per-rule terminal summary and one findings CSV. **HARD** findings drive the exit code (exit 1); **SOFT** findings are informational only and never change the exit code; **WARN** is reserved but unused here. See the [QC Pipeline overview](README.md) for the Finding/Severity framework.

Tiers and attributes read: the document root `TEXT` (and its `xml:lang`, `dialect`, `id`, `audio` attributes); `FORM` elements and their `kindOf` (`original` vs `standard`); `PHON` and its `kindOf`; `TRANSL` and its `xml:lang`/`kindOf`/`ver`; `W` and `M` segmentation elements; and `AUDIO` with its `start`/`end`/`file`.

### HARD rules (drive exit code)

| Rule | Meaning |
|------|---------|
| `V000` | Parse failure, or any XSD schema violation (covers `FORM/@kindOf` and `PHON/@kindOf` enumerations, `AUDIO/@start`/`@end` numeric type, and in-file id uniqueness). |
| `V001` | The document root element must be `TEXT`. |
| `V011` | Every `W` must have at least one `FORM` child. |
| `V012` | Every `M` must have at least one `FORM` child. |
| `V013` | An `S` that has any `FORM` must have one with `kindOf="original"`. |
| `V015` | An `S` may have at most one `FORM` with `kindOf="original"`. |
| `V017` | Every `FORM` must have non-empty text. An `<UNCLEAR/>` child counts as content, and a wholly untranscribed audio-backed `S` is exempt. |
| `V022` | On an `M`, multiple `TRANSL kindOf="original"` must have distinct `xml:lang`. |
| `V023` | Every `TRANSL` must carry an `xml:lang`. |
| `V026` | `M`-level `TRANSL/@kindOf`, when set, must be `original` or `standard`. |
| `V035` | Every `xml:lang` must be a valid ISO 639-3 code (or the allow-listed `zh-Hans`); `TEXT` missing `xml:lang` also fires here. |
| `V036` | `TEXT/@dialect` is required and must be valid for the language (or `unknown`). |
| `V039` | `id` values must be unique across `S`/`W`/`M` within a file. |
| `V051` | `AUDIO/@file`, if present, must be non-empty. |
| `V052` | Single-file-mode `AUDIO` (no own `@file`) requires `start` and `end`. |
| `V053` | An `AUDIO` with no `@file` and no `TEXT/@audio` is an orphan. |
| `V054` | `AUDIO` `start` must be < `end`. |
| `V070` | `PHON` is only permitted under `S`, `W`, or `M`. |
| `V071` | `PHON/@kindOf`, when set, must be `original` or `standard`. |
| `V072` | At most one `PHON` per `kindOf` value per parent. |
| `V073` | `PHON` must have non-empty text (carve-outs: null-morpheme parents, `UNCLEAR` siblings, and wholly untranscribed audio-backed `S` elements). |
| `V084` | `TRANSL/@ver`, when set, must be in the allow-list (currently `{alt}`). |
| `V085` | Multiple same-`xml:lang` `TRANSL`s on one parent require at least one `ver` to discriminate them. |
| `V081` | **Cross-file:** a `TEXT/@id` must not collide with any `TEXT/@id` in published `Corpora/`. |

### SOFT rules (informational; never change exit code)

| Rule | Meaning |
|------|---------|
| `V010` | Count of `S` elements with no `FORM` child (e.g. diarized audio not yet transcribed). |
| `V014` | Count of `S`/`W`/`M` that have `FORM`s but none with `kindOf="standard"`. |

Files consumed: the canonical XSD, `QC/validation/iso-639-3.txt` (valid language codes), `dialects.csv` via the dialect inventory, and (for `V081`) the published `Corpora/` tree. Produces: one findings CSV plus the terminal summary.

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`. The validator uses the shared `search_by` positional with three modes — `by_path`, `by_corpus`, and `by_language`. Common flags may appear before or after the subcommand.

```bash
# Validate one corpus's published XML by path (safest target)
python QC/validation/validate_xml.py by_path --path Corpora/ePark/XML

# Validate a single file
python QC/validation/validate_xml.py by_path --path Corpora/ePark/XML/some_file.xml

# By corpus name (walks <corpora_path>/<corpus>/XML/)
python QC/validation/validate_xml.py by_corpus --corpus ePark --corpora_path Corpora

# By language code (every canonical file whose TEXT/@xml:lang matches)
python QC/validation/validate_xml.py by_language --language ami --corpora_path Corpora

# Write the findings CSV somewhere specific; don't fail the shell on HARD
python QC/validation/validate_xml.py by_path --path Corpora/ePark/XML \
    --csv logs/epark_xml.csv --no-exit-on-hard
```

| Flag | Default | Purpose |
|------|---------|---------|
| `--csv` (alias `--soft-csv`) | `logs/validate_xml_findings.csv` | Path for the single findings CSV (all severities). `--soft-csv` is deprecated. |
| `--published-corpora` | `<repo>/Corpora` | Published tree consulted for the `V081` cross-corpus id check. |
| `--no-exit-on-hard` | off | Always exit 0, even with HARD findings. |
| `--verbose` | off | Accepted but currently ignored (prints a note). |
| `--log_dir` | none | Accepted but currently ignored (prints a note). |

## Output & exit codes

The terminal (stderr) shows a header (`=== Validation summary: N files, M with issues ===`) followed by a per-severity, per-rule count summary with mnemonic titles (e.g. `V013 S_must_have_original_FORM: 4`). Per-finding detail is **not** printed; it goes to the findings CSV, whose path is announced as `Details: <path>`. The CSV (UTF-8 with BOM) carries `file, line, severity, rule_id, title, location, language, character, count, message` and is always written (header-only when clean).

- **HARD** findings cause exit code **1**.
- **SOFT** findings are reported and written to the CSV but never affect the exit code.
- **WARN** would log without affecting the exit code (no WARN rules registered here).

`--no-exit-on-hard` forces exit 0 regardless, for callers that depend on the legacy always-pass behavior.

## When to run it

Run `validate_xml.py` **first**, before any other validator or extraction step — the rest of the pipeline assumes structurally valid input. It has no prerequisites of its own. If a corpus lacks a `standard` tier, `V014` will flag it (SOFT); create the tier with [standardize.py](standardize.md) `--copy` before running the text/orthography stages, but `validate_xml.py` itself does not require it.

Next steps after a clean run: [validate_text.py](validate-text.md) for text-content checks, [validate_dialect.py](validate-dialect.md) to eyeball the dialect distribution, and [validate_glosses.py](validate-glosses.md) for word/morpheme-segmented corpora.

## Related

- [QC Pipeline overview](README.md)
- [validate_text.py](validate-text.md)
- [validate_dialect.py](validate-dialect.md)
- [validate_glosses.py](validate-glosses.md)
- [standardize.py](standardize.md)
- [Running an Audit](../running-an-audit.md)
- [Porting a Corpus In](../porting-a-corpus.md)
