# Phase B regeneration — Song-Kanakanavu-Grammar

Date: 2026-08-12 · Branch: `work/b3-song` (off `main` @ `3ce8e7dac`) ·
Group 2 (bespoke pipeline: full README order, `standardize.py --copy` +
`normalize_standard_forms.py` + `fold_standard_stress.py`, phonology Ortho113)

Corpus: Kanakanavu (`xnb`, dialect Kanakanavu), Song Limei 2018 *Introduction to
Kanakanavu Grammar*. 2 XML files — 699 grammar sentences (650 with `W`/`M`;
3,477 `W`, 5,034 `M`) and 870 dictionary entries. No audio.

## Single entry point

`CodeAndDocs/scripts/rebuild_final_xml.sh` already wrapped the whole pipeline, so
it was **renamed** (`git mv`) to `CodeAndDocs/scripts/make_xml.sh` and extended
rather than wrapped by a new script. Changes:

- Builds **into the published `XML/`** instead of a parallel `CodeAndDocs/Final_XML/`
  tree, so a rebuild is a `git diff` and there is no second copy to compare by
  hand. Output paths moved in `build_xml.py` (`OUTPUT_DIR`) and in the three
  corpus scripts' `DEFAULT_XML_PATH`; the regression tests now read `XML/`.
  `build_xml.py`'s ledger-column check keeps the ledger's literal
  `Final_XML/...` string (the ledger is hash-pinned) — renamed `LEDGER_XML_PATH`.
- FormosanBank checkout defaults to the repository containing the corpus
  (arg 1 / `FORMOSANBANK_PATH` still override); `PYTHON` overridable.
- The commit pin was **stale** (`a20f81b47`, pre-`shared-source-phonology`).
  It could no longer be an assertion: the old script required a *separate clean*
  checkout, which is incompatible with building in place. It is now a recorded
  reference commit (`3ce8e7daca2ab7f58a12b8e9b955fec2fc78d1fd`) that prints a
  note when the checkout differs. All the load-bearing assertions survive
  unchanged in `build_xml.py` (source-PDF/positioned-text hashes, closed
  page/candidate inventory, reviewed-artifact hashes, ledger counts, continuous
  sentence ids).
- `apply_manual_edits.py` **dropped** (no `CodeAndDocs/manual_edits.xml`; the
  step was a documented no-op).
- Dropped the trailing `rm -f cleaner_warnings.csv` so the per-run sidecar is
  reviewable; it is not committed (POL-033).

Run (steps 1–4 regenerate the ledgers from `raw_data/`, and all three
hash-pinned ledgers came back byte-identical):

1. `extract_dictionary.py` → 767 headwords
2. `reconcile_barred_vowels.py --check` → 0 rows need reconciliation
3. `extract_interlinear.py` → 650 analyses / 3,477 W / 5,034 M
4. `build_xml.py` → 699 S + 870 entries (114 split variants, 26 duplicate
   variants dropped, 11 bound citation forms excluded)
5. `clean_xml.py`
6. `standardize.py --copy`
7. `normalize_standard_forms.py` → 117 exact decisions applied, 228 split
   variants + 11 bound exclusions verified, 2 analysis-tier corrections
8. `fold_standard_stress.py` → 762 standard FORMs folded
9. `add_shared_phonology.py` (shared `add_phonology.py`, Ortho113)

Re-running the whole script produced **byte-identical** XML (deterministic).
18/18 regression tests pass (one test asserted the retired `r~ɾ` PHON notation;
updated to `[r|ɾ]` plus a no-bare-tilde assertion).

## `--copy` vs `--remove_accents` (ruling reconciled)

**Kept `--copy`**, as the documented flow requires. Reasons, verified:

