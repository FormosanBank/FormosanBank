# Safolu Amis dictionary

Safolu Kacaw Lalanges (Tsai Chung-Han) dictionary examples, distributed by
the g0v Amis Moedict project. Amis (`ami`), Coastal provenance; no source W/M
annotation or audio. Virginia Fey and Poinsot are separate corpora.

**Status:** blocked before QC. The source parser has been repaired, but final
XML remains the previous 49,179-record output until the orthography and source
decisions below are resolved. It is not ready to port.

[Basecamp card](https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/7112980917)
and [corpus PR #157](https://github.com/FormosanBank/FormosanBank/pull/157).

## Source and coverage

[The source manifest](CodeAndDocs/source_manifest.json) identifies the pinned
`g0v/amis-moedict` `docs/s` input: 42,273 lexical files, 57,361 definitions and
49,419 example fields. The committed compressed snapshot retains each complete
raw example, definition, title and stable source locator. Headwords and
definitions provide context; embedded examples are included, with no invented
word segmentation or glosses.

The revised parser emits 49,455 records before shared dedup, accounting for all
49,419 source fields with 20 excluded fields. The 76 exact-field overrides
retain prior corrections and document the new source-backed repairs. Published
expansion IDs remain fixed; new readings keep the base ID and add `-opt`,
`-opt3`, etc. The former FORM-only merger is removed: equal forms with different
meanings must survive current shared dedup.

The historical ledgers in `data/formosanbank_audit/` are retained as evidence of
the previous output and issue review. They are not current audit verdicts.
See [source review](SOURCE_AUDIT.md) and [dialect evidence](docs/dialect_evidence.md).

## Reproduction

The single build entry point uses committed inputs and the surrounding
FormosanBank tools. Its [provenance record](CodeAndDocs/provenance.json)
currently describes the retained historical XML, whose old build was reproduced
byte for byte. Provenance does not select or pin the tools used for a new build.

```sh
PYTHON=python3 CodeAndDocs/generate_xml.sh /path/to/current/FormosanBank
```

Generation, shared cleaning, standardization and PHON run in temporary staging;
only a completed build installs XML and provenance. Current main lacks the
Safolu profile and conversion table, so the build reports that dependency before
changing the retained XML. Do not substitute an unrelated profile.

**POL-047 deviation:** shared dictionary dedup runs after derived tiers.
Validation and source refresh run separately from generation.

Source parsing can be investigated independently, using an external staging
directory; this is not a final corpus build or QC clearance:

```sh
python3 CodeAndDocs/generate_xml.py --xml-out-dir /tmp/safolu-review/XML \
  --report-dir /tmp/safolu-review
FORMOSANBANK_ROOT=/path/to/current/FormosanBank python3 -m unittest discover -s tests -v
```

To refresh the source deliberately, run
`python3 CodeAndDocs/source_snapshot.py /path/to/clean/amis-moedict` and review
the new manifest and all source changes. Generation never fetches a source or
reads a private clone. Run the installed corpus audit and QC workflow after
the outstanding decisions are resolved; the old count-based acceptance scripts
have been retired.

## Rights

**License:** unresolved; the existing XML copyright prose is retained.

**Rights source:** Safolu Kacaw Lalanges, date unconfirmed; evidence: ask maintainer.

The frozen upstream README says the author allowed g0v Amis Moedict to use the
dictionary under CC BY-NC, without a verified version/date. This does not justify
choosing a vocabulary value by assumption. The XML and companion GitBook rights
claim need an explicit maintainer review before publication (POL-042 through POL-045).

## Audio

None.

## Notes and Issues

- The Safolu PHON profile and conversion table remain unmerged shared inputs.
  Current conversion checking reports an unresolved `u → o` mapping and `d`/`o`
  routing questions. Preserve the source's distinct vowel spellings and mixed
  `g`/`ng`; see [orthography evidence](docs/orthography_evidence.md).
- Forty-two original-FORM parenthesis/slash cases still need source-specific
  interpretation. The revised parser resolves only directly supported cases,
  including the explicit pronunciation examples in the `e` and `i` entries.
- S37193's published Chinese correction was inferred from its sentence and
  definition; an authoritative reading is still needed. It is preserved pending
  review. Source field 35128 still contains unexplained `久` on the publisher's
  page and remains outside released XML.
- The source history includes both PDF-to-TXT and DOCX conversion. A clean JSON
  file does not establish that it is free of earlier extraction errors.
