#!/usr/bin/env python3
"""Resolve the article's parenthesis notation in the ORIGINAL tier.

Step 3 of generate_xml.sh: after clean_xml.py, BEFORE standardize.py, so
standardize derives the standard tier — base and variants alike — from an
original that already carries no parentheses (POL-002, POL-028).

Until 2026-09-09 this ran after standardize and touched the standard tier
only, on the ruling recorded in 694bbc903: "the optional material is handled
with the alternative FORM mechanism, in the standard tier only... The original
tier keeps all of this notation untouched." POL-028, ruled the next day, says
"neither mechanism leaves parentheses in a published FORM", and the maintainer
resolved the conflict on 2026-09-09 in POL-028's favour: the tiers are handled
the same way. Doing it here rather than there also fixed an inconsistency —
the seven alternates this script used to create were the only ones in the bank
spelled in the standard orthography, because they were made after standardize
had run.

The article's key gives `( )` two jobs, and they need opposite treatment.

**Optional material** — `puken-(en)`, `(u)m-lavi`, `ku(a)` — is a real
alternation: the word can be read with the bracketed letters or without them.
No orthography has a parenthesis, and choosing either reading silently asserts
something the article declines to say. So the word gets both readings, through
the POL-028 variant mechanism: the tier's base FORM takes the fuller reading,
closest to the printed letter sequence, and a `ver="alt"` FORM of the same
tier takes the reading without the bracketed material.

The variant goes on the **word**, and only there. Not on the morpheme, where
the alternation is not expressible — a morpheme whose whole form is optional
would have to alternate with nothing — and where it is not the morpheme's
property anyway: whether the segment is present is a fact about the word.
Morphemes therefore just lose the brackets and keep their letters. And not on
the sentence, for the same reason the corpus's slash alternations stop at the
word: a sentence-level variant for one optional letter is noise, and a
sentence carrying two of them could only show one, which reads as a claim that
the other did not vary. The sentence FORM carries the fuller reading.

**The uncertainty marker** `(unctn)` (also `(onctn)`, `(unan)`) is not text at
all; it is the article's annotation that a reading is doubtful. Deleting it
outright would lose a judgement the article deliberately recorded, so it moves
to the element's `@notes` — on the word it qualifies, and on each TRANSL that
carries it (maintainer, 2026-09-09). Where the same marker also appears on the
enclosing sentence FORM it is deleted there: the annotation belongs to the
word, and repeating it up the tree says nothing extra.

A TRANSL whose entire text is the marker is left alone and reported: stripping
it would leave an empty TRANSL, which is a validator error, and choosing a
replacement gloss is a human's call, not this script's.

Strict by design: it reports what it changed, and fails if a parenthesis
survives in any FORM.
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
    return tidy(BRACKETED.sub(r"\1", text))


def without_material(text: str) -> str:
    return tidy(BRACKETED.sub("", text))


def original_form(node):
    for f in node.findall("FORM"):
        if f.get("kindOf") == "original" and f.get("ver") is None:
            return f
    return None


def add_variant(node, value):
    """A ver="alt" FORM in the original tier (POL-028, revised 2026-09-09)."""
    f = ET.Element("FORM", {"kindOf": "original", "ver": "alt"})
    f.text = value
    last = max((i for i, c in enumerate(node) if c.tag == "FORM"), default=-1)
    node.insert(last + 1, f)


def note(element, marker):
    """Record an annotation on the element it qualifies, keeping any note."""
    existing = element.get("notes")
    text = f"source annotation: {marker}"
    element.set("notes", f"{existing} {text}".strip() if existing else text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--xml-dir", default=str(CODE_ROOT.parent / "XML"))
    args = ap.parse_args()

    noted = deleted = alternations = morphemes = 0
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

        # --- optional material, in the original tier ----------------------
        for sentence in root.findall("S"):
            for word in sentence.findall("W"):
                nodes = ([(sentence, "S"), (word, "W")]
                         + [(m, "M") for m in word.findall("M")])
                for node, kind in nodes:
                    form = original_form(node)
                    if form is None or not form.text or "(" not in form.text:
                        continue
                    text = tidy(form.text)
                    form.text = with_material(text)
                    if kind == "W":
                        add_variant(node, without_material(text))
                        alternations += 1
                    elif kind == "M":
                        morphemes += 1
                    touched = True

        if touched:
            path.write_text(prettify(root), encoding="utf-8")

    print(f"  uncertainty marker -> W FORM @notes        : {noted}")
    print(f"  uncertainty marker -> TRANSL @notes        : {transl_noted}")
    print(f"  uncertainty marker deleted (repeat at S)   : {deleted}")
    print(f"  optional material -> base + ver=\"alt\"      : {alternations}")
    print(f"  morphemes unbracketed                      : {morphemes}")
    for name, pid in whole_marker:
        print(f"  .. left alone, whole gloss is the marker: {name} {pid}")

    left = []
    for path in sorted(Path(args.xml_dir).rglob("*.xml")):
        for form in ET.parse(path).getroot().iter("FORM"):
            if "(" in (form.text or ""):
                left.append((path.name, form.text))
    if left:
        for name, text in left:
            print(f"  !! parenthesis survives in {name}: {text}")
        raise SystemExit("parentheses remain in a published FORM")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
