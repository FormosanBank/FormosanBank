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


# Maps ISO 639-3 codes to the English language-name stem used in
# Orthographies/<subdir>/<Name>.tsv. ISO Ref_Name doesn't always match
# the filename (e.g. ISO has "Sediq" but the orthography file is
# "Seediq.tsv"; ISO has "Kanakanabu" but the file is "Kanakanavu.tsv"),
# so this mapping is maintained by hand. Limited to the 16 Formosan
# languages the project tracks; non-Formosan xml:lang values fall
# through to legacy V116 behavior (ASCII + CJK exclusion only).
_ISO_TO_ORTHO_NAME: dict[str, str] = {
    "ami": "Amis",
    "tay": "Atayal",
    "bnn": "Bunun",
    "xnb": "Kanakanavu",
    "ckv": "Kavalan",
    "pwn": "Paiwan",
    "pyu": "Puyuma",
    "dru": "Rukai",
    "sxr": "Saaroa",
    "xsy": "Saisiyat",
    "szy": "Sakizaya",
    "trv": "Seediq",
    "ssf": "Thao",
    "tsu": "Tsou",
    "tao": "Yami",
}


_ORTHOGRAPHIES_ROOT = Path(__file__).resolve().parents[3] / "Orthographies"


# Cache: lang ISO code -> frozenset of non-ASCII chars allowed by orthography.
# Populated lazily by _orthography_allowed_chars below. Module-level cache
# is fine because the Orthographies/ directory is not modified during a
# validator run. Tests that monkey-patch should clear this cache.
_ortho_cache: dict[str, frozenset[str]] = {}


def _orthography_allowed_chars(lang: str) -> frozenset[str]:
    """Return the set of non-ASCII characters that appear in the first
    column ('letter') of any Orthographies/**/<Lang>.tsv for the given
    ISO 639-3 code.

    Char-decompose semantics (per design choice on 2026-06-01): multi-
    character letters like 'ng' are decomposed into their component
    characters and each is added to the allow set. This is the simpler
    of the two tokenization approaches; the trade-off is that a digraph's
    components are individually exempted even when they never appear bare
    in the language. The first column also contains ASCII letters which
    are dropped from the set — V116 only cares about non-ASCII.

    Returns an empty frozenset if the ISO code is not in the Formosan
    mapping or if no orthography file is found for it.
    """
    if lang in _ortho_cache:
        return _ortho_cache[lang]
    name = _ISO_TO_ORTHO_NAME.get(lang)
    if name is None or not _ORTHOGRAPHIES_ROOT.is_dir():
        _ortho_cache[lang] = frozenset()
        return _ortho_cache[lang]
    chars: set[str] = set()
    for tsv_path in _ORTHOGRAPHIES_ROOT.glob(f"*/{name}.tsv"):
        try:
            with tsv_path.open(encoding="utf-8") as fh:
                # Skip header row.
                next(fh, None)
                for line in fh:
                    parts = line.split("\t")
                    if not parts:
                        continue
                    cell = parts[0]
                    for ch in cell:
                        if ord(ch) > 127:
                            chars.add(ch)
        except OSError:
            continue
    result = frozenset(chars)
    _ortho_cache[lang] = result
    return result


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


def _s_standard_triples(tree: etree._ElementTree):
    """Yield (s_elem, s_id, standard_text) for each S with a standard FORM.

    Variant of `_s_standard_pairs` that exposes the S element itself so
    per-occurrence Findings can populate `location` (S id) and `line`
    (sourceline). Added 2026-06-01 alongside the SOFT-CSV upgrade.
    """
    for s in tree.iter("S"):
        text = _s_standard_form_text(s)
        if text is None:
            continue
        yield s, s.get("id") or "", text


def _location_for(elem: etree._Element) -> str:
    """Return 'S=<id>' / 'W=<id>' / 'M=<id>' for an element with an id,
    or just the tag if no id. For non-S/W/M elements (like FORM/TRANSL),
    falls back to the parent's location.
    """
    if elem is None:
        return ""
    if elem.tag in ("S", "W", "M") and elem.get("id"):
        return f"{elem.tag}={elem.get('id')}"
    parent = elem.getparent()
    if parent is not None and parent.tag in ("S", "W", "M") and parent.get("id"):
        return f"{parent.tag}={parent.get('id')}"
    return elem.tag


