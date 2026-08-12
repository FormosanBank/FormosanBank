# Latham 1862 Comparative Philology (Formosan lexical tables)

FormosanBank corpus of the Formosan lexical tables in Robert Gordon Latham's
1862 *Elements of comparative philology* (London: Walton and Maberly),
printed pp. 315–318.

## Repository At A Glance

| Field | Value |
| --- | --- |
| Type | Historical comparative wordlist |
| Languages | Siraya (`fos`, glottocode `sira1267`); Babuza-Favorlang (`bzg`, dialect `Favorlang`, glottocode `favo1235`) |
| Source | Latham 1862, printed pp. 314–319 |
| Size | 62 lexical `S` records; 70 source `FORM` tiers |
| Copyright | Public domain |
| Tiers | `original` only — no `standard` tier, no `PHON` |
| XML | `XML/Siraya/latham_1862_sideia_sida.xml`; `XML/Babuza-Favorlang/latham_1862_favorlang.xml` |

## What you get: the original tier only

**This corpus carries only a `FORM kindOf="original"` tier** (plus
`FORM kindOf="alternate"` where the source cell lists a variant, and English
`TRANSL` glosses). There is **no `standard` tier and no IPA/`PHON`**, and this
is deliberate.

A `standard` FORM is a claim that the text has been transliterated into
FormosanBank's single common orthography, and a `PHON` is a claim about
pronunciation. Neither claim can be supported here. How — or whether — to
standardize a 19th-century comparative wordlist in Babuza-Favorlang and Siraya
is an open question: Siraya is under a standing FormosanBank ruling not to be
standardized to Ortho113 or anything else for now, both varieties'
`standard_orthography` cells in the repo-root `standards.csv` are
correspondingly blank, and no living pronunciation reference exists for either
variety as Latham records them. Rather than ship a
tier that asserts a standardization nobody performed, the corpus ships what
Latham prints.

Practical consequences for a data user:

- Query `FORM[@kindOf="original"]`; do not expect `FORM[@kindOf="standard"]`.
- Tools that default to `--kindOf standard` will find nothing here. FormosanBank's
  token counting is unaffected: it falls back to the original tier, so this
  corpus's word counts are the same as they always were.
- `validate_xml` reports 62 SOFT `V014 count_missing_standard_form` findings
  against this corpus. That is the intended signal that the corpus has no
  standard tier, not a defect to fix.
- The historical spelling, including Latham's diacritics (`â á ó é à`), is
  preserved exactly in the original tier.

