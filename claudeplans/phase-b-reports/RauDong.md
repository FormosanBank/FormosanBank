# Phase B regeneration report — RauDong

**Date:** 2026-08-12 · **Branch:** `work/b4-raudong` (off `main` @ `269c6ef9a`)
**Group:** 2 · **Corpus:** `Corpora/RauDong` — the 20 glossed Yami narrative
texts of Rau, D. V., & Dong, M. N. (2006), *Yami texts with reference grammar
and dictionary* (Academia Sinica). `tao`, `dialect="Yami"`, 20 files, 794 S,
13,295 W, 16,731 M, 61,644 TRANSL (Chinese + English at all three tiers). No
audio.

**Headline:** the corpus's *inputs* are not reproducible and never will be, but
its *published state* now is: a POL-035 snapshot plus one committed pipeline
rebuilds `XML/` byte for byte. The regeneration changed **PHON only** — 24,781
values, 100% classified, zero unexplained — and left every FORM, every TRANSL
and every attribute byte-identical. V147 goes 20,976 → 0. Token delta zero.

---

## 1. Reproducibility: what is and is not true

The README's claim, verbatim, was *"The nature of how the machine-readable
version was obtained is such that we do not have a reproducible pipeline."*
Checked directly, and it is **correct as far as it goes but was hiding two
different things**:

| question | answer |
|---|---|
| Can the XML be rebuilt from the printed book (OCR/parse)? | **No.** `CodeAndDocs/` contains no scrape, no OCR output, no parser, no intermediate — nothing but one accent-stripping script and a set of QC frequency plots. The text was supplied to FormosanBank already digitized. This is unrecoverable and this pass does not pretend otherwise. |
| Was the published XML derivable from anything committed? | **No, before this pass.** `remove_accents.py` was the only script, it edited `XML/` in place, and it presupposed a standard tier and a PHON tier that nothing in the repo produced. |
| Is the published XML reproducible now? | **Yes.** The delivered XML is the source of record; it is snapshotted under `CodeAndDocs/pre_correction_snapshot/XML/` and `CodeAndDocs/make_xml.sh` rebuilds `XML/` from it in three steps. Verified idempotent. |

The tracking doc's three claims about this corpus all check out: `remove_accents.py`
did run after the fact (it mutated an already-published standard tier), the
README did disclaim a pipeline, and the phonology profile was indeed unstated
anywhere in the corpus. §4 establishes the profile from evidence.

### POL-035 snapshot: TAKEN (before any cleaning)

Pristine `XML/` copied to `CodeAndDocs/pre_correction_snapshot/XML/` and
verified byte-identical (`diff -r`, clean) before any pipeline step ran. 11 MB,
20 files. Noted in the README under "Provenance and reproducibility". Per
POL-038 the snapshot is never edited: `make_xml.sh` restores from it on every
run and all shaping happens on the way out.

### Stray committed sidecar (POL-033): REMOVED

`Corpora/RauDong/cleaner_warnings.csv` **was** still present in this worktree
(it is committed on `main`; the removal on `chore/purge-claudeplans` has not
merged). `git rm`'d here too. Its content was 4 rows — the *same 2* `c002`
warnings written twice, which is itself the append-mode bug POL-033 names.

---

## 2. Single entry point: `CodeAndDocs/make_xml.sh` (new, executable, committed)

```
0. restore XML/ from CodeAndDocs/pre_correction_snapshot/XML/
1. QC/cleaning/clean_xml.py        --corpora_path XML
2. QC/utilities/standardize.py     --remove_accents --corpora_path XML
3. QC/utilities/add_phonology.py   --orthography Ortho94 --corpora_path XML
```

Root/interpreter parameterized as in SEALS33/WakelinTexts (`FORMOSANBANK_ROOT`
arg or env, `PYTHON` override). `apply_manual_edits.py` is **absent**: there is
no `CodeAndDocs/manual_edits.xml` and no hand edits to re-apply, so including
it would be a documented no-op.

The script does not wrap another script — it sequences the shared utilities
directly, and it is the only documented command. **Verified idempotent:** a
second full run is byte-identical to the first (`diff -r` clean).

### `remove_accents.py`: RETIRED (equivalence proven on the real data, not asserted)

The bespoke script stripped `á é í ó ú` (and capitals) from every
`FORM[@kindOf="standard"]` **after** the tier already existed.
`standardize.py --remove_accents` builds that tier from the original and
strips accents in the same pass, via `_accents.strip_accents` — which drops the
same combining acute, on any Latin base, and additionally NFC-normalizes.

