"""apply_gloss_standard: writes TRANSL[@kindOf="standard"] beside original
glosses per a conversion table + rules file. POL-036: originals untouched."""
import subprocess, sys, csv
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "QC" / "glossing" / "apply_gloss_standard.py"

TABLE = [
    ("AF", "100", "CONVERT", "AV", "voice ruling", "", ""),
    ("LF", "50", "CONVERT", "LV", "voice ruling", "", "Kavalan→PV (ruling)"),
    ("NOM", "80", "KEEP", "NOM", "Leipzig", "", ""),
    ("FIL", "10", "UNDECIDED", "", "", "", ""),
]
RULES = [
    (r"\.", "KEEP-SEPARATOR", "period"),
    ("-", "KEEP-SEPARATOR", "hyphen"),
    ("=", "KEEP-SEPARATOR", "clitic"),
    ("<([^<>]+)>", "KEEP-BRACKETS", "infix"),
    (r"[()\[\]（）]", "INVESTIGATE", "parens flagged"),
]

XML = """<TEXT xml:lang="{lang}"{dialect} id="t1">
<S id="s1">
  <FORM kindOf="original">kmen nom-x</FORM>
  <TRANSL xml:lang="eng">He eats.</TRANSL>
  <W id="w1">
    <FORM kindOf="original">kmen</FORM>
    <TRANSL xml:lang="eng">eat-AF</TRANSL>
    <M id="m1"><FORM kindOf="original">kmen</FORM>
      <TRANSL xml:lang="eng" kindOf="original">&lt;AF&gt;eat</TRANSL></M>
  </W>
  <W id="w2">
    <FORM kindOf="original">nia</FORM>
    <TRANSL xml:lang="eng" kindOf="original">LF-NOM.FIL</TRANSL>
  </W>
  <W id="w3">
    <FORM kindOf="original">pa</FORM>
    <TRANSL xml:lang="eng" kindOf="original">1P(IN)</TRANSL>
  </W>
  <W id="w4">
    <FORM kindOf="original">zz</FORM>
    <TRANSL xml:lang="eng" kindOf="original">old-AF</TRANSL>
    <TRANSL xml:lang="eng" kindOf="standard">HAND.MADE</TRANSL>
  </W>
</S>
</TEXT>"""


def make_corpus(tmp_path, lang="tay", dialect=""):
    d = tmp_path / "XML"
    d.mkdir(parents=True, exist_ok=True)
    da = f' dialect="{dialect}"' if dialect else ""
    (d / "a.xml").write_text(XML.format(lang=lang, dialect=da), encoding="utf-8")
    t = tmp_path / "table.tsv"
    with open(t, "w", newline="") as h:
        w = csv.writer(h, delimiter="\t", lineterminator="\n")
        w.writerow(["source_code", "count", "status", "standard", "basis",
                    "notes", "language_overrides"])
        w.writerows(TABLE)
    r = tmp_path / "rules.tsv"
    with open(r, "w", newline="") as h:
        w = csv.writer(h, delimiter="\t", lineterminator="\n")
        w.writerow(["pattern", "replacement", "description"])
        w.writerows(RULES)
    return d, t, r


def run(d, t, r, write=True):
    cmd = [sys.executable, str(TOOL), "--path", str(d), "--table", str(t),
           "--rules", str(r)] + (["--write"] if write else [])
    return subprocess.run(cmd, capture_output=True, text=True)


def glosses(d):
    root = ET.parse(d / "a.xml").getroot()
    out = {}
    for w in root.iter("W"):
        out[w.get("id")] = {(tr.get("kindOf"), ): tr.text for tr in
                            w.findall("TRANSL")}
        for m in w.findall("M"):
            out[m.get("id")] = {(tr.get("kindOf"), ): tr.text for tr in
                                m.findall("TRANSL")}
    return root, out


def test_converts_and_adds_standard_tier(tmp_path):
    d, t, r = make_corpus(tmp_path)
    p = run(d, t, r)
    assert p.returncode == 0, p.stderr
    root, g = glosses(d)
    assert g["w1"][("original",)] == "eat-AF"          # original untouched
    assert g["w1"][("standard",)] == "eat-AV"          # converted
    assert g["m1"][("standard",)] == "<AV>eat"         # infix bracket kept


