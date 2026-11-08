# Phase B regeneration report — NTU_Paiwan_ASR

**Date:** 2026-08-12 · **Branch:** `work/ntuasr` · **Group:** 4 (underspecified)
**Corpus:** `Corpora/NTU_Paiwan_ASR` — Paiwan (`pwn`) read and spontaneous speech
collected at NTU by Li-May Sung. 260 files, 16 pseudonymous speakers, four
dialects (Northern 115 / Eastern 98 / Southern 31 / Central 16 files), 3,114 S,
3,170 AUDIO. No `W`/`M` tier, no `TRANSL`.

Group 4 entry read: "`standardize --copy`; add_phonology **profile not
stated**; full reproduction needs private inputs (published XML is present
though)". Both gaps are closed below: the profile is established by evidence
(§2) and the reproduction is split into a private-input path and a runnable
committed-input path (§3).

## 1. POL-035 snapshot: TAKEN (before any cleaning)

The published XML cannot be regenerated from committed material — the ELAN
sources and the real-name ↔ pseudonym key are private (§3.1) — so pristine
`XML/` was copied to `CodeAndDocs/pre_correction_snapshot/XML/` **before any
pipeline step** and verified byte-identical (`diff -r`, clean; 260 files). It
is the documented baseline for the runnable pipeline and the record of the
corpus's one hand edit (§7). Per POL-038, `make_xml.sh` rebuilds `XML/` from
the snapshot; nothing is hand-edited.

## 2. CENTRAL TASK 1 — the phonology profile: **Ortho113**, established by evidence

### 2.1 Candidates

Every `Orthographies/*/Paiwan.tsv` was tested — **six** profiles: `Ortho113`,
`Ortho94`, `Church`, `MinEd`, `Ferrell`, `TaiwanNandao`. (The three
`Orthographies/ConversionTables/Paiwan_*_113.tsv` files are conversion tables,
not phonology profiles, and are not candidates; none is used by this corpus,
see §3.3.)

### 2.2 Reproduction test — does the profile regenerate the corpus's own PHON?

The published PHON predates the current `add_phonology` mapper, so the test
regenerates each sentence's IPA from its published `FORM kindOf="original"`
under the **generating-era algorithm** (sequential longest-key-first,
case-insensitive replacement) with each candidate's table, selecting the
dialect column from `TEXT/@dialect`, and compares to the published
`PHON kindOf="original"` string-for-string. 3,114 sentences:

| profile | exact reproductions | % |
|---|---|---|
| **Ortho113** | **3,106 / 3,114** | **99.74%** |
| Ortho94 | 2,818 / 3,114 | 90.49% |
| MinEd | 1,370 / 3,114 | 43.99% |
| Church | 260 / 3,114 | 8.35% |
| Ferrell | 162 / 3,114 | 5.20% |
| TaiwanNandao | 90 / 3,114 | 2.89% |

The **8 residual Ortho113 misses are not mapping disagreements**: 7 are the
ellipsis `…` (published PHON writes `*`, the mapper's unmapped-glyph marker)
and 1 is the capital `J` of the loan name *John* (same marker). Every letter
of Paiwan text is reproduced in all 3,114.

### 2.3 Letter-inventory test

Original-tier character inventory (lowercased): `' a b c d e g h i j k l m n
o p q r s t u v w y z` — pure ASCII, plus `, . " ! ? ; : ( ) - / …`. Digraphs
`dr tj dj lj ng` are present throughout; `'` occurs 3,902 times and `q` 2,656.

| profile | keys absent from the corpus | verdict |
|---|---|---|
| Ortho113 | — | every key attested |
| Ortho94 | — | every key attested |
| MinEd | — (`D`/`L` fold to attested `d`/`l`) | ambiguous on inventory alone |
| Church | `ṟ ṯ ḏ ḻ` | **excluded** — its four defining letters occur zero times |
| Ferrell | `ḍ ɫ ?` (and writes `ts`, glottal `?`, no `'`) | **excluded** — same |
| TaiwanNandao | — | inventory-compatible, but see 2.2 (2.9%) |

`'` and `q` co-occur as distinct letters, which is the Ortho113/Ortho94 shape
(`'` → ʔ, `q` → q in every dialect column). Ferrell, which writes the glottal
as `?` and has no `'` key at all, is doubly excluded.

### 2.4 The decisive discriminator: Southern dialect

Ortho113 and Ortho94 differ for Paiwan in exactly two places: Ortho113 has an
`o` → u fallback row, and its **Southern** column maps `r` → R and `l` → ɣ
where all other columns map `r` → r and `l` → ɭ. Ortho94's Southern column is
identical to its other columns.

The corpus's **published Southern PHON contains 1,124 ɣ and 518 R, and zero ɭ
and zero r**. Per-dialect reproduction makes the same point:

| dialect | Ortho113 | Ortho94 |
|---|---|---|
| Northern (1,412 S) | 1,405 | 1,405 |
| Eastern (1,132 S) | 1,132 | 1,132 |
| Central (239 S) | 239 | 238 |
| **Southern (331 S)** | **330** | **43** |

Ortho94 cannot produce the corpus's Southern IPA. Ortho113 is the only
candidate that reproduces all four dialects.

### 2.5 Provenance

Concordant, and not the basis of the verdict: `standards.csv` declares
Ortho113 as Paiwan's standard orthography (so the standard-tier PHON is
Ortho113 regardless of what `--orthography` is set to), the transcription is
in the modern Council of Indigenous Peoples writing system that Ortho113
encodes, and the sibling Paiwan corpus `FormosanBankGitBook` declares Ortho113
for its original tier.

