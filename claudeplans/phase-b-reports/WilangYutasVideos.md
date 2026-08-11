# Phase B regeneration — WilangYutasVideos (round 2, redo under 2026-08-11 rulings)

Date: 2026-08-11 · Branch: `sweep/g1-wilang` (reset to sweep tip; round 1 redone) ·
Group 1 (standardize **`--remove_accents`** per updated ruling, add_phonology `--orthography Ortho94`)

Corpus: Atayal (tay, dialect Sekolik) YouTube video transcripts. 82 XML files
(34 with transcripts, 3,014 `<S>`; the rest are no-transcript stubs and
`*_untranscribed.xml` audio companions with no `<S>`). No audio downloaded or
touched by this run.

## Changes from round 1 (maintainer rulings applied)

1. `standardize.py --remove_accents` replaces `--copy` (copy + accent deletion
   + null-unit removal). Accent-diff volume reported explicitly below.
2. New **`CodeAndDocs/make_xml.sh`**: wraps the post-scrape steps in order
   (clean_xml → standardize `--remove_accents` → add_phonology
   `--orthography Ortho94`), FormosanBank root parameterized
   (arg 1 / `$FORMOSANBANK_ROOT` / auto-detected), executable. Documented in
   the README with the per-step explanations retained. (apply_manual_edits
   was initially included; removed in the overnight fixup — see below.)
3. POL-038: the Bopomofo `ㄇ` content flagged by c007 STAYS (informational,
   not a defect) — README now notes it (as a plain content note, per the
   fixup README policy).

## Pipeline run (via `CodeAndDocs/make_xml.sh` against the worktree QC scripts)

1. `clean_xml.py --corpora_path Corpora/WilangYutasVideos/XML`
2. `standardize.py --remove_accents` — copy of original + acute/breve accent
   deletion + null-unit removal.
3. `add_phonology.py --orthography Ortho94`

(The round-2 run also ran `apply_manual_edits.py` first — a no-op, since no
`CodeAndDocs/manual_edits.xml` exists; the fixup removed that step from the
pipeline per the no-spurious-no-op-steps ruling.)

## POL-035 snapshot decision: NOT NEEDED (re-verified)

Every transcribed sentence regenerates deterministically from the **committed**
`CodeAndDocs/raw_scrape/` .txt files (34/34 git-tracked, re-verified via
`git ls-files`) via `make_xml.py`; only the no-text stubs and audio
segmentation need live YouTube. Regenerable in the POL-035 sense for
everything a text correction could touch → no `pre_correction_snapshot/`.
(Moot in practice: zero corrections applied — see below.)

## Quote-correction verification (Atayal armed)

- `quote_corrections.csv`: **not created anywhere** (corpus root, CodeAndDocs,
  XML checked) → **0 corrections**, matching Phase A REV 2's measured 0.
  Any row would have been UNEXPLAINED/blocking; none exist.

## Warning sidecars (POL-033) — reviewed, then deleted

- Fresh `XML/cleaner_warnings.csv`: **1 row** — `c007` Bopomofo `ㄇ` in
  `20190407_..._MVI_1702_yiwancheng.xml` `Atayal_28` (`摸ㄇ`, transcriber CJK
  fragment). Informational; per POL-038 the content stays. Reviewed and
  deleted.
- Stale **committed** `cleaner_warnings.csv` at the corpus root (same c007
  ×6, old append bug): `git rm`'d again (removal via git = fine under
  POL-038; POL-033 says these are per-run reports, never committed).
- No `standardize_warnings.csv` produced.

## Diff audit (element-by-element vs git HEAD)

82 files compared positionally; **identical element structure** everywhere
(no elements added/removed/reordered). 15,399 leaf values (FORM/PHON/TRANSL/
AUDIO/UNCLEAR incl. mixed content) + 26,921 attribute sets compared;
**5,364 changed values in 34 files, 100% classified**:

| Class | Count |
|---|---|
| PHON regenerated: legacy `x~y` → `[x\|y]` variant notation (+punctuation drop) | 3,421 |
| PHON regenerated: punctuation / stray-symbol / CJK star-mask-length / hyphen drop only (letters identical) | 1,845 |
| Standard S-FORM rederived (copy + accent strip) — substantive: 26 source hyphens restored (`Karen-ko`, `Tay-To`, …) + 2 `〜`→`~` propagated | 28 |
| Standard S-FORM — whitespace-only difference | 23 |
| Original FORM whitespace-only reserialization (indentation around `<UNCLEAR/>`) | 23 |
| **Accent removal (`--remove_accents`)** — standard-tier accent deletions | **0** |
| Original FORM `〜` (U+301C wave dash) → `~` clean_xml canonicalization (Japanese song lines, ki_Yagu_04 Atayal_50/51) | 2 |
| PHON residuals, individually classified (below) | 22 |

**Accent-removal volume: 0 — flagged explicitly.** The corpus's only
NFD-decomposable characters are Japanese kana with dakuten (じ, が, …), which
`strip_accents` (acute/breve only) correctly leaves alone; no acute/breve
accents exist in the Sekolik transcripts. Hence `--remove_accents` degrades
to a pure copy here, and the round-1 diff surface reproduces exactly.

22 PHON residuals (all explained, none blocking — same classes as round 1):

