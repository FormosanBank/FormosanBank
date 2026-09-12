# Current reproduction evidence

The readiness rebuild on 2026-08-22 used the clean FormosanBank authority at
`3a3c47c220520113f747e6a2d441494000e13c4b` through an explicit
`FORMOSANBANK_PATH`. The pipeline regenerated the dictionary and interlinear
ledgers, then rebuilt both canonical `XML/` files with the current cleaning,
standardization, and shared Ortho113 phonology tools.

The rebuild applied 128 exact direct-sentence decisions and two exact
analysis-tier decisions, emitted 114 retained split variants after removing 26
cross-record duplicates, omitted 11 unsupported bound citation forms, and
preserved the source stress only in original FORM tiers. Two source analytic
translation parentheticals were moved from primary text to `TRANSL/@notes`
under POL-024.

| Artifact | SHA-256 |
| --- | --- |
| Grammar XML | `d65875e63f85abae0e74b2e0c98998760881e5f5223768e0bfb37f507ef9fc72` |
| Dictionary XML | `c5926593971fbbbd4df7f9d88c1629400ef2f7390797b5e932f6709da5736750` |
| Interlinear ledger | `edb604881218eaaa21a69df58762aca3c8478aa554f3f6ef32d59fa16a2a4799` |
| Source ledger | `92ba3601407427cf827076e90286891724235c6e71281499de4f4610159f771b` |
| Exact decision manifest | `1e30387a07b771b8e758b567de3345accd144642a7b201fe5c7a53089359c1ca` |

Two consecutive complete rebuilds produced the same two XML hashes and
interlinear-ledger hash above. All 21
regression tests passed. The current XML validator reported no findings against
an update view that excludes only the existing intended target
`Song-Kanakanavu-Grammar`. Text and gloss validation reported no HARD findings.
The remaining SOFT findings were reviewed as follows:

- V060 (1,296): all 870 dictionary entries intentionally have no W tier, and 426
  grammar analyses differ from the natural sentence surface in source-printed
  spacing or clitic attachment. The source does not supply dictionary analyses,
  and both printed grammar tiers are preserved.
- V061 (3): pages 68, 128, and 248 print segmented forms with an unsegmented or
  only partially aligned gloss. No segmentation or gloss was invented.
- V064 (4): pages 182, 248, and 258 omit a separately aligned gloss for those M
  units. Their W glosses remain complete.
- V122 (4 rows for one S): S0456 is a complete translated prose parenthetical,
  not optional material. Both variants of the source sentence are not implied.
- V133 (2): S0469 and S0472 use the source-defined break-punctuation dash. Each
  exact decision is recorded in `intermediate/standard_surface_decisions.tsv`.

The source PDF is image-only, so the generic gloss-scrape source extractor
reported zero matchable lines. Direct image checks confirm the 26 G001 and 22
G002 cases are printed form/gloss segmentation mismatches, not extraction
changes. G004 is zero after the POL-014/POL-015 repair. G003 is also zero with
the current shared rule, which accepts a hyphenated M root only when that exact
spelling is derived from its parent W's inline infix. The earlier authority
reported 113 false positives on these required gap roots. The single G005 `RA`
label is printed verbatim on reader page 165. These specialized findings are
triage signals and do not override the canonical validator results.

The Basecamp evidence records the author's permission to publish this corpus
under CC BY-NC 4.0.
