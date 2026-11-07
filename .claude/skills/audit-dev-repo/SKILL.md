---
name: audit-dev-repo
description: Guided audit of an assistant-built corpus dev repo (../Formosan-<Name>/) before QC + porting. Reads the assistant's preprocessing, maps it onto our current pipeline, runs our validators on its output, and diffs its original tier against the source for dropped characters/punctuation and ungrammatical artifacts — pausing for the maintainer's judgment, and publishing review artifacts when a question class has more cases than a chat message can carry. Use when starting to review a new dev repo's preprocessing.
---

# audit-dev-repo

Guided, one-repo-at-a-time audit of a corpus dev repo's preprocessing against the
current FormosanBank pipeline. **Pauses for human judgment** — do not draw
conclusions or write the report without the maintainer signing off on each concern.

## Step 0 — Get oriented (REQUIRED, before touching the repo)

Read, in this order, and do not skip:
1. `claudeplans/2026-06-09-dev-repo-audit-briefing.md` — the objectives, our
   conventions, the current pipeline, and the **concern → tool map**. This is the
   spine of the audit.
2. `FormosanBank/CLAUDE.md` (auto-loaded) and `QC/README.md` — conventions + pipeline order.
3. `POLICIES.md` — at minimum the **Highlights** table and sections **5 (Rights)**
   and **6 (Development)**, which govern step 4b. Cite POL ids rather than
   re-deciding settled questions; the file moves faster than this skill does, so
   read it rather than trusting the summaries here.
4. `claudeplans/sweep-qa-decision-log.md` — newest-first, 20,000+ lines. Read
   every `⏳ OPEN` heading (`grep -n '⏳ OPEN'`) and every entry that names this
   corpus or PR (`grep -n '<Name>'`); its 2026-08 orientation sections are
   stale and 17,000 lines down. Prior rulings and prior findings on the same
   target are binding context, and re-raising a settled point wastes a
   maintainer round-trip. Where your evidence **contradicts** a logged finding,
   say so explicitly and show the check.

**Re-read `POLICIES.md` before going on.** If any instruction in this skill contradicts a policy, stop and show the maintainer both texts before continuing; the policies file moves faster than this skill.

**Audit scope: anything that touches the data.** Every transformation the assistant
applies should make sense and look correct — scrutinize each one, not just a fixed
checklist. The maintainer has **four highlighted concerns** they especially want
checked, but they are priorities, **not the full scope**:
(a) eliminated orthography characters, (b) suppressed punctuation,
(c) other convention breaks, (d) source-extraction artifacts (e.g. ungrammatical
sentences left in). Beyond these, flag any character-, punctuation-, or
structure-altering step that could distort the data. Keep the assistant's profile in mind:
strong coder, does not read the languages, churn-prone — so trust nothing without
evidence.

## Step 0b — Profile the corpus and load its checklists

One audit skill, one lifecycle, with per-shape checklist files: the corpora do
not sort into clean types (ePark is parallel, audio and word-glossed; NTU is
glossed text and audio; Song is grammar examples plus a dictionary appendix),
and most recurring problems cut across types. Profile first, then load what
applies — `checklists/README.md` has the table:

```bash
<python> - <<'EOF'
import glob, collections
from xml.etree import ElementTree as ET
tiers = collections.Counter(); files = 0
for f in glob.glob("<XML dir>/**/*.xml", recursive=True):
    files += 1; root = ET.parse(f).getroot()
    for tag in ("S", "W", "M", "TRANSL", "AUDIO", "PHON"): tiers[tag] += sum(1 for _ in root.iter(tag))
print(files, "files;", dict(tiers))
EOF
ls Corpora/<Name>/ 2>/dev/null | head -3          # re-port if it exists on main
```

Then read `checklists/every-corpus.md` and, by the profile, `dictionary.md`,
`glossed.md` (W or M present, or interlinear source), `text-with-translation.md`
(S + TRANSL, no W/M), `audio.md` (AUDIO, a download script, or recordings),
`re-port.md` (the corpus exists on main). Each item says what to look for, how
to check, what counts as acceptable, and the case in the bank it comes from.
Report, per loaded checklist, which items you ran and what each found; "not
applicable" is an answer, "not run" is not.

