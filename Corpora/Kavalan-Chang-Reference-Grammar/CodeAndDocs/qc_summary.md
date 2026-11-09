# QC summary

## Pipeline

- `build_xml.py` writes the original FORM tier and the source glosses and translations to `XML/Kavalan/`;
  FormosanBank's `standardize.py` adds the standard FORM tier with `Kavalan_TaiwanNandao_113.tsv` (r -> l, l -> d),
  and its `add_phonology.py` adds original PHON with the shared `TaiwanNandao` profile and standard PHON with
  Ortho113 (`generate_xml.sh`). `validate.sh` runs the checks below. Both use the
  FormosanBank checkout they find, normally `main` at HEAD; the commit `XML/` was last built against is in
  `provenance.json` (POL-052).
- Sentence-level TRANSL has no `kindOf`; every word and morpheme gloss has `kindOf="original"`.
- Of the 22 printed alternatives, 12 are sentences of their own (11 distinct; one is printed twice), 8 are a second
  FORM (`ver="alt"`) on their word, and 2 are left out with recorded decisions (analysis notation; a form the book
  marks unacceptable).

## Inventory

- Source ledger: 755 records (478 printed examples, 277 coverage-only vocabulary entries), plus 14 printed examples
  it missed (`source_units_additions.tsv`)
- Proofreading: 59 corrected fields in 50 units, 56 of them (in 47 units) applied; 125 notes; 7 departures recorded
  in `review_adjudication.tsv`
- XML: 461 S (450 examples, 11 alternative readings), 1,661 W and 2,502 M elements
- Original FORM: 4,632 (8 of them a word's second FORM); original PHON: 4,624; PHON conversion failures: 0
- Standard FORM: 4,632; standard PHON: 4,624 (9 of them with `*`: the `o` of miaori(q) 苗栗, which Ortho113 Kavalan lacks)

## Expected FormosanBank findings

On FormosanBank `main` (the commit in `provenance.json`):

- XML: `V144` SOFT count 6
- Text: `V142` SOFT x3; `V134` SOFT x164 (each `<` and `>` of the 82 infixes, in 79 sentence lines)
- Glosses: `V061` SOFT x10; `V065` SOFT x3; `V153` SOFT count 13
- Original-tier duplicate groups: 0

`audit_qc_findings.py` rejects any finding outside this set, any change of location for the per-word findings and
any change of message for the whole-file ones, and records a reason for each:

- `V061`, `V144`, `V153`: words whose printed gloss does not divide the way the word does, and so have no
  morphemes or a different number of them (see the README's "Conventions"); `V153` also counts the hyphen inside
  `知道=動貌（-他）`.
- `V065`: three sentences the book does not gloss at all.
- `V134`: the sentence line writes infixes in angle brackets, as the word FORM does (ruled 2026-11-09).
- `V142`: the word "marginal" in three notes about handwriting in the margin, not about grammaticality.
