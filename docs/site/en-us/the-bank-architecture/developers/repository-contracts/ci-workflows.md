---
icon: circle-play
---

# CI workflows

> Nine workflows run against the FormosanBank repository. Four can block a pull request; five report and never fail. Knowing which is which saves you from both ignoring a real gate and chasing a warning that was never going to stop you.

## What it is

`.github/workflows/` holds nine YAML files. Most carry a header comment stating their intent — whether findings are meant to block — because the intent is a maintainer decision that the YAML alone doesn't make obvious.

The repository's general stance: **new problems block, existing problems report.** Most validators run twice, once scoped to what a pull request changed (blocking, baseline-diffed) and once across all of `Corpora/` on `main` (informational, uploaded as an artifact). That is what lets a corpus with known legacy findings stay in the bank without every unrelated PR turning red.

## Who reads it

You do, mostly when something is red. This table is the map:

### Blocking — these can fail your pull request

<table><thead><tr><th width="200">Workflow</th><th width="190">Runs on</th><th>What actually gates</th></tr></thead><tbody>
<tr><td><code>xml-validation</code></td><td>PR + push to main</td><td>Only HARD finding fingerprints <em>absent from the PR base</em>, on added/modified files under <code>Corpora/*/XML/</code>. An added file has an empty baseline, so it must be clean. The full-corpus job on main is informational.</td></tr>
<tr><td><code>audio-validation</code></td><td>PR + push to main</td><td>HARD findings V100–V103 for corpora whose XML the PR touched. Deliberately does not manufacture V100 failures where no local audio exists. Full-corpus job informational.</td></tr>
<tr><td><code>hf-audio-parity</code></td><td>PR + push + nightly 08:17 UTC</td><td><strong>Everything.</strong> No baseline, no exemption, no swallowed exit code — see <a href="hugging-face-audio-parity.md">Hugging Face audio parity</a>.</td></tr>
<tr><td><code>tests</code></td><td>PR + push to main</td><td><code>pytest</code>. Plain and total.</td></tr>
</tbody></table>

### Informational — these report and move on

<table><thead><tr><th width="200">Workflow</th><th width="190">Runs on</th><th>What it produces</th></tr></thead><tbody>
<tr><td><code>duplicate-sentences</code></td><td>PR + push to main</td><td>Per-corpus duplicate findings as a step-summary table and a 30-day artifact. The <em>remover</em> is deliberately never run from CI — it touches data and must stay opt-in.</td></tr>
<tr><td><code>manual-edits-check</code></td><td>PR</td><td>Warns when a PR edits published XML without touching that corpus's <code>CodeAndDocs/</code> — the signature of an uncaptured hand edit (POL-030). Heuristic and deliberately non-blocking: a pipeline regeneration touches XML too.</td></tr>
<tr><td><code>conversion-tables</code></td><td>PR + push to main</td><td>Conversion-table and registry health. Never blocks on content findings, by maintainer ruling (2026-08-10): phoneme-level mismatches are often legitimate, and registry findings are SOFT per POL-034.</td></tr>
<tr><td><code>token-comparison</code></td><td>PR + push + <code>v1.*</code> tags</td><td>Token-count delta against the PR base or previous push, computed from XML rather than the possibly-stale CSVs. A step summary — no exit-code gate.</td></tr>
<tr><td><code>corpus-metrics</code></td><td>push to main + PR</td><td>Regenerates <code>statistics/</code> and auto-commits on main. See <a href="generated-files.md">Generated files</a>. Its <code>exit 0</code> is a no-changes early return, not a suppressed failure.</td></tr>
</tbody></table>

## How it's enforced

Blocking is expressed three ways, and it is worth being able to read them:

- **Exit code propagates** — the plain case (`hf-audio-parity`, `tests`).
- **Exit code deliberately suppressed** — `--no-exit-on-hard`, or `|| true`. Every informational validator job uses one of these.
- **A shell accumulator** — `xml-validation` and `audio-validation` loop over changed files, set `fail=1`, and `exit $fail` at the end, so one bad file doesn't hide the rest.

{% hint style="warning" %}
**Two workflows do not currently do what their header comments say.** Both are recorded here rather than silently corrected, because the fix is a behaviour change and the intent statements are maintainer decisions.

**`conversion-tables` — the registries gate does not fire.** The header states the registries job "exits nonzero only if a registry file itself is missing or unparseable (a genuinely broken repo)", and `validate_registries.py` does return `1` in exactly that case. But the step pipes into `tee`:

```yaml
run: |
  python QC/validation/validate_registries.py --csv ... | tee -a "$GITHUB_STEP_SUMMARY"
```

GitHub's *default* `run:` shell on Linux is `bash -e {0}`; `pipefail` is added only when you write `shell: bash` explicitly. Without it the pipeline reports `tee`'s status, always `0`, and the return value is discarded. A missing or unparseable registry passes green. Fix: add `shell: bash` to that step.

**`duplicate-sentences` is informational only by accident.** The header promises "a finding does not fail the build", but the step wraps its per-corpus loop in `set -e` with no `|| true`. It is non-blocking solely because `validate_duplicate_sentences.py` hardcodes `return 0`. That script already classifies findings HARD and SOFT; if HARD ever gains a nonzero exit, this workflow silently becomes a repo-wide gate. The intent should be pinned in the YAML the way `audio-validation`'s informational job pins it.
{% endhint %}

## How to change it correctly

**Reproduce locally before pushing.** Every workflow runs a script you can run yourself; the [QC Pipeline](../qc-pipeline/README.md) page for that script gives the invocation. `--no-exit-on-hard` lets you read findings without failing your shell.

**If you add a blocking check**, say so in a header comment, and state what is *not* gated. The existing headers are the reason this page could be written at all.

**If you intend a check to be informational, pin it in the YAML** — `|| true` or `--no-exit-on-hard` — rather than relying on the script's current exit code. A comment is a statement of intent; only the YAML is the contract.

{% hint style="info" %}
CI Python versions are mixed: `tests`, `xml-validation`, `audio-validation`, `hf-audio-parity` and `conversion-tables` use 3.13; `corpus-metrics`, `token-comparison` and `duplicate-sentences` still pin 3.10. The repo `.venv` is 3.13. Worth standardizing.
{% endhint %}
