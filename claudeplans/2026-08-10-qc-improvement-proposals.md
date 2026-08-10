# QC improvement proposals — 2026-08-10

Step-back review after the last few days of work. Data sources: (a) the
`feature/shared-source-phonology` branch vs `main` (~100 commits: null-morpheme
handling, case-aware standardization, standardize-owns-standard-cleaning,
conversion-table validator, per-language standard registry); (b) the ten
gloss-scrape audits and five dev-repo audits from 2026-08-01→10 plus session
memories; (c) the manual-edits mechanism and the hand-edit history in git.

Issues already handled on the branch (null-glyph canonicalization in
`clean_xml`, V069, V120 downgrade, dash canonicalization, C012 migration,
`standards.csv`, `validate_conversion_table.py` existing at all) are *not*
re-proposed; each proposal below is something that is currently unhandled or
under-handled. Format per proposal: **Problem / Proposal / Importance / Risks**.

## Disposition (2026-08-10, after maintainer review)

| Item | Ruling | State |
|---|---|---|
| 0.1 POLICIES.md | draft requested | **Drafted** (`POLICIES.md`, root; sync design inside) |
| 1.1 e2e integration test | plan requested | Planned (`docs/superpowers/plans/2026-08-10-qc-pipeline-tests.md` Task 3) |
| 1.2 rerun-stability | **clean_xml only** — standardize/add_phonology are regenerators, no tests needed | Plan Task 2 trimmed accordingly; warnings-append bug fix is Task 1 |
| 1.3 registry consistency | **SOFT, not HARD** | Planned as `validate_registries.py` V150–V153 (plan Task 4) |
| 1.4 manual-edits tests | wants implementation detail | Plan Task 5; schema verified against `manual_edits_common.py` |
| 1.5 audit-to-fixture | wants practice detail | Convention created (`tests/fixtures/audit_regressions/README.md`) + closing step in `audit-dev-repo` skill |
| 2.3 conversion-table CI | wants design | Design in appendix below |
| 2.4 pre-port gate | **must work without AI** | **Built**: `QC/validation/validate_port_readiness.py` (P001–P006) + tests |
| 2.7 entity decode in clean_xml | explanation requested | See discussion with maintainer; detector half already existed (V132) |
| 3.1 grammaticality rule | **go** | **Built**: V142 SOFT + tests |
| 3.2 gloss-language rule | **go** | **Built**: V143 SOFT (rate-based) + tests |
| 3.3 impostor-M detector | discussion requested (are spurious Ms bad?) | Open — hinges on POL-023 |
| 3.4 double-encoding detector | **go** | Already existed as V132; extended to numeric refs + test |
| 3.5 V060 marker counting | **dropped** (no leading markers should exist; V142 flags them) | Dropped |
| 4.1 run-qc-pipeline | **go** | **Updated** (also fixed wrong TSV naming convention in the skill) |
| 4.2 audit-dev-repo + briefing | **approved** | **Updated** (starred-parens sweep, null glyphs, whitelist, fixture step; briefing pipeline refresh) |
| 4.3 audit-gloss-scrape | needs more detail | Explanation owed to maintainer |
| 4.4 port-corpus-in | **go** | **Updated** (port-readiness gate wired in) |
| 4.5 setup-new-dev-repo | **go** | **Updated** (forward-looking notes) |

## Appendix: conversion-table validation in CI (design for 2.3)

**What runs.** A small driver script
(`QC/validation/run_conversion_table_checks.py`, ~30 lines) enumerates
`Orthographies/ConversionTables/*.tsv`, resolves each table's source/target
profiles from its `<Language>_<Scheme>_113.tsv` filename (the same
resolution `standardize.py` uses), skips self-mapping utility tables, and
invokes `validate_conversion_table.py` per table, collecting one summary
line each (OK / N mismatches / CRASH).

**When it runs.** In a new GitHub Actions workflow (or a job in the existing
xml-validation one) triggered on pull requests and pushes whose paths touch
`Orthographies/**` — not on every XML commit; tables change rarely and the
run takes seconds. Deliberately not merge-to-main-only: the point is to
catch a bad table edit *in the PR that makes it*.

