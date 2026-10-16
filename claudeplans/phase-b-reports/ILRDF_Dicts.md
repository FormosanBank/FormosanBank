# Phase B regeneration report — ILRDF_Dicts

**Date:** 2026-08-12 · **Branch:** `work/ilrdf` (off `work/classifier` @ `59a4212ab`)
**Group:** 4 (underspecified pipeline) · **Corpus:** `Corpora/ILRDF_Dicts` — the
example sentences of the sixteen ILRDF/CIP *Indigenous Languages Online
Dictionary* dictionaries. 16 languages, 16 files, 98,837 S, **0 W, 0 M**, 98,837
Mandarin TRANSL, 98,825 AUDIO, 658,447 tokens.

**Headline:** the phonology question was answerable by measurement, and it was
answered for **all sixteen languages**: `Ortho113`, per language, on both tiers.
Fourteen languages prove it by reproduction — both endpoints of every published
PHON value were reconstructed exactly — and the two that never had PHON (Seediq,
Truku) are adopted on inventory, provenance and registry evidence, which is
weaker and is flagged as such. **One profile is retired**: Amis's undocumented
`Church` declaration is contradicted by the corpus's own letter inventory.
187,619 data points changed and 40,640 added, **100% classified, zero
unexplained**. V147 goes
81,428 → 0. Token delta zero. Quote-correction rows: **zero**. AUDIO untouched.

---

## 1. The central question: what phonology profile per language?

### 1.1 What the corpus already carried

| | languages | PHON values |
|---|---|---|
| both tiers present, legacy bare-tilde notation | 14 | 177,354 |
| **no PHON at all** | Seediq, Truku | 0 |

So fourteen languages carry a great deal of machine output to reproduce, and a
wrong profile could not hide behind it. Two carry none.

A second fact shapes everything below: **the standard FORM tier is byte-identical
to the original tier in fifteen of sixteen languages** (Amis differs in 33
sentences). The source is already written in the target orthography.

### 1.2 Reproduction test — every candidate profile, per language

Every S-level FORM→PHON pair, both tiers, tokenized on whitespace and restricted
to purely alphabetic tokens (so punctuation and `-` cannot confound), run through
every `Orthographies/*/<Language>.tsv` that exists, compared against the
published PHON after normalizing POL-013 notation `[o|u]` → `o~u`. Percentages
are of that language's alphabetic token pairs.

| Language | winner | reproduces | runner-up | verdict |
|---|---|---|---|---|
| **Amis** | `Church` (original tier) | **100.00%** | Ortho94 93.60 | **rejected — see §1.5** |
| **Amis** | `Ortho113`/Xiuguluan (standard tier) | **100.00%** | Ortho113Liberal 100.00 | adopt |
| **Atayal** | `Ortho113` | **100.00%** | Church 71.06 | adopt |
| **Bunun** | `Ortho113`/Junqun | 99.89% | Ortho94 90.51 | adopt |
| **Kanakanavu** | `Ortho113` | 99.98% | Ortho94 59.21 | adopt |
| **Kavalan** | `Ortho113` | 99.91% | Folk / Ortho94 90.18 | adopt |
| **Paiwan** | `Ortho94` 93.22 ≈ `Ortho113` 93.21 | tie | MinEd 92.77 | adopt Ortho113 (§1.4) |
| **Puyuma** | `Ortho113`/Nanwang | **100.00%** | Ortho94 88.10 | adopt |
| **Rukai** | `Ortho113` = `Ortho94` | **100.00%** | MinEd 82.20 | adopt Ortho113 (§1.4) |
| **Saaroa** | `Ortho113` | 88.37% | Ortho94 77.06 | adopt |
| **Saisiyat** | `Ortho113` = `Ortho94` | **100.00%** | Folk 70.03 | adopt Ortho113 (§1.4) |
| **Sakizaya** | `Ortho113` | 99.95% | Ortho94 94.40 | adopt |
| **Seediq** | — no PHON — | n/a | | §1.6 |
| **Thao** | `Ortho113` = `Ortho94` = `MinEd` | **100.00%** | Li 63.71 | adopt Ortho113 (§1.4) |
| **Truku** | — no PHON — | n/a | | §1.6 |
| **Tsou** | `Ortho113` | **100.00%** | Ortho94 85.02 | adopt |
| **Yami** | `Ortho113` = `MinEd` | 96.97% | Ortho94 / Folk 79.97 | adopt Ortho113 (§1.4) |

