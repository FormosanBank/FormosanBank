#!/usr/bin/env python3
"""Remove only reviewed repeat downloads through Wikipedia redirects."""

import argparse
import csv
import hashlib
from pathlib import Path
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent


def remove_redirect_copies(xml: Path, manifest: Path) -> int:
    with manifest.open(encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    removed = {row["file"] for row in rows}
    if len(removed) != len(rows) or removed.intersection(row["retained"] for row in rows):
        raise ValueError("Redirect exclusions must be unique and keep their counterparts")
    for row in rows:
        forms = []
        for field, identifier in (("file", "text_id"), ("retained", "retained_id")):
            root = ET.parse(xml / row[field]).getroot()
            if root.get("id") != row[identifier]:
                raise ValueError(f"Changed source identity: {row[field]}")
            sentences = root.findall("S")
            if len(sentences) != 1 or sentences[0].get("id") != "0":
                raise ValueError(f"Changed article structure: {row[field]}")
            form = sentences[0].find('FORM[@kindOf="original"]')
            if form is None or not form.text:
                raise ValueError(f"Missing source FORM: {row[field]}")
            forms.append(form.text)
        if forms[0] != forms[1] or hashlib.sha256(forms[0].encode()).hexdigest() != row["original_sha256"]:
            raise ValueError(f"Changed redirect content: {row['file']}; no files deleted")
    for row in rows:
        (xml / row["file"]).unlink()
    return len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpora_path", type=Path, default=HERE.parent / "XML")
    args = parser.parse_args()
    count = remove_redirect_copies(args.corpora_path, HERE / "source_redirects.csv")
    print(f"Removed {count} reviewed redirect copies; canonical articles retained")
