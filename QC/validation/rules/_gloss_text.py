"""Read a gloss (TRANSL) whole, with each <UNCLEAR/> as one piece.

Shared by the gloss rules (``rules/gloss.py``, run by validate_glosses) and
the gloss-scrape audit (``rules/gloss_scrape.py``, run by audit_gloss_scrape).

Why not ``transl.text``: in lxml ``.text`` is only the text BEFORE the first
child element. A gloss ``if-main-<UNCLEAR/>-outsider-nom`` reads as
``if-main-``, and a gloss that is only ``<UNCLEAR/>`` reads as empty.

Why not plain ``"".join(transl.itertext())``: <UNCLEAR/> is empty, so that
gives ``if-main--outsider-nom`` -- an empty slot where the gloss has a piece,
which miscounts every rule that counts gloss pieces.

So each <UNCLEAR/> is written as ``UNCLEAR_PLACEHOLDER`` ("?"): one piece, no
letters, no segmentation marker. "?" is also what these sources wrote before
the unknown parts became <UNCLEAR/> (POL-061), so a rule sees the gloss the
same way it saw the pre-conversion text.
"""
from __future__ import annotations

UNCLEAR_PLACEHOLDER = "?"

__all__ = ["UNCLEAR_PLACEHOLDER", "gloss_text"]


def gloss_text(transl) -> str:
    """Return the stripped text of ``transl``, each <UNCLEAR/> as one "?".

    Comments contribute nothing (their tail text is kept); any other child
    element contributes its own text. The XSD allows only <UNCLEAR/> inside
    TRANSL, so that last case is defensive.
    """
    parts = [transl.text or ""]
    for child in transl:
        if child.tag == "UNCLEAR":
            parts.append(UNCLEAR_PLACEHOLDER)
        elif isinstance(child.tag, str):
            parts.append("".join(child.itertext()))
        parts.append(child.tail or "")
    return "".join(parts).strip()
