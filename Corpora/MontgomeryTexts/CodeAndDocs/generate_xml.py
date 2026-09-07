#!/usr/bin/env python3
"""Build Corpora/MontgomeryTexts/XML/ from the pre-correction snapshot.

Step 1 of generate_xml.sh (POL-047). The Montgomery texts were typed into XML
by hand from the 1962 SIL Work Papers article, whose four content pages are
image-only scans with no text layer; there is no scrape or OCR stage to re-run,
so `CodeAndDocs/pre_correction_snapshot/XML/` is this corpus's source of record
(POL-035) and this script is its parser. The snapshot carries the original tier
only: the standard tier is rebuilt downstream by standardize.py (POL-002) and
this corpus publishes no PHON (see ../README.md).

The one transformation performed here is splitting the source's slashed word
glosses. Montgomery prints two English equivalents for a single Amis word --
`good/holy`, `noon/lunch`, `trip/walk`, `whole/all`, `and/with`. The Amis word
does not vary, so POL-027's "one S block per option" does not apply; the second
reading becomes a `TRANSL[@ver="alt"]` on the same W, which is POL-025's
mechanism one tier down (maintainer ruling, 2026-09-07). Each one is listed by
hand in `gloss_alternations.json` (POL-039 -- the table is data, not code)
rather than matched by a blind slash rule, and a listed gloss that no longer
matches the snapshot is a hard error, not a silent skip.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parent
BANK_ROOT = CODE_ROOT.parents[2]
sys.path.insert(0, str(BANK_ROOT))
from QC.utilities._prettify import prettify  # noqa: E402

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--alternations", type=Path, required=True)
    parser.add_argument("--xml-dir", type=Path, required=True)
    return parser.parse_args()


def split_gloss(root: ET.Element, entry: dict, lang: str) -> None:
    """Turn one W's slashed gloss into a primary TRANSL plus a ver="alt" one."""
    word = None
    for candidate in root.iter("W"):
        if candidate.get("id") == entry["w_id"]:
            word = candidate
            break
    if word is None:
        raise ValueError(f"{entry['file']}: no W with id {entry['w_id']}")

    matches = [t for t in word.findall("TRANSL") if (t.text or "") == entry["printed"]]
    if len(matches) != 1:
        raise ValueError(
            f"{entry['file']} {entry['w_id']}: expected exactly one TRANSL reading "
            f"{entry['printed']!r}, found {len(matches)}"
        )
    primary = matches[0]
    primary.text = entry["primary"]
    alt = ET.Element("TRANSL", {XML_LANG: lang, "ver": "alt"})
    alt.text = entry["alt"]
    word.insert(list(word).index(primary) + 1, alt)


def main() -> int:
    args = parse_args()
    table = json.loads(args.alternations.read_text(encoding="utf-8"))
    lang = table["language"]

    by_file: dict[str, list[dict]] = {}
    for entry in table["alternations"]:
        by_file.setdefault(entry["file"], []).append(entry)

    target = args.xml_dir.resolve()
    if target.name != "XML":
        raise ValueError(f"Refusing to replace non-XML directory: {target}")
    if target.exists():
        shutil.rmtree(target)

    snapshot = args.snapshot.resolve()
    sources = sorted(snapshot.rglob("*.xml"))
    if not sources:
        raise ValueError(f"No XML under {snapshot}")

    applied = 0
    for source in sources:
        relative = source.relative_to(snapshot).as_posix()
        tree = ET.parse(source)
        root = tree.getroot()
        for entry in by_file.pop(relative, []):
            split_gloss(root, entry, lang)
            applied += 1
        output = target / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        prettify(root)
        tree.write(output, encoding="utf-8", xml_declaration=True)

    if by_file:
        raise ValueError(f"gloss_alternations.json names absent files: {sorted(by_file)}")
    if applied != len(table["alternations"]):
        raise ValueError(f"applied {applied} of {len(table['alternations'])} alternations")

    print(f"Built {len(sources)} files from the snapshot; split {applied} slashed glosses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
