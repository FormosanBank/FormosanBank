#!/usr/bin/env python3
"""Build Corpora/WakelinTexts/XML/ from the pre-correction snapshot.

Step 1 of generate_xml.sh (POL-047). WakelinTexts was typed into XML by hand
from the 1958 SIL Work Papers article; there is no scrape or OCR stage to
re-run, so `CodeAndDocs/pre_correction_snapshot/XML/` is this corpus's source
of record (POL-035) and this script is its parser.

The one transformation it performs is resolving the source's slash notation.
Wakelin et al. print alternations like `nipi/niripi` and
`akak-aep-an/(mangday su aep)`. These record the *transcriber's* uncertainty,
not alternatives a speaker offered, so POL-027's "one S block per option" does
not apply automatically. Each alternation is classified by hand in
`alternative_decisions.json` (POL-039 — the table is data, not code):

  variant  a spelling variant: overlapping letters, same gloss. Emitted as
           FORM[@kindOf="alternate"] on the node that varies and on each of
           its ancestors, so no published FORM keeps a slash.
  split    anything else — different lexemes, different glosses, or a word
           against a phrase. Emitted as separate S blocks. The first keeps the
           printed sentence number; the rest take suffixes b, c, ...
           POL-037 forbids renumbering the already-published bare id to `a`.

No standard tier and no PHON are produced: this text's orthography has never
been identified, so the corpus asserts neither (see ../README.md).
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

import xml.etree.ElementTree as ET

CODE_ROOT = Path(__file__).resolve().parent
BANK_ROOT = CODE_ROOT.parents[2]
sys.path.insert(0, str(BANK_ROOT))
from QC.utilities._prettify import prettify  # noqa: E402

ENG = "{http://www.w3.org/XML/1998/namespace}lang"


def form(node, kind="original"):
    for f in node.findall("FORM"):
        if f.get("kindOf") == kind:
            return f
    return None


def text_of(node, kind="original"):
    f = form(node, kind)
    return (f.text or "") if f is not None else ""


def alternates(node):
    return [(f.text or "") for f in node.findall("FORM") if f.get("kindOf") == "alternate"]


def drop_alternates(node):
    for f in list(node.findall("FORM")):
        if f.get("kindOf") == "alternate":
            node.remove(f)


def set_form(node, value, kind="original"):
    f = form(node, kind)
    if f is None:
        f = ET.Element("FORM", {"kindOf": kind})
        node.insert(0, f)
    f.text = value


def add_alternate(node, value):
    """Append FORM[@kindOf='alternate'] after the last FORM."""
    f = ET.Element("FORM", {"kindOf": "alternate"})
    f.text = value
    last = max((i for i, c in enumerate(node) if c.tag == "FORM"), default=-1)
    node.insert(last + 1, f)


def resolve(container_text: str, readings: list[str], keep: str) -> str:
    """Collapse the printed `a/b[/c]` group inside container_text down to `keep`.

    `readings` is [original, *alternates] in printed order, so the group is
    their "/"-join. Falls back to substituting the original when the snapshot
    has already resolved the slash out of the containing FORM (Kwaway/S51 does
    exactly that).
    """
    group = "/".join(readings)
    if group in container_text:
        return container_text.replace(group, keep, 1)
    original = readings[0]
    if keep == original:
        return container_text
    if original in container_text:
        return container_text.replace(original, keep, 1)
    raise SystemExit(f"cannot resolve {group!r} in {container_text!r}")


def strip_parens(value: str) -> str:
    """Drop only *unmatched* parentheses.

    A membership split cuts the source's `(imurud nu tau)/(tau d-imurud)` at the
    slash, which leaves each branch's edge words holding half a pair (`(imurud`,
    `tau)`). Those go. Balanced pairs are the corpus's own gloss convention —
    `intrg(unctn)`, `her(unctn)` — and must survive (POL-017).
    """
    if not value:
        return value
    drop, stack = set(), []
    for i, ch in enumerate(value):
        if ch == "(":
            stack.append(i)
        elif ch == ")":
            if stack:
                stack.pop()
            else:
                drop.add(i)
    drop.update(stack)
    return "".join(c for i, c in enumerate(value) if i not in drop)


def ancestors_of(sentence, node_id):
    """[S, ...W, ...M] chain down to node_id, as live elements."""
    for w in sentence.findall("W"):
        if w.get("id") == node_id:
            return [sentence, w]
        for m in w.findall("M"):
            if m.get("id") == node_id:
                return [sentence, w, m]
    raise SystemExit(f"carrier {node_id} not found in {sentence.get('id')}")


def apply_variant(sentence, carriers):
    """Publish each carrier's alternation as alternate FORMs up the chain."""
    for carrier_id in carriers:
        chain = ancestors_of(sentence, carrier_id)
        carrier = chain[-1]
        original = text_of(carrier)
        alts = alternates(carrier)
        if not alts:
            raise SystemExit(f"{carrier_id}: mode=variant but no alternate FORM")
        # The carrier keeps its own alternates; ancestors gain one per reading.
        readings = [original] + alts
        for ancestor in chain[:-1]:
            base = text_of(ancestor)
            drop_alternates(ancestor)   # e.g. Kalaku1/S13's defective W-level alternate
            set_form(ancestor, resolve(base, readings, original))
            for alt in alts:
                add_alternate(ancestor, resolve(base, readings, alt))


