# NTU Corpus of Formosan Languages

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

***

## Notes

### Public audio

Run `./download_audio_data.sh` from this corpus directory to download the
public Grammar and Stories datasets from Hugging Face. The download is pinned
by the repository-level `audio_sources.json` contract and does not require a
Hugging Face account.

The Grammar source currently has 3,754 usable recordings. One Seediq URL was
corrected to the filename that is actually published by NTU. Two source URLs
return 404 and one returns an empty response; their unusable `AUDIO` references
were removed and remain documented in `missing_audio.csv` and the per-language
`failed_audio.csv` files.

### Major issues, user beware

* It is known that the audio does not always match the text. It is not clear how common this is. 

* There are sentences (last count, 56) where the glosses are clearly wrong. Most, but not all, of these cases involve a missing gloss, resulting in glosses being out of sync with the words. See `sentences_with_bad_glosses_removed.csv`

* At the time the NTU Formosan Corpus was created, there were no clear conventions as to whether to write a clitic as a stand-alone word. However, the glosses almost always treat the clitic as attached to another word. This results in sometimes two words corresponding to a single W element. A list of such cases is found in `clitics.csv` (currently 819 cases).

* There are some translated but unglossed wordlists. These lack W elements on account of not having any segmentation or glossing.

* Even after accounting for the two issues above, the number of W elements does not always match the number of words in the sentence. These cases are listed in `validation_results.csv` (current count: 366).

* There are a number of cases where, in the glosses, the wordform and syntactic glosses differ in the number of segments. Many of these cases appear to be due to failing to segment the wordform. Others may be due to the wordforms and syntactic glosses being out of alignment. Known examples are recorded in `validation_m_results.csv` (current count: 1,415).

* The original data often contains transcriber notes or translation notes in the text. These have been removed from the text and placed in a `notes` attribute in the corresponding <FORM />. However, such information may not always be included (it was complicated to extract), so users who are interested in the notes and parentheticals should consult the online version of the NTU Formosan Corpus, which is meant to be read by a human. The `id` of the XML file (check the <TEXT> header element) tells you what the file is on NTU Formosan Corpus. The `id` of the <S> element tells you which line in the NTU Formosan Corpus.

