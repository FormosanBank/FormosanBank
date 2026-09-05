# FormosanBank Policies

One entry per project-wide ruling. When an audit, skill, script, or review
touches one of these questions, **cite the entry (e.g. POL-012) instead of
re-deciding it**. Open questions carry status UNRESOLVED — ask the maintainer
once, record the answer here, and the question is closed everywhere.

Most entries restate a decision already made in code, in a spec, in the
GitBook, or in an audit sign-off; the later ones record a maintainer ruling
directly, and each says which. **Anything the maintainer has not actually
ruled on is marked UNRESOLVED with a recommendation — those entries are
proposals awaiting review, not rules.**

## Highlights

If you read nothing else, read these ten. They have the broadest reach, and
almost every review question that gets re-litigated is settled by one of them.

**The data**

| Policy | The rule |
| --- | --- |
| **POL-001** | The `original` tier is the **actual source text**, not a raw scrape. Fixing an OCR misread or a dropped period makes it *more* faithful; changing the source's spelling is the error to catch. |
| **POL-002** | The `standard` tier is the same content in FormosanBank's one common orthography. It is derived, never hand-edited. |
| **POL-037** | Published identifiers are **stable**. `TEXT/@id` is never reused; S/W/M ids are never renumbered once published. External users cite them. |
| **POL-038** | XML and raw scrape files change **only via committed code** — a pipeline script, `manual_edits.xml`, or a one-off script in `CodeAndDocs/`. Never a hand edit, not even during an audit. |

**Rights**

| Policy | The rule |
| --- | --- |
| **POL-042** | Every `TEXT/@copyright` is exactly one value from `rights_vocabulary.csv`. No exceptions, no free text. |
| **POL-043** | An existing rights claim is **never weakened because a reviewer could not find its evidence.** The evidence lives with the maintainer, not in this repository. Escalate; do not downgrade. |

**Building and reviewing**

| Policy | The rule |
| --- | --- |
| **POL-031** | New corpora are built in per-corpus dev repos and ported into `Corpora/` only after QC. |
| **POL-046** | **Shared tools first.** Extend a shared tool before writing a corpus-specific one. Corpus-specific processing code is a last resort and a fork risk. |
| **POL-047** | One entry point, one step order: `generate_xml.sh` runs generate → manual edits → clean → standardize → add_phonology. Deviation is allowed but must be justified at merge. |
| **POL-048** | A published corpus rebuilds from a **FormosanBank checkout alone.** Dev repos are permanently private and are never a build input. |

**How the file is organised**

| Section | Governs |
| --- | --- |
| 1. Tier semantics | what each tier means |
| 2. Characters and typography | which characters may appear, and how |
| 3. Structure | how S/W/M and their children are arranged |
| 4. Process | what may be done to the data |
| 5. Rights | licensing and permission |
| 6. Development | the code that does all of the above, and how changes to it are reviewed |

Entries carry status **RULED** (decided) or **UNRESOLVED** (open, with a
recommendation). Cite the ID rather than re-deciding the question.

---

## Where this file lives and how it syncs

