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