## Inputs (gather via AskUserQuestion if missing)

- `repo_path` — **either** the sibling dev repo (`../Formosan-<Name>/`), run from
  `FormosanBank` with the dev repo added (`--add-dir`), **or** a port / re-port
  **pull request** against this repo. Dev repos are permanently private (POL-048)
  and are frequently not on disk at all, so the PR is often the only artifact
  there is; the audit works the same either way, over `Corpora/<Name>/CodeAndDocs/`
  instead of the dev repo's scripts.
  - For a PR target: fetch it (`git fetch origin refs/pull/<N>/head:refs/audit/pr/<N>`)
    and check it out in **its own worktree** — the repo checkout is shared with
    other sessions, so never audit on the shared working tree's branch. A sparse
    checkout (`git sparse-checkout set Corpora/<Name> QC tests statistics`) is much
    faster than a full one.
  - Establish the **merge base**, not just `main`'s tip, and diff both sides. The
    predecessor is what makes id changes, removals and rights changes legible.
- `language` — the ISO 639-3 / language name, to pick the right
  `QC/validation/reference/<Language>/` and `Orthographies/Ortho113/<Language>.tsv`.
- `xml_subdir` — where the built XML lives (auto-detect `XML/`, `Final_XML/`, root `*.xml`).

## Review artifacts: how to ask for a ruling at scale

Every ▣ below is a place where the maintainer has to look at data and decide.
Doing that in chat works for three cases and collapses at thirty: the findings
scroll away, the answers arrive interleaved, and nobody can tell later which
were settled. Publish a **review artifact** instead — one page per question
class, with a card per case and a verdict button and note box on each. This is
what turned the Blust Thao audit from a chat into a process; it took an entry
worklist from 445 findings to 0 over 40 rounds.

**The shape that works.**

- **One page per class of question**, not one page for everything. "Every slash
  that still carries a shared tail", "every headword form with lexicographic
  notation", "the entry worklist". A page whose cards all ask the same question
  gets answered in one sitting; a mixed page does not.
- **A card shows the evidence, not a summary of it.** The printed source string,
  the English, what the build currently produces, and what the obvious
  alternative would produce. The maintainer should never have to open the PDF to
  answer an easy card.
- **Verdict buttons are the page's vocabulary.** Three or four, phrased as
  answers rather than judgements: *"shared tail is right"*, *"slash splits the
  whole thing"*, *"book is like this"*, *"needs the page"*. Add a free-text box
  for the ones that do not fit — most of the general rules in the Thao audit came
  out of those boxes, not the buttons.
- **Persist to the artifact `db` capability**, with `localStorage` as a fallback,
  so answers survive the tab closing and can be read back with `read_db`.
- **Regenerate the page from the build, not from a saved list.** A card then
  disappears the moment a rule or a ruling settles it, and the page's own count
  is the progress bar. Carry the verdicts already given inside the generator so
  a ruled card stays gone even if the build still produces it.

**Consuming answers.** Read the collection with `read_db`, and for each answer
ask *"is this one case, or a rule?"* — the maintainer's notes are usually the
latter. `cf. introduces a note` came from a single card and fixed eight
definitions. Prefer a rule that reproduces every ruling to a per-case fix, and
**verify that it does**: assert your rule against the whole ruled set before
adopting it, and report the count.

**Record every ruling in the corpus, with the words it was given in.** Two files,
both read by code so the ruling is reproducible and not just remembered:
`entry-rulings.json` (findings the maintainer ruled are facts about the printed
source, so the validator stops reporting them) and `curated-readings.json`
(readings no rule can derive). A ruling a rule later derives moves to
`settled-readings.json` and is kept as a regression test rather than deleted —
see `Corpora/Blust-Thao-Dictionary/README.md` for the worked version.

