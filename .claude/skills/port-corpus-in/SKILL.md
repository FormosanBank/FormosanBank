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
- `skip_gitbook` — default `false`. If `true`, Phase 5 (Add to GitBook) is skipped and the operator publishes the GitBook page later.

## Pre-checks

1. Verify `source_path` exists.
2. Verify `formosanbank_path/Corpora/` exists.
3. Verify target `formosanbank_path/Corpora/<corpus_name>/` does NOT already exist. Refuse if it does — operator decides whether to merge, replace, or pick a new name.
4. Look for recent QC evidence in `source_path`:
   - `qc-output/<latest-timestamp>/qc-summary.md` exists, OR
   - User explicitly passed `assume_qc_passed=true`.
   - If neither: surface to user. Either ask to run `run-qc-pipeline` first or to set `assume_qc_passed=true`.

## Recipe phases

### Phase 1: Assess source layout

Read `source_path` top-level. Identify and report:

- Does a `README.md` exist?
- Where is the XML? Detect:
  - `XML/` (standard already)
  - `Final_XML/` (common in dev repos)
  - `xml/<chapter>.xml` (common for chapter-segmented corpora)
  - Root-level `*.xml` (monolithic — see below)
- Is the XML monolithic (single file with many `<TEXT>` or `<S>` elements)? If yes, prompt the user: "This corpus has a monolithic XML. Run `split-monolithic-xml` first, then re-invoke port-corpus-in. Do NOT proceed without splitting." (`split-monolithic-xml` is a deferred-backlog item; it may not exist yet.)
- What scripts exist (at root or in a `scripts/` subdir) that likely belong in `CodeAndDocs/`?
- What source data artifacts exist at root (e.g., original PDFs, extracted text files, decrypted source documents) that may belong in `CodeAndDocs/` for reproducibility — *unless* they contain private content per CLAUDE.md's "private source data" caveat, in which case surface to user.
- What scratch dirs exist that should be dropped (`data/`, `raw_data/`, `Original/`, `img-by-page/`, `text-by-page/`, `logs/`, etc.)?
- Does `Private/` exist? If yes, list its contents in the report under a clear "WILL NOT BE PORTED" heading. Do not surface it as a candidate for copying at any point in Phase 2.
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

# README: either copy or generate from template
# If copy:
cp <source README> "<formosanbank_path>/Corpora/<corpus_name>/README.md"
# If generate: render template at .claude/skills/port-corpus-in/README.template.md
# with substitutions from QC summary + user input.

# Audio:
# If has_audio: cp <source download_audio_data.sh> "<formosanbank_path>/Corpora/<corpus_name>/"
```

Drop nothing from the source dev repo unless explicitly approved.

### Phase 4: Validate after port

Run `validate_xml.py` on the new published XML to confirm DTD/XSD conformance.
`--no-exit-on-hard` lets us inspect findings rather than aborting the skill
on first failure; HARD findings appear on stderr regardless.

```bash
<python> <formosanbank_path>/QC/validation/validate_xml.py by_path \
  --path "<formosanbank_path>/Corpora/<corpus_name>/XML" --no-exit-on-hard
```

**Resolve `<python>` in this order:**
1. `<source_path>/.venv/bin/python3` if it exists (dev repos created via `setup-new-dev-repo` have one)
2. Otherwise `<formosanbank_path>/.venv/bin/python3` — FormosanBank always has a venv with the deps
3. If neither, refuse and tell the user to install one before validating

Quick spot-check counts (file count, total size) vs source. If discrepancies, report — do not auto-fix.

**Privacy leak check.** If `<source_path>/Private/` exists, verify nothing from it landed in the published corpus. Two layers:

1. **Content-hash check (hard error).** For every file under `<source_path>/Private/`, compute a SHA-256 hash. For every file under `<formosanbank_path>/Corpora/<corpus_name>/`, compute its hash. Any match means a private file's exact content has leaked to the public corpus, regardless of filename — that's a real leak. Abort the port: do not declare Phase 5 success; surface the matching pair(s); recommend the user delete the offending file(s) (or revert the entire port with `rm -r <formosanbank_path>/Corpora/<corpus_name>/`) and investigate how it happened.
2. **Basename collision check (warning, not blocker).** Any file in the published corpus whose basename matches a basename anywhere under `Private/` — even with different content. This catches plausible name reuse (e.g., a `Private/README.md` of operator notes and a public `README.md`). Surface the list for operator review; do not block.

Suggested implementation (run from the model, not pre-baked into a helper):

```bash
python3 <<'EOF'
import hashlib, sys
from pathlib import Path
priv = Path("<source_path>/Private")
target = Path("<formosanbank_path>/Corpora/<corpus_name>")
if not priv.is_dir():
    print("OK: no Private/ dir in source.")
    sys.exit(0)
def h(p):
    H = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(8192), b""):
            H.update(c)
    return H.hexdigest()
priv_by_hash = {h(f): f for f in priv.rglob("*") if f.is_file()}
priv_names = {f.name for f in priv.rglob("*") if f.is_file()}
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

### Phase 5: Add to GitBook

Publishing a corpus into `Corpora/` is only half-done until it appears in the
public GitBook. This phase wires the corpus's four GitBook integration points
(its own page, the `SUMMARY.md` nav entry, the `corpora/README.md` corpus-list
bullet, and the `CSV_TO_MD` stats map) using the GitBook repo's helper, then fills
the page prose. **Skippable with `--skip-gitbook`** if the operator wants to defer.

The helper does the mechanical edits; the skill (you) writes the prose. The
skill makes working-tree edits only — the operator commits and opens the GitBook
PR separately (this skill is **not a git committer**, consistent with Phase 3).

