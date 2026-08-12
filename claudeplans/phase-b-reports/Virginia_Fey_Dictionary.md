# Virginia_Fey_Dictionary regeneration — ROUND 2 + FIXUP (sweep/g1-fey, 2026-08-11)

Redo of the Group 1 sweep turn for the Fey (1986) Amis dictionary (ami,
dialect Xiuguluan, 1 XML file; hand-cleaned, **non-regenerable**, POL-035
class) under the updated maintainer rulings, plus the 2026-08-11 overnight
fixup batch: (a) the duplicated sentence id `S3797` is fixed by a committed
script; (b) `standardize --remove_accents` replaces `--copy`; (c) the whole
pipeline is wrapped by a committed `CodeAndDocs/make_xml.sh`; (d) **the
corpus is now deduplicated** (POL-022 reference resource) via a declared
`remove_duplicate_sentences` final step; (e) the no-op `apply_manual_edits`
step is removed; (f) the README is trimmed to pipeline + data-user content.
Supersedes the round-1 report.

## POL-035 snapshot + POL-038 id fix

Pristine pre-run `XML/` copied byte-identically (md5-verified) to
`CodeAndDocs/pre_correction_snapshot/` **before** any script ran. The
snapshot was then modified exactly once, **only via the committed script**
`CodeAndDocs/fix_duplicate_ids.py` (POL-038): the second document-order
occurrence of `S3797` ("namanan a demak", line 16905) was re-idd to
**`S3797b`**; the first ("kananaman a demak") keeps `S3797`. Verified: the
only byte difference between the snapshot and pristine HEAD is that one id
attribute; a second script run is an idempotent no-op.

**Id scheme choice — letter suffix, not next-free integer**: every existing
id matches `^S[0-9]+$`, so `S3797b` cannot collide (script verifies
non-collision anyway); a next-free integer would silently claim a gap in the
upstream amis-data numbering (gaps are meaningful) and be indistinguishable
from a genuine source-numbered entry. The suffix makes the administrative
re-id self-evident. This is a deliberate, announced **POL-037** change —
exactly one id affected. (Per the README-content ruling, the rationale
lives here and in the committed script, no longer in the corpus README.)

## Pipeline (`CodeAndDocs/make_xml.sh`, post-fixup)

`XML/` is regenerated FROM the snapshot content: make_xml.sh restores
`XML/` from the snapshot (snapshotting itself is not a pipeline step), then
runs, in order: `fix_duplicate_ids.py` (no-op guard — fix already in the
snapshot) → `clean_xml` → `standardize --remove_accents` → `add_phonology
--orthography Ortho113` → **`remove_duplicate_sentences.py by_path --apply`**
(new final step, POL-022). `apply_manual_edits` was **removed** per the
no-spurious-no-op-steps ruling (no `manual_edits.xml` exists; POL-030 still
requires adding the step back if one is ever created). FormosanBank root is
parameterized (arg 1, default `../../..`; `PYTHON` env override).
Deterministic and idempotent: two consecutive full runs produce
byte-identical output (md5 `514346dc…` both times).

## Dedup (POL-022 fixup ruling)