* The original data also has notes written below the free translation. Many of these simply state the source of the information, but others are useful and relevant. These are NOT included in FormosanBank. (Not because they aren't interesting, but because it's harder than you'd think to extract them and figure out where to put them.)

## Minor notes

* The Amis text does not use the `^` glottal stop. `^` does appear in the original, but as a discourse marker. 

* The Rukai marker `_` is not used in the text.

* A small subset of sentences in the Grammar subcorpus have no word-by-word glosses (the original data does not include them).

* The original data has a lot of prosodic markup and other dialog markup. This has all been removed.

* Item 323 in sentence/Kanakanavu_Kanakanavu/1.json is excluded because it involves two sentence fragments that are hard to deal with.

* Item 12 from sentence/Bunun_Isbukun/59.json is misaligned in the original, but the alignment is straightforward and was corrected by hand.

* In the Sakizaya texts, "i tina" and "i tiza" are sometimes written as "itina" and "itiza". However, the glosses treat them as separate words. We have edited the text to write them as separate words.

* In the Sakizaya texts, "paza'ci" was written as a single word, but based on glossing and other examples, it appears to be "paza' ci". This was corrected as part of parse_grammar.py

* In the Kanakanavu texts, "tia'apacangcangarʉʉn" was often written as one word, whereas it appears that "tia 'apacangcangarʉʉn" is more likely based on glossing. We made this change in parse_grammar.py.

* In the Kanakanavu sentence subcorpus, "∅" appears 31 times, marking a null morpheme (e.g. a phonologically empty REL). Pipeline treatment: the marker is kept in original/W/M FORMs, removed from S-level standard FORMs by `standardize.py`, and silent in PHON (an all-null M gets PHON `∅`); `clean_xml.py` canonicalizes the Grammar subcorpus's `ø`/`Ø` variants to `∅`. See step 7 under Processing.

* Some English glosses contain Mandarin (e.g. `eng="使役-太陽=完成貌"`), most likely because the glossers were Mandarin-dominant. These are left as they are in the source; the known cases are listed in [gloss_anomalies_review.csv](gloss_anomalies_review.csv) (category `eng gloss contains CJK`).

* A handful of wordforms contain or consist of gloss codes rather than actual word material (e.g. `RED-osa-un`, where the annotator wrote the reduplication code instead of the reduplicated syllable, or words whose form cell is just `FIL`/`NOM`/`EXIST`). The true forms are not recoverable from the source; they are listed in [gloss_anomalies_review.csv](gloss_anomalies_review.csv) (categories `gloss code embedded in wordform` and `wordform is a bare gloss code`).

* Some sentences are glossed only in English in the source (no Chinese gloss exists), and some source gloss rows are *echo rows* (the gloss cells just repeat the wordform — common for names and untranslated items). Neither is repairable from the source; see [gloss_anomalies_review.csv](gloss_anomalies_review.csv) (categories `english-only glossing in source` and `echo gloss`). A further small set has the Chinese gloss available in a duplicate of the same word elsewhere in the source (category `zh exists in a source duplicate`), repairable on request.

* Six source JSONs in the sentence subcorpus assign the same record id to two *different* sentences (e.g. `sentence/Bunun_Isbukun/46.json` numbers its records 1,2,3,3,4,...). Because S ids embed the record id, both sentences would receive the same S id (and identical W/M ids below it). The second occurrence (in document order) is disambiguated with a `-2` suffix: `46_S_3` and `46_S_3-2`. For those sentences the NTU line-number provenance is inherently ambiguous — the collision is in the NTU backend itself. Affected: `46_S_3`, `03-4_S_15`, `43_S_2` (Bunun); `3_S_201` (Kanakanavu); `20200530-FW-Andrea-1_S_6`, `20200530-FW-Yongfu-1_S_13` (Rukai).

***

## Processing

All steps below are wrapped by [CodeAndDocs/make.sh](CodeAndDocs/make.sh), which runs
them in order against a fresh parse (audio download only with `--with-audio`), then
finishes with a corpus-wide `add_phonology.py` refresh, re-application of recorded
hand edits (`QC/cleaning/apply_manual_edits.py`, if `CodeAndDocs/manual_edits.xml`
exists), and a `validate_text.py` summary. The step-by-step documentation below is
the reference; `make.sh` is the executable form.

Note on per-step PHON regeneration: steps 5, 9, 11 and 12 regenerate PHON through
a witness check (`scripts/_phon_regen.py`, `borrow_segmentation.py`). Since
2026-08-10 both helpers are thin wrappers over `add_phonology.py`'s own
`load_profile`/`phonologize` (dialect-aware, contextual rules, current
marker/punctuation policy), so the witness passes on any file whose PHON the
current pipeline generated; files carrying an older PHON vintage fail it and are
conservatively skipped. Either way `make.sh` ends with a corpus-wide
`add_phonology.py` refresh that regenerates every PHON canonically.

Note on serialization: the corpus has two serialization conventions — the parsers'
minidom style and the published lxml style (`<?xml version='1.0' encoding='UTF-8'?>`)
— and every repair script refuses to rewrite a file it cannot first reproduce
byte-for-byte (the "round-trip guard", which guarantees a script never introduces
incidental reformatting). `make.sh` converts between the conventions at each
boundary via `scripts/normalize_serialization.py` (minidom for step 4, lxml for
steps 5–20, and lxml again after the final `add_phonology.py` refresh). Until the
next regeneration, nine *published* files are outside the lxml convention (the
seven Tsou Stories files rewritten by the 2026 Tsou-PHON regeneration, plus
`Grammar/Seediq` and `Grammar/Sakizaya`) and are therefore skipped by post-hoc
repair scripts.

**Regeneration status (2026-08-10):** a full from-scratch `make.sh` run was
verified sentence-by-sentence against the published corpus — zero data loss; all
14,663 AUDIO references byte-identical; the differences are intentional pipeline
changes (TRANSL quote/notes normalization, `ø`/`Ø` → `∅`, dash canonicalization,
new-style PHON and standard tier) plus improvements (12 additional borrowed
segmentations, 4 recovered source words including Rukai `malra`). Full triage:
[claudeplans/2026-08-10-ntu-rerun-diff-audit.md](../../claudeplans/2026-08-10-ntu-rerun-diff-audit.md).

* **1. Parse original files**

```bash
    python scripts/run_parsers.py
```

These scripts do *a lot* of cleaning. The JSONs used in the backend of the NTU Formosan corpus are meant to result in something human-readable, not machine readable.

These scripts produce many error logs and warning logs, which are described in the "Notes" above. However, the `validation_results.csv` and `validation_m_mismatches.csv` are produced by running `validate_glossing.py` from FormosanBank QC/validation scripts library.

`run_parsers.py` ends with a normalization pass (2026-08-10): M ids are renamed
from the parsers' `<Wid>_M<j>_<k>` scheme to the corpus's canonical `<Wid>M<n>`
(1-based, document order — the scheme every published M id follows and that
`apply_manual_corrections.py`'s element-id-targeted entries depend on), and the
TEXT `dialect` attributes are pinned from a hard-coded table (per
subcorpus/language; single-dialect languages follow the dialects.csv convention
dialect == language name; `Sentences/Bunun` is Junqun per maintainer
determination although the source folder says Isbukun — Isbukun is recorded as
an OtherName of Junqun in `dialects.csv`).

* **2. Download the audio**

```bash
    python scripts/download_grammar_audio.py
    python scripts/download_stories_audio.py
```

Note that there is no audio associated with sentences. 

Note also that utterances in grammar and stories lack audio, and some of the audio that is supposed to exist does not. An error log reports missing audio.

AUDIO `file` attributes keep the **raw (URL-encoded) basename** of the source URL
(e.g. `Seediq_A1-3-1-6%20n.mp3`) — the published convention that the Hugging Face
audio archives are keyed on; do not decode them. `remove_no_audio_elements.py`
(run by make.sh right after parsing) deletes only the self-closing `<AUDIO/>`
placeholder elements whose filename is the NTU "no audio file" sentinel (沒有音檔,
matched in both its URL-encoded and decoded spellings); sentence content is never
touched.

* **3. Clean, standardize orthography, and add phonology**

First, some more punctuation cleaning. Since the 2026-08-09 null-morpheme spec this
also canonicalizes the null-morpheme marker glyphs (`ø`/`Ø` → `∅`, U+2205) in
morpheme position on **all** tiers, original included — the glyph is annotation, not
source spelling (see step 7):

```bash
    python ../FormosanBank/QC/cleaning/clean_xml.py --corpora_path Final_XML
```

According to the documentation, all data use Ortho94. In practice, though, we found that where there are differences between Ortho94 and Ortho113, the latter fit the data better. The only exception is Amis, which appears to have been influenced by Church. 

* Amis - Church
* Atayal - Ortho113 <-- though with an unexpected number of `v`s. Could be Ortho94.
* Bunun - Ortho113 <-- though a lot of `g`s (mainly not Ortho94 because Junqun in Orth94 didn't have glottal stops).
* Kanakanavu - Ortho113 <-- with a bunch of á and ú and ó
* Kavalan - Ortho113
* Rukai - Ortho113
* Saisiyat - Ortho113 (could be Ortho94, but no important differences)
* Sakizaya - Ortho113
* Seediq - Ortho113 (could be Ortho94)
* Tsou - Ortho113 (could be Ortho94)

```bash
    python scripts/remove_no_audio_elements.py
    python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML --remove_accents
    python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML --orthography Ortho113
```

`standardize.py --remove_accents` (2026-08-10) replaces the old `--copy` +
`remove_stress_accents.py` pair. It copies original → standard and then:

   - Strips combining acute/breve marks from the standard tier, including the
     necessarily-decomposed `ʉ́` (no precomposed codepoint exists; it is stored as
     `ʉ` + U+0301). The Grammar subcorpus (Kanakanavu and Sakizaya) marks stress in
     elicited examples (`Namásia`, `mʉ́rʉpʉ`, `Pánay`/`Panáy`); the same lexemes
     appear unaccented (with the same meanings) in the other subcorpora, so the
     accents are suprasegmental annotation, not orthography. They are kept in
     `original` and removed from `standard`. (Full evidence in
     `scripts/remove_stress_accents.py`, retained for reference — do **not** run it;
     standardize owns this now. Safe for this corpus because accent-bearing data is
     confined to Grammar Kanakanavu/Sakizaya and no NTU language uses an accented
     letter orthographically — a caution that matters for Rukai corpora generally,
     whose Ortho113 includes `é`.)
   - Removes null-morpheme units (`∅`, `∅-`, `-∅`) from **S-level** standard FORMs.
     W- and M-level standard FORMs keep them — see step 7.
   - Applies C012 to the S-level standard FORM of morpheme-segmented sentences:
     segmentation `-` (digit-aware, so `2020-07-31` survives) and clitic `=` are
     stripped. For Bunun, where `-` is an orthographic letter, hyphens are preserved
     and per-occurrence `c012` warnings are written to `standardize_warnings.csv`.

`add_phonology.py` now treats null morphemes as silent — no more `*` in PHON at null
sites — and an M whose FORM is entirely `∅` gets PHON `∅`; unmapped punctuation is
dropped from PHON output.

* **4. Repair empty-form morphemes**

Some morphemes were left with an empty `<FORM>` upstream: when a wordform and its gloss split into a different number of segments, the parsers pad the shorter side (`itertools.zip_longest`), producing `<M>` shells that carry a gloss but no form (or a form but no gloss). This step removes the empty-form shells in the cases where the misalignment is an unambiguous slot-ordering artifact, reattaching the existing glosses to the form-bearing morphemes.

```bash
    python CodeAndDocs/scripts/repair_empty_morphemes.py
```

**Notes**
   - Repairs only words where every gloss tier has exactly as many non-empty glosses as the word has form-bearing `<M>` elements (with an added bracket-alignment check for words containing infixes). No gloss text is re-derived — existing `<M>`-level glosses are only relocated — so FORM, PHON, and gloss content are preserved exactly; only empty shells are removed.
   - Words with a genuine count mismatch between form and gloss (the gloss has more/fewer morphemes than the form, regardless of `-`/`=` placement) are left untouched for manual/source review. They are listed in `empty_M_repair_partition.csv`.
   - Idempotent: re-running makes no further changes. Each file is rewritten only if its unmodified tree first round-trips byte-identically through the serializer, so the script can never introduce unrelated reformatting.

* **5. Borrow segmentation from duplicate instances**

Many remaining empty-form morphemes exist because the source writes a wordform unsegmented (e.g. `matineng`) while glossing it as several morphemes (`主事焦點-知道`). In many cases the same word appears properly segmented elsewhere in the source (`ma-tineng`). This step finds those duplicates in `CodeAndDocs/{grammar,sentence,story}` and applies the borrowed segmentation: the word-level FORM gains its boundary markers, each morpheme slot receives its form piece, and PHON is regenerated for the affected elements via the same Ortho113 mapping `add_phonology.py` uses.

```bash
    python CodeAndDocs/scripts/borrow_segmentation.py
```

**Notes**
   - A word is repaired only if all guards hold: a unique candidate piece-sequence among same-language source duplicates; letter fidelity (boundary markers are added, letters never change — verified); per-tier gloss counts equal to the piece count; and PHON reproducibility (converting the word's current FORM through `add_phonology.py`'s own `phonologize` must exactly regenerate its existing PHON before the mapping is trusted to produce the new per-morpheme PHONs — since 2026-08-10 this uses the real pipeline profile, so it passes on current-pipeline PHON and skips older vintages). Anything failing a guard is skipped and remains listed in `empty_M_repair_partition.csv`.
   - `make.sh` runs this step twice: here, and again as step 5b after the manual corrections (steps 11–12), because a word can become borrowable only after a correction repairs its FORM (e.g. Bunun `61_S_2` `nii＝ik` → `nii=ik`). On a fresh regeneration the two passes recover 122 words — 12 more than the published corpus, since the modernized guard 5 accepts words the old vintage check had to skip.
   - Background on `==`: the source uses `==`/`===` as a prosodic-lengthening marker, which the parsers strip. In a few words the stripped run also contained a real boundary (e.g. `izaw===tu` = `izaw==` + clitic `=tu`), fusing two morphemes; where a cleanly segmented duplicate exists this step recovers them. Spellings containing `==` are never used as the borrowed form.
   - Expects the corpus's current serialization (lxml with XML declaration, after the id-normalization pass); a file is rewritten only if it first round-trips byte-identically, so the script never reformats. Idempotent.

* **6. Disambiguate duplicate sentence ids**

Six sentence-subcorpus source JSONs assign the same record id to two different sentences (see Minor notes), which propagated into duplicate S/W/M ids in the XML. `parse_sentences.py` now disambiguates at generation time (the second occurrence gets a `-2` suffix). For already-published XML, the identical renaming is applied post-hoc:

```bash
    python CodeAndDocs/scripts/dedupe_sentence_ids.py
```

**Notes**
   - Renames only the second-and-later occurrences of a duplicated S id (document order), cascading the prefix into descendant W/M ids. Element content is never touched.
   - Audio safety: a duplicated sentence carrying an AUDIO descendant is skipped with a warning, since audio file names elsewhere embed sentence ids. (None exist today: all duplicates are in the Sentences subcorpus, which has no audio.)
   - Same conventions as steps 4-5: byte-identical round-trip guard, idempotent.

* **7. Remove null-morpheme symbols — RETIRED (2026-08-10)**

The Kanakanavu sentence subcorpus writes a null-morpheme placeholder inside words (e.g. `niarisinatʉ∅kee`; see Minor notes) and the Sakizaya grammar writes a null prefix slot (`ø-sitangah`). Handling is now owned by the shared pipeline (step 3), per the 2026-08-09 null-morpheme spec:

   - `clean_xml.py` canonicalizes the marker glyphs (`ø`/`Ø` → `∅`, morpheme position, all tiers).
   - `standardize.py` (non-`--copy` modes) removes null units from **S-level** standard FORMs only.
   - `add_phonology.py` renders nulls silent; an all-null M FORM gets PHON `∅` (previously the symbols were rendered `*`).
   - W- and M-level standard FORMs **retain** the `∅` marker. This is required by the validators: V069 (HARD — a null in a W FORM needs an M child whose FORM is `∅`) and the V124/V125 propagation rules (a null on the M tier must be witnessed by the parent W FORM and the S-level original FORM). So `ni-arisinatʉ-∅=kee` keeps its null on both W FORM tiers, with the null M's PHON being `∅`.

Do **not** run `CodeAndDocs/scripts/remove_null_symbols.py` (retained for reference only): its W-level stripping contradicts that policy, and it left orphaned boundary markers in the published corpus (`ni-arisinatʉ-=kee` where a rerun now yields `ni-arisinatʉ-∅=kee`).

* **8. Manual review: parentheses and slashes in W/M forms (V121)**

This step is **manual** and must be redone (or the edits re-applied) after any regeneration from source. `validate_text.py` rule V121 flags W/M FORMs containing parentheses or slashes; these are annotation conventions from the source that survive the parsers:

   - Parenthesized optional/elided material, e.g. W forms `(sua)`, `(i)`, `k(a)-u` (~259 W elements). Whether to realize, drop, or annotate these is a linguistic judgment made case by case.
   - Slash-delimited unresolved alternatives, e.g. `si/la`, `ma-lrigi/ma-elre-elrenge/ma-adraw` (~42 W elements; these are in languages where the Kanakanavu-style slash-variant expansion was not applied).

Run `python ../FormosanBank/QC/validation/validate_text.py by_path --path XML` and work through the V121 findings.

**Status (2026-08-10):** no edits have ever been committed under this step. From the from-scratch regeneration (`18868920e`) onward, every XML-touching commit maps to a scripted step or to an `apply_manual_corrections.py` table entry; the V121 work became steps 15–20, and the residue is documented in step 20's notes ("Still open in V121"). The only unscripted hand edits in the published XML were seven AUDIO boundary fixes in six Stories files (two Kavalan, four Seediq; commit `1817ae39e` — zero-duration/overlapping start–end boundaries nudged to valid values). As of 2026-08-10 these are recorded as attribute-targeted `AUDIO_FIXES` entries in `apply_manual_corrections.py` (step 11), so they now survive regeneration like every other one-off correction.

* **9. Remove source annotation codes and overlap markers**

The source embeds transcription machinery that the parsers fused into the published text: bracketed elicitation/annotation codes inside wordforms and translations (`na=unau[u1]`, `Tahail[u1][A2][A3] [TVH4]ran ...`), conversation-analysis overlap markers in the Kavalan dialogs (`[1aw1]`, `[3maiseng=ay3]`), and the Grammar books' example numbers fused to the final word (`cina.25` — fused in the source itself). This step removes them:

```bash
    python CodeAndDocs/scripts/remove_annotation_codes.py
```

**Notes**
   - FORM-side removals are source-driven: only exact fused variants derived from bracket-marked source tokens are replaced, so clean text cannot be affected. TRANSL-side bracketed codes are removed only for codes attested in the source inventory.
   - Removed codes are NOT preserved verbatim (per maintainer decision 2026-06-11); each affected sentence's S-level original FORM gains a `notes` breadcrumb (e.g. `annotation codes removed; consult the NTU Formosan Corpus source`).
   - PHON regenerated via the witness-gated Ortho113 mechanism. Round-trip guard; idempotent.

* **10. Fix swapped gloss languages**

Two sentence-subcorpus source files (`sentence/Bunun_Isbukun/63.json`, `64.json`) are zh-first while the parser assumes eng-first, inverting eng/zho for every W/M gloss in those stems (~16,400); ~170 isolated rows elsewhere have the same per-row inversion:

```bash
    python CodeAndDocs/scripts/fix_swapped_gloss_langs.py        # stems 63/64
    python CodeAndDocs/scripts/fix_swapped_gloss_langs.py --all  # corpus-wide sweep
```

**Notes**
   - Swap gate per element: eng text contains CJK and zho text does not — idempotent, and identical code pairs (DM, TOP) or single-tier elements are untouched. S-level free translations were never affected.
   - Remaining mixed-language cells that the gate cannot resolve are listed in `gloss_anomalies_review.csv` (with bare-code/code-in-form anomalies) for manual review.
   - Round-trip guard as in steps 4-9.

* **11. Apply one-off manual corrections**

Hand-verified single corrections that are too specific for a general rule live in tables inside the script. The tables have grown well beyond the original single entry and now cover: a stray `<` for `(` in a Bunun zho TRANSL (the 1129/1128 `<`/`>` imbalance in V132 counts); the three Grammar/Sakizaya citation sentences (step 11 notes below); fullwidth `＝` normalization; the gloss-table column-shift repairs (with element-id targeting, FILL and DELETE entries); L2-marker PHON residue; and the `AUDIO_FIXES` table — the seven invalid audio start/end boundaries originally hand-edited in commit `1817ae39e` (13 attributes across six Stories files), recorded here so they survive regeneration:

```bash
    python CodeAndDocs/scripts/apply_manual_corrections.py
```

Idempotent (applied corrections stop matching and are reported as no-match). New one-off fixes should be added to the table in the script rather than edited directly into the XML, so they survive regeneration. The table also repairs the three Grammar/Sakizaya sentences whose source records *cite* corpus examples instead of restating them (`13_S_38`, `13_S_39`, `13_S_48`): the IU numbers and pause durations fused to the first word of each intonation unit are stripped from the W/M forms, the S FORM is rebuilt from the cleaned words, the citation is preserved in a `notes` attribute on the S-level original FORM, and PHON is regenerated (witness-gated).

* **12. Repair code-switch (L2) markup**

The source marks code-switched words with tags like `<L2JjidenshaL2J>` (J/M/T/... = the language switched into). Well-formed tags are stripped by the parsers, but the source contains ~30 malformed spellings — transposed closers (`<L2MpiaocunLM2>`), missing `>` (`<L2JjidenshaL2J`), letterless tags (`<L2siyencL2>`, where the stripper previously ate the word's first letter: published `iyenc` for source `siyenc`; likewise `haiya`), square-bracket variants (`[L2JmaemotteL2J]`), and tags inside gloss strings (TRANSL), which were never stripped at all. This step applies a hand-audited token map (every contaminated token in the corpus → its correct form, derived from and verified against the source JSONs):

```bash
    python CodeAndDocs/scripts/repair_l2_markers.py
```

**Notes**
   - Tokens are replaced only on exact match, so clean text cannot be affected; gloss notation like `2SG`/`2PL` is untouched. A gloss that was only a marker becomes a properly empty TRANSL. A FORM is never emptied; the one known marker-only morpheme (`L2M-L2M` under Kanakanavu `kkvNr_dailylife_Angai_S_11_W0`, with its echo-gloss sibling) is left as-is and reported on every run — it needs a structural (manual) fix.
   - PHON of affected elements is regenerated through the Ortho113 mapping, gated by the pre-change original-tier witness check.
   - The parser-side stripper (`strip_l2m` in `scripts/utils.py`) is intentionally left unchanged: this post-step runs after parsing in the pipeline and converges the output regardless, without risking an over-eager regex in the parser (the eaten-letter bug came from exactly that).
   - Same conventions as steps 4-7: byte-identical round-trip guard, idempotent.

* **13. Decode double-encoded gloss entities**

The source JSONs are inconsistent about angle brackets in reduplication/infix notation: most store the real characters (`<RED>cook-LF`), but `sentence/Bunun_Isbukun/63.json` stores HTML-escaped strings (`&lt;RED&gt;`), which reached the XML writer verbatim and were escaped a second time on serialization (`&amp;lt;` in the published file — validate_text rule V132). This step decodes literal entity strings in element text and attribute values by exactly one level (1,109 TRANSL glosses + 3 TRANSL `notes` in `Sentences/Bunun/Bunun.xml`; nothing else in the corpus is affected):

```bash
    python CodeAndDocs/scripts/fix_double_encoded_glosses.py
```

Single non-iterating pass (one decode level only), so it can never over-decode; byte-identical round-trip guard; idempotent.

* **14. Convert M-tier infix notation to `-X-`**

FormosanBank reserves angle brackets for the W FORM (where `<X>` marks the surface position of an infix in its host) and for TRANSL glosses (`<AF>`, `<RED>`); at the morpheme tier an infix must be written `-X-` (validate_glosses rule V067 HARD). The NTU parsers copy source morpheme strings verbatim and the source writes M-level infixes with brackets (`<n>` under `m<n>nanang`), so the published corpus carried ~2,920 bracketed infix Ms across all three subcorpora. This step rewrites them:

```bash
    python CodeAndDocs/scripts/convert_infix_notation.py
```

An M's FORM and PHON (both tiers) are converted only when (a) the M's original FORM is exactly one bracket group `<X>`, (b) that group occurs literally inside the parent W FORM (so the brackets are genuine infix notation, not a word-level code-switch/noise marker), and (c) removing all bracket groups from the W FORM leaves host letters beyond clitic chunks. W FORMs and TRANSL glosses are never touched. The transformation is purely notational, so PHON needs no orthography mapping. Round-trip guard; idempotent.

**Notes / known residue (not converted)**
   - The conversion drops V067 from ~2,946 to **11**. The 11 are not single bracket groups: they are word-level markers (`<BREATH>`, `<jiuhaole>`, `P>`) and bracket groups the parsers split across a morpheme boundary on a dash inside the brackets (`la<in-i>haib-an` → `la<in` / `i>haib`). These need structural repair, not notation conversion, and are left for manual review (the same four sentences also account for the 4 V134 angle-bracket-in-S-FORM SOFT findings).
   - Converting to `-X-` activates **50 V062** (HARD: an infix M requires an angle-bracket gloss on its parent W). These are a pre-existing *source* gloss-completeness gap that the notation fix surfaces rather than creates: the infix morpheme is present at the M tier, but the source glossed the whole word holistically (`q<m>ita` → "then") and never bracketed the infix in the W gloss. The correct `<AF>`-style W gloss cannot be derived mechanically, so these are documented here rather than auto-filled.
   - Marker residue that this sweep exposed in the L2 token map (step 12) — half-eaten bracketed L2 variants (`>ciuru>`, `<gonense>`), prosody-span markers split across words (`<HIGH.PITCH … HIGH.PITCH>`, `<LOW.VOLUME … LOW.VOLUME>`), and stray span closers — was added to that step's token map and to `apply_manual_corrections.py` (for file-vintage PHON whose witness check refused regeneration). Re-run steps 11 and 12 after this step is in place; all three are idempotent.

* **15. Split optional-word parentheticals into two sentences**

In elicitation the source sometimes records a word as *optional* by wrapping it in parentheses — in the running sentence FORM, in the word/morpheme FORM, and in the matching gloss (also parenthesized) — while the free translation has no parentheses (the optional material is a linguist's note, not part of the uttered sentence):

```
S FORM : wavutha (nakuane) pangipalay.
W1     : FORM "(nakuane)"  gloss "(1S.FO)" / "(第一人稱單數.自由斜格)"
TRANSL : "He forced me to fly."          (no parentheses)
```

Parentheses are forbidden in W/M FORMs (validate_text V121 HARD). Rather than guess whether the optional word belongs in the form, this step materializes both readings as real, parenthesis-free sentences:

```bash
    python CodeAndDocs/scripts/split_optional_parentheticals.py
```

A sentence is split only when **all** hold: (1) its FORM has a parenthesis; (2) its free translation has none; (3) every parenthesis-bearing word is a *whole* parenthetical (FORM matches `^\([^()]*\)$`, so no parens are embedded in or split across other words); (4) each such word's gloss is itself fully parenthesized. The original element becomes the **without-optional** reading (the parenthetical word(s) deleted, the optional token removed from the S FORM/PHON, whitespace/punctuation tidied); a **with-optional** reading is inserted right after it (only the optional word's parens stripped, content kept), with id suffix `-opt` and descendant ids rewritten to match. 58 sentences split (39 Bunun, 16 Kanakanavu, 3 Rukai); V121 drops by 246.

**Notes**
   - **Audio**: the recording is of the shorter, actually-uttered sentence, so AUDIO stays on the without-optional reading and is removed from the with-optional one (5 sentences, all Kanakanavu Grammar).
   - **Only the optional word's parens are touched.** Unrelated parenthetical *gloss* annotations elsewhere in the same sentence — an optional gloss particle such as `去(了)`, `song(sing)`, or `(OBL)` — are preserved verbatim in both readings (those are V122 SOFT, not V121, and carry meaning). PHON needs no orthography mapping: removing parentheses never changes a letter.
   - **Duplication of pre-existing findings**: the with-optional reading is a near-copy, so any pre-existing validator finding in a split sentence is inherited by its `-opt` twin. This accounts for, and is confined to, the small post-step increases (V066 +40, V017/V073 +4 from one sentence's empty-M shells, V060 +3, V061 +2) — all in `-opt` ids, no new defect types.
   - Not handled (left for manual review): sentences with parentheses embedded in or split across words, or whose parenthetical word lacks a parenthesized gloss (133 split/intra-word + 61 gloss-mismatch candidates). Byte-identical round-trip guard; idempotent (the outputs contain no FORM parens to re-split).

* **16. Expand slash alternatives into one sentence per alternative**

The source sometimes records several acceptable forms of a word separated by `/` (in the word/morpheme FORM and the also-slashed gloss) while the free translation lists none. The slash scope is the *morpheme*: in `pua/mua/mu-lebe` (gloss `放/去/去-下` / `put/go/go-down`) only M1 (`pua/mua/mu`) alternates and M2 (`lebe`) is shared, so the readings are `pua-lebe` / `mua-lebe` / `mu-lebe` — not the naive split `pua` / `mua` / `mu-lebe`. Slashes are forbidden in W/M FORMs (validate_text V121 HARD). This step materializes each alternative as its own sentence:

```bash
    python CodeAndDocs/scripts/expand_slash_alternatives.py
```

A sentence is expanded only when **all** hold: exactly one word has `/` in its FORM and is `<M>`-segmented; every morpheme's FORM/PHON tiers and glosses split into 1 (shared) or the same N≥2 (alternation); the **word-level FORM splits into exactly N** (this rejects word-level alternation the parser mis-segmented at the morpheme tier — see below); each morpheme group occurs verbatim in the word- and sentence-level FORM/PHON; and the free translation has no `/`. The original element becomes alternative 1; alternatives 2..N are inserted after it with id suffix `-alt2`..`-altN`. Each reading takes its morpheme pieces, and the word/sentence FORM/PHON/gloss are rebuilt by replacing each morpheme group in place (preserving the word's own `-`/`=` separators), so no slash remains. PHON needs no mapping (choosing an alternative changes no letter). AUDIO stays on alternative 1, removed from the rest (no clean slash sentence currently has audio). Round-trip guard; idempotent. Currently expands 1 sentence (Rukai `20200529-FW-Ken-1_S_6`, N=3); V121 drops by 4.

**Not handled — other slash families (left for manual review)**
   - **Word-level alternation with a garbled morpheme tier** (e.g. Rukai `20200528-FW-Yongfu_S_7`, `ma-lrigi/ma-elre-elrenge/ma-adraw` = smart/tall/big): the parser split on `-` and `/` together, so the morphemes are nonsense (`lrigi/ma`, `elrenge/ma`) and the word-level `/`-count (3) disagrees with the morpheme N (2). Re-segmenting would mean inventing morphemes (the zh gloss isn't even `-`-segmented), so it is not auto-expanded.
   - **Trailing/empty-alternative slashes** (~36, mostly Bunun `63`): a stray `/` with an empty second alternative (`bunbun?/`, `ha?/`), not a real alternation — a cleanup, not an expansion.
   - **W/M-only alternation** (3: `si/la`, `ngu/mu-a-ta-tulru`) where the S FORM already collapsed to one alternative, and **slash+paren mixes** (1: `ngu-/mu-(a-)drusa`).

* **17. Strip stray trailing slashes**

A run of Bunun `63` records ends a word with a slash and an empty second alternative — `bunbun?/`, `ha?/`, `mai-babu=tan?/` — where the `?` is sentence-final punctuation kept on the last word and the `/` is a transcription artifact, not an alternation (the matching glosses carry no slash; the S-level FORM never has the stray slash). This step removes trailing `/` from W/M FORM/PHON only:

```bash
    python CodeAndDocs/scripts/strip_trailing_slash.py
```

A genuine alternation has `/` *between* forms, never at the end, so real `a/b` forms (step 16) are untouched. 36 words (144 FORM elements across W/M × both tiers); V121 drops by 144 (to 884). Round-trip guard; idempotent.

* **18. Expand word-level slash alternatives (mis-segmented at the morpheme tier)**

A few words list several *complete* alternative words separated by `/`, each itself multi-morpheme — e.g. Rukai `20200528-FW-Yongfu_S_7` `ma-lrigi/ma-elre-elrenge/ma-adraw` (smart/tall/big). The parser split on `-` and `/` together, garbling the morpheme tier (`lrigi/ma`, `elrenge/ma`), so its slash count disagrees with the word-level count and step 16 refuses it. The word-level FORM/PHON/gloss split cleanly into N on `/`, and each alternative re-segments cleanly on `-`, so the sentence is rebuilt one alternative per S:

```bash
    python CodeAndDocs/scripts/expand_word_level_alternatives.py
```

Because these cases need per-sentence judgement, each is described in the script's `CONFIG` rather than inferred; the `/`-split, `-` re-segmentation, and PHON (from the word's own slashed PHON, no mapping) are mechanical. PHON handling is best-effort by vintage (2026-08-10): when the file's PHON no longer carries the `/` alternation or `-` segmentation markers (the current `add_phonology.py` strips them), the FORMs and glosses are still expanded and PHON is left for `make.sh`'s final `add_phonology.py` refresh to regenerate. Two judgement points for S_7, both recorded in `CONFIG`: (a) the published free translation was **truncated** to the first alternative (source `free` is "Laucu is smart/tall/big"), so each reading's translation is restored from source — the zh `很` is taken to distribute (`Laucu很聰明/很高/很大`); (b) the source wrote `狀態.實現.聰明` with a `.` where the morpheme boundary `-` belongs (cf. the sibling `狀態.實現-大`), repaired so STAT.RLS/be.smart align. The original becomes alternative 1; alternatives 2..N follow with id suffix `-alt2`..`-altN`; mis-segmented morphemes are rebuilt from each alternative's own tiers; AUDIO stays on alternative 1. Expands 1 sentence (S_7 → 3); V121 drops by 6; the readings are clean under validate_glosses. Round-trip guard; idempotent.

* **19. Collapse gloss-only slash alternations**

For a few words the source's running sentence used a single form, but the word's lexical gloss row recorded an alternative with `/` — e.g. Rukai `20200531-FW-Yongfu-2_S_9` says `si` ("and") in the sentence while the gloss row is `si/la` (`and/then`). (Confirmed against the source JSON `ori` field, which carries one form for all three of these.) These must **not** be expanded — the alternative utterance was never made — so this step collapses the word to the alternative that actually appears in the sentence:

```bash
    python CodeAndDocs/scripts/collapse_gloss_only_alternations.py
```

A word is collapsed only if: exactly one slash-word with `<M>` segmentation and no parenthesis (slash+paren mixes left for manual); every morpheme tier/gloss splits into 1 or the same N≥2; the free translation has no `/`; and exactly one alternative's reconstructed surface (dashes/clitics removed) matches a whitespace token of the S-level FORM — the uttered form (0 or >1 ⇒ ambiguous, left for manual). The uttered alternative is kept across all tiers; the dropped alternative form(s) and glosses are recorded in a `notes` attribute on the word's original FORM. The S-level FORM/PHON are already collapsed and untouched. Collapses 3 words (`si/la` ×2, `ngu/mu-a-ta-tulru`); V121 drops by 12 (to 866). Round-trip guard; idempotent.

* **20. Resolve residual whole-word optional parentheticals**

Step 15 split only optional words whose gloss was also parenthesized. This step handles the remaining whole-word parentheticals (plain gloss, or word absent from the sentence) by routing each on whether its surface form appears in the S-level FORM:

```bash
    python CodeAndDocs/scripts/resolve_residual_optional_parens.py
```

- **split** — the parenthesized surface (`(sua)`, `(kumakʉʉn)`) is a token of the S FORM → produce without- and with-optional readings, reusing step 15's `make_without`/`make_with` (id `-opt`). 61 sentences.
- **strip** — the *bare* surface (`la`, `kavay`) is a token of the S FORM → the word is already in the sentence without parens; just remove them. 2 words.
- **delete** — the surface is absent from the S FORM → an optional addition not uttered (Seediq `(so)` glossed `(如此)`); remove the word and record it in a `notes` attribute on the sentence's original FORM. 1 word.

Surface matching strips infix/segmentation markers (`< > - =`) first, so `(k<um>a-kʉʉn)` matches the S-FORM token `(kumakʉʉn)`. V121 drops 866→580. The post-step V017/V073 +14 each are pre-existing empty-M shells duplicated into `-opt` clones (`make_with` is a pure deep copy — it creates no new empties), confined to `-opt` ids. Round-trip guard; idempotent.

   - **Still open in V121** after steps 15–20 (left as-is by maintainer decision): optional sub-morphemic segments inside a word (`k(a)-u`, `a(ʉ)lʉ`, `(=dau)`; ~152 elements), parenthetical asides split across words (`usa-bi(n` … `ma)s`; ~134), and the one slash+paren mix `ngu-/mu-(a-)drusa`. These need manual review.
