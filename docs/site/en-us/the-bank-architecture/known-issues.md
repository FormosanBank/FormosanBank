# Known Issues

Corpus-wide limitations of the current processing pipeline that ought to be
addressed someday. These are documented here rather than fixed piecemeal
because a correct fix needs design work; per-corpus workarounds would make
the data less consistent, not more.

If you spot an issue in the data that isn't listed here, please report it
to the FormosanBank maintainers.

## Segmentation hyphens are removed before phoneme conversion

**Symptom**: when a morpheme boundary in the source falls between two
letters that also form a digraph, the generated IPA merges them. Example:
a word written `n-g…` (morpheme-final *n* followed by morpheme-initial
*g*) loses its hyphen before orthography→IPA conversion, so the converter
sees `ng` and emits the single phoneme *ŋ* instead of *n* + *g*.

**Scope**: any corpus whose text marks morpheme boundaries with `-` and
whose orthography has multi-letter graphemes (`ng`, `tj`, `lj`, …).

**Why there is no quick fix**: for word (`W`) elements the pipeline could
run phoneme conversion *before* suppressing segmentation markers, since
the markers are still present at that stage. But sentence-level (`S`)
FORMs have already lost segmentation by the time IPA is generated, and a
blanket rule (e.g. "always treat `n-g` as `n`+`g`") would be wrong for
the majority of texts, which are not morpheme-segmented at all — there a
hyphen-free `ng` really is the digraph. A real fix must thread
segmentation information through to phonology generation where it exists,
and accept the ambiguity where it doesn't.

## Attested accented letters have no phoneme mapping

**Symptom**: a `*` in a `PHON` tier wherever a `FORM` carries `é` or `ē`
(Puyuma), `á é í ó` (Yami), or `í` (Thao). The `*` is the pipeline's
"unmapped letter" marker, not a data error in the FORM.

**Cause**: two correct rules meeting a gap between them. Those letters appear in
the languages' reference character inventories
(`QC/validation/reference/<Language>/<dialect>/unique_characters.txt`), so
[`standardize.py`](developers/qc-pipeline/standardize.md) and
[`add_phonology.py`](developers/qc-pipeline/add-phonology.md) both decline to
fold their diacritics away — folding would merge two distinct letters. But
`Orthographies/Ortho113/<Language>.tsv` has no row for any of them, so
`add_phonology` reaches them as unmapped letters and writes `*`.

**Scope**: 2,076 `PHON` elements as published — RauDong (Yami) 1,098, ePark
(Puyuma) 910, Presidential_Apologies (Puyuma) 54, Li-Conjunction-Thao (Thao)
20, ILRDF_Dicts (Thao) 14.

**Expect this to grow before it shrinks.** RauDong and Li-Conjunction-Thao
currently star only on the *original* tier: their published standard tiers were
built by a `standardize.py` run predating the 2026-09-04 keep-set fix, which
stripped those letters unconditionally. **Regenerating either corpus restores
the letters to its standard tier** — correct in itself — and the standard `PHON`
will then star too. RauDong's count roughly doubles at that point. Anyone
regenerating those two corpora should expect that diff and not treat it as a
regression.

**Why there is no quick fix**: adding a row per letter to the orthography tables
is the mechanical part; deciding *what phoneme each maps to* is a linguistic
judgement per language.

There is also a prior question about the evidence. Those `unique_characters.txt`
files are **generated** by `orthography_extract.py` from reference text — they
list every character observed, which is why they also contain digits,
punctuation and, for Puyuma, `–`, `…` and `！`. So "appears in the inventory"
means *this character occurs in the reference material*, not *this language's
orthography designates it a letter*. The keep-set rule cannot tell those two
apart. For Puyuma's `ē` the distinction is probably immaterial; for Yami's
`á é í ó` it may not be, since `QC/utilities/_accents.py` cites Yami
`máduk`/`dálix` as its own example of stress marking that *should* be folded.

Rukai is the case already done right: its `é` is both in the inventory and
mapped in `Orthographies/Ortho113/Rukai.tsv`, so it transcribes cleanly.