def _sourceline(elem: etree._Element) -> int | None:
    """lxml's 1-indexed source line for elem, or None if unavailable."""
    return getattr(elem, "sourceline", None)


def _soft_finding(
    rule_id: str,
    message: str,
    path: Path,
    elem: etree._Element,
    *,
    language: str | None = None,
    character: str = "",
    count: int = 1,
) -> Finding:
    """Build a per-occurrence SOFT Finding rooted at `elem`.

    Populates `location` (S/W/M id of elem or its parent) and `line`
    (elem.sourceline) so the SOFT CSV's new location/line columns are
    informative. Stderr aggregation happens later in validate_text.py.
    """
    return Finding(
        rule_id=rule_id,
        severity=Severity.SOFT,
        message=message,
        path=path,
        location=_location_for(elem),
        count=count,
        language=language,
        character=character,
        line=_sourceline(elem),
    )


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
    """V110 SOFT: smart quotes in S-level standard FORM.

    Emits one Finding per smart-quote occurrence so the SOFT CSV pins
    each row to the offending S id and source line. Stderr aggregates
    by (rule, character) before printing.
    """
    lang = _resolve_language(tree)
    findings: list[Finding] = []
    for s, _s_id, text in _s_standard_triples(tree):
        for ch in (_LEFT_SQUOTE, _RIGHT_SQUOTE, _LEFT_DQUOTE, _RIGHT_DQUOTE):
            for _ in range(text.count(ch)):
                findings.append(_soft_finding(
                    rule_id="V110",
                    message=f"V110 SOFT smart_quote {ch!r} in S-standard FORM",
                    path=path,
                    elem=s,
                    language=lang,
                    character=ch,
                ))
    return findings


