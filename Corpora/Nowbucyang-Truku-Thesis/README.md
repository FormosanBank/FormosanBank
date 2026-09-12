# Nowbucyang Truku thesis

Truku examples from Lowking Wei-Cheng Hsu / 許韋晟, *太魯閣語構詞法研究*
[Word Formation in Truku], 2008, MA thesis, National Hsin-Chu University of
Education. The revised corpus has 285 examples, 1,146 words and 1,443 morphemes
(`trv`, dialect `Truku`), with source Chinese translations where supplied.

## Rights

**License:** Unconfirmed; existing XML attribution and permission wording are preserved.

**Rights source:** Lowking Wei-Cheng Hsu / 許韋晟, 2025-04-16; evidence: ask maintainer

The author's email to Joshua Hartshorne permits contributing the examples to
FormosanBank but names no exact POL-042 licence. Publication still requires
that confirmation.

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
inventing finer analysis. The joint gloss for `niya na` is recorded in FORM
notes. The author's inconsistent infix and clitic gloss notation is preserved.

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
It builds original tiers, applies recorded edits, cleans, standardizes,
replays the reviewed merges and generates phonology before replacing `XML/`.
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
