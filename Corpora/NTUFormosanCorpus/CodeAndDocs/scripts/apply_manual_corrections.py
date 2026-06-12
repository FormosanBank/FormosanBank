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

# 4. Gloss-table column shifts (wordform column missing in the source
#    grid, so English glosses became "wordforms" and everything slid):
#    - fishing_Pani S_34 (source record 226): true words matupuru, /
#      kisʉ-ʉn=maku. survive in the source ori field; strays 到達中間/太陽
#      are glosses of untranscribed context words (matavʉcʉ, taniarʉ).
#    - earthquake S_194 (source record 613): true word iza-an-na in ori;
#      stray '608' is an IU number.
#    - TsouConv-informants S_19 (source record 73): true words hia /
#      ma'cohioa. in ori; the shifted third cells are annotator comments.
#      Two impostor W's but only one missing word -> W6 is deleted.
#    Entries use the optional element-id field for M-level precision.

GLOSS_SHIFT = [
    # --- fishing_Pani S_34 ---
    ("Stories/Kanakanavu/Kanakanavu_kkvNr_fishing_Pani.xml", "kkvNr_fishing_Pani_S_34",
     "FORM", None, "makefireAF callPF1SGGEN.", "matupuru, kisʉʉnmaku.", None),
    ("Stories/Kanakanavu/Kanakanavu_kkvNr_fishing_Pani.xml", "kkvNr_fishing_Pani_S_34",
     "FORM", None, "makefireAF", "matupuru,", None),
    ("Stories/Kanakanavu/Kanakanavu_kkvNr_fishing_Pani.xml", "kkvNr_fishing_Pani_S_34",
     "FORM", None, "call-PF=1SGGEN", "kisʉ-ʉn=maku.", None),
    ("Stories/Kanakanavu/Kanakanavu_kkvNr_fishing_Pani.xml", "kkvNr_fishing_Pani_S_34",
     "TRANSL", "eng", "生火.主焦", "make.fire.AF", None),
    ("Stories/Kanakanavu/Kanakanavu_kkvNr_fishing_Pani.xml", "kkvNr_fishing_Pani_S_34",
     "TRANSL", "zho", "到達中間", "生火.主焦", None),
    ("Stories/Kanakanavu/Kanakanavu_kkvNr_fishing_Pani.xml", "kkvNr_fishing_Pani_S_34",
     "TRANSL", "eng", "叫-受焦=1SG.屬格", "call-PF=1SG.GEN", None),
    ("Stories/Kanakanavu/Kanakanavu_kkvNr_fishing_Pani.xml", "kkvNr_fishing_Pani_S_34",
     "TRANSL", "zho", "太陽", "叫-受焦=1SG.屬格", "kkvNr_fishing_Pani_S_34_W10"),
    ("Stories/Kanakanavu/Kanakanavu_kkvNr_fishing_Pani.xml", "kkvNr_fishing_Pani_S_34",
     "FORM", None, "call", "kisʉ", "kkvNr_fishing_Pani_S_34_W10M1"),
    ("Stories/Kanakanavu/Kanakanavu_kkvNr_fishing_Pani.xml", "kkvNr_fishing_Pani_S_34",
     "TRANSL", "eng", "叫", "call", "kkvNr_fishing_Pani_S_34_W10M1"),
    ("Stories/Kanakanavu/Kanakanavu_kkvNr_fishing_Pani.xml", "kkvNr_fishing_Pani_S_34",
     "TRANSL", "zho", "太陽", "叫", "kkvNr_fishing_Pani_S_34_W10M1"),
    ("Stories/Kanakanavu/Kanakanavu_kkvNr_fishing_Pani.xml", "kkvNr_fishing_Pani_S_34",
     "FORM", None, "PF", "ʉn", "kkvNr_fishing_Pani_S_34_W10M2"),
    ("Stories/Kanakanavu/Kanakanavu_kkvNr_fishing_Pani.xml", "kkvNr_fishing_Pani_S_34",
     "TRANSL", "eng", "受焦", "PF", "kkvNr_fishing_Pani_S_34_W10M2"),
    ("Stories/Kanakanavu/Kanakanavu_kkvNr_fishing_Pani.xml", "kkvNr_fishing_Pani_S_34",
     "FORM", None, "1SGGEN", "maku", "kkvNr_fishing_Pani_S_34_W10M3"),
    ("Stories/Kanakanavu/Kanakanavu_kkvNr_fishing_Pani.xml", "kkvNr_fishing_Pani_S_34",
     "TRANSL", "eng", "1SG.屬格", "1SG.GEN", "kkvNr_fishing_Pani_S_34_W10M3"),
    # --- earthquake S_194 ---
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "FORM", None, "dosomethingLF3PLGEN", "izaanna", None),
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "FORM", None, "dosomething-LF-3PLGEN", "iza-an-na", None),
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "TRANSL", "eng", "做某事-處焦-3PL.屬格", "do.something-LF-3PL.GEN", "KavCon-earthquake_abas_haciang_S_194_W1"),
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "TRANSL", "zho", "608", "做某事-處焦-3PL.屬格", "KavCon-earthquake_abas_haciang_S_194_W1"),
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "FORM", None, "dosomething", "iza", "KavCon-earthquake_abas_haciang_S_194_W1M1"),
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "TRANSL", "eng", "做某事", "do.something", "KavCon-earthquake_abas_haciang_S_194_W1M1"),
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "TRANSL", "zho", "608", "做某事", "KavCon-earthquake_abas_haciang_S_194_W1M1"),
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "FORM", None, "LF", "an", "KavCon-earthquake_abas_haciang_S_194_W1M2"),
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "TRANSL", "eng", "處焦", "LF", "KavCon-earthquake_abas_haciang_S_194_W1M2"),
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "FORM", None, "3PLGEN", "na", "KavCon-earthquake_abas_haciang_S_194_W1M3"),
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "TRANSL", "eng", "3PL.屬格", "3PL.GEN", "KavCon-earthquake_abas_haciang_S_194_W1M3"),
    # --- TsouConv-informants S_19 ---
    ("Stories/Tsou/Tsou_TsouConv-informants.xml", "TsouConv-informants_S_19",
     "FORM", None, "hia how teachPF.", "hia ma'cohioa.", None),
    ("Stories/Tsou/Tsou_TsouConv-informants.xml", "TsouConv-informants_S_19",
     "FORM", None, "how", "ma'cohioa.", "TsouConv-informants_S_19_W5"),
    ("Stories/Tsou/Tsou_TsouConv-informants.xml", "TsouConv-informants_S_19",
     "FORM", None, "how", "ma'cohioa.", "TsouConv-informants_S_19_W5M1"),
    ("Stories/Tsou/Tsou_TsouConv-informants.xml", "TsouConv-informants_S_19",
     "TRANSL", "eng", "如何", "teach.PF", "TsouConv-informants_S_19_W5"),
    ("Stories/Tsou/Tsou_TsouConv-informants.xml", "TsouConv-informants_S_19",
     "TRANSL", "zho", "但是這裡出現的是ma'cohioa", "教.受焦", "TsouConv-informants_S_19_W5"),
    ("Stories/Tsou/Tsou_TsouConv-informants.xml", "TsouConv-informants_S_19",
     "TRANSL", "eng", "如何", "teach.PF", "TsouConv-informants_S_19_W5M1"),
    ("Stories/Tsou/Tsou_TsouConv-informants.xml", "TsouConv-informants_S_19",
     "TRANSL", "zho", "但是這裡出現的是ma'cohioa", "教.受焦", "TsouConv-informants_S_19_W5M1"),
]