Dictionary → reference resource → duplicate-free. Dry run inspected before
apply. **9 S elements dropped** (within-file repeats of an earlier
sentence's standard-FORM text; first occurrence kept):

| removed | kept (first) | text |
|---|---|---|
| S1900 | S1899 | hawitid cingra. |
| S2843 | S1862 | herek no lahok |
| S3026 | S3025 | Maletep ako ko demak nira. |
| S5023 | S4389 | parikor to sowal |
| S5142 | S5141 | 'opoen ako ko wawa. |
| S5280 | S5278 | O salikaka ita cingra. |
| S5703 | S5702 | so^so ko kolong iso. |
| S6241 | S3941 | Tatiih ko ngoyos nira. |
| S6916 | S3833 | panayat to romi'ad |

S count 2,049 → **2,040**. **Token delta: −32** (count_tokens corpus
rules, Amis/Xiuguluan: 9,078 → 9,046) — expected and entirely attributable
to the 9 dropped sentences.

**Distinct TRANSLs preserved (maintainer ruling 2026-08-11, POL-025)**:
8 of the 9 pairs had *differing TRANSLs* (the same Amis example glossed
under different headwords, e.g. S5280 "He belongs to our family." vs
removed "He is a part of the Christian community."); only S6916/S3833 was
translation-identical. `remove_duplicate_sentences.py --apply` now merges
every TRANSL the survivor lacks into it as `ver="alt"` before deleting
the duplicate: **14 TRANSLs merged** this run (corpus-wide `ver="alt"`
count 696 → 710; the corpus already used `ver="alt"` for its own
multi-gloss entries, so the mechanism is idiomatic here). Nothing from
the removed sentences is lost.

**POL-022 consequence**: with the dedup step declared in CodeAndDocs, any
future duplicate finding for this corpus is **HARD** (verified live:
`validate_duplicate_sentences` now reports "corpus pipeline declares dedup
— leftovers are pipeline defects": within-file=0, cross-file=0).

## Diff audit vs git HEAD — 100% classified, 0 unclassified

Element-level (pre-dedup stage, unchanged from round 2): every S matched
positionally (2,049 = 2,049); TEXT attributes identical; no child attribute
changed; stray text nodes unchanged. Changed values: 4,034 PHON + 1 id
attribute, all classified:

| class | count | why expected |
|---|---|---|
| **dedup: whole-S removal** | **9 S** (73 element lines) | POL-022 fixup ruling; ids/texts tabled above |
| **S3797 re-id → S3797b** (id attribute only) | 1 | ruled POL-037 fix, carried forward from the snapshot |
| PHON legacy `x~y` → `[x\|y]` notation only | 344 + 344 (orig+std) | 2026-08 PHON notation migration |
| PHON notation + punctuation dropped | 1,609 + 1,609 | same, plus new `phonologize` carries no punctuation into PHON |
| PHON punctuation dropped only | 64 + 64 | no variant sounds, punctuation only |
| accent removal (`--remove_accents` vs `--copy`) | 0 | corpus has 0 combining marks / null glyphs / hyphens / M-tier — structurally no-op |

FORM original/standard: 0 changed outside removed S. TRANSL: 0 changed
outside removed S. Vowel-length colon (`ana:`) correctly kept in PHON.
Serializer artifacts (content-preserving): XML declaration now
`<?xml version='1.0' encoding='UTF-8'?>` (the dedup writer is the last to
serialize, replacing round 2's `<?xml version="1.0" ?>` note); S1117
mixed-content re-wrap (stray `、` byte-preserved); no newline at EOF.
**UNEXPLAINED: none.**

## Quote corrections — ZERO (re-verified)

Amis is armed (edge-filtered hand-validated dictionary, 505 entries;
`resolve_language("ami","Xiuguluan")` → Amis). The production run wrote no
`CodeAndDocs/quote_corrections.csv`. Independent read-only replay over all
2,049 original FORMs: 0 rewrites, 0 corrected positions, 0 ambiguity flags
across 908 apostrophes (773 sentences). Structural, not lucky: 0 sentences
have a quotation-bearing TRANSL, so the tq==0 guard suppresses conversion
everywhere. Matches Phase A's "Total expected Group 1 classifier
corrections: 0".

## Warning sidecars (POL-033)

None produced by any step (no `cleaner_warnings.csv`,
`standardize_warnings.csv`, or `quote_corrections.csv`).

## Validators before → after (re-run post-dedup)

- `validate_xml`: **HARD 3 → 1** (pre-sweep → now; unchanged by dedup,
  1 → 1). Cleared: V000 duplicate-key `S3797` and V039
  id_unique_within_file. Remaining: V000 ×1 — the pre-existing stray `、`
  text node inside S1117 (line 1507), **left as is per instruction** (no
  ruling yet; the character sits between two zho TRANSLs and belongs to
  neither — still needs a maintainer call).
- `validate_text`: SOFT 3,930 → 24 (pre-sweep → now; unchanged by dedup,
  24 → 24 — none of the 9 removed S carried a finding). V147
  phon_legacy_tilde_variant 3,906 → 0; V122 parens_slashes_anywhere 24 →
  24, byte-identical finding set (all in TRANSL; POL-024 review items).
- `validate_duplicate_sentences`: 9 within-file groups → **0** (and now
  HARD-scoped for this corpus, see above).

## README (fixup ruling 3 applied)

Trimmed to pipeline + data-user content: corpus description, source,
non-regenerability + snapshot existence (brief), 5-step pipeline with
one-per-step explanations (fix_duplicate_ids listed with a one-line
description; new dedup step with its POL-022 HARD note), reproduction
instructions, sidecar handling, Notes/References/License. **Removed**: the
POL-037/duplicate-id history-and-rationale section, the
`--remove_accents`-vs-`--copy` comparison, the `[x|y]`/PHON project-wide
notation notes, the measured-zero quote-correction essay, the POL-038
narrative, and the `apply_manual_edits` step. Sentence count in the header
updated to 2,040.

## Verdict

All changed values classified into expected categories (100%), the dropped
sentences being their own expected category (9 S, −32 tokens); duplicate-id
HARD findings cleared (3 → 1, remainder is the reported-only `、` node);
in-scope duplicates now 0 with HARD enforcement; quote corrections zero as
expected. **UNEXPLAINED: none.** Open item for maintainer: 8/9 removed
duplicates carried distinct TRANSLs (see Dedup section) — merge-back into
the kept entries is possible from the snapshot if desired. Ready for
review/merge. Post-merge: GitBook corpus page check (sweep ruling 4).