### 2.6 Verdict

**ADOPT `--orthography Ortho113`.** The evidence is not marginal: 99.74%
whole-sentence reproduction with the 0.26% residue attributable to a marker
glyph rather than to any letter, a letter inventory that matches exactly and
excludes two rivals outright, and a dialect-column signature that only this
profile produces. The WakelinTexts / Siraya_Gospels "generate no PHON"
precedent does **not** apply here — that precedent is for corpora whose
writing system is unidentified, and this one's is identified.

Confirmation after regeneration: all **6,228** PHON values in the rebuilt
corpus are exactly `phonologize(FORM, Ortho113[dialect])` — 6,228 / 6,228 (§6).

## 3. CENTRAL TASK 2 — reproduction with private inputs

### 3.1 What cannot be run here (the original tier)

`FORM kindOf="original"` and the `AUDIO` timings come from ELAN `.eaf` field
transcriptions, converted by `CodeAndDocs/main.py` + `add_dialect.py` +
`add_citations.py` (Year-1 read speech) and
`CodeAndDocs/build_y2_and_spontaneous.py` (Year-2 read speech and all
spontaneous speech). Those scripts are published, name-free and auditable, but
they need two inputs that must stay private: `speaker_key.csv` (the real-name ↔
pseudonym map plus per-speaker filename patterns) and the raw ELAN/audio
sources, which carry participants' real names. `build_y2_and_spontaneous.py`
exits with an explicit error if the key is absent.

So the published XML is **not regenerable end-to-end from committed
material** — which is exactly the POL-035 trigger, hence §1.

### 3.2 What can be run here (the enrichment pipeline)

From the snapshot, one command rebuilds `XML/` completely. Documented in the
README as two explicitly separated paths, on the Safolu model, so a data user
can tell at a glance which half of the reproduction is available to them.

### 3.3 Conversion tables (sweep ruling 3)

**Moot for this corpus: it uses none.** The standard tier is produced by
`standardize.py --remove_accents`, which takes no TSV; the source orthography
already *is* the common orthography, so there is nothing to transliterate.
`validate_conversion_table.py` has no table to verify here.

## 4. Single entry point: `CodeAndDocs/make_xml.sh` (new, executable, committed)

There was no wrapper before; the README described the pipeline in prose only.
The new script is the one documented command
(`./CodeAndDocs/make_xml.sh [FORMOSANBANK_ROOT]`, `PYTHON` override, root
resolution identical to SEALS33):

0. restore `XML/` from the POL-035 snapshot;
1. `QC/cleaning/clean_xml.py`;
2. `QC/utilities/standardize.py --remove_accents`;
3. `QC/utilities/add_phonology.py --orthography Ortho113`.

`apply_manual_edits.py` is deliberately **absent** — there is no
`CodeAndDocs/manual_edits.xml` and nothing to apply, so per the standing
ruling the no-op step is omitted rather than carried (§7 documents why no such
file exists). Audio steps are not in `make_xml.sh` either: they belong to
`download_audio_data.sh` → `extract_audio_clips.py` and never touch the text.

