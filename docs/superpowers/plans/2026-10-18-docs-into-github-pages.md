# Docs into FormosanBank on GitHub Pages — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish all FormosanBank documentation from this repo via GitHub Pages: GitBook content imported with history, corpus READMEs as the single corpus pages, generated language pages with growth figures, build-time statistics, and a sentence-level translation workflow.

**Architecture:** Markdown sources (`docs/site/<edition>/`, `Corpora/*/README.md`, `POLICIES.md`, `AUDIO-PERMISSIONS.md`, `statistics/*.csv`, `docs/translations/*.tsv`) are assembled by `docs/tools/prepare_site.py` into a temporary tree, built per edition by properdocs/mkdocs-material, then link-checked by `docs/tools/check_site.py`. Nothing generated is committed except `statistics/language_history.csv`, which `QC/language_history.py` writes (one-time rebuild here, incremental in `corpus-metrics.yaml`).

**Tech Stack:** Python 3.13 (`/workspace/FormosanBank/.venv`), properdocs 1.6.7, mkdocs-material 9.7.7, mkdocs-literate-nav 0.6.3, matplotlib (already used by `QC/corpus_metrics.py`), lxml/ElementTree, pytest, GitHub Actions (`actions/deploy-pages@v4`).

**Spec:** `docs/superpowers/specs/2026-10-18-docs-into-github-pages-design.md` (read it; rulings are quoted there).

## Global Constraints

- Worktree `/workspace/wt-docs-pages`, branch `feature/docs-github-pages`, off `origin/main`. Stage explicit paths only. ONE PR.
- Commits touching shared files end with `Shared-change-approved: "Approve all of the above" (maintainer, docs-move decision page, 2026-10-18)`. Shared = `QC/`, `.github/`, `.claude/`, `tests/` (outside `tests/corpora/`… which is also covered by the approval list here), `POLICIES.md`, root files. Any shared file NOT on the spec's approved list (notably `QC/corpus_metrics.py`) → stop and ask.
- Commit trailer also: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Never pass `-c user.email`.
- Site base URL: `https://formosanbank.github.io/FormosanBank/`. Editions: `en` at `/`, `zh` at `/zh/`, `paiwan` at `/paiwan/`, `amis` at `/amis/`, `bunun` at `/bunun/`. HTML `lang`: `en`, `zh-TW`, `pwn`, `ami`, `bnn`.
- Corpus README headings, exactly: `## Languages and dialects`, `## Source`, `## Statistics`, `## How to cite`, `## License`, `## Notes and caveats`, `## Reproduction and processing`, `### How to reproduce`, `### What each step does`. `## License` keeps `**License:** …` and `**Rights source:** …` lines.
- Counting comes only from `QC/corpus_counts.py`. `transcribed_words` = words of `S` with an `AUDIO[@file]` child of `S` or of any `S/W`.
- Figures: SVG, log y, plot area height = 2 × width, four lines: total, transcribed, segmented, glossed words.
- Translation email `joshua.hartshorne@sydney.edu.au`; permission text verbatim from the spec. Claude never writes Formosan text.
- No corpus XML change except the FormosanBankGitBook citation/BibTeX via its build code.
- Full pytest ≈30 min: run targeted tests per task; full suite once at the end. Validators per corpus only.

## Review Focus

1. A corpus README containing GitBook-style or HTML that breaks MkDocs (raw `{% %}`, unbalanced `<div>`) → the build fails loudly naming the file, never ships raw markup. (Task 2 test `test_unknown_directive_raises`.)
2. A corpus with no stats CSV yet (new port, CI not run) → its page renders "Statistics not yet computed" and the consistency test names it; build does not crash. (Task 4 test `test_corpus_table_missing_csv`.)
3. A language with data but no `languages.csv` name → hard error naming the code, never a bare ISO code on a page. (Task 4 test `test_unknown_language_code_raises`.)
4. Translator file that is malformed, from an old sentence inventory, or contains a cross-dialect clash → import reports and refuses/flags; never silently overwrites an approved row. (Task 13 tests.)
5. History extend when the cached tip is not an ancestor of HEAD (force-push/reset main) → falls back to a full rebuild rather than appending inconsistent rows. (Task 6 test `test_extend_diverged_tip_rebuilds`.)

