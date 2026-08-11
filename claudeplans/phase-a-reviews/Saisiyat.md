# Saisiyat (xsy) attestation-dictionary review — Phase A — REV 2

Rerun of `claudeplans/phase-a-reviews/Saisiyat.md` under the maintainer corrections in
`00-consolidated.md`: assessment is **per corpus** against each README's declared
original-tier orthography; Wikipedias out of scope (no xsy Wikipedia exists anyway);
known classifier issues are cited, not re-derived. Read-only: replay imported
`apply_quote_corrections` in memory over the published XML, replicating the
`clean_xml.py` call pattern exactly (sentence-level `kindOf="original"` FORM only;
TRANSLs via `itertext()`; dictionary via `_load_attestation("Saisiyat", …)`, 1,773
entries; replayed with both raw and `clean_trans`-processed TRANSLs — identical
results). No XML touched.

Central question: round 1's DO NOT ENABLE was driven by ~50 wrong rewrites in
NTU/ILRDF/ePark — corpora that are **not** in Group 1. Is arming safe for Group 1
(Glosbe + SEALS33) specifically? Answer below: **yes, with grounded caveats.**

## 1. Corpus: Glosbe (`Corpora/Glosbe/XML/xsy/`)

**Declared orthography.** `Corpora/Glosbe/readme.md` (table at lines 52–57): Saisiyat
source orthography **Ortho94**, standardized via `Saisiyat_94_113.tsv` (single
`standard` column), single-dialect assumption; original tier "the source spelling,
preserved exactly". `Orthographies/Ortho94/Saisiyat.tsv` line 9: **`'` → ʔ**. So `'`
IS a letter in this corpus's original-tier orthography; the correction machinery
applies in principle. (`:` → length is also a letter — see §2's S27 finding.)

**Replay (production path).** 490 sentences with original FORM; 225
apostrophe-bearing; 281 apostrophes (matches briefing). Result: **0 rewrites, 0
stranded repairs, 0 ambiguous (c030) flags.**

**Why it is structurally zero, not accidentally zero.**
- Every one of the 225 apostrophe-bearing sentences has at least one TRANSL, and
  **zero TRANSL quote marks exist anywhere in the corpus** (0 sentences with any
  `TRANSL_QUOTES` character). `apply_quote_corrections` line 486 therefore sets
  `quotation_allowed = False` for every sentence individually — all four rules and
  destranding are suppressed sentence-by-sentence.
- Independently, **zero sentences have the Rule 2 shape** (exactly one word-initial
  `'` + exactly one post-punctuation `'`), the only rule that can fire without TRANSL
  corroboration.
- Both-edge-glottal exposure (the class round 1 showed `attested()` cannot veto):
  exactly **1** token — `'inalingo'` "film" (`S GLOSBE_xsy_eng_LEXICAL_U000036`). It
  IS in the dictionary but unvetoable under the letter-run truncation (lookups
  `inalingo'`/`'inalingo`, both absent); it is protected here solely by its quote-free
  TRANSL. Latent, not live.
- **TRANSL quote debris (the NTU failure mode): none.** 0 TRANSLs with odd `"` counts
  or orphan leading-quote patterns. The single quote-adjacent character in any Glosbe
  xsy TRANSL is a curly `’` in English possessive `’s` (S …U000058) — and that
  sentence's FORM is the bare word `a`, no apostrophe; even the proposed
  `TRANSL_QUOTES` `‘’` charset fix cannot make anything fire there (simulated: 0).

**Caution for future refreshes:** Glosbe's safety rests on the `tq == 0` suppression
— the very behavior on the classifier worklist as "suppresses conversion." If that
gate is ever weakened, or a Glosbe re-scrape imports quote-bearing TRANSLs, this
corpus must be re-replayed before cleaning; with `'izo'`-class words unattested and
the truncation bug unfixed, NTU-style false positives would become possible.

**Assessment: safe to arm. Expected volume: 0 rewrites, 0 flags.**

## 2. Corpus: SEALS33 (`Corpora/SEALS33/XML/Saisiyat/`)

**Declared orthography.** `Corpora/SEALS33/README.md` lines 66/74: the transcription
"is already the 94 Orthography" (standardize made no changes); Ortho94 used for the
original tier's phonology. Same `Orthographies/Ortho94/Saisiyat.tsv`: **`'` → ʔ** —
a letter here too.

**Replay (production path).** 29 sentences (long conference abstracts); 28
apostrophe-bearing; 225 apostrophes (matches briefing). Result: **0 rewrites, 0
stranded; 3 c030 audit-flag sentences (S7, S9, S27; 91 flagged apostrophes)** —
flags only, no edits, matching round 1.

**Why the bugs cannot bite on these sentences (grounded per sentence):**
- Both-edge-glottal tokens: 11; they co-occur with quote-bearing TRANSLs in S7 and
  S9 (e.g. `'aylike'` "Eric" in S7). But S7 has 35 apostrophes (6 word-initial, 21
  word-final; tq−fq = 2 vs |se| = 27) and S9 has 52 (11 word-initial; tq−fq = 2 vs
  |se| = 43): Rule 1's count-match fails by an order of magnitude, and Rules 2–4
  require *exactly one* word-initial `'` — unsatisfiable in glottal-dense abstract
  prose. The known opener/truncation gaps are unreachable behind these failed
  preconditions.
- **S27 near-miss — new in REV 2, one guard deep.** FORM: `"zoke'" noka paywan ka
  kapayaka:i' ki kin'al'alihan ka kaspengan`; TRANSLs `排灣語的＂主格＂…` /
  `Paiwan "Nominative" …`. Here tq−fq = 4−2 = 2 **equals** |se| = 2 (`zoke'`,
  `kapayaka:i'`), and the attestation veto is void: `zoke'` is unattested, and
  `kapayaka:i'` IS in the dictionary but `attested()`'s letter-run walk stops at
  `:` (`str.isalpha()` is false for the Ortho94 length letter), looking up `i'`
  (absent). The **only** condition that blocked Rule 1 was its balance guard
  (`len(word_initial) == len(word_final)`: 0 ≠ 2). Two consequences: (a) a new,
  Saisiyat-specific manifestation of the round-1 truncation bug — **`:` inside a
  word defeats the veto for any attested word in `…V:C'` shape** (add to the
  classifier worklist: the letter-run should use the orthography's letter set, not
  `isalpha()`); (b) SEALS33's zero is real but rests on a single precondition, not
  defense-in-depth. On this static, published corpus that is stable — the text
  cannot change under `clean_xml` reruns — so it does not block Group 1 arming.
- **TRANSL debris: none.** 0 odd-count/orphan-quote TRANSLs; the quote marks in
  S7/S9/S27 are legitimate `＂…＂`/`"…"` pairs (titles, scare quotes), correctly left
  as c030 audit flags. (S27's `＂主格＂` pairs with FORM's existing real `"zoke'"`
  quotes — already double quotes per POL-018; nothing to convert.)

**Assessment: safe to arm. Expected volume: 0 rewrites; 3 c030 flag sentences.**

## 3. Dictionary quality (spot re-verification)

The file is byte-unchanged in effect since round 1 (still 1,773 entries):
- **All 15 junk entries still present** (2 CJK `無此詞`/`無此詞彙`, 6 slash-joined
  alternates, 5 affix/citation notations `i~`/`ka-`/`ka-hia`/`kama-`/`tasa-`, single
  letter `a`, ligature `'ælaw`). Round 1's deletion list stands verbatim. All are
  conservative (attestation only blocks rewrites), so deleting them is safe and does
  not change Group 1's zeros.
- **All 7 named high-frequency words still missing** (`'izo'`, `hiza'`, `sa'`,
  `'oe'oe`, `bala'`, `hinola'`, `o'aehae'`). Round 1's coverage figures stand
  (Glosbe 86.7%, SEALS33 69.8% of apostrophe tokens attested).
- Known-good entries spot-checked present (`'oka'`, `'aehae'`, `'okik`, `'oya'`,
  `kita'en`). Round 1 §2 findings are kept unamended, with one addition: coverage
  additions help less than round 1 implied wherever a word contains `:` or has
  glottals at both edges — the truncation bug voids the veto for those shapes until
  the classifier fix lands (e.g. `kapayaka:i'` is attested yet unvetoable, §2).

## 4. Out-of-Group-1 exposure (cited, not re-derived)

Round 1's replay (kept, per instructions): NTU 42 / ILRDF 6 / ePark 2 ≈ 50 wrong
rewrites, ~100% false-positive, driven by the three worklist classifier gaps
(letter-run truncation defeating both-edge veto; Rules 2/3 skipping opener
attestation; NTU notes-derived English TRANSLs carrying orphaned-`"` debris —
verified in `00-consolidated.md`). Also on the worklist: `TRANSL_QUOTES` lacks
`《》〈〉`/`‘’`, and `tq == 0` suppresses conversion (in Group 1 that suppression is
Glosbe's protection — sequence any change to it behind a Glosbe re-replay). Since
arming is per-language (`QC/validation/reference/Saisiyat/attestation.txt` existing
arms every xsy corpus `clean_xml` visits), the Group 1 verdict must be paired with a
process guard: **no `clean_xml` run over NTUFormosanCorpus, ILRDF_Dicts, or ePark
xsy while armed, until the classifier fixes land** (or disarm-then-rearm around
those turns).

## 5. Recommendation

Round 1's blocker does not live in Group 1: both target corpora measure **zero
rewrites via production replay, for structural reasons** (Glosbe: quote-free TRANSLs
suppress every sentence; SEALS33: rule preconditions unsatisfiable in its
glottal-dense abstracts, with the single S27 near-miss blocked by Rule 1's balance
guard and stable on static data). The dictionary's content is sound apart from the
15 junk entries; the classifier gaps are real but unreachable on these texts.

Fixes attached to approval: (1) delete the 15 junk entries; (2) add the 7 missing
high-frequency words (cheap depth for future-proofing, acknowledging §3's veto
limits); (3) record the process guard of §4 on the sweep schedule; (4) add the `:`
truncation manifestation (S27) to the classifier-fix worklist.

Volumes (Wikipedias excluded per fiat; none exist for xsy): **Glosbe 0 rewrites / 0
flags; SEALS33 0 rewrites / 3 c030 flag sentences.** Repo-wide if cleaned while
armed: ~50 wrong rewrites in NTU/ILRDF/ePark (round 1, cited).

**APPROVE WITH FIXES — for Group 1 only (Glosbe + SEALS33); DO NOT ENABLE for
ePark/NTU/ILRDF turns pending classifier fixes.**
