"""Single loader for the human-reviewed NTU source repair registry.

POL-039 keeps critical mapping data out of Python.  All consumers load
``CodeAndDocs/source_repairs.xml`` through the functions in this module.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path


REGISTRY = Path(__file__).resolve().parents[1] / "source_repairs.xml"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


@lru_cache(maxsize=1)
def _load_root() -> ET.Element:
    root = ET.parse(REGISTRY).getroot()
    if root.tag != "SOURCE_REPAIRS":
        raise AssertionError(
            f"unexpected source repair registry root {root.tag!r}: {REGISTRY}"
        )
    return root


def _required_text(parent: ET.Element, path: str) -> str:
    element = parent.find(path)
    if element is None or element.text is None:
        raise AssertionError(f"missing {path} in source repair registry")
    return element.text


def load_grammar_record_repairs() -> dict[tuple[str, int], dict]:
    """Load fail-closed repairs for malformed scraped grammar records."""
    result = {}
    section = _load_root().find("GRAMMAR_RECORD_REPAIRS")
    if section is None:
        raise AssertionError("GRAMMAR_RECORD_REPAIRS section missing")
    for case in section.findall("CASE"):
        source_file = case.get("sourceFile")
        record_id = case.get("recordId")
        source_digest = case.get("sourceDigest")
        if None in (source_file, record_id, source_digest):
            raise AssertionError("incomplete grammar record repair key")
        key = (source_file, int(record_id))
        if key in result:
            raise AssertionError(f"duplicate grammar record repair key: {key}")
        replacement = json.loads(_required_text(case, "REPLACEMENT_JSON"))
        if (
            not isinstance(replacement, list)
            or len(replacement) != 2
            or replacement[0] != key[1]
            or not isinstance(replacement[1], dict)
        ):
            raise AssertionError(f"invalid grammar replacement record: {key}")
        result[key] = {
            "source_digest": source_digest,
            "replacement": replacement,
            "note": _required_text(case, "NOTE"),
        }
    return result


def load_kanakanavu_free_alternatives() -> dict:
    result = {}
    section = _load_root().find("KANAKANAVU_FREE_ALTERNATIVES")
    if section is None:
        raise AssertionError("KANAKANAVU_FREE_ALTERNATIVES section missing")
    for case in section.findall("CASE"):
        key = (case.get("sourceFile"), case.get("sentenceId"))
        if None in key or key in result:
            raise AssertionError(f"invalid or duplicate free-alternative key: {key}")
        sources = {
            element.get(XML_LANG): element.text or ""
            for element in case.findall("SOURCE")
        }
        if set(sources) != {"zho", "eng"}:
            raise AssertionError(f"free-alternative source languages drifted: {key}")
        readings = sorted(
            case.findall("READING"), key=lambda element: int(element.get("index"))
        )
        if [int(element.get("index")) for element in readings] != list(
            range(1, len(readings) + 1)
        ):
            raise AssertionError(f"non-contiguous free-alternative readings: {key}")
        parsed = {"source": sources}
        for lang in ("zho", "eng"):
            parsed[lang] = tuple(
                next(
                    (
                        translation.text
                        for translation in reading.findall("TRANSL")
                        if translation.get(XML_LANG) == lang
                    ),
                    None,
                )
                for reading in readings
            )
        fallback = case.get("fallbackWord")
        if fallback is not None:
            parsed["fallback_word"] = int(fallback)
        for note in case.findall("TRANSL_NOTE"):
            lang = note.get(XML_LANG)
            if lang not in {"zho", "eng"}:
                raise AssertionError(f"invalid TRANSL_NOTE language: {key}")
            parsed[f"{lang}_note"] = note.text or ""
        form_note = case.find("FORM_NOTE")
        if form_note is not None:
            parsed["form_note"] = form_note.text or ""
        result[key] = parsed
    return result


def load_morpheme_slash_alternatives() -> dict:
    """Load reviewed free translations for morpheme-scoped alternatives."""
    result = {}
    section = _load_root().find("MORPHEME_SLASH_ALTERNATIVES")
    if section is None:
        raise AssertionError("MORPHEME_SLASH_ALTERNATIVES section missing")
    for case in section.findall("CASE"):
        key = (case.get("xmlFile"), case.get("sentenceId"))
        if None in key or key in result:
            raise AssertionError(
                f"invalid or duplicate morpheme slash-alternative key: {key}"
            )
        source_file = case.get("sourceFile")
        source_record = case.get("sourceRecord")
        source_digest = case.get("sourceDigest")
        if None in (source_file, source_record, source_digest):
            raise AssertionError(f"incomplete source witness for {key}")
        expected = {
            element.get(XML_LANG): element.text or ""
            for element in case.findall("SOURCE_TRANSL")
        }
        if set(expected) != {"zho", "eng"}:
            raise AssertionError(
                f"morpheme slash source translation languages drifted: {key}"
            )
        readings = sorted(
            case.findall("READING"), key=lambda element: int(element.get("index"))
        )
        if [int(element.get("index")) for element in readings] != list(
            range(1, len(readings) + 1)
        ):
            raise AssertionError(
                f"non-contiguous morpheme slash readings: {key}"
            )
        translations = []
        for reading in readings:
            values = {
                element.get(XML_LANG): element.text or ""
                for element in reading.findall("TRANSL")
            }
            if set(values) != {"zho", "eng"}:
                raise AssertionError(
                    f"morpheme slash reading languages drifted: {key}"
                )
            translations.append(values)
        result[key] = {
            "source_file": source_file,
            "source_record": int(source_record),
            "source_digest": source_digest,
            "expected_translations": expected,
            "translations": tuple(translations),
        }
    return result


def load_malformed_translations() -> list[dict]:
    result = []
    section = _load_root().find("MALFORMED_TRANSLATIONS")
    if section is None:
        raise AssertionError("MALFORMED_TRANSLATIONS section missing")
    for case in section.findall("CASE"):
        indices = case.get("sourceIndices") or ""
        replacement = case.find("REPLACEMENT")
        omit = case.get("omitTranslation") == "true"
        if omit == (replacement is not None):
            raise AssertionError(
                "malformed translation must have exactly one of "
                "omitTranslation or REPLACEMENT"
            )
        result.append({
            "xml": case.get("xmlFile"),
            "sentence_id": case.get("sentenceId"),
            "source": case.get("sourceFile"),
            "source_indices": tuple(int(index) for index in indices.split(",")),
            "source_digest": case.get("sourceDigest"),
            "lang": case.get(XML_LANG),
            "expected": _required_text(case, "EXPECTED"),
            "replacement": None if omit else replacement.text or "",
        })
    return result


def load_compact_translation_alternatives() -> dict:
    result = {}
    section = _load_root().find("COMPACT_TRANSLATION_ALTERNATIVES")
    if section is None:
        raise AssertionError("COMPACT_TRANSLATION_ALTERNATIVES section missing")
    for case in section.findall("CASE"):
        key = (
            case.get("xmlFile"),
            case.get("sentenceId"),
            case.get(XML_LANG),
        )
        if None in key or key in result or case.text is None:
            raise AssertionError(f"invalid or duplicate compact alternative: {key}")
        result[key] = case.text
    return result


def load_indexed_optional_words() -> dict:
    result = {}
    section = _load_root().find("INDEXED_OPTIONAL_WORDS")
    if section is None:
        raise AssertionError("INDEXED_OPTIONAL_WORDS section missing")
    for case in section.findall("CASE"):
        key = (case.get("xmlFile"), case.get("sentenceId"))
        if None in key or key in result:
            raise AssertionError(f"invalid or duplicate indexed optional: {key}")
        options = tuple(
            (
                int(option.get("wordIndex")),
                option.get("expectedWordForm"),
                option.get("surfaceToken"),
            )
            for option in case.findall("OPTIONAL")
        )
        if not options or any(None in option for option in options):
            raise AssertionError(f"invalid indexed optional entries: {key}")
        result[key] = (_required_text(case, "EXPECTED_FORM"), options)
    return result


def load_special_form_cases() -> dict[str, tuple[str, str, str]]:
    result = {}
    section = _load_root().find("SPECIAL_FORM_CASES")
    if section is None:
        raise AssertionError("SPECIAL_FORM_CASES section missing")
    for case in section.findall("CASE"):
        kind = case.get("kind")
        value = (
            case.get("xmlFile"),
            case.get("sentenceId"),
            _required_text(case, "EXPECTED_FORM"),
        )
        if kind is None or None in value or kind in result:
            raise AssertionError(f"invalid or duplicate special FORM case: {kind}")
        result[kind] = value
    return result


def load_story_gloss_repairs() -> dict[tuple[str, int], dict]:
    """Load exact, reviewed repairs for malformed story gloss rows."""
    result = {}
    section = _load_root().find("STORY_GLOSS_REPAIRS")
    if section is None:
        raise AssertionError("STORY_GLOSS_REPAIRS section missing")
    for case in section.findall("CASE"):
        source_file = case.get("sourceFile")
        record_id = case.get("recordId")
        digest = case.get("sourceDigest")
        if source_file is None or record_id is None or digest is None:
            raise AssertionError("incomplete story gloss repair key")
        key = (source_file, int(record_id))
        if key in result:
            raise AssertionError(f"duplicate story gloss repair key: {key}")
        replacement = tuple(
            (
                gloss.get("form") or "",
                gloss.get("eng") or "",
                gloss.get("zho") or "",
            )
            for gloss in case.findall("GLOSS")
        )
        note = _required_text(case, "NOTE")
        result[key] = {
            "source_digest": digest,
            "replacement": replacement,
            "note": note,
        }
    return result
