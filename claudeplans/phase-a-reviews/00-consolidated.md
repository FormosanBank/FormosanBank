# Phase A consolidated — REV 2 (2026-08-11)

Rerun of the five Group 1 attestation-dictionary reviews under the
maintainer's corrections and rulings. Supersedes the round-1 consolidated
report entirely (round 1's per-language framing, "Truku Wikipedia" mislabel,
and "Paiwan glottal = q" premise were all errors — see the per-language
reports' REV 2 headers for what was retracted). Per-language reports sit
alongside this file. Every volume below is a read-only replay of the exact
production `apply_quote_corrections` entry point.

## Governing rulings (maintainer, 2026-08-11)

1. Assessments are **per corpus**, against the orthography each corpus's
   README declares for its original tier — never per language, never from
   any single table.
2. **Seediq Wikipedia**: deterministic normalization instead of the
   classifier — `''`→`"`, then remaining `'`→`"` at word edges and in
   isolation only. Kept as `'`: **word-internal apostrophes** (letter on
   both sides — `b'anux`, `hla'alua`, `mu'izzaddin`; ruled 2026-08-11) and
   the `knita'`/`brbiru'` whitelist (Atayal-vocabulary boilerplate).
   Implemented as `Corpora/Wikipedias/CodeAndDocs/normalize_seediq_quotes.py`
   on branch `feature/wikipedias-seediq-quote-normalization` (9a8690d77 +
   0318c11f0); dry run: 143 original FORMs. XML applies at the sweep turn.
3. **All other Wikipedias languages**: `'` assumed glottal by fiat, until a
   better LM can correct automatically. Straight-vs-curly codepoints in
   wiki sources are NOT trustworthy signal.

## REV 2 verdicts

| Language | Dictionary | Verdict | Live Group 1 corpora → measured volume |
|---|---|---|---|
| Amis | 7,167 | (pre-approved — hand-validated) | Glosbe / Virginia_Fey / (Wikipedia excluded); quote-review worklist rows apply at those turns |
| Atayal | 7,985 | **APPROVE WITH FIXES** | Glosbe (Church orthography, `'`=ʔ) → 0; WilangYutas (Ortho94 Sekolik) → 0. Robust to empty-dictionary counterfactual |
| Saisiyat | 1,773 | **APPROVE WITH FIXES — Group 1 only**; **DO NOT ENABLE for ePark/NTU/ILRDF turns** pending classifier fixes | Glosbe (Ortho94) → 0/0; SEALS33 (Ortho94) → 0 rewrites, 3 c030 flags. Zeros are structural, not lucky |
| Truku | 1,544 | **APPROVE WITH FIXES** | Glosbe (dialect="Truku"; 0 apostrophes) → vacuous 0 |
| Seediq | 3,759 | **APPROVE WITH FIXES** | SEALS33 (dialect="unknown" → Seediq dict; both apostrophes = loan autonym `'Tayal`, structurally unreachable by every rule, stress-tested) → 0 |
| Paiwan | 5,234 | **APPROVE WITH FIXES** | FormosanBankGitBook (Ortho113, `'`=ʔ) → 0; its single apostrophe is the internal glottal in `pu'ui` "wish" |
| Sakizaya | 1,969 | **APPROVE — moot for Group 1** | No szy text in any Group 1 corpus (verified). Gates recorded for later szy turns (ePark 435 quote-bearing-TRANSL sentences, NTU 51, Presidential_Apologies 11, ILRDF 2) |

**Total expected Group 1 classifier corrections: 0.** The only Group 1
apostrophe changes come from the deterministic Seediq Wikipedia step
(ruling 2; 264 FORMs, applied and diff-audited at the Wikipedias sweep
turn).

## Dictionary cleanup — RESOLVED by the edge-filter ruling (2026-08-11)

The maintainer superseded the reviewers' piecemeal fix lists with a single
principle: **only entries that are potentially Formosan words with a
word-initial or word-final `'` matter** — verified against the code (every
classifier lookup tests a `'word` or `word'` shape; nothing else can ever
match). Branch `feature/attestation-edge-filter` (b80bef60c, 950 tests
green) filters all 17 dictionaries accordingly (e.g. Amis 7,167→505,
Atayal 7,985→1,053, Saisiyat 1,773→584). Five came out empty and are
**deleted, disarming those languages** (Seediq, Truku, Thao, Yami, Siraya
— `clean_xml` arms on file *existence*, so empty-but-present would mean
armed-with-no-guard). Group 1 outcomes unchanged. Known caveat:
`build_attestation_dict.py` still generates unfiltered lists, so a future
regeneration (e.g. via `port-corpus-in`) would undo the filter unless the
builder gains the same rule — flagged, not acted on.

The original per-language fix lists below are retained as reference
observations only:

- **Atayal**: delete 38 (28 CJK/Japanese debris, `s%27inu`/`ttu%27`
  URL-encoded, 3 digit-tailed, 5 fillers); optional adds `s'inu`, `ttu'`.
- **Seediq**: delete `b`, `n`, `o`, `-un`, `na;n-`, 3 fullwidth-punct
  compounds, **52** slash-compounds (round 1 said 57 — recounted);
  `'tayal` addition downgraded to optional (geometry alone protects
  SEALS33; a regeneration would silently drop the manual entry).
- **Truku**: delete `無此字彙`, `無此字彚`, `n`, 3 slash-compounds.
- **Paiwan**: delete 8 (2 CJK sentence entries, 3 digit run-togethers, 3
  punctuation-bearing); 209 slash-compounds inert/optional.
- **Sakizaya**: optional cosmetic only (56 inert non-token entries).
  Round-1 partition corrected: 115 final / 55 interior-only / 0 initial
  (`mikisa'pi'` was double-counted).
- **Saisiyat** (with the Group 1-only approval): delete 15 junk entries;
  add the 7 missing high-frequency words (`'izo'`, `hiza'`, `sa'`, … —
  list in report §2).

## Classifier fix worklist (prerequisites before wider arming)

Consolidated from both rounds; none affects Group 1's measured zeros:

1. `attested()` truncates the letter-run at apostrophes → both-edge-glottal
   words (`'oka'`) can never be vetoed (Saisiyat round 1; ~50 wrong
   rewrites in NTU/ILRDF/ePark if armed there).
2. **NEW (REV 2)**: the truncation also stops at `:` — Saisiyat vowel-length
   colon makes attested `kapayaka:i'` look up as `i'`; SEALS33 S27 was a
   one-guard-deep near-miss (only the initial/final balance guard blocked
   a wrong rewrite).
3. Rules 2/3 skip opener attestation.
4. `TRANSL_QUOTES` lacks `《》`/`〈〉` (Chinese title marks) and curly
   singles `‘’`; with `tq == 0` suppressing all conversion, a `《…》`-quoting
   TRANSL falsely "confirms no quotation" (missed corrections only).
5. NTU Saisiyat English TRANSLs carry systematic stray-`"` debris
   (notes-derived, orphaned quotes + truncated subjects) — clean or
   discount before those corpora arm; also an NTU data defect in its own
   right (sweep-turn worklist).

## Process guards

- **Saisiyat**: no `clean_xml` run over NTU/ILRDF/ePark while the Saisiyat
  dictionary is armed, until classifier fixes 1–3 land. Group 1 cleaning is
  safe.
- **Sakizaya and later-group turns generally**: per-corpus README
  orthography call + read-only dry run + dictionary enrichment
  (`--include-interior --min-freq 3` after a pollution check) before any
  TRANSL-bearing corpus arms.

## Decisions

1. ~~Dictionary fix lists~~ — DECLINED 2026-08-11: out of Phase A scope;
   no attestation.txt edits. Recorded above for reference only.
2. ~~Seediq-Wikipedia internal-apostrophe flag~~ — RESOLVED 2026-08-11:
   word-internal apostrophes are kept (implemented, 0318c11f0).
3. Classifier fix worklist — no action now; recorded as the prerequisite
   gate before Saisiyat-armed cleaning reaches ePark/NTU/ILRDF (later
   groups).
4. **Live decision: Phase B go for Group 1.** Quote-correction standpoint:
   measured-zero classifier corrections everywhere; the only apostrophe
   diffs will be the deterministic Seediq Wikipedia step (143 FORMs).
