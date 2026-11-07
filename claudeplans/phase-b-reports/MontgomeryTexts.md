# Phase B regeneration report — MontgomeryTexts

**Date:** 2026-08-12 · **Branch:** `work/montgomery` (off `main` @ `3a3c47c22`)
**Group:** 4 (underspecified pipeline) · **Corpus:** `Corpora/MontgomeryTexts` —
the three glossed Amis texts of Tamih & Montgomery (1962), *Amis text*, SIL-UND
Work Papers 6(6). `ami`, `dialect="unknown"`, 3 files, 40 S, 354 W, **0 M**, 278
English TRANSL, 358 tokens. No audio.

**Headline:** the sweep doc filed this corpus as "no standardize/add_phonology
pipeline documented at all". That was a **documentation** gap, not an unknown
profile. The profile exists, is named after this corpus, and was proved by
reproduction: `Orthographies/Montgomery/Amis.tsv` (original tier) plus
`Ortho113` (standard tier) reproduce **788 / 788** of the corpus's own
published PHON values exactly. The profile is **adopted** and PHON regenerated.
560 data points changed, 100% classified, zero unexplained; every FORM that
matters, every TRANSL and every attribute is byte-identical. V147 goes 482 → 0.
Token delta zero. Quote-correction rows: **zero**.

---

## 1. The central question: what phonology profile, if any?

The README documented no orthography and no pipeline. Rather than pick one, the
corpus's own published PHON was used as evidence — it is machine output, so the
profile that produced it is recoverable.

### 1.1 What PHON the corpus already carried

Both tiers, at both levels: 394 `original` + 394 `standard` PHON values,
all in the retired bare-tilde variant notation (`o~u`, `ɬ~ɮ`). So there was a
great deal of evidence to reproduce, and a wrong profile could not have hidden.

### 1.2 Reproduction test

Every FORM→PHON pair (all 788, S and W, both tiers) was run through each Amis
profile in `Orthographies/`, comparing against the published PHON after
normalizing POL-013 notation `[o|u]` → `o~u`. Restricted first to W-level forms
that are purely alphabetic, so hyphens and punctuation could not confound:

| profile | reproduces published **original** PHON | reproduces published **standard** PHON |
|---|---|---|
| **`Montgomery`** | **273 / 297** | 208 / 297 |
| `Ortho113` | 198 / 297 | **297 / 297 — 100%** |
| `Ortho113Liberal` | 198 / 297 | **297 / 297** |
| `Church` | 71 / 297 | 117 / 297 |
| `Ortho94` | 72 / 297 | 120 / 297 |
| `MinEd` | 72 / 297 | 109 / 297 |
| `TaiwanNandao` | 60 / 297 | 73 / 297 |
| `Huang` | 31 / 297 | 36 / 297 |

`Montgomery` leads the original tier by 75 values over the next candidate, and
`Ortho113` is exact on the standard tier — which is what `standards.csv`
designates for Amis (§1.5), so the standard tier needed no choice at all.

`Montgomery`'s 24 residual misses were not noise: they were the two known
behaviour changes between the generator that wrote the published PHON and the
current one (it kept punctuation and `-`; it applied the profile as a *sequence*
of string replacements, so `ř → r` fed into `r → ɾ` and the two rhotics were
conflated). Simulating that generator — case-insensitive sequential replace over
the table in file order, punctuation kept, legacy `x~y` notation — closes the
gap completely:

| tier | profile | published PHON reproduced |
|---|---|---|
| original | `Montgomery` | **394 / 394 — 100%** |
| standard | `Ortho113` (default column) | **394 / 394 — 100%** |

**788 / 788.** Including the two forms containing the corpus's one
out-of-profile letter, `f̆`, which the old generator marked `*`. There is no
residue and therefore nothing left for a different profile to explain.

### 1.3 Letter inventory

The original tier's complete FORM character inventory is

```
a e f g h i k l m n o p r s t w y ř ?   (+ capitals A E I K L M N O R S T)
plus '-' (132), space, and one combining breve U+0306 (×2)
```

