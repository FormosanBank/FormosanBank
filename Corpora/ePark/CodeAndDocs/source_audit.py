#!/usr/bin/env python3
"""Audit and restore ePark source-owned XML tiers from the committed source files."""

from __future__ import annotations

import argparse
import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
SMART_QUOTES = str.maketrans(
    {
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
        "「": '"',
        "」": '"',
        "『": '"',
        "』": '"',
    }
)

TOPIC_SLUGS = {
    "九階教材": "jiu_jie_jiao_cai_nine_level_materials",
    "學習詞表": "xue_xi_ci_biao_learning_vocabulary",
    "生活會話篇": "sheng_huo_hui_hua_pian_daily_conversation",
    "族語短文": "zu_yu_duan_wen_indigenous_language_essays",
    "文化篇": "wen_hua_pian_cultural_section",
    "閱讀書寫篇": "yue_du_shu_xie_pian_reading_writing",
    "情境族語": "qing_jing_zu_yu_contextual_indigenous_language",
    "句型篇國中": "ju_xing_pian_guo_zhong_sentence_patterns_junior_high",
    "句型篇高中": "ju_xing_pian_gao_zhong_sentence_patterns_senior_high",
    "圖畫故事篇": "tu_hua_gu_shi_pian_picture_story",
    "繪本平台": "hui_ben_ping_tai_picture_book_platform",
}

ENGLISH_TOPICS = {"學習詞表", "族語短文", "情境族語"}
PATTERN_TYPES = {
    "1": "word",
    "2": "sentence",
    "3": "recognize",
    "4": "choiceOne",
    "5": "choiceTwo",
    "6": "match",
    "7": "choiceThree",
    "8": "oralReading",
    "9": "dialogue",
    "10": "pictureTalk",
}


@dataclass(frozen=True)
class SourceRecord:
    slug: str
    dialect: str
    level: str
    record_id: str
    form: str
    translations: tuple[tuple[str, str], ...]
    source_file: str
    source_locator: str
    audio_file: str | None = None
    audio_url: str | None = None

    @property
    def key(self) -> tuple[str, str, str, str]:
        return self.slug, self.dialect, self.level, self.record_id


@dataclass
class Inventory:
    records: dict[tuple[str, str, str, str], SourceRecord]
    decisions: Counter[str]
    malformed_csv_rows: list[dict[str, object]]


def source_text(value: str | None) -> str:
    """Preserve source content while removing line-edge transport whitespace."""
    if value is None:
        return ""
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.strip() for line in normalized.split("\n")).strip()


def canonical_form_text(value: str | None) -> str:
    """Apply current FORM quote and annotation policy to source text."""
    return source_text(value).translate(SMART_QUOTES).replace("*", "")


def load_dialects(repo: Path) -> dict[str, str]:
    with (repo / "dialects.csv").open(encoding="utf-8-sig", newline="") as handle:
        return {row["idx"].zfill(2): row["dialect"] for row in csv.DictReader(handle)}


def add_record(inventory: Inventory, record: SourceRecord) -> None:
    if record.key in inventory.records:
        raise ValueError(f"duplicate source key: {record.key}")
    inventory.records[record.key] = record
    inventory.decisions["included_records"] += 1


def parse_malformed_three_column_row(row: list[str]) -> tuple[str, str, str]:
    """Recover original, Chinese, and URL from an export row split on source commas."""
    if len(row) >= 3:
        return ",".join(row[:-2]), row[-2], row[-1]

    payload, url = row
    matches = list(re.finditer(r',(?=["“「『]?[^\x00-\x7f]*[\u3400-\u9fff])', payload))
    if not matches:
        raise ValueError(f"cannot recover two-column row: {row!r}")
    split = matches[-1].start()
    return payload[:split], payload[split + 1 :], url


