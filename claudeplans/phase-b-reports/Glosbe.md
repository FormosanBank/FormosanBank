# Glosbe regeneration: full diff vs `main` (Phase B sweep turn, REDO 2026-08-11)

Branch `sweep/g1-glosbe`, reset to the sweep tip (12455366f) and rerun from
pristine XML under the 2026-08-11 maintainer rulings. Supersedes the round-1
report of the same date; round 1's diff-classification framework and
quote-correction cross-reference carry over and were re-verified against this
run's output.

## Rulings applied in this redo

1. **Known false positives accepted** ("we are very far from perfect on
   this"): the 4 flagged sentences from round 1 (2 definite FPs, 1
   likely-wrong pair member, 1 under-correction) re-fired identically and
   are **kept** — no exclusions, no hand fixes. The cross-reference analysis
   below documents them.
2. **README notes for data users**: the readme now states plainly that
   apostrophe-vs-quotation disambiguation in the Amis data was automatic,
   that occasional false positives are possible and misses are certain, and
   that corrections are logged with before/after text in
   `CodeAndDocs/quote_corrections.csv`. **At merge time the same text goes
   onto the GitBook Glosbe corpus page** (not touched here).
3. **`quote_corrections.csv` lands in `CodeAndDocs/`** (the code now
   resolves the log there — never inside `XML/`) with
   `form_before`/`form_after` columns. Committed (170 lines: header + 169
   rows).
4. **`CodeAndDocs/make_xml.sh` created**: the post-scrape pipeline (clean →
   per-language standardize → per-language add_phonology) as one
   parameterized script (`BANK` root + `PYTHON` overrides), per-step
   explanations kept, **no** apply_manual_edits step (no manual edits
   exist). Documented in the readme ("Rebuilding the XML"). This run was
   executed through it.
5. **README content policy**: rewritten to current pipeline +
   data-user-relevant notes only (no sweep narrative, no project-wide-rule
   explanations, no V-rule numbers).

## POL-035 snapshot: SNAPSHOT TAKEN

The readme's Reproducibility section states the initial scrape is **not**
reproducible from this checkout (raw 2026 crawl cache and `.jsonl` sidecars
unpublished; dev repo deprecated). Quote correction rewrites the Amis
original tier, so the pristine `XML/` was copied to
`CodeAndDocs/pre_correction_snapshot/` (8 files) **before** cleaning, and
the readme documents it. Committed with this branch.

## Pipeline run

`PYTHON=<venv> Corpora/Glosbe/CodeAndDocs/make_xml.sh`:

1. `clean_xml.py` over `XML/` — quote–glottal correction armed for Amis
   (hand-validated, edge-filtered dictionary, 505 entries), Atayal (1,053),
   Saisiyat (584); Truku disarmed (dictionary deleted by the edge-filter
   ruling).
2. `standardize.py` per readme: ami `Amis_94_113.tsv`/Coastal, tay
   `Atayal_Church_113.tsv`/standard, trv `Seediq_94_113.tsv`/Truku, xsy
   `Saisiyat_94_113.tsv`/standard.
3. `add_phonology.py` per readme: ami Ortho94/Coastal, tay Church, trv
   Ortho94, xsy Ortho94.

No apply_manual_edits step (no `CodeAndDocs/manual_edits.xml` exists).

## Comparison scope

All 8 XML files parsed on both sides; identical S inventories (no S added or
removed; ids unchanged — POL-037 safe): ami 6,484, tay 523, trv 112, xsy 490.
No TRANSL changed anywhere. No attribute changed. 7 files differ
(`Glosbe_tay_eng_tmem.xml` is byte-identical). **Total changed element
values: 13,413 — 100% classified. UNEXPLAINED: none.**

Token count (corpus counting rules): before = after = **91,202**
(ami 89,909 / tay 577 / trv 116 / xsy 600). **Delta 0.**

## Diff classification (counts per language)

### FORM original — 153 changes (all ami)

| category | count | detail |
|---|---|---|
| quote correction (c031/c032) | 84 sentences | 169 apostrophes rewritten `'`→`"` (168 c031, 1 c032 destrand in `GLOSBE_ami_zho_TMEM_U001234`); logged in committed `CodeAndDocs/quote_corrections.csv` |
| dash canonicalization | 69 | `—`→`-` ×66, `–`→`-` ×3; all in ami tmem files |

