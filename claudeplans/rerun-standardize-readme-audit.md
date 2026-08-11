# Regeneration sweep — per-corpus pre-flight audit and tracking doc

**Refreshed 2026-08-11**, after the merge of `feature/shared-source-phonology`
(#92) and the two regeneration branches (#98 HundredPaiwanStories, #99
Presidential_Apologies) into `main`. Originally written 2026-08-10 on
`feature/rerun-standardize-phonology` as a README audit for a naive
standardize+phonology rerun; now serves as the **sweep tracking doc** (step 0
"classify" of `2026-08-10-policy-alignment-sweep-scope.md`). Each corpus README
was checked for (a) assumed orthographies and (b) XML changes made **after**
standardization/phonology that a naive rerun would destroy.

## Maintainer rulings (2026-08-11) — supersede parts of the sweep-scope doc

1. **Quote correction rolls out language-by-language *within* the sweep**, not
   Amis-first-others-later. When a language's first corpus comes up, its
   attestation dictionary (`QC/validation/reference/<Language>/attestation.txt`)
   is reviewed then; corrections run for that language from that point.
   Status: Amis hand-validated; the other 15 committed dictionaries are
   machine-generated and unreviewed (Siraya's has only 37 entries — weakest
   guard). This replaces sweep-scope "tooling gap 3", which recommended
   Amis-only. Two refinements (2026-08-11):
   - **Skip rule — assessed per corpus, not per language** (maintainer
     clarification 2026-08-11): each language has many orthographies, so
     "does the orthography have `'`?" is answered against the orthography
     the corpus's README declares for its original tier, corpus by corpus.
     A corpus whose declared orthography lacks `'` (cross-checked by an
     empirical apostrophe count) needs no dictionary review before its
     cleaning run. Group 1 skips on this basis: Latham, Glosbe-Truku,
     SEALS33-Truku (2 loanword apostrophes, protected). Per-corpus table:
     `claudeplans/phase-a-reviews/00-consolidated.md`.
   - **Phase A is revisitable**: if Phase B pipeline runs surface regen
     differences that interact with the quote mitigation (classifier
     behavior, dictionary contents), the affected language's Phase A review
     is reopened rather than patched ad hoc.
2. **The Amis quote-review worklist** (`quote_review_nonwiki_amis.md`, 239
   sentences, 37 likely-real `'`→`"` fixes) folds into the per-corpus worklists
   of the Amis corpora it draws from (Glosbe, ePark, Safolu, …) — reviewed as
   each is swept, not as a standalone task.
3. **Conversion-table verification happens per corpus**: before trusting a
   corpus's standard tier, run `validate_conversion_table.py` on the table(s)
   its pipeline uses (this also covers the Seediq/Truku V152/V153 wrinkle when
   Seediq/Truku corpora come up). Any tables still unverified when the sweep
   ends get a final cleanup pass.
4. **Closing steps are mandatory per corpus** — see the procedure below: a
   regeneration diff against `main` must be ≥99.9% classified into expected
   categories ("mostly expected" is insufficient), and after merge approval the
   README **and the GitBook corpus page** must be updated.