Ortho113 leads or ties everywhere. The sub-100% figures are **not** profile
disagreement; every one was traced to a specific table row added *after* the
PHON was generated, or to the legacy generator, and closed completely in §1.3.

### 1.3 Both endpoints reconstructed — the decisive test

The published PHON was written by commit `7d9aaa908` (2026-03-14), whose
`add_phonology.py` applied a profile as a *sequence* of `str.replace` calls,
kept all punctuation, and marked unknown characters `*`. Simulating that
generator against the Ortho113 tables **as they stood at `7d9aaa908^`** (the
commit edited the tables and regenerated the XML together) reproduces the
published values:

| tier reconstruction | result |
|---|---|
| baseline PHON = **legacy** generator over baseline FORM | **177,352 / 177,354 — 99.999%** |
| new PHON = **current** generator over new FORM | **197,674 / 197,674 — 100%** |

Two languages needed one identified table row removed to reach 100% on the
baseline side, because those rows were added between generation and the commit:
**Bunun** the `-` letter row (published PHON keeps `-`; with the row it is
dropped) and **Saisiyat** the `a:e` / `o:e` digraph rows. Both were verified by
ablation: Bunun 11,334 → **17,428 / 17,428**, Saisiyat 6,950 → **12,204 /
12,204**. Two Paiwan values (`Paiwan_1665`, both tiers) miss because their FORM
was hand-remediated for zero-width characters in July 2026 without regenerating
PHON — the `**` residue is visible in the published data and is now gone.

There is therefore **no residue** on either side, and nothing left for a
different profile to explain.

### 1.4 Ties broken, and the letter-inventory cross-check

Reproduction ties (Rukai, Saisiyat, Thao, Paiwan, Yami) were broken by
`standards.csv`, which designates `Ortho113` for every language in this corpus.
That is not a coin-flip: the standard tier is a copy of the original tier here,
so the standard PHON *must* use the designated scheme, and using a different
profile for the original tier would make two byte-identical FORM values yield
two different transcriptions.

Independently, the full character inventory of each language's original tier was
compared against every candidate's letter set. Five languages settle on inventory
alone, and all five point to Ortho113 — these are letters Ortho94 does not have:

| Language | Ortho113-only letter | occurrences | Ortho94 coverage |
|---|---|---|---|
| Kanakanavu | `ʉ` (and no `l` at all, which Ortho94 has) | 9,305 | 95.56% |
| Saaroa | `ʉ` (Ortho94 has `e`, which occurs once) | 7,959 | 95.06% |
| Sakizaya | `b` (Ortho94 writes `f`) | 3,254 | 97.78% |
| Atayal | `_` / `n_g` (added in Ortho113) | 214 | reproduces 65.75% |
| Paiwan | `o` (Ortho113 keeps it for loanwords) | 11 | 99.985% |

`Orthographies/readme.md` documents each of these as an Ortho113 change, and the
corpus exhibits all of them. Ortho113 coverage is ≥99.98% for every language;
the uncovered remainder is Chinese personal and place names, a few loanword
letters, and the `?` corruption (§7.1).

### 1.5 Amis: the `Church` declaration is retired

Amis was the one anomaly, and it was internally consistent: the published
pipeline declared the ILRDF Amis source to be in **Church** orthography both in
phonology (`--orthography Church`, which reproduces the original PHON 100%) and
in standardization (`Amis_Church_113.tsv`, which reproduces all 33 standard-tier
FORM differences exactly, including a decapitalization artifact — §5.2). Nothing
documents why.

**The corpus's own letters contradict it.** The defining property of the Church
Amis orthography, in both `Orthographies/Church/Amis.tsv` (rows `ng → ŋ` *and*
`g → ŋ`) and `Amis_Church_113.tsv` (row `g → ng`), is that /ŋ/ may be written
with a bare `g`. In this corpus:

```
g inside the digraph 'ng' : 2,955
bare g                    :     4   (mamag, kinarigo, kolonog, mikongkog)
```

Four tokens out of 2,959. A Church-orthography text would show thousands. Three
further lines of evidence agree: the source is the official CIP/ILRDF dictionary,
published in the official writing system rather than the Presbyterian
romanization; the file declares `dialect="Xiuguluan"`, which Ortho113 models with
its own column while Church has a single undifferentiated `IPA` column and its
own notes concede it "doesn't distinguish between dialects"; and `standards.csv`
designates Ortho113 for Amis. Amis is otherwise indistinguishable from its
fifteen siblings, all of which are Ortho113.

