---
icon: spell-check
---

# Orthography standardization

Formosan language orthographies are not highly standardized in the wild: different sources spell the same word in different ways. FormosanBank therefore attempts to standardize orthography across sources. The standardized text lives in the **STANDARD tier** of the XMLs — every sentence carries a `FORM kindOf="original"` (the source's exact spelling, never altered) and a `FORM kindOf="standard"` (the same text in FormosanBank's common orthography).

- The reference orthographies and the per-source conversion tables live in [`Orthographies/`](https://github.com/FormosanBank/FormosanBank/tree/main/Orthographies) — the Ortho113 profiles define the common standard, and [`Orthographies/ConversionTables/`](https://github.com/FormosanBank/FormosanBank/tree/main/Orthographies/ConversionTables) holds the source-to-standard mappings.
- The tool that builds the standard tier is `QC/utilities/standardize.py`; see [its documentation](../the-bank-architecture/developers/qc-pipeline/standardize.md#related) for modes, rules, and the related pipeline steps.

## Related

- [Glossing standardization](glossing.md)
- [standardize.py](../the-bank-architecture/developers/qc-pipeline/standardize.md)
- [FormosanBank XML Format](../the-bank-architecture/formosanbank-xml-format.md)