1. **Locate the GitBook repo.** Default sibling `<formosanbank_path>/../FormosanBankGitbook`.
   If absent, ask the operator for the path or offer to skip this phase.

2. **Resolve the publish branch (Roadmap Part D / Layer 0 is unresolved).** Report
   the current divergence so the operator can choose:
   ```bash
   cd <gitbook_path>
   git fetch --quiet
   echo "main ahead of en-us by: $(git rev-list --count origin/en-us..main 2>/dev/null || echo '?')"
   echo "en-us ahead of main by: $(git rev-list --count main..origin/en-us 2>/dev/null || echo '?')"
   ```
   Then `AskUserQuestion`: "Which branch does GitBook publish from? I'll make the
   page edits on a fresh feature branch off it." Check out / create a feature
   branch off the operator's choice in the GitBook working tree. Do NOT hardcode
   a branch.

3. **Derive identifiers** and confirm via `AskUserQuestion` (offer defaults, allow override):
   - `slug` — kebab-case of `corpus_name` + `.md` (e.g. `Nowbucyang-Truku-Thesis` → `nowbucyang-truku-thesis.md`).
   - `nav-label` — human label for the table of contents AND the corpus list.
   - `title` — the page H1.
   - `descriptors` — the trailing parenthetical for the corpus-list bullet, summarizing what the corpus contains, in the style of the existing list (e.g. `(text, audio, English, Mandarin)`, `(audio)`, `(text, glossing, English)`). Derive from the corpus's tiers/audio/translations; confirm with the operator.

4. **Scaffold the four integration points** with the helper, passing the skill's template:
   ```bash
   <python> <gitbook_path>/manage_corpus_pages.py add \
     --gitbook-root "<gitbook_path>" \
     --corpus "<corpus_name>" \
     --slug "<slug>" \
     --nav-label "<nav-label>" \
     --title "<title>" \
     --descriptors "<descriptors>" \
     --template "<formosanbank_path>/.claude/skills/port-corpus-in/corpus_page.template.md"
   ```
   This wires: the page, the `SUMMARY.md` nav bullet, the `corpora/README.md` corpus-list bullet, and the `CSV_TO_MD` stats-map entry. (`<python>` resolved as in Phase 4.)

5. **Fill the prose placeholders** in `<gitbook_path>/en-us/the-bank-architecture/corpora/<slug>`,
   reading the corpus README + QC summary:
   - `{{DESCRIPTION}}` — 1–3 sentences on what the corpus is and where it came from.
   - `{{COPYRIGHT}}` — the license/copyright line (e.g. `CC BY-NC`).
   - `{{CITATION}}` — APA-style citation(s); multiple separated by `|` per the XML format conventions.
   - `{{ACCESS}}` — the standard access line:
     `* The repo containing this corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/<corpus_name>).`

6. **Verify the page is fully wired and placeholder-free:**
   ```bash
   <python> <gitbook_path>/manage_corpus_pages.py check \
     --gitbook-root "<gitbook_path>" \
     --corpora-path "<formosanbank_path>/Corpora" \
     --strict
   ```
   A leftover `{{...}}` placeholder or a missing integration point (page / nav / README
   list / stats-map) fails this — fix before declaring the phase done. At this point
   `check` also reports an **informational** "Missing stats CSV" line for the new corpus
   (its stats CSV doesn't exist yet); that is expected *here* and is resolved by step 7
   below, which generates the CSV and injects the tables. Because that line does not
   gate, a `--strict` failure at this step means a real integration problem, not the
   pending stats.

7. **Populate the stats tables (audio-aware).** The page's stats block and the
   `corpora/README.md` aggregate are filled by `update_corpus_stats.py` from the
   corpus's stats CSV. Generate that CSV and inject it, in this order:

   a. **Audio gate (detect + guide).** Check whether the ported XML has audio:
      ```bash
      grep -rl "<AUDIO" "<formosanbank_path>/Corpora/<corpus_name>/XML" | head -1
      ```
      - **No match (no audio):** skip to step 7b.
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

   b. **Generate the per-corpus stats CSV:**
      ```bash
      <python> <formosanbank_path>/QC/utilities/get_corpus_stats.py \
        "<formosanbank_path>/Corpora/<corpus_name>"
      ```
      This writes `<formosanbank_path>/statistics/<corpus_name>_corpora_stats.csv`.
      Commit it with the corpus (CI later regenerates the identical CSV via `--all`).

   c. **Inject the tables into the GitBook:**
      ```bash
      <python> <gitbook_path>/update_corpus_stats.py --stats-dir "<formosanbank_path>/statistics"
      ```
      Pass `--stats-dir` explicitly so it reads the *active* FormosanBank checkout
      (the sibling default may point at a different checkout that lacks the new CSV).
      This fills the new page's stats block and refreshes the `corpora/README.md`
      aggregate. Commit the changed `.md` in the GitBook repo.

   d. **Re-verify:** `manage_corpus_pages.py check --strict` passes and the new
      corpus's "missing stats CSV" informational line is gone.

### Phase 6: Summary

Print:
- What was created (paths)
- What was dropped (paths)
- DTD validation result
- Spot-check results
- GitBook page: <path>
- Stats tables populated from `<corpus_name>_corpora_stats.csv` (audio columns pending if the audio-durations step was skipped).
- "GitBook page created on branch <chosen>; commit and open the GitBook PR separately."
- Open items, e.g.:
  - "README is a stub — please flesh out the {{REPRODUCIBILITY_STEPS}} section before opening a PR"
  - "DTD validation failed on N files — investigate before opening PR"
  - "audio download script copied but not tested; run it to verify it still works in the published location"
  - "Privacy leak check: <result> (clean / N basename collisions to review / HARD ERROR)"
- Recommended next steps:
  - Review the new `Corpora/<corpus_name>/` contents
  - Commit and open a PR

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
