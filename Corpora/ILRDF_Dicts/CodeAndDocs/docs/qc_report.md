# QC report: Formosan-ILRDF_Dicts

- QC date: 2026-08-21
- Basecamp card: `7469488230`
- GitHub issue reviewed: `7`
- Authority commit: `3a3c47c220520113f747e6a2d441494000e13c4b`
- Canonical XML path: `XML/`
- Private technical verdict: `ready to port`

## Final inventory

| Metric | Count |
|---|---:|
| Source language snapshots | 16 |
| Successful headword queries | 139,363 |
| XML files | 16 |
| Sentences | 167,821 |
| Original FORM tiers | 167,821 |
| Standard FORM tiers | 167,821 |
| Standard PHON tiers | 167,821 |
| Original PHON tiers | 0, not applicable |
| Translations | 169,946 |
| Sentences with multiple translations | 2,056 |
| Sentences without a usable translation | 3 |
| Linked audio records | 132,402 |
| Sentences with multiple audio records | 15,064 |
| Standard PHON rows with visible wildcard limitations | 675 |

The source provides sentence examples, translations, and linked audio, but no
word or morpheme gloss analysis. W/M tiers are therefore not applicable.

## Source and reproduction evidence

1. The source boundary is 16 deterministic gzip JSON snapshots from the
   official ILRDF dictionary API. The capture completed every enumerated
   headword query with zero failures. SHA-256 hashes for both compressed and
   uncompressed content are recorded in `source_data/source_manifest.json`.
2. `refresh_source.py` can refresh one or all language snapshots. It aborts a
   language if any query fails and updates files atomically.
3. `reproduce.sh` verifies the pinned authority commit, regenerates XML from
   the snapshots, applies current standardization and phonology, restores all
   source-owned tiers, and runs a fail-closed source audit.
4. Two complete rebuilds produced byte-identical XML. The combined XML digest
   manifest was `e6ac1db8c552b292302b0701da72b5c26344b319dc3ef4c9788f82c53ae73487`.
5. The source audit confirmed all 16 committed XML files have the expected root
   metadata, sentence IDs, original FORM, TRANSL, and AUDIO content.

## Remediation

1. Replaced legacy Pickle-only scraping with committed, hashed API snapshots
   and a deterministic generator.
2. Migrated generated output from legacy `Final_XML/` to canonical `XML/` and
   removed obsolete generated files, local source PDFs, caches, audio helper
   scripts, and historical logs.
3. Preserved every distinct source sentence, translation, and trusted audio
   link when the same example occurs under multiple dictionary headwords.
4. Replaced sequential IDs with stable IDs derived from language and normalized
   source FORM content.
5. Applied only Unicode, invisible-character, spacing, and current quote
   normalization to source FORM. Source translation text is preserved apart
   from Unicode normalization, outer and line-final layout whitespace, and
   invisible characters.
6. Recovered 97 occurrences of source-side `?` corruption only where replacing
   it with `ʉ` or `ɨ` produced a token attested intact in the same language
   snapshot. Twenty-four source strings in the three affected languages remain
   visibly unresolved because no safe same-snapshot attestation exists.
7. Corrected translation language metadata documented in GitHub issue 7:
   English targets are `eng`, copied source-language targets use that language,
   the Rukai target is `dru`, and the Kavalan personal-name-only target is
   `zxx`. No `zho` translation lacks Han text in the final XML.
8. Excluded three Kanakanavu lesson numbers from TRANSL while preserving their
   source FORM and audio. These are the only sentences without a usable
   translation.
9. Suppressed 820 all-zero source audio IDs, two human-confirmed transcript
   mismatches, and both uses of 40 audio IDs assigned to different forms in
   different languages. Every retained audio URL has exactly one sentence-form
   owner.
10. Removed the unsupported `CC-BY-NC` claim and recorded the current rights
    evidence in `source_data/RIGHTS.md`.

## Current checks

| Check | Result |
|---|---|
| Repository tests | PASS, 9 tests |
| Ruff | PASS |
| Deterministic rebuild | PASS, two byte-identical full passes |
| Source audit | PASS, 16 files |
| XML validator against an empty replacement target | PASS, 0 findings |
| XML validator against published corpora | Replacement-only, 16 V081 root ID collisions with existing `Corpora/ILRDF_Dicts` paths |
| Text validator | PASS, 0 HARD; 25,368 source-content SOFT findings |
| Dialect validator | PASS, 16 files use registered `unknown`; sentence-level varieties are absent from the aggregated source |
| Duplicate diagnostic, original FORM | PASS, 0 within-file and 84 cross-file SOFT groups |
| Duplicate diagnostic, standard FORM | PASS, 4 within-file and 84 cross-file SOFT groups |
| Gloss scrape audit | N/A for gloss alignment, 0 HARD; 380 source-owned trailing-parenthetical TRANSL notices |
| Gloss validator | N/A, 167,821 V060 notices because the source has no W/M tiers |
| Audio ownership audit | PASS, 132,402 unique URLs and 0 cross-form collisions |
| Port readiness | PASS, 0 HARD; expected P005 warning until post-port audio statistics exist |

The text findings are V111 1, V112 25, V113 5, V116 231, V122 20,992,
V133 3,882, V134 4, and V137 228. They are visible source-owned punctuation,
alternatives, numbering, mixed-script, and lexical content. The 675 wildcard
PHON rows likewise preserve visible source graphemes or non-Formosan material
that the current phonology tables do not map.

The four within-file standard-tier duplicate groups are source-distinct FORM
pairs whose apostrophe or glottal glyph distinctions converge under current
standardization. The original tier has no within-file duplicate group, so the
source records remain distinct.

## Publication gate

The ILRDF copyright notice does not grant a Creative Commons license. It says
site content is protected and that permission or authorization is required
outside applicable reasonable use. On 2026-08-23, the FormosanBank maintainer
authorized publication of this existing ILRDF corpus update in the public
FormosanBank repository. That project authorization does not relicense the
source content or change downstream obligations under the source terms.

## Verdict

`ready to port`
