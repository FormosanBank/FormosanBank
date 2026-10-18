# Campbell-Favorlang

This corpus contains the Favorlang material in William Campbell's 1896
edition of *The Articles of Christian Instruction in Favorlang-Formosan*. It
has 1,049 Favorlang (`bzg`) sentences and 365 English translations. The corpus
contains 1,049 Favorlang (`bzg`) sentences, including 684 sermon sentences, and
365 English translations.

## Languages and dialects

One language: Babuza-Favorlang (ISO 639-3 `bzg`). The corpus is a single file,
[XML/Babuza-Favorlang/campbell_1896_favorlang_christian_instruction.xml](XML/Babuza-Favorlang/campbell_1896_favorlang_christian_instruction.xml),
whose `<TEXT>` carries `xml:lang="bzg"` and `dialect="Favorlang"`.

Favorlang (Babuza) is a distinct language from Siraya; the corpus is tagged
`bzg` with `dialect="Favorlang"`, matching the treatment in
[Latham 1862](../Latham-1862/README.md).

## Source

Favorlang material from Campbell's 1896 edition of *The Articles of Christian
Instruction in Favorlang-Formosan*. The XML's `source` attribute identifies the
copy used as Internet Archive item `cu31924026424675`. The book prints parallel
Dutch and Favorlang columns with English translations on the same page,
followed by five Favorlang-only sermons (described in
[CodeAndDocs/source_alignment_audit.md](CodeAndDocs/source_alignment_audit.md)).

The five sermons contribute 684 sentences after Madeline Boese's completed
review merged two OCR boundary errors and excluded the printed author
signature. Madeline Boese's completed sermon review is preserved in
[`CodeAndDocs/sermon_review.tsv`](CodeAndDocs/sermon_review.tsv). The reviewed
decisions account for all 687 pre-review sermon units: two pairs are merged,
the printed author signature is excluded, and 684 reviewed forms are emitted.

