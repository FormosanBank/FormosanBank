#!/usr/bin/env python3
"""Generate per-language headword dictionaries from the committed snapshots.

The ILRDF source is a dictionary, but until now FormosanBank published only
its example sentences: the headwords, their Chinese glosses and their parts of
speech were read past and discarded. This emits them as a second file per
language, `XML/<Language>/<Language>_dictionary.xml`.

Shape: one <S> per headword, one <TRANSL> per sense, no W or M tier — the
source carries no morphological analysis. Part of speech rides on the sense's
own TRANSL/@notes, which is the only attribute the schema offers for it and
the right place besides: a headword's part of speech belongs to the reading,
not to the entry.

Source tiers only. The standard tier comes from standardize.py and PHON from
add_phonology.py, exactly as for the sentence files.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from ilrdf_source import (
    LANGUAGES,
    XML_LANG,
    Entry,
    extract_entries,
    root_attributes,
    verify_and_load_snapshot,
)

BASE = Path(__file__).resolve().parent
SOURCE_DATA = BASE / "source_data"
SNAPSHOT_DIR = SOURCE_DATA / "snapshots"
XML_DIR = BASE.parent / "XML"


def _build_tree(language: str, entries: list[Entry], snapshot_date: str) -> ET.Element:
    attributes = dict(root_attributes(language, snapshot_date))
    attributes["id"] = f"{attributes['id']}_dictionary"
    root = ET.Element("TEXT", attributes)
    for entry in entries:
        element = ET.SubElement(root, "S", {"id": entry.identifier})
        ET.SubElement(element, "FORM",
                      {"kindOf": "original"}).text = entry.headword
        for index, sense in enumerate(entry.senses):
            attrs = {XML_LANG: "zho"}
            if index:
                attrs["ver"] = "alt"
            if sense.part_of_speech:
                attrs["notes"] = sense.part_of_speech
            ET.SubElement(element, "TRANSL", attrs).text = sense.gloss
    return root


def _write_tree(root: ET.Element, path: Path) -> None:
    ET.indent(root, space="    ")
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(str(path), encoding="UTF-8", xml_declaration=True)


def run(languages: list[str]) -> int:
    manifest = json.loads(
        (SOURCE_DATA / "source_manifest.json").read_text(encoding="utf-8"))
    snapshot_date = manifest["snapshot_commit_date"]
    total_entries = total_senses = 0
    for language in languages:
        snapshot = verify_and_load_snapshot(language, SNAPSHOT_DIR, manifest)
        entries = extract_entries(language, snapshot)
        root = _build_tree(language, entries, snapshot_date)
        path = XML_DIR / language / f"{language}_dictionary.xml"
        _write_tree(root, path)
        senses = sum(len(e.senses) for e in entries)
        total_entries += len(entries)
        total_senses += senses
        print(f"{language}: {len(entries)} entries, {senses} senses -> {path.name}")
    print(f"total: {total_entries} entries, {total_senses} senses")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", action="append", dest="languages")
    args = parser.parse_args()
    requested = args.languages or list(LANGUAGES)
    unknown = sorted(set(requested) - LANGUAGES.keys())
    if unknown:
        raise SystemExit(f"unknown languages: {', '.join(unknown)}")
    return run([language for language in LANGUAGES if language in requested])


if __name__ == "__main__":
    raise SystemExit(main())
