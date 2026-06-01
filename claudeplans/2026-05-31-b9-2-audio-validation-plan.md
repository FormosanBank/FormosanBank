# B9.2 — Audio validation pipeline plan (rev. 2026-05-31)

**Date:** 2026-05-31
**Roadmap section:** B9.2
**Status:** [MOSTLY DONE 2026-06-01] — structural work for W1–W4, W6–W9 landed on `feature/claude-tooling-phase-0` via the user's `5355d81cc added a number of tests and validators…` commit (B9.2 subagent ran in main tree rather than its worktree branch — see consolidated post-merge cleanup at `06290ab1e`). Per-W status:
- **W1** [DONE] — `QC/cleaning/clean_audio.py` (new) replaces `remove_non_working_audio.py`; dry-run is default; `--apply`, `--also-delete-files`. The 7 xfail tests in `tests/cleaners/test_remove_non_working_audio.py` are removed by replacement, not flip.
- **W2** [DONE] — unified `broken_audio.csv` with `kind` column (`missing`/`unloadable`/`silent`/`invalid_range`); `start >= end` detection added.
- **W3** [DONE] — MP3 silence detection via `ffprobe -af silencedetect`; `is_silent_wav` → `is_silent` dispatches on extension.
- **W4** [DONE] — Finding/Severity integration; rule IDs V100–V105 mapped per the architecture table; HARD exits non-zero, SOFT does not.
- **W5** [PARTIAL] — `QC/validation/validate_audio_quality.py` scaffolded with mocked tests; **real ML pipeline never exercised end-to-end** (`torch`/`torchaudio`/`allosaurus` deferred to `requirements-audio-mt.txt`, not installed). Acceptance criterion "produces a scores CSV from `Corpora/ePark/`" NOT satisfied.
- **W6** [DONE] — `QC/validation/flag_audio_suspicious.py` writes `suspect_audio.csv`; emits SOFT Finding **V120**. ⚠️ V120 collision with B9.4's TR1/V120 — needs renumbering.
- **W7** [DONE] — `QC/utilities/audio_manual_verify.py` (`apply_decision` unit-tested + 3 mocked end-to-end tests for record/resume/back-navigate).
- **W8** [PARTIAL] — `.github/workflows/audio-validation.yaml` created (PR-changed-files blocks on HARD; baseline informational). **Not draft-PR-verified** — `git push` was blocked in the subagent sandbox.
- **W9** [DONE] — `QC/README.md` updated; `requirements-audio-mt.txt` created listing heavy deps (not installed).

Test counts at landing: 59 pass, 1 skip (`torch` import smoke test) on the five audio test files. Full suite green: 255 pass, 1 skip.

OQ resolutions (locked): OQ1 ffprobe for MP3 silence; OQ2 mock ML calls + one slow integration test marked `@pytest.mark.slow`; OQ3 deprecated legacy CSVs (`missing_audio.csv` / `silent_audio.csv` / `non_working_audio.csv`).

Followup landed 2026-06-01 in commit `06290ab1e`: `tests/cleaning/test_clean_audio.py` `_audio_refs` return type fix (`a.get("file", "")` → `list[str]`).
**Supersedes:** earlier draft on the same path that referenced Hunter as the ASR-metrics author — that was wrong; the ASR pipeline is Jacob Ye's, in the `Formosan-Update-Apr_2026` branch of [Formosan-ILRDF_Dicts](/Users/jkhartshorne/Documents/Projects/Formosan/Formosan-ILRDF_Dicts/data_validation/), per the user 2026-05-31.

---

## Goal

Bring audio validation to parity with XML validation, with a small suite of focused scripts:
1. **Always-on broken-audio checks** (file resolves, loadable, not silent, sensible duration) — runs in CI alongside `validate_xml.py`.
2. **On-demand MT quality scoring** — Jacob Ye's four-metric pipeline (CTC, WER, CER, PDM), producing `suspect_audio.csv` that downstream MT training can use to filter unreliable entries.
3. **Interactive verification** — port of `manual_verify.py` for human triage of the suspect worklist.
4. **Cleaner** — single tool that removes the broken entries from XML + disk.

## Decisions locked in (2026-05-31)

| Question | Decision |
|---|---|
| Severity of acoustic-quality metrics (CTC/WER/CER/PDM/words-per-sec) | SOFT |
| Canonical output for downstream MT consumers | `suspect_audio.csv` |
| Broken refs / unloadable / silent / invalid-range | HARD |
| Broken-audio checks run when | Always (CI + standard pipeline) |
| Audio-quality scoring runs when | On-demand only |
| Port Jacob's scripts vs. invoke from his location | Port the three corpus-agnostic ones into FormosanBank |
| ASR model | README defaults (wav2vec2 BASE_960H + Allosaurus universal) now; Formosan-tuned ASR on the deferred list |
| Folder convention | `<Corpus>/XML/` and `<Corpus>/Audio/` (not `Final_XML`/`Final_audio`) going forward |
| TDD discipline | Yes — write tests first for revised validator code |

