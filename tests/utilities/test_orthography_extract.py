"""Unit tests for QC/orthography/orthography_extract.py.

Focused regression coverage. Most of orthography_extract is matplotlib-
dependent plotting and corpus-walking I/O that isn't worth unit-testing
in isolation; this file pins the small pure helpers that have come up
in roadmap items.

`extract_orthographic_info` applies a `>= 5` frequency threshold —
characters seen fewer than 5 times are stripped from the result.
Tests work around this by repeating each character at least 5 times
in the input text.
"""
from QC.orthography.orthography_extract import extract_orthographic_info


def _times(n: int, *literals: str) -> str:
    """Repeat each literal n times with spaces in between (always at
    least one space — extract_orthographic_info has an unconditional
    `unique_chars.remove(" ")` that crashes on space-free input).
    Ensures every character clears the >= 5 frequency threshold."""
    pieces = []
    for literal in literals:
        # Insert a space between every repetition so spaces are always
        # in the input, regardless of how many literals are passed.
        pieces.append(" ".join([literal] * n))
    return " ".join(pieces)


def test_extract_orthographic_info_unescapes_html_entities():
    """B7: literal HTML/XML escape sequences embedded as text in FORM
    content (e.g., from a scraper that double-encoded) must be decoded
    before character counting.

    Without `html.unescape()`, each occurrence of `&amp;` is counted as
    five separate characters (`&`, `a`, `m`, `p`, `;`) instead of the
    single intended `&`, polluting orthography statistics and the
    similarity metrics that feed B4 threshold calibration.
    """
    # Build input where the escape sequences appear 5+ times so the
    # decoded forms (and any accidental literal letters from un-decoded
    # sequences) clear the threshold.
    text = _times(5, "&amp;", "&lt;", "&gt;", "&quot;")
    info = extract_orthographic_info(text)
    chars = set(info["character_frequency"].keys())
    # Decoded forms must be present (each appears 5 times, well above threshold).
    assert "&" in chars
    assert "<" in chars
    assert ">" in chars
    assert '"' in chars
    # If unescape failed, the literal letters of "amp", "lt", "quot"
    # would each appear 5 times and be in the result. 'm' from "amp",
    # 'l' from "lt", 'q' / 'u' / 'o' / 't' from "quot" do not appear in
    # the input outside the escape sequences, so their absence pins the
    # unescape behavior.
    assert "m" not in chars, "html.unescape didn't run — found literal 'amp'"
    assert "l" not in chars, "html.unescape didn't run — found literal 'lt'"
    assert "q" not in chars, "html.unescape didn't run — found literal 'quot'"


def test_extract_orthographic_info_numeric_entity():
    """Numeric character references (&#65; → 'A') also decode."""
    # &#65; is 'A'; repeat enough times so the decoded 'a' clears the
    # threshold while none of the literal entity-sequence chars do.
    text = _times(5, "&#65;")
    info = extract_orthographic_info(text)
    chars = set(info["character_frequency"].keys())
    assert "a" in chars, "&#65; should decode to 'A' (lowercased to 'a')"
    # If unescape failed, '#' would appear 5 times and survive the threshold.
    assert "#" not in chars
    assert "6" not in chars


def test_extract_orthographic_info_plain_text_unchanged():
    """Text without any escape sequences passes through unaffected."""
    # Repeat the alphabet 5 times so every letter clears the threshold.
    text = _times(5, "hello", "world")
    info = extract_orthographic_info(text)
    chars = set(info["character_frequency"].keys())
    assert chars == {"h", "e", "l", "o", "w", "r", "d"}
