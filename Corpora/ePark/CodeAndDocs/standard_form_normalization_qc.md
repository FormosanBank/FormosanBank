# Standard-form repair QC

Baseline: FormosanBank `dc89d0899b92f1c884aa1b09d3e5d720201b5a71`.

The first version of this change treated every hyphen, underscore, slash,
parenthetical, and CJK string as removable analysis. A source-level audit found
that assumption was false. It joined separate words, deleted orthographic
characters, removed code-switched content, and damaged quoted alternatives.

The corrected `normalize_standard_forms.py` changes 16 direct sentence-level
standard forms: nine reviewed grammar templates and seven Puyuma en-dash word
boundaries. The Puyuma boundaries become spaces, not joins. One additional
standard changes with its original through the declared technical asterisk
repair, for 17 changed standards in the XML diff. The script also excludes 18
declared rows that do not contain a Formosan utterance and removes one declared
zero-width character.

## Reviewed changes

| Change | Standards affected | Decision |
|---|---:|---|
| Grammar templates with a recorded primary form | 9 | Use the reviewed recorded surface |
| Puyuma internal en dash | 7 | Replace with a word space |
| Technical asterisk | 1 standard and its original | Remove the metalinguistic artifact |
| Non-surface records | 18 records | Exclude by file and ID |
| Zero-width character | 1 translation | Remove the invisible artifact |

Examples of boundaries that the corrected script deliberately does not join:

| Source standard | Corrected decision | Evidence |
|---|---|---|
| `Tama-Alang` | Retain | The corpus also has `Tama Alang`; `TamaAlang` is unattested |
| `tian-sii` | Retain | Thao uses hyphens in loanword transliteration |
| `n_gyut`, `m_yan` | Retain | `_` represents Atayal schwa in `Orthographies/Ortho113/Atayal.tsv` |
| `na palribak–a trakubakuban` | `na palribak a trakubakuban` | The dash separates the particle `a` from the preceding word |

## Retained notation

These are sentence counts, not a claim that every occurrence is clean. They
remain because a marker-only rule cannot distinguish notation from content:

| Notation | Direct standards retained |
|---|---:|
| ASCII hyphen | 5,482 |
| Slash | 6,390 |
| Parenthesis | 1,481 |
| CJK | 203 |
| Underscore | 161 |

Examples include numeric dates such as `2013/05/23`, spoken lexical lists,
addresses, dialogue, code-switched Chinese nouns, Thao loanwords, and Atayal
schwa notation. These need source-specific review if the project later requires
one alternative per MT row. They are not safely removable segmentation residue.
The 25 retained non-ASCII dash rows are recorded in
`standard_form_unicode_dash_allowlist.tsv` with their reviewed uses.

## Verification

| Check | Result |
|---|---|
| Unit tests | 12 passed |
| Normalizer second dry run | 0 changes |
| XML validator | 436 files, no findings |
| Text validator | 0 HARD findings |
| Protected-content comparison | No unexpected differences across 436 files |

The text validator still reports soft marker inventories, including V133 for
the 5,482 retained hyphenated standards. That rule is a review signal. It does
not establish that each hyphen is a morpheme boundary.
