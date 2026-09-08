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
- V062 SOFT: M with infix-shaped FORM should have an angle-bracket gloss on parent W's TRANSL.
- V063 HARD/SOFT: W-FORM segmentation markers preserved when S-FORM has > 3 markers
  (SOFT when the file has no standard tier at all, so retention is unverifiable).
- V064 SOFT: every M element should have at least one TRANSL child.
- V065 SOFT: every W element should have at least one TRANSL child.
- V066 HARD: '=' (clitic boundary) in a W FORM must appear in at least one child M FORM.
- V067 HARD: '<' or '>' in an M FORM is forbidden; infix Ms must use '-X-' notation.

V062/V064/V065 form the **gloss-presence family**: gloss coverage and
gloss notation are *reported*, never fatal. Some corpora legitimately
gloss only part of their material, and some record infix glosses in
prose rather than Leipzig angle brackets; both are worth surfacing in
case they are unintended, but neither can block publication.
"""
import re
from collections import Counter
from pathlib import Path

from lxml import etree

from QC.validation._corpus_index import CorpusIndex
from QC.validation._finding import Finding, Severity
from QC.validation.rules._reconstruct import (
    DEFAULT_SIMILARITY_THRESHOLD,
    letter_skeleton,
    similarity,
)


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


def _w_form_with_inline_infixes_marked(form_text: str, w_elem: etree._Element) -> str:
    """Rewrite hyphen-notated inline infixes in a W FORM to ``<X>`` form.

    A W FORM like ``G-m-ealu`` is orthographically identical to a
    prefix-root-suffix string (``k-anak-an``), so it cannot be
    disambiguated on its own. The M tier resolves it: when an M child's
    FORM is infix-shaped (``-X-``, the V067 convention), the matching
    inline ``-X-`` in the W FORM is a single infix morpheme, not two
    segment boundaries. We rewrite each such ``-X-`` to ``<X>`` so the
    morpheme count treats it as one infix and rejoins the root halves —
    mirroring native ``<X>`` notation. W FORMs with no infix-shaped M are
    returned unchanged, so prefix-root-suffix counts are unaffected.
    """
    marked = form_text
    for m in w_elem:
        if m.tag != "M":
            continue
        m_form = _get_w_form(m)
        if _INFIX_PATTERN.match(m_form) and m_form in marked:
            marked = marked.replace(m_form, f"<{m_form.strip('-')}>", 1)
    return marked


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

    Scope (POL-041, 2026-09-03): this rule compares counts, so it only
    applies where a W tier exists to count. A file with no W anywhere is
    simply not word-segmented and is skipped outright; within a partially
    segmented file, an S with no W is skipped too. Whether a sentence
    *ought* to have a W tier is a presence question, owned by V148.
    Without these guards the rule fired once per sentence on every
    sentence-only corpus, with a "may be due to normalization or
    spelling" message that did not describe the situation.
    """
    if tree.find(".//W") is None:
        return []

    findings: list[Finding] = []
    for s in tree.iter("S"):
        s_id = s.get("id")
        # No FORM at all -> V010/V013 handle that; we have nothing to compare.
        if s.find('./FORM') is None:
            continue
        # No W at all -> a presence question (V148), not a count mismatch.
        if s.find('./W') is None:
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
        # Hyphen-notated infixes (e.g. 'G-m-ealu' with an infix M '-m-')
        # are rewritten to '<m>' so they count as one infix morpheme,
        # not two segment boundaries.
        expected = _count_morphemes_from_form(
            _w_form_with_inline_infixes_marked(form_text, w))
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
# V063: W-FORM segmentation preservation
# (HARD; SOFT when the FILE has no standard tier at all)
# ---------------------------------------------------------------------------

