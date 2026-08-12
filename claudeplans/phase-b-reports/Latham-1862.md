# Phase B regeneration report — Latham-1862 (ROUND 3, fixup under 2026-08-11 overnight rulings)

Fixup applied 2026-08-11 on branch `sweep/g1-latham` (single commit atop the
sweep tip), superseding the round-2 report. Corpus: historical comparative
wordlist, Latham 1862 pp. 315–318; 2 files, 62 `S` (24 Babuza-Favorlang
`bzg` + 38 Siraya `fos`), hand-transcribed, no `PHON`/`W`/`M`, zero
apostrophes.

## Maintainer rulings applied (2026-08-11 overnight batch)

1. **Latham is EXEMPT from accent removal.** The pipeline uses
   `standardize.py --copy`, not `--remove_accents`. Round 2's 4 accent-strips
   (`chárrina`→`charrina`, `cháan`→`chaan`, `asiél`→`asiel`, `bóá`→`boa`)
   are reverted: `XML/` was restored from the POL-035 snapshot and the
   corrected `make_xml.sh` rerun, so the standard tier regained the accents.
2. **No spurious no-op steps.** `apply_manual_edits.py` (a documented no-op —
   no `manual_edits.xml` exists) was removed from `make_xml.sh` and the
   README pipeline. The pipeline is now: `clean_xml.py` (verified no-op) →
   `standardize.py --copy`. No `add_phonology`, by design.
