#!/usr/bin/env python3
"""DRAFT (scratchpad only): Virginia Fey headword entries -> FormosanBank XML.

One S per headword (sheet column 詞條); each sense row (英文解釋 / 中文解釋)
gives one eng and one zho TRANSL; senses after the first are ver="alt" (POL-025).
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("xml", XML_NS)
XREF_ENG = re.compile(r"^(refer to|see)\s+\S+\.?$", re.I)
FIXME_NOTE = 'The source\'s Chinese translation of this sense was marked "FIXME" and has been dropped.'
XREF_ZHO = re.compile(r"^(詳見|參見|參看|參閱|見)\s*[A-Za-z'^ ,\-]+[。.]?$")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def split_eng(text: str, mode: str) -> list[str]:
    if mode == "split":
        parts = [norm(p) for p in text.split("*")]
        return [p for p in parts if p]
    return [text] if text else []


def split_zho(text: str, mode: str) -> list[str]:
    if mode == "split":
        parts = [norm(p) for p in re.split(r"[，、,]", text)]
        return [p for p in parts if p]
    return [text] if text else []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--split", choices=["keep", "split"], default="keep")
    ap.add_argument("--xref", choices=["drop", "translation"], default="drop")
    ap.add_argument("--affix", choices=["keep", "drop"], default="keep")
    ap.add_argument("--see-also", choices=["none", "notes"], default="none")
    ap.add_argument("--fixme", choices=["keep", "drop", "part"], default="keep",
                    help="drop: a Chinese sense marked (FIXME) is not published; its English TRANSL says so in notes")
    a = ap.parse_args()

    rows = list(csv.DictReader(a.sheet.open(encoding="utf-8")))
    entries: list[dict] = []
    for line, row in enumerate(rows, start=2):  # sheet line (header = 1)
        head = norm(row["詞條"])
        if head:
            entries.append({"form": head, "line": line, "senses": [], "see": []})
        if not entries:
            continue
        eng, zho = norm(row["英文解釋"]), norm(row["中文解釋"])
        if eng or zho:
            entries[-1]["senses"].append((eng, zho))
        if norm(row["參見"]):
            entries[-1]["see"].append(norm(row["參見"]))

    stats: Counter = Counter()
    root = ET.Element("TEXT", {
        f"{{{XML_NS}}}lang": "ami",
        "id": "VirginiaFeyDictionary_headwords",
        "source": "https://github.com/miaoski/amis-data/tree/494e5e4bc276c4d2b8b7b827a2c737597239a73b (headword entries)",
        "copyright": "CC BY-NC 3.0",
        "citation": "Fey, V. (1986). Amis dictionary. Taipei: The Bible Society. | miaoski. (2023). miaoski/amis-data [Python]. GitHub. https://github.com/miaoski/amis-data (Original work published 2013)",
        "BibTeX_citation": "@article{fey1986amis,title={Amis dictionary},author={Fey, Virginia},journal={Taipei: The Bible Society},year={1986}}, @misc{miaoski2023amisfey,author={miaoski},title={miaoski/amis-data [Python]},year={2023},howpublished={\\url{https://github.com/miaoski/amis-data}},note={Original work published 2013},publisher={GitHub}}",
        "dialect": "Xiuguluan",
    })
    for n, e in enumerate(entries, 1):
        stats["headwords"] += 1
        form = e["form"]
        if a.affix == "drop" and (form.startswith("-") or form.endswith("-")):
            stats["affix headwords dropped"] += 1
            continue
        eng_out: list[str] = []
        zho_out: list[str] = []
        eng_notes: dict[str, str] = {}
        fixme_form_note = False
        for eng, zho in e["senses"]:
            stats["senses"] += 1
            if XREF_ENG.match(eng) or XREF_ZHO.match(zho):
                stats["cross-reference senses"] += 1
                if a.xref == "drop":
                    continue
            if "FIXME" in zho.upper():
                stats["Chinese senses marked FIXME"] += 1
                parts = [x.strip() for x in zho.split("；")]
                if a.fixme == "part" and len(parts) > 1:
                    bad = [x for x in parts if "FIXME" in x.upper()]
                    zho = "；".join(x for x in parts if "FIXME" not in x.upper())
                    marked = "；".join(re.sub(r"\s*\(FIXME\)\s*", "", x, flags=re.I) for x in bad)
                    if eng:
                        eng_notes[eng] = f'Part of the source\'s Chinese translation, {marked}, was marked "FIXME" and has been dropped.'
                    stats["Chinese FIXME: only the marked part dropped"] += 1
                elif a.fixme in ("drop", "part"):
                    zho = ""
                    if eng:
                        eng_notes[eng] = FIXME_NOTE
                    else:
                        fixme_form_note = True
            for t in split_eng(eng, a.split):
                if t not in eng_out:
                    eng_out.append(t)
            for t in split_zho(zho, a.split):
                if t not in zho_out:
                    zho_out.append(t)
        if not (eng_out or zho_out):
            stats["headwords with no sense left, not published"] += 1
            continue
        s = ET.SubElement(root, "S", {"id": f"H{n:04d}"})
        fnotes = []
        if a.see_also == "notes" and e["see"]:
            fnotes.append("See also: " + ", ".join(e["see"]))
        if fixme_form_note:
            fnotes.append(FIXME_NOTE)
        fa = {"kindOf": "original"}
        if fnotes:
            fa["notes"] = " | ".join(fnotes)
        ET.SubElement(s, "FORM", fa).text = form
        for lang, items in (("eng", eng_out), ("zho", zho_out)):
            for i, t in enumerate(items):
                at = {f"{{{XML_NS}}}lang": lang}
                if i:
                    at["ver"] = "alt"
                if lang == "eng" and t in eng_notes:
                    at["notes"] = eng_notes[t]
                ET.SubElement(s, "TRANSL", at).text = t
            stats[f"TRANSL {lang}"] += len(items)
        stats["S written"] += 1
    ET.indent(root, space="    ")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(a.out, encoding="UTF-8", xml_declaration=True)
    for k, v in sorted(stats.items()):
        print(f"{v:6d} {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