# 4b. Two more column-shifted rows found by the 2026-06-11 source sweep
#     (impostor English word as form + IU number in the stray cell);
#     true forms from the source ori field.
GLOSS_SHIFT.extend([
    # KavCon-home rec 213: ['how', '如何', '212']; ori: qumuni,
    ("Stories/Kavalan/Kavalan_KavCon-home_buya_imuy.xml", "KavCon-home_buya_imuy_S_69",
     "FORM", None, " how ", " qumuni ", None),
    ("Stories/Kavalan/Kavalan_KavCon-home_buya_imuy.xml", "KavCon-home_buya_imuy_S_69",
     "FORM", None, "how", "qumuni,", "KavCon-home_buya_imuy_S_69_W4"),
    ("Stories/Kavalan/Kavalan_KavCon-home_buya_imuy.xml", "KavCon-home_buya_imuy_S_69",
     "FORM", None, "how", "qumuni,", "KavCon-home_buya_imuy_S_69_W4M1"),
    ("Stories/Kavalan/Kavalan_KavCon-home_buya_imuy.xml", "KavCon-home_buya_imuy_S_69",
     "TRANSL", "eng", "如何", "how", "KavCon-home_buya_imuy_S_69_W4"),
    ("Stories/Kavalan/Kavalan_KavCon-home_buya_imuy.xml", "KavCon-home_buya_imuy_S_69",
     "TRANSL", "zho", "212", "如何", "KavCon-home_buya_imuy_S_69_W4"),
    ("Stories/Kavalan/Kavalan_KavCon-home_buya_imuy.xml", "KavCon-home_buya_imuy_S_69",
     "TRANSL", "eng", "如何", "how", "KavCon-home_buya_imuy_S_69_W4M1"),
    ("Stories/Kavalan/Kavalan_KavCon-home_buya_imuy.xml", "KavCon-home_buya_imuy_S_69",
     "TRANSL", "zho", "212", "如何", "KavCon-home_buya_imuy_S_69_W4M1"),
    # KavCon-relatives rec 225: ['that', '那個', '205']; ori: 'nay==,
    ("Stories/Kavalan/Kavalan_KavCon-relatives_buya_ngengi.xml", "KavCon-relatives_buya_ngengi_S_70",
     "FORM", None, " that ", " 'nay ", None),
    ("Stories/Kavalan/Kavalan_KavCon-relatives_buya_ngengi.xml", "KavCon-relatives_buya_ngengi_S_70",
     "FORM", None, "that", "'nay,", "KavCon-relatives_buya_ngengi_S_70_W1"),
    ("Stories/Kavalan/Kavalan_KavCon-relatives_buya_ngengi.xml", "KavCon-relatives_buya_ngengi_S_70",
     "FORM", None, "that", "'nay,", "KavCon-relatives_buya_ngengi_S_70_W1M1"),
    ("Stories/Kavalan/Kavalan_KavCon-relatives_buya_ngengi.xml", "KavCon-relatives_buya_ngengi_S_70",
     "TRANSL", "eng", "那個", "that", "KavCon-relatives_buya_ngengi_S_70_W1"),
    ("Stories/Kavalan/Kavalan_KavCon-relatives_buya_ngengi.xml", "KavCon-relatives_buya_ngengi_S_70",
     "TRANSL", "zho", "205", "那個", "KavCon-relatives_buya_ngengi_S_70_W1"),
    ("Stories/Kavalan/Kavalan_KavCon-relatives_buya_ngengi.xml", "KavCon-relatives_buya_ngengi_S_70",
     "TRANSL", "eng", "那個", "that", "KavCon-relatives_buya_ngengi_S_70_W1M1"),
    ("Stories/Kavalan/Kavalan_KavCon-relatives_buya_ngengi.xml", "KavCon-relatives_buya_ngengi_S_70",
     "TRANSL", "zho", "205", "那個", "KavCon-relatives_buya_ngengi_S_70_W1M1"),
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
    (_MIWAN, _S32, "TRANSL", "eng", "..", "say-PF", None),
    (_MIWAN, _S32, "TRANSL", "zho", "say-PF", "說-受焦", None),
    (_MIWAN, _S32, "TRANSL", "eng", "kesa-un", "elderly", None),
    (_MIWAN, _S32, "TRANSL", "zho", "elderly", "長者", None),
    (_MIWAN, _S32, "TRANSL", "eng", "rudan", "past", None),
    (_MIWAN, _S32, "TRANSL", "zho", "past", "以前", None),
    (_MIWAN, _S32, "TRANSL", "eng", "cbeyo", "AF.say", None),
    (_MIWAN, _S32, "TRANSL", "zho", "AF.say", "主焦.說", None),
])

