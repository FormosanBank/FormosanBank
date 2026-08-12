# Wikipedias regeneration (sweep/b2-wikipedias, 2026-08-12)

Phase B batch 2 sweep turn for the five language Wikipedias (Amis, Atayal,
Paiwan, Sakizaya, Seediq; no TRANSLs, no W/M tiers). **No re-scraping** —
the live wikis have moved on, so the published XML is the baseline:
**non-regenerable, POL-035 class**. Collaborator issue
[#78](https://github.com/FormosanBank/FormosanBank/issues/78)
(Codex-generated, treated as non-authoritative) was verified claim by
claim; dispositions at the end.

Revised 2026-08-12 to apply four maintainer rulings: duplicate article
copies are **deleted** (not id-suffixed); articles with no Formosan
content are **deleted**; `dialect="unknown"` stands corpus-wide
(including trv); wiki-markup residue (V129 asterisks, literal `|`) is
**retained as-is**. Plus an orthography-evidence appendix (analysis only).

**13,278 → 13,238 published files** (40 deleted).

## POL-035 snapshot

Pristine pre-correction `XML/` (the five language dirs; the two stray
committed sidecars were excluded — see "Sidecars") copied to
`CodeAndDocs/pre_correction_snapshot/` **before** any script ran;
verified byte-identical to `main`'s `Corpora/Wikipedias/XML/`
(13,278 files, re-verified this turn with a full `git archive` +
`diff -rq`: 0 differences).

## Pipeline (`CodeAndDocs/make_xml.sh`)

Restores `XML/` from the snapshot, then runs (all steps committed,
POL-038; no spurious no-op steps). Step numbering below is the original
sweep's; the 2026-08-12 follow-up turn inserted `apply_manual_edits.py`
ahead of them all (see "Follow-up turn"):

1. `delete_duplicate_articles.py` — **new**; one file per TEXT id (below).
2. `delete_nonlatin_articles.py` — **new**; drops articles with no
   Formosan content (below).
3. `add_dialect_attrs.py` — `dialect="unknown"` on all 13,238 TEXTs.
4. `normalize_seediq_quotes.py` — Seediq-only quote normalization
   (pre-existing script, ruled 2026-08-11; runs before `clean_xml` as
   required): **143 original FORMs in 143 files** — exactly the Phase A
   dry-run count, unchanged by the deletions.
5. `QC/cleaning/clean_xml.py`
6. `QC/utilities/standardize.py --remove_accents`
7. `QC/utilities/add_phonology.py --orthography Ortho113`

Retired this turn: `fix_duplicate_text_ids.py` (superseded by step 1 —
no id collisions survive, so there is nothing to disambiguate) and
`drop_empty_phon.py` (the four punctuation-only articles it patched are
now deleted outright by step 2; **0 empty PHON elements remain**, V073
clean).

**Deterministic and idempotent**: two consecutive full runs produce
byte-identical output (aggregate md5 `1b6b5f1381a772b71bca42218394c9ca`
both times) and identical per-run logs and `cleaner_warnings.csv`.

## Ruling 1 — duplicate article copies deleted (29 files)

29 id groups / 58 files: the scrape saved 29 articles twice (duplicate
downloads written as `<name> (1).xml` / `(2).xml`), and the title-derived
TEXT id came out identical (matches issue #78's 58 V081 findings).

Keep rule (deterministic, from each file's own name): keep the single
counter-less file; where a group has no counter-less file (2 groups),
keep the lowest counter. **Every one of the 29 groups is byte-identical
across its copies** — verified by md5 over the snapshot before deletion
and again by the script at run time (`0 group(s) with differing
content`), so there are **no content differences to report and nothing
was lost**. (The script still diffs FORMs and prints a `CONTENT DIFFERS`
block if that ever stops holding.)

Deleted (all paths under `XML/`):

| # | deleted file | kept |
|---|---|---|
| 1 | `Amis/Haba (1).xml` | `Amis/Haba.xml` |
| 2 | `Amis/Mafana’ay_kiso_tono_mita_o_Pangcah’Amis_to_masamaanay_kopi_saroma’_to_kalo’aol_haw (1).xml` | counter-less twin |
| 3 | `Amis/Oro’raw (1).xml` | `Amis/Oro’raw.xml` |
| 4 | `Amis/Saasik_ni_mamo (1).xml` | counter-less twin |
| 5 | `Amis/Samaanen_milekakawa_“Misatatad_to_Taywan” (1).xml` | counter-less twin |
| 6 | `Atayal/msin (2).xml` | `Atayal/msin (1).xml` (no counter-less file) |
| 7 | `Atayal/ulah_nqu_kay'_mqumah (1).xml` | counter-less twin |
| 8 | `Sakizaya/Oro’raw (2).xml` | `Sakizaya/Oro’raw (1).xml` (no counter-less file) |
| 9 | `Sakizaya/anu_caay_kalacawaw_,_mahica_mala_misitekeday_a_cabay (1).xml` | counter-less twin |
| 10 | `Sakizaya/anu_maydih_kisu_tu_adipapang_kanca_pinanami_a_paluma_tu_balu (1).xml` | counter-less twin |
| 11 | `Sakizaya/anu_sigang_samengmeng_han_henay_saka_tinusa (1).xml` | counter-less twin |
| 12 | `Sakizaya/caay_kaku_kabalaki,_eiyda_sa_balaki_ku_mihca_aku (1).xml` | counter-less twin |
| 13 | `Sakizaya/haba (1).xml` | counter-less twin |
| 14 | `Sakizaya/i_cuwa_tu_ci_Wyli (1).xml` | counter-less twin |
| 15 | `Sakizaya/idaw_kisu_itebun_haw (1).xml` | counter-less twin |
| 16 | ``Sakizaya/kinapina_muisi` (1).xml`` | counter-less twin |
| 17 | `Sakizaya/masasudih_madayum_maladay_tu_utiih (1).xml` | counter-less twin |
| 18 | `Sakizaya/mipitulikan_ni_Yu_Ku_Tipus_Sayun-matinengay_mi_sangaay_tu_luma'mahamintu_nizaamuliays_i (1).xml` | counter-less twin |
| 19 | `Sakizaya/mipitulikan_ni_Yuku_Tipus_Sayun-mizizaw_ci_bakian (1).xml` | counter-less twin |
| 20 | `Sakizaya/mitena’tu_libung_a_imelang,_Taywan_u_canan_a_kawawan_ku_sapasubana’_tu_kitakit (1).xml` | counter-less twin |
| 21 | `Sakizaya/sakasenengan_aku_a_labang (1).xml` | counter-less twin |
| 22 | `Sakizaya/tahak_atu_wawa_izay_“lahad”_tuyni_a_pasubana’_tu_wawa_u_kasatiman (1).xml` | counter-less twin |
| 23 | `Sakizaya/tulu_idaw_ku_pangkiw_a_hahunan_,_tulu_idaw_ku_pangkiw_a_tatukusn (1).xml` | counter-less twin |
| 24 | `Sakizaya/u_canan_ku_daesu (1).xml` | counter-less twin |
| 25 | `Sakizaya/u_nabalucu'an_patucek_tu_wayway_atu_kaku_nu_mita (1).xml` | counter-less twin |
| 26 | `Sakizaya/u_tatayna_hananay_,_kanca_minanam_tu_mahiniay (1).xml` | counter-less twin |
| 27 | `Sakizaya/非洲_u_kaliyuhan_nu_sumamaday_a_niyazu'tatayna_wlu_amihcaan_siwawatu (1).xml` | counter-less twin |
| 28 | `Seediq/Bnhangan_kndah_kari_Sediq_Puyuma_-_kndadax_pntingan_btunux_mi_kndadax_pntingan_dima (1).xml` | counter-less twin |
| 29 | `Seediq/Tminun_miri (1).xml` | counter-less twin |

Two kept files still carry ` (1)` in their names (`Atayal/msin (1).xml`,
`Sakizaya/Oro’raw (1).xml`) because the scrape never wrote a counter-less
copy for those two titles. Their ids are the plain title-derived ids;
renaming the files would be a further change nobody ruled on, so they were
left alone (noted in the README).

No TEXT ids are rewritten anywhere in the pipeline any more — the
`dup<n>` suffixes of the previous draft are gone.

## Ruling 2 — articles with no Formosan content deleted (11 files)

Criterion (mechanical): **no FORM in the article contains a single Latin
letter**. All five languages use Latin orthographies, so a Latin letter is
the minimal signature of Formosan content; CJK, digits, and punctuation
are not. This subsumes the four punctuation-only articles the retired
`drop_empty_phon.py` used to patch.

| deleted file | full FORM content | what it is |
|---|---|---|
| `Amis/RyuHover.xml` | `.` | punctuation only |
| `Atayal/UN.xml` | `聯合國 : 193個國` | Chinese gloss ("United Nations: 193 countries") |
| `Atayal/南澳部落.xml` | `== .` | heading markup + `.` |
| `Atayal/泰雅維基百科泰雅姓名學四.xml` | `== 命名的原則與方式 ==` | Chinese section heading |
| `Atayal/範例.xml` | `== 部落 == 範例部落....` | Chinese heading + "example village" |
| `Atayal/紋面文化.xml` | `== .......` | heading markup + dots |
| `Paiwan/kavayan.xml` | `我覺得怪怪的` | Chinese editorial remark ("this seems off to me") |
| `Paiwan/pinaywanan.xml` | `我覺得是錯的` | Chinese editorial remark ("I think this is wrong") |
| `Sakizaya/Dadaya_suleda_a_kung-cu.xml` | `" .` | punctuation only |
| `Sakizaya/Sasapaiyuwan_a_samar.xml` | `撒 奇 萊 雅 族 的 民 族 植 物 記 錄 單` | Chinese title ("Sakizaya ethnobotany record sheet") |
| `Sakizaya/mihapu.xml` | `宣布 源自日語` | Chinese gloss ("announce — from Japanese") |

Each was a single-`S` article; the table shows its entire text. Note
`Atayal/UN.xml` contains digits (`193`) — digits do not count as Formosan
content, and under the corpus counting rules these 11 files still
contributed 22 tokens (see "Token delta").

## Ruling 3 — dialect stays "unknown" (closed)

No TEXT in the published corpus had a dialect attribute (all 13,278;
matches issue #78's V036 count — the pre-flight brief's "five TEXTs" was
an artifact of P003 deduping findings by `(lang, dialect)`). Wikipedia
articles are community-written encyclopedia pages with no dialect
statement, so `add_dialect_attrs.py` sets `dialect="unknown"` on all
13,238 surviving TEXTs.

**The trv question is closed**: `dialect="unknown"` stands, which keeps
the Seediq Wikipedia counted as *Seediq* (trv counts as Truku only with
an explicit `dialect="Truku"`) — consistent with how this corpus has
always been counted.

Per-file reasoning for the five port-gate exemplars is unchanged:

| file | xml:lang | reasoning |
|---|---|---|
| Amis/''ayam.xml | ami | ordinary Amis article ('ayam "bird" — about the chicken, 雞); no dialect statement → unknown |
| Atayal/'Etolan.xml | tay | Atayal-language article about the village 'Etolan; topic ≠ language → unknown |
| Paiwan/1984.xml | pwn | year article; no dialect statement → unknown |
| Sakizaya/'Oponoho.xml | szy | article **about** the 'Oponoho (Mantauran Rukai) village, **written in Sakizaya** → xml:lang stays szy, dialect unknown |
| Seediq/'Oponoho.xml | trv | same topic on the trv wiki, written in Seediq → xml:lang stays trv, dialect unknown |

## Ruling 4 — wiki-markup residue retained (closed)

**V129 (68 asterisks) and V146 (70 literal `|`) are ignored**: the
asterisks are wiki list markup and the `|` are table/citation-line
residue in the source article text, not POL-016 elicited-ungrammatical
markers or legacy variant notation. No content edits were made; both
remain in the FORMs (and the `|` still flows into PHON). They are
audit-flagged only (c022 warning rows, V129 HARD, the `|` share of
V146). One line in the README records that this residue is retained
as-is. These are no longer open calls.

## Diff audit vs `main` — 99.94% classified, 0 unexplained

Element-by-element comparison (every TEXT attribute, every S matched by
id and position, every FORM/PHON child) of the regenerated corpus vs
`main`'s XML, with original-tier expectations **independently
recomputed** (a from-scratch implementation of the Seediq normalization
plus the documented clean_xml character rules — NFC, entity decoding,
caret/typographic/full-width mapping, zero-width stripping, null-glyph
canonicalization, whitespace and repeated-punctuation collapse) and
standard-tier expectations recomputed as
`strip_acute_and_breve(null-unit-removed(new original))`. No S added or
removed anywhere in a surviving file; no non-FORM/PHON children exist.

| class | count | why expected |
|---|---|---|
| FILE DELETED: duplicate copy | 29 | ruling 1 |
| FILE DELETED: no Formosan content | 11 | ruling 2 |
| TEXT `dialect="unknown"` added | 13,238 | ruled fix |
| TEXT id changed | 0 | no id rewriting any more |
| FORM original: documented char rules | 742 | Seediq quote normalization (143) + clean_xml canonicalization; each change verified equal to the independently recomputed expectation |
| FORM standard: rebuilt | 1,266 | tier regenerated from the cleaned original; verified equal to the recomputed expectation |
| PHON regenerated | 26,246 | new add_phonology: legacy `x~y` → `[x\|y]`, punctuation no longer carried into PHON |
| *(sub-case)* FORM standard: Hangul left NFD | 27 | see below — mechanism identified, not a corpus defect |
| **total classified** | **41,532** | |
| **UNCLASSIFIED** | **0** | |

The 27 standard-tier FORMs that did not match the recomputation are all
the same known mechanism: `QC/utilities/_accents.strip_accents` decomposes
text to NFD and recomposes **per grapheme cluster**, so Hangul syllables
(which decompose into conjoining *jamo*, not combining marks) come back
**decomposed** — e.g. `서울` (U+C11C U+C6B8) becomes U+1109 U+1165 U+110B
U+116E U+11AF. It affects the 27 articles that quote Korean names/titles
(Sakizaya 18, Paiwan 5, Amis 2, Seediq 2; 93 spans, 56 distinct tokens).
The original tier is NFC and unaffected; no validator fires. This is a
**QC-tool nit, not corpus data**: a one-line fix (`return
unicodedata.normalize("NFC", "".join(result))` at the end of
`strip_accents`) would remove it for every corpus, but shared-tool changes
were out of scope for this turn — see open items.

Serialization artifacts: none — XML declarations, indentation, and
no-newline-at-EOF are byte-preserved outside the changed values.

**Cross-check against the previous draft of this turn** (commit
`f62163ae3`, whose diff vs `main` was audited to 0 unclassified): the new
output differs from it in exactly (a) the 40 deleted files, (b) the two
surviving counter-named files whose ids revert from `…_dup1` to the plain
id, and (c) the removal of the wrongly committed `XML/cleaner_warnings.csv`
— **zero other byte differences**, confirming the content pipeline is
unchanged and only the two new deletion steps moved.

## Token delta

count_tokens (corpus rules): 5,112,067 → 5,103,288 (**−8,779**), fully
attributed:

| language | main | now | delta | duplicate-copy deletions | no-content deletions | other |
|---|---|---|---|---|---|---|
| Amis | 1,984,068 | 1,982,130 | −1,938 | −1,935 | 0 | −3 |
| Atayal | 555,482 | 555,392 | −90 | −85 | −5 | 0 |
| Paiwan | 123,727 | 123,725 | −2 | 0 | −2 | 0 |
| Sakizaya | 1,656,403 | 1,649,981 | −6,422 | −6,407 | −15 | 0 |
| Seediq | 792,387 | 792,060 | −327 | −327 | 0 | 0 |
| **total** | **5,112,067** | **5,103,288** | **−8,779** | **−8,754** | **−22** | **−3** |

The deletion columns were measured by running `count_tokens.py` over the
`main` copies of the 40 deleted files (8,754 + 22 = 8,776). The remaining
−3 is the previously reported and unchanged content effect: three
standalone `Ø` glyphs (2 in `Amis/Tamorak.xml`, 1 in
`Amis/Tayal_no_'aol.xml`) — decorative bullets in source-credit lines —
canonicalized to `∅` by clean_xml and removed from the S-level standard
tier by standardize's null-unit removal, where they previously counted as
tokens (`Ø` is a letter to `isalnum`).

The 22 tokens from the no-content articles are CJK runs (e.g. `我覺得怪怪的`
is one token, `撒 奇 萊 雅 …` is 13) — they counted as tokens only because
the counting rule accepts any chunk containing a letter.

## Validators before → after

Baselines were re-measured this turn against a copy of `main`'s XML with
its own self-consistent published-id index (so V081 reports the real 58
intra-corpus collisions rather than 13,278 self-matches against the shared
checkout).

- `validate_xml`: **HARD 13,336 → 0**, and **0 SOFT** — the validator
  reports `13238 files, 0 with issues`.
  - V036 missing dialect 13,278 → **0**
  - V081 id collision 58 → **0** (the 29 duplicate files are gone)
  - V073 empty PHON: never reached a committed state; 0 now.
- `validate_text`: HARD 154 → **68**; SOFT 268,913 → **243,130**.
  - V131 zero-width/BOM 86 → **0** (clean_xml removes them)
  - V147 phon_legacy_tilde 21,276 → **0** (PHON regenerated)
  - V146 malformed variant group 78 → **70** — the 8 legacy artifacts are
    gone; the remaining 70 are literal `|` in source article text, ruled
    ignored (ruling 4)
  - V129 asterisk_in_standard_FORM 68 → **68**, ruled ignored (ruling 4);
    this is the only remaining HARD finding class
  - V116 non-ascii 25,501 → 21,071; V122 188,106 → 187,998; V126 5,437 →
    5,422; V133 4,913 → 4,989 (+76: dash look-alikes canonicalized to `-`
    now match the rule); V137 16,828 → 16,806; V111/V134/V136/V138/V142
    byte-unchanged.
- `validate_port_readiness`: P003 HARD 5 → 0 (unchanged from the previous
  draft; the dialect fix is what clears it).

## Quote corrections — ZERO, as required

Amis/Atayal/Paiwan/Sakizaya dictionaries are armed (Seediq's was deleted
by the edge-filter ruling); the corpus has **no TRANSLs**, so the tq==0
guard suppresses conversion everywhere. The run wrote **no
`quote_corrections.csv`** — zero c031/c032, matching Phase A's
measured-zero expectation. c030 ambiguity flags are suppressed for
Wikipedias by the documented fiat (implemented in clean_xml via the
`is_wikipedia` path check).

## Sidecars (POL-033)

- The historical **committed** `XML/cleaner_warnings.csv` (429 rows) is
  deleted. **Correction to the previous draft**: that commit deleted the
  old file but then committed *this run's* `cleaner_warnings.csv` (144
  rows) in its place. It is now removed from the tree and from git.
- Pre-existing `XML/delete_empty_forms.log` moved to `CodeAndDocs/`
  alongside the other historical scrape-provenance logs.
- This run produced `XML/cleaner_warnings.csv` with **c007 (bopomofo) ×40
  and c022 (asterisk) ×103** — audit flags only, no corrections; reviewed
  and deleted. `XML/` now contains only the five language directories.
- No `standardize_warnings.csv`, no `html_entities.log`, no
  `quote_corrections.csv` were produced.

## Issue #78 claim dispositions (non-authoritative input, all verified)

| claim | verdict | action |
|---|---|---|
| 13,278 V036 missing-dialect | CONFIRMED | fixed (`dialect="unknown"` corpus-wide, committed script); V036 → 0 |
| 58 V081 id collisions | CONFIRMED | fixed by deleting the 29 duplicate copies (ruling 1); V081 → 0 |
| 86 V131 zero-width/BOM | CONFIRMED | cleared by the clean_xml rerun → 0 |
| 68 V129 asterisks | CONFIRMED | ruled IGNORED (wiki markup residue, retained as-is) |
| 78 V146 malformed PHON groups | CONFIRMED | 8 legacy artifacts cleared; the 70 literal-`\|` findings ruled IGNORED |
| 21,276 V147 legacy tilde | CONFIRMED | PHON regenerated → 0 |
| P003 port gate fails | CONFIRMED | → 0 HARD |
| 415 SOFT duplicate groups / 985 occurrences | not re-measured | sentence-level duplication is SOFT here by POL-022 (no dedup step declared); the 29 whole-article duplicates are now gone, which removes part of it |
| 2 V142 marginal examples need source review | CONFIRMED (still 2) | human source-review worklist; out of scope |
| "regenerate PHON, fix generator path, no hand edits" | — | done: everything via committed scripts + `make_xml.sh` |

## README

Updated for the rulings: 7-step pipeline with the two deletion steps,
13,238-article count, "one file per article" note (including the two
surviving `(1)` filenames), retained-markup-residue note, and a pointer to
the orthography appendix below. Historical scrape provenance and the
per-language apostrophe section are unchanged.

## Open items for maintainer

1. V142 ×2: human source review.
2. Hangul NFD in the standard tier (27 articles) — one-line fix in
   `QC/utilities/_accents.strip_accents`, a shared-tool change affecting
   every corpus that regenerates.
3. Post-merge: GitBook corpus page check (sweep ruling 4).

**UNEXPLAINED: none.** Ready for review/merge.

## Follow-up turn (`fix/wikipedias-v142`, 2026-08-12)

Two maintainer rulings, closing open item 1 above (V142) and the
Ortho113 question left open by the appendix.

**1. V142 → 0 — the stray leading `?` removed via the manual-edits
mechanism.** `Sakizaya/miladlad_tu_udip.xml` (single `S id="0"`, the whole
article body in one FORM) began with `? `. Ruled: scrape debris, not a
POL-016 grammaticality marker — the article simply starts after it — so
the `? ` (marker plus following space) is dropped from the **original**
tier; the standard tier and PHON regenerate from it.

- Recorded with `QC/utilities/capture_manual_edits.py` (hand-edit the
  original FORM, capture against `HEAD`) into the corpus's first
  `CodeAndDocs/manual_edits.xml`: one `FILE` group, one `S`, stored on the
  strip() basis (standard FORM and PHON removed). `manual_edits.md` is the
  generated changelog.
- `QC/cleaning/apply_manual_edits.py` wired into `make_xml.sh` as **step 1**
  — immediately after the snapshot restore and before `clean_xml`, per
  `QC/README.md` ("before running other cleaners"); the later steps renumber
  to 2–8. Run output: `apply: 1 edit(s) across 1 file(s); 0 no-op(s)`.
- Full pipeline re-run from the POL-035 snapshot. Diff vs the previous
  published state is **exactly one file, exactly that sentence's four
  tiers** (original/standard FORM, original/standard PHON); the sentence
  now starts `makatukuh i lalud, …` in both FORM tiers, and the PHON tiers
  lose the leading space the removed `?` left behind. 13,238 files, no
  other byte changed. `cleaner_warnings.csv` was identical to the reviewed
  run (c007 ×40, c022 ×103) and deleted per POL-033.
- Validators: `validate_text` **V142 2 → 0** (SOFT total 243,130 →
  243,128, i.e. −2 and nothing else moved); HARD unchanged at 68 (the
  ruled-ignored V129 asterisks); `validate_xml` still 0 issues.
- The article's CJK-in-Formosan text is unrelated and untouched.

**2. Ortho113 kept corpus-wide (documentation only).** See the decision
recorded at the end of the appendix below. No code or data change; the
same paragraph is mirrored in `Corpora/Wikipedias/README.md` (PHON note)
and on the GitBook corpus page
(`en-us/the-bank-architecture/corpora/wikipedias.md`, branch
`docs/wikipedias-orthography`).

Remaining open item: the Hangul-NFD nit in
`QC/utilities/_accents.strip_accents` (item 2 above), unchanged.

---

# Appendix — evidence for the Ortho113 assumption (analysis only)

The pipeline phonologizes with `--orthography Ortho113` and no dialect.
This appendix asks what evidence supports that, and what it costs. **No
action was taken; nothing here changed the corpus.**

## (a) What the orthography detector says

`QC/utilities/orthography_detector.py` scores the letter inventory of the
text against every orthography table for the language. Run over the
corpus **combined per language** (original tier, dialect `unknown`, so all
orthographies compete):

| language | best-scoring orthography | score | where Ortho113 lands |
|---|---|---|---|
| Amis | Ortho94 (all five dialect columns tie) | 88.4% | below the top 7 (Ortho113Liberal is 7th at 86.9%) |
| Atayal | Church (Sekolik) / Ortho94 (Sekolik) tie | 86.1% | 5th, 84.3% |
| Paiwan | **Ortho113** (Eastern/Northern/Central/Southern tie) | 82.1% | 1st |
| Sakizaya | **Ortho113** | 73.2% | 1st (Ortho94 2nd, 65.0%) |
| Seediq | **Ortho113** | 87.9% | 1st (Ortho94 4th, 87.9%) |

Per **article** (not a sample — all 13,238 articles scored individually):

| language | articles | best = Ortho113 | other winners | median score gap Ortho113→winner | articles with gap > 0.05 |
|---|---|---|---|---|---|
| Amis | 2,000 | 225 (11.2%) | Ortho94 997, MinEd 456, TaiwanNandao 102, Church 98, Ortho113Liberal 91, Huang 30, Montgomery 1 | 0.018 | 474 |
| Atayal | 3,016 | 292 (9.7%) | Church 1,586, Ortho94 1,138 | 0.018 | 0 |
| Paiwan | 472 | 157 (33.3%) | Ortho94 309, Church 4, MinEd 2 | 0.012 | 0 |
| Sakizaya | 5,692 | 5,209 (91.5%) | Ortho94 483 | 0.000 | 273 |
| Seediq | 2,058 | 824 (40.0%) | Ortho94 1,130, Pgagu 53, TaiwanNandao 44, Ochiai 7 | 0.002 | 10 |

Reading: the detector's per-article "winner" flips a lot, but the margins
are tiny (median 0.000–0.018 on a 0–1 scale) — it scores *inventory
coverage*, and a short article that happens not to use one letter of a
larger inventory hands the win to the smaller table. Real per-article
*orthographic* variation is not what this measures. The one systematic
signal is Amis, where Ortho94 beats Ortho113 corpus-wide and in half the
articles (see (c) — it is the o/u treatment, not a different spelling
convention).

## (b) Cost of the assumption: `*` (unmapped characters) in PHON

`add_phonology` writes `*` for any character with no IPA value. Measured
over the generated PHON tiers (both original and standard PHON):

| language | `*` chars / PHON chars | PHON tokens containing `*` | of the star-producing source characters: digits | Latin letters | CJK/kana/hangul | other |
|---|---|---|---|---|---|---|
| Amis | 466,799 / 33,550,462 (1.39%) | 181,029 / 3,965,408 (4.57%) | 89.3% | 6.7% (g 6,165; G 3,038; z 1,833; J 1,717; q 1,205) | 3.5% | 0.6% |
| Atayal | 155,290 / 7,165,846 (2.17%) | 67,325 / 1,110,826 (6.06%) | 68.8% | 13.0% (d 3,608; f 2,305; v 1,157; D 837; F 757) | 17.9% | 0.2% |
| Paiwan | 36,732 / 1,427,090 (2.57%) | 11,789 / 247,464 (4.76%) | 50.3% | 5.9% (f 360; x 107; F 72; ț 66; ș 65) | 42.3% | 1.5% |
| Sakizaya | 507,638 / 22,281,540 (2.28%) | 159,132 / 3,300,408 (4.82%) | 60.4% | 4.4% (v 2,778; R 2,750; J 1,228; x 972; V 918) | 33.9% | 1.3% |
| Seediq | 250,295 / 8,946,740 (2.80%) | 105,680 / 1,584,400 (6.67%) | 85.6% | 8.8% (f 4,148; F 2,206; v 1,439; z 1,350; V 545) | 4.2% | 1.5% |

(The percentage split is computed over the standard tier, where each
star's source character is identifiable; the star totals cover both
tiers.)

**None of this is Ortho113's fault**: 50–89% of stars are digits (dates,
population figures, footnote numbers), and most of the rest are CJK
quotations and loanword letters (`f`, `v`, `g`, `q`, `z`, `x`, `J`, `R`)
that no Formosan orthography table maps. Swapping Ortho113 for Ortho94 or
Church would not change them — those tables have the same or smaller
letter inventories.

## (c) Where the schemes actually disagree, and how often

Comparing Ortho113's dialect-agnostic column against each rival table,
counting occurrences of the affected letters in the standard tier:

| language | rival | letters that map differently | occurrences |
|---|---|---|---|
| Amis | Ortho94 | `o`: `[o\|u]`→`o`; `u`: `[o\|u]`→`u`; `d`: `[ɬ\|ɮ]`→`ɬ`; `b`,`v`: `[b\|v]`→absent | 973,550 / 40,993 / 218,698 / 16,738 |
| Amis | Church | as above plus `f`: `f`→`[f\|v\|b]` | +113,089 |
| Amis | MinEd | as above plus `'`: `ʡ`→`ʔ` | +294,036 |
| Atayal | Church | `s`: `[s\|ɕ]`→`s`; **`e`: `e`→`ə`**; `c`: `[ʦ\|ʨ]`→`ʦ` | 118,746 / **35,336** / 29,543 |
| Atayal | Ortho94 | `s`: `[s\|ɕ]`→`s`; `b`: `β`→`[β\|v]`; `c`: `[ʦ\|ʨ]`→`ʦ` | 118,746 / 52,229 / 29,543 |
| Paiwan | Ortho94 / Church | `o`: `u`→absent | 2,031 |
| Sakizaya | Ortho94 | `'`: `[ʔ\|ʡ]`→`ʡ`; `f`: `f`→`b`; `g`,`b`: absent in Ortho94 | 106,192 / 6,507 / 267,655 |
| Seediq | Church (Tegudaya) | `j`: `ɟ`→`ɖʐ` | 18,777 |

The decisive pattern: for almost every letter where the schemes disagree,
**Ortho113's value is a variant group, not a competing single value**.
Ortho113 says "this letter is `o` *or* `u`" where Ortho94 commits to one.
The blanket assumption therefore yields PHON that is *under-specified*,
not wrong. How much of the corpus is under-specified this way:

| language | variant groups in PHON | PHON tokens containing one | articles affected | groups used |
|---|---|---|---|---|
| Amis | 2,499,880 | 2,036,512 / 3,965,408 (51.4%) | 1,989 / 2,000 | `[o\|u]` 2,029,008; `[ɬ\|ɮ]` 437,396; `[b\|v]` 33,476 |
| Atayal | 296,533 | 275,097 / 1,110,826 (24.8%) | 2,947 / 3,016 | `[s\|ɕ]` 237,490; `[ʦ\|ʨ]` 59,043 |
| Sakizaya | 750,820 | 625,500 / 3,300,408 (19.0%) | 5,602 / 5,692 | `[r\|ɾ]` 644,628; `[ʔ\|ʡ]` 106,192 |
| Paiwan | 0 | 0 | 0 | — |
| Seediq | 0 | 0 | 0 | — |

The genuinely *conflicting* single-value mappings — where Ortho113 commits
to one IPA value and a plausible rival commits to a different one — are
small and enumerable: Atayal `e` (`e` vs Church `ə`, 35,336 occurrences;
Church is the per-article winner for 52.6% of Atayal articles), Seediq `j`
(`ɟ` vs Church-Tegudaya `ɖʐ`, 18,777), Sakizaya `f` (`f` vs Ortho94 `b`,
6,507), and Paiwan `o` (`u` vs a letter Ortho94/Church do not list,
2,031). Everything else is Ortho113 being more cautious than the rival.

## Conclusion

Per-article orthography variation is **not visibly present**: the
detector's per-article winner changes constantly, but with median score
gaps of 0.000–0.018 that is inventory-coverage noise on short texts, not
evidence that different articles use different spelling conventions.
Corpus-wide, Ortho113 is the top-scoring table for Paiwan, Sakizaya, and
Seediq; for Amis and Atayal, Ortho94/Church score higher, and the reason
is visible in the tables: those schemes commit to a single IPA value where
Ortho113 records a dialect variant group. The practical cost of the
blanket assumption is therefore mostly *ambiguity* rather than error —
19–51% of Amis/Atayal/Sakizaya PHON tokens carry a `[x|y]` group, and 0%
of Paiwan/Seediq do — while outright wrong values are bounded by the four
conflicting letters above (Atayal `e` 35,336; Seediq `j` 18,777; Sakizaya
`f` 6,507; Paiwan `o` 2,031 — together under 0.4% of the corpus's letter
occurrences). Separately, 1.4–2.8% of PHON characters are `*`, but ~50–90%
of those are digits and the rest are CJK/loanword letters that no scheme
maps. If any of this is worth acting on, the highest-value item is Atayal
`e`, where the corpus-wide top-scoring scheme (Church) disagrees with
Ortho113 on a vowel occurring 35,336 times.

## Decision (maintainer ruling, 2026-08-12)

**Ortho113 is used corpus-wide**, for the reasons already stated above.
The one material consequence of the blanket assumption — Atayal `e`
(Ortho113 `e` vs Church `ə`, 35,336 occurrences) — is known, quantified
above, and **accepted as unadjudicable**: the articles state no
orthography and carry no translations, so no evidence available to us
could settle which value their authors intended. The divergence is small
enough to live with, and is documented for users in the corpus README and
on the GitBook corpus page rather than acted on. No code or data change.
