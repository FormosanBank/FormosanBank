# GitBook sync (Roadmap Part D) + port-corpus-in GitBook integration

**Date:** 2026-06-14
**Status:** Design — approved for spec, pre-implementation
**Branch:** `feature/gitbook-sync-part-d` (FormosanBank); a matching branch in `FormosanBankGitbook` is cut at build time
**Supersedes/updates:** Roadmap Part D in [claudeplans/2026-05-27-roadmap.md](../../../claudeplans/2026-05-27-roadmap.md)

## Purpose

Two coupled goals:

1. **Finish `port-corpus-in`.** Porting a corpus into `FormosanBank/Corpora/` is only half-done if the corpus never appears in the public GitBook. Add a "Add to GitBook" phase so a port also produces the corpus's GitBook page.
2. **Roadmap Part D (GitBook sync).** Design the whole of Part D (Layers 0–4) and build the slice that porting needs plus the drift lints that keep the GitBook honest.

The driving example is the live port of `Formosan-Nowbucyang-Truku-Thesis`, which is QC'd and ready.

## Background: how a corpus reaches the GitBook today

The English GitBook (`FormosanBankGitbook/en-us/`) renders one page per corpus under `the-bank-architecture/corpora/<slug>.md`. Publishing a corpus touches **three** places, and missing any one silently half-publishes it:

1. **Page** — `en-us/the-bank-architecture/corpora/<slug>.md`, containing a `<!-- CORPUS STATS START -->` / `<!-- CORPUS STATS END -->` marker block, prose (description, copyright, citation, access link), nothing else load-bearing.
2. **Nav entry** — a bullet under the `## The Bank Architecture` → Corpora sublist in `en-us/SUMMARY.md`.
3. **Stats map** — an entry in the hardcoded `STATS_FILE_MAP` dict in `FormosanBankGitbook/update_corpus_stats.py`, mapping `<FBDir>_corpora_stats.csv` → `<slug>.md`. Without it, `update_corpus_stats.py` never injects the stats table into the page.

`update_corpus_stats.py` reads stats CSVs from `FormosanBankGitbook/statistics/` (themselves produced upstream by `FormosanBank/QC/utilities/get_corpus_stats.py`) and injects a per-language table between the markers.

### Branch state (Layer 0), re-audited 2026-06-14

