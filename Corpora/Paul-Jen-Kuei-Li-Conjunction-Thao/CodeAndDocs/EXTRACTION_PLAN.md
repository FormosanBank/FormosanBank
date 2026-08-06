# Extraction plan

The source is a nine-page article (PDF pp. 394–402 / printed pp. 401–409) in a 402-page ANU PDF volume with embedded text and a separate text bitstream.

1. Reacquire and checksum the official volume and metadata with `download_source_data.sh`.
2. Extract PDF pp. 394–402 with layout-aware `pdftotext`; use text only as a locator.
3. Render and inspect every article page.
4. Maintain all 27 source-visible examples in `raw_data/reviewed_examples.tsv`.
5. Generate deterministic evidence and tiered XML with `scripts/build_xml.py`.
6. Inventory every page in `intermediate/source_ledger.csv`; map every S in `intermediate/xml_source_map.csv`.
7. Render all XML records for review, promote to `Final_XML/Thao/`, and validate there.

Included material is numbered examples (1)–(24) and the three Thao utterances in footnote 7. Prose mentions of words, appendix counts, bibliography, headers, and non-Thao comparative material are excluded with page-level reasons.

The source supplies scholarly sentence forms, aligned gloss lines for examples (1)–(24), and English translations. Final XML uses `xml:lang="ssf"`, `dialect="Thao"`, deterministic S/W/M IDs, source-faithful originals, sentence standards without segmentation markers, and English sentence translations. W nodes follow the printed word/gloss alignment. M nodes are emitted only when matching source form and gloss tokens explicitly mark hyphens or infixes. The three unglossed footnote examples remain sentence-only. There is no audio or source PHON.

Draft: `XML/Thao/li_2014_conjunction_in_thao.xml`. Final: `Final_XML/Thao/li_2014_conjunction_in_thao.xml`.
