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
`kindOf="alternate"`), `drop_punctuation_morphemes.py` and
`apply_prune_and_mirror.py` (see "Word and morpheme tiers" below),
`mark_original_glosses.py`, `align_ids.py` (keep ids stable against the
published corpus, per POL-037), then `run_standard_and_phon.sh`, which
builds the standard tier and both PHON tiers against **Ortho94** — the
orthography the NTU source documentation declares. (Earlier processing
declared Ortho113; see the header of that script.)

## Word and morpheme tiers

What the build does when the word or morpheme tier cannot stand, and why. All
three rules are maintainer rulings, recorded in the decision log.

- **Punctuation-only morphemes** (`drop_punctuation_morphemes.py`, ruling
  2026-09-28). A false start written with its punctuation (`ta-,`) splits into a
  morpheme whose form is `,`. In a multimorphemic word, an unglossed
  punctuation-only morpheme is deleted. A glossed one, when fewer segments are
  glossed than there are segments, is deleted and its gloss shifted onto the
  segment after it. If no segment follows it, or no unglossed segment follows to
  absorb the shift, it is left and reported in
  `logs/punctuation_morpheme_escalations_<subcorpus>.tsv`. The word's FORM keeps
  its punctuation: that is source text.
- **Word tier withdrawn** (`apply_prune_and_mirror.py`, ruling 2026-09-08). A
  sentence whose word tier does not account for its sentence form loses its W
  elements.
