#!/usr/bin/env python3
"""Build the Wu (2006) Amis pa-verb baseline before recorded manual edits."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
SOURCE_TABLE = ROOT / "CodeAndDocs/raw_data/source_examples.tsv"
SOURCE_PDF = ROOT / "CodeAndDocs/raw_data/source.pdf"
SOURCE_PDF_SHA256 = "9ba94321d9c8e926cf8cca3b0b81814400d2bb7194ba48574d77ad54490308f5"
DEFAULT_OUTPUT = ROOT / "Final_XML/Amis/pa-verbs.xml"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

CITATION = (
    "Wu, Joy. 2006. The analysis of pa- verbs in Amis. Paper presented at "
    "the Tenth International Conference on Austronesian Linguistics, "
    "17-20 January 2006, Puerto Princesa City, Palawan, Philippines."
)
BIBTEX = (
    "@inproceedings{wu2006pa, author={Wu, Joy}, title={The analysis of pa- "
    "verbs in Amis}, booktitle={Tenth International Conference on "
    "Austronesian Linguistics}, year={2006}, address={Puerto Princesa City, "
    "Palawan, Philippines}}"
)
COPYRIGHT = (
    "CC BY-NC-SA 4.0 (license recorded on the Basecamp corpus card; the "
    "source PDF itself does not display a license statement)"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_examples() -> list[dict[str, str]]:
    with SOURCE_TABLE.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    required = {
        "id",
        "source_example",
        "source_locator",
        "segmented_form",
        "gloss",
        "translation_1",
        "translation_2",
        "acceptability",
        "decision",
    }
    require(rows and set(rows[0]) == required, "Unexpected source-table columns")
    require(len(rows) == 30, "Expected 30 reviewed generator rows")
    require(len({row["id"] for row in rows}) == len(rows), "Duplicate sentence ID")
    return rows


def sentence_word(token: str) -> str:
    """Remove W-tier segmentation and non-overt null material at S."""

    if token.startswith("ø-"):
        token = token.removeprefix("ø-")
    return token.translate(str.maketrans("", "", "-<>="))


def morphemes(form: str, gloss: str) -> list[tuple[str, str]]:
    """Map only source-supported segmentation to FormosanBank M elements."""

    if "-" in form:
        form_parts = form.split("-")
        gloss_parts = gloss.split("-")
        if len(form_parts) != len(gloss_parts):
            # Wu prints Pa-fli but supplies only the whole-word gloss `give`.
            # Retain both at W while avoiding an unsupported morpheme analysis.
            return []
        return list(zip(form_parts, gloss_parts, strict=True))
    return [(form, gloss)]


def add_translation(parent: ET.Element, value: str, version: str | None = None) -> None:
    attributes = {XML_LANG: "eng"}
    if version is not None:
        attributes["ver"] = version
    node = ET.SubElement(parent, "TRANSL", attributes)
    node.text = value


def build_tree(rows: list[dict[str, str]]) -> ET.ElementTree:
    root = ET.Element(
        "TEXT",
        {
            XML_LANG: "ami",
            "citation": CITATION,
            "BibTeX_citation": BIBTEX,
            "copyright": COPYRIGHT,
            "id": "wu-2006-amis-pa-verbs",
            "dialect": "Coastal",
        },
    )

    for row in rows:
        forms = row["segmented_form"].split()
        glosses = row["gloss"].split()
        require(
            len(forms) == len(glosses),
            f"Word/gloss count mismatch for {row['id']}: {len(forms)} != {len(glosses)}",
        )

        sentence = ET.SubElement(root, "S", {"id": row["id"]})
        sentence_form = ET.SubElement(sentence, "FORM", {"kindOf": "original"})
        sentence_form.text = " ".join(sentence_word(token) for token in forms)
        add_translation(sentence, row["translation_1"])
        if row["translation_2"]:
            add_translation(sentence, row["translation_2"], "alt")

        for word_index, (form, gloss) in enumerate(zip(forms, glosses, strict=True)):
            word = ET.SubElement(sentence, "W", {"id": f"{row['id']}w{word_index}"})
            word_form = ET.SubElement(word, "FORM", {"kindOf": "original"})
            word_form.text = form
            add_translation(word, gloss)
            for morph_index, (morph_form, morph_gloss) in enumerate(
                morphemes(form, gloss)
            ):
                morph = ET.SubElement(
                    word, "M", {"id": f"{row['id']}w{word_index}m{morph_index}"}
                )
                morph_form_node = ET.SubElement(morph, "FORM", {"kindOf": "original"})
                morph_form_node.text = morph_form
                add_translation(morph, morph_gloss)

    return ET.ElementTree(root)


def write_tree(tree: ET.ElementTree, output: Path) -> None:
    ET.indent(tree, space="    ")
    output.parent.mkdir(parents=True, exist_ok=True)
    tree.write(
        output, encoding="utf-8", xml_declaration=True, short_empty_elements=False
    )
    data = output.read_bytes()
    if not data.endswith(b"\n"):
        data += b"\n"
    output.write_bytes(data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    source_hash = hashlib.sha256(SOURCE_PDF.read_bytes()).hexdigest()
    require(source_hash == SOURCE_PDF_SHA256, "Source PDF hash changed")
    rows = read_examples()
    output = args.output.resolve()
    write_tree(build_tree(rows), output)
    print(f"Built {len(rows)} source-adjudicated sentences in {output}")


if __name__ == "__main__":
    main()
