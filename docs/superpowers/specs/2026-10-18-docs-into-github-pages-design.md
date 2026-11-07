# Design: FormosanBank documentation moves from GitBook into the FormosanBank repo (GitHub Pages)

Date: 2026-10-18. Maintainer: Joshua Hartshorne. Decision page with his answers:
https://claude.ai/artifact/LrT9Ktvda8YGLf2rqprFsC (rounds 1-3).

## Intent and why

FormosanBank's public documentation lives in a separate private repo, `FormosanBankGitbook`, published by GitBook.
Two problems: every change needs two PRs (one per repo), and GitBook now charges for the Git Sync integration the
maintainer does not want to pay for. The docs move into the public `FormosanBank` repo and publish via GitHub Pages
(free for public repos). While moving, the maintainer wants (a) one copy of each corpus's documentation instead of two,
(b) new per-language statistics pages with historical growth figures, (c) every statistic and figure kept current
automatically, and (d) a translation workflow so collaborators can translate the site into Mandarin, Paiwan, Amis and
Bunun without Claude accounts. The maintainer wants the build to run in the background with little or no input from
him once he says "go".

## Repos and current state (observed 2026-10-18)

- `FormosanBank` (public, `main` at `cbcaf0214`): corpora under `Corpora/<Name>/{README.md,XML/,CodeAndDocs/}` (33
  corpora), QC tooling in `QC/`, statistics in `statistics/` (per-corpus `*_corpora_stats.csv`,
  `corpus_size_history.csv`, `audio_durations.csv`, four growth PNGs), 11 GitHub workflows. Pages not enabled yet;
  the maintainer will set Settings → Pages → Source: GitHub Actions (no Jekyll/Static HTML starter workflow).
- `FormosanBankGitbook` (private, at `/workspace/FormosanBankGitbook`, import from `origin/main` `3cec529`; `main` is
  63 ahead of `en-us`, 0 behind; 439 commits): `en-us/` (105 md pages), `zh-TW/` (22), `pwn/` (24), each with its own
  `SUMMARY.md` nav (translated pages use different file names, e.g. zh uses pinyin slugs, so editions are NOT
  path-parallel). Tools: `manage_corpus_pages.py` (wires/lints the four integration points of a corpus page),
  `update_corpus_stats.py` (writes stats blocks between `<!-- CORPUS STATS START/END -->` from FormosanBank CSVs,
  run by hand), `sync_upstream_docs.py` (copies `POLICIES.md`, `AUDIO-PERMISSIONS.md` into pages), tests, and two
  workflows (`corpus-page-lint.yaml`, `tests.yaml`). GitBook markup in use: 33 `{% hint %}`, 3 `{% tabs %}` (15 tabs),
  6 `{% content %}` blocks across 29 files.
- Hunter's reverted PR #78 (GitBook commit `f8e7d8f`): `scripts/prepare_site.py`, `scripts/check_site.py`,
  `scripts/build-site.sh`, three mkdocs configs, theme, tests. Rebuilt in a scratch folder on 2026-10-18: English 83
  pages at `/`, Mandarin 21 at `/zh/` (`lang="zh"`), Paiwan 23 at `/paiwan/` (`lang="en"`, wrong), language menu with
  hreflang en/zh-TW/pwn; `check_site.py` failed on 4 corpus pages with two h1s. The revert had no technical reason
  (maintainer: "He was trying this out for me to see if it was feasible. He didn't want responsibility.").
- A prior plan exists: `docs/superpowers/plans/2026-09-05-gitbook-into-formosanbank-pages.md` (12 tasks; covers the
  import, build revival, build-time inclusion of POLICIES/AUDIO-PERMISSIONS, build-time stats, lint repointing, CI,
  skill update, docs update). It predates this design's README consolidation, language pages, history, and
  translation work; reuse its mechanics where they still fit.

## Goals (maintainer's items A–I plus translation)

A. Move all GitBook content into FormosanBank, with history. Open GitBook PRs are ignored.
B. Publish publicly at `https://formosanbank.github.io/FormosanBank/` (editions `/`, `/zh/`, `/paiwan/`, plus new
   `/amis/`, `/bunun/`).