- **Unreconcilable morphemes rebuilt, unglossed** (`apply_prune_and_mirror.py`,
  ruling 2026-09-09: "regenerate the Ms from the W's segmentation and do not
  include glosses in the Ms"). This is judged word by word. A word whose
  morphemes cannot be reconciled with its form and gloss gets one M per piece of
  its own segmented FORM, with no glosses: the segmentation is real data, but no
  confirmed morphosyntactic glossing exists. A word of one piece gets no M ("a
  lack of Ms indicates no clear segmentation"). Every other word keeps its Ms; a
  glossed one-morpheme word keeps its own single M. **No morpheme is ever copied
  from another word.** Until 2026-09-28 this step, and the separate
  `borrow_missing_morphemes.py` (now deleted), copied glossed morphemes from the
  first occurrence of the same word form anywhere in the subcorpus, in any
  language. That was never ruled.
- **A word left bare by a gloss-shift repair** (`borrow_shift_blank_glosses.py`,
  ruling 2026-09-28) may borrow a gloss. It does so only from the same language,
  only when at least 5 other occurrences exist and one gloss accounts for at
  least 90% of them (placeholders such as `FIL` and `XX` don't count), and it
  marks the gloss with a `notes` attribute. Words that were already bare in the
  source are never filled. Declined cases are reported in
  `logs/gloss_shift_borrowed_<subcorpus>.tsv`.

The policy behind the morpheme rules is "the M tier is evidence, never
manufactured": POL-057 on the unmerged `policy/m-tier-is-evidence` branch. It
was numbered POL-054 before 2026-09-10; POL-054 on `main` is now the waivers
policy.

## Data tables

Per POL-039, item-specific corrections live in data files, not in code:

- `free_translation_repairs.tsv` — free-translation fixes keyed by sentence id
- `audio_overrides.tsv` — AUDIO suppression beyond the `沒有音檔` sentinel
- `p2_source_repairs.xml` — recorded whole-record source repairs, each pinned to
  a SHA-256 of the record it replaces so a drifting source fails the build
- `gloss_shift_repairs.tsv` — gloss-shift corrections (see below), applied at
  load time by all three builders; only rows with status `accepted` take effect

## Gloss shifts

Some source records carry their word glosses one word away from the words they
belong to: a gloss went missing (or was fused with a separately written
clitic's), every later gloss in the intonation unit slid one word left, and the
unit's last word was left bare. In Atayal `hunting3_Takun` record 15 the case
marker `ku` carries `climb-LF=1SG.GEN` and the verb `rakiyas-an=mu` has nothing.
The displacement is in NTU's JSON itself, not introduced by this build.

The source JSONs are never edited. A correction is a row in
`gloss_shift_repairs.tsv`, pinned to the SHA-256 of the record(s) it targets,
naming one of a closed set of operations — `shift_right` (a cell is missing),
`shift_left` (a spurious blank), `split` (two glosses fused into one cell),
`merge` (one gloss cut in two), `swap` (the two gloss columns exchanged), and
`fill` (the only operation that writes text, refused without a named
reviewer). Every operation except `fill` is checked mechanically to have moved
cells without changing their content. See `gloss_shift.py`.

```bash
# propose repairs (nothing is applied; output is for review)
python find_gloss_shifts.py --language Atayal --out-dir /tmp/shifts
# trial the proposals in a scratch build and check the blast radius
../qa/try_gloss_shift_repairs.sh stories accepted,proposed /tmp/blast.md
```

`find_gloss_shifts.py` scores each candidate against the rest of the language,
leave-one-out. A repair is proposed only if it raises the number of
(word, gloss) pairs attested elsewhere (placeholder glosses such as `XX`, `??`,
`FIL`, `FS` and `BC` are not evidence). It must also not lower morpheme-count
agreement (checked per gloss language), plain-text reconstruction, the number
of uncontradicted glosses, or the number of words whose English and Chinese
glosses are a pair seen elsewhere. Words a repair leaves bare are reported, not
refused. For each one the report shows how the same word is glossed elsewhere
*in the same language*, as a suggestion for a reviewer to turn into a `fill`
row. Apparatus never receives a gloss: pauses, punctuation, `(LAUGH)`-style
notes, lone `<L2J` tags and speaker labels with a colon (`F:`, `S,G,W:`). The
patterns are `pipeline_stories.py` step 15's own. A lone capital with no colon
(`E==`, `X`) is a word slot, because the builder keeps it once it is glossed.
Grammar and Sentences are scanned one sentence per record, as their builders
publish them. Where equally good windows compete, the detector picks the
*shortest*, so the start of a span may be too late. The report lists the
competing windows, and every row needs a reader of the language before it is
accepted.

`../qa/try_gloss_shift_repairs.sh` builds the subcorpus twice into scratch
directories (never `XML/`): once without the repairs and once with them. Both
builds stop at `build.sh`'s pre-cleanup checkpoint (`NTU_BUILD_CHECKPOINT`).
The clean-up steps (prune and empty-translation removal) deal with what
could not be fixed, so they count neither for nor against a fix. Measured after
them, the 245 Stories proposals of 2026-09-28 appeared to change 26 unrelated
sentences, all through prune's donor morphemes (since removed), and 6 targets disappeared
because prune withdrew their word tier. `../qa/gloss_shift_blast_radius.py`
compares the two builds by (language, sentence id) and fails if anything
outside the targets changed.

## Which source JSONs

The JSONs are NTU's own published output. `liao961120/glossParser` builds them
from the linguists' gloss files and publishes every release to its public
`gh-pages` branch, served at https://yongfu.name/glossParser/. NTU's corpus
site (https://corpus.linguistics.ntu.edu.tw/) reads the same store.

This corpus builds from **NTU's release of 2026-01-10** (gh-pages `48b9e0b`),
adopted 2026-09-28 by maintainer ruling. `../source_release.tsv` maps every
local file to the upstream file it comes from. NTU renames files between
releases (54 are now `*_revised`/`*_edited`), and re-published its edits of two
Atayal stories under names ending in a space. Five upstream files are
deliberately excluded, each with its reason: two superseded old names, and three
alternative transcriptions of texts we already have (open questions).
`../refresh_source.sh` fetches exactly that release and verifies every file's
SHA-256 (`--check` compares, `--latest` reports whether NTU has released since).
It also rewrites `../source_snapshot.json`, which
`../scripts/verify_source_snapshot.py` checks.

History: until 2026-09-28 the corpus built from NTU's release of 2024-04-08
(`3571fd6`). Six of those files carried unrecorded hand edits: four Sakizaya
stories with their backspace characters deleted (the builders strip those
anyway), Kanakanavu `05.json` record 4, and `ap1.json` record 78. The last two
are also fixed, better, by the pinned replacements in `p2_source_repairs.xml`,
which are now re-pinned to NTU's own records. PR #161 had adopted the 2026
release on 2026-08-22, and `2b738f947` reverted it as "unauditable". It is in
fact auditable against NTU's gh-pages history.

Note that the QA suite in [`../qa/`](../qa/) **cannot detect this**. Its tests
measure structural completeness (both glosses present, morpheme counts
matching), so a gloss shifted onto the wrong word passes all of them. A higher
QA score is not evidence of better glossing.

## Environment

| variable | default | why you'd set it |
|---|---|---|
| `PYTHON` | `<bank>/.venv/bin/python` | building from a git worktree, which has no `.venv` |
| `CTABLES` | `<bank>/Orthographies/ConversionTables` | testing an unmerged conversion table |
| `FB_DIALECTS` | `<bank>/dialects.csv` | testing an unmerged dialect/alias row |
| `NTU_BUILD_OUT` | `../../XML` | installing a trial build somewhere else (XML/ untouched) |
| `NTU_BUILD_CHECKPOINT` | unset | `pre-cleanup` skips prune and empty-translation removal, for trialling a fix; never publish it |
| `NTU_GLOSS_SHIFT_STATUSES` | `accepted` | `accepted,proposed` trials proposed gloss-shift rows |
| `NTU_GLOSS_SHIFT_TABLE` | `gloss_shift_repairs.tsv` | trialling another repairs table |

## Audio clip names are keyed by span, not by sentence id

Stories `AUDIO/@url` names the whole-story recording and `@start`/`@end` give
the sentence's span within it; `@file` names the per-sentence clip that
[`../scripts/download_stories_audio.py`](../scripts/download_stories_audio.py)
slices out of that recording and that is published on Hugging Face.

A clip is identified by the span it covers, **not** by the sentence that
happens to contain it. Naming it after the sentence id — which this build did
at first — means that renumbering sentences renames every clip, invalidating
thousands of already-published files for no reason: reusing the id-based names
would have left 6,806 references pointing at clips that do not exist and 6,758
published clips unreferenced, when 99.1% of the audio had not changed at all.

So `clip_name()` looks the span up in
[`audio_clip_names.tsv`](audio_clip_names.tsv), which records every clip name
already published together with the span it covers. A span that is already
published keeps its name whatever the sentence is now called. A span that is
new gets a name built from the span itself
(`<story>_<start>-<end>.mp3`), which cannot collide with the id-based names
already in use — 28 of the 96 new spans in this build would have collided had
they been named after their sentence — and which stays stable if the sentences
are renumbered again.

The result is that a rebuild only ever needs the audio it actually changed.
This build: **10,796 clips keep their published name, 96 spans are new and need
slicing, 49 published clips are no longer referenced.**

### What still needs doing by hand

The 96 new clips must be sliced and uploaded before `hf-audio-parity` passes;
nothing in this repository can publish to Hugging Face. Run
`../scripts/download_stories_audio.py` against the rebuilt XML and publish the
96, then optionally delete the 49 orphans.

### Why any span moves at all

Of 187 story files, 162 have an identical span sequence to the published
corpus. The 25 that differ break down as:

- **12 files** where this build keeps (or drops) an audio-bearing sentence the
  earlier one did not. The spans themselves are unchanged; only which sentences
  exist differs.
- **the rest** are single spans that genuinely differ. A sentence's span runs
  from the first intonation unit's start to the last one's end, in document
  order. It is tempting to take `[min, max]` over all the endpoints instead,
  and that is wrong: 40 of the source's 31,756 units carry an **inverted**
  span, the end before the start (e.g. `[217.3, 215.84]`), and on those the
  minimum reaches back behind the previous sentence's end. That widens the clip
  without capturing a single extra word — the extra audio is the preceding
  sentence's, and 28 sentences overlapped their predecessor that way. Seven
  sentences reduce to `end <= start` in document order; all seven are
  single-unit sentences whose own span is degenerate, and the AUDIO guard
  already drops them.

  The story's zero point is taken from the source units **before** merging, for
  the same reason: computing it from the merged sentences makes it depend on
  the reduction rule, and changing the rule silently re-timed ten Kavalan
  stories by up to 7.8 seconds.

## Checking a rebuild

[`../qa/`](../qa/) holds the regression harness: it re-scores a rebuilt tree
against the recorded baseline and reports any test that moved. Run it after
any change here — see `../qa/README.md`.
