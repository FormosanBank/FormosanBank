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
    their "/"-join. Falls back to substituting the original where the group is
    not spelled out in the containing FORM: a W-level alternation writes the
    slash only in the sentence FORM, so the W itself holds the bare original
    (Kwaway/S9W5 `varit`, alternate `yaked`).
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
        # The carrier keeps its own alternates. Its containing W gains one per
        # reading; the S does NOT (maintainer, 2026-09-06). A sentence-level
        # alternate for a one-morpheme spelling difference is noise, and where
        # a sentence carries two independent alternations — Kalaku1/S17 — an
        # S-level alternate can only show one of them, which misreads as a
        # claim that the other did not vary. The S FORM therefore carries the
        # primary reading only; the variation is on the W and M that vary.
        readings = [original] + alts
        for ancestor in chain[:-1]:
            base = text_of(ancestor)
            drop_alternates(ancestor)   # e.g. Kalaku1/S13's defective W-level alternate
            set_form(ancestor, resolve(base, readings, original))
            if ancestor.tag == "S":
                continue
            for alt in alts:
                add_alternate(ancestor, resolve(base, readings, alt))


UNAN = "unan"


def gloss_units(value: str) -> list[str]:
    """Split a gloss on '-', but not on hyphens inside parentheses.

    The article writes a multi-word gloss for a single morpheme in parentheses:
    `unan-(one-after-another)-us-completely` is four units, not six.
    """
    units, depth, current = [], 0, []
    for ch in value:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == "-" and depth == 0:
            units.append("".join(current))
            current = []
        else:
            current.append(ch)
    units.append("".join(current))
    return [u for u in units if u]


def gloss_of(node):
    t = node.find("TRANSL")
    return (t.text or "") if t is not None else ""


def tidy_glosses(sentence, report):
    """Two rules the maintainer set on 2026-09-06, applied corpus-wide.

    1. `unan` is the article's "unanalyzed" marker, not a gloss. A TRANSL whose
       whole text is `unan` records that the transcriber supplied nothing, so
       it is dropped rather than published as though it meant something.
    2. A W whose morpheme count disagrees with its gloss's unit count is not
       reliably segmented, so its M children are dropped and only the W-level
       gloss is kept. A W left with no gloss at all (rule 1) likewise keeps no
       M. Every drop is reported for review.
    """
    sid = sentence.get("id")
    for w in sentence.findall("W"):
        for node in [w] + w.findall("M"):
            for t in list(node.findall("TRANSL")):
                if (t.text or "").strip().lower() == UNAN:
                    node.remove(t)
        morphemes = w.findall("M")
        if not morphemes:
            continue
        gloss = gloss_of(w)
        if not gloss:
            report.append((sid, w.get("id"), text_of(w), "<unan>", len(morphemes), 0))
            for m in morphemes:
                w.remove(m)
            continue
        # A gloss may itself carry the source's slash alternation across the
        # whole word — Kwaway/S25W1 is `unan-not-I-you(pl)/unan-curse-I-you(pl)`,
        # two complete 4-unit glosses for a 4-morpheme word. Counting the joined
        # string would call that a mismatch and throw the morphemes away, taking
        # the per-morpheme alternative glosses (POL-025) with them. So a word
        # aligns if ANY of its slash-separated glosses has the right unit count.
        # `still/again` is unaffected: it is one unit, and neither half of it
        # matches on its own.
        counts = {len(gloss_units(part)) for part in gloss.split("/")}
        counts.add(len(gloss_units(gloss)))
        if len(morphemes) not in counts:
            report.append((sid, w.get("id"), text_of(w), gloss,
                           len(morphemes), len(gloss_units(gloss))))
            for m in morphemes:
                w.remove(m)


def take_reading(word, which):
    """Keep one reading's glosses across a word being split into two sentences.

    Where the source glosses the two readings differently it records the second
    as TRANSL[@ver="alt"] beside the first (Kwaway/S4W2: `unan-take-unan` for
    `tunanal-aep-an`, `unan` for `nitelemna`). Once the readings become separate
    sentences neither is an "alternative" any more, so each branch keeps its own
    gloss as the plain one. A node with no alt gloss keeps what it has — the two
    readings simply share a gloss.

    Only the split word and its morphemes are touched. An alt gloss elsewhere in
    the sentence is a genuine second reading of the *same* text (POL-025,
    e.g. Kwaway/S19W2 `kanu` = 'when' or 'and(unctn)') and must survive.
    """
    for node in [word] + word.findall("M"):
        translations = node.findall("TRANSL")
        alt = [t for t in translations if t.get("ver") == "alt"]
        plain = [t for t in translations if t.get("ver") != "alt"]
        if not alt:
            continue
        keep, drop = (plain, alt) if which == "primary" else (alt, plain)
        for t in drop:
            node.remove(t)
        for t in keep:
            if "ver" in t.attrib:
                del t.attrib["ver"]


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
    primary_chain = ancestors_of(primary, carrier_id)
    for node in primary_chain:
        drop_alternates(node)
        set_form(node, resolve(text_of(node), readings, original))
    take_reading(primary_chain[1], "primary")

    other = copy.deepcopy(sentence)
    other_chain = ancestors_of(other, carrier_id)
    for node in other_chain:
        drop_alternates(node)
        set_form(node, resolve(text_of(node), readings, alternate))
    take_reading(other_chain[1], "alternate")
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
    ap.add_argument("--gloss-report", default=None,
                    help="write the list of W whose M tier was dropped, for review")
    args = ap.parse_args()

    config = json.loads(Path(args.decisions).read_text(encoding="utf-8"))
    table = config["decisions"]
    by_sentence = {}
    for d in table:
        by_sentence.setdefault(d["file"], {})[d["sentence"]] = d

    snapshot = Path(args.snapshot)
    out_root = Path(args.xml_dir)
    total = {"S": 0, "variant": 0, "split": 0}
    gloss_report: dict[str, list] = {}
    for src in sorted(snapshot.rglob("*.xml")):
        name = src.stem
        tree = ET.parse(src)
        root = tree.getroot()
        if root.findall(".//FORM[@kindOf='standard']") or root.findall(".//PHON"):
            raise SystemExit(f"{src}: snapshot must carry no derived tiers")
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
        for sentence in rebuilt:
            tidy_glosses(sentence, gloss_report.setdefault(name, []))
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
    if args.gloss_report:
        with open(args.gloss_report, "w", encoding="utf-8") as fh:
            fh.write("file\tsentence\tword\tform\tgloss\tmorphemes\tgloss_units\n")
            for name, rows in sorted(gloss_report.items()):
                for row in rows:
                    fh.write(name + "\t" + "\t".join(str(c) for c in row) + "\n")
        print(f"  M-tier dropped for "
              f"{sum(len(v) for v in gloss_report.values())} W "
              f"-> {args.gloss_report}")

    print(f"\n{total['S']} S written "
          f"({total['variant']} variant, {total['split']} split alternations); "
          f"{leftover} unresolved slash FORMs")
    return 1 if leftover else 0


if __name__ == "__main__":
    raise SystemExit(main())