Equivalence is not an argument here, it is a measurement: after regeneration,
**all 30,820 standard FORM values are byte-identical to the published ones**
(§5), i.e. `standardize --remove_accents` from the raw snapshot lands exactly
where `--copy` + old hyphen handling + `remove_accents.py` landed. `git rm`'d.

Note the standing ruling's `--copy` → `--remove_accents` substitution is
**not** in tension with this corpus's own flow: the flow already ended in
accent removal, and `--remove_accents` is that flow expressed as one step. Its
sentence-level hyphen stripping is likewise not new — the published S-level
standard FORMs were already de-hyphenated, and they came back unchanged.

---

## 3. Warning sidecars (POL-033) — reviewed, then deleted

| run | sidecar | rows | disposition |
|---|---|---|---|
| step 1 | `XML/cleaner_warnings.csv` | 2 × `c002` | reviewed, **deleted**, not committed |
| step 2 | `standardize_warnings.csv` | *none written* | `-` is not a Yami letter, so C012 strips silently |

Both `c002` rows are the **same element**: the `xml:lang="zho"` TRANSL of
sentence 41 of text 1, `‘哦，是該死的高進忠’我想…`. `clean_xml` flags the two
Chinese typographic single quotes and **leaves them in place** (the Chinese
TRANSL branch never calls `swap_punctuation`). Verified in the output: the
string is unchanged. So the sidecar reports zero data change, which the diff
audit independently confirms.

**Yami is DISARMED for quote correction and stayed disarmed.** There is no
`QC/validation/reference/Yami/attestation.txt` (only `default/`), and **no
`quote_corrections.csv` was created anywhere in the tree**. This matters here
more than usual: `'` is the glottal-stop *letter* in Yami and occurs 264 times
in FORMs. Nothing touched it.

**Conversion tables (ruling 3):** not applicable — this corpus's pipeline uses
no conversion table (`--remove_accents` takes no TSV). `Yami_94_113.tsv` and
`Yami_MinEd_113.tsv` exist in `Orthographies/ConversionTables/` but nothing in
this corpus consumes them.

---

## 4. Phonology: profile ESTABLISHED (Ortho94), not invented

The corpus documented no profile. Rather than guess, the published PHON was
used as the evidence — it is machine output, so the profile that produced it
can be recovered by reproduction.

**Method.** Take all 26,643 W/M `original` FORM→PHON pairs whose FORM is purely
alphabetic (`[a-z']+`, so hyphens, punctuation and accents cannot confound),
run each candidate Yami profile over the FORM, and compare with the published
PHON (normalizing only the POL-013 notation `[o|u]` → `o~u`).

| profile | exact reproduction of published `original` PHON |
|---|---|
| **`Ortho94`** | **26,643 / 26,643 — 100%** |
| `Folk` | 26,114 (fails on `h`: `ʁ` vs unmapped) |
| `Ortho113` / `MinEd` | 21,685 (fails on `z`, `r`, `s`, `h`, `v`) |
| `StacyHuang` | 16,619 (fails on `z`, `j`, `o`, …) |

Three further lines of evidence agree:

1. **Letter inventory.** The corpus's full FORM alphabet is `a b c d e g h i j
   k l m n o p r s t v w y z` + `'` + `ng`, plus `á é í ó`. That is *exactly*
   the Ortho94 Yami letter set — no `f`, no `q`, no `u`, no `R`. `Folk` is
   excluded because it writes `R`, not `h`; `StacyHuang` posits `q`, `f` and
   `u`, none of which occur.
2. **Chronology.** Ortho94 is the ROC-94 (2005) standard; Rau & Dong is 2006.
3. **`Orthographies/readme.md`** records Ortho94 Yami as "No notes.
   Conversion: no issues".

The **standard** PHON needs no choice: `standards.csv` designates `Ortho113`
for Yami and `add_phonology` resolves it automatically. It reproduced 26,721 /
27,142 of the published standard values; the 421 misses are a *legacy defect*,
not a profile disagreement — see class C in §5.

**The accent is not a segment.** Rau & Dong's acute marks lexical stress.
Ortho94 has no accented-vowel row, so accent-bearing original forms yield the
tool's documented `*` unknown-character marker: 1,127 original PHON values
(`ma-níring` → `ma-n*riŋ`). This is **unchanged from `main`** — the count was
1,127 before and 1,127 after — and it is the honest signal the tool is designed
to give. No profile was extended to paper over it; `StacyHuang` would have
suppressed the `*` only by passing the accent through into IPA (`á` → `á`),
which is not a phonological claim we can make. A further 29 `*`-bearing PHON
values come from Chinese code-switched material (`國小二三年級`), also unchanged.
Both are documented in the README.

