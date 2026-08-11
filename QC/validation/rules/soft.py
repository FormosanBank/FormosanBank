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


def _w_morpheme_counts(tree: etree._ElementTree) -> list[int]:
    """Direct-child M count for every W in the file, in document order."""
    return [
        sum(1 for child in w if child.tag == "M")
        for w in tree.iter("W")
    ]


def _tree_language(tree: etree._ElementTree, path: Path,
                   index: CorpusIndex | None) -> str:
    if index is not None and path in index.langs:
        return index.langs[path]
    return tree.getroot().get(_XML_LANG) or ""


def v144_M_less_W_in_segmented_file(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V144 SOFT (POL-023): morpheme-segmented file with M-less Ws.

    Ruling 2026-08-10: in a file where any W has 2+ M children, every W
    must have at least one M. A single-M W there reads as "analyzed as
    monomorphemic"; a zero-M W is an unfinished segmentation. Aggregated
    per file. SOFT because existing corpora are known to trip this and
    need fixing over time.
    """
    m_counts = _w_morpheme_counts(tree)
    if not any(count >= 2 for count in m_counts):
        return []
    missing = sum(1 for count in m_counts if count == 0)
    if missing == 0:
        return []
    return [Finding(
        rule_id="V144",
        severity=Severity.SOFT,
        message=(
            f"V144 SOFT: {missing} of {len(m_counts)} W elements have no M "
            f"child in a morpheme-segmented file (POL-023: segmented files "
            f"give every W at least one M)"
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
    """V145 SOFT (POL-023): M level present but no W has 2+ Ms.

    Ruling 2026-08-10: corpora without morpheme segmentation should have
    no M level at all — an M tier where every M-bearing W has exactly
    one M identical in role to its W adds no information (historically:
    ~100 spurious M shells shipped in YeddaPalemeqBlog). Aggregated per
    file. SOFT because known corpora will trip this pending cleanup.
    """
    m_counts = _w_morpheme_counts(tree)
    if not m_counts or any(count >= 2 for count in m_counts):
        return []
    singles = sum(1 for count in m_counts if count >= 1)
    if singles == 0:
        return []
    return [Finding(
        rule_id="V145",
        severity=Severity.SOFT,
        message=(
            f"V145 SOFT: M level present but no W has 2+ M children "
            f"({singles} single-M Ws) — unsegmented corpora should have "
            f"no M level (POL-023)"
        ),
        path=path,
        count=singles,
        language=_tree_language(tree, path, index),
        character="",
    )]


RULES: list = [
    v010_count_s_without_form,
    v014_count_missing_standard_form,
    # POL-023 M-tier consistency (2026-08-10)
    v144_M_less_W_in_segmented_file,
    v145_degenerate_all_single_M_tier,
]
CROSS_FILE_RULES: list = []
