# FormosanBank GitBook translations

This corpus contains translations of key FormosanBank GitBook pages into
Formosan languages. The long-term goal is to provide at least the most critical
pages in each Formosan language.

## Languages and dialects

Paiwan (ISO 639-3 `pwn`), Eastern dialect. All six files in `XML/Paiwan/`
declare `xml:lang="pwn"` and `dialect="Eastern"` on `<TEXT>`. The source was
supplied by Xuan; Eastern Paiwan was confirmed on 2025-02-24. Every sentence also
carries the source's Mandarin (`TRANSL xml:lang="zho"`) and English
(`TRANSL xml:lang="eng"`) text.

## Source

This corpus contains Xuan Ruan's Eastern Paiwan translation of the FormosanBank
manual, aligned with its English and Chinese text. Six sections contain 105
records. The source supplies no word/morpheme analysis or audio.

The current public corpus contains 105 aligned records from six GitBook sections
in Eastern Paiwan, generously contributed by Xuan Ruan. Each entry also retains
its English and Mandarin source text.

The source is [Website PWN-v1.2.pdf](CodeAndDocs/raw_data/Paiwan/Website%20PWN-v1.2.pdf),
nine pages with SHA256
`5f7b960a9105f46a3216de6220664334b7d32763e8fc95d1519daadb4b84dd84`.
This published print copy was checked against the original February 11, 2025
file; their extracted text matches after layout whitespace removal.
Joshua supplied the citation on 2025-02-25:

> Ruan, X. (2025). Paiwan translation of FormosanBank manual.

That citation was replaced on 2026-10-18 by one that lists every contributor
and carries a version (see "How to cite").

The source is a nine-page trilingual PDF rather than the GitBook pages it
mirrors, because only the PDF aligns Paiwan, Mandarin and English record by
record. Its Mandarin is a distinct translation, segmented to parallel the
English; the Mandarin edition of this site words the same content differently,
and has no counterpart page for one of the six sections.

All nine pages and their continuations were reviewed against the six preserved
three-column text ledgers. Each blank-line-separated record contains English,
Chinese, then Paiwan. The 315 fields match the PDF's corresponding columns in
source order after layout whitespace removal. Two English/Chinese headings have
no Paiwan counterpart and are excluded: the standalone title FormosanBank (p. 2),
and the heading What must you do? / 您必須做什麼？ (p. 8). Page 8 sets two
headings against a single Paiwan line, `kemuda itjen a pusaladj tua
FormosanBank?`, which is the Paiwan page title and is published as S 0 of
`Contributing_to_FormosanBank.xml`. Column labels, URLs, and page numbers are
layout metadata. Source headings with Paiwan text, names, language lists, and
both repeated bibliographic citations remain data.

| Section | Records | Source pages |
|---|---:|---|
| Welcome | 10 | 1-2 |
| FormosanBank | 29 | 2-4 |
| Formosan Languages | 16 | 4-6 |
| Contributors | 9 | 6-7 |
| Terms of Use | 13 | 7-8 |
| Contributing to FormosanBank | 28 | 8-9 |

The source URL, ledger hash, and count for each section are in
[CodeAndDocs/source_sections.tsv](CodeAndDocs/source_sections.tsv).
[CodeAndDocs/source_records.tsv](CodeAndDocs/source_records.tsv) maps each ledger
record to its published S ID and PDF pages. All 102 earlier S IDs still identify
the same passages. The three recovered source records have distinct IDs:
`p1_people`, `p5_languages`, and `p6_contributors`. A spelling correction does
not change an ID. Existing TEXT IDs and source metadata are retained.

