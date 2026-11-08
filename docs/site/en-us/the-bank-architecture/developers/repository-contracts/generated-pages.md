---
icon: rotate
---

# Generated pages

> Several pages on this site are built from files elsewhere in the FormosanBank repository every time the site is published. There is no copy to edit and nothing to keep in sync: change the source file and the page follows.

## What it is

`docs/tools/prepare_site.py` assembles the site from these sources when [`docs/tools/build_site.py`](https://github.com/FormosanBank/FormosanBank/blob/main/docs/tools/build_site.py) runs:

| Source in the repository | Page |
|---|---|
| `POLICIES.md` | [FormosanBank Policies](../../policies.md) |
| `AUDIO-PERMISSIONS.md` | Audio publication policy (this section) |
| `Corpora/<corpus>/README.md`, one per row of `docs/site/corpus_pages.csv` | each corpus page under [Corpora](../../corpora/README.md) |
| `statistics/<corpus>_corpora_stats.csv` | every statistics table (corpus pages, the corpora index, language pages) |
| `statistics/language_history.csv` | the growth figures (corpora index and language pages) |
| `languages.csv`, `dialects.csv` | language names; which languages get a per-dialect table |

Each generated policy page opens with a "Generated page" note naming its source. Corpus pages are the README as written, with the statistics table inserted under `## Statistics` and relative links turned into GitHub links.

## Why it exists

Until 2026-10 the documentation lived in a separate GitBook repository, and these pages were committed copies kept current by `sync_upstream_docs.py`, a hand-run `update_corpus_stats.py`, and a drift test. The copies drifted anyway: four POLICIES.md changes went unsynced for three weeks, and in 2026-09 four corpus pages and the summary tables were found stale with nothing flagging them. Building from the source removes the copy, so there is nothing to drift.

## Who reads it

Readers of the site, and anyone editing documentation. The rule for editors: **never commit a generated page or table.** Edit the source file; the next build publishes it.

## How it's enforced

- **By construction.** The pages don't exist in the repository, only in the build (`.build/` and `site/` are gitignored).
- **The build fails loudly.** `build_site.py` runs properdocs with `--strict` (a broken link or missing page is an error) and then `check_site.py` (links, anchors, one `h1` per page, `lang` set). The `Documentation site` workflow runs it on every pull request, so a broken page fails review instead of going live.
- **Numbers follow the statistics.** The site rebuilds on every push to `main` and again after every `Corpus Metrics` run, which is the workflow that commits the statistics (its commit can't trigger other workflows by itself).

## How to work with it

Build the site locally:

```bash
python docs/tools/build_site.py          # output in site/, ends "link check clean"
python -m http.server -d site 8000       # then open http://localhost:8000/FormosanBank/
```

**To add a page generated from a repository file**, add an `IncludedDoc` to `INCLUDED_DOCS` in `docs/tools/prepare_site.py` with its source, its page path and an icon, and add it to `docs/site/en-us/SUMMARY.md`.
