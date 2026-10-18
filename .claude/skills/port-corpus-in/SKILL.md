---
name: port-corpus-in
description: Move a QC'd corpus from its Formosan-<CORPUS>/ dev repo into FormosanBank/Corpora/<Name>/ with the standard layout, interactively. Surfaces decisions rather than guessing. Use when a corpus has passed QC and is ready for publication into FormosanBank.
---

# port-corpus-in

Move a QC'd corpus from a development repo into FormosanBank with the standard published layout (`{README.md, XML/, CodeAndDocs/}`, optionally `download_audio_data.sh`).

**Invariant: nothing from `<source_path>/Private/` is ever copied to FormosanBank.** Per the dev-repo convention (see `setup-new-dev-repo`), `Private/` holds development-only material that must not ship — decryption keys, draft notes, source data with private content, etc. The skill enforces this in three places: Phase 1 lists `Private/` but flags it as excluded, Phase 2 never offers its contents for porting, and Phase 4 verifies post-port that nothing from `Private/` landed in the published corpus.

## Inputs (gather via `AskUserQuestion` if missing)

- `source_path` — path to the dev repo (e.g., `~/Documents/Projects/Formosan/Formosan-Nowbucyang-Truku-Thesis/`). Required.
- `corpus_name` — name for the published version. Default: derive from source by stripping `Formosan-` prefix. User can override.
- `formosanbank_path` — default sibling `../FormosanBank/` relative to source.
- `assume_qc_passed` — default `false`. If `false` and no recent QC summary is found, refuse or ask.
- `skip_docs` — default `false`. If `true`, Phase 5 (Add to the documentation site) is skipped and the operator registers the page later. (`skip_gitbook`, the old name, means the same.)

## Pre-checks

0. **Re-read `POLICIES.md` before going on.** If any instruction in this skill contradicts a policy, stop and show the maintainer both texts before continuing; the policies file moves faster than this skill.
1. Verify `source_path` exists.
2. Verify `formosanbank_path/Corpora/` exists.
3. Verify target `formosanbank_path/Corpora/<corpus_name>/` does NOT already exist. Refuse if it does — operator decides whether to merge, replace, or pick a new name.
4. Look for recent QC evidence in `source_path`:
   - `qc-output/<latest-timestamp>/qc-summary.md` exists, OR
   - User explicitly passed `assume_qc_passed=true`.
   - If neither: surface to user. Either ask to run `run-qc-pipeline` first or to set `assume_qc_passed=true`.
5. **The dev repo already has the published build shape** (POL-047/048/052); a
   port copies it, it does not create it. Check, and stop with a list of what is
   missing rather than porting around it (a new corpus is never added to a
   pending list):
   - `CodeAndDocs/generate_xml.sh` exists, is executable, and is the only entry
     point (no `Makefile`, `make_xml.sh`, `reproduce.sh`, `run_qc_pipeline.sh`,
     `build.sh` beside it — POL-047);
   - it reads nothing outside its own `CodeAndDocs/` and the FormosanBank checkout
     (no `Private/`, no `VALIDATOR_ROOT`/`FORMOSANBANK_*` env vars, no second clone
     — POL-048), and runs no validator (build only);
   - `CodeAndDocs/provenance.json` is written by the build and holds a 40-character
     `formosanbank_commit` (POL-052);
   - `CodeAndDocs/tests/` holds the source-accounting test (every source unit is
     either emitted or in the rejected list with a reason; skips when the source
     is absent) — the `setup-new-dev-repo` scaffold ships it as
     `test_source_accounting.py`; a corpus without one has no answer to "is text
     missing from the scrape?" (Seediq-Chang's chapters 5 and 6 were).
   Offer the scaffold's templates (`.claude/skills/setup-new-dev-repo/`) for
   whatever is missing; the fix belongs in the dev repo, before the port.

## Recipe phases

### Phase 1: Assess source layout

