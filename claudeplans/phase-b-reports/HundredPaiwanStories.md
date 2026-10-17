# Phase B regeneration report — HundredPaiwanStories

**Date:** 2026-08-12 · **Branch:** `work/hps-word-glosses` (off `main` @ `71eb1435c`)
**Corpus:** `Corpora/HundredPaiwanStories` — Paiwan (`pwn`; Northern / Southern /
Central / Eastern / unknown), 100 files, 2,915 S / 24,478 W / 36,705 M, no audio.
Source: Early & Whitehorn (2003), *One Hundred Paiwan Texts*.

**Verdict: PROCEEDED.** The rebuild from the committed `.docx` reproduces the
published corpus with **21 sentences** of unattributed difference — well under
the 50-sentence hard-stop — and all 21 are recognizable hand edits (the README's
own `avanu` cascade and `008S28` repair, plus two classes the README did not
name). They are captured into `CodeAndDocs/manual_edits.xml` and re-applied by
`apply_manual_edits.py`, so the corpus is now regenerable end to end from the
Word document.

---

## 1. The finding, confirmed

24,478 `W` elements, **10** with a gloss; 36,705 `M` elements, all glossed.
Cause located in `CodeAndDocs/script.ipynb`: it tokenized the source's three
parallel lines into `(wform, mform, gform)` triples, wrote `W` with a `FORM`
only, then split `gform` on hyphens into the `M`-level `TRANSL`s. The word gloss
was read and discarded. The 10 surviving `W` glosses are all hand-added (nine
restored `amin.` sentences plus `052S17W14`).

## 2. The notebook is now a committed script — `CodeAndDocs/build_xml.py`

Transcribed faithfully first (an exact-behavior copy reproduced the notebook's
own console output line for line, including both `check story …` warnings and
all nine `dropping 1` lines), then changed in four declared ways:

1. **The word gloss is emitted.** `TRANSL[@kindOf="original" xml:lang="eng"]` on
   every `W`, carrying `gform` verbatim as the book prints it (`af=eat` for
   `keman`). POL-036: additive, the `M` tier is untouched.
2. **The `mid` leak is fixed.** In the counts-disagree branch the notebook wrote
   `M id=f'…M{mid}'` with `mid` never assigned in that scope, so it leaked from
   the *previous* word's morpheme loop. Two words hit the branch: `002S3W8` and
   `078S4W19`. Verified against the faithful transcription: the notebook gave
   `002S3W8` the id `M0` by luck (the previous word's loop happened to end at
   `mid=0`) but gave `078S4W19` the id **`M1`**. Both are `M0` now, and both are
   `M0` in the published XML — i.e. `078S4W19` had been repaired by hand before
   publication, which is what the README's "Duplicate M-id renumber" note
   records. Fixing it at source means the build now produces the published ids
   directly, so no id changes (POL-037 holds). The only visible trace is
   `flagged_infix_splits.csv`, where `078S4W19M1` becomes `078S4W19M0`.
