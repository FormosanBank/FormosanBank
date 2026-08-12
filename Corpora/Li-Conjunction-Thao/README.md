# Li (2014), *Conjunction in Thao*

- Language/dialect: Thao (`ssf`, `dialect="Thao"`)
- Source: Paul Jen-Kuei Li, “Conjunction in Thao,” pp. 401–409
- Canonical source: <https://openresearch-repository.anu.edu.au/items/8bfb8bf0-2f58-4eae-947c-bf9af50faf9f>
- Scope: all 24 numbered Thao examples and three additional Thao examples in footnote 7
- Status: expert W/M and standard-form review implemented and validated; published XML in `XML/Thao/`
- Development history: initial processing in the `Formosan-Paul-Jen-Kuei-Li-Conjunction-Thao` dev repo ([Basecamp card 8244168564](https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/8244168564)); everything needed to reproduce the XML is under `CodeAndDocs/`

The source uses Li's scholarly (IPA-style) transcription and aligned gloss lines.
The `original` tier preserves that transcription; the `standard` tier is Li's
transcription mapped to FormosanBank's common Thao orthography (Ortho113).
Examples (1)–(24) have source-aligned W tiers and M tiers wherever the printed
form/gloss explicitly marks morpheme boundaries. The three unglossed footnote
examples remain sentence-only.

**Note for users — M-tier coverage is partial.** The corpus has 211 W elements,
and **140 of them carry no M child** (the source does not segment those words),
which `validate_xml` reports as 140 SOFT V144 findings. The glosses that *do*
exist are sound: `validate_glosses` reports **0 HARD findings** (only 3 SOFT
V060). Completing the M tier per POL-023 is an open **linguistic** worklist item
([issue #102](https://github.com/FormosanBank/FormosanBank/issues/102)); no M
elements are added until the maintainer rules on the analysis.

## The standard tier: Ortho113, with sentence-level segmentation flattened

`make_xml.sh` finalizes the `standard` tier by running FormosanBank's
`standardize.py` with the `Thao_Li_113` conversion table
(`Orthographies/ConversionTables/Thao_Li_113.tsv`), which maps Li's transcription
to Ortho113 (`ð→z`, `ʃ→sh`, `θ→th`, `ŋ→ng`, `ɬ→lh`, `ʔ→'`) and strips stress
accents. It is not a standard tier unless it is Ortho113. (Because the pipeline
converts via this TSV, `standardize.py` runs in TSV mode — not `--copy`, not
`--remove_accents`; the table itself strips the accents.) The table was verified
with `QC/validation/validate_conversion_table.py` (Li/Thao vs Ortho113/Thao) on
2026-08-12: PASS, all 8 rows confirmed, no warnings, mismatches, or coverage
gaps.

`standardize.py` rebuilds the standard tier from the original, so it re-introduces
the source segmentation notation (`-`, `=`, `<`, `>`). `scripts/flatten_standard_segmentation.py`
then removes those markers from the **sentence-level** `FORM[@kindOf="standard"]`.

Since 2026-08, `standardize.py` itself applies the C012 rule (segmentation `-` and
clitic `=` stripped from S-level standard FORMs of morpheme-segmented sentences),
but flatten remains required for two reasons:

1. Thao is one of the two languages whose reference orthography lists `-` as a
   letter, so C012 deliberately *preserves* Thao hyphens and only emits `c012`
   warnings (`standardize_warnings.csv`; 88 of them for this corpus — transient,
   since flatten strips the hyphens immediately after). That exemption exists to
   protect a `-` that is a real orthographic letter; in this source the hyphens
   only ever mark morpheme boundaries in Li's interlinear analysis (the glottal
   stop is written `ʔ`, never `-`), with no evidence Li uses `-` otherwise — so
   the exemption does not apply here.
2. C012 does not touch the infix markers `<` `>` (10 pairs in this corpus's
   sentence FORMs); no shared QC code strips those from the S-level standard tier
   (validate_text V134 merely flags them SOFT).

The markers are still preserved in the `original` sentence tier and in the W/M
tiers (both `original` and `standard`), where they carry the morphological
analysis.

Phonology is then added with `add_phonology.py --orthography Li`: standard `PHON`
from the Ortho113 standard tier, original `PHON` from `Orthographies/Li`. Because
`standardize.py` strips accents from the standard tier, the standard `PHON` is
clean IPA; the original `PHON` renders Li's stress accents `á`/`ú` as `*` (they
are not phonemic and have no orthographic mapping), which is accepted.

**Regenerated under the shared-source-phonology pipeline (2026-08-12 sweep):**
the published `XML/` is the output of `make_xml.sh` run against the current QC
code. Relative to the pre-sweep publication the only change was in sentence-level
`PHON`, where unmapped punctuation (sentence-internal/final `.`/`,`) is dropped —
the pipeline's "punctuation is not sound" policy. All FORM tiers, glosses, and
the W/M structure are unchanged; the source-fidelity audit and the draft/final
byte-match both pass, and a rerun is byte-idempotent.

## Corrected source transcription typos (capital `S` and `D`)

