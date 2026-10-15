#!/usr/bin/env python3
"""Handle the article's parenthesis notation, one tier at a time.

The article's key defines `( )` one way only: "in data, probable discrepancy".
The transcriber was unsure of the bracketed letters. Ruled 2026-10-15
(maintainer): "Not variants. The parentheses should be retained in the
original tier, removed in the standard tier. ... The reason is that while the
author was uncertain, we do not have anything else to go on." So:

  --tier original  (step 3, after clean_xml, before standardize)
      The parentheses stay, as printed: `puken-(en)`, `(u)m-lavi`, `ku(a)`.
      No reading is chosen and no variant is made. Only the uncertainty
      marker is handled (below).
  --tier standard  (step 5b, after standardize)
      The parentheses are removed and the bracketed letters kept, so the
      standard tier reads the fuller form: `puken-en`, `um-lavi`, `kua`.
      Strict: fails if a parenthesis survives in a standard FORM.

This supersedes the 2026-09-09 handling, which resolved each bracket in the
original tier into a base FORM (with the letters) plus a ver="alt" FORM
(without them), and before that the 694bbc903 handling (standard tier only).

**The uncertainty marker** `(unctn)` (also `(onctn)`, `(unan)`) is not text at
all; it is the article's annotation that a reading is doubtful. Deleting it
outright would lose a judgement the article deliberately recorded, so it moves
to the element's `@notes` — on the word it qualifies, and on each TRANSL that
carries it (maintainer, 2026-09-09). Where the same marker also appears on the
enclosing sentence FORM it is deleted there: the annotation belongs to the
word, and repeating it up the tree says nothing extra. This runs in the
original-tier step, before standardize, so neither tier carries the marker.

A TRANSL whose entire text is the marker is left alone and reported: stripping
it would leave an empty TRANSL, which is a validator error, and choosing a
replacement gloss is a human's call, not this script's.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import xml.etree.ElementTree as ET

CODE_ROOT = Path(__file__).resolve().parent
BANK_ROOT = CODE_ROOT.parents[2]
sys.path.insert(0, str(BANK_ROOT))
from QC.utilities._prettify import prettify  # noqa: E402

# The article's own abbreviations, which are annotation rather than letters.
ANNOTATIONS = re.compile(r"\((?:unctn|onctn|unan)\)", re.IGNORECASE)
BRACKETED = re.compile(r"\(([^()]*)\)")


def tidy(text: str) -> str:
    """Collapse a hyphen left dangling by a removed segment."""
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-")


def with_material(text: str) -> str:
    """The fuller reading: brackets removed, bracketed letters kept."""
    return tidy(BRACKETED.sub(r"\1", text))


def note(element, marker):
    """Record an annotation on the element it qualifies, keeping any note."""
    existing = element.get("notes")
    text = f"source annotation: {marker}"
    element.set("notes", f"{existing} {text}".strip() if existing else text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--xml-dir", default=str(CODE_ROOT.parent / "XML"))
    ap.add_argument("--tier", choices=("original", "standard"), default="original")
    args = ap.parse_args()
    if args.tier == "standard":
        return strip_standard_tier(Path(args.xml_dir))

    noted = deleted = 0
    transl_noted = 0
    whole_marker: list[tuple[str, str]] = []

    for path in sorted(Path(args.xml_dir).rglob("*.xml")):
        root = ET.parse(path).getroot()
        touched = False

        # --- the uncertainty marker, wherever it appears -------------------
        for parent in root.iter():
            for child in list(parent):
                if child.tag not in ("FORM", "TRANSL") or not child.text:
                    continue
                found = ANNOTATIONS.search(child.text)
                if not found:
                    continue
                stripped = tidy(ANNOTATIONS.sub("", child.text)).strip()
                if not stripped:
                    # The whole gloss is the marker; emptying it is invalid
                    # XML and picking a replacement is a human's call.
                    whole_marker.append((path.name, parent.get("id") or "?"))
                    continue
                child.text = re.sub(r"\s{2,}", " ", stripped)
                if child.tag == "TRANSL":
                    note(child, found.group(0))
                    transl_noted += 1
                elif parent.tag == "W":
                    note(child, found.group(0))
                    noted += 1
                else:
                    # Same marker repeated up the tree: it belongs to the word.
                    deleted += 1
                touched = True

        if touched:
            path.write_text(prettify(root), encoding="utf-8")

    print(f"  uncertainty marker -> W FORM @notes        : {noted}")
    print(f"  uncertainty marker -> TRANSL @notes        : {transl_noted}")
    print(f"  uncertainty marker deleted (repeat at S)   : {deleted}")
    for name, pid in whole_marker:
        print(f"  .. left alone, whole gloss is the marker: {name} {pid}")

    kept = sum(1 for path in sorted(Path(args.xml_dir).rglob("*.xml"))
               for form in ET.parse(path).getroot().iter("FORM")
               if form.get("kindOf") == "original" and "(" in (form.text or ""))
    print(f"  original-tier FORMs keeping the article's ( ) : {kept}")
    return 0


def strip_standard_tier(xml_dir: Path) -> int:
    """Remove the parentheses from every standard-tier FORM (step 5b)."""
    changed = 0
    for path in sorted(xml_dir.rglob("*.xml")):
        root = ET.parse(path).getroot()
        touched = False
        for form in root.iter("FORM"):
            if form.get("kindOf") == "standard" and "(" in (form.text or ""):
                form.text = with_material(form.text)
                changed += 1
                touched = True
        if touched:
            path.write_text(prettify(root), encoding="utf-8")
    print(f"  standard-tier FORMs with ( ) removed        : {changed}")
    left = [(path.name, form.text) for path in sorted(xml_dir.rglob("*.xml"))
            for form in ET.parse(path).getroot().iter("FORM")
            if form.get("kindOf") == "standard" and any(c in (form.text or "") for c in "()")]
    if left:
        for name, text in left:
            print(f"  !! parenthesis survives in {name}: {text}")
        raise SystemExit("parentheses remain in a standard-tier FORM")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
