# FormosanBank GitBook translations

This corpus contains Xuan Ruan's Eastern Paiwan translation of the FormosanBank
manual, aligned with its English and Chinese text. Six sections contain 105
records. The source supplies no word/morpheme analysis or audio.

## Rights

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

## Source and coverage

The source is [Website PWN-v1.2.pdf](CodeAndDocs/raw_data/Paiwan/Website%20PWN-v1.2.pdf),
nine pages with SHA256
`5f7b960a9105f46a3216de6220664334b7d32763e8fc95d1519daadb4b84dd84`.
This published print copy was checked against the original February 11, 2025
file; their extracted text matches after layout whitespace removal.
The source was supplied by Xuan; Eastern Paiwan was confirmed on 2025-02-24.
Joshua supplied the citation on 2025-02-25:

> Ruan, X. (2025). Paiwan translation of FormosanBank manual.

All nine pages and their continuations were reviewed against the six preserved
three-column text ledgers. Each blank-line-separated record contains English,
Chinese, then Paiwan. The 315 fields match the PDF's corresponding columns in
source order after layout whitespace removal. Two standalone titles have no
separate Paiwan counterpart and are excluded: FormosanBank (p. 2) and
Contributing to FormosanBank (p. 8). Column labels, URLs, and page numbers are
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

## Orthography and source notation

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

## Audio

This written source supplies no audio.

## Notes and Issues

Records include headings and lists as well as prose. The manual reflects its
2025 source, including historical licence wording. Names, English/Chinese
code-switching and licence-link labels are retained; generated PHON may contain
uncertainty stars for unsupported borrowed letters.

## Reproduce

XML is regenerable from the committed reviewed ledgers. The original PDF,
ledgers, stable-key tables, parser, and checks live in `CodeAndDocs/`; generated
output lives only in `XML/Paiwan/`. No private input, network source refresh, or
old Git object is required.

Use the current FormosanBank environment, then run from the corpus root:

```bash
FORMOSANBANK_ROOT=/path/to/FormosanBank PYTHON=/path/to/python3 \
  ./CodeAndDocs/generate_xml.sh
```

Inside a published FormosanBank checkout the root is detected from the corpus
layout. The build always starts with source-tier generation, then runs shared
cleaning, standardization with `--remove_accents`, and phonology with
`--orthography Ortho113`. There are no manual edits or pipeline deviations.
Source text is never restored over the cleaner's output. Build provenance is
recorded in [CodeAndDocs/provenance.json](CodeAndDocs/provenance.json); update it
after rebuilding with different shared tools. It is informational and cannot
select or reject a tools checkout.

Validation is separate:

```bash
FORMOSANBANK_ROOT=/path/to/FormosanBank PYTHON=/path/to/python3 \
  OUTPUT_DIR=/new/path/outside/the/corpus ./CodeAndDocs/validate.sh
```

Use the shared requirements, including pdfplumber for the read-only source
check. That check confirms PDF/ledger identity, ordered field coverage, stable
IDs, and cleaned source-tier consistency. Focused tests protect page
continuations, source notation, published associations, and malformed input.
Review the generated XML against the source and prior corrections as well as
all validator reports; matching hashes and passing checks do not prove every
linguistic interpretation. Cleaner/standardizer warning files are per-run
reports to review outside version control. Preserve any durable
`quote_corrections.csv` if produced.
