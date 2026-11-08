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

## Published corpora predate the current accent rule

**Symptom**: a `*` in a `PHON` tier where the `FORM` carries an accented vowel —
`é`/`ē` in Puyuma, `á é í ó` in Yami, `í` in Thao. The `*` is the pipeline's
"unmapped letter" marker, not a defect in the FORM.

**Cause, now fixed in the tooling**: the accent keep set used to be derived from
`QC/validation/reference/<Language>/*/unique_characters.txt`, which
`orthography_extract.py` generates from sample text and which lists every
character observed. An accent that merely appeared in the sample was therefore
treated as an orthographic letter, preserved — and then had no row in
`Orthographies/Ortho113/<Language>.tsv` to map through, so it starred. Since
2026-09-05 the keep set comes from the language's **designated standard
orthography** instead, so a kept letter is always a mappable one and folding can
no longer produce a `*`. See
[add_phonology.py](developers/qc-pipeline/add-phonology.md).

**Scope**: the code is fixed; the **published data is not**, because nothing was
regenerated when the rule changed. Regenerating a corpus clears its share:
**1,633 `PHON` elements change, 1,039 of them losing a `*`** — RauDong (Yami)
791, ePark (Puyuma) 758 of which 222 starred, Presidential_Apologies (Puyuma) 54,
ILRDF_Dicts (Thao) 14, ePark (Rukai) 12, MontgomeryTexts (Amis) 4. A further
**1,244 standard-tier FORMs** render differently once re-standardized, mostly the
same corpora.

**What to do**: nothing special — the next scheduled regeneration of each corpus
resolves it. Anyone rebuilding one of those corpora should expect that diff and
read it as the fix landing, not as a regression. Until then, a `*` on one of
those letters is known.
