"""Shared FORM selection: the base of a tier, never one of its variants.

POL-028 (revised 2026-09-09) splits a tier into a **base** FORM — the one
whose ``kindOf`` names the tier and which carries no ``ver`` — plus zero
or more ``ver="alt"`` **variants**. Almost every consumer in the bank
wants the base: a variant is a secondary reading of the same node, and
substituting one changes what a validator validates or a counter counts.

The trap this module closes is that ``Element.find("FORM[@kindOf='x']")``
returns the first match in **document order**, which is a variant
whenever a variant happens to be written first. Nothing in the XSD
orders FORM siblings, so that is a matter of luck, not of schema. The
same first-match idiom appeared in ~20 places across ``QC/``; they now
all route through here.

**A tier carrying variants but no base has no base** (maintainer ruling
2026-09-10). The helpers return ``None``/``""`` rather than falling back
to a variant: V149 (HARD) already reports that shape, and every other
consumer should skip the node rather than silently reason about a
secondary reading.

Works with both ``xml.etree.ElementTree`` and ``lxml.etree`` elements —
only ``.findall()``, ``.get()`` and ``.itertext()`` are used, which both
implement. Only *direct* FORM children are considered, so a ``W``'s
lookup never reaches down into its ``M``'s FORM.
"""
from __future__ import annotations

from typing import Iterator

__all__ = ["iter_base_forms", "find_base_form", "base_form_text"]


def iter_base_forms(node, kind: str | None = None) -> Iterator:
    """Yield ``node``'s direct base FORM children, in document order.

    A base FORM is one without a ``ver`` attribute. When ``kind`` is
    given, only FORMs whose ``kindOf`` equals it are yielded.
    """
    for form in node.findall("FORM"):
        if form.get("ver") is not None:
            continue
        if kind is not None and form.get("kindOf") != kind:
            continue
        yield form


def find_base_form(node, kind: str | None = None):
    """Return ``node``'s base FORM of ``kind``, or ``None``.

    ``None`` means "this node has no base of that kind" — including the
    case where it has only variants. Callers must not fall back to a
    variant; see the module docstring.
    """
    return next(iter_base_forms(node, kind), None)


def base_form_text(node, kind: str | None = None) -> str:
    """Return the stripped text of ``node``'s base FORM of ``kind``, or ``""``.

    Uses ``itertext()`` so mixed content survives: ``<UNCLEAR/>`` is an
    element child, and the text following it is that child's *tail*,
    which a plain ``.text`` read would drop.
    """
    form = find_base_form(node, kind)
    if form is None:
        return ""
    return "".join(form.itertext()).strip()
