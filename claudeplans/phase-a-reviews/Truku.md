# Attestation-dictionary review: trv (Truku + Seediq dictionaries) — REV 2

Reviewer: read-only rerun, 2026-08-11. Round 1: `claudeplans/phase-a-reviews/Truku.md`;
rulings applied: `claudeplans/phase-a-reviews/00-consolidated.md` (per-corpus assessment,
Seediq-Wikipedia deterministic normalization, classifier fix worklist). Policies:
POL-010, POL-018; design spec `docs/superpowers/specs/2026-08-10-quote-glottal-correction-design.md`.

## Scope changes vs round 1

Per maintainer rulings, assessment is **per corpus** against each corpus README's declared
original-tier orthography, and `Corpora/Wikipedias/XML/Seediq/` (the SEEDIQ Wikipedia;
xml:lang=trv, no dialect) is **out of classifier scope** — it gets the ruled deterministic
normalization (`''`→`"`, then remaining `'`→`"` except `knita'`/`brbiru'`; branch
`feature/wikipedias-seediq-quote-normalization`). Round 1's 6 Wikipedia corrections are
subsumed by that step and excluded from all volume figures below. The correction-live
Group 1 target corpora for trv are exactly two: **SEALS33** and **Glosbe**.

Both dictionaries are unchanged since round 1 (last commit touching them: `00cfa9abd`).

## Corpus: Corpora/SEALS33 (trv)

- **File:** `Corpora/SEALS33/XML/Seediq/seediq_SEALS.xml` — 1 file, 29 S, 29 original
  S-FORMs, `xml:lang="trv"`, `dialect="unknown"`.
- **Gating dictionary:** `resolve_language("trv", "unknown")` → **Seediq**
  (`QC/corpus_counts.py` line 79: only dialect `truku` casefolded gives Truku), so
  `QC/validation/reference/Seediq/attestation.txt` (3,759 entries) is loaded at
  `QC/cleaning/clean_xml.py` lines 670–671. Confirmed by replay.
