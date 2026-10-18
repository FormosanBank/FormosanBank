"""Position-aware decoding helpers for the dictionary's Type 3 PDF fonts."""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

import fitz


@dataclass(frozen=True)
class Span:
    x0: float
    x1: float
    y0: float
    text: str
    font: str


@dataclass(frozen=True)
class Row:
    y0: float
    spans: tuple[Span, ...]


CONTROL_REPLACEMENTS = {
    "\x0b": "ff",
    "\x0c": "fi",
    "\r": "fl",
    "\x0f": "ffl",
    "\x10": "i",
    "\x12": "θ",
}
ACCENTS = {
    "a": "á",
    "e": "é",
    "i": "í",
    "o": "ó",
    "u": "ú",
    "A": "Á",
    "E": "É",
    "I": "Í",
    "O": "Ó",
    "U": "Ú",
}


# TeX's OT1 text encoding puts its accents in the last positions of the font:
# 0x7B endash, 0x7C emdash, 0x7D double acute, 0x7E TILDE, 0x7F dieresis. The
# first two are already decoded below. The tilde is an accent like the acute at
# 0x13 - drawn as its own glyph, positioned just left of the letter it sits on -
# and NOT a repetition mark: read in place it gives Blust's PAN reconstructions
# back exactly as published (*naCuq~ -> *naCuq with a tilde over the n, i.e.
# *qanud~ -> *qanud -> *qanud). All 74 of them are on 15 pages.
TILDES = {
    "a": "ã", "e": "ẽ", "i": "ĩ", "o": "õ", "u": "ũ", "n": "ñ",
    "A": "Ã", "E": "Ẽ", "I": "Ĩ", "O": "Õ", "U": "Ũ", "N": "Ñ",
}
TILDE_OVERLAY = "~"


def decode_type3(value: str) -> str:
    """Decode the custom glyph codes emitted by PyMuPDF for this source."""
    for encoded, decoded in CONTROL_REPLACEMENTS.items():
        value = value.replace(encoded, decoded)
    value = value.replace("Æ", "ffi")

    result: list[str] = []
    index = 0
    while index < len(value):
        character = value[index]
        if character == "\x13" and index + 1 < len(value):
            base = value[index + 1]
            result.append(ACCENTS.get(base, "\N{COMBINING ACUTE ACCENT}" + base))
            index += 2
            continue
        if character == TILDE_OVERLAY and index + 1 < len(value):
            base = value[index + 1]
            result.append(TILDES.get(base, "\N{COMBINING TILDE}" + base))
            index += 2
            continue
        result.append(character)
        index += 1
    value = (
        "".join(result)
        .replace("{", "–")
        .replace("|", "—")
        .replace("\\", "“")
        .replace('"', "”")
    )
    value = value.replace(BAR_SENTINEL, "|")
    value = unicodedata.normalize("NFC", value)
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"\s+([,.;:?!')])", r"\1", value)
    return value


# Two glyphs of the italic Type 3 face carry no usable ToUnicode mapping and
# come back as ordinary letters. Both are structural, and both were being read
# as text: the vertical bar that brackets a headword (|anak|, which the
# re-typeset p. 291 prints literally) and the arrow that opens a
# cross-reference. They are font-specific, so they cannot be fixed in
# decode_type3, which sees only a string - `j` is a real letter elsewhere
# (Lujan) and `!` real punctuation.
# The bar goes in as a sentinel because decode_type3 is font-blind and maps a
# literal "|" to the em dash it is in every other face.
BAR_SENTINEL = "\ue000"
ITALIC_GLYPHS = {"j": BAR_SENTINEL, "!": "\u2192"}
ITALIC_FACE = "T10"


def repair_span_text(font: str, text: str) -> str:
    if font == ITALIC_FACE and text.strip() in ITALIC_GLYPHS:
        return text.replace(text.strip(), ITALIC_GLYPHS[text.strip()])
    return text


def _flatten(page: fitz.Page) -> list[Span]:
    result: list[Span] = []
    for block in page.get_text("dict", sort=False)["blocks"]:
        for line in block.get("lines", []):
            for item in line["spans"]:
                result.append(
                    Span(
                        x0=float(item["bbox"][0]),
                        x1=float(item["bbox"][2]),
                        y0=float(item["bbox"][1]),
                        text=repair_span_text(
                            str(item["font"]), str(item["text"])
                        ),
                        font=str(item["font"]),
                    )
                )
    return result


def page_rows(page: fitz.Page, tolerance: float = 3.1) -> list[Row]:
    """Cluster positioned spans into visual rows."""
    clusters: list[list[Span]] = []
    for span in sorted(_flatten(page), key=lambda item: (item.y0, item.x0)):
        if clusters:
            center = sum(item.y0 for item in clusters[-1]) / len(clusters[-1])
            if abs(span.y0 - center) <= tolerance:
                clusters[-1].append(span)
                continue
        clusters.append([span])
    return [
        Row(
            y0=sum(item.y0 for item in cluster) / len(cluster),
            spans=tuple(sorted(cluster, key=lambda item: item.x0)),
        )
        for cluster in clusters
    ]