**Profile switched to `Ortho113`/Xiuguluan on both tiers, and the conversion
table dropped from the pipeline.** Consequences, all reported rather than
papered over:

- The original PHON now says `f` is `[f]` and `d` is `[ɬ|ɮ]` (Xiuguluan) instead
  of Church's undifferentiated `f → [f|v|b]`, `d → ɬ`.
- Ortho113 marks `u` NA for Xiuguluan, so the seven source `u` spellings become
  `*` — the tool's honest signal that the letter is not in the declared variety
  (Amis `*` count 35 → 42, the only language that rises).
- The standard tier loses ten source-typo rewrites (six `u`→`o`, four bare
  `g`→`ng`) and **gains back 23 sentence-initial capitals** the old table had
  destroyed. §7.2 puts the ten to the maintainer.

### 1.6 Seediq and Truku: adopted on weaker evidence, flagged

These two never had PHON — the 2026-03 run produced none for them — so **no
reproduction evidence exists**, and this is the one place in the corpus where the
verdict does not rest on measurement. Adopted anyway, on four grounds:

1. **Same source, same writing system.** One dictionary series, one scraper, one
   API; the other fourteen languages are established as Ortho113.
2. **Letter inventory is consistent.** Ortho113 Seediq covers 99.983% of
   Tegudaya's letter characters and Ortho94's letter set is identical, so
   inventory cannot separate the two schemes but does not contradict either.
3. **Ortho113's documented Truku conventions are empirically present.**
   `Orthographies/readme.md` records for Ortho113 Truku that the glottal stop is
   written by doubling the central vowel (`ee`) and that word-final `g` glides.
   The Truku file has 521 `ee` and 262 `ow`; the profile ships the matching
   `Seediq.rules.tsv` sidecar, which Ortho94 has no counterpart for.
4. **`standards.csv` designates Ortho113 for Seediq**, which governs the standard
   tier — and the standard tier here is a copy of the original.

Residual gap, stated plainly: Tegudaya Seediq has no value for `j` or `z`, so the
34 occurrences of those letters transcribe as `*` (Seediq `*` 0 → 30, Truku
0 → 20). Both are noted in the README.

### 1.7 Conversion-table verification (ruling 3)

**Not applicable.** The adopted pipeline uses no conversion table — the source is
already in the target orthography, so `--remove_accents` is the standardization
step. The one table this corpus used to consume, `Amis_Church_113.tsv`, is
retired here (§1.5); it is left in `Orthographies/ConversionTables/` untouched
for other corpora. **`standards.csv`, `Orthographies/` and every shared profile
are unmodified by this branch.**

---

## 2. POL-035 snapshot: TAKEN (before any cleaning)

The corpus is not reproducible from committed inputs. `CodeAndDocs/` holds
`scrape.py`, `xmlify.py`, `audioDL.py` and `requirements.txt` — but neither the
PDF dictionaries the scraper harvests headwords from nor the pickled API
responses are in this repository, and re-running would query the live ILRDF API
as it stands today.

Pristine `XML/` copied to `CodeAndDocs/pre_correction_snapshot/XML/` and verified
byte-identical (`diff -r`, clean) **before any pipeline step ran**. 16 files,
54 MB. Documented in the README under *Provenance and reproduction*. Per POL-038
the snapshot is never edited: `make_xml.sh` restores from it on every run and all
shaping happens on the way out.

---

## 3. Single entry point: `CodeAndDocs/make_xml.sh` (new, executable, committed)

```
0. restore XML/ from CodeAndDocs/pre_correction_snapshot/XML/
1. QC/cleaning/clean_xml.py       --corpora_path XML
2. QC/utilities/standardize.py    --remove_accents --corpora_path XML
3. QC/utilities/add_phonology.py  --orthography Ortho113 --corpora_path XML
```

Root/interpreter parameterized as in SEALS33/RauDong (`FORMOSANBANK_ROOT` arg or
env, `PYTHON` override). It sequences the shared utilities directly rather than
wrapping another script, and it is the only documented command. **Verified
idempotent:** a third full run is byte-identical to the second (`diff -r` clean).

