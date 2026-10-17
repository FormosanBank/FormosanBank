# Phase B regeneration report — Paiwan_Stories

**Date:** 2026-08-12 · **Branch:** `work/paiwanstories` (off `main` @ `3a3c47c22`)
**Group:** 4 (underspecified) · **Corpus:** `Corpora/Paiwan_Stories` — three
short Eastern Paiwan narratives told by tjaiwan giling, published as Juan,
T. F., & Ruan, X. (2024), *Corpus of Paiwan Stories*. `pwn`,
`dialect="Eastern"`, 3 files, 45 S, 556 tokens, 90 FORM, 90 PHON, 45 Chinese
TRANSL. No `W`/`M` tier. Three continuous recordings, not time-aligned.

**Headline:** the phonology profile was **established by measurement, not
adopted by guess** — `Ortho113` (Eastern) reproduces all 45 published original
PHON values exactly under the generator that produced them, where every other
Paiwan profile reproduces at most 10. The corpus is hand-built and
non-regenerable, so a POL-035 snapshot was taken first and one committed
pipeline now rebuilds `XML/` byte for byte. The regeneration changed **PHON
only** — 90 values, 100% classified, zero unexplained — and left every FORM,
every TRANSL and every attribute byte-identical. Token delta zero. Zero quote
corrections.

---

## 1. Reproducibility: what is and is not true

The README's claim, verbatim, was *"The XMLs were created by hand from the
PDF. No automatic processing."* Checked directly, and it is **correct**:

| question | answer |
|---|---|
| Can the XML be rebuilt from the source publication? | **No.** `CodeAndDocs/` held exactly one file, `requirements.txt` (a dev-repo leftover listing matplotlib/seaborn/sklearn). No scrape, no OCR output, no parser, no intermediate. The text, the Chinese translations and the markup are all hand work. Unrecoverable, and this pass does not pretend otherwise. |
| Was the published XML derivable from anything committed? | **No, before this pass.** Nothing in the repository produced it. |
| Is the published XML reproducible now? | **Yes.** The hand-built XML is the source of record; it is snapshotted under `CodeAndDocs/pre_correction_snapshot/XML/` and `CodeAndDocs/make_xml.sh` rebuilds `XML/` from it in three steps. Verified idempotent. |

The tracking doc's Group 4 entry for this corpus checks out on both counts:
`standardize --copy` was indeed what the README documented, and the phonology
profile was indeed named nowhere in the corpus. §4 establishes it.

The README also documented a step 2, `QC/utilities/add_original.py`. **That
script no longer exists in the repository**; `standardize.py` absorbed its job.
The stale step is dropped rather than resurrected.

### POL-035 snapshot: TAKEN (before any cleaning)

Pristine `XML/` copied to `CodeAndDocs/pre_correction_snapshot/XML/` and
verified byte-identical (`diff -r`, clean) before any pipeline step ran. 32 KB,
3 files. Noted in the README under "Provenance and reproducibility". Per
POL-038 the snapshot is never edited: `make_xml.sh` restores from it on every
run and all shaping happens on the way out.

The snapshot is invisible to the validators: `QC/validation/_discovery.py`
skips `CodeAndDocs/` subtrees, so the duplicated `TEXT` ids do not trip the
cross-corpus id-uniqueness check. Confirmed by running `validate_xml`
`by_corpus --corpus Paiwan_Stories` over the whole corpus directory
(snapshot included): **0 findings**. (Pointing a validator *explicitly* at a
path inside `CodeAndDocs/` does surface 3 such findings — that is the
documented behaviour of an explicit path, not a defect, and it is why the
before/after numbers in §6 were taken with the corpus-scoped entry points.)

### Stray committed sidecars (POL-033): none

No `*_warnings.csv`, no `quote_corrections.csv`, no report CSV was committed
under this corpus on `main`, and the pipeline produced none (§3).

---

## 2. Single entry point: `CodeAndDocs/make_xml.sh` (new, executable, committed)

