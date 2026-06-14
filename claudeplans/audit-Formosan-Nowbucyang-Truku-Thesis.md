# Dev-repo audit — Formosan-Nowbucyang-Truku-Thesis

**Date:** 2026-06-10 · **Status:** in progress (pre-port). Steps 1–2 done; specific
data issues triaged with the maintainer; Step 3 (run *current* validators) and
Step 4 (source diff) still outstanding.
**Source:** Hsu, Lowking Wei-Cheng / 許韋晟. 2008. 太魯閣語構詞法研究 *Word Formation
in Truku*. MA thesis. `xml:lang="trv"` (Truku). One TEXT = the thesis's numbered
example sentences.
**Audit driver:** `audit-dev-repo` skill + `claudeplans/2026-06-09-dev-repo-audit-briefing.md`.

## Overall assessment

A conscientious, well-instrumented **PDF → XML** pipeline (decrypt → `pdftotext
-layout` (+PyMuPDF/pdfplumber), no OCR → parse numbered examples → normalize →
gloss-align W/M → dedupe → quality-filter → build XML). Raw text is preserved at
every stage and every cleaning action is logged to sidecar CSVs. Hunter clearly
read our conventions (handles `*`-ungrammatical, footnotes, records the source
Ortho94, even ran an *older* version of our QC). Character/punctuation handling
is gentle and faithful. The issues below are mostly **data-curation nuances of
linguistics-thesis examples** (optional arguments, alternative renderings, Q&A
pairs), not character/punctuation damage.

### The four highlighted concerns — initial read (verify in Step 3/4)
- **(a) orthography characters:** low risk. `clean_inline` = NFC + whitespace
  collapse + remove-space-before-punct only; deletes no letters. `_`/`:`
  preserved (mid-token `:` survives; **word-final `:` is stripped at the W tier**
  — flag for Step 4 if Truku uses it).
- **(b) punctuation/segmentation:** low risk in the original tier (`-`, `<>`,
  in-token `=` preserved). Removes footnote digits, `(*…)` ungrammatical
  parentheticals, layout `=`.
- **(c) conventions:** the **"standard" tier is not Ortho113** — it's a
  paren/Ø-stripped original; real Ortho94→Ortho113 transliteration is **our job**
  at port time (handoff, not a bug). W/M emitted only when reliably aligned.
- **(d) extraction artifacts:** handled well — `*`-initial forms excluded
  (`ungrammatical_starred_form`), footnotes stripped, parse-warnings/confidence
  tracked.

## Findings ledger

Each detector is a new standalone script in the dev repo (`scripts/`, additive —
nothing existing was modified) writing a review CSV under `data/processed/`.
**All are pre-implementation: lists for hand-check before any pipeline change.**

| # | Issue | Affected | Disposition (maintainer 2026-06-10) | Review artifact |
|---|---|---|---|---|
| F1 | **Unglossed / parenthesized form options** | 11 | split-handling, by sub-type (below) | `identify_unglossed_options.py` → `unglossed_option_candidates.csv` |
| F2 | **Alternative translations** (paren in Chinese, not in Truku) | 33 | alt→two TRANSL+`ver="alt"`; note→nothing; slash→defer | `identify_alternative_translations.py` → `alternative_translation_candidates.csv` |
| F3 | **Dropped 2nd sentence** (Q&A; one form per block) | 2 | recover the dropped sentence | `identify_dropped_sentences.py` → `dropped_sentence_candidates.csv` |
| F4 | **Deduplication drops a sentence** (e.g. E010C) | (by design) | **keep dedup as-is** | `data/processed/duplicates.csv` (his) |
| F5 | **`words_only` gloss loss** (no per-morpheme TRANSL) | 32 | see breakdown | `data/processed/gloss_alignment_audit.csv` (his) |

### F1 — parenthesized form options (11)
The form carries a parenthesized span the gloss didn't cover, so the aligner fell
to `words_only`. Three sub-types:
- **`optional_unglossed` (2)** — E008B/E008C; short optional argument (`(ka yaku)`)
  the gloss skips → **two S**: glossed-core (option removed) + all-words (parens
  deleted, no glosses).
