---
icon: circle-check
---

# validate_glosses.py

> The gloss-tier validator: checks the `W` (word) and `M` (morpheme) segmentation — counts, infix notation, clitic propagation, mandatory translations, and morpheme-to-word reconstruction — via the `V06x` rule family.

## What it's for

Only word-segmented corpora carry a `W`/`M` tier, and that tier has its own correctness conditions that the schema cannot express: word counts should match the sentence, morpheme counts should match the word's segmentation markers, infix morphemes need angle-bracket glosses, clitic boundaries must propagate from word to morpheme, and every morpheme needs a translation. `validate_glosses.py` checks all of these.

It is a **stage-2** validator that runs only on corpora with `W`/`M` segmentation. On an unsegmented corpus, `V060` would report every sentence's nonzero word count against zero `W` children, so the result would not be useful.

## How it works

The runner walks the selected target (file, directory, corpus, or language), parses each `.xml` with `lxml`, and applies the rules registered in [QC/validation/rules/gloss.py](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/rules/gloss.py). A file that fails to parse prints a warning to stderr and is skipped (it does **not** emit a `V000` finding the way `validate_xml.py`/`validate_text.py` do). The discovery helpers are imported from `validate_xml.py`, so the by-path/by-corpus/by-language targeting behaves identically.

Tiers read: `S` and its `FORM[@kindOf="original"]` (preferred for word counting), `W` and its preferred FORM (original > any FORM), `M` and its FORM/TRANSL children. Two rules (`V068`, `V060`'s sibling `V141` which lives in `validate_text.py`) use the letter-skeleton "reconstruction" helper in [rules/_reconstruct.py](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/rules/_reconstruct.py): it compares casefolded Unicode-letter multisets so infixes/circumfixes reconstruct perfectly and only genuine misalignment (children belonging to a different parent) drops the similarity below the `0.6` default threshold.

The module holds a **mix of HARD and SOFT severities** (unlike `rules/hard.py`/`rules/soft.py`, which are split by severity). Results flow through the shared `Finding`/`Severity` framework ([_finding.py](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/_finding.py)) and reporter ([_report.py](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/_report.py)): **HARD** drives exit 1, **SOFT** is informational. See the [QC Pipeline overview](README.md) for the severity framework.

### Rules

| Rule | Severity | Meaning |
|------|----------|---------|
| `V060` | SOFT | `W`-count under an `S` should match the whitespace word count of the `S` original FORM. |
| `V061` | SOFT | `M`-count under a `W` should match the morpheme count implied by the `W` FORM's segmentation markers (a monomorphemic `W` with 0 `M`s is fine). |
| `V062` | HARD | An `M` with infix-shaped FORM (`-X-`) requires the parent `W` to have a `TRANSL` carrying an angle-bracket gloss (`<…>`). |
| `V063` | HARD | When an `S` original FORM carries more than 3 segmentation markers, the `W` FORMs (each tier) must collectively retain at least half — catches a cleaner regression that stripped markers. |
| `V064` | HARD | Every `M` must have at least one `TRANSL` child (an unglossed morpheme is invalid). |
| `V065` | SOFT | Every `W` should have at least one `TRANSL` child. |
| `V066` | HARD | A `=` (clitic boundary) in a `W` FORM must also appear in at least one child `M` FORM. |
| `V067` | HARD | No `<`/`>` in any `M` FORM — infix `M`s must use the canonical `-X-` notation, not `<X>`. |
| `V068` | SOFT | The child `M` FORMs of a `W` should reconstruct (spell) the `W` FORM — flags likely morpheme misalignment. |

Note: the `S`->`W` reconstruction sibling `V141` lives in [validate_text.py](validate-text.md), not here. `V060` may also print a stderr warning when it finds nested (non-direct-child) `W` elements under an `S`.

### Legacy CSV artifacts (superseded)

The current findings CSV supersedes two legacy per-run files that the old gloss validator wrote: `validation_results.csv` and `validation_m_mismatches.csv`. Those re-parsed the finding `location` and truncated sentence/word ids at the first space (NTU filenames contain spaces). The single findings CSV now writes `location` verbatim, preserving ids intact.

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`. The validator uses the shared `search_by` positional — `by_path`, `by_corpus`, `by_language`.

```bash
# Validate one corpus's published XML by path (safest target)
python QC/validation/validate_glosses.py by_path --path Corpora/ePark/XML

# A single file
python QC/validation/validate_glosses.py by_path --path tests/fixtures/foo.xml

# By corpus name (walks <corpora_path>/<corpus>/XML/)
python QC/validation/validate_glosses.py by_corpus --corpus ePark --corpora_path Corpora

# By language code (every canonical file whose TEXT/@xml:lang matches)
python QC/validation/validate_glosses.py by_language --language ami --corpora_path Corpora

# Put the findings CSV in a chosen directory; print one debug line per finding
python QC/validation/validate_glosses.py by_corpus --corpus ePark --corpora_path Corpora \
    --output_dir logs --debug
```

| Flag | Default | Purpose |
|------|---------|---------|
| `--csv` | *(unset)* | Explicit path for the single findings CSV. Overrides `--output_dir`. |
| `--output_dir` | `logs/` (CWD) | Directory for the CSV when `--csv` is not given; the file is `validate_glosses_findings.csv`. Retained for the run-qc-pipeline skill and CI. |
| `--debug` | off | Print one `[rule_id] location: message` line per finding to stdout. |
| `--no-exit-on-hard` | off | Always exit 0, even with HARD findings. |

There is no `--check_morpho` flag in the current code (see note below).

## Output & exit codes

If no files match the selection, it prints `No XML files matched the selection.` and exits 0. Otherwise the terminal (stderr) shows the summary header and a per-severity, per-rule count summary with mnemonic titles (e.g. `V064 every_M_has_TRANSL: 3`). Per-finding detail goes to the findings CSV (resolved from `--csv`, else `<output_dir>/validate_glosses_findings.csv`), announced as `Details: <path>`. The CSV (UTF-8 with BOM) carries `file, line, severity, rule_id, title, location, language, character, count, message`, writing `location` verbatim.

- **HARD** findings cause exit code **1**.
- **SOFT** findings are reported and written to the CSV but never affect the exit code.
- **WARN** is unused by this validator.

`--no-exit-on-hard` forces exit 0 regardless.

## When to run it

Run `validate_glosses.py` **last** in the validator sequence, and **only for corpora that have `W`/`M` segmentation**. On an unsegmented corpus, `V060` produces expected but meaningless `W`-count mismatches. It assumes well-formed XML, so run [validate_xml.py](validate-xml.md) first; it also pairs naturally with [validate_text.py](validate-text.md), which owns the text-content `W`/`M` checks (parens/slashes, null propagation) and the `S`->`W` reconstruction rule `V141`.

## Related

- [QC Pipeline overview](README.md)
- [validate_xml.py](validate-xml.md)
- [validate_text.py](validate-text.md)
- [validate_dialect.py](validate-dialect.md)
- [Running an Audit](../running-an-audit.md)
- [Porting a Corpus In](../porting-a-corpus.md)
