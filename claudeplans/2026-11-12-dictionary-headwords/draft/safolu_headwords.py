#!/usr/bin/env python3
"""DRAFT (scratchpad only): Safolu headword entries -> FormosanBank XML.

One S per headword form, one zho TRANSL per sense (senses after the first
ver="alt", POL-025, same layout as ILRDF_Dicts *_dictionary.xml).
Each open question is a switch so every option's output can be shown.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("xml", XML_NS)
SPECIAL = {"=.json", "ch-mapping.json", "index.json", "lenToRegex.json",
           "precomputed.json", "stem-words.json"}
CJK = re.compile(r"[㐀-鿿]")
XREF = re.compile(r"^(同|參見|參閱|參看|詳見|見)\s*")
LABEL = re.compile(r"〔[^〕]*〕|\[[^\]]*\]")
EMB = re.compile(r"^([A-Za-z'^ ,.!?\-]+?)[.!?]?\s*([\u3400-\u9fff].*)$")


def load_sections(path):
    """section_rulings json + tsv (apply_section_rulings.py): {stem: [[action per d] per h]}, {headword: printed_in}"""
    if not path:
        return {}, {}
    import csv
    acts = json.loads(Path(path).read_text(encoding="utf-8"))
    printed = {r["headword"]: r["printed_in"] for r in csv.DictReader(open(Path(path).with_suffix(".tsv"), encoding="utf-8"), delimiter="\t")}
    return acts, printed


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("`", "").replace("~", "")).strip()


def classify(sense: str) -> str:
    """kind of a cleaned sense: empty / xref / label / nochinese / ok"""
    if not sense:
        return "empty"
    body = XREF.sub("", sense)
    if XREF.match(sense) and not CJK.search(body):
        return "xref"
    if not LABEL.sub("", sense).strip(" 。.，,"):
        return "label"
    if not CJK.search(sense):
        return "nochinese"
    return "ok"


def entries(base: Path, pin: Path):
    """Ordinals follow the base snapshot's sorted order; files only in `pin` are appended."""
    base_names = sorted(p.name for p in base.glob("*.json") if p.name not in SPECIAL)
    pin_names = sorted(p.name for p in pin.glob("*.json") if p.name not in SPECIAL)
    order = base_names + [n for n in pin_names if n not in set(base_names)]
    for ordinal, name in enumerate(order, 1):
        path = pin / name
        if not path.exists():
            continue
        yield ordinal, name, json.loads(path.read_text(encoding="utf-8"))


