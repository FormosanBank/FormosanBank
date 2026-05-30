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


_XSD_PATH = Path(__file__).resolve().parents[1] / "xml_template.xsd"
with open(_XSD_PATH) as _f:
    _XSD = etree.XMLSchema(etree.parse(_f))


def v000_schema_validation(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """Validate the parsed tree against the canonical XSD.

    Migrated from DTD validation in Phase 4.5. XSD covers all the
    structural rules the DTD did, plus FORM/@kindOf enumeration (V016),
    PHON/@kindOf enumeration (V071), AUDIO/@start and @end numeric
    type (subsumes the v050 numeric branch), and xs:unique id
    uniqueness across S/W/M within a file (V039).
    """
    if _XSD.validate(tree):
        return []
    findings: list[Finding] = []
    for entry in _XSD.error_log:
        findings.append(Finding(
            rule_id="V000",
            severity=Severity.HARD,
            message=f"Schema violation: {entry.message}",
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



def v050_audio_attr_present(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """AUDIO start/end attributes: required only when the AUDIO element has
    no @file of its own.

    Per the canonical spec at
    en-us/the-bank-architecture/formosanbank-xml-format.md:
      - If <AUDIO> has its own @file attribute, the whole referenced file
        IS the clip — start/end are NOT required.
      - If <AUDIO> has no @file attribute, the audio is shared across the
        XML (the file is named at TEXT/@audio); start and end pinpoint
        the clip within that file and are required.
    Either way, if start/end ARE present they must parse as numeric.

    Phase 5 will likely re-attribute this check to V052 (single-file-mode
    requires start/end) per the design doc rule numbering; for now we keep
    the V050 label.
    """
    findings: list[Finding] = []
    for audio in tree.iter("AUDIO"):
        start = audio.get("start")
        end = audio.get("end")
        has_file = audio.get("file") is not None
        parent = audio.getparent()
        s_id = parent.get("id") if parent is not None else None
        location = f"S={s_id}" if s_id else "AUDIO"

        if not has_file and (start is None or end is None):
            findings.append(Finding(
                rule_id="V050",
                severity=Severity.HARD,
                message="AUDIO without @file must have start and end attributes "
                        "(audio is shared at TEXT level; start/end pinpoint the clip)",
                path=path,
                location=location,
            ))
        # Non-numeric start/end is now rejected by XSD (xs:double), so the
        # float() try/except branch that was here is no longer reachable.
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


def v035_xml_lang_is_iso_639_3(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """Every xml:lang attribute on every element must be a valid ISO 639-3 code.

    Extends the legacy validate_lang_code (which only checked TEXT-level)
    to walk all elements with an xml:lang attribute. Code-switching at the
    S/W/M/TRANSL level is rare but real; when present, the language code
    must still be a valid ISO 639-3 entry from QC/validation/iso-639-3.txt.

    The TEXT-level case is also covered here: a missing xml:lang on TEXT
    raises a finding (xml:lang is required on TEXT, but the DTD-driven
    enforcement may not surface a finding shaped the same way as this rule).
    """
    findings: list[Finding] = []
    root = tree.getroot()
    if root.tag == "TEXT" and root.get(_XML_LANG) is None:
        findings.append(Finding(
            rule_id="V035",
            severity=Severity.HARD,
            message="TEXT element missing xml:lang attribute",
            path=path,
            location="TEXT",
        ))
    for element in tree.iter():
        lang = element.get(_XML_LANG)
        if lang is None:
            continue
        if lang in _ISO_CODES:
            continue
        elem_id = element.get("id")
        location = f"{element.tag}={elem_id}" if elem_id else element.tag
        findings.append(Finding(
            rule_id="V035",
            severity=Severity.HARD,
            message=f"{element.tag} xml:lang={lang!r} is not a valid ISO 639-3 code",
            path=path,
            location=location,
        ))
    return findings


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
    v000_schema_validation,
    v001_root_must_be_TEXT,
    v017_form_must_have_content,
    v035_xml_lang_is_iso_639_3,
    v050_audio_attr_present,
    v051_audio_start_before_end,
]
CROSS_FILE_RULES: list = []
