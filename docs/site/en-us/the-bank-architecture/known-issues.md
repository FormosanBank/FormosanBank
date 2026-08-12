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
