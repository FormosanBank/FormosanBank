# Whitehorn Collection

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

This corpus represents the John Whitehorn audio collections in FormosanBank. It
contains archival recordings in Paiwan, Atayal, Amis, and Seediq. The
recordings are not transcribed, so each XML file describes one audio record or
track and contains no sentence tiers.

## Source and coverage

The source material comes from two World Oral Literature Project collections:

- https://www.repository.cam.ac.uk/collections/1240188b-2f4c-401e-9372-58177440d9c6
- https://www.repository.cam.ac.uk/collections/dc1f2cd8-36da-48e1-979b-fe478eff6a91

`CodeAndDocs/` contains 71 one-page scanned accession forms. The reviewed
inventory in `CodeAndDocs/source_records.json` records each PDF's SHA-256 hash,
page count, inclusion status, linked `TEXT` IDs, source dialect label,
recording date, source description, audio URL, and audio filename.

Seventy forms support 87 published records:

| Language | Dialect | Records |
| --- | --- | ---: |
| Amis | unknown | 1 |
| Atayal | unknown | 3 |
| Paiwan | Southern | 2 |
| Paiwan | unknown | 80 |
| Seediq (`trv`) | unknown | 1 |

The remaining form, `Whitehorn_Paiwan_03A_01.pdf`, describes a BBC Radio 3
broadcast containing five Bunun, two Amis, and one Atayal choir item. It has no
track-aligned audio URL or nonempty published XML record. The released master
file remains a declared Hugging Face extra because one mixed-language recording
cannot be assigned one source-faithful `TEXT/@xml:lang`. Its explicit excluded
disposition remains in the source ledger so the source unit is not silently
lost.

## Metadata decisions

- The World Oral Literature Project granted FormosanBank permission to use the
  Whitehorn collections under CC BY-NC 4.0. Every generated `TEXT` records that
  exact license.
- The accession forms label 46 records as Northwest Paiwan. Northwest is not a
  canonical FormosanBank Paiwan dialect, and review showed that the recordings
  cannot all be mapped to Northern. Following the corpus maintainer decision,
  their canonical `dialect` is `unknown` while the archival `North Western`
  label remains in the source ledger.
- Two forms explicitly say Southern Paiwan. Those two records retain
  `dialect="Southern"`.
- Recording dates remain verbatim in `TEXT/@source` and as structured ledger
  fields because the current FormosanBank XML schema has no recording-date
  attribute.
- Published `TEXT/@id` and `AUDIO/@file` values are stable and unchanged.

These decisions follow POL-030, POL-035, POL-037, and POL-038 in the current
FormosanBank policies.

## Reproduce and validate

The generator uses only the Python standard library.

```bash
python3 CodeAndDocs/generate_xml.py
python3 CodeAndDocs/generate_xml.py --check
```

The first command writes canonical output under `XML/`. The second hashes every
source PDF and compares `XML/` byte for byte with a clean temporary generation.
The source ledger records the 71-source and 87-record coverage contract, stable
language and dialect assignments, conservative Northwest handling, and the
granted license. FormosanBank's repository QC validates the generated XML.

## Audio

The XML points to the source repository URLs and names each released audio
file. To download the FormosanBank audio dataset into ignored `Audio/`:

```bash
bash download_audio_data.sh
```

Audio duration totals are maintained in FormosanBank's
`statistics/audio_durations.csv` under POL-032. The XML repair does not change
any audio reference or audio filename.

## Citation

Whitehorn, J. (n.d.). *The Whitehorn Collections*. World Oral Literature
Project. Retrieved February 24, 2025, from the [first
collection](https://www.repository.cam.ac.uk/collections/1240188b-2f4c-401e-9372-58177440d9c6)
and [second
collection](https://www.repository.cam.ac.uk/collections/dc1f2cd8-36da-48e1-979b-fe478eff6a91).
