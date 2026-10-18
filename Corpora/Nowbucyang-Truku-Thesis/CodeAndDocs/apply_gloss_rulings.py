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


# Ruling 2 -- [nb-C01_E011E] `N-tama ka patas gaga.` (thesis (11e), PDF page 32,
# gloss line 屬-爸爸 主格 書 那). Maintainer: "Use the thesis glosses".
# (The paraphrase `Patas tama ka gaga.` that the thesis prints beside it is
# already its own unglossed S, C01_E011E2, from manual_sentences.xml.)
THESIS_GLOSSES = {
    # W id: (W gloss, [M glosses in M order])
    "C01_E011EW1": ("屬-爸爸", ["屬", "爸爸"]),
    "C01_E011EW2": ("主格", ["主格"]),
    "C01_E011EW3": ("書", ["書"]),
    "C01_E011EW4": ("那", ["那"]),
}


def add_thesis_glosses(ids):
    for word_id, (word_gloss, m_glosses) in THESIS_GLOSSES.items():
        word = _get(ids, word_id, "W")
        ms = word.findall("M")
        _expect(len(ms) == len(m_glosses), f"{word_id}: expected {len(m_glosses)} M")
        _expect(not _glosses(word) and not any(_glosses(m) for m in ms), f"{word_id}: already glossed")
        for m, gloss in zip(ms, m_glosses):
            m.append(_new_gloss(gloss))
        _put_word_gloss(word, _new_gloss(word_gloss))


# Ruling 4 -- infix words printed with four morphemes [nb-inf-C01_E021D,
# nb-inf-C01_E023E, nb-inf-C01_E024B, nb-inf-C02_E004A]. Maintainer chose
# "C: <UNCLEAR/>" and "Four Ms, none glossed." The W keeps the gloss the
# thesis prints. (C01_E023E's printed token 砍-LF-我 also covers the clitic
# =mu; see ruling 8.)
# Ruling 5 -- [nb-whole-C02_E004B] n-hda-an 完成. Maintainer: "<UNCLEAR/> on
# each morpheme" and "Three Ms, none glossed."
UNCLEAR_MORPHEMES = {
    # W id: W gloss as printed (left unchanged)
    "C01_E021DW1": "製作-n-LF",  # S-n-lu-an
    "C01_E023EW1": "砍-LF",  # T-n-tak-an
    "C01_E024BW1": "煮-LF",  # H-n-puy-an
    "C02_E004AW4": "死-n-LF",  # h-n-qil-an
    "C02_E004BW3": "完成",  # n-hda-an
}


def gloss_morphemes_unclear(ids):
    for word_id, word_gloss in UNCLEAR_MORPHEMES.items():
        word = _get(ids, word_id, "W")
        _expect(_gloss_text(word) == word_gloss, f"{word_id}: W gloss is not {word_gloss}")
        ms = word.findall("M")
        _expect(len(ms) in (3, 4) and not any(_glosses(m) for m in ms),
                f"{word_id}: expected three or four unglossed M")
        for m in ms:
            m.append(_new_gloss(unclear=True))


# Ruling 6 -- [nb-single-C02_E001D] `asu skiya`, printed gloss 船 ∅-飛 (PDF
# page 55). Maintainer: "Copy the word gloss to the M" and "So for purposes of
# the W, the FORM should be ∅-skiya. Then 2 Ms, each with its own gloss."
# The sentence FORM stays as printed. The existing M (skiya) keeps its id;
# the new null M takes the next free id and is placed first, as the gloss
# order ∅-飛 requires (POL-037: no renumbering).
NULL_SPLITS = [
    # (W id, W FORM before, W FORM after, W gloss, existing M id, new null M id, M glosses)
    ("C02_E001DW2", "skiya", "∅-skiya", "∅-飛", "C02_E001DW2M1", "C02_E001DW2M2", ("∅", "飛")),
]


def split_null_morpheme(ids):
    for word_id, before, after, word_gloss, m_id, null_id, (null_gloss, m_gloss) in NULL_SPLITS:
        word = _get(ids, word_id, "W")
        _expect(_original(word).text == before, f"{word_id}: FORM is not {before}")
        _expect(_gloss_text(word) == word_gloss, f"{word_id}: W gloss is not {word_gloss}")
        ms = word.findall("M")
        _expect(len(ms) == 1 and ms[0].get("id") == P + m_id and not _glosses(ms[0]),
                f"{word_id}: expected the single unglossed M {m_id}")
        _expect(P + null_id not in ids, f"{null_id}: id already in use")
        _original(word).text = after
        _strip_derived(word)
        null_m = etree.Element("M", {"id": P + null_id})
        etree.SubElement(null_m, "FORM", {"kindOf": "original"}).text = "∅"
        null_m.append(_new_gloss(null_gloss))
        ms[0].addprevious(null_m)
        ms[0].append(_new_gloss(m_gloss))


STEPS = [merge_joint_glosses, add_thesis_glosses, gloss_morphemes_unclear, split_null_morpheme]


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
