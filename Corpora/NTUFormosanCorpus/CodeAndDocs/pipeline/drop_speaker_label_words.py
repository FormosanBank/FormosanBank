#!/usr/bin/env python3
"""Delete words (W) that are a multi-speaker label, and their token in the sentence.

The Tsou conversations label a line spoken by several people at once 'Y,M:',
'W,G,S:'. Maintainer's ruling, 2026-10-18: "Any number of single capital letters
followed by a colon, ignore intervening commas => speaker label." A speaker label
is not a word, so it leaves the word tier and the sentence text.

The labels are found in the source cells, where the colon still is
(pipeline_stories.multi_speaker_labels; step 5 later removes the colon, so the
published W FORM reads 'Y,M'). A W whose FORMs all equal such a label is removed,
and so is one token equal to it in each sentence-level FORM (with the space
before it; drop_punctuation_words.drop_token picks which one).

This runs after the builder has numbered the words, so removing a label leaves a
gap and every other W and M keeps its published id (POL-037: "S/W/M ids ... are
not renumbered once published"; the maintainer, 2026-08-12: "keeping the original
numbering with gaps is preferred over renumbering"). The ids withdrawn this way
are listed in ../withdrawn_ids.tsv. Runs in finish_tiers before the standard tier
and PHON, which are derived from the edited FORMs. Idempotent.

    python drop_speaker_label_words.py --xml_dir <dir> --source_dir <CodeAndDocs> [--report <tsv>]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from drop_punctuation_words import drop_token, has_letter, remove_keep_layout  # noqa: E402
from pipeline_stories import multi_speaker_labels  # noqa: E402


def source_labels(source_dir: Path) -> set:
    labels = set()
    for sub in ("grammar", "sentence", "story"):
        for path in sorted((source_dir / sub).rglob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for rec in data.get("glosses", []):
                if isinstance(rec, list) and len(rec) > 1 and isinstance(rec[1], dict):
                    labels |= multi_speaker_labels(rec[1].get("gloss") or [])
    return labels


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml_dir", required=True, type=Path)
    ap.add_argument("--source_dir", required=True, type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args(argv)
    labels = source_labels(args.source_dir)
    counts, report, files = Counter(), [], 0
    for path in sorted(args.xml_dir.rglob("*.xml")):
        raw = path.read_bytes()
        tree = etree.parse(str(path))
        changed = False
        for s in tree.getroot().iter("S"):
            for w in list(s.findall("W")):
                forms = ["".join(f.itertext()).strip() for f in w.findall("FORM")]
                if not forms or any(f not in labels for f in forms):
                    continue
                ws = s.findall("W")
                k = ws.index(w)
                before = sum(1 for x in ws[:k] if any(has_letter("".join(f.itertext())) for f in x.findall("FORM")))
                for sf in s.findall("FORM"):
                    old = sf.text
                    new = drop_token(sf, forms[0], before, w.get("id"))
                    if new is None:
                        counts["sentence FORM without the label (left)"] += 1
                        continue
                    sf.text = new
                    counts["sentence FORM labels removed"] += 1
                    report.append((path.name, s.get("id"), f"S FORM kindOf={sf.get('kindOf')}", old, new))
                report.append((path.name, s.get("id"), f"W {w.get('id')} removed", forms[0], ""))
                counts["W removed"] += 1
                counts["M removed"] += len(w.findall("M"))
                remove_keep_layout(w)
                changed = True
        if changed:
            decl = raw.split(b"?>", 1)[0] + b"?>\n" if raw.startswith(b"<?xml") else b""
            body = etree.tostring(tree.getroot(), encoding="unicode").encode("utf-8")
            path.write_bytes(decl + body + (b"\n" if raw.endswith(b"\n") else b""))
            files += 1
    print(f"  multi-speaker labels in the source: {len(labels)}")
    for key in sorted(counts):
        print(f"  {key}: {counts[key]}")
    print(f"files rewritten: {files}")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("w", encoding="utf-8", newline="") as fh:
            out = csv.writer(fh, delimiter="\t", lineterminator="\n")
            out.writerow(["file", "s_id", "where", "before", "after"])
            out.writerows(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