def test_undecided_copies_verbatim_and_keep_keeps(tmp_path):
    d, t, r = make_corpus(tmp_path)
    run(d, t, r)
    _, g = glosses(d)
    assert g["w2"][("standard",)] == "LV-NOM.FIL"      # LF→LV, NOM kept, FIL copied


def test_language_override(tmp_path):
    d, t, r = make_corpus(tmp_path, lang="ckv")        # Kavalan
    run(d, t, r)
    _, g = glosses(d)
    assert g["w2"][("standard",)] == "PV-NOM.FIL"      # LF→PV for Kavalan


def test_bare_original_gets_stamped(tmp_path):
    d, t, r = make_corpus(tmp_path)
    run(d, t, r)
    _, g = glosses(d)
    assert ("original",) in g["w1"]                    # was bare, now stamped


def test_residue_copied_verbatim_and_reported(tmp_path):
    d, t, r = make_corpus(tmp_path)
    p = run(d, t, r)
    _, g = glosses(d)
    assert g["w3"][("standard",)] == "1P(IN)"          # verbatim
    assert "residue" in p.stdout.lower()


def test_preexisting_standard_untouched(tmp_path):
    d, t, r = make_corpus(tmp_path)
    run(d, t, r)
    _, g = glosses(d)
    assert g["w4"][("standard",)] == "HAND.MADE"


def test_sentence_transl_untouched(tmp_path):
    d, t, r = make_corpus(tmp_path)
    run(d, t, r)
    root, _ = glosses(d)
    s = root.find("S")
    stl = [tr for tr in s.findall("TRANSL")]
    assert len(stl) == 1 and stl[0].get("kindOf") is None


def test_dry_run_changes_nothing(tmp_path):
    d, t, r = make_corpus(tmp_path)
    before = (d / "a.xml").read_text(encoding="utf-8")
    p = run(d, t, r, write=False)
    assert p.returncode == 0
    assert (d / "a.xml").read_text(encoding="utf-8") == before


# ---- context rules (r2 Yedda UV split; maintainer 2026-11-12: "Conversion
# tool is going to need to implement context rules.") ----

CTX_TABLE = [
    ("UV", "82", "CONVERT", "", "r2: split by diagnostic affix", "", ""),
    ("AF", "10", "CONVERT", "AV", "voice ruling", "", ""),
]
CTX_RULES = RULES + [
    ("UV&-an", "CONTEXT-CONVERT→LV", "UV word whose morphemes include -an"),
    ("UV&si-", "CONTEXT-CONVERT→OV", "UV word with si-"),
    ("UV&-en", "CONTEXT-CONVERT→PV", "UV word with -en"),
    ("UV&⟨in⟩-only", "KEEP-UV", "no diagnostic affix: stays UV"),
]
CTX_XML = """<TEXT xml:lang="pwn" id="t2">
<S id="s1">
  <FORM kindOf="original">x</FORM>
  <W id="w1"><FORM>tjaljan</FORM>
    <TRANSL xml:lang="eng" kindOf="original">plant-UV</TRANSL>
    <M id="m11"><FORM>tjalj</FORM><TRANSL xml:lang="eng" kindOf="original">plant</TRANSL></M>
    <M id="m12"><FORM>-an</FORM><TRANSL xml:lang="eng" kindOf="original">UV</TRANSL></M>
  </W>
  <W id="w2"><FORM>sikan</FORM>
    <TRANSL xml:lang="eng" kindOf="original">UV-eat</TRANSL>
    <M id="m21"><FORM>si-</FORM><TRANSL xml:lang="eng" kindOf="original">UV</TRANSL></M>
    <M id="m22"><FORM>kan</FORM><TRANSL xml:lang="eng" kindOf="original">eat</TRANSL></M>
  </W>
  <W id="w3"><FORM>kanen</FORM>
    <TRANSL xml:lang="eng" kindOf="original">eat-UV</TRANSL>
    <M id="m31"><FORM>kan</FORM><TRANSL xml:lang="eng" kindOf="original">eat</TRANSL></M>
    <M id="m32"><FORM>-en</FORM><TRANSL xml:lang="eng" kindOf="original">UV</TRANSL></M>
  </W>
  <W id="w4"><FORM>kinum</FORM>
    <TRANSL xml:lang="eng" kindOf="original">eat&lt;UV&gt;</TRANSL>
    <M id="m41"><FORM>kinum</FORM><TRANSL xml:lang="eng" kindOf="original">eat.UV</TRANSL></M>
  </W>
  <W id="w5"><FORM>sibuy</FORM>
    <TRANSL xml:lang="eng" kindOf="original">UV.give</TRANSL>
  </W>
</S>
</TEXT>"""


