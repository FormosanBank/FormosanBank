# Attestation-dictionary review — Sakizaya (szy) — REV 2

**Dictionary:** `QC/validation/reference/Sakizaya/attestation.txt` (1,969 entries)
**Reviewed:** 2026-08-11, rerun under the maintainer's post-round-1 rulings (read-only; no XML touched)
**Round 1:** `claudeplans/phase-a-reviews/Sakizaya.md`; rulings in `claudeplans/phase-a-reviews/00-consolidated.md`

Governing corrections applied in this rerun:
1. Assessment is **per corpus** (each corpus's README-declared original-tier orthography), never per language.
2. **Wikipedias are out of scope for correction** by maintainer fiat: non-Seediq Wikipedias keep `'`
   as assumed-glottal until a better LM exists. The Sakizaya Wikipedia — round 1's only target —
   is therefore excluded from correction-volume and risk assessment here.
3. The Sakizaya Wikipedia's `''` sequences are verified (live wikitext `balucu'’”.`) to be word-final
   glottal `'` + a curly `’` closing quote that **our own cleaner** canonicalized onto it; wiki
   authors mix straight/curly punctuation inconsistently, so codepoints are not trustworthy signal.
4. Known classifier issues are cited from the fix worklist, not re-derived: `TRANSL_QUOTES` lacks
   `《》〈〉`/`‘’`; `tq == 0` suppresses conversion; Saisiyat `attested()` apostrophe truncation.

---

## 1. Scope confirmation: no correction-live Group 1 corpus for Sakizaya

With the Sakizaya Wikipedia excluded by ruling 2, the question is whether any *other* Group 1
corpus carries Sakizaya text. Checked all six (re-verified 2026-08-11):

| Group 1 corpus | szy content? | Evidence |
|---|---|---|
| FormosanBankGitBook | none | `XML/` contains only `Paiwan/`; zero `xml:lang="szy"`; "Sakizaya" appears only in the lang-code map of `CodeAndDocs/process_raw.py` |
| Glosbe | none | `XML/` contains only `ami tay trv xsy`; the `szy` rows in `CodeAndDocs/scripts/config.yaml` are scrape *targets* that produced no published XML |
| SEALS33 | none | only Seediq + Saisiyat XML; "Sakizaya"/"Sakiraya" hits are a conference-talk title *about* Sakizaya ("Cliticization of oblique case marker in Sakizaya") translated into Seediq/Saisiyat (S id="28" in both files) — a proper noun, not szy text |
| Virginia_Fey_Dictionary | none | `XML/Amis/` only |
| WilangYutasVideos | none | `XML/Atayal/` only; the grep hits for the substring `szy` are Atayal words `szyon`/`szyun` |
| Latham-1862 | none | `XML/{Babuza-Favorlang, Siraya}` only |

TEXT-level `xml:lang` across all six corpora: `tay ×84, pwn ×6, ami ×6, xsy ×3, trv ×2, fos ×1,
bzg ×1` — **no `szy` anywhere**. Repo-wide, `xml:lang="szy"` occurs only in Wikipedias (5,715
files), ePark (11), NTUFormosanCorpus (16), ILRDF_Dicts (1), Presidential_Apologies (1) — none of
which is a Group 1 correction target for szy.

**Confirmed: Sakizaya has zero correction-live Group 1 corpora.** Correction volume for Group 1
is not merely 0 — it is undefined/moot, and no risk assessment attaches to this dictionary at
Group 1. Round 1's §1 orthography argument and §3 dry-run (0 rewrites on the Wikipedia) remain
factually correct but are now background, not the operative decision: per rulings 1–2 the
Wikipedia keeps its `'` by fiat regardless, and its `''` cases (584 raw hits) belong to the
quote-correction machinery at the Wikipedias sweep turn, ideally consulting pre-canonicalization
dev-repo source text (per ruling 3 and consolidated §"Seediq Wikipedia follow-ups" item 1).

## 2. Dictionary quality — round 1 re-verified, held with one arithmetic amendment

Everything recomputed from scratch this session (venv Python, in-memory only):

- **Provenance: exact.** Rebuilding with `build_attestation_dict.py`'s logic (single-word S-FORM
  types, original+standard tiers, `_strip_flanking_punct` + casefold) per corpus gives
  ePark 1,719 / NTUFormosanCorpus 467 / Wikipedias 132 / ILRDF_Dicts 1 / Presidential_Apologies 0;
  the union is **1,969 and is set-identical to the committed file**, which is also sorted-on-disk
  and casefold-unique. Round 1's table confirmed verbatim.
