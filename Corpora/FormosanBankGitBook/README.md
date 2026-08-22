# FormosanBank GitBook Translations

Eastern Paiwan translations of six sections of the FormosanBank GitBook,
contributed and authorized for publication by Xuan Ruan.

## Corpus At A Glance

| Field | Value |
| --- | --- |
| Language | Paiwan (`pwn`) |
| Dialect | Eastern |
| Source | Six FormosanBank GitBook sections aligned in a nine-page translation PDF |
| Size | 6 XML files, 105 sentence records, 210 translations |
| Copyright | CC-BY-NC |
| Citation | Ruan, X. (2025). *Paiwan translation of FormosanBank manual*. |
| Tiers | Paiwan original and standard `FORM`; original and standard `PHON`; English and Chinese `TRANSL` |

This corpus is also subject to the central FormosanBank terms in
[LICENSE.md](../../LICENSE.md) and
[AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI use is
prohibited without prior written permission.

## Source And Scope

The reviewed source is
`CodeAndDocs/raw_data/Paiwan/Website PWN-v1.2.pdf`. Its SHA-256 is
`5f7b960a9105f46a3216de6220664334b7d32763e8fc95d1519daadb4b84dd84`.
The six three-column text ledgers in the same directory preserve 105 aligned
English, Chinese, and Paiwan records from all nine pages. Two English and
Chinese headings are omitted because the source gives them no distinct Paiwan
counterpart.

Each XML root links to the corresponding source section in the FormosanBank
GitBook. The source-attested `(amilikan|ciniukukan)` string names the English
and Chinese licensing choices in a metalinguistic example. It is not an
unresolved annotation.

## Tiers

Each sentence contains the source Paiwan text as `FORM kindOf="original"`,
plus source English and Chinese translations. The standard form is copied from
the original under the current Ortho113 policy. Curly quotation marks are
normalized to ASCII in `FORM` tiers to satisfy the canonical XML policy.
Original and standard `PHON` tiers are derived with the Ortho113 Paiwan
profile. The source contains no word, morpheme, or audio alignment.

## Reproduce And Validate

The reviewed ledgers are the generator inputs. The source audit pins their
hashes and verifies every emitted source-owned tier. From the FormosanBank
repository root, run:

```bash
(cd Corpora/FormosanBankGitBook/CodeAndDocs && \
  python -m unittest discover -s tests)
ruff check \
  Corpora/FormosanBankGitBook/CodeAndDocs/process_raw.py \
  Corpora/FormosanBankGitBook/CodeAndDocs/source_audit.py \
  Corpora/FormosanBankGitBook/CodeAndDocs/tests
./Corpora/FormosanBankGitBook/CodeAndDocs/make_xml.sh
```

`make_xml.sh` generates into a temporary directory, runs cleaning, restores
the source-owned tiers, copies the standard form, derives phonology, runs the
current XML, text, and gloss validators, and compares all six files with the
published XML byte-for-byte.

## QC Notes

- Source audit: 105 of 105 included records aligned across all six ledgers.
- Structural XML validation: 0 findings.
- Text audit: 107 SOFT findings for source-attested punctuation, names, lists,
  and hyphens; 0 HARD findings.
- Gloss audit: 105 expected V060 SOFT findings because the source does not
  contain word or morpheme segmentation; 0 HARD findings.
- Port readiness: 0 HARD and 0 WARN.