def renumber(node, old_sid, new_sid):
    """Rewrite S/W/M ids under a cloned sentence."""
    node.set("id", new_sid)
    for w in node.findall("W"):
        w.set("id", w.get("id").replace(old_sid, new_sid, 1))
        for m in w.findall("M"):
            m.set("id", m.get("id").replace(old_sid, new_sid, 1))


def build_branch(sentence, spec, decision):
    """Materialize one branch of a membership split."""
    sid = sentence.get("id")
    new_sid = sid + spec["suffix"]
    branch = ET.Element("S", {"id": new_sid})
    set_form(branch, spec["form"])
    for t in sentence.findall("TRANSL"):
        branch.append(copy.deepcopy(t))
    by_id = {w.get("id"): w for w in sentence.findall("W")}
    overrides = spec.get("overrides", {})
    index = 0
    for wid in spec["words"]:
        source = by_id.get(wid)
        if source is None:
            raise SystemExit(f"{sid}: branch word {wid} not in snapshot")
        w = copy.deepcopy(source)
        over = overrides.get(wid)
        if over:
            set_form(w, over["form"])
            for t in w.findall("TRANSL"):
                t.text = over["gloss"]
            keep = set(over.get("morphemes", []))
            for m in list(w.findall("M")):
                if m.get("id") not in keep:
                    w.remove(m)
        set_form(w, strip_parens(text_of(w)))
        for t in w.findall("TRANSL"):
            if t.text:
                t.text = strip_parens(t.text)
        for m in w.findall("M"):
            set_form(m, strip_parens(text_of(m)))
            for t in m.findall("TRANSL"):
                if t.text:
                    t.text = strip_parens(t.text)
        index += 1
        w.set("id", f"{new_sid}W{index}")
        for j, m in enumerate(w.findall("M"), start=1):
            m.set("id", f"{new_sid}W{index}M{j}")
        branch.append(w)
    for extra in spec.get("extra_words", []):
        index += 1
        w = ET.Element("W", {"id": f"{new_sid}W{index}"})
        set_form(w, extra["form"])
        t = ET.SubElement(w, "TRANSL", {ENG: "eng"})
        t.text = extra["gloss"]
        branch.append(w)
    return branch


