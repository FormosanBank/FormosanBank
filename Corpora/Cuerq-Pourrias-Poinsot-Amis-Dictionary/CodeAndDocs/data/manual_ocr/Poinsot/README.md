# Poinsot Manual OCR Overrides

These files repair upstream `miaoski/amis-francais/txt/` pages that are blank or
visibly damaged even though the page scan is readable. `scripts/build_poinsot_xml.py`
uses `data/manual_ocr/Poinsot/<page>.txt` in preference to the upstream `txt/`
page, keeping scan-backed OCR correction reproducible and reviewable.

Each line follows the compact Poinsot dictionary format:

```text
headword - related/headform {category} definition
```

For multiword headwords that the inline OCR parser would otherwise split
ambiguously, use a tab-delimited line:

```text
headword phrase<TAB>definition
```

The source scan for page `NNN.txt` is `_sources/amis-francais/pic/NNN.png`.
