#!/usr/bin/env python3
"""Export the previously published XML into the two committed baseline tables.

The rebuild reconciles against the corpus as it was last published: that is
where the morpheme ids come from (they are not derivable from the source, and
POL-037 requires them to be stable) along with the four TEXT attributes the
source document does not carry.

Depending on a git commit for that made the corpus rebuildable only while
that commit stayed reachable. Instead the baseline is committed as data --
exactly the fields the rebuild reads, and nothing else:

  data/baseline_text_metadata.tsv   one row per file: the TEXT attributes
  data/baseline_morphemes.tsv       one row per M, in document order, giving
                                    its sentence, word, id and original FORM

This script regenerates them from an XML tree. It is not part of the build;
it exists so the tables can be re-derived and audited against the published
corpus they came from.

Usage
-----
    python scripts/export_baseline.py --baseline <XML dir>
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TEXT_FIELDS = ("file", "text_id", "citation", "BibTeX_citation", "dialect", "source")
MORPHEME_FIELDS = ("file", "s_id", "w_id", "m_id", "m_form")


def export(baseline_path: Path) -> tuple[int, int]:
    files = sorted(baseline_path.glob("PaiwanCh2_*.xml"))
    if len(files) != 100:
        raise ValueError(f"expected 100 baseline XML files, found {len(files)}")

    text_rows, morpheme_rows = [], []
    for path in files:
        root = ET.parse(path).getroot()
        text_rows.append(
            {
                "file": path.name,
                "text_id": root.get("id") or "",
                "citation": root.get("citation") or "",
                "BibTeX_citation": root.get("BibTeX_citation") or "",
                "dialect": root.get("dialect") or "",
                "source": root.get("source") or "",
            }
        )
        for sentence in root.findall("S"):
            for word in sentence.findall("W"):
                for morpheme in word.findall("M"):
                    form = morpheme.find("FORM[@kindOf='original']")
                    if form is None:
                        raise ValueError(f"{morpheme.get('id')}: no original FORM")
                    morpheme_rows.append(
                        {
                            "file": path.name,
                            "s_id": sentence.get("id") or "",
                            "w_id": word.get("id") or "",
                            "m_id": morpheme.get("id") or "",
                            "m_form": form.text or "",
                        }
                    )

    for name, fields, rows in (
        ("baseline_text_metadata.tsv", TEXT_FIELDS, text_rows),
        ("baseline_morphemes.tsv", MORPHEME_FIELDS, morpheme_rows),
    ):
        with open(DATA / name, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=fields, delimiter="\t", lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(rows)
    return len(text_rows), len(morpheme_rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    args = parser.parse_args()
    texts, morphemes = export(args.baseline.resolve())
    print(f"baseline_texts={texts}")
    print(f"baseline_morphemes={morphemes}")


if __name__ == "__main__":
    main()