- The bespoke steps assume copy semantics. `normalize_standard_forms.py` applies
  128 exact decisions whose `expected_input` values are matched against the
  *original* FORM (15 of them contain acute accents), and `fold_standard_stress.py`
  is the corpus's reviewed accent step — it folds `á é í ó ú` **and** the
  decomposed `ʉ́` in the standard *and alternate* tiers, at S/W/M level, while
  `add_shared_phonology.py` reuses the same folder for a temporary original-tier
  copy. Accent handling is already owned, deliberately, by corpus code.
- Empirically nothing is left for `--remove_accents` to do: after the run, 0
  standard/alternate FORMs contain a combining mark, and the 762 accented FORMs
  that remain are all `original` (by design — the printed stress is preserved
  there). The corpus has no `∅`/`ø`/`Ø` at all, so the null-unit removal half of
  `--remove_accents` is also vacuous.

## POL-035 snapshot: NOT NEEDED

The README shows a runnable reproduction from committed inputs, and it was
executed here: `raw_data/source.pdf` + `official_text.jsonl` + the six
`intermediate/` ledgers are all git-tracked, and steps 1–4 regenerated the
ledgers and both XML files from them (hash assertions passing) with no network
access. Regenerable in the POL-035 sense → no `pre_correction_snapshot/`.
(Moot in practice: zero corrections applied — below.)

## Quote corrections (Kanakanavu dictionary armed): **0**

`QC/validation/reference/Kanakanavu/attestation.txt` (188 entries) is present and
the classifier ran — 68 `c030` ambiguity flags prove it loaded. **No `c031`/`c032`
row and no `quote_corrections.csv` anywhere** → zero original-tier rewrites,
nothing to commit or cross-check.

Reviewed the 68 flags anyway: all in the grammar file, all in sentences that
already use `"` for the quotation and `'` for the glottal letter — e.g. S0336
`makasi sua 'avia, "ka'anʉ ku tia múkusa 'akuan tamna tanasa sumasima'ʉ."`
(TRANSL `’avia說：＂我不要去’akuan家玩。＂`). The classifier correctly left every one
alone; a correction here would have been a regression.

## Warning sidecars (POL-033) — reviewed, then deleted

Fresh `XML/cleaner_warnings.csv`, 143 rows, deleted after review; no
`standardize_warnings.csv`; nothing committed.

- `c002` × 75 — a `’` inside Kanakanavu names/words embedded in the Chinese
  translations (`Mu’u`, `’angai`, `Pi’i`, `《’usu慢走》`). These are glottal-stop
  letters, not IME quotation artefacts; the Chinese branch leaves them unchanged
  and the committed XML already held them, so they produce no diff. Worth a
  maintainer's eye at some point (the same letter is ASCII `'` in the Formosan
  tiers and `’` inside `zho` TRANSL), but it is a shared-cleaner question, not a
  corpus defect, and out of scope here.
- `c030` × 68 — the quote-classifier ambiguity flags described above.

## Diff audit (element-by-element vs git HEAD)

Both files parsed and walked in document order: **element counts, tags, order and
every attribute set identical** (60,482 elements each side; 0 structural changes,
0 attribute changes). Of the 50,400 non-empty text values (20,160 FORM, 20,160
PHON, 10,080 TRANSL), **5,940 changed — 100% PHON, 100% classified**:

| Class | Count |
|---|---|
| PHON: legacy `x~y` → `[x\|y]` variant notation only | 4,546 |
| PHON: `[x\|y]` migration **+** punctuation dropped | 1,046 |
| PHON: punctuation dropped only | 348 |
| FORM (original / standard / alternate), TRANSL, attributes, structure | **0** |

Even split original/standard (2,970 each). The 5,592 values touching the tilde
migration match the 5,592 pre-run V147 findings exactly. Character-level check of
the punctuation class: the only characters removed anywhere are `.` ×1,120,
`,` ×480, `?` ×222, `"` ×128, `!` ×104, `;` ×16, `(` ×2, `)` ×2; **no character
was added, no letter changed, no hyphen involved** (segmentation markers were
already absent from PHON).