3. **README content policy.** README trimmed to current-state-only: removed
   the sweep/ruling memorialization ("sweep-wide ruling 2026-08-11, replacing
   the earlier --copy convention"), the `_accents.py` strip-set caveat and
   per-form strip list, the "was 9 before the sweep run" V116 history, the
   apply_manual_edits step, and POL-number jargon. Kept: source description,
   pipeline with per-step explanations, brief snapshot note, reproduction
   instructions.

## Verification

| Check | Result |
|---|---|
| Standard vs original tier | **All 62 S letter-for-letter identical** (script comparison, both files); the 4 previously stripped forms verified back to `chárrina`, `cháan`, `asiél`, `bóá` |
| `validate_xml` (by_path XML/) | **0 findings.** Dialect attrs: `dialect="Favorlang"` on the `bzg` file (valid — `dialects.csv` lists Babuza + Favorlang as Official for Babuza-Favorlang) and `dialect="Siraya"` on the `fos` file (valid — single-dialect language, value = language name). Neither attr changed. |
| `validate_port_readiness --corpus_path Corpora/Latham-1862` | **0 HARD, 0 WARN — P002 gone** (sweep tip derives the ISO map from repo-root `languages.csv`, which now includes `bzg` Babuza-Favorlang) |
| `validate_text` (by_path XML/) | **9 SOFT (V116 non_ascii_in_form)** — back to the pre-sweep baseline; all 9 are Latham's intentional diacritics (`â á ó é à`), now present in original, standard, and alternate tiers alike. Round 2's 4 is superseded. |
| Tokens (`count_tokens` on `XML/`) | bzg 26 / fos 38 — delta 0 vs HEAD and vs pre-sweep; `bzg` now resolves to the language name "Babuza-Favorlang" via `languages.csv` |
| Diff vs snapshot | Published `XML/` = POL-035 snapshot + `make_xml.sh` (clean_xml no-op; `--copy` + re-serialization). Only serialization differs from the snapshot; text content identical. Siraya file byte-identical to round 2 (it had no acute-marked standard forms). |

## Pipeline as it now stands

`CodeAndDocs/make_xml.sh [FORMOSANBANK_ROOT]`:
1. `QC/cleaning/clean_xml.py` — verified no-op (clean hand transcription,
   zero apostrophes, no bzg/fos attestation dictionaries).
2. `QC/utilities/standardize.py --copy` — standard tier is a verbatim copy of
   the original tier (no conversion table for these extinct varieties; the
   **accent-removal exemption ruling** applies to this corpus, so diacritics
   are preserved in the standard tier).

No manual-edits step (none exist), no phonology (by design). Warning
sidecars: none produced.

## Notes for the maintainer

1. **Snapshot vs `count_tokens.py` over `Corpora/`:** CI's token-comparison
   workflow rglobs *all* `*.xml`, including
   `CodeAndDocs/pre_correction_snapshot/`, so this commit shows a one-time
   apparent +64 delta (+26 bzg / +38 fos) there. Published-stats path
   unaffected (`get_corpus_stats.py` restricts to `XML/`); precedent exists
   (ePark/Glosbe commit XML under `CodeAndDocs/`). Consider excluding
   `CodeAndDocs/` from `count_tokens.py` discovery as POL-035 snapshots
   accumulate.

## Files in the (amended) commit

- `Corpora/Latham-1862/XML/Babuza-Favorlang/latham_1862_favorlang.xml` — re-serialized only; content identical to pre-sweep (accents intact)
- `Corpora/Latham-1862/XML/Siraya/latham_1862_sideia_sida.xml` — re-serialized only; content identical
- `Corpora/Latham-1862/CodeAndDocs/make_xml.sh` — new, maintenance pipeline wrapper (clean_xml → standardize --copy)
- `Corpora/Latham-1862/CodeAndDocs/pre_correction_snapshot/` — new, POL-035 pristine baseline (2 files)
- `Corpora/Latham-1862/README.md` — pipeline/Reproduce/QC sections updated to current state per the README content policy
- `claudeplans/phase-b-reports/Latham-1862.md` — this report (supersedes rounds 1–2)

---

# Addendum — 2026-08-12: standard tier dropped (ruling)

**Branch:** `work/latham-drop-standard` (off `origin/main` @ `269c6ef9a`)

**Ruling applied:** *"Latham-1862 should lose its standard FORMs for now. I
have a long-term note in Basecamp to figure out how to standardize it, if at
all."*

Rationale, as recorded in the code and README: a `standard` FORM asserts a
transliteration into FormosanBank's common orthography. Siraya is under a
standing ruling not to be standardized to Ortho113 or anything else for now,
both varieties' `standard_orthography` cells in the repo-root `standards.csv`
are blank, and the tier as it stood was a `standardize.py --copy` duplicate of
`original` — letter-for-letter identical, diacritics included. It asserted a
standardization nobody performed, so it is removed.

## What changed

Modelled on `Corpora/WakelinTexts/CodeAndDocs/drop_derived_tiers.py`, the
existing precedent for a corpus that publishes an original tier only. The
script was copied rather than reinvented: mechanism (`_is_derived`,
`drop_derived`'s tail-preserving removal, the shared `QC/utilities/_prettify`
write idiom, the CLI) is byte-for-byte the Wakelin version; only the module
docstring is rewritten for Latham's situation. The two corpora stay
consistent.

| File | Change |
| --- | --- |
| `Corpora/Latham-1862/CodeAndDocs/drop_derived_tiers.py` | **new** — deletes every `FORM[@kindOf="standard"]` and every `PHON` at S/W/M level |
| `Corpora/Latham-1862/CodeAndDocs/make_xml.sh` | step 0 (restore `XML/` from the POL-035 snapshot) added; `standardize.py --copy` **removed**; `drop_derived_tiers.py` added as step 2 |
| `Corpora/Latham-1862/README.md` | new "What you get: the original tier only" section; Tiers row; Extraction/Reproduce/Maintenance/QC sections updated |
| `Corpora/Latham-1862/XML/**` (2 files) | 62 standard FORMs removed |

**POL-038 compliance.** No published XML was hand-edited. The corpus already
carried a POL-035 pre-correction snapshot at
`CodeAndDocs/pre_correction_snapshot/` (confirmed: 2 files, 62 `S`, 62 standard
FORMs, 0 PHON; content identical to published `XML/`, differing only in
serialization — `<?xml version='1.0' encoding='UTF-8'?>` + 2-space indent vs the
pipeline's `<?xml version="1.0" ?>` + 4-space). `make_xml.sh` now restores from
it before running, so `XML/` is regenerated from the fixed baseline on every
run rather than edited in place. The snapshot itself is untouched.

**No phonology — confirmed still true.** `grep -c '<PHON'` is 0 in both
published files *and* in both snapshot files; `drop_derived_tiers.py` removed
0 PHON. The corpus has never had a PHON tier at any stage (build, snapshot,
published), and `add_phonology` is still absent from the pipeline by design.
The step now enforces that as an invariant rather than leaving it to hold by
accident.

## Counts

| | Babuza-Favorlang | Siraya | Total |
| --- | --- | --- | --- |
| S-level standard FORMs removed | 24 | 38 | **62** |
| W-level standard FORMs removed | 0 | 0 | **0** |
| M-level standard FORMs removed | 0 | 0 | **0** |
| PHON removed | 0 | 0 | **0** |

W/M are zero because the corpus has no `W` or `M` elements at all — it is a
lexical table with no segmentation (README, "Extraction Decisions").

## Token delta: 0 — verified, not assumed

`QC/corpus_counts.select_sentence_form()` returns the S-level `standard` FORM
if non-empty **and otherwise falls back to `original`** (read at
`QC/corpus_counts.py`; the docstring states the rule and the code implements
it). Since the standard tier here was a verbatim copy, the fallback yields the
identical string.

Verified empirically rather than reasoned about: `QC/count_tokens.py` was run
against an `origin/main` export of the corpus and against the worktree, and
the two JSON outputs are **byte-identical** — Babuza-Favorlang 26 (Favorlang
26), Siraya 38 (Siraya 38). Run both over `XML/` alone and over the whole
corpus directory (the snapshot is excluded from discovery by
`corpus_counts.collect_tree_records`, which skips any path containing
`CodeAndDocs` — the concern raised in the 2026-08-11 "Notes for the
maintainer" no longer applies). `get_corpus_stats.py Corpora/Latham-1862` was
also re-run: `statistics/Latham-1862_corpora_stats.csv` is unchanged, so CI's
corpus-metrics job has nothing to rewrite.

## Validators before / after

| Validator | Before (`origin/main`) | After | Explanation |
| --- | --- | --- | --- |
| `validate_xml` | 0 findings | **62 SOFT V014** `count_missing_standard_form` (24 `bzg` + 38 `fos`) | The designed signal. V014 counts S/W/M elements that have FORMs but none with `kindOf="standard"`; all 62 `S` now qualify. Its docstring anticipates exactly this case: "Some corpora legitimately lack a standard tier because the orthography is unsettled." 0 HARD, 0 WARN — the XSD does not require a standard FORM. Rise = 62 = number of elements that lost a standard FORM. ✔ |
| `validate_text` | 9 SOFT V116 `non_ascii_in_form` | **1 SOFT V116** | V116 **skips `kindOf="original"` by policy** (rules/text.py: the original tier is source-faithful and legitimately carries annotation characters). So all 9 were on non-original tiers: 8 on the standard tier (`tâu`, `chárrina`, `cháan`, `asiél`, `bóá`×2, `avâu`, `àmagh`) and 1 on an **alternate** FORM (`arribórribon`, `S_favorlang_neck`). Dropping the standard tier removes exactly the 8; the alternate-tier finding is untouched. 9 − 8 = 1. ✔ Latham's diacritics remain intact in the original tier — nothing was stripped, a duplicate view of them was removed. |
| `validate_glosses` | 62 SOFT V060 `W_count_matches_word_count` | **62 SOFT V060** | Findings CSV is byte-identical before and after (`diff` clean). V060 concerns W-count vs word-count and is unaffected by S-level FORM tiers. ✔ |

No rule went from clean to HARD; no HARD or WARN finding exists in any of the
three validators, before or after.

## Idempotence

`make_xml.sh` was run three times in succession; `md5sum` of both published
XML files is identical across runs 1, 2 and 3, and `git diff --stat` after run
3 is still exactly `2 files changed, 62 deletions(-)`. Idempotence is
structural, not incidental: step 0 rebuilds `XML/` from the snapshot every
time, so the pipeline's output is a pure function of the snapshot plus the
committed code.

## Element-by-element diff audit vs `origin/main`

Every element in both trees was compared by (tag, attributes, text), keyed by
a structural path (`S`/`W`/`M` by `@id`, `FORM`/`PHON` by `@kindOf`, `TRANSL`
by `@xml:lang`), old vs new. **258 elements compared, 258 classified (100%)**:

| Count | Category |
| --- | --- |
| 196 | **UNCHANGED** — identical tag, attributes and text (2 `TEXT`, 62 `S`, 62 original `FORM`, 8 alternate `FORM`, 62 `TRANSL`) |
| 62 | **EXPECTED: standard FORM removed** — the ruling |
| 0 | element added |
| 0 | element changed (attribute or text) |

Corroborated at the line level: `git diff -U0` over `XML/` yields **62 removed
lines and 0 added lines**, all 62 of the form
`<FORM kindOf="standard">…</FORM>`. No re-serialization drift — the XML
declaration, 4-space indentation and absent trailing newline all survive the
snapshot round-trip unchanged, because `drop_derived_tiers.py` writes through
the same `QC/utilities/_prettify` path `standardize.py` used.

Not element-level, but audited alongside: `TEXT` attributes (id, citation,
BibTeX_citation, copyright, glottocode, dialect, source, `xml:lang`) are
unchanged on both files; no `S` was added, removed, renamed or reordered; the
8 alternate FORMs are all still present.

### UNEXPLAINED — blocks merge

**None.** Every difference between `origin/main` and this branch is the
removal of a `FORM[@kindOf="standard"]`.

## Open item (unchanged by this commit)

The Basecamp note stands: how, or whether, to standardize a 19th-century
comparative wordlist in Babuza-Favorlang and Siraya. Nothing was discarded —
the standard tier remains in the pre-correction snapshot and can be restored
by changing the pipeline if the question is ever settled.
