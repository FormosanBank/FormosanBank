# Outstanding follow-ups after the B9 sweep

**Date:** 2026-06-01
**Status:** Open. Captured at end of the B9.1–B9.5 / W10 session so nothing is forgotten while the user goes through individual corpora.

Per-item: what's blocked, why, what unblocks it.

---

## 1. B9.2 W5 — `validate_audio_quality.py` end-to-end run blocked on `utils_CTC`

**Plan:** [B9.2 plan](2026-05-31-b9-2-audio-validation-plan.md) — W5.

**Where things stand.**
- Heavy deps installed 2026-06-01 (`torch`, `torchaudio`, `allosaurus`, `Levenshtein`, `unidecode` via `requirements-audio-mt.txt`).
- `validate_audio_quality.py` imports cleanly; the orchestration runs.
- Probe against `Corpora/ILRDF_Dicts/` (the only local corpus with both `<AUDIO>` at `<S>` level AND audio files on disk) found 3 entries, loaded the wav2vec2 model, then crashed at `ModuleNotFoundError: utils_CTC` inside `run_acoustic_pass`.

**Root cause.** `validate_audio_quality.py` (and Jacob Ye's source `compute_metrics.py`) expects a `data_quality_eval/` directory sibling to itself, containing `utils_CTC.py` with `get_trellis` and `backtrack` helpers. That directory does NOT exist in any branch of `Formosan-ILRDF_Dicts` — neither locally at `/Users/jkhartshorne/Documents/Projects/Formosan/Formosan-ILRDF_Dicts/` (branches: `main`, `AddDialects`, `Formosan-Update-Apr_2026`) nor in `git log --all`. The code is effectively undistributed.

**Acceptance criterion still unmet:** "produces a scores CSV from `Corpora/ePark/`" (B9.2 plan §Acceptance criteria).

**Two paths to unblock, pick one:**
1. **Obtain `utils_CTC.py` from Jacob Ye** and either commit to `Formosan-ILRDF_Dicts/data_quality_eval/` upstream, or document a private-checkout convention in `QC/README.md`.
2. **Vendor the CTC helpers into FormosanBank.** They're thin wrappers over standard PyTorch CTC ops (forced alignment trellis + backtrack); a vendored ~100 LOC module under `QC/validation/_ctc_utils.py` would remove the external dependency entirely. Worth doing if Jacob isn't going to publish.

**Adjacent: ePark audio isn't downloaded.** Even after `utils_CTC` lands, the literal acceptance ("against `Corpora/ePark/`") needs `bash Corpora/ePark/download_audio_data.sh` run first. Probably trivial once `utils_CTC` works (the script uses git-lfs/jq/hf, all installed).

---

## 2. B9.2 W8 — `audio-validation.yaml` not draft-PR-verified

**Plan:** [B9.2 plan](2026-05-31-b9-2-audio-validation-plan.md) — W8.

**Where things stand.** `.github/workflows/audio-validation.yaml` was committed by the B9.2 subagent. It's well-formed YAML and the steps invoke `validate_audio.py` correctly. Local validation is fine.

**What's missing.** A draft PR that actually exercises the workflow on GitHub Actions to confirm it goes green (or surfaces issues). The B9.2 subagent couldn't push (sandboxed). I can't push from here either.

**Action: user.** Open a draft PR with any audio-touching change (or just a no-op tweak to `audio-validation.yaml` itself), watch the workflow run, fix what surfaces. Close the PR without merging once green.

---

## 3. ePark duplicates curatorial review

**Plan:** [B9.5 plan](2026-05-31-b9-5-duplicate-sentence-detection-plan.md) — sanity-run result.

**Where things stand.** `validate_duplicate_sentences.py by_path --path Corpora/ePark/XML` surfaced:
- **3,963 HARD duplicate groups** (8,394 occurrences total) — within-file duplicates.
- **23,562 SOFT duplicate groups** (78,474 occurrences) — within-corpus cross-file duplicates.

Heavy concentration in `qing_jing_zu_yu_contextual_indigenous_language/*` and `hui_ben_ping_tai_picture_book_platform/*` sub-corpora.

**Why deferred.** User direction 2026-06-01: handle when going through individual `Corpora/` (in progress). The validator did its job by surfacing; the call between "intentional didactic repetition" and "ingestion bug" is curatorial, not mechanical.

**Action: user (during corpus walk-through).** When you get to ePark, decide per sub-corpus whether to remove duplicates (`remove_duplicate_sentences.py --apply`) or document them as intentional in the corpus README.

---

## 4. B5 follow-up — cleaner-side zero-width / BOM stripping

**Plan:** [B5 plan](2026-05-30-b5-cleaner-extensions-implementation-plan.md) — "Follow-up: cleaner-side zero-width / BOM stripping" section at the bottom.

**Where things stand.** B9.4 W10's V131 (TR16) HARD validator is in place — corpora with U+200B/U+200C/U+200D/U+FEFF in FORM/TRANSL will fail CI. Per the W3 brainstorm sign-off (2026-06-01), the corresponding cleaner-side strip lands in `clean_xml.py` so HARD findings stay near zero in practice.

**Scope (one small task).** Helper `_strip_zero_width(text: str) -> str` that removes the 4 characters, wired into both `clean_text` (FORM) and `clean_trans` (TRANSL). 8 idempotency pins in `tests/cleaners/test_clean_xml.py` (parametrizable). No `CleanerWarnings` row needed — silent mechanical fix like NFC normalization.

**Action: dev session.** Pick up whenever the next B5 work happens; ~30 minutes including tests.

---

## 5. Real Pyright signals not fixed during the session

These were classified as low-priority noise but are real type issues worth fixing eventually:

| File | Line | Issue | Severity |
|---|---|---|---|
| [QC/validation/flag_audio_suspicious.py](../QC/validation/flag_audio_suspicious.py) | 233 | `statistics.median(list[Unknown \| None])` — list comprehension doesn't filter `None`. Real type error; runtime works because actual values are floats. | Low |
| [QC/validation/flag_audio_suspicious.py](../QC/validation/flag_audio_suspicious.py) | 100 | `lang` assigned but not accessed. Dead local. | Trivial |

Fix in a dedicated "Pyright cleanup" pass once enough of these accumulate, or piecemeal when next touching the file.

---

## 6. `ver` attribute allowlist — single-value for now

**Where things stand.** V084 / V085 (committed `9bfb60b2c`) enforce that `TRANSL/@ver` values are in `_ALLOWED_VER_VALUES = {"alt"}`. That's the only documented value so far (Bril Amis Basecamp card, Mar 3, 2026).

**Open: extension policy.** Per the Bril card: *"you'll need to include a list somewhere that explains the possible values (plan for this is TBD)."* If/when new `ver` semantics are needed (e.g., `"literal"`, `"colloquial"`, `"poetic"`), extend `_ALLOWED_VER_VALUES` in `rules/hard.py` and add the rationale to the gitbook spec.

**Action: as needed.** Not blocking; mechanical extension.

---

## 7. V132 on NTU gloss notation — NOT a rule bug; NTU data fix (re-investigated 2026-06-12)

**Roadmap:** B9.4 Gaps list (same-date entry).

**Original framing (2026-06-10, now corrected):** "V132 fires ~2,257 false positives on NTU Bunun W/M TRANSLs where `<X>` is legitimate gloss notation, not entity residue — whitelist it in the rule."

**Corrected finding (2026-06-12).** This is NOT a false positive. The NTU source `Sentences/Bunun/Bunun.xml` is genuinely **double-encoded**: the raw XML contains `&amp;lt;RED&amp;gt;`, which lxml decodes one level into the literal string `&lt;RED&gt;` in `elem.text`. V132's regex requires literal `&lt;`/`&gt;` (it does NOT match bare `<…>`), so it is correctly diagnosing real double-encoding. All 2,237 hits are W/M TRANSL; the intended content is gloss notation (`<RED>` / `<重疊>`) but as stored it renders to any consumer as broken `&lt;RED&gt;`.

**Decision (Joshua, 2026-06-12): keep V132 strict — no rule change.** Whitelisting would mask a real data bug and blind the rule to future double-encoding. The fix is to **un-double-encode the NTU source** (`&amp;lt;`→`&lt;`, `&amp;gt;`→`&gt;` ⇒ decodes to real `<RED>`), after which V132 drops to ~0 on its own. No HARD rule objects to real `<…>` in W/M TRANSL (v067 = M-FORM only, v134 = S-FORM only).

**Action: NTU corpus walk-through branch (deferred, Corpora-touching).** Add a `fix_double_encoded_glosses.py` alongside the existing NTU repair scripts (`apply_manual_corrections.py`, `fix_swapped_gloss_langs.py`); record the step in the NTU README. NOT part of the tooling merge.

**DONE (2026-06-12, branch `ntu-fix-double-encoding`).** Script added as NTU README step 13; decoded 1,109 TRANSL texts + 3 TRANSL `notes` attributes in `Sentences/Bunun/Bunun.xml` (1,122 `&lt;` + 1,118 `&gt;`, one decode level, idempotent, round-trip-guarded). validate_text re-run on the file: V132 = 0 (remaining findings are the known V121/V122/V126/V133 categories). The 3-entity surplus over the element count was double-encoding inside `notes` attributes, which V132 (text-only) never saw.

---

## Cross-reference

For corpus-side data issues surfaced by validators (e.g., specific files needing remediation, missing standard tiers, etc.), see [corpus-cleanup-tasks.md](2026-05-31-corpus-cleanup-tasks.md). That document is for *data* state; this one is for *development* state.