def make_ctx_corpus(tmp_path):
    d = tmp_path / "XML"
    d.mkdir(parents=True, exist_ok=True)
    (d / "a.xml").write_text(CTX_XML, encoding="utf-8")
    t = tmp_path / "table.tsv"
    with open(t, "w", newline="") as h:
        w = csv.writer(h, delimiter="\t", lineterminator="\n")
        w.writerow(["source_code", "count", "status", "standard", "basis",
                    "notes", "language_overrides"])
        w.writerows(CTX_TABLE)
    r = tmp_path / "rules.tsv"
    with open(r, "w", newline="") as h:
        w = csv.writer(h, delimiter="\t", lineterminator="\n")
        w.writerow(["pattern", "replacement", "description"])
        w.writerows(CTX_RULES)
    return d, t, r


def test_context_rules_split_by_word_morphology(tmp_path):
    d, t, r = make_ctx_corpus(tmp_path)
    p = run(d, t, r)
    assert p.returncode == 0, p.stderr
    _, g = glosses(d)
    assert g["w1"][("standard",)] == "plant-LV"   # word has -an
    assert g["w2"][("standard",)] == "OV-eat"     # word has si-
    assert g["w3"][("standard",)] == "eat-PV"     # word has -en
    assert g["w4"][("standard",)] == "eat<UV>"    # no diagnostic affix: kept
    # M-level glosses inherit the WORD's morpheme context
    assert g["m12"][("standard",)] == "LV"
    assert g["m21"][("standard",)] == "OV"
    assert g["m41"][("standard",)] == "eat.UV"
    # unsegmented word: the word's own shape satisfies an affix pattern; voice fused with a lexical
    # gloss is written Leipzig Rule 7 (maintainer, 2026-11-15), so OV.give -> give(OV)
    assert g["w5"][("standard",)] == "give(OV)"


# ---- POL-021 UNCLEAR children: mixed-content glosses must convert without
# losing the element or any text segment ----

UNCLEAR_XML = """<TEXT xml:lang="tay" id="t3">
<S id="s1">
  <FORM kindOf="original">x</FORM>
  <W id="w1"><FORM>abc</FORM>
    <TRANSL xml:lang="eng" kindOf="original"><UNCLEAR />-eat-AF</TRANSL>
  </W>
  <W id="w2"><FORM>def</FORM>
    <TRANSL xml:lang="eng" kindOf="original">LF-<UNCLEAR />=go-AF</TRANSL>
  </W>
  <W id="w3"><FORM>ghi</FORM>
    <TRANSL xml:lang="eng" kindOf="original"><UNCLEAR /></TRANSL>
  </W>
</S>
</TEXT>"""