- **`optional_glossed` (1)** — E011D; the option *is* glossed → two S, both
  glossable (with-option / without-option).
- **`variant_clause` (8)** — the parenthetical is a whole alternative clause
  (`X. = (Y.)`, or a clause ending in `?`/`!` such as E027A) → **two separate
  variant S** (gloss on the first), NOT one concatenated form. *(Classified by the
  parenthetical being a clause, not by raw length — E027A was initially mislabeled
  `optional_unglossed` and corrected 2026-06-10.)*

**Cross-link:** `variant_clause` and F2 alt-translations are largely independent —
of the 8, only **E011E** has both (a word-order form variant *and* a corresponding
alternative translation). The F2 detector cannot surface E011E (it skips any
example whose form has parens), so E011E is the one case needing both treatments.

### F2 — alternative translations (33)
Form has no parenthetical; the Chinese translation does.
- **`alt_translation` (25)** → emit primary `<TRANSL>` + the alternative as a
  second `<TRANSL ver="alt">` (FormosanBank schema). e.g. E010A
  `我要打那個小孩。(那個小孩要被我打)`.
- **`explanatory_note` (7)** → leave as-is (the paren clarifies a word).
- **`inline_slash_option` (1)** → defer (`你今天(現在)/明天/昨天…`).
*(alt/note boundary is heuristic — eyeball borderline rows; the `= (…)` ones leave
a stray space before `。` to clean at implement time.)*

### F3 — dropped second sentences (2)
`_parse_example_block` keeps one form per numbered block; a second sentence falls
into `commentary_raw` (never emitted). Genuine cases:
- **E007D (RAW_0019)** — Q&A: kept Q `N-nima ka patas nii?`; **dropped A**
  `N-naku. / * mu.` → `是我的。` (drop the `* mu` ungrammatical alt on recovery).
- **RAW_0243 (p95 36a)** — kept `Gaga t-m-xiluy ka Tusi.`; dropped
  `Tama Lowking ka emp-txiluy nii.`
**Fix:** split such blocks into multiple records — mirror the existing chapter-2
compound parser, which already emits several records from one block.

### F4 — deduplication (working as intended; keep)
E010**C** (`Mah-un =na ka qsiya.`) is absent because it is an exact within-thesis
duplicate of RAW_0029 (`duplicates.csv`: `omit_from_xml_keep_sidecar`). **Decision:
keep dedup.** (Note: E010**D** is present and correctly glossed — the originally
reported "E010D missing" was actually E010C, and the cause is dedup, not clitics.)

### F5 — `words_only` gloss loss (32 of 253)
Per-morpheme glosses not emitted because the source gloss didn't align:
- **20 `source_gloss_not_reliably_alignable`** — includes the F1 parenthesized
  cases **and a clitic-driven subset** (form counts `=ku`/`=mu` as a token; the
  gloss fuses `sapah=mu`→`家裡-我`). The clitic subset is the **systematic
  gloss-alignment improvement** worth making (maintainer flagged clitics).
- **7** word-level-gloss-not-emitted; **5** `no_source_gloss_line` (genuine — the
  thesis printed no gloss). The latter two are not fixable from the source.

## Pipeline fixes — F1/F2/F3 IMPLEMENTED (2026-06-10/11)

Edited `scripts/pipeline.py` (additive; his other logic untouched) and re-ran
parse→build. **His internal validator PASSes; S count 253→274** (267 automated +
7 hand-curated via `data/manual/manual_sentences.xml`, see below).
- **F3** `_recover_dropped_second_sentence` (parser): recovers a Q/A answer hidden
  in commentary as a 2nd record (id `…E007D2`), dropping `/ *…` ungrammatical alts.
  Recovers only when a translation exists. → **E007D** recovered.