This written source supplies no audio.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/FormosanBankGitBook_corpora_stats.csv` and appears on this corpus's
page on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

* Ruan, X. (2025). Translations of the FormosanBank documentation v1.

BibTeX:

```
@misc{formosanbank_doc_translations, author={Ruan, Xuan}, title={Translations of the FormosanBank documentation v1}, year={2025}}
```

The citation lists every contributor in alphabetical order and carries a
version, so it changes over time as translations collected on the documentation
site are added (maintainer, 2026-10-18: "it should list all contributors in
alphabetical order. Title is just 'Translations of the FormosanBank
documentation vX' going forward. For now, Xuan Ruan is the only author and it
is v1. BibTex will need to be updated as well. This does mean the citation
changes over time, but that's OK."). The build computes it
(`CodeAndDocs/citation.py`) from `CodeAndDocs/contributors.tsv` and the
translation store, and writes it into every file's `citation` and
`BibTeX_citation`; the version is 1 plus the number of dates on which approved
translations were added. Until 2026-10-18 the citation was
"Ruan, X. (2025). Paiwan translation of FormosanBank manual."

## License

**License:** CC BY-NC 4.0

**Rights source:** Xuan Ruan, 2025-02-11; evidence: ask maintainer

The project recorded Xuan's permission on that date. The source PDF and
translations are already published with this corpus. The exact vocabulary
spelling above preserves the existing CC-BY-NC claim; its change requires
maintainer review at merge (POL-042/043/044). The central
[LICENSE.md](https://github.com/FormosanBank/FormosanBank/blob/main/LICENSE.md)
and [AI-USE-ADDENDUM.md](https://github.com/FormosanBank/FormosanBank/blob/main/AI-USE-ADDENDUM.md)
also apply; commercial AI use requires prior written permission. Historical
licensing prose inside the translated manual is source content, not a
replacement for this rights statement.

CC BY-NC 4.0. Xuan Ruan's permission was recorded on 2025-02-11. The corpus
README records the rights statement (the two lines above); FormosanBank's
[Terms of Use](https://formosanbank.github.io/FormosanBank/additional-resources/terms-of-use/)
also apply, including the commercial AI restriction. Historical licensing text
inside the translated manual does not replace the corpus rights statement.

## Notes and caveats

#### Translations collected on the documentation site

Translators can now translate the documentation on the site's translation
pages (Paiwan, Amis and Bunun, plus Mandarin for the site itself). Approved
Formosan translations become files of this corpus under
`XML/<Language>/doc_translations/`, one per translator, dialect and date of
import, with the English sentence and, when one is approved, the Mandarin
translation of the same English sentence attached. Older translations are never
removed: when the documentation changes, translations of the old wording stay
as data. Some attached Mandarin translations began as machine translation and
were approved by a person; the table counts them per file.

<!-- SITE TRANSLATION COUNTS START (written by CodeAndDocs/build_translations.py) -->
No translations collected through the site's translation pages yet. When there are, each file is listed here with its sentence count and how many of its attached Mandarin translations began as machine translation and were then approved by a person.
<!-- SITE TRANSLATION COUNTS END -->

#### Notes on the 2025 translation

These translations preserve historical manual text. Use current
[POLICIES.md](../../POLICIES.md) and the committed English GitBook documentation
for project guidance. Records include headings and lists as well as prose. The
manual reflects its 2025 source, including historical licence wording. Source
names, language lists, repeated citations, and the literal English/Chinese
licence-link labels remain part of the corpus. Names, English/Chinese
code-switching and licence-link labels are retained; generated PHON may contain
uncertainty stars for unsupported borrowed letters, including where it is
applied to non-Paiwan names.

Two records carry known defects, left in place rather than corrected: in the
Welcome roster the group heading `Advisory Board` sits inline among the personal
names, because the source sets the two lists in one column; and the
language-list record's Mandarin tier reproduces the source's untranslated Latin
list rather than Mandarin. In detail:

- `Welcome` S `p1_people` runs the roster as one line, so the group heading
  `Advisory Board` sits inline among the personal names. The source sets the
  Principal Investigators and Advisory Board lists in one column.
- `Formosan_Languages` S `p5_languages` has a `TRANSL xml:lang="zho"` holding
  the source's untranslated Latin language list rather than Mandarin. The
  source document's Mandarin translator left that list in Latin; the Mandarin
  edition of the FormosanBank manual does translate the names.

Records that are lists of names count toward this corpus's word totals.

#### Orthography and source notation

The source uses Eastern Paiwan spelling compatible with the registered
Ortho113 Paiwan profile. Original FORM preserves that spelling; shared cleaning
normalizes typography. Standard FORM uses the current `--remove_accents` mode,
including accent folding in borrowed names. The earlier global u-to-o transform
is obsolete: it corrupted the English loan `open-source` to `open-soorce`.
Joshua's correction remains preserved by the current shared pipeline.

`(amilikan|ciniukukan)` on page 8 names the English/Chinese licence links. It is
literal metalinguistic content, not optional utterance material. Retain it and
its translations without creating extra sentences. `pu’ui` on page 9 has a
word-internal apostrophe, normalized to `pu'ui`; it is not quotation furniture.
Names, Chinese code-switching, parenthesized language labels, numbers, and
source punctuation remain intact even where validators flag them. PHON uses
Ortho113 for both tiers; unmapped loan characters may yield uncertainty stars.