`apply_manual_edits.py` is **absent**: there is no `CodeAndDocs/manual_edits.xml`
and no hand edits to re-apply, so including it would be a documented no-op. The
two recorded corrections to the delivered XML — the `Paiwan_1665` zero-width
removal logged in `qc_mt_text_remediation_20260729.csv`, and the withdrawal of
`Amis_3707`'s mismatched audio, which lives in `xmlify.py` — both predate the
snapshot and are part of it. Both are now named in the README.

### 3.1 `--remove_accents` and the README's "u→o only"

The standing ruling substitutes `--remove_accents` for `--copy`, and the old
README's claim needed reconciling. What it said was wrong twice over:
`standardize.py` was **not** run without a TSV (Amis got `Amis_Church_113.tsv`),
and `u`→`o` was **not** applied corpus-wide (fifteen of sixteen standard tiers
are verbatim copies; the six `u`→`o` rewrites are all Amis). With the Church
declaration retired (§1.5) there is no conversion table left, so
`--remove_accents` is the correct expression of what this corpus needs.

It is not a no-op and it is safe here. `strip_accents` removes only the combining
acute, which touches **seven characters, all Thao `í`**. Verified that it leaves
`ʉ` U+0289 (20,190 occurrences across three languages) and the source's `ē`, `è`,
`ǔ` untouched — those are not decomposable acutes and are not accent-stripped.

---

## 4. Warning sidecars (POL-033) and quote correction

| run | sidecar | rows | disposition |
|---|---|---|---|
| step 1 | `XML/cleaner_warnings.csv` | 2,123 | reviewed, **deleted**, not committed |
| step 2 | `standardize_warnings.csv` | *none written* | — |

Sidecar contents: **1,594 `c002`** (ambiguous quote/apostrophe characters in
Mandarin TRANSL, flagged and left in place) and **529 `c030`** (quote–glottal
ambiguity flags on the original tier). No row carries a `form_before`/`form_after`
value — nothing was rewritten.

### The Saisiyat guard: cleared, empirically

**No `quote_corrections.csv` was created anywhere in the tree** — **0 `c031` rows
and 0 `c032` rows**, so there is nothing to commit and nothing needing individual
scrutiny. This is the specific outcome the process guard was waiting on: the
replay that blocked this corpus predicted 6 wrong `'`→`"` rewrites in Saisiyat,
and after `work/classifier` (`59a4212ab`) the real run produces none.

The guard's language is armed, not disarmed, which is what makes the result
meaningful: `QC/validation/reference/Saisiyat/attestation.txt` (584 entries) was
present and loaded, and Saisiyat is the corpus's heaviest apostrophe user
(20,147 in the original tier, 438 `c002` + 220 `c030` flags raised). Twelve of
the sixteen languages have an attestation dictionary and were armed — Amis,
Atayal, Bunun, Kanakanavu, Kavalan, Paiwan, Puyuma, Rukai, Saaroa, Saisiyat,
Sakizaya, Tsou. Seediq, Thao, Truku and Yami have none and were disarmed. Zero
corrections either way.

**POL-041** (never clean W/M-level TRANSL) is satisfied vacuously and
structurally: this corpus has no `W` or `M` elements at all, and `clean_xml`'s
TRANSL branch is scoped to direct children of `S` regardless.

---

## 5. Diff audit vs `main` — 100% classified

Scripted element-by-element comparison of every atomic datum in all 16 files:
TEXT/S attribute sets, each element's child-tag sequence, and every
FORM/PHON/TRANSL/AUDIO value **and** attribute set, keyed by element id and
`kindOf`/`xml:lang`/`file`.

**1,343,070 data points on `main` → 1,383,710 now. 40,640 added, 0 removed,
187,619 changed, 1,155,451 unchanged.** (Every element contributes two data
points, its text and its attribute set; the 40,640 additions are the 20,320 new
PHON elements.)

| field | changed | added | total now |
|---|---|---|---|
| **PHON** text | **176,808** | 20,320 | 197,674 |
| PHON attrs | 0 | 20,320 | 197,674 |
| **TRANSL** text | **547** | 0 | 98,837 |
| TRANSL attrs | 0 | 0 | 98,837 |
| **FORM** text | **104** | 0 | 197,674 |
| FORM attrs | 0 | 0 | 197,674 |
| **AUDIO** text + attrs | **0** | 0 | 98,825 |
| element `@attrs` (TEXT/S) | 0 | 0 | 98,853 |
| element child sequence | **10,160** | 0 | 98,837 |

