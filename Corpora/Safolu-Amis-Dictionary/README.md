# Safolu Amis Dictionary

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

The **Safolu (Tsai Chung-Han / 蔡中涵) Amis dictionary** from the g0v Amis Moedict
project, converted into valid FormosanBank XML.

| Field | Value |
| --- | --- |
| Type | Published FormosanBank corpus |
| Language | Amis (`ami`, glottocode `amis1246`, dialect `Coastal`) |
| Source | Safolu Kacaw Lalanges / 蔡中涵 dictionary, generated JSON in [g0v/amis-moedict](https://github.com/g0v/amis-moedict) `docs/s` (see https://amis.moedict.tw/) |
| Published XML | `XML/Amis/Safolu/amis_safolu_examples.xml` |
| Reproduction | `CodeAndDocs/make_xml.sh` — the single entry point (add `--from-source` to rebuild from upstream instead of the committed baseline) |

## Data shape

A single `TEXT` root with **49,181** `S` children (example sentences). Each
sentence has:

- `FORM kindOf="original"` — the source text (already in the Ortho113 letter
  set; `'` and `^` are distinct letters: `'` → ʡ, `^` → ʔ).
- `FORM kindOf="standard"` — the common-orthography tier (copy of original
  with accents removed; no transliteration is needed).
- `PHON kindOf="original"` and `PHON kindOf="standard"` — IPA generated from
  the like-named FORM via `Orthographies/Ortho113/Amis.tsv` (Coastal column).
  **Both** tiers use Ortho113: the source spelling already is the Ortho113
  letter set, so there is no separate source orthography to phonologize
  against. Phonemic variants use the `[x|y]` notation (e.g. `o` → `[o|u]`,
  `d` → `[ɬ|ɮ]`); punctuation is not carried into PHON; characters outside
  the Ortho113 inventory become `*`. Because the standard FORM here is the
  original FORM (nothing to transliterate, no accents in the source), the two
  PHON tiers are currently identical string-for-string; they are generated
  independently from their own FORM and will diverge if a future correction
  separates the tiers.
- `TRANSL xml:lang="zho"` — when the source provided a Chinese translation
  (**48,912** sentences; the remaining 269 are valid FORM-only).

No `W`/`M` segmentation — the Moedict examples carry no source-attested word
or morpheme tiers. Hyphens appearing in FORMs (e.g. `Kofit-19`, `si-fu`) are
source content (loanword/name compounds), not segmentation.

## Reproduction

### Canonical: regenerate `XML/` from the committed baseline

The full from-source build needs network access to fetch the upstream
checkouts (they are not committed), so the reproduction baseline is the
pristine pre-correction snapshot at `CodeAndDocs/pre_correction_snapshot/`
(taken 2026-08-12, before automated corrections first touched this corpus;
it changes only via committed scripts).

```sh
Corpora/Safolu-Amis-Dictionary/CodeAndDocs/make_xml.sh
```

runs, in order:

0. restore `XML/` from the snapshot;
1. `QC/cleaning/clean_xml.py` — original-tier cleaning (typography
   canonicalization, entity/width normalization) plus the automatic Amis
   **apostrophe/quotation disambiguation** (see Notes);
2. `QC/utilities/standardize.py --remove_accents` — create
   `FORM kindOf="standard"` (copy of original, accents stripped);
3. `QC/utilities/add_phonology.py --orthography Ortho113` — regenerate
   **both** `PHON kindOf="original"` (from the original FORM) and
   `PHON kindOf="standard"` (from the standard FORM), each with the Ortho113
   Amis table, Coastal column. `--orthography` is what turns on original-tier
   PHON; pointing it at `Ortho113` is correct here because the source
   orthography is Ortho113. `--preserve-existing-original` is deliberately
   not used — this corpus has no expert-supplied source PHON to protect;
4. `QC/cleaning/remove_duplicate_sentences.py --apply` — dedup (this is a
   reference resource, so it is duplicate-free by declaration; leftover
   duplicates are HARD `validate_duplicate_sentences` findings). Distinct
   translations of a removed duplicate are merged into the survivor as
   `ver="alt"` TRANSLs.

The pipeline is deterministic and idempotent (repeated runs are
byte-identical). Warning sidecars (`cleaner_warnings.csv`,
`standardize_warnings.csv`) are per-run reports — review and delete, never
commit. `CodeAndDocs/quote_corrections.csv` is the durable
quote-correction log — commit it when a run adds rows.

### From source (needs network)

```sh
Corpora/Safolu-Amis-Dictionary/CodeAndDocs/make_xml.sh --from-source
```

Same script, same enrichment steps — only the baseline differs. It clones
the pinned `g0v/amis-moedict` (`docs/s`) + `miaoski/amis-safolu` checkouts
into `_sources/`, rebuilds the **original tier** into `Final_XML/`,
validates it and runs the source-coverage audit, then applies enrichment
steps 1–4 to that build. (There is no `Makefile`: the build/validate targets
and the QC recipe both live in `make_xml.sh`, so there is exactly one
command to know.) The build scripts resolve their working tree (`_sources/`,
`Final_XML/`, `data/`) relative to the corpus root, so they run correctly
from the published layout regardless of the caller's working directory.
`Final_XML/` is a scratch build tree — compare it against `XML/` before
promoting anything. Pinned source commits live in
`CodeAndDocs/fetch_sources.py`; see
`CodeAndDocs/SOURCE_AUDIT.md` for the source mapping, recovery/repair rules,
and coverage accounting (every source example field is represented by ≥1
sentence or listed in the rejected audit). The canonical, QC'd copy is the
one committed under `XML/`.

## Notes for data users

- **Apostrophe/quotation disambiguation**: `'` is a letter (glottal ʡ) in
  this orthography, and single quotes are never quotation marks in
  FormosanBank text. `clean_xml` runs an automatic, dictionary-backed
  disambiguation over Amis original FORMs that rewrites apostrophe pairs
  acting as quotation marks to `"…"`. It can have **false positives and
  will certainly miss some cases**; every rewrite is logged with
  form_before/form_after in `CodeAndDocs/quote_corrections.csv` (no rewrites
  have fired on this corpus to date; ambiguous positions are flagged in the
  per-run `cleaner_warnings.csv`).
- A dozen rows carry stray OCR-era characters faithful to the source
  (e.g. `mafutiۥ`, `cangaw﹑fiting`, `Angah‧Alimol`) — SOFT `validate_text`
  findings (V116), not auto-corrected.
- 574 sentences contain parentheses or slashes (V122 SOFT), mostly source
  variant/alternative annotations (e.g. `nanom (nanum)`) in FORM or TRANSL —
  a standing review worklist (POL-026/POL-027), preserved as-is.
- 48 standard FORMs contain a hyphen (V133 SOFT) — source-faithful compound
  hyphens in an unsegmented corpus, not segmentation leftovers.