def parse_epark2_row(topic: str, row: list[str]) -> tuple[str, tuple[tuple[str, str], ...], str]:
    expected = 4 if topic in ENGLISH_TOPICS else 3
    if len(row) == expected:
        if expected == 4:
            form, english, chinese, url = row
            translations = (("zho", source_text(chinese)),)
            if source_text(english):
                translations += (("eng", source_text(english)),)
            return source_text(form), translations, url
        form, chinese, url = row
        return source_text(form), (("zho", source_text(chinese)),), url

    if topic == "族語短文":
        form, english, chinese, url = row[0], ",".join(row[1:-2]), row[-2], row[-1]
        return source_text(form), (
            ("zho", source_text(chinese)),
            ("eng", source_text(english)),
        ), url

    if topic == "情境族語":
        form, english, chinese, url = ",".join(row[:-3]), row[-3], row[-2], row[-1]
        return source_text(form), (
            ("zho", source_text(chinese)),
            ("eng", source_text(english)),
        ), url

    form, chinese, url = parse_malformed_three_column_row(row)
    return source_text(form), (("zho", source_text(chinese)),), url


def inventory_epark1_and_2(repo: Path, inventory: Inventory, dialects: dict[str, str]) -> None:
    for version in ("ePark_1", "ePark_2"):
        for source_file in sorted((repo / version).glob("*/*.csv")):
            topic = source_file.parent.name
            slug = TOPIC_SLUGS[topic]
            idx = source_file.name.split()[0].zfill(2)
            dialect = dialects[idx]
            with source_file.open(encoding="utf-8-sig", newline="") as handle:
                rows = csv.reader(handle)
                last_sentence_id: str | None = None
                for row_number, row in enumerate(rows):
                    inventory.decisions["source_csv_rows"] += 1
                    audio_prefix = f"{slug}_1" if topic in {"文化篇", "族語短文"} else slug
                    if version == "ePark_1":
                        form, chinese, url = row
                        if "C" in url.rsplit("/", 1)[-1]:
                            inventory.decisions["excluded_epark1_word_rows"] += 1
                            continue
                        last_sentence_id = str(row_number)
                        record = SourceRecord(
                            slug,
                            dialect,
                            "S",
                            last_sentence_id,
                            source_text(form),
                            (("zho", source_text(chinese)),),
                            str(source_file.relative_to(repo)),
                            f"row {row_number + 1}",
                        )
                    else:
                        expected = 4 if topic in ENGLISH_TOPICS else 3
                        if len(row) != expected:
                            inventory.decisions["reconstructed_malformed_csv_rows"] += 1
                            inventory.malformed_csv_rows.append(
                                {
                                    "file": str(source_file.relative_to(repo)),
                                    "row": row_number + 1,
                                    "columns": len(row),
                                }
                            )
                        form, translations, url = parse_epark2_row(topic, row)
                        record = SourceRecord(
                            slug,
                            dialect,
                            "S",
                            str(row_number),
                            form,
                            translations,
                            str(source_file.relative_to(repo)),
                            f"row {row_number + 1}",
                            f"{audio_prefix}_{dialect}_{row_number}.wav",
                            source_text(url),
                        )
                    add_record(inventory, record)


def item_text(item: ET.Element, tag: str) -> str | None:
    element = item.find(tag)
    return None if element is None else source_text(element.text)


def joined_parts(item: ET.Element, tags: Iterable[str]) -> str:
    return " ".join(value for tag in tags if (value := item_text(item, tag)))


