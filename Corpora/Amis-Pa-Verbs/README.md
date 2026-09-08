# Wu (2006) Amis pa-verbs

Coastal Amis (`ami`) sentence examples from Joy Wu's [The Analysis of Pa-Verbs in Amis](https://sil-philippines-languages.org/ical/papers/wu_joy-pa%20verbs.pdf), presented at the Tenth International Conference on Austronesian Linguistics, 17–20 January 2006. Page 1 identifies Haian/Coastal Amis from Changpin, Taitung.

The inventory covers sentence examples on pages 6–10 of the 13-page paper. It retains 29 grammatical sentence variants, including both person/car readings of 20c and both case forms of 36a. The 15 exclusion entries identify two repeated earlier examples, seven ungrammatical examples, three forbidden alternatives, one starred translation and two questionable examples. Lexical tables, theory prose and references are accounted for separately in the page ledger, not claimed as sentence records.

Final XML has 29 S, 154 W, 265 M, 448 original and 448 standard FORM/PHON parents, and no audio. The source transcriptions, exclusions and page coverage are under `CodeAndDocs/`. All sentence IDs and existing word associations survive the repair.

## Rights

**License:** CC BY-NC-SA 4.0

**Rights source:** SIL International, 2025-01-25; evidence: ask maintainer

The date records the maintainer's verification of SIL's published archive terms, including the retained January 24 screenshot. Those terms apply unless an item states otherwise; this paper contains no conflicting grant. Credit Joy Wu and SIL International, retain the noncommercial/share-alike conditions, and identify the transcription and normalization changes. The optional PDF verification copy is not a required build input.

## Reproduce

With FormosanBank's documented Python dependencies installed:

```bash
bash Corpora/Amis-Pa-Verbs/CodeAndDocs/generate_xml.sh
```

In the development repository, set `FORMOSANBANK_ROOT` to the selected current FormosanBank checkout and run `bash CodeAndDocs/generate_xml.sh`. `PYTHON` selects the interpreter. The build reads committed tables, applies the six retained correction records, cleans, standardizes `u` to `o` and source apostrophe to `^`, and generates PHON using shared tools. It needs no PDF, network, Git metadata or historical tool checkout. Record the actual tools used for committed output in [provenance.json](CodeAndDocs/provenance.json); this record does not select or gate tools.

Original PHON uses Coastal Ortho94 values with Wu's explicit apostrophe /ʔ/ and q /ʡ/ spellings; standard PHON uses the registered Ortho113 Coastal profile. Their phoneme inventories differ. [Source and conversion notes](CodeAndDocs/README.md) explain the reported differences without claiming strict phonemic equivalence or changing originals to satisfy a validator.

For read-only validation, run `QC_REPORT_DIR=/outside/corpus/reports bash CodeAndDocs/validate.sh` with the same environment. The conversion comparison reports a reviewed phoneme-level mismatch and therefore returns a nonzero command status. Review every report; script success alone cannot establish readiness. Source refresh and human source review remain separate from generation.
