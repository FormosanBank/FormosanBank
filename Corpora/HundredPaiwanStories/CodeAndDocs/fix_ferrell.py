#!/usr/bin/env python3
"""Resolve Ferrell question-mark and glottal-stop ambiguity in XML tiers."""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import regex as re


FORM_RULES = (
    (re.compile(r"(\p{L})'$"), r"\1?"),
    (re.compile(r"'(\")$"), r"?\1"),
    (re.compile(r"(\p{L})'(\")"), r"\1?\2"),
)
PHON_RULES = (
    (re.compile(r"(\p{L})ʔ$"), r"\1"),
    (re.compile(r"ʔ(\")$"), r"\1"),
    (re.compile(r"(\p{L})ʔ(\")"), r"\1\2"),
)


def apply_rules(value: str, rules: tuple[tuple[re.Pattern, str], ...]) -> str:
    for pattern, replacement in rules:
        value = pattern.sub(replacement, value)
    return value


def fix(corpora_path: Path) -> tuple[int, int]:
    files_changed = 0
    values_changed = 0
    for path in sorted(corpora_path.rglob("*.xml")):
        tree = ET.parse(path)
        root = tree.getroot()
        file_changes = 0
        for element in root.iter():
            if not element.text:
                continue
            if element.tag == "FORM":
                revised = apply_rules(element.text, FORM_RULES)
            elif element.tag == "PHON":
                revised = apply_rules(element.text, PHON_RULES)
            else:
                continue
            if revised != element.text:
                element.text = revised
                file_changes += 1
        if file_changes:
            ET.indent(root, space="    ")
            tree.write(path, encoding="utf-8", xml_declaration=True)
            files_changed += 1
            values_changed += file_changes
    return files_changed, values_changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpora-path", type=Path, default=Path("XML"))
    args = parser.parse_args()
    files, values = fix(args.corpora_path.resolve())
    print(f"files_changed={files}")
    print(f"values_changed={values}")


if __name__ == "__main__":
    main()
