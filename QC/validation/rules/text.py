"""Text-content rules for validate_text.py (B9.4).

These rules check the *textual content* of FORM and TRANSL elements —
punctuation conventions, character set, leftover segmentation markers,
null-symbol propagation between tiers. They operate on well-formed XML
(post-validate_xml.py) and complement the structural rules in
rules/hard.py / rules/soft.py.

Each rule is a function with signature:
    rule(tree: etree._ElementTree, path: Path, index: CorpusIndex | None)
    -> list[Finding]

The validate_text.py orchestrator calls them in pass 1 against each
parsed tree.

SOFT findings are pre-aggregated per (rule_id, file, language,
character) to keep CSV row counts manageable.

Rule ID assignments (B9.4):
  W1: V110 smart_quotes, V111 imbalanced_parens, V112 repeated_punct,
      V113 consecutive_dashes, V114 multiple_whitespace,
      V115 mismatched_quotes
  W2: V116 non_ascii_in_form
  W4: V120 TR1 null in S-standard FORM (HARD)
  W5: V121 TR2 parens/'/' in W/M FORM (HARD)
      V122 TR3 parens/'/' anywhere in FORM/TRANSL (SOFT)
  W6: V123 TR4 null in W/M std FORM ⇒ also in sister original (HARD)
  W7: V124 TR5 null in M FORM ⇒ also in parent W AND S-original (HARD)
  W8: V125 TR6 null in W FORM ⇒ also in some child M AND S-original (HARD)
  W9: V126 TR7 '=' in S-standard FORM (SOFT)
  W10: V127 TR8 smart quotes in either FORM tier (HARD)
       V128 TR10 control chars (<0x20 except \\t \\n \\r) in FORM/TRANSL (HARD)
       V129 TR11 '*' in standard-tier FORM (HARD)
       V130 TR15 leading/trailing whitespace in FORM (HARD)
       V131 TR16 zero-width / BOM chars in FORM/TRANSL (HARD)
       V132 TR9 HTML entities in FORM/TRANSL (SOFT)
       V133 TR12 '-' in S-standard FORM (SOFT)
       V134 TR13 '<'/'>' in S-level FORM either tier (SOFT)
       V135 TR14 trailing-punct mismatch original vs standard (SOFT)
       V136 TR18 mixed-script confusables (SOFT)
       V137 TR19 trailing-decimal footnote in FORM/TRANSL (SOFT)
       V138 TR20 superscript-digit footnote in FORM/TRANSL (SOFT)
       V139 TR21 bracketed-digit footnote in FORM/TRANSL (SOFT)
"""
import re
from pathlib import Path

from lxml import etree

from QC.validation._corpus_index import CorpusIndex
from QC.validation._finding import Finding, Severity


_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

# Null symbol used in W/M-tier FORM to mark elided morphemes/words.
# Per the B9.4 plan (and Joshua's open question resolved on 2026-05-31),
# the canonical null symbol is U+2205 EMPTY SET ('∅').
NULL_SYMBOL = "∅"

# CJK ranges: characters in these blocks are NOT counted as non-ASCII for
# the V116 rule (preserves non_ascii_counts.py behavior).
_CJK_RANGES: tuple[tuple[int, int], ...] = (
    (0x4E00, 0x9FFF),   # CJK Unified Ideographs
    (0x3400, 0x4DBF),   # CJK Unified Ideographs Extension A
    (0x20000, 0x2A6DF), # Extension B
    (0x2A700, 0x2B73F), # Extension C
    (0x2B740, 0x2B81F), # Extension D
    (0x2B820, 0x2CEAF), # Extension E
    (0x2CEB0, 0x2EBEF), # Extension F
    (0x30000, 0x3134F), # Extension G
)


def _is_cjk(char: str) -> bool:
    code = ord(char)
    return any(lo <= code <= hi for lo, hi in _CJK_RANGES)


