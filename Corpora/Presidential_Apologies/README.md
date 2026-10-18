# Presidential Apologies

The official 2016 presidential apology in 16 Indigenous languages, aligned with Mandarin and English. The corpus contains 16 TEXT records and 524 paragraph-sized S records; it has no word or morpheme analysis. The [Presidential Office Indigenous Historical Justice project](https://indigenous-justice.president.gov.tw/) provided the bilingual publications.

**Basecamp card:** [6991940238](https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/6991940238)

## Languages and dialects

One XML file per language, `XML/<Language>/<Language>.xml`. Each declares its language code (`xml:lang`) and dialect (`dialect`) on `<TEXT>`:

| File | `xml:lang` | `dialect` | TEXT id | Sections |
| --- | --- | --- | --- | --- |
| `XML/Amis/Amis.xml` | `ami` | Xiuguluan | `PA_Amis` | 33 |
| `XML/Atayal/Atayal.xml` | `tay` | Sekolik | `PA_Atayal` | 33 |
| `XML/Bunun/Bunun.xml` | `bnn` | Junqun | `PA_Bunun` | 33 |
| `XML/Kanakanavu/Kanakanavu.xml` | `xnb` | Kanakanavu | `PA_Kanakanavu` | 29 |
| `XML/Kavalan/Kavalan.xml` | `ckv` | Kavalan | `PA_Kavalan` | 33 |
| `XML/Paiwan/Paiwan.xml` | `pwn` | Central | `PA_Paiwan` | 33 |
| `XML/Puyuma/Puyuma.xml` | `pyu` | Nanwang | `PA_Puyuma` | 33 |
| `XML/Rukai/Rukai.xml` | `dru` | Wutai | `PA_Rukai` | 33 |
| `XML/Saaroa/Saaroa.xml` | `sxr` | Saaroa | `PA_Saaroa` | 33 |
| `XML/Saisiyat/Saisiyat.xml` | `xsy` | Saisiyat | `PA_Saisiyat` | 33 |
| `XML/Sakizaya/Sakizaya.xml` | `szy` | Sakizaya | `PA_Sakizaya` | 33 |
| `XML/Seediq/Seediq.xml` | `trv` | Tegudaya (glottocode `teke1282`) | `PA_Seediq` | 33 |
| `XML/Thao/Thao.xml` | `ssf` | Thao | `PA_Thao` | 33 |
| `XML/Truku/Truku.xml` | `trv` | Truku | `PA_Truku` | 33 |
| `XML/Tsou/Tsou.xml` | `tsu` | Tsou | `PA_Tsou` | 33 |
| `XML/Yami/Yami.xml` | `tao` | Yami | `PA_Yami` | 33 |

#### Language, dialect and IDs

Seediq and Truku share the ISO code `trv`; the `dialect` attribute tells them apart. Every sentence carries a Mandarin (`TRANSL xml:lang="zho"`) and an English (`TRANSL xml:lang="eng"`) translation.

`CodeAndDocs/data/dialect_authority.tsv` records source files, section counts, language codes, dialects, TEXT IDs and the Seediq glottocode. Dialects come from the cited published baseline, not from labels in the PDFs. That baseline is historical evidence, not a tools version pin. English has no bilingual-PDF witness, and the PDFs do not establish the inherited dialect labels.

Published TEXT IDs `PA_<Language>` and zero-based S IDs remain unchanged: `0` through `32`, or `0` through `28` for Kanakanavu. The tests compare source tiers, translations and IDs with a supplied published baseline.

## Source

#### Overview

On **August 1, 2016**, President Tsai Ing-wen delivered a historic apology to Taiwan's indigenous peoples on behalf of the government during **Indigenous Peoples' Day**. The apology addressed the pain and mistreatment endured by indigenous communities over four centuries and marked the establishment of the **Presidential Office Indigenous Historical Justice and Transitional Justice Committee (Indigenous Justice Committee)**.&#x20;

This apology text, as part of the effort to promote **historical justice**, has been translated into the 16 officially recognized Formosan languages: **Amis**, **Atayal**, **Saisiyat**, **Thao**, **Seediq**, **Bunun**, **Paiwan**, **Rukai**, **Truku**, **Kavalan**, **Tsou**, **Kanakanavu**, **Saaroa**, **Puyuma**, **Yami**, and **Sakizaya**. The translated apologies are the main texts forming the corpus described here. This corpus consists exclusively of **text data.** The apology text is also available in **English** and **Chinese**.

The corpus contains 524 aligned sections: 33 per language (29 for Kanakanavu), each with the Indigenous-language text, its Mandarin translation and its English translation. No audio is included.

* The Office of the President provides the [official English apology](https://english.president.gov.tw/NEWS/4950), and the Council of Indigenous Peoples provides the [16 Formosan-language versions](https://www.cip.gov.tw/zh-tw/news/data-list/01F6453A792735EC/index.html?cumid=01F6453A792735EC).
* The corpus XML and the code that produces it are available [in FormosanBank](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Presidential_Apologies).

#### Source files and alignment

`CodeAndDocs/Apologies/` contains one bilingual PDF and one native transcript per language, shared Mandarin and English transcripts, and separate Kanakanavu translations. The 36 files are checksummed in `CodeAndDocs/data/source_manifest.csv`. Fifteen texts have 33 aligned sections; Kanakanavu has 29. Sections can combine source paragraphs to align the translations.

**Sources.** `CodeAndDocs/Apologies/` holds, for each language, the official bilingual PDF (Indigenous language and Mandarin) and a plain-text transcript of the Indigenous-language text, plus shared Mandarin and English transcripts and separate Kanakanavu translations. The 36 files are checksummed in `CodeAndDocs/data/source_manifest.csv`.

**Alignment.** Each paragraph of every language was aligned with its Mandarin and English translation by dividing the apology into 33 sections, the same in every language. Kanakanavu, whose paragraphing differs, was divided separately into 29. Each transcript holds one section per line. An example:

<figure><img src="../../docs/site/en-us/.gitbook/assets/Screenshot 2024-12-08 at 9.41.01 PM.png" alt=""><figcaption></figcaption></figure>

#### Audio

None.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Presidential_Apologies_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

* **Citing the apology in general**: Tsai, I. W. (2016, August 1). _President Tsai Ing-wen's apology to the Indigenous Peoples on behalf of the government_ \[Speech transcript]. [Office of the President](https://english.president.gov.tw/NEWS/4950).
* **Language specific**: Tsai, I. W. (2016, August 1). _President Tsai Ing-wen's apology to the Indigenous Peoples on behalf of the government_ \[Speech transcript, Amis translation]. [Council of Indigenous Peoples](https://www.cip.gov.tw/zh-tw/news/data-list/01F6453A792735EC/index.html?cumid=01F6453A792735EC).

## License

**License:** public domain

**Rights source:** Wael Mohamed (recorded source status), 2024-10-16; evidence: ask maintainer

This retains the published corpus's public-domain status. The dated source coordination record confirms that status; it is not a new licence grant by the compiler. The committed PDFs and transcript snapshots are the recorded public build inputs.

According to [Copyright rules by territory/Taiwan](https://commons.wikimedia.org/wiki/Commons:Copyright_rules_by_territory/Taiwan), transcriptions of presidential speeches are not copyrighted as they are listed under public domain.

> ### Not protected <a href="#not_protected" id="not_protected"></a>
>
> See also: [Commons:Unprotected works](https://commons.wikimedia.org/wiki/Commons:Unprotected_works)
>
> According to the _Copyright Act as amended on 15 June 2022_, The following items shall not be the subject matter of copyright, to which [\{{PD-ROC-exempt\}}](https://commons.wikimedia.org/wiki/Template:PD-ROC-exempt) applied:\[2022 Art.9]
>
> 1. The constitution, acts, regulations, or official documents.
> 2. Translations or compilations by central or local government agencies of works referred to in the preceding subparagraph.
> 3. Slogans and common symbols, terms, formulas, numerical charts, forms, notebooks, or almanacs.
> 4. Oral and literary works for news reports that are intended strictly to communicate facts.
> 5. Test questions and alternative test questions from all kinds of examinations held pursuant to acts or regulations.
>
> The term "official documents" in the first subparagraph of the preceding paragraph includes proclamations, text of speeches, news releases, and other documents prepared by civil servants in the course of carrying out their duties.\[2022 Art.9]

## Notes and caveats

- **Saaroa sections 22 and 23 have identical Saaroa text.** The official Saaroa PDF prints the same Saaroa paragraph on page 22 and again on page 23, each time beside a different Mandarin paragraph. Both sections are kept as printed, so at least one of them is probably not a translation of the Mandarin and English it is paired with. The source repeats Saaroa S22/S23 on physical PDF pages 22/23 beside different translations. Both records are intentional and retained.
- Four words are printed with an alternative in parentheses: Puyuma section 28 `parubalruk(pasenkin)`, Tsou section 2 `taa’uzva(taa’uiva)` and `esmiza(esmia)`, and Tsou section 9 `mahiz’o(mahi’o)`. Each of these sections gives the reading outside the parentheses as its main text and the other readings as variant forms (`ver="alt"`). Tsou section 2's two alternations vary independently, so it has three variants. The IPA follows the main reading. (How these are built: step 2 under "What each step does".)
- Mandarin code-switching, explanatory quotations and numbers are part of the source text. Mandarin glosses in parentheses (e.g. Tsou and Kavalan `zipun( 日 本 )`) are kept in the original tier and removed from the standard tier (see Corpus Processing). Not every parenthesis marks optional spoken material. (Corpus Processing is step 7 under "What each step does".)
- The English translation has no witness in the bilingual PDFs, and the PDFs do not state the dialect of each translation; the dialect labels are inherited.
- **Amis**: the letter `b` occurs only in `Balay` and `Sbalay`, Atayal words quoted in the apology ("In the Atayal language, truth is called 'Balay', and reconciliation is called 'Sbalay'").
- **Tsou**: the official PDF prints `x` where `ʉ` is meant in seven words. The original tier keeps the printed spelling; the standard tier corrects it: section 1 `ahmxskʉ` → `ahmʉskʉ`, section 4 `;oyonatmopsx` → `'oyonatmopsʉ` (the `;` is also a slip), section 5 `tposx` → `tposʉ`, section 6 `hxpxhxpxxngx` → `hʉpʉhʉpʉʉngʉ`, section 16 `suezopx` → `suezopʉ`, section 25 `axt'ʉcʉ` → `aʉt'ʉcʉ`, section 27 `tmopsx` → `tmopsʉ`. Six of these spellings occur elsewhere in the same PDF; section 6's does not, and reads each `x` as `ʉ`. (How this is applied: step 5 under "What each step does".)
- **Kanakanavu**: the text uses a small number of `h`s and `f`s, which are controversial. None of the words with them appear in the ILRDF dictionary, with or without the `h`s and `f`s, so they have been left in.
- **Puyuma**: Puyuma uses a small number of `h`s and `f`s, which are non-standard and may reflect borrowings. It also uses a number of ē's, the phonological significance of which are unclear. For now, these have been treated as identical to `e`. The words with ē, with their number of appearances: `yēncumincu` 47, `sēhu` 27, `yēncumin` 4, `sincengyēn` 3, `uēiyēnhuy` 2, `lihuayiēn` 1, `siyēnhua` 1, `sēfu` 1, `tuytonghuēiy` 1, `uēiyēn` 1, `yiēn` 1.
- **Sakizaya**: a small number of `f`s appear to be in loanwords.
- **IPA `*`**: each file's IPA (`PHON`) is generated from a single dialect's orthography table, and a letter that table does not have is written as `*` rather than borrowed from another dialect. Words affected in the standard tier: Thao 136 (`c`, `g`, `o`, mostly romanized Mandarin such as `guan-cu-min-cok`), Puyuma 129 (`c`, `h`, `o`, e.g. `yēncumincu`, `sēhu`, `Pinpucu`), Bunun 38 (`e`, `y`, e.g. `sehu`), Saaroa 20 (`o`, e.g. `kokana`), Kanakanavu 6, Amis 5 (`b` in `Balay`/`Sbalay`), Kavalan 5 (`f`, e.g. `cungtungfuan`), Saisiyat 2, Seediq 1; Atayal, Paiwan, Rukai, Sakizaya, Truku, Tsou and Yami have none (in Tsou, the seven words printed with `x` keep a `*` in the original tier's IPA only). Treat the IPA of these words as incomplete.
- **Hand corrections to the transcripts.** Earlier corrections in `CodeAndDocs/data/source_corrections.csv` preserve Kavalan S6 word boundaries, Saaroa S0 `mualiuhlu`, and the Truku S25 text-layer apostrophe. The Truku PDF font displays a missing glyph, while its embedded text identifies U+FF07. Nine further paragraph repairs have PDF locators in the same correction ledger and are applied from `manual_edits.xml`. Shared tooling regenerates [manual_edits.md](CodeAndDocs/manual_edits.md) as the readable correction changelog.
- **Orthography.** The [published orthography decision](https://github.com/FormosanBank/FormosanBank/commit/9608caee5) uses `standardize.py --copy` and original PHON profile `Ortho113`, including the previously reviewed Thao choice. PHON follows the declared dialect column. Current shared tools own accent handling in derived PHON; unavailable dialect sound values remain `*` without borrowing another dialect's values.

## Reproduction and processing

### How to reproduce

```bash
bash Corpora/Presidential_Apologies/CodeAndDocs/generate_xml.sh
```

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

Use a current FormosanBank checkout with its dependencies installed. From this corpus folder (`Corpora/Presidential_Apologies/`):

```bash
FORMOSANBANK_ROOT=/path/to/FormosanBank PYTHON=python3 \
  CodeAndDocs/generate_xml.sh
```

Both variables are optional: `FORMOSANBANK_ROOT` defaults to the FormosanBank checkout three folders above `CodeAndDocs/`, and `PYTHON` defaults to `python3`.

The build generates fresh source XML, applies recorded edits, cleans, copies standard FORM, applies the standard-tier spelling corrections in [standard_corrections.tsv](CodeAndDocs/data/standard_corrections.tsv), generates PHON with `Ortho113`, then applies the scoped annotation handling below. It replaces only `XML/` and rewrites `CodeAndDocs/provenance.json`; it does not fetch sources or run validators. Optional `QC_OUTPUT_DIR` selects an external warning directory. [provenance.json](CodeAndDocs/provenance.json) records the actual FormosanBank tools commit and never selects or pins the tools checkout. A Git-free export retains this provenance record.

Source auditing and tests are separate from generation:

```bash
python3 -m pip install -r CodeAndDocs/requirements.txt
python3 CodeAndDocs/scripts/audit_source_alignment.py \
  --xml-dir XML --report /path/outside/repository/source_alignment.csv
PRESIDENTIAL_PUBLIC_XML_ROOT=/path/to/FormosanBank/Corpora/Presidential_Apologies/XML \
  python3 -m pytest CodeAndDocs/tests
```

Run current FormosanBank QC separately and review its findings. Compare two fresh builds byte-for-byte; source-audit scores and unchanged record counts alone do not establish correctness. Keep audit/QC reports outside the repository. `XML/<Language>/` is the sole final-output tree.

### What each step does

`generate_xml.sh` first checks that the FormosanBank checkout contains `QC/cleaning/clean_xml.py`, and builds in a temporary staging folder (`CodeAndDocs/.build.XXXXXX`, deleted on exit), so a failed step leaves `XML/` untouched. It stops at the first step that fails.

**Build.** One command, `bash Corpora/Presidential_Apologies/CodeAndDocs/generate_xml.sh`, rebuilds the published XML from these files. It runs, in order:

1. `main.py` reads each language's transcript and the matching Mandarin and English transcripts line by line (checking that each has the expected 33 or 29 sections), and writes one XML file per language: one `S` per section, with the Indigenous-language text as the original `FORM` and the two translations as `TRANSL`. It also writes each file's language code, dialect, citation and `public domain` status. The language, code, dialect, section count, TEXT id, glottocode and input files of each file come from `CodeAndDocs/data/dialect_authority.tsv`; an empty section, or a section count that differs from that table, stops the build.
2. `apply_manual_edits.py` applies the 15 recorded hand edits in `CodeAndDocs/manual_edits.xml`: nine sections where the transcript had run words together or dropped words (corrected against the PDFs), three small corrections where the transcript differs from the PDF (the Saaroa title, where the PDF prints `mualiuhlu` with a plain final `u` and the transcript had `ʉ`; Truku section 25, where the transcript has `;` for the closing quotation mark; and Kavalan section 6, where the spaces after the two Mandarin glosses were missing), and the three sections with alternative readings described above.
   - Puyuma S28 `parubalruk(pasenkin)` and Tsou S2/S9 `taa’uzva(taa’uiva)`, `esmiza(esmia)`, `mahiz’o(mahi’o)` print an alternative reading in parentheses. Each is published as a variant FORM (`ver="alt"`, POL-028) of one S, recorded in `CodeAndDocs/manual_edits.xml`: the base FORM has the reading outside the parentheses and the variant the one inside. Tsou S2's two alternations vary independently, so it has three variants (maintainer ruling, 2026-10-16).
3. `clean_xml.py` normalizes Unicode (combining marks are joined to their letters) and decodes HTML entities. In the Indigenous-language text it converts full-width and typographic punctuation to plain ASCII (every dash variant becomes `-`), collapses runs of spaces, and reduces repeated punctuation (`!!` → `!`); in the Mandarin translations it makes the full-width double quote `＂` the only double quote. It also checks each apostrophe that might be a quotation mark rather than the glottal-stop letter; in this corpus it changed none and flagged 1,053 ambiguous cases for review. It runs with `--warnings_dir` set to `QC_OUTPUT_DIR` (or a new temporary folder), so its warning reports are written outside the corpus.
4. `standardize.py --copy` adds the standard tier as a copy of the original tier (the sources already use the standard orthographies), including the variant forms.
5. `apply_standard_corrections.py` makes the seven Tsou spelling corrections listed in `CodeAndDocs/data/standard_corrections.tsv` (see Notes and Issues) in the standard tier only. It stops with an error if a listed word is not found.
   - Those notes are under "Notes and caveats" above. The script also stops if the word occurs more than once in either tier's main reading.
   - The official Tsou PDF prints `x` where `ʉ` is meant in seven words. The original FORM keeps the printed spelling; the standard FORM, and so its PHON, is corrected by `CodeAndDocs/scripts/apply_standard_corrections.py` from [standard_corrections.tsv](CodeAndDocs/data/standard_corrections.tsv) (maintainer ruling, 2026-10-16): S1 `ahmxskʉ` → `ahmʉskʉ`, S4 `;oyonatmopsx` → `'oyonatmopsʉ` (the `;` is also a slip, for `‘`), S5 `tposx` → `tposʉ`, S6 `hxpxhxpxxngx` → `hʉpʉhʉpʉʉngʉ`, S16 `suezopx` → `suezopʉ`, S25 `axt'ʉcʉ` → `aʉt'ʉcʉ`, S27 `tmopsx` → `tmopsʉ`. Six of these spellings occur elsewhere in the same PDF; S6's does not, and reads each `x` as `ʉ`. The original-tier PHON of these words still contains `*`.
6. `add_phonology.py --orthography Ortho113` writes the IPA (`PHON`) for both tiers from the Ortho113 orthography tables, using each file's declared dialect column (e.g. Amis Xiuguluan, Bunun Junqun, Puyuma Nanwang). Stress and length marks are removed before conversion, so Puyuma `ē` is read as `e`; punctuation is not written in IPA; a letter the dialect's table cannot transcribe becomes `*`. (The original-tier table is the one named by `--orthography`; the standard-tier table is the language's standard orthography in `standards.csv`, which is Ortho113 for all 16 languages here.)
7. `remove_standard_cjk_annotations.py` removes Mandarin-only glosses in parentheses (e.g. `( 日 本 )`) from the standard tier, main reading and variants alike, and rewrites the IPA with those glosses left out. The original tier keeps them, and Mandarin words written inline as part of the sentence stay in both tiers. A parenthesis counts as a gloss only if it contains a Chinese character and no Latin letter.

   **POL-047 deviation:** The [published annotation handling](https://github.com/FormosanBank/FormosanBank/commit/f73f24a78) runs `remove_standard_cjk_annotations.py` after phonology. It removes only CJK-only parenthetical annotations from standard FORM and regenerates PHON with those annotations masked. Original FORM, bare inline Mandarin and Latin parentheticals remain intact. This retains the corpus-specific ruling while shared tools supply the sound values.

   Mandarin code-switching, explanatory quotations and numbers are source content. CJK-only parenthetical annotations follow the scoped handling above. Do not treat every parenthesis as optional spoken material.
8. The staging folder is copied over `XML/` (`rsync -a --delete`, so files no longer produced are removed), and, when the FormosanBank checkout is a git repository, its current commit is written to `CodeAndDocs/provenance.json`. A checkout without git must already have that file, or the build stops.

The result is written to `XML/<Language>/<Language>.xml`. `CodeAndDocs/provenance.json` records the FormosanBank commit whose shared tools built it.

#### Source audit (separate from the build)

The source audit compares all 524 native and 524 Mandarin sections with their PDF pages. It checks native body coverage and embedded word spaces, excluding synthetic layout spacing. Alignment allows documented typography differences and an added terminal period in titles or closings, without folding case, letters or diacritics. English is absent from the bilingual PDFs: its committed snapshots are checked for integrity, section counts and mapping, without claiming PDF verification.