The 10,160 child-sequence changes are exactly Seediq (5,478) + Truku (4,682): the
S elements that gained two PHON children. Nothing else moved structurally.

### 5.1 PHON — 197,674 values, 100% accounted

Both endpoints reconstruct from the FORM tier (§1.3), so every value on both
sides is a deterministic function of its own FORM. Classes overlap; the 50
distinct combinations sum to 176,808 changed, plus 20,320 newly generated.

| class | values affected |
|---|---|
| **P2. non-phonological characters dropped** — sentence punctuation, and the Bunun/Thao syllable hyphen (6,230 of them) | **176,718** |
| **P1. POL-013 notation** — legacy `x~y` → `[x\|y]` | **81,414** |
| **P8. table row changed** since the PHON was generated (Kanakanavu `h`/`w`/`y`, Kavalan `c`/`g`, Sakizaya `g`, Saaroa long vowels, Saisiyat `a:e`/`o:e`, Bunun `c`/`e`/`o`, Paiwan `o`) | **43,058** |
| **P6. PHON newly generated** (Seediq 10,956 + Truku 9,364) | **20,320** |
| **P9. chained-replacement conflation fixed** — see below | **6,548** |
| **P5. Amis original profile** `Church` → `Ortho113` | **5,482** |
| **P3. letter now mapped**, `*` resolved | **349** |
| **P7. FORM changed, PHON follows** | **98** |
| **P4. letter now unmapped** (dialect column NA) | **57** |
| **UNEXPLAINED** | **0** |

By tier: original 88,404 · standard 88,404 (exactly symmetric — the two tiers are
the same text almost everywhere).

**P1 is the sweep's target and its count reconciles exactly.** 81,428 baseline
PHON values contain a legacy `~`; 81,414 of them acquire a `[x|y]` group, and the
other **14** do not, because the letter that carried the alternation is now
unmapped and transcribes `*` instead (Bunun `e`/`o` under Junqun, Amis `u` under
Xiuguluan). 81,414 + 14 = 81,428 = the V147 baseline to the unit.

**P9 is a real defect fixed, in two languages.** The old generator applied the
table as a sequence of string replacements, so a mapping whose output was itself
a later `letter` row got re-mapped:

- **Paiwan** `tj → c` (the palatal stop) was fed into the later row `c → ʦ`, so
  the palatal stop and the affricate were **conflated**: `tjaqali` transcribed
  `ʦaqaɭi`. It now reads `caqaɭi`, while genuine `c` stays `ʦ`.
- **Yami** `z → r` was fed into `r → ɻ`, the same conflation RauDong documented.

6,548 values recover a distinction they had lost.

**P4 is the honest cost of §1.5 and §1.6** and is small: 57 values, mostly the
seven Amis `u` spellings and Bunun's `e`/`o` in code-switched material. Corpus
`*` count falls overall, 765 → 505.

### 5.2 FORM — 104 values, and the original tier barely moves

| class | tier | count |
|---|---|---|
| fullwidth `！` U+FF01 → `!` | original | **32** |
| fullwidth `！` U+FF01 → `!` | standard | 32 |
| Amis sentence-initial `Ng` decapitalization **reverted** | standard | 23 |
| Amis `u`→`o` / bare `g`→`ng` rewrites reverted (§1.5) | standard | 10 |
| Thao acute accent removed (`í` → `i`) | standard | 7 |
| **UNEXPLAINED** | | **0** |

**Only 32 original-tier FORM values changed in the entire corpus**, and all 32 are
one typographic canonicalization. No spelling was touched anywhere in the
original tier.

The 23 Amis reversions are a **defect repaired, not data lost**: the legacy
standardizer's capitalization hack matched `Ng` at sentence start, found no
mapping for it, and substituted the `ng` row's value — so `Ngerngeren` had been
published as `ngerngeren`. `Amis_Church_113.tsv` reproduces all 33 of the old
rewrites exactly, which is how the mechanism was identified.

### 5.3 TRANSL — 547 values, all C002 Branch B

