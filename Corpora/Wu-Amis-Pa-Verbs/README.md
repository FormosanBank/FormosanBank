# The Analysis of Pa-Verbs in Amis

This corpus contains the Coastal Amis examples from Joy Wu's 2006 paper, “The
Analysis of Pa- Verbs in Amis.”

The Basecamp corpus card records the source license as **CC BY-NC-SA 4.0**. The
source PDF does not display that license statement. The corpus is also subject to
the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and
[AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md).

| Field | Value |
|---|---|
| Language | Amis (`ami`, dialect `Coastal`) |
| Source | [Wu, “The Analysis of Pa- Verbs in Amis”](https://www.sil.org/resources/archives/25653) |
| Source license | CC BY-NC-SA 4.0, as recorded on the corpus card |
| Scope | 29 accepted example variants |
| XML | [`XML/Amis/pa-verbs.xml`](XML/Amis/pa-verbs.xml) |
| Development repository | [Formosan-Amis-Pa-Verbs](https://github.com/FormosanBank/Formosan-Amis-Pa-Verbs) |

The corpus has 29 `S`, 153 `W`, and 262 `M` elements. Sentence-level original
forms are unsegmented. Word-level original forms preserve Wu's printed
segmentation, and printed nulls are retained as `ø` at W/M while omitted from S.

## Reproduce

`CodeAndDocs/` contains the hash-pinned source PDF, reviewed extraction tables,
recorded manual edits, deterministic builder, and source-alignment audit. The
reproduction pipeline builds in a temporary directory and does not modify the
published XML.

The shared phonology step requires a clean FormosanBank checkout at commit
`14442ea6894e6cff561c6504fbf42ddd873cd14b` from
[PR #90](https://github.com/FormosanBank/FormosanBank/pull/90). From this corpus
directory, run:

```bash
FORMOSANBANK_PATH=/path/to/FormosanBank \
    bash CodeAndDocs/scripts/reproduce.sh
```

The script reapplies `manual_edits.xml`, runs the shared cleaning,
standardization, and phonology utilities, checks source alignment and core XML
validators, and byte-compares the result with `XML/Amis/pa-verbs.xml`.

## Source decisions

- Madeline Boese's review is recorded as three sentence replacements, one
  insertion, and two deletions in `CodeAndDocs/manual_edits.xml`.
- Example 20c is split into the person and car readings supported by its printed
  gloss and translation. The person reading ends at `cingra`; `a paliding`
  belongs to the `k-u-ni` car reading.
- Both unstarred case forms of example 36a are retained. The starred reading is
  excluded.
- Starred examples and alternatives are excluded. The source-questionable
  38a-prime and 38c-prime readings are also excluded under review.
- `Pa-fli` keeps its printed W segmentation but has no M split because Wu gives
  only the whole-word gloss `give`.
- Nulls are silent in mixed PHON forms. A null-only morpheme retains `PHON ∅`.

## Citation

Wu, J. (2006). The analysis of pa- verbs in Amis. Paper presented at the Tenth
International Conference on Austronesian Linguistics, Puerto Princesa City,
Palawan, Philippines.