```
0. restore XML/ from CodeAndDocs/pre_correction_snapshot/XML/
1. QC/cleaning/clean_xml.py        --corpora_path XML
2. QC/utilities/standardize.py     --remove_accents --corpora_path XML
3. QC/utilities/add_phonology.py   --orthography Ortho113 --corpora_path XML
```

Root/interpreter parameterized as in RauDong/SEALS33/WakelinTexts
(`FORMOSANBANK_ROOT` arg or env, `PYTHON` override). `apply_manual_edits.py` is
**absent**: there is no `CodeAndDocs/manual_edits.xml` and no hand edits to
re-apply, so including it would be a documented no-op.

The script does not wrap another script — it sequences the shared utilities
directly, and it is the only documented command. **Verified idempotent:** a
second full run is byte-identical to the first (`diff -r` clean).

### `--copy` → `--remove_accents`: substitution verified, not assumed

The documented flow used `--copy`. The standing ruling substitutes
`--remove_accents` unless the documented flow contradicts it, and here it does
not: the corpus has **no accented characters, no segmentation hyphens and no
clitic `=` markers**, which are the only things the two modes differ over.

Equivalence is a measurement, not an argument: the full pipeline was run twice
from the snapshot, once with `--remove_accents` and once with `--copy`, and the
two `XML/` trees are **byte-identical** (`diff -r` clean). `--remove_accents`
is what `make_xml.sh` runs, and the README states why.

### Conversion tables (ruling 3): not applicable

This corpus's pipeline uses **no conversion table**. `--remove_accents` takes
no TSV, and none is needed: the source is already written in the official
Paiwan orthography, which is FormosanBank's standard for Paiwan, so the
standard tier is a copy — verified, all 45 sentences have byte-identical
`original` and `standard` FORMs, before and after regeneration.

---

## 3. Warning sidecars (POL-033) — none produced

| run | sidecar | rows | disposition |
|---|---|---|---|
| step 1 | `cleaner_warnings.csv` | *none written* | — |
| step 1 | `quote_corrections.csv` | *none written* | — |
| step 2 | `standardize_warnings.csv` | *none written* | — |

A tree-wide `find` after the run turned up no new sidecar anywhere; the only
matches were other corpora's files already committed on `main` (Glosbe,
HundredPaiwanStories, Latham-1862, Nowbucyang).

### Quote corrections: ZERO rows, and the classifier was genuinely armed

Paiwan **is** armed — `QC/validation/reference/Paiwan/attestation.txt` exists
(131 entries) — so this is a real zero, not a skipped run. The exposure surface
is one character:

- The corpus contains **exactly one `'`** in the whole of its FORM text:
  `na'en` 'my', in `DingDing.xml` `S1`. Running the classifier directly returns
  `[(27, 'GLOTTAL_INTERNAL')]` — a word-internal apostrophe, kept as the
  glottal-stop letter, which is what it is. (`na'en` is not in the 131-entry
  dictionary; `GLOTTAL_INTERNAL` does not consult it, and the sentence's
  Chinese translation carries no quotation marks either, so both tests agree.)
- Quotation in this corpus is written with `"` — 6 occurrences, 3 pairs, all
  in `maljialjian a qaciljay.xml`. None was touched.

The one thing this corpus's history shows about its quotes is already resolved:
commit `4e1a510df` (2026-06-08, *"fixed an orthography error"*) replaced
typographic `“ ”` with straight `" "` in one sentence and hand-patched its PHON
to match. That state is what the snapshot preserves; step 1 finds nothing left
to canonicalize, and step 3 regenerates the PHON from the FORM so the hand
patch is absorbed rather than perpetuated.

---

## 4. Phonology: profile ESTABLISHED (Ortho113), not invented

The README said only "the usual way". Rather than guess, the published PHON was
used as the evidence — it is machine output, so the profile that produced it
can be recovered by reproduction.