**Blocking policy, two stages.** Stage 1 (now): report-only — the job exits
0 and writes the per-table summary to the step summary (and PR comment).
The current baseline (18 of 34 tables effectively blocked) makes a blocking
job unusable today. Stage 2 (after remediation): a checked-in baseline file
(`QC/validation/conversion_table_baseline.txt`, the tables currently allowed
to fail) makes the job block on *regressions* only — a failing table not in
the baseline fails CI; fixing a table shrinks the baseline; at zero, delete
the file and the job is fully blocking.

**Remediation order** (from `claudeplans/conversion-table-audit-findings.md`):
(1) the 5 dialect-name crashes (Rukai ×3, Seediq ×2) — pure header/profile
sync, no linguistic judgment needed; (2) profile gaps (missing
long-vowel/glottal graphemes); (3) the 13 reported IPA mismatches — these
need per-language review and may change published standard tiers on
regeneration, so batch per language and diff before committing. The
validator's deferred case-awareness (audit findings #5/#7) rides along as
its own small task.

---

## 0. Cross-cutting (highest leverage)

### 0.1 A project policy ledger (`POLICIES.md`) that skills and audits cite

**Problem.** The same policy questions get re-raised, re-argued, and separately
resolved corpus by corpus. In the last ten days alone: typographic apostrophe
U+2019 vs U+0027 (3 corpora), tilde U+223C vs `~` (1), null-glyph choice per
tier (5), `*`/`?` marginality marking (4), infix-host M-tier notation
(rejoined vs hyphenated — 3), degenerate single-M elements (1), lexical-corpus
duplicates (1). Every audit report ends with "maintainer ruling needed" on
items that were already ruled on elsewhere, or that will recur on the next
corpus. The rulings currently live scattered across per-corpus READMEs,
claudeplans reports, and memory files.

**Proposal.** One versioned `POLICIES.md` (repo root or `QC/`), one short
entry per ruling: the question, the ruling, the rationale, date, and which
tier(s) it applies to. Skills (`audit-dev-repo`, `audit-gloss-scrape`,
`port-corpus-in`, `run-qc-pipeline`) reference it by anchor instead of
restating policy; audit reports cite entries instead of asking. Open questions
get an entry marked UNRESOLVED so they're asked once, answered once. Seed it
with the rulings already made (original-tier = actual source; null-glyph
canonical ∅; W/M-at-end soft convention; dash canonicalization) and the
currently-open ones (apostrophe, tilde, grammaticality marking, infix hosts).

**Importance.** High — this is the single cheapest change that reduces
repeated work; nearly every audit in the last week would have been shorter
with it.

**Risks.** Essentially none. Only risk is drift (ledger says one thing, code
does another) — mitigated by linking each entry to the implementing rule ID
or script.

---

## 1. Tests for the QC pipeline itself

### 1.1 End-to-end pipeline integration test (HIGH)

