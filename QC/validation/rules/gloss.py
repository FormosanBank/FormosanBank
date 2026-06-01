"""Gloss-validation rules.

Rule module for `validate_glosses.py`. Same signature contract as
`rules/hard.py` and `rules/soft.py`:

    rule(tree: etree._ElementTree, path: Path, index: CorpusIndex | None) -> list[Finding]

Severities are per-rule, not per-module (this file holds a mix of
HARD and SOFT rules). The naming follows the historical convention
where `rules/hard.py` already mixes severities; renaming hard.py is
deferred (see B9.3 plan, "Open questions").

Rules:
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
    v062_infix_M_needs_angle_gloss,
]
CROSS_FILE_RULES: list = []