def apply_split(sentence, decision):
    """Return the list of S elements this sentence becomes."""
    sid = sentence.get("id")
    if decision.get("kind") == "membership":
        return [build_branch(sentence, spec, decision) for spec in decision["branches"]]

    # substitution split: same W skeleton, one node's text differs
    (carrier_id,) = decision["carriers"]
    chain = ancestors_of(sentence, carrier_id)
    carrier = chain[-1]
    original = text_of(carrier)
    alts = alternates(carrier)
    if len(alts) != 1:
        raise SystemExit(f"{carrier_id}: substitution split needs exactly one alternate")
    alternate = alts[0]

    readings = [original, alternate]
    primary = copy.deepcopy(sentence)
    for node in ancestors_of(primary, carrier_id):
        drop_alternates(node)
        set_form(node, resolve(text_of(node), readings, original))

    other = copy.deepcopy(sentence)
    other_chain = ancestors_of(other, carrier_id)
    for node in other_chain:
        drop_alternates(node)
        set_form(node, resolve(text_of(node), readings, alternate))
    if decision.get("drop_morphemes"):
        holder = other_chain[1]
        for m in list(holder.findall("M")):
            holder.remove(m)
    renumber(other, sid, sid + "b")
    return [primary, other]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", default=str(CODE_ROOT / "pre_correction_snapshot" / "XML"))
    ap.add_argument("--decisions", default=str(CODE_ROOT / "alternative_decisions.json"))
    ap.add_argument("--xml-dir", default=str(CODE_ROOT.parent / "XML"))
    args = ap.parse_args()

    config = json.loads(Path(args.decisions).read_text(encoding="utf-8"))
    table = config["decisions"]
    by_sentence = {}
    for d in table:
        by_sentence.setdefault(d["file"], {})[d["sentence"]] = d
    repairs = {}
    for r in config.get("snapshot_repairs", {}).get("entries", []):
        repairs.setdefault(r["file"], []).append(r)

    snapshot = Path(args.snapshot)
    out_root = Path(args.xml_dir)
    total = {"S": 0, "variant": 0, "split": 0}
    for src in sorted(snapshot.rglob("*.xml")):
        name = src.stem
        tree = ET.parse(src)
        root = tree.getroot()
        if root.findall(".//FORM[@kindOf='standard']") or root.findall(".//PHON"):
            raise SystemExit(f"{src}: snapshot must carry no derived tiers")
        for r in repairs.get(name, []):
            target = root.find(f".//*[@id='{r['node']}']")
            if target is None or text_of(target) != r["from"]:
                raise SystemExit(
                    f"{src}: snapshot_repair for {r['node']} no longer applies "
                    f"(expected {r['from']!r}). Re-check the repair against the snapshot."
                )
            set_form(target, r["to"])
            if r.get("also_drop_alternate"):
                for f in list(target.findall("FORM")):
                    if f.get("kindOf") == "alternate" and f.text == r["also_drop_alternate"]:
                        target.remove(f)
        decisions = by_sentence.get(name, {})
        rebuilt = []
        for sentence in root.findall("S"):
            decision = decisions.get(sentence.get("id"))
            if decision is None:
                rebuilt.append(sentence)
            elif decision["mode"] == "variant":
                apply_variant(sentence, decision["carriers"])
                rebuilt.append(sentence)
                total["variant"] += 1
            else:
                rebuilt.extend(apply_split(sentence, decision))
                total["split"] += 1
        for sentence in root.findall("S"):
            root.remove(sentence)
        for sentence in rebuilt:
            root.append(sentence)
        total["S"] += len(rebuilt)

        dest = out_root / src.relative_to(snapshot)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(prettify(root), encoding="utf-8")
        print(f"  {dest.relative_to(out_root.parent)}: {len(rebuilt)} S")

    leftover = 0
    for path in sorted(out_root.rglob("*.xml")):
        for f in ET.parse(path).getroot().iter("FORM"):
            if "/" in (f.text or ""):
                print(f"  !! slash survives in {path.name}: {f.text}")
                leftover += 1
    print(f"\n{total['S']} S written "
          f"({total['variant']} variant, {total['split']} split alternations); "
          f"{leftover} unresolved slash FORMs")
    return 1 if leftover else 0


if __name__ == "__main__":
    raise SystemExit(main())
