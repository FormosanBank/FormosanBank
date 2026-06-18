#!/usr/bin/env python3
"""Validate the FormosanBank XML constraints used by this repository.

The converted Moedict examples do not contain source-attested word segmentation
or morpheme gloss tiers, so finalized XML may stop at sentence-level S elements.
If optional W/M layers are ever added for another source, this validator still
checks their local FormosanBank structure.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


XML_NS = "http://www.w3.org/XML/1998/namespace"
REQUIRED_TEXT_ATTRS = {"id", "citation", "BibTeX_citation", "copyright", f"{{{XML_NS}}}lang"}
FORM_ATTRS = {"kindOf"}
TRANSL_ATTRS = {f"{{{XML_NS}}}lang", "kindOf"}
AUDIO_ATTRS = {"start", "end", "file", "url"}


def text_of(element: ET.Element) -> str:
    return (element.text or "").strip()


def extra_attrs(element: ET.Element, allowed: set[str]) -> set[str]:
    return set(element.attrib).difference(allowed)


def validate_form(element: ET.Element, context_id: str) -> list[str]:
    errors: list[str] = []
    extra = extra_attrs(element, FORM_ATTRS)
    if extra:
        errors.append(f"{context_id} has FORM with unsupported attributes: {', '.join(sorted(extra))}")
    if element.attrib.get("kindOf") != "original":
        errors.append(f"{context_id} has FORM without kindOf=\"original\"")
    if len(element):
        errors.append(f"{context_id} has FORM with child elements")
    if not text_of(element):
        errors.append(f"{context_id} has empty FORM")
    return errors


def validate_translation(element: ET.Element, context_id: str) -> list[str]:
    errors: list[str] = []
    extra = extra_attrs(element, TRANSL_ATTRS)
    if extra:
        errors.append(f"{context_id} has TRANSL with unsupported attributes: {', '.join(sorted(extra))}")
    lang = element.attrib.get(f"{{{XML_NS}}}lang")
    if not lang:
        errors.append(f"{context_id} has TRANSL without xml:lang")
    elif len(lang) != 3 or not lang.isalpha():
        errors.append(f"{context_id} has TRANSL with non-ISO-639-3-looking xml:lang: {lang!r}")
    if len(element):
        errors.append(f"{context_id} has TRANSL with child elements")
    if not text_of(element):
        errors.append(f"{context_id} has empty TRANSL")
    return errors


def validate_audio(element: ET.Element, context_id: str) -> list[str]:
    errors: list[str] = []
    extra = extra_attrs(element, AUDIO_ATTRS)
    if extra:
        errors.append(f"{context_id} has AUDIO with unsupported attributes: {', '.join(sorted(extra))}")
    if "start" not in element.attrib or "end" not in element.attrib:
        errors.append(f"{context_id} has AUDIO without start/end")
    if len(element) or text_of(element):
        errors.append(f"{context_id} has non-empty AUDIO element")
    return errors


def validate_morpheme(morpheme: ET.Element, seen_ids: set[str], word_id: str) -> list[str]:
    errors: list[str] = []
    if morpheme.tag != "M":
        return [f"{word_id} can only contain M morpheme children after FORM/TRANSL/AUDIO, got {morpheme.tag!r}"]

    m_id = morpheme.attrib.get("id")
    if set(morpheme.attrib) != {"id"}:
        errors.append(f"{word_id} has M with attributes other than id")
    if not m_id:
        errors.append(f"{word_id} has M without id")
        m_id = f"{word_id}/M-without-id"
    elif m_id in seen_ids:
        errors.append(f"Duplicate id: {m_id}")
    else:
        seen_ids.add(m_id)

    forms = [el for el in morpheme if el.tag == "FORM"]
    if not forms:
        errors.append(f"{m_id} is missing FORM")
    for child in morpheme:
        if child.tag == "FORM":
            errors.extend(validate_form(child, m_id))
        elif child.tag == "TRANSL":
            errors.extend(validate_translation(child, m_id))
        elif child.tag == "AUDIO":
            errors.extend(validate_audio(child, m_id))
        else:
            errors.append(f"{m_id} has unsupported child {child.tag!r}")
    return errors


def validate_word(word: ET.Element, seen_ids: set[str], sentence_id: str) -> list[str]:
    errors: list[str] = []
    if word.tag != "W":
        return [f"{sentence_id} can only contain W word children after FORM/TRANSL/AUDIO, got {word.tag!r}"]

    w_id = word.attrib.get("id")
    if set(word.attrib) != {"id"}:
        errors.append(f"{sentence_id} has W with attributes other than id")
    if not w_id:
        errors.append(f"{sentence_id} has W without id")
        w_id = f"{sentence_id}/W-without-id"
    elif w_id in seen_ids:
        errors.append(f"Duplicate id: {w_id}")
    else:
        seen_ids.add(w_id)

    forms = [el for el in word if el.tag == "FORM"]
    if not forms:
        errors.append(f"{w_id} is missing FORM")

    for child in word:
        if child.tag == "FORM":
            errors.extend(validate_form(child, w_id))
        elif child.tag == "TRANSL":
            errors.extend(validate_translation(child, w_id))
        elif child.tag == "AUDIO":
            errors.extend(validate_audio(child, w_id))
        elif child.tag == "M":
            errors.extend(validate_morpheme(child, seen_ids, w_id))
        else:
            errors.append(f"{w_id} has unsupported child {child.tag!r}")
    return errors


def validate_sentence(sentence: ET.Element, seen_ids: set[str]) -> list[str]:
    errors: list[str] = []
    s_id = sentence.attrib.get("id")
    if set(sentence.attrib) != {"id"}:
        errors.append("S has attributes other than id")
    if not s_id:
        errors.append("S is missing id")
        s_id = "S-without-id"
    elif s_id in seen_ids:
        errors.append(f"Duplicate id: {s_id}")
    else:
        seen_ids.add(s_id)

    forms = [el for el in sentence if el.tag == "FORM"]
    if not forms:
        errors.append(f"{s_id} is missing sentence FORM")
    # TRANSL is optional in FormosanBank's schema (S_Type is an xs:choice with
    # minOccurs="0"), so a sentence with a FORM and no translation is valid.

    for child in sentence:
        if child.tag == "FORM":
            errors.extend(validate_form(child, s_id))
        elif child.tag == "TRANSL":
            errors.extend(validate_translation(child, s_id))
        elif child.tag == "AUDIO":
            errors.extend(validate_audio(child, s_id))
        elif child.tag == "W":
            errors.extend(validate_word(child, seen_ids, s_id))
        else:
            errors.append(f"{s_id} has unsupported child {child.tag!r}")
    return errors


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    root = ET.parse(path).getroot()

    if root.tag != "TEXT":
        errors.append(f"Root element must be TEXT, got {root.tag!r}")
        return errors

    missing = REQUIRED_TEXT_ATTRS.difference(root.attrib)
    if missing:
        errors.append(f"TEXT is missing required attributes: {', '.join(sorted(missing))}")

    seen_ids: set[str] = set()
    for child in root:
        if child.tag != "S":
            errors.append(f"TEXT can only contain S children, got {child.tag!r}")
            continue
        errors.extend(validate_sentence(child, seen_ids))

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xml", type=Path, nargs="+")
    args = parser.parse_args()

    all_errors: list[str] = []
    for xml_path in args.xml:
        all_errors.extend(f"{xml_path}: {error}" for error in validate(xml_path))

    if all_errors:
        for error in all_errors:
            print(error, file=sys.stderr)
        raise SystemExit(1)

    for xml_path in args.xml:
        sentence_count = sum(1 for child in ET.parse(xml_path).getroot() if child.tag == "S")
        print(f"Validated {xml_path} ({sentence_count} S elements)")


if __name__ == "__main__":
    main()