`--remove_accents` replaces the README's old `--copy`, and the documented flow
does not contradict it: the corpus is pure ASCII, so accent removal is a no-op
and the two flags differ only in that `--remove_accents` also runs the C012
hyphen step — which is itself a no-op here because C012 only fires on
morpheme-segmented sentences and this corpus has no `M` tier (§6, class 4).

**Verified idempotent**: a second full `make_xml.sh` run is byte-identical to
the first (`diff -r`, clean).

## 5. Warning sidecars (POL-033) and quote correction

**No sidecar of any kind was produced** — no `cleaner_warnings.csv`, no
`standardize_warnings.csv`, no `html_entities.log`, anywhere in the tree.
Nothing to review or delete, nothing committed.

**Paiwan is ARMED, and fired zero times.**
`QC/validation/reference/Paiwan/attestation.txt` exists (131 entries after the
edge-apostrophe pruning), so `clean_xml` ran the disambiguation over every
original FORM. **No `quote_corrections.csv` was created** — for this corpus or
any other.

Independently replayed in memory, calling `apply_quote_corrections` exactly as
`clean_xml.py` calls it, over all 3,114 sentences:

```
sentences=3114  TRANSL-bearing sentences=0  apostrophes=3902
sentences containing an apostrophe=1306
corrected=0  stranded=0  ambiguous=0  sentences rewritten=0
```

**Zero rows to report.** Two independent reasons, either sufficient: (a) the
corpus has **no TRANSL tier at all**, so `tq = 0` and `transl_has_pair` is
false, which disables classifier rules 1, 3 and 4 outright, and makes the
`ambiguous` audit flag unreachable (it requires `tq > 0`); (b) rule 2 — the
one TRANSL-independent rule — requires *exactly one* word-initial `'` in a
sentence plus exactly one `'` after closing punctuation, and never matched:
word-initial `'` is ordinary Paiwan vocabulary here (`'acauan`, `'iljas`,
`'udra'udral`), so sentences essentially never contain just one. The Phase A
Paiwan review anticipated this corpus by name as a risk case; the risk it
named (11% apostrophe attestation coverage failing open) cannot bite without a
translation tier to corroborate a quotation.

**Carry-over, not fixed here:** one of Phase A's eight junk dictionary entries
survives the pruning — `'em~` at line 62 of the Paiwan `attestation.txt`. It
is inert (junk can only block a correction, never cause one) and the file is a
shared reference consumed by every Paiwan corpus, so it belongs on the
maintainer's mechanical dictionary-fix branch, not this one.

## 6. Diff audit vs `main` — 100% classified

Scripted element-by-element comparison of every atomic datum in all 260 files:
TEXT and S attribute sets, child-element lists, and every FORM/PHON/AUDIO value
and attribute set keyed by element id and `kindOf`.

**37,942 data points. 32,127 identical, 5,815 changed, 0 added, 0 removed.**

| class | count | notes |
|---|---|---|
| 1. **PHON regenerated** | **5,800** | of 6,228 PHON elements; 428 unchanged |
| 2. **standard FORM: source hyphens restored** | **15** | 23 hyphens, all one speaker |
| 3. original FORM changed | **0** | `clean_xml` altered nothing |
| 4. TEXT/S attribute sets, child lists, ids | **0** | |
| 5. AUDIO | **0** | §8 |
| | **5,815** | **TOTAL classified — 0 UNEXPLAINED (100%)** |

**Class 1 — PHON regenerated.** Verified positively, not by inspection: every
one of the **6,228** PHON values in the rebuilt corpus equals
`phonologize(its own FORM, Ortho113[dialect])` — **6,228 / 6,228**. The 5,800
that changed decompose into three mechanisms, in combination:

| sub-class | count |
|---|---|
| punctuation dropped from PHON **+** `tj` → c (was ʦ) | 3,670 |
| punctuation dropped from PHON | 1,938 |
| `tj` → c (was ʦ) | 178 |
| the above **+** unmapped-glyph `*` differs | 14 |

