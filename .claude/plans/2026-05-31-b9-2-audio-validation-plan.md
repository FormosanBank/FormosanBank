# B9.2 — Audio validation pipeline plan

**Date:** 2026-05-31
**Roadmap section:** B9.2 (Audio category of the six-category validator audit)
**Status:** Plan; not yet started.

---

## Goal

Bring the audio-validation pipeline to parity with the XML-validation pipeline so the maintainer can run one command and know "does this corpus's audio match the spec, and is anything broken, missing, or implausible?"

## Current state

**Exists:**
- [QC/validation/validate_audio.py](../../QC/validation/validate_audio.py) — primary validator. Hard-checks: audio files referenced by `AUDIO/@file` resolve on disk; `start < end`; durations are non-negative. Soft-checks: declared duration vs. actual duration agreement.
- [QC/cleaning/remove_non_working_audio.py](../../QC/cleaning/remove_non_working_audio.py) — companion remover. **Has 7 `xfail(strict=True)` tests in [tests/validators/](../../tests/validators/) that encode the intended refactor.**

**Missing:**
- No unit-test file `tests/validators/test_validate_audio.py` — coverage is zero.
- No words-per-second soft check (catches mismatched alignment when `<W>` count vs. `(end - start)` produces implausible speech rates).
- "Hunter's ASR comparison script" — referenced in pre-compaction conversation as a tool that compares the transcript against ASR output, but its location is unknown. Could be in this repo under a non-obvious name, in `~/Documents/Projects/Formosan/Formosan-*/`, or never extant.
- No `clean_audio.py` companion. The roadmap mentions it as a "fix things `validate_audio.py` finds" tool but it does not currently exist.

## Open questions to resolve before coding

1. **Hunter's ASR script: find or rebuild?** Before designing anything new, spend ≤30 min searching:
   - `rg -i "asr|whisper|wav2vec" QC/` and across `../Formosan-*/`
   - Check sibling repos' READMEs and `*.ipynb` files
   - Ask Hunter (or look at recent PRs / issues) if not found
   If found: decide whether to port into `QC/validation/validate_audio_asr.py` (separate hard validator) or `QC/utilities/compare_audio_asr.py` (advisory, slow). If not found: descope to a roadmap follow-up; do not rebuild speculatively.

2. **Should the words/sec check be HARD or SOFT?** Speech rate varies hugely across Formosan languages and speakers; a hard threshold will produce false positives. Recommend SOFT with a wide tolerance (e.g., flag if rate < 1 word/sec or > 6 words/sec).

3. **`clean_audio.py` scope.** Two possible designs:
   - (a) thin wrapper that runs `validate_audio.py` and removes broken refs (mirrors `remove_non_working_audio.py`).
   - (b) thicker tool that also trims/normalizes audio files themselves.
   The roadmap's intent (per the conversation) was (a). Confirm before scoping (b).

## Concrete work items

In dependency order. Each item is a separable commit.

### W1. Tests for `validate_audio.py`

- **File to create:** `tests/validators/test_validate_audio.py`
- Cover, at minimum:
  - File-exists hard check (build a temp corpus with an `AUDIO/@file` pointing at a nonexistent path → expect HARD finding).
  - `start < end` invariant (swap them → expect HARD finding).
  - Negative duration (start > end → expect HARD finding).
  - Declared vs. actual duration agreement (mock the actual duration; assert SOFT when they diverge by >tolerance).
  - Clean case (everything valid → zero findings).
- Pattern: mirror `tests/validators/test_validate_xml.py` — same Finding dataclass, same `tmp_path` corpus-building idiom.

### W2. Refactor `remove_non_working_audio.py` to clear the 7 xfails

- **File to edit:** `QC/cleaning/remove_non_working_audio.py`
- **Driver:** the 7 `xfail(strict=True)` tests in `tests/validators/`. Read them first; the test names + assertions specify the intended behavior.
- Flip them from xfail → pass; do NOT change the tests themselves except to drop the xfail decorator.
- If any test reveals a real ambiguity in spec, surface it before changing — don't silently re-interpret.

### W3. Words/sec soft check in `validate_audio.py`

- **File to edit:** `QC/validation/validate_audio.py`
- Per `<S>` (and `<W>`?) that has both an `<AUDIO start end>` and a wordcount derivable from children:
  - rate = wordcount / (end - start) in seconds
  - Emit SOFT finding if rate < 1 or > 6 (conservative defaults; revisit after first corpus run).
- Test file: extend `tests/validators/test_validate_audio.py`.

### W4. Hunter's ASR script — locate or descope

- Search per the open question above.
- If found: write a short porting plan as `.claude/plans/2026-XX-XX-asr-comparison-port.md`; do not port in this work item.
- If not found: add an entry to `.claude/plans/2026-05-31-corpus-cleanup-tasks.md` titled "ASR comparison validator (deferred)" and move on.

### W5. `clean_audio.py` (only after W2 and the open question is resolved)

- **File to create:** `QC/cleaning/clean_audio.py`
- Mirror `remove_non_working_audio.py`'s CLI shape so the two stay learnable as a pair.
- Test file: `tests/validators/test_clean_audio.py`.

## Out of scope for B9.2

- Audio re-encoding, sample-rate normalization, or format conversion. That's a different problem (data conditioning, not validation).
- ASR-driven re-transcription. If Hunter's script does comparison, that's a validator; generating new transcripts from audio is a separate initiative.

## Acceptance criteria

- `pytest tests/validators/test_validate_audio.py` passes with ≥6 substantive cases.
- The 7 remove_non_working_audio xfails are flipped to passing tests; no new xfails added.
- `python QC/validation/validate_audio.py by_corpus --corpus <Name> --corpora_path Corpora` runs against at least one audio-bearing corpus (ePark, NTUFormosanCorpus) and produces a finding report — quoted in the PR description, not just "exited 0".
