#!/usr/bin/env python3
"""Safolu headword entries -> FormosanBank XML (XML/Amis/Safolu/amis_safolu_headwords.xml).

Reads the committed snapshot of the upstream headword fields (headword_source.jsonl.gz, from headword_snapshot.py)
and the committed lists in this folder; generate_xml.sh passes the switches that the maintainer's rulings chose
(decision log, "Dictionary headwords", 2026-11-12 to 2026-11-15). One S per headword form, one zho TRANSL per sense
(senses after the first ver="alt", POL-025). Shared tools (clean_xml, standardize, add_phonology, dedup) run after.
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

XML_NS = "http://www.w3.org/XML/1998/namespace"
CUTS, POSL, BORROW, BORROW_RAW, PIECES, SPLIT, RESTORE, REPLACE, ADD, ADD_DONE, ROWS, SNAP, MANIFEST = {}, set(), {}, {}, {}, set(), {}, {}, {}, {}, [], {}, {}
LETTER = re.compile(r"阿美語[族的]?[元輔母]音之一|阿美語的?輔音之一")
STRONG = re.compile(r"^(用法如下：)?(（\d）)?\s*[(（〔\[]?\s*(複合|復合)?(前綴|後綴|前後綴)(詞)?\s*[)）〕\]]?\s*[。，,:：]?")
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


HERE = Path(__file__).resolve().parent


def load_snapshot(path: Path) -> list[dict]:
    """Rows of headword_source.jsonl.gz in ordinal order (ordinals follow the examples' source order)."""
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def build(args) -> tuple[ET.ElementTree, Counter, list]:
    global CUTS, POSL, BORROW, BORROW_RAW, PIECES, SPLIT, RESTORE, REPLACE, ADD, ADD_DONE, ROWS, SNAP, MANIFEST
    ROWS = load_snapshot(args.snapshot)
    SNAP = {r["file"]: r for r in ROWS}
    MANIFEST = json.loads(args.manifest.read_text(encoding="utf-8"))
    stats: Counter = Counter()
    log: list = []
    root = ET.Element("TEXT", {
        "id": "amis_safolu_headwords",
        "citation": "Tsai, Chung-Han (Safolu Kacaw Lalanges). (n.d.). Amis dictionary. Provided to the g0v Amis Moedict project.",
        "BibTeX_citation": "@misc{tsai_amis_dictionary, author={{Tsai Chung-Han (Safolu Kacaw Lalanges)}}, title={Amis dictionary}, year={n.d.}, note={Provided to the g0v Amis Moedict project}}",
        "copyright": "CC BY-NC-SA 3.0 TW",
        f"{{{XML_NS}}}lang": "ami",
        "source": f"Safolu/Tsai dictionary headword entries, g0v/amis-moedict@{MANIFEST['text_commit']} docs/s.",
        "glottocode": "amis1246",
        "dialect": "Coastal",
    })
    for r in load_tsv(args.add_entries):
        ADD.setdefault(r["after_headword"], []).append({"headword": r["headword"], "stem": r["stem"], "senses": [x.strip() for x in r["senses"].split("‖") if x.strip()]})
    REPLACE = {(r["headword"], r["old"]): r["new"] for r in load_tsv(args.replace)}
    SPLIT = {r["headword"] for r in load_tsv(args.split)}
    for r in load_tsv(args.restore):
        RESTORE.setdefault(r["headword"], []).append((int(r["position"]), r["sense"]))
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
    # r6-missed-headwords: senses of a headword the converter missed move out of the parent's entry
    MOVED, EXTRA, SUBSTEM, SUBPARENT = {}, {}, {}, {}
    for r in load_tsv(args.missed):
        if r["status"] != "split":
            continue
        pairs_ = {tuple(int(x) for x in u.split(".")) for u in r["parent_senses_h.d"].split(",") if u}
        MOVED.setdefault(r["filed_under"], {}).update({u: r["headword"] for u in pairs_})
        SUBSTEM[r["headword"]] = r["stem"]
        SUBPARENT[r["headword"]] = r["filed_under"]; SUBPARENT[r["headword"].lower()] = r["filed_under"]
        if r["own_file_upstream"] == "yes":
            pe = SNAP[r["filed_under"].lower() + ".json"]
            ds = [pe["h"][h]["d"][d] for h, d in sorted(pairs_)]
            EXTRA.setdefault(r["headword"].lower(), []).append({"d": ds})
    for row in ROWS:
        ordinal, name, entry = row["ordinal"], row["file"], row
        stats["headword files"] += 1
        title = entry["t"].strip()
        if title.lower() in EXTRA:
            entry = dict(entry, h=list(entry.get("h", [])) + EXTRA[title.lower()])
            stats["missed headword: senses joined to its own upstream headword"] += 1
        if args.affix == "drop" and "…" in title:
            stats["affix headwords dropped"] += 1
            log.append(("affix-dropped", title))
            continue
        if args.affix == "drop" and (title.startswith("-") or title.endswith("-")):
            stats["affix headwords dropped"] += 1
            log.append(("affix-dropped", title))
            continue
        # group senses by the form they belong to: heteronym `name` if it differs, else the title
        # r6-homs-plausible splits one S per printed entry; two upstream entries joined by a confirmed break are halves of
        # one printed entry and stay together
        hgroup, g = {}, 0
        if title in SPLIT:
            H_ = entry.get("h", [])
            for hi_ in range(len(H_)):
                if hi_:
                    prev_d, cur_d = H_[hi_ - 1].get("d", []), H_[hi_].get("d", [])
                    if prev_d and cur_d and (title, clean(prev_d[-1].get("f", "")), clean(cur_d[0].get("f", ""))) in CUTS:
                        stats["homophone split: entries kept together across a repaired break"] += 1
                    else:
                        g += 1
                hgroup[hi_] = g
        groups: dict[str, list[str]] = {}
        notes_by_form: dict[str, list[str]] = {}
        tag_from_sense: dict[str, str] = {}
        entry_pos: dict[str, str] = {}
        for hi, het in enumerate(entry.get("h", [])):
            form = (het.get("name") or "").strip() or title
            if title in SPLIT and not (het.get("name") or "").strip():
                form = f"{title}\x00{hi}"  # r6-homs-plausible (RULED): one S per printed entry
            groups.setdefault(form, [])
            notes_by_form.setdefault(form, [])
            for di, d in enumerate(het.get("d", [])):
                stats["senses in source"] += 1
                mv = MOVED.get(title, {}).get((hi, di))
                if mv:
                    if mv.lower() in EXTRA:
                        stats["missed headword: sense moved to its own upstream headword"] += 1
                        continue
                    form = mv
                    groups.setdefault(form, []); notes_by_form.setdefault(form, [])
                    stats["missed headword: sense moved to a new headword"] += 1
                else:
                    form = (het.get("name") or "").strip() or title
                    if title in SPLIT and not (het.get("name") or "").strip():
                        form = f"{title}\x00{hgroup.get(hi, hi)}"
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
        k = 0
        for gkey, pairs in groups.items():
            form = gkey.split("\x00")[0]
            notes = list(notes_by_form.get(gkey, []))
            for i, (x, hi) in enumerate(pairs):
                if (form, x) in REPLACE:
                    pairs[i] = (REPLACE[(form, x)], hi); stats["sense corrected from the 2015 text"] += 1
            if form in RESTORE:
                for pos, sense in RESTORE[form]:
                    pairs.insert(pos, (sense, pairs[0][1] if pairs else 0))
                    stats["sense restored from the 2015 text"] += 1
            # r2-cut-paste (RULED): rejoin translations the converter broke at a source paragraph break
            # the break / piece / correction lists are keyed by the upstream headword the text sat in: for a missed headword
            # that is its parent
            aliases = [form, title] + ([SUBPARENT[form]] if form in SUBPARENT else []) + ([SUBPARENT[title.lower()]] if title.lower() in SUBPARENT else [])
            i = 0
            while i + 1 < len(pairs):
                ck = next(((a_, pairs[i][0], pairs[i + 1][0]) for a_ in aliases if (a_, pairs[i][0], pairs[i + 1][0]) in CUTS), None)
                if ck:
                    pairs[i:i + 2] = [(CUTS[ck], pairs[i][1])]
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
            pcs = set().union(*[PIECES.get(a_, set()) for a_ in aliases])
            if pcs:
                keep = []
                for x, tn in zip(senses, tnotes):
                    if x in pcs:
                        stats["example-sentence pieces removed from headword senses"] += 1
                        if tn and keep:  # a borrowing/part-of-speech note on the piece moves to the sense before it
                            keep[-1][1].extend(n for n in tn if n not in keep[-1][1])
                            stats["note moved from a removed piece to the sense before it"] += 1
                        continue
                    keep.append((x, tn))
                senses, tnotes = [x for x, _ in keep], [tn for _, tn in keep]
            if entry_pos.get(gkey):
                tnotes = [tn + [entry_pos[gkey]] for tn in tnotes]
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
            if args.headings == "drop":
                # r2-heading (RULED): a sense that is only a heading ending in a colon (主要表示： etc.) is left out
                keep = [(x, tn) for x, tn in zip(senses, tnotes) if not re.search(r"[：:]\s*$", x)]
                stats["colon headings left out"] += len(senses) - len(keep)
                senses, tnotes = [x for x, _ in keep], [tn for _, tn in keep]
            if args.affix_strong:
                # r5-affix-approval (RULED): senses whose text starts with 前綴 / 複合前綴 / 後綴 without brackets, the 詞綴 note,
                # and a's (1)前綴詞 are affix meanings too
                keep = []
                for x, tn in zip(senses, tnotes):
                    if STRONG.match(x) and STRONG.match(x).group(4) or any("詞綴" in n for n in tn):
                        stats["affix sense left out (approved list)"] += 1
                        log.append(("affix-approved-dropped", form, x, tn)); continue
                    keep.append((x, tn))
                senses, tnotes = [x for x, _ in keep], [tn for _, tn in keep]
            if args.letters == "drop-desc" and any(LETTER.search(x) for x in senses):
                # r4-letters (RULED): the letter entries' sound descriptions are left out; word senses stay
                keep = [(x, tn) for x, tn in zip(senses, tnotes) if not DESC.search(x)]
                stats["letter-entry sound descriptions left out"] += len(senses) - len(keep)
                log.append(("letter-split", form, [x for x in senses if DESC.search(x)], [x for x, _ in keep]))
                senses, tnotes = [x for x, _ in keep], [tn for _, tn in keep]
            if args.stem_tag == "notes" and form in SUBSTEM and form != title:
                notes.insert(0, f"Stem: {SUBSTEM[form]}")
            elif args.stem_tag == "notes":
                if entry.get("stem"):
                    notes.insert(0, f"Stem: {entry['stem']}")
                if entry.get("tag"):
                    notes.insert(0, f"Tag: {entry['tag']}")
                elif tag_from_sense.get(gkey):
                    notes.insert(0, f"Tag: {tag_from_sense[gkey]}")
            if not senses and not (args.keep_senseless and notes):
                stats["headword forms with no sense, not published"] += 1
                log.append(("no-sense", form, notes))
                continue
            k += 1
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
                stats["extra S under one headword (capitalised form or separate printed entry)"] += 1
        for add in ADD.get(title, []) if not ADD_DONE.get(title) else []:
            # r7-missed-lost (RULED): a missed headword upstream lost, from the converter's input
            k += 1
            s2 = ET.SubElement(root, "S", {"id": f"H{ordinal:05d}-{k}"})
            ET.SubElement(s2, "FORM", {"kindOf": "original", "notes": f"Stem: {add['stem']}"}).text = add["headword"]
            for i, sense in enumerate(add["senses"]):
                a2 = {f"{{{XML_NS}}}lang": "zho"}
                if i:
                    a2["ver"] = "alt"
                ET.SubElement(s2, "TRANSL", a2).text = sense
            stats["S written"] += 1; stats["TRANSL written"] += len(add["senses"])
            stats["missed headword restored from the converter's input"] += 1
        ADD_DONE[title] = True
    ET.indent(root, space="    ")
    return ET.ElementTree(root), stats, log


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--snapshot", type=Path, default=HERE / "headword_source.jsonl.gz")
    p.add_argument("--manifest", type=Path, default=HERE / "headword_manifest.json")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--xref", choices=["drop", "notes", "translation"], default="drop")
    p.add_argument("--label", choices=["drop", "notes", "translation"], default="drop")
    p.add_argument("--nochinese", choices=["drop", "notes", "translation"], default="drop")
    p.add_argument("--affix", choices=["keep", "drop"], default="keep")
    p.add_argument("--stem-tag", choices=["none", "notes"], default="none")
    p.add_argument("--syn-rel", choices=["none", "notes"], default="none")
    p.add_argument("--keep-senseless", action="store_true")
    p.add_argument("--embedded", choices=["keep", "drop"], default="keep")
    p.add_argument("--cuts", type=Path, help="cut_confirmed.tsv: rejoin the breaks whose pasted text matches the 2015 text")
    p.add_argument("--pos", type=Path, help="pos_labels.tsv: labels marked yes go to TRANSL notes")
    p.add_argument("--borrow", type=Path, help="borrow_labels.tsv: borrowing labels go to TRANSL notes")
    p.add_argument("--restore-lost", action="store_true", help="r2-cut-lost: restore characters lost at a break from the 2015 text")
    p.add_argument("--tags", choices=["leave", "norm"], default="leave", help="r3-tags: a 〔疊 N〕 sense becomes one Tag note")
    p.add_argument("--label-pos", choices=["form", "transl"], default="form", help="r3-label-pos")
    p.add_argument("--affix-rule", action="store_true", help="r4-affixes: leave out senses marked 前綴/後綴")
    p.add_argument("--letters", choices=["keep", "drop-desc"], default="keep", help="r4-letters")
    p.add_argument("--pieces", type=Path, help="example_pieces_removed.tsv: translations absorbed into rebuilt example sentences")
    p.add_argument("--headings", choices=["keep", "drop"], default="keep", help="r2-heading")
    p.add_argument("--split", type=Path, help="homophone_split.tsv: headwords that get one S per printed entry")
    p.add_argument("--restore", type=Path, help="restored_senses.tsv: senses lost from the converter input, from the 2015 text")
    p.add_argument("--replace", type=Path, help="replace_senses.tsv: senses corrected from the 2015 text")
    p.add_argument("--missed", type=Path, help="missed_headwords.tsv: split out headwords the converter missed")
    p.add_argument("--add-entries", type=Path, help="lost_headwords.tsv: missed headwords upstream lost, from the converter input")
    p.add_argument("--affix-strong", action="store_true", help="r5-affix-approval: unbracketed 前綴/後綴 senses, 詞綴 note")
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
