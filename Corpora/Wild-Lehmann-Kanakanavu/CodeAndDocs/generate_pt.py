#!/usr/bin/env python3
"""generate_pt.py -- the site's phonetic line (PT) -> CodeAndDocs/PT/, one XML file per text.

Not published data. Maintainer, round 2: "Audio will be handled as untranscribed
audio. The PT transcriptions go in separate files but not the XML folder. But
them in CodeAndDocs. They should be described in the documentation as being
available but requiring alignment." Round 3 (pt-files): "xml", one file per text.

Each source unit with a PT row becomes one S whose only child is
FORM kindOf="original" (PT is IPA-like, so the shared cleaner, standardizer and
pronunciation steps are not run on it). Ids are the published ones with _PT_
after the corpus prefix, so a PT line can be matched to its sentence. The
page's recording is the TEXT's AUDIO, as in the published files: the lines are
not aligned to it.

Changes to the printed PT, in this order:
  1. CodeAndDocs/pt_corrections.tsv, row by row: `from` must occur exactly
     once in the line as it stands (the build stops otherwise); it becomes
     `to`; a row's note goes into FORM/@notes. Each row names its ruling.
  2. ts -> ʦ and tʃ -> ʧ (maintainer, round 2: "ts-tsh"), except in umavitsʃi
     ("umavitsʃi is uncorrectable, leave as is").
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

from lxml import etree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import generate_xml as g  # noqa: E402  (same folder: read_page, SITE, XML_LANG)

KEEP = ("umavitsʃi",)


def affricates(t: str) -> str:
    hold = {k: f"\x00{i}\x00" for i, k in enumerate(KEEP)}
    for k, v in hold.items():
        t = t.replace(k, v)
    t = t.replace("tʃ", "ʧ").replace("ts", "ʦ")
    for k, v in hold.items():
        t = t.replace(v, k)
    return t


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--source", required=True, type=Path, help="CodeAndDocs/source")
    ap.add_argument("--out", required=True, type=Path, help="folder to write the PT files into")
    args = ap.parse_args()
    meta = json.loads((HERE / "corpus_metadata.json").read_text(encoding="utf-8"))
    rows: dict = {}
    with (HERE / "pt_corrections.tsv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            rows.setdefault((r["page"], r["rf"]), []).append(r)
    n_rows, applied, n_files, n_s = sum(len(v) for v in rows.values()), 0, 0, 0
    args.out.mkdir(parents=True, exist_ok=True)
    pages = sorted(p for p in (args.source / "html" / "language-documentation").glob("*.html") if p.name != "index.html")
    for p in pages:
        page, data = p.stem, g.read_page(p)
        slug = page.replace("-", "_")
        text_id = f"{meta['text_id_prefix']}_PT_{slug}"
        source = " ".join(x for x in [f'kanakanavu.info, "{data["title"]}", {g.SITE}{page}.html.', data["recorded"], data["speaker"]] if x)
        source += " The site's phonetic transcription (PT) line only; not aligned to the recording."
        root = etree.Element("TEXT", {"id": text_id, g.XML_LANG: meta["xml_lang"], "dialect": meta["dialect"],
                                      "citation": meta["citation"], "BibTeX_citation": meta["bibtex"],
                                      "copyright": meta["copyright"], "source": source})
        for m in data["media"]:
            name = m if m.lower().endswith(".mp3") else m.rsplit(".", 1)[0] + meta["video_audio_ext"]
            etree.SubElement(root, "AUDIO", {"file": name})
        for unit in data["units"]:
            r = {}
            for label, cells in unit["rows"]:
                r.setdefault(label, list(cells))
            rf = (r.get("rf") or [""])[0]
            pt = " ".join(c for c in (r.get("PT") or []) if c).strip()
            if not rf or not pt:
                continue
            notes = []
            for c in rows.get((page, rf), []):
                if pt.count(c["from"]) != 1:
                    raise SystemExit(f"{page} {rf}: PT correction expects {c['from']!r} once, found {pt.count(c['from'])} in {pt!r}")
                pt = re.sub(r"\s+", " ", pt.replace(c["from"], c["to"])).strip()
                applied += 1
                if c["note"]:
                    notes.append(c["note"])
            s = etree.SubElement(root, "S", {"id": f"{text_id}_{rf.replace(chr(39), '')}"})
            form = etree.SubElement(s, "FORM", {"kindOf": "original"})
            form.text = affricates(pt)
            if notes:
                form.set("notes", "; ".join(notes))
            n_s += 1
        if len(root.findall("S")):
            etree.ElementTree(root).write(str(args.out / f"{meta['file_prefix']}_PT_{slug}.xml"),
                                          encoding="UTF-8", xml_declaration=True, pretty_print=True)
            n_files += 1
    if applied != n_rows:
        raise SystemExit(f"{n_rows} rows in pt_corrections.tsv but {applied} applied")
    print(f"generate_pt.py: {n_files} PT files, {n_s} sentences, {applied} PT corrections", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
