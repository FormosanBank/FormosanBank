# FormosanBank Policies

One entry per project-wide ruling. When an audit, skill, script, or review
touches one of these questions, **cite the entry (e.g. POL-012) instead of
re-deciding it**. Open questions carry status UNRESOLVED — ask the maintainer
once, record the answer here, and the question is closed everywhere.

**DRAFT — every ruling below is a restatement of decisions found in code,
specs, the GitBook, or audit sign-offs. Rulings the maintainer has not
actually made are marked UNRESOLVED with a recommendation. Please review.**

## Where this file lives and how it syncs

This file (`FormosanBank/POLICIES.md`) is **canonical** — it versions together
with the code that implements the rulings, and entries cite rule IDs and
scripts by name. A rendered copy is published in the GitBook at
`en-us/the-bank-architecture/policies.md` with a header marking it as synced;
the GitBook repo's test suite gains a drift check (byte-comparison against a
FormosanBank checkout, alongside the existing `update_corpus_stats.py`
tooling) so the copy cannot silently diverge. The GitBook's
[FormosanBank XML Format](../FormosanBankGitbook/en-us/the-bank-architecture/formosanbank-xml-format.md)
page remains the narrative description of the format; where it states a
convention, the matching POL entry cites it rather than duplicating prose.

Entry format: **ID · Status · Date · Applies to** — ruling, rationale,
implemented-by.

---

## 1. Tier semantics

### POL-001 · RULED · long-standing · original FORM tier
The `original` tier represents the **actual original source** (the printed
book, the web page), not the raw scrape or OCR pass. Correcting OCR/scraping
errors to match what the source prints makes the tier *more* faithful and is
expected; punctuation may be normalized (POL-010/011). The source's
**spelling** — its orthographic letter choices — must be preserved.
Implemented by: convention; enforced through audits (`audit-dev-repo`,
`audit-gloss-scrape`).

### POL-002 · RULED · 2026-08-09 · standard FORM tier
The `standard` tier is **derived and machine-owned**: `standardize.py`
regenerates it from the original tier on every run (`create_standard`
replaces existing content before applying any conversion). Consequences:
never hand-edit a standard FORM — the edit is clobbered on the next run.
The manual-edits tooling encodes this: `capture_manual_edits.py` records
each edited `<S>` whole but first *deletes* every `FORM[@kindOf="standard"]`
and every `PHON` from the record (at S, W, and M level) before storing or
comparing, because those tiers are regenerated downstream and recording
them would only capture churn; `apply_manual_edits.py` likewise replaces an
edited sentence with the stripped record and lets standardize/add_phonology
rebuild the derived tiers. Net effect: an edit made *only* to a standard
FORM or PHON is invisible to capture and futile anyway — edit the original
and let regeneration propagate. All standard-tier cleaning lives in
`standardize.py`, none in `clean_xml.py`.
Spec: `docs/superpowers/specs/2026-08-09-standardize-owns-standard-cleaning-design.md`.

### POL-003 · RULED · 2026-08-09 · PHON tier
PHON is derived and machine-owned (`add_phonology.py` regenerates it;
hand edits are stripped from manual-edit records). It is **marker-free**:
segmentation markers (`-`, `=`, infix brackets) are not represented; infix
*content* is, since it is pronounced. Unmapped punctuation is dropped;
unmapped letters surface as `*`. Standard PHON uses the language's designated
standard orthography per `standards.csv` (blank entry = standard PHON
deliberately skipped). Sources: GitBook XML-format page §PHON;
`docs/superpowers/specs/2026-08-09-per-language-standard-orthography-design.md`.

### POL-004 · RULED · long-standing · cross-corpus comparison
Cross-corpus/orthographic statistics use `kindOf="standard"`; token counting
uses the standard sentence-level FORM with original fallback
(`QC/corpus_counts.py` is the single source of truth for counting rules).

---

## 2. Characters and typography

### POL-010 · RULED (recorded 2026-08-10) · all Formosan-text tiers
**Typographic apostrophes and quotes canonicalize to ASCII** `'` and `"`:
U+2018/U+2019 curly singles, U+02BC modifier apostrophe, U+02BB, backtick,
and U+02C8 stress mark all → `'`; curly doubles → `"`. Rationale: the glottal
stop's canonical *spelling* in Formosan orthographies is the straight
apostrophe; curly variants in print are typography, not orthography, so this
does not violate POL-001. Chinese TRANSL text follows Chinese conventions
instead (fullwidth quotes retained/canonicalized; title marks 《》
untouched). Implemented by: `clean_xml.py` `swap_punctuation` (C001/C002).
*Audit note: U+2019→U+0027 in a dev repo's build script is conforming
behavior — cite this entry instead of flagging it.* Companion ruling:
single quotes never serve as quotation marks (POL-018).