Every one is `clean_xml`'s documented Chinese double-quote canonicalization: the
corner brackets 「」 (467), curly doubles “ ” (79) and one white corner bracket
pair 『』 collapse to U+FF02 FULLWIDTH QUOTATION MARK. Title marks 《》 and 〈〉 are untouched
by design. **This is established repo behaviour, not new here** — Glosbe's swept
XML already carries U+FF02, and ILRDF was the last published corpus still holding
`「`. No Formosan-language tier is affected; no translation text was otherwise
altered. §7.3 records the one reservation.

### 5.4 Byte-level corroboration

`git diff --numstat` over `XML/` is symmetric for the fourteen PHON-bearing files
(e.g. Amis 11,008/11,008, Rukai 20,856/20,856) and asymmetric for exactly the two
that gained PHON (Seediq 11,010/54, Truku 9,491/127). Line-tag census of the whole
diff: **373,936 `<PHON>` lines, 1,094 `<TRANSL>`, 208 `<FORM>`, 32 `</TEXT>`, 30
XML declarations**. The declaration and closing-tag lines are the shared
`prettify` writing `<?xml version='1.0' encoding='UTF-8'?>` and a trailing
newline — serializer form, no data. No re-indentation anywhere else.

---

## 6. Token delta and validators

| metric | `main` | now | Δ |
|---|---|---|---|
| **tokens, all 16 languages** | 658,447 | **658,447** | **0** |
| per language (Amis 37,140 · Atayal 53,688 · Bunun 53,541 · Kanakanavu 38,130 · Kavalan 53,088 · Paiwan 38,316 · Puyuma 51,590 · Rukai 60,572 · Saaroa 19,149 · Saisiyat 37,491 · Sakizaya 32,233 · Seediq 51,673 · Thao 44,889 · Truku 27,973 · Tsou 19,184 · Yami 39,790) | | **identical, `diff` clean** | **0 each** |
| S / W / M | 98,837 / 0 / 0 | same | 0 |
| AUDIO elements | 98,825 | 98,825 | 0 |
| `validate_xml` HARD / SOFT | 0 / 0 | **0 / 0** | 0 |
| `validate_text` HARD / SOFT | 0 / 94,228 | **0 / 12,761** | **−81,467** |
| `validate_glosses` HARD / SOFT | 0 / 98,837 | **0 / 98,837** | 0 |

All three validators ran to completion and exited 0 under `--no-exit-on-hard`.
**No HARD findings before or after.** Validated on this corpus alone, per the
scale warning.

- **V147 `phon_legacy_tilde_variant` 81,428 → 0.** The sweep's target metric,
  cleared; it reappears independently as diff class P1 (§5.1).
- **V116 `non_ascii_in_form` 56 → 17 (−39).** The 32 fullwidth `！` and the 7
  Thao acutes. The 17 remaining are genuine source oddities left alone: four
  Amis `ē`, six `…`, and one each of `＿`, `Ｍ`, `´`, `è`, `ǔ`, `│`, `；`.
- **V122 `parens_slashes_anywhere` 9,610 → 9,610, unchanged.** All are `(`/`)`
  inside the dictionary's own Mandarin translations. POL-026/027 govern FORM
  tiers, not translations.
- **V133 `dash_in_S_standard_FORM` 3,118 → 3,118, unchanged**, and it splits in
  two. **3,078 are false positives**: 3,047 Bunun and 31 Thao, where `-` is a
  *letter* (syllable boundary), not a segmentation marker, so `standardize.py`
  correctly declines to strip it. The other **40** — Kanakanavu 11, Tsou 7,
  Paiwan 5, Yami 5, Saaroa 3, Saisiyat 3, Seediq 3, Amis 1, Puyuma 1, Sakizaya 1
  — are in languages where `-` is *not* a letter and C012 should have stripped
  them from the standard tier. It did not, for the reason MontgomeryTexts
  escalated. §7.4.
- **V126 (2), V137 (14) unchanged** — source text, untouched by regeneration.
- **V060 `W_count_matches_word_count` 98,837, unchanged and inherent**: it fires
  once per S because this corpus has no word tier at all. Not a defect.

---

## 7. Verified findings referred to the maintainer (not fixed here)