— pure ASCII apart from `ř` and that breve. Two entries settle the candidate
question on their own:

- **`ř`** (64 occurrences). It is a letter row in **`Montgomery/Amis.tsv` and
  nowhere else** — no other Amis profile in the repository lists it.
- **`?`** (80 occurrences), used word-internally and word-finally (`roma?`,
  `nay-foti?`, `mi-sa?osi`). `Montgomery` maps it `ʡ`; Ortho113/94/Church/MinEd
  have no `?` row at all (they write the glottal `'`), so under any of them the
  glottal stop would be **silently deleted as punctuation** — the exact failure
  WakelinTexts documents for Yami.

Conversely, every letter the corpus uses is in the Montgomery profile; the
profile's unused rows (`b v d x : ^ u`) are inert here. The digraph `ts` (→ `ʦ`)
is likewise Montgomery-only among the candidates; Ortho113 writes `c`.

### 1.4 Provenance and date

- **The profile was built for this corpus.** `git log` shows
  `Orthographies/Montgomery/Amis.tsv` and
  `ConversionTables/Amis_Montgomery_113.tsv` were both **added in commit
  `10f53f04a` ("Updated Montgomery after Akiw comments.", 2026-03-19)** — the
  same commit that regenerated all three of this corpus's XML files. The two
  files have been touched exactly once since, by the repo-wide POL-013 notation
  migration `33b0e076d`. Nothing else in the repository references them.
- **The same commit deleted the line "The orthographic system used has not yet
  been identified."** from the corpus README, replacing it with the
  `mi-salrama` note. The orthography was identified in March; only the README
  sentence recording the *absence* was removed, and nothing was written in its
  place. That is the whole of the Group 4 gap.
- **Chronology** is consistent but not decisive here: the source is 1962, long
  before any modern scheme, which is why it needs a bespoke profile at all.

### 1.5 `standards.csv`

`standards.csv` line 2 is `Amis,Ortho113`. Respected: the standard tier is
built with the `Amis_Montgomery_113` conversion table and its PHON is generated
from Ortho113 (the `default` dialect column, since `dialect="unknown"`).
`standards.csv`, `Orthographies/` and every shared profile are **untouched** by
this pass.

### 1.6 Conversion-table verification (ruling 3)

`validate_conversion_table.py Orthographies/Montgomery/Amis.tsv
Orthographies/Ortho113/Amis.tsv
Orthographies/ConversionTables/Amis_Montgomery_113.tsv`:

| dialect column | confirmed | mismatch |
|---|---|---|
| **Southern** | **5 / 5** (`ts→c`, `?→'`, `l→d`, `r→l`, `ř→r`) | 0 |
| Xiuguluan / Coastal / Malan / Hengchun | 4 / 5 | 1 — `l → d` (`d` / `[ɬ\|ɮ]`) |

Four of the five rows are confirmed under every dialect. The fifth, `l → d`, is
coherent only under Southern, where Ortho113 `d` is a stop; elsewhere `d` is a
lateral fricative. So the corpus's `l` is transcribed `d` in the original IPA
and `ɬ~ɮ` in the standard IPA, for the same word. **Reported, not fixed**
(§7.1): the fix is either a dialect assignment or a profile edit, and both are
linguistic calls. Nothing was changed to paper it over.

### 1.7 Verdict

**Evidence is clear. Profile adopted, PHON generated.** This corpus is not a
WakelinTexts (no identifiable writing system) or a Siraya_Gospels (a standard
tier with no designated standard scheme): its source orthography is documented
in a committed profile, that profile reproduces its published phonology
exactly, and its target scheme is the one `standards.csv` names.

---

## 2. POL-035 snapshot: TAKEN (before any cleaning)

The corpus is **not** reproducible from committed inputs. `CodeAndDocs/` held
only `Original.pdf`: no OCR output, no parser, no intermediate. (The OCR text
survives in an uncommitted sibling working directory; it is not in this
repository and this pass does not rely on it.) The hand-checked XML is
therefore the source of record.

