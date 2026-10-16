# Kanakanavu Texts

Asai, Mei, Li and Tsuchida (2026), *Kanakanavu texts*, edited by Paul Jen-kuei
Li and published by ILCAA, Tokyo University of Foreign Studies.

**Status:** needs remediation before QC. The retained XML is the previous
1,455-sentence output, moved into `XML/Kanakanavu/` without changing its bytes.
Passing the source comparison or regression tests does not establish readiness.

[Basecamp card](https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/10012922283),
[corpus PR #155](https://github.com/FormosanBank/FormosanBank/pull/155),
and [GitBook PR #51](https://github.com/FormosanBank/FormosanBankGitbook/pull/51).

## Source and coverage

The committed [252-page PDF](CodeAndDocs/data/raw/pdf/B602_KanakanavuText.pdf)
has SHA-256 `785058bad6a8495f8b5fb51ed3d0eaf7da1736e791b308611d9442c010d93c03`.
The parser accounts for 44 narratives and 40 numbered introduction examples
(48 introduction units), totalling 1,431 source units. Of 24 parenthetical
constructions, eight use W/M FORM variants and 16 retain separate S readings,
producing 1,447 numbered-example S records. Another source file contains 57
lexical records from 49 explanatory footnotes. Introduction tables/prose and
the title linked to footnote 29 add 101 S, for 1,605 source-stage S records.
The 45 retained final XML files still have 1,455 S and await regeneration.
The [footnote ledger](CodeAndDocs/footnote_lexemes.jsonl) accounts for all 87
notes. The [introduction ledger](CodeAndDocs/introduction_lexemes.json) keeps
historical transcription columns and the Saaroa comparison in separate files.
It records bound morphology/templates as context and the unresolved village
phonetics explicitly. The printed /kaɨnɨ/ and [kɅɨnɨ] pair keeps its source
FORM and source-supplied PHON separately. Tsuchida's source distinguishes the two vocatives
from ordinary pronouns; all four forms keep separate records. These counts are
not a whole-book coverage verdict.
The source parser repairs a misplaced interjection gloss in Naparamaci example
68, omits empty gloss padding, restores the aligned W/M tiers of introduction
examples 23a-d and separates eight stacked infix pairs. Final XML awaits the
shared build below.

Source W/M glosses and free translations remain separate. Source narrative
repetitions, publisher corrections, Japanese name characters, and meaningful
translation parentheses are preserved. See [source decisions](CodeAndDocs/source-decisions.md).

## Reproduction

Install [the declared dependencies](CodeAndDocs/requirements.txt). The executable
entry point reads committed inputs and uses the supplied current FormosanBank
checkout, or the containing checkout when this package is under `Corpora/`:

```sh
python3 -m pip install -r CodeAndDocs/requirements.txt
PYTHON=python3 CodeAndDocs/generate_xml.sh /path/to/current/FormosanBank
```

The build stages source extraction, shared cleaning, standardization and PHON,
then installs successful output. It performs no QC or source refresh. Narrative
deduplication is not a build step. Generation stops before changing XML until
the remaining Szakos group has a supported conversion route for ö.

The [provenance record](CodeAndDocs/provenance.json) describes the retained
historical XML. It does not select or pin tools for a new build. The previous
private phonology override and count-based QC acceptance wrapper are retired.
The entry point passes the committed narrative, Table 1 and Saaroa tables
under `CodeAndDocs/scripts/orthographies/` directly to the shared tools, with
separate file/language routing. Table 1's Tsuchida 1969 and 2007 vocabulary
columns map source ɨ/ʉ to standard ʉ, preserving their historical forms.
Table 2's 16 pronouns use the narrative route's reviewed subset. Shared PHON
preserves the one explicit source transcription and derives all other PHON.
These tables need no installation in FormosanBank.

For source investigation without producing final derived tiers:

```sh
python3 CodeAndDocs/scripts/pipeline.py --workspace /tmp/kanakanavu-review
python3 CodeAndDocs/scripts/source_xml_audit.py --workspace /tmp/kanakanavu-review \
  --xml /tmp/kanakanavu-review/build/xml_drafts
KANAKANAVU_WORKSPACE=/tmp/kanakanavu-review python3 -m pytest -q
```

The comparison checks extracted text, source sidecars and the selected XML,
including W/M FORM variants and supplemental forms, meanings and context. Source-only
output has no derived tiers, so the report still fails its completeness checks.
It never certifies a visual review.
Use the installed gloss audit, corpus audit
and current QC workflow after the outstanding source and tool work is resolved.

## Rights

**License:** CC BY 4.0, stated on source PDF physical page 3.

**Rights source:** Paul Jen-kuei Li, Yi-Chun Chen, Hsiu-min Huang and Amy
Ming-luan Chen, 2026; exact grant date not stated; evidence: ask maintainer.

The source PDF may be redistributed under that licence with attribution.
Source generation writes the canonical licence value `CC BY 4.0` (POL-042),
with attribution retained here. The retained XML still carries its old
copyright prose and awaits final regeneration.

## Audio

None supplied with this source.

## Notes and Issues

- Standard PHON follows Ortho113 (POL-003). The source's conditioned c/s
  pronunciation stays in original PHON; the former private standard override
  is retired. The two tiers therefore differ in those environments.
- The source parser resolves eight spelling/pronunciation variants and the old
  V1/V2 IDs. Tsuchida's notation key resolves ha/sua in two passages;
  two parenthetical classifications still need resolution under POL-028.
  Clause grouping stays at S; shared cleaning normalizes its brackets to
  parentheses and PHON omits them. These clauses are not optional material.
- Introduction lexical material has seven transcription groups, including Saaroa
  and the explicit phonemic/phonetic pair. Szakos ö still needs a supported sound
  mapping. Table 2's 16 pronouns have a
  verified segmental route; their stress marks remain in original FORM.
  The Saaroa comparison has a
  source-backed `ɫ` -> `hl` conversion and the corrected Saaroa code `sxr`,
  separate from the narrative profile.
  The village-labelled phonetic comparison remains open in the ledger.
  Supplemental records preserve printed readings; only three analyzed prose
  examples supply W/M tiers. They remain source-stage output pending the full build.
- The earlier ten-page expert review and historical samples cover those records
  only. They do not establish a current visual review of every page or reading.
