# NTU rerun-and-diff audit (2026-08-10)

**Question.** README step 8 ("manual V121 review") is undocumented hand work. Can we
back out what it actually did by rerunning the recorded pipeline and diffing against
the published corpus — and fold anything found into `apply_manual_corrections.py`?

**Method.** In a scratch worktree at `main` (old QC code, current parsers), the full
recorded pipeline was rerun from the source JSONs: `run_parsers` →
`remove_no_audio_elements` → `clean_xml` → `standardize --copy` →
`remove_stress_accents` → `add_phonology` → steps 4–7, 9–20 (audio download skipped;
serialization converted at each boundary, since step 4 expects the parsers' minidom
style while steps 5–20 expect lxml). The result was compared per-`<S>` (c14n,
whitespace-insensitive) against the published XML, with PHON, standard-tier FORM and
W/M id values normalized out as regenerable/derived.

## Headline result

**There are no unrecorded hand edits in the published corpus beyond the seven audio
boundary fixes of commit `1817ae39e`** (13 AUDIO attributes across 6 Stories files —
now recorded in `apply_manual_corrections.py`'s `AUDIO_FIXES` table). Step 8 never
produced edits; its V121 work became scripted steps 15–20 and the residue is
documented in step 20's notes. Every other difference between the rerun and the
published corpus traces to a script/parser vintage change, itemized below.

Comparison totals (19,232 published S elements, 193 files on both sides):
2,175 byte-equal; 17,132 differ only in PHON / standard FORM / W-M id scheme
(regenerable tiers); 923 rows of "content" difference, all accounted for:

| count | class | explanation |
|---|---|---|
| 661 | TRANSL | quote-glyph and parenthetical-notes extraction drift (see F4) |
| 57 | TRANSL other | same two parser-vintage families on inspection: `「」`→`＂`, `[...]`→`(...)`, junk-tail cleanup around extracted notes |
| 61 | AUDIO | "no-audio" sentinel elements the regen failed to remove (F3) |
| 29 | AUDIO real | 12 S's = the known `1817ae39e` boundary hand edits ✓; 17 Grammar S's = `d27c1cc29` URL-reference repairs reproduced differently by the updated `parse_grammar.py` |
| 100 | TEXT-attrs | all exactly the `dialect` attribute, missing from regen (F2) |
| 13 | FORM classes | 6 = gloss-shift repair targets left unrepaired because id-targeted table entries no-match (F1); 3 = parser recoveries of source words publication had dropped (Kanakanavu `arivureemaku`, `na`; deferred-regen improvements); 1 = Rukai `*(malra)` restoration (the deferred starred-parens fix, `149537a10` ✓); 1 = Rukai S_7 unexpanded (step 18 crash, F5); 2 = Kavalan Teaching-Weaving punctuation/overlap-marker drift (`Raw.`→`Raw`, `o...`→`o`) |
| 2 | only-published | `S_7-alt2`/`-alt3` — absent because step 18 crashed (F5) |

## Findings to fix before a real regeneration

**F1 — M-id scheme is not reproducible (blocks id-targeted corrections).** The
published corpus uses `<sid>_W0M1`-style M ids, but the committed parsers emit
`<sid>_W0_M0_0` style (and did already at 2026-06-01, before the 2026-06-10
regeneration commit `18868920e`) — the id-normalization pass that produced the
published scheme was never committed. Consequence: the 54 element-id-targeted
entries in `apply_manual_corrections.py` (GLOSS_SHIFT precision entries, FILLS,
DELETE_W) silently no-match on a fresh parse, leaving those 6 sentences unrepaired.
Fix: add an id-normalization step to the parsers (or a post-pass script) that
renames `_W{i}_M{j}_{k}` → `_W{i}M{n}` (1-based, document order), OR migrate the
table entries to a scheme-independent addressing. S ids ARE reproduced faithfully.

**F2 — `dialect` TEXT attributes are not reproduced.** All 100 dialect-bearing
files lose the attribute on regen (it was added by hand/`c8a6b411a`-era work).
Needs a recorded metadata step (e.g. a per-file dialect table applied after
parsing); language identity for Seediq/Truku and the per-dialect stats depend on it.

**F3 — `remove_no_audio_elements.py` regression.** The updated `parse_grammar.py`
(since `d27c1cc29`) writes the no-audio sentinel *decoded* (`file="沒有音檔"`), but
the script's pattern matches only the URL-encoded form — 61 sentinel AUDIO elements
leaked into the regen. Fix the pattern to match both forms.

**F4 — parser normalization drift in TRANSL (~718 sentences).** Current parsers
normalize CJK corner quotes `「」` to `＂` and square brackets `[...]` to `(...)`,
and extract parenthetical notes more cleanly than the published vintage (published
sometimes retains junk tails like `例句比較)`). Regen output is generally *better*;
accept as an expected published-diff class when regenerating, or pin down desired
quote convention first.

**F5 — step 18 (`expand_word_level_alternatives`) crashes on fresh parses.** Its
per-sentence CONFIG hard-codes the published-vintage (mis)segmentation of Rukai
`20200528-FW-Yongfu_S_7`; the current parser segments the slashed word differently
(assertion `[3, 3, 1, 1, 3, 3]`). Update CONFIG against the new parse at regen time
(and re-check whether step 16 can now handle it instead).

**F6 — PHON vintage.** Published PHON keeps clitic `=` and infix `<>` markers;
current `add_phonology` strips them. Irrelevant under the new shared-source-
phonology pipeline (all PHON is regenerated), but explains the bulk of the 17k
derived-only rows.

## Artifacts

Scratch (session-local, disposable): worktree `scratchpad/ntu-old` (regen output in
`Corpora/NTUFormosanCorpus/XML`), `rerun2.log`, `cmp2_summary.txt`,
`cmp2_content.csv` (923 rows), `cmp2_details.txt` (per-S diffs), `compare_ntu.py`
(the comparer, reusable).
