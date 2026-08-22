# Source Audit: Safolu Amis Dictionary

Upstream repositories inspected:

- `g0v/amis-moedict` at `e7c6976a0766e9b0aeb7083e2c06db60f5485252`
- `miaoski/amis-safolu` at `f512d5ba0d08f81b26093a9b7b4a85acac760a30`

Checked against the public FormosanBank XML Format documentation:
https://ai4commsci.gitbook.io/formosanbank/the-bank-architecture/formosanbank-xml-format

## Dictionary Mapping

The `g0v/amis-moedict` README maps the generated JSON folders as:

- `s`: 蔡中涵大辭典 / Safolu Kacaw Lalanges-Tsai dictionary: **this repository**.
- `p`: 方敏英字典 / Virginia Fey dictionary: processed separately (out of scope).
- `m`: 潘世光、博利亞阿法字典 / Maurice Poinsot & Louis Pourrias dictionary: moved
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

- **185** retained rows had an empty Amis field but a recoverable Amis phrase at the start
  of the Chinese field; recovered with `recovered_form_from_translation`. A single
  leading annotation (`〔…〕`, `﹝…﹞`, `(…)`, `（…）`) is peeled off first so loanword notes
  like `(閩南語借詞) O 'amis ko hongti niyam.…` recover the real Amis sentence
  rather than a stray parenthesis. A `（…）` annotation that straddles the split
  point (`…hikoki（外來語）.孩子…`) is repaired so the form stays pure Amis.
- **29** retained rows had the Amis embedded inside a Chinese grammar/pronunciation note in
  the source `` `…~ `` link markup; recovered with `recovered_form_from_note`
  (single embedded Amis phrase + following Chinese gloss only).
- **191** sentences come from **CJK-in-FORM** fields the source packed with
  `Amis 中文gloss` content (`split_from_cjk_form`): a single glued pair
  (`Itira 在那裡.` → `Itira` / 在那裡) or a `；`/`，`-separated derivational list
  (often prefixed `如`), e.g. `kalacokap 當鞋子穿；kalasakaen 當菜餚吃；…` → one
  sentence per pair. Each pair becomes its own `S` with id `S<ordinal>_<k>`.
- **269** retained rows have a real Amis FORM but no Chinese translation; kept as valid
  FORM-only sentences (`no_translation`).
- A few source form fields begin with an orphaned `）`/`)` (digitization artifact);
  the leading close-paren is stripped.
- **61** source fields use fail-closed, ordinal-keyed corrections or recoveries.
  Each override asserts the exact cleaned pinned-upstream fields before applying.
- **21** Chinese translation fields began with a clause copied from the Amis
  source. The Chinese translation is now typed separately while the repeated
  Amis text remains in TRANSL notes and complete raw-source metadata.
- **2** packed derivational fields are split into three explicit Amis and
  Chinese pairs each. One interrupted sentence is realigned, and one stray
  terminal slash is repaired as punctuation.
- **22** source fields remain unrecoverable (**16** `empty_form` + **6**
  `cjk_in_form_unsplittable`) and
  are written to `amis_safolu_examples.rejected.json` with their reason.

Coverage is tracked at the **source-field** level (a field can expand into several
sentences), via each record's `source_ordinal`:

```text
49,440 extracted/recovered sentences from 49,397 represented source fields
  + 22 rejected source fields  =  49,419 source example fields
  - 261 duplicate source rows  =  49,179 final XML sentences
```

Duplicate equivalence is evaluated on the reviewed standard FORM because this
is a dictionary under POL-022. The durable duplicate ledger retains every
dropped source row. The generator merges every distinct same-language
translation into the survivor and marks the later reading `ver="alt"` under
POL-025; 140 such Chinese readings are preserved.

### Residual validator findings

Current validator findings are written to an external per-run directory and
were classified during the private QC handoff. Confirmed corruption such
as `mafutiۥ`, `dadaydayㄡ`, and `cangaw﹑fiting` is corrected through the
override table. The residual inventory is 3 source-authentic non-ASCII
characters, 578 balanced parenthesis or slash findings, and 48 source-faithful
standard-tier hyphens. All are SOFT and exact; current validators report zero
HARD findings.

## Orthography derivation

The original tier preserves the source's distinct `o` and `u` spellings and
its mixed legacy `g` / current `ng` representation of /ŋ/. These are source
spellings, not Ortho113 output. Safolu Kacaw Lalanges argues explicitly for
retaining both vowel letters in his 2013 article. Li (2013:27) documents the
older Amis church use of `g` for /ŋ/ and the later shift to `ng`. The pinned
data itself includes 95 records with single `g`, including an exact
`tagila` / `tangila` duplicate pair. See
`CodeAndDocs/docs/orthography_evidence.md`.

The pipeline therefore:

1. generates original FORM directly from the pinned source;
2. runs original PHON with the FormosanBank Safolu Coastal profile;
3. generates standard FORM with
   `Orthographies/ConversionTables/Amis_Safolu_113.tsv`, Coastal column, in
   longest-source single-pass mode so existing `ng` is not remapped;
4. generates standard PHON with the current Ortho113 Coastal profile.

### Reviewed unmapped PHON characters

POL-003 makes unmapped FORM characters visible as `*` in PHON rather than
inventing a pronunciation. The final inventory was checked exactly in the
private QC handoff: 226 digits in dates, year ranges, and `COVID-19`;
five uppercase `V` characters in `COVID-19`; four source `b` characters
(`Cabgalal`, `fafahiyab`, `bungka`, `Kebalan`); three source `z` characters
(`Skizaya`, two `zakaimo`); one `v` in `vitos`; and one isolated source `q` in
`Aqaay`. These 240 characters produce exactly 240 reviewed stars in each PHON
tier. The foreign names, loans, alphanumeric labels, and isolated anomalous
spellings are preserved without assigning unsupported Amis phonological values.

## TEXT/@dialect

`dialect="Coastal"` records the author's documented Madawdaw community provenance.
Official teaching sources place Madawdaw under Coastal Amis. See
`CodeAndDocs/docs/dialect_evidence.md`; the label does not assert independent dialect
classification of every dictionary example.

## Public package layout

```
XML/Amis/Safolu/amis_safolu_examples.xml
CodeAndDocs/data/safolu_source_overrides.json
CodeAndDocs/data/orthography/Amis_Safolu_113.tsv
CodeAndDocs/docs/orthography_evidence.md
CodeAndDocs/docs/dialect_evidence.md
```

`XML` intentionally contains only `.xml` files. The rebuild generates the
per-record provenance, rejection, and duplicate ledgers in its external work
directory. Per-run audit reports, validator CSVs, logs, and warning sidecars
remain outside the repository.
Virginia Fey (`docs/p`) is out of scope; the Poinsot dictionary (`docs/m`)
lives in `Formosan-Poinsot-Amis-Dictionary`.