def join_spans(spans: list[Span] | tuple[Span, ...], gap: float = 2.2) -> str:
    """Reassemble TeX fragments, retaining spaces visible between words."""
    # A standalone acute-accent glyph is positioned just to the right of the
    # vowel span it modifies. Move only that overlay ahead of the base span.
    ordered = sorted(
        spans,
        key=lambda item: item.x0 - 0.5
        if item.text in ("\x13", TILDE_OVERLAY)
        else item.x0,
    )
    if not ordered:
        return ""
    parts = [ordered[0].text]
    right = ordered[0].x1
    for span in ordered[1:]:
        if span.x0 - right > gap:
            parts.append(" ")
        parts.append(span.text)
        right = max(right, span.x1)
    return decode_type3("".join(parts))


#: Hyphenated English words the book prints WITHIN a single column line, so a
#: hyphen at a line break that would rebuild one of them is the word's own and
#: not TeX's. Empty until `learn_hyphenation` is called, which leaves
#: `append_wrapped` behaving exactly as it always did: a trailing hyphen is
#: always TeX's. See `learn_hyphenation` for why it has to be learned.
HYPHENATED_WORDS: frozenset = frozenset()

_HYPHENATED = re.compile(r"(?<![-\w])([A-Za-z]+(?:-[A-Za-z]+)+)(?![-\w])")
_WRAPPED_TAIL = re.compile(r"([A-Za-z]+(?:-[A-Za-z]+)*)-$")
_WRAPPED_HEAD = re.compile(r"[A-Za-z]+(?:-[A-Za-z]+)*")


def learn_hyphenation(lines) -> frozenset:
    """Record every hyphenated word the book prints inside one printed line.

    TeX hyphenates at a line break with the same glyph the text uses for a
    real hyphen, so a line ending in `-` is ambiguous, and no rule over the
    string alone can tell `contin-`/`uation` from `daughter-`/`in-law`.

    The book resolves it. Each of these words is ALSO printed somewhere it did
    not fall at a break - `daughter-in-law` 16 times, `well-behaved` 4, the
    place names `Sun-Moon` 31 and `Pu-Li` 81 - so the book is its own evidence
    for which hyphens belong to the word. Where it offers none the hyphen is
    assumed to be TeX's, which is right the overwhelming majority of the time:
    of 5,586 line-break joins this keeps the hyphen in 60, across 39 words.

    `lines` is every printed line of the book, ALREADY SPLIT BY COLUMN - a raw
    page row spans both columns and interleaves them, which manufactures
    hyphenations that were never printed.
    """
    global HYPHENATED_WORDS
    found = set()
    for line in lines:
        for match in _HYPHENATED.finditer(line):
            found.add(match.group(1).casefold())
    HYPHENATED_WORDS = frozenset(found)
    return HYPHENATED_WORDS


def learn_hyphenation_from(document, pages, column_split: float = 300.0,
                           line_tolerance: float = 7.5,
                           gap: float = 1.2) -> frozenset:
    """Build the evidence from the book, one column at a time.

    The column split and tolerance mirror parse_entries' own line clustering,
    because the lines this reads have to be the lines the joiner will meet.
    """
    lines = []
    for pdf_page in pages:
        # DICTIONARY_PAGES holds 1-based printed page numbers, as every other
        # caller in this repo assumes.
        rows = page_rows(document[pdf_page - 1])
        for low, high in ((0.0, column_split), (column_split, 1e9)):
            clustered: list[tuple[float, list]] = []
            for row in sorted(rows, key=lambda item: item.y0):
                spans = [s for s in row.spans if low <= s.x0 < high]
                if not spans:
                    continue
                if clustered and row.y0 - clustered[-1][0] <= line_tolerance:
                    clustered[-1][1].extend(spans)
                else:
                    clustered.append((row.y0, list(spans)))
            lines.extend(
                join_spans(sorted(spans, key=lambda s: s.x0), gap=gap)
                for _y0, spans in clustered
            )
    return learn_hyphenation(lines)


def append_wrapped(previous: str, continuation: str) -> str:
    """Join printed lines while removing source line-break hyphenation."""
    previous = previous.rstrip()
    continuation = continuation.lstrip()
    if not previous:
        return continuation
    if previous.endswith("-"):
        if HYPHENATED_WORDS:
            tail = _WRAPPED_TAIL.search(previous)
            head = _WRAPPED_HEAD.match(continuation)
            if tail and head:
                whole = f"{tail.group(1)}-{head.group(0)}"
                if whole.casefold() in HYPHENATED_WORDS:
                    # The word's own hyphen, which happened to land on the
                    # break: `daughter-` + `in-law`, not `contin-` + `uation`.
                    return previous + continuation
        return previous[:-1] + continuation
    if previous.endswith("–"):
        return previous + continuation
    return f"{previous} {continuation}"


def standardize_blust(value: str) -> str:
    """Convert Blust's stated source alphabet to canonical Thao Ortho113."""
    decomposed = unicodedata.normalize("NFD", value)
    without_stress = "".join(
        character
        for character in decomposed
        if unicodedata.category(character) != "Mn"
    )
    value = unicodedata.normalize("NFC", without_stress).replace("–", "-")
    value = re.sub(r"c", "th", value)
    value = re.sub(r"C", "Th", value)
    value = re.sub(r"g", "ng", value)
    value = re.sub(r"G", "Ng", value)
    return value
