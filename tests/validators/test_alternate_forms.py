"""Tests for the POL-028 alternate-FORM rules (V149 HARD, V150 SOFT)."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from lxml import etree

from QC.validation.rules import hard as hard_rules
from QC.validation.rules import soft as soft_rules

_HEAD = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<TEXT id="T1" citation="t" BibTeX_citation="@t{t}" '
    'copyright="t" xml:lang="pwn">'
)


def _tree(body: str) -> etree._ElementTree:
    return etree.parse(BytesIO((_HEAD + body + "</TEXT>").encode("utf-8")))


def test_v149_alternate_without_base_sibling_is_hard():
    tree = _tree('<S id="S1"><FORM kindOf="alternate">soa</FORM></S>')
    findings = hard_rules.v149_alternate_FORM_requires_base_sibling(
        tree, Path("test.xml"), None
    )
    assert len(findings) == 1
    assert findings[0].rule_id == "V149"
    assert findings[0].location == "S=S1"


def test_v149_alternate_with_original_sibling_passes():
    tree = _tree(
        '<S id="S1">'
        '<FORM kindOf="original">so</FORM>'
        '<FORM kindOf="alternate">soa</FORM>'
        '</S>'
    )
    assert hard_rules.v149_alternate_FORM_requires_base_sibling(
        tree, Path("test.xml"), None
    ) == []


def test_v149_alternate_with_standard_sibling_passes():
    """The sibling need not be the original tier — any non-alternate counts."""
    tree = _tree(
        '<W id="S1W1">'
        '<FORM kindOf="standard">poken-en</FORM>'
        '<FORM kindOf="alternate">poken</FORM>'
        '</W>'
    )
    assert hard_rules.v149_alternate_FORM_requires_base_sibling(
        tree, Path("test.xml"), None
    ) == []


def test_v149_checks_own_parent_not_ancestors():
    """An S-level original does not license a bare alternate on a child W."""
    tree = _tree(
        '<S id="S1">'
        '<FORM kindOf="original">so</FORM>'
        '<W id="S1W1"><FORM kindOf="alternate">soa</FORM></W>'
        '</S>'
    )
    findings = hard_rules.v149_alternate_FORM_requires_base_sibling(
        tree, Path("test.xml"), None
    )
    assert [f.location for f in findings] == ["W=S1W1"]


def test_v149_file_with_no_alternates_is_silent():
    tree = _tree('<S id="S1"><FORM kindOf="original">so</FORM></S>')
    assert hard_rules.v149_alternate_FORM_requires_base_sibling(
        tree, Path("test.xml"), None
    ) == []


def _pair(base_kind: str, base: str, alt: str) -> etree._ElementTree:
    return _tree(
        f'<W id="W1">'
        f'<FORM kindOf="{base_kind}">{base}</FORM>'
        f'<FORM kindOf="alternate">{alt}</FORM>'
        f'</W>'
    )


def _v150(tree):
    return soft_rules.v150_alternate_FORM_low_overlap(tree, Path("t.xml"), None)


def test_v150_high_overlap_passes():
    """so/soa — a real Latham spelling variant, ratio 0.80."""
    assert _v150(_pair("original", "so", "soa")) == []


def test_v150_both_forms_short_is_exempt():
    """a/u scores 0.00 but is a correct one-letter variant (Wakelin Kwaway
    S2W3). Neither condition may fire: the ratio is unmeasurable at this
    length, and the lengths are equal."""
    assert _v150(_pair("original", "a", "u")) == []


def test_v150_cross_lexeme_fails_overlap():
    """tau/ratta — Latham 'hair', two different words. Overlap fails
    (ratio 0.50, shorter form 3 > 2); proportion passes (5 <= 2*3). This is
    the defect a looser overlap cutoff would hide."""
    findings = _v150(_pair("original", "tau", "ratta"))
    assert len(findings) == 1
    assert findings[0].rule_id == "V150"
    assert findings[0].severity is soft_rules.Severity.SOFT
    assert findings[0].location == "W=W1"
    assert "overlap" in findings[0].message


def test_v150_short_against_long_fails_proportion_only():
    """am/namen — Wakelin. The shorter form is 2, so the overlap condition
    is exempt; only proportion catches it (5 > 2*2).

    This test is what proves the proportion condition is load-bearing:
    delete `proportion_fails` from the rule and this test goes green
    wrongly."""
    findings = _v150(_pair("original", "am", "namen"))
    assert len(findings) == 1
    assert "lengths" in findings[0].message
    assert "overlap" not in findings[0].message


def test_v150_wildly_mismatched_lengths_fail_both():
    """The control case: a short form paired with a very long one is never a
    spelling variant, and must be caught even if either condition is later
    refactored."""
    findings = _v150(
        _pair("original", "dog", "supercalifragilisticexpialidocious")
    )
    assert len(findings) == 1
    assert "overlap" in findings[0].message
    assert "lengths" in findings[0].message


def test_v150_truncation_fails_proportion():
    """tigpapahoang/tigp — Utrecht W118, 12 vs 4."""
    findings = _v150(_pair("original", "tigpapahoang", "tigp"))
    assert len(findings) == 1
    assert "lengths" in findings[0].message


def test_v150_compares_against_closest_sibling():
    """With both an original and a standard present, the alternate is judged
    against whichever it resembles most — here the standard."""
    tree = _tree(
        '<W id="W1">'
        '<FORM kindOf="original">zzzzzz</FORM>'
        '<FORM kindOf="standard">poken-en</FORM>'
        '<FORM kindOf="alternate">poken</FORM>'
        '</W>'
    )
    assert _v150(tree) == []


def test_v150_ignores_case():
    """Kan/kan-u differs only in case once folded."""
    assert _v150(_pair("original", "Kan", "kan-u")) == []


def test_v150_ignores_diacritics():
    """Combining marks are stripped before comparison, so a pair differing
    only in accents reads as identical rather than as five substitutions.

    Chosen so folding changes the verdict: unfolded these share no
    characters at all (ratio 0.00, which would flag), folded they are the
    same string.
    """
    assert _v150(_pair("original", "áéíóú", "aeiou")) == []


def test_v150_no_base_sibling_is_left_to_v149():
    tree = _tree('<W id="W1"><FORM kindOf="alternate">soa</FORM></W>')
    assert _v150(tree) == []


def test_v150_long_near_identical_pair_does_not_collapse():
    """A >200-character pair differing by a single letter must score near
    1.0, not be dragged down by difflib's default autojunk heuristic.

    difflib.SequenceMatcher(autojunk=True) (the default) treats any element
    occurring more than len(b)//100 + 1 times in a sequence of length >=200
    as "popular" and excludes it from matching. Natural-language text is
    mostly a small alphabet repeated often, so at this length nearly every
    character gets marked junk and the ratio collapses even though only one
    character actually differs. This reproduces that failure mode with
    repeated phrase text (as opposed to a hand-picked pathological string)
    and pins the fix: the rule must pass autojunk=False.
    """
    phrase = "sasavakan ku wawa i cireng no riyar "
    base = (phrase * 10)[:220]
    alt = base[:110] + ("q" if base[110] != "q" else "p") + base[111:]
    assert len(base) >= 200
    assert _v150(_pair("original", base, alt)) == []
