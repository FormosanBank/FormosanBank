# Safolu-Amis-Dictionary regeneration (sweep/b2-safolu, 2026-08-12)

Phase B batch 2 turn for the Safolu (Tsai Chung-Han) Amis dictionary (ami,
dialect Coastal, 1 XML file, 49,181 S; no W/M). Group 2 bespoke pipeline
(declared dedup). Addresses issue #104 ("regenerate PHON with migrated
variant notation").

**Fixup pass (2026-08-12, second turn)** applied two maintainer rulings:
original-tier PHON is now generated as well (§ "PHON tiers"), and the
corpus's two competing entry points were collapsed into one (§ "Single
entry point"). All other results below were re-derived from a fresh run of
the consolidated pipeline and are unchanged.

## POL-035 snapshot

The from-source build (`make sources` + `make safolu`) needs network to
fetch the pinned upstream checkouts into `_sources/` — **not runnable from
committed inputs** → snapshot mandatory. Pristine `XML/` copied
byte-identically (md5 `201a8d6a…` both sides, verified) to
`CodeAndDocs/pre_correction_snapshot/` before any script ran. The snapshot
is untouched since (no POL-038 scripts needed).

## Single entry point (`CodeAndDocs/make_xml.sh`)

The corpus had **two** entry points — `make_xml.sh` (snapshot → enrichment)
and a `Makefile` whose `qc` target re-listed the same four enrichment steps
alongside the from-source `sources`/`safolu`/`validate` targets. Collapsed
to the script, which is the repo-wide convention (6 other published corpora
ship `CodeAndDocs/make_xml.sh`; none ship a Makefile). **`Makefile`
deleted**; its from-source targets moved into `make_xml.sh --from-source`
(fetch → build → `validate_formosanbank_xml.py` → `audit_source_coverage.py`
→ Final_XML-is-XML-only check), which then calls the *same* `enrich()` shell
function the default mode does, so the four QC steps exist in exactly one
place. Bonus fix: the Makefile's `Final_XML` paths were relative to the
caller's cwd while the Python scripts anchor `Final_XML/` at the corpus root
— the `validate`/`qc`/`check-final-xml-only` targets were broken from the
published layout; the script uses the corpus-root path. `FORMOSANBANK_ROOT`
and `PYTHON` are now env overrides (the old positional arg is gone).

Two modes, one command:

```sh
CodeAndDocs/make_xml.sh                 # canonical: snapshot → XML/
CodeAndDocs/make_xml.sh --from-source   # network: upstream → Final_XML/
```