def test_unclear_children_preserved_and_segments_converted(tmp_path):
    d = tmp_path / "XML"
    d.mkdir(parents=True, exist_ok=True)
    (d / "a.xml").write_text(UNCLEAR_XML, encoding="utf-8")
    t = tmp_path / "table.tsv"
    with open(t, "w", newline="") as h:
        w = csv.writer(h, delimiter="\t", lineterminator="\n")
        w.writerow(["source_code", "count", "status", "standard", "basis",
                    "notes", "language_overrides"])
        w.writerows(TABLE)
    r = tmp_path / "rules.tsv"
    with open(r, "w", newline="") as h:
        w = csv.writer(h, delimiter="\t", lineterminator="\n")
        w.writerow(["pattern", "replacement", "description"])
        w.writerows(RULES)
    p = run(d, t, r)
    assert p.returncode == 0, p.stderr
    root = ET.parse(d / "a.xml").getroot()
    std = {}
    for w in root.iter("W"):
        for tr in w.findall("TRANSL"):
            if tr.get("kindOf") == "standard":
                std[w.get("id")] = ET.tostring(tr, encoding="unicode")
    # leading UNCLEAR kept, following atoms converted
    assert "<UNCLEAR />-eat-AV" in std["w1"].replace("<UNCLEAR/>", "<UNCLEAR />")
    # interior UNCLEAR kept, atoms on BOTH sides converted (LF→LV before it)
    assert "LV-" in std["w2"] and "=go-AV" in std["w2"] and "UNCLEAR" in std["w2"]
    # pure-UNCLEAR gloss: no standard tier is added (nothing to convert)
    assert "w3" not in std


def test_variant_ver_transl_standardized_with_ver(tmp_path):
    """A TRANSL with ver= is a variant reading: it gets no kindOf stamp (V022
    forbids two same-lang originals), but it IS standardized — its standard
    TRANSL carries the same ver value (V085 discriminates same-lang standards
    by ver). Multiple gloss languages coexist; dedup is per (lang, ver)."""
    xml = """<TEXT xml:lang="tay" id="t4">
<S id="s1"><FORM kindOf="original">x</FORM>
  <W id="w1"><FORM>abc</FORM>
    <M id="m1"><FORM>s</FORM>
      <TRANSL xml:lang="eng">AF</TRANSL>
      <TRANSL xml:lang="eng" ver="alt" notes="source reading">LF-AF</TRANSL>
      <TRANSL xml:lang="zho">主事焦點</TRANSL>
    </M>
  </W>
</S></TEXT>"""
    d = tmp_path / "XML"; d.mkdir(parents=True)
    (d / "a.xml").write_text(xml, encoding="utf-8")
    t = tmp_path / "table.tsv"
    with open(t, "w", newline="") as h:
        w = csv.writer(h, delimiter="\t", lineterminator="\n")
        w.writerow(["source_code", "count", "status", "standard", "basis",
                    "notes", "language_overrides"])
        w.writerows(TABLE)
    r = tmp_path / "rules.tsv"
    with open(r, "w", newline="") as h:
        w = csv.writer(h, delimiter="\t", lineterminator="\n")
        w.writerow(["pattern", "replacement", "description"])
        w.writerows(RULES)
    p = run(d, t, r)
    assert p.returncode == 0, p.stderr
    root = ET.parse(d / "a.xml").getroot()
    m = root.find(".//M")
    trs = m.findall("TRANSL")
    # The variant original keeps its ver, stays unstamped, text unchanged
    variant_originals = [tr for tr in trs
                         if tr.get("ver") and tr.get("kindOf") != "standard"]
    assert len(variant_originals) == 1
    assert variant_originals[0].get("kindOf") is None
    assert variant_originals[0].text == "LF-AF"
    originals = [tr for tr in trs if tr.get("kindOf") == "original"]
    assert len(originals) == 2   # eng AF + zho, both stamped
    # Every gloss, variant included, gets a standard carrying its ver
    standards = {(tr.get("{http://www.w3.org/XML/1998/namespace}lang"),
                  tr.get("ver")): tr.text
                 for tr in trs if tr.get("kindOf") == "standard"}
    assert standards == {("eng", None): "AV",
                         ("eng", "alt"): "LV-AV",
                         ("zho", None): "主事焦點"}
    # Idempotent: a second run adds nothing (dedup keyed on (lang, ver))
    p2 = run(d, t, r)
    assert p2.returncode == 0, p2.stderr
    root2 = ET.parse(d / "a.xml").getroot()
    assert len(root2.find(".//M").findall("TRANSL")) == len(trs)


