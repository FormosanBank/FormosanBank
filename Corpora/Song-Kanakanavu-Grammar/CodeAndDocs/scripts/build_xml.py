#!/usr/bin/env python3
"""Build reviewed Kanakanavu grammar examples into FormosanBank XML."""

from __future__ import annotations

import csv
from collections import Counter
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import normalize_standard_forms


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "intermediate" / "source_ledger.csv"
PAGE_INVENTORY = ROOT / "intermediate" / "page_inventory.csv"
CANDIDATE_LEDGER = ROOT / "intermediate" / "candidate_ledger.csv"
DICTIONARY_LEDGER = ROOT / "intermediate" / "dictionary_ledger.csv"
INTERLINEAR_LEDGER = ROOT / "intermediate" / "interlinear_ledger.jsonl"
SOURCE_PDF = ROOT / "raw_data" / "source.pdf"
OFFICIAL_TEXT = ROOT / "raw_data" / "official_text.jsonl"
OUTPUT_DIR = ROOT.parent / "XML" / "Kanakanavu"
GRAMMAR_OUTPUT = OUTPUT_DIR / "Song_2018_Kanakanavu_Grammar.xml"
DICTIONARY_OUTPUT = OUTPUT_DIR / "Song_2018_Kanakanavu_Grammar_Dictionary.xml"
EXPECTED_PDF_SHA256 = "dcd553f0ab59d55570a27e859cf60b1df22c5ed873018a192d167a0312079893"
EXPECTED_FILE_SHA256 = {
    OFFICIAL_TEXT: "47fc6dc5a22e263b57d96781cb39c0d9dbd3fb77a6189609024be2801347d5ab",
    PAGE_INVENTORY: "3754c3017eb77d788dadefb6a6d361b5b0b3cb4cb8a86e5d623a20afd36d1bfb",
    CANDIDATE_LEDGER: "5e0f917f87cefbec6e7acf3768d159be7ccce413efec6a03504966b750c38e89",
    LEDGER: "9643a9433e7e041083ac1775d88ffd862fa226ae4d73eae601c66742c097b08c",
    DICTIONARY_LEDGER: "9799290ae5ce0ee415d47fa5949d53e3b1c552a4e4ae20df65a8f23cb1ed64fb",
    INTERLINEAR_LEDGER: "f07a876e85dd8ddca0b20b6f6563c092e205f6e8d958c37d7c07bb42b571e42d",
    ROOT / "intermediate" / "standard_surface_decisions.tsv": (
        "1e30387a07b771b8e758b567de3345accd144642a7b201fe5c7a53089359c1ca"
    ),
}
EXPECTED_PAGES = 268
EXPECTED_CANDIDATES = 443
EXPECTED_INCLUDED = 699
EXPECTED_EXCLUDED = 14
EXPECTED_DICTIONARY = 767
EXPECTED_DICTIONARY_EXCLUDED = 11
# Reader page 190 defines the source's typewriter double hyphen as its break
# punctuation (one dash). Per the reviewer decision of 2026-08-07 it is a
# single dash, corrected here at build so every downstream tier inherits it.
BREAK_DASH_IDS = {
    "song-2018-kanakanavu-S0469",
    "song-2018-kanakanavu-S0472",
}
BREAK_DASH_NOTE = (
    "Source typewriter double-hyphen break punctuation (reader page 190) "
    "rendered as a single dash."
)
# The ledger keeps the source's typographic apostrophes; the decision manifest
# stores inputs in the cleaned ASCII form clean_xml later produces. Map only
# the apostrophe variants clean_xml collapses so the two can be compared.
_APOSTROPHE_MAP = str.maketrans({ch: "'" for ch in "‘’ˈ`ʼʻ"})


def _canonical_apostrophes(text: str) -> str:
    return text.translate(_APOSTROPHE_MAP)