⚠️ **Card ids must be storable.** The verdict store accepts only
`[A-Za-z0-9_-.~:@+]` as a document id. Headwords routinely are not: `dahda(h)`
has brackets, `maka–sia–siaq` has en dashes. A card keyed on one of those has
every save rejected while the `localStorage` fallback goes on reporting *saved*,
so the maintainer rules it and nothing arrives. Sanitise the id for the store and
keep the readable one for `localStorage` — two attributes, `data-db-id` and
`data-id`. This cost three rulings before it was found.

⚠️ **Publish, do not describe.** The maintainer works in a container and cannot
open files in your worktree. An artifact URL is the deliverable; "see
`scratchpad/foo.html`" is not.

## Procedure (guided — pause at each ▣)

### 1. Read the preprocessing
Read the repo `README` and every scrape/parse/build script. Produce a plain-language
summary of the transformations it applies and their order — flag every step that
**deletes or substitutes characters** or **drops/normalizes punctuation**.
▣ Present the summary; confirm your read with the maintainer before proceeding.

### 2. Map each transformation to our pipeline
For each step, classify: (i) our pipeline already does this (and how it differs),
(ii) no-op for us, or (iii) conflicts with a convention (cite which). Pay special
attention to anything touching the **original** tier (must stay faithful) and W-tier
segmentation markers (`-`, `=`, `<…>` must survive).
**What counts as acceptable** (maintainer, 2026-10-17): a policy with a test is
enforced by the test — HARD is HARD; SOFT is raised to the maintainer with a
description and a categorisation of where the warnings come from. A policy
with no test is a guideline: the audit proposes, the maintainer decides; the
audit never acts on it alone.

**Rulings since 2026-10 that a glossed corpus must be mapped against** (cite the
POL id; read the entry rather than this summary):
- POL-057 (2026-10-17): a W with exactly one M asserts the word is monomorphemic;
  build code must never insert an M so that every W has one. No validator checks
  it (V144 SOFT / V145 HARD cover only the degenerate cases) — read the builder
  for where Ms are created, and count single-M words.
- POL-060 (2026-10-14): words the source glosses as one unit are one W.
- POL-061 (2026-10-15): an unglossed word is glossed `?`. The 2026-09-04
  HundredPaiwanStories ruling went the other way (no `?` gloss, an absent TRANSL);
  surface both to the maintainer rather than choosing.
- POL-028 as amended 2026-10-15: a segmentation difference makes a separate S
  only if it is glossed and the glossing differs; otherwise `ver="alt"`.
- POL-059: published layout is `XML/` plus a language-named directory.

▣ Present the mapping table; get the maintainer's reaction.

### 3. Run our validators on the XML output
Either invoke the `run-qc-pipeline` skill, or run the four validators directly:
`validate_xml.py`, `validate_text.py`, `validate_glosses.py` (if W/M present),
and `validate_orthography.py --quiet` + `validate_vocabulary.py --quiet` (after
`orthography_extract.py --kindOf original`; both always exit 0 — quote their
`SUMMARY orthography | …` / `SUMMARY vocabulary | …` lines, which name the
characters and words on each side only; `--quiet` leaves only the group
header, metrics, WARNING and SUMMARY lines, the full output is for a human
at the terminal). Then `QC/validation/declared_vs_detected.py
--xml <XML> --generate-xml <generate_xml.sh>`: `TEXT/@dialect` against the dialect
detector and the declared source orthography against the orthography detector
(original tier; standard tier against Ortho113). Quote its tables; every row
marked MISMATCH is a question for the maintainer, not a finding to fix.
Read the per-rule summary + the findings CSV(s). Organize hits by concern (a–d)
using the briefing's map (e.g. V129/V137–V139 → (d); V110–V116/V126/V133/V134 → (b);
orthography deltas → (a); schema/V063/V068/V141 → (c)).
▣ Present findings grouped by concern, with the CSV path(s). Past a dozen
cases in any one class, publish a review artifact for it rather than listing them.