Default mode regenerates `XML/` FROM the snapshot: restore → `clean_xml`
(Amis quote-correction armed) → `standardize --remove_accents` (per the
mid-sweep ruling, replacing the README's old `--copy`) → `add_phonology
--orthography Ortho113` (see below) → `remove_duplicate_sentences by_path
--apply` (POL-022 declared dedup). No `apply_manual_edits` step (no
`manual_edits.xml` exists; per the no-spurious-no-op-steps ruling).
Deterministic and idempotent: two consecutive full runs byte-identical
(md5 `3bac0109…`). The old double-`clean_xml` order is retired. Profile
verified by inspection: Ortho113/Amis.tsv Coastal column carries migrated
`[o|u]` / `[ɬ|ɮ]` cells (POL-013). Dedup is still declared in CodeAndDocs
after the Makefile deletion — re-verified live (HARD banner, see below).

## PHON tiers — original + standard, both Ortho113

Maintainer ruling: generate original-tier PHON too, from Ortho113. In
`add_phonology.py` the standard tier is always driven by the language's
declared standard scheme (`standards.csv`: Amis → Ortho113); the original
tier is generated **only when `--orthography` is passed**, and that flag
names the folder used for it. So the invocation is:

```
add_phonology.py --orthography Ortho113 --corpora_path <XML>
```

`--orthography Ortho113` is what turns original PHON on, and pointing it at
Ortho113 (rather than a source-specific table) is right here because the
source spelling already *is* the Ortho113 letter set — the corpus has no
separate source orthography. `--target_column` was not needed: both profiles
resolve the column from `dialect="Coastal"`, and Amis.tsv has a `Coastal`
column, so both tiers use it. `--preserve-existing-original` was **not**
used: it exists to protect expert-supplied source PHON, and this corpus had
**no** original PHON at all (verified: 0 `PHON kindOf="original"` on main),
so there was nothing to preserve and every original PHON must be generated.

Verification after the run:

- 49,181 `PHON kindOf="original"` — one per S, **every** S that has a
  standard PHON also has an original PHON (0 gaps), no W/M tiers exist.
- Independent recomputation: `phonologize(original FORM, Ortho113/Amis,
  Coastal)` == committed original PHON for **all 49,181** (0 mismatches);
  same check on the standard tier also 0 mismatches.
- Placement: all 49,181 S have child order `FORM original, PHON original,
  FORM standard, PHON standard` (0 deviations).
- Spot-checks confirm derivation from the *original* FORM and the Coastal
  column: `O maan ko 'a'acaen iso saw?` → `[o|u] maan k[o|u] ʡaʡaʦaən
  is[o|u] saw` (`o`→`[o|u]`, `'`→ʡ, `c`→ʦ, `e`→ə, punctuation dropped);
  `Fafutingen a fanaw` → `fafutiŋən a fanaw` (`ng`→ŋ); `Misalalanay a koli`
  → `misaɾaɾanaj a k[o|u]ɾi` (`l`→ɾ, `y`→j).
- The two PHON tiers are currently **identical string-for-string**, because
  original FORM == standard FORM for all 49,181 S (nothing to transliterate;
  0 combining marks in the source, so `--remove_accents` is a no-op here).
  Not a redundancy bug: each tier is generated from its own FORM and they
  will diverge the moment a correction separates the FORMs. Documented in
  the README so a data user is not surprised.

## Diff audit vs git HEAD — 100% classified, 0 unclassified

Element-by-element by S id (sequence identical, 49,181 = 49,181; TEXT
attributes identical; no S removed; FORM original and TRANSL byte-identical
everywhere). Added elements: 49,181 PHON original. Changed elements: 48,979
PHON standard + 48 FORM standard (202 PHONs unchanged — short forms with no
variant letter or punctuation):

| class | count | why expected |
|---|---|---|
| **PHON original ADDED** | **49,181** | this turn's ruling: original-tier PHON, Ortho113/Coastal, one per S (§ "PHON tiers"); the only new category vs the first turn |
| PHON legacy `x~y` → `[x\|y]` + punctuation dropped | 46,879 | POL-013 notation migration (`o~u`→`[o\|u]`, `ɬ~ɮ`→`[ɬ\|ɮ]`) + new `phonologize` carries no punctuation |
| PHON punctuation dropped only | 1,502 | no variant letters in the sentence |
| PHON notation only | 595 | no punctuation in the sentence |
| PHON `…`/`‧` no longer `*` | 3 | old tool mapped U+2026/U+2027 to `*`; new drops them as punctuation (S07322, S32560, S33251); inside the notation class |
| FORM std hyphen restored | 48 | old pipeline stripped `-` from the standard tier; current standardize keeps source hyphens in an unsegmented corpus (`Kofit19`→`Kofit-19`, `sifu`→`si-fu`, …). New std == original in all 48 |

Independent verification: `phonologize(<tier> FORM, Amis/Coastal)` ==
committed PHON for **all 49,181** sentences on **both** tiers (0
mismatches). Vowel-length `:` and unknown-char `*` correctly retained in
PHON. Cross-check against the first turn's output: the new XML differs from
it by *exactly* the 49,181 added original PHON elements and nothing else
(0 other adds/removes/changes) — every previously classified class carries
over untouched. **UNEXPLAINED: none.**

## Quote corrections — ZERO rewrites

Amis armed (edge-filtered hand-validated dictionary). **0 c031/c032
rewrites** — no `quote_corrections.csv` was written, so there is nothing to
commit and nothing outside the reviewed set to justify. The only
Safolu-flagged sentence in `quote_review_nonwiki_amis.md` (S00963,
AMBIGUOUS, amb=3, FORM-only) keeps its FORMs byte-unchanged (only its PHON
changed, in the notation class). Per-run flags: 19 c030
ambiguity flags across 13 sentences (S01098×4, S15072×2, S21236×2,
S46493×2, +9 singles — flag-only, no rewrite; S00963 not among them: the
review used the old union dictionary, production uses the edge-filtered
Amis dictionary) and 69 c002 single-quote-variant warnings in Chinese
TRANSLs (warn-only by design, POL-018).

## Dedup (POL-022) — zero removals

`remove_duplicate_sentences --apply`: **0 duplicates found, 0 S removed, 0
`ver="alt"` TRANSL merges** — the published corpus was already deduplicated
at build time (255 sentences, old drop-only tool; their TRANSLs are
recoverable only from a from-source rebuild, noted for the maintainer).
Dedup is now declared in CodeAndDocs → duplicates HARD for this corpus
(verified live: within-file=0, cross-file=0 under the HARD banner).

## Token delta

**0** (count_tokens corpus rules, Amis/Coastal: 243,710 → 243,710; the two
JSON outputs are byte-identical). Dedup removed nothing; FORM-token content
is unchanged (hyphenated chunks still contain letters); PHON is not counted,
so the added original tier cannot move it.

## Validators before → after

(Re-run against the fixup output; `before` = the file on `main`.)

- `validate_xml`: clean → clean (0 findings both) — original PHON is
  schema-valid where it sits. (Run in the published layout: running the same
  check on a scratch copy raises a spurious V081 duplicate-`text_id`, since
  the real corpus is still in the tree.)
- `validate_text`: SOFT 48,066 → **625**. Unchanged by the added tier: the
  post-fixup finding set is identical to the first turn's. V147 phon_legacy_tilde_variant
  **47,477 → 0** (the issue-#104 target). V137 footnote-like **12 → 0** —
  resolved with source backing: all 12 (`t19`/`T19`/`D19`) were artifacts
  of the old hyphen stripping (`Kofit-19`→`Kofit19`); the restored source
  hyphen dissolves them (all 12 ids ⊆ the 48 hyphen-restored set). V116
  non-ascii 3 → 3 (OCR-era chars faithful to source, README-documented).
  V122 parens/slashes 574 → 574, **identical finding set** (212 FORM /
  362 TRANSL; POL-026/027 review worklist — inspected, not bulk-deleted,
  disposition documented in README). V116/V122 rows compare equal on every
  column except `line`, which shifts because the added PHON elements move
  the file's line numbering. V133 dash_in_S_standard_FORM 0 → 48 —
  the restored hyphens, source-faithful compounds (README-documented).
- `validate_duplicate_sentences`: 0 groups, now HARD-scoped (see above).

## Sidecars (POL-033)

`cleaner_warnings.csv` (88 rows: 69 c002 + 19 c030 — byte-identical across
both fixup runs) reviewed above and deleted; no `standardize_warnings.csv`;
no `quote_corrections.csv` produced. Nothing committed.

## Issue #104 disposition

Verified: V147 47,477 (exact), V137 12, V122 574, no HARD findings,
Coastal profile — all confirmed against reality. Wrong in the issue: the
file is `XML/Amis/Safolu/amis_safolu_examples.xml`, not `XML/Amis/Amis.xml`.
Done-criteria: V147 = 0 ✓ (via the reproducible pipeline, not by editing
published PHON ✓); V137 12 → 0 with source-backed explanation ✓; V122 574
inspected, unchanged, dispositioned as the POL-026/027 review worklist
(alternative/variant annotations, e.g. `nanom (nanum)`) — not bulk-deleted ✓.
Issue can be closed on merge.

## README

Rewritten to pipeline + data-user content: data shape with real counts
(49,181 S / 48,912 zho TRANSL / 269 FORM-only — the old 49,145/272 figures
were stale), canonical `make_xml.sh` reproduction + snapshot note,
from-source path marked network-dependent with its dev-repo layout caveat,
notes on the automatic apostrophe/quotation disambiguation (possible false
positives, certain misses, logged in `CodeAndDocs/quote_corrections.csv`),
OCR-character V116 rows, V122 worklist, V133 hyphens. Dropped: the old
double-`clean_xml` pipeline, the stale "dialect unknown" note, stale
build-result numbers (moved to SOURCE_AUDIT.md pointer).

Fixup pass: the data-shape section now documents **both** PHON tiers (and
why they are currently identical); step 3 documents `--orthography Ortho113`
and why `--preserve-existing-original` is not used; the reproduction table
row and the from-source section now name **one** command
(`make_xml.sh` / `make_xml.sh --from-source`) with the `Makefile` gone.

## Verdict

100% of changes classified (0 unexplained); quote-correction volume zero;
dedup delta zero; token delta zero; V147 cleared; original PHON present and
independently reproduced on all 49,181 S; one entry point. Ready for
maintainer review/merge (no push/merge this turn). Post-merge: GitBook
corpus page check (sweep ruling 4); close #104.