def extract_pattern_item(topic: str, item: ET.Element) -> list[tuple[str, str]]:
    type_id = item_text(item, "typeId")
    if not type_id or type_id not in PATTERN_TYPES:
        return []
    prefix = PATTERN_TYPES[type_id]
    single_types = {"1", "3", "10"}
    if topic == "句型篇高中":
        single_types.add("7")
    if type_id in single_types:
        form, translation = item_text(item, f"{prefix}Ab"), item_text(item, f"{prefix}Ch")
        return [] if not form else [(form, translation or "")]

    single_audio_types = {"2"} if topic == "句型篇國中" else {"2", "4"}
    if type_id in single_audio_types:
        forms: list[str] = []
        translations: list[str] = []
        for suffix in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            form = item_text(item, f"{prefix}{suffix}Ab")
            translation = item_text(item, f"{prefix}{suffix}Ch")
            if not form or translation is None:
                break
            forms.append(form)
            if translation:
                translations.append(translation)
        return [(" ".join(forms), " ".join(translations))] if forms else []

    if type_id == "6" and topic == "句型篇國中":
        records: list[tuple[str, str]] = []
        for suffix in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            left = item_text(item, f"match{suffix}AbA")
            right = item_text(item, f"match{suffix}AbB")
            translation_left = item_text(item, f"match{suffix}ChA")
            translation_right = item_text(item, f"match{suffix}ChB")
            if left is None or translation_left is None:
                break
            records.append(
                (
                    " ".join(value for value in (left, right) if value),
                    " ".join(value for value in (translation_left, translation_right) if value),
                )
            )
        return records

    records = []
    for suffix in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        form = item_text(item, f"{prefix}{suffix}Ab")
        translation = item_text(item, f"{prefix}{suffix}Ch")
        if form is None or translation is None:
            break
        records.append((form, translation))
    return records


def inventory_pattern_topics(repo: Path, inventory: Inventory, dialects: dict[str, str]) -> None:
    for directory, topic in (("1.句型篇國中", "句型篇國中"), ("2.句型篇高中", "句型篇高中")):
        slug = TOPIC_SLUGS[topic]
        for source_file in sorted((repo / "ePark_3" / directory / "xml").glob("*/*.xml")):
            idx = source_file.parent.name.zfill(2)
            dialect = dialects[idx]
            root = ET.parse(source_file).getroot()
            for item_number, item in enumerate(root.findall(".//item"), 1):
                inventory.decisions["source_epark3_items"] += 1
                auto_id = item_text(item, "autoId")
                class_id = item_text(item, "classId")
                if not auto_id or not class_id:
                    inventory.decisions["excluded_epark3_incomplete_items"] += 1
                    continue
                extracted = extract_pattern_item(topic, item)
                if not extracted:
                    inventory.decisions["excluded_epark3_empty_items"] += 1
                    continue
                single_audio_types = {"2"} if topic == "句型篇國中" else {"2", "4"}
                type_id = item_text(item, "typeId")
                if type_id in single_audio_types:
                    prefix = PATTERN_TYPES[type_id]
                    populated_fields = sum(
                        item_text(item, f"{prefix}{suffix}Ab") is not None
                        for suffix in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    )
                    if populated_fields > 1:
                        inventory.decisions["combined_source_fields_single_audio"] += 1
                for offset, (form, translation) in enumerate(extracted):
                    suffix = "" if offset == 0 else f"_{offset}"
                    add_record(
                        inventory,
                        SourceRecord(
                            slug,
                            dialect,
                            "S",
                            f"{class_id}_{auto_id}{suffix}",
                            form,
                            (("zho", translation),),
                            str(source_file.relative_to(repo)),
                            f"item {item_number}",
                            f"{auto_id}{suffix}.wav",
                        ),
                    )


def inventory_csv_topics(repo: Path, inventory: Inventory, dialects: dict[str, str]) -> None:
    configs = (
        ("3.圖畫故事篇", "圖畫故事篇", "klokah_story_sentence.csv"),
        ("9.繪本平台", "繪本平台", "klokah_PBC_sentence.csv"),
    )
    for directory, topic, filename in configs:
        slug = TOPIC_SLUGS[topic]
        source_file = repo / "ePark_3" / directory / filename
        seen: set[str] = set()
        with source_file.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            next(reader)
            for row_number, row in enumerate(reader, 2):
                inventory.decisions["source_epark3_csv_rows"] += 1
                record_id, text_id, idx, form, translation = row[:5]
                if record_id in seen:
                    inventory.decisions["excluded_epark3_duplicate_ids"] += 1
                    continue
                seen.add(record_id)
                if not source_text(form):
                    reason = (
                        "excluded_epark3_blank_rows"
                        if not source_text(translation)
                        else "excluded_epark3_translation_only_rows"
                    )
                    inventory.decisions[reason] += 1
                    continue
                add_record(
                    inventory,
                    SourceRecord(
                        slug,
                        dialects[idx.zfill(2)],
                        "S",
                        record_id,
                        source_text(form),
                        (("zho", source_text(translation)),),
                        str(source_file.relative_to(repo)),
                        f"row {row_number}",
                        f"{slug}_{dialects[idx.zfill(2)]}_{record_id}.wav",
                        f"https://web.klokah.tw/text/sound/{text_id}/{record_id}.mp3",
                    ),
                )