There is no audio.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Campbell-Favorlang_corpora_stats.csv` and appears on this corpus's
page on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

Campbell, W. (Ed.). (1896). *The Articles of Christian Instruction in
Favorlang-Formosan*. London: Kegan Paul, Trench, Trubner & Co.

## License

Public domain. The source is public domain. The XML records this as
`copyright="public domain"`.

The FormosanBank rights block (the `**License:**` and `**Rights source:**`
lines, POL-044) has not been filled in for this corpus yet: who confirmed the
public-domain status, when, and where the evidence is are not recorded here.

## Notes and caveats

- FormosanBank currently designates no standard orthography for
  Babuza-Favorlang, so this corpus has no standard or PHON tier. Because
  FormosanBank currently designates no standard orthography for
  Babuza-Favorlang, the source spelling is preserved without a standard or
  PHON tier. Each sentence has only a `FORM kindOf="original"` and, where
  Campbell gives one, an English `TRANSL`.
- Only 365 of the 1,049 sentences have an English translation: the sermons
  are printed without one.
- The Dutch column is not published: the source alignment audit says the
  available Fraktur OCR is not reliable enough for a source-faithful tier.
- Private source files are not included here. The full from-source build
  (below) cannot be run from this repository; the published XML is rebuilt
  from the tracked reviewed-record ledger instead.

## Reproduction and processing

### How to reproduce

```bash
bash Corpora/Campbell-Favorlang/CodeAndDocs/generate_xml.sh
```

The corpus XML, review ledgers, and reconstruction code are in the
[FormosanBank repository](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Campbell-Favorlang).
The tracked reviewed-record ledger is sufficient for a source-free rebuild:
no network, no private files. The script overwrites
`XML/Babuza-Favorlang/campbell_1896_favorlang_christian_instruction.xml` in
place. Pass a FormosanBank root as the first argument, or set
`FORMOSANBANK_PATH`, to use a different checkout's shared cleaning tools. Set
`PYTHON` to choose the interpreter; otherwise the script uses that
FormosanBank root's `.venv/bin/python`, falling back to `python3`.

This corpus does not yet have a `CodeAndDocs/provenance.json` (POL-052; it is
listed in `provenance_pending.txt`). The published files were refreshed from
private development commit `c07eb523f180dc1fd76887f9ad7221f1be8b2d57` and
revalidated on 2026-08-22 against FormosanBank tooling commit
`3a3c47c220520113f747e6a2d441494000e13c4b`, then retagged from `fos`/Siraya to
`bzg`/Favorlang on port to match `languages.csv` and `Corpora/Latham-1862`.
The corpus and publication metadata were revalidated on 22 August 2026 against
the current FormosanBank tooling and completed sermon-review evidence.

### What each step does

[CodeAndDocs/generate_xml.sh](CodeAndDocs/generate_xml.sh) runs two steps and
one check, stopping at the first error (`set -euo pipefail`).

#### 1. `build_xml.py --from-ledger`

[CodeAndDocs/build_xml.py](CodeAndDocs/build_xml.py) with `--from-ledger`
reads only
[CodeAndDocs/extracted_records.tsv](CodeAndDocs/extracted_records.tsv), the
reviewed-record ledger (1,049 rows, one per sentence). Before writing anything
it checks that the ledger still has exactly 1,049 rows with distinct
`record_id`s, and that each row's `has_translation`, `form_chars` and
`translation_chars` columns still match its `translation` and `form` text; any
mismatch stops the build.

It then writes one `<TEXT>` (id `campbell_1896_favorlang_christian_instruction`,
`xml:lang="bzg"`, `dialect="Favorlang"`, `copyright="public domain"`, and the
citation and BibTeX fixed in the script) and one `<S>` per ledger row, in
ledger order:

- `S/@id` is the ledger's `record_id` (for example
  `section_15_first_sermon_sentence_001`).
- `S/@source` records where the sentence is printed: printed page(s), PDF
  object page(s), section number, record id, record type and label, joined by
  `;` (for example
  `printed_pages_75-78;pdf_object_pages_107-110;section_15;section_15_first_sermon_sentence_001;sermon_sentence;label_sentence_001`).
- `FORM kindOf="original"` is the ledger's `form` column.
- `TRANSL xml:lang="eng"` is the ledger's `translation` column, written only
  when it is non-empty (365 rows).

The ledger also has a `standard` column; the ledger build does not write it to
the XML. `sermon_review.tsv` is not read in this mode: its decisions are
already applied in the ledger.

The ledger's record types, by count: `sermon_sentence` 684, `numbered_item`
160, `dialogue_turn` 160, `qa_turn` 22, `section_title` 14, `primary_section`
8, `section_preamble` 1.

Without `--from-ledger`, `build_xml.py` rebuilds the ledger itself from the
Internet Archive word-coordinate OCR under `Private/source/` and applies the
source, diacritic, reviewer and sermon-review corrections before writing the
XML. `generate_xml.sh` does not run that mode, and it needs files that are not
in this repository.

#### 2. `QC/cleaning/clean_xml.py --corpora_path XML`

The shared cleaner ([../../QC/cleaning/clean_xml.py](../../QC/cleaning/clean_xml.py))
rewrites the XML in place. It replaces non-breaking spaces with ordinary
spaces, then on each sentence's `FORM`: Unicode NFC normalization, HTML-entity
decoding (logged to `XML/html_entities.log` if any are found), zero-width
character removal, caret-variant and typographic-punctuation normalization to
ASCII, null-morpheme normalization, whitespace collapsing and trimming of
repeated punctuation. `TRANSL` text gets zero-width removal, entity decoding,
caret-variant and punctuation normalization, whitespace collapsing and
repeated-punctuation trimming (no NFC step, no null-morpheme step). It also normalizes translation-language metadata.
Its apostrophe/glottal-stop correction does not run here, because there is no
`QC/validation/reference/Babuza-Favorlang/attestation.txt` for it to consult.
Warnings go to `XML/cleaner_warnings.csv` (no `--warnings_dir` is passed).

#### 3. Warning-file check

If `XML/cleaner_warnings.csv` or `XML/standardize_warnings.csv` exists after
cleaning, the script prints `Unexpected warning sidecar` and exits with an
error, so a published rebuild never carries a warning file. Otherwise it prints
`Rebuilt Campbell Favorlang XML from the reviewed record ledger.`
