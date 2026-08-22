#!/usr/bin/env python3
"""apply_manual_corrections.py

Apply a small table of hand-verified one-off corrections to the
published XML. Entries name the file, the S id, the element tag, and an
exact old->new text substitution; every matching element inside that S
(both kindOf tiers, W- and M-level alike) is corrected. Entries that already
contain the replacement are reported separately. Missing or drifted targets
fail the run.

After the substitutions, the PHON of every S/W/M element whose FORM
changed is recomputed through the Ortho113 mapping, gated by a
pre-change witness check (converting the old original FORM must
reproduce the old original PHON exactly; see _phon_regen.py).

Current corrections
-------------------
1. Grammar/Sakizaya 13_S_38 / 13_S_39 / 13_S_48: the source grammar
   chapter *cites* corpus examples instead of restating them, so the
   parser made the citation string the sentence FORM, and the real
   words (from the gloss table) carry IU numbers and pause durations
   fused to the first word of each intonation unit
   (``100....（2.2）yah`` -> ``yah``). The corrections strip the IU
   junk from the W/M forms, rebuild the S FORM from the cleaned words,
   and preserve the citation in a ``notes`` attribute on the S-level
   original FORM.
2. AUDIO boundary repairs (see the AUDIO_FIXES table): seven invalid
   start/end boundaries in six Stories files, originally hand-edited in
   commit 1817ae39e and recorded here so they survive regeneration.

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
from decimal import Decimal, InvalidOperation
from pathlib import Path

import lxml.etree as etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _phon_regen import dialect_of, language_of, load_mappings, convert  # noqa: E402

_XLANG = "{http://www.w3.org/XML/1998/namespace}lang"

_SKZY = "Grammar/Sakizaya/Sakizaya.xml"
_CIT38 = "(NTU Formosan Corpus skzyNr-movingkulang IU100-101)"
_CIT39 = "(NTU Formosan Corpus skzyNr-movingkulang IU105-107)"
_CIT48 = "(NTU Formosan Corpus skzyNr-movingkulang IU 309-312)"

# (relative file, S id, element tag, xml:lang or None, old substring, new text)
CORRECTIONS = [
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

# 3. Gloss-table column shifts (wordform column missing in the source
#    grid, so English glosses became "wordforms" and everything slid):
#    - earthquake S_194 (source record 613): true word iza-an-na in ori;
#      stray '608' is an IU number.
#    - TsouConv-informants S_19 (source record 73): true words hia /
#      ma'cohioa. in ori; the shifted third cells are annotator comments.
#      Two impostor W's but only one missing word -> W6 is deleted.
#    Entries use the optional element-id field for M-level precision.

GLOSS_SHIFT = [
    # --- earthquake S_194 ---
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "FORM", None, "dosomethingLF3PLGEN", "izaanna", None),
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "FORM", None, "dosomething-LF-3PLGEN", "iza-an-na", None),
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "TRANSL", "eng", "608", "do.something-LF-3PL.GEN", "KavCon-earthquake_abas_haciang_S_194_W1"),
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "FORM", None, "dosomething", "iza", "KavCon-earthquake_abas_haciang_S_194_W1M1"),
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "TRANSL", "eng", "608", "do.something", "KavCon-earthquake_abas_haciang_S_194_W1M1"),
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "FORM", None, "LF", "an", "KavCon-earthquake_abas_haciang_S_194_W1M2"),
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "FORM", None, "3PLGEN", "na", "KavCon-earthquake_abas_haciang_S_194_W1M3"),
    # --- TsouConv-informants S_19 ---
    ("Stories/Tsou/Tsou_TsouConv-informants.xml", "TsouConv-informants_S_19",
     "FORM", None, "hia how teachPF.", "hia ma'cohioa.", None),
    ("Stories/Tsou/Tsou_TsouConv-informants.xml", "TsouConv-informants_S_19",
     "FORM", None, "how", "ma'cohioa.", "TsouConv-informants_S_19_W6"),
    ("Stories/Tsou/Tsou_TsouConv-informants.xml", "TsouConv-informants_S_19",
     "FORM", None, "how", "ma'cohioa.", "TsouConv-informants_S_19_W6M1"),
    ("Stories/Tsou/Tsou_TsouConv-informants.xml", "TsouConv-informants_S_19",
     "TRANSL", "eng", "如何", "teach.PF", "TsouConv-informants_S_19_W6"),
    ("Stories/Tsou/Tsou_TsouConv-informants.xml", "TsouConv-informants_S_19",
     "TRANSL", "zho", "但是這裡出現的是ma'cohioa", "教.受焦", "TsouConv-informants_S_19_W6"),
    ("Stories/Tsou/Tsou_TsouConv-informants.xml", "TsouConv-informants_S_19",
     "TRANSL", "eng", "如何", "teach.PF", "TsouConv-informants_S_19_W6M1"),
    ("Stories/Tsou/Tsou_TsouConv-informants.xml", "TsouConv-informants_S_19",
     "TRANSL", "zho", "但是這裡出現的是ma'cohioa", "教.受焦", "TsouConv-informants_S_19_W6M1"),
]

# 4b. Two more column-shifted rows found by the 2026-06-11 source sweep
#     (impostor English word as form + IU number in the stray cell);
#     true forms from the source ori field.
GLOSS_SHIFT.extend([
    # KavCon-home rec 213: ['how', '如何', '212']; ori: qumuni,
    ("Stories/Kavalan/Kavalan_KavCon-home_buya_imuy.xml", "KavCon-home_buya_imuy_S_69",
     "FORM", None, " how ", " qumuni ", None),
    ("Stories/Kavalan/Kavalan_KavCon-home_buya_imuy.xml", "KavCon-home_buya_imuy_S_69",
     "FORM", None, "how", "qumuni,", "KavCon-home_buya_imuy_S_69_W6"),
    ("Stories/Kavalan/Kavalan_KavCon-home_buya_imuy.xml", "KavCon-home_buya_imuy_S_69",
     "FORM", None, "how", "qumuni,", "KavCon-home_buya_imuy_S_69_W6M1"),
    ("Stories/Kavalan/Kavalan_KavCon-home_buya_imuy.xml", "KavCon-home_buya_imuy_S_69",
     "TRANSL", "eng", "212", "how", "KavCon-home_buya_imuy_S_69_W6"),
    ("Stories/Kavalan/Kavalan_KavCon-home_buya_imuy.xml", "KavCon-home_buya_imuy_S_69",
     "TRANSL", "eng", "212", "how", "KavCon-home_buya_imuy_S_69_W6M1"),
    # KavCon-relatives rec 225: ['that', '那個', '205']; ori: 'nay==,
    ("Stories/Kavalan/Kavalan_KavCon-relatives_buya_ngengi.xml", "KavCon-relatives_buya_ngengi_S_70",
     "FORM", None, " that ", " 'nay ", None),
    ("Stories/Kavalan/Kavalan_KavCon-relatives_buya_ngengi.xml", "KavCon-relatives_buya_ngengi_S_70",
     "FORM", None, "that", "'nay,", "KavCon-relatives_buya_ngengi_S_70_W2"),
    ("Stories/Kavalan/Kavalan_KavCon-relatives_buya_ngengi.xml", "KavCon-relatives_buya_ngengi_S_70",
     "FORM", None, "that", "'nay,", "KavCon-relatives_buya_ngengi_S_70_W2M1"),
    ("Stories/Kavalan/Kavalan_KavCon-relatives_buya_ngengi.xml", "KavCon-relatives_buya_ngengi_S_70",
     "TRANSL", "eng", "205", "that", "KavCon-relatives_buya_ngengi_S_70_W2"),
    ("Stories/Kavalan/Kavalan_KavCon-relatives_buya_ngengi.xml", "KavCon-relatives_buya_ngengi_S_70",
     "TRANSL", "eng", "205", "that", "KavCon-relatives_buya_ngengi_S_70_W2M1"),
])
# 4c. Source echo rows and a diagonally-slid grid (2026-06-11 review of
#     gloss_anomalies_review.csv). In sdqCon-dialog2 record 187 the gloss
#     cells just repeat the wordform (echo rows); clean duplicates of the
#     same words elsewhere in the file supply the real glosses. In
#     sdqNr-mother_iwan record 143 the grid slid diagonally and the four
#     Chinese glosses fell into orphan rows; both gloss tiers are
#     recoverable from the record itself.
_DLG2="Stories/Seediq/Seediq_sdqCon-dialog2_ciwas_tiwas 2021s.xml"
_MIWAN="Stories/Seediq/Seediq_sdqNr-mother_iwan 2020s.xml"
_S128="sdqCon-dialog2_ciwas_tiwas 2021s_S_128"
_S32="sdqNr-mother_iwan 2020s_S_32"
GLOSS_SHIFT.extend([
    (_DLG2, _S128, "TRANSL", "eng", "mu[da", "AF-pass", None),
    (_DLG2, _S128, "TRANSL", "zho", "m-u[da", "主焦-經過", None),
    (_DLG2, _S128, "TRANSL", "eng", "icin", "another", None),
    (_DLG2, _S128, "TRANSL", "zho", "icin", "另一", None),
])

# 5. Stray number fused to a wordform in the source gloss table
#    (Grammar/Kanakanavu 12_S_5: gloss-table wordform 'na33' vs ori 'na';
#    same genus as the fused example numbers, but not sentence-final).
GLOSS_SHIFT.append(
    ("Grammar/Kanakanavu/Kanakanavu.xml", "12_S_5", "FORM", None, "na33", "na", None))

# 6. M-tier completion for the gloss-shift repairs (2026-06-11 follow-up:
#    the S_32/S_128 repairs initially fixed only the W tier, leaving the
#    whole-word gloss unsplit on M1 and junk in siblings; also fill the
#    benign missing English cells left by the earlier per-M repairs).
#    FILL entries: (file, S id, element id, tag, kindOf-or-lang, text) —
#    set only if the tier is empty/absent; FORM fills also set the
#    matching empty PHON via the Ortho113 mapping.
FILLS = [
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "KavCon-earthquake_abas_haciang_S_194_W1M2", "TRANSL", "eng", "LF"),
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "KavCon-earthquake_abas_haciang_S_194_W1M3", "TRANSL", "eng", "3PL.GEN"),
    ("Stories/Seediq/Seediq_sdqCon-dialog2_ciwas_tiwas 2021s.xml", "sdqCon-dialog2_ciwas_tiwas 2021s_S_128",
     "sdqCon-dialog2_ciwas_tiwas 2021s_S_128_W8M2", "TRANSL", "eng", "pass"),
]
_S128b="sdqCon-dialog2_ciwas_tiwas 2021s_S_128"
_S32b="sdqNr-mother_iwan 2020s_S_32"
GLOSS_SHIFT.extend([
    # S_128 W5: split the whole-word gloss across the morphemes
    (_DLG2, _S128b, "TRANSL", "eng", "AF-pass", "AF", _S128b+"_W8M1"),
    (_DLG2, _S128b, "TRANSL", "zho", "m", "主焦", _S128b+"_W8M1"),
    (_DLG2, _S128b, "TRANSL", "zho", "u[da", "經過", _S128b+"_W8M2"),
    # S_32 W17-W20: the source grid's second column contains segmented
    # forms and its third column contains English glosses; Chinese glosses
    # survive in the following four orphan rows.
    (_MIWAN, _S32b, "FORM", None, "kesun", "kesa-un", _S32b+"_W17"),
    (_MIWAN, _S32b, "TRANSL", "eng", "kesa-un", "say-PF", _S32b+"_W17"),
    (_MIWAN, _S32b, "TRANSL", "zho", "say-PF", "說-受焦", _S32b+"_W17"),
    (_MIWAN, _S32b, "TRANSL", "eng", "rudan", "elderly", _S32b+"_W18"),
    (_MIWAN, _S32b, "TRANSL", "zho", "elderly", "長者", _S32b+"_W18"),
    (_MIWAN, _S32b, "TRANSL", "eng", "rudan", "elderly", _S32b+"_W18M1"),
    (_MIWAN, _S32b, "TRANSL", "zho", "elderly", "長者", _S32b+"_W18M1"),
    (_MIWAN, _S32b, "TRANSL", "eng", "cbeyo", "past", _S32b+"_W19"),
    (_MIWAN, _S32b, "TRANSL", "zho", "past", "以前", _S32b+"_W19"),
    (_MIWAN, _S32b, "TRANSL", "eng", "cbeyo", "past", _S32b+"_W19M1"),
    (_MIWAN, _S32b, "TRANSL", "zho", "past", "以前", _S32b+"_W19M1"),
    (_MIWAN, _S32b, "TRANSL", "eng", "mesa.\\", "AF.say", _S32b+"_W20"),
    (_MIWAN, _S32b, "TRANSL", "zho", "AF.say", "主焦.說", _S32b+"_W20"),
    (_MIWAN, _S32b, "TRANSL", "eng", "mesa.\\", "AF.say", _S32b+"_W20M1"),
    (_MIWAN, _S32b, "TRANSL", "zho", "AF.say", "主焦.說", _S32b+"_W20M1"),
])
# (relative file, S id, W id to delete) — impostor words with no source word
DELETE_W = [
    ("Stories/Tsou/Tsou_TsouConv-informants.xml", "TsouConv-informants_S_19",
     "TsouConv-informants_S_19_W7"),
]

GLOSS_SHIFT_NOTES = [
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "gloss-table column shift repaired from source; consult the NTU Formosan Corpus source"),
    ("Stories/Tsou/Tsou_TsouConv-informants.xml", "TsouConv-informants_S_19",
     "gloss-table column shift repaired from source; an impostor word was removed; consult the NTU Formosan Corpus source"),
    ("Stories/Kavalan/Kavalan_KavCon-home_buya_imuy.xml", "KavCon-home_buya_imuy_S_69",
     "gloss-table column shift repaired from source; consult the NTU Formosan Corpus source"),
    ("Stories/Kavalan/Kavalan_KavCon-relatives_buya_ngengi.xml", "KavCon-relatives_buya_ngengi_S_70",
     "gloss-table column shift repaired from source; consult the NTU Formosan Corpus source"),
    ("Stories/Seediq/Seediq_sdqCon-dialog2_ciwas_tiwas 2021s.xml", "sdqCon-dialog2_ciwas_tiwas 2021s_S_128",
     "source echo-row glosses replaced from clean duplicates; consult the NTU Formosan Corpus source"),
    ("Stories/Seediq/Seediq_sdqNr-mother_iwan 2020s.xml", "sdqNr-mother_iwan 2020s_S_32",
     "gloss grid slid in source; glosses restored from the record's orphan rows; consult the NTU Formosan Corpus source"),
]

# (relative file, S id, notes value set on the S-level original FORM)
NOTES = [
    (_SKZY, "13_S_38", "Source cites NTU Formosan Corpus skzyNr-movingkulang IU100-101"),
    (_SKZY, "13_S_39", "Source cites NTU Formosan Corpus skzyNr-movingkulang IU105-107"),
    (_SKZY, "13_S_48", "Source cites NTU Formosan Corpus skzyNr-movingkulang IU 309-312"),
]

# 7. AUDIO boundary repairs (2026-07-29 remediation, commit 1817ae39e;
#    recorded here 2026-08-10 so they survive regeneration): seven invalid
#    start/end boundaries in the Stories subcorpus — zero-duration or
#    overlapping segments (end <= start, or a boundary shared with the next
#    sentence sitting on the wrong side) nudged to the nearest valid value,
#    plus one start that carried a copy-paste value from the end of the
#    file (dialog5 S_1: start 418.22 on a 0.64-end segment -> 0.29).
#    (relative file, S id, attribute, old value, new value) — applied to
#    the S-level AUDIO element; entries whose attribute already holds the
#    new value are reported as already-applied.
_EARTHQ = "Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml"
_HOME = "Stories/Kavalan/Kavalan_KavCon-home_buya_imuy.xml"
_DLG1 = "Stories/Seediq/Seediq_sdqCon-dialog1_ciwas_tiwas 2021s.xml"
_DLG3 = "Stories/Seediq/Seediq_sdqCon-dialog3_robo_bakan 2021s.xml"
_DLG5 = "Stories/Seediq/Seediq_sdqCon-dialog5_dakis_takun 2020s.xml"
AUDIO_FIXES = [
    (_EARTHQ, "KavCon-earthquake_abas_haciang_S_101", "end",   "351.4",  "351.43"),
    (_EARTHQ, "KavCon-earthquake_abas_haciang_S_102", "start", "351.4",  "351.43"),
    (_HOME,   "KavCon-home_buya_imuy_S_77",           "end",   "304.45", "304.50"),
    (_HOME,   "KavCon-home_buya_imuy_S_78",           "start", "304.45", "304.50"),
    (_DLG1,   "sdqCon-dialog1_ciwas_tiwas 2021s_S_142", "end",   "416.05", "416.06"),
    (_DLG1,   "sdqCon-dialog1_ciwas_tiwas 2021s_S_143", "start", "416.05", "416.06"),
    (_DLG2,   "sdqCon-dialog2_ciwas_tiwas 2021s_S_111", "end",   "250.53", "250.54"),
    (_DLG2,   "sdqCon-dialog2_ciwas_tiwas 2021s_S_112", "start", "250.53", "250.54"),
    (_DLG2,   "sdqCon-dialog2_ciwas_tiwas 2021s_S_130", "end",   "291.74", "291.75"),
    (_DLG3,   "sdqCon-dialog3_robo_bakan 2021s_S_1",    "end",   "0.63",   "1.05"),
    (_DLG3,   "sdqCon-dialog3_robo_bakan 2021s_S_2",    "start", "0.63",   "1.05"),
    (_DLG5,   "sdqCon-dialog5_dakis_takun 2020s_S_1",   "start", "418.22", "0.29"),
]


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def _tier(el, tag, kind):
    for c in el.findall(tag):
        if c.get("kindOf") == kind:
            return c
    return None


def _same_audio_boundary(actual, expected):
    """Compare serialized audio seconds without depending on zero padding."""
    try:
        return Decimal(actual) == Decimal(expected)
    except (InvalidOperation, TypeError):
        return actual == expected


def main():
    corpus = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", default=str(corpus / "XML"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    by_file = {}
    for entry in CORRECTIONS:
        e = entry if len(entry) == 7 else entry + (None,)
        by_file.setdefault(e[0], []).append(("text",) + e[1:])
    for entry in GLOSS_SHIFT:
        by_file.setdefault(entry[0], []).append(("text",) + entry[1:])
    for rel, sid, wid in DELETE_W:
        by_file.setdefault(rel, []).append(("delw", sid, wid))
    for rel, sid, eid, tag, kol, text in FILLS:
        by_file.setdefault(rel, []).append(("fill", sid, eid, tag, kol, text))
    for rel, sid, note in list(NOTES) + GLOSS_SHIFT_NOTES:
        by_file.setdefault(rel, []).append(("note", sid, note))
    for rel, sid, attr, old, new in AUDIO_FIXES:
        by_file.setdefault(rel, []).append(("audio", sid, attr, old, new))

    applied = already = drifted = phon = 0
    for rel, entries in by_file.items():
        path = os.path.join(args.xml_dir, rel)
        if not os.path.exists(path):
            print(f"  MISSING FILE: {rel}")
            drifted += 1
            continue
        original = open(path, "rb").read()
        tree = etree.parse(path)
        if serialize(tree) != original:
            print(f"  SKIP (round-trip guard): {rel}")
            drifted += 1
            continue
        root = tree.getroot()
        mp = load_mappings(language_of(root), dialect_of(root))
        sindex = {s.get("id"): s for s in root.iter("S")}
        note_witnesses = {
            (wrel, wsid): note
            for wrel, wsid, note in list(NOTES) + GLOSS_SHIFT_NOTES
        }

        def has_repair_witness(sid):
            sentence = sindex.get(sid)
            form = (
                _tier(sentence, "FORM", "original")
                if sentence is not None else None
            )
            notes = form.get("notes") or "" if form is not None else ""
            witness = note_witnesses.get((rel, sid))
            return bool(witness and witness in notes)

        witness_of = {}   # parent element -> witness bool, captured pre-change
        modified = False
        for entry in entries:
            if entry[0] == "audio":
                _, sid, attr, old, new = entry
                s = sindex.get(sid)
                a = s.find("AUDIO") if s is not None else None
                current = a.get(attr) if a is not None else None
                if a is None:
                    print(f"  no match for audio fix (no S-level AUDIO): {rel} {sid}")
                    drifted += 1
                elif _same_audio_boundary(current, new):
                    print(
                        f"  audio fix already applied: {rel} {sid} "
                        f"{attr}={current}"
                    )
                    already += 1
                elif _same_audio_boundary(current, old):
                    a.set(attr, new)
                    applied += 1
                    modified = True
                    print(f"  audio fix: {rel} {sid} {attr}: {old} -> {new}")
                else:
                    print(f"  no match for audio fix (drifted: {attr}="
                          f"{current!r}): {rel} {sid}")
                    drifted += 1
                continue
            if entry[0] == "note":
                _, sid, note = entry
                s = sindex.get(sid)
                fe = _tier(s, "FORM", "original") if s is not None else None
                if fe is None:
                    print(f"  no match for notes: {rel} {sid}")
                    drifted += 1
                elif note not in (fe.get("notes") or ""):
                    existing = fe.get("notes") or ""
                    fe.set("notes", f"{existing} | {note}" if existing else note)
                    applied += 1
                    modified = True
                    print(f"  notes appended: {rel} {sid}")
                else:
                    already += 1
                    print(f"  notes already present: {rel} {sid}")
                continue
            if entry[0] == "fill":
                _, sid, eid, tag, kol, text = entry
                s_el = sindex.get(sid)
                parent = None
                if s_el is not None:
                    for cand in s_el.iter():
                        if cand.tag in ("W", "M", "S") and cand.get("id") == eid:
                            parent = cand
                            break
                if parent is None:
                    if has_repair_witness(sid):
                        print(f"  fill already applied (repair witness): {rel} {eid}")
                        already += 1
                    else:
                        print(f"  no match for fill: {rel} {eid}")
                        drifted += 1
                    continue
                if tag == "TRANSL":
                    tel = next((t for t in parent.findall("TRANSL")
                                if (t.get(_XLANG) or t.get("lang")) == kol), None)
                    if tel is None:
                        tel = etree.SubElement(parent, "TRANSL")
                        tel.set(_XLANG, kol)
                    current = (tel.text or "").strip()
                    if current == text:
                        print(f"  fill already applied: {rel} {eid} {tag}/{kol}")
                        already += 1
                        continue
                    if current:
                        if has_repair_witness(sid):
                            print(
                                f"  fill already applied (repair witness): "
                                f"{rel} {eid} {tag}/{kol}"
                            )
                            already += 1
                        else:
                            print(
                                f"  fill drifted: {rel} {eid} {tag}/{kol}; "
                                f"expected empty or {text!r}, found {current!r}"
                            )
                            drifted += 1
                        continue
                    tel.text = text
                else:
                    el2 = _tier(parent, tag, kol)
                    if el2 is None:
                        print(f"  fill drifted (missing tier): {rel} {eid} {tag}/{kol}")
                        drifted += 1
                        continue
                    current = (el2.text or "").strip()
                    if current == text:
                        print(f"  fill already applied: {rel} {eid} {tag}/{kol}")
                        already += 1
                        continue
                    if current:
                        if has_repair_witness(sid):
                            print(
                                f"  fill already applied (repair witness): "
                                f"{rel} {eid} {tag}/{kol}"
                            )
                            already += 1
                        else:
                            print(
                                f"  fill drifted: {rel} {eid} {tag}/{kol}; "
                                f"expected empty or {text!r}, found {current!r}"
                            )
                            drifted += 1
                        continue
                    el2.text = text
                    if tag == "FORM" and mp is not None:
                        pe = _tier(parent, "PHON", kol)
                        if pe is not None and not (pe.text or "").strip():
                            pe.text = convert(text, mp)
                            phon += 1
                applied += 1
                modified = True
                print(f"  filled: {rel} {eid} {tag}/{kol} = {text!r}")
                continue
            if entry[0] == "delw":
                _, sid, wid = entry
                s = sindex.get(sid)
                target = None
                if s is not None:
                    for w in s.iter():
                        if w.tag in ("W", "M") and w.get("id") == wid:
                            target = w
                            break
                if target is None:
                    print(f"  delete-W already applied: {rel} {wid}")
                    already += 1
                else:
                    target.getparent().remove(target)
                    applied += 1
                    modified = True
                    print(f"  deleted impostor W: {rel} {wid}")
                continue
            _, sid, tag, lang, old, new, elem_id = entry
            s = sindex.get(sid)
            matches = []
            replacements = []
            if s is not None:
                for el in s.iter(tag):
                    el_lang = el.get(_XLANG) or el.get("lang")
                    if lang is not None and el_lang != lang:
                        continue
                    if elem_id is not None:
                        parent = el.getparent()
                        if parent is None or parent.get("id") != elem_id:
                            continue
                    if old in (el.text or ""):
                        matches.append(el)
                    if new in (el.text or ""):
                        replacements.append(el)
            if not matches:
                if replacements:
                    already += 1
                    print(
                        f"  already applied ({len(replacements)} element(s)): "
                        f"{rel} {sid} {tag}: {new!r}"
                    )
                elif has_repair_witness(sid):
                    already += 1
                    print(
                        f"  already applied (repair witness): {rel} {sid} "
                        f"{tag}: {old!r} -> {new!r}"
                    )
                else:
                    drifted += 1
                    print(
                        f"  DRIFTED: {rel} {sid} {tag}; found neither "
                        f"{old!r} nor {new!r}"
                    )
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
    print(
        f"\ncorrections {verb}applied: {applied} "
        f"(already applied: {already}, drifted: {drifted}, "
        f"PHON regenerated: {phon})"
    )
    if drifted:
        raise AssertionError(
            f"{drifted} manual correction target(s) drifted or were unavailable"
        )


if __name__ == "__main__":
    main()