- *Punctuation dropped*: the current mapper drops unmapped punctuation from
  PHON as "not sound"; the published tier carried commas, periods and quotes
  straight through.
- *`tj` → c*: Ortho113 maps `tj` → c (palatal stop). The published PHON writes
  ʦ for `tj`, which is the signature of the generating-era sequential
  replacement re-mapping its own output (`tj` → `c`, then the later `c` → ʦ
  row rewriting the `c` it had just produced). The current mapper matches the
  longest key once and never remaps generated IPA, so `tj` now correctly
  yields c. **This is a correction, not a regression** — the two Paiwan
  affricate/stop phonemes were previously merged in the IPA tier.
- *`*` marker*: 24 asterisks → 2. The 22 that went away were the ellipsis `…`,
  now recognised as punctuation and dropped; the surviving 2 are the capital
  `J` of *John* (7 sentences × 2 tiers = the 14 above).

**Class 2 — standard FORM hyphens.** All 15 are in one speaker's files
(`Nira`), and every one is **hyphen-restoration only**: the new standard FORM
equals the original FORM exactly, and the old standard FORM equals the new one
with its hyphens deleted. 23 hyphens in total, e.g. `tja-kakudakudan`,
`ku-pacekan`, `ma-pavalit-anga`. The published tier had them stripped by the
pre-2026-08-09 `--copy` semantics, which stripped unconditionally; C012 now
only strips hyphens from morpheme-segmented sentences, and this corpus has no
`M` tier, so the transcriber's morphological boundaries are preserved as
source content. The result is that the standard tier is now a faithful copy of
the original in **3,114 / 3,114** sentences.

### 6.1 Byte-level corroboration

`git diff --numstat` over `XML/`: **202 files, 6,219 lines added, 6,219
deleted** — a line-for-line replacement with no structural churn. Classified
by the leading tag of each replaced line:

| replaced line | count |
|---|---|
| `<PHON …>` | 5,800 |
| `<?xml …?>` (declaration) | 202 |
| `</TEXT>` (trailing-newline removal, below) | 202 |
| `<FORM …>` | 15 |
| | **6,219 = 100%** |

Nothing else moved: no re-indentation, no TEXT attribute rewrite, no id
change, no `<S>`/`<AUDIO>` line touched. The 58 `*_untranscribed.xml` stubs
are **byte-identical** to `main` (they carry no FORM, so no step rewrites
them).

Two serialization classes, both convergence onto house style and neither a
data change:

