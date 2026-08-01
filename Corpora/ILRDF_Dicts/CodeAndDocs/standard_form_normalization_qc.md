# Standard-form normalization QC

Baseline: FormosanBank `dc89d0899b92f1c884aa1b09d3e5d720201b5a71`.

`normalize_standard_forms.py` changed 4,130 direct sentence-level standard
forms while leaving all original forms, translations, PHON, AUDIO, attributes,
IDs, and document structure unchanged. A canonical XML comparison verified the
protected content across all 16 files.

## Change inventory

| Source pattern | Standards affected |
|---|---:|
| ASCII morpheme boundary `-` | 3,118 |
| Atayal infix placeholder `_` | 214 |
| Parenthetical alternative or annotation | 148 |
| Slash-ordered alternative | 32 |
| Inline Chinese editor note after parenthetical cleanup | 12 |
| Equals-ordered alternative | 2 |

Counts overlap when one standard contains more than one pattern. The output is
idempotent: a second dry run reports zero changes.

The residual direct-standard inventory is zero for ASCII dash, underscore,
slash, equals, plus, parentheses, angle brackets, CJK, asterisk, and zero-width
characters. Four tildes remain because they are source-backed sound or
hesitation notation rather than segmentation:

| File | S id | Decision |
|---|---|---|
| `Seediq/Seediq.xml` | `Seediq_1787` | Retain quoted `wing~` sound |
| `Truku/Truku.xml` | `Truku_435` | Retain hesitation/prosodic notation |
| `Truku/Truku.xml` | `Truku_757` | Retain hesitation/prosodic notation |
| `Truku/Truku.xml` | `Truku_2168` | Retain hesitation/prosodic notation |

## Validation

| Check | Result |
|---|---|
| Unit tests | 6 passed |
| Normalizer second dry run | 0 changes |
| XML validator | 16 files, no findings |
| Text validator | 0 HARD; V126 = 0; V133 = 0 |
| Gloss validator | No structural W/M analysis exists; V060 emits its known sentence-only soft findings |
| Dialect inventory | 16 files accounted for; unchanged from baseline |
| Duplicate sentences | 225 same-file groups after normalization, versus 197 at baseline |

The 28 new duplicate groups are expected collisions where distinct source
records reduce to the same first surface reading after analytical boundaries or
alternatives are removed. They retain distinct original text, translations,
IDs, and audio metadata, so no source record was deleted.

The text validator's remaining soft findings are outside direct standard-form
segmentation: V116 (56), V122 (9,270), V135 (45), and V137 (14). V122 is in
preserved original/translation text. V135 reflects the intentional difference
between an original ending in an annotation delimiter and its clean standard.
