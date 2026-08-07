# Li (2014), *Conjunction in Thao*

Private FormosanBank development repository for [Basecamp card 8244168564](https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/8244168564).

- Language/dialect: Thao (`ssf`, `dialect="Thao"`)
- Source: Paul Jen-Kuei Li, “Conjunction in Thao,” pp. 401–409
- Canonical source: <https://openresearch-repository.anu.edu.au/items/8bfb8bf0-2f58-4eae-947c-bf9af50faf9f>
- Scope: all 24 numbered Thao examples and three additional Thao examples in footnote 7
- Status: Madeline's W/M and standard-form review is implemented and validated
- Final deliverable: `Final_XML/Thao/li_2014_conjunction_in_thao.xml`

The source uses Li's scholarly (IPA-style) transcription and aligned gloss lines.
The `original` tier preserves that transcription; the `standard` tier is Li's
transcription mapped to FormosanBank's common Thao orthography (Ortho113).
Examples (1)–(24) have source-aligned W tiers and M tiers wherever the printed
form/gloss explicitly marks morpheme boundaries. The three unglossed footnote
examples remain sentence-only.

## The standard tier: Ortho113, with sentence-level segmentation flattened

`scripts/reproduce.sh` finalizes the `standard` tier by running FormosanBank's
`standardize.py` with the `Thao_Li_113` conversion table
(`Orthographies/ConversionTables/Thao_Li_113.tsv`), which maps Li's transcription
to Ortho113 (`ð→z`, `ʃ→sh`, `θ→th`, `ŋ→ng`, `ɬ→lh`, `ʔ→'`) and strips stress
accents. It is not a standard tier unless it is Ortho113.

`standardize.py` rebuilds the standard tier from the original, so it re-introduces
the source segmentation notation (`-`, `=`, `<`, `>`). `scripts/flatten_standard_segmentation.py`
then removes those markers from the **sentence-level** `FORM[@kindOf="standard"]`.
This includes the hyphen, even though Thao's reference orthography lists `-` as a
letter and the general FormosanBank `clean_xml` C012 rule therefore keeps it for
Thao. That C012 exemption exists to protect a `-` that is a real orthographic
letter; in this source the hyphens only ever mark morpheme boundaries in Li's
interlinear analysis (the glottal stop is written `ʔ`, never `-`), with no
evidence Li uses `-` otherwise — so the exemption does not apply here. The markers
are still preserved in the `original` sentence tier and in the W/M tiers (both
`original` and `standard`), where they carry the morphological analysis.

Phonology is then added with `add_phonology.py --orthography Li`: standard `PHON`
from the Ortho113 standard tier, original `PHON` from `Orthographies/Li`. Because
`standardize.py` strips accents from the standard tier, the standard `PHON` is
clean IPA; the original `PHON` renders Li's stress accents `á`/`ú` as `*` (they
are not phonemic and have no orthographic mapping), which is accepted.

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

From a clean checkout, using Python 3.11 or newer, with `FORMOSANBANK_PATH` set to
a FormosanBank checkout (it supplies `standardize.py`, `add_phonology.py`, and the
`Li`/`Ortho113` orthography tables, and its Python env must have `lxml`):

```bash
FORMOSANBANK_PATH=/path/to/FormosanBank ./scripts/reproduce.sh
```

The command rebuilds the draft and `Final_XML` from the committed reviewed
records — build → source-fidelity audit → `standardize` (Ortho113) → flatten
sentence-level segmentation → `add_phonology` — and verifies that both outputs
byte-match. To reacquire the official source bundle for visual review, run
`./download_source_data.sh`; downloads stay under ignored `Private/`.

## QC

Set `FORMOSANBANK_PATH` to a clean FormosanBank reference checkout, then run the commands recorded in `docs/qc_report.md`. Final logs are under `logs/final_qc/`.

Accepted source-specific findings are scholarly non-ASCII transcription, source infix notation in original tiers, English parentheses/slashes, and three W-count notices for footnote examples without source glosses. There are zero unresolved findings.
