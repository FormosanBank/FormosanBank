"""SOFT-severity rules: violations populate the SOFT CSV but do not
affect exit code.

Each rule pre-aggregates per (rule_id, file, language, character).
Returning thousands of un-aggregated Findings per file would flood
the CSV writer.

Signature: same as HARD rules.
"""
from pathlib import Path

from lxml import etree

from QC.validation._corpus_index import CorpusIndex
from QC.validation._finding import Finding, Severity


_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def v010_count_s_without_form(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V010 SOFT: count S elements that have no FORM children.

    Per design, this is informational rather than fatal: the S has no
    sentence-level text but the file is still well-formed (e.g., a
    diarized-audio S that has not yet been transcribed). Aggregated per
    (rule, file, language) — one Finding per file with the total count.

    Does NOT consult index; runs in pass 1.
    """
    count = sum(
        1 for s in tree.iter("S")
        if not any(child.tag == "FORM" for child in s)
    )
    if count == 0:
        return []
    # Resolve language: from index if available, else from tree root.
    if index is not None and path in index.langs:
        lang = index.langs[path]
    else:
        lang = tree.getroot().get(_XML_LANG) or ""
    return [Finding(
        rule_id="V010",
        severity=Severity.SOFT,
        message=f"V010 SOFT: count={count} S elements missing FORM",
        path=path,
        count=count,
        language=lang,
        character="",
    )]


def v014_count_missing_standard_form(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V014 SOFT: count S/W/M elements that have FORM children but none
    with kindOf='standard'.

    Per design, missing a standard-tier FORM is informational rather
    than fatal. Some corpora legitimately lack a standard tier because
    the orthography is unsettled. Aggregated per (rule, file, language)
    — one Finding per file with the total count.

    Does NOT consult index; runs in pass 1.
    """
    count = 0
    for elem in tree.iter("S", "W", "M"):
        forms = [child for child in elem if child.tag == "FORM"]
        if not forms:
            # No FORMs at all — V010 (SOFT) handles this case for S;
            # V011/V012 (HARD) handle it for W/M.
            continue
        has_standard = any(f.get("kindOf") == "standard" for f in forms)
        if not has_standard:
            count += 1
    if count == 0:
        return []
    # Resolve language: from index if available, else from tree root.
    if index is not None and path in index.langs:
        lang = index.langs[path]
    else:
        lang = tree.getroot().get(_XML_LANG) or ""
    return [Finding(
        rule_id="V014",
        severity=Severity.SOFT,
        message=f"V014 SOFT: count={count} S/W/M elements missing standard FORM (missing-standard tier)",
        path=path,
        count=count,
        language=lang,
        character="",
    )]


def _children(elem: etree._Element, tag: str) -> list:
    """Direct children of `elem` with the given tag."""
    return [child for child in elem if child.tag == tag]


def _sentence_words(tree: etree._ElementTree) -> list:
    """Per sentence, its direct-child W elements (sentences with W only)."""
    return [ws for ws in (_children(s, "W") for s in tree.iter("S")) if ws]


def _first_form_text(elem: etree._Element) -> str:
    """Text of the element's first FORM child, whitespace-stripped."""
    for child in elem:
        if child.tag == "FORM":
            return (child.text or "").strip()
    return ""


def _carries_parsing(ws: list) -> bool:
    """Does this sentence carry *some* morphological analysis?

    Two clauses, either one sufficient — the same criterion applied by
    YeddaPalemeqBlog's CodeAndDocs/fix_m_tier.py, kept identical so a
    corpus fixed by that script validates clean:

    1. some W has two or more M children; or
    2. some M's FORM differs from its parent W's FORM (an infix split
       such as ``l<em>angeda`` -> ``l-angeda`` / ``-em-`` carries an
       analysis even at one M per W).

    Anything else is an all-single-M mirror tier: no analysis at all.
    """
    for w in ws:
        ms = _children(w, "M")
        if len(ms) >= 2:
            return True
        w_form = _first_form_text(w)
        if any(_first_form_text(m) != w_form for m in ms):
            return True
    return False


def _tree_language(tree: etree._ElementTree, path: Path,
                   index: CorpusIndex | None) -> str:
    if index is not None and path in index.langs:
        return index.langs[path]
    return tree.getroot().get(_XML_LANG) or ""


def v144_M_less_W_in_parsed_sentence(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V144 SOFT (POL-023): a morphologically parsed sentence with M-less Ws.

    Ruling 2026-08-12 (re-scoped from per file to **per sentence**): the
    unit of morphological analysis is the sentence, not the file. In a
    sentence that carries *some* parsing every W needs at least one M (a
    single M there reads "analyzed as monomorphemic"); a sentence the
    author simply never analyzed carries no M tier at all, and demanding
    M there would fake an analysis. The old file-scoped reading punished
    exactly that honest mixed state — one parsed sentence made every
    unparsed sentence in the file a finding.

    Aggregated per file (one Finding, counting the M-less Ws inside
    parsed sentences). SOFT because existing corpora trip this and need
    fixing over time.
    """
    parsed = [ws for ws in _sentence_words(tree) if _carries_parsing(ws)]
    if not parsed:
        return []
    missing = 0
    sentences = 0
    for ws in parsed:
        m_less = sum(1 for w in ws if not _children(w, "M"))
        if m_less:
            missing += m_less
            sentences += 1
    if missing == 0:
        return []
    return [Finding(
        rule_id="V144",
        severity=Severity.SOFT,
        message=(
            f"V144 SOFT: {missing} W elements in {sentences} of "
            f"{len(parsed)} morphologically parsed sentences have no M "
            f"child (POL-023: within a parsed sentence every W gets at "
            f"least one M; an unparsed sentence carries no M tier)"
        ),
        path=path,
        count=missing,
        language=_tree_language(tree, path, index),
        character="",
    )]


def v145_degenerate_all_single_M_tier(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V145 SOFT (POL-023): M level present but the file carries no parsing.

    Ruling 2026-08-10: corpora without morpheme segmentation should have
    no M level at all — an M tier where every M-bearing W has exactly
    one M identical in role to its W adds no information (historically:
    ~100 spurious M shells shipped in YeddaPalemeqBlog).

    Deliberately kept **file-scoped** when V144 went per-sentence
    (2026-08-12). "Every M mirrors its W" is only evidence of a fake
    tier in bulk: a single sentence whose handful of words really are
    monomorphemic is indistinguishable from a mirror tier, and POL-023
    explicitly blesses single-M Ws as "analyzed as monomorphemic". A
    whole file with no multi-morphemic word anywhere is the reliable
    signal; one sentence is not. Same severity as before.
    """
    sentences = _sentence_words(tree)
    if not sentences or any(_carries_parsing(ws) for ws in sentences):
        return []
    singles = sum(1 for ws in sentences for w in ws if _children(w, "M"))
    if singles == 0:
        return []
    return [Finding(
        rule_id="V145",
        severity=Severity.SOFT,
        message=(
            f"V145 SOFT: M level present but no sentence in the file "
            f"carries any morphological parsing ({singles} mirror single-M "
            f"Ws) — unsegmented corpora should have no M level (POL-023)"
        ),
        path=path,
        count=singles,
        language=_tree_language(tree, path, index),
        character="",
    )]


def v148_W_less_S_in_segmented_file(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V148 SOFT (POL-041): a partially word-segmented file.

    The W tier asks the same question as the M tier (POL-023) one level
    up, and gets the same answer at file scope: a corpus with no word
    segmentation has **no W level at all**, and that is the normal state
    for most of the bank — never a finding. But a file where *some*
    sentences carry a W tier and others do not is an incomplete
    segmentation pass, and the unsegmented sentences are worth
    surfacing.

    Deliberately **file-scoped**, unlike V144. V144 can be per sentence
    because a parsed sentence announces itself (a W with 2+ M, or an M
    FORM differing from its W FORM). A sentence with no W announces
    nothing at all — there is no per-sentence signal distinguishing
    "not segmented yet" from "not segmented, by design". Only the
    presence of segmented siblings in the same file makes the omission
    legible, so the file is the unit.

    An S with no FORM is never counted: an untranscribed-audio shell has
    no text to segment (V010 already reports it). Aggregated per file.
    """
    with_form = [s for s in tree.iter("S") if s.find("./FORM") is not None]
    if not with_form:
        return []
    w_less = [s for s in with_form if s.find("./W") is None]
    # No W anywhere -> not a segmented corpus. All W -> nothing to report.
    if not w_less or len(w_less) == len(with_form):
        return []
    return [Finding(
        rule_id="V148",
        severity=Severity.SOFT,
        message=(
            f"V148 SOFT: {len(w_less)} of {len(with_form)} sentences have "
            f"no W tier while others in the file do — incomplete word "
            f"segmentation (POL-041)"
        ),
        path=path,
        count=len(w_less),
        language=_tree_language(tree, path, index),
        character="",
    )]


RULES: list = [
    v010_count_s_without_form,
    v014_count_missing_standard_form,
    # POL-023 M-tier consistency (2026-08-10; V144 per-sentence 2026-08-12)
    v144_M_less_W_in_parsed_sentence,
    v145_degenerate_all_single_M_tier,
    # POL-041 W-tier presence (2026-09-03), file-scoped
    v148_W_less_S_in_segmented_file,
]
CROSS_FILE_RULES: list = []