### POL-011 · RULED · 2026-08 · all tiers
**All dash/hyphen look-alikes canonicalize to ASCII `-`** (U+2010…U+2015,
U+2212, U+FE58, U+FE63, U+FF0D). Much corpus text is OCRed, so a source's
hyphen-vs-dash choice cannot be trusted as principled. Downstream, C012 in
`standardize.py` strips `-` from S-level standard FORMs only in
morpheme-segmented sentences, preserving digit-flanked `-` (dates, verse
ranges). Implemented by: `swap_punctuation`; C012.

### POL-012 · RULED · 2026-08-09 · null morphemes, all tiers
The canonical null-morpheme marker is **`∅` U+2205**. In morpheme position
(neighbors are edge/whitespace/`-`), `ø` U+00F8 and `Ø` U+00D8 normalize to
`∅` on every tier including original — the null marker is analytic notation,
not source spelling, so POL-001 is not violated; letter-adjacent `ø`
(Danish loanwords) is never touched. Null units (`∅` plus one bridging
hyphen) are removed from S-level **standard** FORMs in TSV/remove-accents
modes; `--copy` keeps them (V120 SOFT = "re-standardize when convenient").
A null in a W FORM requires a null M child (V069 HARD). Null morphemes are
silent in PHON; a whole-null FORM gets PHON `∅`. A dev repo may keep the
source's glyph (`ø`/`Ø`) while work is in progress — two 2026-08 audits
chose to — but that choice does not survive publication: `clean_xml`
canonicalizes the glyph the first time the corpus runs through the
pipeline, so there is no per-corpus opt-out of `∅` in published data. Spec:
`docs/superpowers/specs/2026-08-09-null-morpheme-handling-design.md`.

### POL-013 · RULED · 2026-08-10 · the tilde
1. **Semantics — RULED (2026-08-10).** Phonemic variants on the PHON tier
   (and in orthography-profile IPA cells, which flow verbatim into PHON)
   are written **`[x|y]`** — two or more pipe-separated alternatives in
   square brackets (`[b|v]`, `[ɬ|ɮ|l]`, multi-char fine: `[l|ll]`). The
   bare-tilde notation (`b~v`) is retired: it had no grouping scope and
   collided with the Leipzig reduplication marker. `~` is thereby freed
   for reduplication (FORM tiers) only. Profiles migrated 2026-08-10 (98
   cells, 26 files; the two `Bunun.rules.tsv` context-resolution patterns
   carry the regex-escaped form `\[ʦ\|ʨ\](?=i)`). Guards: V154 (legacy
   notation in a profile), V146 (malformed group in PHON), V147 (legacy
   `~` in PHON — regenerate). Published PHON migrates at the regeneration
   sweep. Spec:
   `docs/superpowers/specs/2026-08-10-phon-variant-notation-design.md`.
