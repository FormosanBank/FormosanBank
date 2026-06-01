# E: Claude Code project tooling — design spec

**Date:** 2026-05-27
**Status:** Draft for review
**Supersedes:** the E section in [`2026-05-27-roadmap.md`](2026-05-27-roadmap.md) (the roadmap entry stays as the one-line index; this is the detail).

## Scope

Phase 0 (build now) is **three items**:

1. **Hook:** block writes under `statistics/`
2. **Skill:** `run-qc-pipeline` — smart orchestrator with a human-judgment pause
3. **Skill:** `port-corpus-in` — interactive guided checklist

Everything else from the original E sketch goes to the [deferred backlog](#deferred-backlog) with explicit trigger conditions for when to build it.

## Item 1 — Hook: block writes under `statistics/`

### Goal

Make CLAUDE.md's "do not hand-edit those two files" rule mechanically enforced. User's decision: block any write under `statistics/`, not just the two specific files — slightly stricter than the literal CLAUDE.md text, but it also prevents accidental edits to future statistics files.

### Design

**Hook type:** `PreToolUse` matcher on `Edit|Write|MultiEdit|NotebookEdit`.

**Implementation:** small Python script that reads the tool-call JSON from stdin, checks whether `tool_input.file_path` resolves inside `<repo>/statistics/`, exits with code 2 and an explanatory message if so.

**Files added:**
- `.claude/hooks/block-statistics-edits.py` (the script)
- `.claude/settings.local.json` — new top-level `"hooks"` key registering the hook

**Script behavior:**
- Parse stdin as JSON; extract `tool_name` and `tool_input.file_path` (and `tool_input.notebook_path` for `NotebookEdit`).
- Resolve `file_path` to absolute. Compare against the absolute path of `<repo>/statistics/`.
- If the file is under `statistics/`: emit message to stderr and exit 2. Message:
  > Blocked: `statistics/` is auto-managed by `.github/workflows/corpus-metrics.yaml`. Don't hand-edit. To change what gets committed, modify the workflow or the upstream data; to change a chart, modify the script that generates it (`QC/corpus_metrics.py` etc.). If you have a genuine reason to override, disable this hook in `.claude/settings.local.json`.
- Otherwise exit 0.

**Settings excerpt** (added to `.claude/settings.local.json`):

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "Edit|Write|MultiEdit|NotebookEdit",
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PROJECT_DIR}/.claude/hooks/block-statistics-edits.py\""
        }
      ]
    }
  ]
}
```

(Need to verify whether `CLAUDE_PROJECT_DIR` is the right env var — see [open questions](#open-questions--known-limitations).)

### Out of scope

- Blocking writes from the CI workflow itself (the workflow runs in a clean checkout where this hook doesn't fire — fine).
- Blocking *all* hand-editing under `statistics/` outside of Claude Code (user's git workflow isn't gated by Claude's hooks; this is a defense-in-depth measure, not a security boundary).

---

## Item 2 — Skill: `run-qc-pipeline`

### Goal

Make running the canonical QC sequence on a development corpus a single skill invocation, with a single human-judgment pause at orthography detection and a per-corpus README-style summary at the end.

### Operating context (important)

This skill **runs in a `Formosan-<CORPUS>/` development repo**, not in the published `FormosanBank/Corpora/<Name>/` tree. The development repo is where QC happens *before* a corpus is ready to port in. The skill assumes:
- The dev repo contains XML files (location varies — common patterns: `Final_XML/`, `XML/`, root-level `*.xml`).
- The QC scripts live in `FormosanBank/QC/` and are invoked from the dev repo's working directory.
- Output goes to a logs directory inside the dev repo (or wherever the user specifies).

### Design

**File:** `.claude/skills/run-qc-pipeline.md` with YAML frontmatter and a body that's a recipe I follow.

**Inputs the skill accepts:**
- `corpus_path` (default: current working directory) — the dev repo root.
- `output_dir` (default: `<corpus_path>/qc-output/<UTC-timestamp>/`).
- `xml_subdir` (default: auto-detect from common patterns).

**Pre-checks (run before any phase):**
- `.venv` and key deps available (largely covered by item 4's SessionStart hook, but verify here too).
- XML location resolves.
- **`<corpus_path>/README.md` exists.** If not, scaffold a minimal one (corpus name, primary-language placeholder, source-description placeholder). The scaffold is intentionally bare — Phase 2 needs somewhere to persist its answer, but the skill shouldn't silently invent content the user didn't ask for.

**Recipe phases:**

**Phase 1 — Clean.** Run `clean_xml.py --corpora_path <xml_path>`. Capture the log. No decisions needed.

**Phase 2 — Orthography detection (HUMAN PAUSE).**
- If `<corpus_path>/README.md` already records an orthography under the stable section heading (see "persist" bullet below), present it and short-circuit: *"README says <X> — still right? [Confirm / Override / Re-run detector]"*. Skip to Phase 3 on confirm.
- Otherwise, run `orthography_detector.py` and capture its output.
- Read the output. The current detector "does not give an easy answer" (per user) — typically presents evidence (character frequencies, candidate orthography matches, etc.) that requires interpretation.
- Use `AskUserQuestion` to present the detector's findings and ask: *"Based on the detector output above, what's the original orthography of this corpus?"* with options derived from what the detector suggests plus a free-text fallback.
- Store the user's answer for Phase 3.
- **Persist the answer to `<corpus_path>/README.md`** under a stable section heading (e.g. `## Orthography`). This makes the human pause one-time per corpus rather than every-run, and doubles as user-facing documentation about what orthography the originals are in. The same README is carried into `Corpora/<Name>/` by `port-corpus-in`, so this fact propagates to published end-users.

