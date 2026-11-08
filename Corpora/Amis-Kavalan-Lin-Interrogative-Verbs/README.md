# Lin (2015): Amis and Kavalan interrogative verbs

Lin, Dong-yi. 2015. The syntactic derivations of interrogative verbs in Amis and
Kavalan. In Elizabeth Zeitoun, Stacy F. Teng and Joy J. Wu (eds.), *New Advances
in Formosan Linguistics*, 253–289. Asia-Pacific Linguistics
([ANU repository](https://hdl.handle.net/1885/14354)). The corpus contains the
chapter's numbered Amis and Kavalan examples with their word and morpheme glosses
and English translations.

## Languages and dialects

- **Amis** (ISO 639-3 `ami`, glottocode `cent2104`): `XML/Amis/`, `dialect="Coastal"`.
  The chapter describes its Amis as "Central Amis, which is spoken in Changpin
  village, Taitung County".
- **Kavalan** (ISO 639-3 `ckv`, glottocode `kava1241`): `XML/Kavalan/`,
  `dialect="Kavalan"`. The chapter's Kavalan is Hsinshe Kavalan, from Hsinshe
  village, Hualien County.

## Source

The chapter's numbered examples, as printed (pp. 253–289). The transcription the
build reads is [CodeAndDocs/extracted_examples.tsv](CodeAndDocs/extracted_examples.tsv).

Two TEXT files contain 74 S (38 Amis, 36 Kavalan), 336 W and 504 M, with 89
sentence translations (15 of them alternative translations, `ver="alt"`) and 840
word and morpheme glosses.

The chapter has 96 numbered Amis and Kavalan occurrences (49 Amis, 47 Kavalan).
The corpus leaves out the 19 the source stars as ungrammatical and the 2 it marks
as marginal (POL-016); 18 further units are theoretical structures or examples
from other languages. Seven examples are printed twice and appear once. The
excluded units are listed in
[CodeAndDocs/excluded_source_units.tsv](CodeAndDocs/excluded_source_units.tsv).

Audio: none in the source.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Amis-Kavalan-Lin-Interrogative-Verbs_corpora_stats.csv` and appears on
this corpus's page on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

Lin, Dong-yi. 2015. The syntactic derivations of interrogative verbs in Amis and
Kavalan. In Elizabeth Zeitoun, Stacy F. Teng and Joy J. Wu (eds.), *New Advances
in Formosan Linguistics*, 253–289. Canberra: Asia-Pacific Linguistics.

See the FormosanBank [Terms of Use](https://formosanbank.github.io/FormosanBank/additional-resources/terms-of-use/).

## License

**License:** CC BY 4.0

**Rights source:** the chapter's own licence statement (Lin 2015, published CC BY 4.0); evidence: ask maintainer

Creative Commons Attribution 4.0 International (CC BY 4.0).

## Notes and caveats

None known.

## Reproduction and processing

### How to reproduce

From a FormosanBank checkout, with its Python dependencies installed:

```bash
source .venv/bin/activate
./Corpora/Amis-Kavalan-Lin-Interrogative-Verbs/CodeAndDocs/generate_xml.sh
python -m unittest discover -s Corpora/Amis-Kavalan-Lin-Interrogative-Verbs/CodeAndDocs/tests
QC_REPORT_DIR=/path/outside/the/corpus ./Corpora/Amis-Kavalan-Lin-Interrogative-Verbs/CodeAndDocs/validate.sh
```

`generate_xml.sh` uses the checkout three levels above `CodeAndDocs/` and
`python3`; `FORMOSANBANK_ROOT` and `PYTHON` name others. The FormosanBank commit
the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools). `validate.sh` runs the validators
separately; the build does not.

### What each step does

Everything is built in a temporary staging directory and installed into `XML/`
only when every step has succeeded.

1. `build_xml.py` builds the S, W and M records from the transcription. A
   printed optional word gives two S (the shorter with `-opt` IDs, POL-026); a
   printed optional prefix gives `ver="alt"` word and morpheme FORMs (POL-028).
   The sentence line keeps the printed infix marks `‹ ›`; the word tier writes
   them `< >` (POL-014). The four constituent brackets of examples 59–60 are
   left off for now (step 7).
2. `QC/cleaning/apply_manual_edits.py`, only if `CodeAndDocs/manual_edits.xml`
   exists (it does not at present).
3. `QC/cleaning/clean_xml.py`, with its report kept out of `XML/` (POL-033).
4. `QC/utilities/standardize.py`: Amis with
   `Orthographies/ConversionTables/Amis_94_113.tsv` (Coastal column), Kavalan
   with `Orthographies/ConversionTables/Kavalan_94_113.tsv`. The source spells in
   Ortho94.
5. `apply_standard_exceptions.py` applies `standard_tier_exceptions.tsv`: in
   example 14a, the one word with `q` (which Ortho94 lacks), `q` becomes `'` in
   its standard FORMs.
6. `QC/utilities/add_phonology.py --orthography Ortho94` for both languages.
7. `build_xml.py --restore-brackets` puts the printed constituent brackets back
   on the four original sentences of examples 59–60; their standard sentences
   and phonology have none.
8. The staged XML replaces `XML/`, and `provenance.json` records the tools.

**POL-047 deviation:** step 5 edits the standard tier after standardization, for
one sentence; step 7 edits the original tier after phonology, for four sentences.
Each checks that the text it edits is the text it expects and stops otherwise.
