# Orthography Report

- Source orthography: Ortho94, as noted in the thesis/source review comments.
- XML handling: sentence-level `FORM kindOf="original"` and W-level `FORM` keep source segmentation. Sentence-level `FORM kindOf="standard"` removes segmentation/null/parenthetical markers conservatively.
- XSD constraint: FormosanBank `FORM@kindOf` only permits `original`, `standard`, or `alternate`; `Ortho94` is therefore recorded in `TEXT@source` and this sidecar report, not as a `kindOf` value.
- Null `Ø` markers are preserved in original S/W forms where present and removed from sentence-level standard forms.
- No machine translation or OCR-derived text is used in XML.