- **Declared orthography:** README ("transcription is already the 94 Orthography …
  Ortho94 is used here for the original tier"). `Orthographies/Ortho94/Seediq.tsv`
  (24 letters, Truku/Tegudaya/Duda/DeluValley columns) has **no `'` row** — the
  apostrophe is not a letter of this corpus's declared orthography.
- **The 2 apostrophes** (all of them), re-verified in context: both are the loan
  autonym **`'Tayal`** "Atayal" with a genuine initial glottal, in S16
  (`… kari 'Tayal ma kari Seediq`, TRANSL "The mystery of Atayalic /x/…") and S26
  (`… quri kari 'Tayal ma kari Seediq ga …`, TRANSL "Standardization … among Atayalic
  communities"). This is exactly the POL-018 rationale case: a language whose declared
  orthography lacks the glottal letter still carries it in rampant loanwords — so
  `'` must be treated as a letter here, not paired punctuation. Round 1's
  characterization stands.
- **Replay** (`apply_quote_corrections`, exact clean_xml TRANSL gathering, in-memory):
  **corrected 0, stranded 0, ambiguous 0** over all 29 FORMs.
- **Protection is structural, not dictionary-dependent.** Each sentence has exactly one
  apostrophe, word-initial: Rule 1 requires openers == closers (word_initial=1,
  word_final=0 → blocked); Rule 2 needs an after-punct `'` (none); Rules 3–4 need a
  word-final `'` (none). Stress-tested: with no TRANSL, with quote-bearing TRANSLs, and
  with NTU-style orphaned-`"` TRANSL debris, the result is still 0 rewrites (worst case
  one c030 ambiguous flag, which is leave+warn). The known `tq == 0` suppression and the
  `TRANSL_QUOTES` charset gap (fix-worklist items — cited, not re-derived) are therefore
  irrelevant to this corpus's safety: fixing either cannot make a rule fire on this
  geometry.
- **Volume: 0 corrections.** Safe.

## Corpus: Corpora/Glosbe (trv)

- **File:** `Corpora/Glosbe/XML/trv/Glosbe_trv_eng_lexical.xml` — 1 file, 112 S,
  112 original S-FORMs, `xml:lang="trv"`, `dialect="Truku"`.
- **Gating dictionary:** dialect `Truku` → **Truku**,
  `QC/validation/reference/Truku/attestation.txt` (1,544 entries). Confirmed by replay.
- **Declared orthography:** README table — source orthography Ortho94, conversion
  `Seediq_94_113.tsv` Truku column, `dialect="Truku"` asserted. Same Ortho94 Seediq
  table: **no `'` row**.
- **Apostrophes: 0** across all 112 original FORMs (re-counted). Replay: corrected 0,
  stranded 0, ambiguous 0.
- **Volume: 0 corrections.** Vacuously safe — the correction machinery has literally
  nothing to inspect.

## Dictionary quality: Seediq attestation.txt (3,759 entries)

Re-verified: 0 duplicates, fully casefolded, 1 apostrophe-bearing entry (`hla'alua`,
line 701 — Saaroa ethnonym, keep). Round 1's structural point stands: with one
`'`-bearing entry the dictionary is nearly guard-inert (only `'`-shaped lookups can
veto), so junk is harmless and the file functions mostly as the existence-gate.

**Fix list re-verified, one amendment.** All round-1 deletions confirmed present:
`-un` (line 1), `b` (43), `n` (1898), `o` (2001), `na;n-` (1901), and the 3
fullwidth-punct/ellipsis compounds `kla；tduwa` (965), `kndalax…betaq` (1041),
`ubung；trasi` (3646). Slash-compounds: **52 entries, not 57** as round 1 stated
(recount: 52 lines contain `/`; `empeungac/t/empkngatun` and `phing/ungac/t` carry two
slashes each, which may explain the miscount). The list itself is unchanged in
substance — delete every entry containing `/` (`bindo/sbiki` … `ungac/t`). Keep
`covid-19` (line 330), `hla'alua`, and the Japanese-loan hyphen entries.

**`'tayal` addition — re-examined, downgraded to optional.** With the Seediq Wikipedia
out of classifier scope, SEALS33 is the Seediq dictionary's only correction-live
consumer, and its two `'Tayal` tokens are protected by rule geometry alone (shown
above): adding `'tayal` changes **no outcome in any tested scenario**, including
hostile-TRANSL stress tests. The entry remains *correct* (genuinely attested, twice,
in published trv text; `attested()` for a word-initial `'` looks up `'`+letters, so
this is the right shape) and remains *safe* (a veto can only produce false negatives,
acceptable by design). Recommendation: still add it, but as forward-looking hygiene
for later TRANSL-bearing Seediq corpora (ePark Seediq etc.) — it protects the
Rule-1 balanced-pair path when a future sentence pairs `'Tayal` with a second edge
apostrophe — not as a Group 1 safety requirement. Note it cannot be harvested
automatically: `'Tayal` never occurs as a single-word S-FORM, so
`build_attestation_dict.py` will silently drop it on regeneration; it needs a
manual-additions mechanism or re-adding after each regen.

## Dictionary quality: Truku attestation.txt (1,544 entries)

Re-verified: 0 duplicates, fully casefolded, **0** apostrophe-bearing entries — fully
guard-inert; pure existence-gate for the Truku-resolving corpora (Glosbe trv is the
only Group 1 target; TangRecordingsOfTaroko, Presidential_Apologies/Truku, ePark
Truku, Nowbucyang, ILRDF_Dicts sit behind the same gate at their own sweep turns).

**Fix list re-verified, stands exactly.** Delete: `無此字彙` (line 1543), `無此字彚`
(1544) — ILRDF "no such word" placeholders; `n` (775); slash-compounds `kuyuh/kuyuh`
(463), `paru/takar` (836), `smuk/teeci` (1291). Keep `n-naku` (776) and everything
else. No new junk found.

## Recommendations

- **Seediq attestation.txt: APPROVE WITH FIXES** — delete `b`, `n`, `o`, `-un`,
  `na;n-`, 3 fullwidth-punct compounds, **52** slash-compounds (amended from 57);
  optionally add `'tayal` (hygiene for future TRANSL-bearing corpora; no Group 1
  behavioral effect, and regeneration will drop it unless preserved manually).
- **Truku attestation.txt: APPROVE WITH FIXES** — delete `無此字彙`, `無此字彚`, `n`,
  3 slash-compounds.

**Per-corpus correction volumes (Group 1, Wikipedias excluded per ruling):**
SEALS33 trv **0** (2 apostrophes, both `'Tayal`, structurally unreachable by every
rule); Glosbe trv **0** (0 apostrophes, vacuous). Total expected trv Group 1
corrections: **0**. No REGENERATE needed; `--include-interior` remains contraindicated
for these languages.
