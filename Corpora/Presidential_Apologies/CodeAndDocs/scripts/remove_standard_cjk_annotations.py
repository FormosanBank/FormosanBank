#!/usr/bin/env python3
"""Remove Mandarin parenthetical annotations from the standard FORM tier."""

from __future__ import annotations

import argparse
import importlib
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

_IDEOGRAPH = re.compile(r"[㐀-鿿豈-﫿]")
_LATIN = re.compile(r"[A-Za-z]")
_GROUP = re.compile(r"\([^()]*\)")


@dataclass(frozen=True)
class FormosanBankTools:
    add_phonology: ModuleType
    dialect_inventory: ModuleType


def load_formosanbank_tools(root: Path) -> FormosanBankTools:
    root = root.resolve()
    if not (root / "QC" / "utilities" / "add_phonology.py").is_file():
        raise ValueError(f"not a FormosanBank checkout: {root}")
    sys.path.insert(0, str(root))
    try:
        add_phonology = importlib.import_module("QC.utilities.add_phonology")
        dialect_inventory = importlib.import_module(
            "QC.validation._dialect_inventory"
        )
    finally:
        sys.path.pop(0)
    return FormosanBankTools(add_phonology, dialect_inventory)


def is_annotation(group: str) -> bool:
    inner = group[1:-1]
    return bool(_IDEOGRAPH.search(inner)) and not _LATIN.search(inner)


def remove_annotations(text: str) -> tuple[str, int]:
    """Remove CJK-only parenthetical groups and return the removal count."""
    output: list[str] = []
    position = 0
    removed = 0
    for match in _GROUP.finditer(text):
        if not is_annotation(match.group(0)):
            continue
        start, end = match.start(), match.end()
        while start > position and text[start - 1] == " ":
            start -= 1
        while end < len(text) and text[end] == " ":
            end += 1
        start = max(start, position)
        left = text[start - 1] if start > 0 else ""
        right = text[end] if end < len(text) else ""
        if right in ".,;:!?)":
            separator = ""
        elif right == '"' and text[:start].count('"') % 2 == 1:
            separator = ""
        elif left in ("(", "") or right == "":
            separator = ""
        else:
            separator = " "
        output.append(text[position:start])
        output.append(separator)
        position = end
        removed += 1
    output.append(text[position:])
    if not removed:
        return text, 0
    return "".join(output).strip(), removed


def process_file(
    path: Path,
    tools: FormosanBankTools,
    dry_run: bool,
) -> tuple[int, int]:
    tree = ET.parse(path)
    root = tree.getroot()
    text_element = root if root.tag == "TEXT" else root.find(".//TEXT")
    if text_element is None:
        raise ValueError(f"{path}: missing TEXT element")
    language_code = (
        text_element.get("xml:lang", "")
        or text_element.get("{http://www.w3.org/XML/1998/namespace}lang", "")
        or text_element.get("lang", "")
    ).strip()
    language = tools.dialect_inventory.ISO_TO_LANGUAGE.get(
        language_code, language_code
    )
    dialect = text_element.get("dialect", "").strip() or "default"
    standard_profile = tools.add_phonology.load_profile(
        tools.dialect_inventory.standard_orthography(language),
        language,
        dialect,
    )
    original_profile = tools.add_phonology.load_profile(
        "Ortho113", language, dialect
    )

    removed = 0
    changed = 0
    for sentence in root.iter("S"):
        original = sentence.find('FORM[@kindOf="original"]')
        standard = sentence.find('FORM[@kindOf="standard"]')
        if original is None or not original.text or standard is None or not standard.text:
            continue
        new_standard, standard_count = remove_annotations(standard.text)
        if standard_count:
            standard.text = new_standard
            removed += standard_count
            changed += 1
        masked_original, original_count = remove_annotations(original.text)
        if standard_profile is not None:
            phon = sentence.find('PHON[@kindOf="standard"]')
            if phon is not None:
                new_phon = tools.add_phonology.phonologize(
                    standard.text, standard_profile
                )
                if phon.text != new_phon:
                    phon.text = new_phon
                    changed += 1
        if original_profile is not None and original_count:
            phon = sentence.find('PHON[@kindOf="original"]')
            if phon is not None:
                new_phon = tools.add_phonology.phonologize(
                    masked_original, original_profile
                )
                if phon.text != new_phon:
                    phon.text = new_phon
                    changed += 1

    if changed and not dry_run:
        xml_string = tools.add_phonology.prettify(root)
        xml_string = "\n".join(
            line for line in xml_string.splitlines() if line.strip()
        )
        path.write_text(xml_string, encoding="utf-8")
    return removed, changed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formosanbank-root", type=Path, required=True)
    parser.add_argument(
        "--xml-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "XML",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tools = load_formosanbank_tools(args.formosanbank_root)
    files = sorted(args.xml_dir.glob("*/*.xml"))
    if not files:
        print(f"no XML files in {args.xml_dir}", file=sys.stderr)
        return 1
    total_removed = 0
    total_changed = 0
    for path in files:
        removed, changed = process_file(path, tools, args.dry_run)
        if removed or changed:
            print(
                f"{path.parent.name}: removed {removed} annotations; "
                f"updated {changed} elements"
            )
        total_removed += removed
        total_changed += changed
    verb = "would remove" if args.dry_run else "removed"
    print(
        f"{verb} {total_removed} CJK parenthetical annotations; "
        f"updated {total_changed} elements"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
