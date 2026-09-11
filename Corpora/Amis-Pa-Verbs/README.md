# Wu (2006) Amis pa-verbs

Coastal Amis (`ami`) sentence examples from Joy Wu's [The Analysis of Pa-Verbs in Amis](https://sil-philippines-languages.org/ical/papers/wu_joy-pa%20verbs.pdf), presented at the Tenth International Conference on Austronesian Linguistics, 17–20 January 2006. Page 1 identifies Haian/Coastal Amis from Changpin, Taitung.

The inventory covers sentence examples on pages 6–10 of the 13-page paper. It retains 29 grammatical sentence variants, including both person/car readings of 20c and both case forms of 36a. The 15 exclusion entries identify two repeated earlier examples, seven ungrammatical examples, three forbidden alternatives, one starred translation and two questionable examples. Lexical tables, theory prose and references are accounted for separately in the page ledger, not claimed as sentence records.

Final XML has 29 S, 154 W, 265 M, 448 original and 448 standard FORM/PHON parents, and no audio. `TEXT/@source` carries the paper's URL and the SHA-256 of the PDF it was transcribed from. The source transcriptions, exclusions and page coverage are under `CodeAndDocs/`.

## Rights

**License:** CC BY-NC-SA 4.0

**Rights source:** SIL International, 2025-01-25; evidence: ask maintainer

The date records the maintainer's verification of SIL's published archive terms, including the retained January 24 screenshot. Those terms apply unless an item states otherwise; this paper contains no conflicting grant. Credit Joy Wu and SIL International, retain the noncommercial/share-alike conditions, and identify the transcription and normalization changes. The optional PDF verification copy is not a required build input.

## Audio

The source paper supplies no audio.

## Notes and Issues

The paper segments `Pa-fli` but gives only the whole-word gloss `give`. Its two morphemes therefore have no individual glosses. Other source form/gloss mismatches and analytic nulls are preserved; the source notes explain the reviewed cases.

Original and standard PHON use different inventories, including the source's narrower vowel and lateral values. The conversion report records these differences; the tiers do not imply strict phonemic equivalence. In particular the `standard` tier merges Wu's `u`/`o` distinction, because Ortho113 Coastal writes one `o` for /o~u/; the `original` tier keeps the distinction.

Wu prints example 36a in two case forms. They are two `S` blocks, `s36a` and `s36a-opt`, because the alternation is a competing lexeme with a different gloss (`t-u`/DAT-NCM against `i`/PREP) rather than a spelling variant (POL-027/POL-028).

This corpus has its own build test suite at [`CodeAndDocs/tests/`](CodeAndDocs/tests/), which pins the reviewed source decisions — exact sentence and morpheme ids, counts, the unglossed `Pa-fli` boundary, and the retained exclusions — so a change to the shared tools or to the transcription cannot silently move them. Run it with `python -m pytest Corpora/Amis-Pa-Verbs/CodeAndDocs/tests`; `CodeAndDocs/validate.sh` also runs it as its `source-tests` check. **It is not collected by the repository's own `pytest` run**, whose `testpaths` is `tests/`, so it does not gate CI.

## Reproduce

With FormosanBank's documented Python dependencies installed:

```bash
bash Corpora/Amis-Pa-Verbs/CodeAndDocs/generate_xml.sh
```

In the development repository, set `FORMOSANBANK_ROOT` to the selected current FormosanBank checkout and run `bash CodeAndDocs/generate_xml.sh`. `PYTHON` selects the interpreter. The build reads committed tables, cleans, standardizes `u` to `o` and source apostrophe to `^`, and generates PHON using shared tools. It needs no PDF, network, Git metadata or historical tool checkout. Record the actual tools used for committed output in [provenance.json](CodeAndDocs/provenance.json); this record does not select or gate tools — the build always runs the tools in the checkout it is invoked from (POL-052).

Original PHON uses [`Orthographies/Wu/Amis.tsv`](../../Orthographies/Wu/Amis.tsv) — Coastal Ortho94 values with Wu's explicit apostrophe /ʔ/ and q /ʡ/ spellings — and converts through [`Orthographies/ConversionTables/Amis_Wu_113.tsv`](../../Orthographies/ConversionTables/Amis_Wu_113.tsv); standard PHON uses the registered Ortho113 Coastal profile. Their phoneme inventories differ. [Source and conversion notes](CodeAndDocs/README.md) explain the reported differences without claiming strict phonemic equivalence or changing originals to satisfy a validator.

For read-only validation, run `QC_REPORT_DIR=/outside/corpus/reports bash CodeAndDocs/validate.sh` with the same environment. The conversion comparison reports a reviewed phoneme-level mismatch and therefore returns a nonzero command status. Review every report; script success alone cannot establish readiness. Source refresh and human source review remain separate from generation.