## Current state

### What already works
- [QC/validation/validate_audio.py](../../QC/validation/validate_audio.py) is more capable than the earlier draft credited:
  - File-existence check (HARD-equivalent) → `missing_audio.csv`.
  - Loadable check via `mutagen.mp3.MP3` / `wave.open` failures (HARD-equivalent) → `non_working_audio.csv` (written from the top-level `main()`, separate from the existence-check output).
  - Silence detection for WAV via `is_silent_wav` (RMS amplitude vs. threshold), behind `--check_silence` flag → `silent_audio.csv`.
  - Words/sec + chars/sec SOFT check with hardcoded thresholds → `audio_duration_issues.csv`.
  - Path resolution with three fallback candidates per file (`resolve_audio_path`).
  - Walks the XML and audio roots from args — does **not** hardcode `Final_XML/Final_audio`.
- [QC/cleaning/remove_non_working_audio.py](../../QC/cleaning/remove_non_working_audio.py) — consumes `non_working_audio.csv`, removes `<AUDIO>` elements from XML. ILRDF-shaped: hardcodes `path.replace("Final_audio", "Final_XML")`, no CLI, `os.remove()` of the audio file itself is **commented out** (line 42).
- [Formosan-ILRDF_Dicts/data_validation/](/Users/jkhartshorne/Documents/Projects/Formosan/Formosan-ILRDF_Dicts/data_validation/) — Jacob's pipeline. Five scripts; the three corpus-agnostic ones (`compute_metrics.py`, `flag_suspicious.py`, `manual_verify.py`) are what we port. The two ILRDF-specific ones (`scrape_one.py`, `build_word_map.py`) attach a headword column; they stay where they are.

### What's missing
- **Zero test coverage** for any audio code in this repo.
- **No MP3 silence detection** — `is_silent_wav` covers WAV only.
- **No `start < end` invariant check** in the XSD or the Python rules. (Earlier draft assumed this existed; it does not.)
- **No Finding-framework integration** for audio. validate_audio.py writes CSVs and stdout; aggregate QC reports don't see audio findings.
- **No unified broken-audio artifact**. Missing / silent / unloadable are spread across three CSVs.
- **No tool to actually delete the audio file from disk** (only `<AUDIO>` element removal exists, and even that is ILRDF-pathed).
- **No port of Jacob's four-metric pipeline.**

## Target architecture

| Script | When | Findings emitted | Output artifact |
|---|---|---|---|
| `QC/validation/validate_audio.py` (refactored) | Always (CI) | HARD: V100 missing, V101 unloadable, V102 silent, V103 invalid range. SOFT: V104 declared-vs-actual duration, V105 words/sec out of range. | Unified `broken_audio.csv` with `kind` column |
| `QC/cleaning/clean_audio.py` (new; replaces remove_non_working_audio.py) | On-demand | — | Modifies XML + removes audio files on disk |
| `QC/validation/validate_audio_quality.py` (port of compute_metrics.py) | On-demand | None (raw scores) | `{Lang}_scores.csv` |
| `QC/validation/flag_audio_suspicious.py` (port of flag_suspicious.py) | On-demand | SOFT (one per suspicious entry) | `suspect_audio.csv` |
| `QC/utilities/audio_manual_verify.py` (port of manual_verify.py) | Interactive | — | `{Lang}_verdicts.csv` |

## Open questions still to resolve

1. **Silence detection on MP3 — which dep?** Three options:
   - `ffprobe -af silencedetect` — already required by validate_audio.py's duration path; lightest add.
   - `pydub` — pleasant Python API, but pulls in pydub + ffmpeg integration code.
   - `torchaudio` — already in Jacob's reqs for W5; heavy, GPU-aware. Reusable for the metrics path.
   Recommend **ffprobe** for `validate_audio.py` (always-on, must stay light); torchaudio dependency is fine for the on-demand metrics scripts.

2. **Test strategy for ML-driven code (W5).** Running wav2vec2 + Allosaurus in CI is not viable (model download, GPU desirable). Options:
   - Mock the model calls; test the orchestration only.
   - Use small fixture audio + a tiny test-only model.
   - Skip W5 tests in CI, run them locally only.
   Recommend **mock the model calls** for unit tests, plus one slow integration test marked `@pytest.mark.slow` that actually runs the pipeline on a small fixture.