This file (`FormosanBank/POLICIES.md`) is **canonical** — it versions together
with the code that implements the rulings, and entries cite rule IDs and
scripts by name. A rendered copy is published in the GitBook at
`en-us/the-bank-architecture/policies.md` with a header marking it as synced;
the GitBook repo regenerates it with `python sync_upstream_docs.py`, and its
`tests/test_upstream_doc_sync.py` drift check (a byte-comparison against a
FormosanBank checkout) fails when the copy diverges. The GitBook's
[FormosanBank XML Format](https://ai4commsci.gitbook.io/formosanbank/the-bank-architecture/formosanbank-xml-format)
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
3. **CJK context — RULED (2026-09-03).** A `~` **between two CJK
   characters** is not gloss notation and carries no morphological
   meaning. Chinese glosses and translations use it for an open semantic
   argument (`把~抓住`, "catch ~"), for prosodic lengthening after an
   interjection (`哇~真漂亮`), and for numeric ranges (`五~六`). The
   gloss-scrape rules therefore strip it before parsing morpheme
   structure, so it neither contributes a morpheme slot nor enters a
   marker skeleton. The exception requires CJK on *both* sides, which
   leaves Leipzig-style `CAU~walk` untouched. Implemented in
   `gloss_scrape._gloss_notation_text` (consumed by G001, G002, G007).

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
repeat, and may be kept deliberately.
**Mechanism (ruled 2026-08-11 — deliberately no corpus-type registry):**
whether a corpus should be duplicate-free is that corpus's own choice,
expressed in its pipeline — reference resources include a dedup step
(`remove_duplicate_sentences.py`) in their `CodeAndDocs/` reproduction
pipeline; narratives don't. `validate_duplicate_sentences` reports every
duplicate as **SOFT** (maintainer decides), *upgrading to HARD only when
the corpus's CodeAndDocs declares a dedup step* — a leftover duplicate
then signals a pipeline defect, not a content question. The within-file
vs cross-file distinction survives as the finding's `scope`.

### POL-023 · RULED · 2026-08-10 · M-tier presence (scope amended 2026-08-12)
**The unit of morphological analysis is the sentence, not the file.** In a
sentence that carries *some* morphological parsing, **every W gets at least
one M**; a W with exactly one M there is read as "analyzed as
monomorphemic". A sentence that carries **no** parsing carries **no M at
all** — the author may simply never have analyzed it, and requiring an M
there would fake an analysis it does not have. The same holds of a whole
corpus: with no morpheme segmentation there is **no M level at all**, since
an all-single-M mirror tier adds no information.

A sentence "carries some parsing" when either (a) some W in it has two or
more M children, or (b) some M's FORM differs from its parent W's FORM (an
infix split, or an M that shows a segmentation the W FORM does not).

**Why per sentence** (amended 2026-08-12): a file-level rule cannot express
"this sentence is unanalyzed". Corpora that parse some sentences and leave
others alone are the normal, honest case (YeddaPalemeqBlog: 494 parsed
sentences, 161 unparsed), and under the file-level reading a single parsed
sentence turned every unparsed sentence in the file into a finding.

Enforced as SOFT findings in `validate_xml.py`; SOFT because some existing
corpora trip these and will need fixing over time:
- **V144** — M-less W inside a *parsed sentence* (per sentence).
- **V145** — an M level in a file where **no** sentence carries any parsing
  (per **file**, deliberately). "Every M mirrors its W" is evidence of a
  fake tier only in bulk: one short sentence whose words really are
  monomorphemic looks identical to a mirror tier, and single-M Ws are
  explicitly legal, so sentence-scoping V145 would manufacture false
  positives. A whole file with no multi-morphemic word anywhere is the
  reliable signal.

(Resolves the Bunun-Topic-Focus degenerate-single-M question: its 51
single-M Ws are conforming as long as no W lacks an M.)

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

### POL-036 · RULED · 2026-08-11 · gloss standardization is additive
Original source glosses are **preserved as written** (in
`TRANSL[@kindOf="original"]` at M/W level). Standardizing a gloss — e.g.
normalizing a source's idiosyncratic label to a Leipzig-style code — never
overwrites the original: it is recorded as a *separate*
`TRANSL[@kindOf="standard"]` alongside it. Made explicit from the GitBook
XML-format page's long-standing instruction ("Original source glosses
should be preserved. A standardized gloss can be added as a separate
kindOf='standard' translation"); companion to POL-001's source-fidelity
guarantee, applied to the gloss tier.

### POL-037 · RULED · 2026-08-11 · stable public identifiers
Published identifiers are **stable**: a `TEXT/@id` must never collide with
(or be reused from) an already-published `TEXT/@id`, and S/W/M ids —
unique within their file — are not renumbered once published. Rationale:
external users cite and align against these ids, and the manual-edits
mechanism (POL-030) keys its records by sentence id — renumbering
silently orphans both. Regeneration pipelines must therefore produce the
same ids run over run; an id scheme change is a breaking change to
announce, not a cleanup. Made explicit from the id rules implicit in the
GitBook XML-format page.

### POL-038 · RULED · 2026-08-11 · data files change only via code
XML files and raw scrape files are **only ever modified by committed
code** — a pipeline script, a recorded `manual_edits.xml` applied by
`apply_manual_edits.py` (POL-030), or a one-off script committed to
`CodeAndDocs/`. Never by hand and never ad hoc (including "quick"
interactive edits during audits or reviews): a non-code edit is not
reproducible and is silently destroyed on regeneration. This applies to
published `XML/`, to raw scrapes under `CodeAndDocs/`, and to POL-035
pre-correction snapshots alike (a snapshot defect is fixed by a committed
script run against the snapshot, not by editing it). Raised by: the
2026-08-11 Group 1 sweep review.

### POL-039 · RULED · 2026-08-11 · no data tables hidden in code
Lookup tables and other data that critical steps depend on are **never
hardcoded inside a python file**. Expose them as human-readable CSV/TSV/
XML in a prominent, documented place (repo-root registries —
`languages.csv`, `dialects.csv`, `standards.csv` — or `Orthographies/`)
and load them from there, through exactly one loader. Raised by the ISO
639-3 map drift: four separate hardcoded copies of the code→language
table had diverged (`bzg` present in one, `pzh` in another).
Implemented by: `languages.csv` + `QC/corpus_counts.load_language_codes`
(the other three copies now import from it).

### POL-040 · RULED · 2026-08-12 · language identity registry
`languages.csv` (repo root) is the canonical registry of ISO 639-3 code →
language name; every consumer loads it through
`QC/corpus_counts.load_language_codes` (POL-039). Its `Language` values
use the same spellings as `dialects.csv` and `standards.csv` — the three
registries name languages identically. Consistency is checked by
`validate_registries.py` (V150: every language has a standards.csv row;
V155: dialects.csv↔languages.csv naming, unique lowercase ISO codes;
SOFT per POL-034). Adding a language = one `languages.csv` row, plus a
`standards.csv` row (blank scheme until a standard is designated) and
`dialects.csv` rows if multi-dialect. Documented for end users on the
GitBook "Formosan Dialects" page.

### POL-041 · RULED · 2026-09-03 · W-tier presence
The W tier asks the same question as the M tier (POL-023) one level up,
and gets the same answer at the level of the file: a corpus with **no**
word segmentation has **no W level at all**, which is the normal state
for most of the bank and never a finding. But a file where *some*
sentences carry a W tier and others do not is an **incomplete
segmentation pass**, and the unsegmented sentences are reported.

An `S` with no `FORM` is never counted: an untranscribed-audio shell has
no text to segment, and V010 already reports it.

**Why the file, not the sentence** — the opposite of the POL-023
amendment, deliberately. V144 can be per sentence because a parsed
sentence announces itself (a W with two or more M children, or an M FORM
differing from its parent W FORM). A sentence with **no W announces
nothing at all**: there is no per-sentence signal that distinguishes
"not segmented yet" from "not segmented, by design". Only the presence
of segmented siblings in the same file makes the omission legible, so
the file is the unit of judgement.

Enforced as SOFT finding **V148** (`v148_W_less_S_in_segmented_file`) in
`validate_xml.py`, aggregated per file. SOFT because a partly segmented
file is a work-in-progress, not a defect in what it does contain.

Scope consequence for **V060** (W-count vs word-count, `validate_glosses.py`):
V060 compares counts, so it now applies only where a W tier exists — it
skips a file with no W anywhere, and skips an individual `S` with no W
inside a partially segmented file. Whether a sentence *ought* to have a W
tier is this policy's question, not V060's. Previously V060 fired once per
sentence on every sentence-only corpus, reporting a missing tier as a
count mismatch "due to normalization or spelling". Raised by:
`codex/qc-sentence-only-gloss-noise` (2026-06-25), which fixed the
sentence-only half but not the partially segmented half.

---

## 5. Rights

### POL-042 · RULED · 2026-09-05 · every published TEXT
Every published `TEXT/@copyright` is **exactly one of the values in
`rights_vocabulary.csv`** (repo root, joining `languages.csv`, `dialects.csv`
and `standards.csv` as a registry per POL-039): a Creative Commons licence, or
`public domain`. Exact match, not a pattern — a sentence that *mentions* a
licence is not a licence declaration, and free text admits errors no reader
catches (`CC NC-BY` shipped in RauDong across 20 files). Where a value names no
version it is 4.0.

**No exceptions.** A corpus whose rights cannot be expressed as one of these
values is not published in FormosanBank, however genuine the permission behind
it. Permission that does not amount to a licence is recorded in the corpus
README (POL-044), not in `@copyright`.

**One licence per corpus.** Per-item rights variation within a corpus is not
representable and is deliberately not designed for; the case does not exist
today. Implemented by: V160 (`copyright_present`) and V161
(`copyright_in_vocabulary`), both HARD, in `QC/validation/rules/rights.py`.
Spec: `docs/superpowers/specs/2026-09-05-rights-enforcement-design.md`.

### POL-043 · RULED · 2026-09-05 · existing rights claims
An existing rights claim in published XML is **never removed or weakened on the
grounds that the reviewer could not find its evidence.** Permission evidence is
held by the maintainer, not in this repository, so its absence here proves
nothing. A reviewer who doubts a claim escalates to the maintainer; only a
*positive* finding — the source says otherwise, or the grant is known not to
exist — justifies a change.

Rationale: in the August 2026 RE-PORT batch five pull requests replaced a
Creative Commons licence with bespoke permission prose, each reasoning from an
absence (#165, #167, #174, #179, #181). #167 was overturned by the maintainer,
who held the correspondence the reviewer could not see. A single cautious
judgement propagates to every `TEXT` in the corpus — 100 files for #167, 16 for
#179 — and is expensive to reverse.

### POL-044 · RULED · 2026-09-05 · rights documentation and merge review
**Documented.** Each corpus README carries a `## Rights` section with two
structured lines and prose beneath:

```
**License:** CC BY-NC 4.0
**Rights source:** <grantor>, <YYYY-MM-DD>; evidence: ask maintainer
```

The licence must equal the corpus's `@copyright`; the date is when permission
was granted or last confirmed. `evidence: ask maintainer` rather than naming a
system — the evidence store may change, the instruction to a reader will not.
The prose explains where the right came from and is required but unchecked. The
GitBook corpus page carries the same licence in its `## Copyright` section.

**Interrogated at merge.** Any change to a corpus's licence, in either
direction, fails `.github/workflows/rights-comparison.yaml`, which compares the
head against the base ref exactly as `token-comparison.yaml` does. There is no
committed baseline — a baseline is redundant state that can itself drift, and a
merge check already has both sides available. A legitimate change lands by
explicit maintainer override, which is deliberately the hardest step in the
mechanism. There is no label-based bypass; the friction is the control
(maintainer, 2026-09-05).
Implemented by: `QC/validation/rights_delta.py`,
`tests/corpora/test_rights_documentation.py`, and the GitBook repo's
`manage_corpus_pages.py check --strict`.

### POL-045 · RULED · 2026-09-05 · audio rights
**Audio inherits the XML licence.** Audio published for a corpus carries that
corpus's `@copyright`; audio for a corpus that is not published in
`Corpora/` is not licensed for reuse. The licence is therefore **never recorded
separately**: `audio_permissions.json` stores only what cannot be derived —
repositories, `access`, `status`, corpus mapping, and the approval pointer —
and a loader resolves the licence from the corpus XML and the Hugging Face slug
from `rights_vocabulary.csv`.

Rationale: the rule was already stated in two places (`AUDIO-PERMISSIONS.md`,
and `publication_rule` in the JSON) and already true in fact — all 22 audio
sources matched their corpus XML, the only exceptions being the two private
development repositories, which correctly carry no licence. Storing the derived
value meant every rights change had to be made twice, and
`validate_hf_audio.py` needed a `license_family()` helper to paper over the two
spellings. Absorbs the policy text formerly in `AUDIO-PERMISSIONS.md`.

---

## 6. Development

Section 4 governs what may be done to the data. This section governs **the code
that does it, and how changes to that code are reviewed.** Its recurring theme
is that thirty-odd corpora built thirty-odd different ways cost more than they
save: every fork of a shared behaviour is a rule that has to be re-audited,
re-explained, and re-fixed once per corpus.

Rights entries with a development bearing live in section 5 and are not
repeated here: **POL-043** (never weaken an existing rights claim from absence
of evidence) and **POL-044** (licence changes are interrogated at merge).

### POL-046 · RULED · 2026-09-05 · processing code
**Shared tools first; corpus-specific processing code is a last resort.**
The order of preference for any cleaning, standardization, phonology, or
repair step is:

1. **Use the existing shared tool as it is** (`QC/cleaning/*`,
   `QC/utilities/*`). If an existing flag does the job, use the flag.
2. **Extend the shared tool.** If the behaviour is right for the bank but the
   tool cannot yet express it, change the tool — and add the test. A behaviour
   that one corpus needs, several usually need.
3. **Write corpus-specific code only when the behaviour is genuinely unique to
   that corpus.**

**Initial parsing is the standing exception.** Turning a particular PDF, DOCX,
scrape, or database dump into the original tier is inherently
source-specific; `generate_xml.py` is expected to be corpus-local and needs no
justification. Everything downstream of it does.

Rationale — this is a guard against forking, not a style preference. The
2026-09-05 pipeline audit found the same downstream behaviours reimplemented
per corpus: five mutually incompatible ways of invoking `standardize.py`, three
ways of passing an orthography to `add_phonology.py` (including omitting it),
and corpus-local reimplementations of cleaning that the shared cleaner already
performs. Each fork is a place where a bank-wide ruling silently fails to apply.

**At merge**, corpus-specific code that duplicates shared behaviour is a
review finding: either fold it into the shared tool, or record in the corpus
README why the shared tool cannot serve.

### POL-047 · RULED · 2026-09-05 · reproduction pipeline
Every published corpus has **one entry point, with one name and one canonical
step order.**

```
CodeAndDocs/
  refresh_source.sh     # optional — scrapes/fetches source into CodeAndDocs/.
                        #   Only where the source can be re-fetched. Never
                        #   invoked by generate_xml.sh.
  generate_xml.sh       # THE entry point: source -> published XML/.
    1. generate_xml.py            # corpus-local; builds the original tier
    2. QC/cleaning/apply_manual_edits.py   # optional; no-op when absent
    3. QC/cleaning/clean_xml.py
    4. QC/utilities/standardize.py
    5. QC/utilities/add_phonology.py
```

**Where manual edits sit relative to the cleaner is not forced** (maintainer,
2026-09-05). Both orders are in use and both are fine; before is mildly
preferable, because the cleaner then normalizes the hand-entered text along with
everything else. Two things about step 2 *are* constraints, and they are what the
order has to respect:

- **It runs on fresh pre-manual build output.** `apply_manual_edits.py` is not
  idempotent — re-run over already-applied XML it prunes its own records as
  no-ops (`QC/README.md`, "Discipline"). Whatever the position, nothing before
  it may have already applied the edits.
- **It runs before `standardize.py` and `add_phonology.py`.** An edit record
  carries no standard FORM and no PHON, so both are regenerated from the edited
  original. A corpus that repairs the original tier late must re-run steps 4 and
  5 afterwards, as NTUFormosanCorpus does.

`apply_manual_edits.py` (shared, POL-030) is for one-off human judgement; a
corpus-local `apply_manual_corrections.py` is for *systematic, source-derived*
rules and belongs after step 5, not in place of it.

Four properties the entry point must have:

- **Idempotent.** Re-running over a clean checkout leaves `git status` empty.
  Achieve it by restoring a POL-035 snapshot or by building into a staging
  directory and installing — never by mutating published `XML/` in place with
  no baseline. This is also what lets a non-idempotent step like
  `apply_manual_edits.py` sit inside an idempotent pipeline: it never sees its
  own previous output, because the run starts from a fresh baseline.
- **Self-contained** — see POL-048, and POL-052 for recording which
  tool version built the published bytes.
- **Build only.** Validators do not run inside `generate_xml.sh`. Put them in a
  separate `validate.sh` if the corpus wants a committed QC run; a build that
  cannot complete because a validator fails cannot be used to investigate the
  failure.
- **Complete.** A corpus whose XML changes but which ships no script that
  produces that XML violates POL-038.

**Deviation is permitted, but is not silent.** Extra steps, a missing step, or
a different order are all legitimate for real reasons — several corpora
correctly have no `standard` tier and therefore no steps 4–5. The requirement is
that the deviation is **stated in the corpus README and interrogated at merge**,
not discovered later by an auditor. Reviewers: an unexplained departure from
this shape is a review finding on its own.

Raised by the 2026-09-05 pipeline audit: across 33 corpora on `main` and in open
PRs there were eight entry-point conventions (`make_xml.sh` ×16,
`reproduce.sh` ×11, two corpora with no build script at all) and twelve
distinct step orderings, with nothing in this file, in `QC/README.md`, or in CI
constraining any of it. The shape above is the existing plurality, not a new
invention.

### POL-048 · RULED · 2026-09-03 · reproduction inputs
**A published corpus rebuilds from a FormosanBank checkout alone.**
Dev repos are permanently private and inaccessible to everyone but the
maintainer, so a build that reads one is not reproducible by anybody who has the
published data. The pinned `Formosan-*` dev-repo commit is **provenance
metadata, never a build input.**

Concretely, `generate_xml.sh` must not require: a second clone pinned to a
particular commit, a private reference repository, a gitignored `Private/`
directory, or environment variables naming any of those. Everything the build
reads is committed under that corpus's `CodeAndDocs/` or in the shared repo.

Maintainer ruling, 2026-09-03: *"We want to retain the reproducibility **within**
the main FormosanBank repo. Dev repos are permanently private so not accessible
to others."* Raised by the RE-PORT batch, where builds required
`FORMOSANBANK_AUTHORITY` pinned to a specific commit, `VALIDATOR_ROOT`,
`FORMOSANBANK_QC_ROOT`, and in one case a private reference repository — and by
a build that hard-exited without a `CodeAndDocs/Private/` source file.
A commit pin also self-invalidates: it refuses to run against the repository it
lives in as soon as `main` advances.

**Recording a commit is not the same as depending on one.** POL-052 requires
every corpus to record the FormosanBank commit its published XML was built
against; what this entry forbids is treating that record as a build input.

### POL-049 · RULED · 2026-09-05 · pull-request scope
A pull request that ports or reworks one corpus **does not change shared
code.** Changes to `QC/`, `tests/`, `POLICIES.md`, repo-root
registries, `requirements.txt`, or `.github/workflows/` belong in their own pull
request, reviewed on their own merits and merged first.

Rationale: a shared-code change buried in a 3,000-file corpus diff is not
reviewed, and it silently couples merge order. In the RE-PORT batch one PR was
the sole carrier of a new `standardize.py` flag that its own build script
depended on; another was the sole carrier of a `corpus_counts.py` change; a
third carried a policy entry, a data-loss fix, its test, and a dependency pin
that would all have been lost had the competing PR for the same corpus landed
instead. Repo-wide edits were bundled into single-corpus PRs at least five times.

**This does not conflict with POL-046 step 2.** Extending a shared tool because
one corpus needs it is encouraged — it just happens in its own pull request,
merged first, so the extension is reviewed as a shared-tool change and the
corpus PR that depends on it cannot become its sole carrier.

### POL-050 · RULED · 2026-09-05 · superseding a ruling
A merged decision is reversed **explicitly or not at all.**
A change that undoes something previously ruled and merged must say so, cite
the commit or POL entry it supersedes, and give the reason. Rediscovering the
old behaviour and reinstating it as though it were new is not a reversal, it is
drift.

Rationale: two pull requests reintroduced `standard` tiers that merged commits
had deliberately removed, neither mentioning the earlier decision. Separately,
two merged rulings on where `apply_manual_edits.py` runs contradicted each
other for three weeks, and five corpora implemented one and two the other —
resolved only by POL-047 above.

### POL-051 · RULED · 2026-09-05 · removing published content
Removing published content — sentences, words, morphemes, translations, audio
elements — is **disclosed in the pull request with a count and a reason**, and is
interrogated at merge. Silence is the finding, not the
deletion: deletions are often correct, and several were.

The mechanism already half exists. `.github/workflows/token-comparison.yaml`
compares token counts across a merge and `rights-comparison.yaml` compares
licences (POL-044); the same shape extended to element counts would make this
checkable rather than a review convention. In the RE-PORT batch one PR removed
144,436 `AUDIO` elements, 126,239 `W` elements, and every original `PHON` tier;
another removed 1,968 translations. Three of the batch's twenty-four PRs
disclosed their removals.

In force now as a review convention; extending the comparison workflows to
element counts is the mechanism that would make it checkable rather than
remembered.

### POL-052 · RULED · 2026-09-05 · tool provenance
**Record which tools built the published XML; rebuild with the current ones.**

Each corpus records the FormosanBank commit its published `XML/` was last built
against, in **`CodeAndDocs/provenance.json`** — one fixed path, one fixed shape,
so the record is machine-readable and can be checked:

```json
{
  "_note": "The FormosanBank commit this corpus was built against. Provenance only — the build does not read this file.",
  "formosanbank_commit": "3a3c47c220520113f747e6a2d441494000e13c4b",
  "built": "2026-09-05"
}
```

`formosanbank_commit` (a full 40-character SHA) is required; `_note` and `built`
are optional. The corpus README's reproduction section **links to the file**
rather than repeating the SHA, so there is one copy to keep current; the GitBook
page's `## Corpus Processing` section does the same. A SHA transcribed into
prose is a second copy that drifts.

**Enforced** by `tests/corpora/test_provenance.py`: the file must exist, parse,
and carry a well-formed commit, and the README must link it. Corpora that
predate this entry are listed in `provenance_pending.txt` at the repo root — a
list that only ever shrinks, and that a new or rebuilt corpus is never added to.

**The record is documentation, never a gate.** `generate_xml.sh` runs with the
tools in the checkout it is invoked from — normally `main` at HEAD — not with
the recorded commit. On a mismatch it **notes the difference and continues**;
it does not refuse to run, and it does not go looking for another checkout.
A build that exits because the surrounding repository is not at the recorded
commit violates this entry and POL-048, and self-invalidates the moment `main`
advances. `Corpora/Song-Kanakanavu-Grammar` has the intended shape — one
`git rev-parse HEAD`, one note to stderr, and the build proceeds. A build script
that reads `provenance.json` to compare against, rather than hard-coding the SHA
a second time, is better still.

**Why record it at all, if it does not constrain the build.** Because it is what
makes a rerun's diff readable. Shared tools change, and when they do, every
corpus built before the change will produce a diff on its next rebuild that has
nothing to do with why it was rebuilt. The 2026-09-04 `add_phonology.py` stress-
accent fold left **9,355 committed PHON tiers across nine corpora** that no
longer match what a rebuild produces; nothing is wrong with any of them, but the
next person to rerun one of those pipelines meets a large unexplained diff. The
recorded commit answers the question that diff raises — *did I cause this, or did
the tools move underneath me?* — and turns it into a `git log` on `QC/`.

**Reproducing the exact published bytes** at the tool version that produced them
is always possible by checking out the recorded commit; that is the record's
other use. It is deliberately not the default, because pinning corpora to the
tool versions they were born with is how a bank of thirty-odd corpora ends up
with thirty-odd behaviours (POL-046).

**Consequence for review:** `provenance.json` is updated in the same pull
request that rebuilds the corpus. A rebuild that leaves the old commit in place
is a stale record, which is worse than none — it asserts a correspondence
between the tools and the bytes that no longer holds.