- **F1** `_xml_variants_for_row` now returns two variants for `optional_unglossed`
  (glossed-core S + all-words no-W S) and `variant_clause` (first-clause S + variant
  S), id suffix `b`. → E008B/E008C, the 7 variant_clause split; E011D/E011E skipped.
- **F2** `_add_translations`: alternative renderings → primary `<TRANSL>` +
  `<TRANSL ver="alt">` (25 rows, e.g. E010A). His validator extended to allow `ver`.
- **F1-translation (2026-06-11)** `_option_variant_translations`: for an
  `optional_unglossed` split, the source translation is now specialized per variant
  instead of duplicated raw — the *option* parenthetical (a slash list `(明天/昨天)`
  or a short particle `(了)`) is **dropped in the glossed-core** variant and
  **resolved to the grammatical option** (the non-starred form token, mapped by slash
  position) **in the all-words** variant. Affected 6 S: E023C `這隻狗我要帶走。` /
  E023Cb `這隻狗明天我要帶走。`, E023D `這隻狗是我帶走的。` / E023Db `這隻狗昨天是我帶走的。`,
  E026A `我吃過飯。` / E026Ab `我吃過飯了。`. Longer/sentence-like parentheticals
  (explanatory notes, alt renderings — e.g. E031B, E010B) are left untouched for F2;
  a post-build sweep confirmed no slash-option list survives in any S translation and
  no non-target translation changed.

Still maintainer-side at port time: clitic-aware gloss alignment (F5 subset);
Ortho94→Ortho113 standardization; the by-hand parens/slash pass.

## Manual additions / hand-pass status

**Manual-additions / OVERRIDE mechanism (new 2026-06-11; upgraded to override same day).**
Hand-curated S live verbatim in `data/manual/manual_sentences.xml` (a well-formed
`<MANUAL_SENTENCES>` root of `<S>` children). `build_formosanbank_xml` now collects
those ids up front and **skips any automated S of the same id**, then appends the
manual copies (with `xml_index.csv` rows). So a manual entry both *adds* S the parser
can't derive AND *overrides* an existing automated S — letting hand-edits to automated
sentences survive rebuilds, which the original append-only version could not (it
skipped same-id entries, so the automated version always won and clobbered hand-edits).
**Workflow:** edit that file, then rebuild — direct edits to `Final_XML` are overwritten.

**DONE — additions (not derivable from the PDF text layer):**
- **E011D2** — the optional_glossed split of E011D, with full M glosses (a W-id typo
  `E011DW3`→`E011D2W3` was corrected).
- **E011E2** — the second word-order variant of E011E (primary + `ver="alt"`).
- **E025A2** — a further hand-added glossed example.
- **E011I/J/K/L** — four examples not derivable from the PDF text layer (a malformed
  `</FORM>` close-tag in E011K, which had made the file unparseable, was corrected).

**DONE — overrides of existing automated S (hand-edits restored after a rebuild
clobbered them; reconstructed from the maintainer's specs + the preserved `-2`
siblings, then re-applied via the override mechanism):**
- **E011D** — original `Mgay =ku pila sunan ka yaku.` (parenthetical dropped),
  standard `Mgay ku pila sunan ka yaku.`, 6 glossed W/M (Mgay→AF-給, =ku→我, pila→錢,
  sunan→你, ka→主格, yaku→我).
- **E011E** — parenthetical removed from the original S-FORM (`N-tama ka patas gaga.`),
  W tier trimmed to that clause's 4 words (the second clause is E011E2).
- **E025A1** — `M-ha =su inu ka sayang?` with two sentence TRANSL (你今天…/`ver="alt"`
  你現在…) and W5 `sayang` morpheme TRANSL 今天 + `ver="alt"` 現在. His internal
  validator's W/M-level TRANSL checks were extended to allow `ver` (only S-level did).

**Ø-in-standard (raised 2026-06-11): not a code bug — a stale committed `Final_XML`.**
The committed XML predated the de-segmentation code and was hand-patched, so it still
showed Ø. *Resolution (see below) moved de-segmentation ownership to FB's `clean_xml`.*