# 5. Stray number fused to a wordform in the source gloss table
#    (Grammar/Kanakanavu 12_S_5: gloss-table wordform 'na33' vs ori 'na';
#    same genus as the fused example numbers, but not sentence-final).
GLOSS_SHIFT.append(
    ("Grammar/Kanakanavu/Kanakanavu.xml", "12_S_5", "FORM", None, "na33", "na", None))

# 6. M-tier completion for the gloss-shift repairs (2026-06-11 follow-up:
#    the S_32/S_128 repairs initially fixed only the W tier, leaving the
#    whole-word gloss unsplit on M1 and junk in siblings; also fill the
#    benign missing zho cells left by the earlier per-M repairs).
#    FILL entries: (file, S id, element id, tag, kindOf-or-lang, text) —
#    set only if the tier is empty/absent; FORM fills also set the
#    matching empty PHON via the Ortho113 mapping.
FILLS = [
    ("Stories/Kanakanavu/Kanakanavu_kkvNr_fishing_Pani.xml", "kkvNr_fishing_Pani_S_34",
     "kkvNr_fishing_Pani_S_34_W10M2", "TRANSL", "zho", "受焦"),
    ("Stories/Kanakanavu/Kanakanavu_kkvNr_fishing_Pani.xml", "kkvNr_fishing_Pani_S_34",
     "kkvNr_fishing_Pani_S_34_W10M3", "TRANSL", "zho", "1SG.屬格"),
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "KavCon-earthquake_abas_haciang_S_194_W1M2", "TRANSL", "zho", "處焦"),
    ("Stories/Kavalan/Kavalan_KavCon-earthquake_abas_haciang.xml", "KavCon-earthquake_abas_haciang_S_194",
     "KavCon-earthquake_abas_haciang_S_194_W1M3", "TRANSL", "zho", "3PL.屬格"),
    ("Stories/Seediq/Seediq_sdqCon-dialog2_ciwas_tiwas 2021s.xml", "sdqCon-dialog2_ciwas_tiwas 2021s_S_128",
     "sdqCon-dialog2_ciwas_tiwas 2021s_S_128_W5M2", "TRANSL", "eng", "pass"),
    ("Stories/Seediq/Seediq_sdqNr-mother_iwan 2020s.xml", "sdqNr-mother_iwan 2020s_S_32",
     "sdqNr-mother_iwan 2020s_S_32_W17M2", "FORM", "original", "un"),
    ("Stories/Seediq/Seediq_sdqNr-mother_iwan 2020s.xml", "sdqNr-mother_iwan 2020s_S_32",
     "sdqNr-mother_iwan 2020s_S_32_W17M2", "FORM", "standard", "un"),
    ("Stories/Seediq/Seediq_sdqNr-mother_iwan 2020s.xml", "sdqNr-mother_iwan 2020s_S_32",
     "sdqNr-mother_iwan 2020s_S_32_W17M2", "TRANSL", "eng", "PF"),
]
_S128b="sdqCon-dialog2_ciwas_tiwas 2021s_S_128"
_S32b="sdqNr-mother_iwan 2020s_S_32"
GLOSS_SHIFT.extend([
    # S_128 W5: split the whole-word gloss across the morphemes
    (_DLG2, _S128b, "TRANSL", "eng", "AF-pass", "AF", _S128b+"_W5M1"),
    (_DLG2, _S128b, "TRANSL", "zho", "m", "主焦", _S128b+"_W5M1"),
    (_DLG2, _S128b, "TRANSL", "zho", "u[da", "經過", _S128b+"_W5M2"),
    # S_32 W17: borrow segmentation kesa-un from the source row
    (_MIWAN, _S32b, "FORM", None, "kesun", "kesa", _S32b+"_W17M1"),
    (_MIWAN, _S32b, "TRANSL", "eng", "say-PF", "say", _S32b+"_W17M1"),
    (_MIWAN, _S32b, "TRANSL", "zho", "say", "說", _S32b+"_W17M1"),
    (_MIWAN, _S32b, "TRANSL", "zho", "PF", "受焦", _S32b+"_W17M2"),
    # S_32 W17 W-level: carry the source segmentation (kesa-un) so the
    # M count matches the form (corpus convention; V061)
    (_MIWAN, _S32b, "FORM", None, "kesun", "kesa-un", _S32b+"_W17"),
    (_MIWAN, _S32b, "PHON", None, "kesun", "kesa-un", _S32b+"_W17"),
    # S_32 W17M1 PHON: this file's PHON predates the current mapping
    # (stores 'kesun', today's mapping gives kəsun), so the witness
    # correctly refused regeneration; set the vintage-style value.
    (_MIWAN, _S32b, "PHON", None, "kesun", "kesa", _S32b+"_W17M1"),
    # S_32 W18: M1 stale eng; M2 is a junk shell (deleted below)
    (_MIWAN, _S32b, "TRANSL", "eng", "kesa", "elderly", _S32b+"_W18M1"),
])
# (relative file, S id, W id to delete) — impostor words with no source word
DELETE_W = [
    ("Stories/Tsou/Tsou_TsouConv-informants.xml", "TsouConv-informants_S_19",
     "TsouConv-informants_S_19_W6"),
    # junk M shell left by the diagonally-slid grid (rudan is monomorphemic)
    ("Stories/Seediq/Seediq_sdqNr-mother_iwan 2020s.xml",
     "sdqNr-mother_iwan 2020s_S_32", "sdqNr-mother_iwan 2020s_S_32_W18M2"),
]