2. **Codepoint — RULED (2026-08-10).** Tilde look-alikes canonicalize to
   ASCII `~` U+007E: U+223C TILDE OPERATOR (what LaTeX-typeset PDFs emit
   for the reduplication tilde — e.g. Bril 2024's `RED∼stem`) and U+301C
   WAVE DASH. Implemented in `clean_xml`'s `swap_punctuation` (C029),
   pure typography per the POL-010 rationale. Chinese TRANSL is
   unaffected (that branch never calls `swap_punctuation`).

### POL-014 · RULED · GitBook · infixes on W/M tiers
W-tier FORMs mark an infix with ASCII angle brackets (`k<um>a'en`); S-level
original FORMs may keep the source's typography (e.g. guillemets `k‹um›a'en`).
At M level the infixed root is **one** morpheme FORM, written with `-` at
the infixation point, and the infix is `-b-`. Worked example: `t<um>a-taŋi`
(root `ta`, infix `um`, plus morpheme `taŋi`) → three M FORMs `t-a`, `-um-`,
`taŋi` — this is the conformant shape (Kanakanavu's practice conforms).
What deviates, and gets flagged at audit time: writing the root *rejoined*
with no hyphen (`ta`), or splitting it into two separate M elements (`t-`
and `a-`). Circumfixes are analogous, unless the source glosses them as
prefix + suffix. Source: GitBook XML-format page §Special Rules.

### POL-015 · RULED · GitBook · clitics
M-level clitic FORMs retain the `=` marker whether or not the source wrote
the clitic attached. Source: GitBook XML-format page §Special Rules.

### POL-016 · RULED · 2026-08-10 · ungrammatical/marginal examples
**Exclude them.** Elicited examples the source marks ungrammatical (`*`) or
questionable/marginal (`?`) are not ingested into FormosanBank corpora —
neither with the marker inline nor with the marker stripped. `*` and `?`
examples are treated the same way. If a collection of ungrammatical
examples is ever wanted, it will be a different, purpose-built corpus.
Enforcement: V129 HARD (`*` in any FORM) and V142 SOFT (leading `? ` in
FORM, or ungrammaticality/marginality asserted only in `@source`/`@notes`
free text) both now read as "this sentence should have been excluded — or
the marker is stray punctuation to clean; review and remove one or the
other." Applies at intake (dev-repo build scripts); existing published
hits are the V142/V129 review worklist. Raised by:
Lin-Interrogative-Verbs, Puyuma-Teng, Sakizaya audits; NTU `*(malra)`
incident.

### POL-017 · RULED · 2026-08-10 · obligatory/forbidden parentheses
In source notation, `*(X)` means X is **obligatory** (keep X, unstarred) and
`(*X)` means X is **forbidden** (drop X). Parsers must distinguish the two;
treating them identically published an ungrammatical sentence (NTU Rukai
`*(malra)`, parser fixed 149537a10). Audits sweep for both patterns.

### POL-018 · RULED · 2026-08-10 · quotation marks
**Single quotes are never used as quotation marks** in Formosan text — on
any tier, in any language. The straight apostrophe/single quote is
confusable with the glottal-stop letter, and this holds even for languages
whose orthography lacks a glottal stop, because loanwords carrying the
letter are rampant. Quotations use double quotes (`"`). Consequences: a
`'…'` pair functioning as quotation marks is an intake bug to fix (rewrap
in `"` or drop), never something to preserve as source typography; cleaners
and validators treat `'` as a letter, not as paired punctuation
(`clean_xml`'s c002 warning on single-quote variants in Chinese TRANSL
exists for exactly this reason). Cross-ref POL-010.

---

## 3. Structure

### POL-020 · RULED · 2026-06-01 · sibling order
Sibling order of FORM/PHON/TRANSL/AUDIO/W within S (and within W) is **not
schema-enforced**; W/M-at-end is a soft documentation convention. Rationale:
AUDIO must be positionable anywhere; XSD 1.0 cannot express the mixed
constraint without UPA violations.

### POL-021 · RULED · GitBook · untranscribable content
`<UNCLEAR/>` marks content actively reviewed but unrecoverable (distinct
from a missing FORM = never transcribed). Not counted as a token.
`standardize.py` preserves it when duplicating original → standard.

### POL-022 · RULED · 2026-08-10 · duplicate sentences
**Narratives may repeat; reference resources may not.** In narrative and
spontaneous-speech corpora, exact duplicate sentences are *fine* — natural
repetition is part of the text. In dictionaries, wordlists, and grammar
example collections, repeats should be excluded — a reference resource
gains nothing from the same entry twice. Nuance from the Latham 2026-08
call: a wordlist repeat with *distinct provenance* (attested from a
different source variety or page) is informative attestation, not a
repeat, and may be kept deliberately. Implementation follow-up:
`validate_duplicate_sentences` currently applies one severity everywhere;
it should scope by corpus type (duplicates in reference corpora
actionable, in narratives not findings at all).

### POL-023 · RULED · 2026-08-10 · M-tier presence
In an XML file where any W has two or more M children (i.e. the file is
morpheme-segmented), **every W gets at least one M**; a W with exactly one M
there is read as "analyzed as monomorphemic". In corpora with **no**
morpheme segmentation, there is **no M level at all** — an all-single-M
tier adds no information. Enforced as SOFT findings V144 (M-less W in a
segmented file) and V145 (M level present but nothing multi-M) in
`validate_xml.py`; SOFT because some existing corpora trip these and will
need fixing over time. (Resolves the Bunun-Topic-Focus degenerate-single-M
question: its 51 single-M Ws are conforming as long as no W lacks an M.)

### POL-024 · RULED · 2026-08-10 · parentheticals in translations
Two different things, treated differently:
- **Literal translations / analytic paraphrases** (`(Lit. the money that
  Utay took is how much?)`) belong in a `ver="alt"` TRANSL or a `notes`
  attribute, not inline in the primary TRANSL text.
- **Naturalistic elaboration** (`Sally went to Porto (a town in
  Portugal).`) MAY stay inline: a human translator might really produce
  that parenthetical, and one may *want* MT to learn to produce it.
  Moving it to `notes` is permitted but optional — a judgment call, not a
  cleanup target. Auditors should not flag inline naturalistic
  parentheticals as defects.

### POL-025 · RULED · 2026-08-10 · alternative translations
When a source gives more than one translation of a sentence into the same
language, they all live **in the same `<S>` block** as multiple TRANSL
elements, with all but one carrying `ver="alt"`. (The XSD already requires
a `ver` when a parent has two same-language TRANSLs.) Do not drop the
extra readings (Puyuma-Teng audit found 7 lost) and do not create
duplicate S blocks for them.

### POL-026 · RULED · 2026-08-10 · optional material in examples
A source sentence with optional words — `x y (z)` — becomes **two S
blocks**: `x y` and `x y z`. Care at conversion time: the gloss tier of
the `x y` block must not contain z's gloss (and its W/M tier must not
contain z), and each block's translation must match its own variant.