Nothing else moved: the standard tier reproduced exactly through
`--copy` → 128 decisions → stress folding, which is the strongest available check
that the bespoke steps still behave as reviewed.

**UNEXPLAINED: none.**

## Token delta

5,256 → **5,256** (Kanakanavu/Kanakanavu; delta 0).

## Validators (before → after)

| | before | after |
|---|---|---|
| `validate_xml` | 7 SOFT (V144 ×7) | 7 SOFT (V144 ×7) — unchanged |
| `validate_text` | 5,598 SOFT (V147 ×5,592, V122 ×4, V133 ×2) | **6 SOFT** (V122 ×4, V133 ×2) |
| `validate_glosses` | 1,304 SOFT (V060 ×1,296, V061 ×8) | 1,304 SOFT — unchanged |

V147 → 0 (the point of the rerun). No HARD findings before or after. V122 (prose
parentheses) and V133 (the two deliberate break-punctuation dashes, S0469/S0472)
are the corpus's documented expected diagnostics.

## Issue #96 claim dispositions (verified independently)

| Claim | Verdict | Disposition |
|---|---|---|
| 5,592 V147 findings; PHON uses retired bare-tilde variants | **Confirmed** (5,592 before) | **Fixed** — regenerated, 0 after; machine-owned PHON regenerated, never edited |
| 7 of 3,477 W have no M child (V144) | **Confirmed** (7; the issue's "1 finding" is one summary row) | **Not actioned — out of scope.** All 7 are words the book glosses with a *single* printed gloss for a complex form (`m-u'iara` 慢, `pa-arivivini-ʉn` 使動-跟隨在後, `t<um>a-túturu` <主事焦點>-告知 …); `interlinear_ledger.jsonl` records `morphemes: null` for exactly these. Adding M would be inventing an analysis the source does not print — the issue's own "complete only source-supported M analyses". Linguistic worklist item; README now documents the gap for data users. |
| 8 V061 morpheme-count mismatches | **Confirmed** (8, unchanged) | Same items: 7 are the M-less W above; the 8th (`a'unu-ʉn=cu`, S0636-W002) has 2 M for an implied 3. Source-analysis question, not a pipeline defect. |
| 63 within-file duplicate groups / 130 occurrences | **Confirmed** (63 groups, 130 S; 0 cross-file) | **SOFT, no pipeline defect.** The corpus declares no dedup step, so POL-022 leaves the call to the maintainer, and the evidence favours keeping: 45 of 63 groups have *different* translations (dictionary senses — `'akia` = 不（在） vs 沒有（某物）, i.e. the issue's own example is two senses, not a repeat), and every `S` carries a distinct `source` page/label (S0014 p.69 ex. 4-11 vs S0031 p.74 fn. 17). Of the 18 same-translation groups, 17 are grammar examples reprinted on a different page to illustrate a different point, and 1 is the stress pair `ivatá`/`iváta` (0081/0081a) that collapses only after standard-tier stress folding. Documented in the README instead of removed. |

The issue's framing "fix the reproducible generator" needed no generator fix: the
ledgers and every FORM/TRANSL value regenerated byte-identically, and the only
stale output was PHON.

## README

Rewritten Reproduction section around the single command
(`CodeAndDocs/scripts/make_xml.sh`), in-place rebuild, dependency install,
overrides, determinism, and the tests; pipeline renumbered to 9 steps with the
no-op manual-edits step removed; two new user-facing notes (repeated surface
forms with distinct provenance; the 7 words with no morpheme analysis); the
`r~ɾ` shorthand in the orthography note rewritten in prose. `docs/
clean_clone_reproduction.md` keeps the 2026-08-06 clean-clone record and now also
carries the current XML hashes with a one-line statement of what changed.

## Not done / for the maintainer

- GitBook corpus page update (sweep step 9) — not part of this turn.
- The `zho`-TRANSL `’`-as-glottal question raised by the 75 `c002` rows.