`standards.csv`, `Orthographies/` and every shared profile are **untouched** by
this pass.

---

## 5. Diff audit vs `main` — 100% classified

Scripted element-by-element comparison of every atomic datum in all 20 files:
TEXT/S/W/M attribute sets, each element's child-tag sequence, and every
FORM/PHON/TRANSL value **and** attribute set, keyed by element id and
`kindOf`/`xml:lang`.

**431,508 data points on `main` → 431,508 now. 0 added, 0 removed, 24,781
changed, 406,727 unchanged.**

Every changed data point is a PHON value:

| field type | changed | unchanged |
|---|---|---|
| PHON | **24,781** | 98,499 |
| FORM (text + attrs) | **0** | 123,280 |
| TRANSL (text + attrs) | **0** | 123,288 |
| element `@attrs` | **0** | 30,840 |
| element child sequence | **0** | 30,820 |

### Classification

Each changed PHON was classified by reconstructing **both** endpoints from the
FORM tier: the new value must equal `phonologize(new FORM, profile)` under the
current generator, and the old value must equal a simulation of the generator
that produced it (sequential `str.replace` over the profile table as it stood
at `0e61b7b8e`, keeping punctuation, marking unknowns `*`). Every one of the
24,781 satisfied both.

| class | values affected |
|---|---|
| **A. POL-013 notation** — legacy bare-tilde variant `o~u` → `[o|u]` | **20,976** |
| **B. non-phonological characters dropped** — sentence punctuation (`, . ? ! " :`), segmentation `-`, infix-point `:` | **24,460** |
| **C. `z` disambiguated** — standard PHON `ɻ` → `r` | **890** |
| by tier | original 12,212 · standard 12,569 |
| by level | S 1,588 · W 13,046 · M 10,147 |
| **UNEXPLAINED** | **0** |

(A and B and C overlap; the 19 distinct combinations sum to 24,781.)

**Class A** is the sweep's target and its count is exact: 20,976 = the V147
baseline to the unit.

**Class B**: the generator that produced the published PHON kept anything in
`string.punctuation`. The current one drops unmapped punctuation as "not
sound" and strips `-` where it is not a letter. So `'"a jakən rana am, mi ko~u
pa ma-ŋo~utaʂ …'` → `'a jakən rana am mi k[o|u] pa maŋ[o|u]taʂ …'`, and the
infix-point marker in `k:an` stops appearing in IPA (`ʂ:araj` → `ʂaraj`).

**Class C is a real defect fixed, and worth stating plainly.** The old
generator applied the profile table as a *sequence of string replacements*. In
the Ortho113 Yami table `z → r` comes before `r → ɻ`, so every `z` was mapped
to `r` and then re-mapped to `ɻ` along with the genuine `r`s — the two
phonemes were **conflated** in the published standard PHON. The current
generator maps each input grapheme once, so `apnezak` is now `apnərak` (not
`apnəɻak`) while `rana` stays `ɻana`. 890 values recover a distinction they had
lost. The `original` tier was never affected (Ortho94 maps `r → r`, no
collision).

**Byte-level corroboration:** `git diff --numstat` over `XML/` is **24,781
lines added, 24,781 deleted**, and every single changed line is a `<PHON …>`
line — no re-indentation, no XML-declaration rewrite, no serializer churn.

---

## 6. Token delta and validators

| metric | `main` | now | Δ |
|---|---|---|---|
| tokens (Yami / dialect Yami) | 13,295 | **13,295** | **0** |
| S / W / M | 794 / 13,295 / 16,731 | same | 0 |
| `validate_xml` HARD / SOFT | 0 / 0 | **0 / 0** | 0 |
| `validate_text` HARD / SOFT | 0 / 21,181 | **0 / 205** | **−20,976** |
| `validate_glosses` HARD / SOFT | 0 / 75 | **0 / 75** | 0 |

All three validators ran to completion and exited 0 under `--no-exit-on-hard`.
No validator errored, and there are **no HARD findings before or after**.

- **V147 `phon_legacy_tilde_variant` 20,976 → 0.** The sweep's target metric,
  cleared.
- **V122 `parens_slashes_anywhere` 205 → 205 (SOFT), unchanged.** All 205 are
  `(`/`)` inside **TRANSL** strings — the published Chinese and English
  translations' own parentheses. POL-026/POL-027 govern FORM tiers, not
  translations; nothing to do. (FORMs contain only 4 `(` and 4 `)` in total.)
