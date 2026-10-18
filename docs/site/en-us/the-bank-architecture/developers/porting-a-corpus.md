---
icon: box-open
---

# Porting a Corpus In

Once a corpus has passed [QC](qc-pipeline/README.md) and any [audit](running-an-audit.md) findings are resolved, it is **ported** from its dev repo (`Formosan-<Name>/`) into FormosanBank's published tree (`Corpora/<Name>/`) with the standard layout, and registered on this site (its README becomes its page). This page describes that as a manual procedure — and, importantly, the **decisions you have to make** along the way that the guided [`port-corpus-in` Claude skill](using-the-claude-skills.md) would otherwise prompt you for.

{% hint style="warning" %}
**Port only QC'd corpora.** Porting is not a fix-it step. If QC found problems, fix them in the dev repo (or consciously accept them) *before* porting — don't try to repair data during the port.
{% endhint %}

## The published layout

A ported corpus lives at `Corpora/<Name>/` and contains:

- `README.md` — what the corpus is, where the source came from, and how to reproduce `XML/`.
- `XML/`: the canonical published data, optionally grouped by language, subcorpus, or speaker (see [Folder structure](folder-structure.md)).
- `CodeAndDocs/` — the scripts and docs needed to **reproduce** `XML/` from the source.
- `download_audio_data.sh`: **only** when remotely hosted audio must be retrieved.

## The hard invariant: nothing from `Private/`

Dev repos created with the [`setup-new-dev-repo` skill](using-the-claude-skills.md) have a `Private/` folder for development-only material that must never ship — decryption keys, draft notes, source data with private content. **Nothing under `Private/` is ever copied into FormosanBank.** Treat it as out of scope at every step, and verify after the port (see Step 4) that nothing leaked.

## What you need

- The corpus dev repo at a known path, with recent QC evidence (e.g. a `qc-output/<timestamp>/qc-summary.md`). If there is none, run QC first.
- A local FormosanBank clone with `Corpora/` present and the `.venv` active.

Refuse to proceed if `Corpora/<Name>/` already exists — decide whether to merge, replace, or rename before overwriting anything.

## The procedure

### 1. Assess the source layout

Inspect the dev repo's top level and identify:

- Whether a `README.md` exists.
- Where the XML lives: `XML/` (standard), `Final_XML/` (common in older dev repos), `xml/<chapter>.xml`, or a root-level monolithic `*.xml`. **A monolithic single-file XML must be split into per-`TEXT` files first** — do not port it as-is.
- Which scripts (root or `scripts/`) belong in `CodeAndDocs/`.
- Which source artifacts (PDFs, extracted text) belong in `CodeAndDocs/` for reproducibility — *unless they contain private content*.
- Which scratch dirs to drop (`data/`, `raw_data/`, `Original/`, `img-by-page/`, `logs/`, …).
- Whether `Private/` exists (list it as **will not be ported**) and whether there's a `download_audio_data.sh`.

### 2. Decide the plan

This is the step the skill exists to make explicit. **Before touching the filesystem**, settle each of these — they are judgment calls a conversation with Claude would otherwise resolve:

| Decision | Default | Notes |
|----------|---------|-------|
| **Corpus name** | source name minus the `Formosan-` prefix | The published `Corpora/<Name>/` directory name. |
| **Which XML to copy** | the detected `XML/` (or `Final_XML/`) tree | If the layout is ambiguous (multiple plausible XML locations), pick deliberately. |
| **What goes in `CodeAndDocs/`** | reproduction scripts + non-private source docs | Everything needed to rebuild `XML/` from source. |
| **What to drop** | scratch/build dirs; **always** `Private/` | Never offered as a copy candidate. |
| **README handling** | copy as-is, generate from a template, or skip | If the source has none, generate from the template and flesh it out. |
| **Copy or move?** | copy (leave the dev repo intact) | |
| **Include `download_audio_data.sh`?** | yes iff the corpus has audio | |

### 3. Execute the plan

Create the target layout and copy the approved items. Drop nothing from the source unless explicitly decided.

```bash
mkdir -p Corpora/<Name>/XML Corpora/<Name>/CodeAndDocs
cp -r <source>/XML/*            Corpora/<Name>/XML/
cp     <source>/<scripts>       Corpora/<Name>/CodeAndDocs/
cp     <source>/README.md       Corpora/<Name>/README.md      # or generate from a template
# audio corpora only:
cp     <source>/download_audio_data.sh  Corpora/<Name>/
```

### 4. Validate after the port

