An original Word document was provided by R. J. Early. Preparation involved the following steps:

1. The free translation was not always on its own line. This was fixed manually, the result being `Original/Paiwan Ch2.docx`. 

2. The scripts in the Jupyter notebook `script.ipynb` was then used to create the XMLs.

3. The character encodings from the original Word document did not transfer correctly, and no automatic solution was found. These were fixed using regular expressions (probably; unfortunately, the exact process was not recorded).

4. The following lines were fixed by hand:

story 061, sentence 034<br>
story 062, sentence 022<br>
story 071, sentence 064<br>
story 072, sentence 045<br>
story 074, sentence 070<br>
story 075, sentence 075<br>
story 095, sentence 008<br>
story 096, sentence 049<br>
story 097, sentence 022<br>

5. The QC script `clean_xml.py` was run, as per usual procedure. This mostly standardizes punctuation.

6. Handle orthography.

The Ferrell script was detected. Standardize with:

```bash
    python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML --tsv_path ../FormosanBank/Orthographies/ConversionTables/Paiwan_Ferrell_113.tsv
```

Then add IPA:

```bash
    python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML --orthography Ferrell
```

The fact that in some texts `?` is a character in the original text AND punctuation causes some problems. The following should clean most of that up:

```bash
    python fix_ferrell.py
```

7. **Confirm glossing worked**

For now the glossing isn't standardized across corpora. But the following will at least check to make sure the glosses exist everywhere they are supposed to:

```bash
    python ../FormosanBank/QC/validation/validate_glosses.py Final_XML --check_morpho
```

8. **Tag gloss translations with a language**

The morpheme-level (`M`) interlinear glosses were emitted as bare `<TRANSL>` elements with no `xml:lang`, which fails validator rule V023 (`xml:lang` is required on every `TRANSL`). The glosses are all English (English words plus Leipzig glossing abbreviations), so `xml:lang="eng"` was added to every such tag with:

```bash
    python CodeAndDocs/add_transl_lang.py
```

The script edits via targeted string replacement (leaving all other formatting intact) and re-parses each file with lxml to confirm the `TRANSL` count is unchanged and none remain without `xml:lang`. The sentence-level (`S`) free translations already carried `xml:lang="eng"` and were untouched.

9. **Split infix / reduplication morphemes**

The glosser packed actor-focus/perfective infixes and partial reduplication into a single `<M>` using `INFIX=ROOT` notation in *citation* form (e.g. `keman` → one `<M>` of `em=kan` / `af=eat`, where the surface is `k‹em›an`). `split_infix_morphemes.py` splits each such single-`M` word into two `<M>` elements — the infix/reduplicant (`-em-`, gloss `af`/`RED`) and the root with the infix position marked by `-` (`k-an`) — locating the infix by splicing it into the citation root to match the surface word (allowing one root-vowel syncope, e.g. `qetsi` → `q‹em›tsi`). The two new `<M>` carry only `FORM kindOf="original"` and `TRANSL`; their standard `FORM` and `PHON` are dropped and regenerated later (see the note below).

```bash
    python CodeAndDocs/split_infix_morphemes.py
```

Cases that do not splice cleanly (consonant mutation, stacked `=`, an extra unglossed prefix) are written to `flagged_infix_splits.csv` for manual handling; `=` morphemes inside already-multi-`M` words — where the morpheme maps to an unknown *substring* of the word — are listed in `multi_M_eq_morphemes.csv` and left untouched.

10. **Capitalize the reduplication gloss**

An `<M>`-level `TRANSL` of exactly `red` is always the reduplication marker in this corpus (every instance is a reduplicant copying a sister morpheme; there is no colour-word `red`). `capitalize_red.py` rewrites these to the glossing abbreviation `RED`, leaving any word/sentence-level `red` untouched.

```bash
    python CodeAndDocs/capitalize_red.py
```

11. **Fill the standard tier on the new morphemes**

The `<M>` created in steps 9–10 (and other hand-repaired morphemes) initially had only an original `FORM` and a `TRANSL`. `fill_standard_tier.py` adds their standard `FORM` by applying the `Paiwan_Ferrell_113.tsv` mappings directly to each new morpheme's original FORM (additions-only; existing forms untouched).

```bash
    python CodeAndDocs/fill_standard_tier.py
```

> **Do not run `standardize.py` (step 6) over the published `XML/`.** Its TSV maps `? → '`, which reconflates sentence-final question-mark *punctuation* with the glottal stop; in the dev-repo build this is undone afterward by `fix_ferrell.py`, but that script is hardcoded to the dev path and does not run here. Applying the TSV to only the new morphemes (step 11) is safe because morpheme FORMs never carry question-mark punctuation. (`add_phonology.py` carries the same whole-file caveat and is likewise not run over the published `XML/`; PHON for the new morphemes was filled by the same targeted character-mapping.)

### Citation

Early, R. J., and Whitehorn, J. (2003). One hundred Paiwan texts. Pacific Linguistics, Research School of Pacific and Asian Studies, The Australian National University.

This corpus is available CC BY-NC, with permission of the R. J. Early. The text itself is also freely available online from several sources.