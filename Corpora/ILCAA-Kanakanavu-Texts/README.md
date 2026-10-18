# Asai et al. (2026) Kanakanavu Texts

This corpus is the Kanakanavu (`xnb`) text of Asai, Mei, Li and Tsuchida's 2026 *Kanakanavu Texts* (Research Institute for Languages and Cultures of Asia and Africa, Tokyo University of Foreign Studies): 44 narratives and the example sentences of the book's grammatical introduction, with the book's own English translations and, for the narratives and the introduction's numbered examples, its word and morpheme glossing. The introduction's word lists and the book's explanatory footnotes add single-word entries. The source is a born-digital PDF, so nothing was OCR'd. There is no audio.

## Languages and dialects

Language is Kanakanavu (`xnb`). All 48 files in `XML/Kanakanavu/` declare `xml:lang="xnb"` and `dialect="Kanakanavu"` on their `<TEXT>`; the dialect value is the language name, as for every single-dialect language in [dialects.csv](../../dialects.csv). The book does not divide its texts by village or dialect. The one village-labelled phonetic comparison in the introduction (page 15) is not published (see Notes and caveats).

The introduction's lexical material comes from two transcription groups, and each has its own file: `ILCAA_KanakanavuTexts_intro_Asai2026.xml` (53 S) and `ILCAA_KanakanavuTexts_intro_Tsuchida1976.xml` (16 S, Table 2's pronouns). Both are Kanakanavu.

## Source

Asai, Mei, Li and Tsuchida (2026), *Kanakanavu texts*, edited by Paul Jen-kuei
Li and published by ILCAA, Tokyo University of Foreign Studies.

#### Source and coverage

The committed [252-page PDF](CodeAndDocs/data/raw/pdf/B602_KanakanavuText.pdf)
has SHA-256 `785058bad6a8495f8b5fb51ed3d0eaf7da1736e791b308611d9442c010d93c03`.
The parser accounts for 44 narratives and 40 numbered introduction examples
(48 introduction units), totalling 1,431 source units. Of 24 parenthetical
constructions, nine use W/M FORM variants and 15 retain separate S readings,
producing 1,446 numbered-example S records. Another source file contains 57
lexical records from 49 explanatory footnotes. Introduction tables/prose and
the title linked to footnote 29 add 69 S, for 1,572 S in the final XML.

Table 1 of the introduction (physical page 16) is not published: maintainer
ruling 2026-10-18, "Drop all of Table 1." Neither are the two prose examples
next to it (kumakaɨn(ɨ) and the /kaɨnɨ/ [kɅɨnɨ] pair): "Drop the prose
examples." All 32 records are recorded as an excluded region in the
introduction ledger.

The [footnote ledger](CodeAndDocs/footnote_lexemes.jsonl) accounts for all 87
notes. The [introduction ledger](CodeAndDocs/introduction_lexemes.json) keeps
the Tsuchida 1976 pronouns in a separate file. The one Saaroa word the
introduction cites (iɫakia, PDF page 20) is not published (maintainer, 2026-10-18).
It records bound morphology/templates as context and the unresolved village
phonetics explicitly. Tsuchida's source distinguishes the two vocatives
from ordinary pronouns; all four forms keep separate records. These counts are
not a whole-book coverage verdict.

The source parser repairs a misplaced interjection gloss in Naparamaci example
68, omits empty gloss padding, restores the aligned W/M tiers of introduction
examples 23a-d and separates eight stacked infix pairs.

Source W/M glosses and free translations remain separate. Source narrative
repetitions, publisher corrections, Japanese name characters, and meaningful
translation parentheses are preserved. See [source decisions](CodeAndDocs/source-decisions.md).

#### Audio

None supplied with this source.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/ILCAA-Kanakanavu-Texts_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

Asai, E., Mei, K., Li, P. J.-k., & Tsuchida, S. (2026). *Kanakanavu Texts* (P. J.-k. Li, Ed.). Research Institute for Languages and Cultures of Asia and Africa, Tokyo University of Foreign Studies.

