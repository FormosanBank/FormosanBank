#!/usr/bin/env python3
"""Remove the author's "(a)" from the standard tier.

Maintainer, 2026-11-26: "Throughout, Yedda includes `(a)` in her
segmentations where one `a` immediately follows another `a` and so is not
pronounced. These `(a)`s should be removed from the standard tier. This will
require modifying the standard tier (which we don't normally do) as part of
standardization, but I think we need to do it here."

Runs after standardize.py and before add_phonology.py, so the standard PHON is
made from the edited FORM. Only FORM kindOf="standard" (base and variants) is
touched, and only where the letter before "(a)" (skipping spaces and hyphens)
is "a". The original tier keeps her text. Idempotent.

Usage: strip_unpronounced_a.py --corpora_path <dir>
"""

from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path

UNPRONOUNCED_A = re.compile(r"(?<=[aA])([\s-]*)\(a\)")


def strip(text: str) -> str:
    text = UNPRONOUNCED_A.sub(lambda m: m.group(1).rstrip() if m.group(1).strip() == "" else m.group(1), text)
    return re.sub(r"  +", " ", text).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--corpora_path", required=True)
    args = parser.parse_args()
    for path in sorted(Path(args.corpora_path).rglob("*.xml")):
        tree = ET.parse(path)
        changed = []
        for element in tree.getroot().iter():
            if element.tag not in {"S", "W", "M"}:
                continue
            for form in element.findall("FORM[@kindOf='standard']"):
                if form.text and "(a)" in form.text:
                    new = strip(form.text)
                    if new != form.text:
                        changed.append((element.get("id"), form.text, new))
                        form.text = new
        if changed:
            tree.write(path, encoding="UTF-8", xml_declaration=True)
        for element_id, old, new in changed:
            print(f"{path.name} {element_id}: {old!r} -> {new!r}")
        print(f"{path.name}: {len(changed)} standard FORM(s) without the unpronounced (a)")


if __name__ == "__main__":
    main()