Run the mechanical port-readiness gate — on the source dev repo (ideally you already did, before step 1) and on the ported copy:

```bash
python QC/validation/validate_port_readiness.py --corpus_path ../Formosan-<Name>
python QC/validation/validate_port_readiness.py --corpus_path Corpora/<Name>
```

It exits 1 on blockers (git-tracked `Private/` content, unknown `xml:lang`, non-canonical dialect) and warns on judgment calls (divergent commit pins in README/sidecars, stale audio statistics, unvalidated conversion tables). See [validate\_port\_readiness.py](qc-pipeline/validate-port-readiness.md) for the full check list.

Then confirm the published XML still conforms, and run the privacy-leak check.

```bash
python QC/validation/validate_xml.py by_path --path Corpora/<Name>/XML --no-exit-on-hard
```

`--no-exit-on-hard` lets you inspect findings rather than aborting on the first one; HARD findings still appear on stderr. Spot-check file counts and total size against the source.

**Privacy-leak check (only if `Private/` exists).** Two layers:

1. **Content-hash check (hard error).** Hash every file under `Private/` and every file under `Corpora/<Name>/`. Any matching hash means private content leaked, regardless of filename — abort the port, surface the pair, and revert (`rm -r Corpora/<Name>/`).
2. **Basename-collision check (warning).** Any published file whose *basename* also appears under `Private/` (even with different content) — surface for review; not a blocker.

### 5. Add to the documentation site

The corpus page on this site **is the corpus README**, rendered when the site is built with the statistics table inserted under `## Statistics`. It ships in the port's own pull request; there is no second repository.

1. **Make sure the README follows the corpus layout** (headings in order: Languages and dialects, Source, Statistics, How to cite, License, Notes and caveats, Reproduction and processing; POL-055). The template is `.claude/skills/port-corpus-in/README.template.md`.
2. **Decide the page identifiers**: the page `slug` (its URL name, kebab-case), the menu label, and the "descriptors" for the corpus list (e.g. `text, audio, English, Mandarin`) derived from the corpus's tiers/audio/translations.
3. **Register the page** (one row in `docs/site/corpus_pages.csv`; the menu entry, the corpus-list bullet and the statistics table follow from it):

   ```bash
   python docs/tools/manage_corpus_pages.py add \
     --corpus "<Name>" --slug "<slug>" --nav-label "<label>" --descriptors "<descriptors>"
   ```
4. **Generate the per-corpus stats CSV (audio-aware):**

   ```bash
   # If the corpus has audio, populate audio seconds FIRST (see decision below), then:
   python QC/utilities/get_corpus_stats.py Corpora/<Name>     # writes statistics/<Name>_corpora_stats.csv
   ```

   {% hint style="warning" %}
   **Audio decision.** If the corpus has audio, the audio-seconds columns need `statistics/audio_durations.csv` populated *before* `get_corpus_stats.py` runs, or they come out 0. Choose: run [update_audio_stats.py](qc-pipeline/audio-duration-stats.md) if the audio is local; use [refresh_audio_stats.py](qc-pipeline/audio-duration-stats.md) if it's only on Hugging Face; or skip and note that the page's audio columns are pending a later refresh.
   {% endhint %}
5. **Verify**: `python docs/tools/manage_corpus_pages.py check --strict` passes, and `python docs/tools/build_site.py` ends with `link check clean`. Open `site/the-bank-architecture/corpora/<slug>/index.html` and check the table.

### 6. Summarize and commit

Record what was created, what was dropped, the validation result, the privacy-leak result, and any open items (README still a stub, audio columns pending, etc.). The port itself makes working-tree changes only — **you commit and open the pull request** (one, containing the corpus and its page). The new `statistics/<Name>_corpora_stats.csv` is committed with the corpus; CI later regenerates an identical CSV.

## Decisions you own (the skill never guesses these)

- Monolithic-XML splitting, when applicable.
- Ambiguous source layouts (multiple plausible XML locations).
- README handling when the source has none.
- Copy vs move of source files.
- Whether the QC evidence is sufficient to proceed.
- Whether translation updates are in scope for the port. The English `en-us` branch remains canonical.
- How to populate audio seconds (local vs HF vs defer).

## Related

- [Running an Audit](running-an-audit.md)
- [Using the Claude Skills](using-the-claude-skills.md)
- [get_corpus_stats.py](qc-pipeline/get-corpus-stats.md) · [Audio duration stats](qc-pipeline/audio-duration-stats.md)
- [Folder structure](folder-structure.md)