**Method.** Every one of the 45 published `original` FORM→PHON pairs was
reproduced under each candidate Paiwan profile, with two generators: the
**legacy** one (sequential `str.replace` over the TSV in row order, ASCII
punctuation kept, unknown characters → `*`) exactly as it stood at `8ea69e752`
— the commit that *introduced* `add_phonology.py`, three minutes before
`a02c306c5` wrote this corpus's PHON — and the **current** one (single-pass,
longest-match-first, no remapping of generated IPA).

| profile | exact reproduction of published `original` PHON (legacy generator) | (current generator) |
|---|---|---|
| **`Ortho113`** | **45 / 45 — 100%** | 0 / 45 |
| **`Ortho94`** | **45 / 45 — 100%** | 0 / 45 |
| `MinEd` | 10 / 45 | 0 / 45 |
| `Church` | 4 / 45 | 0 / 45 |
| `Ferrell` | 3 / 45 | 0 / 45 |
| `TaiwanNandao` | 1 / 45 | 0 / 45 |

Re-run against the tables **as they stood at `a02c306c5`**, the numbers are
identical (`TaiwanNandao/Paiwan.tsv` did not exist yet). The "current
generator" column is 0/45 across the board for a reason that is itself part of
the finding — see §5 class A and B.

**Ortho113 and Ortho94 tie because on this data they are the same profile.**
At generation time their `Paiwan.tsv` files differed *only* in the `Southern`
column; the `Eastern` column, which `dialect="Eastern"` selects, was
byte-identical. Today they differ by one further row — Ortho113 gained `o` → `u`
in `af56c6216` — and **the corpus contains no `o`**. Running the whole pipeline
under each and diffing confirms it: `--orthography Ortho94` and
`--orthography Ortho113` produce **byte-identical `XML/`**. The choice between
them is empirically undecidable *and* immaterial.

Ortho113 is the one declared, for three reasons:

1. **Tier identity.** All 45 `original` FORMs are byte-identical to their
   `standard` FORMs, and the published `original` PHON was byte-identical to
   the `standard` PHON. The standard tier is Ortho113 by `standards.csv`
   (`Paiwan,Ortho113`), and the legacy generator hardcoded Ortho113 for it. A
   corpus already written in the standard orthography should declare the
   standard's profile for its original tier too; declaring anything else would
   assert a distinction the data does not have.
2. **Chronology.** Ortho113 is the current MOE standard; Ortho94 (ROC-94, 2005)
   is its superseded predecessor. The source was recorded in 2020 and published
   in 2024.
3. **Superset.** Ortho113's letter set contains Ortho94's; on data with no `o`
   it cannot differ, and on any future addition to this corpus it is the safer
   declaration.

Three further lines of evidence agree on excluding the rest:

1. **Letter inventory.** The corpus's alphabet is `a b c d e g h i j k l m n p
   q r s t u v w y z` plus `'` and the digraphs `dr tj dj lj ng` — no `o`, no
   `f`, and `j` occurs only inside `dj`/`tj`/`lj`. That is *exactly* the
   Ortho94 letter set, and Ortho113's minus `o`. The excluded profiles do not
   have the corpus's digraphs as letters at all: `Church` writes `ṟ ṯ ḏ ḻ`
   instead of `dr tj dj lj`; `Ferrell` writes `ḍ ɫ ts` and uses `?`, not `'`,
   for the glottal stop; `MinEd` writes `D`/`L` for `ɖ`/`ɭ` and has no `dr`.
   Note that these failures are **silent** rather than marked — an unknown
   digraph is mapped letter-by-letter (`dr` → `dr`), not flagged `*` — which is
   why the reproduction test above, not an unmapped-character count, is the
   discriminator. (`*` count is 0 under every candidate.)
2. **`'` is a real letter here.** Ortho113/Ortho94 map `'` → `ʔ` and keep `q` as
   the distinct uvular stop (71 occurrences). The published PHON has `naʔən`
   for `na'en` and `q` throughout, so the profile that produced it must be one
   that treats `'` orthographically. `Ferrell`, which has no `'` row, cannot.
3. **`TaiwanNandao` post-dates the PHON** and disagrees on four letters
   (`dj`→`ɟ`, `lj`→`l`, `c`→`ts`, `l`→`ɾ`); it reproduces 1 of 45.

