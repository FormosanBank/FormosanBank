# QC pipeline overhaul: shared source phonology, tier ownership, new validators, and project policies

This document describes everything that lands in the merge of `feature/shared-source-phonology` into `main` (~136 commits). It is written for maintainers who have not followed the work day to day.

## 1. Overview

This branch is a broad overhaul of FormosanBank's QC pipeline. It centralizes phonology generation around reviewed, per-source orthography profiles; redraws the ownership boundaries between the cleaning, standardization, and phonology stages; adds a substantial set of new validators, two non-blocking CI workflows, and a system that corrects apostrophes misused as quotation marks; and records the project's accumulated conventions in a single policy ledger (`POLICIES.md`). Three corpora were regenerated with the new pipeline as proof of the machinery; the remaining published corpora are deliberately left untouched until a planned, separately reviewed regeneration sweep.

## 2. Executive summary

### 2.1 Behavior changes to published-data processing

When the pipeline next runs over a corpus, its XML will change in the following ways (none of these have been applied to most published corpora yet — see "Deferred work" below):

- **Pipeline order simplifies** from `clean_xml → standardize → clean_xml → add_phonology` to `clean_xml → standardize → add_phonology`. `clean_xml` now cleans only the `original` tier (plus translations and metadata); `standardize.py` owns and fully regenerates every `standard` FORM.
- **Punctuation canonicalization on the original tier**: all dash/hyphen look-alikes (en/em dashes, minus signs, fullwidth forms) become ASCII `-`; tilde look-alikes (U+223C TILDE OPERATOR, U+301C WAVE DASH) become ASCII `~`; typographic apostrophes and quotes become straight `'` and `"` (unchanged rule, now backed by policy); double-encoded HTML entity residue (literal `&amp;lt;` chains) is decoded to a fixed point.
- **Null-morpheme markers** (`ø`, `Ø`) in morpheme position canonicalize to `∅` on every tier; letter-adjacent occurrences (Danish loanwords such as *Grønland*) are never touched. Null units are removed from sentence-level standard FORMs (except in `--copy` mode); null morphemes are silent in PHON, with a whole-null morpheme getting PHON `∅`.
- **PHON output changes**: unmapped punctuation is dropped from PHON (punctuation is not sound); segmentation markers never appear; phonemic variants are written `[x|y]` instead of the retired `x~y` notation; each language's standard PHON uses the orthography declared in the new `standards.csv` registry rather than a hardcoded Ortho113 assumption.
- **Hyphen stripping in the standard tier** (rule C012, now living in `standardize.py`) applies only to morpheme-segmented sentences and preserves digit-flanked hyphens (dates, verse ranges).
- **Apostrophe-as-quotation correction** (Amis only for now): `'` characters that the classifier confidently identifies as quotation marks are rewritten to `"` on the original tier, and stranded glottal apostrophes separated from their word by whitespace are rejoined. Every such rewrite is logged to a durable, committed `quote_corrections.csv`.

### 2.2 New validators

The branch adds one HARD rule, one downgrade, a family of SOFT rules, a WARN rule, two new standalone validators, and one bug fix to an existing rule. Full inventory with definitions in section 3.5. Highlights: V069 (HARD) enforces that a null morpheme in a word's FORM is represented as a null morpheme element; V120 (null in standard FORM) is downgraded from HARD to SOFT because `--copy` corpora legitimately retain nulls; V142–V147 cover informal ungrammaticality marking, translation language/script mismatches, morpheme-tier consistency, and PHON variant-notation hygiene; V150–V154 (in the new `validate_registries.py`) check cross-file registry consistency; V070 (WARN) flags gloss codes masquerading as word/morpheme forms; and `validate_port_readiness.py` (P001–P006) is a plain-script, AI-free gate run before porting a corpus.

### 2.3 New policies: POLICIES.md