## Reproduction and processing

### How to reproduce

From the FormosanBank repository root:

```bash
bash Corpora/FormosanBankGitBook/CodeAndDocs/generate_xml.sh
```

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

XML is regenerable from the committed reviewed ledgers. The original PDF,
ledgers, stable-key tables, parser, and checks live in `CodeAndDocs/`; generated
output lives only in `XML/Paiwan/`. No private input, network source refresh, or
old Git object is required. The public package retains that PDF, the reviewed
ledgers, stable source keys, parser, source audit, and focused tests. Two builds
reproduced all six XML files from the public inputs alone.

Run `./CodeAndDocs/generate_xml.sh` from the corpus directory using the current
FormosanBank environment. Use the current FormosanBank environment, then run
from the corpus root:

```bash
FORMOSANBANK_ROOT=/path/to/FormosanBank PYTHON=/path/to/python3 \
  ./CodeAndDocs/generate_xml.sh
```

Inside a published FormosanBank checkout the root is detected from the corpus
layout. It generates source tiers from the reviewed Paiwan, Mandarin, and
English ledgers, then runs shared cleaning, standardization with
`--remove_accents`, and Ortho113 phonology. The build always starts with
source-tier generation, then runs shared cleaning, standardization with
`--remove_accents`, and phonology with `--orthography Ortho113`. There are no
manual edits or pipeline deviations. Source text is never restored over the
cleaner's output. Build provenance is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json); update it after
rebuilding with different shared tools. It is informational and cannot select
or reject a tools checkout. The corpus README gives reproduction and validation
commands here; [build provenance](CodeAndDocs/provenance.json) records the
shared tools used.

#### Validation

Validation and source review are separate from generation. Validation is
separate:

```bash
FORMOSANBANK_ROOT=/path/to/FormosanBank PYTHON=/path/to/python3 \
  OUTPUT_DIR=/new/path/outside/the/corpus ./CodeAndDocs/validate.sh
```

Use the shared requirements, including pdfplumber for the read-only source
check. That check confirms PDF/ledger identity, ordered field coverage, stable
IDs, and cleaned source-tier consistency. All 315 source fields were checked in
their original column order. The three recovered lists have new IDs; all 102
earlier sentence IDs still identify the same source passages. Focused tests
protect page continuations, source notation, published associations, and
malformed input. Review the generated XML against the source and prior
corrections as well as all validator reports; matching hashes and passing
checks do not prove every linguistic interpretation. Cleaner/standardizer
warning files are per-run reports to review outside version control. Preserve
any durable `quote_corrections.csv` if produced.

`validate.sh` refuses to run unless `OUTPUT_DIR` is a new absolute path outside
the corpus. It writes every report there: it builds a view of the other
published corpora (for cross-corpus checks), then runs, each into its own log,
`CodeAndDocs/source_audit.py`, the unit tests in `CodeAndDocs/tests/`,
`validate_xml.py`, `validate_text.py`, `validate_duplicate_sentences.py` and
`orthography_extract.py` + `validate_orthography.py` for both the original and
standard tiers, `validate_vocabulary.py` (standard tier), `validate_dialect.py`,
`validate_registries.py` and `validate_port_readiness.py`. It exits 1 if any of
them failed. Gloss, conversion-table and audio checks are not run, because the
source supplies no W/M tiers or audio.

### What each step does

`CodeAndDocs/generate_xml.sh` runs these steps in order and stops at the first
failure (`set -euo pipefail`). It takes the FormosanBank root from
`FORMOSANBANK_ROOT`, or else three folders above `CodeAndDocs/`, and the Python
interpreter from `PYTHON` (default `python3`). It first checks that
`QC/cleaning/clean_xml.py` exists under that root.