---

### Task 1: Import the GitBook repo with history

**Files:** Create `docs/site/{en-us,zh-TW,pwn}/**`, `docs/tools/{manage_corpus_pages.py,update_corpus_stats.py,corpus_pages_ignore.txt}`, `tests/site/**`; Modify `.gitignore`.

- [ ] Step 1: `pip install git-filter-repo` into a scratch venv; clone `/workspace/FormosanBankGitbook` to scratchpad, checkout `origin/main` (`004e1d9`), `git filter-repo --path-rename en-us/:docs/site/en-us/ --path-rename pwn/:docs/site/pwn/ --path-rename zh-TW/:docs/site/zh-TW/ --path-rename manage_corpus_pages.py:docs/tools/manage_corpus_pages.py --path-rename update_corpus_stats.py:docs/tools/update_corpus_stats.py --path-rename corpus_pages_ignore.txt:docs/tools/corpus_pages_ignore.txt --path-rename tests/:tests/site/ --path .github/ --path __pycache__/ --invert-paths`.
- [ ] Step 2: Verify: `git log --oneline | wc -l` ≥ 440; `git ls-tree -r --name-only HEAD | grep -v -E '^(docs/|tests/site/)'` lists only loose root files (README.md, pytest.ini, requirements-dev.txt, sync_upstream_docs.py, statistics/ if any).
- [ ] Step 3: `git merge --allow-unrelated-histories --no-ff` into the branch; `git rm` the loose root files, `docs/tools/sync_upstream_docs.py` (if renamed there), `tests/site/test_upstream_doc_sync.py`, `docs/site/en-us/the-bank-architecture/policies.md`; add `.build/` and `/site/` to `.gitignore`. Commit.

### Task 2: Site build pipeline

**Files:** Create `docs/tools/prepare_site.py`, `docs/tools/check_site.py`, `docs/tools/build-site.sh`, `docs/theme/**`, `mkdocs.yml`, `mkdocs.zh.yml`, `mkdocs.paiwan.yml`, `mkdocs.amis.yml`, `mkdocs.bunun.yml`, `requirements-site.txt`, `tests/site/conftest.py` (loader), `tests/site/test_prepare_site.py`, `tests/site/test_check_site.py`; Modify `requirements.txt`.

**Interfaces — Produces:** `prepare_site.Edition(source: str | None, output: str, public_prefix: str, html_lang: str)`; `EDITIONS` tuple; `NEW_SITE = "https://formosanbank.github.io/FormosanBank"`; `prepare_site(repo_root: Path, out_root: Path) -> None`; `transform_markdown(text, *, current_source, current_output, mapping, public_prefix) -> str` (raises `ValueError("unhandled GitBook directive …")` on leftover `{% … %}`); `check_site.main(site_dir) -> int`.

- [ ] Step 1: Extract Hunter's files from GitBook commit `f8e7d8f` (paths per the 2026-09-05 plan Task 2) to the new paths; port `tests/test_prepare_site.py`.
- [ ] Step 2: Failing tests: `test_legacy_url_rewritten_to_project_base` (asserts `https://formosanbank.github.io/FormosanBank/xml`), `test_unknown_directive_raises`, `test_paiwan_html_lang_is_pwn` (built `paiwan/index.html` contains `lang="pwn"`), `test_absolute_link_with_project_base_resolves` (check_site), `test_parse_page_collects_duplicate_ids`.
- [ ] Step 3: Implement: sources under `docs/site/`; base URL; directive guard; `{% content-ref %}` blocks converted (6 occurrences); theme `language` override per edition; `site_url` per config. Fix the 4 corpus pages with two h1 (MontgomeryTexts, Siraya-Gospels, WakelinTexts, WilangYutasVideos) at source.
- [ ] Step 4: `pip install -r requirements-site.txt`; `bash docs/tools/build-site.sh` → exit 0; tests pass. Commit (shared trailer: requirements.txt).

### Task 3: Build-time pages from canonical files

