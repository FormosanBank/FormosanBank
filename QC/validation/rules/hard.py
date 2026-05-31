"""HARD-severity rules: violations cause the validator to exit nonzero.

Each rule is a function with signature:
    rule(tree: etree._ElementTree, path: Path, index: CorpusIndex | None) -> list[Finding]

Rules that do NOT consult `index` go in RULES; the runner calls them
in pass 1. Rules that DO consult `index` go in CROSS_FILE_RULES; the
runner calls them in pass 2 after the index is built.
"""
import csv
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
    no @file of its own (single-file mode).

    Per the canonical spec:
      - If <AUDIO> has its own @file attribute, the whole referenced file
        IS the clip — start/end are NOT required.
      - If <AUDIO> has no @file attribute, the audio is shared across the
        XML (the file is named at TEXT/@audio); start and end pinpoint
        the clip within that file and are required (single-file mode).

    V052: single-file mode requires missing start and missing end to be
    reported explicitly.
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
            missing = []
            if start is None:
                missing.append("missing start")
            if end is None:
                missing.append("missing end")
            findings.append(Finding(
                rule_id="V052",
                severity=Severity.HARD,
                message=(
                    f"AUDIO in single-file mode must have start and end attributes "
                    f"({', '.join(missing)}); "
                    f"audio is shared at TEXT level via TEXT/@audio"
                ),
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

    V054: end < start (end before start) is a violation.
    """
    findings: list[Finding] = []
    for audio in tree.iter("AUDIO"):
        start = audio.get("start")
        end = audio.get("end")
        if start is None or end is None:
            continue  # v050/v052 already reports
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
                rule_id="V054",
                severity=Severity.HARD,
                message=f"AUDIO end < start: start ({start}) >= end ({end}); end before start violation",
                path=path,
                location=location,
            ))
    return findings


def v051_audio_empty_file(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V051: AUDIO/@file, if present, must be non-empty.

    An AUDIO with file="" is neither valid single-file mode (no @file)
    nor valid segmented mode (has @file but the path is empty).
    """
    findings: list[Finding] = []
    for audio in tree.iter("AUDIO"):
        file_val = audio.get("file")
        if file_val is not None and file_val.strip() == "":
            parent = audio.getparent()
            s_id = parent.get("id") if parent is not None else None
            location = f"S={s_id}" if s_id else "AUDIO"
            findings.append(Finding(
                rule_id="V051",
                severity=Severity.HARD,
                message="AUDIO has empty @file attribute (empty audio/@file); "
                        "@file must be a non-empty path",
                path=path,
                location=location,
            ))
    return findings


def v053_orphan_audio(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V053: AUDIO with no @file when TEXT/@audio is also absent is an orphan.

    Without either an AUDIO/@file (segmented mode) or TEXT/@audio
    (single-file mode), the AUDIO element is unmoored — there is no
    audio source to reference.
    """
    root = tree.getroot()
    text_audio = root.get("audio") if root.tag == "TEXT" else None
    if text_audio is not None:
        return []  # single-file mode: TEXT/@audio is the source
    findings: list[Finding] = []
    for audio in tree.iter("AUDIO"):
        if audio.get("file") is None:
            parent = audio.getparent()
            s_id = parent.get("id") if parent is not None else None
            location = f"S={s_id}" if s_id else "AUDIO"
            findings.append(Finding(
                rule_id="V053",
                severity=Severity.HARD,
                message="orphan AUDIO: no @file attribute and TEXT/@audio is not set; "
                        "AUDIO is unmoored with no audio source",
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


# ---------------------------------------------------------------------------
# Category 1: FORM tier (V013, V015)
# ---------------------------------------------------------------------------

def v013_S_must_have_original_FORM(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V013: every S must have at least one direct-child FORM with kindOf='original'.

    DTD/XSD content models cannot express attribute-conditional cardinality,
    so this is a Python check.
    """
    findings: list[Finding] = []
    for s in tree.iter("S"):
        has_original = any(
            child.tag == "FORM" and child.get("kindOf") == "original"
            for child in s
        )
        if not has_original:
            s_id = s.get("id")
            findings.append(Finding(
                rule_id="V013",
                severity=Severity.HARD,
                message=f"S id={s_id!r} has no original FORM (missing original tier); "
                        "each S must have a kindOf='original' FORM",
                path=path,
                location=f"S={s_id}" if s_id else "S",
            ))
    return findings


def v015_S_at_most_one_original_FORM(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V015: each S must have at most one direct-child FORM with kindOf='original'.

    Duplicate kindOf on sibling FORMs under the same S is forbidden.
    """
    findings: list[Finding] = []
    for s in tree.iter("S"):
        originals = [
            child for child in s
            if child.tag == "FORM" and child.get("kindOf") == "original"
        ]
        if len(originals) > 1:
            s_id = s.get("id")
            findings.append(Finding(
                rule_id="V015",
                severity=Severity.HARD,
                message=f"S id={s_id!r} has {len(originals)} FORM kindOf='original' "
                        "elements; duplicate kindOf is forbidden",
                path=path,
                location=f"S={s_id}" if s_id else "S",
            ))
    return findings


# ---------------------------------------------------------------------------
# Category 2: TRANSL rules (V021, V022, V023, V026)
# ---------------------------------------------------------------------------

_XML_LANG_ATTR = "{http://www.w3.org/XML/1998/namespace}lang"


def v021_M_lone_TRANSL_must_be_original(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V021: on an M element, if exactly one TRANSL child exists, it must be kindOf='original'.

    A single TRANSL on M without kindOf='original' is ambiguous and
    disallowed. (Multiple TRANSLs may include non-original forms.)
    """
    findings: list[Finding] = []
    for m in tree.iter("M"):
        transls = [child for child in m if child.tag == "TRANSL"]
        if len(transls) == 1 and transls[0].get("kindOf") != "original":
            m_id = m.get("id")
            kind = transls[0].get("kindOf") or "(unset)"
            findings.append(Finding(
                rule_id="V021",
                severity=Severity.HARD,
                message=f"M id={m_id!r} has a lone TRANSL with kindOf={kind!r}; "
                        "single transl on M must be kindOf='original'",
                path=path,
                location=f"M={m_id}" if m_id else "M",
            ))
    return findings


def v022_M_originals_distinct_lang(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V022: on an M element, multiple TRANSL kindOf='original' must have distinct xml:lang.

    Duplicate xml:lang among original-tier TRANSLs on the same M is
    ambiguous (which one is canonical?).
    """
    findings: list[Finding] = []
    for m in tree.iter("M"):
        originals = [
            child for child in m
            if child.tag == "TRANSL" and child.get("kindOf") == "original"
        ]
        seen: dict[str, int] = {}
        for t in originals:
            lang = t.get(_XML_LANG_ATTR) or ""
            seen[lang] = seen.get(lang, 0) + 1
        for lang, count in seen.items():
            if count > 1:
                m_id = m.get("id")
                findings.append(Finding(
                    rule_id="V022",
                    severity=Severity.HARD,
                    message=f"M id={m_id!r} has {count} TRANSL kindOf='original' with "
                            f"duplicate xml:lang={lang!r}; same xml:lang among originals "
                            "is forbidden",
                    path=path,
                    location=f"M={m_id}" if m_id else "M",
                ))
    return findings


def v023_transl_must_have_xml_lang(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V023: every TRANSL element must have an xml:lang attribute.

    XSD enforces this via #REQUIRED/use='required', so this Python rule
    is redundant with V000's XSD finding. It exists to ensure a finding
    with rule-specific markers (v023, 'TRANSL has no xml:lang') is
    emitted even when the XSD message wording differs.
    """
    findings: list[Finding] = []
    for transl in tree.iter("TRANSL"):
        if transl.get(_XML_LANG_ATTR) is None:
            parent = transl.getparent()
            p_id = parent.get("id") if parent is not None else None
            p_tag = parent.tag if parent is not None else "?"
            findings.append(Finding(
                rule_id="V023",
                severity=Severity.HARD,
                message="TRANSL has no xml:lang attribute; "
                        "xml:lang is required on every TRANSL",
                path=path,
                location=f"{p_tag}={p_id}" if p_id else p_tag,
            ))
    return findings


def v026_M_transl_kindof_enum(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V026: TRANSL/@kindOf at M level must be 'original' or 'standard' when set.

    Free-form values (e.g., 'DeepL', 'freeform') are only valid at the
    sentence/text tier. M-level TRANSL kindOf is strictly enumerated.
    """
    _ALLOWED = {"original", "standard"}
    findings: list[Finding] = []
    for m in tree.iter("M"):
        for transl in m:
            if transl.tag != "TRANSL":
                continue
            kind = transl.get("kindOf")
            if kind is not None and kind not in _ALLOWED:
                m_id = m.get("id")
                findings.append(Finding(
                    rule_id="V026",
                    severity=Severity.HARD,
                    message=f"M id={m_id!r}: M-level TRANSL kindOf={kind!r} is not "
                            "allowed; transl kindof on M must be 'original' or 'standard'",
                    path=path,
                    location=f"M={m_id}" if m_id else "M",
                ))
    return findings


# ---------------------------------------------------------------------------
# Category 3: TEXT attribute rules (V036, V039)
# ---------------------------------------------------------------------------

def _load_dialects() -> dict[str, set[str]]:
    """Load dialects.csv into a dict mapping Language name -> set of dialect names.

    CSV format: Language,Official,Chinese,glottocode,OtherNames
    We use the 'Language' and 'Official' columns (Language is the language
    name; Official is the dialect name).
    """
    dialects_path = Path(__file__).resolve().parents[3] / "dialects.csv"
    result: dict[str, set[str]] = {}
    with open(dialects_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lang = row["Language"].strip()
            dialect = row["Official"].strip()
            if lang and dialect:
                result.setdefault(lang, set()).add(dialect)
    return result


# ISO 639-3 code -> Language name (matches dialects.csv "Language" column).
# Source: QC/corpus_metrics.py LANG_CODES dict.
_ISO_TO_LANGUAGE: dict[str, str] = {
    "ami": "Amis",
    "tay": "Atayal",
    "pwn": "Paiwan",
    "bnn": "Bunun",
    "pyu": "Puyuma",
    "dru": "Rukai",
    "tsu": "Tsou",
    "xsy": "Saisiyat",
    "tao": "Yami",
    "ssf": "Thao",
    "ckv": "Kavalan",
    "trv": "Seediq",
    "szy": "Sakizaya",
    "sxr": "Saaroa",
    "xnb": "Kanakanavu",
    "fos": "Siraya",
}

_DIALECT_MAP: dict[str, set[str]] = _load_dialects()


def v036_text_dialect_valid(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V036: TEXT/@dialect, if set, must be a valid dialect for the language.

    Dialect validity is checked against dialects.csv (Language -> Official
    dialect names). The ISO 639-3 code in TEXT/@xml:lang is mapped to a
    Language name via the hardcoded _ISO_TO_LANGUAGE dict (sourced from
    QC/corpus_metrics.py). If the language code is not in the dict, the
    rule skips the check (unknown language; other rules cover invalid lang
    codes).
    """
    root = tree.getroot()
    if root.tag != "TEXT":
        return []
    dialect = root.get("dialect")
    if not dialect:
        return []
    lang_code = root.get(_XML_LANG_ATTR) or root.get("xml:lang") or ""
    language = _ISO_TO_LANGUAGE.get(lang_code)
    if language is None:
        return []  # unknown language code; v035 handles that
    allowed = _DIALECT_MAP.get(language, set())
    if dialect not in allowed:
        return [Finding(
            rule_id="V036",
            severity=Severity.HARD,
            message=f"TEXT dialect={dialect!r} is not a valid dialect for "
                    f"language {language!r}; check dialects.csv for allowed values",
            path=path,
            location="TEXT",
        )]
    return []


def v039_id_unique_within_file(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V039: id values must be unique across S, W, M within a single file.

    XSD enforces this via xs:unique, but the Python rule emits a finding
    with rule-specific markers ('duplicate id', 'id collision') so that
    the corresponding test can match on rule ID rather than relying on
    V000's XSD message wording.
    """
    seen: dict[str, list[str]] = {}
    for elem in tree.iter("S", "W", "M"):
        elem_id = elem.get("id")
        if elem_id:
            seen.setdefault(elem_id, []).append(elem.tag)
    findings: list[Finding] = []
    for elem_id, tags in seen.items():
        if len(tags) > 1:
            tag_str = " and ".join(f"<{t}>" for t in tags)
            findings.append(Finding(
                rule_id="V039",
                severity=Severity.HARD,
                message=f"duplicate id {elem_id!r} appears as both {tag_str}; "
                        "id collision within file",
                path=path,
                location=f"id={elem_id}",
            ))
    return findings


# ---------------------------------------------------------------------------
# Category 5: W/M segmentation (V062)
# ---------------------------------------------------------------------------

import re as _re

_INFIX_PATTERN = _re.compile(r"^-[^-]+-$")


def v062_infix_M_needs_angle_gloss(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V062: an M whose FORM has infix shape ('-X-') requires parent W to have
    a TRANSL containing an angle-bracket gloss (e.g., '<AV>').

    Infix shape: FORM text matches /^-[^-]+-$/ (starts and ends with '-').
    Angle-bracket gloss: TRANSL text contains '<...>' (any '<' followed
    eventually by '>').
    """
    findings: list[Finding] = []
    for m in tree.iter("M"):
        # Check if M has an infix-shaped FORM
        form_text = None
        for child in m:
            if child.tag == "FORM":
                form_text = (child.text or "").strip()
                break
        if form_text is None or not _INFIX_PATTERN.match(form_text):
            continue
        # Find parent W
        parent_w = m.getparent()
        if parent_w is None or parent_w.tag != "W":
            continue
        # Check if parent W has a TRANSL with angle-bracket gloss
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
                severity=Severity.HARD,
                message=f"M id={m_id!r} has infix FORM {form_text!r} but parent "
                        f"W id={w_id!r} has no TRANSL with an angle-bracket gloss "
                        "('<X>'); infix morphemes require angle-bracket gloss notation",
                path=path,
                location=f"M={m_id}" if m_id else "M",
            ))
    return findings


# ---------------------------------------------------------------------------
# Category 6: PHON rules (V070, V071, V072, V073)
# ---------------------------------------------------------------------------

_PHON_ALLOWED_PARENTS = {"S", "W", "M"}
_PHON_KINDOF_ALLOWED = {"original", "standard"}


def v070_phon_placement(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V070: PHON is only permitted as a child of S, W, or M.

    XSD already rejects PHON under TEXT (it's not in TEXT's content
    model), so this Python rule is partly redundant with V000. It exists
    to emit a finding with the marker 'PHON placement' / 'PHON must be
    a child of S, W, or M' so the V070 test can match on rule-specific
    text.
    """
    findings: list[Finding] = []
    for phon in tree.iter("PHON"):
        parent = phon.getparent()
        parent_tag = parent.tag if parent is not None else None
        if parent_tag not in _PHON_ALLOWED_PARENTS:
            findings.append(Finding(
                rule_id="V070",
                severity=Severity.HARD,
                message=f"PHON placement error: PHON must be a child of S, W, or M "
                        f"(found under <{parent_tag}>)",
                path=path,
                location=parent_tag or "PHON",
            ))
    return findings


def v071_phon_kindof_enum(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V071: PHON/@kindOf must be 'original' or 'standard' when set.

    XSD enforces this via an enum, making this rule redundant with V000.
    The Python rule exists to emit a finding with 'PHON kindOf' /
    'PHON/@kindOf' markers for the V071 test.
    """
    findings: list[Finding] = []
    for phon in tree.iter("PHON"):
        kind = phon.get("kindOf")
        if kind is not None and kind not in _PHON_KINDOF_ALLOWED:
            parent = phon.getparent()
            p_id = parent.get("id") if parent is not None else None
            p_tag = parent.tag if parent is not None else "?"
            findings.append(Finding(
                rule_id="V071",
                severity=Severity.HARD,
                message=f"PHON kindOf={kind!r} is not valid; "
                        "PHON/@kindOf must be 'original' or 'standard'",
                path=path,
                location=f"{p_tag}={p_id}" if p_id else p_tag,
            ))
    return findings


def v072_duplicate_phon_kindof(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V072: at most one PHON per kindOf value per parent element (S, W, M).

    Duplicate PHON kindOf siblings under the same parent are ambiguous.
    """
    findings: list[Finding] = []
    for parent in tree.iter("S", "W", "M"):
        counts: dict[str, int] = {}
        for child in parent:
            if child.tag == "PHON":
                kind = child.get("kindOf") or ""
                counts[kind] = counts.get(kind, 0) + 1
        for kind, count in counts.items():
            if count > 1:
                p_id = parent.get("id")
                findings.append(Finding(
                    rule_id="V072",
                    severity=Severity.HARD,
                    message=f"{parent.tag} id={p_id!r} has {count} PHON elements with "
                            f"kindOf={kind!r}; duplicate PHON kindOf is forbidden",
                    path=path,
                    location=f"{parent.tag}={p_id}" if p_id else parent.tag,
                ))
    return findings


def v073_phon_non_empty(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V073: PHON must have non-empty text content.

    A PHON with empty or whitespace-only text is a data error.
    """
    findings: list[Finding] = []
    for phon in tree.iter("PHON"):
        text = phon.text or ""
        if not text.strip():
            parent = phon.getparent()
            p_id = parent.get("id") if parent is not None else None
            p_tag = parent.tag if parent is not None else "?"
            findings.append(Finding(
                rule_id="V073",
                severity=Severity.HARD,
                message="PHON is empty; PHON must have non-empty text content",
                path=path,
                location=f"{p_tag}={p_id}" if p_id else p_tag,
            ))
    return findings


def v081_text_id_unique_across_published_corpora(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V081: a TEXT/@id in the corpus-under-test must not collide with
    any TEXT/@id in published Corpora/. Cross-file rule; consults the
    CorpusIndex's published_ids.
    """
    if index is None:
        return []
    root = tree.getroot()
    if root.tag != "TEXT":
        return []
    text_id = root.get("id")
    if text_id is None:
        return []
    collisions = index.published_ids.get(text_id, [])
    collisions = [p for p in collisions if p.resolve() != path.resolve()]
    if not collisions:
        return []
    return [Finding(
        rule_id="V081",
        severity=Severity.HARD,
        message=(
            f"TEXT/@id={text_id!r} collides with id in published corpora: "
            f"{', '.join(str(p) for p in collisions)}"
            f" (cross-corpus id collision)"
        ),
        path=path,
        location=f"TEXT[@id={text_id!r}]",
    )]


RULES: list = [
    v000_schema_validation,
    v001_root_must_be_TEXT,
    v013_S_must_have_original_FORM,
    v015_S_at_most_one_original_FORM,
    v017_form_must_have_content,
    v021_M_lone_TRANSL_must_be_original,
    v022_M_originals_distinct_lang,
    v023_transl_must_have_xml_lang,
    v026_M_transl_kindof_enum,
    v035_xml_lang_is_iso_639_3,
    v036_text_dialect_valid,
    v039_id_unique_within_file,
    v051_audio_empty_file,
    v050_audio_attr_present,
    v051_audio_start_before_end,
    v053_orphan_audio,
    v062_infix_M_needs_angle_gloss,
    v070_phon_placement,
    v071_phon_kindof_enum,
    v072_duplicate_phon_kindof,
    v073_phon_non_empty,
]
CROSS_FILE_RULES: list = [v081_text_id_unique_across_published_corpora]