3. **The mojibake map is recorded** (README step 3's "fixed using regular
   expressions (probably; unfortunately, the exact process was not recorded)").
   The document stores four Paiwan letters in a legacy font encoding. The map is
   exactly four characters and is exact — the substituted characters never occur
   with their Unicode meaning anywhere in the document:

   | in the .docx | published | count in .docx | count published |
   |---|---|---|---|
   | `î` U+00EE | `ɫ` U+026B | 9,218 | 9,219 |
   | `ï` U+00EF | `Ɫ` U+2C62 | 53 | 53 |
   | `÷` U+00F7 | `ḍ` U+1E0D | 1,368 | 1,369 |
   | `ª` U+00AA | `Ḍ` U+1E0C | 40 | 40 |

   (The two +1s are morphemes the infix splits duplicate.)
4. **Attributes the pipeline needs are written at build time** rather than
   patched afterwards: `kindOf="original"` on the `W`-level `FORM` and
   `xml:lang="eng"` on every gloss. This **retires `add_transl_lang.py`**
   (deleted; it existed only to back-fill `xml:lang` on bare `M` glosses).

### 2a. A fifth, unplanned bug the rebuild exposed: the dialect table never fired

The notebook's `dialect_map` keys were spelled with `ł` (U+0142, l with stroke)
while the document has the mojibake `î`, so **ten of the twelve village names
could never match**. Only `Kaviangan` and `Kapayuanan` (no special letters) did:
the notebook produced 90 texts with no dialect at all. Someone assigned the
other 94 by hand afterwards. With the demojibake applied before the lookup, the
table now matches and **reproduces all 94 published dialect assignments
exactly**, plus:

- `dialect="unknown"` is written explicitly where the subtitle names no village
  (090 "conversation piece", 097/099 "Dialect not noted", 091 which has no
  subtitle line at all) — matching the published value.
- Two subtitles name a *dialect* rather than a village: 095 "Makazayazaya
  dialect" and 098 "Kazazaɫan dialect", both published as `Central`. They are in
  the table now, with a comment saying so.

## 3. Rebuild vs published — the 33 differing sentences, all classified

Method: build → `clean_xml` → the two infix splits → `capitalize_red`, then an
element-by-element comparison against the published `XML/` on the
**manual-edits strip basis** (all standard `FORM` and all `PHON` removed, so
`standardize`/`add_phonology` drift cannot masquerade as a hand edit), ignoring
the new `W` glosses (which have no published counterpart to compare against).

**33 sentences differed; 0 added, 0 removed; every S/W/M id identical.**

| class | sentences | disposition |
|---|---|---|
| clean_xml quote correction — nested `'…'` → `"…"` | 12 | **rebuild is the improvement**, not a hand edit — not captured |
| dropped one-word closing sentences, restored | 9 | captured |
| the `avanu` desync cascade | 8 | captured |
| hand splits of flagged `=` morphemes | 3 | captured |
| `008S28` quotation repair | 1 | captured |

**Unattributed differences: none.** 12 + 21 = 33.

**The 12 quote-correction sentences** (`047S12`, `047S22`, `047S23`, `050S17`,
`050S39`, `051S14`, `058S33`, `073S32`, `075S12`, `075S23`, `084S7`, `084S11`)
are *current-pipeline* output, not hand work: `clean_xml`'s attestation-backed
quote correction — which did not exist when this corpus was published — rewrites
nested single-quote quotation marks as double quotes, per the standing ruling
that `'` is the glottal letter in this corpus. 24 `'` → `"` rewrites, logged in
the durable `CodeAndDocs/quote_corrections.csv` (POL-035). Capturing them as
"hand edits" would have frozen the *old* single-quote text and defeated the
correction, so they are deliberately excluded from `manual_edits.xml`.

**The 21 captured records**, grouped:

- **Nine sentences the parser drops** (`061S34`, `062S22`, `071S64`, `072S45`,
  `074S70`, `075S75`, `095S8`, `096S49`, `097S22`) — the README listed these as
  "fixed by hand" without saying what the fix was. Each is a one-word closing
  formula (`amin.` / `?aming`) whose block therefore has no tab, so the parser
  reads the single line as the free translation and leaves the sentence empty.
  The published fix supplies the sentence, its `W`, its `M` and a `W`-level
  gloss.
- **The `avanu` cascade** (`009S2`, `030S6`, `039S12`, `039S14`, `044S4`,
  `050S52`, `052S17`, `063S4`) — as the README describes: `avanu` is glossed
  `avan nu` with an internal space, adding a token that shifts every following
  word's analysis by one to the end of the sentence.
- **Three hand splits** (`001S51`, `003S27`, `003S28`) of `=` morphemes that
  `split_infix_morphemes.py` / `split_multi_M_infix.py` flag as unspliceable
  (`in=petju` → `-in-` + `pe-tju`, `in=pa` → `-in-` + `p-a`). Not mentioned
  anywhere in the README — this is the second class of unrecorded hand work.
- **`008S28`** — the `'aa'` / `'aa?` quotation repair the README records.

### Word glosses inside the captured records

The records come from the published XML, which has no `W` glosses, so each
record was given one before capture, by rule:

- if the published `W` already carried a gloss (10 cases), keep it;
- for the 8 desync sentences, **hyphen-join the published `M` glosses** — the
  rebuild's own `gform` is shifted by one there and cannot be used, whereas the
  corrected `M` glosses *are* the source's gloss tokens, correctly re-aligned
  (`avanu` → `exact-of`, `sika` → `reason`, `tutsu.` → `OBL-this`);
- otherwise (the restored, split and `008S28` sentences, where word identity is
  unchanged) take the rebuild's verbatim `gform`.

Every resulting gloss was inspected; the reconciliation in §6 shows the whole
corpus's `W` glosses agreeing with the `M` tier.

### One published value the rebuild deliberately does not reproduce

`003S28W3`'s published `FORM` is `"pinapavanavan` — with a leading double quote
the source does not have. Its whole `W` block is byte-identical to `003S27W4`,
which *does* legitimately open a quotation: the hand split of `003S28` was
copy-pasted from `003S27` and brought the quote mark with it. The captured
record drops the stray quote (`pinapavanavan`). This is the only place where the
rebuild overrides published content on purpose.

## 4. Pipeline: one entry point, `CodeAndDocs/make_xml.sh`

Executable, committed, FormosanBank root and interpreter parameterized:

1. `build_xml.py` (docx → `XML/`, from scratch)
2. `QC/cleaning/clean_xml.py`
3. `split_infix_morphemes.py`
4. `split_multi_M_infix.py` — 477 split, 68 left for review
5. `capitalize_red.py` — 1,307 `red` → `RED`
6. `QC/cleaning/apply_manual_edits.py` — **21 edits, 0 no-ops**
7. `add_infix_w_gloss.py` — 1,368 angle-bracket glosses (new, §5)
8. `QC/utilities/standardize.py --tsv_path …/Paiwan_Ferrell_113.tsv`
9. `QC/utilities/add_phonology.py --orthography Ferrell`
10. `fix_ferrell.py`

`apply_manual_edits` runs at step 6, not step 0, because three of its records
*are* hand splits of the `M` tier that steps 3–4 produce; the records were
captured against that state and must be applied against it.

Verified **idempotent**: two consecutive full runs leave `XML/` byte-identical
(md5 of the md5 list), and `quote_corrections.csv` at the same 24 rows (step 2
resets the append-mode log first, since this is a from-scratch rebuild).

**Deleted as superseded:** `script.ipynb` (replaced by `build_xml.py`),
`add_transl_lang.py` (its job is done at build time), and `convert.py` — an
interactive one-off standard-tier character converter (`ts→c`, `ł→lj`, …) that
nothing referenced and that `standardize.py` + the Ferrell conversion table have
done since; running it today would double-convert the standard tier.
`python-docx==1.2.0` added to `requirements.txt` (the build needs it and the
repo `.venv` did not have it).

## 5. V062 needed more than a gloss — `CodeAndDocs/add_infix_w_gloss.py`

The brief expected V062 (1,368 HARD) to clear "since each infix's parent W now
carries a gloss". It does not work that way: V062 requires the parent `W` to
have a `TRANSL` containing **angle-bracket notation** (`<X>`), and the book's
word gloss for `keman` is `af=eat`, which has none.

So a second, derived gloss is added — `TRANSL[@kindOf="standard" ver="alt"]` —
in the notation the rest of the bank uses (cf. RauDong's `<AF>row` for
`k-om-aod`). It is built from the `M` tier: each morpheme's gloss in order,
wrapped in `<>` if that morpheme's FORM is infix-shaped, joined with `-` except
that no hyphen follows an angle-bracket piece:

| word | M tier | standard gloss |
|---|---|---|
| `keman` | `-em-`/af, `k-an`/eat | `<af>eat` |
| `qemaqivu` | `-em-`/af, `q-a`/RED, `qivu`/speak | `<af>RED-speak` |
| `naqemereng` | `na`/past, `-em-`/af, `q-ereng`/lie.down | `past-<af>lie.down` |

1,368 added — exactly the V062 population, one per offending `W`. The book's own
gloss is never rewritten (POL-036); `ver="alt"` marks it as the canonical one of
the two same-language `TRANSL`s, which V085 requires.

## 6. Verification

**Every `W` is glossed.** 24,478 / 24,478 carry
`TRANSL[@kindOf="original"]`; none is empty. **No word is left unglossed by the
source.** 37 glosses contain no letter: 18 are the book's own `?`
("meaning unknown" — e.g. `ḍaakasi`, `tjatjainu`), 19 are numerals glossing
numbers. No gloss contains a slash.

**Word glosses reconcile with the morpheme tier.** Comparing each `W` gloss
against the hyphen-join of its `M` glosses, 22,064 / 24,478 match exactly and
every one of the 2,414 that do not is explained:

| | count | why |
|---|---|---|
| infix split | 1,364 | `W` keeps the book's `=` (`af=eat`); the `M` tier was split into `-em-` + `k-an` |
| case only | 1,041 | `capitalize_red` uppercases the `M` gloss `red`→`RED`; the `W` keeps the book's lowercase |
| both of the above | 8 | |
| piece count differs | 1 | `052S17W14`: the hand-supplied word gloss `long.time` vs the morphemes `PAST-RED-when` — both correct, kept |

**Every existing `M` gloss is unchanged**: 36,705 before and after, **0 changed**
(§7).

## 7. Diff audit vs `main` — 100% classified

Scripted element-by-element comparison of every `TEXT` attribute, every S/W/M id
list, and every `FORM` / `PHON` / `TRANSL` value keyed by (file, element id,
tag+kindOf+lang): **324,214 keys published, 350,051 rebuilt.**

| | count | class |
|---|---|---|
| **added** | 24,478 | `W` `TRANSL[@kindOf="original"]` — the word glosses (§2) |
| | 1,368 | `W` `TRANSL[@kindOf="standard"]` — angle-bracket glosses (§5) |
| | 1 | `TEXT/@source` on text 098 (below) |
| **removed** | 10 | the 10 old `W` `TRANSL` with no `kindOf`; re-added as `kindOf="original"` with identical text |
| **changed** | 24 | the 12 quote-correction sentences, S-level `FORM` original + standard (§3) |
| | 2 | `003S28W3` `FORM` original + standard, losing the copy-pasted `"` (§3) |
| **UNEXPLAINED** | **0** | |

Nothing else moved: **0 PHON values changed**, 0 `M` values changed, 0 sentence
translations changed, all S/W/M id lists identical, all other `TEXT` attributes
identical. (The PHON tiers were already regenerated under the current
`add_phonology` by the 2026-08-11 HPS regen that is on `main`.)

**Text 098 regains its `source` attribute.** Published `PaiwanCh2_098.xml` is
the only file with no `source`; the document gives it a subtitle
("Kazazaɫan dialect") like every other story, and 095's identically-shaped
subtitle *was* kept. Reproducing an accidental omission is worse than fixing it,
so the rebuild writes it. Declared here as the one added attribute.

## 8. Tokens and validators

Token counts are computed from the sentence-level `FORM`, so glosses do not
enter them — confirmed:

| | published | rebuilt | Δ |
|---|---|---|---|
| tokens Paiwan | 24,478 | 24,478 | **0** |
| Northern / Southern / Central / Eastern / unknown | 9,017 / 9,444 / 3,714 / 1,198 / 1,105 | identical | 0 |
| S / W / M | 2,915 / 24,478 / 36,705 | identical | 0 |
| S-TRANSL / W-TRANSL / M-TRANSL | 2,915 / 10 / 36,705 | 2,915 / **25,846** / 36,705 | +25,836 W |

| validator | published | rebuilt | Δ |
|---|---|---|---|
| `validate_xml` HARD / SOFT | 0 / 0 | 0 / 0 | — |
| `validate_text` HARD (V121) | 32 | 32 | 0 |
| `validate_text` SOFT (V122) | 4,351 | 8,127 | **+3,776** |
| `validate_glosses` HARD | **1,368** (V062) | **0** | **−1,368** |
| `validate_glosses` SOFT | 33,048 | 8,580 | −24,468 |
| — V065 `every_W_has_TRANSL` | **24,468** | **0** | **−24,468** |
| — V062 `infix_M_needs_angle_gloss` | **1,368** | **0** | **−1,368** |
| — V061 `M_count_matches_form_segmentation` | 8,539 | 8,539 | 0 |
| — V068 `M_reconstructs_W` | 41 | 41 | 0 |

**V122 +3,776**: all of them `(` / `)` in a `W`-level `TRANSL`, and **zero
findings disappeared** — the source's own gloss conventions (`(name)`,
`(place)`, `f.you(p)`) now appear at the word tier as well as the morpheme tier,
where they already accounted for the 4,351 baseline. This is the POL-026
worklist, not a regression: it is what glossing the word tier from this book
necessarily costs.