Read `source_path` top-level. Identify and report:

- Does a `README.md` exist?
- Where is the XML? Detect:
  - `XML/` (standard already)
  - `Final_XML/` (common in dev repos)
  - `xml/<chapter>.xml` (common for chapter-segmented corpora)
  - Root-level `*.xml` (monolithic — see below)
- Is the XML monolithic (single file with many `<TEXT>` or `<S>` elements)? If yes, stop and tell the user the XML must first be split into the published per-file layout — via a committed script in the dev repo's `CodeAndDocs/` (POL-038) — then re-invoke port-corpus-in. Do not port a monolithic file.
- What scripts exist (at root or in a `scripts/` subdir) that likely belong in `CodeAndDocs/`?
- What source data artifacts exist at root (e.g., original PDFs, extracted text files, decrypted source documents) that may belong in `CodeAndDocs/` for reproducibility — *unless* they contain private content per CLAUDE.md's "private source data" caveat, in which case surface to user.
- What scratch dirs exist that should be dropped (`data/`, `raw_data/`, `Original/`, `img-by-page/`, `text-by-page/`, `logs/`, etc.)?
- Does `Private/` exist — or any top-level directory whose name begins with `Private` (`Private:Source/` is in use)? If yes, list its contents in the report under a clear "WILL NOT BE PORTED" heading. Do not surface it as a candidate for copying at any point in Phase 2.
- Is there a `download_audio_data.sh`?

### Phase 2: Present plan

Build a concrete file-by-file plan and present via `AskUserQuestion`:

