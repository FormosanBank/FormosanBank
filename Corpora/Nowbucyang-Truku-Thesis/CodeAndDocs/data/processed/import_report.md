# Import Report

- Source: HSU_LOWKING_TRUKU_WORDFORMATION_2008
- Final XML path: `Final_XML/Truku/Hsu_Lowking_Truku_WordFormation_2008.xml`
- XML S elements ready for import: 253
- XML W elements emitted: 1120
- XML M elements emitted: 1407
- Sentence records with W/M: 253
- Sentence records with morpheme-level source glosses: 221
- Sentence records with word-level gloss translations: 0
- Sentence records with W/M but no reliable source gloss alignment: 32
- Machine translation used: no
- OCR used in XML: no
- Source glosses are encoded only as morpheme-level `M/TRANSL` where alignment is reliable; unaligned W/M forms are left unglossed and documented in `data/processed/gloss_alignment_audit.csv`.
- Morphology tables are preserved as sidecars and excluded from sentence XML unless they yielded an XML-eligible example.
- Slash-option expansions and parenthesized examples that need human translation/QC review are listed in `data/processed/manual_qc_slash_options.txt` and `data/processed/manual_qc_parentheses.txt`.
- Final_XML cleanliness: checked by `scripts/validate_formosanbank_xml.py`.
- FormosanBank punctuation/structure QC passes. Source segmentation is preserved in original S/W forms; sentence-level standard forms are de-segmented for standardized search/use.

Import status: ready for FormosanBank import if `validation_report.md` final summary remains PASS.