*(A `validate_xml` run over an out-of-tree copy of the published files reports
`V081 text_id_unique_across_published_corpora: 100`; that is the copy colliding
with the real corpus's ids in the registry. Re-run in place, the published
corpus is clean — verified — so the before/after is 0 → 0.)*

**One rule was tripped and fixed during the turn**: the first version of the
angle-bracket gloss gave a `W` two bare `xml:lang="eng"` `TRANSL`s, which is
V085 HARD (1,368). Adding `ver="alt"` to the derived one clears it; `validate_xml`
is now 0/0.

## 9. Observations for the maintainer (non-blocking)

- **`red` vs `RED` at two tiers.** `capitalize_red.py` deliberately touches only
  the `M` tier, so 1,041 words now read `red-long.time` at the `W` tier and
  `RED-long.time` at the `M` tier. Under POL-036 the `W` value is right (it is
  the book's), and the `M` value is a pre-existing normalization of the book's
  text. Worth a ruling on whether the `M` normalization should instead have been
  an additive `kindOf="standard"` gloss.
- **`095S8` / `096S49` spell the same word two ways.** The hand-restored
  sentence has `?aming` at S level but `qaming` at W and M level. Both survive
  into the standard tier (`'aming` vs `qaming`). A content call — left as the
  editor wrote it, recorded in `manual_edits.xml`.
- **Three stale rows in `flagged_infix_splits.csv`** (`052S17W14`, `063S4W14`,
  `063S4W16`). The split scripts run before `apply_manual_edits`, so they see the
  desynced analysis of three `avanu`-cascade words and flag it; step 6 then
  replaces those words. Harmless, but the CSV over-reports by three. Documented
  in the README's "Known limitations".
- **`clean_xml` cleans S-level `TRANSL` only.** The new `W` glosses get no
  `clean_trans` pass — a repo-wide asymmetry (also noted in the
  YeddaPalemeqBlog report). Here it matters only for the curly quotes in
  `008S28W11`'s gloss `‘ah’`, which are the book's.
- **`Paiwan Ch2.docx`** (6 MB, the unprepared original) is kept for provenance
  and read by nothing; `Paiwan Ch2 Preprocessed.docx` (634 KB) is the build
  input. The preprocessing (moving each free translation onto its own line) is
  hand work that predates the repo and is not reproducible from the original.
- GitBook corpus-page update deferred to post-merge.

**UNEXPLAINED items: none.**