EXPECTED_ANALYSES = 650
EXPECTED_WORDS = 3477
EXPECTED_MORPHEMES = 5034
# The value the reviewed ledger records for grammar sentences; kept verbatim
# because the ledger is hash-pinned (the build now writes into XML/ directly).
LEDGER_XML_PATH = "Final_XML/Kanakanavu/Song_2018_Kanakanavu_Grammar.xml"

CITATION = (
    "Song, Limei. (2018). Kanakanafu yu yufa gailun [Introduction to "
    "Kanakanavu Grammar]. Taiwan nandao yuyan congshu, 16. Council of "
    "Indigenous Peoples."
)
BIBTEX = (
    "@book{song2018kanakanavu, author={Song, Limei}, title={Kanakanafu yu "
    "yufa gailun [Introduction to Kanakanavu Grammar]}, series={Taiwan "
    "nandao yuyan congshu}, volume={16}, publisher={Council of Indigenous "
    "Peoples}, year={2018}}"
)
SOURCE_URL = (
    "https://alilin.cip.gov.tw/ebook/5949734115b6abe6caf971/HTML5/pc.html#/page/1"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def assert_closed_review() -> None:
    pages = read_csv(PAGE_INVENTORY)
    candidates = read_csv(CANDIDATE_LEDGER)
    official_pages = read_jsonl(OFFICIAL_TEXT)

    expected_numbers = list(range(1, EXPECTED_PAGES + 1))
    page_numbers = [int(row["reader_page"]) for row in pages]
    page_locators = [row["source_locator"] for row in pages]
    if page_numbers != expected_numbers or page_locators != [
        f"page-{page:03d}" for page in expected_numbers
    ]:
        raise ValueError("Page inventory is missing, duplicated, or reordered")
    if any(not row["coverage_status"].startswith("REVIEWED_") for row in pages):
        raise ValueError("Page inventory contains a nonterminal review status")

    positioned_numbers = [int(record["page"]) for record in official_pages]
    if positioned_numbers != expected_numbers:
        raise ValueError("Positioned text is missing, duplicated, or reordered")

    if len(candidates) != EXPECTED_CANDIDATES:
        raise ValueError(
            f"Expected {EXPECTED_CANDIDATES} candidates; found {len(candidates)}"
        )
    if any(
        not row["review_status"].startswith(("REVIEWED_", "REJECTED_"))
        for row in candidates
    ):
        raise ValueError("Candidate ledger contains a nonterminal review status")
    candidate_pages = Counter(int(row["reader_page"]) for row in candidates)
    for row in candidates:
        page = int(row["reader_page"])
        if row["source_locator"] != f"page-{page:03d}" or page not in expected_numbers:
            raise ValueError("Candidate ledger contains an invalid page locator")
    inventory_counts = {
        int(row["reader_page"]): int(row["candidate_count"]) for row in pages
    }
    if any(candidate_pages[page] != inventory_counts[page] for page in expected_numbers):
        raise ValueError("Candidate totals disagree with the page inventory")

    digest = hashlib.sha256(SOURCE_PDF.read_bytes()).hexdigest()
    if digest != EXPECTED_PDF_SHA256:
        raise ValueError(f"Source PDF hash changed: {digest}")
    for path, expected in EXPECTED_FILE_SHA256.items():
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Reviewed artifact hash changed for {path}: {actual}")


def xml_word_form(text: str) -> str:
    """Remove parenthetical apparatus while preserving printed segmentation."""
    normalized = re.sub(r"\([^)]*\)", "", text)
    if not normalized:
        raise ValueError(f"Word form became empty after normalization: {text!r}")
    return normalized


def make_root(identifier: str, source: str) -> ET.Element:
    return ET.Element(
        "TEXT",
        {
            "id": identifier,
            "{http://www.w3.org/XML/1998/namespace}lang": "xnb",
            "dialect": "Kanakanavu",
            "citation": CITATION,
            "BibTeX_citation": BIBTEX,
            "copyright": (
                "Song, Limei (2018), Introduction to Kanakanavu Grammar (Council "
                "of Indigenous Peoples). Licensed to FormosanBank under CC BY-NC 4.0 "
                "by permission of the author (Li-May Sung)."
            ),
            "source": source,
        },
    )


def add_analysis(
    sentence: ET.Element,
    sentence_id: str,
    analysis: dict[str, object],
) -> None:
    for word_index, word in enumerate(analysis["words"], start=1):
        word_id = f"{sentence_id}-W{word_index:03d}"
        word_element = ET.SubElement(sentence, "W", {"id": word_id})
        ET.SubElement(word_element, "FORM", {"kindOf": "original"}).text = str(
            xml_word_form(str(word["form"]))
        )
        ET.SubElement(
            word_element,
            "TRANSL",
            {"{http://www.w3.org/XML/1998/namespace}lang": "zho"},
        ).text = str(word["gloss"])
        for morph_index, morph in enumerate(word.get("morphemes", []), start=1):
            morph_element = ET.SubElement(
                word_element,
                "M",
                {"id": f"{word_id}-M{morph_index:02d}"},
            )
            ET.SubElement(
                morph_element,
                "FORM",
                {"kindOf": "original"},
            ).text = str(morph["form"])
            ET.SubElement(
                morph_element,
                "TRANSL",
                {"{http://www.w3.org/XML/1998/namespace}lang": "zho"},
            ).text = str(morph["gloss"])


def write_xml(root: ET.Element, output: Path) -> None:
    ET.indent(root, space="  ")
    output.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(output, encoding="UTF-8", xml_declaration=True)


def build_grammar(included: list[dict[str, str]]) -> None:
    analyses = read_jsonl(INTERLINEAR_LEDGER)
    analysis_by_id = {str(analysis["s_id"]): analysis for analysis in analyses}
    word_count = sum(len(analysis["words"]) for analysis in analyses)
    morph_count = sum(
        len(word.get("morphemes", []))
        for analysis in analyses
        for word in analysis["words"]
    )
    if (len(analyses), word_count, morph_count) != (
        EXPECTED_ANALYSES,
        EXPECTED_WORDS,
        EXPECTED_MORPHEMES,
    ):
        raise ValueError(
            "Expected "
            f"{EXPECTED_ANALYSES} analyses/{EXPECTED_WORDS} words/"
            f"{EXPECTED_MORPHEMES} morphemes; found "
            f"{len(analyses)}/{word_count}/{morph_count}"
        )

    root = make_root(
        "song_2018_kanakanavu_grammar",
        (
            f"Official Alilin reader {SOURCE_URL}; 268 page images reviewed directly; "
            f"source PDF sha256 {EXPECTED_PDF_SHA256}; Basecamp card 10081339846."
        ),
    )
    corrected_dashes = 0
    for row in included:
        sentence = ET.SubElement(
            root,
            "S",
            {
                "id": row["final_s_id"],
                "source": (
                    f"Song 2018 official reader page {row['reader_page']}; "
                    f"ledger label {row['example_label']}; {row['confidence_review_note']}."
                ),
            },
        )
        original = ET.SubElement(sentence, "FORM", {"kindOf": "original"})
        target_text = row["target_text"]
        if row["final_s_id"] in BREAK_DASH_IDS:
            if target_text.count("--") != 1:
                raise ValueError(
                    f"{row['final_s_id']} expected one source double hyphen; "
                    f"found {target_text!r}"
                )
            target_text = target_text.replace("--", "-", 1)
            original.set("notes", BREAK_DASH_NOTE)
            corrected_dashes += 1
        elif "--" in target_text:
            raise ValueError(
                f"Unreviewed double hyphen in {row['final_s_id']}: {target_text!r}"
            )
        original.text = target_text
        ET.SubElement(
            sentence,
            "TRANSL",
            {"{http://www.w3.org/XML/1998/namespace}lang": "zho"},
        ).text = row["translation"]
        if row["final_s_id"] in analysis_by_id:
            add_analysis(
                sentence,
                row["final_s_id"],
                analysis_by_id[row["final_s_id"]],
            )
    if corrected_dashes != len(BREAK_DASH_IDS):
        raise ValueError(
            f"Expected {len(BREAK_DASH_IDS)} break-dash corrections; "
            f"made {corrected_dashes}"
        )
    write_xml(root, GRAMMAR_OUTPUT)
    print(
        f"Wrote {GRAMMAR_OUTPUT} with {len(included)} sentences, "
        f"{word_count} words, and {morph_count} morphemes."
    )


def build_dictionary() -> None:
    rows = read_csv(DICTIONARY_LEDGER)
    expected_ids = [
        f"song-2018-kanakanavu-dictionary-{index:04d}"
        for index in range(1, EXPECTED_DICTIONARY + 1)
    ]
    if len(rows) != EXPECTED_DICTIONARY or [row["entry_id"] for row in rows] != expected_ids:
        raise ValueError("Dictionary ledger count or deterministic IDs changed")
    excluded = [row for row in rows if row["included"] == "no"]
    if len(excluded) != EXPECTED_DICTIONARY_EXCLUDED or any(
        not row["form"].endswith("-") or not row["exclusion_reason"]
        for row in excluded
    ):
        raise ValueError("Dictionary bound-citation exclusions changed")
    rows = [row for row in rows if row["included"] == "yes"]

    decisions = normalize_standard_forms.decisions_for_scope(
        normalize_standard_forms.load_decisions(), "dictionary"
    )
    manifest_excluded = {
        record_id for record_id, decision in decisions.items() if decision.excluded
    }
    if manifest_excluded != {row["entry_id"] for row in excluded}:
        raise ValueError(
            "Ledger exclusions and manifest bound-exclusion decisions diverged"
        )
    split = {
        record_id: decision
        for record_id, decision in decisions.items()
        if not decision.excluded
    }

    root = make_root(
        "song_2018_kanakanavu_grammar_dictionary",
        (
            f"Official Alilin reader {SOURCE_URL}; Appendix 2A pages 193-206, "
            "cross-checked against duplicate Chinese-sorted Appendix 2B pages "
            f"207-220; source PDF sha256 {EXPECTED_PDF_SHA256}."
        ),
    )
    planned = []
    for row in rows:
        decision = split.get(row["entry_id"])
        canonical_form = _canonical_apostrophes(row["form"])
        source = (
            f"Song 2018 official reader page {row['reader_page']}; "
            f"Appendix 2A column {row['column']}; {row['method']}."
        )
        if decision is None:
            if normalize_standard_forms.DICTIONARY_MARKER_RE.search(canonical_form):
                raise ValueError(
                    f"Unreviewed source apparatus in {row['entry_id']}: "
                    f"{row['form']!r}"
                )
            forms = [(row["entry_id"], row["form"], None)]
        else:
            if canonical_form != decision.expected_input:
                raise ValueError(
                    f"Ledger form changed for {row['entry_id']}: "
                    f"{canonical_form!r}; manifest expects "
                    f"{decision.expected_input!r}"
                )
            note = (
                f'Source prints "{decision.expected_input}"; source-defined '
                "forms emitted as separate entries (exact outputs in "
                "intermediate/standard_surface_decisions.tsv)."
            )
            forms = [
                (
                    normalize_standard_forms.variant_entry_id(
                        row["entry_id"], index
                    ),
                    output,
                    note,
                )
                for index, output in enumerate(decision.output_forms)
            ]
        for entry_id, form_text, note in forms:
            planned.append(
                {
                    "entry_id": entry_id,
                    "text": form_text,
                    "note": note,
                    "source": source,
                    "translation": row["translation"],
                    "is_variant": entry_id != row["entry_id"],
                    "record_id": row["entry_id"],
                }
            )

    # A split variant whose (form, translation) duplicates a non-variant
    # entry is dropped: the source prints that form as its own record, which
    # keeps it. The computed set must match the reviewed constant exactly.
    def entry_key(entry: dict[str, str]) -> tuple[str, str]:
        return (
            _canonical_apostrophes(entry["text"]),
            _canonical_apostrophes(entry["translation"]),
        )

    primary_keys = {
        entry_key(entry) for entry in planned if not entry["is_variant"]
    }
    computed_duplicates = {
        entry["entry_id"]
        for entry in planned
        if entry["is_variant"] and entry_key(entry) in primary_keys
    }
    if computed_duplicates != normalize_standard_forms.DUPLICATE_VARIANT_ENTRY_IDS:
        raise ValueError(
            "Duplicate variant coverage changed: "
            f"unexpected={sorted(computed_duplicates - normalize_standard_forms.DUPLICATE_VARIANT_ENTRY_IDS)}, "
            f"missing={sorted(normalize_standard_forms.DUPLICATE_VARIANT_ENTRY_IDS - computed_duplicates)}"
        )
    dropped_records = {
        entry["record_id"]
        for entry in planned
        if entry["entry_id"] in computed_duplicates
    }
    planned = [
        entry for entry in planned if entry["entry_id"] not in computed_duplicates
    ]
    remaining_keys = [entry_key(entry) for entry in planned]
    if len(remaining_keys) != len(set(remaining_keys)):
        raise ValueError("Dictionary (form, translation) pairs are not unique")

    entry_count = 0
    variant_count = 0
    for entry in planned:
        sentence = ET.SubElement(
            root, "S", {"id": entry["entry_id"], "source": entry["source"]}
        )
        original = ET.SubElement(sentence, "FORM", {"kindOf": "original"})
        note = entry["note"]
        if note is not None:
            if entry["record_id"] in dropped_records:
                note += (
                    " Duplicate source-printed forms are represented by "
                    "their own records."
                )
            original.set("notes", note)
        original.text = entry["text"]
        ET.SubElement(
            sentence,
            "TRANSL",
            {"{http://www.w3.org/XML/1998/namespace}lang": "zho"},
        ).text = entry["translation"]
        entry_count += 1
        variant_count += entry["is_variant"]
    expected_variants = (
        normalize_standard_forms.EXPECTED_DICTIONARY_EXTRA_ENTRIES
        - len(normalize_standard_forms.DUPLICATE_VARIANT_ENTRY_IDS)
    )
    if variant_count != expected_variants:
        raise ValueError(
            f"Expected {expected_variants} variant entries after duplicate "
            f"removal; emitted {variant_count}"
        )
    write_xml(root, DICTIONARY_OUTPUT)
    print(
        f"Wrote {DICTIONARY_OUTPUT} with {entry_count} lexical entries "
        f"({len(rows)} published records, {variant_count} split variants, "
        f"{len(computed_duplicates)} duplicate variants dropped, "
        f"{len(excluded)} bound citation forms excluded)."
    )


def main() -> None:
    assert_closed_review()
    rows = read_csv(LEDGER)
    included = [row for row in rows if row["included"] == "yes"]
    excluded = [row for row in rows if row["included"] == "no"]
    if (len(included), len(excluded)) != (EXPECTED_INCLUDED, EXPECTED_EXCLUDED):
        raise ValueError(
            f"Expected {EXPECTED_INCLUDED} included and {EXPECTED_EXCLUDED} excluded; "
            f"found {len(included)} and {len(excluded)}"
        )

    expected_ids = [
        f"song-2018-kanakanavu-S{i:04d}" for i in range(1, len(included) + 1)
    ]
    actual_ids = [row["final_s_id"] for row in included]
    if actual_ids != expected_ids:
        raise ValueError("Included sentence IDs are not continuous and deterministic")
    if any(row["final_xml_path"] not in {"", LEDGER_XML_PATH} for row in included):
        raise ValueError("Included ledger rows contain an unexpected XML path")

    build_grammar(included)
    build_dictionary()


if __name__ == "__main__":
    main()
