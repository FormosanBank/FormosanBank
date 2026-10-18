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
        # Round 3 (maintainer, 2026-10-18): chose "A: ∅ in the sentence too"
        # and "But explain in note that it's been added there." V124/V125
        # require a W/M null to appear in the S original FORM as well.
        sentence = word.getparent()
        s_form = _original(sentence)
        _expect(s_form.text == NULL_SENTENCE_BEFORE and s_form.get("notes") is None,
                f"{sentence.get('id')}: S FORM is not '{NULL_SENTENCE_BEFORE}' without notes")
        s_form.text = NULL_SENTENCE_AFTER
        s_form.set("notes", NULL_SENTENCE_NOTE)
        _strip_derived(sentence)


NULL_SENTENCE_BEFORE = "asu skiya"
NULL_SENTENCE_AFTER = "asu ∅-skiya"
NULL_SENTENCE_NOTE = ("The ∅- is not printed in the thesis sentence (PDF page 55, 'asu skiya'); "
                      "FormosanBank added it to match the word and morpheme analysis, since the "
                      "thesis glosses skiya as ∅-飛.")


# Ruling 8 -- [nb-other-clitic-gloss-fusion]. Maintainer: "Treat host +
# clitic as one W (POL-060)". The thesis writes a clitic as its own token
# (`Ini =ku`) but usually prints ONE gloss token for host and clitic (不-我).
# data/manual/clitic_merges.tsv lists every such pair, with the printed form
# and gloss lines; pairs whose clitic has its own printed gloss token are not
# in it. Excluded for now by the maintainer, awaiting a follow-up card:
# S-n-rus =mu (C03_E012A), B-n-arig =ku (C04_E003B), Mgay =ku (C01_E011D,
# C01_E011D2). The merged W keeps the host's id, FORM "host clitic", and the
# printed gloss; its Ms are the host's Ms then the clitic's M, each with its
# gloss and its published id. The clitic W is removed.
CLITIC_MERGES = HERE / "data" / "manual" / "clitic_merges.tsv"


def merge_clitic_glosses(ids):
    with CLITIC_MERGES.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    _expect(rows, "clitic_merges.tsv is empty")
    for row in rows:
        host, clitic = ids.get(row["host_w_id"]), ids.get(row["clitic_w_id"])
        label = f"{row['sentence_id'][len(P):]} {row['merged_form']}"
        _expect(host is not None and clitic is not None and host.getnext() is clitic
                and host.getparent().get("id") == row["sentence_id"], f"{label}: words not found")
        _expect(_original(host).text == row["host_form"] and _original(clitic).text == row["clitic_form"],
                f"{label}: FORMs changed")
        _expect(_gloss_text(host) == row["host_gloss"] and _gloss_text(clitic) == row["clitic_gloss"],
                f"{label}: glosses changed")
        _expect(row["merged_gloss"] == f"{row['host_gloss']}-{row['clitic_gloss']}", f"{label}: bad table row")
        _expect(set(clitic.attrib) == {"id"} and {c.tag for c in clitic} <= {"FORM", "PHON", "TRANSL", "M"},
                f"{label}: clitic W carries more than FORM/PHON/TRANSL/M")
        clitic_ms = clitic.findall("M")
        _expect(len(clitic_ms) == 1, f"{label}: clitic W should have one M")
        _original(host).text = row["merged_form"]
        _strip_derived(host)
        host.find("TRANSL").text = row["merged_gloss"]
        host.findall("M")[-1].addnext(clitic_ms[0])
        host.getparent().remove(clitic)


# Ruling 9 -- [nb-other-starred-alt-translation] (8c), PDF page 130, prints
# 星星出來了。(* 螢火蟲出來了): the starred reading is one the sentence does NOT
# have. Maintainer: "Keep it as a note on the translation".
# Ruling 10 -- [nb-other-parenthetical-as-alt-translation] (28a)/(28b), PDF
# page 44, print 要來這裡了(在路上) and 剛剛到達這裡(已看到人). Maintainer:
# "Move to a note". In each, the ver="alt" TRANSL is removed and the
# parenthetical, as printed, becomes the notes of the primary TRANSL.
ALT_TO_NOTE = [
    # (S id, alt TRANSL text now, note)
    ("C04_E008C", "* 螢火蟲出來了", "(* 螢火蟲出來了)"),
    ("C01_E028A", "在路上", "(在路上)"),
    ("C01_E028B", "已看到人", "(已看到人)"),
]


def move_alt_translations_to_notes(ids):
    for sentence_id, alt_text, note in ALT_TO_NOTE:
        sentence = _get(ids, sentence_id, "S")
        alts = [t for t in sentence.findall("TRANSL") if t.get("ver") == "alt"]
        primary = [t for t in sentence.findall("TRANSL") if t.get("ver") is None]
        _expect(len(alts) == 1 and alts[0].text == alt_text, f"{sentence_id}: alt TRANSL is not {alt_text}")
        _expect(len(primary) == 1 and primary[0].get("notes") is None, f"{sentence_id}: expected one primary TRANSL without notes")
        sentence.remove(alts[0])
        primary[0].set("notes", note)


