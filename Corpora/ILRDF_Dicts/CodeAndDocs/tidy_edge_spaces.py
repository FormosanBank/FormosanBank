#!/usr/bin/env python3
"""Remove the space next to punctuation at the very start or end of a FORM.

Maintainer ruling 2026-10-18 (asked why generated PHON had spaces at its
edges): "Revert; fix ILRDF text (Recommended)", then for the remaining forms
"Same treatment (Recommended) -- Also remove the space next to punctuation at
the start/end of the text (" Dopohen -> "Dopohen, ( vava ) -> (vava), end
' ,' / ' ...' -> ',' / '...') and close up the headwords (caca - -> caca-).
Then no ILRDF PHON has an outer space."

Only the ORIGINAL tier is edited (standardize.py derives the standard tier
from it afterwards), in the sentence files and the headword files, and only
these patterns:

  final       a space before sentence-final . ? ! at the end
              ('tukamia .' -> 'tukamia.')
  leading_dot a stray period before the first word
              ('. Aiza ...' -> 'Aiza ...', '.Ansahanava' -> 'Ansahanava')
  open        a space after opening punctuation at the start
              ('" Dopohen' -> '"Dopohen')
  close       a space before closing punctuation at the end
              ('cinhuz-a. "' -> 'cinhuz-a."', 'ismut ,' -> 'ismut,',
               'caca -' -> 'caca-', 'no ...' -> 'no...')
  bracket     the spaces inside a bracket group that ends the text
              ('( vava ).' -> '(vava).')

Run after clean_xml.py (which turns full-width ？！． into ASCII and so
exposes some of these spaces) and before standardize.py:

    python tidy_edge_spaces.py --xml-dir ../XML --report docs/edge_space_report.csv
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import re

from lxml import etree

#: The final run may itself hold a space ('wah ! .' -> 'wah!.').
FINAL = re.compile(r"\s+([.?!](?:\s*[.?!])*)$")
LEADING_DOT = re.compile(r"^\.\s*(?=\w)")
OPEN = re.compile(r"^([\"“「『(（]+)\s+")
CLOSE = re.compile(r"\s+([,…\-\"”」』)）][,…\-\"”」』)）.?!]*)$")
#: Only a group whose closing bracket has a space before it: that space is
#: what reaches the edge of PHON. Its opening space goes too ("( vava ) ->
#: (vava)").
BRACKET = re.compile(r"([(（])\s*([^()（）]*?)\s+([)）])([.?!]*)$")


def _bracket(text: str) -> str:
    match = BRACKET.search(text)
    if match is None:
        return text
    opening, body, closing, tail = match.groups()
    return text[:match.start()] + f"{opening}{body.strip()}{closing}{tail}"


RULES = (
    ("leading_dot", lambda t: LEADING_DOT.sub("", t, count=1)),
    ("open", lambda t: OPEN.sub(r"\1", t, count=1)),
    ("bracket", _bracket),
    ("final", lambda t: FINAL.sub(lambda m: re.sub(r"\s+", "", m.group(1)), t, count=1)),
    ("close", lambda t: CLOSE.sub(r"\1", t, count=1)),
)


def tidy(text: str) -> tuple[str, list[str]]:
    """Return the tidied text and the names of the rules that changed it."""
    applied = []
    for name, rule in RULES:
        new = rule(text)
        if new != text:
            applied.append(name)
            text = new
    return text, applied


def process(xml_dir: Path, rows: list[dict[str, str]]) -> int:
    changed_total = 0
    for path in sorted(xml_dir.rglob("*.xml")):
        tree = etree.parse(str(path))
        changed = 0
        for sentence in tree.getroot().iter("S"):
            for form in sentence.findall('FORM[@kindOf="original"]'):
                if form.text is None or len(form):
                    continue
                new, applied = tidy(form.text)
                if not applied:
                    continue
                rows.append({"file": path.relative_to(xml_dir).as_posix(),
                             "id": sentence.get("id"), "ver": form.get("ver") or "",
                             "rules": " ".join(applied), "before": form.text,
                             "after": new})
                form.text = new
                changed += 1
        if changed:
            tree.write(str(path), encoding="UTF-8", xml_declaration=True)
        changed_total += changed
    return changed_total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--xml-dir", type=Path,
                        default=Path(__file__).resolve().parents[1] / "XML")
    parser.add_argument("--report", type=Path,
                        default=Path(__file__).resolve().parent / "docs" / "edge_space_report.csv")
    args = parser.parse_args()
    rows: list[dict[str, str]] = []
    total = process(args.xml_dir.resolve(), rows)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["file", "id", "ver", "rules", "before", "after"],
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    counts: dict[str, int] = {}
    for row in rows:
        for name in row["rules"].split():
            counts[name] = counts.get(name, 0) + 1
    print(f"edge spaces: {total} original FORMs changed; by rule: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