Pristine `XML/` copied to `CodeAndDocs/pre_correction_snapshot/XML/` and
verified byte-identical (`diff -r`, clean) **before any pipeline step ran**.
3 files, 120 KB. Noted in the README under "Provenance and reproducibility".
Per POL-038 the snapshot is never edited: `make_xml.sh` restores from it on
every run and all shaping happens on the way out.

---

## 3. Single entry point: `CodeAndDocs/make_xml.sh` (new, executable, committed)

```
0. restore XML/ from CodeAndDocs/pre_correction_snapshot/XML/
1. QC/cleaning/clean_xml.py                       --corpora_path XML
2. QC/utilities/standardize.py --tsv_path Orthographies/ConversionTables/Amis_Montgomery_113.tsv
3. CodeAndDocs/desegment_standard_sentences.py    --corpora_path XML   (new this pass)
4. QC/utilities/add_phonology.py --orthography Montgomery --corpora_path XML
```

Root/interpreter parameterized as in SEALS33/RauDong (`FORMOSANBANK_ROOT` arg
or env, `PYTHON` override). The script sequences the shared utilities directly
and is the only documented command. **Verified idempotent:** a second full run
is byte-identical to the first (`diff -r` clean).

`apply_manual_edits.py` is **absent**: there is no `CodeAndDocs/manual_edits.xml`
and no hand edits to re-apply, so including it would be a documented no-op. The
two editorial corrections to the source text (`mi-salrama` → `mi-salama`, and
the OCR mis-set `f̂` → the printed `f̆`) predate the snapshot and are part of it.

Step 1 is a **verified no-op** on this corpus (snapshot vs post-clean `diff -r`
is clean) — the source text is plain ASCII apart from `ř` and the breve. It is
kept so the canonicalization guarantee holds by construction, not by accident.

The standing `--copy` → `--remove_accents` substitution **does not apply**: this
corpus's flow uses a real conversion table (`--tsv_path`), which is the third,
strongest option and mutually exclusive with both. `--remove_accents` would
have thrown away the five-letter transliteration that is the whole point of
this corpus's standard tier. Reconciled and documented in the README.

### 3.1 Step 3, and the shared-utility gap behind it — ESCALATED

`standardize.py` strips morpheme-segmentation hyphens from S-level standard
FORMs (its C012 step) whenever `-` is not a letter of the target orthography.
It is not a letter of Amis, so C012 should fire here. It does not:
`_apply_standard_hyphens` returns early on `if element.find(".//M") is None`,
and **this corpus has no morpheme tier** — it is segmented at the sentence and
word tiers with `-`, but carries zero `M` elements.

The consequence is measurable. With steps 1→2→4 only, the regeneration *added*
hyphens back into 29 sentence-level standard FORMs that the published corpus
did not have, and `validate_text` went from **0 to 31** `V133
dash_in_S_standard_FORM` SOFT findings — a rule whose own docstring calls the
character "a leftover segmentation marker that should have been removed". The
tool and the validator disagree, and the validator is right.

Two things follow:

1. **The published de-hyphenated state was a hand edit, not a pipeline
   product.** Commit `132bb7839` (2026-06-08) removed those hyphens by hand
   — including from the PHON tier — with the message "*Removing hyphens from
   standard tier for Montgomery, though in fact it's not at all clear if they
   should be there or not*". That is an unrecorded hand edit of exactly the
   kind procedure step 2 (POL-030) asks to capture.
2. **It is captured as committed code, not re-applied by hand.**
   `CodeAndDocs/desegment_standard_sentences.py` is a corpus-local one-off, the
   form POL-038 prescribes (the WakelinTexts `drop_derived_tiers.py`
   precedent). It **imports `standardize._process_standard_hyphens`** rather
   than reimplementing the rule, so the two cannot drift; it touches S-level
   standard FORMs only; it writes through the shared `_prettify.prettify` with
   standardize.py's blank-line-stripping idiom, so serialization is
   byte-identical to house style. Run output: `TOTAL: 31 S-level standard
   FORM(s) de-segmented across 3 files` (14 / 8 / 9). Verified idempotent (a
   second run reports 0 and rewrites no bytes).

