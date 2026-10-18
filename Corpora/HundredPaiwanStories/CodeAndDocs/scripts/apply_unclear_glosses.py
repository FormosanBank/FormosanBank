#!/usr/bin/env python3
"""Write the source's unknown-gloss markers as ``<UNCLEAR/>``.

Ferrell's interlinear glosses mark a morpheme the analyst could not identify
with a bare ``?`` (e.g. 001S7, morpheme ``ta`` glossed ``?``). FormosanBank
has an element for exactly that, ``<UNCLEAR/>``, so the build writes it in
place of the question mark. Maintainer's rulings, 2026-10-17:

* "B. A, plus ? used as a placeholder inside a gloss", where A = "Convert
  glosses that are exactly ? or ??". A W or M ``TRANSL`` whose whole text
  is ``?``, ``??`` or ``???`` (ASCII or full-width) becomes
  ``<TRANSL ...><UNCLEAR/></TRANSL>`` with its attributes unchanged.
* "B. Glosses UNCLEAR; sentence translations omitted": an S-level
  ``TRANSL`` whose whole text is such a marker is not emitted.
* "if the S FORM is simply <UNCLEAR/>, no Ws. If the W FORM is
  <UNCLEAR />, no Ms under it." Nothing in this build writes UNCLEAR into a
  FORM, so this script only checks that no such case exists and fails if
  one does.

A ``?`` that is one piece of a longer gloss (``?-what``, ``stat-exact-?``)
is converted only for the glosses listed in
``unclear_gloss_placeholders.tsv`` (columns ``gloss``, ``lang``); the
maintainer decides those per gloss (2026-10-17, for this corpus: "All rows
in this corpus: placeholder → UNCLEAR"). In a listed gloss, every ``?`` piece
bounded by ``-``, ``=``, ``.``, whitespace or the ends of the string becomes
``<UNCLEAR/>``; a ``?`` attached to a word (``LIG?``) is kept. A listed row
that matches no gloss, or matches a gloss with no such piece, is an error.

This runs last, after normalize_sentence_standards.py and before the
validators, so no later step re-indents the XML: ``ET.indent`` (used by the
corpus's own scripts) would put whitespace inside a TRANSL whose only
content is ``<UNCLEAR/>``. Files are written back with their own XML
declaration line and otherwise exactly as lxml serialises them, which is
byte-identical to the input for everything this script does not change.
Idempotent: a TRANSL that already holds an UNCLEAR is left alone.

Usage
-----
    python scripts/apply_unclear_glosses.py --corpora-path <XML dir>
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLACEHOLDERS = ROOT / "unclear_gloss_placeholders.tsv"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

MARK = "[?？]{1,3}"
WHOLE_MARKER = re.compile(MARK)
# A marker standing as a whole gloss piece: bounded by - = . whitespace or
# the ends of the string on both sides.
PIECE = re.compile(rf"(?<![^-=.\s]){MARK}(?![^-=.\s])")


def load_placeholders(path: Path) -> set[tuple[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != ["gloss", "lang"]:
            raise ValueError(f"{path}: header must be gloss<TAB>lang")
        rows = [(row["gloss"], row["lang"]) for row in reader]
    if len(set(rows)) != len(rows):
        raise ValueError(f"{path}: duplicate rows")
    for gloss, lang in rows:
        if not gloss or not lang:
            raise ValueError(f"{path}: empty gloss or lang in row {gloss!r}")
        if not PIECE.search(gloss):
            raise ValueError(f"{path}: {gloss!r} has no ? standing as a gloss piece")
    return set(rows)


def is_only_unclear(element: etree._Element) -> bool:
    """True when ``element`` holds an UNCLEAR and no other text."""
    return element.find("UNCLEAR") is not None and not "".join(
        element.itertext()
    ).strip()


def as_written(transl: etree._Element) -> str:
    """The gloss with each UNCLEAR child read back as "?"."""
    parts = [transl.text or ""]
    for child in transl:
        parts.append("?" if child.tag == "UNCLEAR" else "".join(child.itertext()))
        parts.append(child.tail or "")
    return "".join(parts)


def replace_pieces(transl: etree._Element, text: str) -> None:
    """Rewrite ``transl`` as mixed content with UNCLEAR for each ? piece."""
    pieces = PIECE.split(text)
    transl.text = pieces[0] or None
    for following in pieces[1:]:
        unclear = etree.SubElement(transl, "UNCLEAR")
        unclear.tail = following or None


def convert_tree(
    root: etree._Element,
    placeholders: set[tuple[str, str]],
    stats: Counter,
    used: set[tuple[str, str]],
) -> bool:
    changed = False
    for sentence in root.iter("S"):
        for form in sentence.iter("FORM"):
            if form.getparent().tag in {"S", "W"} and is_only_unclear(form):
                raise ValueError(
                    f"{form.getparent().get('id')}: FORM is only <UNCLEAR/>; "
                    "the ruling then removes the tier below it, which this "
                    "build does not implement"
                )
        for transl in list(sentence.iter("TRANSL")):
            if len(transl):
                # Already converted (or other mixed content). A listed
                # placeholder gloss converted on an earlier run still counts
                # as matched, so a second run is a no-op, not an error.
                written = (as_written(transl), transl.get(XML_LANG, ""))
                used.update(
                    key
                    for key in placeholders
                    if (PIECE.sub("?", key[0]), key[1]) == written
                )
                continue
            text = transl.text or ""
            level = transl.getparent().tag
            if level == "S":
                if WHOLE_MARKER.fullmatch(text.strip()):
                    sentence.remove(transl)
                    stats["omitted_sentence_translations"] += 1
                    changed = True
                continue
            if level not in {"W", "M"}:
                continue
            if WHOLE_MARKER.fullmatch(text.strip()):
                transl.text = None
                etree.SubElement(transl, "UNCLEAR")
                stats[f"unclear_{level.lower()}_glosses"] += 1
                changed = True
                continue
            key = (text, transl.get(XML_LANG, ""))
            if key in placeholders:
                replace_pieces(transl, text)
                used.add(key)
                stats[f"placeholder_{level.lower()}_glosses"] += 1
                changed = True
    return changed


def write_preserving_declaration(path: Path, tree: etree._ElementTree) -> None:
    raw = path.read_bytes()
    declaration = raw.split(b"\n", 1)[0] if raw.startswith(b"<?xml") else None
    body = etree.tostring(tree.getroot(), encoding="unicode").encode("utf-8")
    trailing = raw[len(raw.rstrip()):]
    out = (declaration + b"\n" if declaration is not None else b"") + body + trailing
    path.write_bytes(out)


def apply(corpora_path: Path, placeholders_path: Path) -> Counter:
    placeholders = load_placeholders(placeholders_path)
    stats: Counter = Counter()
    used: set[tuple[str, str]] = set()
    changed = []
    for path in sorted(corpora_path.rglob("*.xml")):
        tree = etree.parse(str(path))
        if convert_tree(tree.getroot(), placeholders, stats, used):
            changed.append((path, tree))
    unused = sorted(placeholders - used)
    if unused:
        raise ValueError(
            f"{placeholders_path.name}: rows match no gloss in the XML: {unused}"
        )
    # Nothing is written until every check above has passed.
    for path, tree in changed:
        write_preserving_declaration(path, tree)
        stats["files_changed"] += 1
    return stats


REPORTED = (
    "unclear_w_glosses",
    "unclear_m_glosses",
    "placeholder_w_glosses",
    "placeholder_m_glosses",
    "omitted_sentence_translations",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpora-path", type=Path, required=True)
    parser.add_argument("--placeholders", type=Path, default=DEFAULT_PLACEHOLDERS)
    args = parser.parse_args()
    stats = apply(args.corpora_path.resolve(), args.placeholders)
    for key in REPORTED:
        print(f"{key}={stats[key]}")


if __name__ == "__main__":
    main()
