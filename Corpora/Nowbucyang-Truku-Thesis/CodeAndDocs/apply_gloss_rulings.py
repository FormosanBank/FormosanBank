"""Apply the maintainer's 2026-10-18 gloss rulings to the staged build.

The rulings were made on the Nowbucyang Gloss Review page; each step below
quotes the maintainer's words. generate_xml.sh runs this after
apply_manual_edits.py and before clean_xml.py, so standardize.py and
add_phonology.py regenerate the standard FORM and PHON tiers of everything
changed here. Every step first checks that the XML is in the state the ruling
was made against and stops with an error otherwise, so an upstream change
cannot be silently overwritten. Published W and M ids are kept (POL-037).
"""

import argparse
import csv
from pathlib import Path

from lxml import etree

P = "HSU_LOWKING_TRUKU_WORDFORMATION_2008_"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
HERE = Path(__file__).resolve().parent


class RulingMismatch(ValueError):
    pass


def _expect(condition, message):
    if not condition:
        raise RulingMismatch(message)


def _index(root):
    return {e.get("id"): e for e in root.iter("S", "W", "M")}


def _original(element):
    form = element.find("FORM[@kindOf='original']")
    _expect(form is not None, f"{element.get('id')}: no original FORM")
    return form


def _glosses(element):
    return element.findall("TRANSL")


def _gloss_text(element):
    glosses = _glosses(element)
    _expect(len(glosses) <= 1, f"{element.get('id')}: more than one TRANSL")
    return glosses[0].text if glosses else None


def _strip_derived(element):
    """Drop the standard FORM and PHON tiers; the shared tools regenerate them."""
    for child in list(element):
        if child.tag == "PHON" or (child.tag == "FORM" and child.get("kindOf") == "standard"):
            element.remove(child)


def _new_gloss(text=None, unclear=False):
    transl = etree.Element("TRANSL", {XML_LANG: "zho"})
    if unclear:
        etree.SubElement(transl, "UNCLEAR")
    else:
        transl.text = text
    return transl


def _put_word_gloss(word, transl):
    """Insert a W gloss before the W's first M (the pipeline's placement)."""
    children = list(word)
    first_m = next((i for i, c in enumerate(children) if c.tag == "M"), len(children))
    word.insert(first_m, transl)


def _get(ids, short_id, tag):
    element = ids.get(P + short_id)
    _expect(element is not None and element.tag == tag, f"{short_id}: no {tag} with this id")
    return element


# Ruling 1 -- [nb-pol060-C03_E037A_0206_01], [nb-pol060-C03_E039C]
# Maintainer: "One W “niya na” = 尚未" (one M, same gloss).
JOINT_GLOSSES = [
    # (first W, second W, joint FORM, gloss)
    ("C03_E037A_0206_01W4", "C03_E037A_0206_01W5", "niya na", "尚未"),
    ("C03_E039CW4", "C03_E039CW5", "niya na", "尚未"),
]


def merge_joint_glosses(ids):
    for first_id, second_id, joint_form, gloss in JOINT_GLOSSES:
        first, second = _get(ids, first_id, "W"), _get(ids, second_id, "W")
        _expect(first.getparent() is second.getparent() and first.getnext() is second,
                f"{first_id}/{second_id}: not adjacent words of one sentence")
        _expect(f"{_original(first).text} {_original(second).text}" == joint_form,
                f"{first_id}/{second_id}: FORMs are not '{joint_form}'")
        for word in (first, second):
            _expect(not _glosses(word), f"{word.get('id')}: already glossed")
            ms = word.findall("M")
            _expect(len(ms) == 1 and not _glosses(ms[0]), f"{word.get('id')}: expected one unglossed M")
        first_m = first.find("M")
        _original(first).text = joint_form
        _original(first_m).text = joint_form
        _strip_derived(first)
        _strip_derived(first_m)
        first_m.append(_new_gloss(gloss))
        _put_word_gloss(first, _new_gloss(gloss))
        first.getparent().remove(second)


STEPS = [merge_joint_glosses]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml", type=Path, required=True)
    args = parser.parse_args()
    tree = etree.parse(str(args.xml))
    ids = _index(tree.getroot())
    for step in STEPS:
        step(ids)
        ids = _index(tree.getroot())
    tree.write(str(args.xml), encoding="UTF-8", xml_declaration=True)
    print(f"apply_gloss_rulings: applied {len(STEPS)} ruling step(s) to {args.xml.name}")


if __name__ == "__main__":
    main()