**The `.//M` guard itself was NOT patched.** It is shared code affecting every
corpus without a morpheme tier, and changing it inside a corpus turn is the
sweep-wide decision this branch has no mandate to make. **Escalated to the
maintainer** as the proper fix, after which this corpus-local step becomes a
harmless no-op.

---

## 4. Warning sidecars (POL-033) and quote correction

**No sidecar of any kind was produced.** After a full run, no
`cleaner_warnings.csv`, no `standardize_warnings.csv` and no `html_entities.log`
exists anywhere under `Corpora/MontgomeryTexts` — nothing to review or delete,
nothing committed. (The `quote_corrections.csv` and `html_entities.log` that
`find` reports elsewhere in the tree belong to Glosbe, ePark, YeddaPalemeqBlog
and Nowbucyang and are pre-existing on `main`.)

**Amis quote correction is ARMED and it fired zero times.**
`QC/validation/reference/Amis/attestation.txt` (505 entries, hand-validated) is
present and was loaded — this is not a "disarmed language" case. **No
`quote_corrections.csv` was created anywhere in the tree**, so there are
**0 c031 rows and 0 c032 rows** to report.

The reason is structural rather than lucky, and it is worth stating because it
generalizes: `clean_xml` runs quote correction on S-level
`FORM[@kindOf="original"]` containing `'`, and **this corpus's original tier
contains no apostrophe of any kind** — zero straight, zero typographic. It
writes the glottal stop `?` (80 occurrences), which the classifier never
inspects. The character inventory in §1.3 is the proof. The standard tier's 80
`'` are out of scope by design (`standardize.py` owns the standard tier).

**Cross-reference against `quote_review_nonwiki_amis.md`** (repo root, 239
flagged sentences): the worklist draws from **Glosbe (224), ePark (12),
NTUFormosanCorpus (1), Presidential_Apologies (1), Safolu-Amis-Dictionary (1)**
and **zero MontgomeryTexts sentences**. Consistent with the empirical count.
No correction here needs individual justification, because there are none.

**POL-041** (never clean W/M-level TRANSL) is satisfied without special
handling: `clean_xml` reaches W-level FORMs but its TRANSL branch is scoped to
`sentence.findall('TRANSL')` — direct children of S only. All 278 TRANSL values
came through byte-identical (§5).

---

## 5. Diff audit vs `main` — 100% classified

Scripted element-by-element comparison of every atomic datum in all 3 files:
TEXT/S/W attribute sets, each element's child-tag sequence, and every
FORM/PHON/TRANSL value **and** attribute set, keyed by element id and
`kindOf`/`xml:lang`.

**4,502 data points on `main` → 4,502 now. 0 added, 0 removed, 560 changed,
3,942 unchanged.**

| field | changed | total |
|---|---|---|
| **PHON** text | **554** | 788 |
| **FORM** text | **6** | 788 |
| FORM attrs | 0 | 788 |
| PHON attrs | 0 | 788 |
| TRANSL text | **0** | 278 |
| TRANSL attrs | 0 | 278 |
| element `@attrs` (TEXT/S/W) | 0 | 397 |
| element child sequence | 0 | 397 |

### 5.1 Both endpoints reconstructed from the FORM tier

As in the RauDong pass, each changed value was verified by rebuilding *both*
sides, not by eyeballing the delta:

| check | result |
|---|---|
| baseline PHON = **legacy** generator over baseline FORM | **788 / 788** |
| new PHON = **current** generator over new FORM | **788 / 788** |

Every PHON value on both sides is a deterministic function of its own FORM
under the respective generator. Nothing in the PHON tier is unaccounted for by
construction.

### 5.2 Classification

Classes overlap; the 14 distinct combinations sum to 560.

| class | values affected |
|---|---|
| **P1. POL-013 notation** — legacy `x~y` → `[x\|y]` | **482** |
| **P2. non-phonological characters dropped** — segmentation `-`, sentence punctuation | **145** |
| **P3. `ř` / `r` de-conflated** — both used to map to `ɾ`; now `ř`→`r`, `r`→`ɾ` | **57** |
| **P4. the `f̆` breve no longer marked `*`** in original PHON | **4** |
| **P5. capitalized title line converted, PHON follows** | **2** |
| **F2. capital letters now converted by the table** (standard FORM) | **4** |
| **F3. combining breve stripped from the standard tier** (standard FORM) | **2** |
| **UNEXPLAINED** | **0** |

