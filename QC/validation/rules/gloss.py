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
- V061 SOFT: M-count vs. morpheme count implied by W FORM segmentation.
- V062 HARD: M with infix-shaped FORM requires angle-bracket gloss on parent W's TRANSL.
- V063 HARD: W-FORM segmentation markers preserved when S-FORM has > 3 markers.
- V064 HARD: every M element must have at least one TRANSL child.
- V065 SOFT: every W element should have at least one TRANSL child.
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


def _count_morphemes_from_form(form_text: str) -> int:
    """Number of morphemes implied by a W FORM string.

    Rules:
    - Each ``<...>`` group is one infix morpheme.
    - After removing the infix groups, split the remainder on ``-`` and
      ``=`` to get the remaining morpheme segments.
    - Total = number of infix groups + number of non-empty segments.

    Examples:
        'ka'        -> 1
        'ika-doa'   -> 2
        'k-anak-an' -> 3
        'ma=luhay'  -> 2
        'k<um>ita'  -> 2  (infix 'um' + root 'kita')
    """
    if not form_text:
        return 0
    infixes = re.findall(r'<[^>]+>', form_text)
    remainder = re.sub(r'<[^>]+>', '', form_text)
    segments = re.split(r'[-=]', remainder)
    return len(infixes) + len([s for s in segments if s])


def _get_w_form(w_elem: etree._Element) -> str:
    """Return W's preferred FORM text. Original > any FORM > ''."""
    original = w_elem.find('./FORM[@kindOf="original"]')
    if original is not None and original.text:
        return original.text.strip()
    any_form = w_elem.find('./FORM')
    if any_form is not None and any_form.text:
        return any_form.text.strip()
    return ''


def _count_segmentation_chars(text: str) -> int:
    """Count occurrences of ``-``, ``=``, ``<``, ``>`` in ``text``.

    Used by V063 to measure how much segmentation information a FORM
    string carries.
    """
    if not text:
        return 0
    return sum(text.count(c) for c in "-=<>")


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
# V061: M-count vs. implied-morpheme-count (SOFT)
# ---------------------------------------------------------------------------

