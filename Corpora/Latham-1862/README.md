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
| XML | `XML/Siraya/latham_1862_sideia_sida.xml`; `XML/Babuza-Favorlang/latham_1862_favorlang.xml` |

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
  exists; the machine-owned `standard` tier is regenerated from `original` by
  `standardize.py --copy` and is letter-for-letter identical to it, diacritics
  included.
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
#    then run the maintenance pipeline (see below) to produce the
#    published state from a build put in place as XML/.
diff -r Final_XML CodeAndDocs/pre_correction_snapshot
bash CodeAndDocs/make_xml.sh
```

`build_lexical_xml.py` writes to a scratch `Final_XML/` tree that is
byte-identical to `CodeAndDocs/pre_correction_snapshot/` (the pre-pipeline
baseline). The published `XML/` is that build **plus** the maintenance
pipeline, which re-serializes the files in the pipeline's output format
(`<?xml version="1.0" ?>`, 4-space indent, no trailing newline). Text content
is identical in build, snapshot, and published XML.

## Maintenance pipeline

`CodeAndDocs/make_xml.sh [FORMOSANBANK_ROOT]` runs FormosanBank's canonical
cleaning/standardization pipeline over `XML/`, in order (the script's comments
explain each step; interpreter override via the `PYTHON` env var):

1. `QC/cleaning/clean_xml.py` — character-level cleaning of the original
   tier. A verified no-op on this corpus (transcription is already clean;
   zero apostrophes, no `bzg`/`fos` attestation dictionaries, so quote
   correction never arms).
2. `QC/utilities/standardize.py --copy` — regenerates the standard tier as a
   verbatim copy of the original tier (no transliteration table exists for
   these historical varieties, and Latham's diacritics are preserved).

No `add_phonology` step, **by design**: a historical lexical table with no
living pronunciation reference gets no `PHON` tier.

### Pre-correction snapshot

`CodeAndDocs/pre_correction_snapshot/` is a byte-identical copy of the
pristine `XML/` taken before the corpus's first pipeline run, kept as the
fixed pre-pipeline baseline (this corpus is hand-transcribed, hence
non-regenerable from any upstream source other than the ledger). It is never
edited.

## QC Notes

- Structural XML validation: 0 findings.
- Text: 9 SOFT findings (V116 non-ASCII) — Latham's historical diacritics
  (`â á ó é à`), which are intentional and preserved in all tiers.
- Gloss: 62 SOFT (V060) — expected; a lexical table has no `W`/`M` tiers.
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
