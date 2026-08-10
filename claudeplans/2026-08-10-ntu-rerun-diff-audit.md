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

## Addendum (same day): F1–F3 fixed and verified; F4–F6 quantified

- **F1/F2 fixed** in `run_parsers.py` (new `run_normalize()` pass): M ids pinned to
  `<Wid>M<n>` — validated exact for all 198,185 published M elements, zero
  exceptions — and the 16-entry `DIALECTS` table pins the published dialect
  attributes (set-if-absent; parser-set values already matched published where
  present; `Sentences/Bunun` is Junqun per maintainer determination despite the
  source folder saying Isbukun). Verified against the regen: after normalization,
  `apply_manual_corrections.py` applied **50 formerly-dead corrections** (all
  fills, the impostor deletion, id-targeted repairs, and the 12 `AUDIO_FIXES`);
  byte-equal sentences rose 2,175 → 5,006; TEXT-attr diffs 0/193; FORM-class rows
  13 → 7, the seven being exactly the expected set (3 parser word-recoveries,
  the `*(malra)` restoration, `S_7` (F5), 2 Teaching-Weaving punctuation drifts).
- **F3 fixed** in `remove_no_audio_elements.py`: pattern now matches the encoded
  and decoded sentinel (61 leaked elements verified removed). Related residue:
  the same `d27c1cc29` parser change also writes *real* audio `file` attributes
  decoded (`A1-3-1-6 n.mp3` vs published `A1-3-1-6%20n.mp3`; 17 elements, `url`
  unchanged) — decide at regen time whether to normalize (audio filenames embed
  these).
- **F5 root cause corrected**: not parser segmentation — step 18 splits the
  W-level PHON on `-` to build per-morpheme PHONs, but current `add_phonology`
  strips `-`/`=`/`<>` from PHON, so PHON yields 1 piece against FORM's 3 (the
  `[3, 3, 1, 1, 3, 3]` assertion). At regen time, let step 18 skip PHON piece
  assignment and rely on `make.sh`'s final `add_phonology` refresh.
- **F4 quantified** (element level): of 732 differing TRANSL elements, 691 are
  glyph-only (`「」`→`＂`, `[...]`→`(...)`, punctuation/whitespace); 41 are
  parenthetical-note extraction edge cases (junk tails), regen usually cleaner.
- **F6 quantified**: of 75,144 differing PHON elements, 74,884 differ only by the
  stripped markers (`=`, `<>`, `-`); 224 are contextual-rule improvements now
  applying across removed boundaries (`t<n>gesa`→`tŋesa`, `s<in>aipuk`→`ɕinaipuk`);
  36 involve `*` (nulls/unknown chars — superseded by the new pipeline's null
  handling).
- **Remaining regen-time worklist**: a few gloss-shift cells where FILL rightly
  refused fresh-parse junk (earthquake `S_194` W1M2/M3, home `S_69`, relatives
  `S_70`) — extend the GLOSS_SHIFT table with the fresh-parse cell contents; the
  script's no-match/fill-skipped output pinpoints them. Step 18 CONFIG per F5.
  **And: merge `main` into `feature/shared-source-phonology` first** — the branch
  lacks main's parser fixes (`149537a10` starred-parens, `d27c1cc29` audio refs).

## Addendum 2: full NEW-pipeline regen via make.sh (2026-08-10, after merging main)

With main merged into `feature/shared-source-phonology` and all fixes applied,
`make.sh` ran end-to-end (audio skipped) and the output was compared to the
published corpus. **Every difference is either an intentional new-pipeline
change or a verified improvement; nothing was lost.** Of 20,130 sentences:
2,067 byte-equal, 17,308 differ only in regenerable tiers (PHON new-style,
standard-FORM C012/null/accent handling, W/M id scheme — all by design), and
755 content rows, fully triaged:

- 729 TRANSL: 696 glyph normalization (`「」`→`＂`, `[...]`→`(...)`), 33
  parenthetical-note junk-tail cleanups — parser normalization, regen cleaner.
- 7 FORM: `ø`/`Ø` → `∅` canonicalization (by design, null-morpheme spec).
- 11 FORM: NEW `borrow_segmentation` recoveries (e.g. Bunun M `nii=ik` + empty
  shell → `nii` + `ik`) — unlocked by routing the reproducibility guard through
  the current `phonologize` (13 repairs total; 2 restore published repairs the
  guard had lost, 11 are net-new).
- 4 FORM: parser recoveries of source words publication dropped (Kanakanavu
  `arivureemaku`, `na`; Rukai `malra` — the deferred starred-parens fix).
- 2 FORM: Kavalan Teaching-Weaving punctuation drift (`Raw.`→`Raw`, `o...`→`o`).
- 1 FORM: Tsou `wu—` → `wu-` (clean_xml dash canonicalization, by design).
- 1 AUDIO: `00_Seediq_A2-3-3` file attr — parser override added, converges on
  the next parse.

Bugs found and fixed by this run (commit 999c7635e): empty-string M PHON broke
later steps' round-trip guards (steps 19/20 silently skipped Rukai.xml — the
make.sh run initially produced 0 of step 19's 3 collapses); the final
add_phonology refresh leaves files outside the lxml convention (make.sh now
normalizes after it); `_phon_regen.py` / `borrow_segmentation.py` re-implemented
an obsolete PHON vintage (now thin wrappers over `load_profile`/`phonologize`,
dialect-aware).

Also observed: **9 published files fail the lxml round-trip guard today** (incl.
the four Tsou files rewritten by the b94ebb942 add_phonology run) — they have
been silently immune to every post-hoc repair script; the regen re-serializes
them. And on the published corpus the modernized `borrow_segmentation` would
now recover 8 more style-invariant words (4 files) — left for the regen rather
than applied post-hoc.

## Artifacts

Scratch (session-local, disposable): worktree `scratchpad/ntu-old` (regen output in
`Corpora/NTUFormosanCorpus/XML`), `rerun2.log`, `cmp2_summary.txt`,
`cmp2_content.csv` (923 rows), `cmp2_details.txt` (per-S diffs), `compare_ntu.py`
(the comparer, reusable).