**No profile was extended, and no table was touched.** `standards.csv`,
`Orthographies/` and every shared profile are untouched by this pass.

---

## 5. Diff audit vs `main` — 100% classified

Scripted element-by-element comparison of every atomic datum in all 3 files:
TEXT/S attribute sets, each element's child-tag sequence, and every
FORM/PHON/TRANSL value **and** attribute set, keyed by element id and
`kindOf`/`xml:lang`.

**546 data points on `main` → 546 now. 0 added, 0 removed, 90 changed, 456
unchanged.**

Every changed data point is a PHON value — that is, **every PHON value in the
corpus changed, and nothing else did**:

| field type | changed | unchanged |
|---|---|---|
| PHON text | **90** | 0 |
| FORM (text + attrs) | **0** | 180 |
| TRANSL (text + attrs) | **0** | 90 |
| element `@attrs` | **0** | 48 |
| element child sequence | **0** | 48 |

### Classification

Each changed PHON was classified by reconstructing **both** endpoints from the
FORM tier: the new value must equal `phonologize(FORM, Ortho113/Eastern)` under
the current generator, and the old value must equal the legacy generator's
output on the same FORM. All 90 satisfied both.

| class | PHON values affected |
|---|---|
| **A. `tj`/`c` conflation repaired** — `tj` was mapped to `ʦ`, now `c` | **54** |
| **B. non-phonological punctuation dropped** — `. , ? ! " :` | **90** |
| by tier | original 45 · standard 45 |
| **UNEXPLAINED** | **0** |

Combinations: A+B 54, B alone 36; they sum to 90.

**Class A is a real defect fixed, and worth stating plainly.** The legacy
generator applied the profile table as a *sequence of string replacements*. In
the Ortho113/Ortho94 Paiwan table the row `tj → c` comes before the row
`c → ʦ`, so every `tj` was first rewritten to `c` and then re-rewritten to `ʦ`
along with the genuine `c`s — the palatal stop and the affricate were
**conflated** in every published PHON value that contained a `tj`. The current
generator maps each grapheme once, longest match first, so `tjekacauan` is now
`cəkaʦauan` (not `ʦəkaʦauan`) while `caucau` stays `ʦauʦau`. 54 values recover
a distinction they had lost. This is the same failure mode as RauDong's
`z`/`r` conflation, in a different language.

`tj` occurs in 40 tokens (28 distinct word types) spread over 27 of the 45
sentences — hence 54 of the 90 PHON values. `dr`, `dj`, `lj` and `ng` were
never affected, because their IPA outputs (`ɖ ɉ ʎ ŋ`) are not themselves
letters in the table and so were never re-matched.

**Class B**: the generator that produced the published PHON kept anything in
`string.punctuation`. The current one drops unmapped punctuation as "not
sound". Every sentence ends in `.`, `!` or `?`, so all 90 values are affected.
Example (`DingDing` `S1`):

```
- u paqənəʦən ka qaqunuan naʔən, nu kaɉamaɉaman ru vaik a kidiŋdiŋ ti kina.
+ u paqənəcən ka qaqunuan naʔən nu kaɉamaɉaman ru vaik a kidiŋdiŋ ti kina
```

Both changes are visible in that one line: `paqenetjen` → `paqənəcən` (class A)
and the loss of `,` and `.` (class B). `na'en` → `naʔən` is *unchanged* — the
glottal letter survived, as it must.

**Byte-level corroboration:** `git diff --numstat` over `XML/` is **90 lines
added, 90 deleted** (30 per file), and every single changed line is a `<PHON …>`
line — no re-indentation, no XML-declaration rewrite, no serializer churn.

**Legacy tilde notation (V147): not applicable here.** The corpus contains zero
`~` characters before and after; its PHON never used the retired variant
notation, so the sweep's headline metric is 0 → 0 for this corpus.

---

## 6. Token delta and validators