- **18** — PHON now covers text **after `<UNCLEAR/>`** that the old PHON
  silently truncated (9 sentences × original+standard tiers: kinhulan
  Atayal_532; dierduan Atayal_176/215/232/259; dibaduan Atayal_8/10;
  MVI_1702 Atayal_11; MVI_1703 Atayal_22). Regeneration coverage fix.
- **4** — segmentation hyphen now dropped *before* grapheme conversion, so
  `n-g` merges into the `ng` → `ŋ` digraph (`n-glgan` → PHON `ŋlɣan`,
  dierduan Atayal_165; `ln-gan` → `lŋan`, muqian… Atayal_390; ×2 tiers each).
  Known consequence of add_phonology ordering; flagged for maintainer
  awareness (same as round 1).

(Bookkeeping note vs round 1: round 1's separate "CJK star-mask recount (4)"
and "stray symbol drop (3)" residuals fall inside this round's letters-equal
punctuation class, and its post-UNCLEAR count was 20; net classification is
identical and totals match — 5,364 both rounds.)

Cross-checks:

- **AUDIO untouched**: 0 attribute changes, 0 text changes across all 82
  files (verified element-by-element; every element's full attribute dict
  compared).
- **Copy invariant**: standard S-FORM == original S-FORM (incl. `<UNCLEAR/>`
  children) for all 3,014 sentences (0 violations) — consistent with the
  0-accent finding.
- TRANSL: 0 changes. UNEXPLAINED: 0.

## Token delta

24,957 → **24,957** (Atayal/Sekolik; delta 0).

## Validators

- `validate_xml`: clean before, clean after (82 files, 0 issues).
- `validate_text`: 3,608 SOFT → **191 SOFT**, all movements explained:
  - **V147 phon_legacy_tilde_variant 3,442 → 0** (the point of the rerun).
  - V116 non_ascii_in_form 91 → 88 (exactly the `〜` chars canonicalized to `~`).
  - V133 dash_in_S_standard_FORM 0 → 26 — Japanese-loanword hyphens restored
    to the standard tier by the copy semantics of `--remove_accents` (no
    conversion table); the standing "re-standardize when a table exists"
    signal, documented in the README.
  - V114 multiple_whitespace 0 → 2 — whitespace runs in two near-empty
    standard FORMs copied from `<UNCLEAR/>`-bearing originals. Cosmetic.
  - V111 (1), V122 (72), V137 (2) unchanged.

## README (round-1 modernizations re-applied + round-2 changes + fixup cuts)

Updated: published layout (`CodeAndDocs/`, `XML/Atayal/`), correct script
names, reproducibility note (committed raw_scrape vs network-dependent
stubs), Bopomofo/Japanese content note (stays; plain one-liner), pipeline
presented via `make_xml.sh` with the three commands **and per-step
explanations kept**, `--remove_accents` semantics (incl. the fact it changes
nothing here) and the loanword-hyphen consequence documented, Ortho94
assumption retained as documented.

## Fixup (2026-08-11 overnight maintainer rulings)

1. **No-op step removed**: `apply_manual_edits.py` dropped from
   `CodeAndDocs/make_xml.sh` (now 3 steps, probe path switched to
   `clean_xml.py`) and from the README pipeline — no manual edits exist for
   this corpus.
2. **README content policy applied** — removed: POL-038 citation in
   Reproducibility, POL-033 citation in the clean_xml step, `c007` rule
   reference in the Bopomofo note (kept as a plain "faithful to source,
   intentionally kept" line), V133/SOFT-finding references in the
   standardize step (loanword-hyphen behavior kept, described plainly),
   the `[x|y]` project-notation sentence, and the entire "Maintenance
   history" sweep-narrative section. Kept: corpus description, source,
   3-step pipeline with per-step explanations, reproduction and
   audio-download instructions.
3. **Sanity re-run — pipeline is NOT byte-idempotent (new finding, XML
   reverted)**: re-running `make_xml.sh` over the committed XML changed 9
   files, 100% whitespace-only (`git diff -w` empty): the indentation-like
   whitespace in mixed-content tails after `<UNCLEAR/>` **doubles on every
   run** (32 → 64 → 128 spaces; a third run doubles again — no fixed
   point). Root cause is shared QC tooling, not corpus code: the
   `prettify()` line-indent-doubling regex
   (`re.sub(r"^( +)", lambda m: m.group(1) * 2, line)`) at
   `QC/utilities/standardize.py:194` and `QC/utilities/add_phonology.py:61`
   doubles leading whitespace of *every* line, including lines whose leading
   whitespace is text content (the `<UNCLEAR/>` tail spanning a newline
   before `</FORM>`/`</PHON>`). Affects any corpus with multiline mixed
   content. Out of scope for this corpus fixup (fixing it would desync
   other sweep worktrees mid-flight) — **XML reverted to the committed
   state** (semantically identical), flagged for a repo-wide QC fix.
   Fresh `cleaner_warnings.csv` (same single c007 row) reviewed and deleted.
4. **Validators re-confirmed unchanged** on the committed XML:
   `validate_xml` 82 files / 0 issues; `validate_text` 191 SOFT with the
   identical per-rule breakdown (V111 1, V114 2, V116 88, V122 72, V133 26,
   V137 2). **AUDIO untouched** (XML tree back at HEAD byte-for-byte; the
   transient re-run diffs contained no AUDIO changes).

## UNEXPLAINED items

None.
