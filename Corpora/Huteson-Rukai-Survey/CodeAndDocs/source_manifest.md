# Source manifest

- Public archive: https://www.sil.org/resources/archives/9008
- Citation: Huteson, Greg. 2003. *Sociolinguistic Survey Report for the Tona and
  Maga Dialects of the Rukai Language*. SIL International.
- Rights: SIL's terms of use — "Unless stated otherwise in the file or item
  description, all items are available under the Creative Commons
  Attribution-Noncommercial-Share Alike 4.0 Unported License." Read 2025-01-24;
  recorded as `CC BY-NC-SA 4.0` per `rights_vocabulary.csv`. ("Unported" is a
  Creative Commons 3.0-era word; the version named is 4.0, which is what the
  corpus records.)
- Source PDF: 46 pages. SHA-256
  `adf8c6124f46ed414c61c7d121fab22f489c6b98fb17dcd584dbc2eac210b91f`
- Corpus scope: Appendix B, pages 38-44. Every page's disposition is recorded in
  `source_page_coverage.tsv`.
- Layout text cache (optional, for inspection only): `pdftotext -layout` output.
  SHA-256 `eaa82f21c539b3f0f9c4cc0caa50f044947fc82e197d25b015d254778a4d062b`
- Licence screenshot (internal copy of the terms above). SHA-256
  `e308f3a55cd605ed8c59de0748131034c12fd09f7e2349845985952fdb0ddff4`
- Acquisition method: download the report from the public archive above. **The
  build does not read the PDF** — `build_xml.py` works from the reviewed
  transcription in `manual_source_review.tsv`, so a rebuild needs nothing but a
  FormosanBank checkout (POL-048).
- Local verification: `audit_source_alignment.py --source <pdf>` checks a local
  copy against the SHA-256 recorded above, which it reads from this file.
- Internal copy: Basecamp card 8255603132 (maintainer only; not a build input).