- **Copy these to `Corpora/<corpus_name>/XML/`**: <list of XML paths>
- **Copy these to `Corpora/<corpus_name>/CodeAndDocs/`**: <list of scripts and docs>
- **Drop these (won't be ported)**: <list of scratch dirs / build artifacts>. `Private/` (if present) is **always** in this list and is never offered as a porting candidate, even if its contents look corpus-relevant.
- **README handling**: copy as-is | generate from template | skip
- **Copy or move?**: default copy (leave dev repo intact)
- **Include `download_audio_data.sh`?**: yes/no based on audio presence

User can: approve, request changes to the plan, or abort. **No filesystem changes before approval.**

### Phase 3: Execute the plan

For each item in the approved plan:

```bash
mkdir -p "<formosanbank_path>/Corpora/<corpus_name>/XML"
mkdir -p "<formosanbank_path>/Corpora/<corpus_name>/CodeAndDocs"

# Copy XML
cp -r <source XML> "<formosanbank_path>/Corpora/<corpus_name>/XML/"

# Copy scripts
cp <source scripts> "<formosanbank_path>/Corpora/<corpus_name>/CodeAndDocs/"

# README: the corpus's only documentation (the documentation site renders it as
# the corpus page). It must follow the layout in README.template.md (headings
# checked by tests/corpora/test_readme_sections.py). If the dev repo's README
# already follows it, copy it; otherwise render the template from the dev
# README + QC summary + user input, keeping every sentence of the dev README.
cp <source README> "<formosanbank_path>/Corpora/<corpus_name>/README.md"   # or render the template

# Audio:
# If has_audio: cp <source download_audio_data.sh> "<formosanbank_path>/Corpora/<corpus_name>/"
```

**Audio parity with Hugging Face (if has_audio).** The XML's `<AUDIO file=…>`
references are the contract CI checks against the Hub (`validate_hf_audio.py`,
blocking). Before the PR, show the operator the dry run of the sync tool for
the corpus's dataset — it lists the clips the XML references that the Hub
lacks and the Hub files nothing references any more, and changes nothing
without `--apply`:

```bash
<python> <formosanbank_path>/QC/utilities/sync_hf_audio.py \
  --repo FormosanBank/<dataset> --xml "<formosanbank_path>/Corpora/<corpus_name>/XML"
```

Running it with `--apply` (write token, ffmpeg) is the operator's call and a
separate step; record the revision SHA it prints in `audio_sources.json`.

Drop nothing from the source dev repo unless explicitly approved.

### Phase 4: Validate after port

**The gate GitHub runs, run here first.** A pull request is checked by three
validators, not one, and each is compared with what `main` already has: any
HARD finding that is new fails the PR. Run exactly that, and quote the counts
("0 new HARD in xml / text / glosses") above the push block in Phase 6. A
corpus that passes only `validate_xml.py` can still turn the PR red for a text
or gloss defect — it has happened, and the fix then lands after the hand-over
instead of before it.

```bash
cd <formosanbank_path>
C="Corpora/<corpus_name>"
# The baseline: what main holds for this corpus (empty for a new port, so every
# HARD finding is new; the predecessor for a re-port).
rm -rf /tmp/port-base && mkdir -p /tmp/port-base
git archive origin/main -- "$C" 2>/dev/null | tar -x -C /tmp/port-base || true
for v in validate_xml validate_text validate_glosses; do
  <python> QC/validation/${v}.py --no-exit-on-hard by_path --path "$C/XML" --csv /tmp/port-$v-head.csv
  args=(--candidate /tmp/port-$v-head.csv --severity HARD)
  if [ -d "/tmp/port-base/$C/XML" ]; then
    <python> QC/validation/${v}.py --no-exit-on-hard by_path --path "/tmp/port-base/$C/XML" --csv /tmp/port-$v-base.csv
    args+=(--baseline /tmp/port-$v-base.csv)
  fi
  echo "== $v: new HARD findings vs main =="; <python> QC/validation/compare_findings.py "${args[@]}"
done
```

(`validate_glosses.py` is a no-op on a corpus without W/M; run it anyway so the
line reads "0".) SOFT findings do not gate: list them in the Phase 6 summary
by rule, with what each class is, for the operator to read.

**The static build-shape tests, for this corpus.** The repository's own tests
check the port shape (one entry point in canonical order, self-contained,
provenance recorded and linked, the README layout (headings in order, the
License block, Notes and caveats), only XML under `XML/`, no deviation stated
in prose alone). Run them for the ported corpus and quote the pass count:

```bash
<python> -m pytest tests/corpora -q -k "<corpus_name>"
```

**The build, actually run (POL-047 idempotency).** The maintainer wants this
done locally in the port, not in CI. From the FormosanBank checkout, run the
corpus's entry point and require a clean tree afterwards:

```bash
cd <formosanbank_path>
bash "Corpora/<corpus_name>/CodeAndDocs/generate_xml.sh"
git status --porcelain "Corpora/<corpus_name>" "statistics/"    # must print nothing
```

A build that changes files on a clean checkout is not idempotent; one that
exits because a table, a private file or a second clone is missing is not
self-contained (POL-048). Either is a finding to surface, not to work around.
If the build needs more than about twenty minutes, say so and ask before
running it.

**The corpus's own tests.** They are the per-corpus regression layer (Tang's 16
each corrupt one thing and assert the complaint; Song's 21 pin every printed
record) and nothing in CI collects them (`testpaths = ["tests"]`). Run them
here, with the environment the corpus expects, and quote the pass count:

```bash
cd <formosanbank_path>
FORMOSANBANK_ROOT="$PWD" <python> -m pytest "Corpora/<corpus_name>/CodeAndDocs/tests" "Corpora/<corpus_name>/tests" -q 2>/dev/null
```

The source-accounting test (pre-check 5) must be among them and must pass; if
it skips because the source is absent from the public checkout, say so.

**Resolve `<python>` in this order:**
1. `<source_path>/.venv/bin/python3` if it exists (dev repos created via `setup-new-dev-repo` have one)
2. Otherwise `<formosanbank_path>/.venv/bin/python3` — FormosanBank always has a venv with the deps
3. If neither, refuse and tell the user to install one before validating

