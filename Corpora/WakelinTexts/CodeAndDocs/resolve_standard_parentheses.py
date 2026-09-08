#!/usr/bin/env python3
"""Resolve the article's parenthesis notation in the STANDARD tier.

Step 5 of generate_xml.sh: after standardize.py, before add_phonology.py.
The original tier is never touched — the parentheses are the article's own
notation and belong in a faithful record of it (POL-017).

The article's key gives `( )` two jobs, and they need opposite treatment.

**Optional material** — `puken-(en)`, `(u)m-lavi`, `ku(a)` — is a real
alternation: the word can be read with the bracketed letters or without them.
A standard tier cannot carry a parenthesis, because no orthography has one, and
choosing either reading silently asserts something the article declines to say.
So the word gets both, through the mechanism the corpus already uses for the
source's slash alternations: `FORM[@kindOf="standard"]` takes the fuller
reading, closest to the printed letter sequence, and `FORM[@kindOf="alternate"]`
takes the reading without the bracketed material (maintainer, 2026-09-07).

The alternate goes on the **word**, and only there. Not on the morpheme, where
the alternation is not expressible — a morpheme whose whole form is optional
would have to alternate with nothing — and where it is not the morpheme's
property anyway: whether the segment is present is a fact about the word.
Morphemes therefore just lose the brackets and keep their letters. And not on
the sentence, for the same reason the corpus's slash alternations stop at the
word: a sentence-level alternate for one optional letter is noise, and a
sentence carrying two of them could only show one, which reads as a claim that
the other did not vary. The sentence FORM carries the fuller reading.

**The uncertainty marker** `(unctn)` is not text at all; it is the article's
annotation that a reading is doubtful. It is dropped from the standard tier
rather than transliterated — otherwise the vowel rules rewrite it, and
`sira(unctn)` reaches the standard tier as `sira(onctn)`, which is nonsense.

Strict by design: it reports what it changed, and fails if a parenthesis
survives in the standard tier.
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


def standard_form(node):
    for f in node.findall("FORM"):
        if f.get("kindOf") == "standard":
            return f
    return None


def add_alternate(node, value):
    f = ET.Element("FORM", {"kindOf": "alternate"})
    f.text = value
    last = max((i for i, c in enumerate(node) if c.tag == "FORM"), default=-1)
    node.insert(last + 1, f)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--xml-dir", default=str(CODE_ROOT.parent / "XML"))
    args = ap.parse_args()

    annotations = alternations = morphemes = 0
    for path in sorted(Path(args.xml_dir).rglob("*.xml")):
        root = ET.parse(path).getroot()
        touched = False
        for sentence in root.findall("S"):
            for word in sentence.findall("W"):
                nodes = [(sentence, "S"), (word, "W")] + [(m, "M") for m in word.findall("M")]
                for node, kind in nodes:
                    form = standard_form(node)
                    if form is None or not form.text or "(" not in form.text:
                        continue
                    text = ANNOTATIONS.sub("", form.text)
                    if text != form.text:
                        annotations += 1
                    text = tidy(text)
                    if "(" not in text:
                        form.text = text
                        touched = True
                        continue
                    form.text = with_material(text)
                    if kind == "W":
                        add_alternate(node, without_material(text))
                        alternations += 1
                    elif kind == "M":
                        morphemes += 1
                    touched = True
        if touched:
            path.write_text(prettify(root), encoding="utf-8")

    print(f"  annotations dropped from the standard tier : {annotations}")
    print(f"  optional material -> standard + alternate  : {alternations}")
    print(f"  morphemes unbracketed                      : {morphemes}")

    left = []
    for path in sorted(Path(args.xml_dir).rglob("*.xml")):
        for form in ET.parse(path).getroot().iter("FORM"):
            if form.get("kindOf") in ("standard", "alternate") and "(" in (form.text or ""):
                left.append((path.name, form.text))
    if left:
        for name, text in left:
            print(f"  !! parenthesis survives in {name}: {text}")
        raise SystemExit("parentheses remain in the standard tier")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
