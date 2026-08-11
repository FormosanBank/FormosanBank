"""Shared XML pretty-printer, safe for mixed content and idempotent.

History: standardize/add_phonology used pretty_print plus a line-based
leading-space doubler, which doubled *content* whitespace that started a
line (an inline <UNCLEAR/> tail) on every run — no byte-level fixed
point. lxml's etree.indent is also unsafe here: it rewrites None/blank
tails even inside a text-bearing (mixed) element, injecting whitespace
into FORM content. This indenter touches a level only when nothing at
that level is content: an element whose text — or any child's tail —
contains non-whitespace is left byte-for-byte alone (children's own
subtrees are still indented).
"""
import xml.etree.ElementTree as ET

from lxml import etree

INDENT = "    "


def _indent(elem, level=0):
    if not len(elem):
        return
    mixed = (elem.text is not None and elem.text.strip()) or any(
        c.tail is not None and c.tail.strip() for c in elem
    )
    for child in elem:
        _indent(child, level + 1)
    if mixed:
        return
    elem.text = "\n" + INDENT * (level + 1)
    for child in elem:
        child.tail = "\n" + INDENT * (level + 1)
    elem[-1].tail = "\n" + INDENT * level


def prettify(elem) -> str:
    """Serialize an (ElementTree or lxml) element pretty-printed."""
    rough_string = ET.tostring(elem, encoding="utf-8") \
        if not isinstance(elem, etree._Element) else etree.tostring(elem)
    reparsed = etree.fromstring(
        rough_string, etree.XMLParser(remove_blank_text=True))
    _indent(reparsed)
    body = etree.tostring(reparsed, encoding="unicode")
    return f'<?xml version="1.0" ?>\n{body}\n'
