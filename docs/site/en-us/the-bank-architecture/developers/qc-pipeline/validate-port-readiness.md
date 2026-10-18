---
icon: clipboard-check
---

# validate\_port\_readiness.py

> Mechanical pre-port gate: run it on a dev repo before porting a corpus into `Corpora/`, and again on the ported copy. Plain Python — no AI tooling involved — so every porter runs the same checks.

## What it's for

Recent audits kept finding the same port-blocking problems late, by hand: private source material about to be published, dialect labels that don't match [`dialects.csv`](https://github.com/FormosanBank/FormosanBank/blob/main/dialects.csv), README files pinning FormosanBank commits that don't exist (or three documents pinning three *different* commits), stale audio statistics, and conversion tables nobody had validated. This script mechanizes those checks so they run in seconds at port time instead of surfacing in an audit afterwards.

It complements the rule-based validators: they check the **XML content**; this checks the **corpus as a publishable unit** (repo hygiene, metadata registries, sidecar statistics).

## The checks

**HARD findings block the port (exit code 1):**

| ID | Check |
| --- | --- |
| `P001` | A git-tracked file sits under a `Private/` directory. `Private/` holds development-only material (keys, notes, restricted source data) that must never ship; a tracked file there would be published by the next push. |
| `P002` | A `TEXT/@xml:lang` is not a known Formosan ISO 639-3 code. |
| `P003` | A `TEXT/@dialect` is missing or not canonical for its language per `dialects.csv` (`unknown` is allowed). |

**WARN findings need human judgment (never block):**

| ID | Check |
| --- | --- |
| `P004` | Commit hashes pinned in `README`/`reproducibility`/`qc_status` files disagree with each other or are unreachable in the FormosanBank repository. Decide which pin is authoritative and fix the others. A hash inside a URL or a markdown link target is a link, not a pin, and is ignored (since October 2026). |
| `P005` | The corpus's `AUDIO` element count doesn't match `statistics/audio_durations.csv` — the published audio seconds are stale. Refresh with `QC/utilities/refresh_audio_stats.py` after the port. |
| `P006` | `CodeAndDocs/` standardizes through a conversion table — one under `Orthographies/ConversionTables/`, or any other `--tsv_path`; a corpus-local table is marked as such because it sits outside the POL-056 sweep. Run [validate\_conversion\_table.py](https://github.com/FormosanBank/FormosanBank/blob/main/QC/validation/validate_conversion_table.py) on it before trusting the standard tier it produced. |

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`:

```bash
# Before porting: point it at the dev repo root (the dir holding XML/)
python QC/validation/validate_port_readiness.py --corpus_path ../Formosan-<Name>

# After porting: check the published copy too
python QC/validation/validate_port_readiness.py --corpus_path Corpora/<Name>
```

`--repo-root` overrides which FormosanBank checkout is used for the commit-pin and audio-statistics checks (default: the checkout the script lives in).

Output is one line per finding plus a `port-readiness: N HARD, M WARN` summary. Exit code is 1 if and only if there is at least one HARD finding, so the script can gate automation as well as humans.

## When to run it

- As step one of [porting a corpus in](../porting-a-corpus.md) — and again on the ported copy before publishing.
- Any time a dev repo's metadata (language, dialect, README pins) changes late in development.

The `port-corpus-in` Claude skill runs it automatically, but the script does not require Claude: it is the same gate for everyone.