3. **Keep the legacy CSVs (`missing_audio.csv`, `silent_audio.csv`, `non_working_audio.csv`) for backward compat?** Anything external consuming them? Recommend: **deprecate and remove** during W2 — `broken_audio.csv` with the `kind` column subsumes them. Grep before deletion.

## Work items (TDD discipline)

Each item is a separable commit. Pattern per W*: write failing test → run to verify fail → implement → run to verify pass → commit. The user has asked specifically that tests come first.

### W1. New `clean_audio.py` replacing `remove_non_working_audio.py`

- **Files:**
  - Create: `QC/cleaning/clean_audio.py`
  - Create: `tests/cleaning/test_clean_audio.py` (create `tests/cleaning/` if it doesn't exist)
  - Delete: `QC/cleaning/remove_non_working_audio.py` and its 7 xfail tests in `tests/validators/`
- **Test cases (W1.1):**
  - Removes the `<AUDIO>` element when entry is in `broken_audio.csv` (regardless of `kind`)
  - Removes the audio file from disk when `--also-delete-files` flag is set
  - Dry-run (`--dry-run`, default ON) leaves XML untouched and prints intended changes
  - Walks `<corpus>/XML/` (not `Final_XML/`); resolves files in `<corpus>/Audio/`
  - CLI surface: `--corpus_path`, `--broken_csv`, `--dry-run`/`--apply`, `--also-delete-files`
  - Empty `broken_audio.csv` → no-op
- **Implementation notes:** mirror `clean_xml.py`'s in-place-edit convention; print a one-line diff summary per file modified.

### W2. `validate_audio.py`: unify broken-audio outputs + add `start < end` + invalid-range detection

- **Files:**
  - Modify: `QC/validation/validate_audio.py`
  - Create: `tests/validators/test_validate_audio.py`
- **Test cases (W2.1):**
  - Missing file → row in `broken_audio.csv` with `kind="missing"`
  - Unloadable file (mutagen/wave failure) → row with `kind="unloadable"`
  - Silent WAV (with `--check_silence`) → row with `kind="silent"`
  - `AUDIO/@start >= AUDIO/@end` → row with `kind="invalid_range"` (new)
  - Clean corpus → empty `broken_audio.csv` (header only)
- **Implementation notes:** preserve the words/sec SOFT outputs in `audio_duration_issues.csv` (separate concern); remove legacy `missing_audio.csv` / `silent_audio.csv` / `non_working_audio.csv` after grepping for external consumers (Open Question 3).

### W3. `validate_audio.py`: MP3 silence detection

- **Files:**
  - Modify: `QC/validation/validate_audio.py`
  - Extend: `tests/validators/test_validate_audio.py`
- **Test cases (W3.1):**
  - Known-silent MP3 fixture → `is_silent` returns True
  - Known-non-silent MP3 fixture → False
  - Corrupt MP3 → None (escalated to `kind="unloadable"` upstream)
- **Implementation notes:** new helper `is_silent_mp3` via `ffprobe -af silencedetect`. Rename `is_silent_wav` → `is_silent` and dispatch on extension. Per Open Question 1.

### W4. `validate_audio.py`: emit Findings into the suite

- **Files:**
  - Modify: `QC/validation/validate_audio.py`
  - Extend: `tests/validators/test_validate_audio.py`
- **Test cases (W4.1):**
  - Validator emits Finding objects with rule_ids V100–V105 mapped per the architecture table
  - HARD findings cause non-zero exit
  - SOFT findings warn but don't fail (mirrors `validate_xml.py`'s exit semantics)
- **Implementation notes:** integrate with the `Finding`/`Severity` dataclasses from `QC/validation/_finding.py`. CSVs continue to be written as artifacts so external consumers (clean_audio.py) keep working.

### W5. Port `compute_metrics.py` → `QC/validation/validate_audio_quality.py`

- **Files:**
  - Create: `QC/validation/validate_audio_quality.py`
  - Create: `tests/validators/test_validate_audio_quality.py`
