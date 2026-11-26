#!/usr/bin/env python3
"""Build the Yedda prose dictionary: forms the author glosses only in her notes.

Maintainer, 2026-11-26 (voice page round 3): "add a dictionary XML that
consists of (so far) such `meqaca` `me-qaca` `AV-grow up`"; round 6: "Build it
as shown", with the entries in ``prose_dictionary.tsv`` (one row per entry:
her form, her segmentation, the piece glosses her same note gives, her
meaning, and the word whose gloss it comes from).

Writes ``XML/Paiwan/Paiwan_Yedda_Blog_Dictionary.xml`` with the original tier
only; the shared steps in generate_xml.sh then add the standard tier and
phonology, as for the blog file. The voice and mood columns of the table are
data for the voice analyses and are not written to the XML.
"""

from __future__ import annotations

import csv
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "prose_dictionary.tsv"
BLOG = ROOT.parent / "XML/Paiwan/Paiwan_Yedda_Blog.xml"
OUTPUT = ROOT.parent / "XML/Paiwan/Paiwan_Yedda_Blog_Dictionary.xml"
HEADER = [
    "entry_id", "form", "word_form", "morphemes", "translation",
    "source_word_id", "source_word", "voice", "mood", "voice_basis", "hold",
]
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
ALT = re.compile(r"^(.*?) \[alt (.+)\]$")


def forms(cell: str) -> tuple[str, str | None]:
    """'puhanaan [alt puhanan]' -> base and POL-028 variant (both readings of her
    optional (a); maintainer, 2026-11-26: "Spell out both readings as variants")."""
    match = ALT.match(cell)
    return (match.group(1), match.group(2)) if match else (cell, None)


def add_forms(parent: ET.Element, cell: str, notes: str | None = None) -> None:
    base, alt = forms(cell)
    attrs = {"kindOf": "original"}
    if notes:
        attrs["notes"] = notes
    ET.SubElement(parent, "FORM", attrs).text = base
    if alt:
        ET.SubElement(parent, "FORM", {"kindOf": "original", "ver": "alt"}).text = alt


def main() -> None:
    with TABLE.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
        if reader.fieldnames != HEADER:
            raise SystemExit(f"{TABLE.name}: unexpected header {reader.fieldnames}")
        rows = list(reader)
    blog = ET.parse(BLOG).getroot()
    sentences = {s.get("id"): s for s in blog.findall("S")}
    words = {w.get("id"): w for w in blog.iter("W")}

    text = ET.Element("TEXT", {
        "id": blog.get("id") + "_Dictionary",
        XML_LANG: blog.get(XML_LANG),
        "source": blog.get("source"),
        "dialect": blog.get("dialect"),
        "citation": blog.get("citation"),
        "BibTeX_citation": blog.get("BibTeX_citation"),
        "copyright": blog.get("copyright"),
    })
    held = [row for row in rows if row["hold"]]
    rows = [row for row in rows if not row["hold"]]
    for row in held:
        print(f"Held back: {row['entry_id']} {row['word_form']}: {row['hold']}")
    for row in rows:
        source_word = words.get(row["source_word_id"])
        if source_word is None:
            raise SystemExit(f"{TABLE.name}: {row['entry_id']} names no word {row['source_word_id']}")
        sentence_id = row["source_word_id"].rsplit("W", 1)[0]
        base = next(
            f.text for f in source_word.findall("FORM")
            if f.get("kindOf") == "original" and f.get("ver") is None
        )
        if base != row["source_word"]:
            raise SystemExit(
                f"{TABLE.name}: {row['entry_id']}: {row['source_word_id']} is {base!r}, "
                f"not {row['source_word']!r}"
            )
        entry_id = row["entry_id"]
        entry = ET.SubElement(text, "S", {"id": entry_id})
        if sentences[sentence_id].get("source"):
            entry.set("source", sentences[sentence_id].get("source"))
        add_forms(entry, row["form"], f"From the author's gloss of {row['source_word']} ({row['source_word_id']})")
        translation = ET.SubElement(entry, "TRANSL", {XML_LANG: "eng"})
        translation.text = row["translation"]
        word = ET.SubElement(entry, "W", {"id": f"{entry_id}W1"})
        add_forms(word, row["word_form"])
        for index, piece in enumerate(row["morphemes"].split(" | "), 1):
            morph_form, _, gloss = piece.partition("=")
            morpheme = ET.SubElement(word, "M", {"id": f"{entry_id}W1M{index}"})
            add_forms(morpheme, morph_form)
            if gloss:
                ET.SubElement(morpheme, "TRANSL", {XML_LANG: "eng"}).text = gloss
    tree = ET.ElementTree(text)
    ET.indent(tree, space="  ")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tree.write(OUTPUT, encoding="utf-8", xml_declaration=True)
    print(f"Built {len(rows)} prose-dictionary entries into {OUTPUT.name}.")


if __name__ == "__main__":
    main()
