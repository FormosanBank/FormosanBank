---
icon: layer-group
---

# standardize.py

> Creates the `FORM kindOf="standard"` sentence tier that the rest of the QC pipeline assumes — either as an exact copy of the original, or by applying a TSV transliteration mapping.

## What it's for

Most QC scripts expect every `<S>` to carry two sentence-level `FORM`s: `kindOf="original"` (the source spelling) and `kindOf="standard"` (FormosanBank's common orthography). Many corpora arrive with only the original tier. `standardize.py` builds the standard tier so orthography, punctuation, and metrics checks have a consistent target.

It has three modes:

- **`--copy`** — duplicate the original text verbatim into a new standard tier. This does **not** normalize spelling; it just guarantees the tier exists.
- **`--remove_accents`** — like `--copy`, but **deletes accents** from the standard tier (no TSV, no dialectal letter conversion). Use this when the dialect is unknown or mixed so a dialect-specific conversion table can't be chosen, but you still want an accent-free standard tier. Accent removal is dialect-independent, so it is safe without a conversion table — but it is **not** unconditional; see [Accents](#accents-are-stripped-unless-the-orthography-attests-them) below.
- **`--tsv_path`** — create the standard tier *and* apply a find-and-replace transliteration map, producing genuinely standardized spelling.

## How it works

For every `<S>` (matched as any element containing a `FORM` child) the script calls `create_standard`:

- If the element has no `FORM[@kindOf='original']`, it errors out and exits — there must be an original tier to standardize from.
- If a `FORM[@kindOf='standard']` already exists, its content is replaced; otherwise a new `FORM kindOf="standard"` element is inserted. Mixed content (notably inline `<UNCLEAR/>` markers) is deep-copied so it is not dropped.

In `--copy` mode that is the whole operation. In `--remove_accents` mode it additionally runs `apply_standard` with an **empty** mapping, which deletes accents but converts no letters. In TSV mode it runs `apply_standard` with the loaded map, converting the standard tier's text a rule at a time (an empty replacement deletes the matched string; see [How rules are applied](#how-rules-are-applied) for why order in the TSV does not matter).

### Accents are stripped unless the orthography attests them

**Accents are stripped before any mapping is applied** (in both `--remove_accents` and TSV modes). Most accents in a source text are prosody rather than spelling — Glosbe marks stress (`máduk`, `dálix`), and a Mandarin or Japanese word quoted inside a Formosan sentence brings its own diacritics with it. Those are the plain letter wearing a mark, and the standard tier drops the mark. `apply_standard` does this on the **standard** tier only: decompose to NFD, remove the marks in `_accents.ACCENTS_TO_STRIP` (the combining **acute**, **breve** and **macron**), recompose to NFC. In TSV mode this also guarantees a mapping entry keyed on the bare vowel still matches — without it a rule such as `us → os` would silently skip `ús`. The **original** tier is never touched; it keeps the source's exact spelling, accents and all. (`--copy` runs no `apply_standard` at all, so it preserves accents verbatim; use `--remove_accents` when you want a copy *with* accents removed.)

**But some accented letters are real letters,** and stripping their mark would merge two distinct graphemes — the same class of damage as conflating `tj` with `c`. Three languages in the bank spell with a macron, each contrastive against its bare base:

| Language | Letter | Where |
| --- | --- | --- |
| Puyuma (`pyu`) | `ē` | throughout; listed in `QC/validation/reference/Puyuma/` |
| Siraya (`fos`) | `ǣ` | Siraya Gospels, beside plain `æ` |
| Favorlang (`bzg`) | `ḡ` | Campbell Favorlang, beside plain `g` |

So stripping is filtered through a **keep set** — accented letters that survive because the language attests them as spelling:

- `standardize.py` builds the keep set per file from that language's (and, where given, that dialect's) reference orthography inventories under `QC/validation/reference/<Language>/`, the same data [validate_orthography.py](validate-orthography.md) scores against. It passes the set to `strip_accents` in **both** `--remove_accents` and TSV modes. This is what protects Puyuma's `ē` while still stripping the macron off a Mandarin loanword quoted in Paiwan.
- Some languages have **no reference orthography directory at all** — Siraya and Favorlang are documentary languages outside the 16 living Formosan languages, so there is nothing to derive a keep set from. Their letters live in **`QC/utilities/_accents.ALWAYS_KEEP`**, a small frozenset unioned into `keep` on *every* call to `strip_accents`, by every caller, regardless of language. It currently holds `ǣ` and `ḡ`.

**If you add a language, or hit a letter being flattened that shouldn't be:** first check whether the language has a reference orthography that lists the letter — that is the right fix, because it also feeds validation. Only if the language has no reference orthography at all does the letter belong in `ALWAYS_KEEP`, and it should be removed from there once one exists. Adding a mark to `ACCENTS_TO_STRIP` without checking which languages spell with it is how a real letter gets silently merged into its base.

**Choosing the TSV column.** The mapping TSV has an `original` column plus one or more value columns. The target column is resolved as follows:

- `--target_column` overrides everything.
- Otherwise, for **multi-dialect** languages (per `dialects.csv`), the file's `TEXT/@dialect` selects the column, falling back to a `standard` column (with a warning) or erroring if neither exists.
- For **single-dialect** languages, a `dialect`-named column is used if present, else the sole non-`original` column, else `standard`.

### How rules are applied

Replacements are literal — no regex, no word boundaries — but they are **not**
naively sequential, and **the order of rows in the TSV does not matter.**

Every rule is staged through a placeholder before any replacement text is
written back, longest source first. Two consequences, and they are the point:

- **A rule's output is never matched by another rule.** `Rukai_Church`'s
  `lh → l` used to become `lrh`, because the `l` it produced was then caught by
  `l → lr`. It now yields `l`.
