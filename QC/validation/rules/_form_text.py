"""Read a FORM whole, past any inline <UNCLEAR/>.

A FORM may hold <UNCLEAR/> in the middle of its text (POL-061):
``waecenge ka <UNCLEAR/>lalasu ki kidringi.`` The text after the marker is
the marker's *tail*, so a plain ``form.text`` read stops at
``waecenge ka``. Rules read FORMs through these helpers instead; this is
the FORM counterpart of _gloss_text.py.

``form_text`` — every character the FORM holds; <UNCLEAR/> adds none. For
rules that check which characters a FORM contains or compare spellings.

``form_words_text`` — each <UNCLEAR/> as one ``UNCLEAR_PLACEHOLDER``
("?"), as gloss_text writes it, so a word written only as <UNCLEAR/>
(``… tiwas <UNCLEAR/> <UNCLEAR/>``) still counts as a word. For rules that
count words.
"""
from __future__ import annotations

from ._gloss_text import UNCLEAR_PLACEHOLDER

__all__ = ["form_text", "form_words_text"]


def _joined(form, unclear: str) -> str:
    parts = [form.text or ""]
    for child in form:
        if child.tag == "UNCLEAR":
            parts.append(unclear)
        elif isinstance(child.tag, str):
            parts.append("".join(child.itertext()))
        # Comments contribute nothing; their tail text is kept.
        parts.append(child.tail or "")
    return "".join(parts)


def form_text(form) -> str:
    """Return all of ``form``'s text, unstripped; <UNCLEAR/> adds nothing."""
    return _joined(form, "")


def form_words_text(form) -> str:
    """Return ``form``'s text, unstripped, each <UNCLEAR/> as one "?"."""
    return _joined(form, UNCLEAR_PLACEHOLDER)
