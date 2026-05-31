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


RULES: list = [v010_count_s_without_form, v014_count_missing_standard_form]
CROSS_FILE_RULES: list = []