1. **The `?`-for-`ʉ` corruption is still in the published data.** 329 tokens
   contain a letter-`?`-letter sequence: Saaroa 163, Kanakanavu 121, Tsou 33 —
   the loss of `ʉ` U+0289 in ILRDF's own database, confirmed at the byte level
   against the live API in the 2026-06-14 dev-repo audit and unrecoverable by
   re-scraping — plus 12 in Kavalan, Yami, Paiwan and Thao that are a different
   artifact (a real sentence-final `?` run together with the next word). The
   audit produced repair lists (`claudeplans/ilrdf-q-corruption-FIXED.csv`, 61
   word repairs) that were applied to the **dev repo's** working tree and never
   ported here. Applying them belongs in a committed pipeline step, not this
   pass. Documented in the README.
2. **Ten Amis source typos are now preserved rather than silently rewritten**
   (§1.5): six vowels spelled `u` where Xiuguluan writes `o`, four velar nasals
   spelled with a bare `g`. Retiring the Church table is what surfaces them. If
   the maintainer wants them normalized, the right mechanism is a
   `manual_edits.xml` record against the **original** tier — they are misspellings
   in the source, not an orthography conversion — after which both derived tiers
   follow automatically. Nothing was invented here.
3. **Chinese quotation loses its open/close distinction.** C002 Branch B collapses
   directional 「 」 and “ ” to the non-directional U+FF02. It is deliberate,
   documented in `clean_xml.py`, and already applied elsewhere in the repo, so it
   is out of scope for a corpus turn — but this corpus is the largest body of
   Mandarin translation in the bank (547 values affected), and if the rule is ever
   revisited, this is where the cost lands.
4. **V133 splits into a validator gap and a `standardize.py` gap.** 3,078 of the
   3,118 findings are structurally false: the rule reads any `-` in a standard
   S-FORM as leftover segmentation, but in Bunun and Thao it is a letter. A rule
   that consulted the language's profile — the same `_hyphen_is_letter` check
   `standardize.py` already performs — would not fire on them. The **other 40**,
   spread over ten languages where `-` is not a letter, are C012's job and
   survive because `_apply_standard_hyphens` returns early on
   `if element.find(".//M") is None` and this corpus has **no morpheme tier at
   all**. That is exactly the shared-utility gap the MontgomeryTexts pass
   escalated (§3.1 of that report), independently reproduced here at a second
   M-less corpus. Both are shared-code changes, deliberately left to the
   maintainer; no corpus-local workaround was added.
5. **Seediq/Truku phonology rests on non-reproduction evidence** (§1.6), and
   Tegudaya Seediq has no value for `j` (23) or `z` (11). If the maintainer would
   rather this corpus's Seediq and Truku carried no PHON, deleting step 3's output
   for those two files is a one-line change to `make_xml.sh`; the recommendation
   here is to keep it.
6. **`dialect="unknown"` on eight of sixteen languages** (Kanakanavu, Kavalan,
   Saaroa, Saisiyat, Sakizaya, Thao, Tsou, Yami), so dialect-specific profiles
   fall back to their default column. Assigning varieties is expert work; none
   was guessed.

---

## 8. Issue #76 — claim-by-claim disposition

Every claim re-verified against the tree; none taken on trust.

| # | claim | verified? | disposition |
|---|---|---|---|
| 1 | 81,428 V147 across 8 files; PHON uses retired bare-tilde notation; regenerate per POL-013 | **partly** — the count is exact (81,428), the file count is **wrong**: the findings span **14** files, not 8 (the other two never had PHON) | **DONE.** Regenerated through the committed pipeline. V147 → 0. The 81,428 reconciles exactly as 81,414 (class P1) + 14 (§5.1). |
| 2 | 197 within-file duplicate groups, 395 occurrences; review under POL-022 "preserving distinct-provenance attestations" | **yes**, exactly 197 groups / 395 rows / 0 cross-file | **REVIEWED — all retained, and the provenance is now measured, not assumed.** In **189 of 197** groups the two copies carry **different audio URLs keyed to different headwords** (e.g. Amis_39/Amis_177 share a sentence but are recorded under `'odawis` and `ca'ayay`): one example illustrating two dictionary entries, two independent attestations, two recordings. Deleting either would destroy a headword attestation and an audio clip. Of the remaining 8, all under a single headword, **4 carry different Mandarin translations** (two distinct source records) and **4 are fully identical** — `Amis_4976/4977`, `Atayal_5249/5250`, `Seediq_4538/4539`, `Saisiyat_5854/5934`. Those four are the only genuine extraction duplicates in 98,837 sentences. No dedup step is declared for this corpus, so POL-022 keeps them SOFT; nothing removed. |
| 3 | audio statistics stale for `ami/Xiuguluan` and `pwn/Northern`; hosted-audio parity passes | **yes** | **REPORTED, not refreshed** — see §9. |
| 4 | 3,118 V133 standard-tier dash findings | **yes**, 3,118 | **REPORTED as false positives** (§7.4). Unchanged by regeneration. |
| 5 | 14 V137 footnote-like strings | **yes**, 14 | **REPORTED, not fixed.** Source text in the dictionary's own translations; unchanged. |
| 6 | 2 V126 clitic markers | **yes**, 2 | **REPORTED, not fixed.** Source text; unchanged. |
| 7 | "no XML, text, or gloss HARD findings reproduce" | **yes** | Confirmed before and after: 0 HARD throughout. |
| 8 | "Make repairs in the reproducible development pipeline. Do not hand-edit PHON or bulk-delete punctuation." | — | **Honoured.** Every change in this branch was produced by committed code (POL-038); no PHON was hand-edited; punctuation left the phonology tiers only because the current generator drops non-sounds, and it is untouched in every FORM and TRANSL. |

