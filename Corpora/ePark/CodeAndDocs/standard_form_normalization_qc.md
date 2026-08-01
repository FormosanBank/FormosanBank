# Standard-form normalization QC

Baseline: FormosanBank `dc89d0899b92f1c884aa1b09d3e5d720201b5a71`.

`normalize_standard_forms.py` changed 13,961 direct sentence-level standard
forms. It also excluded 23 records that contain only instructions,
bibliographic notes, or an explicit “no word” sentinel, not a Formosan
utterance. Nine grammar-template records were surface-resolved from their
source-ordered primary form and paired recording.

A canonical comparison across all 436 XML files verified that original forms,
translations, PHON, W tiers, AUDIO, attributes, IDs, and structure are
unchanged, except for the 23 declared exclusions and three declared technical
text edits: the same metalinguistic asterisk in one original/standard pair and
one invisible BOM in a W translation.

## Change inventory

| Source pattern | Standards affected |
|---|---:|
| Slash-ordered alternative | 6,371 |
| ASCII morpheme boundary `-` | 5,450 |
| Parenthetical alternative or annotation | 1,462 |
| Infix placeholder `_` | 160 |
| Inline Chinese teaching note after parenthetical cleanup | 83 |
| Grammar template `+` | 9 |
| Unmatched source parenthesis | 8 |
| Internal Puyuma en-dash boundary | 7 |

Counts overlap when one standard contains more than one pattern. Eleven fully
parenthesized Saisiyat song lines were unwrapped and retained. The output is
idempotent: a second dry run reports zero changes.

The residual direct-standard inventory is zero for ASCII dash, underscore,
slash, equals, plus, parentheses, angle brackets, CJK, asterisk, and zero-width
characters. The remaining 170 tildes are source-backed elongation, sound, or
prosodic notation. The 25 non-ASCII dashes are individually identified in
`standard_form_unicode_dash_allowlist.tsv`; they are prose or sound punctuation,
not morpheme boundaries.

## Validation

| Check | Baseline | Normalized |
|---|---:|---:|
| Unit tests | n/a | 8 passed |
| Normalizer second dry run | n/a | 0 changes |
| XML HARD findings | 0 | 0 |
| Text HARD findings | 3 | 0 |
| V129 asterisk | 2 | 0 |
| V131 zero-width/BOM | 1 | 0 |
| V133 ASCII dash in S-standard | 5,482 | 0 |
| V141 W-to-S reconstruction | 2 | 2 |
| Same-file duplicate groups | 2,513 | 2,517 |
| Cross-file duplicate groups | 29,595 | 29,578 |

The two V141 findings are unchanged and compare original-tier S/W text, so this
standards-only repair cannot alter them without changing protected source
analysis. Current V122 supersedes the issue's older V121 label; its remaining
41,569 soft findings occur in preserved original, W, or translation content,
not direct S-standard forms. V135's 330 new soft findings
are expected where a standard drops an original annotation delimiter.

The four new same-file duplicate groups are expected collisions after choosing
the same first surface variant. Cross-file duplicate groups decrease by 17.
The source originals and record metadata remain available for every retained
sentence.
