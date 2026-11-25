#!/usr/bin/env python3
"""Build canonical Yedda XML from the frozen complete scrape snapshot."""

from __future__ import annotations

import copy
import csv
import hashlib
import re
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = ROOT.parent
SOURCE = ROOT / "data/source_snapshot/Paiwan_Yedda_Blog.xml"
OUTPUT = CORPUS_ROOT / "XML/Paiwan/Paiwan_Yedda_Blog.xml"
AUDIT = ROOT / "data/formosanbank_audit"
EXPECTED_SOURCE_SHA256 = (
    "e18d0aa67893278cb7754e9725e68a81075760961391b3db941eca7d873ddba6"
)
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
# Glosses in which the maintainer has ruled, row by row, that a `?` standing as
# a whole gloss piece is the author's unknown-gloss placeholder. Header
# `gloss<TAB>lang`; each row is one exact W/M TRANSL text and its xml:lang.
UNCLEAR_PLACEHOLDER_TABLE = ROOT / "unclear_gloss_placeholders.tsv"
# Maintainer's ruling, 2026-10-17: a W/M gloss that is exactly `?`, `??` or
# `???` (half- or full-width) is the source's unknown-gloss marker.
WHOLE_UNKNOWN_GLOSS = re.compile(r"[?？]{1,3}")
# A `?` run standing as a whole gloss piece: bounded on both sides by -, =, .,
# whitespace, or the string's ends. `LIG?` and `right?` do not match.
PLACEHOLDER_PIECE = re.compile(r"(?<![^\-=.\s])[?？]+(?![^\-=.\s])")
# Word glosses the maintainer ruled on one by one (2026-10-17): the author's
# whole gloss text moves to the TRANSL's notes attribute and the gloss becomes
# new_gloss, where the literal `<UNCLEAR/>` means the gloss is <UNCLEAR/>.
# Header `w_id<TAB>form<TAB>lang<TAB>old_gloss<TAB>new_gloss`.
GLOSS_TO_NOTES_TABLE = ROOT / "gloss_to_notes.tsv"
# The author's mark of uncertainty on a gloss she did give (POL-021 as amended
# 2026-11-11): the gloss becomes new_gloss and the TRANSL gets notes="uncertain".
# Same header as gloss_to_notes.tsv. Maintainer (2026-11-11): "LIG? -> LIG +
# uncertainty", "ligature (?) -> ligature + uncertainty", "to, towards? ->
# to/towards + uncertainty", "bring or send? I don't know this word. ->
# bring/send + uncertainty" (and complementizer?, function word?, subject case
# marker?).
UNCERTAIN_GLOSS_TABLE = ROOT / "uncertain_glosses.tsv"
UNCLEAR_SENTINEL = "<UNCLEAR/>"

# Reviewed repairs to the frozen snapshot, one table each (maintainer,
# 2026-11-25: chose "Yes, as proposed" for "tables + three-way check"). Every
# row names the text it expects to find. Per row the build applies the repair
# when that text is there, skips it (and says so) when the repaired text is
# already there, and stops, naming the row, when neither is.
# Sentence translations restored or separated after the frozen-scrape review.
ISSUE_REPAIRS_TABLE = ROOT / "issue_repairs.tsv"
ISSUE_REPAIRS_HEADER = [
    "s_id", "rule", "expected_translation", "repaired_translation",
    "resolution", "evidence",
]
# Sentences printed with alternatives (qali/drava, ...), emitted as two records.
# The split itself is code (split_alternatives); this table holds the source
# text it expects and the audit metadata.
VARIANTS_TABLE = ROOT / "source_variants.tsv"
VARIANTS_HEADER = [
    "source_s_id", "output_s_ids", "source_form", "resolution", "evidence",
]
# Sentence translations taken from the live source; an empty
# expected_translation means the snapshot has no translation there.
SOURCE_TRANSLATION_TABLE = ROOT / "source_translation_repairs.tsv"
SOURCE_TRANSLATION_HEADER = [
    "s_id", "expected_translation", "translation", "resolution", "evidence",
]
# Word glosses taken from the live source for words the snapshot leaves unglossed.
SOURCE_WORD_TRANSLATION_TABLE = ROOT / "source_word_translation_repairs.tsv"
SOURCE_WORD_TRANSLATION_HEADER = ["w_id", "form", "source_head", "translation"]
# Second spellings the source gives in an "X or Y" (or "X / Y") list headword,
# written as POL-028 variants: FORM kindOf="original" ver="alt" on the word, and
# on its single morpheme when that morpheme spells the whole word. standardize.py
# derives the standard-tier variant. Maintainer, 2026-11-25: "That should be
# handled through our normal lexical alternate scheme."
WORD_ALTERNATES_TABLE = ROOT / "word_alternates.tsv"
WORD_ALTERNATES_HEADER = ["w_id", "form", "alternate", "source_head"]
# Word glosses the frozen scrape attached to the wrong list item.
WORD_GLOSS_CORRECTIONS_TABLE = ROOT / "word_gloss_corrections.tsv"
WORD_GLOSS_CORRECTIONS_HEADER = ["w_id", "form", "expected_gloss", "corrected_gloss", "evidence"]
# Notes added to a sentence translation (e.g. a phrase gloss with no word to sit on).
SENTENCE_NOTES_TABLE = ROOT / "sentence_translation_notes.tsv"
SENTENCE_NOTES_HEADER = ["s_id", "expected_translation", "note"]


