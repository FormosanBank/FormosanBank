# Rebuilding NTUFormosanCorpus from source

The JSON files under [`../grammar/`](../grammar/), [`../sentence/`](../sentence/)
and [`../story/`](../story/) are this corpus's starting point. Nothing is
scraped, so there is no refresh step — those JSONs *are* the source, and
everything in `../../XML/` is derived from them by this directory.

```bash
source ../../../../.venv/bin/activate
./build.sh              # or: ./build.sh grammar | sentences | stories
```

`build.sh` writes `../../XML/{Grammar,Sentences,Stories}` from scratch
(each subcorpus is built in a temp dir and installed only on success), and
is idempotent — rerunning it is safe and should produce byte-identical XML.

## What runs, in order

Each subcorpus goes through three phases.

**A. Builder — JSON → XML.** One script per subcorpus, sharing its helpers
with `pipeline_grammar.py`:

| subcorpus | builder | steps |
|---|---|---|
| Grammar | `pipeline_grammar.py` | 1–17, 19, 21, 22 |
| Sentences | `pipeline_sentences.py` | 0–5, 7–11, 14, 15, 18 |
| Stories | `pipeline_stories.py` | 0–5, 7–11, 14–16, 18 |

`--list-steps` on any builder prints the numbered step list with a one-line
description of each. The numbers are *creation* order, not application
order; `--steps` selects which run, and `build.sh` pins the sets above.

**B. Repairs.** `QC/cleaning/clean_xml.py` from the bank, then the
per-subcorpus repair scripts in [`../scripts/`](../scripts/) — infix
notation, optional parentheticals, annotation codes, clitic boundaries, and so
on. Grammar and the two flat subcorpora use overlapping but not identical
chains; `build.sh` is the authority.

`repair_translation_parentheticals.py` is **not** run. It encodes a completed
human review of 453 candidate translations plus a SHA-256 of that population,
and no corpus state now yields it (the published corpus yields 0, this build
140), so it can never fire. Its job — moving transcriber and translator
commentary out of the translation text and into `@notes` — is done at build
time instead by `utils.extract_notes`, which handles every parenthetical span,
ASCII or fullwidth, anywhere in the string. The ~60 "naturalistic elaborations"
that review chose to keep inline are not preserved; that is accepted.

**C. Tiers.** `resolve_slash_alternatives.py` (competing readings →
`kindOf="alternate"`), `apply_prune_and_mirror.py --only prune` (drop
M elements that carry no morphological evidence, per POL-054),
`borrow_missing_morphemes.py`, `align_ids.py` (keep ids stable against the
published corpus, per POL-037), then `run_standard_and_phon.sh`, which
builds the standard tier and both PHON tiers against **Ortho94** — the
orthography the NTU source documentation declares. (Earlier processing
declared Ortho113; see the header of that script.)

## Data tables

Per POL-039, item-specific corrections live in data files, not in code:

- `free_translation_repairs.tsv` — free-translation fixes keyed by sentence id
- `audio_overrides.tsv` — AUDIO suppression beyond the `沒有音檔` sentinel
- `p2_source_repairs.xml` — recorded whole-record source repairs, each pinned to
  a SHA-256 of the record it replaces so a drifting source fails the build
- `gloss_restorations.tsv` — 1,320 gloss cells that the audited source output
  blanked to the `_` absent-gloss placeholder but which the previously published
  source carries as real glossing (978 lexical/grammatical, 342 discourse codes;
  96% of them in three Saisiyat story files). Restored at load time, each keyed
  by source file, record, row and cell and carrying the wordform as a witness,
  so the corpus keeps the audited source's row realignments *and* this glossing.

  Measured on the Stories subcorpus, this hybrid beats both alternatives:

  | | W FORM + both glosses | M with both glosses | morpheme count matches |
  |---|---|---|---|
  | audited source as-is | 99.1% | 99.1% | 98.9% |
  | previously published source | 99.3% | 98.3% | 98.4% |
  | **hybrid (this table)** | **99.7%** | **99.2%** | **98.9%** |

  Restoring the 342 discourse codes (`BC`, `FIL`, `DM`, `FS`) along with the 978
  lexical glosses scores better than leaving them blanked, so they are restored
  too. Blanking them at source is not a policy the corpus follows anywhere else:
  ~16,000 such glosses exist corpus-wide and the audited source zeroed only 672
  of them (93% of `BC`, but 0.3% of `FIL`). If they should go, that belongs in
  the cleaning stage as a rule applied to all of them, not in the source.

## Environment

| variable | default | why you'd set it |
|---|---|---|
| `PYTHON` | `<bank>/.venv/bin/python` | building from a git worktree, which has no `.venv` |
| `CTABLES` | `<bank>/Orthographies/ConversionTables` | testing an unmerged conversion table |
| `FB_DIALECTS` | `<bank>/dialects.csv` | testing an unmerged dialect/alias row |

## Checking a rebuild

[`../qa/`](../qa/) holds the regression harness: it re-scores a rebuilt tree
against the recorded baseline and reports any test that moved. Run it after
any change here — see `../qa/README.md`.
