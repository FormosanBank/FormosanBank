---
icon: tags
---

# Gloss standardization

Morphological gloss codes vary across sources just as spellings do: one source writes `AF`, another 主事焦點, a third `AV` — for the same category. FormosanBank therefore attempts to standardize glosses across sources, into a single vocabulary based on the [Leipzig Glossing Rules](https://www.eva.mpg.de/lingua/resources/glossing-rules.php) plus a small registry of project codes. The standardized glosses live in the **STANDARD tier** of the XMLs — beside every original gloss (`TRANSL kindOf="original"`, never altered) sits a `TRANSL kindOf="standard"` with the converted codes; codes whose mapping is not yet decided are copied verbatim, so the standard tier is always complete.

- The per-corpus conversion documents — one standardization list per source, recording every decided and still-open code — live in [`Glossing/ConversionTables/`](https://github.com/FormosanBank/FormosanBank/tree/main/Glossing/ConversionTables), and the project-wide approach is described in [`Glossing/README.md`](https://github.com/FormosanBank/FormosanBank/blob/main/Glossing/README.md).
- The **gloss dictionary** — the ruled vocabulary per language, with a definition for every code the standard tier uses — is in [`Glossing/GlossDictionaries/`](https://github.com/FormosanBank/FormosanBank/tree/main/Glossing/GlossDictionaries); each [language page](../languages/README.md) on this site also renders its language's dictionary ("Ruled gloss codes").
- The tool that builds the standard gloss tier is `QC/glossing/apply_gloss_standard.py`; see [its documentation](../the-bank-architecture/developers/qc-pipeline/apply-gloss-standard.md#related).

## Related

- [Orthography standardization](orthography.md)
- [apply_gloss_standard.py](../the-bank-architecture/developers/qc-pipeline/apply-gloss-standard.md)
- [validate_glosses.py](../the-bank-architecture/developers/qc-pipeline/validate-glosses.md)
- [FormosanBank XML Format](../the-bank-architecture/formosanbank-xml-format.md)