- **V061 (66) and V068 (9) unchanged** — see §7.
- Token count is unchanged because no FORM changed at all; PHON is not counted.

---

## 7. Issue #85 — claim-by-claim disposition

Every claim re-verified against the tree; none taken on trust.

| # | claim | verified? | disposition |
|---|---|---|---|
| 1 | 20,976 V147 across all 20 files; PHON uses retired bare-tilde notation; regenerate per POL-013 | **yes**, exactly 20,976 | **DONE.** Regenerated through the committed pipeline (not hand-edited). V147 → 0. The 20,976 figure reappears independently as diff class A. |
| 2 | 66 V061 morpheme-count mismatches "need source review" | **yes**, 66 | **REPORTED, not fixed** (linguistic worklist). **60 of 66 are one notation pattern**, not 66 separate defects: the source writes infixes as their own hyphen-delimited segment at word level (`k-om-an`, `s-in-avat`, `ni-t-om-agtag`), and the morpheme tier splits them into infix + root with `:` at the infixation point (`om` + `k:an`). V061 counts hyphens in the W FORM, so it fires on every one. This deviates from POL-014 (angle brackets at W level, `-` at the infixation point); converting the notation is a linguistic task, deliberately not invented here. The remaining **6** are the `UNK` words of row 3. |
| 3 | 9 V068 W/M reconstruction warnings "need source review" | **yes**, 9 | **REPORTED, not fixed** — and the cause is now known and exact: **the corpus contains exactly 9 morphemes whose FORM is the literal placeholder `UNK`** (with `UNK` glosses), one per finding, 1:1. They are `ngomon-an`, `ngomon`, `mapa-sila-siláp-i`, `veza-no-dehdeh`, `vozovóza`, `nimakalkalima-so-nakem` (×2), `pángap`, `kong-koan`. The source gives no analysis for these words; supplying one is expert work. Documented in the README. |
| 4 | one within-file duplicate group in `16. kavavatanen no kotat.xml`, S 22 and 50; POL-022 allows narrative repetition unless provenance shows an extraction duplicate | **yes** | **NOT A DEFECT — both kept, source-backed.** The Yami is identical (`i-ké-yngen na no oo na ni ina na a ka no ama na am,`) but **each occurrence carries its own, differently worded Chinese and English translation** ('非常的頭痛' / "a pain in the neck" vs '很頭痛' / "a big nuisance"), and the surrounding sentences (21/23 vs 49/51) are unrelated passages of the story. Independently translated at two points = the source printed the line twice. Narrative corpus, no dedup step declared → SOFT, correctly retained. |
| 5 | "Do not hand-edit PHON or remove the repeated sentence without source evidence" | — | **Honoured.** Every change in this branch was produced by committed code (POL-038); the repeated sentence is retained. |
| 6 | "review morphology signals" | — | **Reported, not analysed.** Rows 2 and 3 quantify and characterize the signals and name the linguistic decision each needs. No morphological analysis was invented. |

---

## 8. README

Rewritten. It previously had no corpus description, no contents, no tier
description, no orthography statement, and a "Processing" section documenting
one script that no longer exists. It now carries:

- what the corpus is (texts, counts, tiers, translations, no audio);
- **the orthography, stated and justified**: Ortho94 letters plus a lexical
  stress accent, what each tier does with the accent, and the two reasons a
  `*` appears in PHON (accents; Chinese code-switching), with counts;
- **the notation a data user would otherwise misread**: `-` segmentation, `:`
  as the infixation point, `'` as the glottal-stop *letter* (not a quote),
  `UNK` placeholder morphemes, code-switched Chinese;
- **provenance and full reproduction**: that no scrape/OCR stage exists or can
  be reconstructed, the snapshot's role, `make_xml.sh` with its arguments and
  environment overrides, and all four steps written out as runnable commands;
  `XML/` is reproducible from committed inputs by one command;
- the sidecar policy, and why there is no manual-edits step;
- known caveats (infix notation, `UNK` words, the repeated sentence, parens in
  translations).

Per the README content policy it carries no sweep narrative, no validator rule
numbers and no project-wide-rule explanations.

---

## 9. Closing steps not done here

- **GitBook corpus-page update** (per-corpus procedure step 9) — deferred to
  post-merge with the other closing steps. The page will want the orthography
  statement and the `:`/`UNK` notation notes.
- No push, no merge. One commit on `work/b4-raudong`.

**UNEXPLAINED items: none.**
