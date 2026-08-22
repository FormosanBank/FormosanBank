# Li (2014), *Conjunction in Thao*

This corpus contains all 24 numbered Thao examples and three additional Thao examples from footnote 7 in Paul Jen-Kuei Li's *Conjunction in Thao*.

- Language and dialect: Thao (`ssf`, `dialect="Thao"`)
- Source pages: PDF pages 394-402, printed pages 401-409
- Contents: 27 S, 211 W, and 309 M elements
- License: Creative Commons Attribution 4.0 International (CC BY 4.0)
- Official source: [ANU Open Research](https://openresearch-repository.anu.edu.au/items/8bfb8bf0-2f58-4eae-947c-bf9af50faf9f)

The corpus is also subject to the central terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md).

## Source fidelity

The reviewed records preserve the printed source. This includes the printed `S` in `ɬpaðiSan`, six printed `D` characters in the footnote examples, and the printed English strings `firewoodon`, `erson`, and `wildanimals`. These are not silently corrected in original FORM, translations, or glosses.

Examples 1-24 have aligned W and M analysis. Every W in those parsed examples has at least one M child, including a single M for source-supported monomorphemic words. The three footnote examples have no printed gloss line and remain sentence-only.

The standard tier is generated through the reviewed source-specific Li 2014 to Ortho113 conversion table. Its 12 mappings pass the current transitive conversion validator with no mismatches, warnings, or coverage gaps. Sentence-level hyphen and equals-sign segmentation is removed by the shared standardizer. Source infix brackets remain where the standardizer preserves them, and the W and M tiers retain the source analysis.

Only safe standard PHON is generated. The generic Li profile cannot represent the source's stress-marked vowels and interprets the printed capitals as ordinary `s` and `d`. A reviewed probe produced 30 placeholders across 26 original PHON tiers plus incorrect S and D readings, so original PHON is deliberately omitted.

## Public reproduction data

Everything needed to recreate the published XML is under `CodeAndDocs/`:

- `data/reviewed_examples.tsv` contains the 27 page-addressed source records.
- `data/source_ledger.csv` accounts for all 27 retained records and four page-level exclusions.
- `data/source_manifest.json` pins the official PDF by URL, size, page count, and SHA-256.
- `data/orthographies/` contains the reviewed source orthography and conversion table.
- `scripts/build_xml.py` creates raw original tiers and the complete W and M structure.
- `scripts/audit_source_fidelity.py` verifies the official PDF, source literals, ledger, IDs, tier counts, and generated forms.

Private review workflow metadata is not part of the public reproduction package.

## Reproduce

From this corpus directory, download the official source and run the build with a current FormosanBank Python environment:

```bash
./CodeAndDocs/download_source_data.sh
PYTHON=/path/to/FormosanBank/.venv/bin/python ./CodeAndDocs/make_xml.sh
```

You can instead set `SOURCE_PDF=/absolute/path/to/Papers-from-12-ICAL-Volume-2.pdf`. Set `FORMOSANBANK_ROOT=/path/to/FormosanBank` only when the corpus is being rebuilt outside its containing FormosanBank checkout.

The build verifies that the checkout contains the pinned authority revision, checks the official PDF and full coverage ledger, requires shared cleaning to be a source-preserving no-op, validates the 12-row conversion, creates standard FORM and standard PHON with shared utilities, reruns source checks, and requires the published XML SHA-256. Repeated builds are byte-identical.

## Validation status

The 2026-08-22 current-authority review passed the nine-page source audit, nine development tests, Ruff, XML, text, gloss, gloss-scrape, duplicate, dialect, conversion, orthography, vocabulary, registry, phonology-probe, and port-readiness checks. All 139 expected findings were source-adjudicated with none unresolved. Port readiness reported 0 hard findings and 0 warnings.

This replacement completes the source-supported M-tier work tracked in [issue #102](https://github.com/FormosanBank/FormosanBank/issues/102). No unprinted morphological analysis was invented.

## Citation

Li, P. J.-K. 2014. Conjunction in Thao. In I Wayan Arka and N. L. K. Mas Indrawati, editors, *Papers from 12-ICAL, Volume 2: Argument Realisations and Related Constructions in Austronesian Languages*, pages 401-409. Asia-Pacific Linguistics.