**Phase 3 — Standardize.** Based on Phase 2 answer:
- If user said "Ortho113": run `standardize.py --copy --corpora_path <xml_path>`.
- Otherwise: run `standardize.py --tsv_path <appropriate mapping> --target_column standard --corpora_path <xml_path>`. The TSV mapping path depends on the source orthography; the skill should resolve this from a convention (TBD — see open questions).

**Phase 4 — Phonology.** Run `add_phonology.py` to add `<PHON>` tiers. No decisions needed.

> **Caveat baked into the skill:** the DTD at `QC/validation/xml_template.dtd` currently has no `<PHON>` element, so running `validate_xml.py` *after* this phase will fail validation purely because of the schema/code drift. The skill should note this in its summary and not treat it as a corpus problem. Resolving this is B's reconciliation work, not this skill's.

**Phase 5 — Validate.** Two tiers:

*Hard-gate validators* (run in order; abort the recipe on failure — failure here means the corpus is actually broken, or downstream extraction has nothing to work with):
- `validate_xml.py by_path --path <xml_path>` — DTD conformance.
  - **Open issue:** Phase 4's `add_phonology.py` introduces `<PHON>` elements not in the DTD, guaranteeing failure if `validate_xml` runs after Phase 4. Options: (a) move `validate_xml` to a sub-phase between Phase 1 (clean) and Phase 4 (add_phonology) so it gates on a DTD-conformant corpus; (b) make the gate `<PHON>`-aware (treat "PHON not allowed" failures as a known schema drift, gate only on other failures). Decision deferred — see open questions.
- `validate_punct.py by_path --path <xml_path>` — punctuation conformance.
- `orthography_extract.py --kindOf standard --by_dialect true --corpora_path <xml_path>` — produces the extract logs that the soft validators consume. If this fails, nothing downstream runs anyway.

*Soft validators* (informational; capture findings, do not abort):
- `validate_orthography.py` (reads Phase-5 extract output, compares against reference)
- `validate_vocabulary.py` (reads Phase-5 extract output, compares against reference)
- `validate_glosses.py` — *only* if any XML file has `<W>` or `<M>` elements (detect by simple grep before deciding to run).

Capture each output to its own log under `output_dir`. A hard-gate failure surfaces a clear error in the Phase 6 summary plus the truncated validator log; subsequent phases are skipped.

**Phase 6 — Summary.** Produce a markdown summary at `<output_dir>/qc-summary.md`. Format follows existing per-corpus README structure (open question: which existing README is the model). Sections to include at minimum:
- Corpus name, dev repo path, timestamp
- Orthography determined in Phase 2 (with the evidence the user used)
- Counts: texts, sentences, words (if W-tier), morphemes (if M-tier), per language/dialect
- Hard-gate findings (validate_xml DTD pass/fail; punctuation issues; gloss-count mismatches)
- Soft-check numbers (orthography/vocabulary similarity to reference) with a note about thresholds being uncalibrated (B Phase B4 work)
- Anything unusual surfaced in any phase
- "Ready to port?" verdict — best-effort heuristic with explicit caveats

