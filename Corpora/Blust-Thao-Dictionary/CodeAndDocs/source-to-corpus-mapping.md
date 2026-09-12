# Source-to-corpus mapping

## Authority and admitted scope

The locked source is Robert Blust's 2003 *Thao Dictionary*, SHA-256
`bd769bc6e625f53a631cc51f7dba87dfb90f4ac87039ea01f581fde991d22f95`.
The Institute of Linguistics, Academia Sinica authorization covers the five
interlinear texts on printed pages 244-274 and dictionary example sentences on
printed pages 280-1068 under CC BY-NC from 2024-01-31 through 2034-01-31.
Definitions, expository prose, front matter, notes that are not examples, and
the English-Thao index are excluded.

## Field mapping

| Source field | Corpus destination | Treatment |
| --- | --- | --- |
| Text sentence line | S `FORM kindOf="original"` | Preserved in Blust's spelling |
| Text word line | W `FORM kindOf="original"` | Preserved in printed alignment |
| Text word gloss | W English `TRANSL` | Exact whole-word gloss; no inferred M tier |
| Text free translation | S English `TRANSL` | Preserved as ordinary translation |
| Dictionary example | S `FORM kindOf="original"` | Preserved in Blust's spelling |
| Dictionary English | S English `TRANSL` | Preserved, subject to POL-024 and POL-025 structure |
| Printed placement note | Original FORM `notes` | Kept outside the Thao form |
| Page and record identity | S `source` | Printed page, PDF page, and stable source key |

Twenty-seven printed word positions lack an independently aligned gloss. Their
W elements are retained without a TRANSL rather than receiving an inferred
gloss. The source gives whole-word alignment but not an independently aligned
morpheme gloss line, so no M elements are generated.

Blust's whole-word English glosses also contain ordinary hyphenated phrases
such as `young-men`, `live-in-the-forest`, and `finished-Pudaqu`. Those printed
hyphens do not supply independently aligned morpheme glosses. They remain exact
W-level translations and are not used to invent M elements. Parentheses in
dictionary translations likewise carry source meaning or usage context, for
example `I killed (it)` and `said in begging`; they remain in TRANSL unless the
source explicitly labels the content as a literal analysis.

## Explicit alternatives

The reviewed raw extraction has 8,353 dictionary examples and 166 text
sentences. POL-026 expands each explicit parenthetical source option into
complete out/in records. POL-027 expands each explicit slash alternative into
one complete record per reading. All 92 slash-bearing source records have a
curated scope entry in `slash-alternatives.json`. Expansion produces 8,635
dictionary sentences and 167 text sentences with stable suffixes. POL-025 keeps
the two `==` English readings as sibling TRANSL elements, with later siblings
marked `ver="alt"`. POL-024 moves each explicit `(lit. ...)` analysis to the
corresponding TRANSL `notes` attribute.

## Orthography and derived tiers

Blust's practical spelling uses `c` for /theta/, `g` for /eng/, `sh`, `lh`, and
`z`; an apostrophe represents glottal stop, accents mark stress, and the printed
en dash marks a morpheme boundary. The original FORM retains this source
spelling before canonical punctuation cleaning. The conversion table maps
`c` to Ortho113 `th` and `g` to Ortho113 `ng`; canonical cleaning maps the dash
to ASCII hyphen, and `standardize.py` removes stress accents. Standard FORM and
both PHON tiers are generated only by the hash-locked FormosanBank utilities.
Blust's backtick plus closing-apostrophe convention marks quoted speech. The
builder converts those source-typographic delimiters to ASCII double quotes,
while independently attested word-final apostrophes remain glottal stops.
Rendered printed pages 266 and 269 also confirm three Type3 extraction gaps in
which an opening quote plus `A` aligned to FUT or A was returned as only the
quote; the extractor restores those three source-backed `A` words explicitly.
The generic `pdfplumber` gloss audit matched 8,614 of 8,802 generated sentences
but detected zero numbered example regions and left 160 sentences unmatched.
Rendered checks of representative unmatched records on printed pages 255, 280,
385, 876, and 1038 confirm that the records are present and match the reviewed
extraction. The unmatched bucket is therefore treated as a Type3 extraction
limitation, not evidence that those sentences are absent from the source.

The canonical output is 13 XML files under `XML/Thao`: one per interlinear text
and eight stable dictionary page-range parts. Sentence IDs derive from printed
text number and sentence number or from the extracted dictionary record key.
Word IDs append their stable printed position. The build checks global sentence
ID uniqueness and complete dictionary partition coverage.
