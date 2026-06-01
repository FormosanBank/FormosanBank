"""Gloss-validation rules.

Rule module for `validate_glosses.py`. Same signature contract as
`rules/hard.py` and `rules/soft.py`:

    rule(tree: etree._ElementTree, path: Path, index: CorpusIndex | None) -> list[Finding]

Severities are per-rule, not per-module (this file holds a mix of
HARD and SOFT rules). The naming follows the historical convention
where `rules/hard.py` already mixes severities; renaming hard.py is
deferred (see B9.3 plan, "Open questions").

Rules:
- V060 SOFT: W-count vs. word-count in S-level FORM[@kindOf="original"].
- V062 HARD: M with infix-shaped FORM requires angle-bracket gloss on parent W's TRANSL.
"""
import re
from pathlib import Path

from lxml import etree

from QC.validation._corpus_index import CorpusIndex
from QC.validation._finding import Finding, Severity


# Infix shape: starts and ends with '-' with non-'-' content between.
_INFIX_PATTERN = re.compile(r"^-[^-]+-$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _count_words(text: str | None) -> int:
    """Count whitespace-delimited words in ``text``.

    Mirrors validate_glosses.py's pre-refactor behavior: split on any
    run of whitespace, drop empty segments.
    """
    if not text:
        return 0
    parts = re.split(r"\s+", text.strip())
    return len([p for p in parts if p])


def _extract_s_direct_text(s_elem: etree._Element) -> str:
    """Return the text of the S element's preferred FORM child.

    Preference order: FORM[@kindOf='original'] > any FORM > S's own
    direct text. Matches validate_glosses.py's extract_s_direct_text
    behavior; carried over so V060's word counts agree with the legacy
    CSV output.
    """
    original = s_elem.find('./FORM[@kindOf="original"]')
    if original is not None and original.text:
        return original.text.strip()
    any_form = s_elem.find('./FORM')
    if any_form is not None and any_form.text:
        return any_form.text.strip()
    return (s_elem.text or "").strip()


# ---------------------------------------------------------------------------
# V060: W-count vs. word-count (SOFT)
# ---------------------------------------------------------------------------

def v060_W_count_matches_word_count(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V060 SOFT: count of <W> children of S should match the number of
    whitespace-delimited words in the S's FORM[@kindOf="original"].

    Why SOFT: spelling normalization and standardization can legitimately
    change word count between the S-level FORM (free text) and the W
    tier (tokenized). Reporting these is informational, not a corpus
    bug per se.
    """
    findings: list[Finding] = []
    for s in tree.iter("S"):
        s_id = s.get("id")
        # No FORM at all -> V010/V013 handle that; we have nothing to compare.
        if s.find('./FORM') is None:
            continue
        s_text = _extract_s_direct_text(s)
        word_count = _count_words(s_text)
        direct_w = [child for child in s if child.tag == "W"]
        w_count = len(direct_w)
        nested_w = list(s.iter("W"))
        if len(nested_w) != w_count:
            # Preserve validate_glosses.py:166-169 warning behavior:
            # nested W (descendant of S but not direct child) is unusual.
            # Surface it but don't double-count.
            print(
                f"  Warning: Found {len(nested_w)} total W elements but "
                f"{w_count} direct children in S[@id='{s_id}'] of {path}"
            )
        if word_count == w_count:
            continue
        findings.append(Finding(
            rule_id="V060",
            severity=Severity.SOFT,
            message=(
                f"S id={s_id!r}: W-count ({w_count}) does not match "
                f"word-count ({word_count}) in FORM[@kindOf='original']; "
                "may be due to normalization or spelling"
            ),
            path=path,
            location=f"S={s_id}" if s_id else "S",
            count=1,
        ))
    return findings


# ---------------------------------------------------------------------------
# V062: infix-M requires angle-bracket gloss on parent W's TRANSL (HARD)
# ---------------------------------------------------------------------------

def v062_infix_M_needs_angle_gloss(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V062: an M whose FORM has infix shape ('-X-') requires parent W to have
    a TRANSL containing an angle-bracket gloss (e.g., '<AV>').

    Infix shape: FORM text matches /^-[^-]+-$/ (starts and ends with '-').
    Angle-bracket gloss: TRANSL text contains '<...>' (any '<' followed
    eventually by '>').

    Moved here from rules/hard.py during B9.3 — conceptually a gloss
    rule, not an XML-structure rule.
    """
    findings: list[Finding] = []
    for m in tree.iter("M"):
        form_text = None
        for child in m:
            if child.tag == "FORM":
                form_text = (child.text or "").strip()
                break
        if form_text is None or not _INFIX_PATTERN.match(form_text):
            continue
        parent_w = m.getparent()
        if parent_w is None or parent_w.tag != "W":
            continue
        has_angle_gloss = False
        for child in parent_w:
            if child.tag == "TRANSL":
                text = child.text or ""
                if "<" in text and ">" in text:
                    has_angle_gloss = True
                    break
        if not has_angle_gloss:
            m_id = m.get("id")
            w_id = parent_w.get("id")
            findings.append(Finding(
                rule_id="V062",
                severity=Severity.HARD,
                message=(
                    f"M id={m_id!r} has infix FORM {form_text!r} but parent "
                    f"W id={w_id!r} has no TRANSL with an angle-bracket gloss "
                    "('<X>'); infix morphemes require angle-bracket gloss notation"
                ),
                path=path,
                location=f"M={m_id}" if m_id else "M",
            ))
    return findings


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

RULES: list = [
    v060_W_count_matches_word_count,
    v062_infix_M_needs_angle_gloss,
]
CROSS_FILE_RULES: list = []
