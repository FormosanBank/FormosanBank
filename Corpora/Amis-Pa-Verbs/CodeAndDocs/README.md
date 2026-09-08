# Source and conversion notes

`source_examples.tsv` is the build transcription with stable sentence/word IDs, segmented forms, aligned W glosses, translations and sentence endings. `source_coverage.tsv` accounts for all 13 PDF pages; `rejected_source_examples.tsv` records exclusions and `direct_source_checks.tsv` retains raw notation at the difficult cases. `build_xml.py` generates source tiers, shared tools own derived tiers, and `audit_source_alignment.py` only checks consistency against the transcription. The optional source PDF's identity is recorded in `source_manifest.tsv`; it is not fetched or required during builds.

## Preserved review and repairs

Madeline Boese's full-document review on 2026-08-07 corrected person/car scope in 20c/20d, added the `i/PREP` variant of 36a and excluded the questionable 38a-prime/38c-prime examples. Preserve those six decisions and the exact source `ni/GEN-NCM`, `ku/NOM-NCM`, `Pa-fli/give` pairs. Their three G001 findings are source-inherent and guarded by exact ID/count fixtures. PDF extraction also flags theory paragraphs as missing examples; its region counts are not a coverage verdict.

The September source review corrects July's reading of page 8 example 32c: `*(i)` means that `i` is obligatory (POL-017), so `i/PREP` is restored. New W `s32cwi` precedes the unchanged `s32cw4` and `s32cw5`; the printed `payau` remains. All 22 printed sentence endings are restored on S, including the two expanded readings; the seven unpunctuated source examples remain so. Sentence punctuation is not part of lexical W/M segmentation.

The source segments `Pa-fli` but supplies only W gloss `give`. August's internally segmented whole-word M was unsupported. Two unglossed M forms, `Pa` and `fli`, retain the actual boundary without inventing gloss alignment (POL-023/036). `morpheme_ids.tsv` maps the retired `s32aw0m0` to its two new parts. Source W/gloss and all free translations remain unchanged; V064/V065/G002 are reviewed consequences of missing individual source glosses.

The six manual records remain, with their four affected S endings corrected and their FILE path repaired to `Amis/pa-verbs.xml`. The former path silently skipped every record. Four replacement records are expected no-ops because the transcription includes them; the two deletions remain recorded. No records are pruned (POL-030).

The older April advice to remove analytic nulls from S predates POL-012 and its V125 specification. Preserve all seven ∅ units on S original and W/M; shared standardization removes them only from S standard. Whole-null PHON is ∅; a null within a word is silent. Source CaU remains alongside additive standard CAU.

## Orthography and conversion construction

Original PHON uses `source_orthography/Amis.tsv`: the current Coastal Ortho94 values, with Wu's explicit apostrophe /ʔ/ and q /ʡ/ spellings. Wu's [2006 dissertation](https://arts-sciences.buffalo.edu/content/dam/arts-sciences/linguistics/AlumniDissertations/Wu%20dissertation.pdf), printed xviii, gives that distinction and source `u/u`, `o/o` and `d/ɬ`; p.4 identifies the same Haian/Coastal Changpin variety. Dissertation example 5.27a, printed p.313, repeats the paper's 36a exactly, including `Ma-na’ay`. The earlier generic Ortho94 route incorrectly read its apostrophe as /ʡ/. The original source forms remain unchanged; standard `^` and both generated PHON tiers now represent /ʔ/ on the two sentence variants and their corresponding W/root M.

`wu_source_to_ortho113.tsv` retains `u→o` and maps source apostrophe to `^`, and q to standard apostrophe. No q or uppercase U occurs in the current source. All other Coastal source-profile values are unchanged. Standard PHON uses the registered Coastal Ortho113 profile, whose broader vowel/lateral classes differ from the source. The direct conversion validator still reports the source `u` versus target `[o|u]` mismatch and inventory/identity-route coverage limitations. These require review under the 2026-08-10 conversion-driver ruling; they are not malformed mappings or permission to broaden source phonemes to obtain PASS.

The former validation-only profile, which assigned target classes to the source without generating the corpus, remains removed. The new profile drives the actual shared generator and is justified by the source's explicit key and identical example, not by a cleaner validation result. Historical reports do not supply a current verdict. To verify a new acquisition, compare its SHA-256 with the source manifest and inspect the PDF before changing the transcription.

Public packaging copies `README.md`, all of `XML/`, and `CodeAndDocs/` except `history/`, `dorothy_lineage.md`, and caches. Those exclusions are development history, not required inputs; no XML is excluded. Copy files and executable modes unchanged. No public wrapper adaptation is needed.