def _resolve_language(tree: etree._ElementTree) -> str:
    """Read xml:lang from the TEXT root, or empty string if absent."""
    root = tree.getroot()
    if root.tag == "TEXT":
        return root.get(_XML_LANG) or ""
    return ""


def _s_standard_form_text(s: etree._Element) -> str | None:
    """Return text of the S element's direct-child kindOf='standard' FORM, or None."""
    for child in s:
        if child.tag == "FORM" and child.get("kindOf") == "standard":
            return child.text or ""
    return None


def _s_original_form_text(s: etree._Element) -> str | None:
    """Return text of the S element's direct-child kindOf='original' FORM, or None."""
    for child in s:
        if child.tag == "FORM" and child.get("kindOf") == "original":
            return child.text or ""
    return None


def _direct_form_by_kind(elem: etree._Element, kind: str) -> str | None:
    """Return the text of a direct-child FORM with the given kindOf, or None."""
    for child in elem:
        if child.tag == "FORM" and child.get("kindOf") == kind:
            return child.text or ""
    return None


def _s_standard_pairs(tree: etree._ElementTree):
    """Yield (s_id, standard_text) for each S whose standard FORM exists."""
    for s in tree.iter("S"):
        text = _s_standard_form_text(s)
        if text is None:
            continue
        yield s.get("id") or "", text


# ---------------------------------------------------------------------------
# W1: ported validate_punct.py rules
# ---------------------------------------------------------------------------

_LEFT_SQUOTE = "‘"
_RIGHT_SQUOTE = "’"
_LEFT_DQUOTE = "“"
_RIGHT_DQUOTE = "”"


