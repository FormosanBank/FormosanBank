# Nowbucyang Truku thesis

Truku examples from Lowking Wei-Cheng Hsu / 許韋晟, *太魯閣語構詞法研究*
[Word Formation in Truku], 2008, MA thesis, National Hsin-Chu University of
Education. The revised corpus has 285 examples, 1,049 W (1,146 written words:
97 W each join two words the thesis glosses as one unit) and 1,442 morphemes
(`trv`, dialect `Truku`), with source Chinese translations where supplied.

## Rights

**License:** CC BY-NC 4.0

**Rights source:** Lowking Wei-Cheng Hsu 許韋晟 (the author), date not recorded in this repository; evidence: ask maintainer

The thesis is used with the author's permission (`rights_status=full_rights_obtained` in `TEXT@source`). Until 2026-10-17 `TEXT/@copyright` carried the prose "© Lowking Wei-Cheng Hsu / 許韋晟. Used by FormosanBank with permission."; the maintainer ruled the licence CC BY-NC 4.0 on 2026-10-15.

## Orthography

The source specifies Ortho94 on PDF page 22, with its tables on pages 23–24.
Original FORM preserves source spelling and analysis, except for the nine
sentences Joshua ruled should have no W/M or segmentation notation.
The current shared tools generate standard FORM and both PHON tiers, using
the Seediq conversion tables and their Truku column. Original PHON uses
Ortho94; standard PHON follows the current project standard.

## Audio

None.

## Notes and Issues

Three examples have word glosses but no free translation. Some source glosses
do not align to individual written morphemes; retain the word gloss without
inventing finer analysis. The author's inconsistent infix and clitic gloss
notation is preserved.

`CodeAndDocs/apply_gloss_rulings.py` applies the maintainer's 2026-10-18 gloss
rulings to the build; each step quotes the ruling it implements. `niya na`,
which the thesis glosses jointly as `尚未` (C03_E037A_0206_01, C03_E039C), is
one W with one M (POL-060); the FORM notes recording the joint gloss are kept.
C01_E011E (`N-tama ka patas gaga.`, PDF page 32) carries the thesis's gloss
line `屬-爸爸 主格 書 那`; its printed paraphrase `Patas tama ka gaga.` is the
separate, unglossed C01_E011E2.
Where the thesis prints more written morphemes than gloss pieces and the
maintainer ruled the pieces cannot be matched, each M is glossed `<UNCLEAR/>`
and the W keeps the printed gloss: the four-morpheme infix words `S-n-lu-an`
(C01_E021D), `T-n-tak-an` (C01_E023E), `H-n-puy-an` (C01_E024B) and
`h-n-qil-an` (C02_E004A), and `n-hda-an` 完成 (C02_E004B). Whole sentences the
thesis does not gloss stay unglossed: `<UNCLEAR/>` is for a gloss the source
marks as unclear or that the maintainers cannot recover, not for a sentence
the author chose not to gloss.
`skiya` in C02_E001D (`asu skiya`, printed gloss `船 ∅-飛`) is the W
`∅-skiya` with a null M `∅` (gloss `∅`, a new id, …W2M2) before the M `skiya`
(gloss `飛`, its published id …W2M1); the sentence FORM stays as printed.
The thesis writes a clitic as its own token (`Ini =ku`) but usually prints one
gloss token for host and clitic (`不-我`). Those 95 pairs, listed with their
printed form and gloss lines in `CodeAndDocs/data/manual/clitic_merges.tsv`,
are one W each (POL-060): FORM `Ini =ku`, gloss `不-我`, the host's Ms then the
clitic's M, all keeping their published ids. Three clitics with their own
printed gloss token stay separate W (`Hpuy-an =nami` 煮-LF 我們, C01_E024A;
`Gaga =su` and `Gisu =su` 正在 你, C01_E027A/B). `S-n-rus =mu` (C03_E012A),
`B-n-arig =ku` (C04_E003B) and `Mgay =ku` (C01_E011D, C01_E011D2) await a
maintainer ruling and are unchanged, as is the morpheme boundary of `Nnita`
(C03_E003A).
Three parentheticals the thesis prints after a free translation are notes on
that translation, not alternative translations: `(* 螢火蟲出來了)` in C04_E008C
(the starred reading the sentence does not have) and `(在路上)` / `(已看到人)`
in C01_E028A / C01_E028B.

Lexical and derivation tables remain source evidence outside the published
sentence/interlinear-example scope. Original PHON follows the source's
Ortho94 values; the current Ortho113 profile gives `g` and `l` different sound
values in standard PHON. See the source decisions for the scoped conversion
ruling and retained repetitions.

## Reproduction

From a FormosanBank checkout with its Python dependencies installed:

```bash
PYTHON=python3 Corpora/Nowbucyang-Truku-Thesis/CodeAndDocs/generate_xml.sh
```

For private development, set `FORMOSANBANK_ROOT` to the current shared
checkout and run `CodeAndDocs/generate_xml.sh`. `QC_OUTPUT_DIR` optionally
selects an external report directory. The build uses committed examples and
manual records, requires no PDF or private clone, and starts in fresh staging.
It builds original tiers, applies recorded edits and the gloss rulings
(`apply_gloss_rulings.py`), cleans, standardizes, replays the reviewed merges
and generates phonology before replacing `XML/`.
Validators and private PDF extraction are separate from the build.
[provenance.json](CodeAndDocs/provenance.json) records the actual shared build
commit; it never selects or requires an older tool checkout.

**POL-047 deviation:** After standardization and before phonology,
`replay_reviewed_merges.py` calls the current shared merger with the five
specific August 12 decisions in `reviewed_merges.csv`. The generic current
merger intentionally does not infer these translation-differing merges.

The original parser and private source-review helpers remain in
`CodeAndDocs/scripts/`. Do source refresh separately with the permitted PDF;
review resulting example inputs before regeneration. Raw PDFs, page images
and ephemeral reports are not publication inputs. The source hashes and
locators remain in the committed metadata and example records.
`data/manual/source_additions.csv` selects reviewed examples from the preserved
raw blocks and verifies their source text hashes before rebuilding.

Parser regression checks: `python3 -m pytest CodeAndDocs/tests`.

## Preserved decisions

See [source-decisions.md](CodeAndDocs/source-decisions.md). The existing
`data/manual/manual_sentences.xml` overrides/additions and all nine original
`manual_edits.xml` records are retained. Further records preserve the reviewed
punctuation-differing translations, partial source glosses and repeated examples'
alternative gloss readings.
The three distinct-provenance duplicate groups are retained, including
`C01_E026A_0079_01` / `C03_E034b`. Source-backed morphemes are never removed
because their gloss is absent; V064 is SOFT under current policy.
