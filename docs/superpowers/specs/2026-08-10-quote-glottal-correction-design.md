# `'`-as-quotation correction — design

**Date:** 2026-08-10
**Branch of origin:** `feature/quote-glottal-classifier`
**Status:** approved design, pre-implementation

## Problem

In most Formosan orthographies the apostrophe `'` is a **letter** (the glottal
stop: `'ayam`, `faloco'`, `romi'ad`). But some source texts also use `'` as a
**quotation mark**. Where a `'` is really a quotation mark, the `original` tier
should carry `"` instead, so that (a) the glottal-stop letter is unambiguous for
downstream phonology/orthography QC, and (b) real quotation is represented with
the project's quotation character.

We already have a classifier (`QC/utilities/classify_quotes.py`) that decides,
per `'`, whether it is a glottal stop, a quotation mark, or ambiguous, using a
TRANSL first pass plus dictionary-attestation/pairing logic. This project wires
that decision into the cleaning pipeline as an automated correction.

The classifier was validated on Amis: with translations available it resolves
98%+ of quote-bearing sentences, leaving a small, human-reviewable residual.
See the analysis that motivated this work — the residual ambiguity is
concentrated in untranslated long-prose corpora (Wikipedias).

## Goals

1. During `clean_xml` (before `standardize.py`), for each `original`-tier
   sentence FORM in a language whose orthography uses `'`:
   - `'` concluded to be **quotation** → rewrite to `"`.
   - `'` concluded to be **glottal** (incl. stranded) → leave as `'`.
   - `'` **ambiguous** → leave as `'`, raise a warning "in the normal way"
     (a `CleanerWarnings` row) for consideration during audits.
2. Deliver this **end-to-end for Amis** first, gated so other `'`-languages
   light up only as their dictionaries are generated.
3. Keep the source-tier mutation auditable: every `'`→`"` rewrite is logged.

## Non-goals

- The `standard` tier. `standardize.py` owns all `standard`-tier cleaning
  (C012 et al.); this correction runs earlier and touches only `original`
  (and, by inheritance, W/M FORMs, consistent with existing `clean_xml`
  handling — see "Tier scope" below).
- Generating attestation dictionaries for the other 14 `'`-languages and
  enabling them. The generator supports `--language <Name>`, but this project
  generates only Amis. Rollout is a follow-up, one language at a time.
- Re-deriving or re-tuning the classifier's decision rules. Its behavior is
  taken as given; this project reuses it.

## Components

### A. Classifier core (reused)

`QC/utilities/classify_quotes.py` already exposes the decision logic. This
project treats it as a stable import surface:

- `classify(form_text, dictionary) -> list[(index, outcome_label)]`
- `translation_confirms_glottal(form_text, transl_texts) -> bool`

Outcome labels map to three **actions**:

| Outcome label(s)                                   | Action        |
|----------------------------------------------------|---------------|
| `QUOTATION`                                         | rewrite `'`→`"` |
| `GLOTTAL_TRANSL`, `GLOTTAL_INTERNAL`, `GLOTTAL_BOUND_NO_MATCH`, `GLOTTAL_PAIR`, `STRANDED_GLOTTAL` | leave (glottal) |
| `AMBIGUOUS`                                         | leave + warn  |

The existing `main()` CLI (full-language audit runs) is retained.

No behavioral change to the classifier is in scope. If the import surface needs
minor tidying (docstrings, `__all__`), that is acceptable housekeeping.

### B. Per-language attestation dictionary (precomputed reference)

New generator: `QC/utilities/build_attestation_dict.py`.

- **Input:** `--language <Name>` (e.g. `Amis`), optional `--min-freq N`
  (default `3`), `--corpora_path` (default repo `Corpora/`).
- **Scan:** all `Corpora/*/XML` files whose TEXT `xml:lang` maps to `<Name>`.
  From each, collect sentence-level (`S`) FORMs of `kindOf` in
  `{original, standard}`.