The roadmap (2026-05-30) recorded `en-us` as ~19 commits ahead of `main`. That is **stale**. As of 2026-06-14 in the local checkout: `origin/en-us` has **zero** commits not on `main`; `main` is **4 commits ahead** of `en-us` (PR #20 MT-toolkit merge, the XML-format update, RauDong notes, a typo fix). So `en-us` now merely lags `main`. Which branch GitBook actually publishes from is **not determinable from the repo** and is an explicit open decision (see L0 below). The design therefore does **not** hardcode a target branch; the skill resolves it interactively at port time.

## Approach (selected)

**Hybrid (Approach C).** A small reusable Python helper in the GitBook repo owns the **mechanical, verifiable** edits to the three integration points; the **prose** is written by the skill/operator (human judgment). The same helper in `check` mode is the Layer 1 drift lint, so one body of code serves both the port and CI.

Rejected: (A) all-in-skill-prose — nested `SUMMARY.md` insertion and dict edits are fiddly and nothing verifies consistency; (B) all-in-helper — page prose is a judgment call, a poor fit for a script.

## Build scope vs design-only

| Part D layer | Disposition | Notes |
|---|---|---|
| **D-port** — `port-corpus-in` Phase 6 | **BUILD** | + live Truku port exercises it |
| **L0** — branch reconciliation | **DESIGN-ONLY** | Repo evidence recorded above; skill detects+asks at port time; policy resolution is its own follow-up |
| **L1** — drift lints + lint CI | **BUILD** | `check` mode of the helper + a GitBook CI workflow |
| **L1** — cross-repo stats-CSV regeneration | **DESIGN-ONLY** | The messy cross-repo sync (get_corpus_stats → gitbook statistics/) is scoped, not built |
| **L2** — zh-TW translation PRs | **DESIGN-ONLY** | Largest new subsystem (supersession state, MT/LLM engine) |
| **L3** — pwn manual | **BUILD (report only)** | Falls out of `check`'s translation-lag report; banner is policy |
| **L4** — cleaning-convention docs | **DESIGN-ONLY** | Blocked on B5 item 24 |

## Piece 1 — `manage_corpus_pages.py` (GitBook repo)

New script `FormosanBankGitbook/manage_corpus_pages.py`. Two subcommands over a shared model of a corpus's three integration points.

### `add` — scaffold a new corpus page (idempotent)

Arguments:
- `--corpus <FBDir>` — the `Corpora/` directory name (e.g. `Nowbucyang-Truku-Thesis`). Drives the expected stats-CSV name `<FBDir>_corpora_stats.csv`.
- `--slug <name>.md` — the GitBook page filename under `corpora/`.
- `--nav-label "<label>"` — the human label in `SUMMARY.md`.
- `--title "<title>"` — the page H1.
- `--template <path>` — **required**, no default. The skill passes its own template (see Piece 3). Tests pass a fixture template.
- `--gitbook-root <path>` — default `.` (the repo the script lives in).

Actions, each a no-op if already present (re-running is safe):
1. **Page**: if `corpora/<slug>` does not exist, render it from `--template`. Template carries the stats-marker block and `{{TITLE}}`, `{{DESCRIPTION}}`, `{{COPYRIGHT}}`, `{{CITATION}}`, `{{ACCESS}}` placeholders. `{{TITLE}}` is substituted from `--title`; the prose placeholders are left in place for the skill to fill.
2. **Nav**: if no `SUMMARY.md` bullet references `corpora/<slug>`, insert `  * [<nav-label>](the-bank-architecture/corpora/<slug>)` as the **last** item of the Corpora sublist — located as the line immediately before the top-level `* [Developers](...)` bullet. Indentation matches sibling bullets (two spaces).
3. **Stats map**: if `STATS_FILE_MAP` has no key `'<FBDir>_corpora_stats.csv'`, insert `    '<FBDir>_corpora_stats.csv': '<slug>',` into the dict literal in `update_corpus_stats.py`, placed alphabetically among existing keys. Implemented by locating the dict's line range and the correct insertion line; preserve existing formatting/quote style.

Output: a per-action report (`created` / `already present`) for each of the three points, and a nonzero exit only on hard failure (e.g. template missing, `SUMMARY.md` Developers anchor not found, `STATS_FILE_MAP` not locatable).

### `check` — drift lint (L1) + translation-lag report (L3)

Source of truth for "shipped corpora" = directory names under `--corpora-path` (default `../FormosanBank/Corpora`), each being a real corpus dir (has an `XML/` child).

Checks, grouped:

**Integration (gating under `--strict`):**
- Each shipped corpus (not in the ignore list) has: a stats CSV in `statistics/`, a `STATS_FILE_MAP` entry, an existing mapped page file, and a `SUMMARY.md` nav entry pointing to that page.
- No corpus page contains a leftover `{{…}}` placeholder (a half-filled port).
- No "Coming Soon" text in `en-us/` names a corpus that now exists under `Corpora/`.

**Translation lag (never gating — informational, L3):**
- Corpus pages present in `en-us/the-bank-architecture/corpora/` but absent from the parallel `pwn/` and `zh-TW/` trees, reported as two lists.

Flags:
- `--strict` — exit nonzero if any *integration* check fails. Translation-lag never affects exit.
- `--ignore <path>` — path to a checked-in newline-delimited list of `Corpora/` dir names intentionally not published to the GitBook. Default `corpus_pages_ignore.txt` in the GitBook repo root if present. Documented exclusions only; an unlisted missing corpus fails CI.
- `--corpora-path <path>` — override the FormosanBank `Corpora/` location.

### Idempotency & safety

- All edits are text-surgical and re-entrant; running `add` twice yields no duplicate bullets/keys/pages.
- `add` never edits prose or the stats-marker contents; `update_corpus_stats.py` remains the only writer between the markers.
- No git operations. The script mutates the working tree only.

## Piece 2 — `port-corpus-in` Phase 6 "Add to GitBook"

Inserted between current Phase 4 (validate after port) and the current Phase 5 (summary), which becomes Phase 6. New ordering: 1 assess · 2 plan · 3 execute · 4 validate · **5 GitBook** · 6 (was 5) summary. (Numbering in SKILL.md updated accordingly.)

Phase 5 steps:
1. **Locate GitBook repo** — default sibling `<formosanbank_path>/../FormosanBankGitbook`. If absent, `AskUserQuestion` for the path or offer to skip the phase.
2. **Resolve publish branch (L0)** — detect whether `main`/`en-us` diverge (report the ahead/behind counts), then `AskUserQuestion`: "Which branch does GitBook publish from?" Check out (or create a feature branch off) the chosen branch in the GitBook working tree. The skill makes working-tree edits only; the operator commits and opens the GitBook PR (consistent with the skill's existing "Not a git operation" principle).
3. **Derive identifiers** — propose `slug` (kebab-cased corpus name), `nav-label`, and `title` with defaults from `corpus_name`; let the operator override via `AskUserQuestion`.
4. **Scaffold** — run `manage_corpus_pages.py add` with the skill's `corpus_page.template.md` as `--template`.
5. **Fill prose** — replace the page's `{{DESCRIPTION}}` / `{{COPYRIGHT}}` / `{{CITATION}}` / `{{ACCESS}}` placeholders using the corpus README + QC summary. `{{ACCESS}}` is the standard "repo containing this corpus … [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/<corpus_name>)" line.
6. **Verify** — run `manage_corpus_pages.py check --strict` and confirm the corpus is fully wired and no placeholders remain.
7. The Phase 6 summary gains a **GitBook page** line (path + "commit/PR the GitBook repo separately") and notes the chosen publish branch.

`--skip-gitbook` short-circuits the phase for operators who want to defer the GitBook page.

## Piece 3 — template, CI, tests

### Template
`.claude/skills/port-corpus-in/corpus_page.template.md` (co-located with the existing `README.template.md`). Mirrors the established page shape (H1, description, `***` rule, stats-marker block, Access Details, Copyright, Citation) using the `{{…}}` placeholders above. The GitBook helper stays generic via `--template`.

### CI (GitBook repo)
`.github/workflows/corpus-page-lint.yaml` — on PR and push:
- `actions/checkout` the GitBook repo, plus `actions/checkout` `FormosanBank` into a sibling path so `Corpora/` is available.
- Run `python manage_corpus_pages.py check --strict --corpora-path <checked-out FormosanBank>/Corpora`.
- Fails the build on any integration drift; prints the translation-lag report as informational log output.

### Tests (GitBook repo)
The GitBook repo currently has **no** test infrastructure. Add a minimal `tests/` + a `requirements-dev.txt` (pytest). Cover:
- `add` idempotency (second run is a clean no-op for all three points).
- Nav bullet inserted at the correct position (last in Corpora sublist, before Developers).
- `STATS_FILE_MAP` key inserted alphabetically, formatting preserved.
- Each `check` category: missing CSV / missing map entry / missing page / missing nav / leftover placeholder / Coming-Soon-names-shipped, and the ignore-list suppression.
- Translation-lag never affects exit code.

## Design-only layers (recorded for sequencing)

- **L0 — branch reconciliation.** Deliverable: a written decision of which branch GitBook publishes from and the normal `main`↔`en-us` flow, after confirming the GitBook space's sync setting (out-of-repo). Until then the skill asks at port time. Owning follow-up branch, not this one.
- **L1 cross-repo stats sync.** A workflow that regenerates `FormosanBank/statistics/*_corpora_stats.csv` (via `get_corpus_stats.py`), copies them into `FormosanBankGitbook/statistics/`, runs `update_corpus_stats.py`, and commits. Cross-repo write/PR mechanics deferred; the within-repo lint CI ships now.
- **L2 — zh-TW suggested-translation PRs.** Reads the `en-us` diff, drafts zh-TW translations, opens draft PRs, applies supersession logic to obsolete prior bot PRs. Needs new persistent state and an engine choice (LLM vs MT). Largest piece; design-only.
- **L4 — cleaning-convention docs.** Document the cleaner's punctuation/caret/segmentation rules (C001/C002/C002b/C007/C006/C012) in the GitBook, owned by whichever script ends up with the C012 logic after B5 item 24 lands. Blocked on B5.

## Recommendation: keep the GitBook a separate repo

Part D open-question #5 asks whether `FormosanBankGitbook` should become a subdirectory of `FormosanBank`. **Recommendation: keep them separate.**

How GitBook publishing works (worth confirming in the GitBook space admin, since it is configured out-of-repo): a GitBook *space* uses **Git Sync** bound to one GitHub repo + one branch. The published URL is a property of the *space*, not the repo path. GitBook does support monorepo sync (a space can point at a *subdirectory* of a repo), so a merge is technically possible — but it would require **reconfiguring each language space's Git Sync** to the new repo + subdirectory. If that reconfiguration is done wrong, the public URL stops updating (or worse, points at the wrong content). The user has stated they don't know the current sync setup, which makes that reconfiguration the single largest risk of a merge.

Weighing it:

- **Costs of merging:** reconfigure 3 language-space Git Syncs (en-us/zh-TW/pwn) with no in-repo way to verify correctness; entangle the GitBook's multi-language *branch* structure (separate translation branches) with FormosanBank's `main` + CI; every GitBook-only edit now churns the much larger code repo and runs its CI.
- **Benefits of merging:** atomic commits that touch code + docs together; one PR instead of two; no cross-repo lint checkout. These are *convenience* gains.
- **What this design already buys without merging:** the `manage_corpus_pages.py` helper + `check` lint + GitBook CI remove most of the day-to-day cross-repo friction (the lint reaches across repos via a CI checkout; the skill drives both). So the marginal benefit of an actual merge is small.

The convenience gains do not outweigh the URL-breakage risk against an unknown sync configuration. Keep the repos separate; treat the cross-repo seams as a *tooling* problem (solved here) rather than a *structural* one. Revisit only if (a) the GitBook sync config is fully understood and (b) cross-repo friction proves materially worse than expected in practice.

## Out of scope

- No edits to `update_corpus_stats.py` behavior beyond adding a `STATS_FILE_MAP` entry.
- No zh-TW/pwn content generation (L2/L3 automation).
- No cross-repo commit/PR automation; the operator commits both repos.
- No changes to FormosanBank's existing CI or stats pipeline.

## Acceptance

- `manage_corpus_pages.py add` wires all three points idempotently for a new corpus; `check --strict` passes afterward.
- `check --strict` fails on a deliberately half-wired corpus and passes once fixed or ignore-listed.
- `port-corpus-in` Phase 6 produces a complete, placeholder-free GitBook page on the operator-chosen branch.
- The live `Formosan-Nowbucyang-Truku-Thesis` port lands in `Corpora/` and in the GitBook (page + nav + stats map), validated by `validate_xml.py` and `check --strict`.
- GitBook CI lint runs on PR and gates integration drift.
- Roadmap Part D is updated to reflect built vs design-only status.
