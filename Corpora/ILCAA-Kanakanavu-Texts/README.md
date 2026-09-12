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
constructions, six use W/M FORM variants and 18 retain separate S readings,
producing 1,449 source-stage S records. The 45 retained final XML files still
have 1,455 S records and await regeneration.
Unnumbered introduction forms, comparison tables and footnote lexical material
still need coverage review. The numbered-unit count is not a whole-book verdict.
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
deduplication is not a build step. Current main lacks the shared Asai2026 source
profile and conversion table, so generation stops before changing XML.

The [provenance record](CodeAndDocs/provenance.json) describes the retained
historical XML. It does not select or pin tools for a new build. The previous
private phonology override and count-based QC acceptance wrapper are retired.
The tables under `CodeAndDocs/scripts/orthographies/` retain the earlier
reviewed mapping as evidence; generation does not load them.

For source investigation without producing final derived tiers:

```sh
python3 CodeAndDocs/scripts/pipeline.py --workspace /tmp/kanakanavu-review
python3 CodeAndDocs/scripts/source_xml_audit.py --workspace /tmp/kanakanavu-review \
  --xml /tmp/kanakanavu-review/build/xml_drafts/Kanakanavu
KANAKANAVU_WORKSPACE=/tmp/kanakanavu-review python3 -m pytest -q
```

The comparison checks extracted text, source sidecars and the selected XML,
including W/M FORM variants. Source-only output has no derived tiers, so the
report still fails its completeness checks. It never certifies a visual review.
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

- The Asai2026 profile, conversion and reviewed conditioned phonology need a
  shared implementation reviewed separately from this corpus (POL-049).
- The source parser resolves six spelling variants and the old V1/V2 IDs.
  Four parenthetical classifications still need resolution under POL-028.
  Clause brackets remain at S; the shared PHON step must handle them as
  analytical notation.
- Unnumbered lexical material uses several source orthographies. Its coverage
  and routing must be resolved without applying the narrative profile blindly.
- The earlier ten-page expert review and historical samples cover those records
  only. They do not establish a current visual review of every page or reading.