**Problem.** Every module on the branch is well unit-tested (~160 new tests),
but no test runs the actual pipeline sequence `apply_manual_edits → clean_xml
→ standardize → add_phonology → validators` over one fixture corpus. The
branch's whole point was *redistributing responsibilities across stages*
(C012 moved from clean_xml to standardize; standardize now assumes clean_xml
already canonicalized dashes and null glyphs; add_phonology assumes
standardize's output). Cross-stage assumption breakage is exactly the bug
class module tests can't see, and the specs themselves state the ordering
invariants without any test enforcing them.

**Proposal.** A `tests/integration/` suite with one small synthetic corpus
(2–3 TEXTs covering: null morphemes in W/M, hyphen/dash variants, a TSV
conversion, a `--copy` language, digit-flanked hyphens, a foreign-ø word).
One test runs the full sequence via each script's `main()` and asserts a
golden output tree; companion tests assert the stated invariants (null marker
survives to M tier as ∅; standard S-FORM has no null units after TSV-mode
standardize; PHON regenerates identically).

**Importance.** High. This is the top gap: the refactor just merged, will be
rerun over ~26 published corpora, and any stage-interaction bug becomes a
corpus-wide diff.

**Risks.** Low (test-only). Golden files add maintenance cost — keep the
fixture minimal and regenerate goldens via a documented script rather than by
hand.

### 1.2 Rerun-stability tests (MEDIUM-HIGH) — *revised 2026-08-10 after investigation*

**Investigation result (maintainer asked whether these tools can/should be
idempotent).** Two different properties are in play:

- `standardize.py` and `add_phonology.py` are **regenerators, not
  transformers**: in every mode, `create_standard` *replaces* the standard
  FORM with a fresh copy of the original before conversion, and
  add_phonology rewrites existing PHON. Conversion never sees its own
  output, so even a non-idempotent table rule (Cauquelin Puyuma `l→ll`) is
  safe — verified empirically: double TSV runs yield `llima`, never
  `llllima`; double `--copy` and `add_phonology` runs are byte-identical.
  The guaranteed-by-construction property is **regeneration determinism**
  (run 2 == run 1), and the tests should pin its two enabling invariants:
  derived tiers replaced not appended; conversion input is the original
  tier only.
- `clean_xml.py` faces the **true idempotence** question, because its
  steady-state input *is* its own prior output (published corpora get
  re-cleaned). Verified empirically: a double run over all 93 dirty test
  fixtures left every XML byte-identical. But this holds rule-by-rule, not
  by construction — a future rule whose output falls in another rule's
  input domain breaks it silently. The test converts "not guaranteed" into
  "continuously verified"; if a future rule genuinely can't be idempotent,
  the failing test forces that discussion instead of shipping churn.
- **One real bug found:** `CleanerWarnings.write_csv` opens in append mode,
  so every rerun duplicates persistent warn-only rows in
  `cleaner_warnings.csv` / `standardize_warnings.csv` (84→166 rows on a
  no-op second run). Fix: rewrite per run (warnings CSVs are per-run
  reports — POL-033).

**Proposal.** As specced in
`docs/superpowers/plans/2026-08-10-qc-pipeline-tests.md`: fix the warnings
append bug first, then run-twice tests asserting run2 == run1 byte-for-byte
(clean_xml over all fixtures; standardize in `--copy`, `--remove_accents`,
and TSV modes with an `l→ll` doubling-rule fixture; add_phonology), never
run1 == input (first runs may legitimately reformat).

**Importance.** Medium-high; cheap, protects every future rerun.

**Risks.** Low — the empirical baseline already passes; the one known
failure (warnings sidecar) has a two-line fix.

### 1.3 Cross-file registry consistency tests (MEDIUM-HIGH)

**Problem.** The pipeline now depends on agreement among loosely coupled data
files: `standards.csv` ↔ `ISO_TO_LANGUAGE`, `dialects.csv` ↔ orthography
profile columns ↔ conversion-table headers ↔ rules-sidecar `dialect` values.
The very first run of `validate_conversion_table.py` found 5 tables that
*crash* purely on dialect-name mismatches (Rukai ×3, Seediq ×2). One test
exists (every language resolves in standards.csv) but nothing stops a new
language/dialect being added to one file and not the others.

**Proposal** *(revised per maintainer ruling 2026-08-10: SOFT, not HARD —
registries may be legitimately out of sync)*: a repo-level
`QC/validation/validate_registries.py` emitting **SOFT** findings
(V150–V153) through the standard findings framework: every language in
`ISO_TO_LANGUAGE` has a standards.csv row; non-blank schemes have an
`Orthographies/<scheme>/` folder; conversion-table value columns and
`.rules.tsv` `dialect` values are canonical per `dialects.csv`. Exit 1 only
when a registry file is unreadable. Specced in
`docs/superpowers/plans/2026-08-10-qc-pipeline-tests.md` Task 4.

**Importance.** Medium-high — this exact class already produced 5 broken
tables, and the branch multiplied the number of dialect-keyed files.

**Risks.** Low as SOFT: legacy drift shows up as a shrink-over-time baseline
rather than a CI blocker.

### 1.4 Manual-edits round-trip and pipeline-survival test (MEDIUM)

**Problem.** `capture_manual_edits.py` / `apply_manual_edits.py` is the
mechanism we want every corpus to adopt (currently exactly one —
Wu-Amis-Pa-Verbs — uses it), but there is no test that (a) capture→apply
round-trips a hand edit, (b) an applied edit *survives the rest of the
pipeline* (clean_xml/standardize don't undo it), or (c) the no-op pruning
doesn't silently discard a real edit whose only difference is one the
canonicalizer strips (standard FORM and PHON are deliberately stripped from
records — an edit made *only* to those tiers is unrepresentable and would
vanish without warning).

**Proposal.** Round-trip tests plus a "survival" test through the full
pipeline; a test pinning the documented limitation that standard-FORM/PHON
edits are rejected loudly at capture time rather than silently pruned.

**Importance.** Medium now, rising as adoption grows (see 2.5).

**Risks.** Low; may force a small capture-time UX change (explicit error).

### 1.5 Audit-to-fixture convention (MEDIUM)

**Problem.** The last week's audits found a series of concrete bug shapes
(`*(malra)` obligatory-clitic inversion, ø/Ø/∅ variants, eng/zho swapped
glosses, `&lt;`-double-encoding, leading `? ` counted as a word). The parser
bugs got fixed, but nothing prevents regressions: the findings live in prose
reports, not in fixtures.

**Proposal.** A lightweight convention: every audit finding that led to a
code fix gets a minimal XML fixture in `tests/fixtures/audit_regressions/`
named after the finding, plus one assertion. Add this as a closing step in
the `audit-dev-repo` / `audit-gloss-scrape` skills ("if the fix landed in
FormosanBank code, add the regression fixture").

**Importance.** Medium — steady compounding value.

**Risks.** None beyond minor fixture sprawl; naming convention keeps it
navigable.

### 1.6 `standardize_warnings.csv` contract test (LOW)

**Problem.** Standardize now emits a warnings CSV (c012/c022) but only two
tests assert it exists; schema, row content, and no-double-reporting are
untested. Downstream tooling and skills will start reading this file.

**Proposal.** One test asserting header schema and exact expected rows for a
fixture that triggers both codes once each.

**Importance.** Low. **Risks.** None.

---

## 2. QC pipeline improvements

### 2.1 Typographic-normalization policy + one canonicalization pass (HIGH)

**Problem.** Character-level typography is decided per corpus, differently
each time: curly apostrophe U+2019 → straight `'` (Lin: 14 pairs; Kuo-Sung: 1;
Sakizaya: 3), tilde U+223C vs ASCII `~` (Amis-Adversative, open), fullwidth
`＝`/comma variants (NTU, Sakizaya), guillemet `‹um›` vs ASCII `<um>` per tier
(Lin — accepted two-tier convention). Three audits explicitly requested "one
project-level ruling instead of per-corpus relitigating." The branch already
did this for dashes/hyphens; the rest of the typography space is unowned.

**Proposal.** (1) Rule in POLICIES.md per character class: canonical form,
which tiers it applies to, and the crucial carve-out that a codepoint which is
a *letter* in a language's orthography profile is spelling, not typography
(the apostrophe/glottal is a letter in several Formosan orthographies — the
original tier's spelling-preservation guarantee governs). (2) Implement as a
table-driven pass in `clean_xml.py` mirroring the dash pass, gated per
character class on the language's profile (skip if the codepoint is in the
letter inventory), with a `--report-only` mode first run.

**Importance.** High frequency: some form of this appeared in at least 5 of
the last 10 gloss audits and will appear in essentially every print-derived
corpus.

**Risks.** Medium — this is the one cleaning change that can corrupt
original-tier spelling if the letter-inventory gate is wrong or a profile is
incomplete. Mitigations: report-only rollout, per-language gating, and the
1.2 idempotence tests. Also note U+2019→U+0027 changes PHON derivability if
a profile maps only one of the two.

### 2.2 Machine-readable grammaticality/marginality marking (MEDIUM-HIGH; policy decision first)

**Problem.** Elicited-example corpora contain starred (`*`) and marginal
(`?`) examples. Current handling is inconsistent *within single corpora*
(Lin: `?` kept inline in FORM, `*` stripped with the fact surviving only in
free-text `source`/`notes`), and inconsistent across corpora (Kuo-Sung
rejected starred examples at admission; Puyuma-Teng keeps them with
notes-only marking; NTU published one genuinely ungrammatical sentence when
`*(malra)` was mis-parsed). Downstream consumers — token counts, LM training,
orthography stats — cannot machine-distinguish these sentences. Inline `?`
also corrupts word counts (2 of Lin's 7 V060 findings).

**Proposal.** Maintainer ruling (POLICIES.md), then: add an optional S-level
attribute (e.g. `grammaticality="ungrammatical|marginal"`) to the XSD; strip
the inline marker from FORM in both cases; `corpus_counts.py` excludes (or
separately counts) marked sentences; a validator rule flags (a) sentence-
initial `*`/`? ` left in any FORM and (b) `source`/`notes` text matching
/ungrammatical|marginal/ on a sentence *without* the attribute.

**Importance.** Medium-high — 4+ corpora in one week, and it directly affects
data consumers (the one published-ungrammatical-sentence incident is the
failure mode).

**Risks.** Schema change: XSD bump, downstream consumers must at minimum
ignore the attribute; counting-rule change shifts token metrics (CI
token-comparison will flag it — announce the discontinuity like the 2026-06
one). Retrofitting existing corpora needs per-corpus source knowledge — do it
at audit/port time, not as a bulk sweep.

### 2.3 Conversion-table remediation + wire the validator into CI (HIGH)

**Problem.** First full run of `validate_conversion_table.py`: 34 tables, 18
effectively blocked (13 reported failures, 5 crashes). These tables generate
the standard tier and PHON for entire languages, so defects here are
multiplied through every corpus of that language. The branch's own spec also
defers case-awareness in the validator (audit findings #5/#7 remain open).
Nothing runs the validator automatically, so tables can silently regress
again after remediation.

**Proposal.** Three steps: (1) remediate the 5 crash-class defects
(dialect-name sync — overlaps with 1.3) and triage the 13 reported failures
against profiles; (2) teach the validator the same case-derivation rule
standardize now uses (closes findings #5/#7); (3) add a CI job (or extend an
existing workflow) that runs the validator over `Orthographies/
ConversionTables/` — report-only until the backlog is zero, then blocking.

**Importance.** High — highest blast radius per defect of anything in this
list.

**Risks.** Fixing tables changes standard-tier/PHON output on next
regeneration → large corpus diffs. Stage per language, diff before commit,
and rely on the token-comparison workflow to spot count shifts. CI job risk:
noisy-until-clean; report-only mode handles that.

### 2.4 Pre-port consistency gate (MEDIUM-HIGH)

**Problem.** Port-blocking problems keep being discovered *ad hoc* late:
language/dialect/glottocode not in `dialects.csv`/ISO map (Latham needed
rows + renames); README/`qc_status.json`/`reproducibility.md` pinning three
*different* FormosanBank commit hashes (Kuo-Sung: audited-PDF hash ≠ README
pin); `Private/` content gitignore hazards (Kuo-Sung); stale
`audio_durations.csv` interplay. Each was caught by a human reading
carefully, not by a check.

**Proposal.** A `QC/validation/validate_port_readiness.py` (or a checklist
step in `port-corpus-in` backed by a script) that mechanically checks:
language/dialect/glottocode triple resolves against `dialects.csv` + ISO
list; every commit-hash-like string in README/sidecars exists in this repo's
history and they all agree; no file under a `Private`-named dir is
git-tracked; source-PDF hash in README matches the file if present; audio
count vs `audio_durations.csv` freshness. Run it in `port-corpus-in` Phase 4
and optionally as CI on `Corpora/` changes.

**Importance.** Medium-high — every port passes this gate, and 3 of the last
5 dev-repo audits hit at least one of these.

**Risks.** Low. Hash-grepping has false positives (any 40-hex string);
scope the regex to context lines mentioning commit/pin/reproduc.

### 2.5 Manual-edits adoption migration (MEDIUM)

**Problem.** The reproducible-hand-edits mechanism exists but only one corpus
uses it. Everywhere else, hand edits are direct XML commits or bespoke
`apply_manual_corrections.py`-style scripts (NTU has a 20-step README of
them). Direct edits don't survive regeneration — which matters *now*,
because the branch's null-glyph/dash normalization implies a pipeline rerun
over published corpora that would collide with or orphan un-captured hand
edits.

**Proposal.** Before the big rerun: for each corpus with known hand edits,
run `capture_manual_edits.py` against the appropriate baseline to convert
them into `CodeAndDocs/manual_edits.xml`; where a bespoke script exists,
either keep it (it's already reproducible) or fold its output into the
manual-edits file — but record which of the two owns each edit. Track
per-corpus status in a small table (claudeplans or POLICIES.md appendix).

**Importance.** Medium, but *sequencing matters*: doing it before the
normalization rerun avoids losing edits; after, it's forensic work.

**Risks.** Medium — capture diffs build output together with hand edits if
the baseline ref is wrong; needs per-corpus care. The mechanism's
sentence-granularity means some edits (splits/merges, attribute-only
changes) can't be expressed — those stay in scripts, which is fine if
recorded.

### 2.6 Apply the new normalizations to the data, deliberately (MEDIUM)

**Problem.** The branch changes tooling only; the specs note no corpus data
is edited. NTU Grammar Sakizaya's 12 `ø` markers, Kanakanavu's nulls, and
every corpus's dash/hyphen variants normalize "on the next cleaning run" —
which currently means whenever someone happens to rerun cleaning, corpus by
corpus, with diffs of very different sizes landing at random times.

**Proposal.** One planned, announced regeneration pass: per corpus, run the
pipeline, review the diff (the 1.2 idempotence tests make second runs
trustworthy), commit with a uniform message. Sequence *after* 2.5 (capture
hand edits first) and ideally after 1.1/1.2 land.

**Importance.** Medium — it's the payoff step for the branch; until it runs,
validators and corpora disagree.

**Risks.** Large diffs; token-count shifts trip CI comparison (expected —
document). Doing it un-sequenced (before 2.5) risks clobbering hand edits.

### 2.7 Single-pass HTML-entity double-encoding fix in clean_xml (LOW-MEDIUM)

**Problem.** NTU had 1,109 TRANSL values containing literal `&lt;`/`&gt;`
entity chains from double escaping. Fixed by hand there; nothing prevents or
detects recurrence in other scrapes.

**Proposal.** A clean_xml rule: decode exactly one level when text content
matches a double-encoded pattern (`&amp;lt;`, `&amp;#`, literal `&lt;` where
no markup is legal), with a validator twin (see 3.4) so it's visible even
when cleaning isn't run.

**Importance.** Low-medium frequency, but trivial cost and unambiguous.

**Risks.** Low — the one hazard is text that *legitimately* discusses
entities (essentially impossible in this corpus domain). Single-level decode
guard prevents over-decoding.

---

## 3. Validator improvements

### 3.1 Grammaticality-consistency rule (pairs with 2.2) (MEDIUM-HIGH)

**Problem/Proposal.** As 2.2: flag sentence-initial `*` or `? ` in any FORM
(SOFT until policy lands, then HARD for unattributed cases), and flag
`source`/`notes` free text asserting ungrammaticality on sentences without
machine-readable marking. Catches both the Lin inconsistency and any future
parser slip of the `*(X)`/`(*X)` kind at publication time rather than at
audit time.

**Importance.** Medium-high — this is the class that already put one
ungrammatical sentence into a published corpus.

**Risks.** Sentence-initial `*` has near-zero false-positive rate in this
domain; the notes-text regex is heuristic — keep that half SOFT.

### 3.2 Rate-based gloss-language integrity rule (MEDIUM-HIGH)

**Problem.** The single largest hand-edit event in repo history — ~16,300
eng/zho *swapped* TRANSL/gloss values in NTU Bunun, plus column-shifted
glosses in Kanakanavu — had no validator signal. Existing per-element checks
can't call a swap; the signal is distributional (a *file* whose `eng` values
are mostly CJK).

**Proposal.** In `validate_glosses.py` or `validate_text.py`: per file × per
`xml:lang` of TRANSL, compute the fraction of values whose script class
(CJK vs Latin) contradicts the declared language; flag files above a
threshold (say 20%) as one SOFT finding ("probable language swap or column
shift"), and small counts as per-element findings. Pure heuristic, no
dictionaries needed.

**Importance.** Medium-high: when it fires it's catching thousand-element
corruption that otherwise ships.

**Risks.** Loanwords, code-switching, and romanized-Chinese glosses cause
noise → rate-based + SOFT keeps it safe. Threshold needs one calibration
pass over published corpora.

### 3.3 Impostor-morpheme / gloss-code-in-FORM detector (MEDIUM)

**Problem.** Two recurring shapes with no validator: (a) M or W FORMs that
are actually gloss codes or annotation debris (`AF`, `PFV`, `L2M-L2M`, IU
numbers, annotator comments) — NTU had impostor words, Kanakanavu had
marker-only morphemes; (b) spurious M tiers where every W has exactly one M
identical to itself (Yedda shipped ~100 such elements; Bunun-Topic-Focus has
51 as a *documented decision*).

**Proposal.** Two SOFT rules in `validate_glosses.py`: FORM-matches-gloss-
code-vocabulary (all-caps token from a fixed Leipzig-style list, or empty
FORM with non-empty TRANSL); and corpus-level "degenerate M tier" (≥95% of
Ws have a single M with identical FORM) reported once per file. The latter
needs a per-corpus waiver mechanism given Bunun's documented policy — a
`notes`-level or config allowlist.

**Importance.** Medium — several corpora, moderate element counts, and it's
exactly what audits currently find by eyeball.

**Risks.** Real words that look like codes (rare; the all-caps + list gate
handles it). The degenerate-M rule *must* have the waiver or it permanently
flags a deliberate policy.

### 3.4 Double-encoding detector (LOW, cheap)

**Problem/Proposal.** Twin of 2.7: SOFT rule flagging literal `&lt;`,
`&amp;#`, `&gt;` sequences in FORM/TRANSL text. One regex, catches the NTU
class at validation time even for corpora that skip cleaning.

**Importance.** Low frequency; near-zero cost. **Risks.** None meaningful.

### 3.5 Marker-aware word counting in V060 (LOW, cheap)

**Problem.** V060 (W count matches word count) counts a leading `? ` or `*`
marker as a word — 2 of the 7 V060 findings in the Lin audit were this false
positive. If 2.2 strips markers into an attribute this disappears; until
then it's noise in every elicited corpus.

**Proposal.** Make V060's tokenizer skip leading marginality markers (and any
future `grammaticality`-attributed sentence entirely).

**Importance.** Low but free, and de-noising validators keeps HARD/SOFT
signal trustworthy.

**Risks.** None.

### 3.6 Null-glyph visibility rule (LOW-MEDIUM)

**Problem.** clean_xml now canonicalizes ø/Ø→∅, but corpora that haven't
been re-cleaned — and dev repos generating XML upstream of clean_xml — still
carry variants, and the whole V069/V120/V123–V125/V140 family silently
returns vacuous passes on them (the "blindness" documented in three audit
reports).

**Proposal.** SOFT rule in `validate_text.py`: any `ø`/`Ø` in a
morpheme-position context (same regex clean_xml uses) → "non-canonical null
glyph; null-propagation rules are unreliable until normalized." This turns
an invisible vacuity into a visible finding.

**Importance.** Low-medium — transitional, but exactly the trap three audits
fell into and had to document by hand.

**Risks.** Foreign words with genuine ø (Danish loans in citations) — the
morpheme-position regex already excludes in-word ø; keep SOFT regardless.

### 3.7 Corpus-type exception for duplicate-sentence HARD (LOW)

**Problem.** `validate_duplicate_sentences` HARD-fails on within-file exact
duplicates; Latham (a comparative wordlist) legitimately attests the same
form twice from different source varieties. Current workaround is
`--no-exit-on-hard`, which also mutes *real* problems.

**Proposal.** A corpus-level flag (config or CLI `--corpus-type lexical`)
downgrading within-file exact-duplicate findings to SOFT for lexical/wordlist
corpora only.

**Importance.** Low (one corpus so far, but every future wordlist corpus
hits it).

**Risks.** Misuse could mask genuine duplication in a lexical corpus —
acceptable given the finding remains visible as SOFT.

---

## 4. Skills improvements

### 4.1 `run-qc-pipeline`: sync with the branch (HIGH)

**Problem.** The skill predates the branch. It doesn't mention:
`standardize_warnings.csv` (should be collected into the Phase 5 summary);
the `standards.csv` registry (a language with a blank entry now *silently by
design* skips standard PHON — operators must know it's intentional);
`validate_conversion_table.py` as a step whenever standardize runs in TSV
mode; the V069/V120/V123–V125/V140 family's meaning (V120 SOFT = "re-
standardize when convenient", not a defect); or that dash canonicalization on
the original tier is expected. An operator following the skill today gets
correct-but-confusing runs.

**Proposal.** Update the skill: pre-flight `standards.csv` check; TSV mode →
run the conversion-table validator and halt on blocking verdicts; collect
warnings CSV; add a short "interpreting null-family findings" note (or cite
POLICIES.md).

**Importance.** High — this skill is the operator's map for every QC run;
staleness here propagates confusion into every audit downstream.

**Risks.** None beyond skill-editing time.

### 4.2 `audit-dev-repo` + briefing: new checks, expected-normalization whitelist (HIGH)

**Problem.** (a) The audit briefing still describes the pre-branch pipeline
order (`clean_xml → standardize → clean_xml`). (b) No instruction to sweep
for `*(X)`/`(*X)` obligatory-vs-forbidden parenthesis notation — the exact
class that published an ungrammatical NTU sentence and that the repo-wide
audit then had to do by hand. (c) No instruction to check null-glyph
variants. (d) Auditors keep re-flagging *expected* normalizations (dashes →
ASCII; curly quotes absent from PHON) as suspected data loss, wasting a
round-trip with the maintainer each time.

**Proposal.** Refresh the briefing's pipeline description; add to the
concern checklist: starred-parens sweep (grep source for `*(` / `(*`, trace
each into FORM), null-glyph grep, README-pinned-hash verification. Add an
"expected normalizations — do not flag" whitelist section citing
POLICIES.md. Add the closing "audit-to-fixture" step (1.5).

**Importance.** High — audits are currently the project's main QA activity;
each gap here is an hour of repeated manual work per audit.

**Risks.** None.

### 4.3 `audit-gloss-scrape`: encode the hard-won tool limits (HIGH)

**Problem.** Ten audits in ten days surfaced operational knowledge that
lives only in memory files and reports: the tool OOMs on big scanned PDFs
(pre-extract to txt); G021=0 is *vacuous* when the PDF text layer drops
label parentheses — G023 region count must be checked first; scans with no
text layer need `--no-source` + visual page reads at 300dpi; `--source`
must always be pinned; starred forms need a manual `*( )`/`(* )` sweep; G004
false-positives on stacked/double infixes (Puyuma); G023 has no quantitative
proceed/stop gate; G006 firing means the V120+ family results downstream are
untrustworthy until normalization.

**Proposal.** Fold all of the above into the SKILL.md (and fix G004's
stacked-infix handling in `audit_gloss_scrape.py` itself — that one is a
code fix, not prose). Add a G023 heuristic gate (e.g. <70% region match →
recommend manual spot-check / `--no-source`).

**Importance.** High — this skill will run on every future scrape; today a
fresh session re-derives these limits from scratch or falls into them.

**Risks.** None for the prose; the G004 fix needs its own tests (stacked
infixes have legitimate one-at-a-time analyses).

### 4.4 `port-corpus-in`: pre-port gate + conversion-table check (MEDIUM-HIGH)

**Problem.** The skill doesn't verify README-pinned commit hashes (three
mutually inconsistent hashes shipped in one dev repo), doesn't run
`validate_conversion_table.py` when the corpus standardizes via TSV, lumps
the two distinct `Private/` leak layers (content hash vs basename collision)
into one message, and its audio-stats step doesn't first check whether
`audio_durations.csv` already has fresh entries.

**Proposal.** Wire in the 2.4 port-readiness script (or its checks inline);
distinguish the two leak severities in the summary; add the
conversion-table validation step; pre-check `audio_durations.csv`.

**Importance.** Medium-high — every publication passes through this skill.

**Risks.** None.

### 4.5 `setup-new-dev-repo`: small forward-looking additions (LOW)

**Problem/Proposal.** Add: a `standards.csv` pre-check ("your language has
no designated standard orthography — standard-tier PHON will be skipped");
a pointer to the manual-edits workflow in the next-steps section; a README
template slot for documenting any conversion table used; note that
clean_xml will canonicalize null glyphs and dashes so scrapers needn't.

**Importance.** Low (new repos only), but nearly free.

**Risks.** None.

---

## Suggested ordering

1. **0.1 POLICIES.md** + the pending rulings (apostrophe, tilde,
   grammaticality, infix hosts) — unblocks several items below.
2. **1.1 / 1.2** integration + idempotence tests — prerequisite confidence
   for any data regeneration.
3. **4.1–4.3** skill refreshes — cheap, immediately reduce audit friction.
4. **2.5 → 2.6** capture hand edits, then the planned regeneration pass.
5. **2.3 / 1.3** conversion-table remediation + registry consistency tests.
6. **2.2 + 3.1** grammaticality schema work (after the ruling).
7. Remaining validators (3.2–3.7) and 2.4/4.4 port gate as capacity allows.