The summary is the artifact the human reads to decide "good enough to port to FormosanBank/Corpora/?"

### What the skill is NOT

- Not a fully-automated pipeline. The Phase 2 pause is the load-bearing human input; the Phase 5 "good enough?" judgment is also human.
- Not opinionated about *fixing* discovered problems. It reports; the user (or me, in a follow-up) decides what to do.
- Not coupled to porting. It can be run repeatedly on a dev repo during development, completely separate from any port-in operation.

---

## Item 3 — Skill: `port-corpus-in`

### Goal

Move a QC'd corpus from its dev repo into `FormosanBank/Corpora/<Name>/` with the standard layout, interactively, surfacing decisions rather than guessing.

### Operating context

- Runs from anywhere; takes a source dev repo path and a destination corpus name.
- Target is *always* `<FormosanBank>/Corpora/<Name>/`.
- The user explicitly forbade modifications to associated repos during the roadmap-planning task. For port-in operations, modifications to the **FormosanBank** repo are the whole point. Modifications to the source dev repo should be limited to "if explicitly needed for the port" and confirmed before execution.

### Design

**File:** `.claude/skills/port-corpus-in.md` with frontmatter and recipe body.

**Inputs:**
- `source_path` — path to dev repo (e.g., `~/Documents/Projects/Formosan/Formosan-Nowbucyang-Truku-Thesis/`).
- `corpus_name` — name for the published version (default: derive from source by stripping `Formosan-` prefix; user can override).
- `assume_qc_passed` (default: false) — if false, skill refuses to proceed if no recent QC summary is found.

**Recipe phases:**