- **A digraph beats a single letter regardless of row order.** `Puyuma_MinEd`
  writes `ll → ll` precisely to shield `ll` from `l → lr`; that idiom used to
  fail (`ll` came out `lrlr`) and now holds even though the short rule is listed
  first.

Generalizing the placeholder corrected **17 rules across five tables** —
`Amis_Church` `ng`, `Puyuma_Cauquelin` `L`/`ɭ`, `Puyuma_MinEd` `ll`,
`Rukai_Church` `lh`, and `Rukai_Li` `ə:`. None of those five was in use by a
published corpus. `tests/utilities/test_standardize_rule_application.py` now
asserts that every rule in every committed table produces exactly its own
replacement.

> **Corrected 2026-09-11.** This section, and POL-056 itself, said that *no
> published data changed*. That is not right. The check behind it swept the 342
> individual **symbols** in the committed tables, which cannot see a rule whose
> source another rule *produces*. `Yami_Wakelin_113` has both `ch → c` and
> `cy → ci`, and WakelinTexts — published, and table-driven — relied on the
> first feeding the second, so `chya` used to reach `cia` and afterwards stopped
> at `cya`. 29 standard FORMs and their 29 `PHON` values changed silently. The
> table now carries its own `chy → ci` row, which is what a set-of-rules table
> requires: every rule must say what it means on its own. When auditing a
> conversion table, test **chained** rules — does rule A's output match rule B's
> source? — and re-run the corpus's `generate_xml.sh`, since a symbol sweep will
> not catch it.

Two cell values are read specially, and they mean different things:

| cell | meaning |
| --- | --- |
| `NA` | the letter does not occur in this dialect — **not a rule at all** |
| empty | a rule that **deletes** the matched string (Bunun `w`, Sakizaya `x`, Wakelin `?`) |

Deletions are audited like any other rule. `validate_conversion_table.py` reports
each as a `deletion` and separates the two cases that decide whether it is
acceptable: a phoneme the target orthography **cannot** write has nowhere else to
go, while one it **could** have written is a real loss. `Yami_Wakelin_113` is the
live example — it deletes `?`, and Ortho113 Yami writes that phoneme as `'`.
Deletions never fail a run; they surface in the phoneme-level section of
`run_conversion_table_checks.py` for a human to judge.

Review the diff anyway.

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`.

```bash
# Copy mode: just create the standard tier (no spelling changes)
python QC/utilities/standardize.py \
  --copy \
  --corpora_path /path/to/corpus-or-Final_XML

# Accent-removal mode: create the standard tier as a copy with accents deleted
# (no TSV; for unknown/mixed-dialect corpora)
python QC/utilities/standardize.py \
  --remove_accents \
  --corpora_path /path/to/corpus-or-Final_XML

# Transliteration mode: create + standardize via a TSV map
python QC/utilities/standardize.py \
  --corpora_path /path/to/corpus-or-Final_XML \
  --tsv_path /path/to/orthography-map.tsv \
  --target_column standard
```

| Flag | Default | Notes |
| --- | --- | --- |
| `--copy` | off | Duplicate original → standard with no transformation. |
| `--remove_accents` | off | Duplicate original → standard, then delete accents (no TSV, no letter conversion). For unknown/mixed-dialect corpora. |
| `--tsv_path` | none | TSV with an `original` column and target column(s). |
| _(mode)_ | — | Exactly one of `--copy`, `--remove_accents`, or `--tsv_path` is required. |
| `--target_column` | auto | Force a specific TSV column; otherwise auto-detected from dialect/language. |
| `--corpora_path` | (required) | Corpora root, a single corpus dir, or a single `.xml` file. |
| `--corpus` | none | Restrict to one corpus under `--corpora_path`. |
| `--language` | none | Restrict to files whose path matches this language name. |
| `--hard-remove-segmentation` | off | C012: remove segmentation hyphens from the standard tier even where the language treats `-` as a letter. |
| `--ortho-path` | `Orthographies/Ortho113/` | Orthography profile directory used to decide whether `-` is a letter for the language. |

### Single-file wrapper

`standardize.py --corpora_path <file.xml>` can operate on one XML file directly. `QC/utilities/standardize_single_file.py` is still available as a wrapper for workflows that prefer an explicit `--xml_path`; it copies the file into a temp directory, invokes `standardize.py --corpora_path <tempdir> --tsv_path …`, then writes the result back. Flags: `--xml_path`, `--tsv_path`, `--target_column`. (It has no `--copy` mode.)

## Output & side effects

**Modifies XML in place.** Each processed file is re-serialized (pretty-printed, blank lines stripped) and overwritten, with a new `FORM kindOf="standard"` element added to every element that has an original FORM (S/W/M, not just sentence level). The serializer preserves inline mixed content, including text around `<UNCLEAR/>`, without inserting formatting whitespace into the tier. Always `git diff` before committing. In TSV mode especially, confirm the transliteration did what you expected.

## When to run it

Early in the pipeline, immediately after [validate_xml.py](validate-xml.md) and **before** text/orthography checks. Run `--copy` whenever a corpus has only one sentence-level `FORM` and its source spelling should be preserved as-is; run `--remove_accents` when the dialect is unknown or mixed and you just want an accent-free standard tier; run the TSV mode when an actual per-dialect transliteration map is available. See [Running an Audit](../running-an-audit.md) and [Porting a Corpus In](../porting-a-corpus.md).

## Related

- [QC Pipeline overview](README.md)
- [add_phonology.py](add-phonology.md)
- [orthography_extract.py](orthography-extract.md)
- [validate_text.py](validate-text.md)
- [validate_orthography.py](validate-orthography.md)
