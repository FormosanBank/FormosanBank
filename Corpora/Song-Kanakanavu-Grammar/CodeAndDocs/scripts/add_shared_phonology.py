#!/usr/bin/env python3
"""Run shared Ortho113 phonology without changing source FORM tiers.

The book's acute vowels mark stress, not distinct orthographic segments. This
wrapper folds those marks only in a temporary copy, runs FormosanBank's shared
phonology utility there, restores every original FORM exactly, and installs the
resulting PHON tiers. It does not define or override any phonology mapping.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from fold_standard_stress import fold_stress


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_XML_PATH = ROOT.parent / "XML"
PARENT_TAGS = {"S", "W", "M"}


@dataclass(frozen=True)
class FormSnapshot:
    text: str | None
    attributes: dict[str, str]


def xml_files(path: Path) -> list[Path]:
    return [path] if path.is_file() else sorted(path.rglob("*.xml"))


def original_forms(root: ET.Element) -> dict[str, ET.Element]:
    forms: dict[str, ET.Element] = {}
    for parent in root.iter():
        if parent.tag not in PARENT_TAGS:
            continue
        identifier = parent.get("id", "")
        matches = parent.findall("./FORM[@kindOf='original']")
        if len(matches) != 1:
            raise ValueError(
                f"{identifier or '<missing id>'} has {len(matches)} original FORMs"
            )
        if not identifier or identifier in forms:
            raise ValueError(f"Missing or duplicate tier parent id: {identifier!r}")
        forms[identifier] = matches[0]
    return forms


def fold_temporary_originals(path: Path) -> tuple[int, dict[str, FormSnapshot]]:
    tree = ET.parse(path)
    root = tree.getroot()
    forms = original_forms(root)
    snapshots = {
        identifier: FormSnapshot(form.text, dict(form.attrib))
        for identifier, form in forms.items()
    }
    changed = 0
    for form in forms.values():
        folded = fold_stress(form.text or "")
        if folded != (form.text or ""):
            form.text = folded
            changed += 1
    ET.indent(root, space="  ")
    tree.write(path, encoding="UTF-8", xml_declaration=True)
    return changed, snapshots


def restore_originals_and_install(
    processed_path: Path,
    destination: Path,
    snapshots: dict[str, FormSnapshot],
) -> None:
    tree = ET.parse(processed_path)
    root = tree.getroot()
    forms = original_forms(root)
    if set(forms) != set(snapshots):
        raise ValueError(f"Tier parent IDs changed while processing {destination}")
    for identifier, form in forms.items():
        snapshot = snapshots[identifier]
        form.text = snapshot.text
        form.attrib.clear()
        form.attrib.update(snapshot.attributes)

    for parent in root.iter():
        if parent.tag not in PARENT_TAGS:
            continue
        if parent.find("./PHON[@kindOf='original']") is None:
            raise ValueError(f"Missing original PHON for {parent.get('id')}")
        if (
            parent.find("./FORM[@kindOf='standard']") is not None
            and parent.find("./PHON[@kindOf='standard']") is None
        ):
            raise ValueError(f"Missing standard PHON for {parent.get('id')}")

    ET.indent(root, space="  ")
    with tempfile.NamedTemporaryFile(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
        delete=False,
    ) as handle:
        staging = Path(handle.name)
    try:
        tree.write(staging, encoding="UTF-8", xml_declaration=True)
        os.replace(staging, destination)
    finally:
        staging.unlink(missing_ok=True)


def process(corpora_path: Path, shared_script: Path) -> tuple[int, int]:
    if not shared_script.is_file():
        raise FileNotFoundError(f"Shared phonology utility not found: {shared_script}")
    files = xml_files(corpora_path)
    if not files:
        raise ValueError(f"No XML files found under {corpora_path}")

    with tempfile.TemporaryDirectory(prefix="kanakanavu-phonology-") as temp_name:
        temp_root = Path(temp_name)
        snapshots_by_file: dict[Path, dict[str, FormSnapshot]] = {}
        total_folded = 0
        for source in files:
            relative = Path(source.name) if corpora_path.is_file() else source.relative_to(corpora_path)
            temporary = temp_root / relative
            temporary.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, temporary)
            folded, snapshots = fold_temporary_originals(temporary)
            total_folded += folded
            snapshots_by_file[relative] = snapshots

        subprocess.run(
            [
                sys.executable,
                str(shared_script),
                "--corpora_path",
                str(temp_root),
                "--orthography",
                "Ortho113",
            ],
            check=True,
        )

        for source in files:
            relative = Path(source.name) if corpora_path.is_file() else source.relative_to(corpora_path)
            restore_originals_and_install(
                temp_root / relative,
                source,
                snapshots_by_file[relative],
            )
    return len(files), total_folded


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpora_path", type=Path, default=DEFAULT_XML_PATH)
    parser.add_argument("--shared-script", type=Path, required=True)
    args = parser.parse_args()
    file_count, folded_count = process(args.corpora_path, args.shared_script)
    print(
        f"Added shared Ortho113 PHON tiers to {file_count} files after folding "
        f"stress in {folded_count} temporary original FORM tiers"
    )


if __name__ == "__main__":
    main()