- **XML declaration**: 202 files carried `<?xml version='1.0' encoding='UTF-8'?>`
  (from ElementTree's `tree.write`); the shared `_prettify.prettify` emits
  `<?xml version="1.0" ?>`, which is the bank convention (27,204 files under
  `Corpora/` now carry it) and what the corpus's own 58 stubs already used.
  All 260 now agree. Expected, not a finding.
- **Trailing newline**: the same 202 files ended with a newline; the shared
  blank-line-stripping idiom in `add_phonology.py` removes it. All 260 now end
  without one, matching every recently regenerated corpus (checked:
  HundredPaiwanStories 0/100, Presidential_Apologies 0/16,
  Safolu-Amis-Dictionary 0/1, SEALS33 0/2, Glosbe 0/8 end with a newline).

## 7. Manual edits (POL-030)

The corpus has **one** recorded hand edit — the removal of the last two audio
segments of `02SC105-1_Belmira.xml`, whose audio is silent — and it was applied
inside the private build, before anything reached this repository. There is no
committed pre-edit state, so `capture_manual_edits.py` has nothing to diff
against and no `manual_edits.xml` can be honestly synthesized. Per sweep ruling
5 this is a mechanism with different semantics: the **snapshot is the record**,
and the README says so under a "Manual edits" heading. Nothing in `XML/` is
hand-edited after the snapshot; every later change comes from committed code
(POL-038).

## 8. AUDIO — verified untouched

**No audio was downloaded at any point.**

`AUDIO` elements were compared attribute-set by attribute-set across all 260
files: **3,170 on `main`, 3,170 now, all 3,170 identical, 0 files differing.**
Every `start`, `end` and `file` value is unchanged, and no `AUDIO` element was
added, removed or reordered. This is corroborated by §6.1 — not one `<AUDIO`
line appears in the byte diff.

This is guaranteed by construction rather than by luck: `clean_xml` iterates
`FORM` and `TRANSL` only; `standardize` writes `FORM[@kindOf="standard"]`;
`add_phonology` writes `PHON`. None of the three reads or writes `AUDIO`, and
`make_xml.sh` runs no audio step — clip extraction lives in
`download_audio_data.sh` → `extract_audio_clips.py`, which is not part of the
XML rebuild. `make_xml.sh`'s header states this.

## 9. Token counts and validators

| metric | main | now | Δ |
|---|---|---|---|
| tokens, Paiwan | 57,433 | **57,433** | **0** |
| — Northern | 27,735 | 27,735 | 0 |
| — Eastern | 20,512 | 20,512 | 0 |
| — Southern | 5,554 | 5,554 | 0 |
| — Central | 3,632 | 3,632 | 0 |
| S / AUDIO elements | 3,114 / 3,170 | 3,114 / 3,170 | 0 |
| `validate_xml` HARD / SOFT | 0 / 0 | **0 / 0** | 0 |
| `validate_text` HARD / SOFT | 0 / 33 | **0 / 48** | **+15 SOFT** |
| `validate_glosses` HARD / SOFT | 0 / 3,114 | **0 / 3,114** | 0 |
| V147 (legacy PHON tildes) | 0 | **0** | 0 |

No validator errored; all three ran to completion and exited 0 under
`--no-exit-on-hard`. **Zero HARD findings before and after.**

- **Tokens unchanged, exactly as expected.** `select_sentence_form` counts the
  standard tier, and the only standard-tier change is hyphen restoration — a
  hyphen never splits a whitespace token, so `tja-kakudakudan` is one token
  either way. Verified against both states.
- **`validate_text` +15 SOFT is entirely V133 `dash_in_S_standard_FORM`**, one
  per hyphen-bearing sentence — the designed signal for class 2 in §6, and
  correct: those hyphens are now in the standard tier because they are source
  content, not segmentation. V116 (11, all `…`, 7 sentences) and V122 (22, 6
  sentences) are unchanged pre-existing items.
- **`validate_glosses` 3,114 SOFT is V060 `W_count_matches_word_count`**, one
  per sentence, unchanged: the corpus has no `W` tier. Pre-existing and
  structural.
- **V147 is 0 in both states** — this corpus never used the legacy `x~y`
  variant notation (zero `~` anywhere in `XML/`), so the sweep's headline
  metric was already clean here.

## 10. README

Rewritten. It now carries:

- a summary table (language, dialects, source, published XML, audio,
  reproduction entry point, citation);
- a **Data shape** section for data users: the four elements per `S`, the
  absence of `W`/`M`/`TRANSL`, `'` as the glottal *letter* vs `q` as the
  uvular, why the two FORM tiers (and hence the two PHON tiers) are identical,
  the 58 partial-transcription stubs, and an explicit warning that **Southern
  PHON legitimately differs** (ɣ / R rather than ɭ / r);
- **Reproduction split into two labelled paths** — Path 1 (ELAN → original
  tier) naming the two private inputs and why they must stay private and
  stating plainly that the corpus is not regenerable end-to-end from committed
  material; Path 2 (`make_xml.sh` over the snapshot) written out as a runnable
  command with each step, what it does, and what it does *not* change;
- a **Why Ortho113** section carrying the §2 evidence in short form (the
  reproduction table, the inventory exclusions, the Southern discriminator) so
  the profile is never again "not stated";
- a **Manual edits** heading pointing at the snapshot as the record;
- data-user notes: apostrophes are glottal letters and the disambiguation has
  never fired; the corpus is unsegmented by nature; the 23 hyphens are the
  transcriber's and are preserved; the `…` and paren/slash review items;
- the audio section, corrected to describe what `download_audio_data.sh`
  actually does (delegates to `QC/utilities/download_audio.py`).

Per the README content policy it carries no sweep narrative and no rule
numbers.

## 11. Closing steps not done here

- **GitBook corpus-page update** (per-corpus procedure step 9) — deferred to
  post-merge. The page will need the Ortho113 statement and the
  two-path reproduction note.
- Statistics CSVs and the growth graph are CI-owned and were not touched.
- No push, no merge; one commit on `work/ntuasr`.

**UNEXPLAINED items: none.**
