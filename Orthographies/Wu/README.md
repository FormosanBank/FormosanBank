# Wu — Joy Wu's Amis orthography

The spelling system Joy Wu uses for Coastal (Haian) Amis, as keyed in her
2006 Buffalo dissertation, printed page xviii. Registered here because
`Corpora/Amis-Pa-Verbs` (Wu 2006, ICAL 10) builds its `original` PHON tier
from it and converts to Ortho113 through
[`../ConversionTables/Amis_Wu_113.tsv`](../ConversionTables/Amis_Wu_113.tsv).

## What distinguishes it

Wu's system is **Ortho94 Coastal with two deliberate changes**, both keyed in
the dissertation:

| letter | Wu | Ortho94 Coastal | note |
| --- | --- | --- | --- |
| `'` | `ʔ` | `ʡ` | Wu's apostrophe is the **glottal** stop |
| `q` | `ʡ` | *(absent)* | Wu spells the **epiglottal** stop `q` |

Every other cell matches Ortho94's Coastal column. That is the whole
difference: one reassigned value and one added letter.

The distinction matters because reading Wu's apostrophe as Ortho94 does —
`ʡ` — puts the wrong phoneme in the published PHON tier. Dissertation example
5.27a (printed p. 313) repeats the ICAL paper's example 36a verbatim,
including `Ma-na'ay`, which is what ties the dissertation's key to the paper's
text. Dissertation p. 4 identifies the same Haian/Coastal Changpin variety as
the paper's p. 1.

## Conversion to Ortho113

`Amis_Wu_113.tsv` carries three rules:

| rule | evidence |
| --- | --- |
| `u` → `o` | Ortho113 Coastal writes one `o` for /o~u/; Wu's source `u`/`o` stay distinct in the `original` PHON tier |
| `'` → `^` | Wu's apostrophe is /ʔ/, which Ortho113 Amis writes `^` |
| `q` → `'` | Wu's `q` is /ʡ/, which Ortho113 Amis writes `'` |

The last two are identical to
[`../ConversionTables/Amis_MinEd_113.tsv`](../ConversionTables/Amis_MinEd_113.tsv),
which makes the same two reassignments; `u` → `o` is the addition.

`validate_conversion_table.py` rates `'` → `^` and `q` → `'` as **confirmed
equivalences** and reports `u` → `o` as an unresolved mismatch (source `u`
against target `[o|u]`). That mismatch is a phoneme-class widening, not a
malformed rule: Ortho113 Coastal genuinely merges /o/ and /u/ under `o`, so
the `standard` tier loses a distinction the `original` tier keeps. Expected,
and reviewed.

**No `q` and no uppercase `U` occurs in the published corpus today**, so the
last rule is currently inert and capital-letter derivation has nothing to act
on. Both are registered so that a later text using them converts correctly.

## Why it is not an existing scheme

`orthography_detector.py` on the corpus's `original` tier ranks **Ortho94
Coastal first at 72.83%**, with no orthography scoring near an exact fit:

```
Best Match: Amis (Coastal) - Ortho94   72.83%
Missing Letters: ^, x
Unexpected Tokens: .(16), -(7), ∅(7)
```

The unexpected tokens are all punctuation and null-morpheme notation (POL-012),
not letters, and the missing letters are Ortho94 letters the text simply does
not use — so the corpus's **letter inventory is Ortho94 Coastal exactly**.

That is the limit of what the detector can settle. It compares letters in the
text against a table's letter column, and Wu's sole departure from Ortho94 is
the *phonetic value* of `'`, which lives in the IPA column and never appears
in the text. **The detector therefore cannot distinguish Wu from Ortho94**, and
the case for a separate scheme rests on the dissertation key, not on detection.

For contrast, the same detector on the `standard` tier ranks Ortho113 Coastal
first at 82.41%, up from 29.21% on the `original` tier — independent
confirmation that the conversion lands where it should.
