#!/usr/bin/env python3
"""Parentheticals in a glossed example, and what each one is.

A printed example carries parentheses on both sides of the gloss, and they are
not one thing. Three kinds matter, and POLICIES.md names only two of them:

**Paired with the source.** When the Formosan sentence and its translation carry
the *same number* of parentheticals, they are about the same thing: the
translation's parenthesis renders the source's, and neither is the editor
talking. ``yaku m-agqaqili sa azazak (sa pagka)`` / ``I was carrying a child
(a chair) on my hip`` is one example with an optional object, not an example
plus a translator's aside. POL-026 makes two S blocks out of the source; this
module is what lets the translation follow it, so the reading without ``sa
pagka`` does not still say "a chair" (maintainer, 2026-09-10).

**An editorial note.** ``(lit. ...)``, ``(answer to Where were you?)``,
``(said, e.g., in anger)``, ``(seems to apply not only to stupidity ...)``.
These are the author writing about the example rather than translating it, and
they belong in a ``notes`` attribute (POL-024). Two signals find them: an
opening marker, which is exact, and length, which is the backstop — a long
parenthetical with no counterpart in the source is not rendering anything.

**Supplied material.** ``(and)``, ``(it)``, ``(he)``, ``(a chair)`` — a word the
translator adds because English needs it and the Formosan does not. Ordinary
translation practice, stays inline, and POL-024 says not to flag it.

Measured over Blust's *Thao Dictionary* (8,368 examples, 2,430 parentheticals in
the translations): 64.3% are two words or fewer, 15.5% open with a marker, 5.7%
are long with no marker, 13.4% are three to five words with no marker, and 1.2%
pair with the source.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

PAREN = re.compile(r"\(([^()]*)\)")

#: How many words a parenthetical with no counterpart in the source needs
#: before length alone reads it as an editorial note. Six keeps the supplied
#: words and the short naturalistic elaboration POL-024 protects inline.
DEFAULT_NOTE_WORDS = 5

#: An opening that marks the author writing *about* the example. Exact where
#: length is a guess, so it is checked first and is not length-limited.
#:
#: Deliberately not here: a bare grammatical label such as ``(pl.)`` or
#: ``(incl.)``. It looks metalinguistic but it is attached to a pronoun and is
#: part of the translation - "We (incl.) are early" loses its sense without it.
#: ``etc.`` is an elaboration wherever it sits, not supplied material:
#: "I fell through (a floor, etc.)" reads complete without it, and the
#: parenthesis is the author listing what else could be meant
#: (maintainer's ruling, 2026-09-11).
ETCETERA = re.compile(r"\betc\.", re.IGNORECASE)

NOTE_MARKERS = re.compile(
    r"""^(
        lit\.|literally|viz\.|e\.g\.|i\.e\.|cf\.
      | said\b | answer\b | reply\b | asking\b | statement\b | advice\b
      | as\ (when|to|in|if|opposed|a\ polite)
      | of\ (inquiries|a\ man|a\ woman|people|two\ people)
      | (more|less)\ (familiar|formal|marked|perfect|polite)
      | considered\b | recorded\b | variant\ of\b | seems\ to\b
      | in\ (more\ modern|this\ sentence)
      | with\ reference\b | part\ of\ the\ ritual\b
      | response\b | further\b
    )""",
    re.IGNORECASE | re.VERBOSE,
)

PAIRED = "paired"
NOTE = "note"
INLINE = "inline"


@dataclass(frozen=True)
class Parenthetical:
    """One ``(...)`` span, with the role it plays."""

    start: int
    end: int
    inner: str
    kind: str

    @property
    def text(self) -> str:
        return f"({self.inner})"

    @property
    def words(self) -> int:
        return len(self.inner.split())


def parentheticals(text: str) -> list[Parenthetical]:
    r"""Every OUTERMOST ``(...)`` span in ``text``, unclassified.

    Depth-counted rather than matched, because a parenthetical can contain one:

        I put bananas into the storage jar to ripen
        (lit. I am ripening bananas, (I) put them into the storage jar)

    ``\([^()]*\)`` cannot span that, so the note was invisible and stayed in
    the translation - all 25 of the ``(lit. ...)`` left inline in the published
    Thao Dictionary were nested ones (maintainer, 2026-09-11). The outermost
    span is the right unit: the note is the whole remark, not the fragment
    after its inner bracket.

    An unclosed ``(`` yields nothing rather than running to the end of the
    string; validate_text's V111 is what reports it.
    """
    spans, depth, start = [], 0, None
    for index, character in enumerate(text or ""):
        if character == "(":
            if depth == 0:
                start = index
            depth += 1
        elif character == ")" and depth:
            depth -= 1
            if depth == 0:
                spans.append(
                    Parenthetical(start, index + 1, text[start + 1:index].strip(), INLINE)
                )
    return spans


def pairs_with_source(
    source: str,
    translation: str,
    *,
    never_pairs: frozenset = frozenset(),
) -> bool:
    """True when the two sides carry the same non-zero number of parentheticals.

    The maintainer's rule: equal counts mean they are about the same thing, so
    the translation's parentheses are not the translator's notes and have to be
    expanded in step with the source rather than copied to both readings.

    ``never_pairs`` names source words that are optional so often, and carry so
    little, that bracketing one says nothing about the translation. In Blust's
    Thao a bracketed ``tu``, ``sa``, ``a``, ``ya`` or ``wa`` is a particle with
    no clear gloss, while the bracket beside it in the English is the
    translator supplying ``(it)`` or ``(and)`` - the counts match and the two
    have nothing to do with each other (maintainer, 2026-09-11). The set is a
    caller's, not this module's: which words those are is a fact about a
    language, not about parentheses.
    """
    counted = [
        span for span in parentheticals(source)
        if span.inner.strip().lower() not in never_pairs
    ]
    return bool(counted) and len(counted) == len(parentheticals(translation))


def classify(
    source: str,
    translation: str,
    *,
    note_words: int = DEFAULT_NOTE_WORDS,
    markers: re.Pattern = NOTE_MARKERS,
    never_pairs: frozenset = frozenset(),
) -> list[Parenthetical]:
    """Label every parenthetical in ``translation``."""
    paired = pairs_with_source(source, translation, never_pairs=never_pairs)
    # One bracketed source WORD cannot be rendered by a note's worth of English.
    # `a ma-kan (ihu) afu` / "You will eat some rice (polite invitation to
    # someone to eat)" has one parenthetical a side, so the two were expanded in
    # step and the second reading read "You will eat some rice polite invitation
    # to someone to eat" - a translator's note welded into the sentence with its
    # brackets stripped. Length on its own is not the test: `m-ilu (i-say
    # lhalhuzu a wazaqan i-nay)` / "bathed (in the lake beside the fish trap
    # over there)" is long on both sides and does pair. It is the mismatch of
    # scale that gives it away (maintainer, 2026-09-11).
    bracketed = [
        span for span in parentheticals(source)
        if span.inner.strip().lower() not in never_pairs
    ]
    lopsided = paired and len(bracketed) == 1 and bracketed[0].words == 1
    out = []
    for span in parentheticals(translation):
        # An editorial marker beats the pairing count. `m-ara (sa) apiq` /
        # "marry off one's son (lit. get a daughter-in-law)" has one
        # parenthetical on each side, but `(sa)` is an optional Thao word and
        # `(lit. ...)` is a paraphrase of the whole sentence - they are not
        # about the same thing, and equal counts are a default, not a proof
        # (maintainer, 2026-09-11).
        if markers.match(span.inner):
            kind = NOTE
        elif lopsided and (
            span.words >= note_words or ETCETERA.search(span.inner)
        ):
            kind = NOTE
        elif paired:
            kind = PAIRED
        elif (
            markers.match(span.inner)
            or span.words >= note_words
            or ETCETERA.search(span.inner)
        ):
            kind = NOTE
        else:
            kind = INLINE
        out.append(Parenthetical(span.start, span.end, span.inner, kind))
    return out


def _tidy(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:?!])", r"\1", text)
    return re.sub(r"\(\s+", "(", text)


def take_notes(
    source: str,
    translation: str,
    *,
    note_words: int = DEFAULT_NOTE_WORDS,
    markers: re.Pattern = NOTE_MARKERS,
    never_pairs: frozenset = frozenset(),
) -> tuple[str, list[str]]:
    """Lift the editorial parentheticals out of ``translation``.

    Returns the translation without them and the notes in printed order. A
    parenthetical paired with the source is never taken: it belongs to the
    example, not to the editor.
    """
    spans = classify(
        source, translation, note_words=note_words, markers=markers
    )
    notes = [s.inner for s in spans if s.kind == NOTE]
    if not notes:
        return translation, []
    kept = []
    last = 0
    for span in spans:
        if span.kind != NOTE:
            continue
        kept.append(translation[last : span.start])
        last = span.end
    kept.append(translation[last:])
    return _tidy("".join(kept)), notes


def split_in_step(
    source: str,
    translation: str,
    *,
    note_words: int = DEFAULT_NOTE_WORDS,
    markers: re.Pattern = NOTE_MARKERS,
    never_pairs: frozenset = frozenset(),
) -> list[tuple[str, str]] | None:
    """Expand one paired parenthetical on both sides at once (POL-026).

    ``x y (z)`` / ``X Y (Z)`` becomes ``x y`` / ``X Y`` and ``x y z`` / ``X Y Z``.
    Returns None unless exactly one parenthetical pairs on each side, because
    with two or more nothing says which renders which.

    Whether they pair is ``classify``'s question, not a bare count's: an
    editorial marker, or a note's worth of English against a single bracketed
    source word, means the bracket is about the sentence and there is nothing to
    expand in step.
    """
    labelled = classify(
        source, translation,
        note_words=note_words, markers=markers, never_pairs=never_pairs,
    )
    if len(labelled) != 1 or labelled[0].kind != PAIRED:
        return None
    src = parentheticals(source)
    if len(src) != 1:
        return None
    s, t = src[0], labelled[0]

    def without(text, span):
        return _tidy(text[: span.start] + text[span.end :])

    def within(text, span):
        return _tidy(text[: span.start] + span.inner + text[span.end :])

    return [
        (without(source, s), without(translation, t)),
        (within(source, s), within(translation, t)),
    ]
