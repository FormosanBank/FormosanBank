#!/usr/bin/env python3
"""Give every recording its own S (maintainer ruling 2026-10-17).

  "A. One S per distinct recording; identical copies kept once"
  ids: "-opt, -opt3" -- the first S keeps the existing id.
  Yami: "These will need to result in 3 S blocks each. We don't have a
  mechanism for multiple audio files for one S block, and i don't want one."

generate_xml.py has already chosen each sentence's distinct recordings, put
them in order and named their files (audio_recordings.py). This step runs
after split_alternatives.py -- which moves the recordings of records whose
source prints alternatives out to TEXT level -- and replaces each S that still
holds k > 1 AUDIO by k copies: the same FORM/TRANSL, one AUDIO each, ids
<id>, <id>-opt, <id>-opt3 .... Untranscribed (TEXT-level) audio and the
dictionary files are not touched.

    python one_recording_per_s.py --xml-dir ../XML --report docs/recording_split_ids.csv
"""
from __future__ import annotations

import argparse
import copy
import csv
from pathlib import Path

from lxml import etree

from audio_recordings import split_id


def split_file(path: Path, rows: list[dict[str, str]]) -> int:
    tree = etree.parse(str(path))
    root = tree.getroot()
    ids = {s.get("id") for s in root.findall("S")}
    added = 0
    for sentence in list(root.findall("S")):
        audio = sentence.findall("AUDIO")
        if len(audio) < 2:
            continue
        base = sentence.get("id")
        index = list(root).index(sentence)
        for offset, keep in enumerate(audio):
            identifier = split_id(base, offset)
            if offset and identifier in ids:
                raise ValueError(f"{path.name}: {identifier} already exists")
            clone = copy.deepcopy(sentence)
            clone.set("id", identifier)
            for position, item in enumerate(clone.findall("AUDIO")):
                if position != offset:
                    clone.remove(item)
            root.insert(index + offset, clone)
            ids.add(identifier)
            if offset:
                added += 1
                rows.append({"language": path.parent.name, "base_id": base,
                             "new_id": identifier, "file": keep.get("file"),
                             "url": keep.get("url", "")})
        root.remove(sentence)
    if added:
        etree.indent(root, space="    ")
        tree.write(str(path), encoding="UTF-8", xml_declaration=True)
    return added


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml-dir", type=Path,
                        default=Path(__file__).resolve().parents[1] / "XML")
    parser.add_argument("--report", type=Path,
                        default=Path(__file__).resolve().parent / "docs" / "recording_split_ids.csv")
    args = parser.parse_args()
    rows: list[dict[str, str]] = []
    total = 0
    for path in sorted(args.xml_dir.resolve().rglob("*.xml")):
        if path.name.endswith("_dictionary.xml"):
            continue
        added = split_file(path, rows)
        total += added
        print(f"  {path.parent.name}: {added} S added")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, lineterminator="\n",
                                fieldnames=["language", "base_id", "new_id", "file", "url"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"one S per recording: {total} S added; listed in {args.report.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
