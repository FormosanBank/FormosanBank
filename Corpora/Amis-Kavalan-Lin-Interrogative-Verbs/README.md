# Lin Amis and Kavalan interrogative verbs

Dong-yi Lin (2015), “The syntactic derivations of interrogative verbs in Amis and Kavalan,” *New Advances in Formosan Linguistics*, pp. 253–289. [ANU source](https://hdl.handle.net/1885/14354).

**Status:** the source and build repairs are complete. Technical readiness remains blocked by evidence for the Amis source phonology described below. Do not treat the earlier readiness reports as approval.

## Source and coverage

The source PDF has 38 pages, including the final blank page, all reviewed against the transcription. SHA-256: `fb39fca379012a953ed21bc82d39c2545adc0227aa870a009841ed318aece28d`.

The committed [source table](CodeAndDocs/extracted_examples.tsv) records 96 Formosan occurrences: 49 Amis and 47 Kavalan. The [exclusion ledger](CodeAndDocs/excluded_source_units.tsv) accounts for 19 starred and two marginal occurrences under POL-016, plus 18 theory or other-language units. The 75 admitted occurrences include seven repeated reference examples, represented by 68 canonical identities. Eight optional forms expand under POL-026, yielding 76 S records, 38 per language. All 347 W and 506 M are retained. There is no audio.

Printed Amis 5b was missing from the old ledger; it remains excluded. Amis 6a and Kavalan 52a retain the source's translation parentheses. Footnote 6 explicitly corrects Amis 14a to “I will tenderise only the meat.” The source table retains the superseded body reading, which is no longer presented as an equal translation. Original sentence forms retain the constituent brackets in 59a/b and 60a/b; standard sentence forms omit them. The repeated 7a prints `just now`; canonical 2a retains its printed `just.now`.

Source W/M glosses, literal readings, infix gaps and the eight aligned optional expansions are preserved. Kavalan 41b retains the printed `<AV>take` gloss despite its “bite” translation. The source-to-S mapping is stored explicitly; spelling corrections do not renumber records. Historical page-review and alignment reports are retained as earlier evidence, including their now-corrected omissions.

## Orthography and open decision

The chapter identifies Central Amis from Changpin and Hsinshe Kavalan. Current FormosanBank aliases represent these as Xiuguluan and Kavalan. Madeline's August 13 review accepted the grammaticality repairs and W/M forms and requested standard FORM and PHON; her orthography comment was “I think Lin is using Ortho113.”

The existing [Amis profile](CodeAndDocs/Orthographies/LinAmis/Amis.tsv) and letter mapping are retained pending source evidence. They distinguish `q` from apostrophe but assign both printed `u` and `o` to `[o|u]`. Lin quotes Wu, whose phonetic key distinguishes those vowels, and also uses his own fieldwork. The available review does not explicitly approve this custom profile. A matching conversion-table result is not independent confirmation of its sounds. A source-backed profile or a specific maintainer ruling is required before a positive readiness verdict. Kavalan uses Ortho113.

## Rebuild and validate

Build from the committed transcription with current FormosanBank tools. No source download, private file, network request or old Git object is needed. Build provenance is recorded in [provenance.json](CodeAndDocs/provenance.json); it is not a tool pin.

```bash
FORMOSANBANK_ROOT=/path/to/FormosanBank PYTHON=/path/to/python3 \
  ./CodeAndDocs/generate_xml.sh

python3 -m unittest discover -s CodeAndDocs/tests -v

FORMOSANBANK_ROOT=/path/to/FormosanBank PYTHON=/path/to/python3 \
  QC_REPORT_DIR=/path/outside/the/corpus \
  ./CodeAndDocs/validate.sh
```

The entry point rebuilds `XML/`, applies any recorded manual edits, cleans, standardizes and adds phonology. Shared tools own standard FORM and PHON (POL-002/003). Validation is separate and runs every check even when one fails; inspect findings and actual reference coverage. It does not adjudicate warnings or declare readiness.

**POL-047 deviation:** after the shared derived-tier steps, `build_xml.py --restore-brackets` restores the four original S constituent brackets from the source table. The intermediate S forms omit these silent analysis markers, so the standard sentence and PHON tiers remain marker-free. Passing square brackets directly to the current phonology tool retains them as though they were IPA-alternative brackets. This final step changes only four original S forms, verifies their expected intermediate values, and leaves shared-generated tiers untouched.

## Rights

**Licence:** CC BY 4.0.

**Grantor and evidence:** the chapter's author copyright notice (2015) and the ANU volume's licence statement specify Creative Commons Attribution 4.0. The ANU evidence was recorded on January 28, 2025. The committed transcription and corpus may be redistributed with attribution under that licence; XML uses the exact vocabulary value. No audio is included. Source files and the preserved evidence screenshot are unnecessary for rebuilding the transcription.
