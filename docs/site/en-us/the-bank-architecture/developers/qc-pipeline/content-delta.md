---
icon: code-compare
---

# content_delta.py

> Compares the published XML of the merge base with the head and goes red on anything removed, renamed or relabelled — TEXT and sentence ids, element counts per tier, dialect and licence values — for the maintainer to override, exactly as a licence change is.

## What it's for

POL-037 says ids are stable and POL-051 says removals are disclosed, and until October 2026 nothing checked either at pull-request time. Of the twenty-four re-port PRs of September 2026, three disclosed their removals; among the rest, one rehashed all 98,837 ILRDF ids, one dropped eight published sentences, one renamed every Paiwan Stories TEXT id, one removed 144,436 `AUDIO` and 126,239 `W` elements, one deleted 88,677 `PHON` tiers and relabelled 62,484 Truku records `dialect="unknown"`. This tool is the check that makes each of those a red line a reviewer sees.

## How it works

For every corpus on either side (or only the corpora named with `--corpus`) it reads each published `TEXT`: its id, `@dialect`, `@copyright`, the ordered sentence ids with their original `FORM` text, and the number of `S`, `W`, `M`, `TRANSL`, `AUDIO` and `PHON` elements. Then, per corpus:

- **TEXT ids removed**, or **renamed**: a removed id whose sentences reappear under an added id, matched by content, is reported as a rename rather than a removal plus an addition.
- **S ids removed** inside a kept TEXT, or **renumbered**: the same original text under a new id.
- **Element counts that go down**, per tier, summed across kept TEXTs.
- **`@dialect` and `@copyright` values that change**, per TEXT.

Additions (new corpora, new TEXTs, counts that go up) are reported and never red. Every other line is red and the exit code is 1.

## Usage

```bash
# as CI runs it: the base tree materialized from git, only the corpora the PR touches
python QC/validation/content_delta.py --base /tmp/base/Corpora --head Corpora --corpus ePark

# everything on both sides
python QC/validation/content_delta.py --base /tmp/base/Corpora --head Corpora
```

| Flag | Default | Purpose |
| --- | --- | --- |
| `--base` | required | The merge base's `Corpora/` directory. |
| `--head` | required | The head's `Corpora/` directory. |
| `--corpus` | all | Restrict to one corpus; repeatable. |

## Output & exit codes

One line per change, `RED` for anything that needs an override:

```
Content changes between base and head (POL-037 ids, POL-051 removals):
  RED Seediq-Chang-Reference-Grammar: S ids renumbered (same text, new id) ×1 — POL-037: ids are stable
  RED Seediq-Chang-Reference-Grammar: S removed ×1 — chang-2000-seediq-long-texts/C5-005
  RED Seediq-Chang-Reference-Grammar: W count down ×10 — −10 across kept TEXTs
  RED Seediq-Chang-Reference-Grammar: TEXT/@dialect changed ×1 — chang-2000-seediq-long-texts: Tegudaya → unknown
      C: TEXT ids added ×1 — t3
```

Exit 1 on any red line, 0 otherwise. There is no label-based bypass: a legitimate re-port is merged by maintainer override, and the PR body says what was removed and why (POL-051).

## When to run it

CI runs it on every pull request that touches `Corpora/*/XML/` (the `content-comparison` workflow, modelled on `rights-comparison`). Run it by hand before opening a re-port PR, so the red lines in the PR are the ones you intended.

## Related

- [CI workflows](../repository-contracts/ci-workflows.md)
- [validate_port_readiness.py](validate-port-readiness.md)
- [QC Pipeline overview](README.md)
