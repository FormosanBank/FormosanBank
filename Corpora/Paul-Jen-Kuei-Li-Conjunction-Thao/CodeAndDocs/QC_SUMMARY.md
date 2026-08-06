# QC summary

The reviewed XML passed the applicable FormosanBank checks:

- XML: 0 findings.
- Text: 0 HARD findings; 428 reviewed SOFT findings for source scholarly
  notation, English parentheses/slashes, infix notation, and mixed-script
  symbols.
- Glosses: 0 HARD findings; three expected V060 notices for the unglossed
  footnote examples.
- Original and standard duplicate checks: 0 HARD and 0 SOFT groups.
- Source fidelity: five fixed checks and all 27 structural checks passed.
- Reproduction: `bash CodeAndDocs/reproduce.sh` rebuilds byte-identical XML.

The existing reviewed sentence standard tier is preserved. It is intentionally
not replaced with a copy of the original tier because this corpus removes
source segmentation markers at S level while retaining them in W-level forms
for gloss alignment. No PHON or AUDIO tier is source-supplied or inferred.