### FORM standard — 153 changes (all ami)

| category | count | detail |
|---|---|---|
| quote correction propagated | 84 | standard tier rederived from corrected originals |
| dash canonicalization | 69 | same sentences as the original-tier dashes |

(No accent-strip or u→o deltas: the published standard tier already carried
those; rederivation reproduced it byte-identically elsewhere.)

### PHON — 13,107 changes

| category | ami orig | ami std | tay orig | tay std | trv std | xsy orig | xsy std | why expected |
|---|---|---|---|---|---|---|---|---|
| legacy `x~y` → `[x\|y]` notation only | — | 238 | — | 135 | — | 129 | 129 | variant-notation migration; letters identical |
| notation + punctuation dropped | 6,061 | 6,054 | 3 | 3 | — | 5 | 5 | new `phonologize` drops unmapped punctuation; letters verified identical via letter-skeleton comparison |
| quote-corrected sentence regen | 84 | 84 | — | — | — | — | — | the `'`→`"` rewrite removes the corresponding `ʡ` (incl. U001234's floating destranded `ʡ`) |
| `*` unknown-char artifact fixed | 83 | 83 | — | — | — | — | — | old tokenizer emitted `n*` where `ng` failed longest-grapheme match (now `ŋ`, e.g. `fan*ʦaɾaj`→`faŋʦaɾaj`) and lone `*` for unmapped punctuation now simply dropped; digit-derived `*` runs remain by design |
| Truku dialect-rule update | — | — | — | — | 11 | — | — | see below |

Column totals: ami 6,228 orig + 6,459 std; tay 3 + 138; trv 0 + 11;
xsy 134 + 134 = **13,107** ✓. 153 + 153 + 13,107 = **13,413** ✓.

Reconciliation with round 1: every per-language/per-tier column total is
identical to round 1's. Within ami, this redo's classifier draws the
boundary between "punctuation dropped" and "`*` artifact fixed" differently
(round 1: 6,129/15 orig; here: 6,061/83 — the 68-row difference is PHONs
where a starred unmapped char sits alongside dropped punctuation); the union
of the two letters-preserving categories is unchanged.

**Truku standard-PHON changes (ruling wording):** the 11 trv changes are the
dialect-scoped sidecar rules in `Orthographies/Ortho113/Seediq.rules.tsv` —
**"i lowers to [e] before/after h,q"** (`i(?=[ħq])→e`, `(?<=[ħq])i→e`,
dialect=Truku) — producing `e` where the old pipeline wrote `ə` (10 values,
e.g. FORM `ahing`: `aħəŋ`→`aħeŋ`; FORM `puniq`: `punəq`→`puneq`), plus one
syllabic-mark simplification `m̩`→`m` (FORM `mbanah`). This is **not** a
letter-e remap: it is the source letter `i` adjacent to `h`/`q` now
receiving its ruled [e] realization.

## Quote corrections — volume and match vs round 1

**Production corrections: 84 sentences, 169 rows (168 c031 + 1 c032) —
byte-for-byte the same sentence set and rule signature as round 1**
(verified: identical 84 ids; only `GLOSBE_ami_zho_TMEM_U001234` carries a
c032). Log now in `CodeAndDocs/quote_corrections.csv` with
`form_before`/`form_after` columns.

Cross-reference against `quote_review_nonwiki_amis.md` (carried over from
round 1; the correction set is identical so the analysis re-applies
unchanged):

- **16** corrected sentences match reviewed QUOTATION candidates — expected.
- **51** match reviewed AMBIGUOUS entries ("need a human call") — each was
  read against its TRANSL in round 1; all but the 4 below are clean
  TRANSL-confirmed quotations.
- **17** are NOT in the review file (12 eng + 5 zho) — individually
  justified in round 1; every one is a TRANSL-confirmed quotation. (The
  review pass used the 13,333-entry union dictionary and a different
  first-pass classifier; the 5 zho rows additionally carry `14 `/`15 `-style
  prefixes the review file's source rows lacked.)
- **8** distinct reviewed QUOTATION forms were NOT corrected (conservative
  misses, acceptable by design): `GLOSBE_ami_eng_TMEM_U001682` and review
  ids Amis_1671, Amis_2535, Amis_3211, Amis_3686, Amis_4392, Amis_5099,
  Amis_5333 (zho-side stranded-opener patterns the destrander didn't
  reach). Their apostrophes remain glottal-assumed.

### Known imperfections — ACCEPTED per the 2026-08-11 ruling

These re-fired identically and are kept as-is ("we are very far from
perfect on this"); the readme's data-user notes cover the possibility, the
pristine text is in `CodeAndDocs/pre_correction_snapshot/`, and every
rewrite is row-logged with before/after:

1. `GLOSBE_ami_eng_TMEM_U001286` — false positive: glottal of `mipaino'`
   became `"`; the true closer survives as `,'`.
2. `GLOSBE_ami_eng_TMEM_U001294` — false positive: glottal of `ilaloma'`
   became `"`; true closer `.'` stranded.
3. `GLOSBE_ami_zho_TMEM_U001790` — likely wrong member of the double
   apostrophe in `a''odingaray`; leaves `a'"`.
4. `GLOSBE_ami_zho_TMEM_U001443` — under-correction: opener/closer of two
   quoted phrases paired across the phrases; inner pair remains `'`.

Watch item (plausible either way): `GLOSBE_ami_eng_TMEM_U003989` `siri'`→
`siri"` (union dict attests both `siri` and `siri'`).

### Per-language outcome vs Phase A predictions

| language | Phase A prediction | measured |
|---|---|---|
| Amis | corrections expected (review worklist applies here) | 84 sentences / 169 rows |
| Atayal | armed, 0 | 0 ✓ |
| Saisiyat | armed, 0 | 0 ✓ |
| Truku | disarmed, vacuous 0 (0 apostrophes) | 0 evaluations ✓ |

(The full 84-sentence inventory with per-sentence review status is in the
round-1 report; the sentence set here is identical, and the row-level log is
the committed CSV.)

## Validators

- `validate_xml`: **clean before, clean after** (8 files, 0 issues).
- `validate_text` (all SOFT, no HARD either side): 8,589 → **1,764**.
  - phon_legacy_tilde_variant 6,819 → **0** (sweep target met).
  - non_ascii_in_form 79 → 6 (dashes gone; remaining are pre-existing `®`,
    `ā`×2, `ṣ`, `ʔ`, `æ` — standing worklist items, untouched by design).
  - dash_in_S_standard_FORM 45 → 112 (em/en dashes canonicalized to `-` are
    now visible to the dash rule; same underlying sentences, SOFT worklist).
  - parens_slashes 1,640 and angle_brackets 6 unchanged.

## Warning sidecars (POL-033 — reviewed, summarized, deleted)

`XML/cleaner_warnings.csv` (deleted after review): 1,245 `c030` ambiguity
flags (735 eng_tmem + 510 zho_tmem, 596 distinct Amis sentences —
apostrophes in quote-bearing-TRANSL sentences the classifier left as
glottal) and 19 `c002` flags (12 zho sentences — apostrophe/single-quote IME
artifacts inside Chinese TRANSLs; warn-only, no change). Identical to round
1. No `standardize_warnings.csv` was produced.

## README updates (per the content-policy ruling)

- New "Cleaning and Quote Correction" section with the mandated data-user
  notes (automatic disambiguation; FPs possible, misses certain; log with
  before/after in `CodeAndDocs/quote_corrections.csv`; snapshot pointer).
- New "Rebuilding the XML" section documenting `make_xml.sh` with per-step
  explanations and the `PYTHON`/`BANK` overrides; replaces the inline
  command block.
- "Preserved exactly" original-tier claim qualified ("cleaned as described
  above"); Reproducibility section now names `make_xml.sh` and the
  snapshot.
- Dropped: stale `standardize.py`-build note; no sweep narrative,
  project-wide-rule explanations, or V-rule numbers added.

## GitBook (merge-time, not done here)

The Glosbe corpus page must gain the same data-user notes as the readme's
"Cleaning and Quote Correction" section (automatic disambiguation; FPs
possible, misses certain; corrections logged with before/after in
`CodeAndDocs/quote_corrections.csv`), via the standard 4-integration-point
update on a branch off the GitBook repo's `main`.

## Verdict

Diff 100% classified (13,413/13,413); token delta 0; validate_xml clean;
legacy-tilde findings zeroed; correction set identical to round 1; known
imperfections accepted by ruling. **No merge-gating questions remain from
this turn.** UNEXPLAINED: none.