**Standard-tier de-segmentation moved out of the build → owned by FB QC tooling
(2026-06-11).** Two coupled changes:
- **FB `clean_xml` (shared tooling):** C012 now strips the null-morpheme marker `Ø`
  (U+00D8) from the standard S-FORM — together with its bridging hyphen — alongside the
  `-`/`=` it already removed (`QC/cleaning/clean_xml.py`; TDD, 2 fixtures + tests; full
  cleaners suite 73 passed). `Ø` is an annotation, never an orthographic letter, so it is
  stripped unconditionally (even where `-` is a letter, e.g. Bunun/Thao) without eating
  real letter-hyphens.
- **Hunter's build:** the standard tier is now emitted as a **verbatim copy of the
  original** at every level (S/M); the build no longer de-segments it, and the validator's
  three "standard FORM still contains Ø" checks were removed (de-segmentation is no longer
  the build's job). His validator still PASSes.
- **End-to-end proof:** build emits `Ø-dhuq sapah ka tama da.` in both tiers → `clean_xml`
  yields standard `dhuq sapah ka tama da.` (0 residual Ø, 0 S-level hyphens) with the
  original tier untouched. Rationale: `standardize.py --copy` would overwrite any
  build-side standard with a copy of the original anyway, so build-side de-segmentation was
  redundant and fragile; `clean_xml` runs on the corpus in the dev repo (and again later in
  FB) and owns it for **every** corpus.

**Dialect now wired into the build (2026-06-11).** The build never emitted `TEXT/@dialect`
(`use_dialect_or_location_attribute_if_validated: false`), so the maintainer hand-added
`dialect="Truku"` and every rebuild dropped it (re-breaking our V036). Fixed: config now
sets `use_dialect_or_location_attribute_if_validated: true` + `dialect: "Truku"`, and the
build emits `TEXT/@dialect` from config. Our `validate_xml` now reports **0 HARD findings**
(V036 cleared; only the expected SOFT V014 W/M-missing-standard remains).

**Still open:**
- **RAW_0243** (p95 36a) — dropped sentence `Tama Lowking ka emp-txiluy nii.` has **no
  translation in the source**; supply one (then add it to `manual_sentences.xml`) or omit.
- The **1 inline-slash** translation (`你今天(現在)/明天/昨天…`).

## Step 3 — our current validators on the regenerated `Final_XML` (informational)
Run with `--no-exit-on-hard`. Most findings are the expected pre-port state, not
regressions from F1/F2/F3:
- **validate_xml:** **0 HARD** as of 2026-06-11 — the lone `V036` (TEXT/@dialect) was
  resolved by wiring `dialect="Truku"` through config into the build (see above).
  ~2467 SOFT `V014` (W/M lack a standard tier — resolved by standardization at port).
- **validate_text:** 12 HARD `V121` + 83 SOFT `V122` (parens/slashes — the slash
  options + remaining parentheticals awaiting the hand-pass); 9 `V116` non-ASCII; 5 `V135`.
- **validate_glosses:** **161 HARD `V064` (M without TRANSL)** — the real integration
  decision: his glossing is M-level and partial, so unaligned morphemes emit M FORMs
  with no gloss; our V064 requires every M to have a TRANSL. Decide: omit unaligned M,
  complete glosses, or relax V064 for this corpus. Plus 1083 SOFT `V065` (W without
  TRANSL — he glosses at M not W), 20 `V062` infix, 18 `V063` segmentation, 14/20 `V060/061`.

## Outstanding audit steps
- **Step 3:** run the *current* validators (`validate_xml`/`text`/`glosses`) on
  `Final_XML/` — Hunter's `logs/formosan_qc/` used an older pipeline; disregard.
- **Step 4:** source diff for (a)/(b) on a sample; check word-final `:` impact.

## Decisions log
- 2026-06-10: keep deduplication (F4). Alt-renderings → `ver="alt"` (F2);
  explanatory notes untouched; inline slashes deferred. Recover genuine dropped
  sentences (F3). Optional/variant form-parenthetical handling per F1 sub-types.
