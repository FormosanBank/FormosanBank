#!/usr/bin/env python3
"""Apply shared C012 to one exact NTU S tier that has W but no M tiers.

The shared standardizer intentionally runs C012 only when a sentence has an
M tier.  NTU Bunun 60_S_16 has source-aligned W tiers but no recoverable M
tiers, so its S-level standard FORM otherwise retains a clitic ``=`` marker
and triggers V126.  This guarded pass calls the shared C012 implementation
for that exact sentence after the final standard-tier refresh.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from lxml import etree


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BANK = Path(
    os.environ.get("FORMOSANBANK_ROOT", REPO.parent / "FormosanBank")
).resolve()
if str(BANK) not in sys.path:
    sys.path.insert(0, str(BANK))

from QC.utilities.standardize import _process_standard_hyphens  # noqa: E402


RELATIVE = Path("Sentences/Bunun/Bunun.xml")
SENTENCE_ID = "60_S_16"
SOURCE_FORM = "mansia Tainancia hai na=unau unku tu asang."
STANDARD_FORM = "mansia Tainancia hai naunau unku tu asang."
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def repair(xml_dir: Path) -> bool:
    path = xml_dir / RELATIVE
    if not path.is_file():
        raise AssertionError(f"expected XML file missing: {path}")
    tree = etree.parse(str(path))
    root = tree.getroot()
    if root.get(XML_LANG) != "bnn":
        raise AssertionError(
            f"expected bnn root language in {path}; found {root.get(XML_LANG)!r}"
        )
    matches = root.xpath(f"./S[@id='{SENTENCE_ID}']")
    if len(matches) != 1:
        raise AssertionError(
            f"expected one {SENTENCE_ID} in {path}; found {len(matches)}"
        )
    sentence = matches[0]
    original = sentence.find("FORM[@kindOf='original']")
    standard = sentence.find("FORM[@kindOf='standard']")
    if original is None or original.text != SOURCE_FORM:
        raise AssertionError(
            f"source FORM drifted for {SENTENCE_ID}; expected {SOURCE_FORM!r}, "
            f"found {None if original is None else original.text!r}"
        )
    if sentence.find(".//M") is not None:
        raise AssertionError(
            f"{SENTENCE_ID} now has M tiers; shared standardize should own C012"
        )
    if standard is None or not standard.text:
        raise AssertionError(f"standard FORM missing for {SENTENCE_ID}")
    if standard.text == STANDARD_FORM:
        return False
    if standard.text != SOURCE_FORM:
        raise AssertionError(
            f"standard FORM drifted for {SENTENCE_ID}; expected "
            f"{SOURCE_FORM!r}, found {standard.text!r}"
        )

    rendered = _process_standard_hyphens(
        standard.text,
        str(path),
        SENTENCE_ID,
        "bnn",
        None,
        False,
        None,
    )
    if rendered != STANDARD_FORM:
        raise AssertionError(
            f"shared C012 output drifted for {SENTENCE_ID}; expected "
            f"{STANDARD_FORM!r}, found {rendered!r}"
        )
    standard.text = rendered
    path.write_bytes(etree.tostring(tree, xml_declaration=True, encoding="UTF-8"))
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml-dir", type=Path, default=REPO / "XML")
    args = parser.parse_args()
    changed = repair(args.xml_dir.resolve())
    print(
        "unsegmented standard clitic repair: "
        + ("1 sentence updated" if changed else "already current")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
