# Nowbucyang Truku thesis

Truku Word Formation — Hsu (2008) Thesis. Truku example sentences, with word-
and morpheme-level glosses and the thesis's own Mandarin translations, from a
2008 MA thesis on Truku word formation.

## Languages and dialects

One language and one dialect, in one file:

| File | `xml:lang` | `dialect` |
| --- | --- | --- |
| `XML/Truku/Hsu_Lowking_Truku_WordFormation_2008.xml` | `trv` | `Truku` |

ISO 639-3 has one code, `trv`, for both Seediq and Truku; the `dialect="Truku"`
attribute is what makes this a Truku corpus. The build configuration
(`CodeAndDocs/scripts/config.yaml`) lists the community locations as Dumung /
銅門 and Tkijig / 崇德; the XML does not record a location or a finer dialect.

## Source

Truku examples from Lowking Wei-Cheng Hsu / 許韋晟, *太魯閣語構詞法研究*
[Word Formation in Truku], 2008, MA thesis, National Hsin-Chu University of
Education. The revised corpus has 285 examples, 1,045 W (1,146 written words:
101 W each join two words the thesis glosses as one unit) and 1,440 morphemes
(`trv`, dialect `Truku`), with source Chinese translations where supplied.

This corpus is drawn from Lowking Wei-Cheng Hsu's (許韋晟) 2008 MA thesis,
太魯閣語構詞法研究 (*Word Formation in Truku*), submitted to the Graduate
Institute of Taiwan Languages and Language Education, National Hsin-Chu
University of Education. The thesis's numbered Truku example sentences were
extracted from the source PDF (via a text-layer extraction pipeline, no OCR),
paired with their Mandarin translations, and — where the source's interlinear
gloss line aligns reliably — annotated with word- and morpheme-level glosses.
The Truku is recorded in its source Ortho94 orthography (with FormosanBank's
standard Ortho113 tier alongside). The data is used by FormosanBank with the
author's permission.

