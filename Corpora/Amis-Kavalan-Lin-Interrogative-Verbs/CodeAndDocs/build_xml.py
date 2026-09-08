#!/usr/bin/env python3
"""Build FormosanBank XML from Lin 2015 Amis/Kavalan numbered examples.

The source PDF has a usable text layer, but the article interleaves positive
examples, starred/marginal contrasts, theoretical trees, and non-target
examples. The page-checked transcription is in extracted_examples.tsv.
Rebuilds never overwrite source evidence.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from xml.dom import minidom
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
XML_ROOT = ROOT / "XML"
ACCEPTED_TSV = ROOT / "CodeAndDocs" / "extracted_examples.tsv"

XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("xml", XML_NS)

CITATION = (
    "Lin, Dong-yi. 2015. The syntactic derivations of interrogative verbs in "
    "Amis and Kavalan. In Elizabeth Zeitoun, Stacy F. Teng, and Joy J. Wu "
    "(eds.), New Advances in Formosan Linguistics, 253-289. Asia-Pacific "
    "Linguistics."
)
BIBTEX = (
    "@incollection{lin2015AmisKavalanInterrogativeVerbs,"
    "title={The syntactic derivations of interrogative verbs in Amis and Kavalan},"
    "author={Lin, Dong-yi},"
    "booktitle={New Advances in Formosan Linguistics},"
    "editor={Zeitoun, Elizabeth and Teng, Stacy F. and Wu, Joy J.},"
    "pages={253--289},"
    "publisher={Asia-Pacific Linguistics},"
    "year={2015}}"
)
SOURCE = "https://hdl.handle.net/1885/14354; Lin (2015), pp. 253-289"
COPYRIGHT = "CC BY 4.0"

LANGUAGES = {
    "Amis": {
        "xml_lang": "ami",
        "dialect": "Xiuguluan",
        "glottocode": "nat1254",
        "source_dialect": "Central Amis, Changpin village, Taitung County",
    },
    "Kavalan": {
        "xml_lang": "ckv",
        "dialect": "Kavalan",
        "glottocode": "kava1241",
        "source_dialect": "Hsinshe Kavalan, Hsinshe village, Hualien County",
    },
}


@dataclass(frozen=True)
class Example:
    language: str
    source_id: str
    printed_page: int
    form: str
    gloss: str
    translation: str
    note: str = ""
    xml_id: str = ""
    readings: tuple[str, ...] = ()

    @property
    def pdf_page(self) -> int:
        return self.printed_page - 252

    @property
    def printed(self) -> str:
        return self.form



@dataclass(frozen=True)
class FormVariant:
    id_suffix: str
    label: str
    form: str
    aligned_form: str
    gloss: str


def read_source() -> tuple[list[Example], dict[tuple[str, str], str]]:
    examples = []
    repeats = {}
    seen = set()
    canonical_ids = set()
    with ACCEPTED_TSV.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            key = row["language"], row["source_id"]
            if key in seen:
                raise ValueError(f"Duplicate source occurrence: {key}")
            seen.add(key)
            readings = json.loads(row["translation_readings_eng_json"])
            if not isinstance(readings, list) or any(not isinstance(x, str) for x in readings):
                raise ValueError(f"Invalid translation readings: {key}")
            example = Example(row["language"], row["source_id"], int(row["printed_page"]),
                              row["source_form"], row["gloss"], row["source_translation_eng"],
                              row["source_note"], xml_id=row["xml_id"], readings=tuple(readings))
            if row["admission_status"] not in ("admitted", "excluded"):
                raise ValueError(f"Unknown admission status: {key}")
            marked = example.printed.startswith(("* ", "? "))
            if marked != (row["admission_status"] == "excluded"):
                raise ValueError(f"Admission contradicts the source marker: {key}")
            if int(row["pdf_page"]) != example.pdf_page:
                raise ValueError(f"Inconsistent page locator: {key}")
            canonical = row["xml_record_source_id"]
            if marked:
                if canonical or example.xml_id:
                    raise ValueError(f"Excluded occurrence has an XML identity: {key}")
            elif not canonical or not example.xml_id:
                raise ValueError(f"Missing immutable source identity: {key}")
            elif canonical != example.source_id:
                repeats[key] = canonical
            elif example.xml_id in canonical_ids:
                raise ValueError(f"Duplicate XML identity: {example.xml_id}")
            else:
                canonical_ids.add(example.xml_id)
            examples.append(example)
    by_key = {(e.language, e.source_id): e for e in examples}
    for key, target in repeats.items():
        if by_key[key].xml_id != by_key[(key[0], target)].xml_id:
            raise ValueError(f"Repeat identity differs from canonical occurrence: {key}")
    return examples, repeats


EXAMPLES, REPEAT_TARGETS = read_source()


WORD_EDGE_CHARS = '*,.;:!?…[]{}"“”‘’'


def exclusion_reason(example: Example) -> str:
    """Return the current intake-policy reason for excluding a source example."""
    if example.printed.startswith("* "):
        return "source-marked ungrammatical example excluded under POL-016"
    if example.printed.startswith("? "):
        return "source-marked marginal example excluded under POL-016"
    return ""


def admitted_examples() -> list[Example]:
    """Return source examples eligible for generated corpus XML."""
    return [example for example in EXAMPLES if not exclusion_reason(example)]


def source_order(item: Example) -> tuple[int, str, str]:
    match = re.fullmatch(r"(\d+)([a-z]?)", item.source_id)
    if match is None:
        raise ValueError(f"Unexpected source ID: {item.source_id}")
    return int(match.group(1)), match.group(2), item.language


def prettify(root: ET.Element) -> str:
    xml = ET.tostring(root, encoding="utf-8")
    parsed = minidom.parseString(xml)
    lines = parsed.toprettyxml(indent="    ").splitlines()
    return "\n".join(line for line in lines if line.strip()) + "\n"


def lexical_tokens(text: str) -> list[str]:
    """Return source words without sentence or constituent-edge punctuation."""
    tokens: list[str] = []
    for raw_token in text.split():
        token = raw_token.strip(WORD_EDGE_CHARS)
        if token:
            tokens.append(
                token.replace("(", "")
                .replace(")", "")
                .replace("‹", "<")
                .replace("›", ">")
            )
    return tokens


def normalize_source_form(text: str, *, preserve_infix: bool = False) -> str:
    """Normalize source notation without changing source spelling."""
    normalized = (
        text.removeprefix("* ")
        .removeprefix("? ")
        .replace("‘", "'")
        .replace("’", "'")
        .replace("[", "")
        .replace("]", "")
    )
    if preserve_infix:
        normalized = normalized.replace("‹", "<").replace("›", ">")
    else:
        normalized = normalized.replace("‹", "").replace("›", "")
    return re.sub(r"\s+", " ", normalized).strip()


def form_variants(example: Example) -> tuple[FormVariant, ...]:
    """Expand one optional source constituent into aligned S variants."""
    source = example.printed.removeprefix("* ").removeprefix("? ")
    optional = re.search(r"\(([^()]*)\)", source)
    if optional is None:
        return (
            FormVariant(
                "",
                "source form",
                normalize_source_form(source),
                normalize_source_form(source, preserve_infix=True),
                example.gloss,
            ),
        )

    included_source = source[: optional.start()] + optional.group(1) + source[optional.end() :]
    omitted_source = source[: optional.start()] + source[optional.end() :]
    included = normalize_source_form(included_source)
    omitted = normalize_source_form(omitted_source)
    included_aligned = normalize_source_form(included_source, preserve_infix=True)
    omitted_aligned = normalize_source_form(omitted_source, preserve_infix=True)
    included_words = lexical_tokens(included_aligned)
    omitted_words = lexical_tokens(omitted_aligned)
    included_glosses = lexical_tokens(example.gloss)
    omitted_glosses = included_glosses.copy()

    if len(included_words) == len(omitted_words) + 1:
        difference = next(
            index
            for index, word in enumerate(included_words)
            if index >= len(omitted_words) or word != omitted_words[index]
        )
        if len(included_glosses) != len(included_words):
            raise ValueError(
                f"Cannot align optional gloss for {example.language} {example.source_id}"
            )
        omitted_glosses.pop(difference)
    elif len(included_words) != len(omitted_words):
        raise ValueError(
            f"Unsupported optional form shape for {example.language} {example.source_id}"
        )

    return (
        FormVariant(
            "",
            "optional material included",
            included,
            included_aligned,
            example.gloss,
        ),
        FormVariant(
            "_OPT0",
            "optional material omitted",
            omitted,
            omitted_aligned,
            " ".join(omitted_glosses),
        ),
    )


def alignment_words(variant: FormVariant) -> tuple[list[tuple[str, str]], str]:
    """Return source-supported word/gloss pairs or an explicit omission reason."""
    if not variant.gloss:
        return [], "source supplies no gloss"
    if "/" in variant.aligned_form or "/" in variant.gloss:
        return [], "source presents unresolved slash alternatives"
    form_words = lexical_tokens(variant.aligned_form)
    gloss_words = lexical_tokens(variant.gloss)
    if len(form_words) != len(gloss_words):
        return [], f"word/gloss token count differs ({len(form_words)} != {len(gloss_words)})"
    return list(zip(form_words, gloss_words, strict=True)), ""


def morpheme_parts(token: str, *, mark_infix: bool) -> list[str]:
    parts: list[str] = []
    for component in re.split(r"[-=]", token):
        if not component:
            continue
        infixes = re.findall(r"<([^<>]+)>", component)
        base = re.sub(r"<[^<>]+>", "-" if mark_infix else "", component)
        if base:
            parts.append(base)
        parts.extend(f"-{infix}-" if mark_infix else infix for infix in infixes)
    return parts


def marker_skeleton(token: str) -> str:
    return "".join(char for char in token if char in "-=<>")


def aligned_morphemes(form_token: str, gloss_token: str) -> tuple[list[str], list[str]]:
    """Align only segmentation that is explicit and one-to-one in the source."""
    if "/" in form_token or "/" in gloss_token:
        return [], []
    if marker_skeleton(form_token) != marker_skeleton(gloss_token):
        return [], []

    form_components = form_token.split("=")
    gloss_components = gloss_token.split("=")
    if len(form_components) != len(gloss_components):
        return [], []

    form_parts_by_component = [
        morpheme_parts(component, mark_infix=True) for component in form_components
    ]
    gloss_parts_by_component = [
        morpheme_parts(component, mark_infix=False) for component in gloss_components
    ]
    if any(
        len(form_parts) != len(gloss_parts)
        for form_parts, gloss_parts in zip(
            form_parts_by_component, gloss_parts_by_component, strict=True
        )
    ):
        return [], []

    for component_index in range(1, len(form_parts_by_component)):
        form_parts_by_component[component_index][0] = (
            "=" + form_parts_by_component[component_index][0]
        )

    form_parts = [part for component in form_parts_by_component for part in component]
    gloss_parts = [part for component in gloss_parts_by_component for part in component]
    return form_parts, gloss_parts


def add_word_tiers(sentence: ET.Element, variant: FormVariant) -> str:
    """Add every safe printed W/M alignment and return an omission reason, if any."""
    word_pairs, reason = alignment_words(variant)
    if reason:
        if variant.gloss:
            raise ValueError(f"Unresolved source alignment: {reason}: {variant.aligned_form!r}")
        return reason

    analyses = [
        aligned_morphemes(form_word, gloss_word)
        for form_word, gloss_word in word_pairs
    ]
    sentence_is_parsed = any(len(forms) >= 2 for forms, _ in analyses)

    for word_index, ((form_word, gloss_word), (form_morphemes, gloss_morphemes)) in enumerate(
        zip(word_pairs, analyses, strict=True), start=1
    ):
        word = ET.SubElement(
            sentence,
            "W",
            {"id": f"{sentence.attrib['id']}_W{word_index:02d}"},
        )
        ET.SubElement(word, "FORM", {"kindOf": "original"}).text = form_word
        ET.SubElement(
            word,
            "TRANSL",
            {"kindOf": "original", f"{{{XML_NS}}}lang": "eng"},
        ).text = gloss_word

        if not form_morphemes and any(mark in form_word for mark in "-=<>"):
            raise ValueError(f"Unresolved segmented alignment: {word.attrib['id']} {form_word!r} / {gloss_word!r}")
        if sentence_is_parsed and len(form_morphemes) < 2:
            form_morphemes = [form_word]
            gloss_morphemes = [gloss_word]
        if not sentence_is_parsed or len(form_morphemes) != len(gloss_morphemes):
            continue
        for morph_index, (form_morph, gloss_morph) in enumerate(
            zip(form_morphemes, gloss_morphemes, strict=True), start=1
        ):
            morph = ET.SubElement(
                word,
                "M",
                {"id": f"{word.attrib['id']}_M{morph_index:02d}"},
            )
            ET.SubElement(morph, "FORM", {"kindOf": "original"}).text = form_morph
            ET.SubElement(
                morph,
                "TRANSL",
                {"kindOf": "original", f"{{{XML_NS}}}lang": "eng"},
            ).text = gloss_morph
    return ""


def make_text(language: str, examples: list[Example]) -> ET.Element:
    info = LANGUAGES[language]
    root = ET.Element(
        "TEXT",
        {
            "id": f"lin_2015_{language.lower()}_interrogative_verbs",
            f"{{{XML_NS}}}lang": info["xml_lang"],
            "dialect": info["dialect"],
            "glottocode": info["glottocode"],
            "source": (
                f"{SOURCE}; source dialect note: {info['source_dialect']}; "
                "sentence examples extracted from numbered examples"
            ),
            "copyright": COPYRIGHT,
            "citation": CITATION,
            "BibTeX_citation": BIBTEX,
        },
    )
    canonical = [
        example
        for example in examples
        if (example.language, example.source_id) not in REPEAT_TARGETS
    ]
    for example in sorted(canonical, key=source_order):
        occurrences = [
            item
            for item in examples
            if item.source_id == example.source_id
            or REPEAT_TARGETS.get((item.language, item.source_id)) == example.source_id
        ]
        occurrence_note = ", ".join(
            f"{item.source_id} (printed p. {item.printed_page}; PDF page {item.pdf_page})"
            for item in sorted(occurrences, key=source_order)
        )
        label = "example" if len(occurrences) == 1 else "source occurrences"
        note = f"{label} {occurrence_note}"
        if len(occurrences) > 1:
            note = f"{note}; repeated reference example represented by one S"
        if example.note:
            note = f"{note}; {example.note}"
        variants = form_variants(example)
        for variant in variants:
            variant_note = note
            if len(variants) > 1:
                variant_note = f"{note}; {variant.label} under POL-026"
            sentence = ET.SubElement(
                root,
                "S",
                {
                    "id": f"{example.xml_id}{variant.id_suffix}",
                    "source": variant_note,
                },
            )
            ET.SubElement(sentence, "FORM", {"kindOf": "original"}).text = variant.form
            for reading_index, reading in enumerate(example.readings):
                attributes = {f"{{{XML_NS}}}lang": "eng"}
                if reading_index:
                    attributes["ver"] = "alt"
                ET.SubElement(sentence, "TRANSL", attributes).text = reading
            add_word_tiers(sentence, variant)
    return root


def write_xml() -> None:
    by_language: dict[str, list[Example]] = {}
    for example in admitted_examples():
        by_language.setdefault(example.language, []).append(example)

    for language, examples in sorted(by_language.items()):
        language_dir = XML_ROOT / language
        language_dir.mkdir(parents=True, exist_ok=True)
        out_path = language_dir / f"lin_2015_{language.lower()}_interrogative_verbs.xml"
        out_path.write_text(prettify(make_text(language, examples)), encoding="utf-8")


def restore_brackets() -> None:
    """Restore source constituent brackets after deriving marker-free sentence tiers."""
    for path in sorted(XML_ROOT.rglob("*.xml")):
        tree = ET.parse(path)
        root = tree.getroot()
        expected = {e.xml_id: e.printed for e in EXAMPLES if e.printed.startswith("[")}
        changed = False
        for sentence in root.findall("S"):
            original = expected.get(sentence.get("id"))
            if original is None:
                continue
            form = sentence.find("FORM[@kindOf='original']")
            cleaned = original.replace("[", "").replace("]", "")
            if form is None or form.text not in (original, cleaned):
                raise ValueError(f"Unexpected bracket cleanup: {sentence.get('id')}")
            form.text = original
            changed = True
        if changed:
            path.write_text(prettify(root), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore-brackets", action="store_true")
    args = parser.parse_args()
    if args.restore_brackets:
        restore_brackets()
    else:
        write_xml()