C. One document per corpus. **The corpus `README.md` is the single copy; the site renders it.** Section order and
   headings (approved):
   ```
   # <Corpus name>
   ## Languages and dialects      (say so explicitly when unknown)
   ## Source                      (brief description of the source; audio goes here)
   ## Statistics                  (table inserted at build time; nothing committed)
   ## How to cite
   ## License                     (keeps POL-044's two structured lines, then prose on evidence / where to find it)
   **License:** <must equal @copyright>
   **Rights source:** <grantor>, <YYYY-MM-DD>; evidence: ask maintainer
   ## Notes and caveats           ("None known." when empty; issues users should know, incl. contestable import decisions)
   ## Reproduction and processing
   ### How to reproduce           (usually two .sh files; links CodeAndDocs/provenance.json per POL-052)
   ### What each step does        (blow-by-blow walk through the scripts)
   ```
   Existing README sections map: "Audio" → Source (and Notes if there's a problem); "Validation" and "Publication
   packaging" → Reproduction and processing. GitBook-page-only content (e.g. plain-language summary paragraphs,
   "Access Details" link) is merged in. **Nothing may be dropped**: a sentence-coverage script compares each new
   README against its old README and old GitBook page and lists every sentence whose content no longer appears; the
   list goes in the final review page.
D. Check "Reproduction and processing" against the code **by reading the scripts only** (no re-running builds).
   Corrections go into the docs, never the code; mismatches that suggest a code problem are listed for the maintainer.
E. One generated page per language with data (19 today: the 16 recognised languages, Truku and Seediq separate per
   `QC/corpus_counts.resolve_language`, plus Babuza-Favorlang, Pazeh, Siraya): the same statistic rows the GitBook
   tables show today (word count; audio hours total/transcribed/untranscribed; translated words English/Mandarin/
   Japanese/Dutch; morphologically segmented; glossed words), a per-dialect table for languages with more than one
   dialect (including "unknown" = no `dialect` attribute), the list of corpora with data for it (links to corpus
   pages), and a growth figure.
   **Growth figure:** x = time, y = number of words on a log scale, **plot area twice as tall as wide**; four lines:
   total words, transcribed words, segmented words, glossed words.
F. Two growth figures on the main corpora page, summed over all languages: all data, and all data excluding the
   `Wikipedias` corpus.