The corpus is also subject to the central FormosanBank [Terms of Use](https://formosanbank.github.io/FormosanBank/additional-resources/terms-of-use/).

## License

**License:** CC BY 4.0

**Rights source:** Paul Jen-kuei Li, Yi-Chun Chen, Hsiu-min Huang and Amy
Ming-luan Chen, 2026 (the source was published under this licence; there is no
separate grant); evidence: ask maintainer

CC BY 4.0 (Creative Commons Attribution 4.0 International). The licence is stated on the source PDF itself (physical page 3); the rights holders are Paul Jen-kuei Li, Yi-Chun Chen, Hsiu-min Huang and Amy Ming-luan Chen (2026).

The licence is stated on the source PDF itself (physical page 3). The source
PDF may be redistributed under that licence with attribution.
Source generation writes the canonical licence value `CC BY 4.0` (POL-042),
with attribution retained here. All 48 files carry `CC BY 4.0`.

## Notes and caveats

- **The standard tier is a transliteration into Ortho113.** The book writes Kanakanavu with IPA-style letters (`ʔ`, `ŋ`, `ə`). The standard tier writes `ʔ` as `'`, `ŋ` as `ng` and `ə` as `e`. It also writes `l` as `r`, as Ortho113 has a single `r`. Two distinctions are therefore lost in the standard tier: `ə` versus the rarer native `e`, and `l` versus `r`. The original tier keeps both.
  The standard tier merges `ə` and the rarer native `e` into `e`, and `l` and `r` into `r`,
  as Ortho113 does. The original tier keeps both distinctions.
- Standard PHON follows Ortho113 (POL-003). The source's conditioned c/s
  pronunciation stays in original PHON; the former private standard override
  is retired. The two tiers therefore differ in those environments.
- **The capital glottal stop `Ɂ` is written `ʔ`.** Four of the narratives and three introduction examples print the glottal stop with this glyph. The original tier writes it as the ordinary `ʔ`, so a search for `ʔ` finds all of them.
  The printed capital glottal stop `Ɂ` (four narratives and three introduction examples) is written `ʔ` in the original
  tier from the start and is then the ordinary `ʔ`. Capitalization is not phonemic, so
  shared PHON lower-cases names.
- **Infix brackets stay in the original sentence form, not the standard one.** The original tier keeps the book's `<um>`; the standard sentence form drops the brackets. Word and morpheme forms keep their segmentation marks (`-`, `=`, `<...>`) as printed, and the morpheme tier carries the infix as `-um-`.
  Infix angle brackets stay in the original sentence FORM and are dropped from the standard
  sentence FORM; W and M forms keep their segmentation marks. Hyphens are removed from the
  standard FORM of the lexical records, too.
- **Spelling variants the book prints in parentheses are kept as alternatives.** For example `mu-usa (= mu-kusa)` is one sentence whose word carries `mu-kusa` as an alternative reading. Nine pairs are handled this way. Where the two readings would be glossed differently, or the book prints whole optional words, the second reading is its own sentence, with the same ID plus `-opt`.
  The source parser resolves nine spelling/pronunciation variants and the old
  V1/V2 IDs. Tsuchida's notation key resolves ha/sua in two passages. Page 195
  example 35 (ha/sua and iihaa/iisua) stays two S readings (maintainer, 2026-10-18).
- **The example-23 clauses.** The book prints square brackets around the pseudo-cleft clause in examples 23a to 23d. The original sentence form shows them as parentheses; the standard form and the word and morpheme forms have none.
  In examples 23a-d the clause brackets are written as parentheses in the original sentence
  FORM (shared cleaning) and are absent from the standard FORM and from every W and M.
  Clause grouping stays at S; shared cleaning normalizes its brackets to
  parentheses and PHON omits them. These clauses are not optional material.
- **`əhə kai` is one word.** In Naparamaci example 68 the book prints a single gloss, "interjection", under the two words, so they are published as one word and one morpheme.
  Naparamaci example 68 prints one gloss under two words, so `əhə kai` is one W and one M.
- **Not every sentence has word-level analysis.** The introduction's word lists and the footnote entries are single words that the book does not segment; they carry a translation and no word or morpheme tier. Only three of the introduction's lexical examples come with the book's own morpheme analysis.
  Introduction lexical material has two transcription groups (Asai 2026 and
  Tsuchida 1976). Table 1 is not published (see above).
  Table 2's 16 pronouns have a
  verified segmental route; their stress marks remain in original FORM.
  Supplemental records preserve printed readings; only three analyzed prose
  examples supply W/M tiers.
- **Not included.** The introduction's Table 1 (historical transcriptions by Tsuchida 1969, Szakos 1999 and the 2007 Basic Vocabulary) and two prose examples next to it are left out by decision. The village-labelled phonetic comparison on page 15 is also left out, because the book gives no written form for it.
  The village-labelled phonetic comparison remains open in the ledger.
- **Printed translation parentheses are kept.** The book's own clarifications, for example `Thereupon, (the girl) left`, stay in the English translations. One translation prints an em dash that the shared cleaning step writes as a hyphen.
  One English translation prints an em dash that shared cleaning writes as a hyphen
  (`clean_xml.py` writes every dash as `-`); the maintainer ruled to leave it.
- **Repeated passages are kept.** Repetition within a story is source data and is not removed.
- The earlier ten-page expert review and historical samples cover those records
  only. They do not establish a current visual review of every page or reading.

## Reproduction and processing

**Status:** built on 2026-10-18 by `CodeAndDocs/generate_xml.sh` (48 Kanakanavu
files, 1,572 S). The maintainer reviewed the QC findings and
the open notation questions that day; the rulings are in
[source decisions](CodeAndDocs/source-decisions.md).

[Basecamp card](https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/10012922283),
[corpus PR #155](https://github.com/FormosanBank/FormosanBank/pull/155),
and [GitBook PR #51](https://github.com/FormosanBank/FormosanBankGitbook/pull/51).

### How to reproduce

```bash
bash Corpora/ILCAA-Kanakanavu-Texts/CodeAndDocs/generate_xml.sh
```

Run `bash Corpora/ILCAA-Kanakanavu-Texts/CodeAndDocs/generate_xml.sh` in a FormosanBank checkout. It extracts the text from the committed source PDF, builds the XML, then runs FormosanBank's shared cleaning, standardization and phonology steps. The README documents the dependencies, the source coverage and every decision about the book's notation. The [build provenance](CodeAndDocs/provenance.json) records the FormosanBank commit the published XML was built against.

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

Install [the declared dependencies](CodeAndDocs/requirements.txt). The executable
entry point reads committed inputs and uses the supplied current FormosanBank
checkout, or the containing checkout when this package is under `Corpora/`:

```sh
python3 -m pip install -r CodeAndDocs/requirements.txt
PYTHON=python3 CodeAndDocs/generate_xml.sh /path/to/current/FormosanBank
```

The build stages source extraction, shared cleaning, standardization and PHON,
then installs successful output. It performs no QC or source refresh. Narrative
deduplication is not a build step.

The [provenance record](CodeAndDocs/provenance.json) names the FormosanBank
commit that built the XML. The previous private phonology override and count-based QC acceptance wrapper are retired.
The entry point reads the Kanakanavu source profile `Asai2026` from the
FormosanBank checkout (`Orthographies/Asai2026/`), and the conversion table `Kanakanavu_Asai2026_113.tsv` from
`Orthographies/ConversionTables/`.
Table 2's 16 pronouns use the narrative route's reviewed subset.
These tables need no installation in FormosanBank.

For source investigation without producing final derived tiers:

```sh
python3 CodeAndDocs/scripts/pipeline.py --workspace /tmp/kanakanavu-review
python3 CodeAndDocs/scripts/source_xml_audit.py --workspace /tmp/kanakanavu-review \
  --xml /tmp/kanakanavu-review/build/xml_drafts
KANAKANAVU_WORKSPACE=/tmp/kanakanavu-review python3 -m pytest -q
```

The comparison checks extracted text, source sidecars and the selected XML,
including W/M FORM variants and supplemental forms, meanings and context. Source-only
output has no derived tiers, so the report still fails its completeness checks.
It never certifies a visual review.

### What each step does

`CodeAndDocs/generate_xml.sh` runs these steps in this order. It stops at the first failure (`set -euo pipefail`), and nothing is copied into `XML/` unless every earlier step succeeded.

1. **Find the FormosanBank checkout.** It uses, in order: the `FORMOSANBANK_ROOT` environment variable, the first command-line argument, the checkout two levels above the corpus folder if it has a `QC/` folder (the normal case under `Corpora/`), or a sibling `../FormosanBank`. The Python interpreter is `$PYTHON`, default `python3`.
2. **Check the transcription groups.** An inline Python check reads `CodeAndDocs/introduction_lexemes.json` and exits with status 2 if any record names a transcription group other than `Asai2026` or `Tsuchida1976`. (Table 2's 16 `Tsuchida1976` pronouns are converted with the reviewed `Asai2026` letter subset; no other group has a reviewed route.)
3. **Check the orthography inputs.** It exits with status 2 unless all three exist in the FormosanBank checkout: `Orthographies/Asai2026/Kanakanavu.tsv`, `Orthographies/Asai2026/Kanakanavu.rules.tsv` and `Orthographies/ConversionTables/Kanakanavu_Asai2026_113.tsv`.
4. **Make a staging folder** `CodeAndDocs/.build-XXXXXX` (random suffix). It is deleted when the script exits, together with every report written into it.
5. **Extract the source and build source-only XML:** `scripts/pipeline.py --workspace <staging>`. In order, it:
   - refuses to run unless `CodeAndDocs/data/raw/pdf/B602_KanakanavuText.pdf` exists and has the SHA-256 given above;
   - reads every page's words with their positions (PyMuPDF) and writes page text and positioned-word files into the staging folder;
   - reads the table of contents and cuts the book into the 44 narratives listed in the script, plus one text for the introduction's numbered examples 1-40 (physical pages 17-27);
   - parses each numbered example into a source line, a gloss line and a free translation, and aligns source words with gloss words by their position on the page to build the W and M rows;
   - extracts the 87 footnotes and the printed styles;
   - writes a review queue (`manual_review_queue.csv`) and a duplicate report (`duplicates.csv`). Both are reports only: no sentence is dropped on their account, which is why narrative deduplication is not a build step;
   - expands the 24 reviewed parenthetical constructions (the table `PARENTHETICAL_VARIANTS` in the script). The nine listed as `form_variants` in [notation_decisions.tsv](CodeAndDocs/notation_decisions.tsv) become one S whose differing W and M forms carry the second reading as a `FORM ver="alt"`; the other 15 become two S, the second with `-opt` added to its ID, and both carry a `notes` attribute on the original FORM. Two starred introduction examples (page 24 example 23b and page 25 example 26a, per [source decisions](CodeAndDocs/source-decisions.md); the table `RESOLVED_JUDGMENT_GLOSS_REPLACEMENTS` in the script) have the excluded material removed from their gloss line, and their original FORM carries a `notes` attribute saying so. For the four `clause_brackets` rows (examples 23a-d) the square brackets are removed before the W tier is built. The script stops if it finds other than 1,431 source units or 1,446 S;
   - writes one XML file per narrative and one for the introduction examples. Every `<TEXT>` gets `xml:lang="xnb"`, `dialect="Kanakanavu"`, the citation, the BibTeX citation, `copyright="CC BY 4.0"` and a `source` attribute naming the part, text and printed pages. Each S has an original FORM and its English TRANSL; W and M carry an original FORM and the book's gloss as `TRANSL kindOf="original"`;
   - writes `ILCAA_KanakanavuTexts_footnote_lexemes.xml` (57 S) from [footnote_lexemes.jsonl](CodeAndDocs/footnote_lexemes.jsonl) via `scripts/footnote_lexemes.py`. It stops if the footnote inventory differs from the PDF, if a footnote's SHA-256 has changed, or if a recorded form or translation does not appear in its footnote. Each S has the form, any printed variants as `FORM ver="alt"`, its translations, and the footnote text in the FORM's `notes`;
   - writes `ILCAA_KanakanavuTexts_intro_Asai2026.xml` (53 S) and `ILCAA_KanakanavuTexts_intro_Tsuchida1976.xml` (16 S) from [introduction_lexemes.json](CodeAndDocs/introduction_lexemes.json) via `scripts/introduction_lexemes.py`. It stops if any of the 11 listed pages' text has changed or a recorded reading is not on its page. The three records with the book's own analysis get one W with its M tier;
   - writes coverage and notation reports (`source_unit_coverage.csv`, `source_notation_audit.csv`) into the staging folder.
6. **Shared cleaning:** `QC/cleaning/clean_xml.py --corpora_path <staging>/build/xml_drafts`. Among other normalizations it writes square brackets as parentheses and every dash as `-` (the example-23 brackets and the em dash in Notes and caveats). Its warnings file lands in the staging folder and is not published.
7. **For each XML file, in turn:**
   - `QC/utilities/standardize.py --tsv_path Orthographies/ConversionTables/Kanakanavu_Asai2026_113.tsv --target_column standard --segmented-without-m-tier --corpora_path <file>` writes the standard FORMs. The table maps `ŋ`→`ng`, `l`→`r`, `r`→`r`, `ʔ`→`'`, `ə`→`e`. `--segmented-without-m-tier` removes the morpheme hyphens from the standard S FORM of the lexical records, which have no M tier (maintainer, 2026-10-18: the hyphens "should be deleted in the standard S FORM");
   - `scripts/strip_standard_brackets.py <file>` removes `<` and `>` from every sentence-level standard FORM, and also `(` and `)` from the standard FORMs of examples 23a-d (the `clause_brackets` rows of `notation_decisions.tsv`). Original FORMs are not touched;
   - `QC/utilities/add_phonology.py --orthography Orthographies/Asai2026 --corpora_path <file> --preserve-existing-original` writes PHON: original PHON from the `Asai2026` source profile, standard PHON from Ortho113. `--preserve-existing-original` keeps any original PHON already in the file.
8. **Provenance note.** It prints a note if the FormosanBank checkout's commit differs from the one in `CodeAndDocs/provenance.json`. It never reads that file to decide anything and never rewrites it.
9. **Install.** It deletes the existing `XML/Kanakanavu/*.xml` and copies in the 48 staged files.