def build_inventory(repo: Path) -> Inventory:
    inventory = Inventory({}, Counter(), [])
    dialects = load_dialects(repo)
    inventory_epark1_and_2(repo, inventory, dialects)
    inventory_pattern_topics(repo, inventory, dialects)
    inventory_csv_topics(repo, inventory, dialects)
    return inventory


def direct_children(element: ET.Element, tag: str) -> list[ET.Element]:
    return [child for child in element if child.tag == tag]


def original_form(element: ET.Element) -> ET.Element | None:
    return next(
        (child for child in direct_children(element, "FORM") if child.get("kindOf") == "original"),
        None,
    )


def replace_translations(element: ET.Element, translations: tuple[tuple[str, str], ...]) -> None:
    for child in direct_children(element, "TRANSL"):
        element.remove(child)
    insertion_index = next(
        (index for index, child in enumerate(element) if child.tag in {"W", "AUDIO"}),
        len(element),
    )
    for language, text in translations:
        translation = ET.Element("TRANSL", {XML_LANG: language})
        translation.text = text
        element.insert(insertion_index, translation)
        insertion_index += 1


def remove_original_phonology(element: ET.Element) -> int:
    removed = 0
    for child in list(element):
        if child.tag == "PHON" and child.get("kindOf") == "original":
            element.remove(child)
            removed += 1
    return removed


def canonical_index(
    xml_root: Path,
) -> tuple[
    dict[tuple[str, str, str, str], ET.Element],
    dict[tuple[str, str, str, str], Path],
    dict[int, ET.Element],
    dict[Path, ET.ElementTree],
]:
    index: dict[tuple[str, str, str, str], ET.Element] = {}
    paths: dict[tuple[str, str, str, str], Path] = {}
    parents: dict[int, ET.Element] = {}
    trees: dict[Path, ET.ElementTree] = {}
    for path in sorted(xml_root.rglob("*.xml")):
        tree = ET.parse(path)
        root = tree.getroot()
        slug = path.relative_to(xml_root).parts[0]
        dialect = path.stem
        trees[path] = tree
        for sentence in root.findall("S"):
            key = slug, dialect, "S", sentence.get("id", "")
            if key in index:
                raise ValueError(f"duplicate canonical key: {key}")
            index[key] = sentence
            paths[key] = path
            for word in sentence.findall("W"):
                word_key = slug, dialect, "W", word.get("id", "")
                if word_key in index:
                    raise ValueError(f"duplicate canonical key: {word_key}")
                index[word_key] = word
                paths[word_key] = path
                parents[id(word)] = sentence
    return index, paths, parents, trees


