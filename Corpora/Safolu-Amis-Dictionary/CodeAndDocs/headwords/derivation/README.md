# How the headword lists were derived

The build (`../generate_headwords.py`, run by `../../generate_xml.sh`) reads only the committed lists in
`CodeAndDocs/headwords/`. These scripts made them, during the maintainer's review (decision log, "Dictionary
headwords", 2026-11-12 to 2026-11-15). They are kept so the lists can be re-derived; they are not part of the
build and are never run by it.

They expect one working folder `WORK` laid out like this:

| Path | What |
|---|---|
| `WORK/src/4cb8/docs/s` | `g0v/amis-moedict` `docs/s` at `4cb82539d7e51e7211e262d4dbaecaa41a772b2f` (the text the headwords publish) |
| `WORK/src/printed/amis-safolu` | `miaoski/amis-safolu` at `f512d5ba0d08f81b26093a9b7b4a85acac760a30`: its `dict/*.txt` is the 2015 conversion of the printed manuscript, and `db/amis-sqlite3-db.sqlite3` is the converter's own database, whose `raw_contents` holds the source document's paragraphs before the converter split anything |
| `WORK/main-ro` | a FormosanBank checkout (for the published examples file) |
| `WORK/draft/` | the scripts' inputs and outputs, and a draft headword build (`generate_headwords.py` with the same switches as `generate_xml.sh`) |

| List | Made by |
|---|---|
| `repaired_breaks.tsv` | `cut_check.py WORK <draft build>` then `cut_2015.py WORK` (writes `cut_confirmed.tsv`): a translation is a suspected break when it has unbalanced brackets or no sentence-final punctuation; a break is confirmed when the joined pieces are one continuous run of text in the converter's input and the first piece does not end a sentence; each is then checked against the 2015 text. |
| `repaired_breaks_unchecked.tsv` | the rows of `repaired_breaks.tsv` whose 2015 check is "not locatable in 2015 text" or "headword not in 2015 text" |
| `example_pieces_removed.tsv` | `embedded_rebuild.py WORK` and `amis_tails_rebuild.py WORK <draft build>` (rebuild the example sentences, also used for `../../definition_examples.json`), then `example_pieces.py WORK <draft build without the missed-headword switches>`; `examples_manual.tsv` rows (mimingay from the 2015 text, and the examples of the restored headwords) are added by hand |
| `homophone_split.tsv` | `homophone_triage.py WORK --no-sections`: the headwords whose verdict is "plausibly homophones: no shared meaning" (the maintainer ruled them split, r6-homs-plausible) |
| `missed_headwords.tsv` | `missed_headwords.py WORK` |
| `lost_headwords.tsv` | `lost_headwords.py WORK` |
| `pos_labels.tsv`, `borrow_labels.tsv` | written by the review page's builder from the editors' version: every bracketed label opening a sense, and every bracketed text containing 借詞/借語; the maintainer checked both lists and marked 短語 as a part of speech |
| `restored_senses.tsv`, `corrected_senses.tsv` | by hand, from the 2015 text (each row cites the line) |

`homophone_triage.py` and `example_pieces.py`'s inputs come from a copy of the generator saved as
`WORK/draft/safolu_headwords.py` (the triage imports its `clean` and `classify`), and the triage still opens
`WORK/draft/section_rulings_4cb8.json`, which `--no-sections` then ignores (the maintainer ruled sections 23 and 24
treated like any other entry, r2-sections).