**Phase 1 — Assess source layout.** Read the dev repo top-level:
- Is there a README? (2/8 unpublished repos don't have one.)
- What's the XML location? Common patterns: `XML/`, `Final_XML/`, root-level `*.xml`, `xml/<chapter>.xml`. Detect; if ambiguous, ask.
- Are there scripts at the root? They likely belong in `CodeAndDocs/`.
- Are there scratch dirs (`data/`, `raw_data/`, `Original/`, `img-by-page/`, `text-by-page/`, `pivot_corpora_final/`)? They likely get dropped.
- Is the XML monolithic (a single file with many `<TEXT>`/`<S>`)? If yes, recommend invoking the deferred `split-monolithic-xml` skill first; do not proceed without confirmation.
- Is there evidence of recent QC (a `qc-output/` directory or similar)? If `assume_qc_passed` is false and there's no QC evidence, surface and either ask or refuse.

**Phase 2 — Present plan.** Build a concrete file-by-file plan and present it via `AskUserQuestion` for sign-off:
- Files/dirs to copy and where (e.g., `Final_XML/Truku/* → Corpora/<Name>/XML/`)
- Files/dirs to drop (e.g., `data/`, `__pycache__/`, `*.log`)
- README handling: **copy-as-is is the default if the dev repo has one**. `run-qc-pipeline` writes the corpus's documented orthography into a stable section of the dev-repo README, and that record should propagate to `Corpora/<Name>/` unchanged. Generate-from-template is the fallback for corpora with no README at all (mostly older imports).
- Whether to copy or move scripts (default: copy, leave dev repo intact)
- Whether to include `download_audio_data.sh` (only if the corpus has audio)

User can: approve, request specific changes, or abort.

**Phase 3 — Execute.** Apply the approved plan:
- `mkdir -p Corpora/<Name>/{XML,CodeAndDocs}`
- Copy XML files into `XML/` with any path adjustments from the plan.
- Copy scripts into `CodeAndDocs/`.
- Generate README from template if needed (template lives at `.claude/skills/port-corpus-in/README.template.md`).
- Drop nothing from the source dev repo unless explicitly approved.

**Phase 4 — Validate after port.** Run at minimum:
- `validate_xml.py by_path --path Corpora/<Name>/XML/` to confirm DTD conformance.
- A quick spot-check (file count, total size) compared to the source.

Report any discrepancies, but do not auto-fix.

**Phase 5 — Summary.** Print a summary of what was created, what was dropped, and any open items (e.g., "README is a stub — please flesh out", "DTD validation failed on N files — investigate before opening PR").

### Decision points the skill must surface (not guess)

- Monolithic XML splitting (if applicable)
- Ambiguous source layouts (multiple plausible XML locations)
- README handling when source has none
- Whether to copy or move source files
- Whether the dev repo has QC evidence sufficient to proceed

### What the skill is NOT

- Not a fix-it tool for problems found by QC. If QC says the corpus isn't ready, the skill defers to the user; it doesn't try to clean things up.
- Not a git operation. It creates files in the working tree; the user commits.

---

## Item 4 — Hook: SessionStart `.venv` check

### Goal

Catch the "wrong env" pitfall early: when Claude (or the user) starts a session in a FormosanBank-ecosystem repo, the hook verifies `.venv` exists and has the expected deps installed. If something is off, it warns immediately so subsequent `python ...` invocations don't fail confusingly. Defensive backstop that complements item 5 (which prevents the problem up front by setting up `.venv` correctly during dev-repo creation).

### Design

**Hook type:** `SessionStart`.

**Implementation:** Python script that:
1. Locates project root via `${CLAUDE_PROJECT_DIR}` (or falls back to `pwd`).
2. Checks `<root>/.venv/bin/python3` exists. If not: emit a single-line warning naming the project and the missing path.
3. If `.venv/bin/python3` exists: invoke it to `import lxml, pandas, regex, lxml.etree` (the load-bearing deps from `requirements.txt`). On `ImportError`: emit a single-line warning naming the missing module.
4. If everything OK: silent (no notification noise).

Hook stdout becomes session context I see; warnings prevent me from blindly running python commands that would fail confusingly.

**Files added:**
- `.claude/hooks/check-venv.py` (the script)
- New entry in `.claude/settings.local.json` `"hooks"` key for SessionStart

**Settings excerpt:**

```json
"SessionStart": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "python3 \"${CLAUDE_PROJECT_DIR}/.claude/hooks/check-venv.py\""
      }
    ]
  }
]
```

**Where it gets installed:**
- FormosanBank itself: via this spec's implementation (manual setup).
- New dev repos: installed automatically by item 5 (`setup-new-dev-repo`) as part of its scaffold step.
- Existing dev repos: added on first `run-qc-pipeline` or `port-corpus-in` invocation against them (skill detects missing hook and offers to install it).

### Out of scope

- Auto-fixing missing `.venv` (that's item 5's job).
- Version pinning checks ("right version of lxml installed?") — just "does it import?".
- Network egress checks (e.g., huggingface CLI reachability) — out of scope for the basic safety hook.

---

## Item 5 — Skill: `setup-new-dev-repo`

### Goal

Bootstrap a new `Formosan-<CORPUS>/` development repo with the directory structure, Python environment, gitignore, README scaffold, and Claude Code safety rails (item 4's hook) needed for QC work. Pairs with item 4: this prevents the missing-venv pitfall up front; item 4 catches the case where setup didn't happen.

### Operating context

- Runs from anywhere; creates a new directory at `<parent_dir>/Formosan-<corpus_name>/` (default parent: `~/Documents/Projects/Formosan/`).
- Does NOT clone or modify FormosanBank itself; assumes FormosanBank is already cloned as a sibling, since the recipe reads its `requirements.txt`.
- Refuses to overwrite if the target directory already exists (operator must explicitly delete first or pick a new name).

### Design

**File:** `.claude/skills/setup-new-dev-repo.md` with YAML frontmatter and recipe body.

**Inputs:**
- `corpus_name` — the suffix after `Formosan-` (e.g., `Bunun-NewDialect`). Required.
- `language` — primary Formosan language (for README pre-fill). Required.
- `has_audio` — bool, whether to include audio download scaffolding. Default false.
- `parent_dir` — default `~/Documents/Projects/Formosan/`.
- `remote_url` — optional git remote URL.

**Recipe phases:**

**Phase 1 — Confirm intent.** Build a concrete plan and present via `AskUserQuestion`:
- Target dir
- What files/dirs get created
- Which deps get installed (read from FormosanBank `requirements.txt`)
- Whether to set up a git remote
- Whether to include audio scaffolding

User can approve, request changes, or abort. No filesystem changes before approval.

**Phase 2 — Create directory and init git.**
- `mkdir -p <target>/{XML,CodeAndDocs}`
- `cd <target> && git init -b main`
- If `remote_url`: `git remote add origin <remote_url>`

**Phase 3 — Create `.venv`.**
- `python3 -m venv .venv`
- `.venv/bin/pip install --upgrade pip`
- `.venv/bin/pip install -r <FormosanBank-path>/requirements.txt`
- Capture output; surface any install failures to the user immediately (don't continue with broken env).

**Phase 4 — Scaffold layout.**
- Create placeholder files: `XML/.gitkeep`, `CodeAndDocs/.gitkeep`.
- Generate `README.md` from template at `.claude/skills/setup-new-dev-repo/README.template.md`. Template fields: corpus name, primary language, status ("Pre-QC, in development"), source description placeholder, attribution placeholder, scripts inventory placeholder.
- Generate `.gitignore` from template. Defaults: `.venv/`, `__pycache__/`, `*.pyc`, `*.log`, `qc-output/`, `data/`, `raw_data/`, `Original/`, `img-by-page/`, `text-by-page/`, `.DS_Store`, `.claude/settings.local.json` (per FormosanBank convention).
- If `has_audio`: generate stub `download_audio_data.sh` from template; otherwise skip.

**Phase 5 — Install Claude Code safety rails.**
- Create `.claude/hooks/check-venv.py` by copying from FormosanBank's `.claude/hooks/check-venv.py` (so the script is local; the new repo isn't dependent on FormosanBank's filesystem location).
- Create `.claude/settings.local.json` with the SessionStart hook entry from item 4, plus `additionalDirectories` pointing at the parent dir so reads of sibling repos work (matches FormosanBank's own setup).

**Phase 6 — Initial commit.**
- `git add . && git commit -m "Initial scaffold for Formosan-<corpus_name>"`
- If `remote_url` was provided and remote is reachable: ask whether to push now.

**Phase 7 — Summary.** Print summary of what was created and recommended next steps:
- `source .venv/bin/activate`
- Start adding source material under `XML/` (or run an ingestion script you'll add to `CodeAndDocs/`)
- When source XML is ready, run `run-qc-pipeline` from this directory
- When QC passes, run `port-corpus-in` from FormosanBank

### Decisions the skill surfaces (not guesses)

- Whether to set up a git remote (and what URL).
- Audio scaffolding (default off; user toggles).
- Additional libs beyond FormosanBank's `requirements.txt` (default: none; user can specify per-corpus needs).

### What the skill is NOT

- Not a corpus ingestion tool — it scaffolds structure, doesn't populate `XML/`.
- Not a port-in tool — `port-corpus-in` (item 3) is for the *finished* dev repo going into FormosanBank.
- Not a clone-FormosanBank tool — it assumes FormosanBank is already present locally.

---

## Build order

Within Phase 0, five items now. Suggested sequence with rationale:

1. **Hook: block `statistics/` writes** (item 1) — smallest, lowest-risk. ~30 minutes.
2. **Hook: SessionStart `.venv` check** (item 4) — also small; building before the skills means subsequent skill development gets the early-warning benefit. ~30–45 minutes.
3. **Skill: `setup-new-dev-repo`** (item 5) — bootstraps fresh dev repos and installs the venv-check hook into them. ~2–3 hours. Depends on item 4 existing (the recipe copies that hook into new repos).
4. **Skill: `run-qc-pipeline`** (item 2) — likely first tested against `Formosan-Nowbucyang-Truku-Thesis` (the most active candidate per the investigation). ~1–2 hours including fixtures. Independent of item 5 but benefits from venv assumed-present via item 4.
5. **Skill: `port-corpus-in`** (item 3) — depends on `run-qc-pipeline` existing (Phase 1 of port-in checks for QC evidence). ~2–3 hours including README template.

Total: ~6–9 hours across 2–3 focused sessions.

---

## Deferred backlog

These are recognized as valuable but not built now. Each has an explicit trigger condition — when the trigger fires, build the item before tackling the work that triggered it.

| # | Item | Type | Trigger to build |
|---|---|---|---|
| 6 | `split-monolithic-xml` | Skill | First request to port one of the 3 Amis Constructions dev repos. |
| 7 | `update-gitbook` | Skill | D Layer 0 reconciliation done; ready to automate Layer 1. |
| 8 | PostToolUse on `clean_xml.py` / `clean_nonlatin.py` | Hook | Evidence of accidentally not diffing after running these (i.e., a real incident or close call). |
| 9 | `corpus-content-reviewer` | Subagent | Start of C.2 Hunter S backlog review (Wikipedia / ePark mass-rewrite review). |
| 10 | `compare-original-vs-standard` | Skill | Start of B Phase B1 discovery. |
| 11 | `saw-a-problem-write-regression-test` | Skill | First time we ship a fix for a bug found during operations (per A's "Standing instruction"). |

This list is the canonical backlog; new items get added here as they're identified, not snuck into in-flight work.

---

## Cross-cutting status

- **`security-guidance` plugin:** uninstalled by user (per user statement). No further action.
- **`coderabbit` plugin:** uninstalled by user (per user statement). No further action.
- **`typescript-lsp` plugin:** disabled for this project in `.claude/settings.local.json` (done earlier this session).
- **`pyright-lsp` plugin:** install verified earlier (marker plugin; `pyright` binary at `/opt/homebrew/bin/pyright` works against project Python). No further action.

## Open questions / known limitations

1. **`CLAUDE_PROJECT_DIR` env var.** The hook script needs to know the repo root to resolve relative `file_path`s. I'm assuming `CLAUDE_PROJECT_DIR` is set by the harness when hooks run. Need to verify; if not, fall back to looking for `.git/` upward from the script location.
2. **`add_phonology.py` produces `<PHON>` elements not in DTD.** Running `validate_xml.py` after `add_phonology.py` will fail purely because of schema drift. The skill should note this but not treat it as a corpus error. The real fix is B's spec-vs-DTD reconciliation work; this skill should not work around it.
3. **`orthography_detector.py` quality.** The current detector "does not give an easy answer" (per user). This is a known unsolved problem and is its own track of work, possibly under B. The `run-qc-pipeline` skill explicitly handles this by pausing for human judgment; improving the detector is out of scope here.
4. **TSV mapping path for non-Ortho113 source orthographies.** Where do the orthography-conversion TSVs live? `Orthographies/ConversionTables/` was mentioned in CLAUDE.md but I haven't confirmed the actual structure or naming convention. Needs verification before `run-qc-pipeline` Phase 3 can resolve the right TSV automatically.
5. **README template for `port-corpus-in`.** Need to pick an existing corpus README as the model. Candidates: `Corpora/HundredPaiwanStories/README.md` (or wherever has a good current example). Worth a quick survey before drafting the template.
6. **Summary format for `run-qc-pipeline`.** Same — need a model existing README to base the QC-summary structure on.
7. **Per-corpus QC-passed signal.** What does `port-corpus-in` actually look for to decide "QC has passed recently"? A file? A specific log path? A user assertion? This affects Phase 1 of port-in.
8. **README section format and conflict resolution for `run-qc-pipeline`.** Need to settle: (a) the exact heading text for the persisted orthography section (`## Orthography`? `## QC metadata`?); (b) behavior when a re-run's answer differs from what the README already records (overwrite silently, prompt, abort?); (c) round-trip preservation for the free-text "Other (specify)" branch — write/read must keep the user's exact string, no normalization.
9. **Where to run `validate_xml` to make it a hard gate.** See Phase 5 open issue above. Either restructure phases so `validate_xml` runs before `add_phonology`, or make the gate `<PHON>`-aware. Picking (a) is simpler and matches the canonical CLAUDE.md pipeline order; picking (b) preserves the current "all validators in Phase 5" grouping.
10. **Retroactive QC on existing published corpora.** Running improved QC against already-published `Corpora/<Name>/` trees is a planned follow-up but the dynamics differ enough (no dev-repo, README already exists in published form, can't blindly scaffold, etc.) that it should be a separate skill, not a flag on `run-qc-pipeline`. Out of scope for items 1–5 here.

## Next step

After this spec is approved, invoke `superpowers:writing-plans` to produce the implementation plan that turns these designs into a concrete sequence of file edits, fixture creation, and verification steps.