def build(args) -> tuple[ET.ElementTree, Counter, list]:
    stats: Counter = Counter()
    log: list = []
    root = ET.Element("TEXT", {
        "id": "amis_safolu_headwords",
        "citation": "Tsai, Chung-Han (Safolu Kacaw Lalanges). (n.d.). Amis dictionary. Provided to the g0v Amis Moedict project.",
        "BibTeX_citation": "@misc{tsai_amis_dictionary, author={{Tsai Chung-Han (Safolu Kacaw Lalanges)}}, title={Amis dictionary}, year={n.d.}, note={Provided to the g0v Amis Moedict project}}",
        "copyright": "CC BY-NC-SA 3.0 TW",
        f"{{{XML_NS}}}lang": "ami",
        "source": f"Safolu/Tsai dictionary headword entries, g0v/amis-moedict@{args.pin_commit} docs/s.",
        "glottocode": "amis1246",
        "dialect": "Coastal",
    })
    sec_acts, printed = load_sections(args.sections)
    for ordinal, name, entry in entries(args.base, args.pin):
        stats["headword files"] += 1
        title = entry["t"].strip()
        acts = sec_acts.get(name[:-5])
        if acts and all(a != "keep" for h in acts for a in h):
            if "main" in printed.get(title, "") and args.merged == "keep":
                stats["merged upstream (printed in 01-22 and 23/24): kept"] += 1
                acts = None
            elif "main" in printed.get(title, ""):
                stats["merged upstream (printed in 01-22 and 23/24): dropped"] += 1
        if args.affix == "drop" and "…" in title:
            stats["affix headwords dropped"] += 1
            log.append(("affix-dropped", title))
            continue
        if args.affix == "drop" and (title.startswith("-") or title.endswith("-")):
            stats["affix headwords dropped"] += 1
            log.append(("affix-dropped", title))
            continue
        # group senses by the form they belong to: heteronym `name` if it differs, else the title
        groups: dict[str, list[str]] = {}
        notes_by_form: dict[str, list[str]] = {}
        for hi, het in enumerate(entry.get("h", [])):
            form = (het.get("name") or "").strip() or title
            groups.setdefault(form, [])
            notes_by_form.setdefault(form, [])
            for di, d in enumerate(het.get("d", [])):
                stats["senses in source"] += 1
                if acts and acts[hi][di] != "keep":
                    stats[f"senses dropped by section ruling: {acts[hi][di]}"] += 1
                    continue
                sense = clean(d.get("f", ""))
                m = EMB.match(sense)
                if args.embedded == "drop" and m and len(m.group(1).split()) >= 3:
                    stats["embedded example sentences taken out of the headword senses"] += 1
                    continue
                kind = classify(sense)
                stats[f"sense kind: {kind}"] += 1
                if kind == "empty":
                    continue
                if kind == "xref":
                    if args.xref == "translation":
                        pass
                    elif args.xref == "notes":
                        notes_by_form[form].append(sense)
                        continue
                    else:
                        continue
                if kind == "label":
                    if args.label == "translation":
                        pass
                    elif args.label == "notes":
                        notes_by_form[form].append(sense)
                        continue
                    else:
                        continue
                if kind == "nochinese":
                    if args.nochinese == "notes":
                        notes_by_form[form].append(sense)
                        continue
                    if args.nochinese == "drop":
                        continue
                if sense not in groups[form]:
                    groups[form].append(sense)
                else:
                    stats["repeated sense text merged"] += 1
                if args.syn_rel == "notes":
                    for key, label in (("s", "Synonym"), ("r", "Related")):
                        for w in d.get(key, []) or []:
                            note = f"{label}: {clean(w)}"
                            if note not in notes_by_form[form]:
                                notes_by_form[form].append(note)
        for k, (form, senses) in enumerate(groups.items(), 1):
            notes = list(notes_by_form.get(form, []))
            if args.stem_tag == "notes":
                if entry.get("stem"):
                    notes.insert(0, f"Stem: {entry['stem']}")
                if entry.get("tag"):
                    notes.insert(0, f"Tag: {entry['tag']}")
            if not senses and not (args.keep_senseless and notes):
                stats["headword forms with no sense, not published"] += 1
                log.append(("no-sense", form, notes))
                continue
            sid = f"H{ordinal:05d}" + (f"-{k}" if k > 1 else "")
            s = ET.SubElement(root, "S", {"id": sid})
            fattr = {"kindOf": "original"}
            if notes:
                fattr["notes"] = " | ".join(notes)
            ET.SubElement(s, "FORM", fattr).text = form
            for i, sense in enumerate(senses):
                a = {f"{{{XML_NS}}}lang": "zho"}
                if i:
                    a["ver"] = "alt"
                ET.SubElement(s, "TRANSL", a).text = sense
            stats["S written"] += 1
            stats["TRANSL written"] += len(senses)
            if k > 1:
                stats["S for a heteronym with its own name form"] += 1
    ET.indent(root, space="    ")
    return ET.ElementTree(root), stats, log


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base", type=Path, required=True, help="docs/s at the examples' snapshot (id order)")
    p.add_argument("--pin", type=Path, required=True, help="docs/s whose text is published")
    p.add_argument("--pin-commit", required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--xref", choices=["drop", "notes", "translation"], default="drop")
    p.add_argument("--label", choices=["drop", "notes", "translation"], default="drop")
    p.add_argument("--nochinese", choices=["drop", "notes", "translation"], default="drop")
    p.add_argument("--affix", choices=["keep", "drop"], default="keep")
    p.add_argument("--stem-tag", choices=["none", "notes"], default="none")
    p.add_argument("--syn-rel", choices=["none", "notes"], default="none")
    p.add_argument("--keep-senseless", action="store_true")
    p.add_argument("--sections", type=Path, help="section_rulings_4cb8.json from apply_section_rulings.py")
    p.add_argument("--merged", choices=["keep", "drop"], default="keep")
    p.add_argument("--embedded", choices=["keep", "drop"], default="keep")
    p.add_argument("--log", type=Path)
    a = p.parse_args()
    tree, stats, log = build(a)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    tree.write(a.out, encoding="UTF-8", xml_declaration=True)
    for k, v in sorted(stats.items()):
        print(f"{v:7d} {k}")
    if a.log:
        a.log.write_text(json.dumps(log, ensure_ascii=False, indent=0), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