# Round 2 (maintainer, 2026-10-18): the three host + clitic pairs held back
# from ruling 8. The sentence FORMs are not changed.
# - S-n-rus =mu (C03_E012A): chose "A: infix notation" -- "This is infix
#   notation, you are correct." W `S<n>rus =mu` = 擦-n-我; Ms `S-rus` = 擦,
#   `-n-` = n, `=mu` = 我.
# - B-n-arig =ku (C04_E003B): "A" -- W `B<n>arig =ku` = 買-n-我; Ms
#   `B-arig` = 買, `-n-` = n, `=ku` = 我.
# As in the q-m-pah-an repair (source-decisions.md), the root keeps M1's id,
# the infix keeps M2's, old M3 (the rest of the root) is removed, and the
# clitic's M keeps its published id.
INFIX_CLITIC_MERGES = [
    # (host W, clitic W, host FORM before, new W FORM, W gloss before, new W gloss,
    #  [(M id, FORM before, FORM after, gloss)], M id removed)
    ("C03_E012AW1", "C03_E012AW2", "S-n-rus", "S<n>rus =mu", "擦-n", "擦-n-我",
     [("C03_E012AW1M1", "S", "S-rus", "擦"), ("C03_E012AW1M2", "n", "-n-", "n")], ("C03_E012AW1M3", "rus")),
    ("C04_E003BW1", "C04_E003BW2", "B-n-arig", "B<n>arig =ku", "買-n", "買-n-我",
     [("C04_E003BW1M1", "B", "B-arig", "買"), ("C04_E003BW1M2", "n", "-n-", "n")], ("C04_E003BW1M3", "arig")),
]
# - Mgay =ku (C01_E011D, C01_E011D2): "A" -- W `Mgay =ku` glossed AF-給=我
#   (the maintainer's spelling); M `Mgay` = <UNCLEAR/>; M `=ku` = 我.
UNCLEAR_HOST_CLITIC_MERGES = [
    # (host W, clitic W, new W FORM, W gloss before, new W gloss, host M id)
    ("C01_E011DW1", "C01_E011DW2", "Mgay =ku", "AF-給", "AF-給=我", "C01_E011DW1M1"),
    ("C01_E011D2W1", "C01_E011D2W2", "Mgay =ku", "AF-給", "AF-給=我", "C01_E011D2W1M1"),
]


def _merge_clitic_word(host, clitic, new_form, new_gloss):
    clitic_ms = clitic.findall("M")
    _expect(len(clitic_ms) == 1 and _gloss_text(clitic) == "我" and _gloss_text(clitic_ms[0]) == "我",
            f"{clitic.get('id')}: expected one clitic M glossed 我")
    _expect(set(clitic.attrib) == {"id"} and {c.tag for c in clitic} <= {"FORM", "PHON", "TRANSL", "M"},
            f"{clitic.get('id')}: clitic W carries more than FORM/PHON/TRANSL/M")
    _original(host).text = new_form
    _strip_derived(host)
    host.find("TRANSL").text = new_gloss
    host.findall("M")[-1].addnext(clitic_ms[0])
    host.getparent().remove(clitic)


def merge_held_clitics(ids):
    for host_id, clitic_id, before, form, gloss_before, gloss, m_changes, (gone_id, gone_form) in INFIX_CLITIC_MERGES:
        host, clitic = _get(ids, host_id, "W"), _get(ids, clitic_id, "W")
        _expect(host.getnext() is clitic, f"{host_id}/{clitic_id}: not adjacent")
        _expect(_original(host).text == before and _gloss_text(host) == gloss_before,
                f"{host_id}: not {before} / {gloss_before}")
        ms = host.findall("M")
        _expect([m.get("id") for m in ms] == [P + m_changes[0][0], P + m_changes[1][0], P + gone_id]
                and [_original(m).text for m in ms] == [m_changes[0][1], m_changes[1][1], gone_form]
                and not any(_glosses(m) for m in ms), f"{host_id}: Ms not as expected")
        for m, (_, _, new_m_form, m_gloss) in zip(ms, m_changes):
            _original(m).text = new_m_form
            _strip_derived(m)
            m.append(_new_gloss(m_gloss))
        host.remove(ms[2])
        _merge_clitic_word(host, clitic, form, gloss)
    for host_id, clitic_id, form, gloss_before, gloss, m_id in UNCLEAR_HOST_CLITIC_MERGES:
        host, clitic = _get(ids, host_id, "W"), _get(ids, clitic_id, "W")
        _expect(host.getnext() is clitic, f"{host_id}/{clitic_id}: not adjacent")
        ms = host.findall("M")
        _expect(_original(host).text == "Mgay" and _gloss_text(host) == gloss_before
                and len(ms) == 1 and ms[0].get("id") == P + m_id and _gloss_text(ms[0]) == gloss_before,
                f"{host_id}: not Mgay with one M glossed {gloss_before}")
        ms[0].remove(ms[0].find("TRANSL"))
        ms[0].append(_new_gloss(unclear=True))
        _merge_clitic_word(host, clitic, form, gloss)


STEPS = [merge_joint_glosses, add_thesis_glosses, gloss_morphemes_unclear, split_null_morpheme,
         merge_clitic_glosses, move_alt_translations_to_notes, merge_held_clitics]


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