# ---------------------------------------------------------------------------
# Leipzig Rule 7 for voice, RULE7-PARENS, CONTEXT-ADD, --redo-changed (maintainer, 2026-11-15, unvoiced-verbs
# audit: Rule 7 "see(AV)"; "All 12,001 with a lexical gloss; the 3,684 on affixes/auxiliaries stay as they are";
# tests 2026-11-16: "Yes, add them to the same PR"). Gloss shapes are real published ones.
# ---------------------------------------------------------------------------

R7_TABLE = [
    ("AF", "100", "CONVERT", "AV", "voice ruling", "", ""),
    ("PF", "100", "CONVERT", "PV", "voice ruling", "", ""),
    ("AUX", "10", "KEEP", "AUX", "Leipzig", "", ""),
]
R7_RULES = [
    (r"\.", "KEEP-SEPARATOR", "period"),
    ("-", "KEEP-SEPARATOR", "hyphen"),
    ("=", "KEEP-SEPARATOR", "clitic"),
    ("x(CODE)", "RULE7-PARENS", "Rule 7 parentheses"),
    (r"[()\[\]（）]", "INVESTIGATE", "other parentheses are residue"),
    ("say&=aya", "CONTEXT-ADD→AV", "bare aya 'say' is AV"),
]


def _w(wid, form, *glosses, standard=None):
    ms = "".join(f'<M id="{wid}m{i}"><FORM kindOf="original">{form}</FORM>'
                 f'<TRANSL xml:lang="eng" kindOf="original">{g}</TRANSL>'
                 + (f'<TRANSL xml:lang="eng" kindOf="standard">{standard}</TRANSL>' if standard else "")
                 + "</M>" for i, g in enumerate(glosses, 1))
    return f'<W id="{wid}"><FORM kindOf="original">{form}</FORM>{ms}</W>'


def make_r7_corpus(tmp_path, words):
    d = tmp_path / "XML"
    d.mkdir(parents=True, exist_ok=True)
    (d / "a.xml").write_text(
        '<TEXT xml:lang="pwn" id="t1"><S id="s1"><FORM kindOf="original">x</FORM>'
        + "".join(words) + "</S></TEXT>", encoding="utf-8")
    t, r = tmp_path / "table.tsv", tmp_path / "rules.tsv"
    for path, head, rows in ((t, ["source_code", "count", "status", "standard", "basis", "notes",
                                  "language_overrides"], R7_TABLE),
                             (r, ["pattern", "replacement", "description"], R7_RULES)):
        with open(path, "w", newline="", encoding="utf-8") as h:
            w = csv.writer(h, delimiter="\t", lineterminator="\n")
            w.writerow(head)
            w.writerows(rows)
    return d, t, r


def m_standards(d):
    root = ET.parse(d / "a.xml").getroot()
    return {m.get("id"): [tr.text for tr in m.findall("TRANSL") if tr.get("kindOf") == "standard"]
            for m in root.iter("M")}


def test_rule7_voice_fused_with_a_lexical_gloss_moves_into_parentheses(tmp_path):
    d, t, r = make_r7_corpus(tmp_path, [
        _w("w1", "kmen", "AF.eat"),        # Rule 4 voice + lexical gloss -> Rule 7
        _w("w2", "na", "AUX.AF"),          # voice on an auxiliary: no lexical piece, stays Rule 4
        _w("w3", "ki", "PF.FUT.go"),       # other codes stay in the group
    ])
    p = run(d, t, r)
    assert p.returncode == 0, p.stderr
    assert m_standards(d) == {"w1m1": ["eat(AV)"], "w2m1": ["AUX.AV"], "w3m1": ["FUT.go(PV)"]}


def test_rule7_parens_converts_code_parens_and_leaves_others_as_residue(tmp_path):
    d, t, r = make_r7_corpus(tmp_path, [
        _w("w1", "matsai", "die(AF)"),     # codes only in the parentheses: converted, kept as Rule 7
        _w("w2", "kui", "(name)"),         # anything else in parentheses: residue, copied verbatim
    ])
    p = run(d, t, r)
    assert p.returncode == 0, p.stderr
    assert m_standards(d) == {"w1m1": ["die(AV)"], "w2m1": ["(name)"]}
    assert "residue" in p.stdout and "'(name)'" in p.stdout


