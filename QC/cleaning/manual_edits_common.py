"""Shared helpers for the manual-edits capture/apply pair.

manual_edits.xml records hand edits to a corpus's XML as full <S> blocks
(see claudeplans/2026-06-15-manual-edits-reproducibility-design.md):

    <MANUAL_EDITS>
      <FILE path="Amis/story01.xml">
        <S id="...">...</S>                  upsert (replace-by-id or insert)
        <S id="..." after="...">...</S>      upsert of a NEW id, placement hint
        <S id="..." action="delete"/>        delete-by-id
      </FILE>
    </MANUAL_EDITS>

Recorded <S> blocks are stored on the strip() basis: all standard-tier
FORM and all PHON removed, because standardize.py / add_phonology.py
regenerate those tiers downstream (apply runs before them).
"""
from __future__ import annotations

import copy
from pathlib import Path

from lxml import etree

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


# ----- path resolution -------------------------------------------------------

def default_manual_file(corpora_path) -> Path:
    """Default manual-edits file: <corpus-root>/CodeAndDocs/manual_edits.xml,
    i.e. a CodeAndDocs/ sibling of the XML directory given as corpora_path."""
    return Path(corpora_path).resolve().parent / "CodeAndDocs" / "manual_edits.xml"


def changelog_path(manual_file) -> Path:
    """Human-readable changelog path next to the manual file (.md suffix)."""
    return Path(manual_file).with_suffix(".md")


# ----- the strip()/canonical basis -------------------------------------------

def strip_s(s_elem: etree._Element) -> etree._Element:
    """Deep copy of <S> reduced to manual-relevant content: every standard-tier
    FORM and every PHON removed (S/W/M), and after/action attrs dropped."""
    el = copy.deepcopy(s_elem)
    el.attrib.pop("after", None)
    el.attrib.pop("action", None)
    for form in el.findall(".//FORM[@kindOf='standard']"):
        form.getparent().remove(form)
    for phon in el.findall(".//PHON"):
        phon.getparent().remove(phon)
    return el


def canonical_s(s_elem: etree._Element) -> str:
    """Canonical (c14n) string of an <S> on the strip() basis, for equality.

    Reparsed with remove_blank_text so indentation differences don't make two
    otherwise-identical blocks compare unequal.
    """
    stripped = strip_s(s_elem)
    reparsed = etree.fromstring(
        etree.tostring(stripped), parser=etree.XMLParser(remove_blank_text=True)
    )
    return etree.tostring(reparsed, method="c14n").decode("utf-8")


def render_s(s_elem: etree._Element) -> str:
    """One-line human rendering for the changelog: original FORM + TRANSLs."""
    parts: list[str] = []
    originals = s_elem.findall("FORM[@kindOf='original']")
    if not originals:
        originals = s_elem.findall("FORM")[:1]
    for form in originals:
        if form.text and form.text.strip():
            parts.append(form.text.strip())
    for tr in s_elem.findall("TRANSL"):
        lang = tr.get(XML_LANG, "")
        text = (tr.text or "").strip()
        if text:
            parts.append(f"[{lang}] {text}")
    return " / ".join(parts)
