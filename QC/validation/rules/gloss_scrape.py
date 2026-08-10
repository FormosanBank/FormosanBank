"""Gloss-scrape audit rules (G namespace).

Rule module for `audit_gloss_scrape.py`. Same signature contract as
`rules/gloss.py`:

    rule(tree: etree._ElementTree, path: Path, index: CorpusIndex | None) -> list[Finding]

These rules audit a *freshly scraped* gloss paper, before the QC pipeline
runs. They are deliberately NOT registered in `validate_glosses.py` or CI:
some encode assumptions specific to scrape output, and several are
informational. Severity here ranks triage priority for a human reader; the
audit entry point exits 0 regardless.

Rules:
- G001 HARD: marker skeleton of W FORM must match that of W TRANSL.
- G002 SOFT: M-count vs. gloss-unit count implied by the W TRANSL.
- G003 SOFT: internal '-' in an M FORM (segmentation leaked into the morpheme).
- G004 HARD: infix root reconstruction — '<X>' in a W FORM implies a root M.
- G005 WARN: gloss-label inventory; singletons near a frequent label.
- G006 HARD: non-canonical null symbol (ø/Ø/0/NULL instead of ∅).
- G010 WARN: mixed marker retention in S FORM[@kindOf='original'].
- G011 SOFT: unsplit '/' alternate (slash in both S FORM and the W tier).
- G012 SOFT: trailing parenthetical left in TRANSL text, not the notes attribute.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from lxml import etree

from QC.validation._finding import Finding, Severity

# Segmentation / notation markers, per the FormosanBank gloss conventions.
MARKERS = "-<>=~"
_ANGLE = re.compile(r"<[^>]*>")
_INFIX_FORM = re.compile(r"^-[^-]+-$")
_SPLIT_UNITS = re.compile(r"[-=~]")
# A dash with a non-dash character on BOTH sides, i.e. an internal boundary
# rather than an affix-attachment dash ('pa-', '-en') or an infix ('-em-').
_INTERNAL_DASH = re.compile(r"(?<=[^-])-(?=[^-])")

CANONICAL_NULL = "∅"  # ∅ EMPTY SET
# Spellings of "null morpheme" seen in real scrapes. U+00F8 (ø) is the
# common one and is invisible to every existing ∅ rule (V120, V123-V125,
# V140), which match U+2205 only.
NULL_VARIANTS = ("ø", "Ø", "⌀", "NULL")

# Gloss labels are conventionally uppercase (Leipzig style). Allow digits and
# dots ('3SG', 'make.clothes' is lexical and won't match because of the
# lowercase letters).
_LABEL_RE = re.compile(r"^[A-Z][A-Z0-9.]*$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def marker_skeleton(text: str | None) -> str:
    """Return only the notation characters of ``text``, in order.

    'Pa~pa<mi>kat-en' -> '~<>-'
    'CAU~<IMP>walk-UV' -> '~<>-'

    The scraping guide's own sanity check: the text tier and the gloss tier
    describe the same morphological object, so their notation must agree.
    """
    if not text:
        return ""
    return "".join(ch for ch in text if ch in MARKERS)


def _form_text(elem: etree._Element, kind: str = "original") -> str:
    """Return the element's preferred direct-child FORM text.

    Preference: FORM[@kindOf=kind] > any FORM > ''. Only direct children,
    so a W's lookup never picks up an M's FORM.
    """
    preferred = elem.find(f'./FORM[@kindOf="{kind}"]')
    if preferred is not None and preferred.text:
        return preferred.text.strip()
    any_form = elem.find("./FORM")
    if any_form is not None and any_form.text:
        return any_form.text.strip()
    return ""


def _transl_text(elem: etree._Element) -> str:
    """Return the element's original-tier TRANSL text, or '' if ambiguous.

    Preference: TRANSL[@kindOf='original'] > the sole TRANSL. When there are
    several TRANSLs and none is marked original we return '' rather than
    guess — comparing against an 'alt' gloss would produce noise.
    """
    original = elem.find('./TRANSL[@kindOf="original"]')
    if original is not None and original.text:
        return original.text.strip()
    transls = [c for c in elem if c.tag == "TRANSL"]
    if len(transls) == 1 and transls[0].text:
        return transls[0].text.strip()
    return ""


def _gloss_units(text: str) -> int:
    """Number of morpheme slots a gloss string implies.

    Each '<...>' is one infix unit; the remainder splits on '-', '=', '~'.
    'CAU~<IMP>walk-UV' -> 1 infix + {CAU, walk, UV} = 4.
    """
    if not text:
        return 0
    infixes = _ANGLE.findall(text)
    remainder = _ANGLE.sub("", text)
    segments = [s for s in _SPLIT_UNITS.split(remainder) if s.strip()]
    return len(infixes) + len(segments)


def _loc(w: etree._Element) -> str:
    """Location string 'S=<sid> W=<wid>' matching the V-rule convention."""
    w_id = w.get("id") or ""
    parent = w.getparent()
    s_id = parent.get("id") if parent is not None and parent.tag == "S" else None
    base = f"W={w_id}" if w_id else "W"
    return f"S={s_id} {base}" if s_id else base


def _m_loc(m: etree._Element) -> str:
    m_id = m.get("id") or ""
    parent = m.getparent()
    w_id = parent.get("id") if parent is not None and parent.tag == "W" else None
    base = f"M={m_id}" if m_id else "M"
    return f"W={w_id} {base}" if w_id else base


def _edit_distance_le_1(a: str, b: str) -> bool:
    """True when ``a`` and ``b`` differ by at most one edit.

    Small hand-rolled check (labels are short) so this module stays free of
    the optional rapidfuzz dependency, which only the source-alignment half
    of the audit requires.
    """
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        return sum(x != y for x, y in zip(a, b)) == 1
    shorter, longer = (a, b) if la < lb else (b, a)
    i = j = 0
    skipped = False
    while i < len(shorter) and j < len(longer):
        if shorter[i] == longer[j]:
            i += 1
            j += 1
        elif skipped:
            return False
        else:
            skipped = True
            j += 1
    return True


# ---------------------------------------------------------------------------
# G001 / G007: marker-skeleton parity between W FORM and W TRANSL
# ---------------------------------------------------------------------------

def g001_marker_skeleton_parity(
    tree: etree._ElementTree,
    path: Path,
    index=None,
) -> list[Finding]:
    """G001 HARD: the notation of a W FORM must match that of its W TRANSL.

    Structural mismatch only: '~' is normalised to '-' before comparison, so
    a mere reduplication-vs-hyphen slip falls to G007 instead. A difference
    that survives that normalisation means the two tiers disagree about how
    many morphemes there are, or where the infix sits — a genuine alignment
    failure that invalidates the M tier beneath it.
    """
    findings: list[Finding] = []
    for w in tree.iter("W"):
        form = _form_text(w)
        transl = _transl_text(w)
        if not form or not transl:
            continue  # V011/V065 own missing FORM/TRANSL
        fs = marker_skeleton(form)
        ts = marker_skeleton(transl)
        if fs.replace("~", "-") == ts.replace("~", "-"):
            continue
        findings.append(Finding(
            rule_id="G001",
            severity=Severity.HARD,
            message=(
                f"W FORM {form!r} has notation {fs!r} but its TRANSL "
                f"{transl!r} has notation {ts!r}; the text and gloss tiers "
                "disagree about the morpheme segmentation"
            ),
            path=path,
            location=_loc(w),
        ))
    return findings


def g007_marker_type_mismatch(
    tree: etree._ElementTree,
    path: Path,
    index=None,
) -> list[Finding]:
    """G007 SOFT: FORM and TRANSL agree on segmentation but not marker type.

    Typically '-' written where '~' (reduplication) belongs, e.g. FORM
    'Pa~pakat' glossed 'CAU-walk'. The morpheme count is right, so the M
    tier is salvageable; only the notation is wrong.
    """
    findings: list[Finding] = []
    for w in tree.iter("W"):
        form = _form_text(w)
        transl = _transl_text(w)
        if not form or not transl:
            continue
        fs = marker_skeleton(form)
        ts = marker_skeleton(transl)
        if fs == ts:
            continue
        if fs.replace("~", "-") != ts.replace("~", "-"):
            continue  # G001 owns structural mismatches
        findings.append(Finding(
            rule_id="G007",
            severity=Severity.SOFT,
            message=(
                f"W FORM {form!r} uses notation {fs!r} but its TRANSL "
                f"{transl!r} uses {ts!r}; same segmentation, different "
                "marker type (likely '-' where '~' belongs, or vice versa)"
            ),
            path=path,
            location=_loc(w),
            count=1,
        ))
    return findings


# ---------------------------------------------------------------------------
# G002: M-count vs. gloss-unit count
# ---------------------------------------------------------------------------

def g002_M_count_matches_gloss_units(
    tree: etree._ElementTree,
    path: Path,
    index=None,
) -> list[Finding]:
    """G002 SOFT: the number of M children should match the number of gloss
    units in the W TRANSL.

    V061 compares the M-count to the *FORM* segmentation. Nothing compares it
    to the *gloss* segmentation, so a word whose FORM and M tier agree with
    each other but disagree with the gloss passes every existing rule.

    A monomorphemic W with no M children is acceptable.
    """
    findings: list[Finding] = []
    for w in tree.iter("W"):
        transl = _transl_text(w)
        if not transl:
            continue
        expected = _gloss_units(transl)
        actual = sum(1 for child in w if child.tag == "M")
        if expected == 1 and actual == 0:
            continue
        if expected == actual:
            continue
        findings.append(Finding(
            rule_id="G002",
            severity=Severity.SOFT,
            message=(
                f"W has {actual} M children but its TRANSL {transl!r} "
                f"implies {expected} gloss unit(s)"
            ),
            path=path,
            location=_loc(w),
            count=1,
        ))
    return findings


# ---------------------------------------------------------------------------
# G003: internal dash residue in an M FORM
# ---------------------------------------------------------------------------

def g003_internal_dash_in_M_FORM(
    tree: etree._ElementTree,
    path: Path,
    index=None,
) -> list[Finding]:
    """G003 SOFT: an M FORM with an internal '-' has un-split segmentation.

    An M is a single morpheme, so a dash with letters on both sides means a
    word (or two morphemes) was placed in one M — e.g. 'k-uda', 'm-angay',
    'chita-en', all real examples from published corpora.

    Exempt: the canonical infix notation '-X-' (V067's convention), and
    leading- or trailing-only dashes marking affix attachment ('pa-', '-en'),
    which are harmless. '=' is not flagged at all: V066 *requires* the clitic
    boundary to propagate to the M tier.
    """
    findings: list[Finding] = []
    for m in tree.iter("M"):
        form = _form_text(m)
        if not form or _INFIX_FORM.match(form):
            continue
        if not _INTERNAL_DASH.search(form):
            continue
        findings.append(Finding(
            rule_id="G003",
            severity=Severity.SOFT,
            message=(
                f"M FORM {form!r} contains an internal '-'; a morpheme should "
                "not carry a segmentation boundary (infix '-X-' excepted)"
            ),
            path=path,
            location=_m_loc(m),
            count=1,
        ))
    return findings


# ---------------------------------------------------------------------------
# G004: infix root reconstruction
# ---------------------------------------------------------------------------

def g004_infix_root_reconstructed(
    tree: etree._ElementTree,
    path: Path,
    index=None,
) -> list[Finding]:
    """G004 HARD: a W FORM containing '<X>' must have an M for the rejoined root.

    Per the scraping guide, 'pa<mi>kat' is two morphemes: the infix 'mi' and
    the root 'pakat' — the root's halves are rejoined across the infix. If no
    M carries the rejoined root, the infix was mis-segmented (usually the
    halves were left as two separate morphemes).

    V068 checks this only fuzzily, as a letter multiset; because an infix
    reconstructs perfectly under a multiset comparison, V068 cannot see this
    failure at all. Comparison here is casefolded, since the guide forbids
    lowercasing the text tier but the root may be capitalised in only one place.

    A root may carry several infixes ('t<em>a<ka>kesi', Puyuma): the expected
    M is the root rejoined across ALL of them ('takesi'), so the surrounding
    context of each infix is cleared of the other infixes before rejoining,
    and one missing root is reported once, not once per infix.
    """
    findings: list[Finding] = []
    for w in tree.iter("W"):
        form = _form_text(w)
        if not form or "<" not in form:
            continue
        ms = [child for child in w if child.tag == "M"]
        if not ms:
            continue  # G002/V061 own the missing M tier
        m_forms = {
            (_form_text(m) or "").strip("-").casefold()
            for m in ms
        }
        reported: set[str] = set()
        for match in _ANGLE.finditer(form):
            left = _SPLIT_UNITS.split(_ANGLE.sub("", form[:match.start()]))[-1]
            right = _SPLIT_UNITS.split(_ANGLE.sub("", form[match.end():]))[0]
            root = (left + right).strip()
            if not root or root.casefold() in m_forms or root in reported:
                continue
            reported.add(root)
            findings.append(Finding(
                rule_id="G004",
                severity=Severity.HARD,
                message=(
                    f"W FORM {form!r} has infix {match.group(0)!r}, so the root "
                    f"rejoins as {root!r}, but no child M FORM spells it "
                    f"(found: {sorted(f for f in m_forms if f)})"
                ),
                path=path,
                location=_loc(w),
            ))
    return findings


# ---------------------------------------------------------------------------
# G005: gloss-label inventory
# ---------------------------------------------------------------------------

def g005_gloss_label_inventory(
    tree: etree._ElementTree,
    path: Path,
    index=None,
) -> list[Finding]:
    """G005 WARN: rare gloss labels one edit away from a frequent one.

    Scrape typos in grammatical labels ('NCM' for 'NOM', 'PV' for 'UV') are
    invisible to structural rules — the XML is well-formed and the counts all
    agree. They surface statistically: a label used once or twice that is one
    edit from a label used dozens of times is almost always a typo.

    Reported for human eyes, never as a verdict; a genuine rare category will
    also appear here and should be kept.
    """
    labels: Counter[str] = Counter()
    example_loc: dict[str, str] = {}
    for m in tree.iter("M"):
        transl = _transl_text(m)
        if not transl:
            continue
        for unit in _SPLIT_UNITS.split(_ANGLE.sub("", transl)):
            unit = unit.strip()
            if unit and _LABEL_RE.match(unit):
                labels[unit] += 1
                example_loc.setdefault(unit, _m_loc(m))

    findings: list[Finding] = []
    if not labels:
        return findings
    for label, freq in sorted(labels.items()):
        if freq > 2:
            continue
        near = [
            (other, other_freq)
            for other, other_freq in labels.items()
            if other != label
            and other_freq >= max(5, freq * 5)
            and _edit_distance_le_1(label, other)
        ]
        if not near:
            continue
        near.sort(key=lambda t: -t[1])
        other, other_freq = near[0]
        findings.append(Finding(
            rule_id="G005",
            severity=Severity.WARN,
            message=(
                f"gloss label {label!r} used {freq}x is one edit from "
                f"{other!r} used {other_freq}x; possible scrape typo"
            ),
            path=path,
            location=example_loc.get(label, ""),
            character=label,
            count=freq,
        ))
    return findings


# ---------------------------------------------------------------------------
# G006: non-canonical null symbol
# ---------------------------------------------------------------------------

def g006_non_canonical_null_symbol(
    tree: etree._ElementTree,
    path: Path,
    index=None,
) -> list[Finding]:
    """G006 HARD: null morphemes must be written '∅' (U+2205).

    Scrapes commonly use 'ø' (U+00F8 LATIN SMALL LETTER O WITH STROKE), which
    is a *letter*, not the empty-set sign. Every existing null rule — V120,
    V123, V124, V125, V140 — matches U+2205 only, so an entire rule family
    silently passes on such a corpus while the null propagation is unchecked.

    Fires on an M FORM that is exactly a null variant, and on any FORM where a
    variant sits next to a segmentation marker ('ø-ci'). Both patterns are
    unambiguous; a bare 'ø' inside a word is left alone, since no check should
    assume a character is not part of some language's orthography.
    """
    findings: list[Finding] = []
    for elem in tree.iter("M", "W", "S"):
        for form in elem.findall("./FORM"):
            text = (form.text or "").strip()
            if not text:
                continue
            for variant in NULL_VARIANTS:
                if variant not in text:
                    continue
                standalone = elem.tag == "M" and text == variant
                adjacent = re.search(
                    f"(?:{re.escape(variant)}[{re.escape(MARKERS)}]"
                    f"|[{re.escape(MARKERS)}]{re.escape(variant)})",
                    text,
                )
                if not standalone and not adjacent:
                    continue
                loc = _m_loc(elem) if elem.tag == "M" else (
                    _loc(elem) if elem.tag == "W" else f"S={elem.get('id') or ''}"
                )
                findings.append(Finding(
                    rule_id="G006",
                    severity=Severity.HARD,
                    message=(
                        f"{elem.tag} FORM {text!r} writes the null morpheme as "
                        f"{variant!r} (U+{ord(variant[0]):04X}) instead of the "
                        f"canonical '{CANONICAL_NULL}' (U+2205); the V120/V123-V125/"
                        "V140 null-propagation rules cannot see this spelling"
                    ),
                    path=path,
                    location=loc,
                    character=variant,
                ))
                break
    return findings


# ---------------------------------------------------------------------------
# G010: mixed marker retention across S FORM[@kindOf='original']
# ---------------------------------------------------------------------------

def g010_mixed_marker_retention(
    tree: etree._ElementTree,
    path: Path,
    index=None,
) -> list[Finding]:
    """G010 WARN: S-original tiers inconsistently retain segmentation markers.

    Both styles are legal (maintainer decision, 2026-08-03): the S-original
    may keep '-'/'=' from the source, or present the unsegmented sentence.
    Presence is therefore never flagged. A corpus that does *both* is the
    signature of a half-applied transformation, and that is what fires here.

    Only sentences whose W tier actually carries markers are counted — a
    sentence with no affixes anywhere is not evidence of stripping, and
    counting it would make every corpus look mixed.
    """
    retained = 0
    stripped = 0
    example: dict[str, str] = {}
    for s in tree.iter("S"):
        w_has_marker = any(
            any(ch in MARKERS for ch in _form_text(w))
            for w in s.iter("W")
        )
        if not w_has_marker:
            continue
        s_text = _form_text(s)
        if not s_text:
            continue
        if any(ch in MARKERS for ch in s_text):
            retained += 1
            example.setdefault("retained", f"S={s.get('id')}: {s_text!r}")
        else:
            stripped += 1
            example.setdefault("stripped", f"S={s.get('id')}: {s_text!r}")

    total = retained + stripped
    if total < 4:
        return []  # too few to call a mix
    minority = min(retained, stripped)
    if minority == 0:
        return []  # consistent either way; both styles are legal
    return [Finding(
        rule_id="G010",
        severity=Severity.WARN,
        message=(
            f"S FORM[@kindOf='original'] inconsistently retains segmentation "
            f"markers: {retained}/{total} retain, {stripped}/{total} stripped. "
            f"Both styles are legal but mixing them suggests a half-applied "
            f"transformation. Retained e.g. {example.get('retained', 'n/a')}; "
            f"stripped e.g. {example.get('stripped', 'n/a')}"
        ),
        path=path,
        location="",
        count=minority,
    )]


# ---------------------------------------------------------------------------
# G011: unsplit '/' alternate
# ---------------------------------------------------------------------------

def g011_unsplit_slash_alternate(
    tree: etree._ElementTree,
    path: Path,
    index=None,
) -> list[Finding]:
    """G011 SOFT: '/' in an S-original whose W tier also carries '/'.

    The guide requires a slash alternate to become two separate <S> elements.
    A slash present at both tiers means the split never happened. Sharper than
    V122, which flags every slash anywhere, including legitimate ones in free
    translations.
    """
    findings: list[Finding] = []
    for s in tree.iter("S"):
        s_text = _form_text(s)
        if "/" not in s_text:
            continue
        slashed_w = [w for w in s.iter("W") if "/" in _form_text(w)]
        if not slashed_w:
            continue
        findings.append(Finding(
            rule_id="G011",
            severity=Severity.SOFT,
            message=(
                f"S FORM {s_text!r} and {len(slashed_w)} of its W FORM(s) "
                "contain '/'; an alternate should have been split into two "
                "separate <S> elements"
            ),
            path=path,
            location=f"S={s.get('id') or ''}",
            count=1,
        ))
    return findings


# ---------------------------------------------------------------------------
# G012: trailing parenthetical left in TRANSL text
# ---------------------------------------------------------------------------

_TRAILING_PAREN = re.compile(r"\(([^()]{2,})\)\s*$")


def g012_trailing_paren_note_in_TRANSL(
    tree: etree._ElementTree,
    path: Path,
    index=None,
) -> list[Finding]:
    """G012 SOFT: a trailing '(...)' in a TRANSL belongs in the notes attribute.

    Covers both commentary ('(The causee is a little child.)') and source
    attributions ('(Wu 1995, p. 34)'), which are metadata about the example,
    not part of the translation. Only fires when the element has no `notes`
    attribute, so an already-extracted note is not re-flagged.
    """
    findings: list[Finding] = []
    for s in tree.iter("S"):
        for transl in s.findall("./TRANSL"):
            text = (transl.text or "").strip()
            if not text or transl.get("notes"):
                continue
            match = _TRAILING_PAREN.search(text)
            if not match:
                continue
            findings.append(Finding(
                rule_id="G012",
                severity=Severity.SOFT,
                message=(
                    f"TRANSL {text!r} ends with parenthetical "
                    f"{match.group(1)!r} and has no notes attribute; "
                    "commentary and source attributions belong in notes"
                ),
                path=path,
                location=f"S={s.get('id') or ''}",
                count=1,
            ))
    return findings


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

RULES: list = [
    g001_marker_skeleton_parity,
    g002_M_count_matches_gloss_units,
    g003_internal_dash_in_M_FORM,
    g004_infix_root_reconstructed,
    g005_gloss_label_inventory,
    g006_non_canonical_null_symbol,
    g007_marker_type_mismatch,
    g010_mixed_marker_retention,
    g011_unsplit_slash_alternate,
    g012_trailing_paren_note_in_TRANSL,
]
CROSS_FILE_RULES: list = []
