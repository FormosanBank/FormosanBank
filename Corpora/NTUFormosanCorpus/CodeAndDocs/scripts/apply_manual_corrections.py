#!/usr/bin/env python3
"""apply_manual_corrections.py

Apply a small table of hand-verified one-off corrections to the
published XML. Entries name the file, the S id, the element tag, and an
exact old->new text substitution; every matching element inside that S
(both kindOf tiers, W- and M-level alike) is corrected. Entries that no
longer match are reported (so silent drift is impossible) but do not
fail the run.

After the substitutions, the PHON of every S/W/M element whose FORM
changed is recomputed through the Ortho113 mapping, gated by a
pre-change witness check (converting the old original FORM must
reproduce the old original PHON exactly; see _phon_regen.py).

Current corrections
-------------------
1. Sentences/Bunun 59_S_12, zho TRANSL: stray ``<`` where an opening
   parenthesis was meant (also the cause of the V132 1129/1128
   bracket-count imbalance). Parenthetical content stays, consistent
   with TRANSL parentheticals corpus-wide.
2. Grammar/Sakizaya 13_S_38 / 13_S_39 / 13_S_48: the source grammar
   chapter *cites* corpus examples instead of restating them, so the
   parser made the citation string the sentence FORM, and the real
   words (from the gloss table) carry IU numbers and pause durations
   fused to the first word of each intonation unit
   (``100....（2.2）yah`` -> ``yah``). The corrections strip the IU
   junk from the W/M forms, rebuild the S FORM from the cleaned words,
   and preserve the citation in a ``notes`` attribute on the S-level
   original FORM.

A file is rewritten only if its unmodified tree first re-serializes
byte-identically (lxml, xml declaration, UTF-8). Idempotent: applied
corrections simply stop matching.

Usage
-----
    python apply_manual_corrections.py            # corpus XML/ by default
    python apply_manual_corrections.py --dry-run
"""

import argparse
import os
import sys
from pathlib import Path

import lxml.etree as etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _phon_regen import language_of, load_mappings, convert  # noqa: E402

_XLANG = "{http://www.w3.org/XML/1998/namespace}lang"

_SKZY = "Grammar/Sakizaya/Sakizaya.xml"
_CIT38 = "(NTU Formosan Corpus skzyNr-movingkulang IU100-101)"
_CIT39 = "(NTU Formosan Corpus skzyNr-movingkulang IU105-107)"
_CIT48 = "(NTU Formosan Corpus skzyNr-movingkulang IU 309-312)"

# (relative file, S id, element tag, xml:lang or None, old substring, new text)
CORRECTIONS = [
    ("Sentences/Bunun/Bunun.xml", "59_S_12", "TRANSL", "zho",
     "< 敬禮請原諒)", "(敬禮請原諒)"),
    # 13_S_38
    (_SKZY, "13_S_38", "FORM", None, "100....2.2yah", "yah"),
    (_SKZY, "13_S_38", "FORM", None, "101....sa", "sa"),
    (_SKZY, "13_S_38", "FORM", None, _CIT38,
     "yah ta-luma' kina adiwawa. sa ku babalaki."),
    # 13_S_39
    (_SKZY, "13_S_39", "FORM", None, "105....0.8sa", "sa"),
    (_SKZY, "13_S_39", "FORM", None, "106....ha", "ha"),
    (_SKZY, "13_S_39", "FORM", None, "107....0.8sa", "sa"),
    (_SKZY, "13_S_39", "FORM", None, _CIT39,
     "sa-ka-ta-luma' namu mi-cudad. ha-nima ma-idih mi-cudad, sa ci ina niyam."),
    # 13_S_48
    (_SKZY, "13_S_48", "FORM", None, "309....0.7ya", "ya"),
    (_SKZY, "13_S_48", "FORM", None, "310....2.2sansicigu", "sansicigu"),
    (_SKZY, "13_S_48", "FORM", None, "311....0.9caliw", "caliw"),
    (_SKZY, "13_S_48", "FORM", None, "312....tu", "tu"),
    (_SKZY, "13_S_48", "FORM", None, _CIT48,
     "ya umah han=tu hananay sa, sansicigu nanay nu taw kya umah, "
     "caliw sa kya taywan u, tu pida tu mih-mihca-an."),
]