**Audio:** None.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Nowbucyang-Truku-Thesis_corpora_stats.csv` and appears on this
corpus's page on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

* Hsu, Lowking Wei-Cheng / 許韋晟. 2008. 太魯閣語構詞法研究 [*Word Formation in Truku*]. MA thesis, Graduate Institute of Taiwan Languages and Language Education, National Hsin-Chu University of Education.

See the [Terms of Use](https://formosanbank.github.io/FormosanBank/additional-resources/terms-of-use/).

## License

**License:** CC BY-NC 4.0
**Rights source:** Lowking Wei-Cheng Hsu 許韋晟 (the author), date not recorded in this repository; evidence: ask maintainer

CC BY-NC 4.0, with the permission of the author, Lowking Wei-Cheng Hsu / 許韋晟.

The thesis is used with the author's permission (`rights_status=full_rights_obtained` in `TEXT@source`). Until 2026-10-17 `TEXT/@copyright` carried the prose "© Lowking Wei-Cheng Hsu / 許韋晟. Used by FormosanBank with permission."; the maintainer ruled the licence CC BY-NC 4.0 on 2026-10-15.

## Notes and caveats

#### Orthography

The source specifies Ortho94 on PDF page 22, with its tables on pages 23–24.
Original FORM preserves source spelling and analysis, except for the nine
sentences Joshua ruled should have no W/M or segmentation notation.
The current shared tools generate standard FORM and both PHON tiers, using
the Seediq conversion tables and their Truku column. Original PHON uses
Ortho94; standard PHON follows the current project standard.

Original PHON follows the source's Ortho94 values; the current Ortho113
profile gives `g` and `l` different sound values in standard PHON.

#### Glosses, word division and translations

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
(gloss `飛`, its published id …W2M1). The sentence's original FORM is
`asu ∅-skiya`: the `∅-` is not printed in the thesis and was added, with a
`notes` attribute saying so, to match the word and morpheme analysis.
In one sentence (`asu ∅-skiya`) FormosanBank added the `∅` the thesis's gloss
implies; a note on that sentence says so.

The thesis writes a clitic as its own token (`Ini =ku`) but usually prints one
gloss token for host and clitic (`不-我`). Those 95 pairs, listed with their
printed form and gloss lines in `CodeAndDocs/data/manual/clitic_merges.tsv`,
are one W each (POL-060): FORM `Ini =ku`, gloss `不-我`, the host's Ms then the
clitic's M, all keeping their published ids. Three clitics with their own
printed gloss token stay separate W (`Hpuy-an =nami` 煮-LF 我們, C01_E024A;
`Gaga =su` and `Gisu =su` 正在 你, C01_E027A/B). `S-n-rus =mu` (C03_E012A),
`B-n-arig =ku` (C04_E003B) are one W in infix notation (`S<n>rus =mu`
擦-n-我: Ms `S-rus` 擦, `-n-` n, `=mu` 我; `B<n>arig =ku` 買-n-我 likewise).
`Mgay =ku` (C01_E011D, C01_E011D2) is one W glossed `AF-給=我`, with M `Mgay`
`<UNCLEAR/>` and M `=ku` 我.

Words the thesis glosses as one unit are one word in the word tier
(FormosanBank POL-060): the thesis writes a clitic as its own token (`Ini =ku`)
but usually prints one gloss for host and clitic (`不-我`), so those 95 pairs
are single words. The sentence text is unchanged.

`Nnita` (C03_E003A) keeps one unglossed M. Three parentheticals the thesis prints after a free translation are notes on
that translation, not alternative translations: `(* 螢火蟲出來了)` in C04_E008C
(the starred reading the sentence does not have) and `(在路上)` / `(已看到人)`
in C01_E028A / C01_E028B.

#### Scope

Lexical and derivation tables remain source evidence outside the published
sentence/interlinear-example scope. See the
[source decisions](CodeAndDocs/source-decisions.md) for the scoped conversion
ruling and retained repetitions.

#### Preserved decisions

See [source-decisions.md](CodeAndDocs/source-decisions.md). The existing
`data/manual/manual_sentences.xml` overrides/additions and all nine original
`manual_edits.xml` records are retained. Further records preserve the reviewed
punctuation-differing translations, partial source glosses and repeated examples'
alternative gloss readings.
The three distinct-provenance duplicate groups are retained, including
`C01_E026A_0079_01` / `C03_E034b`. Source-backed morphemes are never removed
because their gloss is absent; V064 is SOFT under current policy.

## Reproduction and processing

### How to reproduce

From a FormosanBank checkout with its Python dependencies installed:

```bash
PYTHON=python3 Corpora/Nowbucyang-Truku-Thesis/CodeAndDocs/generate_xml.sh
```

The XML is rebuilt reproducibly by `CodeAndDocs/generate_xml.sh`; the thesis
PDF itself is not published with the corpus (it is kept with the development
repository).

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).
[provenance.json](CodeAndDocs/provenance.json) records the actual shared build
commit; it never selects or requires an older tool checkout.

For private development, set `FORMOSANBANK_ROOT` to the current shared
checkout and run `CodeAndDocs/generate_xml.sh`. `QC_OUTPUT_DIR` optionally
selects an external report directory. The build uses committed examples and
manual records, requires no PDF or private clone, and starts in fresh staging.
It builds original tiers, applies recorded edits and the gloss rulings
(`apply_gloss_rulings.py`), cleans, standardizes, replays the reviewed merges
and generates phonology before replacing `XML/`.
Validators and private PDF extraction are separate from the build.

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

There is no `validate.sh` for this corpus.

### What each step does

`CodeAndDocs/generate_xml.sh`, in order:

1. **Set-up.** `FORMOSANBANK_ROOT` defaults to the checkout three levels above
   `CodeAndDocs/`; `PYTHON` defaults to `python3`; reports go to
   `QC_OUTPUT_DIR`, or to a new temporary directory. A fresh staging directory
   `CodeAndDocs/.build.XXXXXX` is created (and deleted on exit), and the
   committed inputs are copied into it: `scripts/`, `data/manual/`
   (`manual_sentences.xml`, `source_additions.csv`, `clitic_merges.tsv`), six
   files from `data/processed/` (`quality_filtered_examples.jsonl`,
   `examples_raw.jsonl`, `examples_clean.jsonl`, `gloss_records.jsonl`,
   `duplicates.csv`, `source_metadata.csv`) and `manual_edits.xml`.
2. **`scripts/pipeline.py --step build_formosanbank_xml`** (corpus script)
   writes the original-tier XML. It reads the 260 committed examples in
   `quality_filtered_examples.jsonl` (an earlier, PDF-dependent run of the
   same pipeline produced that file and is not re-run; its 74 rejected records
   and their reasons are in `data/processed/rejected_records.csv`), drops the
   6 marked as exact duplicates in `duplicates.csv`, and appends the 7
   reviewed examples that `data/manual/source_additions.csv` recovers from
   `examples_raw.jsonl` by source record and line range, stopping if a
   recorded SHA-256 of those source lines no longer matches. For each example
   it removes parenthesized starred (ungrammatical) forms; keeps grammatical
   slash alternatives inside the one sentence and drops starred ones; turns a
   form with an optional parenthesized part, or a printed variant clause, into
   two sentences (the second with id suffix `b`); splits words on whitespace
   and morphemes at `-` and `=` (keeping `=` on the clitic M, and an
   angle-bracketed infix as its own M after the first segment); gives
   each W the gloss-line token it aligns with, and glosses an M only when
   that word's gloss splits into the same number of pieces. The standard FORM
   is written as a copy of the original; the shared tools convert it later.
   Every `S` in `data/manual/manual_sentences.xml` (31) replaces the
   automated sentence with the same id, or is added, verbatim. A W gloss is
   then reconstructed from its M glosses wherever every M is glossed. The
   `TEXT` attributes (citation, BibTeX, `copyright="CC BY-NC 4.0"`,
   `dialect="Truku"`, and `source` with the PDF's SHA-256) come from
   `scripts/common.py` and `scripts/config.yaml`; the SHA-256 is read from
   `source_metadata.csv` when the PDF is absent.
3. **`QC/cleaning/apply_manual_edits.py --manual_file manual_edits.xml`**
   (shared) re-applies the 14 recorded hand edits listed in
   [CodeAndDocs/manual_edits.md](CodeAndDocs/manual_edits.md) (the nine W/M-free
   readings, the second reading of `C01_E026B_0080_01`, the two `niya na` notes
   and the two repeated-example gloss readings); the changelog it writes is
   copied back to `CodeAndDocs/manual_edits.md`.
4. **`apply_gloss_rulings.py`** (corpus script) applies the 2026-10-18 gloss
   rulings described under "Notes and caveats" in this order: `niya na` as one
   W; the C01_E011E thesis glosses; `<UNCLEAR/>` on the M of the five words;
   the `∅-skiya` null M and sentence note; the 95 host + clitic merges from
   `clitic_merges.tsv`; the three parenthetical translations moved to notes;
   the three held-back host + clitic words. Each step first checks that the XML
   is in the state the ruling was made against and stops with an error
   otherwise. It removes the standard FORM and PHON of every element it
   changes, so the next steps regenerate them.
5. **`QC/cleaning/clean_xml.py --warnings_dir <reports>`** (shared) cleans the
   text. No Truku attestation dictionary is available, so its quote-glottal
   correction does not change anything.
6. **`QC/utilities/standardize.py --tsv_path Orthographies/ConversionTables/Seediq_94_113.tsv`**
   (shared) writes the standard FORM tiers from the table's `Truku` column.
7. **`replay_reviewed_merges.py`** (corpus script; the POL-047 deviation above)
   removes the five sentences listed in `reviewed_merges.csv` through the
   shared `QC/cleaning/remove_duplicate_sentences.apply_removals`, which moves
   any translation the kept sentence lacks onto it as `ver="alt"`. It stops if
   either sentence's original FORM no longer matches.
8. **`QC/utilities/add_phonology.py --orthography Ortho94`** (shared) writes
   original PHON from `Orthographies/Ortho94/Seediq.tsv` and standard PHON from
   the Ortho113 table, both in their `Truku` column.
9. **Finish.** Report CSV/TXT files are copied to the reports directory; if
   a `quote_corrections.csv` is found in the build the script stops; the
   staged XML replaces `XML/` (`rsync --delete`); when `FORMOSANBANK_ROOT` is
   a git checkout its current commit is written to `CodeAndDocs/provenance.json`.