### 4. Diff the output against the source (concerns a, b, d)
Sample sentences (use `sample_sentences.py` or pick representative ids). For each,
compare the `FORM[@kindOf="original"]` to the **actual original text** (the printed
page image / true source — *not* merely the raw scrape). The original tier is meant
to match the real source, so OCR/scrape-error corrections toward it are **expected
and legitimate**; the check is fidelity to the true text, not "did it change the
scrape?":
- (a) Did any orthographic letter disappear vs the *source*? (Check the char
  inventory vs `reference/<Language>/` and vs the source. Watch curly apostrophes →
  loss.) A `u`→`ʉ`-type correction that matches the printed page is good — verify it
  actually matches the page, don't flag it as a violation.
- (b) Did punctuation/segmentation the *source has* vanish from the original tier?
  (Punctuation *normalization* that preserves spelling is fine; the bug is source
  punctuation/segmentation silently disappearing.)
- (d) Are there sentence-initial `*` (ungrammatical — should have been excluded),
  footnote digit leaks, or out-of-language runs?
- (d) **Starred-parenthesis sweep (POL-017).** Grep the *source* (and extraction
  ledgers) for `*(` and `(*`: `*(X)` = X obligatory (X must be in FORM,
  unstarred); `(*X)` = X forbidden (X must NOT be in FORM). Trace every hit into
  the XML and flag any script that treats the two identically — that inversion
  published an ungrammatical sentence in NTU Rukai (`*(malra)`).
- (a) **Null-glyph check (POL-012).** Grep the XML for `ø`/`Ø` in morpheme
  position: preprocessing that emits non-canonical null glyphs leaves the whole
  V069/V120/V123–V125/V140 family vacuously blind until `clean_xml` normalizes
  them to `∅`. Flag as "normalize at intake", not as data loss.

