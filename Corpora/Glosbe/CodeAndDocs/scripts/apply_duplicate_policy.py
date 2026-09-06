from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = ROOT.parent
XML_ROOT = CORPUS_ROOT / "XML"
INDEX_PATH = ROOT / "data/processed/xml_index.csv"
REPORT_PATH = ROOT / "data/processed/current_duplicate_sentence_removals.csv"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_shared_module(path: Path):
    spec = importlib.util.spec_from_file_location("formosanbank_remove_duplicates", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load shared duplicate policy: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shared-script", type=Path, required=True)
    args = parser.parse_args()

    shared = load_shared_module(args.shared_script.resolve())
    removals = shared.plan_removals(str(XML_ROOT), scope="file", tier="standard")
    shared.apply_removals(removals)

    with INDEX_PATH.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        fields = list(reader.fieldnames or [])
        index_rows = list(reader)

    removal_map: dict[tuple[str, str], tuple[str, str]] = {}
    report_rows = []
    for removed_file, removed_id, kept_file, kept_id in removals:
        removed_rel = str(Path(removed_file).resolve().relative_to(CORPUS_ROOT))
        kept_rel = str(Path(kept_file).resolve().relative_to(CORPUS_ROOT))
        removal_map[(removed_rel, removed_id)] = (kept_rel, kept_id)
        report_rows.append(
            {
                "file": removed_rel,
                "kept_sentence_id": kept_id,
                "removed_sentence_id": removed_id,
            }
        )

    for row in index_rows:
        replacement = removal_map.get((row["xml_file"], row["sentence_id"]))
        if replacement:
            row["xml_file"], row["sentence_id"] = replacement

    xml_groups: dict[tuple[str, str], tuple[str, list[str]]] = {}
    for path in sorted(XML_ROOT.rglob("*.xml")):
        rel_path = str(path.relative_to(CORPUS_ROOT))
        for sentence in ET.parse(path).getroot().findall("S"):
            xml_groups[(rel_path, sentence.get("id", ""))] = (
                sentence.findtext("FORM", default=""),
                [translation.text or "" for translation in sentence.findall("TRANSL")],
            )

    rows_by_group: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in index_rows:
        rows_by_group[(row["xml_file"], row["sentence_id"])].append(row)

    synchronized_rows = []
    for key, (form, translations) in xml_groups.items():
        rows = rows_by_group.get(key, [])
        unique_rows = []
        seen_target_hashes = set()
        for row in rows:
            target_hash = row["target_sentence_sha256"]
            if target_hash in seen_target_hashes:
                continue
            seen_target_hashes.add(target_hash)
            unique_rows.append(row)
        if len(unique_rows) != len(translations):
            raise RuntimeError(
                f"Index/XML translation count mismatch for {key}: "
                f"{len(unique_rows)} index rows and {len(translations)} translations"
            )
        for row, translation in zip(unique_rows, translations, strict=True):
            row["source_sentence_sha256"] = sha256_text(form)
            row["target_sentence_sha256"] = sha256_text(translation)
            row["pair_sha256"] = sha256_text(form + "\n" + translation)
            synchronized_rows.append(row)

    if len(synchronized_rows) != sum(len(translations) for _, translations in xml_groups.values()):
        raise RuntimeError("XML index does not cover every canonical translation")

    write_csv(INDEX_PATH, synchronized_rows, fields)
    write_csv(
        REPORT_PATH,
        report_rows,
        ["file", "kept_sentence_id", "removed_sentence_id"],
    )
    print(f"Applied {len(removals)} current duplicate removals")


if __name__ == "__main__":
    main()
