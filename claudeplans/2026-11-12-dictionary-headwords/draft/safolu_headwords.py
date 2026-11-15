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
CUTS, POSL, BORROW, BORROW_RAW, PIECES = {}, set(), {}, {}, {}
LETTER = re.compile(r"阿美語[族的]?[元輔母]音之一|阿美語的?輔音之一")
DESC = re.compile(r"音值|元音|輔音|母音|詞尾|詞首|詞終|讀如|讀時|送氣|喉塞化|顎化|齶化|長音化|方言區|發音|音節|鼻音|塞音|擦音|邊音|顫音|半母音|舌面|舌尖|舌葉|雙唇|唇齒|聲門|喉門")
ET.register_namespace("xml", XML_NS)
SPECIAL = {"=.json", "ch-mapping.json", "index.json", "lenToRegex.json",
           "precomputed.json", "stem-words.json"}
CJK = re.compile(r"[㐀-鿿]")
XREF = re.compile(r"^(同|參見|參閱|參看|詳見|見)\s*")
LABEL = re.compile(r"〔[^〕]*〕|\[[^\]]*\]")
EMB = re.compile(r"^([A-Za-z'^ ,.!?\-]+?)[.!?]?\s*([\u3400-\u9fff].*)$")


def load_tsv(path):
    import csv
    return list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t")) if path else []


LEAD = re.compile(r"^[（(]([^（）()]{1,14})[）)]\s*[。.]?\s*")


