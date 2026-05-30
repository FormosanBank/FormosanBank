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


def v050_audio_attr_present(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """Each <AUDIO> element must have start and end attributes that are numeric.

    Preserves the legacy validate_audio_attr behavior. Note: the legacy code
    has a known bug around audio="diarized" vs audio="segmented" semantics.
    Phase 5's V050-V056 rule migrations will refactor this rule to fix the bug;
    for now we keep the bug so the existing tests continue to pass.
    """
    findings: list[Finding] = []
    for audio in tree.iter("AUDIO"):
        start = audio.get("start")
        end = audio.get("end")
        parent = audio.getparent()
        s_id = parent.get("id") if parent is not None else None
        location = f"S={s_id}" if s_id else "AUDIO"
        if start is None or end is None:
            findings.append(Finding(
                rule_id="V050",
                severity=Severity.HARD,
                message="AUDIO missing required start or end attribute",
                path=path,
                location=location,
            ))
            continue
        try:
            float(start)
            float(end)
        except ValueError:
            findings.append(Finding(
                rule_id="V050",
                severity=Severity.HARD,
                message=f"AUDIO start/end not numeric (start={start!r}, end={end!r})",
                path=path,
                location=location,
            ))
    return findings


def v051_audio_start_before_end(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """Each <AUDIO> element with numeric start/end must have start < end.

    Preserves the legacy validate_audio_attr behavior. The diarized/segmented
    bug noted above also affects this rule; Phase 5 fixes both together.
    """
    findings: list[Finding] = []
    for audio in tree.iter("AUDIO"):
        start = audio.get("start")
        end = audio.get("end")
        if start is None or end is None:
            continue  # v050 already reports
        try:
            s = float(start)
            e = float(end)
        except ValueError:
            continue  # v050 already reports
        if s >= e:
            parent = audio.getparent()
            s_id = parent.get("id") if parent is not None else None
            location = f"S={s_id}" if s_id else "AUDIO"
            findings.append(Finding(
                rule_id="V051",
                severity=Severity.HARD,
                message=f"AUDIO start ({start}) >= end ({end})",
                path=path,
                location=location,
            ))
    return findings


def _load_iso_639_3() -> frozenset[str]:
    """Load valid ISO 639-3 codes from the bundled reference file.

    The reference file is QC/validation/iso-639-3.txt: tab-separated,
    header on line 1, 3-letter code in column 1.
    """
    iso_path = Path(__file__).resolve().parents[1] / "iso-639-3.txt"
    codes: set[str] = set()
    with open(iso_path, encoding="utf-8") as f:
        next(f)  # skip header
        for line in f:
            parts = line.split("\t")
            if parts and parts[0].strip():
                codes.add(parts[0].strip())
    return frozenset(codes)


_ISO_CODES = _load_iso_639_3()
_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def v035_text_lang_is_iso_639_3(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """The TEXT root's xml:lang must be a valid ISO 639-3 code.

    Preserves the legacy validate_lang_code behavior at TEXT-level only.
    Element-level (S, W, M) xml:lang checks are deferred to Phase 5
    (V035 expansion).
    """
    root = tree.getroot()
    if root.tag != "TEXT":
        return []  # v001/v000 already report root-tag issues
    lang = root.get(_XML_LANG)
    if lang is None:
        return [Finding(
            rule_id="V035",
            severity=Severity.HARD,
            message="TEXT element missing xml:lang attribute",
            path=path,
            location="TEXT",
        )]
    if lang not in _ISO_CODES:
        return [Finding(
            rule_id="V035",
            severity=Severity.HARD,
            message=f"TEXT xml:lang={lang!r} is not a valid ISO 639-3 code",
            path=path,
            location="TEXT",
        )]
    return []


def v017_form_must_have_content(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V017: every <FORM> element must have non-empty text content.

    The DTD allows mixed content on FORM, so this constraint cannot be
    expressed in pure XSD/DTD — it requires a Python rule.
    """
    findings: list[Finding] = []
    for form in tree.iter("FORM"):
        text = form.text or ""
        if text.strip():
            continue
        parent = form.getparent()
        parent_id = parent.get("id") if parent is not None else None
        parent_tag = parent.tag if parent is not None else "FORM"
        kind = form.get("kindOf") or "(no kindOf)"
        findings.append(Finding(
            rule_id="V017",
            severity=Severity.HARD,
            message=f"empty FORM (kindOf={kind!r}) — form is empty",
            path=path,
            location=f"{parent_tag}={parent_id}" if parent_id else parent_tag,
        ))
    return findings


RULES: list = [
    v000_dtd_validation,
    v001_root_must_be_TEXT,
    v016_known_kindOf_values,
    v017_form_must_have_content,
    v035_text_lang_is_iso_639_3,
    v050_audio_attr_present,
    v051_audio_start_before_end,
]
CROSS_FILE_RULES: list = []
