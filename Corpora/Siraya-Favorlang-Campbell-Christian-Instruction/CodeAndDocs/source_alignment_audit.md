# Source Alignment Audit

## Verdict

- Errors: 0
- Warnings: 0
- Notices: 2

## Logical Extraction

- 1,049 records across 19 printed sections.
- 365 records carry Campbell's English translation.
- Fourteen Favorlang/English heading pairs are retained as title records.
- Article X's 80 numbered exchanges are emitted as 160 speaker turns.
- Boundary numbers and speaker labels are retained in provenance, not text.
- Five sermons are emitted as 684 hand-reviewed source-only sentence records.
- `sermon_review.tsv` applies Madeline Boese's 2026-08-12 hand corrections to every pre-review sermon unit with baseline and review-source hashes.
- Section XII's 11 question/answer pairs are emitted as 22 turns.
- Physical page continuations are joined before record emission.
- Sections X, XI, XIII, and XIV use numbered secondary boundaries; section XII uses question/answer labels.

| Record type | Count |
| --- | ---: |
| primary_section | 8 |
| section_title | 14 |
| section_preamble | 1 |
| numbered_item | 160 |
| dialogue_turn | 160 |
| qa_turn | 22 |
| sermon_sentence | 684 |

## Primary Source Files

| File | Role | SHA-256 | Status |
| --- | --- | --- | --- |
| `Private/source/archive-org/campbell_1896_articles_favorlang_formosan.pdf` | Internet Archive full source PDF | `62a1cc9f31d429fad19169c57699b6755d4d6b14cb9bfe395f4483fe67c13e15` | ok |
| `Private/source/archive-org/campbell_1896_articles_favorlang_formosan_djvu.txt` | Internet Archive plain OCR | `898ad01ff8578785b242b002c514d5d8eeb70d113f6c8454ae40f76017f291cb` | ok |
| `Private/source/archive-org/campbell_1896_articles_favorlang_formosan_djvu.xml` | Internet Archive word-coordinate OCR | `f4c1e78d28bf9b6e644b3d88b514959f9a6cfadf2e3841f6698c475db00d92d9` | ok |
| `Private/source/archive-org/campbell_1896_articles_favorlang_formosan_layout.txt` | Local pdftotext layout cache | `1c7bb858533e6fe280420d6b80bd057d1bc4c9c08667ffb3f5df3492ec156d31` | ok |

## Rendered-Page Checks

The following independent source locations were visually checked against rendered pages through 2026-07-27:

| Section | Printed page(s) | PDF object page(s) | Check |
| --- | --- | --- | --- |
| I | 1 | 33 | Lord's Prayer boundary and full diacritics |
| II | 2-3 | 34-35 | Christian Belief continuation and diacritics |
| III | 3-5 | 35-37 | preamble, ten numbered commandments, page join |
| IV-VII | 5, 7-9 | 37, 39-41 | Favorlang/English title pairs |
| VIII-IX | 11 | 43 | Favorlang/English title pairs |
| X | 12-32 | 44-64 | all 80 dialogue exchanges, speaker turns, and OCR details |
| XI-XIV | 33, 38, 41, 68 | 65, 70, 73, 100 | Favorlang/English title pairs |
| XV | 75-79 | 107-111 | first sermon start and page joins |
| XVII-XVIII | 86-91 | 118-123 | sermon boundary on printed page 91 |
| XIX | 98-101 | 130-133 | fifth-sermon start and closing text |

## Translation And Orthography Decisions

- English footer extraction is restricted to the detected footer on each physical page; Dutch and Favorlang body OCR are not accepted as English translation.
- Standalone footer letters are excluded.
- Digits and source punctuation are retained.
- Dutch is not emitted as an alternate translation: the available Fraktur OCR is not reliable enough for a source-faithful tier.
- `CodeAndDocs/diplomatic_diacritics.tsv` records 1951 source-backed diacritic restorations. Each entry is supported by multi-scale raster consensus, repeated-form corroboration, or a rendered source crop.
- `CodeAndDocs/source_checks.tsv` records 29 independent source-to-XML checks across the original and translation tiers, spanning printed pages 1-101.
- `CodeAndDocs/diacritic_review_queue.tsv` records 68 one-scale or conflicting candidates that were deliberately not applied without independent support.
- The edition's declared accent, macron-g, and comma-under-s orthography is preserved. The latest hand correction accepts one t-underdot occurrence in section II.

## Findings

- NOTICE: The 2026-08-06 hand correction supersedes the earlier t-underdot rejection and accepts one ṭ in section_02_christian_belief.
- NOTICE: The Campbell IA PDF is hash-distinct from both pinned Gravius source PDFs.