GLOSS_SHIFT_NOTES = [
    ("Stories/Kanakanavu/Kanakanavu_kkvNr_fishing_Pani.xml", "kkvNr_fishing_Pani_S_34",
     "gloss-table column shift repaired from source; stray glosses belonged to untranscribed words; consult the NTU Formosan Corpus source"),
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
                    print(f"  no match for fill: {rel} {eid}")
                    stale += 1
                    continue
                if tag == "TRANSL":
                    tel = next((t for t in parent.findall("TRANSL")
                                if (t.get(_XLANG) or t.get("lang")) == kol), None)
                    if tel is None:
                        tel = etree.SubElement(parent, "TRANSL")
                        tel.set(_XLANG, kol)
                    if (tel.text or "").strip():
                        print(f"  fill skipped (already non-empty): {rel} {eid} {tag}/{kol}")
                        stale += 1
                        continue
                    tel.text = text
                else:
                    el2 = _tier(parent, tag, kol)
                    if el2 is None or (el2.text or "").strip():
                        print(f"  fill skipped (missing tier or non-empty): {rel} {eid} {tag}/{kol}")
                        stale += 1
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
                    print(f"  no match for delete-W (already applied?): {rel} {wid}")
                    stale += 1
                else:
                    target.getparent().remove(target)
                    applied += 1
                    modified = True
                    print(f"  deleted impostor W: {rel} {wid}")
                continue
            _, sid, tag, lang, old, new, elem_id = entry
            s = sindex.get(sid)
            matches = []
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
