# Reproduction inputs

The entry point is `CodeAndDocs/generate_xml.sh`; the corpus README's
"Reproduction and processing" section lists its steps. It runs with the current
FormosanBank tools and records them in [provenance.json](../provenance.json).

Inputs:

- `extraction_report.csv` and `table_extraction_report.csv`: the IDs and source
  locations of the 670 transcribed records.
- `manual_edits.xml`: the expert transcription of those records, including all
  W and M and the alternative readings.
- `source_data/` (see its README): the TEXT metadata, the footnote and prose
  supplement, the added records and the corrections.

Example 17d keeps the null prefix the source prints (scan pp. 37–38): the
original sentence reads `∅-imelang ci Taymu kiyu si-dinget.`, the word has a
null M and a root M, and the standard sentence omits the silent prefix.
Example 23c prints `kiya hemay` and 飯 in parentheses (scan p. 55), so it is
two S; the shorter reading has `-opt` IDs and only its own W, M and
translation. The four footnote examples without glosses have no W.

The source scan is needed only to re-inspect the source; the build does not
read it.