def v061_M_count_matches_form_segmentation(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V061 SOFT: count of <M> children of W should match the number of
    morphemes implied by the W's FORM segmentation markers
    (``-``, ``=``, ``<...>``).

    Exception: a monomorphemic W with 0 M children is acceptable —
    morpheme markup is optional when there is only one morpheme.
    """
    findings: list[Finding] = []
    for w in tree.iter("W"):
        form_text = _get_w_form(w)
        if not form_text:
            continue  # V011/V012 handle missing FORM
        expected = _count_morphemes_from_form(form_text)
        actual = sum(1 for child in w if child.tag == "M")
        # Monomorphemic with no M tags is acceptable
        if expected == 1 and actual == 0:
            continue
        if expected == actual:
            continue
        w_id = w.get("id")
        parent_s = w.getparent()
        s_id = parent_s.get("id") if parent_s is not None and parent_s.tag == "S" else None
        loc = f"W={w_id}" if w_id else "W"
        if s_id:
            loc = f"S={s_id} {loc}"
        findings.append(Finding(
            rule_id="V061",
            severity=Severity.SOFT,
            message=(
                f"W id={w_id!r}: M-count ({actual}) does not match implied "
                f"morpheme count ({expected}) from FORM {form_text!r}"
            ),
            path=path,
            location=loc,
            count=1,
        ))
    return findings


# ---------------------------------------------------------------------------
# V063: W-FORM segmentation preservation (HARD)
# ---------------------------------------------------------------------------

def v063_W_FORM_retains_segmentation(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V063 HARD: when an S-level FORM[@kindOf='original'] carries more
    than 3 segmentation markers (``-``, ``=``, ``<``, ``>``), the W
    children's FORMs (both ``original`` and ``standard`` tiers) must
    collectively retain at least N/2 such markers each.

    Catches the failure mode where a cleaner regressed and stripped
    segmentation markers from W-level FORMs (which would silently
    destroy gloss alignment). The >3 threshold avoids false positives
    on short S elements where rounding "at least half" is ambiguous —
    e.g., a single inflectional ``-`` plus one clitic ``=`` would
    yield N=2, threshold=1, and a single retained marker would
    technically satisfy the rule without genuinely preserving the
    segmentation.
    """
    findings: list[Finding] = []
    for s in tree.iter("S"):
        s_original = s.find('./FORM[@kindOf="original"]')
        if s_original is None:
            continue
        s_count = _count_segmentation_chars(s_original.text or "")
        if s_count <= 3:
            continue
        ws = [child for child in s if child.tag == "W"]
        if not ws:
            continue  # legitimately unsegmented; rule no-ops
        threshold = s_count / 2
        original_sum = 0
        standard_sum = 0
        for w in ws:
            for form in w.findall('./FORM'):
                kind = form.get("kindOf")
                marker_count = _count_segmentation_chars(form.text or "")
                if kind == "original":
                    original_sum += marker_count
                elif kind == "standard":
                    standard_sum += marker_count
        s_id = s.get("id")
        loc = f"S={s_id}" if s_id else "S"
        if original_sum < threshold:
            findings.append(Finding(
                rule_id="V063",
                severity=Severity.HARD,
                message=(
                    f"S id={s_id!r}: W FORM[@kindOf='original'] retains "
                    f"{original_sum} segmentation markers but S-level FORM has "
                    f"{s_count}; expected at least {threshold:g}. Possible "
                    "cleaner regression dropped segmentation markers."
                ),
                path=path,
                location=loc,
            ))
        if standard_sum < threshold:
            findings.append(Finding(
                rule_id="V063",
                severity=Severity.HARD,
                message=(
                    f"S id={s_id!r}: W FORM[@kindOf='standard'] retains "
                    f"{standard_sum} segmentation markers but S-level FORM has "
                    f"{s_count}; expected at least {threshold:g}. Possible "
                    "cleaner regression dropped segmentation markers."
                ),
                path=path,
                location=loc,
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
# V064: every M must have a TRANSL child (HARD)
# ---------------------------------------------------------------------------

def v064_every_M_has_TRANSL(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V064 HARD: every M element must have at least one TRANSL child.

    Per user direction: an unglossed morpheme has no legitimate purpose
    in a segmented corpus. One Finding per offending M.
    """
    findings: list[Finding] = []
    for m in tree.iter("M"):
        if any(child.tag == "TRANSL" for child in m):
            continue
        m_id = m.get("id")
        findings.append(Finding(
            rule_id="V064",
            severity=Severity.HARD,
            message=(
                f"M id={m_id!r} has no TRANSL child; every M must have "
                "at least one TRANSL (M-level gloss is mandatory)"
            ),
            path=path,
            location=f"M={m_id}" if m_id else "M",
        ))
    return findings


# ---------------------------------------------------------------------------
# V065: every W should have a TRANSL child (SOFT)
# ---------------------------------------------------------------------------

def v065_every_W_has_TRANSL(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V065 SOFT: every W element should have at least one TRANSL child.

    SOFT (not HARD) because rare legitimate cases exist where a W-level
    gloss is absent (e.g., function-word stubs glossed only at the M
    tier).
    """
    findings: list[Finding] = []
    for w in tree.iter("W"):
        if any(child.tag == "TRANSL" for child in w):
            continue
        w_id = w.get("id")
        findings.append(Finding(
            rule_id="V065",
            severity=Severity.SOFT,
            message=(
                f"W id={w_id!r} has no TRANSL child; W-level gloss is "
                "almost always expected"
            ),
            path=path,
            location=f"W={w_id}" if w_id else "W",
            count=1,
        ))
    return findings


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

RULES: list = [
    v060_W_count_matches_word_count,
    v061_M_count_matches_form_segmentation,
    v062_infix_M_needs_angle_gloss,
    v063_W_FORM_retains_segmentation,
    v064_every_M_has_TRANSL,
    v065_every_W_has_TRANSL,
]
CROSS_FILE_RULES: list = []
