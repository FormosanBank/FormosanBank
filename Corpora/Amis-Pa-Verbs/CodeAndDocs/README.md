# Source and conversion notes

`source_examples.tsv` is the build transcription with stable sentence/word IDs, segmented forms, aligned W glosses, translations and sentence endings. `source_coverage.tsv` accounts for all 13 PDF pages; `rejected_source_examples.tsv` records exclusions and `direct_source_checks.tsv` retains raw notation at the difficult cases. `build_xml.py` generates source tiers, shared tools own derived tiers, and `audit_source_alignment.py` only checks consistency against the transcription. The optional source PDF's identity is recorded in `source_manifest.tsv`; it is not fetched or required during builds.

## Preserved review and repairs

Madeline Boese's full-document review on 2026-08-07 corrected person/car scope in 20c/20d, added the `i/PREP` variant of 36a and excluded the questionable 38a-prime/38c-prime examples. Preserve those six decisions and the exact source `ni/GEN-NCM`, `ku/NOM-NCM`, `Pa-fli/give` pairs. Their three G001 findings are source-inherent and guarded by exact ID/count fixtures. PDF extraction also flags theory paragraphs as missing examples; its region counts are not a coverage verdict.

The September source review corrects July's reading of page 8 example 32c: `*(i)` means that `i` is obligatory (POL-017), so `i/PREP` is restored. New W `s32cwi` precedes the unchanged `s32cw4` and `s32cw5`; the printed `payau` remains. All 22 printed sentence endings are restored on S, including the two expanded readings; the seven unpunctuated source examples remain so. Sentence punctuation is not part of lexical W/M segmentation.

The source segments `Pa-fli` but supplies only W gloss `give`. August's internally segmented whole-word M was unsupported. Two unglossed M forms, `Pa` and `fli`, retain the actual boundary without inventing gloss alignment (POL-023/036). `morpheme_ids.tsv` maps the retired `s32aw0m0` to its two new parts. Source W/gloss and all free translations remain unchanged; V064/V065/G002 are reviewed consequences of missing individual source glosses.

The six manual records remain, with their four affected S endings corrected and their FILE path repaired to `Amis/pa-verbs.xml`. The former path silently skipped every record. Four replacement records are expected no-ops because the transcription includes them; the two deletions remain recorded. No records are pruned (POL-030).

The older April advice to remove analytic nulls from S predates POL-012 and its V125 specification. Preserve all seven ∅ units on S original and W/M; shared standardization removes them only from S standard. Whole-null PHON is ∅; a null within a word is silent. Source CaU remains alongside additive standard CAU.

## Orthography and conversion construction

Original PHON continues to use `Orthographies/Ortho94/Amis.tsv`, Coastal. Wu's [2006 dissertation](https://arts-sciences.buffalo.edu/content/dam/arts-sciences/linguistics/AlumniDissertations/Wu%20dissertation.pdf), printed xviii, documents source `u/u`, `o/o` and `d/ɬ`; p. 4 identifies the same Haian/Coastal Changpin variety. This supports the existing source distinctions. The old validation-only profile instead assigned the target's broader values to the source and falsely described the mapping as loss-free; it has been removed.

`wu_source_to_ortho113.tsv` retains the existing single `u→o` spelling conversion. Validate it against the actual Ortho94 source profile and Ortho113 Coastal target. The direct validator reports `u/[o|u]` mismatch, missing explicit routes for unchanged `d` and `o`, and target-only `:`/`[ɬ|ɮ]` coverage. Unlisted letters pass through unchanged; the corpus has no colon. These are reviewed phoneme-inventory/identity-route limitations, not missing profiles, malformed mappings, or a claim that the source used every target phoneme. Original PHON preserves the source distinctions; standard PHON reflects the broader current registered classes. Per the 2026-08-10 ruling documented in `QC/validation/run_conversion_table_checks.py`, phoneme-level reports require this review and do not imply a structural conversion failure. Do not alter a profile or invent source phonemes merely to produce PASS.

The build uses the single lowercase `u` mapping; no uppercase U occurs in the source. The shared case-variant notice is therefore reviewed, not hidden. To verify a new source acquisition, compare its SHA-256 with the manifest and inspect the PDF before changing the transcription. Historical development reports do not supply a current verdict.

Public packaging copies `README.md`, all of `XML/`, and `CodeAndDocs/` except `history/`, `dorothy_lineage.md`, and caches. Those exclusions are development history, not required inputs; no XML is excluded. Copy files and executable modes unchanged. No public wrapper adaptation is needed.
