#!/usr/bin/env python3
"""Restore the POL-035 Wikipedia snapshot and its documented licence."""

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
LANGUAGES = ("Amis", "Atayal", "Paiwan", "Sakizaya", "Seediq")
TEXT_TAG = re.compile(r"<TEXT\b[^>]*>", re.DOTALL)


def restore() -> None:
    source, output = HERE / "pre_correction_snapshot", HERE.parent / "XML"
    for language in LANGUAGES:
        if not (source / language).is_dir():
            raise FileNotFoundError(source / language)
    for language in LANGUAGES:
        target = output / language
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source / language, target)
        for path in sorted(target.glob("*.xml")):
            raw = path.read_text(encoding="utf-8")
            tag = TEXT_TAG.search(raw)
            if tag is None or tag.group().count('copyright="CC BY-SA"') != 1:
                raise ValueError(f"Unexpected snapshot licence: {path}")
            updated = tag.group().replace('copyright="CC BY-SA"',
                                          'copyright="CC BY-SA 4.0"')
            path.write_text(raw[:tag.start()] + updated + raw[tag.end():],
                            encoding="utf-8")


def provenance(formosanbank: Path, record: bool) -> None:
    result = subprocess.run(
        ["git", "-C", str(formosanbank), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
    )
    if result.returncode or Path(result.stdout.strip()).resolve() != formosanbank.resolve():
        print("Export has no Git metadata; retained the supplied provenance record.")
        return
    commit = subprocess.check_output(
        ["git", "-C", str(formosanbank), "rev-parse", "HEAD"], text=True,
    ).strip()
    value = {
        "_note": "The FormosanBank commit this corpus was built against. Provenance only; the build uses the current checkout.",
        "formosanbank_commit": commit,
    }
    path = HERE / "provenance.json"
    if record:
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    else:
        try:
            saved = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            saved = {}
        expected = saved.get("formosanbank_commit") if isinstance(saved, dict) else None
        if expected != commit:
            print(f"Provenance differs from current checkout {commit}; using its current tools.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--record-provenance", type=Path)
    action.add_argument("--check-provenance", type=Path)
    args = parser.parse_args()
    if args.record_provenance:
        provenance(args.record_provenance, record=True)
    elif args.check_provenance:
        provenance(args.check_provenance, record=False)
    else:
        restore()
