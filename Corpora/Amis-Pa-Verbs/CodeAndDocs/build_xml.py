#!/usr/bin/env python3
"""Build the source-adjudicated Wu (2006) Amis pa-verb corpus."""

from __future__ import annotations

import csv
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SOURCE_TABLE = ROOT / "CodeAndDocs/source_examples.tsv"
XML_PATH = ROOT / "XML/Amis/pa-verbs.xml"
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
COPYRIGHT = "CC BY-NC-SA 4.0"

TRANSLATION_NOTES = {
    ("s20c_person", 1): "The causee is a little child.",
    ("s20c_car", 2): 'Introduced by "i.e." in the source.',
}


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
        "sentence_ending",
        "word_ids",
    }
    require(rows and set(rows[0]) == required, "Unexpected source-table columns")
    require(len(rows) == 29, "Expected 29 reviewed sentence variants")
    require(len({row["id"] for row in rows}) == len(rows), "Duplicate sentence ID")
    return rows


def sentence_word(token: str) -> str:
    """Remove W-tier segmentation while retaining analytic null notation."""

    if token.startswith("∅-"):
        return token
    return token.translate(str.maketrans("", "", "-<>="))


def morphemes(form: str, gloss: str) -> list[tuple[str, str | None]]:
    """Map only source-supported segmentation to FormosanBank M elements."""

    if "-" in form:
        form_parts = form.split("-")
        gloss_parts = gloss.split("-")
        if len(form_parts) != len(gloss_parts):
            # Preserve printed boundaries without assigning an unaligned gloss.
            return [(part, None) for part in form_parts]
        return list(zip(form_parts, gloss_parts, strict=True))
    return [(form, gloss)]


def standardized_gloss(value: str) -> str | None:
    """Return the one source-backed abbreviation normalization in the paper."""

    normalized = value.replace("CaU", "CAU")
    return normalized if normalized != value else None


def add_translation(
    parent: ET.Element,
    value: str,
    *,
    version: str | None = None,
    kind_of: str | None = None,
    notes: str | None = None,
) -> None:
    attributes = {XML_LANG: "eng"}
    if version is not None:
        attributes["ver"] = version
    if kind_of is not None:
        attributes["kindOf"] = kind_of
    if notes is not None:
        attributes["notes"] = notes
    node = ET.SubElement(parent, "TRANSL", attributes)
    node.text = value


def add_source_gloss(parent: ET.Element, value: str) -> None:
    standard = standardized_gloss(value)
    add_translation(
        parent,
        value,
        kind_of="original" if standard is not None else None,
    )
    if standard is not None:
        add_translation(parent, standard, kind_of="standard", version="alt")


def build_tree(rows: list[dict[str, str]]) -> ET.ElementTree:
    with (ROOT / "CodeAndDocs/morpheme_ids.tsv").open(newline="") as handle:
        morph_ids = {
            (row["word_id"], int(row["index"])): row["id"]
            for row in csv.DictReader(handle, delimiter="\t")
        }
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
        word_ids = row["word_ids"].split()
        require(
            len(forms) == len(glosses) == len(word_ids),
            f"Word/gloss count mismatch for {row['id']}: {len(forms)} != {len(glosses)}",
        )

        sentence = ET.SubElement(root, "S", {"id": row["id"]})
        sentence_form = ET.SubElement(sentence, "FORM", {"kindOf": "original"})
        require(row["sentence_ending"] in {"", ".", "!"}, "Unknown source ending")
        sentence_form.text = (
            " ".join(sentence_word(token) for token in forms) + row["sentence_ending"]
        )
        add_translation(
            sentence,
            row["translation_1"],
            notes=TRANSLATION_NOTES.get((row["id"], 1)),
        )
        if row["translation_2"]:
            add_translation(
                sentence,
                row["translation_2"],
                version="alt",
                notes=TRANSLATION_NOTES.get((row["id"], 2)),
            )

        for word_id, form, gloss in zip(word_ids, forms, glosses, strict=True):
            word = ET.SubElement(sentence, "W", {"id": word_id})
            word_form = ET.SubElement(word, "FORM", {"kindOf": "original"})
            word_form.text = form
            add_source_gloss(word, gloss)
            for morph_index, (morph_form, morph_gloss) in enumerate(
                morphemes(form, gloss)
            ):
                morph = ET.SubElement(
                    word, "M", {"id": morph_ids.get(
                        (word_id, morph_index), f"{word_id}m{morph_index}"
                    )}
                )
                morph_form_node = ET.SubElement(morph, "FORM", {"kindOf": "original"})
                morph_form_node.text = morph_form
                if morph_gloss is not None:
                    add_source_gloss(morph, morph_gloss)

    return ET.ElementTree(root)


def write_tree(tree: ET.ElementTree) -> None:
    ET.indent(tree, space="    ")
    XML_PATH.parent.mkdir(parents=True, exist_ok=True)
    tree.write(
        XML_PATH, encoding="utf-8", xml_declaration=True, short_empty_elements=False
    )
    data = XML_PATH.read_bytes()
    if not data.endswith(b"\n"):
        data += b"\n"
    XML_PATH.write_bytes(data)


def main() -> None:
    rows = read_examples()
    write_tree(build_tree(rows))
    print(f"Built {len(rows)} source-adjudicated sentences in {XML_PATH}")


if __name__ == "__main__":
    main()