`POLICIES.md` (repo root) is a new one-entry-per-ruling ledger that skills, audits, and code comments cite by ID instead of re-deciding recurring questions. It records roughly 30 entries across tier semantics, characters/typography, structure, and process. Entries dated 2026-08 are **newly RULED** during this work: POL-002 (standard tier is machine-owned), POL-010/018 (apostrophes/quotes; single quotes never serve as quotation marks), POL-011 (dash canonicalization), POL-012 (null morphemes), POL-013 (tilde codepoint and `[x|y]` variant notation), POL-016 (ungrammatical/marginal examples are excluded), POL-017 (`*(X)` obligatory vs `(*X)` forbidden), POL-022 (duplicates are SOFT/maintainer's-call; HARD only when the corpus's own pipeline declares a dedup step), POL-023 (M-tier presence), POL-024–027 (translations, optional material, alternatives), POL-033 (warnings sidecars are per-run reports), POL-034 (registry findings are SOFT), and POL-035 (pre-correction baselines for automated original-tier corrections). Long-standing conventions (original tier equals the actual source, corpus development in dev repos, audio statistics, etc.) are restated with their existing status. The file carries a DRAFT banner pending a final maintainer read-through; a sync mechanism to the public GitBook is designed inside the file.

### 2.4 New CI workflows — all non-blocking

Two GitHub Actions workflows are added, and **neither ever fails a build**:

- `conversion-tables.yaml` runs the conversion-table validator over `Orthographies/**` changes and posts a two-section summary (structural defects to fix vs phoneme-level mismatches to review). It never blocks, by explicit ruling: imperfect conversions are often legitimate, since older orthographies under-distinguish phonemes.
- `manual-edits-check.yaml` warns on pull requests that hand-edit published corpus XML without touching that corpus's `CodeAndDocs/` — the signature of an unrecorded hand edit. It is a heuristic and deliberately never fails.

### 2.5 Manual-edits reproducibility

The recorded-hand-edits mechanism is hardened. `apply_manual_edits.py` now **keeps** records that no-op at apply time (previously it pruned them, which was hazardous when the pipeline reruns over already-edited XML); a salient warning marks each kept no-op, and a new `--prune` flag restores removal as an explicit maintenance action. A repository hook reminds interactive sessions to capture any direct edit to published XML, and the CI check above surfaces uncaptured edits in pull requests. New tests prove that an applied hand edit survives the full pipeline.

### 2.6 The quote/glottal correction system

In most Formosan orthographies the apostrophe is a letter (the glottal stop), but sources also use `'` as a quotation mark. A new classifier (`QC/utilities/classify_quotes.py`) decides, per apostrophe, between glottal stop, quotation mark, and ambiguous, using the sentence's translations plus per-language attestation dictionaries; `clean_xml` applies its confident decisions. The system **activates per language only when that language has an attestation dictionary** at `QC/validation/reference/<Language>/attestation.txt`. Dictionaries now exist for every language with published data (16 of 17): Amis's was hand-validated; the other fifteen were generated from single-word sentence FORMs and are committed but not yet human-reviewed — meaning quote correction is armed for those languages at the next cleaning run, and the regeneration sweep's per-corpus diff review is the checkpoint. Siraya's dictionary is tiny (37 entries; weak attestation guard — review before its corpus is cleaned) and Pazeh has none (no published data; an empty dictionary would activate correction with no guard at all). Corrections (`'`→`"` rewrites and stranded-glottal repairs) go to a durable, committed `quote_corrections.csv`; ambiguity flags go to the ephemeral per-run `cleaner_warnings.csv` (and are suppressed by fiat for the translation-less Wikipedias corpus, documented in its README).

### 2.7 PHON variant notation

Phonemic alternatives in orthography profiles and generated PHON are now written `[x|y]` (pipe-separated alternatives in square brackets, e.g. `[b|v]`, `[ɬ|ɮ|l]`, `[l|ll]`) instead of the old bare-tilde `b~v`, which had no grouping scope and collided with the reduplication tilde. All profiles were migrated in one pass (98 cells across 26 files); the two Bunun context-resolution rule patterns carry the regex-escaped form `\[ʦ\|ʨ\](?=i)`. Published PHON still carries the legacy notation until regeneration; V147 tracks the remainder.

### 2.8 Compatibility notes

