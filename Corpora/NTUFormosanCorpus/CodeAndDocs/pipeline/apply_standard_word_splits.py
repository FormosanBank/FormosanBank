#!/usr/bin/env python3
"""Write the word divisions listed in standard_word_splits.tsv into the STANDARD sentence tier.

Ruling 2026-10-16 (review page round 2, "B: split in standard only"): where NTU's
sentence text writes one word that NTU's own word glosses treat as two, the
original tier keeps NTU's spelling and the standard tier writes the words as
glossed. Only the base S-level FORM[@kindOf="standard"] is touched; the word tier
already follows the glosses.

Runs after standardize.py and before add_phonology.py, so the standard PHON is
derived from the split form. A row applies where its language directory holds its
sentence id (the ids are Grammar ids, so the Sentences and Stories builds find
none and skip). A row whose sentence is found but whose standard FORM does not
contain 'joined' exactly once as a whole word exits 1: the source or an earlier
step changed, and the row must be reviewed rather than silently skipped.

usage: apply_standard_word_splits.py <xml dir> [table]
"""
import csv
import re
import sys
from pathlib import Path

from lxml import etree


def load(path):
    rows = [line for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")]
    return list(csv.DictReader(rows, delimiter="\t"))


def main(argv):
    xml_dir = Path(argv[1])
    table = Path(argv[2]) if len(argv) > 2 else Path(__file__).with_name("standard_word_splits.tsv")
    rows = load(table)
    applied = 0
    for language in sorted({r["language"] for r in rows}):
        for path in sorted((xml_dir / language).glob("*.xml")) if (xml_dir / language).is_dir() else []:
            tree = etree.parse(str(path))
            by_id = {s.get("id"): s for s in tree.getroot().iter("S")}
            changed = False
            for r in (r for r in rows if r["language"] == language):
                s = by_id.get(r["s_id"])
                if s is None:
                    continue
                form = s.find("FORM[@kindOf='standard']")
                pattern = re.compile(r"(?<![\w'’])" + re.escape(r["joined"]) + r"(?![\w'’])")
                text = form.text if form is not None else None
                if text is None or len(pattern.findall(text)) != 1:
                    print(f"apply_standard_word_splits: {language} {r['s_id']}: standard FORM "
                          f"{text!r} does not contain {r['joined']!r} exactly once", file=sys.stderr)
                    return 1
                form.text = pattern.sub(r["split"], text)
                applied += 1
                changed = True
            if changed:
                tree.write(str(path), encoding="utf-8", xml_declaration=True)
    print(f"  standard word splits applied: {applied}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
