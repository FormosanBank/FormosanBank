"""HARD-severity rules: violations cause the validator to exit nonzero.

Each rule is a function with signature:
    rule(tree: etree._ElementTree, path: Path, index: CorpusIndex | None) -> list[Finding]

Rules that do NOT consult `index` go in RULES; the runner calls them
in pass 1. Rules that DO consult `index` go in CROSS_FILE_RULES; the
runner calls them in pass 2 after the index is built.
"""
from pathlib import Path

from lxml import etree

from QC.validation._corpus_index import CorpusIndex
from QC.validation._finding import Finding, Severity


_DTD_PATH = Path(__file__).resolve().parents[1] / "xml_template.dtd"
with open(_DTD_PATH) as _f:
    _DTD = etree.DTD(_f)

_KNOWN_KINDOF = {"original", "standard", "alternate"}


def v000_dtd_validation(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """Validate the parsed tree against the canonical DTD.

    DTD violations cover V003 (S under TEXT), V004 (W under S), V005
    (M under W), V011 (W must have FORM), V012 (M must have FORM),
    V030–V038 (required attributes the DTD declares as #REQUIRED), and
    any other structural invariants the DTD encodes. Phase 4 (DTD
    tightening) extends this rule's reach by adding constraints to
    xml_template.dtd; no parallel Python rule is needed when the DTD
    can express the check.
    """
    if _DTD.validate(tree):
        return []
    findings: list[Finding] = []
    for entry in _DTD.error_log:
        findings.append(Finding(
            rule_id="V000",
            severity=Severity.HARD,
            message=f"DTD violation: {entry.message}",
            path=path,
            location=f"line={entry.line}",
        ))
    return findings


def v001_root_must_be_TEXT(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V001: The document root element must be TEXT.

    The DTD does not enforce which element is the root (it validates
    any declared element at the root), so this check is a direct
    inspection of the root tag.
    """
    root = tree.getroot()
    if root.tag == "TEXT":
        return []
    return [Finding(
        rule_id="V001",
        severity=Severity.HARD,
        message=f"root element must be TEXT, got <{root.tag}>",
        path=path,
        location="line=1",
    )]


def v016_known_kindOf_values(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V016: FORM/@kindOf must be one of original, standard, alternate.

    The DTD declares kindOf as CDATA (any string), so the enumeration
    check requires a Python rule. The XSD had this as an xs:enumeration;
    this rule migrates that constraint.
    """
    findings: list[Finding] = []
    for form in tree.iter("FORM"):
        val = form.get("kindOf")
        if val is not None and val not in _KNOWN_KINDOF:
            findings.append(Finding(
                rule_id="V016",
                severity=Severity.HARD,
                message=f"FORM/@kindOf invalid value {val!r}; expected one of {sorted(_KNOWN_KINDOF)}",
                path=path,
                location=f"line={form.sourceline}",
            ))
    return findings


RULES: list = [v000_dtd_validation, v001_root_must_be_TEXT, v016_known_kindOf_values]
CROSS_FILE_RULES: list = []