def test_context_add_gives_voice_only_to_the_bare_word(tmp_path):
    d, t, r = make_r7_corpus(tmp_path, [
        _w("w1", "aya", "say"),            # bare aya: gets AV
        _w("w2", "aya", "say", "AF"),      # already voiced: untouched
        _w("w3", "vaik", "say"),           # same gloss, other stem: untouched
    ])
    p = run(d, t, r)
    assert p.returncode == 0, p.stderr
    assert m_standards(d) == {"w1m1": ["say(AV)"], "w2m1": ["say"], "w2m2": ["AV"], "w3m1": ["say"]}
    root = ET.parse(d / "a.xml").getroot()
    originals = [tr.text for tr in root.iter("TRANSL") if tr.get("kindOf") == "original"]
    assert originals == ["say", "say", "AF", "say"]          # POL-036: originals untouched


def test_redo_changed_replaces_tool_made_and_keeps_hand_made_standards(tmp_path):
    d, t, r = make_r7_corpus(tmp_path, [
        _w("w1", "kmen", "AF.eat", standard="AV.eat"),     # what the tool made before Rule 7: re-derived
        _w("w2", "kmen", "AF.eat", standard="AV.eat.it"),  # not the tool's output (hand-made): kept
        _w("w3", "aya", "say", standard="say"),            # tool-made, and a CONTEXT-ADD word: re-derived
    ])
    p = run(d, t, r)                                         # without the flag: existing standards kept
    assert p.returncode == 0, p.stderr
    assert m_standards(d) == {"w1m1": ["AV.eat"], "w2m1": ["AV.eat.it"], "w3m1": ["say"]}
    p = subprocess.run([sys.executable, str(TOOL), "--path", str(d), "--table", str(t), "--rules", str(r),
                        "--redo-changed", "--write"], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    assert m_standards(d) == {"w1m1": ["eat(AV)"], "w2m1": ["AV.eat.it"], "w3m1": ["say(AV)"]}
    assert "redone=2" in p.stdout and "handmade_standard_kept=1" in p.stdout


def test_whole_gloss_rule_converts_only_an_exact_whole_gloss(tmp_path):
    # maintainer 2026-11-16 (unvoiced-verbs audit, whole_gloss_rule_r8): "Yes" to a rule that replaces one exact
    # whole gloss. Shapes are real: HPS "(name)", "(name)-(name)"; Yedda "ligature (LIG)".
    d, t, r = make_r7_corpus(tmp_path, [
        _w("w1", "Tjukutjuku", "(name)"),                 # exact match: -> PN
        _w("w2", "Kuɫe-Pulelelelengan", "(name)-(name)"),  # not the whole gloss: residue, copied as is
        _w("w3", "a", "ligature (LIG)"),                  # exact match, with a space inside: -> LNK
        _w("w4", "a", "ligature (LIG)?"),                 # one character more: residue, copied as is
        _w("w5", "kui", "(place)"),                       # no rule for it: residue, copied as is
    ])
    with open(r, "a", encoding="utf-8") as h:
        h.write("(name)\tWHOLE-GLOSS→PN\tHPS names\nligature (LIG)\tWHOLE-GLOSS→LNK\tYedda prose gloss\n")
    p = run(d, t, r)
    assert p.returncode == 0, p.stderr
    assert m_standards(d) == {"w1m1": ["PN"], "w2m1": ["(name)-(name)"], "w3m1": ["LNK"],
                              "w4m1": ["ligature (LIG)?"], "w5m1": ["(place)"]}
    root = ET.parse(d / "a.xml").getroot()
    assert [tr.text for tr in root.iter("TRANSL") if tr.get("kindOf") == "original"] == \
        ["(name)", "(name)-(name)", "ligature (LIG)", "ligature (LIG)?", "(place)"]   # POL-036: originals untouched