Quick spot-check counts (file count, total size) vs source. If discrepancies, report — do not auto-fix.

**Port-readiness gate.** Run the mechanical pre-port checks on the source dev
repo AND on the ported copy (this script is deliberately AI-free so
non-Claude porters run the same gate — point them at it too):

```bash
<python> <formosanbank_path>/QC/validation/validate_port_readiness.py \
  --corpus_path "<source_path>" --repo-root "<formosanbank_path>"
<python> <formosanbank_path>/QC/validation/validate_port_readiness.py \
  --corpus_path "<formosanbank_path>/Corpora/<corpus_name>" \
  --repo-root "<formosanbank_path>"
```

Exit 1 (HARD: tracked Private/ content, unknown xml:lang, non-canonical
dialect) blocks the port. WARNs need operator judgment: P004 = README /
`qc_status.json` / `reproducibility.md` pin different or unreachable
FormosanBank commits (ask which is authoritative and fix the others);
P005 = `statistics/audio_durations.csv` stale for this corpus (run
`refresh-audio-stats` after the port); P006 = the corpus standardizes via a
conversion table — run `validate_conversion_table.py` on it (source profile,
target profile, table as the three positional args) before trusting the
standard tier.

**Re-port: what changed against the merge base, and why each change was
approved.** When `main` already holds this corpus, run the content-delta check
CI will run and read every red line:

```bash
<python> <formosanbank_path>/QC/validation/content_delta.py \
  --base /tmp/port-base/Corpora --head "<formosanbank_path>/Corpora" --corpus <corpus_name>
```