The printed source contains two capital-letter transcription typos, both inherited
from Blust's *Thao Dictionary* (2003), which Li quotes. They were checked against
Blust's original and are **corrected in code** by `correct_source_typos()` in
[`scripts/build_xml.py`](scripts/build_xml.py), applied to the Thao *original*
field at the earliest step — before the original text is used to build the
standard, W, or M tiers — so the fix propagates uniformly to every tier. The raw
transcription in [`raw_data/reviewed_examples.tsv`](raw_data/reviewed_examples.tsv)
is left exactly as printed; only the generated XML carries the correction.

| Printed | Correct grapheme | Count | Where | Basis |
|---|---|---:|---|---|
| `S` | `ʃ` | 1 | example (21), `ɬpaðiSan` → `ɬpaðiʃan` | typo in Blust's dictionary for /ʃ/ |
| `D` | `ð` | 6 | footnote-7 examples (S025–S027): `iDa` (×2), `saqaDi`, `waDaqan`, `aDaDak` (×2) | typo in Blust's dictionary for /ð/ |

The correction touches **only** the Thao `original` field, never the gloss or
metadata columns, where capital `D`/`S` legitimately occur (`DET`, `RED`, `STA`,
`CAUS`, and the `PDF p. …` locators). After correction the corpus contains no
unknown/uninterpretable graphemes: every letter maps cleanly through the Li
orthography table (`Orthographies/Li/Thao.tsv`) and the Li→Ortho113 conversion
table (`Orthographies/ConversionTables/Thao_Li_113.tsv`) in FormosanBank.

## Reproduce

The corpus is fully regenerable from the committed reviewed records
(`raw_data/reviewed_examples.tsv`) — no pre-correction snapshot is needed.
From `CodeAndDocs/`, using Python 3.11 or newer, with `FORMOSANBANK_PATH` set to
a FormosanBank checkout (it supplies `standardize.py`, `add_phonology.py`, and the
`Li`/`Ortho113` orthography tables, and its Python env must have `lxml`):

```bash
FORMOSANBANK_PATH=/path/to/FormosanBank ./make_xml.sh
```

`make_xml.sh` is the **only** script needed; it is the whole pipeline, not a
wrapper around another one:

1. `scripts/build_xml.py` — draft `XML/` and `Final_XML/` from the reviewed TSV,
   including the scripted Blust-typo corrections
2. `scripts/audit_source_fidelity.py` — source-fidelity audit, while the tiers
   are still in Li's transcription
3. `QC/cleaning/clean_xml.py` — the shared character-level cleaning of the
   original tier (see below)
4. `standardize.py` in TSV mode (Thao_Li_113 → Ortho113)
5. `scripts/flatten_standard_segmentation.py` — strips `- = < >` from the
   S-level standard FORMs
6. `add_phonology.py --orthography Li`
7. draft/final byte-match, then install `Final_XML` into the corpus-level `XML/`
   and clear the scratch outputs (`CodeAndDocs/XML/`, `Final_XML/`,
   `intermediate/`, and the `standardize_warnings.csv` sidecars, whose expected
   content is exactly the 88 Thao `c012` hyphen warnings — see above; per-run
   reports, never committed)

`clean_xml` (step 3) runs where every other corpus runs it — after the build,
**before** `standardize`, so the standard tier is rebuilt from an already-clean
original tier. It does far more than quote correction: dash/tilde/quote
canonicalization, HTML-entity and double-encoded-entity decoding, null-glyph
canonicalization, Unicode flattening, empty-element removal, and
translation-metadata normalization. On this corpus it is **currently a no-op —
because the XML is born clean from the reviewed TSV**, not because any of that
machinery is inapplicable; `make_xml.sh` prints whether that still holds on
every run. Thao's letter `-` is not at risk: the dash rule maps only dash
*look-alikes* (en dash, em dash, minus sign, …) onto ASCII `-`, and never
touches an ASCII `-` that is already there.

There is no `apply_manual_edits` step: the corpus has no `manual_edits.xml`
(the only hand-checked fixes are the scripted typo corrections in
`build_xml.py`).

To reacquire the official source bundle for visual review, run
`./download_source_data.sh`; downloads stay under ignored `Private/`.

## QC

From the FormosanBank root, against this corpus's `XML/`:

```bash
python QC/validation/validate_xml.py     by_path --path Corpora/Li-Conjunction-Thao/XML
python QC/validation/validate_text.py    by_path --path Corpora/Li-Conjunction-Thao/XML
python QC/validation/validate_glosses.py by_path --path Corpora/Li-Conjunction-Thao/XML
```

Current baseline (2026-08-12): **no HARD findings from any of the three.** SOFT
findings, all accepted source-specific characteristics:

- `validate_xml` — 140 × V144 (M-less W; see the M-coverage note above)
- `validate_text` — 44 × V122 (English parentheses/slashes in translations),
  20 × V134 (source infix notation `<...>` in original S FORMs), 22 × V136
  (scholarly non-ASCII transcription confusables)
- `validate_glosses` — 3 × V060 only, **0 HARD**

On [issue #102](https://github.com/FormosanBank/FormosanBank/issues/102): its
gloss-validator concern is **satisfied** — `validate_glosses` is HARD-clean. Its
M-coverage concern is **not** satisfied — 140 of 211 W still have no M (V144
SOFT ×140), and that remains an unruled linguistic worklist item. Do not add M
elements to close it without a maintainer ruling on the analysis.