def audit_canonical(repo: Path, xml_root: Path, apply: bool) -> dict[str, object]:
    inventory = build_inventory(repo)
    inventory.decisions["canonicalized_source_forms_for_policy"] = sum(
        record.form != canonical_form_text(record.form) for record in inventory.records.values()
    )
    canonical, canonical_paths, parents, trees = canonical_index(xml_root)
    findings = Counter()
    metrics = Counter()
    touched: set[Path] = set()

    for key, record in inventory.records.items():
        element = canonical.get(key)
        if element is None:
            findings["missing_canonical_records"] += 1
            continue
        form = original_form(element)
        expected_form = canonical_form_text(record.form)
        if form is None:
            findings["missing_original_form"] += 1
        elif (form.text or "") != expected_form:
            findings["source_form_mismatches"] += 1
            if apply:
                form.text = expected_form
                touched.add(canonical_paths[key])
        actual_translations = tuple(
            (child.get(XML_LANG, ""), child.text or "")
            for child in direct_children(element, "TRANSL")
        )
        if actual_translations != record.translations:
            findings["source_translation_mismatches"] += 1
            if apply:
                replace_translations(element, record.translations)
                touched.add(canonical_paths[key])
        audios = direct_children(element, "AUDIO")
        if record.audio_file is None:
            metrics["source_records_without_audio"] += 1
        elif not audios:
            metrics["source_audio_unavailable_in_canonical"] += 1
        elif len(audios) > 1:
            findings["multiple_audio_elements"] += 1
        else:
            audio = audios[0]
            metrics["source_audio_references_verified"] += 1
            if audio.get("file") != record.audio_file:
                findings["source_audio_file_mismatches"] += 1
                if apply:
                    audio.set("file", record.audio_file)
                    touched.add(canonical_paths[key])
            actual_url = audio.get("url")
            if actual_url != record.audio_url:
                findings["source_audio_url_mismatches"] += 1
                if apply:
                    if record.audio_url is None:
                        audio.attrib.pop("url", None)
                    else:
                        audio.set("url", record.audio_url)
                    touched.add(canonical_paths[key])

    for key, element in canonical.items():
        if key[2] == "W":
            findings["unsafe_epark1_words"] += 1
            if apply:
                parent = parents[id(element)]
                parent.remove(element)
                touched.add(canonical_paths[key])
            continue
        if key not in inventory.records:
            findings["unexpected_canonical_records"] += 1
        for standard in (
            child for child in direct_children(element, "FORM") if child.get("kindOf") == "standard"
        ):
            normalized_standard = canonical_form_text(standard.text).replace("*", "")
            if (standard.text or "") != normalized_standard:
                findings["noncanonical_standard_form_annotations"] += 1
                if apply:
                    standard.text = normalized_standard
                    touched.add(canonical_paths[key])
        for phon in (
            child for child in direct_children(element, "PHON") if child.get("kindOf") == "standard"
        ):
            normalized_phon = source_text(phon.text)
            if text := phon.text:
                if text != normalized_phon:
                    findings["noncanonical_standard_phon_whitespace"] += 1
                    if apply:
                        phon.text = normalized_phon
                        touched.add(canonical_paths[key])
        removed = remove_original_phonology(element) if apply else sum(
            child.tag == "PHON" and child.get("kindOf") == "original" for child in element
        )
        if removed:
            findings["unsupported_original_phonology"] += removed
            if apply:
                touched.add(canonical_paths[key])
        if key[0] == TOPIC_SLUGS["九階教材"]:
            audios = direct_children(element, "AUDIO")
            if audios:
                findings["unsafe_epark1_audio"] += len(audios)
            if apply and audios:
                for audio in audios:
                    element.remove(audio)
                touched.add(canonical_paths[key])

    if apply:
        for path in sorted(touched):
            tree = trees[path]
            ET.indent(tree, space="    ")
            tree.write(path, encoding="utf-8", xml_declaration=True, short_empty_elements=True)

    return {
        "source_inventory": dict(sorted(inventory.decisions.items())),
        "canonical_findings": dict(sorted(findings.items())),
        "canonical_metrics": dict(sorted(metrics.items())),
        "source_records": len(inventory.records),
        "canonical_records_before_apply": len(canonical),
        "malformed_csv_rows": inventory.malformed_csv_rows,
        "files_touched": len(touched),
        "applied": apply,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--xml", type=Path, default=Path("XML"))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    repo = args.repo.resolve()
    xml_root = args.xml if args.xml.is_absolute() else repo / args.xml
    report = audit_canonical(repo, xml_root, args.apply)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.report:
        report_path = args.report if args.report.is_absolute() else repo / args.report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    hard_keys = {"missing_canonical_records", "missing_original_form", "unexpected_canonical_records"}
    if not args.apply:
        hard_keys.update(report["canonical_findings"])
    hard = sum(report["canonical_findings"].get(key, 0) for key in hard_keys)
    return 1 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main())
