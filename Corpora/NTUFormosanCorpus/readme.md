# NTU Corpus of Formosan Languages


***

## Notes

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

* In the Kanakanavu sentence subcorpus, "∅" appears 31 times. Its interpretation is unclear. 

* Six source JSONs in the sentence subcorpus assign the same record id to two *different* sentences (e.g. `sentence/Bunun_Isbukun/46.json` numbers its records 1,2,3,3,4,...). Because S ids embed the record id, both sentences would receive the same S id (and identical W/M ids below it). The second occurrence (in document order) is disambiguated with a `-2` suffix: `46_S_3` and `46_S_3-2`. For those sentences the NTU line-number provenance is inherently ambiguous — the collision is in the NTU backend itself. Affected: `46_S_3`, `03-4_S_15`, `43_S_2` (Bunun); `3_S_201` (Kanakanavu); `20200530-FW-Andrea-1_S_6`, `20200530-FW-Yongfu-1_S_13` (Rukai).

***

## Processing

* **1. Parse original files**

```bash
    python scripts/run_parsers.py
```

These scripts do *a lot* of cleaning. The JSONs used in the backend of the NTU Formosan corpus are meant to result in something human-readable, not machine readable.

These scripts produce many error logs and warning logs, which are described in the "Notes" above. However, the `validation_results.csv` and `validation_m_mismatches.csv` are produced by running `validate_glossing.py` from FormosanBank QC/validation scripts library.

* **2. Download the audio**

```bash
    python scripts/download_grammar_audio.py
    python scripts/download_stories_audio.py
```

Note that there is no audio associated with sentences. 

Note also that utterances in grammar and stories lack audio, and some of the audio that is supposed to exist does not. An error log reports missing audio.

* **3. Standardize orthography

First, some more punctuation cleaning:

```bash
    python ../FormosanBank/QC/cleaning/clean_xml.py --corpora_path Final_XM
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
    python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML --copy 
    python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML --orthography Ortho113
```

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
   - A word is repaired only if all guards hold: a unique candidate piece-sequence among same-language source duplicates; letter fidelity (boundary markers are added, letters never change — verified); per-tier gloss counts equal to the piece count; and PHON reproducibility (the Ortho113 mapping must exactly regenerate the word's existing PHON before it is trusted to produce the new per-morpheme PHONs). Anything failing a guard is skipped and remains listed in `empty_M_repair_partition.csv`.
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

* **7. Remove null-morpheme symbols from the standard tier**

The Kanakanavu sentence subcorpus writes a null-morpheme placeholder inside words (e.g. `niarisinatʉ∅kee`; see Minor notes). This is linguist's annotation, not orthography, so it is kept in `original` but removed from `standard`:

```bash
    python CodeAndDocs/scripts/remove_null_symbols.py
```

**Notes**
   - Cleans only S- and W-level `FORM`/`PHON` with `kindOf="standard"`. M-level null symbols (where `∅`/`ø` is itself a morpheme slot, e.g. Sakizaya `ø-sitangah` → M `ø` + M `sitangah`) are deliberately left: stripping them would create empty-form morphemes. An element is never emptied; would-be-emptied elements are skipped and reported.
   - Default removes `∅` only; `--chars` can extend the set.
   - Same conventions as steps 4-6: byte-identical round-trip guard, idempotent.

* **8. Manual review: parentheses and slashes in W/M forms (V121)**

This step is **manual** and must be redone (or the edits re-applied) after any regeneration from source. `validate_text.py` rule V121 flags W/M FORMs containing parentheses or slashes; these are annotation conventions from the source that survive the parsers:

   - Parenthesized optional/elided material, e.g. W forms `(sua)`, `(i)`, `k(a)-u` (~259 W elements). Whether to realize, drop, or annotate these is a linguistic judgment made case by case.
   - Slash-delimited unresolved alternatives, e.g. `si/la`, `ma-lrigi/ma-elre-elrenge/ma-adraw` (~42 W elements; these are in languages where the Kanakanavu-style slash-variant expansion was not applied).

Run `python ../FormosanBank/QC/validation/validate_text.py by_path --path XML` and work through the V121 findings.
