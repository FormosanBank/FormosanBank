# Source Audit: Safolu Amis Dictionary

Upstream repositories inspected:

- `g0v/amis-moedict` at `e7c6976a0766e9b0aeb7083e2c06db60f5485252`
- `miaoski/amis-safolu` at `f512d5ba0d08f81b26093a9b7b4a85acac760a30`

Checked against the public FormosanBank XML Format documentation:
https://ai4commsci.gitbook.io/formosanbank/the-bank-architecture/formosanbank-xml-format

## Dictionary Mapping

The `g0v/amis-moedict` README maps the generated JSON folders as:

- `s`: 蔡中涵大辭典 / Safolu Kacaw Lalanges-Tsai dictionary — **this repository**.
- `p`: 方敏英字典 / Virginia Fey dictionary — processed separately (out of scope).
- `m`: 潘世光、博利亞阿法字典 / Maurice Poinsot & Louis Pourrias dictionary — moved
  to the **`Formosan-Poinsot-Amis-Dictionary`** repository (needs OCR-correction work).

This export targets example sentence / phrase translation pairs. Lexical headwords
and definitions are preserved in metadata as context for each example, not promoted
into sentence records.

## Morphology and Gloss Tiers

The finalized XML stops at sentence-level `S` elements. The Safolu `docs/s`
examples are Moedict-delimited fields embedded in definition records (entry,
heteronym, definition, example); they carry no source-attested word segmentation,
morphological segmentation, or word-by-word gloss tiers, so adding `W`/`M` layers
would invent annotation rather than preserve data.

## Safolu / Tsai

The frozen `miaoski/amis-safolu` README says the source moved to
`g0v/amis-moedict/docs/s` after March 20, 2022, so the converter uses the current
generated JSON from `docs/s`.

The inspected `docs/s` tree contains:

- 42,273 lexical JSON files
- 57,361 definitions
- 49,419 example fields

All 49,419 example fields use the Moedict delimiters:

- `U+FFF9`: Amis form start
- `U+FFFA`: middle translation separator
- `U+FFFB`: final translation separator

For Safolu the final translation field is Chinese. The middle field is empty
except for one `undefined` artifact, which is discarded and recorded in metadata.

## Recovered and Rejected Rows

FormosanBank XML requires a non-empty `FORM`; `TRANSL` is optional (the schema
`S_Type` is an `xs:choice` with `minOccurs="0"`). Malformed example fields are
recovered where possible instead of being dropped:

- **187** rows had an empty Amis field but a recoverable Amis phrase at the start
  of the Chinese field; recovered with `recovered_form_from_translation`. A single
  leading annotation (`〔…〕`, `(…)`, `（…）`) is peeled off first so loanword notes
  like `(閩南語借詞) O 'amis ko hongti niyam.…` recover the real Amis sentence
  rather than a stray parenthesis. A `（…）` annotation that straddles the split
  point (`…hikoki（外來語）.孩子…`) is repaired so the form stays pure Amis.
- **32** rows had the Amis embedded inside a Chinese grammar/pronunciation note in
  the source `` `…~ `` link markup; recovered with `recovered_form_from_note`
  (single embedded Amis phrase + following Chinese gloss only).
- **191** sentences come from **CJK-in-FORM** fields the source packed with
  `Amis 中文gloss` content (`split_from_cjk_form`): a single glued pair
  (`Itira 在那裡.` → `Itira` / 在那裡) or a `；`/`，`-separated derivational list
  (often prefixed `如`), e.g. `kalacokap 當鞋子穿；kalasakaen 當菜餚吃；…` → one
  sentence per pair. Each pair becomes its own `S` with id `S<ordinal>_<k>`.
- **272** rows have a real Amis FORM but no Chinese translation; kept as valid
  FORM-only sentences (`no_translation`).
- A few source form fields begin with an orphaned `）`/`)` (digitization artifact);
  the leading close-paren is stripped.
- **44** source fields remain unrecoverable (**26** `empty_form` + **18**
  `cjk_in_form_unsplittable`, the latter including the 4 pure-Chinese notes) and
  are written to `amis_safolu_examples.rejected.json` with their reason.

Coverage is tracked at the **source-field** level (a field can expand into several
sentences), via each record's `source_ordinal`:

```text
49,400 XML sentences from 49,375 represented source fields
  + 44 rejected source fields  =  49,419 source example fields
```

### Residual source artifacts (SOFT, left as-is)

About a dozen forms carry stray OCR/encoding characters from the original
digitization — e.g. `mafutiۥ` (glottal `'` mis-OCR'd as U+06E5), `dadaydayㄡ`
(a Bopomofo character), `cangaw﹑fiting` (a fullwidth list comma). These surface
as `validate_text` SOFT findings (V116) and are faithful to the source; they are
not auto-corrected.

## TEXT/@dialect

`dialect="unknown"` is emitted because the Safolu dictionary does not record a
single Amis dialect. The honest sentinel passes FormosanBank validation (V036);
set the real dialect during QC before porting.

## Final Package Layout

```
Final_XML/Amis/Safolu/amis_safolu_examples.xml
data/formosanbank_audit/Safolu/amis_safolu_examples.metadata.json   (per-sentence provenance)
data/formosanbank_audit/Safolu/amis_safolu_examples.rejected.json   (unrecoverable rows)
data/formosanbank_audit/manifest.json                               (sizes + SHA-256)
data/formosanbank_audit/coverage_audit.json                         (coverage checks)
```

`Final_XML` intentionally contains only `.xml` files. Virginia Fey (`docs/p`) is
out of scope; the Poinsot dictionary (`docs/m`) lives in `Formosan-Poinsot-Amis-Dictionary`.