- **Test cases (W5.1):**
  - Walks `<corpus>/XML/` and `<corpus>/Audio/`
  - Produces a CSV with columns `lang,sentence_id,word,audio_path,transcript,asr_hypothesis,ctc_score,wer,cer,pdm_score`
  - Resumable: re-running skips IDs already present in the output CSV
  - `--metrics ctc,wer,cer` skips PDM column
  - `--sample 5` produces exactly 5 rows
  - `word` column is blank when no word_map.pkl is provided (matches Jacob's design)
- **Implementation notes:** dependency on `data_quality_eval` sibling clone — document in script docstring and `QC/README.md`. Mock wav2vec2 + Allosaurus calls in unit tests (Open Question 2); one slow integration test runs the real pipeline on a tiny fixture. Add `torch`, `torchaudio`, `torchcodec`, `allosaurus`, `Levenshtein`, `unidecode` to `requirements-audio-mt.txt` (separate file — these are heavy and only needed on-demand).

### W6. Port `flag_suspicious.py` → `QC/validation/flag_audio_suspicious.py`

- **Files:**
  - Create: `QC/validation/flag_audio_suspicious.py`
  - Create: `tests/validators/test_flag_audio_suspicious.py`
- **Test cases (W6.1):**
  - Reads a scores CSV; rank-normalizes per-language
  - Default `--worst-pct 5 --min-agreement 1` keeps 5% of entries
  - `--worst-pct 0.5 --min-agreement 3` keeps only sharp-tail multi-metric agreement
  - Output sorted worst-first by `suspicion = (100 - worst_pct_rank) + 10 * (n_triggers - 1)`
  - Each row carries `triggers`, `n_triggers`, `worst_pct_rank`, `suspicion`, `word`
- **Implementation notes:** standardize output filename to `suspect_audio.csv` (per user direction), not Jacob's per-language `{Lang}_scores_suspicious.csv`. Emit one SOFT Finding per suspicious row so the rest of QC has visibility.

### W7. Port `manual_verify.py` → `QC/utilities/audio_manual_verify.py`

- **Files:**
  - Create: `QC/utilities/audio_manual_verify.py`
  - Create: `tests/utilities/test_audio_manual_verify.py`
- **Test cases (W7.1):**
  - Reads `suspect_audio.csv`
  - Records verdicts to `{Lang}_verdicts.csv`
  - Resumes from first unverified row on re-run
  - Mocked-keypress test for c/w/u/p/n/s/b/q decisions
  - `--player ffplay`/`--player afplay` selection
- **Implementation notes:** preserve Jacob's interactive UX; the `b`(ack) and `n`(ote) shortcuts are useful and worth keeping.

### W8. CI integration for always-on broken-audio checks

- **Files:**
  - Create: `.github/workflows/audio-validation.yaml`
- Recommend a new workflow file rather than extending `xml-validation.yaml`: different deps (mutagen, ffprobe), can be skipped for PRs that don't touch audio-bearing corpora.
- HARD findings (`V100-V103`) fail the job; SOFT findings (`V104-V105`) emit warnings.
- Verify in a draft PR before merging.

### W9. `QC/README.md` documentation update

- Document validate_audio.py in the canonical pipeline (between `validate_xml.py` and `orthography_extract.py`).
- Document the on-demand MT-quality pipeline (`validate_audio_quality.py` → `flag_audio_suspicious.py` → `audio_manual_verify.py`) in a separate "MT data prep" section.
- Document the `data_quality_eval` sibling-clone requirement and the heavy `requirements-audio-mt.txt`.

## Out of scope for B9.2

- Audio re-encoding, sample-rate normalization, format conversion.
- ASR-driven re-transcription (generating new transcripts from audio).
- The corpus-specific ILRDF prep scripts (`scrape_one.py`, `build_word_map.py`) — they stay in Jacob's dev repo.
- Using a Formosan-tuned ASR model (deferred — see "future work").

## Deferred to "future work"

- **Formosan-tuned ASR model.** README's wav2vec2 BASE_960H is off-the-shelf and produces only relative anomaly scores. A Formosan-fine-tuned ASR would change the metrics from "relative" to "absolute" quality. Add to corpus-cleanup-tasks list or a separate future-plan doc once we know more about model availability.

## Acceptance criteria

- `pytest tests/validators/test_validate_audio.py tests/validators/test_validate_audio_quality.py tests/validators/test_flag_audio_suspicious.py tests/cleaning/test_clean_audio.py tests/utilities/test_audio_manual_verify.py` — all green with ≥3 substantive cases per file.
- `validate_audio.py` produces a single `broken_audio.csv` with a `kind` column, integrated with the Finding framework.
- `clean_audio.py` cleanly replaces `remove_non_working_audio.py`; the 7 xfails are removed (by replacement, not flip).
- `validate_audio_quality.py` runs against `Corpora/ePark/` (audio-bearing) and produces a scores CSV. Output quoted in the PR description, not just "exited 0".
- `flag_audio_suspicious.py` produces `suspect_audio.csv` from that scores CSV.
- Always-on broken-audio CI is wired and verified in a draft PR before merge.
- `QC/README.md` lists validate_audio.py in the canonical pipeline and the MT-quality pipeline in a separate section.