The issue's framing that this is only a PHON-regeneration job was incomplete: it
did not mention that two of the sixteen languages had **no phonology at all**, nor
that the corpus's phonology profile was undocumented — the actual blocking
question, answered in §1.

---

## 9. Audio: untouched, and the stale statistics (P005)

**AUDIO is verified untouched**: 98,825 elements before and after, and the
element-by-element audit reports **0 changed and 0 added AUDIO values or
attribute sets** across all 16 files. No audio was downloaded at any point in this
pass.

`statistics/audio_durations.csv` records **98,827** audio for this corpus against
the XML's **98,825**, in two rows, both `computed_at 2026-06-12`:

| row | CSV count | XML now | cause of the drift |
|---|---|---|---|
| `ami` / `Xiuguluan` | 5,482 | **5,481** | `7a2679285` withdrew `Amis_3707`'s mismatched recording |
| `pwn` / `Northern` | 5,365 | **5,364** | `4d326544d` skipped an example with no source text |

`get_corpus_stats.py --report-stale-audio` flags exactly these two.
**Not refreshed here** — that is `refresh_audio_stats.py`'s job on demand, it
requires pulling the corpus's audio from Hugging Face, and this branch changed
nothing about the audio. The drift is unchanged by this pass and is reported for
scheduling.

---

## 10. README

Rewritten. It was the dev repo's own README, describing a directory layout
(`dicts/`, `.PickleScrapes/`, `words_list/`, `Final_XML/`) that does not exist
here, with `clean_xml`/`add_original`/`standardize` written out as steps 4–6
against paths that no longer apply, a duplicated "Download Audio" section, no
statement of what the corpus contains, no orthography, and the inaccurate
"standardize with no TSV, all u's converted to o's". It now carries:

- what the corpus is, with a per-language table of sentences, tokens and audio;
- the tier structure, and the fact that there is **no word or morpheme tier**;
- **the orthography, stated and justified** — that the source is already in the
  standard writing system, what each tier therefore does, what `*` means and how
  many there are, and the Amis and Seediq/Truku gaps;
- **the notation a data user would otherwise misread**: `'` as the glottal
  *letter*, Saisiyat `:` as vowel length, Bunun/Thao `-` as a syllable boundary,
  `ʉ`, the `[x|y]` variant notation, and U+FF02 in the translations;
- **provenance and full reproduction**: why the scrape cannot be replayed, the
  snapshot's role, `make_xml.sh` with its arguments and environment overrides,
  and all four steps written out as runnable commands; `XML/` is reproducible
  from committed inputs by one command;
- the sidecar policy, and why there is no manual-edits step;
- the two recorded corrections, and known issues (the `?` corruption with counts,
  the repeated sentences with their provenance, `dialect="unknown"`).

Per the README content policy it carries no sweep narrative, no validator rule
numbers and no project-wide-rule explanations.

---

## 11. Closing steps not done here

- **GitBook corpus-page update** (per-corpus procedure step 9) — deferred to
  post-merge with the other closing steps. The page will want the orthography
  statement, the no-word-tier note and the `?`-corruption caveat.
- **Audio statistics refresh** — §9, on demand, not part of a merge.
- No push, no merge. One commit on `work/ilrdf`.

**UNEXPLAINED items: none.**