def v110_smart_quotes(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V110 SOFT: count smart quotes in S-level standard FORM.

    Smart quote conventions vary widely in the source corpora; the
    standardized tier is expected to use the project's canonical
    apostrophe/quotation conventions. This rule counts the occurrences
    of left/right single/double smart quotes so that a per-corpus
    review of the SOFT CSV can spot anomalies.
    """
    lang = _resolve_language(tree)
    counts: dict[str, int] = {}
    for _, text in _s_standard_pairs(tree):
        for ch in (_LEFT_SQUOTE, _RIGHT_SQUOTE, _LEFT_DQUOTE, _RIGHT_DQUOTE):
            n = text.count(ch)
            if n:
                counts[ch] = counts.get(ch, 0) + n
    findings: list[Finding] = []
    for ch, n in counts.items():
        findings.append(Finding(
            rule_id="V110",
            severity=Severity.SOFT,
            message=f"V110 SOFT smart_quotes: count={n} {ch!r} in S-standard FORM",
            path=path,
            count=n,
            language=lang,
            character=ch,
        ))
    return findings


def v111_imbalanced_parens(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V111 SOFT: imbalanced ASCII parentheses in S-level standard FORM."""
    lang = _resolve_language(tree)
    total = 0
    for _, text in _s_standard_pairs(tree):
        diff = abs(text.count("(") - text.count(")"))
        total += diff
    if total == 0:
        return []
    return [Finding(
        rule_id="V111",
        severity=Severity.SOFT,
        message=f"V111 SOFT imbalanced_parens: count={total} unmatched () in S-standard FORM",
        path=path,
        count=total,
        language=lang,
        character="()",
    )]


_REPEATED_PUNCT = re.compile(r"([?!])\1+")


def v112_repeated_punct(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V112 SOFT: repeated terminal punctuation (??, !!) in S-standard FORM."""
    lang = _resolve_language(tree)
    total = 0
    for _, text in _s_standard_pairs(tree):
        total += len(_REPEATED_PUNCT.findall(text))
    if total == 0:
        return []
    return [Finding(
        rule_id="V112",
        severity=Severity.SOFT,
        message=f"V112 SOFT repeated_punct: count={total} repeated punct in S-standard FORM",
        path=path,
        count=total,
        language=lang,
        character="",
    )]


_CONSECUTIVE_DASHES = re.compile(r"--+")


def v113_consecutive_dashes(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V113 SOFT: two or more consecutive dashes in S-standard FORM."""
    lang = _resolve_language(tree)
    total = 0
    for _, text in _s_standard_pairs(tree):
        total += len(_CONSECUTIVE_DASHES.findall(text))
    if total == 0:
        return []
    return [Finding(
        rule_id="V113",
        severity=Severity.SOFT,
        message=f"V113 SOFT consecutive_dashes: count={total} runs of -- in S-standard FORM",
        path=path,
        count=total,
        language=lang,
        character="-",
    )]


_MULTI_WS = re.compile(r" {2,}")


def v114_multiple_whitespace(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V114 SOFT: two or more consecutive spaces in S-standard FORM."""
    lang = _resolve_language(tree)
    total = 0
    for _, text in _s_standard_pairs(tree):
        total += len(_MULTI_WS.findall(text))
    if total == 0:
        return []
    return [Finding(
        rule_id="V114",
        severity=Severity.SOFT,
        message=f"V114 SOFT multiple_whitespace: count={total} runs of multi-space in S-standard FORM",
        path=path,
        count=total,
        language=lang,
        character=" ",
    )]


def v115_mismatched_quotes(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V115 SOFT: left/right smart quotes do not balance in S-standard FORM."""
    lang = _resolve_language(tree)
    bad_s_count = 0
    for _, text in _s_standard_pairs(tree):
        if (text.count(_LEFT_SQUOTE) != text.count(_RIGHT_SQUOTE)) or (
            text.count(_LEFT_DQUOTE) != text.count(_RIGHT_DQUOTE)
        ):
            bad_s_count += 1
    if bad_s_count == 0:
        return []
    return [Finding(
        rule_id="V115",
        severity=Severity.SOFT,
        message=(
            f"V115 SOFT mismatched_quotes: count={bad_s_count} S-standard FORM(s) "
            "with mismatched smart-quote pairs"
        ),
        path=path,
        count=bad_s_count,
        language=lang,
        character="",
    )]


# ---------------------------------------------------------------------------
# W2: ported non_ascii_counts.py rule
# ---------------------------------------------------------------------------

def v116_non_ascii_in_form(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V116 SOFT: count non-ASCII characters in ALL FORM tiers.

    Mirrors non_ascii_counts.py: walks every FORM element across S, W, M
    and counts characters with codepoint > 127, excluding CJK ranges.
    Findings are pre-aggregated per (file, character) to keep the CSV
    compact — one row per unique non-ASCII character per file.
    """
    lang = _resolve_language(tree)
    per_char: dict[str, int] = {}
    for form in tree.iter("FORM"):
        text = form.text or ""
        for ch in text:
            if ord(ch) <= 127:
                continue
            if _is_cjk(ch):
                continue
            per_char[ch] = per_char.get(ch, 0) + 1
    findings: list[Finding] = []
    for ch, n in per_char.items():
        findings.append(Finding(
            rule_id="V116",
            severity=Severity.SOFT,
            message=f"V116 SOFT non_ascii_in_form: count={n} {ch!r}",
            path=path,
            count=n,
            language=lang,
            character=ch,
        ))
    return findings


# ---------------------------------------------------------------------------
# W4: TR1 — null symbol in S-level standard FORM (HARD)
# ---------------------------------------------------------------------------

def v120_null_in_S_standard(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V120 HARD (TR1): null symbol '∅' in S-level standard FORM is forbidden.

    The S-standard tier is the project's canonical sentence-level surface
    text. A null symbol there indicates an unresolved elision marker
    that should have been resolved during cleaning.
    """
    findings: list[Finding] = []
    for s in tree.iter("S"):
        text = _s_standard_form_text(s)
        if text is None or NULL_SYMBOL not in text:
            continue
        s_id = s.get("id") or ""
        findings.append(Finding(
            rule_id="V120",
            severity=Severity.HARD,
            message=(
                f"V120 HARD: null symbol '{NULL_SYMBOL}' in S-level standard FORM "
                f"(null in s-level standard); S id={s_id!r}"
            ),
            path=path,
            location=f"S={s_id}" if s_id else "S",
        ))
    return findings


# ---------------------------------------------------------------------------
# W5: TR2 + TR3 — parens/slashes in W/M FORM (HARD) and anywhere SOFT
# ---------------------------------------------------------------------------

_PAREN_OR_SLASH_RE = re.compile(r"[()/]")


def v121_parens_slashes_in_W_or_M_FORM(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V121 HARD (TR2): parens or '/' in W- or M-level FORM is forbidden.

    W/M FORM elements are token / morpheme surface forms. Parens and
    slashes there indicate stray metalinguistic annotation that escaped
    cleaning.
    """
    findings: list[Finding] = []
    for parent in tree.iter("W", "M"):
        for child in parent:
            if child.tag != "FORM":
                continue
            text = child.text or ""
            if _PAREN_OR_SLASH_RE.search(text):
                p_id = parent.get("id") or ""
                findings.append(Finding(
                    rule_id="V121",
                    severity=Severity.HARD,
                    message=(
                        f"V121 HARD: parens or slash in W/M FORM "
                        f"(paren in w/m or slash in w/m); {parent.tag} id={p_id!r} "
                        f"FORM kindOf={child.get('kindOf')!r}"
                    ),
                    path=path,
                    location=f"{parent.tag}={p_id}" if p_id else parent.tag,
                ))
    return findings


def v122_parens_slashes_anywhere(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V122 SOFT (TR3): parens or '/' anywhere in FORM or TRANSL.

    Closes roadmap C023 ('/' = alternative forms) and C024 (parens in
    free translations: flag-only, no auto-normalize). Aggregated per
    (file, character) to keep the CSV compact.
    """
    lang = _resolve_language(tree)
    per_char: dict[str, int] = {}
    for elem in tree.iter("FORM", "TRANSL"):
        text = elem.text or ""
        for ch in text:
            if ch in "()/":
                per_char[ch] = per_char.get(ch, 0) + 1
    findings: list[Finding] = []
    for ch, n in per_char.items():
        findings.append(Finding(
            rule_id="V122",
            severity=Severity.SOFT,
            message=(
                f"V122 SOFT: parens or slash in FORM/TRANSL "
                f"(paren or slash); count={n} {ch!r}"
            ),
            path=path,
            count=n,
            language=lang,
            character=ch,
        ))
    return findings


# ---------------------------------------------------------------------------
# W6: TR4 — null in W/M std FORM ⇒ also in sister original FORM (HARD)
# ---------------------------------------------------------------------------

def v123_null_in_WM_std_requires_sister_original_null(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V123 HARD (TR4): if a W- or M-level standard FORM contains the null
    symbol, the W's or M's direct-child kindOf='original' FORM must also
    contain it.

    Rationale: the standardized morpheme/word tier is a transliteration
    of the original. A null in the standardized form without a null in
    the sister original means the elision was introduced during
    standardization rather than preserved from the source. Either both
    tiers should carry the null, or neither.
    """
    findings: list[Finding] = []
    for parent in tree.iter("W", "M"):
        std = _direct_form_by_kind(parent, "standard")
        if std is None or NULL_SYMBOL not in std:
            continue
        orig = _direct_form_by_kind(parent, "original")
        if orig is not None and NULL_SYMBOL in orig:
            continue
        p_id = parent.get("id") or ""
        findings.append(Finding(
            rule_id="V123",
            severity=Severity.HARD,
            message=(
                f"V123 HARD: null in {parent.tag}-level standard FORM but not "
                f"in sister original (null propagation TR4); {parent.tag} id={p_id!r}"
            ),
            path=path,
            location=f"{parent.tag}={p_id}" if p_id else parent.tag,
        ))
    return findings


# ---------------------------------------------------------------------------
# W7: TR5 — null in M FORM ⇒ also in parent W FORM AND S-original (HARD)
# ---------------------------------------------------------------------------

def _form_contains_null(elem: etree._Element) -> bool:
    """Return True if elem has any direct-child FORM whose text contains '∅'."""
    for child in elem:
        if child.tag == "FORM" and child.text and NULL_SYMBOL in child.text:
            return True
    return False


def v124_null_in_M_requires_parent_W_and_S_original(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V124 HARD (TR5): if an M FORM contains '∅', the parent W must also
    have a FORM containing '∅', AND the S-level original-tier FORM must
    also contain '∅'.

    This enforces that a morpheme-level null propagates UP to the W
    surface form and to the S-level original surface form. A null at M
    that isn't in the containing W or S indicates inconsistent
    annotation.
    """
    findings: list[Finding] = []
    for m in tree.iter("M"):
        if not _form_contains_null(m):
            continue
        # Find parent W
        parent_w = m.getparent()
        if parent_w is None or parent_w.tag != "W":
            # Schema enforces M under W; if not, V005 / schema reports.
            continue
        parent_w_has_null = _form_contains_null(parent_w)
        # Find ancestor S
        ancestor_s = parent_w.getparent()
        s_orig_has_null = False
        if ancestor_s is not None and ancestor_s.tag == "S":
            orig_text = _s_original_form_text(ancestor_s) or ""
            s_orig_has_null = NULL_SYMBOL in orig_text
        if parent_w_has_null and s_orig_has_null:
            continue
        m_id = m.get("id") or ""
        missing: list[str] = []
        if not parent_w_has_null:
            missing.append("parent W FORM")
        if not s_orig_has_null:
            missing.append("S-level original FORM")
        findings.append(Finding(
            rule_id="V124",
            severity=Severity.HARD,
            message=(
                f"V124 HARD: null in M-level FORM but not in {', '.join(missing)} "
                f"(M null propagation TR5); M id={m_id!r}"
            ),
            path=path,
            location=f"M={m_id}" if m_id else "M",
        ))
    return findings


# ---------------------------------------------------------------------------
# W8: TR6 — null in W FORM ⇒ also in some child M FORM AND S-original (HARD)
# ---------------------------------------------------------------------------

def v125_null_in_W_requires_child_M_and_S_original(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V125 HARD (TR6): if a W FORM contains '∅', AT LEAST ONE child M
    FORM must also contain '∅', AND the S-level original-tier FORM must
    contain '∅'.

    This enforces propagation DOWN to morpheme tier and UP to the S
    original surface form.

    Edge case: a W with no M children at all (monomorphemic) and a null
    W FORM cannot satisfy the "some child M has null" requirement — the
    rule still fires. That is intentional: a null W form without any
    morpheme structure to explain the elision is anomalous. Adjust the
    rule (or add a separate exemption) if real corpora demonstrate that
    pattern is legitimate.
    """
    findings: list[Finding] = []
    for w in tree.iter("W"):
        if not _form_contains_null(w):
            continue
        child_m_has_null = any(
            child.tag == "M" and _form_contains_null(child)
            for child in w
        )
        ancestor_s = w.getparent()
        s_orig_has_null = False
        if ancestor_s is not None and ancestor_s.tag == "S":
            orig_text = _s_original_form_text(ancestor_s) or ""
            s_orig_has_null = NULL_SYMBOL in orig_text
        if child_m_has_null and s_orig_has_null:
            continue
        w_id = w.get("id") or ""
        missing: list[str] = []
        if not child_m_has_null:
            missing.append("child M FORM")
        if not s_orig_has_null:
            missing.append("S-level original FORM")
        findings.append(Finding(
            rule_id="V125",
            severity=Severity.HARD,
            message=(
                f"V125 HARD: null in W-level FORM but not in {', '.join(missing)} "
                f"(W null propagation TR6); W id={w_id!r}"
            ),
            path=path,
            location=f"W={w_id}" if w_id else "W",
        ))
    return findings


# ---------------------------------------------------------------------------
# W9: TR7 — '=' in S-level standard FORM (SOFT)
# ---------------------------------------------------------------------------

def v126_equal_sign_in_S_standard(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V126 SOFT (TR7): '=' in S-level standard FORM, likely a leftover
    clitic boundary marker that should have been resolved.

    Aggregated per file (count of S elements whose standard FORM
    contains at least one '='). Original-tier '=' is preserved verbatim
    and is not flagged.
    """
    lang = _resolve_language(tree)
    count = 0
    for _, text in _s_standard_pairs(tree):
        if "=" in text:
            count += 1
    if count == 0:
        return []
    return [Finding(
        rule_id="V126",
        severity=Severity.SOFT,
        message=(
            f"V126 SOFT equal sign: count={count} S-standard FORM(s) containing "
            "'=' (clitic marker leftover)"
        ),
        path=path,
        count=count,
        language=lang,
        character="=",
    )]


# ---------------------------------------------------------------------------
# W10: brainstorm-derived rules (V127-V139)
# ---------------------------------------------------------------------------


# TR8 V127 HARD — smart quotes in either FORM tier.
#
# Per W3 sign-off (2026-06-01): ASCII straight `'` U+0027 and `"` U+0022 are
# the only acceptable apostrophe/quote characters in either FORM tier. Curly
# smart quotes (U+2018/U+2019/U+201C/U+201D) and Chinese full-width quote
# brackets (「 」 『 』 《 》) HARD-fail in either FORM tier. Scope is FORM
# only; TRANSL is intentionally excluded.
_SMART_QUOTE_CHARS: tuple[str, ...] = (
    "‘",  # ‘ LEFT SINGLE QUOTATION MARK
    "’",  # ’ RIGHT SINGLE QUOTATION MARK
    "“",  # “ LEFT DOUBLE QUOTATION MARK
    "”",  # ” RIGHT DOUBLE QUOTATION MARK
    "「",  # 「 LEFT CORNER BRACKET
    "」",  # 」 RIGHT CORNER BRACKET
    "『",  # 『 LEFT WHITE CORNER BRACKET
    "』",  # 』 RIGHT WHITE CORNER BRACKET
    "《",  # 《 LEFT DOUBLE ANGLE BRACKET
    "》",  # 》 RIGHT DOUBLE ANGLE BRACKET
)
_SMART_QUOTE_SET = frozenset(_SMART_QUOTE_CHARS)


def v127_smart_quotes_in_FORM_hard(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V127 HARD (TR8): smart-quote characters in any FORM (either tier).

    Only ASCII straight `'` (U+0027) and `"` (U+0022) are acceptable in
    a FORM element. Curly smart quotes U+2018/U+2019/U+201C/U+201D and
    Chinese full-width corner/angle brackets are HARD failures because
    the project's standard convention forbids them outright. One finding
    per offending FORM (severity HARD requires per-element location).
    """
    findings: list[Finding] = []
    for form in tree.iter("FORM"):
        text = form.text or ""
        offenders = sorted({ch for ch in text if ch in _SMART_QUOTE_SET})
        if not offenders:
            continue
        # Locate parent and id for diagnostics.
        parent = form.getparent()
        parent_tag = parent.tag if parent is not None else ""
        parent_id = (parent.get("id") if parent is not None else None) or ""
        location = f"{parent_tag}={parent_id}" if parent_id else parent_tag
        offenders_str = "".join(offenders)
        findings.append(Finding(
            rule_id="V127",
            severity=Severity.HARD,
            message=(
                f"V127 HARD smart quote(s) in FORM: non-ASCII quote "
                f"chars={offenders_str!r}; "
                f"{parent_tag} id={parent_id!r} FORM kindOf={form.get('kindOf')!r}"
            ),
            path=path,
            location=location,
        ))
    return findings


# TR10 V128 HARD — control characters (codepoint < 0x20) other than
# \t (0x09), \n (0x0A), \r (0x0D) — anywhere in FORM or TRANSL.
#
# Defensive in practice: lxml/libxml2 refuses to load most C0 controls
# from disk and lxml's API setter raises on them, so the rule normally
# cannot fire end-to-end. It is implemented because the plan calls for
# it (W3 sign-off) and to catch the case where a tree was constructed
# in a way that bypasses lxml's checks (or a future relaxation in
# libxml2). The companion `_disallowed_control_chars` helper is unit-
# testable directly.
_ALLOWED_CONTROL_CHARS: frozenset[str] = frozenset("\t\n\r")


def _disallowed_control_chars(text: str) -> frozenset[str]:
    """Return the set of C0 control chars in `text` other than \\t \\n \\r."""
    return frozenset(
        ch for ch in text
        if ord(ch) < 0x20 and ch not in _ALLOWED_CONTROL_CHARS
    )


def v128_control_chars_in_FORM_TRANSL(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V128 HARD (TR10): C0 control chars (<0x20 except \\t \\n \\r) in
    FORM or TRANSL elements.
    """
    findings: list[Finding] = []
    for elem in tree.iter("FORM", "TRANSL"):
        text = elem.text or ""
        offenders = _disallowed_control_chars(text)
        if not offenders:
            continue
        parent = elem.getparent()
        parent_tag = parent.tag if parent is not None else ""
        parent_id = (parent.get("id") if parent is not None else None) or ""
        location = f"{parent_tag}={parent_id}" if parent_id else parent_tag
        offenders_str = "+".join(f"U+{ord(ch):04X}" for ch in sorted(offenders))
        findings.append(Finding(
            rule_id="V128",
            severity=Severity.HARD,
            message=(
                f"V128 HARD control character(s) in {elem.tag}: codepoints "
                f"{offenders_str}; {parent_tag} id={parent_id!r} "
                f"{elem.tag} kindOf={elem.get('kindOf')!r}"
            ),
            path=path,
            location=location,
        ))
    return findings


# TR11 V129 HARD — '*' in standard-tier FORM (any level).
#
# The asterisk is a metalinguistic ungrammaticality marker. It can be
# meaningful in raw source / original transcripts but should never
# appear in the project's standardized surface form. Scope: any FORM
# (S, W, or M) with kindOf='standard'.


def v129_asterisk_in_standard_FORM(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V129 HARD (TR11): '*' in any standard-tier FORM."""
    findings: list[Finding] = []
    for form in tree.iter("FORM"):
        if form.get("kindOf") != "standard":
            continue
        text = form.text or ""
        if "*" not in text:
            continue
        parent = form.getparent()
        parent_tag = parent.tag if parent is not None else ""
        parent_id = (parent.get("id") if parent is not None else None) or ""
        location = f"{parent_tag}={parent_id}" if parent_id else parent_tag
        findings.append(Finding(
            rule_id="V129",
            severity=Severity.HARD,
            message=(
                f"V129 HARD asterisk in standard-tier FORM: '*' in "
                f"{parent_tag} id={parent_id!r}"
            ),
            path=path,
            location=location,
        ))
    return findings


RULES: list = [
    # W1 (V110-V115): ported from validate_punct.py
    v110_smart_quotes,
    v111_imbalanced_parens,
    v112_repeated_punct,
    v113_consecutive_dashes,
    v114_multiple_whitespace,
    v115_mismatched_quotes,
    # W2 (V116): ported from non_ascii_counts.py
    v116_non_ascii_in_form,
    # W4-W9 (V120-V126): TR1-TR7 user-specified rules
    v120_null_in_S_standard,
    v121_parens_slashes_in_W_or_M_FORM,
    v122_parens_slashes_anywhere,
    v123_null_in_WM_std_requires_sister_original_null,
    v124_null_in_M_requires_parent_W_and_S_original,
    v125_null_in_W_requires_child_M_and_S_original,
    v126_equal_sign_in_S_standard,
    # W10 (V127-V139): brainstorm-derived rules
    v127_smart_quotes_in_FORM_hard,
    v128_control_chars_in_FORM_TRANSL,
    v129_asterisk_in_standard_FORM,
]
CROSS_FILE_RULES: list = []
