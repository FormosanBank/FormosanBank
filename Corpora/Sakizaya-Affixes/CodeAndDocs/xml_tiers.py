"""Helpers for emitting FormosanBank-style S/W/M XML tiers."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET


XML_NS = "http://www.w3.org/XML/1998/namespace"

MERGED_GLOSS_ATOMS = [
    "我們.屬格",
    "我們.主格",
    "你們.屬格",
    "你們.主格",
    "我.屬格",
    "我.主格",
    "你.屬格",
    "你.主格",
    "處所格",
    "普名標記",
    "完成貌",
    "主格",
    "屬格",
    "斜格",
    "受格",
    "人名",
    "繫詞",
    "助詞",
    "所以",
    "已經",
    "現在",
]


def word_tokens(text: str) -> list[str]:
    return [part for part in re.split(r"\s+", text.strip()) if part]


def word_surface_form(text: str, *, sentence_final: bool = False) -> str:
    """Remove sentence punctuation from the final W-level token only."""

    if not sentence_final:
        return text
    return re.sub(r"[.,!?;:。！？；：]+$", "", text)


def gloss_tokens(text: str, expected_count: int) -> list[str]:
    cleaned = re.sub(r"\s*/\s*", " ", text.strip())
    tokens = [part for part in re.split(r"\s+", cleaned) if part]
    if len(tokens) == expected_count:
        return tokens
    expanded: list[str] = []
    for token in tokens:
        expanded.extend(split_merged_gloss_token(token))
    return expanded if len(expanded) == expected_count else []


def split_merged_gloss_token(text: str) -> list[str]:
    pieces: list[str] = []
    pos = 0
    buffer = ""
    while pos < len(text):
        matched = ""
        for atom in MERGED_GLOSS_ATOMS:
            if not text.startswith(atom, pos):
                continue
            # Do not split inside a hyphenated morpheme gloss such as m-我.屬格.
            if pos > 0 and text[pos - 1] in "-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz":
                continue
            matched = atom
            break
        if matched:
            if buffer:
                pieces.append(buffer)
                buffer = ""
            pieces.append(matched)
            pos += len(matched)
        else:
            buffer += text[pos]
            pos += 1
    if buffer:
        pieces.append(buffer)
    return pieces if len(pieces) > 1 else [text]


def morpheme_surface_parts(text: str) -> list[str]:
    core = text.strip()
    core = re.sub(r'^[（(「『"“”]+', "", core)
    core = re.sub(r'[.,!?;:。！？；：「」『』"“”）)]+$', "", core)
    if not core:
        return []
    if "-" not in core and "=" not in core:
        return [core]
    pieces = [piece for piece in re.split(r"[-=]", core) if piece]
    return pieces if pieces else [core]


def morpheme_gloss_parts(text: str) -> list[str]:
    if "-" not in text and "=" not in text:
        return [text]
    pieces = [piece for piece in re.split(r"[-=]", text) if piece]
    return pieces if pieces else [text]


def add_form_pair(
    parent: ET.Element,
    original_text: str,
    standard_text: str | None = None,
    *,
    original_notes: str = "",
) -> None:
    original_attrs = {"kindOf": "original"}
    if original_notes:
        original_attrs["notes"] = original_notes
    original = ET.SubElement(parent, "FORM", original_attrs)
    original.text = original_text
    if standard_text is not None:
        standard = ET.SubElement(parent, "FORM", {"kindOf": "standard"})
        standard.text = standard_text


def add_translation(
    parent: ET.Element,
    text: str,
    *,
    lang: str = "zho",
    kind_of: str = "",
    ver: str = "",
    notes: str = "",
) -> None:
    attrs = {f"{{{XML_NS}}}lang": lang}
    if kind_of:
        attrs["kindOf"] = kind_of
    if ver:
        attrs["ver"] = ver
    if notes:
        attrs["notes"] = notes
    translation = ET.SubElement(parent, "TRANSL", attrs)
    translation.text = text


def add_word_tiers(
    sentence: ET.Element,
    sentence_id: str,
    form_text: str,
    source_gloss: str = "",
    aligned_glosses: list[str] | None = None,
) -> None:
    words = word_tokens(form_text)
    if aligned_glosses is None:
        aligned_glosses = gloss_tokens(source_gloss, len(words)) if source_gloss else []
    if aligned_glosses and len(aligned_glosses) != len(words):
        raise ValueError(
            f"Expected {len(words)} aligned gloss cells for {sentence_id}; "
            f"received {len(aligned_glosses)}"
        )
    for word_index, word in enumerate(words, 1):
        surface_word = word_surface_form(
            word,
            sentence_final=word_index == len(words),
        )
        word_el = ET.SubElement(sentence, "W", {"id": f"{sentence_id}W{word_index}"})
        add_form_pair(word_el, surface_word)

        word_gloss = aligned_glosses[word_index - 1] if aligned_glosses else ""
        if not word_gloss:
            continue
        add_translation(word_el, word_gloss, kind_of="original")

        morphemes = morpheme_surface_parts(surface_word)
        glosses = morpheme_gloss_parts(word_gloss)
        if len(morphemes) != len(glosses):
            continue
        for morph_index, (morpheme, gloss) in enumerate(zip(morphemes, glosses), 1):
            morph_el = ET.SubElement(word_el, "M", {"id": f"{sentence_id}W{word_index}M{morph_index}"})
            add_form_pair(morph_el, morpheme)
            add_translation(morph_el, gloss, kind_of="original")


def add_single_word_tier(
    sentence: ET.Element,
    sentence_id: str,
    form_text: str,
    translation_text: str,
    *,
    original_notes: str = "",
) -> None:
    word_el = ET.SubElement(sentence, "W", {"id": f"{sentence_id}W1"})
    add_form_pair(
        word_el,
        form_text,
        original_notes=original_notes,
    )
    add_translation(word_el, translation_text, kind_of="original")