G. Retool every GitBook↔FormosanBank sync mechanism (stats, policy pages, audio-permission page, corpus-page lint,
   port-corpus-in skill's GitBook phase).
H. Retool affected GitHub Actions so the prior mission (keeping docs current) is still accomplished.
I. All statistics tables and figures stay current automatically.
T. Translation workflow (below).

## Non-goals

- No change to any corpus XML or data in this job, except the FormosanBank GitBook corpus citation/BibTeX (S3) and,
  later, new files there built from approved translations. Data problems found while
  writing pages go into that page's Notes and caveats and the review list.
- No fixing of corpus build code (item D is read-only verification).
- No translation into Formosan languages by Claude, ever. Machine translation is Mandarin only.
- No migration of open GitBook PRs.
- The existing `corpus_size_history.csv`, its four PNGs and the root README's references keep updating exactly as now.

## Anti-goals (would make this a failure even if it technically works)

- Losing any sentence of existing corpus documentation in the merge.
- Published stats that lag the CSVs (e.g. because a bot commit didn't trigger the site build).
- Committing generated pages, tables or figures (except the history CSV, which is an expensive-to-rebuild cache and
  is written only by script/workflow).
- Changing a shared file outside the approved list without asking.
- Any unapproved translation appearing on the site.

## Constraints

- **Shared-file rule.** Approved list (maintainer clicked "Approve all of the above", 2026-10-18):
  `.github/workflows/` (new `pages.yaml`; `corpus-metrics.yaml`; `tests.yaml`); `QC/` (`corpus_counts.py` and
  `get_corpus_stats.py` gain a transcribed-words count; new history builder; delete or repoint
  `QC/utilities/port_audio_seconds_from_gitbook.py`); `tests/` (new `tests/site/`; update `test_readme_sections.py`,
  `test_provenance.py`, `test_get_corpus_stats.py`); `POLICIES.md` (amend POL-044/052/055; replace GitBook references
  that describe current practice; historical "Source: GitBook XML-format page" notes stay); `.claude/skills/`
  (`port-corpus-in` + both templates, `audit-dev-repo` checklist); root files (`CLAUDE.md`, `README.md`,
  `requirements.txt`, new `requirements-site.txt` and site configs, `.gitignore`, `readme_sections_pending.txt`,
  `LICENSE.md`, `.well-known/tdmrep.json`, `.devcontainer` notes); `statistics/` (new history CSV). Anything else
  shared: stop and ask. Commits touching shared files carry
  `Shared-change-approved: "Approve all of the above" (maintainer, docs-move decision page, 2026-10-18)`; the
  POLICIES amendment cites his click "Approve these headings and the three amendments" (2026-10-18) per POL-050.
- **One PR** for everything. Work in an isolated git worktree on a branch off `origin/main`; never on the shared
  checkout's branch. Stage explicit paths only. Commit email is the GitHub noreply address (never pass
  `-c user.email`). The maintainer pushes and opens PRs himself (`gh` doesn't run in the container); hand over a push
  command and a `gh pr create` command.
- Agents launched for corpus pages: edit only `Corpora/<that corpus>/`; any deviation → stop and report. After each
  agent, list every file it changed outside its folder.
- Python 3.13 repo `.venv`. Container network: GitHub and PyPI only.
- Full pytest ≈ 30–34 min; run validators per corpus, not whole-tree (OOM).
- `corpus-metrics.yaml` pushes with rebase-and-retry (fixed after the 2026-09-11 race); keep that.
- **GitHub Actions trap:** pushes made with `GITHUB_TOKEN` don't trigger other workflows. The stats auto-commit is such
  a push, so `pages.yaml` must also run on `workflow_run` completion of `corpus-metrics` (on `main`).
- Counting rules come only from `QC/corpus_counts.py` (single source of truth): tokens from sentence-level FORM,
  standard tier with original fallback; language identity from `xml:lang` + `dialect` (`trv` + `Truku` → Truku,
  else Seediq). `segmented_words` = words of sentences containing any `M`; `glossed_words` = words of sentences
  containing an `M/TRANSL`.
- **New count, `transcribed_words`:** words of sentences that have an `AUDIO` element with a `file` attribute either
  directly under `S` or under any of its `W`. (Observed: this and the S-only definition differ by 98 of 2,637,835
  words, all ePark.) Added as a new column in the per-corpus stats CSVs (after existing columns, which are a published
  interface).

## Decided architecture

### Site

- Content: `docs/site/en-us/`, `docs/site/zh-TW/`, `docs/site/pwn/` (imported with history via `git filter-repo`
  path rewrite + `--allow-unrelated-histories` merge, as in the prior plan's Task 1), plus generated `ami` and `bnn`
  editions. Stack: `properdocs==1.6.7`, `mkdocs-material==9.7.7`, `mkdocs-literate-nav==0.6.3` (Hunter's, tested).
  Hunter's `prepare_site.py`/`check_site.py` revived under `docs/tools/`. Build output gitignored.
- GitBook directives converted to MkDocs-Material equivalents; any unconverted `{% … %}` fails the build.
- Paiwan `lang` attribute fixed (`pwn`); Amis `ami`, Bunun `bnn`.
- Corpus pages: built from `Corpora/<Name>/README.md` at build time; stats table inserted under `## Statistics` from
  `statistics/<Name>_corpora_stats.csv` (+ `audio_durations.csv` seconds); relative links rewritten to GitHub URLs
  (`https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/<Name>/…`).
- Policies and Audio Permissions pages generated from `POLICIES.md`/`AUDIO-PERMISSIONS.md` (English edition).
- Existing Mandarin/Paiwan corpus pages kept, each with a line linking to the current English corpus page.
- Corpus-page lint (`manage_corpus_pages.py check --strict`) repointed in-repo and extended to check the README
  heading structure; runs in `tests.yaml`.
- `LICENSE.md`, `.well-known/tdmrep.json`, root `README.md`, `CLAUDE.md`, `.devcontainer` notes repointed to the new
  site. The maintainer updates the repo "website" field and archives the GitBook repo after cut-over.

### Statistics, history, figures

- New history file `statistics/language_history.csv` (name is builder's choice), long format: one row per (commit,
  corpus, language, dialect) with date, commit, corpus, language, dialect, words, transcribed_words,
  segmented_words, glossed_words. Built once from every first-parent commit on `main` that changed corpus XML (178
  commits since 2024-10-25; 130,498 distinct XML blob versions; parse each blob once, cache by blob id), applying
  today's counting rules to every commit. Corpus identity = the `Corpora/<dir>` name at that commit; language =
  `xml:lang`/`dialect` at that commit. Only commits on `main` count.
- `corpus-metrics.yaml` extends it incrementally on each run and commits it with the other stats.
- Language pages, the two main-page figures and all tables are generated at build time from the CSVs; figures are SVG
  (matplotlib), log y-axis, plot area height = 2 × width.
- `pages.yaml`: on push to `main` (build + deploy), on `pull_request` (build only, including link check), on
  `workflow_dispatch`, and on `workflow_run` of `corpus-metrics` completed on `main` (build + deploy).
- A test asserts every published corpus has a stats CSV and appears on its language pages.

### Retired

`sync_upstream_docs.py` and its drift test; `update_corpus_stats.py`'s commit-into-pages mode and sibling-repo
resolution; the GitBook repo's two workflows; the `port-corpus-in` skill's second-repo/second-PR phase (the corpus page
now ships in the port's own PR); `port_audio_seconds_from_gitbook.py` if nothing references it (else repoint).

### Translation workflow (rulings, 2026-10-18)

Maintainer's words, abridged: artifacts for collaborators "for translating. These need to work for people without
Claude accounts … download their work so far and re-upload when they restart. At any point, they can email me their
work … select what page to work on from a menu … sentence-by-sentence … If there is an existing translation, that
appears with the ability to edit it. For Mandarin, we can prepopulate using MT … but we don't *use* anything for an
actual GitHub Page until it's been approved … For Mandarin, in principle everything is a target of translation. For
Formosan languages, we would not translate the 'Reproduction and Processing' section of the corpus pages … standard
section headings once … headings on tables and figures once … artifacts for Paiwan, Amis, Bunun, and Mandarin …
when we consume these, they become part of the FormosanBank GitBook corpus itself … Old translations are not removed
from the corpus … new translations may reflect new sentence; they are out of date for the documentation, but they are
still data."

- **Store:** one file per target language, `docs/translations/<lang>.tsv`. Row key = normalized English source
  sentence text. Fields: English sentence, translation, approved (yes/no), origin (`human`, `mt`,
  `previous-website`, `corpus-match`), translator name, translator dialect, date, plus where the sentence occurs
  (page ids). When English text changes, the old row stays; the new sentence is a new, untranslated key.
- **Shared label list:** standard section headings, table row/column labels, figure titles/axis labels/legend labels,
  language and dialect names — translated once per language, used on every page and figure of that edition.
- **Approval (ruled):** "If somebody types into the box, it counts as 'approved' unless they deliberately un-tick it.
  The ticking is mostly for approving prior work (MT-based, guesstimated translation from a previous version of the
  website, etc)." So: human-typed/edited → approved by default (tick can be removed); prefilled rows (`mt`,
  `previous-website`, `corpus-match`) start unapproved and need a tick.
- **Prefill:** Mandarin machine translation (by Claude) of every English sentence, unapproved, origin `mt`. Previous
  website translations (existing `zh-TW/` and `pwn/` pages) aligned to current English sentences as guesses,
  unapproved, origin `previous-website` (the ruling explicitly anticipates "guesstimated translation from a previous
  version of the website"). Exact English matches against the 105 sentences of `Corpora/FormosanBankGitBook` (each
  Paiwan sentence carries `TRANSL eng` and `TRANSL zho`) prefill Paiwan and Mandarin, unapproved, origin
  `corpus-match`. Amis and Bunun start with no prefill at all (not even shared labels): Claude never writes Formosan
  text.
- **Site (ruled):** "The translated part appears. The untranslated part does not." A translated edition's page shows
  only approved sentences; untranslated sentences are omitted (not shown in English). Each such page carries a line
  linking the full English page. A page with zero approved sentences doesn't exist in that edition — except that an
  existing old `zh-TW`/`pwn` page stays as-is (decision 4) until its first approved sentence arrives, then the
  generated page replaces it. Formosan editions never include "Reproduction and processing" sections.
- **Translation tool (ruled S1, 2026-10-18: "Sounds good!" to putting it on the new site):** four static pages on the
  site, `/translate/mandarin/`, `/translate/paiwan/`, `/translate/amis/`, `/translate/bunun/`, built by the site build
  from the current sentence inventory (so they never go stale). No account of any kind. Work kept in the browser
  (localStorage, try/catch), "Download my work" (`.json`, ordinary browser download) and "Open saved work" (file input).
  Shows `joshua.hartshorne@sydney.edu.au` as a mailto link plus selectable text with a copy button. Permission text
  (R5): "When you email your work to Joshua Hartshorne (joshua.hartshorne@sydney.edu.au), you agree that FormosanBank may
  publish it on the FormosanBank website and in the FormosanBank corpus under the CC BY-NC 4.0 license, credited to you
  by the name you entered." Translator enters name and dialect at start. Page menu with progress counts; one English
  sentence at a time with the current translation in an editable box and an approve tick (typing = approved unless
  un-ticked); Formosan pages also show the approved Mandarin for the sentence when one exists, and omit corpus
  "Reproduction and processing" sentences. Shared labels are a menu entry of their own. Announced to translators only
  after the PR merges.
- **Dialects (ruled S2: "We will worry about that if it ever happens!"):** dialect is recorded on every row; no
  website-dialect rule is built. If an import would add an approved translation for a sentence that already has an
  approved translation in a different dialect of the same language, the import script stops and reports it for a
  ruling.
- **Import:** a script reads a translator's `.json` (or pasted text), validates it against the current sentence
  inventory, shows a summary (new / changed / approved counts, conflicts with existing rows), and merges on
  confirmation.
- **Corpus (ruled R3, R4, S3):** approved Formosan translations become new XML files in `Corpora/FormosanBankGitBook/`
  (one TEXT per translator × dialect × import batch; `S` FORM = the Formosan sentence; `TRANSL eng` = the English
  sentence; `TRANSL zho` = the approved Mandarin of the same English sentence when one exists). Mandarin with no
  Formosan counterpart is not corpus data (website only). Existing corpus files are never removed (only dedup/merge
  per existing policy). The corpus README's Notes and caveats states, with per-file counts, how many Mandarin
  translations began as machine translation and were approved.
  **Citation (S3, his words):** "it should list all contributors in alphabetical order. Title is just 'Translations of
  the FormosanBank documentation vX' going forward. For now, Xuan Ruan is the only author and it is v1. BibTex will need
  to be updated as well. This does mean the citation changes over time, but that's OK." So every TEXT in the corpus
  carries the same current citation and BibTeX, regenerated by the corpus build: now
  `Ruan, X. (2025). Translations of the FormosanBank documentation v1.` License and rights-source format approved:
  `copyright="CC BY-NC 4.0"`; README `**Rights source:** Xuan Ruan, 2025-02-11; <Name>, <date of their email>;
  evidence: ask maintainer`. Builder's calls (flag in review): the version number goes up by one at each import that
  adds approved translations to the corpus; the year is the year of that version; the existing six files' citation and
  BibTeX change now (through the corpus build code, POL-038), which is the one corpus-XML change in this job.
- **Delivery:** Mandarin first draft ≈ 8,000–10,000 sentences, all unapproved, stored in `docs/translations/zho.tsv`.

## Left to the builder

Code structure, module names, test design, sentence-splitting rules (must be deterministic and stable across builds),
translation-page visual design, the exact stats-table markup, history-file name, ordering of work, and how agents are used.
Whatever the builder decides, the final review page must show: key built pages, every dropped-sentence flag, every
reproduction mismatch, every judgement call made.

## Addendum (2026-10-18, after "go")

- Corpora now number 34 (ILCAA-Kanakanavu-Texts merged); GitBook import point is GitBook `origin/main` `004e1d9`.
- Maintainer, mid-run: *"I would like you to look at the historical statistics for the whole corpus as you are
  recomputing for individual languages. I'm suspicious of the number of mandarin-translated words over time, which seems
  to not have noticed a significant jump when I fully ported in NTU corpus, which is pretty large."* So the new history
  also records `zho_transl_count` (and `eng_transl_count`) per corpus, and the run includes an audit of the whole-corpus
  history in `statistics/corpus_size_history.csv` against the recomputation, tracing NTU specifically. A defect found in
  `QC/corpus_metrics.py` (not on the approved shared-file list) is reported, not fixed, until he approves.
- Maintainer on pushing: *"since I won't be checking often, don't wait on pushing and PR opening if you don't absolutely
  need to wait."*
