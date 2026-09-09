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
- `p2_source_repairs.xml` — recorded whole-record source repairs, each pinned to
  a SHA-256 of the record it replaces so a drifting source fails the build

## Which source JSONs

The JSONs under `../grammar`, `../sentence` and `../story` are the ones this
corpus has always published. An "audited source output" revision of 207 of them
exists on the `fix/ntu-gloss-placeholder` branch, but **no script in the
repository produces it**: every `json.dumps` in `../scripts/` computes a SHA-256
digest, and nothing reads a source JSON and writes it back. That revision is
therefore unauditable and unreproducible, and this build does not use it.

It also is not simply better. Adjudicating the contested gloss rows against
glosses from records both versions agree on (a lexicon of 32,417 wordforms drawn
only from uncontested records), the published source carries the attested gloss
1,154 times against that revision's 682, with a larger margin (84,140 vs 56,165).
Its characteristic error is an off-by-one gloss shift: `ila` PFV (attested 363x)
becomes empty, `a` FIL (305x) becomes `IRR` (0x), `yau` EXIST (256x) becomes
`one` (0x).

Note that the QA suite in [`../qa/`](../qa/) **cannot detect this**. Its tests
measure structural completeness — both glosses present, morpheme counts matching
— so a gloss shifted onto the wrong word passes all of them. A higher QA score
is not evidence of better glossing.



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