def v063_W_FORM_retains_segmentation(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V063: when an S-level FORM[@kindOf='original'] carries more than 3
    segmentation markers (``-``, ``=``, ``<``, ``>``), the W children's
    FORMs (both ``original`` and ``standard`` tiers) must collectively
    retain at least N/2 such markers each.

    Catches the failure mode where a cleaner regressed and stripped
    segmentation markers from W-level FORMs (which would silently
    destroy gloss alignment). The >3 threshold avoids false positives
    on short S elements where rounding "at least half" is ambiguous —
    e.g., a single inflectional ``-`` plus one clitic ``=`` would
    yield N=2, threshold=1, and a single retained marker would
    technically satisfy the rule without genuinely preserving the
    segmentation.

    Severity by tier:

    - **original tier under-retains → HARD.** Unconditional: every
      corpus has an original tier.
    - **standard tier present but under-retains → HARD.** A corpus that
      does maintain a standard tier and drops its markers is a real
      regression.
    - **the file has no standard-tier W FORM at all → SOFT.** Nothing
      was stripped; there is simply no standard tier to check, so
      standard-tier retention is *unverifiable* rather than violated.
      Reported (not skipped) so the gap stays visible. This aligns V063
      with V014 (``QC/validation/rules/soft.py``), which holds that a
      missing standard-tier FORM is informational: some corpora
      legitimately lack one because the orthography is unsettled.

    **Granularity of "has no standard tier": per FILE**, not per
    sentence. A standard tier is all-or-nothing for an XML file: if a
    file has a standard tier, it should appear in every sentence in
    that file (maintainer ruling). A partially populated standard tier
    is therefore itself an anomaly, not a normal case to accommodate,
    so it must not buy a sentence a softer verdict. Consequences:

    - No standard-tier W FORM anywhere in the file → every qualifying
      sentence gets the SOFT "unverifiable" finding.
    - The file *does* have a standard tier → the standard branch is
      exactly what it always was, HARD, for every sentence — including
      a sentence that happens to carry no standard FORMs at all, whose
      ``standard_sum`` of 0 falls below the threshold. In a file that
      has the tier, a sentence missing it is a defect worth failing on.

    Nothing is lost by that strictness: V014 (SOFT) separately counts
    every element missing a standard FORM, so the partially populated
    case is still reported in its own right rather than only as a V063
    HARD.
    """
    findings: list[Finding] = []
    # Decided once for the whole file, before any sentence is judged:
    # a standard tier is all-or-nothing per file (see docstring).
    file_has_standard_tier = any(
        form.get("kindOf") == "standard"
        for w in tree.iter("W")
        for form in w.findall('./FORM')
    )
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
        if not file_has_standard_tier:
            findings.append(Finding(
                rule_id="V063",
                severity=Severity.SOFT,
                message=(
                    f"S id={s_id!r}: no standard tier in this file — no W element "
                    "anywhere in it has a FORM[@kindOf='standard'], so standard-tier "
                    "segmentation retention cannot be verified (S-level FORM has "
                    f"{s_count} segmentation markers; a standard tier would need "
                    f"at least {threshold:g}). Informational, per V014: a corpus "
                    "may legitimately lack a standard tier."
                ),
                path=path,
                location=loc,
            ))
        elif standard_sum < threshold:
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
# V062: infix-M should have angle-bracket gloss on parent W's TRANSL (SOFT)
# ---------------------------------------------------------------------------

def v062_infix_M_needs_angle_gloss(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V062 SOFT: an M whose FORM has infix shape ('-X-') should have a parent
    W with a TRANSL containing an angle-bracket gloss (e.g., '<AV>').

    Infix shape: FORM text matches /^-[^-]+-$/ (starts and ends with '-').
    Angle-bracket gloss: TRANSL text contains '<...>' (any '<' followed
    eventually by '>').

    Moved here from rules/hard.py during B9.3 — conceptually a gloss
    rule, not an XML-structure rule.

    SOFT, not HARD (maintainer ruling): what this rule detects is a
    *notation* difference, not missing data. A corpus may gloss its
    infixes in prose instead of Leipzig angle-bracket notation —
    YeddaPalemeqBlog writes "bring, AV. The root is kacu 'bring'." —
    and that gloss is present and correct, merely written another way.
    POL-036 makes any standardized ``<AV>`` gloss *additive* anyway, so
    the angle-bracket form can be supplied later without discarding
    what the source wrote. Reported so an unexpected omission is still
    visible; never fatal. Part of the gloss-presence family with
    V064/V065 (see module docstring).
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
                severity=Severity.SOFT,
                message=(
                    f"M id={m_id!r} has infix FORM {form_text!r} but parent "
                    f"W id={w_id!r} has no TRANSL with an angle-bracket gloss "
                    "('<X>'); infix morphemes are normally glossed with "
                    "angle-bracket notation, though a corpus may legitimately "
                    "gloss them in prose instead"
                ),
                path=path,
                location=f"M={m_id}" if m_id else "M",
            ))
    return findings


# ---------------------------------------------------------------------------
# V064: every M should have a TRANSL child (SOFT)
# ---------------------------------------------------------------------------

def v064_every_M_has_TRANSL(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V064 SOFT: every M element should have at least one TRANSL child.

    One Finding per offending M.

    SOFT, not HARD (maintainer ruling, superseding the original "an
    unglossed morpheme has no legitimate purpose" direction): for some
    corpora only *some* words are glossed. That is worth flagging in
    case it is unexpected, but gloss completeness cannot be a hard rule
    — partial glossing is a real property of real sources, not a
    defect the pipeline can fix. Part of the gloss-presence family with
    V062/V065 (see module docstring).
    """
    findings: list[Finding] = []
    for m in tree.iter("M"):
        if any(child.tag == "TRANSL" for child in m):
            continue
        m_id = m.get("id")
        findings.append(Finding(
            rule_id="V064",
            severity=Severity.SOFT,
            message=(
                f"M id={m_id!r} has no TRANSL child; an M-level gloss is "
                "normally expected (some corpora gloss only part of their "
                "material)"
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
    tier), and more broadly because some corpora gloss only part of
    their material. Part of the gloss-presence family with V062/V064
    (see module docstring): gloss presence and notation are reported,
    never fatal.
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
# V066: clitic boundary '=' in W FORM must appear in at least one child M FORM (HARD)
# ---------------------------------------------------------------------------


def _m_forms(m_elem: etree._Element) -> list[str]:
    """Return all direct-child FORM text values of an M element."""
    return [
        (child.text or "")
        for child in m_elem
        if child.tag == "FORM"
    ]


def v066_clitic_in_W_requires_clitic_in_M(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V066 HARD: if a W's preferred FORM contains '=' (clitic boundary)
    and the W has at least one child M, at least one of those child M
    FORMs (any kindOf, any tier) must also contain '='.

    Rationale: '=' marks a clitic boundary in the canonical FormosanBank
    convention. The morpheme tier should carry the boundary marker
    explicitly on the cliticized morpheme so that downstream tooling can
    distinguish a clitic from an ordinary affix. A W like 'akia=cu with
    Ms 'akia and 'cu' silently drops the clitic-vs-affix distinction.

    No-ops on Ws with no M children (V061 covers count of Ms; the
    boundary-type check is meaningless without the M tier).
    """
    findings: list[Finding] = []
    for w in tree.iter("W"):
        w_form = _get_w_form(w)
        if "=" not in w_form:
            continue
        ms = [child for child in w if child.tag == "M"]
        if not ms:
            continue
        clitic_present_in_any_M = any(
            "=" in text
            for m in ms
            for text in _m_forms(m)
        )
        if clitic_present_in_any_M:
            continue
        w_id = w.get("id") or ""
        parent_s = w.getparent()
        s_id = parent_s.get("id") if parent_s is not None and parent_s.tag == "S" else None
        loc = f"W={w_id}" if w_id else "W"
        if s_id:
            loc = f"S={s_id} {loc}"
        findings.append(Finding(
            rule_id="V066",
            severity=Severity.HARD,
            message=(
                f"W id={w_id!r}: W FORM {w_form!r} contains '=' (clitic boundary) "
                "but no child M FORM does; clitic boundary must propagate to the M tier"
            ),
            path=path,
            location=loc,
        ))
    return findings


# ---------------------------------------------------------------------------
# V067: angle-bracket notation in M FORM is forbidden (HARD)
# ---------------------------------------------------------------------------


def v067_no_angle_brackets_in_M_FORM(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V067 HARD: no '<' or '>' in any M FORM, either tier.

    Infix morphemes at the M tier must use the canonical '-X-' notation
    (a leading and trailing dash). The angle-bracket convention '<X>'
    is reserved for the W FORM (where it indicates the surface position
    of the infix in the host root) and for the TRANSL gloss (where it
    matches the gloss to the infix morpheme).

    Scope: any direct-child FORM of an M. Fires once per offending M.
    """
    findings: list[Finding] = []
    for m in tree.iter("M"):
        offending_forms: list[tuple[str | None, str]] = []
        for child in m:
            if child.tag != "FORM":
                continue
            text = child.text or ""
            if "<" in text or ">" in text:
                offending_forms.append((child.get("kindOf"), text))
        if not offending_forms:
            continue
        m_id = m.get("id") or ""
        # Compose a stable message listing the first offending FORM
        # (sufficient for diagnostics; downstream tooling can re-parse
        # the M if it needs the full list).
        kind, text = offending_forms[0]
        findings.append(Finding(
            rule_id="V067",
            severity=Severity.HARD,
            message=(
                f"M id={m_id!r}: FORM kindOf={kind!r} contains '<' or '>' "
                f"({text!r}); infix M FORMs must use '-X-' notation, not '<X>'"
            ),
            path=path,
            location=f"M={m_id}" if m_id else "M",
        ))
    return findings


# ---------------------------------------------------------------------------
# V068: M FORMs reconstruct the W FORM (SOFT)
# ---------------------------------------------------------------------------

def v068_M_reconstructs_W(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V068 SOFT: the M FORMs of a W should spell the W FORM.

    Compares the letter-skeleton (Unicode-letter multiset, casefolded) of
    W FORM[@kindOf='original'] against the summed skeletons of its child M
    FORM[@kindOf='original']. SOFT finding when their ``similarity`` falls
    below ``DEFAULT_SIMILARITY_THRESHOLD`` — i.e., the morphemes likely
    belong to a different word (misalignment). This is a content check, not
    a count check (V061): a W could have the right number of Ms that spell
    something unrelated and pass every other gloss rule.

    Original tier only (if it reconstructs, the standard tier follows).
    Because the comparison is a multiset, infixes/circumfixes reconstruct
    perfectly; the threshold tolerates reduplication placeholders and null
    morphemes. Ws with no M child (monomorphemic) and Ws/Ms missing an
    original FORM are skipped — other rules own those cases.
    """
    findings: list[Finding] = []
    for w in tree.iter("W"):
        ms = [child for child in w if child.tag == "M"]
        if not ms:
            continue  # monomorphemic; nothing to reconstruct
        w_form = w.find('./FORM[@kindOf="original"]')
        if w_form is None:
            continue
        w_skel = letter_skeleton(w_form.text)
        if not w_skel:
            continue
        m_skel: Counter = Counter()
        saw_m_form = False
        for m in ms:
            m_form = m.find('./FORM[@kindOf="original"]')
            if m_form is not None and (m_form.text or "").strip():
                saw_m_form = True
                m_skel += letter_skeleton(m_form.text)
        if not saw_m_form:
            continue  # M FORMs missing -> V011/V012/other rules own this
        sim = similarity(w_skel, m_skel)
        if sim >= DEFAULT_SIMILARITY_THRESHOLD:
            continue
        w_id = w.get("id")
        parent_s = w.getparent()
        s_id = parent_s.get("id") if parent_s is not None and parent_s.tag == "S" else None
        loc = f"W={w_id}" if w_id else "W"
        if s_id:
            loc = f"S={s_id} {loc}"
        findings.append(Finding(
            rule_id="V068",
            severity=Severity.SOFT,
            message=(
                f"W id={w_id!r}: child M FORMs reconstruct only {sim:.0%} of the "
                f"W FORM letters; the morphemes may belong to a different word. "
                f"W FORM={w_form.text!r}"
            ),
            path=path,
            location=loc,
            count=1,
        ))
    return findings


# ---------------------------------------------------------------------------
# V069: null morpheme '∅' in W FORM must appear as its own M FORM (HARD)
# ---------------------------------------------------------------------------

_STANDALONE_NULL_RE = re.compile(r"(?:^|(?<=[\s\-]))∅(?=[\s\-]|$)")


def v069_null_morpheme_in_W_requires_null_M(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V069 HARD: if a W's preferred FORM contains a standalone null-morpheme
    marker '∅' (bordered by string edges, whitespace, or segmentation '-')
    and the W has at least one child M, then at least one child M FORM (any
    kindOf) must be exactly '∅'.

    Rationale: the standard tier keeps null morphemes at the W and M levels
    (standardize.py strips them from S-level FORMs only), so a W spelled
    '∅-dhuq' must decompose into M '∅' + M 'dhuq'. A missing null M silently
    drops the zero morpheme from the gloss tier.

    No-ops on Ws with no M children (V061 covers M counts).

    Overlap with V125 (QC/validation/rules/text.py): V125 requires that *some*
    M FORM *contains* '∅' (substring) AND that the S-level original FORM also
    contains '∅'. V069 is stricter on the M side — the M FORM must be *exactly*
    '∅' in standalone morpheme position — and is silent on the S-original
    requirement. Both rules intentionally coexist: V125 operates at the
    text-validation level across all corpora; V069 adds finer-grained
    morpheme-position enforcement at the gloss-validation level.
    """
    findings: list[Finding] = []
    for w in tree.iter("W"):
        w_form = _get_w_form(w)
        if not _STANDALONE_NULL_RE.search(w_form):
            continue
        ms = [child for child in w if child.tag == "M"]
        if not ms:
            continue
        null_m_present = any(
            text.strip() == "∅"
            for m in ms
            for text in _m_forms(m)
        )
        if null_m_present:
            continue
        w_id = w.get("id") or ""
        parent_s = w.getparent()
        s_id = parent_s.get("id") if parent_s is not None and parent_s.tag == "S" else None
        loc = f"W={w_id}" if w_id else "W"
        if s_id:
            loc = f"S={s_id} {loc}"
        findings.append(Finding(
            rule_id="V069",
            severity=Severity.HARD,
            message=(
                f"W id={w_id!r}: W FORM {w_form!r} contains a null morpheme "
                "'∅' but no child M FORM is '∅'; the null morpheme must "
                "appear on the M tier"
            ),
            path=path,
            location=loc,
        ))
    return findings


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# V070 WARN — gloss-code-like FORM (impostor wordforms / annotation debris)
#
# Hand-edit history motivates this: NTU shipped W FORMs that were actually
# gloss codes ('how', 'teach_PF' impostors), and Kanakanavu carried an
# unsalvageable 'L2M-L2M' marker-residue morpheme. WARN (not SOFT/HARD)
# because a match is suggestive, not conclusive — a real word could in
# principle be spelled like a code (maintainer ruling 2026-08-10:
# "surface as a warning, since it's hard to know for sure").
# ---------------------------------------------------------------------------

# Conservative Leipzig-style vocabulary: only unambiguous all-caps codes.
_GLOSS_CODES = frozenset({
    "AF", "PF", "LF", "IF", "NAF", "AV", "PV", "LV", "CV", "IV", "UV",
    "NOM", "GEN", "OBL", "ACC", "ERG", "ABS", "DAT", "LOC", "TOP", "LNK",
    "LIG", "NEG", "IMP", "PFV", "IPFV", "PROG", "FUT", "PST", "PRS",
    "CAUS", "RECP", "REFL", "RED", "EXCL", "INCL", "EXIST", "COP", "COMP",
    "INTJ", "PRT", "ASP", "MOD", "EVID", "HORT", "FIL", "MID", "DIST",
    "PROX", "PN", "NCM",
})
_PERSON_NUMBER_RE = re.compile(r"^[123](SG|PL|DU)(\.[A-Z]+)*$")
_L2_DEBRIS_RE = re.compile(r"^L2[A-Z]?([-_=]L2[A-Z]?)*$")


def v070_gloss_code_as_FORM(
    tree: etree._ElementTree,
    path: Path,
    index: "CorpusIndex | None",
) -> list[Finding]:
    """V070 WARN: a W- or M-level FORM that is a bare gloss code.

    Fires when the FORM text (any kindOf, stripped of the segmentation
    markers '-' and '=') is exactly a known Leipzig-style code, a
    person-number gloss like 3SG.NOM, or language-switch marker debris
    (L2M-L2M). S-level FORMs are never checked — a code can legitimately
    appear inside running text there only via its W tier anyway.
    """
    findings: list[Finding] = []
    for parent_tag in ("W", "M"):
        for elem in tree.iter(parent_tag):
            for form in elem.findall("FORM"):
                text = (form.text or "").strip()
                core = text.strip("-=")
                if not core:
                    continue
                if (core in _GLOSS_CODES
                        or _PERSON_NUMBER_RE.match(core)
                        or _L2_DEBRIS_RE.match(core)):
                    findings.append(Finding(
                        rule_id="V070",
                        severity=Severity.WARN,
                        message=(
                            f"V070 WARN: {parent_tag} FORM "
                            f"(kindOf={form.get('kindOf')!r}) is the bare "
                            f"gloss code / marker residue {text!r} — likely "
                            f"an impostor wordform or annotation debris"
                        ),
                        path=path,
                        location=f"{parent_tag}={elem.get('id') or ''}",
                    ))
    return findings


RULES: list = [
    v060_W_count_matches_word_count,
    v061_M_count_matches_form_segmentation,
    v062_infix_M_needs_angle_gloss,
    v063_W_FORM_retains_segmentation,
    v064_every_M_has_TRANSL,
    v065_every_W_has_TRANSL,
    v066_clitic_in_W_requires_clitic_in_M,
    v067_no_angle_brackets_in_M_FORM,
    v068_M_reconstructs_W,
    v069_null_morpheme_in_W_requires_null_M,
    v070_gloss_code_as_FORM,
]
CROSS_FILE_RULES: list = []