**Files:** Modify `docs/tools/prepare_site.py`; Create `docs/site/corpus_pages.csv` (columns `corpus,slug,nav_label,descriptors`, one row per `Corpora/<dir>`, slugs = today's GitBook file stems so paths are kept); Test `tests/site/test_included_pages.py`.

**Interfaces — Produces:** `render_included_doc(repo_root, source_name, title) -> str`; `render_corpus_page(repo_root, corpus: str, stats_md: str) -> str` (README text with the `## Statistics` section body replaced by `stats_md`, relative links rewritten to `https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/<corpus>/…` (`tree/` for dirs), first `# ` heading kept as page title); `load_corpus_pages(repo_root) -> list[CorpusPage]`.

- [ ] Step 1: Failing tests: policies page contains a unique line from a fixture `POLICIES.md`; corpus page from a fixture README has rewritten `CodeAndDocs/x.sh` link and injected table; README without `## Statistics` gets the table inserted after the `## Source` section; `corpus_pages.csv` has exactly one row per `Corpora/*` dir (real repo).
- [ ] Step 2: Implement; English edition corpus pages at `the-bank-architecture/corpora/<slug>.md` now come from READMEs (committed `docs/site/en-us/the-bank-architecture/corpora/<slug>.md` files are deleted in Task 12 after their content is merged into READMEs; until then the generated page wins and the committed one is ignored). Nav: corpora sub-list generated from `corpus_pages.csv` in the English SUMMARY.
- [ ] Step 3: Build; tests pass. Commit.

### Task 4: Statistics tables library

**Files:** Create `docs/tools/site_stats.py`; Test `tests/site/test_site_stats.py`. (Logic ported from `docs/tools/update_corpus_stats.py`, which is then deleted along with its test.)

**Interfaces — Produces:** `load_stats(stats_dir: Path) -> list[StatsRow]` (adds `corpus` from file name); `corpus_table(rows, corpus) -> str`; `language_table(rows) -> str` (columns = languages); `dialect_table(rows, language) -> str | None` (None unless `dialects.csv` lists ≥2 dialects for the language; files without `dialect` → column `unknown`); `language_name(code, dialect) -> str` (via `corpus_counts.resolve_language`; raises `KeyError` naming the code if unnamed). Row labels as today's `ROW_DEFS`, plus a `Transcribed words` row after `Word count`.

- [ ] Step 1: Failing tests: `test_corpus_table_matches_legacy_format` (fixture CSV → expected markdown incl. `13.4h` audio formatting), `test_dialect_table_unknown_column`, `test_no_dialect_table_for_single_dialect_language`, `test_corpus_table_missing_csv` (returns the "Statistics not yet computed" note), `test_unknown_language_code_raises`, `test_truku_split_from_seediq`.
- [ ] Step 2: Implement; wire into Task 3's `render_corpus_page` and the corpora index page aggregate tables. Delete `update_corpus_stats.py` + its test. Commit.

### Task 5: `transcribed_words` count

**Files:** Modify `QC/corpus_counts.py` (`COUNT_FIELDS`, `analyze_root`), `QC/utilities/get_corpus_stats.py` (append column last), `tests/utilities/test_get_corpus_stats.py`; Create `tests/utilities/test_transcribed_words.py`.

- [ ] Step 1: Failing test: fixture TEXT with S1 (S/AUDIO file, 3 words), S2 (W/AUDIO only, 2 words), S3 (AUDIO without file, 4 words), S4 (no audio, 5 words) → `transcribed_words == 5`.
- [ ] Step 2: Implement; regenerate nothing by hand (CI regenerates CSVs). Run `pytest tests/utilities -q`. Commit (shared trailer).

### Task 6: Per-corpus, per-language history

**Files:** Create `QC/language_history.py`, `tests/utilities/test_language_history.py`, `statistics/language_history.csv`.

**Interfaces — Produces:** `HISTORY_FIELDS = ("date","commit","corpus","language","dialect","words","transcribed_words","segmented_words","glossed_words","zho_transl_count","eng_transl_count")`; `rebuild(repo_root: Path, cache_dir: Path | None) -> list[dict]`; `extend(repo_root: Path, csv_path: Path) -> list[dict]`; CLI `python QC/language_history.py {rebuild,extend} --csv statistics/language_history.csv`. Reuses `corpus_metrics.history_commits`, `changed_xml_files`, `read_git_blobs`, `commits_after`, `is_ancestor`, `snapshot_records`-style seeding (import, don't modify). Records via `corpus_counts.analyze_root`; corpus = `Corpora/<dir>`; language = `resolve_language`; dialect `""` → `unknown`. Blob-id → record memo (dict; optional on-disk pickle in `cache_dir`).

- [ ] Step 1: Failing tests on a temp git repo with 3 commits (add corpus A; add corpus B + modify A; delete a file of A): rows per (commit, corpus, language, dialect) correct; `test_extend_appends_only_new_commits`; `test_extend_diverged_tip_rebuilds`.
- [ ] Step 2: Implement; run `rebuild` on the real repo in the background (log progress to scratchpad); verify the final commit's per-corpus totals equal `statistics/*_corpora_stats.csv` word/segmented/glossed/zho columns exactly. Commit CSV + code (shared trailer).

### Task 7: Whole-corpus Mandarin history audit (maintainer's request)

**Files:** none committed unless a defect is in an approved file; findings go to the review page.

- [ ] Step 1: Sum Task 6 rows per commit → series for words and zho; join with `statistics/corpus_size_history.csv` on commit; list every commit where they differ, with per-corpus breakdown.
- [ ] Step 2: Trace NTU (`Corpora/NTUFormosanCorpus`) across all commits: words, zho, file count; identify the "full port" merge(s) (e.g. #266/#271, 2026-10-16) and whether the old CSV shows them.
- [ ] Step 3: If the cause is in `QC/corpus_metrics.py`: write the diagnosis with evidence, do NOT edit (not on approved list) — ask the maintainer. If the old CSV merely has rows computed under old rules, say so with the rows.

### Task 8: Language pages and growth figures

**Files:** Create `docs/tools/language_pages.py`, `tests/site/test_language_pages.py`; Modify `docs/tools/prepare_site.py` (call it), English SUMMARY (a "Languages" section generated).

**Interfaces — Produces:** `growth_series(history_rows, *, language: str | None, exclude_corpora: set[str] = frozenset()) -> list[Point]`; `render_growth_svg(series, title: str, labels: Labels) -> str`; `language_page(language, stats_rows, history_rows, corpus_pages, labels) -> str`; `write_language_pages(out_dir, ...) -> list[Path]`. Main corpora page gets two figures: all data, and `exclude_corpora={"Wikipedias"}`.

- [ ] Step 1: Failing tests: SVG plot-area height/width == 2.0 (parse `viewBox`/axes rect); y axis log; four `<path>` series with legend labels `Total words`, `Transcribed words`, `Segmented words`, `Glossed words`; zero values are not plotted on log scale (gap, not crash); page lists each corpus with data for the language and links its slug; dialect table present for Amis, absent for Thao; 19 pages generated from real stats.
- [ ] Step 2: Implement (matplotlib, Agg, SVG). Build; open two pages' HTML and verify a figure and tables exist. Commit.

### Task 9: Policies, README tests, lint, skills

**Files:** Modify `POLICIES.md` (POL-044, POL-052, POL-055 amendments per POL-050 citing "Approve these headings and the three amendments" 2026-10-18; current-practice GitBook references), `tests/corpora/test_readme_sections.py` (headings `License`, `Notes and caveats`), `tests/corpora/test_provenance.py`, `readme_sections_pending.txt`, `docs/tools/manage_corpus_pages.py` (in-repo paths, `corpus_pages.csv` instead of `CSV_TO_MD`, check README heading order), `tests/site/test_manage_corpus_pages.py`, `.claude/skills/port-corpus-in/{SKILL.md,README.template.md}`, delete `.claude/skills/port-corpus-in/corpus_page.template.md`, `.claude/skills/audit-dev-repo/checklists/every-corpus.md`.

- [ ] Step 1: Failing tests: lint flags a README missing `## Notes and caveats` or with headings out of order; lint flags a corpus dir with no `corpus_pages.csv` row.
- [ ] Step 2: Implement; `python docs/tools/manage_corpus_pages.py check --strict` reports exactly the READMEs not yet rewritten (expected until Task 12). Commit (shared trailer).

### Task 10: Workflows

**Files:** Create `.github/workflows/pages.yaml`; Modify `.github/workflows/corpus-metrics.yaml` (after stats: `python QC/language_history.py extend --csv statistics/language_history.csv`; add it to `git add`; add `QC/language_history.py` to path filters), `.github/workflows/tests.yaml` (paths `docs/**`, `mkdocs*.yml`, `requirements-site.txt`; step `manage_corpus_pages.py check --strict`).

- [ ] Step 1: `pages.yaml`: triggers `push: branches [main]`, `pull_request`, `workflow_dispatch`, `workflow_run: workflows: ["Corpus Metrics"] types: [completed] branches: [main]`; build job (Python 3.13, `pip install -r requirements-site.txt matplotlib lxml`, `bash docs/tools/build-site.sh`, `actions/upload-pages-artifact@v3`); deploy job only when not a PR (`actions/deploy-pages@v4`, environment `github-pages`); concurrency group `pages`; checkout with `ref: main` for workflow_run.
- [ ] Step 2: Validate YAML (`python -c "import yaml…"`), and run the build command locally exactly as the job does. Commit (shared trailer).

### Task 11: Repo docs and pointers

**Files:** Modify `CLAUDE.md` (Related repos → `docs/site/`; stats paragraph), `README.md` (site link), `LICENSE.md` (Terms of Use URL → `https://formosanbank.github.io/FormosanBank/additional-resources/terms-of-use/`), `.well-known/tdmrep.json` (same URL), `.devcontainer/README.md`, `.devcontainer/devcontainer.json` comment; `QC/utilities/port_audio_seconds_from_gitbook.py` (delete if unreferenced; else repoint); repository-contracts pages under `docs/site/en-us/the-bank-architecture/developers/repository-contracts/` (synced-pages → generated pages; ci-workflows; generated-files; single-sources-of-truth).

- [ ] Step 1: `git grep -n -i 'ai4commsci.gitbook.io\|FormosanBankGitbook'` outside `claudeplans/`, `docs/superpowers/`, historical POLICIES source notes → zero hits after edits; the built site resolves the new Terms of Use URL (check_site). Commit (shared trailer).

### Task 12: Corpus READMEs (34) — agents

**Files:** `Corpora/<each>/README.md`; delete merged `docs/site/en-us/the-bank-architecture/corpora/<slug>.md`; Create `docs/tools/check_readme_coverage.py`, `tests/site/test_check_readme_coverage.py`.

**Interfaces — Produces:** `check_readme_coverage.uncovered(old_texts: list[str], new_text: str) -> list[str]` (sentences of the old texts whose normalized letter content is not found in the new text; normalization: strip markdown/links/HTML, casefold, collapse whitespace; boilerplate the new format replaces — GitBook "Access Details" and the stats block — excluded and listed).

- [ ] Step 1: Failing tests for `uncovered` (reworded-but-present sentence not flagged only when its letters appear verbatim; dropped sentence flagged).
- [ ] Step 2: Dispatch agents, ≤5 at a time, one corpus each. Each agent prompt: the spec's heading list, the section mapping, "nothing dropped", D = read every script `generate_xml.sh`/`validate.sh` invoke and correct the "What each step does" text to match, list mismatches suggesting code problems in a report file; edit ONLY `Corpora/<corpus>/README.md` (+ delete that corpus's old GitBook page file); any deviation → stop and report; report ≤300 words.
- [ ] Step 3: After each agent: `git status` for files outside its corpus; `check_readme_coverage` on old README (`git show origin/main:…`) + old GitBook page vs new README; `pytest tests/corpora -q -k <corpus>`; collect flags for the review page. Commit per corpus.

### Task 13: Translation store, inventory, import

**Files:** Create `docs/tools/translations.py`, `docs/tools/import_translations.py`, `docs/translations/labels.tsv`, `docs/translations/{zho,pwn,ami,bnn}.tsv`, `tests/site/test_translations.py`.

**Interfaces — Produces:** `TRANSLATION_FIELDS = ("english","translation","approved","origin","translator","dialect","date","pages")`; `split_sentences(markdown: str) -> list[Segment]` (deterministic; headings, list items, table cells, sentences; code blocks and URLs excluded); `inventory(repo_root, edition) -> dict[str, list[Segment]]` keyed by page id (Formosan editions skip `### How to reproduce`/`### What each step does`/`## Reproduction and processing` segments of corpus pages); `load_store(lang) / save_store(lang, rows)`; `merge_import(store, payload, *, today) -> ImportReport` (counts new/changed/approved; refuses rows whose `english` key is unknown AND not in store history → kept as data with a warning; flags cross-dialect approved clash and stops).

- [ ] Step 1: Failing tests: splitter stability on a fixture page; import of a valid payload; malformed JSON → error, store unchanged; approved row never overwritten by an unapproved one; cross-dialect clash → `ImportReport.blocked` non-empty and store unchanged.
- [ ] Step 2: Prefill: `corpus-match` from `Corpora/FormosanBankGitBook/XML/**` (exact English match → pwn + zho); `previous-website` alignment for zh-TW and pwn pages (zh: align by meaning; pwn: only via the corpus's eng/zho triplets); Mandarin `mt` for every remaining English segment and every label — generated by agents in batches, written as unapproved rows.
- [ ] Step 3: Commit.

### Task 14: Translation tool pages and translated editions

**Files:** Create `docs/tools/translate_page/{template.html,app.js}`, Modify `prepare_site.py` (emit `/translate/<lang>/index.html` + `inventory.json` per language into the English site; generate zh/paiwan/amis/bunun edition pages from approved rows: only approved segments, untranslated omitted, link to English page; old zh-TW/pwn page kept until its first approved segment); Test `tests/site/test_translated_editions.py`.

- [ ] Step 1: Failing tests: page with 3 segments, 1 approved → output contains that translation, not the other two English sentences, and the "full English page" link; page with 0 approved and an old page → old page used; amis edition absent when no approved rows; labels applied to stats table headers.
- [ ] Step 2: Implement tool page: name + dialect form, page menu with "n of m approved", one segment at a time, editable box (typing sets approved, tick removable), approved Mandarin shown for Formosan languages, localStorage (try/catch), Download (.json via Blob) / Open saved work (file input), email address with copy button + mailto, permission text verbatim. Build; open the built page HTML and verify inventory loads (node-free check: parse inventory.json; serve with `python -m http.server` and fetch).
- [ ] Step 3: Commit.

### Task 15: FormosanBankGitBook corpus citation + translation build

**Files:** `Corpora/FormosanBankGitBook/CodeAndDocs/process_raw.py` (citation/BibTeX constants → v1 pattern), new `Corpora/FormosanBankGitBook/CodeAndDocs/build_translations.py` (approved Formosan rows → one TEXT per translator×dialect×batch; none yet), README (citation, Notes and caveats with MT counts line, Reproduction steps), regenerated XML.

- [ ] Step 1: Run the corpus's `generate_xml.sh`/reproduction; diff XML: only `citation` and `BibTeX_citation` attributes change on 6 files (show the diff).
- [ ] Step 2: `build_translations.py` unit test with a fixture store (2 approved pwn rows, 1 unapproved) → one TEXT, 2 S, TRANSL eng + zho when approved Mandarin exists. Commit.

### Task 16: Verify, review page, hand over

- [ ] Step 1: Rebase onto latest `origin/main`; new corpora get `corpus_pages.csv` rows + README rewrite.
- [ ] Step 2: Full `pytest -q` (record pass/fail counts), `bash docs/tools/build-site.sh` (exit 0, check_site clean), `manage_corpus_pages.py check --strict` clean, validators for FormosanBankGitBook.
- [ ] Step 3: Publish review artifact: built key pages (screenshots or HTML excerpts), every coverage flag, every reproduction mismatch, Mandarin history audit, every judgement call. Update the decision log.
- [ ] Step 4: Push the branch if the container can (`git push -u origin feature/docs-github-pages`); otherwise give push + `gh pr create` commands.