| metric | `main` | now | Δ |
|---|---|---|---|
| tokens (Paiwan / dialect Eastern) | 556 | **556** | **0** |
| S / W / M | 45 / 0 / 0 | same | 0 |
| `validate_xml` HARD / SOFT | 0 / 0 | **0 / 0** | 0 |
| `validate_text` HARD / SOFT | 0 / 0 | **0 / 0** | 0 |
| `validate_glosses` HARD / SOFT | 0 / 45 | **0 / 45** | 0 |

`count_tokens.py` output is byte-identical before and after (no FORM changed;
PHON is not counted). All three validators ran to completion under
`--no-exit-on-hard`; **no HARD findings before or after**.

- **`validate_glosses` V060 `W_count_matches_word_count`: 45 SOFT, unchanged
  and pre-existing.** One finding per sentence, all of the form "W-count (0)
  does not match word-count (n)". The corpus has no word tier at all; this is
  the validator noting that fact, not a regression. Segmenting these texts is
  linguistic work that has not been done.
- `validate_text` is clean in both directions: no V121/V122 parens, no
  non-ASCII findings, no punctuation findings.

---

## 7. Worklist items surfaced (reported, not fixed)

Neither is a regeneration defect; both predate this pass and both are data
changes outside the sweep's remit, so the diff was kept 100% PHON.

1. **`TEXT/@audio` does not resolve.** The three texts carry
   `audio="dingding.mp3"`, `"kavatjes ni vuvu.mp3"`, `"maljialjian a
   qaciljay.mp3"`; `audio_sources.json` publishes and `download_audio_data.sh`
   fetches `DingDing.wav`, `kavatjes_ni_vuvu.wav`, `maljialjian_a_qaciljay.wav`.
   Neither the stem case/spacing nor the extension matches. Documented in the
   README's caveats. A fix belongs in `clean_audio.py`/`clean_filepaths.py` as a
   pipeline step, not a hand edit.
2. **The three `.wav` files are committed to git** (15 MB) even though
   `.gitignore` carries `**/*.wav` — they were added before the ignore rule and
   tracked files override it. Every other corpus pulls its audio from Hugging
   Face; this one ships it in the repository *and* publishes it on HF. Removing
   them from tracking is a maintainer call.

Also noted: `CodeAndDocs/requirements.txt` is a dev-repo leftover (matplotlib,
seaborn, scikit-learn) and is not an input to the build. Left in place,
documented as such in the README.

---

## 8. README

Rewritten. It previously described the corpus as a *development repository*
("Clone this repository", "Project Structure: **Final_XML**"), documented a
pipeline step whose script no longer exists, told the reader that step 1 "isn't
necessary… listed just to make it clear that we didn't forget", and named no
orthography. It now carries:

- what the corpus is (three stories, counts, tiers, one translation language,
  no word tier, audio);
- **the orthography, stated and justified**: the letter and digraph inventory,
  `'` as the glottal-stop **letter** with `q` as the distinct uvular, the
  `tj`/`c` and `dr`/`d` and `lj`/`l` contrasts spelled out with worked
  examples, and the note that Ortho94 would produce the same output but
  Ortho113 is what is declared;
- **the notation a data user would otherwise misread**: that PHON carries no
  punctuation, that no PHON value contains `*`, that the standard tier is a
  byte-identical copy of the original and why;
- **provenance and full reproduction**: that the XML is hand-built with no
  reconstructable scrape/OCR stage, the snapshot's role, `make_xml.sh` with its
  arguments and environment overrides, and all four steps written out as
  runnable commands; `XML/` is reproducible from committed inputs by one
  command;
- the sidecar policy, why there is no manual-edits step, and how to get the
  audio;
- known caveats (the `@audio` mismatch, no word tier, Chinese only).

Per the README content policy it carries no sweep narrative, no validator rule
numbers and no project-wide-rule explanations.

---

## 9. Closing steps not done here

- **GitBook corpus-page update** (per-corpus procedure step 9) — deferred to
  post-merge with the other closing steps. The page will want the orthography
  statement and the `'`-is-a-letter note.
- No push, no merge. One commit on `work/paiwanstories`.

**UNEXPLAINED items: none.**