By tier: original PHON 280, standard PHON 274. By level: S 80, W 474 (+ 6 FORM:
4 at S, 2 at W). All 6 changed FORMs are `standard`; **no `original` FORM
changed anywhere**.

**P1** is the sweep's target and its count is exact: **482 = the V147 baseline
to the unit.**

**P3 is a real defect fixed.** The old generator applied the profile as a
sequence of string replacements, and in `Montgomery/Amis.tsv` the row `ř → r`
precedes `r → ɾ`; so every `ř` became `r` and was then re-mapped to `ɾ` along
with the genuine `r`s. The trill and the tap were **conflated** in the published
original PHON. The current generator maps each grapheme once, so `tayřa` is now
`tajra` (not `tajɾa`) while `roma?` stays `ɾomaʡ`. 57 values recover a
distinction they had lost. The standard tier was never affected (the conversion
table separates the two letters before Ortho113 sees them).

**F2** is likewise a defect fixed: the three capitalized title lines
(`SIRO`, `NAMAR`, `O-LEMAK`) had been left in *source* spelling in the standard
tier, because the pre-2026 run derived no capital variants from the conversion
table. `standardize.py` now does, so they read `SILO`, `NAMAL`, `O-DEMAK`. P5 is
their PHON following along.

**F3 / P4** are the corpus's one out-of-profile letter, `f̆`, in `Day_I_Now`
S15/S15W6. `standardize.py` treats unlisted diacritics as source prosody and
strips the breve from the standard tier (`masasi'af̆a'araw` →
`ma-sasi'afa'araw`); `add_phonology` now lets combining marks through instead of
flagging them `*`. Net effect on the visibility of the gap: the standard tier
loses a signal (2 values) and the original PHON loses its `*` marker (4 values).
Both are the shared tools' documented behaviour, not corpus-specific handling;
both are called out in the README so a data user is not misled. **Reported,
not patched** (§7.2).

### 5.3 Byte-level corroboration

`git diff --numstat` over `XML/` is **560 added / 560 deleted** (273/273,
160/160, 127/127), and every changed line is a `<PHON …>` (554) or `<FORM …>`
(6) line. No re-indentation, no XML-declaration rewrite, no trailing-newline
change, no serializer churn.

---

## 6. Token delta and validators

| metric | `main` | now | Δ |
|---|---|---|---|
| **tokens** (Amis / dialect unknown) | 358 | **358** | **0** |
| S / W / M | 40 / 354 / 0 | same | 0 |
| `validate_xml` HARD / SOFT | 0 / 0 | **0 / 0** | 0 |
| `validate_text` HARD / SOFT | 0 / 501 | **0 / 17** | **−484** |
| `validate_glosses` HARD / SOFT | 0 / 175 | **0 / 175** | 0 |

All three validators ran to completion and exited 0 under `--no-exit-on-hard`.
No validator errored, and there are **no HARD findings before or after**.

Rule by rule:

- **V147 `phon_legacy_tilde_variant` 482 → 0.** The sweep's target metric,
  cleared. Reappears independently as diff class P1.
- **V116 `non_ascii_in_form` 2 → 0.** The two `f̆`-bearing *standard* FORMs;
  the breve is now stripped there (§5.2 F3). The original tier keeps it and is
  not in this rule's scope.
- **V133 `dash_in_S_standard_FORM` 0 → 0.** Held at zero by step 3; it was
  0 → 31 without it (§3.1).
- **V122 `parens_slashes_anywhere` 15 → 15 (SOFT), unchanged.** All 15 are
  `(`/`)`/`/` inside **TRANSL** strings — the 1962 translator's own
  parentheses and one alternation. POL-026/POL-027 govern FORM tiers, not
  translations; nothing to do. The FORM tiers contain no parens or slashes at
  all.