### POL-027 · RULED · 2026-08-10 · alternatives in examples
A source sentence offering alternatives — `Sally likes x / y / z` —
becomes **one S block per option**, never a single block with the slashes
retained. Same care as POL-026: each block's glosses, W/M tier, and
translation reflect only its own option. (V121/V122 flag leftover
parens/slashes; unresolved slash alternatives in published FORMs are the
symptom of skipping this rule.)

---

## 4. Process

### POL-030 · RULED · 2026-06-15 · reproducible hand edits
Every hand edit to published XML must be reproducible: recorded in
`CodeAndDocs/manual_edits.xml` (via `capture_manual_edits.py`, re-applied
first in the pipeline by `apply_manual_edits.py`) or by a committed script.
Direct XML edits without a record are not acceptable — they are lost on
regeneration. Standard-FORM/PHON tiers are never hand-edited (POL-002/003).
Records that no-op at apply time are **kept** with a salient warning;
`apply_manual_edits.py --prune` removes them — an explicit maintenance
action for when the upstream build has genuinely absorbed the fix
(ruling 2026-08-10).

### POL-031 · RULED · long-standing · corpus development
New corpora are developed in per-corpus dev repos and ported into
`Corpora/` only after QC. See CLAUDE.md §Development workflow.

### POL-032 · RULED · 2026-06 · audio statistics
`statistics/audio_durations.csv` is the source of truth for audio seconds;
CI only reads it. Refresh on demand via `refresh_audio_stats.py` /
`update_audio_stats.py`.

### POL-033 · RULED · 2026-08-10 · warnings sidecars
`cleaner_warnings.csv` / `standardize_warnings.csv` are **per-run reports**,
not stable artifacts: they are rewritten by each run, never committed, and
never treated as cumulative logs. (Requires the append-mode fix in
`CleanerWarnings.write_csv`; see 2026-08-10 QC test plan, Task 1.)

### POL-034 · RULED · 2026-08 · registry consistency findings
Cross-file registry checks (`standards.csv`, `dialects.csv`, orthography
profiles, conversion-table headers) report **SOFT** findings, not HARD
failures — registries may be legitimately out of sync mid-migration. Only
structural unreadability (file missing/unparseable) is HARD.

### POL-035 · RULED · 2026-08-10 · pre-correction baselines
When automated corrections first touch a corpus's published XML, what
guarantees we can still see (and reproduce) the uncorrected state depends
on the corpus type:
- **Regenerable corpora** (a reproduction pipeline exists in
  `CodeAndDocs/` — e.g. Glosbe): nothing extra. Each pipeline run
  self-corrects from source; the pipeline *is* the baseline.
- **Non-regenerable corpora**: before corrections are **first** applied,
  snapshot the pristine pre-correction XML into that corpus's
  `CodeAndDocs/` as the reproduction baseline, and document the snapshot
  in the corpus README.
No real corpus data has been corrected yet, so this is a per-corpus step
at the time the pipeline actually runs (i.e. during the regeneration
sweep). Backstops either way: git history, and a committed correction
log. Source ruling: `feature/quote-glottal-classifier`'s
quote-glottal-correction spec (its `'`→`"` rewrite is the first
non-self-correcting mutation of the original tier). Companion to
POL-030, which covers *hand* edits; this covers *automated* corrections.
**Reconciled at merge (2026-08-10):** original-tier rewrites are logged
as `c031` (corrected `'`→`"`) and `c032` (stranded-repair) rows in a
dedicated, durable **`quote_corrections.csv`** (append-only across runs;
commit it after correcting runs) — distinct from `cleaner_warnings.csv`,
which stays an ephemeral per-run report per POL-033 and carries only the
`c030` ambiguity flags.