- **Token counts may shift when corpora are regenerated** (hyphen stripping, null-unit removal, marker cleanup). The token-comparison CI will flag the shifts; they should be announced as a counting discontinuity, as was done in 2026-06. The one full regeneration already on the branch (HundredPaiwanStories) had a token delta of exactly zero.
- **Some published corpora already trip the new SOFT/WARN rules.** Baseline runs are recorded in `claudeplans/2026-08-10-new-rule-baselines.md`: V142 flags 4 sentences (likely stray punctuation, not marginality); V144 flags four corpora with unsegmented words in segmented files (NTU 477, Wakelin 428, Li-Conjunction-Thao 140, Song 7); V070 flags 16 morpheme forms in NTU Seediq stories; the port-readiness gate finds two HARD items (Latham's non-Formosan ISO code, five dialect-less Wikipedias TEXTs); registry checks flag the known Seediq/Truku modeling wrinkle. None of these block CI; all are review worklists.
- `standardize.py`'s `--ortho113` flag is renamed `--remove_accents` (identical behavior); `clean_xml.py` loses `--hard-remove-segmentation` and `--ortho-path`, which move to `standardize.py`.

### 2.9 Deliberately deferred

- **The regeneration sweep.** Most published corpora are untouched on this branch; applying the new cleaning/standardization/phonology to them is a planned, per-corpus pass with diff review, scoped in `claudeplans/2026-08-10-policy-alignment-sweep-scope.md` (classify regenerable vs not, snapshot non-regenerable corpora per POL-035, capture outstanding hand edits per POL-030, run, review, commit). NTU's XML regeneration in particular is prepared but deferred to the sweep.
- **Linguistic review worklists**: the V144 segmentation-completeness questions, V070 impostor morphemes, the 16 phoneme-level conversion-table mismatches, and the Latham/Wikipedias port-gate items all need human linguistic judgment and are tracked, not resolved.
- Conversion-table validator case-awareness remains a known follow-up, as does human review of the fifteen newly generated (unreviewed) attestation dictionaries before their languages' corpora are cleaned.

## 3. Blow-by-blow, by subsystem

### 3.1 Phonology generation (`QC/utilities/add_phonology.py`) and source orthography profiles

This is the branch's namesake work. Previously, per-corpus dev repos each reimplemented source-orthography-to-IPA logic; now:

- **Reviewed source profiles are centralized** under `Orthographies/<Scheme>/<Language>.tsv`, in the same TSV shape as the official orthography tables (a `letter` column plus per-dialect IPA value columns). Thirteen newly committed profiles (StacyHuang/Yami, Pgagu/Seediq, TaiwanNandao Amis/Rukai/Puyuma/Paiwan/Seediq, Huang/Bunun, Zhang/Kavalan, Li/Rukai, Cauquelin/Puyuma, Tsuchida/Pazeh, Ochiai/Seediq) carry their review-evidence references and documented boundaries in `Orthographies/readme.md`.
- **Longest-grapheme, single-pass mapping.** The tokenizer matches the longest source grapheme first and maps each input grapheme exactly once — fixing a class of bugs where generated IPA was re-mapped by later rules (e.g. the old Paiwan `tj`→`c`→`ʦ` double-map). Unknown characters surface as `*` for review, never silently copied.
- **Ordered rules sidecars** (`<Language>.rules.tsv`) hold documented, deterministic context rules (regex over the mapped phonology), now with an optional `dialect` column scoping a rule to specific dialects or to a `default` fallback — Truku, for instance, takes its own Seediq phonotactic rules.
- **Per-language standard orthography registry.** The hardcoded "standard = Ortho113" assumption is replaced by `standards.csv` (repo root): each language declares its standard scheme, and a blank cell means "no standard designated yet" (standard PHON is then skipped with a distinct warning). All languages currently map to Ortho113, so behavior is unchanged until a maintainer decides otherwise. Spec: `docs/superpowers/specs/2026-08-09-per-language-standard-orthography-design.md`.
- **Tiers process independently**: a source profile can produce original PHON even when no standard table exists (Pazeh), and `--preserve-existing-original` retains expert-supplied source PHON (Tsuchida's Saisiyat).
- **Null morphemes are silent** in PHON; a whole-null FORM gets PHON `∅` (never an empty tier). **Unmapped punctuation is deleted** from PHON output.

### 3.2 Cleaning (`QC/cleaning/clean_xml.py`)

- **Tier ownership**: `clean_xml` no longer touches any `standard` FORM at any level (S/W/M). It cleans original FORMs, translations, and metadata. Spec: `docs/superpowers/specs/2026-08-09-standardize-owns-standard-cleaning-design.md`.
- **Dash canonicalization**: ten dash/hyphen look-alike codepoints (U+2010–U+2015, U+2212, U+FE58, U+FE63, U+FF0D) map to ASCII `-` in `swap_punctuation` (POL-011). Much corpus text is OCRed, so hyphen-vs-dash choices in sources are not principled.
- **Null-glyph canonicalization**: `ø`/`Ø` in morpheme position → `∅` on all tiers; letter-adjacent occurrences preserved (POL-012).
- **C028** (new rule): decodes double-encoded HTML entity residue (literal `&amp;lt;`-style chains, including numeric character references) to a fixed point, with one warning row per occurrence. This mechanizes the fix for the 1,109-value incident found in NTU.
- **C029** (new rule): tilde look-alikes U+223C and U+301C → ASCII `~` (POL-013 codepoint half). Chinese translations are unaffected.
- **Quote/glottal correction** (rules c030/c031/c032): see 3.4.
- The old C012 (standard-tier hyphen handling) is removed from `clean_xml` entirely; it now lives in `standardize.py`.

### 3.3 Standardization (`QC/utilities/standardize.py`)

- **Owns the standard tier**: `standardize.py` regenerates every standard FORM from the original on every run, and now performs all standard-tier cleaning itself (POL-002). Consequence, recorded as policy: never hand-edit a standard FORM or PHON — edit the original and regenerate.
- **C012 moved in**: hyphen/clitic-marker stripping applies to sentence-level standard FORMs only, gated on the sentence actually being morpheme-segmented, and digit-flanked hyphens survive. Bunun/Thao (where `-` is a letter) keep hyphens with a warning unless `--hard-remove-segmentation`.
- **Null units removed** from sentence-level standard FORMs in conversion and accent-stripping modes; `--copy` remains a pure duplication (its retained nulls are flagged SOFT by V120 as "re-standardize when a table exists").
- **Case-aware standardization**: conversion-table rules automatically derive Title-case and ALL-CAPS variants of lowercase rules (`o→u` also converts sentence-initial `O`), suppressed when the capital is a phonemic letter in the source profile (Li Rukai's `T` /ʈ/ vs `t`) or when an explicit row exists. The source profile is resolved from the table filename (`<Language>_<Scheme>_113.tsv`); redundant uppercase rows were removed from the tables. New module `QC/utilities/_case_variants.py`. Spec: `docs/superpowers/specs/2026-08-09-standardize-capitalization-design.md`.
- **`--ortho113` renamed `--remove_accents`** (same behavior).
- **Warnings sidecar**: standardize writes its c012/c022 warnings to `standardize_warnings.csv`, which — like `cleaner_warnings.csv` — is a per-run report rewritten on every run (POL-033; this fixes an append-mode bug that duplicated rows on reruns).
- The orthography detector (`orthography_detector.py`, `_accents.py`) now keeps accents that are attested letters in the orthographies being scored, instead of stripping them unconditionally.

### 3.4 Quote/glottal correction (`classify_quotes.py`, `build_attestation_dict.py`)

Design: `docs/superpowers/specs/2026-08-10-quote-glottal-correction-design.md` (including a merge-reconciliation addendum that renumbered the rules and split the logs).

- **Classifier** (`QC/utilities/classify_quotes.py`, ~640 lines, 20+ tests): a translation-based first pass resolves sentences whose translations confirm all apostrophes are glottal; otherwise four high-confidence pairing rules classify each `'` as QUOTATION, glottal, or AMBIGUOUS, using dictionary attestation to protect real glottal-final words. A guarded translation-quote-count rule handles sentences whose quoted span boundaries end in genuine glottals. Validated on Amis at 98%+ resolution of quote-bearing sentences with zero observed false positives.
- **Attestation dictionaries**: `QC/utilities/build_attestation_dict.py` generates `QC/validation/reference/<Language>/attestation.txt` from single-word sentence FORMs across all published corpora of that language (interior running-text tokens are excluded by default because unresolved quote marks polluted them). The committed Amis dictionary has 7,167 entries. **The missing-dictionary gate is the rollout switch**: languages without a dictionary are skipped entirely; enabling a new language means generating and reviewing its dictionary. The `port-corpus-in` skill regenerates the dictionary when a new corpus adds data for a covered language.
- **Cleaner integration**: in `clean_xml`, confident QUOTATION apostrophes are rewritten to `"` (c031) and stranded glottals rejoined to their word (c032, e.g. `o ' ayam` → `o 'ayam`); both are appended to a dedicated, durable, committed `quote_corrections.csv` (POL-035 recoverability record). Ambiguous cases (c030) go to the ephemeral `cleaner_warnings.csv`, suppressed for the Wikipedias corpus by documented fiat.
- **Recoverability policy (POL-035)**: because a wrong rewrite is not self-correcting, non-regenerable corpora get a pristine pre-correction snapshot in `CodeAndDocs/` before corrections first run; regenerable corpora need nothing extra. No published corpus has been corrected yet.
- **Review artifacts** at repo root: `quote_review_nonwiki_amis.md`/`.csv` (239 flagged non-Wikipedia Amis sentences for human review), `amis_attestation_union.txt` and `amis_wordlist_ilrdf_epark_safolu.txt` (dictionary-construction inputs).

### 3.5 Validators

New and changed rules, with definitions:

| Rule | Severity | What it flags | Where |
|---|---|---|---|
| V069 | HARD (new) | A null morpheme `∅` in a word-level FORM without a null morpheme child element | `validate_glosses.py` (`rules/gloss.py`) |
| V070 | WARN (new) | A word/morpheme FORM that is a bare gloss code (e.g. `RED`) — annotation debris masquerading as a wordform | `validate_glosses.py` |
| V120 | HARD→**SOFT** | `∅` in a sentence-level standard FORM — now a "re-standardize when convenient" heads-up, since `--copy` corpora legitimately retain nulls | `validate_text.py` (`rules/text.py`) |
| V129 | HARD (reworded) | `*` in any FORM — now reads as "this sentence should have been excluded" per POL-016 | `validate_text.py` |
| V132 | (extended) | Double-encoded entity residue — now also catches numeric character references | `validate_text.py` |
| V142 | SOFT (new) | Ungrammaticality/marginality visible only informally: a leading `? ` in a FORM, or ungrammaticality asserted only in free-text `source`/`notes` (POL-016) | `validate_text.py` |
| V143 | SOFT (new) | Translation language/script mismatch, rate-based per file — catches wholesale English/Chinese swaps like the ~16,300-value NTU Bunun incident | `validate_text.py` |
| V144 | SOFT (new) | A word with no morpheme child in a morpheme-segmented file (POL-023) | `validate_xml.py` |
| V145 | SOFT (new) | A morpheme tier present but nothing multi-morphemic — an all-single-M tier adds no information (POL-023) | `validate_xml.py` |
| V146 | SOFT (new) | Malformed `[x\|y]` variant group in PHON (unbalanced brackets, nesting, empty alternatives) | `validate_text.py` |
| V147 | SOFT (new) | Legacy `x~y` variant notation in PHON — regenerate with migrated profiles | `validate_text.py` |
| V150–V153 | SOFT (new) | Registry consistency: every language has a `standards.csv` row; declared scheme folders exist; conversion-table columns and rules-sidecar dialects are canonical per `dialects.csv` (POL-034) | `validate_registries.py` (new) |
| V154 | SOFT (new) | Legacy `x~y` variant notation in an orthography profile cell | `validate_registries.py` |
| G004 | HARD (fixed) | Infix root reconstruction — now handles stacked infixes and accepts both root spellings permitted by POL-014 | `audit_gloss_scrape` rules |
| P001–P006 | HARD/WARN (new) | Pre-port gate: tracked `Private/` content (P001 HARD); unknown ISO code (P002 HARD); non-canonical dialect (P003 HARD); disagreeing/unreachable commit-hash pins (P004 WARN); stale audio counts (P005 WARN); conversion table needing validation (P006 WARN) | `validate_port_readiness.py` (new) |

New standalone validators:

- **`QC/validation/validate_registries.py`** — repo-level, no corpus argument; SOFT findings only (POL-034), exit 1 only when a registry file itself is unreadable.
- **`QC/validation/validate_port_readiness.py`** — a plain script requiring no AI assistance, run on a dev repo before porting and again on the ported copy; mechanizes the port-blocking problems the 2026-08 audit season kept finding by hand.
- **`QC/validation/validate_conversion_table.py`** (+ tests) — audits an orthography conversion table transitively through IPA: applying the table to the source orthography should reproduce the target orthography's phonology. Verdict tiers separate confirmed equivalences, warnings needing human confirmation (length-vs-doubling, digraph-vs-affricate), unresolved mismatches, information loss (merges, unencodable distinctions), coverage gaps, and table-integrity defects (unknown source graphemes, untokenizable targets). Its first full run over 41 tables (`claudeplans/conversion-table-audit-findings.md`) found 5 crash-class dialect-naming defects (since fixed), profile gaps, and 16 phoneme-level items now on the review worklist.
- **`QC/validation/run_conversion_table_checks.py`** — the CI driver: enumerates all conversion tables, resolves profiles from filenames, and emits the two-section (structural vs phoneme-level) summary. Always exits 0.

### 3.6 Registries and orthography data (`Orthographies/`, `standards.csv`, `dialects.csv`)

- `standards.csv` (new): per-language standard orthography declaration (see 3.1).
- `dialects.csv`: alternate names recorded for Rukai dialects (Budai, Tona, Maga, Mantauran) and Bunun Junqun (Isbukun).
- Conversion tables repaired per the audit: Rukai/Seediq dialect-name mismatches fixed (split space-merged `Dawu Dona` columns, canonical Seediq dialect names), redundant uppercase rows removed (now auto-derived), phonotactics recoded from table rows into rules sidecars (Thao, Yami, Seediq, Bunun glides/palatalization), the stray `Saisiyat_folk_113 2.tsv` renamed to canonical form, and new tables added (Puyuma_Cauquelin_113 with construction notes, Rukai_Li_113, Saisiyat_Tsuchida_113, Seediq_Ochiai_113, Pazeh_Tsuchida_113, Bunun_Huang_113).
- All profile variant cells migrated from `x~y` to `[x|y]` (98 cells, 26 files); Bunun rules regex-escaped.
- `Orthographies/readme.md` now documents the profile format, the rules-sidecar schema with dialect scoping, and the reviewed-profile inventory. A Cauquelin-vs-Ortho113 Puyuma orthography-difference writeup is added under `Orthographies/Cauquelin/`.

### 3.7 Manual-edits reproducibility (POL-030)

- `QC/cleaning/apply_manual_edits.py`: no-op records are **kept** with a salient `NO-OP manual edit (KEPT)` warning; `--prune` removes them explicitly. Rationale: the pipeline's step 0 runs over already-edited published XML, where every record no-ops by design — silently pruning would destroy the reproducibility record.
- `.claude/hooks/remind-manual-edits-capture.py` (+ tests, registered in `.claude/settings.json`): after any interactive edit to `Corpora/**/XML/**/*.xml`, the session is reminded that the edit must be captured into `CodeAndDocs/manual_edits.xml`.
- `.github/workflows/manual-edits-check.yaml`: warns (never fails) on PRs whose corpus changes are XML-only.
- New tests: capture→apply round-trip behavior, and a survival test proving an applied hand edit is not undone by `clean_xml`/`standardize`.

### 3.8 Corpus data and per-corpus pipelines (`Corpora/`)

- **HundredPaiwanStories** — fully regenerated with the new pipeline. An element-by-element diff against `main` (`claudeplans/2026-08-11-hps-regen-diff-report.md`) classifies 100% of differences into expected categories: punctuation dropped from PHON, the `tj` double-map fix, spurious glottal stops removed, PHON newly generated for four unknown-dialect texts, C012 hyphen stripping in standard FORMs, and improved `'`-vs-`?` classification in the rewritten `fix_ferrell.py` (position-hardened rules; source `(?)` uncertainty markers now treated as punctuation). Token delta: zero. Exactly one original-tier hand edit (a stray quote in sentence 008S28), recorded in the README. The bespoke `fill_phon_tier.py`/`fill_standard_tier.py` scripts are deleted in favor of the shared tools.
- **Presidential_Apologies** — regenerated. PHON now uses each file's declared dialect column (letters the dialect's orthography cannot transcribe surface as `*`, an explicit maintainer decision recorded in the README); a new `remove_standard_cjk_annotations.py` step removes parenthesized Mandarin annotations from the standard tier reproducibly; the README's reproduction instructions are rewritten for the new pipeline.
- **NTUFormosanCorpus** — reproduction pipeline modernized (`make.sh`, `run_parsers.py`, serialization normalization, parsers fixed to distinguish `*(X)` obligatory from `(*X)` forbidden material per POL-017, dialect pinning, morpheme-ID normalization, audio hand edits recorded); a rerun-and-diff audit (`claudeplans/2026-08-10-ntu-rerun-diff-audit.md`) verified no unrecorded hand edits. **The regenerated XML itself is deliberately not committed here** — it lands in the regeneration sweep.
- **Wikipedias** — README documents the ambiguous-apostrophe-is-glottal fiat. **Li-Conjunction-Thao** — README updated with published framing and regeneration status. No other corpus XML changes.

### 3.9 CI workflows

Covered in 2.4; both new workflows (`conversion-tables.yaml`, `manual-edits-check.yaml`) are informational only and never block a merge.

### 3.10 Tests

The suite grows to **947 passing tests**. New coverage includes:

- `tests/integration/`: an end-to-end pipeline run over a synthetic corpus asserting the cross-stage invariants the refactor depends on, plus an idempotence guard — `clean_xml` is verified truly idempotent over all fixtures (its steady-state input is its own output; every future cleaning rule runs into this test). `standardize` and `add_phonology` were established as deterministic regenerators by design review (they rebuild derived tiers from the original tier on every run, so even a non-idempotent conversion rule like Cauquelin Puyuma's `l→ll` cannot double-apply); by maintainer ruling they carry no rerun tests, and the `l→ll` fixture exercises conversion-from-original in the end-to-end test.
- The warnings-sidecar fix (per-run rewrite, not append) with a contract test for `standardize_warnings.csv`'s schema.
- Manual-edits round-trip and pipeline-survival tests.
- Full unit coverage for the classifier, attestation-dictionary generator, conversion-table validator, registry validator, port-readiness gate, case-variant derivation, and all new cleaner/validator rules.
- A new convention (`tests/fixtures/audit_regressions/README.md`): every audit finding that led to a code fix gets a named regression fixture, wired into the audit skills as a closing step.

### 3.11 Skills, hooks, and internal documentation

- Skills under `.claude/skills/` are synchronized with the new pipeline: `run-qc-pipeline` (rewritten phases, `standards.csv` pre-flight, conversion-table validation in TSV mode, warnings-CSV collection, dialect/duplicate/audio validators, a summary template), `audit-dev-repo` (starred-parens sweep, null-glyph checks, an expected-normalizations whitelist citing POLICIES.md, the audit-to-fixture step), `audit-gloss-scrape` (hard-won tool limits encoded), `port-corpus-in` (port-readiness gate, cross-corpus duplicate check, attestation-dictionary regeneration), `setup-new-dev-repo` (forward-looking notes). The dev-repo audit briefing is refreshed to the new pipeline order.
- Design specs live in `docs/superpowers/specs/` (seven new documents dated 2026-08-09/10 covering each subsystem above) with matching implementation plans in `docs/superpowers/plans/`.
- Reports in `claudeplans/`: the QC improvement proposals with the maintainer's disposition table, the new-rule baselines, the conversion-table audit findings, the NTU rerun audit, the HundredPaiwanStories regeneration diff, and the policy-alignment sweep scope that defines the follow-up work.
- `QC/README.md` documents the new `add_phonology` workflow and the quote-correction behavior; `CLAUDE.md` is updated for the no-op-keeping manual-edits behavior.