- **V135 `trailing_punct_mismatch` 2 → 2 (SOFT), unchanged — and both are
  false positives.** `Day_I_Now` S2 ends `nay-foti?` and `Silo` S7 likewise;
  the standard tier ends `'`. The rule reads the glottal *letter* as trailing
  punctuation. Same cause as the `?` question in §1.3. Documented in the README
  caveats; no rule change proposed from a corpus turn.
- **V060 (2), V061 (57), V065 (116) unchanged** — all read the original tier
  and the element structure, neither of which moved. See §7.3.

---

## 7. Verified findings referred to the maintainer (not fixed here)

1. **The `l` / `d` correspondence is dialect-dependent and the dialect is
   `unknown`.** `Montgomery/Amis.tsv` maps source `l` → `d` (a stop). Ortho113
   Amis writes `d` for a stop only in the **Southern** column; in Xiuguluan,
   Coastal, Malan and Hengchun `d` is `[ɬ|ɮ]`. Because `dialect="unknown"`
   resolves to the `default` column, the same word is `datəŋ` in original IPA
   and `ɬ~ɮatəŋ` in standard IPA. Either the corpus is Southern Amis (the
   conversion table is fully coherent only there — §1.6) or the profile's
   `l` row overstates the stop. Both are linguistic calls; the article does not
   name Tamih's variety. Nothing was changed.
2. **`f̆` is undescribed.** One word, `ma-sasi?af̆a?ařaw` (`Day_I_Now` S15 and
   S15W6). Commit `132bb7839` already corrected an OCR mis-set `f̂` to the
   printed `f̆`, so the breve is what the article prints — but no profile row
   covers it and the article's key is not in `CodeAndDocs/`. Adding a row
   would make both derived tiers state a sound we cannot source.
3. **No morpheme tier, and the segmentation is visible without one.** 57 W
   FORMs carry a hyphen but have no `M` children (V061), and the three
   capitalized title lines have no W tier at all (V060 ×2, one per file with a
   multi-word title). 116 of 354 W elements have no gloss (V065) — the article
   glosses selectively. Supplying morphemes or glosses is expert work; none was
   invented.
4. **The `.//M` guard on C012.** §3.1. A shared-utility change, deliberately
   left to the maintainer.
5. **V135 misreads the glottal letter `?` as trailing punctuation** (2
   findings). Cosmetic, SOFT, and the same class of question as WakelinTexts'
   `?`. A rule that consulted the source profile's letter set would not fire.

---

## 8. README

Rewritten. It was a 17-line fragment with no contents, no tier description, no
pipeline, and a bare sentence about one hand correction. It now carries:

- what the corpus is (three texts with their titles and sizes, tiers, counts,
  glossing coverage, no audio, `dialect="unknown"` and why);
- **the orthography, stated and justified**: the five-letter correspondence
  table, and the two traps a modern reader falls into — `?` is the glottal
  *letter*, and the source's `l`/`r`/`ř` are not the modern `l`/`r`;
- the `f̆` gap and what each tier does with it;
- the hyphen convention (word tier keeps segmentation, sentence tier does not);
- the two editorial corrections to the source text;
- **provenance and full reproduction**: that no OCR/parse stage exists or can be
  reconstructed, the snapshot's role, `make_xml.sh` with its arguments and
  environment overrides, and all steps written out as runnable commands
  with what each does; `XML/` is reproducible from committed inputs by one
  command;
- the sidecar policy, and why there is no manual-edits step;
- known caveats (no morpheme tier, unglossed words, the `l`/`d` dialect
  question, parens in translations, the `?`-as-punctuation false positive).

Per the README content policy it carries no sweep narrative, no validator rule
numbers and no project-wide-rule explanations.

---

## 9. Closing steps not done here

- **GitBook corpus-page update** (per-corpus procedure step 9) — deferred to
  post-merge with the other closing steps. The page will want the orthography
  statement and the `?`-is-a-letter note.
- No push, no merge. One commit on `work/montgomery`.

**UNEXPLAINED items: none.**
