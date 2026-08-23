#!/usr/bin/env python3
"""Rebuild the Hundred Paiwan Stories XML from the reviewed Word source."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import string
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from paiwan_source import (
    AnalysisUnit,
    SourceSentence,
    SourceStory,
    canonical_word,
    infer_infix_positions,
    insert_markers,
    insertion_hosts,
    normalize_legacy,
    normalized_letters,
    parse_docx,
    split_units,
)


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
COPYRIGHT = (
    "Author permission allows attributed, non-profit derivative use. "
    "For-profit republication of the source as-is is not permitted."
)
MISSING_GLOSS_NOTE = "No source gloss was supplied for final -i."


@dataclass(frozen=True)
class OptionalVariant:
    sentence_id: str
    source_ordinal: int
    word_index: int
    included_token: str
    omitted_sentence_id: str
    rationale: str


@dataclass(frozen=True)
class AlignmentOverride:
    sentence_id: str
    word_index: int
    natural_form: str
    source_morph: str
    source_gloss: str
    canonical_forms: tuple[str, ...]
    canonical_glosses: tuple[str, ...]
    decision: str
    evidence: str


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def load_sentence_ids() -> dict[tuple[int, int], dict[str, str]]:
    rows = read_tsv(DATA / "sentence_id_exceptions.tsv")
    if len(rows) != 30:
        raise ValueError(f"expected 30 sentence ID exceptions, found {len(rows)}")
    result: dict[tuple[int, int], dict[str, str]] = {}
    for row in rows:
        key = (int(row["story_number"]), int(row["source_ordinal"]))
        if key in result:
            raise ValueError(f"duplicate sentence ID exception: {key}")
        result[key] = row
    if set(key for key in result if key[0] == 91) != {
        (91, ordinal) for ordinal in range(1, 30)
    }:
        raise ValueError("story 091 must have an exhaustive 29-row ID mapping")
    return result


def load_optional_variants() -> dict[str, OptionalVariant]:
    rows = read_tsv(DATA / "optional_variants.tsv")
    if len(rows) != 5:
        raise ValueError(f"expected five optional variants, found {len(rows)}")
    result = {}
    for row in rows:
        item = OptionalVariant(
            sentence_id=row["sentence_id"],
            source_ordinal=int(row["source_ordinal"]),
            word_index=int(row["word_index"]),
            included_token=row["included_token"],
            omitted_sentence_id=row["omitted_sentence_id"],
            rationale=row["rationale"],
        )
        if item.sentence_id in result:
            raise ValueError(f"duplicate optional variant: {item.sentence_id}")
        result[item.sentence_id] = item
    return result


def load_alignment_overrides() -> dict[tuple[str, int], AlignmentOverride]:
    rows = read_tsv(DATA / "word_alignment_overrides.tsv")
    if len(rows) != 2:
        raise ValueError(f"expected two word alignment overrides, found {len(rows)}")
    result = {}
    for row in rows:
        item = AlignmentOverride(
            sentence_id=row["sentence_id"],
            word_index=int(row["word_index"]),
            natural_form=row["natural_form"],
            source_morph=row["source_morph"],
            source_gloss=row["source_gloss"],
            canonical_forms=tuple(row["canonical_forms"].split(" | ")),
            canonical_glosses=tuple(row["canonical_glosses"].split(" | ")),
            decision=row["decision"],
            evidence=row["evidence"],
        )
        key = (item.sentence_id, item.word_index)
        if key in result:
            raise ValueError(f"duplicate word alignment override: {key}")
        result[key] = item
    return result


def load_note_extractions() -> dict[str, dict[str, str]]:
    rows = read_tsv(DATA / "translation_note_extractions.tsv")
    if len(rows) != 3:
        raise ValueError(
            f"expected three translation note extractions, found {len(rows)}"
        )
    return {row["sentence_id"]: row for row in rows}


def load_translation_corrections() -> dict[str, dict[str, str]]:
    rows = read_tsv(DATA / "translation_punctuation_corrections.tsv")
    if len(rows) != 1:
        raise ValueError(
            f"expected one translation punctuation correction, found {len(rows)}"
        )
    return {row["sentence_id"]: row for row in rows}


def load_recovered_words() -> dict[str, dict[str, str]]:
    rows = read_tsv(DATA / "recovered_final_words.tsv")
    if len(rows) != 9:
        raise ValueError(f"expected nine recovered final words, found {len(rows)}")
    return {row["sentence_id"]: row for row in rows}


def load_metadata_corrections() -> dict[int, dict[str, str]]:
    rows = read_tsv(DATA / "text_metadata_corrections.tsv")
    if len(rows) != 4:
        raise ValueError(f"expected four TEXT metadata corrections, found {len(rows)}")
    result = {int(row["story_number"]): row for row in rows}
    if set(result) != {81, 91, 92, 98}:
        raise ValueError("unexpected TEXT metadata correction inventory")
    return result


def sentence_id(
    story: SourceStory,
    record: SourceSentence,
    exceptions: dict[tuple[int, int], dict[str, str]],
) -> str:
    default = f"{story.number:03}S{record.source_ordinal}"
    exception = exceptions.get((story.number, record.source_ordinal))
    if exception is None:
        if record.printed_label != f"{record.source_ordinal:03}":
            raise ValueError(
                f"story {story.number:03} source sentence {record.source_ordinal}: "
                f"unexpected printed label {record.printed_label!r}"
            )
        return default
    if record.printed_label != exception["printed_label"]:
        raise ValueError(
            f"story {story.number:03} source sentence {record.source_ordinal}: "
            "printed label differs from the reviewed ID table"
        )
    return exception["stable_sentence_id"]


def form(parent: ET.Element, text: str) -> ET.Element:
    element = ET.SubElement(parent, "FORM", {"kindOf": "original"})
    element.text = text
    return element


def translation(
    parent: ET.Element,
    text: str,
    *,
    notes: str | None = None,
    kind_of: str | None = None,
) -> ET.Element:
    attributes = {XML_LANG: "eng"}
    if kind_of is not None:
        attributes["kindOf"] = kind_of
    if notes:
        attributes["notes"] = notes
    element = ET.SubElement(parent, "TRANSL", attributes)
    element.text = text
    return element


def baseline_original(element: ET.Element) -> str:
    original = element.find("FORM[@kindOf='original']")
    if original is None or original.text is None:
        raise ValueError(f"{element.get('id')}: baseline element lacks original FORM")
    return original.text


def partition_old_morphemes(
    old_forms: list[str],
    new_forms: list[str],
) -> list[tuple[int, int]] | None:
    """Partition new units into the packed units represented by old Ms."""

    old_letters = [normalized_letters(value) for value in old_forms]
    new_letters = [normalized_letters(value) for value in new_forms]

    def solve(old_index: int, new_index: int) -> list[tuple[int, int]] | None:
        if old_index == len(old_letters):
            return [] if new_index == len(new_letters) else None
        remaining_old = len(old_letters) - old_index - 1
        latest_end = len(new_letters) - remaining_old
        combined = ""
        for end in range(new_index + 1, latest_end + 1):
            combined += new_letters[end - 1]
            if combined != old_letters[old_index]:
                continue
            tail = solve(old_index + 1, end)
            if tail is not None:
                return [(new_index, end), *tail]
        return None

    return solve(0, 0)


def assign_morpheme_ids(
    word_id: str,
    m_forms: list[str],
    old_word: ET.Element | None,
) -> tuple[list[str], list[dict[str, str]]]:
    if old_word is None:
        return [f"{word_id}M{index}" for index in range(len(m_forms))], []

    old_morphemes = old_word.findall("M")
    old_ids = [morpheme.get("id") or "" for morpheme in old_morphemes]
    if any(not value for value in old_ids):
        raise ValueError(f"{word_id}: baseline M without an ID")
    if len(old_morphemes) == len(m_forms):
        return old_ids, []
    if len(old_morphemes) > len(m_forms):
        raise ValueError(f"{word_id}: rebuild would remove a published M ID")
    if not old_morphemes:
        return [f"{word_id}M{index}" for index in range(len(m_forms))], []

    old_forms = [baseline_original(morpheme) for morpheme in old_morphemes]
    groups = partition_old_morphemes(old_forms, m_forms)
    if groups is None:
        raise ValueError(
            f"{word_id}: cannot reconcile packed baseline Ms {old_forms!r} "
            f"with source units {m_forms!r}"
        )

    result = [""] * len(m_forms)
    report_rows = []
    for old_id, (start, end) in zip(old_ids, groups):
        result[start] = old_id
        added_ids = []
        for offset, new_index in enumerate(range(start + 1, end)):
            if offset >= len(string.ascii_lowercase):
                raise ValueError(f"{word_id}: too many units expanded from one M")
            new_id = f"{old_id}{string.ascii_lowercase[offset]}"
            result[new_index] = new_id
            added_ids.append(new_id)
        if added_ids:
            report_rows.append(
                {
                    "level": "M",
                    "source_id": old_id,
                    "published_ids": old_id,
                    "rebuild_ids": " | ".join([old_id, *added_ids]),
                    "action": "expand_packed_source_units_without_renumbering",
                }
            )
    if any(not value for value in result) or len(set(result)) != len(result):
        raise ValueError(f"{word_id}: invalid reconciled M IDs {result!r}")
    return result, report_rows


def public_infix_positions(
    units: list[AnalysisUnit],
    old_word: ET.Element | None,
) -> dict[int, int]:
    if old_word is None:
        return {}
    old_morphemes = old_word.findall("M")
    if len(old_morphemes) != len(units):
        return {}
    if any(
        normalized_letters(baseline_original(old)) != normalized_letters(unit.form)
        for old, unit in zip(old_morphemes, units)
    ):
        return {}

    hosts = insertion_hosts(units)
    fixed: dict[int, int] = {}
    for host_index in sorted(set(hosts.values())):
        infix_indexes = [
            index
            for index, host in hosts.items()
            if host == host_index and units[index].role == "infix"
        ]
        if not infix_indexes:
            continue
        root = baseline_original(old_morphemes[host_index])
        positions = []
        letter_position = 0
        for character in root:
            if character == "-":
                positions.append(letter_position)
            else:
                letter_position += 1
        if len(positions) == len(infix_indexes):
            fixed.update(zip(infix_indexes, positions))
    return fixed


def units_for_word(
    sentence: str,
    word_index: int,
    morph: str,
    gloss: str,
    overrides: dict[tuple[str, int], AlignmentOverride],
) -> list[AnalysisUnit]:
    override = overrides.get((sentence, word_index))
    if override is None or sentence == "009S2":
        return split_units(morph, gloss)
    if sentence != "078S4" or word_index != 19:
        raise ValueError(f"unsupported alignment override: {(sentence, word_index)}")
    if normalize_legacy(morph) != override.source_morph:
        raise ValueError("078S4W19 morph source differs from the reviewed override")
    if normalize_legacy(gloss) != override.source_gloss:
        raise ValueError("078S4W19 gloss source differs from the reviewed override")
    if override.canonical_glosses[-1] != "?":
        raise ValueError("078S4W19 must mark its missing final source gloss explicitly")
    return [
        AnalysisUnit("al", "qal", "infix", "="),
        AnalysisUnit("te", "do", "regular", "-"),
        AnalysisUnit("talem", "plant", "regular", "-"),
        AnalysisUnit("i", "?", "regular", ""),
    ]


def align_cells(
    sentence: str,
    record: SourceSentence,
    overrides: dict[tuple[str, int], AlignmentOverride],
) -> tuple[list[str], list[str], list[str]]:
    natural = [normalize_legacy(value) for value in record.natural_cells]
    while natural and not natural[-1]:
        natural.pop()
    morph = [normalize_legacy(value) for value in record.morph_cells]
    gloss = [normalize_legacy(value) for value in record.gloss_cells]

    override = overrides.get((sentence, 7))
    if sentence == "009S2":
        if override is None:
            raise ValueError("009S2W7 alignment override is missing")
        if len(natural) != 7 or len(morph) != 8 or len(gloss) != 8:
            raise ValueError("009S2 source alignment shape changed")
        source_morph = " | ".join(morph[6:])
        source_gloss = " | ".join(gloss[6:])
        if (
            source_morph != override.source_morph
            or source_gloss != override.source_gloss
        ):
            raise ValueError("009S2W7 source differs from the reviewed override")
        morph = [*morph[:6], "-".join(override.canonical_forms)]
        gloss = [*gloss[:6], "-".join(override.canonical_glosses)]

    if not (len(natural) == len(morph) == len(gloss)):
        raise ValueError(
            f"{sentence}: unreviewed source word alignment "
            f"({len(natural)} natural, {len(morph)} morph, {len(gloss)} gloss)"
        )
    return natural, morph, gloss


def strip_optional_marker(value: str, token: str, sentence: str) -> str:
    expected = f"({token})"
    if value != expected:
        raise ValueError(
            f"{sentence}: optional source cell {value!r} differs from {expected!r}"
        )
    return token


def prepare_translation(
    sentence: str,
    record: SourceSentence,
    extractions: dict[str, dict[str, str]],
    corrections: dict[str, dict[str, str]],
) -> tuple[str, str | None]:
    value = record.translation
    notes = list(record.comments)
    correction = corrections.get(sentence)
    if correction is not None:
        if value != correction["source_translation"]:
            raise ValueError(f"{sentence}: translation differs from punctuation review")
        value = correction["corrected_translation"]
    extraction = extractions.get(sentence)
    if extraction is not None:
        suffix = extraction["source_translation_suffix"]
        if not value.endswith(suffix):
            raise ValueError(f"{sentence}: translation note suffix differs from review")
        value = value[: -len(suffix)]
        notes.append(extraction["note_attribute"])
    return value, " | ".join(notes) if notes else None


def build_sentence(
    sentence: str,
    natural: list[str],
    morph: list[str],
    gloss: list[str],
    free_translation: str,
    notes: str | None,
    old_sentence: ET.Element | None,
    overrides: dict[tuple[str, int], AlignmentOverride],
    gap_rows: list[dict[str, str]],
    id_rows: list[dict[str, str]],
    stats: Counter,
) -> ET.Element:
    element = ET.Element("S", {"id": sentence})
    form(element, " ".join(natural))
    translation(element, free_translation, notes=notes)

    old_words = old_sentence.findall("W") if old_sentence is not None else []
    for position, (surface, source_morph, source_gloss) in enumerate(
        zip(natural, morph, gloss), start=1
    ):
        word_id = f"{sentence}W{position}"
        old_word = old_words[position - 1] if position <= len(old_words) else None
        if old_word is not None:
            published_id = old_word.get("id")
            if published_id != word_id:
                raise ValueError(
                    f"{sentence}: expected published W ID {word_id}, found {published_id}"
                )

        units = units_for_word(
            sentence, position, source_morph, source_gloss, overrides
        )
        hosts = insertion_hosts(units)
        fixed = public_infix_positions(units, old_word)
        if hosts:
            positions, score = infer_infix_positions(surface, units, fixed)
        else:
            positions, score = {}, 0
        if score > 3:
            raise ValueError(
                f"{word_id}: source insertion alignment score {score} exceeds review limit"
            )

        host_markers = {}
        inferred_infixes = []
        for host_index in sorted(set(hosts.values())):
            infix_indexes = [
                index
                for index, host in hosts.items()
                if host == host_index and units[index].role == "infix"
            ]
            if not infix_indexes:
                continue
            infix_positions = [positions[index] for index in infix_indexes]
            host_markers[host_index] = insert_markers(
                units[host_index].form,
                [units[index].form for index in infix_indexes],
                infix_positions,
            )
            inferred_infixes.extend(
                index for index in infix_indexes if index not in fixed
            )

        word_form, word_gloss, m_forms = canonical_word(units, host_markers)
        morpheme_ids, expansion_rows = assign_morpheme_ids(word_id, m_forms, old_word)
        id_rows.extend(expansion_rows)
        missing_gloss_word = sentence == "078S4" and position == 19

        word = ET.SubElement(element, "W", {"id": word_id})
        form(word, word_form)
        if word_gloss:
            translation(
                word,
                word_gloss,
                notes=MISSING_GLOSS_NOTE if missing_gloss_word else None,
                kind_of="standard" if missing_gloss_word else "original",
            )
        for unit_index, (unit, m_form, morpheme_id) in enumerate(
            zip(units, m_forms, morpheme_ids)
        ):
            morpheme = ET.SubElement(word, "M", {"id": morpheme_id})
            form(morpheme, m_form)
            if unit.gloss:
                explicit_unknown = missing_gloss_word and unit_index == len(units) - 1
                translation(
                    morpheme,
                    unit.gloss,
                    notes=MISSING_GLOSS_NOTE if explicit_unknown else None,
                    kind_of="standard" if explicit_unknown else "original",
                )
                stats["explicit_unknown_morphemes"] += int(explicit_unknown)
            else:
                stats["unglossed_morphemes"] += 1

        if inferred_infixes:
            gap_rows.append(
                {
                    "sentence_id": sentence,
                    "word_id": word_id,
                    "surface": surface,
                    "source_morph": source_morph,
                    "inferred_infixes": " | ".join(
                        f"{units[index].form}@{positions[index]}"
                        for index in inferred_infixes
                    ),
                    "edit_distance": str(score),
                    "method": "source_surface_alignment",
                }
            )
        stats["words"] += 1
        stats["morphemes"] += len(units)
        stats["public_gap_positions_reused"] += len(fixed)
        stats["source_gap_positions_inferred"] += len(inferred_infixes)
        stats[f"insertion_score_{score}"] += int(bool(hosts))
    return element


def build_corpus(
    source_path: Path,
    baseline_path: Path,
    output_path: Path,
    reports_path: Path,
) -> Counter:
    stories = parse_docx(source_path)
    baseline_files = sorted(baseline_path.glob("PaiwanCh2_*.xml"))
    if len(baseline_files) != 100:
        raise ValueError(
            f"expected 100 baseline XML files, found {len(baseline_files)}"
        )

    id_exceptions = load_sentence_ids()
    optional_variants = load_optional_variants()
    alignment_overrides = load_alignment_overrides()
    note_extractions = load_note_extractions()
    translation_corrections = load_translation_corrections()
    recovered_words = load_recovered_words()
    metadata_corrections = load_metadata_corrections()

    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True)
    if reports_path.exists():
        shutil.rmtree(reports_path)
    reports_path.mkdir(parents=True)

    gap_rows: list[dict[str, str]] = []
    id_rows: list[dict[str, str]] = []
    stats: Counter = Counter()
    seen_sentences = set()
    published_ids: set[str] = set()
    rebuilt_ids: set[str] = set()

    for story in stories:
        baseline_file = baseline_path / f"PaiwanCh2_{story.number:03}.xml"
        baseline_root = ET.parse(baseline_file).getroot()
        baseline_file_ids = {
            identifier
            for item in baseline_root.iter()
            if (identifier := item.get("id")) is not None
        }
        if len(baseline_file_ids) != sum(
            item.get("id") is not None for item in baseline_root.iter()
        ):
            raise ValueError(f"{baseline_file.name}: duplicate published element ID")
        overlap = published_ids & baseline_file_ids
        if overlap:
            raise ValueError(
                f"published element IDs repeat across files: {sorted(overlap)[:3]}"
            )
        published_ids.update(baseline_file_ids)
        correction = metadata_corrections.get(story.number)
        baseline_source = baseline_root.get("source")
        if correction is None:
            if baseline_source != story.source_label:
                raise ValueError(
                    f"story {story.number:03}: unreviewed source metadata difference"
                )
            source_metadata = story.source_label
        else:
            recorded_baseline = correction["baseline_source"]
            if recorded_baseline == "<missing>":
                recorded_baseline = None
            if baseline_source != recorded_baseline:
                raise ValueError(
                    f"story {story.number:03}: baseline metadata differs from review"
                )
            source_metadata = correction["corrected_source"]
            expected_source = story.source_label or story.title
            if source_metadata != expected_source:
                raise ValueError(
                    f"story {story.number:03}: corrected metadata differs from DOCX"
                )
        baseline_sentences = {
            sentence.get("id") or "": sentence
            for sentence in baseline_root.findall("S")
        }
        root_attributes = {
            "id": baseline_root.get("id") or "",
            XML_LANG: "pwn",
            "copyright": COPYRIGHT,
            "citation": baseline_root.get("citation") or "",
            "BibTeX_citation": baseline_root.get("BibTeX_citation") or "",
            "source": source_metadata or "",
            "dialect": baseline_root.get("dialect") or "unknown",
        }
        if any(
            not root_attributes[key]
            for key in ("id", "citation", "BibTeX_citation", "source")
        ):
            raise ValueError(f"story {story.number:03}: incomplete TEXT metadata")
        rebuilt_root = ET.Element("TEXT", root_attributes)

        for record in story.sentences:
            sid = sentence_id(story, record, id_exceptions)
            if sid in seen_sentences:
                raise ValueError(f"duplicate rebuilt sentence ID: {sid}")
            seen_sentences.add(sid)
            natural, morph, gloss = align_cells(sid, record, alignment_overrides)
            variant = optional_variants.get(sid)
            if variant is not None:
                if variant.source_ordinal != record.source_ordinal:
                    raise ValueError(f"{sid}: optional variant source ordinal changed")
                index = variant.word_index - 1
                natural[index] = strip_optional_marker(
                    natural[index], variant.included_token, sid
                )

            free_translation, notes = prepare_translation(
                sid,
                record,
                note_extractions,
                translation_corrections,
            )
            old_sentence = baseline_sentences.get(sid)
            if sid != "091S0" and old_sentence is None:
                raise ValueError(f"{sid}: published sentence ID disappeared")
            rebuilt = build_sentence(
                sid,
                natural,
                morph,
                gloss,
                free_translation,
                notes,
                old_sentence,
                alignment_overrides,
                gap_rows,
                id_rows,
                stats,
            )
            rebuilt_root.append(rebuilt)
            stats["source_sentences"] += 1

            if sid == "091S0":
                id_rows.append(
                    {
                        "level": "S",
                        "source_id": "story091_source001",
                        "published_ids": "",
                        "rebuild_ids": sid,
                        "action": "add_omitted_source_sentence_without_renumbering",
                    }
                )

            recovered = recovered_words.get(sid)
            if recovered is not None:
                expected_word_id = f"{sid}W{len(natural)}"
                if recovered["word_id"] != expected_word_id:
                    raise ValueError(f"{sid}: recovered final-word ID changed")
                if natural[-1] != recovered["word"]:
                    raise ValueError(f"{sid}: recovered final word differs from review")
                id_rows.append(
                    {
                        "level": "W",
                        "source_id": f"DOCX_page_{recovered['rendered_docx_page']}",
                        "published_ids": "",
                        "rebuild_ids": recovered["word_id"],
                        "action": "restore_truncated_source_final_word",
                    }
                )

            if variant is not None:
                omitted_sid = variant.omitted_sentence_id
                if omitted_sid in seen_sentences:
                    raise ValueError(f"duplicate optional sentence ID: {omitted_sid}")
                seen_sentences.add(omitted_sid)
                remove_index = variant.word_index - 1
                omitted = build_sentence(
                    omitted_sid,
                    [*natural[:remove_index], *natural[remove_index + 1 :]],
                    [*morph[:remove_index], *morph[remove_index + 1 :]],
                    [*gloss[:remove_index], *gloss[remove_index + 1 :]],
                    free_translation,
                    notes,
                    None,
                    alignment_overrides,
                    gap_rows,
                    id_rows,
                    stats,
                )
                rebuilt_root.append(omitted)
                stats["optional_variant_sentences"] += 1
                id_rows.append(
                    {
                        "level": "S",
                        "source_id": sid,
                        "published_ids": sid,
                        "rebuild_ids": f"{sid} | {omitted_sid}",
                        "action": "expand_optional_source_token_to_complete_sentences",
                    }
                )

        rebuilt_file_ids = {
            identifier
            for item in rebuilt_root.iter()
            if (identifier := item.get("id")) is not None
        }
        if len(rebuilt_file_ids) != sum(
            item.get("id") is not None for item in rebuilt_root.iter()
        ):
            raise ValueError(f"{baseline_file.name}: duplicate rebuilt element ID")
        overlap = rebuilt_ids & rebuilt_file_ids
        if overlap:
            raise ValueError(
                f"rebuilt element IDs repeat across files: {sorted(overlap)[:3]}"
            )
        rebuilt_ids.update(rebuilt_file_ids)
        ET.indent(rebuilt_root, space="    ")
        output_file = output_path / baseline_file.name
        ET.ElementTree(rebuilt_root).write(
            output_file,
            encoding="utf-8",
            xml_declaration=True,
        )
        stats["stories"] += 1

    if set(optional_variants) - seen_sentences:
        raise ValueError("not every optional variant was applied")
    if set(note_extractions) - seen_sentences:
        raise ValueError("not every translation note extraction was applied")
    if set(translation_corrections) - seen_sentences:
        raise ValueError("not every translation punctuation correction was applied")
    if set(recovered_words) - seen_sentences:
        raise ValueError("not every recovered final word was applied")
    if stats["stories"] != 100 or stats["source_sentences"] != 2916:
        raise ValueError(f"unexpected rebuild inventory: {dict(stats)}")
    if stats["optional_variant_sentences"] != 5:
        raise ValueError("expected five complete omitted-token sentence variants")
    if published_ids - rebuilt_ids:
        missing = sorted(published_ids - rebuilt_ids)
        raise ValueError(f"published element IDs disappeared: {missing[:5]}")
    if len(published_ids) != 64198 or len(rebuilt_ids) != 64515:
        raise ValueError(
            "unexpected published/rebuilt element ID inventory: "
            f"{len(published_ids)}/{len(rebuilt_ids)}"
        )
    stats["published_ids_preserved"] = len(published_ids)
    stats["rebuilt_ids"] = len(rebuilt_ids)
    stats["sentences"] = stats["source_sentences"] + stats["optional_variant_sentences"]
    stats["alignment_overrides"] = len(alignment_overrides)
    stats["metadata_corrections"] = len(metadata_corrections)
    stats["note_extractions"] = len(note_extractions)
    stats["recovered_final_words"] = len(recovered_words)
    stats["translation_punctuation_corrections"] = len(translation_corrections)
    if stats["explicit_unknown_morphemes"] != 1:
        raise ValueError("expected one explicit marker for a missing source gloss")
    if stats["unglossed_morphemes"] != 0:
        raise ValueError("unexpected unglossed source morpheme")

    write_tsv(
        reports_path / "gap_inference.tsv",
        gap_rows,
        (
            "sentence_id",
            "word_id",
            "surface",
            "source_morph",
            "inferred_infixes",
            "edit_distance",
            "method",
        ),
    )
    write_tsv(
        reports_path / "id_reconciliation.tsv",
        sorted(id_rows, key=lambda row: (row["rebuild_ids"], row["level"])),
        ("level", "source_id", "published_ids", "rebuild_ids", "action"),
    )
    with (reports_path / "rebuild_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(dict(sorted(stats.items())), handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return stats


def write_tsv(
    path: Path,
    rows: list[dict[str, str]],
    fields: tuple[str, ...],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            delimiter="\t",
            fieldnames=fields,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "Private" / "source" / "Paiwan Ch2 Preprocessed.docx",
    )
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "XML" / "Paiwan")
    parser.add_argument("--reports", type=Path, default=ROOT / "reports" / "rebuild")
    args = parser.parse_args()
    stats = build_corpus(
        args.source.resolve(),
        args.baseline.resolve(),
        args.output.resolve(),
        args.reports.resolve(),
    )
    print(json.dumps(dict(sorted(stats.items())), ensure_ascii=False))


if __name__ == "__main__":
    main()