5. **Manual-edit records standardize to `manual_edits.xml`** (ruled mid-sweep,
   2026-08-11): where a corpus records hand edits under a bespoke mechanism
   (see inventory below), its sweep turn migrates them to
   `CodeAndDocs/manual_edits.xml` where the semantics fit (id-keyed
   corrections to parser output — e.g. NTU's `apply_manual_corrections.py`),
   so future maintainers find hand edits in one standard place. Mechanisms
   with different semantics (Nowbucyang's *additions* file merged at build;
   source-side fixes baked into committed intermediates) stay as they are but
   get a README pointer under a "Manual edits" heading.

## Per-corpus procedure

1. **POL-035 snapshot** (non-regenerable corpora only): copy pristine `XML/`
   into `CodeAndDocs/pre_correction_snapshot/` + README note, *before* any
   original-tier correction (quote correction touches originals, so this
   applies even to corpora where only derived tiers seem at stake).
2. **POL-030 capture**: record any unrecorded hand edits (see inventory below)
   via `capture_manual_edits.py` or a committed script.
3. **Attestation dictionary review** — first corpus of each language only
   (ruling 1).
4. **Verify the conversion table(s)** the corpus uses (ruling 3).
5. **Regenerate** as far as possible **without re-scraping or re-OCRing** —
   start from committed intermediates; run the corpus's *full documented
   pipeline* (not a naive standardize+phonology pass) per its README.
6. **Diff audit vs `main`**: element-by-element classification of every change
   into expected categories, HPS-diff-report style
   (`2026-08-11-hps-regen-diff-report.md` is the model). ≥99.9% of changes
   must be understood and expected; unexplained changes block.
7. **Maintainer approval**, then merge. Commit `quote_corrections.csv` rows if
   corrections ran.
8. **README update**: new pipeline description, drop stale notes (e.g. the old
   double-`clean_xml` order), add snapshot/correction notes.
9. **GitBook corpus page update** (4 integration points; use
   `manage_corpus_pages.py`; branch off the GitBook repo's `main`).
10. **Verify**: re-run the baseline validators (V142/V144/V147/port gate) for
    the corpus; V147 and null-family findings should go to zero for it.

Expected diff classes everywhere: null glyphs `ø/Ø→∅`, dash look-alikes → `-`,
curly apostrophes → `'`, U+223C → `~`, C028 entity decoding, C012 hyphen
stripping (segmented sentences), PHON regenerated (legacy `x~y` → `[x|y]`,
punctuation dropped), quote corrections (c031/c032) for dictionary-enabled
languages. Scale note: ~496k published PHON values in ~11k files still carry a
bare tilde — PHON diffs will dominate everywhere.

## Phase A — Group 1 attestation-dictionary reviews (launched 2026-08-11)

Original-tier apostrophe scan of Group 1 (includes typographic variants that
canonicalize to `'`):

| Corpus | Language | Apostrophes | Sentences |
|---|---|---|---|
| FormosanBankGitBook | pwn | 1 | 102 |
| Glosbe | ami | 7,438 | 6,484 |
| Glosbe | tay | 101 | 523 |
| Glosbe | trv | 0 | 112 |
| Glosbe | xsy | 281 | 490 |
| Latham-1862 | bzg/fos | 0 | 62 |
| SEALS33 | trv | 2 | 29 |
| SEALS33 | xsy | 225 | 29 |
| Virginia_Fey_Dictionary | ami | 908 | 2,049 |
| Wikipedias | ami | 147,180 | 2,006 |
| Wikipedias | pwn | 872 | 474 |
| Wikipedias | szy | 53,287 | 5,715 |
| Wikipedias | tay | 49,595 | 3,023 |
| Wikipedias | trv | 1,576 | 2,060 |
| WilangYutasVideos | tay | 857 | 3,014 |

**REV 2 reviews complete 2026-08-11** (rerun under the maintainer's
per-corpus framing and rulings) — reports in `claudeplans/phase-a-reviews/`
(`00-consolidated.md` is the operative sign-off). Verdicts: Atayal /
Saisiyat / Truku / Seediq / Paiwan APPROVE WITH FIXES, Sakizaya APPROVE
(moot — no szy text in Group 1). Saisiyat's approval is **Group 1 only**,
with a process guard: no cleaning of NTU/ILRDF/ePark while its dictionary
is armed, until classifier fixes land. **Total expected Group 1 classifier
corrections: 0** — the only apostrophe changes are the deterministic Seediq
Wikipedia normalization (`normalize_seediq_quotes.py`, branch
`feature/wikipedias-seediq-quote-normalization`, 264 FORMs, applied at the
Wikipedias sweep turn; the ~340 word-internal-apostrophe exception question
is flagged there). New classifier worklist item from REV 2: `attested()`
truncation also breaks at Saisiyat's vowel-length `:`. Awaiting maintainer:
dictionary fix lists (one mechanical branch); internal-apostrophe exception
call; classifier-fix scheduling; Phase B go.

## Group 0 — Already regenerated with the new pipeline (verify-only)

| Corpus | State |
|---|---|
| HundredPaiwanStories | #98 merged. README documents a fully re-runnable pipeline (steps 5–13 safe over published XML; `fill_*` scripts deleted). Token delta zero. **Closing checks run 2026-08-11**: GitBook page already updated (GitBook PR #40); V147 = 0; validate_xml clean. validate_text surfaces a **pre-existing** worklist: V121 HARD ×32 — 16 W elements with `(word)` optional-material parens (e.g. `011S75W3` `(aken)`), present in pre-regen published XML; POL-026 review items, not regen defects. |
| Presidential_Apologies | #99 merged. CJK-annotation removal is scripted step 5 (idempotent). **Closing checks run 2026-08-11**: GitBook page already updated (GitBook PR #43). Found + fixed: 514 PHON values in 8 files still carried legacy `x~y` variant notation (regen f73f24a78 predates the profile migration 33b0e076d). Reran README steps 4–5 on branch `feature/group0-presapol-phon-notation` (commit 672bcd4df); diff 100% classified as notation migration; V147 → 0; validate_xml clean; validate_text SOFT baseline unchanged (465). **Awaiting review/merge.** OPEN linguistic item: dialect-column NA letters star loanword IPA (Puyuma worst). |

## Group 1 — Clear to rerun (orthography known, no post-standardization edits)

| Corpus | standardize | add_phonology | Sweep notes |
|---|---|---|---|
| FormosanBankGitBook | `--copy` | `--orthography Ortho113` | |
| Glosbe | per-lang TSV: Amis `Amis_94_113`(Coastal), Atayal `Atayal_Church_113`, Truku `Seediq_94_113`(Truku), Saisiyat `Saisiyat_94_113` | ami: Ortho94/Coastal; tay: Church; trv,xsy: Ortho94 | Amis quote-review rows land here; Truku table = Seediq/Truku wrinkle (ruling 3) |
| SEALS33 | `--copy` | `--orthography Ortho94` | |
| Virginia_Fey_Dictionary | `--copy` | `--orthography Ortho113` | Hand-cleaned XML → non-regenerable → POL-035 snapshot before Amis quote correction |
| Wikipedias | `--copy` | `--orthography Ortho113` (default IPA; dialect unknown) | Fix the 5 dialect-less TEXTs (port-gate P003) while touched; no rescrape → treat published XML as baseline; ambiguous-apostrophe-is-glottal fiat documented in README |
| WilangYutasVideos | `--copy` | `--orthography Ortho94` | |
| Latham-1862 | `--copy` | none (no phonology by design) | Hand-transcribed → snapshot; `bzg` ISO question (P002) rides along |

## Group 2 — Bespoke post-standardization steps → run the FULL documented pipeline

Naive standardize+phonology would destroy recorded work; each of these runs its
own README pipeline end-to-end instead.

| Corpus | Why naive rerun is wrong | Sweep notes |
|---|---|---|
| **NTUFormosanCorpus** | 17+ post-standardization repair steps; now fully wrapped by `CodeAndDocs/make.sh` (ends with corpus-wide `add_phonology` refresh). | Regen was prepared and verified 2026-08-10 (`2026-08-10-ntu-rerun-diff-audit.md`) but XML deliberately not committed — **its sweep turn is executing that prepared regen** (incl. POL-017 starred-parens fixes). |
| **ePark** | `drop_unmapped_phon.py`, `fix_parenthetical_spacing.py`, second standard-tier clean pass; per-sub-corpus orthographies (Ortho113 / Ortho113Liberal / Ortho94). | Amis quote-review rows land here. |
| **Li-Conjunction-Thao** | `flatten_standard_segmentation.py` required after standardize. | Verify `Thao_Li_113.tsv` first (P006 + ruling 3); V144: 140 M-less W (66%) — segmentation question on the worklist. |
| **Nowbucyang-Truku-Thesis** | Second `clean_xml` (de-segment) after standardize. | Manual sentences merge by id from `data/manual/manual_sentences.xml` — survives rebuilds. Truku wrinkle (ruling 3). |
| **Safolu-Amis-Dictionary** | `remove_duplicate_sentences.py --apply` after phonology (drops 255 sentences). | Dedup step declared → POL-022 duplicates are HARD here. Amis quote-review rows land here. |
| **Song-Kanakanavu-Grammar** | `normalize_standard_forms.py` (128 reviewed decisions) + `fold_standard_stress.py` after `--copy`; wrapper + pinned FormosanBank commit. | Pin needs updating to post-merge main. |
| **RauDong** | `remove_accents.py` after the fact; README: "we do not have a reproducible pipeline." Phonology profile unstated. | Non-regenerable → POL-035 snapshot; profile decision needed (also Group 4-like). |
| **Siraya_Gospels** | Bespoke `regenerate_standard_tier.py`; historical Gravius orthography; no phonology. **Should not be standardized to Ortho113.** | Siraya dictionary = 37 entries → review before any clean run, or pull the dictionary for now (ruling 1). |
| **WakelinTexts** | Standard tier = original minus hyphens; `Yami_Wakelin_113.tsv` "should not be taken seriously"; orthography unidentified. | Hand-built XML → snapshot; V144: 428 M-less W; table verification will likely fail structurally (known — no source profile). |
| **YeddaPalemeqBlog** | Manual `/`-and-`()` hand corrections applied directly to published XML, **recorded only as README prose** (§5) — no id list, no script. | **Capture first** (step 2): rebuild from committed HTML (no re-download), diff vs published to recover the hand edits into `manual_edits.xml`, then proceed. Duplicate M-ids note in README §6 to re-check. |

## Group 3 — No text (out of sweep)

| Corpus | Note |
|---|---|
| TangRecordingsOfTaroko | Audio only; untranscribed. |
| Whitehorn_Collection | Audio only; XMLs are hand-compiled audio-pointer metadata. |

## Group 4 — Underspecified pipeline / unknown phonology profile → needs a call

| Corpus | Gap |
|---|---|
| MontgomeryTexts | No standardize/add_phonology pipeline documented at all (Amis, thin README). |
| ILRDF_Dicts | `standardize` with no TSV (u→o only); no `add_phonology` documented. **16 languages → its turn triggers dictionary review for most languages at once (ruling 1); schedule after the single-language corpora have seeded reviews.** |
| Paiwan_Stories | `--copy`; phonology "the usual way", no profile named. Hand-built XML → snapshot. |
| NTU_Paiwan_ASR | `--copy`; phonology profile not stated; full reproduction needs private inputs (published XML present). Snapshot. |

## Manual-edit record inventory (POL-030, surveyed 2026-08-11)

No corpus has a `CodeAndDocs/manual_edits.xml`, but most hand edits ARE
recorded under other names:

| Corpus | Mechanism | Reproducible? |
|---|---|---|
| NTUFormosanCorpus | `CodeAndDocs/scripts/apply_manual_corrections.py` (element-id-targeted), run by `make.sh` | ✔ |
| Nowbucyang-Truku-Thesis | `data/manual/manual_sentences.xml`, merged by id at build step 14 | ✔ |
| HundredPaiwanStories | README "Manual corrections (provenance only)" — one-off fixes listed with sentence ids; corrected state committed | ✔ (documented provenance) |
| Siraya_Gospels | OCR hand corrections baked into digitized source; hyphen fixes later automated (`fix_linebreak_hyphens.py`) | ✔ |
| Song-Kanakanavu-Grammar | README states apply step is a no-op (no records needed) | ✔ |
| **YeddaPalemeqBlog** | README §5 prose only — edited sentences not identified anywhere | **✘ — capture at sweep turn** |
| Paiwan_Stories, WakelinTexts, Whitehorn, Virginia_Fey, Latham-1862 | XML/tables themselves are the hand product (no separable edit records) | n/a — POL-035 snapshot instead |

## Recommended order

1. **Group 0** closing checks (cheap; exercises the ruling-4 checklist end to
   end on corpora whose diffs are already understood).
2. **Group 1**, single-language corpora first — each seeds its language's
   dictionary review (ruling 1).
3. **Group 2**, with NTU early (regen already prepared and audited) and
   Siraya/Wakelin/RauDong late (weakest guards, most judgment calls).
4. **Group 4** after maintainer calls on the missing profiles; ILRDF_Dicts
   last (touches nearly every language).
5. **End of sweep**: verify any conversion tables not yet covered (ruling 3);
   re-run all baseline sweeps (`2026-08-10-new-rule-baselines.md`); announce
   the token-count discontinuity as in 2026-06.
