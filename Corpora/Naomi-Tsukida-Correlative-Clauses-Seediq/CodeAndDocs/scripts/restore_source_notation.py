#!/usr/bin/env python3
"""Restore exact source square brackets changed by the shared XML cleaner."""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path


ORIGINAL_RESTORATIONS = {
    "tsukida2014_seediq_S018": (
        "Wada qeduriq ka se'diq (p-en-huqil rebiq-an).",
        "Wada qeduriq ka se'diq [p-en-huqil rebiq-an].",
    ),
    "tsukida2014_seediq_S019": (
        "Wada qeduriq ka (p-en-huqil rebiq-an ka se'diq).",
        "Wada qeduriq ka [p-en-huqil rebiq-an ka se'diq].",
    ),
    "tsukida2014_seediq_S020": (
        "S-em-en-teruŋ=ku se'diq (m-en-uway patas rebiq-an).",
        "S-em-en-teruŋ=ku se'diq [m-en-uway patas rebiq-an].",
    ),
    "tsukida2014_seediq_S021": (
        "S-em-en-teruŋ=ku (m-en-uway patas rebiq-an ka se'diq).",
        "S-em-en-teruŋ=ku [m-en-uway patas rebiq-an ka se'diq].",
    ),
    "tsukida2014_seediq_S029": (
        "(P-en-huqil rebiq-an ka se'diq) 'u, wada qeduriq.",
        "[P-en-huqil rebiq-an ka se'diq] 'u, wada qeduriq.",
    ),
}
TRANSLATION_RESTORATIONS = {
    "tsukida2014_seediq_S020": (
        "I met (the man who gave Rubiq a book).",
        "I met [the man who gave Rubiq a book].",
    ),
    "tsukida2014_seediq_S021": (
        "I met (the man who gave Rubiq a book).",
        "I met [the man who gave Rubiq a book].",
    ),
}


def restore_value(current: str | None, cleaned: str, source: str, location: str) -> str:
    if current == source:
        return source
    if current != cleaned:
        raise ValueError(f"Unexpected cleaner output at {location}: {current!r}")
    return source


def process(path: Path) -> tuple[int, int]:
    tree = ET.parse(path)
    root = tree.getroot()
    by_id = {sentence.get("id", ""): sentence for sentence in root.findall("S")}
    changed = 0
    for sentence_id, (cleaned, source) in ORIGINAL_RESTORATIONS.items():
        sentence = by_id.get(sentence_id)
        if sentence is None:
            raise ValueError(f"Missing source-notation sentence: {sentence_id}")
        form = sentence.find("FORM[@kindOf='original']")
        if form is None:
            raise ValueError(f"Missing original form: {sentence_id}")
        restored = restore_value(form.text, cleaned, source, sentence_id)
        if restored != form.text:
            form.text = restored
            changed += 1
    for sentence_id, (cleaned, source) in TRANSLATION_RESTORATIONS.items():
        sentence = by_id[sentence_id]
        translation = sentence.find("TRANSL")
        if translation is None:
            raise ValueError(f"Missing translation: {sentence_id}")
        restored = restore_value(
            translation.text, cleaned, source, f"{sentence_id}/TRANSL"
        )
        if restored != translation.text:
            translation.text = restored
            changed += 1
    if changed:
        ET.indent(root, space="    ")
        tree.write(path, encoding="utf-8", xml_declaration=True)
    return len(ORIGINAL_RESTORATIONS) + len(TRANSLATION_RESTORATIONS), changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, required=True)
    args = parser.parse_args()
    paths = [args.path] if args.path.is_file() else sorted(args.path.rglob("*.xml"))
    if len(paths) != 1:
        raise SystemExit(f"Expected one corpus XML file; found {len(paths)}")
    expected, changed = process(paths[0])
    print(f"Restored {changed} source value(s); {expected} restoration(s) verified.")


if __name__ == "__main__":
    main()