- **Hygiene: clean, as reported.** 0 digit-bearing, 0 non-ASCII, 0 single-letter entries.
  The **56 out-of-alphabet entries** reproduce exactly: 51 slash-joined variant listings
  (`ala/dikec`, …), 4 vowel-length-colon forms (`amahi:ca`, `kaisa:sa`, `sitangata:ngah`,
  `tatu:sa`), 1 stray `tipus.suaya`. These remain inert: `attested()` extracts pure letter-runs,
  which `/` `:` `.` break, so they can never match — dead weight, optional cosmetic cleanup only
  (consolidated fix list already records this as "optional cosmetic only").
- **Apostrophe entries: 170 total, 0 initial — one count amended.** Round 1 said "115 final, 56
  interior"; those overlap by one entry, `mikisa'pi'`, which has both an interior and a final
  apostrophe. Correct partition: **115 apostrophe-final (incl. `mikisa'pi'`), 55 interior-only,
  0 initial; total 170** (round 1's 170 total was right; 115+56 double-counted one entry).
  Two-letter entries `co ku na nu tu wa zo` confirmed present and harmless.
- **Coverage: confirmed thin.** Against the Sakizaya Wikipedia original tier: attested
  apostrophe-bearing types **132** covering **23,852 tokens** — identical to round 1. My totals
  are 7,704 apo types / 52,349 apo tokens (round 1: 7,701 / 52,179; <0.4% tokenization-detail
  drift), giving **1.7% type / 45.6% token coverage** (round 1 reported 45.7% — same figure
  within rounding). Overall type coverage 1,694/143,564 = 1.2%. Top unattested words are common
  real lexemes (`kabana'` 1,021, `niyadu'` 857, `kasalumaluma'` 810, `inayi'` 754,
  `saadidi'ay` 721) — the coverage gap is real, but with the Wikipedia out of correction scope it
  has **no Group 1 consumer**; it becomes load-bearing only at the later-group turns below.

Verdict on content: the dictionary is exactly what its generator specifies, hygienically clean,
with genuine Sakizaya apostrophe vocabulary and no quote-polluted debris. No pre-enable edits
required; the 56-entry cleanup stays optional.

## 3. What remains for later groups (the operative exposure)

The published szy corpora, none in Group 1, all TRANSL-bearing except Wikipedias
(profiled this session, original tier):

| Corpus | szy files | S | TRANSLs | S with quote-bearing TRANSL | orig-tier `'` |
|---|---|---|---|---|---|
| ePark | 11 | 7,391 | 9,532 | **435** | 2,285 |
| NTUFormosanCorpus | 16 | 2,077 | 2,999 | **51** | 480 |
| ILRDF_Dicts | 1 | 5,360 | 5,360 | 2 | 1,920 |
| Presidential_Apologies | 1 | 33 | 66 | 11 | 53 |
| Wikipedias | 5,715 | 5,715 | 0 | 0 | 53,287 (out of scope by ruling) |

With this `attestation.txt` committed, the correction is **armed for all of these** at their next
`clean_xml` run. On the TRANSL-bearing corpora the quote-count rules (1/3/4) *can* fire, and
there the 45.6%-token / 1.7%-type coverage gap becomes load-bearing: an unattested glottal-final
word at a quoted span's edge (`kabana'`, `inayi'`, …) is exactly what the attestation guard is
supposed to protect and currently cannot. ePark szy is the largest exposure (435 quote-bearing
TRANSL sentences). Known classifier issues also apply at those turns (cited from the fix
worklist, not re-derived): `TRANSL_QUOTES` missing `《》〈〉`/`‘’` (Chinese TRANSLs falsely read as
quote-free; `tq == 0` then suppresses conversion — missed corrections, not wrong rewrites) and
the Saisiyat-discovered `attested()` truncation at apostrophes (matters for glottal-edge words —
Sakizaya has 115 final-apostrophe entries, so partially degraded veto power until fixed).

**Gate before the ePark / NTU / ILRDF (and Presidential_Apologies) szy turns:**
1. per-corpus orthography call from each corpus's README (ruling 1);
2. read-only dry run of `apply_quote_corrections` on that corpus's szy XML;
3. dictionary enrichment first if the dry run shows edge-word rewrites — consolidated
   recommendation: regenerate with `--include-interior --min-freq 3` after checking szy interior
   tokens for quote pollution;
4. classifier fix worklist (charset gap, `attested()` truncation) landed or consciously waived.

The Wikipedias sweep turn separately owns the 584 `''` glottal+curly-quote collapses (ruling 3) —
a cleaner/source-text problem, not an attestation-dictionary problem.

## 4. Recommendation

Dictionary content: clean, provenance-exact, nothing to fix before it sits in the tree. Group 1:
no szy corpus exists, so enabling is a no-op there. Later groups: do not treat this approval as
covering the TRANSL-bearing szy corpora — each gets the per-corpus gate above.

**APPROVE** (moot for Group 1 — no correction-live szy corpus; per-corpus dry-run + dictionary
enrichment is the gate before the ePark/NTU/ILRDF/Presidential_Apologies szy turns)