- **Build set (casefolded):** union of
  1. **single-word S-FORMs** — a FORM whose text is a single whitespace-free
     token (the classifier's existing dictionary notion), and
  2. **interior tokens** — tokens that are neither sentence-initial nor
     sentence-final, punctuation-stripped, containing at least one letter/digit,
     appearing with frequency `>= min-freq` across the scanned FORMs.
- **Output:** newline-delimited, sorted, casefolded words to
  `QC/validation/reference/<Language>/attestation.txt` (one file per language;
  glottal words are shared across dialects, so this is **not** per-dialect).

This mirrors `/tmp/build_union.py` (the script that produced the validated Amis
`amis_attestation_union.txt`, 13,333 words) promoted to a checked-in tool.
Dictionaries are precomputed reference data, regenerated deliberately — not on
every clean run.

**Regeneration trigger.** The `port-corpus-in` skill gains a step after its
Phase 4 (validate-after-port): for each language the newly-ported corpus adds,
run `build_attestation_dict.py --language <Name>` to refresh
`reference/<Language>/attestation.txt` so it reflects the new data. The
generator is also runnable standalone at any time.

### C. `clean_xml` integration

Hook point: `analyze_and_modify_xml_file` in `QC/cleaning/clean_xml.py`, inside
the existing `for sentence in root.findall('.//S')` loop. The correction cannot
live inside `clean_text` (which is called with `lang="na"` and sees only one
text node); it needs the real `xml:lang` and the sentence's sibling TRANSLs.

Per-run setup (once):

1. Resolve the TEXT root's `xml:lang` → Language name. Reuse existing
   language-resolution logic where present (`QC/corpus_counts.py` maps
   `xml:lang`+`dialect` → language); for the correction we need only the
   language, not the dialect. If no clean reusable helper exists, add a small
   ISO-639-3 → Language map limited to `'`-languages.
2. Load `reference/<Language>/attestation.txt` into a set (casefolded), cached.
   **If the file does not exist, skip correction entirely for this file.**
   This missing-dict gate is what keeps the feature Amis-only now and rolls it
   out language-by-language as dictionaries are generated.

Per `original`-tier S-FORM (after the existing `clean_text` step, so all quotes
are already ASCII-normalized; before the `c022` `*` check):

1. Gather the sentence's TRANSL texts.
2. `translation_confirms_glottal(form_text, transls)` → if `True`, every `'` is
   glottal; no rewrite, no warning; skip the rest.
3. Otherwise `classify(form_text, dictionary)`; for each `(index, outcome)`:
   - `QUOTATION` → mark index for `'`→`"` rewrite.
   - `AMBIGUOUS` → warning (subject to Wikipedia suppression, §D).
   - glottal outcomes → nothing.
4. If any rewrite indices: rebuild the FORM text with `"` spliced at those
   indices, set `form_element.text`, `modified = True`, and record `'`→`"` in
   `TransformCounter` (count = number of rewrites).

### D. Warnings + Wikipedia fiat

Two new `CleanerWarnings` rule ids (per-occurrence rows: `rule_id, file, s_id,
character, position`):

- `c023` — **ambiguous** `'` (needs a human call during audit).
- `c024` — **corrected** `'`→`"` (records every original-tier mutation so
  auditors can see exactly where source spelling was changed, matching how
  `clean_xml` already logs HTML-entity rewrites).

**Wikipedia fiat.** For the Wikipedias corpus (target file path contains
`/Wikipedias/`): suppress `c023` — ambiguous `'` is treated as a glottal stop
silently, by fiat. Confident `QUOTATION` corrections still apply (and are still
logged as `c024`), though they are rare there because Wikipedia FORMs have no
TRANSLs. This is documented, not just coded: add to `Corpora/Wikipedias/
README.md` a note that ambiguous `'` is accepted as glottal for now and should
be revisited when a more complete dictionary is available.

### E. Tier scope

`clean_xml` already applies FORM cleaning to all non-`standard` FORMs, including
descendant W/M FORMs. The `'`→`"` correction likewise applies to `original`
sentence-level FORMs. Whether to also run it on W/M FORMs: **sentence-level
`original` FORM only** for this project — the classifier's TRANSL/pairing logic
is defined over a sentence, and W/M tiers are word/morpheme fragments where the
pairing geometry does not apply. W/M FORMs keep their existing punctuation/
Unicode cleanup but are not quote-corrected.

## Data flow

```
clean_xml.analyze_and_modify_xml_file(file)
  ├─ resolve xml:lang → Language
  ├─ load reference/<Language>/attestation.txt   (skip file if absent)
  └─ for each S:
       for each original sentence FORM (after clean_text):
         transls = S.TRANSLs
         if translation_confirms_glottal(form, transls):  # first pass
             leave all '
         else:
             for (i, outcome) in classify(form, dict):
                 QUOTATION  -> splice " at i ; log c024
                 AMBIGUOUS  -> log c023   (unless /Wikipedias/)
                 glottal    -> leave
         write back if modified
```

## Error handling

- **Missing dictionary** → skip correction for that language (documented gate),
  not an error.
- **Unparseable / non-TEXT file** → existing `clean_xml` behavior unchanged.
- **Language not resolvable from `xml:lang`** → skip correction (no dict lookup
  possible); do not raise.
- Rewrites operate on the already-`clean_text`-normalized string, so `'` are
  ASCII apostrophes and `"`/curly quotes are ASCII `"` before any counting.

## Testing

Reuse the existing 18 tests in `tests/utilities/test_classify_quotes.py`. Add:

- **Correction application:** a FORM with a `QUOTATION` pair → `"` spliced at the
  right indices; glottal `'` untouched; multiple corrections in one FORM.
- **Ambiguous → warning:** `AMBIGUOUS` outcome produces a `c023` row.
- **Wikipedia suppression:** same ambiguous FORM under a `/Wikipedias/` path
  produces **no** `c023` row; a `QUOTATION` there still produces `c024`.
- **TRANSL first pass integration:** a FORM whose TRANSL confirms glottal is
  left fully intact (no rewrite, no warning).
- **Missing-dict gate:** a language with no `attestation.txt` → FORM unchanged,
  no warnings.
- **Dictionary generator:** over a tiny fixture corpus, produces the expected
  single-word ∪ interior-freq set at the expected path; `--min-freq` honored.

## Deliverables

1. `QC/utilities/build_attestation_dict.py` (+ generated
   `QC/validation/reference/Amis/attestation.txt`).
2. `clean_xml.py` correction hook + `c023`/`c024` warnings + Wikipedia
   suppression.
3. `port-corpus-in` skill: post-Phase-4 dictionary-regeneration step.
4. `Corpora/Wikipedias/README.md`: by-fiat policy + revisit note.
5. Docs: `QC/README.md` pipeline note describing the new `clean_xml` behavior.
6. Tests as above.

## Post-approval additions (2026-08-10, both approved by the user)

After reviewing concrete cases, two behaviors were added to §A/§C/§D:

- **Gap 2 — closing quote after terminal punctuation.** A `'` that follows
  terminal punctuation (`. , ; : ? !`, optionally across a space) with nothing
  opening after it (`word.'`, `word. '`) now pairs with an earlier opener as a
  QUOTATION **closer**. Implemented via a new `follows_terminal`/`end_closer`
  signal in `_evaluate_pair`/`_classify_floating`/`_classify_bound`. (Reopened
  the classifier; done before it was in production, so no data was affected.)
- **Gap 1 — stranded-glottal whitespace repair.** A floating `'` separated from
  its word by whitespace that reattaches to exactly one attested word
  (`o ' ayam` → `o 'ayam`; `faloco ' iso` → `faloco' iso`) has the intervening
  space removed. New action, logged as a **`c025`** warning; `stranded_side()`
  exposes the reattachment direction.

Correction entry point is now
`apply_quote_corrections(form_text, transls, dictionary) -> (new_text, corrected, stranded, ambiguous)`.
Warning rules: `c023` ambiguous (Wikipedia-suppressed), `c024` `'`→`"`,
`c025` stranded repair. Implemented and tested in commit `04b3ca4a0`.

## Phase 2 additions (2026-08-10, approved by the user)

Prompted by four GLOSBE review sentences (U001038/U001319/U001404/U002127):

- **Guarded TRANSL-count quotation rule.** Complementary to the existing
  all-glottal first pass: when the S has TRANSL(s) and (TRANSL quote-mark count −
  FORM `"` count) = `need` > 0 and even, and there are ≥ `need` non-internal `'`
  candidates whose **outermost** `need` (first need/2 + last need/2) do NOT sit
  in an attested token, those outermost `'` become `"` and every other `'` is
  left glottal. This **overrides** the per-`'` classifier for that sentence,
  because the pairing misfires when the quoted span's boundary words themselves
  end in glottals (`Mafana'`, `riko'`). The attestation guard prevents false
  positives on genuine glottal-boundary sentences (`'ayam … faloco'`).
  Implemented as `_transl_quotation_targets` + a precedence branch in
  `apply_quote_corrections`.

- **Single-word-only attestation dictionary (default).** `build_attestation_dict`
  now defaults to **single-word S-FORMs only**; `--include-interior` re-adds the
  freq-based interior tokens. Interior tokens harvested from running text were
  polluted by unresolved quote-`'` (e.g. `'madimadiay`, `koli'` leaking in as if
  words), which defeated the attestation guard. Single-word entries are clean;
  coverage grows as dictionary entries are added. Amis regenerated 43,271 → 7,167.
  Together with the TRANSL rule, all four review sentences now auto-correct — no
  manual edits needed.

## Recoverability policy (non-regenerable corpora)

The `'`→`"` rewrite mutates the source-fidelity `original` tier. A *correct*
rewrite is punctuation normalization (allowed); a *wrong* one (glottal letter →
`"`) corrupts spelling, and an in-place rewrite is **not self-correcting** — a
later, better dictionary cannot reconsider a `'` that is already `"`.

- **Regenerable corpora** (a working reproduction pipeline in `CodeAndDocs/`,
  e.g. GLOSBE): no special action — each full pipeline run rebuilds the
  `original` tier from source and re-applies the correction with the current
  dictionary, so it self-corrects over time.
- **Non-regenerable corpora:** before first applying the correction, snapshot the
  pristine (pre-correction) XML into that corpus's `CodeAndDocs/` as the
  reproduction baseline, and document in the corpus README that reproduction
  starts from that snapshot. This re-establishes a "source" so the correction
  stays re-derivable with a better dictionary later. This is a per-corpus step
  performed when corrections are first run on real data (none have been yet).

Every rewrite is additionally logged (`c024`/`c025` in `cleaner_warnings.csv`,
committed for several corpora) and preserved in git history.

## Open decisions (resolved)

- Dictionary source: **precomputed reference file**, regenerated via the
  `port-corpus-in` skill (and standalone). ✔
- Wikipedia ambiguous: **suppressed in-tool** (glottal by fiat) + documented in
  README. ✔
- Scope: **Amis end-to-end first**; other languages follow as dicts are built. ✔
- Log every `'`→`"` correction as `c024`. ✔
- Threshold default `3`, exposed as `--min-freq`. ✔
