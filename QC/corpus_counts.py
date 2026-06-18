"""Single source of truth for FormosanBank corpus counting rules.

Both statistics pipelines import from here:
  - QC/utilities/get_corpus_stats.py (per-corpus CSVs for the Gitbook)
  - QC/corpus_metrics.py and QC/count_tokens.py (size tracker + PR deltas)

Rules (decided 2026-06-10):
  - A token is a whitespace-separated chunk containing at least one
    Unicode letter or digit. "123" counts; "?" does not.
  - Per sentence, count the `standard` FORM if non-empty, else the
    `original` FORM, else 0. Word counts come from the S tier only —
    W and M FORMs are never counted as tokens.
  - Language identity comes from xml:lang + dialect attributes only:
    trv + dialect "Truku" is Truku; trv + anything else is Seediq.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

LANG_CODE_TO_NAME = {
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

# All display names a record can resolve to (the 16 codes plus Truku,
# which is distinguished from Seediq by dialect rather than ISO code).
LANGUAGE_NAMES = sorted(set(LANG_CODE_TO_NAME.values()) | {"Truku"})

ENG_CODES = {"eng", "en"}
ZHO_CODES = {"zho", "zh", "zh-hant", "zh-hans"}


def count_words(text: str | None) -> int:
    """Count whitespace-separated chunks containing >=1 letter or digit."""
    if not text:
        return 0
    return sum(1 for chunk in text.split() if any(c.isalnum() for c in chunk))


def select_sentence_form(sentence) -> str | None:
    """Return the text to count for one <S>: standard tier, else original.

    Only direct FORM children of S are considered (S-tier rule)."""
    for kind in ("standard", "original"):
        for form in sentence.findall("FORM"):
            if form.get("kindOf") == kind and form.text and form.text.strip():
                return form.text
    return None


def resolve_language(language_code: str | None, dialect: str | None) -> str | None:
    """Resolve (xml:lang, dialect) to a display language name.

    trv + dialect 'Truku' is Truku; trv + anything else is Seediq.
    Returns None for unknown or missing codes (caller decides how to
    label those)."""
    code = (language_code or "").strip().lower()
    if not code:
        return None
    if code == "trv" and (dialect or "").strip().lower() == "truku":
        return "Truku"
    return LANG_CODE_TO_NAME.get(code)


COUNT_FIELDS = (
    "word_count",
    "sentences",
    "segmented_words",
    "glossed_words",
    "eng_transl_count",
    "zho_transl_count",
    "transcribed_audio_count",
    "untranscribed_audio_count",
    "word_elements",
    "morpheme_elements",
    "translation_elements",
    "audio_elements",
    "file_count",
)


def split_audio_elements(root) -> tuple[list, list]:
    """Return (transcribed, untranscribed) AUDIO elements with a file attr.

    Transcribed = nested in S or W; untranscribed = direct child of TEXT."""
    transcribed = [e for e in root.findall(".//S/AUDIO") if "file" in e.attrib]
    transcribed += [e for e in root.findall(".//W/AUDIO") if "file" in e.attrib]
    untranscribed = [e for e in root.findall("AUDIO") if "file" in e.attrib]
    return transcribed, untranscribed


def analyze_root(root) -> dict:
    """Compute the per-file statistics record from a parsed TEXT element."""
    language = (root.get(XML_LANG) or "").strip().lower()
    dialect = (root.get("dialect") or "").strip()
    warnings = []
    if not language:
        warnings.append("missing xml:lang attribute")
    if not dialect:
        warnings.append("missing dialect attribute")

    record: dict[str, Any] = {field: 0 for field in COUNT_FIELDS}
    record.update({"language": language, "dialect": dialect, "file_count": 1})

    for sentence in root.findall(".//S"):
        record["sentences"] += 1
        text = select_sentence_form(sentence)
        if text is None:
            if sentence.find("FORM") is None:
                warnings.append(
                    f"sentence {sentence.get('id', '?')} has no countable FORM at the S level"
                )
            n = 0
        else:
            n = count_words(text)
        record["word_count"] += n

        transl_langs = {
            (t.get(XML_LANG) or "").strip().lower()
            for t in sentence.findall("TRANSL")
            if t.text and t.text.strip()
        }
        if transl_langs & ENG_CODES:
            record["eng_transl_count"] += n
        if transl_langs & ZHO_CODES:
            record["zho_transl_count"] += n
        if sentence.find(".//M") is not None:
            record["segmented_words"] += n
        if sentence.find(".//M/TRANSL") is not None:
            record["glossed_words"] += n

    transcribed, untranscribed = split_audio_elements(root)
    record["transcribed_audio_count"] = len(transcribed)
    record["untranscribed_audio_count"] = len(untranscribed)
    record["word_elements"] = len(root.findall(".//W"))
    record["morpheme_elements"] = len(root.findall(".//M"))
    record["translation_elements"] = len(root.findall(".//TRANSL"))
    record["audio_elements"] = len(root.findall(".//AUDIO"))
    record["warnings"] = warnings
    return record


def analyze_file(xml_path) -> dict:
    """Parse one XML file and return its statistics record.

    Raises xml.etree.ElementTree.ParseError on malformed XML — callers
    decide whether to collect or abort."""
    root = ET.parse(xml_path).getroot()
    record = analyze_root(root)
    record["path"] = str(xml_path)
    return record


def collect_records(xml_dir) -> tuple[list[dict], list[dict]]:
    """Analyze every *.xml under xml_dir. Returns (records, parse_errors)."""
    records, parse_errors = [], []
    for xml_file in sorted(Path(xml_dir).rglob("*.xml")):
        try:
            records.append(analyze_file(xml_file))
        except Exception as exc:
            parse_errors.append({"path": str(xml_file), "error": str(exc)})
    return records, parse_errors