Mismatching what was recorded prevents a merge; the check stays red until the
maintainer overrides it. The skill's part is the **audit artifact** that makes
the override an informed one: publish one page for the re-port listing every
class of change the tool reports (TEXT ids removed or renamed, S removed or
renumbered, elements removed per tier, dialect and licence changes), one row
each with its count, the decision it traces to — a quoted ruling from the
decision log, a disclosure in the PR body, or a POL entry — and, where none
can be found, the flag **"no approved decision found"**. Rows with that flag
are the questions the maintainer answers before overriding; rows with a trace
are what the override is for. Link the page in the Phase 6 summary and the PR
body. (This is the shape the maintainer asked for on PRs #173 and #164.)

**Declared vs detected.** The build declares a dialect (`TEXT/@dialect`) and a
source orthography (`--orthography` / the conversion table in
`generate_xml.sh`); check that the text agrees before the corpus is published:

```bash
<python> <formosanbank_path>/QC/validation/declared_vs_detected.py \
  --xml "<formosanbank_path>/Corpora/<corpus_name>/XML" \
  --generate-xml "<formosanbank_path>/Corpora/<corpus_name>/CodeAndDocs/generate_xml.sh"
```

Quote the three tables in the Phase 6 summary. A row marked MISMATCH is not
a blocker by itself (the detectors are statistical, the dialect models cover
seven languages, and a corpus can legitimately mix sources), but it is a
question for the operator before the PR is opened, never something to fix
silently.

**Waivers are a tool to know, not a step.** `Corpora/<corpus_name>/CodeAndDocs/qc_waivers.tsv`
(POL-054) records a HARD finding the maintainer has ruled waived, so CI stops
failing on it while new findings still fail. Mention it only when a HARD
finding survives and the maintainer says it is acceptable; do not create or
extend it on your own.

**Cross-corpus duplicate check.** Now that the corpus sits alongside the rest of the bank, check whether its sentences already exist in other published corpora with `QC/utilities/find_duplicate_sentences.py` — the cross-corpus complement of `validate_duplicate_sentences.py`, whose within-corpus check already ran during `run-qc-pipeline`. Run once per language in the corpus, from the FormosanBank root (the script's `--corpora` default is `./Corpora`):

```bash
cd <formosanbank_path>

# If the corpus XML is split by language (XML/<Language>/):
<python> QC/utilities/find_duplicate_sentences.py \
  --source-corpus <corpus_name> --language <Language> \
  --output logs/<corpus_name>_<Language>_duplicates.csv

# If the XML is flat (no language subdirs), point at each XML file instead:
<python> QC/utilities/find_duplicate_sentences.py \
  --source-xml "Corpora/<corpus_name>/XML/<file>.xml" --language <Language> \
  --output logs/<corpus_name>_<Language>_duplicates.csv
```

(`logs/` is gitignored, so the CSV stays out of the tree.) Caveats to keep in mind when reading the result:

- Comparison uses the standard tier by default (`--kind-of standard`), matching case-insensitively on whole-sentence text.
- Target files are discovered by looking for `<Language>` as a path component under `Corpora/`, so published corpora with *flat* XML layouts are not scanned as targets — a clean result is informative, not exhaustive.
- Matches are **informational, not blockers** — and per POL-022, expectations differ by corpus type: narratives may legitimately repeat sentences (within and across corpora built from the same materials), while for dictionaries, wordlists, and grammar example collections overlap is worth scrutinizing (repeats should generally be excluded unless the attestations carry distinct provenance). Report the match count and CSV path in the Phase 6 summary; the operator decides whether overlap warrants dropping or annotating anything before opening the PR.

**Privacy leak check.** If any top-level directory of `<source_path>` whose
name begins with `Private` exists — `Private/`, but also `Private:Source/`,
`Private-data/` and the like (the Amis Kuo-Sung dev repo keeps its PDF in
`Private:Source/`, which a check on `Private/` alone never saw) — verify
nothing from it landed in the published corpus. Two layers:

1. **Content-hash check (hard error).** For every file under `<source_path>/Private/`, compute a SHA-256 hash. For every file under `<formosanbank_path>/Corpora/<corpus_name>/`, compute its hash. Any match means a private file's exact content has leaked to the public corpus, regardless of filename — that's a real leak. Abort the port: do not declare Phase 5 success; surface the matching pair(s); recommend the user delete the offending file(s) (or revert the entire port with `rm -r <formosanbank_path>/Corpora/<corpus_name>/`) and investigate how it happened.
2. **Basename collision check (warning, not blocker).** Any file in the published corpus whose basename matches a basename anywhere under `Private/` — even with different content. This catches plausible name reuse (e.g., a `Private/README.md` of operator notes and a public `README.md`). Surface the list for operator review; do not block.

Suggested implementation (run from the model, not pre-baked into a helper):

```bash
python3 <<'EOF'
import hashlib, sys
from pathlib import Path
privs = [p for p in Path("<source_path>").iterdir() if p.is_dir() and p.name.startswith("Private")]
target = Path("<formosanbank_path>/Corpora/<corpus_name>")
if not privs:
    print("OK: no Private* dir in source.")
    sys.exit(0)
print("private dirs:", [p.name for p in privs])
def h(p):
    H = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(8192), b""):
            H.update(c)
    return H.hexdigest()
priv_files = [f for priv in privs for f in priv.rglob("*") if f.is_file()]
priv_by_hash = {h(f): f for f in priv_files}
priv_names = {f.name for f in priv_files}
content_leaks, name_collisions = [], []
for tf in target.rglob("*"):
    if not tf.is_file(): continue
    if h(tf) in priv_by_hash:
        content_leaks.append((tf, priv_by_hash[h(tf)]))
    if tf.name in priv_names:
        name_collisions.append(tf)
if content_leaks:
    print("HARD ERROR: private content leaked to public corpus:")
    for t, p in content_leaks: print(f"  {t}  <-  {p}")
    sys.exit(2)
if name_collisions:
    print("Warning: target filenames also exist under Private/ (different content):")
    for n in name_collisions: print(f"  {n}")
print("OK: no private content leaked.")
EOF
```

### Phase 4b: Is the attestation dictionary stale?

The quote/glottal correction in `clean_xml` reads a precomputed per-language
attestation dictionary (`QC/validation/reference/<Name>/attestation.txt`).
Refreshing it is **not** part of a port (maintainer, 2026-10-17: "Refreshing
the attestation dictionary should be part of building the dev repo (if it is
needed at all) … automatically refreshing doesn't make sense"), and a
corpus PR never changes `QC/` (POL-049). What the port does is check how old
the dictionary is and ask:

```bash
cd <formosanbank_path>
for L in <each language in the corpus>; do
  f="QC/validation/reference/${L}/attestation.txt"
  [ -f "$f" ] || { echo "$L: no attestation dictionary"; continue; }
  echo "$L: attestation last changed $(git log -1 --format=%cs -- "$f"); newest $L corpus merged $(git log -1 --format=%cs -- $(grep -l "xml:lang=\"<iso>\"" -r Corpora/*/XML -m1 --include=*.xml | awk -F/ '{print $1"/"$2}' | sort -u | tr '\n' ' '))"
done
```

If the dictionary predates one or more corpora of that language by months,
raise it as a question in the Phase 6 summary ("the <Name> attestation
dictionary is from <date>; <N> corpora of <Name> merged since — refresh in
its own PR?"). Do not run `build_attestation_dict.py` here and never commit
`QC/validation/reference/` in the corpus PR; a refresh is its own PR, merged
first, with its number noted in the corpus PR body.

### Phase 5: Add to the documentation site

The corpus page on the documentation site (https://formosanbank.github.io/FormosanBank/)
is the corpus README itself, rendered when the site is built, with its statistics
table inserted under `## Statistics`. It ships in this port's own PR; there is no
second repository and no second PR. **Skippable with `skip_docs`** if the operator
wants to defer. Working-tree edits only (this skill is **not a git committer**).

1. **Derive identifiers** and confirm via `AskUserQuestion` (offer defaults, allow override):
   - `slug` — the page's URL name: kebab-case of `corpus_name` (e.g. `Nowbucyang-Truku-Thesis` → `nowbucyang-truku-thesis`).
   - `nav-label` — human label for the site menu and the corpus list.
   - `descriptors` — what the corpus contains, in the style of the existing list (e.g. `text, audio, English, Mandarin`, `audio`, `text, glossing, English`). Derive from the corpus's tiers/audio/translations; confirm with the operator.

2. **Register the page** (one row in `docs/site/corpus_pages.csv`; the menu entry,
   the corpora-index bullet and the statistics table all follow from it):
   ```bash
   <python> <formosanbank_path>/docs/tools/manage_corpus_pages.py add \
     --corpus "<corpus_name>" --slug "<slug>" \
     --nav-label "<nav-label>" --descriptors "<descriptors>"
   ```
   (`<python>` resolved as in Phase 4.)

3. **Check the README layout and registration:**
   ```bash
   <python> <formosanbank_path>/docs/tools/manage_corpus_pages.py check --strict
   <python> -m pytest tests/corpora/test_readme_sections.py -q -k "<corpus_name>"
   ```
   Both must pass. A failure names the heading that is missing or out of order.

4. **Generate the per-corpus stats CSV (audio-aware).**

   a. **Audio gate (detect + guide).** Check whether the ported XML has audio:
      ```bash
      grep -rl "<AUDIO" "<formosanbank_path>/Corpora/<corpus_name>/XML" | head -1
      ```
      - **No match (no audio):** skip to step 4b.
      - **Has audio:** the audio-seconds columns need `statistics/audio_durations.csv`
        populated for this corpus *before* `get_corpus_stats` runs (otherwise audio
        seconds are 0). Do NOT automate this — surface the choice to the maintainer
        via `AskUserQuestion`:
        - *Audio is available locally* (downloaded into the corpus dir) →
          `<python> <formosanbank_path>/QC/utilities/update_audio_stats.py Corpora/<corpus_name>`
        - *Audio is only on Hugging Face* (`download_audio_data.sh` ported + uploaded) →
          use the `refresh-audio-stats` skill / `refresh_audio_stats.py <corpus_name>`
        - *Maintainer chooses to skip:* proceed; note in the Phase 6 summary that the
          page's audio columns are pending a later `refresh-audio-stats` run.

   b. **Generate the CSV:**
      ```bash
      <python> <formosanbank_path>/QC/utilities/get_corpus_stats.py \
        "<formosanbank_path>/Corpora/<corpus_name>"
      ```
      This writes `<formosanbank_path>/statistics/<corpus_name>_corpora_stats.csv`.
      Commit it with the corpus (CI later regenerates the identical CSV via `--all`).
      Do not edit `statistics/language_history.csv`: the corpus-metrics workflow
      extends it after the merge, and the site's growth figures follow.

5. **Build the site and look at the page:**
   ```bash
   <python> <formosanbank_path>/docs/tools/build_site.py
   ```
   It must end `link check clean`. The page is at
   `site/the-bank-architecture/corpora/<slug>/index.html`; confirm its statistics
   table shows the corpus's languages, and that the corpus appears on each of its
   languages' pages under `site/languages/`.

### Phase 6: Summary

Print:
- What was created (paths)
- What was dropped (paths)
- The gate: "N new HARD in xml / text / glosses vs main" (three numbers), SOFT findings by rule with a one-line description each
- Static build-shape tests for this corpus: pass count
- The build run: "generate_xml.sh ran in <time>; git status clean" (or what it changed / why it stopped)
- The corpus's own tests: pass count, and whether the source-accounting test ran or skipped
- Re-port only: the content-delta lines and the link to the audit artifact (rows traced / rows flagged "no approved decision found")
- Attestation dictionary: age per language, and the refresh question if it is stale
- Spot-check results
- Cross-corpus duplicate check: match count per language + CSV path(s), or why it was skipped
- Declared vs detected: the three tables from `declared_vs_detected.py`, every MISMATCH row called out
- Audio parity (if has_audio): the `sync_hf_audio.py` dry-run counts (referenced / on the Hub / to upload / to delete)
- Documentation site: registered as `<slug>` in `docs/site/corpus_pages.csv`; `build_site.py` result line
- Stats table from `<corpus_name>_corpora_stats.csv` (audio columns pending if the audio-durations step was skipped).
- Open items, e.g.:
  - "README is a stub — please flesh out the {{PROCESSING_STEPS}} section (What each step does) before opening a PR"
  - "XSD validation failed on N files — investigate before opening PR"
  - "audio download script copied but not tested; run it to verify it still works in the published location"
  - "Privacy leak check: <result> (clean / N basename collisions to review / HARD ERROR)"
- Recommended next steps:
  - Review the new `Corpora/<corpus_name>/` contents
  - Commit and open a PR — the PR body carries what Phase 6 printed: the three gate counts, the build result, the test counts, and (re-port) the audit artifact link and every removal with its reason (POL-051)

## Decisions the skill surfaces (does NOT guess)

- Monolithic XML splitting (if applicable)
- Ambiguous source layouts (multiple plausible XML locations)
- README handling when source has none
- Whether to copy or move source files
- Whether QC evidence is sufficient to proceed

## What this skill is NOT

- Not a fix-it tool. If QC found problems, fix them in the dev repo (or accept them) before porting; don't try to fix during port.
- Not a git operation. Creates files in the working tree; user commits.
- Not a force-port. Will refuse to overwrite an existing published corpus.

## Data files change only via code (POL-038)

Never modify XML or raw scrape files by hand or ad hoc — only via committed code (pipeline scripts, `manual_edits.xml` via the capture/apply tooling, or a one-off script committed to `CodeAndDocs/`). This includes POL-035 snapshots: fix snapshot defects with a committed script, never a direct edit. A non-code edit is unreproducible and is destroyed on regeneration.
