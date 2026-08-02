# Standard-form repair QC

Baseline: FormosanBank `dc89d0899b92f1c884aa1b09d3e5d720201b5a71`.

The first version of this change removed every hyphen and underscore. That was
not correct. Hyphens have mixed uses in this dictionary corpus, including
proper names such as `Tai-uan` and `Ma-Ing-Cyo`, punctuation, morphology, and
Bunun/Thao notation. Underscores encode Atayal schwa. The corrected normalizer
retains both.

The corrected script changes 193 direct sentence-level standards while leaving
all originals, translations, PHON, AUDIO, attributes, IDs, and structure
unchanged. A canonical comparison verified the protected content across all 16
files.

## Change inventory

| Reviewed source pattern | Standards affected |
|---|---:|
| Parenthetical alternative or annotation | 146 |
| Slash-ordered alternative | 32 |
| Exact source repair | 13 |
| Equals-ordered alternative | 2 |

The 13 exact repairs include six Saaroa extraction failures, six unambiguous
trailing Chinese editor notes, and the Sakizaya `101` building number. The
Saaroa repairs are supported by dictionary headwords or a duplicate clean
sentence. For example:

| Corrupt standard | Repaired standard | Evidence |
|---|---|---|
| `u數詞u paapuhla...` | `ʉnʉmʉ paapuhla...` | Dictionary numeral headword `ʉnʉmʉ` |
| `muasala isiparu tu數詞u...` | `muasala 'isiparʉtʉnʉmʉ...` | Exact clean duplicate in Saaroa S 92 |
| `kapita數詞ia` | `kapitanʉia` | Dictionary headword `kapitanʉ` |
| `luma' (101)` | `luma' 101` | Translation identifies the 101 building |

## Retained notation

| Notation | Direct standards retained | Decision |
|---|---:|---|
| ASCII hyphen | 3,118 | Mixed orthographic, name, punctuation, and morphology uses require review |
| Underscore | 214 | Retain Atayal schwa notation |

The remaining validator markers are therefore an inventory for review, not
evidence that 3,118 sentences are mechanically segmentable.

## Verification

| Check | Result |
|---|---|
| Unit tests | 9 passed |
| Normalizer second dry run | 0 changes |
| XML validator | 16 files, no findings |
| Text validator | 0 HARD findings |
| Protected-content comparison | No unexpected differences across 16 files |

The text validator reports soft V133 findings for the retained hyphens. It also
reports source notation in protected originals and translations. No validator
HARD finding remains.
