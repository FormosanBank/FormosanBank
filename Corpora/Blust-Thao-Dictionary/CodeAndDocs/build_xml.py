#!/usr/bin/env python3
"""Build source-owned FormosanBank XML from the reviewed Thao records."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET


_FB = os.environ.get("FORMOSANBANK_PATH")
if _FB:
    sys.path.insert(0, _FB)
else:
    for _parent in Path(__file__).resolve().parents:
        if (_parent / "QC" / "utilities" / "parentheticals.py").is_file():
            sys.path.insert(0, str(_parent))
            break
from QC.utilities.parentheticals import take_notes  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

#: Thao words that are optional so often, and carry so little, that bracketing
#: one says nothing about the English beside it, so the two never pair
#: (maintainer, 2026-09-11). Both builders use it, and they must use the same
#: one or the same printed example reads differently in the two trees.
THAO_PARTICLES = frozenset({"tu", "sa", "a", "ya", "wa"})

DATA_PATH = ROOT / "CodeAndDocs" / "expanded-records.json"
DEFAULT_OUTPUT = ROOT / "XML" / "Thao"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

CITATION = (
    "Blust, Robert. 2003. Thao Dictionary. Language and Linguistics "
    "Monograph Series A5. Taipei: Institute of Linguistics (Preparatory "
    "Office), Academia Sinica."
)
BIBTEX = (
    "@book{blust2003thao, author={Blust, Robert}, year={2003}, "
    "title={Thao Dictionary}, series={Language and Linguistics Monograph "
    "Series A5}, publisher={Institute of Linguistics (Preparatory Office), "
    "Academia Sinica}, address={Taipei}}"
)
# POL-042: exactly one value from FormosanBank's rights_vocabulary.csv. The
# permission behind it (Institute of Linguistics, Academia Sinica, 2024-01-30)
# is documented in the README's Rights section, never in the attribute.
COPYRIGHT = "CC BY-NC 4.0"
CATALOG_URL = (
    "https://www.ling.sinica.edu.tw/item/en?act=publish_book&bookID=97&code=view"
)
PDF_URL = (
    "https://www.ling.sinica.edu.tw/item/en?act=publish_book&article_id=446"
    "&code=download&type=article"
)
BASECAMP_CARD = "7012450955"

DICTIONARY_PARTS = (
    (280, 379),
    (380, 479),
    (480, 579),
    (580, 679),
    (680, 779),
    (780, 879),
    (880, 979),
    (980, 1068),
)

LETTER_RUN = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)*'?", re.UNICODE)

# The reviewed sentence count after expansion. A build that produces a
# different number has either gained or lost source material and stops.
# 8,818 until the 21 records whose bracket sits INSIDE a word stopped
# splitting: those are one lexeme spelt two ways, so they are one sentence
# with a ver="alt" FORM rather than two (maintainer, 2026-09-11).
EXPECTED_SENTENCES = 8797


def page_list(pages: list[int]) -> str:
    """Render sorted pages as stable comma-separated ranges."""
    ordered = sorted(set(pages))
    if not ordered:
        return ""
    ranges: list[str] = []
    start = previous = ordered[0]
    for page in ordered[1:]:
        if page == previous + 1:
            previous = page
            continue
        ranges.append(str(start) if start == previous else f"{start}-{previous}")
        start = previous = page
    ranges.append(str(start) if start == previous else f"{start}-{previous}")
    return ",".join(ranges)


def attested_unquoted_tokens(data: dict[str, object]) -> set[str]:
    """Collect printed word-final glottals outside backtick quotations."""
    forms = [
        str(sentence["form"])
        for text in data["texts"]
        for sentence in text["sentences"]
    ]
    forms.extend(str(record["source"]) for record in data["dictionary_examples"])
    return {
        match.group().casefold()
        for form in forms
        if "`" not in form
        for match in LETTER_RUN.finditer(form)
    }


def _candidate_token(value: str, apostrophe: int) -> str:
    start = apostrophe - 1
    while start >= 0 and value[start].isalpha():
        start -= 1
    return value[start + 1 : apostrophe + 1].casefold()


def normalize_blust_quotes(value: str, attested: set[str]) -> str:
    """Map Blust's backtick/single-quote typography to semantic double quotes.

    A backtick is always an opening quotation mark in this source. Within each
    backtick span, the last non-internal apostrophe is a closing mark unless its
    word-final form is independently attested outside quotations. That guard
    preserves lexical glottal stops such as qriu'.
    """
    openers = [index for index, character in enumerate(value) if character == "`"]
    if not openers:
        return value
    replacements = set(openers)
    for opener_number, opener in enumerate(openers):
        boundary = (
            openers[opener_number + 1]
            if opener_number + 1 < len(openers)
            else len(value)
        )
        candidates: list[int] = []
        for index in range(opener + 1, boundary):
            if value[index] != "'":
                continue
            left = value[index - 1] if index else ""
            right = value[index + 1] if index + 1 < len(value) else ""
            if left in ".,;:?!":
                candidates.append(index)
            elif (left.isalpha() or left.isdigit()) and not right.isalpha():
                if not left.isalpha() or _candidate_token(value, index) not in attested:
                    candidates.append(index)
        if candidates:
            replacements.add(candidates[-1])
    return "".join('"' if index in replacements else char for index, char in enumerate(value))


def normalize_aligned_gloss(raw_form: str, normalized_form: str, gloss: str) -> str:
    """Mirror source-word quote replacements in its printed whole-word gloss."""
    result = gloss
    if "`" in raw_form and '"' in normalized_form:
        result = result.replace("`", '"')
    if any(
        before == "'" and after == '"'
        for before, after in zip(raw_form, normalized_form, strict=True)
    ):
        candidates = []
        for index, character in enumerate(result):
            if character != "'":
                continue
            left = result[index - 1] if index else ""
            right = result[index + 1] if index + 1 < len(result) else ""
            if left in ".,;:?!" or (
                (left.isalpha() or left.isdigit()) and not right.isalpha()
            ):
                candidates.append(index)
        if candidates:
            index = candidates[-1]
            result = result[:index] + '"' + result[index + 1 :]
    return result


def _note_label(note: str) -> str:
    """How a note reads once it is out of the translation."""
    head = note.split(None, 1)[0].lower() if note.split() else ""
    if head in {"lit.", "literally"}:
        rest = note.split(None, 1)[1] if len(note.split(None, 1)) > 1 else ""
        return f"Literal translation: {rest}"
    return f"Source note: {note}"


def translation_tiers(
    value: str, source: str = ""
) -> list[tuple[str, str | None]]:
    """Source translation alternatives, with the editorial parentheses lifted out.

    Which parentheses those are is QC/utilities/parentheticals.py's decision,
    not this corpus's: an opening marker (`lit.`, `answer to`, `said`) or, for
    anything with no counterpart in the Thao, length. A parenthetical that
    pairs with one in the source belongs to the example and is never taken.
    """
    value = normalize_blust_quotes(value, set())
    parts = [part.strip() for part in value.split("==")]
    if not parts or any(not part for part in parts):
        raise ValueError(f"empty same-language translation alternative: {value!r}")
    tiers = []
    for part in parts:
        kept, notes = take_notes(source, part, never_pairs=THAO_PARTICLES)
        if not kept:
            raise ValueError(f"translation is nothing but notes: {part!r}")
        tiers.append(
            (kept, " | ".join(_note_label(note) for note in notes) or None)
        )
    return tiers


def text_root(text_id: str, source: str) -> ET.Element:
    return ET.Element(
        "TEXT",
        {
            "id": text_id,
            "citation": CITATION,
            "BibTeX_citation": BIBTEX,
            "copyright": COPYRIGHT,
            XML_LANG: "ssf",
            "source": source,
            "glottocode": "thao1240",
            "dialect": "Thao",
        },
    )


def add_translation(
    parent: ET.Element,
    value: str,
    *,
    alternate: bool = False,
    notes: str | None = None,
) -> None:
    attributes = {XML_LANG: "eng"}
    if alternate:
        attributes["ver"] = "alt"
    if notes:
        attributes["notes"] = notes
    translation = ET.SubElement(parent, "TRANSL", attributes)
    translation.text = value


def text_sentence_id(text_number: int, sentence: dict[str, object]) -> str:
    base = f"blust-text-t{text_number:02d}-s{int(sentence['number']):03d}"
    suffix = str(sentence.get("variant_suffix", ""))
    return f"{base}-{suffix}" if suffix else base


def build_text(
    record: dict[str, object],
    attested: set[str],
) -> tuple[str, ET.ElementTree]:
    number = int(record["number"])
    source_pdf_pages = [int(page) for page in record["source_pdf_pages"]]
    translation_pdf_pages = [
        int(page) for page in record["translation_pdf_pages"]
    ]
    source_printed = [page - 10 for page in source_pdf_pages]
    translation_printed = [page - 10 for page in translation_pdf_pages]
    text_id = f"blust_2003_thao_text_{number:02d}"
    source = (
        f"Blust 2003, {record['title']!s}; source printed pp. "
        f"{page_list(source_printed)} (PDF pp. {page_list(source_pdf_pages)}); "
        f"English printed pp. {page_list(translation_printed)} "
        f"(PDF pp. {page_list(translation_pdf_pages)}); {PDF_URL}; "
        f"Basecamp card {BASECAMP_CARD}"
    )
    root = text_root(text_id, source)
    for sentence_record in record["sentences"]:
        sentence = sentence_record
        sentence_id = text_sentence_id(number, sentence)
        source_pages = [int(page) for page in sentence["source_pdf_pages"]]
        translation_pages = [
            int(page) for page in sentence["translation_pdf_pages"]
        ]
        locator = (
            f"text {number}, sentence {int(sentence['number'])}; source printed "
            f"pp. {page_list([page - 10 for page in source_pages])} "
            f"(PDF pp. {page_list(source_pages)}); English printed pp. "
            f"{page_list([page - 10 for page in translation_pages])} "
            f"(PDF pp. {page_list(translation_pages)})"
        )
        if sentence.get("variant_suffix"):
            locator += f"; expansion {sentence['variant_suffix']}"
        sentence_element = ET.SubElement(
            root,
            "S",
            {"id": sentence_id, "source": locator},
        )
        raw_form = str(sentence["form"])
        normalized_form = normalize_blust_quotes(raw_form, attested)
        original = ET.SubElement(sentence_element, "FORM", {"kindOf": "original"})
        original.text = normalized_form
        for index, (translation, notes) in enumerate(
            translation_tiers(str(sentence["translation"]), str(sentence["form"]))
        ):
            add_translation(
                sentence_element,
                translation,
                alternate=index > 0,
                notes=notes,
            )
        raw_word_forms = [str(word["form"]) for word in sentence["words"]]
        normalized_word_forms = normalize_blust_quotes(
            " ".join(raw_word_forms), attested
        ).split(" ")
        if len(normalized_word_forms) != len(raw_word_forms):
            raise ValueError(f"quote normalization changed word count in {sentence_id}")
        if " ".join(normalized_word_forms) != normalized_form:
            raise ValueError(f"sentence/word quote normalization differs in {sentence_id}")
        for word_number, (word, normalized_word) in enumerate(
            zip(sentence["words"], normalized_word_forms, strict=True),
            start=1,
        ):
            word_element = ET.SubElement(
                sentence_element,
                "W",
                {"id": f"{sentence_id}-w{word_number:03d}"},
            )
            word_form = ET.SubElement(word_element, "FORM", {"kindOf": "original"})
            word_form.text = normalized_word
            if word["gloss"] is not None:
                add_translation(
                    word_element,
                    normalize_aligned_gloss(
                        str(word["form"]), normalized_word, str(word["gloss"])
                    ),
                    # A printed footnote on this word: Blust's own commentary on
                    # the gloss, kept beside it rather than inline (POL-024).
                    notes=(
                        f"Source footnote: {word['note']}"
                        if word.get("note")
                        else None
                    ),
                )
    ET.indent(root, space="    ")
    return f"blust_2003_thao_text_{number:02d}.xml", ET.ElementTree(root)


def expansion_description(record: dict[str, object]) -> str:
    expansion = record["expansion"]
    labels: list[str] = []
    if expansion["slash_option"] is not None:
        labels.append(f"slash option {int(expansion['slash_option'])}")
    labels.extend(str(label) for label in expansion["optional_choices"])
    return "; ".join(labels)


def build_dictionary_part(
    start_page: int,
    end_page: int,
    records: list[dict[str, object]],
    attested: set[str],
) -> tuple[str, ET.ElementTree]:
    text_id = f"blust_2003_thao_dictionary_{start_page:04d}_{end_page:04d}"
    source = (
        f"Blust 2003 Thao-English dictionary example sentences, printed pp. "
        f"{start_page}-{end_page} (PDF pp. {start_page + 10}-{end_page + 10}); "
        f"{CATALOG_URL}; {PDF_URL}; Basecamp card {BASECAMP_CARD}"
    )
    root = text_root(text_id, source)
    for record in records:
        locator = (
            f"printed p. {int(record['source_printed_page'])}; PDF p. "
            f"{int(record['source_pdf_page'])}; source record "
            f"{record['source_record_id']}"
        )
        expansion = expansion_description(record)
        if expansion:
            locator += f"; {expansion}"
        sentence = ET.SubElement(
            root,
            "S",
            {"id": str(record["id"]), "source": locator},
        )
        form_attributes = {"kindOf": "original"}
        if record.get("source_note"):
            form_attributes["notes"] = f"Source note: {record['source_note']}"
        original = ET.SubElement(sentence, "FORM", form_attributes)
        form_text = normalize_blust_quotes(str(record["source"]), attested)
        original.text = form_text
        # POL-028: a tier carrying a ver FORM carries exactly one FORM of the
        # same kindOf without ver - the reading the variants vary from. Blust
        # brackets material inside a word to give two spellings of one lexeme
        # (`mashta(y)`, `ihu-(n)`), and that is an alternate reading of this
        # sentence, not a second sentence (maintainer, 2026-09-11).
        if record.get("alternate"):
            alternate = ET.SubElement(
                sentence, "FORM", {"kindOf": "original", "ver": "alt"}
            )
            alternate.text = normalize_blust_quotes(
                str(record["alternate"]), attested
            )
        for index, (translation, notes) in enumerate(
            translation_tiers(str(record["translation"]), str(record["source"]))
        ):
            add_translation(
                sentence,
                translation,
                alternate=index > 0,
                notes=notes,
            )
        add_word_tier(sentence, str(record["id"]), form_text)
    ET.indent(root, space="    ")
    name = f"blust_2003_thao_dictionary_{start_page:04d}_{end_page:04d}.xml"
    return name, ET.ElementTree(root)


SEGMENTATION = re.compile(r"[-\u2013]")


def add_word_tier(sentence: ET.Element, sentence_id: str, form_text: str) -> None:
    """Word and morpheme tiers for a dictionary example.

    Blust prints morpheme boundaries in the dictionary examples (a dash inside
    a word) and not in the five interlinear texts, so only these sentences
    carry the analysis and only these get an M tier -- POL-023 reads the tier
    per sentence, and a sentence with no parsing takes no M at all.

    FORM only: Blust glosses the examples as wholes, not morpheme by morpheme,
    so a W or M here carries no TRANSL. That is the gloss-presence family's
    reported-never-fatal case (V064/V065), not a gap to fill with invented
    glosses.
    """
    tokens = form_text.split()
    # POL-023 reads the M tier per sentence: a sentence that carries some
    # parsing gives every W at least one M (one M = "analysed as
    # monomorphemic"), and a sentence that carries none takes no M at all.
    parsed = any(SEGMENTATION.search(token) for token in tokens)
    for number, token in enumerate(tokens, start=1):
        word = ET.SubElement(
            sentence, "W", {"id": f"{sentence_id}-w{number:03d}"}
        )
        word_form = ET.SubElement(word, "FORM", {"kindOf": "original"})
        word_form.text = token
        if not parsed:
            continue
        pieces = SEGMENTATION.split(token)
        for piece_number, piece in enumerate(pieces, start=1):
            morpheme = ET.SubElement(
                word, "M", {"id": f"{sentence_id}-w{number:03d}-m{piece_number:03d}"}
            )
            morpheme_form = ET.SubElement(morpheme, "FORM", {"kindOf": "original"})
            morpheme_form.text = piece


def build_all(texts_only: bool = False) -> list[tuple[str, ET.ElementTree]]:
    """Every file this pipeline produces, or - with `texts_only` - just the five.

    The published corpus takes its dictionary from the schema parse
    (build_entry_xml.py), which carries the entry each example belongs to. It
    takes the five interlinear texts from here, because this is the only
    pipeline that reads them. So the canonical build runs this first with
    `--texts-only` and then lets build_entry_xml add the entries and examples
    beside them (maintainer, 2026-09-11).

    The whole-corpus guards below still run on a full build. On a texts-only
    build the statistics check still runs - it is about the input, not the
    output - and the id check is scoped to the texts.
    """
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if data["statistics"]["total_sentences"] != EXPECTED_SENTENCES:
        raise ValueError("expanded input does not have the reviewed sentence count")
    attested = attested_unquoted_tokens(data)
    output = [build_text(record, attested) for record in data["texts"]]
    if texts_only:
        ids = [s.get("id") for _n, tree in output
               for s in tree.getroot().findall("S")]
        if len(ids) != len(set(ids)) or not ids:
            raise ValueError("text sentence IDs are missing or non-unique")
        return output
    dictionary = data["dictionary_examples"]
    assigned: set[str] = set()
    for start_page, end_page in DICTIONARY_PARTS:
        part = [
            record
            for record in dictionary
            if start_page <= int(record["source_printed_page"]) <= end_page
        ]
        assigned.update(str(record["id"]) for record in part)
        output.append(build_dictionary_part(start_page, end_page, part, attested))
    dictionary_ids = {str(record["id"]) for record in dictionary}
    if assigned != dictionary_ids:
        raise ValueError(
            "dictionary partition mismatch: "
            f"missing={sorted(dictionary_ids - assigned)}, "
            f"extra={sorted(assigned - dictionary_ids)}"
        )
    sentence_ids = [
        sentence.get("id")
        for _name, tree in output
        for sentence in tree.getroot().findall("S")
    ]
    if len(sentence_ids) != EXPECTED_SENTENCES or len(sentence_ids) != len(set(sentence_ids)):
        raise ValueError("generated sentence IDs are incomplete or non-unique")
    return output


def write_all(output_dir: Path, texts_only: bool = False) -> None:
    temporary = output_dir.parent / f".{output_dir.name}-raw-build"
    if temporary.exists():
        shutil.rmtree(temporary)
    temporary.mkdir(parents=True)
    try:
        built = build_all(texts_only)
        for filename, tree in built:
            tree.write(
                temporary / filename,
                encoding="utf-8",
                xml_declaration=True,
            )
        if output_dir.exists():
            shutil.rmtree(output_dir)
        temporary.replace(output_dir)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    print(f"wrote {len(built)} raw XML files to {output_dir}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--texts-only", action="store_true",
                        help="write only the five interlinear texts")
    args = parser.parse_args()
    write_all(args.output_dir.resolve(), args.texts_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