**Expected normalizations — do not flag as data loss** (cite the POLICIES.md
entry instead): dash/hyphen look-alikes → ASCII `-` (POL-011); typographic
apostrophes/quotes → ASCII `'`/`"` in Formosan text (POL-010 — including a dev
repo's `’`→`'` in its build scripts); null glyphs `ø`/`Ø` → `∅` in morpheme
position (POL-012); curly quotes absent from PHON (PHON drops unmapped
punctuation, POL-003). Re-flagging these wastes a maintainer round-trip.

▣ Present concrete before/after samples per concern; get the maintainer's call on
each class (real bug vs acceptable vs needs source check). This is the step that
most often needs a review artifact: the samples are per-record and the answers
are per-record.

### 4b. Check the build and the rights against sections 5–6 of POLICIES.md
Concerns (a)–(d) are about the data. These are about **the code that produced it
and the licence it ships under** — the questions a port PR is now failed on at
merge. Run them whenever the target is a corpus about to be published or a
re-port PR; skip them only for a dev repo too early to have a build shape yet.

| Check | Rule | How |
|---|---|---|
| Rebuilds from a FormosanBank checkout alone | POL-048 | Read every build entry point for `Private/`, a second clone, a pinned dev-repo commit, or `FORMOSANBANK_*`/`VALIDATOR_ROOT` env vars. **Then actually run it** from a clean checkout of the PR — a declared input can be missing from the tree even when the script is honest about needing it. |
| One entry point, canonical order | POL-047 | `CodeAndDocs/generate_xml.sh` running generate → manual edits → clean → standardize → add_phonology. Deviations are legitimate but must be **stated in the README**; an unexplained departure is a finding on its own. Validators must **not** run inside the build ("build only"). Re-running on a clean checkout must leave `git status` empty. |
| Shared tools, not forks | POL-046 | Corpus-local reimplementations of cleaning/standardizing/phonology are a finding: fold into the shared tool, or record in the README why it cannot serve. Initial parsing (`generate_xml.py`) is the standing exception. |
| Build provenance | POL-052 | `CodeAndDocs/provenance.json` exists with a 40-char `formosanbank_commit`; the README **links** it rather than repeating the SHA in prose. A rebuild that leaves the old commit is a stale record. Corpora predating this are in `provenance_pending.txt`, a list that only shrinks. |
| Licence value | POL-042 | `TEXT/@copyright` is an **exact** value from `rights_vocabulary.csv`. No validator rule enforces this yet (V160/V161 are planned but absent from the rule set) — check the values against the vocabulary directly. |
| Licence documentation | POL-044 | README `## Rights` section with `**License:**` and `**Rights source:** <grantor>, <YYYY-MM-DD>; evidence: ask maintainer`. Any licence change fails `rights-comparison.yaml` and needs a deliberate maintainer override — say so in the report rather than treating red CI as a defect. |
| Never downgrade from absence | POL-043 | A rights claim replaced by bespoke prose because the reviewer could not find the evidence is a **finding against the PR**, not against the old claim. Escalate to the maintainer, who holds the correspondence. |
| Published ids | POL-037 | Diff the published id set against the predecessor. Retirements, renumberings and reused-id reassignments are breaking changes to **announce**, not cleanups — check each is listed with a reason. |
| Removals disclosed | POL-051 | Count removed S/W/M/TRANSL/AUDIO/PHON against the merge base. Silence is the finding, not the deletion. |
| Reversals explicit | POL-050 | A change that undoes something previously merged must cite the commit or POL entry it supersedes. Re-adding a standard tier a merged ruling removed is the recurring case. |
| PR scope | POL-049 | A corpus PR does not change `QC/`, `tests/`, `POLICIES.md`, root registries, `requirements.txt`, or `.github/workflows/`. Those belong in their own PR, merged first. |
| W-tier completeness | POL-041 | No W tier anywhere is normal and never a finding; *some* sentences segmented and others not is an incomplete pass (V148, SOFT). |
| Decisions as data, not code | POL-039 | Record-level decisions (overrides, corrections, exclusions, review verdicts) live in a content-gated table — stable record id + the input text expected + reason + date + the maintainer's words, refused when the input drifts (Safolu `safolu_source_overrides.json`, Seediq-Chang `review_corrections.tsv`) — not as Python literals; `lint_hidden_tables.py --corpus` lists the files to read. `manual_edits.xml` keys on positional ids and cannot carry a standard-tier edit. |
| Content delta (re-port) | POL-037/051 | `content_delta.py --base <merge base> --head Corpora --corpus <Name>`; every red line traced on the audit artifact (`checklists/re-port.md` item 1) or flagged "no approved decision found". |

▣ Present the conformance table with a verdict per row; get the maintainer's call
on which gaps block the merge and which are recorded and carried.

### 5. Record the report
Link every review artifact you published, with its final count, so the report says
what was asked as well as what was answered. Only after sign-off, write `claudeplans/audit-<Repo>.md`: what the assistant did, findings
by concern (a–d) with evidence, the pipeline mapping, and recommended remediation
(which conflicts must be fixed in the reproduction before porting).

### 6. Regression fixtures (when a finding leads to a FormosanBank code fix)
If remediation lands in FormosanBank code (a cleaner rule, a validator, a
pipeline script — as opposed to the dev repo's own build scripts), the fix is
not complete until a minimal reproduction fixture and one test exist under
`tests/fixtures/audit_regressions/` (see its README for naming). Add creating
them to the remediation list.

## Notes
- This is an audit, not a fix: do not modify the dev repo or `Corpora/` here. Remediation
  belongs in the reproduction scripts (per the dev-repo workflow).
- Evidence over assertion: every finding cites file + id + a source/XML sample.

## Data files change only via code (POL-038)

Never modify XML or raw scrape files by hand or ad hoc — only via committed code (pipeline scripts, `manual_edits.xml` via the capture/apply tooling, or a one-off script committed to `CodeAndDocs/`). This includes POL-035 snapshots: fix snapshot defects with a committed script, never a direct edit. A non-code edit is unreproducible and is destroyed on regeneration.