def v111_imbalanced_parens(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V111 SOFT: imbalanced ASCII parentheses in S-level standard FORM.

    One finding per offending S; `count` carries the per-S excess
    (number of unmatched parens) so stderr aggregation can sum across
    sentences."""
    lang = _resolve_language(tree)
    findings: list[Finding] = []
    for s, _s_id, text in _s_standard_triples(tree):
        diff = abs(text.count("(") - text.count(")"))
        if diff:
            findings.append(_soft_finding(
                rule_id="V111",
                message=(
                    f"V111 SOFT imbalanced_parens: {diff} unmatched () "
                    "in S-standard FORM"
                ),
                path=path,
                elem=s,
                language=lang,
                character="()",
                count=diff,
            ))
    return findings


_REPEATED_PUNCT = re.compile(r"([?!])\1+")


def v112_repeated_punct(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V112 SOFT: repeated terminal punctuation (??, !!) in S-standard FORM.

    One finding per match (each run of `??`/`!!`)."""
    lang = _resolve_language(tree)
    findings: list[Finding] = []
    for s, _s_id, text in _s_standard_triples(tree):
        for _ in _REPEATED_PUNCT.findall(text):
            findings.append(_soft_finding(
                rule_id="V112",
                message="V112 SOFT repeated_punct in S-standard FORM",
                path=path,
                elem=s,
                language=lang,
            ))
    return findings


_CONSECUTIVE_DASHES = re.compile(r"--+")


def v113_consecutive_dashes(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V113 SOFT: two or more consecutive dashes in S-standard FORM.

    One finding per run of consecutive dashes."""
    lang = _resolve_language(tree)
    findings: list[Finding] = []
    for s, _s_id, text in _s_standard_triples(tree):
        for _ in _CONSECUTIVE_DASHES.findall(text):
            findings.append(_soft_finding(
                rule_id="V113",
                message="V113 SOFT consecutive_dashes (-- or longer) in S-standard FORM",
                path=path,
                elem=s,
                language=lang,
                character="-",
            ))
    return findings


_MULTI_WS = re.compile(r" {2,}")


def v114_multiple_whitespace(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V114 SOFT: two or more consecutive spaces in S-standard FORM.

    One finding per run of consecutive spaces."""
    lang = _resolve_language(tree)
    findings: list[Finding] = []
    for s, _s_id, text in _s_standard_triples(tree):
        for _ in _MULTI_WS.findall(text):
            findings.append(_soft_finding(
                rule_id="V114",
                message="V114 SOFT multiple_whitespace run in S-standard FORM",
                path=path,
                elem=s,
                language=lang,
                character=" ",
            ))
    return findings


def v115_mismatched_quotes(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V115 SOFT: left/right smart quotes do not balance in S-standard FORM.

    One finding per offending S."""
    lang = _resolve_language(tree)
    findings: list[Finding] = []
    for s, _s_id, text in _s_standard_triples(tree):
        if (text.count(_LEFT_SQUOTE) != text.count(_RIGHT_SQUOTE)) or (
            text.count(_LEFT_DQUOTE) != text.count(_RIGHT_DQUOTE)
        ):
            findings.append(_soft_finding(
                rule_id="V115",
                message=(
                    "V115 SOFT mismatched_quotes: S-standard FORM has "
                    "mismatched smart-quote pairs"
                ),
                path=path,
                elem=s,
                language=lang,
            ))
    return findings


# ---------------------------------------------------------------------------
# W2: ported non_ascii_counts.py rule
# ---------------------------------------------------------------------------

def v116_non_ascii_in_form(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V116 SOFT: count non-ASCII characters in ALL FORM tiers.

    Mirrors non_ascii_counts.py: walks FORM elements across S, W, M
    and counts characters with codepoint > 127, excluding CJK ranges
    AND characters that appear in the first ('letter') column of any
    Orthographies/<subdir>/<Lang>.tsv for the file's TEXT@xml:lang
    (Formosan-language exclusion added 2026-06-01).

    FORM[@kindOf="original"] is skipped (2026-06-11): the original tier
    is source-faithful by policy and legitimately carries annotation
    characters (e.g. NTU Grammar stress accents like á/ʉ́, null-morpheme
    symbols) that are deliberately preserved there and removed from the
    standard tier. Flagging them contradicts that policy; cleanliness is
    only an invariant of the non-original tiers.

    Findings are pre-aggregated per (file, character) to keep the CSV
    compact — one row per unique non-ASCII character per file.
    """
    lang = _resolve_language(tree)
    allowed_ortho_chars = _orthography_allowed_chars(lang)
    findings: list[Finding] = []
    for form in tree.iter("FORM"):
        if form.get("kindOf") == "original":
            continue
        text = form.text or ""
        for ch in text:
            if ord(ch) <= 127:
                continue
            if _is_cjk(ch):
                continue
            if ch in allowed_ortho_chars:
                continue
            findings.append(_soft_finding(
                rule_id="V116",
                message=f"V116 SOFT non_ascii_in_form: {ch!r}",
                path=path,
                elem=form,
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
    free translations: flag-only, no auto-normalize). One finding per
    occurrence so the SOFT CSV pins each row to the offending element.
    """
    lang = _resolve_language(tree)
    findings: list[Finding] = []
    for elem in tree.iter("FORM", "TRANSL"):
        text = elem.text or ""
        for ch in text:
            if ch in "()/":
                findings.append(_soft_finding(
                    rule_id="V122",
                    message=(
                        f"V122 SOFT: {ch!r} (paren or slash) in {elem.tag}"
                    ),
                    path=path,
                    elem=elem,
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

    One finding per offending S so the SOFT CSV pins each row to a
    specific sentence. Original-tier '=' is preserved verbatim and is
    not flagged.
    """
    lang = _resolve_language(tree)
    findings: list[Finding] = []
    for s, _s_id, text in _s_standard_triples(tree):
        if "=" in text:
            findings.append(_soft_finding(
                rule_id="V126",
                message=(
                    "V126 SOFT '=' (clitic marker leftover) in S-standard FORM"
                ),
                path=path,
                elem=s,
                language=lang,
                character="=",
            ))
    return findings


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


# TR11 V129 HARD — '*' in any FORM (original or standard, any level).
#
# Originally scoped to standard-tier only (rationale: original tier could
# preserve source-text metalinguistic ungrammaticality markers). Joshua
# extended the scope on 2026-06-01 — FormosanBank corpora aren't
# faithful verbatim source preservation, so the asterisk should not
# leak into either tier.


def v129_asterisk_in_standard_FORM(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V129 HARD (TR11): '*' in any FORM, either tier (original or standard)."""
    findings: list[Finding] = []
    for form in tree.iter("FORM"):
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
                f"V129 HARD asterisk in FORM (kindOf={form.get('kindOf')!r}): "
                f"'*' in {parent_tag} id={parent_id!r}"
            ),
            path=path,
            location=location,
        ))
    return findings


# TR15 V130 HARD — leading/trailing whitespace in any FORM.
#
# clean_xml.py's `normalize_whitespace` already strips this at the
# cleaner stage; the validator HARD just guarantees the cleaner ran.
# Empty FORMs are not flagged (legitimate elision marker handling).


def v130_leading_trailing_whitespace_in_FORM(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V130 HARD (TR15): FORM text has leading or trailing whitespace."""
    findings: list[Finding] = []
    for form in tree.iter("FORM"):
        text = form.text
        if not text:
            continue
        if text == text.strip():
            continue
        # Carve-out: pretty-printers (notably xml.dom.minidom in
        # standardize.py / add_phonology.py) indent every child element
        # of a mixed-content parent, which puts \n+spaces into
        # `form.text` around any inline child like <UNCLEAR/>. That's a
        # serialization artifact, not a content bug — the cleaner-stage
        # signal V130 exists to catch doesn't apply here. Mirrors the
        # V017/V073 carve-outs for UNCLEAR. Added 2026-06-08.
        if form.find("UNCLEAR") is not None:
            continue
        sides: list[str] = []
        if text != text.lstrip():
            sides.append("leading")
        if text != text.rstrip():
            sides.append("trailing")
        parent = form.getparent()
        parent_tag = parent.tag if parent is not None else ""
        parent_id = (parent.get("id") if parent is not None else None) or ""
        location = f"{parent_tag}={parent_id}" if parent_id else parent_tag
        findings.append(Finding(
            rule_id="V130",
            severity=Severity.HARD,
            message=(
                f"V130 HARD {'/'.join(sides)} whitespace in FORM; "
                f"{parent_tag} id={parent_id!r} "
                f"FORM kindOf={form.get('kindOf')!r}"
            ),
            path=path,
            location=location,
        ))
    return findings


# TR16 V131 HARD — zero-width / BOM in FORM or TRANSL, anywhere.
#
# Per W3 sign-off: U+200B ZWSP, U+200C ZWNJ, U+200D ZWJ, U+FEFF BOM are
# invisible characters with no legitimate use in Formosan / English /
# Chinese content. Subsumes the earlier TR17 "BOM at position 0" idea
# (broader scope; one rule). Cleaner-side strip queued for B5.
_ZERO_WIDTH_CHARS: frozenset[str] = frozenset((
    "​",  # ZERO WIDTH SPACE
    "‌",  # ZERO WIDTH NON-JOINER
    "‍",  # ZERO WIDTH JOINER
    "﻿",  # ZERO WIDTH NO-BREAK SPACE (BOM)
))


def v131_zero_width_or_BOM_in_FORM_TRANSL(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V131 HARD (TR16): zero-width or BOM in FORM or TRANSL."""
    findings: list[Finding] = []
    for elem in tree.iter("FORM", "TRANSL"):
        text = elem.text or ""
        offenders = sorted({ch for ch in text if ch in _ZERO_WIDTH_CHARS})
        if not offenders:
            continue
        parent = elem.getparent()
        parent_tag = parent.tag if parent is not None else ""
        parent_id = (parent.get("id") if parent is not None else None) or ""
        location = f"{parent_tag}={parent_id}" if parent_id else parent_tag
        offenders_str = "+".join(f"U+{ord(ch):04X}" for ch in offenders)
        findings.append(Finding(
            rule_id="V131",
            severity=Severity.HARD,
            message=(
                f"V131 HARD zero-width/BOM char(s) in {elem.tag}: codepoints "
                f"{offenders_str}; {parent_tag} id={parent_id!r} "
                f"{elem.tag} kindOf={elem.get('kindOf')!r}"
            ),
            path=path,
            location=location,
        ))
    return findings


# TR9 V132 SOFT — HTML entity-like substrings in FORM or TRANSL.
#
# XML parsers decode well-formed entities, so `&amp;` in source becomes
# `&` in element.text. Finding a literal `&amp;`, `&apos;`, `&lt;`, or
# `&gt;` in element.text means the source was double-encoded
# (e.g., `&amp;amp;` in the XML). Aggregated per (file, entity) for the
# SOFT CSV.

_HTML_ENTITY_RE = re.compile(r"&(?:amp|apos|lt|gt|quot);")


def v132_html_entities_in_FORM_TRANSL(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V132 SOFT (TR9): HTML entity-like substrings in FORM or TRANSL.

    One finding per match so the SOFT CSV pins each row to the
    offending element.
    """
    lang = _resolve_language(tree)
    findings: list[Finding] = []
    for elem in tree.iter("FORM", "TRANSL"):
        text = elem.text or ""
        for match in _HTML_ENTITY_RE.findall(text):
            findings.append(_soft_finding(
                rule_id="V132",
                message=(
                    f"V132 SOFT html entity-like residue {match!r} "
                    f"in {elem.tag} (likely double-encoded source)"
                ),
                path=path,
                elem=elem,
                language=lang,
                character=match,
            ))
    return findings


# TR12 V133 SOFT — '-' (segmentation marker) in S-level standard FORM.


def v133_dash_in_S_standard_FORM(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V133 SOFT (TR12): '-' in S-level standard FORM, likely a leftover
    segmentation/hyphenation marker that should have been removed.

    One finding per offending S."""
    lang = _resolve_language(tree)
    findings: list[Finding] = []
    for s, _s_id, text in _s_standard_triples(tree):
        if "-" in text:
            findings.append(_soft_finding(
                rule_id="V133",
                message=(
                    "V133 SOFT '-' (segmentation leftover) in S-standard FORM"
                ),
                path=path,
                elem=s,
                language=lang,
                character="-",
            ))
    return findings


# TR13 V134 SOFT — '<' or '>' (infix delimiter) in S-level FORM, either tier.
#
# Scope: S-level (direct-child FORM of S). Lower-tier FORMs (W, M) may
# legitimately use angle-bracket annotation for infixes (e.g., m<um>law)
# and are out of scope for V134.


def v134_angle_brackets_in_S_FORM(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V134 SOFT (TR13): '<' or '>' in S-level FORM at either tier.

    One finding per occurrence; location is the S id of the parent."""
    lang = _resolve_language(tree)
    findings: list[Finding] = []
    for s in tree.iter("S"):
        for child in s:
            if child.tag != "FORM":
                continue
            text = child.text or ""
            for ch in text:
                if ch in "<>":
                    findings.append(_soft_finding(
                        rule_id="V134",
                        message=(
                            f"V134 SOFT angle bracket / infix delimiter "
                            f"{ch!r} in S-level FORM"
                        ),
                        path=path,
                        elem=child,
                        language=lang,
                        character=ch,
                    ))
    return findings


# TR14 V135 SOFT — trailing-punctuation mismatch between original and
# standard tiers (per-S).
#
# We compare the trailing run of recognized punctuation (after stripping
# trailing whitespace) between the S-level original and standard FORMs.
# Recognized punctuation set is intentionally conservative: ASCII
# `.,!?;:` plus full-width Chinese counterparts. A mismatch on the
# trailing run is flagged per S (aggregated to one finding per file).
_TRAILING_PUNCT_CHARS: frozenset[str] = frozenset(".,!?;:" + "。，！？；：")


def _trailing_punct(text: str) -> str:
    """Return the run of recognized trailing-punct chars at the end of text,
    ignoring trailing whitespace. Returns '' if none."""
    stripped = text.rstrip()
    end = len(stripped)
    i = end
    while i > 0 and stripped[i - 1] in _TRAILING_PUNCT_CHARS:
        i -= 1
    return stripped[i:end]


def v135_trailing_punct_mismatch(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V135 SOFT (TR14): trailing-punct mismatch in S-level FORM pair.

    One finding per offending S."""
    lang = _resolve_language(tree)
    findings: list[Finding] = []
    for s in tree.iter("S"):
        orig = _s_original_form_text(s)
        std = _s_standard_form_text(s)
        if orig is None or std is None:
            # Need both tiers to compare.
            continue
        if _trailing_punct(orig) != _trailing_punct(std):
            findings.append(_soft_finding(
                rule_id="V135",
                message=(
                    "V135 SOFT trailing-punct mismatch: original and "
                    "standard S FORM tiers end in different punctuation"
                ),
                path=path,
                elem=s,
                language=lang,
            ))
    return findings


# TR18 V136 SOFT — mixed-script confusables.
#
# Pragmatic heuristic, not a full Unicode script-property analysis: flag
# a FORM that contains characters from two or more of
# {Latin, Cyrillic, Greek} simultaneously. Other scripts (CJK / Hiragana
# / Katakana / Hangul / Arabic / Hebrew) are NOT considered for the
# mixed-script test because the corpus legitimately mixes Latin with CJK
# annotation and with other scripts in TRANSL; the confusable concern is
# specifically about Latin homograph attacks (Cyrillic 'а' vs Latin 'a',
# Greek omicron vs Latin 'o', etc.). Aggregated per file.
#
# Scope: FORM only. TRANSL is intentionally excluded — TRANSL into
# Chinese, Japanese, etc. legitimately mixes scripts.

_LATIN_BLOCKS = (
    (0x0041, 0x005A),  # Basic Latin upper
    (0x0061, 0x007A),  # Basic Latin lower
    (0x00C0, 0x00FF),  # Latin-1 Supplement letters
    (0x0100, 0x017F),  # Latin Extended-A
    (0x0180, 0x024F),  # Latin Extended-B
)
_CYRILLIC_BLOCKS = (
    (0x0400, 0x04FF),
    (0x0500, 0x052F),
)
_GREEK_BLOCKS = (
    (0x0370, 0x03FF),
)


def _in_ranges(code: int, ranges) -> bool:
    return any(lo <= code <= hi for lo, hi in ranges)


def _script_for(ch: str) -> str | None:
    """Return 'latin' / 'cyrillic' / 'greek' or None for chars not in
    the confusable-script set."""
    code = ord(ch)
    if _in_ranges(code, _LATIN_BLOCKS):
        return "latin"
    if _in_ranges(code, _CYRILLIC_BLOCKS):
        return "cyrillic"
    if _in_ranges(code, _GREEK_BLOCKS):
        return "greek"
    return None


def v136_mixed_script_confusables(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V136 SOFT (TR18): mixed Latin/Cyrillic/Greek scripts in FORM text.

    One finding per offending FORM."""
    lang = _resolve_language(tree)
    findings: list[Finding] = []
    for form in tree.iter("FORM"):
        text = form.text or ""
        scripts = {s for s in (_script_for(ch) for ch in text) if s is not None}
        if len(scripts) >= 2:
            findings.append(_soft_finding(
                rule_id="V136",
                message=(
                    "V136 SOFT mixed-script / confusable: FORM mixes "
                    "two or more of {Latin, Cyrillic, Greek}"
                ),
                path=path,
                elem=form,
                language=lang,
            ))
    return findings


# V137 SOFT — footnote-like markers anywhere in any FORM or TRANSL.
#
# Two patterns, both treated as likely footnote leaks from scraped source:
#   - `.<digits>` not preceded by another digit (e.g. 'world.1', not '3.14')
#   - `<letter><digits>` (e.g. 'nganai12', 'B12')
#
# Scope was originally narrow (end-of-string, S-level only, per-file
# aggregated). Broadened on 2026-06-01 to scan every FORM (S/W/M, both
# tiers) and every TRANSL, anywhere in the text, with one Finding per
# occurrence so the stderr summary lists each call-site.

_FOOTNOTE_RE = re.compile(r"(?<!\d)\.\d+|[A-Za-z]\d+")


def v137_trailing_decimal_footnote_in_S_FORM_TRANSL(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V137 SOFT: footnote-like substrings (`.<digits>` not preceded by a
    digit, or `<letter><digits>`) anywhere in any FORM (S/W/M, either
    kindOf) or any TRANSL element.

    Emits one Finding per matched occurrence so per-FORM locations are
    visible in the stderr summary (the SOFT CSV remains aggregated).

    False-positive guard: plain decimal numerals like '3.14' are not
    flagged (digit before '.' blocks the first pattern, and there is no
    letter immediately before the digit run).
    """
    lang = _resolve_language(tree)
    findings: list[Finding] = []
    for elem in tree.iter("FORM", "TRANSL"):
        text = elem.text or ""
        for match in _FOOTNOTE_RE.finditer(text):
            parent_tag = elem.tag
            host = elem.getparent()
            host_tag = host.tag if host is not None else ""
            host_id = (host.get("id") if host is not None else None) or ""
            location = (
                f"{host_tag}={host_id} {parent_tag}"
                if host_id else f"{host_tag} {parent_tag}".strip()
            )
            findings.append(Finding(
                rule_id="V137",
                severity=Severity.SOFT,
                message=(
                    f"V137 SOFT footnote-like substring {match.group(0)!r} "
                    f"in {parent_tag} (kindOf={elem.get('kindOf')!r}); "
                    f"{host_tag} id={host_id!r}"
                ),
                path=path,
                location=location,
                count=1,
                language=lang,
                character="",
            ))
    return findings


# TR20 V138 SOFT — superscript-digit footnote in FORM or TRANSL.
#
# Superscript digits in element text are almost always footnote leaks
# from scrape. Recognized codepoints:
#   U+00B9 ¹ SUPERSCRIPT ONE
#   U+00B2 ² SUPERSCRIPT TWO
#   U+00B3 ³ SUPERSCRIPT THREE
#   U+2070 ⁰ SUPERSCRIPT ZERO
#   U+2074-U+2079 ⁴-⁹ SUPERSCRIPT FOUR through NINE
# Aggregated per (file, character).

_SUPERSCRIPT_DIGITS: frozenset[str] = frozenset(
    "¹²³⁰" + "".join(chr(c) for c in range(0x2074, 0x207A))
)


def v138_superscript_digit_footnote(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V138 SOFT (TR20): superscript digit (¹²³…) in FORM or TRANSL.

    One finding per occurrence."""
    lang = _resolve_language(tree)
    findings: list[Finding] = []
    for elem in tree.iter("FORM", "TRANSL"):
        text = elem.text or ""
        for ch in text:
            if ch in _SUPERSCRIPT_DIGITS:
                findings.append(_soft_finding(
                    rule_id="V138",
                    message=(
                        f"V138 SOFT superscript-digit footnote {ch!r} "
                        f"in {elem.tag} (likely footnote leak)"
                    ),
                    path=path,
                    elem=elem,
                    language=lang,
                    character=ch,
                ))
    return findings


# V140 HARD — null in S-original FORM must propagate DOWN to at least
# one W (and that same W must have at least one M FORM with the null).
# Converse of V125 (which propagates UP from W to S-original); closes
# the round-trip so a `∅` cannot live only at the surface tier.


def v140_null_in_S_original_requires_child_W_and_M(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V140 HARD: if an S-level FORM[@kindOf='original'] contains '∅',
    then S must have at least one child W with '∅' in some FORM, AND
    that same W must have at least one child M with '∅' in some FORM.

    Symmetric with V125 (which fires when a W carries '∅' but the
    upward propagation is missing). V140 catches the opposite failure
    mode: '∅' marked at the sentence surface but never grounded in the
    morpheme tier.

    No-ops on S elements with no W children (unsegmented S). The lack
    of a tokenization tier is V060's domain, not V140's.
    """
    findings: list[Finding] = []
    for s in tree.iter("S"):
        orig_text = _s_original_form_text(s)
        if orig_text is None or NULL_SYMBOL not in orig_text:
            continue
        ws = [child for child in s if child.tag == "W"]
        if not ws:
            continue
        satisfied = False
        for w in ws:
            if not _form_contains_null(w):
                continue
            if any(child.tag == "M" and _form_contains_null(child) for child in w):
                satisfied = True
                break
        if satisfied:
            continue
        s_id = s.get("id") or ""
        findings.append(Finding(
            rule_id="V140",
            severity=Severity.HARD,
            message=(
                f"V140 HARD: S-original FORM has null '{NULL_SYMBOL}' but no W "
                "child has both a null FORM and a child M with a null FORM "
                "(S-original null propagation); "
                f"S id={s_id!r}"
            ),
            path=path,
            location=f"S={s_id}" if s_id else "S",
        ))
    return findings


# TR21 V139 SOFT — bracketed-digit footnote (`word[1]`, `[1]`) anywhere
# in FORM or TRANSL. Pattern is conservative: ASCII square brackets
# wrapping digit(s).

_BRACKETED_DIGIT_RE = re.compile(r"\[\d+\]")


def v139_bracketed_digit_footnote(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V139 SOFT (TR21): bracketed-digit footnote in FORM or TRANSL.

    One finding per match."""
    lang = _resolve_language(tree)
    findings: list[Finding] = []
    for elem in tree.iter("FORM", "TRANSL"):
        text = elem.text or ""
        for match in _BRACKETED_DIGIT_RE.findall(text):
            findings.append(_soft_finding(
                rule_id="V139",
                message=(
                    f"V139 SOFT bracketed-digit footnote {match!r} "
                    f"in {elem.tag} (likely footnote / citation leak)"
                ),
                path=path,
                elem=elem,
                language=lang,
                character=match,
            ))
    return findings


def v141_W_reconstructs_S(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V141 SOFT: the W FORMs of an S should spell the S FORM.

    Sentence-level sibling of the gloss rule V068 (M->W). Compares the
    letter-skeleton (Unicode-letter multiset, casefolded) of S
    FORM[@kindOf='original'] against the summed skeletons of its direct W
    children's FORM[@kindOf='original']. SOFT finding when ``similarity``
    falls below ``DEFAULT_SIMILARITY_THRESHOLD`` — i.e., the word tier is
    likely misaligned with the sentence (e.g., the W decomposition belongs
    to a different sentence). Content check, not the word-count check V060.

    Original tier only. No-ops on unsegmented corpora (S with no direct W)
    and skips S/W elements missing an original FORM (other rules own those).
    """
    findings: list[Finding] = []
    for s in tree.iter("S"):
        ws = [child for child in s if child.tag == "W"]
        if not ws:
            continue  # unsegmented; nothing to reconstruct
        s_form = s.find('./FORM[@kindOf="original"]')
        if s_form is None:
            continue
        s_skel = letter_skeleton(s_form.text)
        if not s_skel:
            continue
        w_skel: Counter = Counter()
        saw_w_form = False
        for w in ws:
            w_form = w.find('./FORM[@kindOf="original"]')
            if w_form is not None and (w_form.text or "").strip():
                saw_w_form = True
                w_skel += letter_skeleton(w_form.text)
        if not saw_w_form:
            continue  # W FORMs missing -> structural rules own this
        sim = similarity(s_skel, w_skel)
        if sim >= DEFAULT_SIMILARITY_THRESHOLD:
            continue
        s_id = s.get("id")
        findings.append(Finding(
            rule_id="V141",
            severity=Severity.SOFT,
            message=(
                f"S id={s_id!r}: child W FORMs reconstruct only {sim:.0%} of the "
                f"S FORM letters; the word tier may be misaligned with the "
                f"sentence. S FORM={s_form.text!r}"
            ),
            path=path,
            location=f"S={s_id}" if s_id else "S",
            count=1,
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
    v130_leading_trailing_whitespace_in_FORM,
    v131_zero_width_or_BOM_in_FORM_TRANSL,
    v132_html_entities_in_FORM_TRANSL,
    v133_dash_in_S_standard_FORM,
    v134_angle_brackets_in_S_FORM,
    v135_trailing_punct_mismatch,
    v136_mixed_script_confusables,
    v137_trailing_decimal_footnote_in_S_FORM_TRANSL,
    v138_superscript_digit_footnote,
    v139_bracketed_digit_footnote,
    # V140: converse of V125 (null in S-original requires W and M)
    v140_null_in_S_original_requires_child_W_and_M,
    # V141: W FORMs reconstruct the S FORM (sibling of gloss V068)
    v141_W_reconstructs_S,
]
CROSS_FILE_RULES: list = []
