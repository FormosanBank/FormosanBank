# Sentence and entry ids

Two kinds of sentence id are published side by side (POL-037; maintainer
ruling 2026-10-15: *"Keep main's ids for the 96,988 (frozen in the ledger);
GUID ids only for new records."*):

| Kind | Example | Which records |
|---|---|---|
| main's id, `<Language>_<n>` | `Amis_0` | every sentence FormosanBank published before the 2026 rebuild that is still published |
| source GUID, `<Language>_<GUID>` | `Amis_20a69646-e70a-f011-bd65-00155db40116` | sentences new in the 2026 source |

Dictionary entries are always `<Language>_d<GUID>` (`d` for dictionary).
A record that is split into several `S` follows POL-028: the first keeps the
id, the second takes `-opt`, a third `-opt3`, and so on
(`Atayal_3715`, `Atayal_3715-opt`). A sentence with several different
recordings becomes one `S` per recording named the same way (`Bunun_1995`,
`Bunun_1995-opt`); see `recording_split_ids.csv`.

## Main's ids are frozen, not recomputed

`match_main_ids.py` matched every main sentence to the 2026 source **once**,
and its output is committed as `source_data/main_id_ledger.csv`. The build
reads the ledger and never re-matches, so a rebuild cannot move an id.

Matching, per main sentence:

1. its original FORM equals the 2026 text after normalisation (NFC;
   `ʼ ’ ‘` → `'`; whitespace runs collapsed);
2. otherwise, the Chinese translation is identical and the headword /
   explanation / example position in main's old audio URL
   (`…/Audio/<lang>/<headword>_{n}_@_<explanation>.<example>.mp3`) is the
   same;
3. otherwise, the Chinese translation is identical to exactly one 2026
   sentence item in the language (`ZH_UNIQUE_FALLBACK`; this is what the
   2026-10-15 review's matcher did, and it catches upstream edits that also
   renamed the headword).

| Ledger status | Count | What is published |
|---|---:|---|
| `kept` | 97,062 | the 2026 record, under the main id |
| `merged-kept` | 259 | main published the sentence 2–3 times, the 2026 source once: the lowest main id is kept, and its `S` carries every distinct translation of the copies |
| `merged-retired` | 261 | not published; listed in `../old_to_new_ids.csv` |
| `withdrawn` | 1,255 | no 2026 record: published as main published it, from the POL-035 snapshot in `source_data/main_2024/`, marked with `S/@source` |

Of the 97,062 `kept`, 73 are replaced by the maintainer's per-sentence
rulings in `source_data/alternative_rulings.json` (4 of them publish no `S`)
and one (Puyuma_888, repair #3) is withdrawn; those five retired ids are also
in `../old_to_new_ids.csv`.

## Why new records carry the source GUID

The ILRDF API assigns a GUID to every word, explanation, and sentence item
(verified across all 16 committed snapshots on 2026-09-05: 210,502 distinct
sentence GUIDs, none carrying more than one text, none shared between
languages). A GUID id survives our corrections to the text, which a hash of
the text would not, and it is what lets `manual_edits.xml` (which matches
records by `S/@id`) work at all. The GUID is carried whole so an id can be
grepped straight back to the snapshot.

The same sentence often appears under several headwords; 2026 records are
merged by normalised original text, and a new record's id is the **lowest
GUID in the group**.

## The two ledgers

- `source_data/main_id_ledger.csv` — input. Which 2026 record keeps which
  main id. Rewritten only by `match_main_ids.py --write`, deliberately.
- `source_data/published_ids.csv` — lockfile over the built tree.
  `generate_xml.py audit` (run by `validate.sh`) fails if an id disappears
  without being declared, if the XML has an id the ledger does not declare,
  or if an id's source GUIDs change.