# Word glosses whose spaces the old scraper dropped at italics (its
# get_text(strip=True)); repaired_gloss is the fixed scraper's reading of the
# downloaded blog HTML. A row may change whitespace only: the build refuses a
# row whose two glosses differ once all whitespace is removed. Applied first,
# to the snapshot's own word ids, before any other repair.
GLOSS_WHITESPACE_TABLE = ROOT / "gloss_whitespace_repairs.tsv"
GLOSS_WHITESPACE_HEADER = ["w_id", "form", "lang", "snapshot_gloss", "repaired_gloss"]
WHITESPACE = re.compile(r"\s+")


def read_table(path: Path, header: list[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
        if reader.fieldnames != header:
            raise SystemExit(f"{path.name}: unexpected header {reader.fieldnames}")
        return list(reader)


def stop(table: Path, row_id: str, found: str) -> None:
    raise SystemExit(
        f"{table.name}: row {row_id} finds neither its expected text nor its "
        f"repaired text; found {found!r}"
    )


SKIPPED: list[str] = []


def skipped(table: Path, row_id: str) -> None:
    SKIPPED.append(f"{table.name} {row_id}")


# The one sentence whose source text carries segmentation hyphens in running
# sentence text. POL-014/015 put those markers on the W/M tiers, so the standard
# tier drops them -- which standardize.py's C012 step does by rule. Nothing here
# edits the standard tier; this only annotates the original so a reader knows
# why the two tiers differ. Asserted, not searched: if the source surface ever
# changes, the build fails rather than annotating the wrong sentence.
SOURCE_SEGMENTATION_NOTE = (
    "S652653654_2",
    "pai, maya manu seman-neka-aravac tua zuma.",
    "Source prints the segmentation seman-neka-aravac. Per POL-014/015 the "
    "markers belong on the W and M tiers, so the standard tier drops them; the "
    "original keeps the source surface.",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_sentence(root: ET.Element, sentence_id: str) -> ET.Element:
    sentence = root.find(f"S[@id='{sentence_id}']")
    if sentence is None:
        raise RuntimeError(f"Missing source sentence {sentence_id}")
    return sentence


def find_word(sentence: ET.Element, word_id: str) -> ET.Element:
    word = sentence.find(f"W[@id='{word_id}']")
    if word is None:
        raise RuntimeError(f"Missing source word {word_id}")
    return word


def original_form(element: ET.Element) -> ET.Element:
    # The base: the one original FORM without ver (POL-028); ver="alt" variants
    # are added by add_word_alternates.
    forms = [
        form for form in element.findall("FORM")
        if form.get("kindOf") == "original" and form.get("ver") is None
    ]
    if len(forms) != 1:
        raise RuntimeError(
            f"Expected one base original FORM under {element.tag} {element.get('id')}"
        )
    return forms[0]


def set_original_form(element: ET.Element, text: str, notes: str | None = None) -> None:
    form = original_form(element)
    form.text = text
    if notes:
        form.set("notes", notes)


def strip_derived_tiers(root: ET.Element) -> None:
    for parent in root.iter():
        for child in list(parent):
            if child.tag == "PHON" or (
                child.tag == "FORM" and child.get("kindOf") == "standard"
            ):
                parent.remove(child)


def remove_audio(sentence: ET.Element) -> None:
    sentence.attrib.pop("audio_url", None)
    for audio in sentence.findall("AUDIO"):
        sentence.remove(audio)


def rename_descendant_ids(sentence: ET.Element, old: str, new: str) -> None:
    for element in list(sentence.iter())[1:]:
        element_id = element.get("id")
        if element_id and element_id.startswith(old):
            element.set("id", new + element_id[len(old) :])
    sentence.set("id", new)


def add_word_translation(
    word: ET.Element,
    text: str,
    notes: str | None = None,
) -> None:
    for translation in word.findall("TRANSL"):
        word.remove(translation)
    translation = ET.Element("TRANSL", {XML_LANG: "eng"})
    translation.text = text
    if notes:
        translation.set("notes", notes)
    insert_at = len(word)
    for index, child in enumerate(word):
        if child.tag == "M":
            insert_at = index
            break
    word.insert(insert_at, translation)


def remove_word(sentence: ET.Element, word_id: str) -> None:
    sentence.remove(find_word(sentence, word_id))


def replace_with_variants(
    root: ET.Element, source_id: str, variants: list[ET.Element]
) -> None:
    source = find_sentence(root, source_id)
    index = list(root).index(source)
    root.remove(source)
    for offset, variant in enumerate(variants):
        root.insert(index + offset, variant)


def repair_gloss_whitespace(root: ET.Element) -> int:
    """Put back the spaces in word glosses; returns how many were repaired."""
    repaired = 0
    for row in read_table(GLOSS_WHITESPACE_TABLE, GLOSS_WHITESPACE_HEADER):
        word_id, old, new = row["w_id"], row["snapshot_gloss"], row["repaired_gloss"]
        if WHITESPACE.sub("", old) != WHITESPACE.sub("", new):
            raise SystemExit(
                f"{GLOSS_WHITESPACE_TABLE.name}: row {word_id} changes more than whitespace"
            )
        word = find_word(find_sentence(root, word_id.rsplit("W", 1)[0]), word_id)
        if (original_form(word).text or "") != row["form"]:
            raise SystemExit(
                f"{GLOSS_WHITESPACE_TABLE.name}: {word_id} is not {row['form']!r}"
            )
        translations = [
            t for t in word.findall("TRANSL") if t.get(XML_LANG) == row["lang"]
        ]
        if len(translations) != 1 or len(translations[0]):
            raise SystemExit(
                f"{GLOSS_WHITESPACE_TABLE.name}: {word_id} has no single text-only "
                f"{row['lang']} gloss"
            )
        found = translations[0].text or ""
        if found == old:
            translations[0].text = new
            repaired += 1
        elif found == new:
            skipped(GLOSS_WHITESPACE_TABLE, word_id)
        else:
            stop(GLOSS_WHITESPACE_TABLE, word_id, found)
    return repaired


def check_variant_sources(root: ET.Element) -> dict[str, dict[str, str]]:
    """Each sentence split_alternatives splits must still print its listed text.

    There is no "already split" case to skip: a split sentence no longer
    carries the source text, so it stops here.
    """
    variants = {}
    for row in read_table(VARIANTS_TABLE, VARIANTS_HEADER):
        found = original_form(find_sentence(root, row["source_s_id"])).text or ""
        if found != row["source_form"]:
            stop(VARIANTS_TABLE, row["source_s_id"], found)
        variants[row["source_s_id"]] = {
            "output_ids": row["output_s_ids"],
            "source_form": row["source_form"],
            "resolution": row["resolution"],
            "evidence": row["evidence"],
        }
    if sorted(variants) != ["S24_1", "S483_1", "S535_1"]:
        raise SystemExit(
            f"{VARIANTS_TABLE.name}: split_alternatives splits S24_1, S483_1 and "
            f"S535_1; the table lists {sorted(variants)}"
        )
    return variants


def split_alternatives(root: ET.Element) -> None:
    source = copy.deepcopy(find_sentence(root, "S24_1"))
    qali = copy.deepcopy(source)
    drava = copy.deepcopy(source)
    rename_descendant_ids(drava, "S24_1", "S24_1b")
    note = (
        'Source prints "a kipaparangez tua mareka qali/drava maru tjalja '
        'semeljecan a tja kava nu kaljavuceleljan."; source-defined alternatives '
        "are emitted as separate records. The shared recording pronounces both alternatives and is omitted."
    )
    for sentence, word_id, value, gloss in (
        (qali, "S24_1W5", "qali", "male friend"),
        (drava, "S24_1bW5", "drava", "female friend"),
    ):
        remove_audio(sentence)
        set_original_form(
            sentence,
            f"a kipaparangez tua mareka {value} maru tjalja semeljecan a tja kava nu kaljavuceleljan.",
            note,
        )
        word = find_word(sentence, word_id)
        set_original_form(word, value, note)
        morpheme = word.find("M")
        if morpheme is None:
            raise RuntimeError(f"Missing morpheme under {word_id}")
        set_original_form(morpheme, value, note)
        add_word_translation(word, gloss)
    replace_with_variants(root, "S24_1", [qali, drava])

    source = copy.deepcopy(find_sentence(root, "S483_1"))
    abar = copy.deepcopy(source)
    yasi = copy.deepcopy(source)
    rename_descendant_ids(yasi, "S483_1", "S483_1b")
    note = (
        'Source prints "liyaw a talem ni kama a abar (yasi)."; source-defined '
        "alternatives are emitted as separate records. The shared recording pronounces both alternatives and is omitted."
    )
    remove_audio(abar)
    set_original_form(abar, "liyaw a talem ni kama a abar.", note)
    remove_word(abar, "S483_1W8")
    add_word_translation(find_word(abar, "S483_1W7"), "coconut tree")
    remove_audio(yasi)
    set_original_form(yasi, "liyaw a talem ni kama a yasi.", note)
    remove_word(yasi, "S483_1bW7")
    add_word_translation(find_word(yasi, "S483_1bW8"), "coconut tree")
    for sentence in (abar, yasi):
        for translation in sentence.findall("TRANSL"):
            sentence.remove(translation)
        main = ET.Element(
            "TRANSL",
            {
                XML_LANG: "eng",
                "notes": "Source prints both free-translation versions in one parenthetical target.",
            },
        )
        main.text = "The coconut trees planted by father are a lot."
        alt = ET.Element("TRANSL", {XML_LANG: "eng", "ver": "alt"})
        alt.text = "Father plants many coconut trees."
        first_word = next(i for i, child in enumerate(sentence) if child.tag == "W")
        sentence.insert(first_word, main)
        sentence.insert(first_word + 1, alt)
    replace_with_variants(root, "S483_1", [abar, yasi])

    source = copy.deepcopy(find_sentence(root, "S535_1"))
    tjangtjang = copy.deepcopy(source)
    siyak = copy.deepcopy(source)
    rename_descendant_ids(siyak, "S535_1", "S535_1b")
    note = (
        'Source prints "izua tucu a kinarupurupung, tjangtjang / siyak, asaw '
        "na vurasi 'ata runi." + '"; source-defined alternatives are emitted as '
        "separate records. The shared recording pronounces both alternatives and is omitted."
    )
    remove_audio(tjangtjang)
    set_original_form(
        tjangtjang,
        "izua tucu a kinarupurupung, tjangtjang, asaw na vurasi 'ata runi.",
        note,
    )
    remove_word(tjangtjang, "S535_1W7")
    add_word_translation(find_word(tjangtjang, "S535_1W5"), "pumpkin")
    remove_audio(siyak)
    set_original_form(
        siyak,
        "izua tucu a kinarupurupung, siyak, asaw na vurasi 'ata runi.",
        note,
    )
    remove_word(siyak, "S535_1bW5")
    add_word_translation(find_word(siyak, "S535_1bW7"), "pumpkin")
    replace_with_variants(root, "S535_1", [tjangtjang, siyak])


def repair_issue_rows(root: ET.Element) -> list[dict[str, str]]:
    rows = []
    table = read_table(ISSUE_REPAIRS_TABLE, ISSUE_REPAIRS_HEADER)
    for finding, row in enumerate(table, 1):
        sentence_id = row["s_id"]
        sentence = find_sentence(root, sentence_id)
        translations = sentence.findall("TRANSL")
        if len(translations) != 1:
            raise RuntimeError(f"Expected one source translation in {sentence_id}")
        translation = translations[0]
        frozen = translation.text or ""
        if frozen == row["expected_translation"]:
            translation.text = row["repaired_translation"]
            translation.set("notes", f"Frozen scrape target: {frozen}")
        elif frozen == row["repaired_translation"]:
            skipped(ISSUE_REPAIRS_TABLE, sentence_id)
        else:
            stop(ISSUE_REPAIRS_TABLE, sentence_id, frozen)
        rows.append(
            {
                "finding": str(finding),
                "rule": row["rule"],
                "s_id": sentence_id,
                "resolution": row["resolution"],
                "source_url": sentence.get("source", ""),
                "evidence": row["evidence"],
            }
        )
    return rows


def restore_source_translations(root: ET.Element) -> list[dict[str, str]]:
    rows = []
    for row in read_table(SOURCE_TRANSLATION_TABLE, SOURCE_TRANSLATION_HEADER):
        sentence_id, text = row["s_id"], row["translation"]
        sentence = find_sentence(root, sentence_id)
        translations = sentence.findall("TRANSL")
        if len(translations) > 1:
            raise RuntimeError(
                f"Expected at most one source translation in {sentence_id}"
            )
        frozen = translations[0].text or "" if translations else ""
        if frozen == text and translations:
            skipped(SOURCE_TRANSLATION_TABLE, sentence_id)
        elif frozen != row["expected_translation"]:
            stop(SOURCE_TRANSLATION_TABLE, sentence_id, frozen)
        else:
            for existing in translations:
                sentence.remove(existing)
            note = (
                f"Frozen scrape target: {frozen}"
                if frozen
                else "Restored from the live source after frozen-scrape review."
            )
            translation = ET.Element(
                "TRANSL",
                {
                    XML_LANG: "eng",
                    "notes": note,
                },
            )
            translation.text = text
            first_word = next(
                (index for index, child in enumerate(sentence) if child.tag == "W"),
                len(sentence),
            )
            sentence.insert(first_word, translation)
        rows.append(
            {
                "s_id": sentence_id,
                "resolution": row["resolution"],
                "source_url": sentence.get("source", ""),
                "frozen_translation": frozen,
                "translation": text,
                "evidence": row["evidence"],
            }
        )
    return rows


def restore_source_word_translations(root: ET.Element) -> list[dict[str, str]]:
    rows = []
    note = "Restored from the live source after frozen-scrape review."
    for row in read_table(SOURCE_WORD_TRANSLATION_TABLE, SOURCE_WORD_TRANSLATION_HEADER):
        word_id, text = row["w_id"], row["translation"]
        sentence_id = word_id.rsplit("W", 1)[0]
        sentence = find_sentence(root, sentence_id)
        word = find_word(sentence, word_id)
        if (original_form(word).text or "") != row["form"]:
            raise SystemExit(
                f"{SOURCE_WORD_TRANSLATION_TABLE.name}: {word_id} is not {row['form']!r}"
            )
        existing = [t.text or "" for t in word.findall("TRANSL")]
        if not existing:
            add_word_translation(word, text, note)
        elif existing == [text]:
            skipped(SOURCE_WORD_TRANSLATION_TABLE, word_id)
        else:
            stop(SOURCE_WORD_TRANSLATION_TABLE, word_id, " | ".join(existing))
        rows.append(
            {
                "s_id": sentence_id,
                "w_id": word_id,
                "resolution": "restored_exact_live_word_gloss",
                "source_url": sentence.get("source", ""),
                "source_head": row["source_head"],
                "translation": text,
            }
        )
    return rows


def correct_word_glosses(root: ET.Element) -> None:
    for row in read_table(WORD_GLOSS_CORRECTIONS_TABLE, WORD_GLOSS_CORRECTIONS_HEADER):
        word_id = row["w_id"]
        word = find_word(find_sentence(root, word_id.rsplit("W", 1)[0]), word_id)
        if (original_form(word).text or "") != row["form"]:
            raise SystemExit(f"{WORD_GLOSS_CORRECTIONS_TABLE.name}: {word_id} is not {row['form']!r}")
        translations = word.findall("TRANSL")
        found = " | ".join(t.text or "" for t in translations)
        if len(translations) != 1 or len(translations[0]):
            stop(WORD_GLOSS_CORRECTIONS_TABLE, word_id, found)
        if found == row["expected_gloss"]:
            translations[0].text = row["corrected_gloss"]
        elif found == row["corrected_gloss"]:
            skipped(WORD_GLOSS_CORRECTIONS_TABLE, word_id)
        else:
            stop(WORD_GLOSS_CORRECTIONS_TABLE, word_id, found)


def add_variant_form(element: ET.Element, text: str) -> None:
    base = original_form(element)
    variant = ET.Element("FORM", {"kindOf": "original", "ver": "alt"})
    variant.text = text
    element.insert(list(element).index(base) + 1, variant)


def add_word_alternates(root: ET.Element) -> int:
    added = 0
    for row in read_table(WORD_ALTERNATES_TABLE, WORD_ALTERNATES_HEADER):
        word_id, alt = row["w_id"], row["alternate"]
        word = find_word(find_sentence(root, word_id.rsplit("W", 1)[0]), word_id)
        if (original_form(word).text or "") != row["form"]:
            raise SystemExit(f"{WORD_ALTERNATES_TABLE.name}: {word_id} is not {row['form']!r}")
        present = [f.text for f in word.findall("FORM[@kindOf='original']") if f.get("ver")]
        if present == [alt]:
            skipped(WORD_ALTERNATES_TABLE, word_id)
            continue
        if present:
            stop(WORD_ALTERNATES_TABLE, word_id, " | ".join(t or "" for t in present))
        add_variant_form(word, alt)
        morphemes = word.findall("M")
        if len(morphemes) == 1 and (original_form(morphemes[0]).text or "") == row["form"]:
            add_variant_form(morphemes[0], alt)
        added += 1
    return added


def add_sentence_translation_notes(root: ET.Element) -> None:
    for row in read_table(SENTENCE_NOTES_TABLE, SENTENCE_NOTES_HEADER):
        sentence_id = row["s_id"]
        translations = find_sentence(root, sentence_id).findall("TRANSL")
        if len(translations) != 1 or (translations[0].text or "") != row["expected_translation"]:
            stop(SENTENCE_NOTES_TABLE, sentence_id, " | ".join(t.text or "" for t in translations))
        current = translations[0].get("notes")
        if current == row["note"]:
            skipped(SENTENCE_NOTES_TABLE, sentence_id)
        elif current is not None:
            stop(SENTENCE_NOTES_TABLE, sentence_id, f"notes={current!r}")
        else:
            translations[0].set("notes", row["note"])


def read_placeholder_table(path: Path) -> set[tuple[str, str]]:
    """Return the (gloss, lang) pairs ruled to carry `?` placeholders."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
        header = next(reader, None)
        if header != ["gloss", "lang"]:
            raise SystemExit(f"{path.name}: header must be gloss<TAB>lang, got {header}")
        rows: set[tuple[str, str]] = set()
        for line_number, row in enumerate(reader, start=2):
            if len(row) != 2 or not row[0] or not row[1]:
                raise SystemExit(f"{path.name}:{line_number}: expected gloss<TAB>lang")
            gloss, lang = row
            if WHOLE_UNKNOWN_GLOSS.fullmatch(gloss.strip()):
                raise SystemExit(
                    f"{path.name}:{line_number}: {gloss!r} is a whole unknown-gloss "
                    "marker, converted without a table row"
                )
            if not PLACEHOLDER_PIECE.search(gloss):
                raise SystemExit(
                    f"{path.name}:{line_number}: {gloss!r} has no `?` standing as a "
                    "whole gloss piece"
                )
            rows.add((gloss, lang))
    return rows


def set_mixed_unclear(translation: ET.Element, segments: list[str]) -> None:
    """Rewrite a text-only TRANSL as segments joined by <UNCLEAR/> elements."""
    if len(translation):
        raise RuntimeError("Expected a text-only TRANSL")
    translation.text = segments[0] or None
    for segment in segments[1:]:
        marker = ET.SubElement(translation, "UNCLEAR")
        marker.tail = segment or None


def move_glosses_to_notes(
    root: ET.Element, table: Path, notes: str | None = None,
    resolution: str = "ruled_gloss_to_notes",
) -> list[dict[str, str]]:
    """Apply the ruled gloss_to_notes.tsv rows; fail on any mismatch.

    The TRANSL's notes are the old gloss, or `notes` when given
    (uncertain_glosses.tsv: notes="uncertain").

    Must run after ET.indent, like mark_unclear_glosses.
    """
    with table.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
        if reader.fieldnames != ["w_id", "form", "lang", "old_gloss", "new_gloss"]:
            raise SystemExit(f"{table.name}: unexpected header {reader.fieldnames}")
        rules = list(reader)
    rows = []
    for rule in rules:
        sentence_id = rule["w_id"].rsplit("W", 1)[0]
        word = find_word(find_sentence(root, sentence_id), rule["w_id"])
        if original_form(word).text != rule["form"]:
            raise SystemExit(f"{table.name}: {rule['w_id']} is not {rule['form']!r}")
        translations = [
            t for t in word.findall("TRANSL") if t.get(XML_LANG) == rule["lang"]
        ]
        if (
            len(translations) != 1
            or len(translations[0])
            or translations[0].text != rule["old_gloss"]
            or translations[0].get("notes") is not None
        ):
            raise SystemExit(
                f"{table.name}: {rule['w_id']} does not carry exactly the listed "
                "gloss as a text-only TRANSL without notes"
            )
        translation = translations[0]
        translation.set("notes", rule["old_gloss"] if notes is None else notes)
        if rule["new_gloss"] == UNCLEAR_SENTINEL:
            translation.text = None
            set_mixed_unclear(translation, ["", ""])
        elif "<" in rule["new_gloss"] or not rule["new_gloss"].strip():
            raise SystemExit(f"{table.name}: bad new_gloss for {rule['w_id']}")
        else:
            translation.text = rule["new_gloss"]
        rows.append(
            {
                "element": "W",
                "id": rule["w_id"],
                "lang": rule["lang"],
                "source_gloss": rule["old_gloss"],
                "unclear_count": str(len(translation)),
                "resolution": resolution,
            }
        )
    return rows


def mark_unclear_glosses(
    root: ET.Element, placeholders: set[tuple[str, str]]
) -> list[dict[str, str]]:
    """Turn the source's unknown-gloss markers in W/M TRANSL into <UNCLEAR/>.

    Must run after ET.indent so no indentation whitespace is put inside the
    TRANSL around the marker. Sentence-level translations are never touched.
    """
    rows = []
    matched: set[tuple[str, str]] = set()
    for element in [*root.iter("W"), *root.iter("M")]:
        for translation in element.findall("TRANSL"):
            if len(translation):
                continue
            text = translation.text or ""
            lang = translation.get(XML_LANG, "")
            if WHOLE_UNKNOWN_GLOSS.fullmatch(text.strip()):
                set_mixed_unclear(translation, ["", ""])
                resolution = "whole_unknown_gloss_marker"
            elif (text, lang) in placeholders:
                matched.add((text, lang))
                set_mixed_unclear(translation, PLACEHOLDER_PIECE.split(text))
                resolution = "listed_placeholder_pieces"
            else:
                continue
            rows.append(
                {
                    "element": element.tag,
                    "id": element.get("id", ""),
                    "lang": lang,
                    "source_gloss": text,
                    "unclear_count": str(len(translation)),
                    "resolution": resolution,
                }
            )
    unmatched = sorted(placeholders - matched)
    if unmatched:
        raise SystemExit(
            f"{UNCLEAR_PLACEHOLDER_TABLE.name}: rows match no W/M gloss: {unmatched}"
        )
    return rows


def write_tsv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def write_audits(
    source_ids: list[str],
    issue_rows: list[dict[str, str]],
    translation_rows: list[dict[str, str]],
    word_translation_rows: list[dict[str, str]],
    unclear_rows: list[dict[str, str]],
    variants: dict[str, dict[str, str]],
) -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
    write_tsv(
        AUDIT / "unclear_gloss_review.tsv",
        unclear_rows,
        ["element", "id", "lang", "source_gloss", "unclear_count", "resolution"],
    )
    coverage = []
    for sentence_id in source_ids:
        variant = variants.get(sentence_id)
        coverage.append(
            {
                "source_s_id": sentence_id,
                "output_s_ids": variant["output_ids"] if variant else sentence_id,
                "status": "expanded_source_alternatives" if variant else "included",
                "reason": variant["resolution"]
                if variant
                else "source_record_preserved",
            }
        )
    write_tsv(
        AUDIT / "source_coverage.tsv",
        coverage,
        ["source_s_id", "output_s_ids", "status", "reason"],
    )
    write_tsv(
        AUDIT / "issue_1_review.tsv",
        issue_rows,
        ["finding", "rule", "s_id", "resolution", "source_url", "evidence"],
    )
    variant_rows = [
        {
            "source_s_id": sentence_id,
            "output_s_ids": values["output_ids"],
            "source_form": values["source_form"],
            "resolution": values["resolution"],
            "evidence": values["evidence"],
            "audio_disposition": "omitted_shared_multi_alternative_recording",
        }
        for sentence_id, values in variants.items()
    ]
    write_tsv(
        AUDIT / "source_variant_review.tsv",
        variant_rows,
        [
            "source_s_id",
            "output_s_ids",
            "source_form",
            "resolution",
            "evidence",
            "audio_disposition",
        ],
    )
    write_tsv(
        AUDIT / "source_translation_review.tsv",
        translation_rows,
        [
            "s_id",
            "resolution",
            "source_url",
            "frozen_translation",
            "translation",
            "evidence",
        ],
    )
    write_tsv(
        AUDIT / "source_word_translation_review.tsv",
        word_translation_rows,
        [
            "s_id",
            "w_id",
            "resolution",
            "source_url",
            "source_head",
            "translation",
        ],
    )
    (AUDIT / "source_review_summary.md").write_text(
        "# Yedda source review summary\n\n"
        "- Frozen source records: 668\n"
        "- Canonical records after three source-defined alternative expansions: 671\n"
        "- Source records omitted: 0\n"
        "- Audit issue findings reviewed: 9/9\n"
        "- Live-source sentence translation repairs: 24\n"
        "- Exact live-source word glosses restored: 49\n"
        "- Unresolved source or issue findings: 0\n"
        "- Shared recordings omitted from split alternatives: 3\n\n"
        "All other original FORM, W, M, and word-gloss content is carried from "
        "the frozen complete scrape snapshot. Missing source glosses remain "
        "missing rather than being invented. Standard FORM and both PHON tiers "
        "are regenerated with pinned current FormosanBank authority.\n",
        encoding="utf-8",
    )


def annotate_source_segmentation(root: ET.Element) -> None:
    """Record why S652653654_2's two FORM tiers differ, on the original tier.

    The standard tier is machine-owned (POL-002) and is not touched here or
    anywhere downstream of standardize.py; C012 removes the hyphens from it.
    """
    sentence_id, expected, note = SOURCE_SEGMENTATION_NOTE
    sentence = find_sentence(root, sentence_id)
    original = original_form(sentence)
    if original.text != expected:
        raise SystemExit(
            f"Unexpected {sentence_id} source surface: {original.text!r}"
        )
    original.set("notes", note)


def main() -> None:
    actual_hash = sha256(SOURCE)
    if actual_hash != EXPECTED_SOURCE_SHA256:
        raise SystemExit(
            f"Source snapshot hash mismatch: expected {EXPECTED_SOURCE_SHA256}, got {actual_hash}"
        )
    tree = ET.parse(SOURCE)
    root = tree.getroot()
    source_sentences = root.findall("S")
    source_ids = [sentence.get("id", "") for sentence in source_sentences]
    if len(source_ids) != 668 or len(set(source_ids)) != 668 or "" in source_ids:
        raise SystemExit("Frozen source snapshot must contain 668 unique sentence IDs")

    strip_derived_tiers(root)
    spaced = repair_gloss_whitespace(root)
    variants = check_variant_sources(root)
    split_alternatives(root)
    annotate_source_segmentation(root)
    issue_rows = repair_issue_rows(root)
    translation_rows = restore_source_translations(root)
    word_translation_rows = restore_source_word_translations(root)
    correct_word_glosses(root)
    alternates = add_word_alternates(root)
    add_sentence_translation_notes(root)
    output_ids = [sentence.get("id", "") for sentence in root.findall("S")]
    if len(output_ids) != 671 or len(set(output_ids)) != 671:
        raise SystemExit("Canonical pre-QC output must contain 671 unique sentence IDs")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(tree, space="  ")
    unclear_rows = move_glosses_to_notes(root, GLOSS_TO_NOTES_TABLE)
    unclear_rows += move_glosses_to_notes(
        root, UNCERTAIN_GLOSS_TABLE, notes="uncertain", resolution="ruled_uncertain"
    )
    unclear_rows += mark_unclear_glosses(
        root, read_placeholder_table(UNCLEAR_PLACEHOLDER_TABLE)
    )
    tree.write(OUTPUT, encoding="utf-8", xml_declaration=True)
    write_audits(
        source_ids, issue_rows, translation_rows, word_translation_rows, unclear_rows,
        variants,
    )
    print(f"Word glosses with their spaces put back: {spaced}")
    print(f"Words given a second spelling from an \"X or Y\" headword: {alternates}")
    for row in SKIPPED:
        print(f"Skipped, repaired text already present: {row}")
    print(
        f"Built 671 source-backed pre-QC records from {len(source_ids)} frozen records."
    )


if __name__ == "__main__":
    main()