If the standardization question is ever settled, the tier can be regenerated
from the pre-correction snapshot by changing the pipeline (see "Maintenance
pipeline"); no source data was discarded.

## Source And Scope

The source is the six-page scan of Latham 1862 (public scan:
https://archive.org/details/elementsofcompar00lathrich). The scan has no text
layer, so the lexical table was transcribed by hand from the page renders into
`CodeAndDocs/source_ledger.tsv`, the authoritative, page-addressed
transcription.

The extraction covers the Formosan cells on printed pp. 315–318:

- Sideia and Sida are represented as Siraya (`fos`).
- Favorlang is represented as Babuza-Favorlang (`bzg`), dialect `Favorlang`.
- Philippine, Bashi, Malay, and Micronesian comparison data are out of scope.
- The 64-cell target grid contains 62 lexical cells and two printed dashes
  (Sida Forehead and Beard), which are terminally omitted.

## Extraction Decisions

- Each source cell becomes one lexical `S` record.
- A comma-separated source variant becomes a separate `FORM kindOf="alternate"`
  in the same record.
- `FORM kindOf="original"` preserves the reviewed historical spelling exactly,
  including Latham's diacritics (`â á ó é à`). There is **no orthographic
  standard** for these historical varieties, so no transliteration table
  exists and the published corpus carries no `standard` tier at all (see
  "What you get" above). The build still emits a `standard` tier — a verbatim
  copy of `original` — into the pre-correction snapshot, which is never edited
  (POL-035/POL-038); the maintenance pipeline removes it on the way to `XML/`.
- Lexical meanings are given as `TRANSL xml:lang="eng"`.
- No `PHON`, `W`, or `M` content is inferred: this is a lexical table with no
  phonology, segmentation, or morphology in the source.

## Reproduce

Requires Python 3 with `lxml` and `openpyxl` (FormosanBank's `.venv` has both).
The build reads `CodeAndDocs/source_ledger.tsv`; the original source PDF is
**not** required.

```bash
# 1. Rebuild the XML from the reviewed source ledger.
python CodeAndDocs/build_lexical_xml.py

# Independently verify every emitted XML field against the ledger
# (62/62 source cells; 2 dash cells omitted; 0 unresolved).
python CodeAndDocs/audit_source_coverage.py

# 2. Verify the build against the pre-correction snapshot (expected: no diff),
#    then run the maintenance pipeline (see below), which restores XML/ from
#    the snapshot and produces the published state from it.
diff -r Final_XML CodeAndDocs/pre_correction_snapshot
bash CodeAndDocs/make_xml.sh
```

`build_lexical_xml.py` writes to a scratch `Final_XML/` tree that is
byte-identical to `CodeAndDocs/pre_correction_snapshot/` (the pre-pipeline
baseline). The published `XML/` is that snapshot **plus** the maintenance
pipeline, which removes the derived `standard` tier and re-serializes the
files in the pipeline's output format (`<?xml version="1.0" ?>`, 4-space
indent, no trailing newline). Original- and alternate-tier text content is
identical in build, snapshot, and published XML.

## Maintenance pipeline

`CodeAndDocs/make_xml.sh [FORMOSANBANK_ROOT]` rebuilds the published `XML/`
from the pre-correction snapshot, in order (the script's comments explain each
step; interpreter override via the `PYTHON` env var). It is **idempotent**:
every run starts by restoring the snapshot, so re-running it is a no-op on the
published bytes.

0. Restore `XML/` from `CodeAndDocs/pre_correction_snapshot/`. The pipeline
   regenerates published data from the fixed baseline rather than editing
   `XML/` in place (POL-038).
1. `QC/cleaning/clean_xml.py` — character-level cleaning of the original
   tier. A verified no-op on this corpus (transcription is already clean;
   zero apostrophes, no `bzg`/`fos` attestation dictionaries, so quote
   correction never arms).
2. `CodeAndDocs/drop_derived_tiers.py` — deletes every
   `FORM[@kindOf="standard"]` and every `PHON`, at `S`, `W` and `M` level,
   leaving the original and alternate tiers untouched. On the current data
   this removes 62 S-level standard FORMs (24 Babuza-Favorlang, 38 Siraya)
   and 0 PHON. See "What you get" above for why, and
   `Corpora/WakelinTexts/CodeAndDocs/drop_derived_tiers.py`, the corpus this
   step is modeled on.

There is **no `standardize.py` step**: it was removed when the standard tier
was dropped, and re-adding it would put the tier straight back.

No `add_phonology` step either, **by design**: a historical lexical table with
no living pronunciation reference gets no `PHON` tier. Step 2 enforces that as
an invariant rather than leaving it to hold by accident — no `PHON` has ever
existed in this corpus, at any tier, in build, snapshot, or published XML.

### Pre-correction snapshot

`CodeAndDocs/pre_correction_snapshot/` is a byte-identical copy of the
pristine `XML/` taken before the corpus's first pipeline run, kept as the
fixed pre-pipeline baseline (this corpus is hand-transcribed, hence
non-regenerable from any upstream source other than the ledger). It is never
edited.

## QC Notes

- Structural XML validation: 62 SOFT (V014 `count_missing_standard_form`;
  24 `bzg` + 38 `fos`) — one per `S`, the designed signal that this corpus has
  no standard tier. 0 HARD, 0 WARN.
- Text: 1 SOFT finding (V116 non-ASCII) — the `ó` in the alternate-tier
  `arribórribon` (`S_favorlang_neck`). V116 skips the original tier by policy,
  so the other eight of the former nine findings were the *same* diacritics
  seen through the duplicate standard tier and went away with it. Latham's
  historical diacritics (`â á ó é à`) remain intact in the original tier.
- Gloss: 62 SOFT (V060) — expected; a lexical table has no `W`/`M` tiers.
  Unchanged by the tier removal.
- Token counts are unchanged by the tier removal (26 `bzg`, 38 `fos`):
  `QC/corpus_counts.py` counts the standard `FORM` if present and otherwise
  falls back to the original.
- Duplicates: `rahpal` (Foot) and `rima` (Hand) are genuine, distinct source
  attestations across varieties/pages and are retained (see
  `CodeAndDocs/duplicate_group_review.csv`).
- No orthography/vocabulary reference profile exists for these historical
  varieties, so those comparisons are unavailable; verification here is
  fidelity of the XML to the transcribed source (`CodeAndDocs/source_checks.tsv`,
  `CodeAndDocs/source_coverage_audit.md`).

## Citation

Latham, Robert Gordon. 1862. *Elements of comparative philology*. London:
Walton and Maberly. Public scan:
https://archive.org/details/elementsofcompar00lathrich