def tidy(x):
    """text after a label is moved out: collapse spaces, doubled 。, trailing commas"""
    x = re.sub(r"\s+", " ", x).strip()
    x = re.sub(r"\s+([。，、；])", r"\1", x)
    x = re.sub(r"。+", "。", x)
    return x.strip(" ，,、；;")


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
    global CUTS, POSL, BORROW, BORROW_RAW, PIECES
    for r in load_tsv(args.pieces):
        PIECES.setdefault(r["headword"], set()).add(r["translation_removed"])
    # r2-cut-paste (RULED): breaks the 2015 text confirms; r2-cut-unchecked (RULED): breaks it cannot check
    PASTE = {"pasting reproduces 2015", "not locatable in 2015 text", "headword not in 2015 text"}
    CUTS = {}
    for r in load_tsv(args.cuts):
        if r.get("check_2015") in PASTE:
            CUTS[(r["FORM"], r["piece_1"], r["piece_2"])] = r["piece_1"] + r["piece_2"]
        elif r.get("check_2015") == "characters lost at the break" and args.restore_lost:
            # r2-cut-lost (RULED): restore the characters the 2015 text has at the break
            CUTS[(r["FORM"], r["piece_1"], r["piece_2"])] = r["piece_1"] + r["lost_chars"] + r["piece_2"]
    POSL = {r["label"] for r in load_tsv(args.pos) if r.get("treated_as_part_of_speech") == "yes"}
    rows = load_tsv(args.borrow)
    BORROW = {r["label_as_printed"]: r["note_text"] for r in rows}
    BORROW_RAW = {r["label_as_printed"]: r["label_as_printed"] for r in rows}
    sec_acts, printed = load_sections(args.sections)
    if args.keep_24:
        sec_acts = {k: [["keep" if a == "drop-24" else a for a in h] for h in v] for k, v in sec_acts.items()}
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
        tag_from_sense: dict[str, str] = {}
        entry_pos: dict[str, str] = {}
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
                    lab = re.match(r"^[〔\[]\s*([^〕\]]+?)\s*[〕\]][。.]?$", sense)
                    inner = lab.group(1) if lab else ""
                    if args.tags == "norm" and inner.startswith("疊"):
                        # r3-tags (RULED): a 〔疊 N〕 left behind as a sense becomes one Tag note
                        num = re.search(r"\d", inner)
                        tag_from_sense[form] = f"[疊 {num.group(0)}]" if num else "[疊]"
                        stats["疊 tag left as a sense, made a Tag note"] += 1
                        continue
                    if args.label_pos == "transl" and inner in POSL:
                        # r3-label-pos (RULED): a part-of-speech label standing alone in 〔 〕 goes on the translations
                        entry_pos[form] = inner
                        stats["part-of-speech label in 〔 〕 standing alone, moved to TRANSL notes"] += 1
                        continue
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
                if sense not in [x for x, _ in groups[form]]:
                    groups[form].append((sense, hi))
                else:
                    stats["repeated sense text merged"] += 1
                if args.syn_rel == "notes":
                    for key, label in (("s", "Synonym"), ("r", "Related")):
                        for w in d.get(key, []) or []:
                            note = f"{label}: {clean(w)}"
                            if note not in notes_by_form[form]:
                                notes_by_form[form].append(note)
        for k, (form, pairs) in enumerate(groups.items(), 1):
            notes = list(notes_by_form.get(form, []))
            # r2-cut-paste (RULED): rejoin translations the converter broke at a source paragraph break
            i = 0
            while i + 1 < len(pairs):
                if (form, pairs[i][0], pairs[i + 1][0]) in CUTS:
                    pairs[i:i + 2] = [(CUTS[(form, pairs[i][0], pairs[i + 1][0])], pairs[i][1])]
                    stats["broken translations rejoined"] += 1
                i += 1
            # r2-pos (RULED): part-of-speech labels to TRANSL notes; a label standing alone applies to the
            # following senses of the same upstream entry, up to the next label
            out, cur = [], {}
            for x, hi in pairs:
                m = LEAD.match(x); L = m.group(1).strip() if m else None
                if L in POSL and not x[m.end():].strip(" 。."):
                    cur[hi] = L; stats["part-of-speech label standing alone, moved to notes"] += 1; continue
                if L in POSL:
                    out.append([x[m.end():].strip(), [L]]); stats["part-of-speech label at start of sense, moved to notes"] += 1; continue
                out.append([x, [cur[hi]] if cur.get(hi) else []])
            # r2-borrow (RULED, borrow_labels.tsv): borrowing labels to TRANSL notes; r2-loanonly (RULED): a sense that
            # is only a label goes to FORM notes
            senses, tnotes = [], []
            for x, tn in out:
                hit = [lab for lab in BORROW if lab in x]
                for lab in hit:
                    x = x.replace(lab, "")
                    tn.append(BORROW[lab])
                if hit:
                    stats["borrowing labels moved to TRANSL notes"] += len(hit)
                    x = tidy(x)
                    if not x.strip(" 。.，,"):
                        notes.extend(BORROW_RAW[l] for l in hit); stats["sense that is only a borrowing label, moved to FORM notes"] += 1
                        continue
                if x in senses:
                    stats["repeated sense text merged"] += 1; continue
                senses.append(x); tnotes.append(tn)
            # r3-embedded-rebuilt (RULED): pieces absorbed into a rebuilt example sentence are not headword translations
            if PIECES.get(form):
                keep = [(x, tn) for x, tn in zip(senses, tnotes) if x not in PIECES[form]]
                stats["example-sentence pieces removed from headword senses"] += len(senses) - len(keep)
                senses, tnotes = [x for x, _ in keep], [tn for _, tn in keep]
            if entry_pos.get(form):
                tnotes = [tn + [entry_pos[form]] for tn in tnotes]
            if args.affix_rule:
                # r4-affixes (RULED): senses marked explicitly as affixes (前綴 / 後綴 in brackets, now a note) are left out
                keep = []
                for x, tn in zip(senses, tnotes):
                    if any(("前綴" in n or "後綴" in n) for n in tn) or re.match(r"^[〔\[(（]\s*(複合|復合)?(前綴|後綴|前後綴)\s*[〕\])）]", x):
                        stats["affix sense left out (marked 前綴/後綴)"] += 1
                        log.append(("affix-sense-dropped", form, x, tn))
                        continue
                    keep.append((x, tn))
                senses, tnotes = [x for x, _ in keep], [tn for _, tn in keep]
            if args.letters == "drop-desc" and any(LETTER.search(x) for x in senses):
                # r4-letters (RULED): the letter entries' sound descriptions are left out; word senses stay
                keep = [(x, tn) for x, tn in zip(senses, tnotes) if not DESC.search(x)]
                stats["letter-entry sound descriptions left out"] += len(senses) - len(keep)
                log.append(("letter-split", form, [x for x in senses if DESC.search(x)], [x for x, _ in keep]))
                senses, tnotes = [x for x, _ in keep], [tn for _, tn in keep]
            if args.stem_tag == "notes":
                if entry.get("stem"):
                    notes.insert(0, f"Stem: {entry['stem']}")
                if entry.get("tag"):
                    notes.insert(0, f"Tag: {entry['tag']}")
                elif tag_from_sense.get(form):
                    notes.insert(0, f"Tag: {tag_from_sense[form]}")
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
                if tnotes[i]:
                    a["notes"] = " | ".join(dict.fromkeys(tnotes[i]))
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
    p.add_argument("--keep-24", action="store_true", help="with --sections: drop section-23 senses only")
    p.add_argument("--cuts", type=Path, help="cut_confirmed.tsv: rejoin the breaks whose pasted text matches the 2015 text")
    p.add_argument("--pos", type=Path, help="pos_labels.tsv: labels marked yes go to TRANSL notes")
    p.add_argument("--borrow", type=Path, help="borrow_labels.tsv: borrowing labels go to TRANSL notes")
    p.add_argument("--restore-lost", action="store_true", help="r2-cut-lost: restore characters lost at a break from the 2015 text")
    p.add_argument("--tags", choices=["leave", "norm"], default="leave", help="r3-tags: a 〔疊 N〕 sense becomes one Tag note")
    p.add_argument("--label-pos", choices=["form", "transl"], default="form", help="r3-label-pos")
    p.add_argument("--affix-rule", action="store_true", help="r4-affixes: leave out senses marked 前綴/後綴")
    p.add_argument("--letters", choices=["keep", "drop-desc"], default="keep", help="r4-letters")
    p.add_argument("--pieces", type=Path, help="example_pieces_removed.tsv: translations absorbed into rebuilt example sentences")
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
