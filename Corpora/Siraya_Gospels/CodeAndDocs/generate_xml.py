#!/usr/bin/env python3
"""Restore the corrected transcription and align the retained Bible editions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lxml import etree

from reference_translations import read_cuv, read_kjv

HERE = Path(__file__).resolve().parent
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def build(output: Path) -> None:
    reference = HERE / "reference_translations"
    manifest = json.loads((reference / "manifest.json").read_text())
    split = manifest["john_1_split"]
    english = read_kjv(reference / "eng-kjv-nltk-gutenberg.tsv")
    chinese = {
        book: read_cuv(reference / "cmn-cu89t_usfm" / filename)
        for book, filename in manifest["mandarin"]["books"].items()
    }
    omissions = {tuple(row) for row in manifest["mandarin"]["omitted_verses"]}
    for path in sorted((HERE / "baseline").rglob("*.xml")):
        relative = path.relative_to(HERE / "baseline")
        book = relative.parts[-2]
        chapter = int(path.stem.removeprefix("chapter"))
        tree = etree.parse(str(path))
        for node in tree.findall(".//FORM[@kindOf='standard']") + tree.findall(".//PHON"):
            node.getparent().remove(node)
        for sentence in tree.findall(".//S"):
            verse = int(sentence.get("id").removeprefix("verse"))
            split_chapter = book == split["book"] and chapter == split["chapter"]
            mapped = verse - 1 if split_chapter and verse >= split["right_verse"] else verse
            for translation in sentence.findall("TRANSL"):
                language = translation.get(XML_LANG)
                if language == "eng":
                    text, notes = english[(book, chapter, mapped)], ""
                elif language == "zho":
                    if (book, chapter, verse) in omissions:
                        raise ValueError(f"Unexpected translation of an omitted CUV verse: {relative}:{verse}")
                    text, notes = chinese[book][chapter, mapped]
                else:
                    continue
                if split_chapter and verse in {split["left_verse"], split["right_verse"]}:
                    marker = split["markers"][language]
                    if text.count(marker) != 1:
                        raise ValueError("Reference no longer contains the recorded verse split")
                    left, right = text.split(marker)
                    text = left.strip() if verse == split["left_verse"] else marker + right
                translation.text = text
                if notes:
                    translation.set("notes", notes)
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        etree.indent(tree, space="    ")
        tree.write(str(target), encoding="utf-8", xml_declaration=True, pretty_print=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    build(parser.parse_args().output_dir)