# 3. Fullwidth equals (＝) used as a clitic boundary or in gloss strings;
#    normalized to ASCII '=' consistent with clean_xml's fullwidth-punctuation
#    handling (all tiers; the parser's clean_punctuation lacks this mapping).
FW_EQ = [
    ("Sentences/Bunun/Bunun.xml", "61_S_2", "FORM", None, "nii＝ik", "nii=ik"),
    ("Sentences/Bunun/Bunun.xml", "63_S_781", "TRANSL", None, "PF＝COS", "PF=COS"),
    ("Sentences/Bunun/Bunun.xml", "54_S_12", "TRANSL", None, "PF＝COS", "PF=COS"),
    ("Stories/Bunun/Bunun_bnNr-frog_Adus.xml", "bnNr-frog_Adus_S_39", "TRANSL", None,
     "虎頭蜂＝遠距", "虎頭蜂=遠距"),
    ("Stories/Bunun/Bunun_bnNr-frog_Laniahu.xml", "bnNr-frog_Laniahu_S_53", "TRANSL", None,
     "狗＝遠距", "狗=遠距"),
    ("Grammar/Sakizaya/Sakizaya.xml", "ap1_S_76", "TRANSL", None,
     "走＝完成貌", "走=完成貌"),
    ("Stories/Saisiyat/Saisiyat_SaiNr-election_lahi_ a taro_ babay.xml",
     "SaiNr-election_lahi_ a taro_ babay_S_3", "TRANSL", None, "那＝你", "那=你"),
    ("Sentences/Kanakanavu/Kanakanavu.xml", "3_S_436", "FORM", None,
     "nomani＝nguain", "nomani=nguain"),
    ("Sentences/Kanakanavu/Kanakanavu.xml", "3_S_437", "FORM", None,
     "in＝kee", "in=kee"),
]
CORRECTIONS.extend(FW_EQ)

# (relative file, S id, notes value set on the S-level original FORM)
NOTES = [
    (_SKZY, "13_S_38", "Source cites NTU Formosan Corpus skzyNr-movingkulang IU100-101"),
    (_SKZY, "13_S_39", "Source cites NTU Formosan Corpus skzyNr-movingkulang IU105-107"),
    (_SKZY, "13_S_48", "Source cites NTU Formosan Corpus skzyNr-movingkulang IU 309-312"),
]


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def _tier(el, tag, kind):
    for c in el.findall(tag):
        if c.get("kindOf") == kind:
            return c
    return None


def main():
    corpus = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", default=str(corpus / "XML"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    by_file = {}
    for entry in CORRECTIONS:
        by_file.setdefault(entry[0], []).append(("text",) + entry[1:])
    for rel, sid, note in NOTES:
        by_file.setdefault(rel, []).append(("note", sid, note))

    applied = stale = phon = 0
    for rel, entries in by_file.items():
        path = os.path.join(args.xml_dir, rel)
        if not os.path.exists(path):
            print(f"  MISSING FILE: {rel}")
            continue
        original = open(path, "rb").read()
        tree = etree.parse(path)
        if serialize(tree) != original:
            print(f"  SKIP (round-trip guard): {rel}")
            continue
        root = tree.getroot()
        mp = load_mappings(language_of(root))
        sindex = {s.get("id"): s for s in root.iter("S")}
        witness_of = {}   # parent element -> witness bool, captured pre-change
        modified = False
        for entry in entries:
            if entry[0] == "note":
                _, sid, note = entry
                s = sindex.get(sid)
                fe = _tier(s, "FORM", "original") if s is not None else None
                if fe is None:
                    print(f"  no match for notes: {rel} {sid}")
                    stale += 1
                elif fe.get("notes") != note:
                    fe.set("notes", note)
                    applied += 1
                    modified = True
                    print(f"  notes set: {rel} {sid}")
                continue
            _, sid, tag, lang, old, new = entry
            s = sindex.get(sid)
            matches = []
            if s is not None:
                for el in s.iter(tag):
                    el_lang = el.get(_XLANG) or el.get("lang")
                    if lang is not None and el_lang != lang:
                        continue
                    if old in (el.text or ""):
                        matches.append(el)
            if not matches:
                stale += 1
                print(f"  no match (already applied or drifted): "
                      f"{rel} {sid} {tag} {old!r}")
                continue
            for el in matches:
                parent = el.getparent()
                if tag == "FORM" and parent is not None \
                        and parent.tag in ("S", "W", "M") \
                        and parent not in witness_of:
                    of = _tier(parent, "FORM", "original")
                    op = _tier(parent, "PHON", "original")
                    witness_of[parent] = (
                        mp is not None and of is not None and op is not None
                        and (of.text or "").strip() and (op.text or "").strip()
                        and convert(of.text, mp) == op.text)
                el.text = el.text.replace(old, new)
                applied += 1
                modified = True
            print(f"  applied ({len(matches)} element(s)): {rel} {sid} {tag}: "
                  f"{old!r} -> {new!r}")
        # PHON regeneration for elements whose FORM changed
        for parent, witness in witness_of.items():
            if not witness:
                print(f"  PHON left (witness failed): {rel} "
                      f"{parent.tag} id={parent.get('id')!r}")
                continue
            for kind in ("original", "standard"):
                fe, pe = _tier(parent, "FORM", kind), _tier(parent, "PHON", kind)
                if fe is not None and pe is not None and (fe.text or "").strip():
                    newp = convert(fe.text, mp)
                    if newp != pe.text:
                        pe.text = newp
                        phon += 1
        if modified and not args.dry_run:
            with open(path, "wb") as f:
                f.write(serialize(tree))
    verb = "would be " if args.dry_run else ""
    print(f"\ncorrections {verb}applied: {applied} (no-match: {stale}, "
          f"PHON regenerated: {phon})")


if __name__ == "__main__":
    main()