1. **`CodeAndDocs/process_raw.py`** (also computes the citation and BibTeX
   with `CodeAndDocs/citation.py`; see "How to cite") (no flags; defaults `--source-dir
   CodeAndDocs/raw_data/Paiwan`, `--output XML/Paiwan`). Reads the section list
   from `CodeAndDocs/source_sections.tsv` and requires exactly one ledger
   `<section>.txt` per listed section in `raw_data/Paiwan/` (any missing or extra
   `.txt` file is an error). It does not read the PDF. Each ledger is split at
   blank lines; every block must be exactly three non-empty lines, read as
   English, Chinese, Paiwan. Sentence IDs come from
   `CodeAndDocs/source_records.tsv`, whose rows for a section must number the
   records 0, 1, 2, ... in order with no duplicate ID; otherwise the build fails
   rather than renumbering. It refuses to run if `XML/Paiwan/` holds an `.xml`
   file that no ledger produces. It then writes (overwriting) one
   `XML/Paiwan/<section>.xml` per section: `<TEXT>` with `id="gitbook_Paiwan_<section>"`,
   `xml:lang="pwn"`, `dialect="Eastern"`, `source="translation of FormosanBank
   gitbook in Paiwan"`, `copyright="CC BY-NC 4.0"`, and the citation and BibTeX
   citation; and per record one `<S>` holding `FORM kindOf="original"` (the
   Paiwan line), `TRANSL xml:lang="zho"` (the Chinese line) and
   `TRANSL xml:lang="eng"` (the English line). No W, M, PHON, standard FORM or
   AUDIO is written at this step. The `source_url` and `sha256` columns of
   `source_sections.tsv` are not used here (`source_audit.py` checks the hashes).
1b. **`CodeAndDocs/build_translations.py`** (no flags). Reads the approved rows
   of FormosanBank's `docs/translations/pwn.tsv`, `ami.tsv` and `bnn.tsv` and
   writes one TEXT per translator, dialect and import date under
   `XML/<Language>/doc_translations/` (original FORM = the translation;
   TRANSL eng = the English sentence; TRANSL zho = the approved Mandarin of the
   same English sentence from `zho.tsv`, if any), then rewrites the counts table
   under "Notes and caveats". With no approved rows it writes no XML. A
   translator missing from `CodeAndDocs/contributors.tsv` stops the build.
2. **`QC/cleaning/clean_xml.py --corpora_path XML --warnings_dir CodeAndDocs`**
   (shared). Edits the XML in place: replaces non-breaking spaces; in FORM text
   strips zero-width characters, decodes leftover HTML entities, maps caret-like
   characters to `^`, converts full-width and typographic punctuation to ASCII,
   normalizes null-morpheme signs, collapses whitespace and trims repeated
   punctuation; TRANSL text gets the same treatment, with language-aware quote
   handling for Mandarin. Its per-run report `cleaner_warnings.csv` goes to
   `CodeAndDocs/` (gitignored there); any original-tier quote rewrites are
   logged durably in `CodeAndDocs/quote_corrections.csv`.
3. **`QC/utilities/standardize.py --corpora_path XML --remove_accents`**
   (shared). For every element with a FORM, copies the original FORM to a new
   `FORM kindOf="standard"`, removes null-morpheme units from the sentence-level
   standard FORM, and strips accents, keeping any accented letters the Paiwan
   reference orthography attests. No conversion table is applied, so letters
   are not changed. Its per-run report is `XML/standardize_warnings.csv`.
4. **`QC/utilities/add_phonology.py --corpora_path XML --orthography Ortho113`**
   (shared). Writes `PHON kindOf="original"` from the original FORM and
   `PHON kindOf="standard"` from the standard FORM, both with
   `Orthographies/Ortho113/Paiwan.tsv` (its `Eastern` column, chosen from the
   `dialect` attribute; Ortho113 is Paiwan's standard orthography in
   `standards.csv`). Unmapped punctuation is dropped from PHON; any other
   unmapped character becomes `*`, which is where the uncertainty stars in
   borrowed names come from (for example `FormosanBank` becomes
   `*urmusanbank`).
