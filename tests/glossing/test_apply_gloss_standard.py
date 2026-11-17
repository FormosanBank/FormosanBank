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
    # unsegmented word: the word's own shape satisfies an affix pattern
    assert g["w5"][("standard",)] == "OV.give"


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


# ---- LGR Rule 7 parens + notes-attribute parens (maintainer 2026-11-15:
# "these should remain Rule 7. But that also means our gloss standardizer
# needs to handle such cases appropriately."; card P3 "drop") ----

PAREN_RULES = RULES + [
    (r"\((?:AF|AV|UV|HORT)\)", "KEEP-PARENS",
     "LGR Rule 7 inherent-category tag: keep parens, convert inside, strip preceding space"),
    (r"\(ritual\)", "NOTE-PARENS",
     "clarifier moves to the standard TRANSL's notes attribute"),
]
PAREN_XML = """<TEXT xml:lang="tay" id="t5">
<S id="s1">
  <FORM kindOf="original">x</FORM>
  <W id="w1"><FORM>a</FORM>
    <TRANSL xml:lang="eng" kindOf="original">go (AF)</TRANSL>
  </W>
  <W id="w2"><FORM>b</FORM>
    <TRANSL xml:lang="eng" kindOf="original">LF-ring(AF)</TRANSL>
  </W>
  <W id="w3"><FORM>c</FORM>
    <TRANSL xml:lang="eng" kindOf="original">one(person)</TRANSL>
  </W>
  <W id="w4"><FORM>d</FORM>
    <TRANSL xml:lang="eng" kindOf="original">sikaisiisi (ritual)</TRANSL>
  </W>
</S>
</TEXT>"""


def make_paren_corpus(tmp_path):
    d = tmp_path / "XML"
    d.mkdir(parents=True, exist_ok=True)
    (d / "a.xml").write_text(PAREN_XML, encoding="utf-8")
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
        w.writerows(PAREN_RULES)
    return d, t, r


def test_keep_parens_rule7_kept_converted_space_stripped(tmp_path):
    d, t, r = make_paren_corpus(tmp_path)
    p = run(d, t, r)
    assert p.returncode == 0, p.stderr
    _, g = glosses(d)
    assert g["w1"][("standard",)] == "go(AV)"       # space stripped, AF->AV inside
    assert g["w2"][("standard",)] == "LV-ring(AV)"  # outside and inside both convert
    assert g["w1"][("original",)] == "go (AF)"      # original untouched


def test_unmatched_parens_still_residue(tmp_path):
    d, t, r = make_paren_corpus(tmp_path)
    p = run(d, t, r)
    _, g = glosses(d)
    assert g["w3"][("standard",)] == "one(person)"  # verbatim, still flagged
    assert "one(person)" in p.stdout


def test_note_parens_moved_to_notes_attribute(tmp_path):
    d, t, r = make_paren_corpus(tmp_path)
    run(d, t, r)
    root = ET.parse(d / "XML" / "a.xml" if (d / "XML").exists() else d / "a.xml").getroot()
    w4 = [w for w in root.iter("W") if w.get("id") == "w4"][0]
    std = [tr for tr in w4.findall("TRANSL") if tr.get("kindOf") == "standard"]
    assert len(std) == 1
    assert std[0].text == "sikaisiisi"
    assert std[0].get("notes") == "(ritual)"


# ---- context-rule fallback falls through to the table (maintainer card Q5
# 2026-11-15, choice "yes": the 'arup exception needs REC&'arup-, and atoms
# with context rules in OTHER words must still convert by the table) ----

FALLBACK_RULES = RULES + [
    ("AF&zz-", "CONTEXT-CONVERT→XX", "AF on a zz- word becomes XX"),
]
FALLBACK_XML = """<TEXT xml:lang="tay" id="t6">
<S id="s1">
  <FORM kindOf="original">x</FORM>
  <W id="w1"><FORM>zzat</FORM>
    <M id="m1"><FORM>zz-</FORM><TRANSL xml:lang="eng" kindOf="original">AF</TRANSL></M>
    <M id="m2"><FORM>at</FORM><TRANSL xml:lang="eng" kindOf="original">eat</TRANSL></M>
  </W>
  <W id="w2"><FORM>kmen</FORM>
    <M id="m3"><FORM>kmen</FORM><TRANSL xml:lang="eng" kindOf="original">AF-eat</TRANSL></M>
  </W>
</S>
</TEXT>"""


def test_context_fallback_goes_to_table(tmp_path):
    d = tmp_path / "XML"
    d.mkdir(parents=True, exist_ok=True)
    (d / "a.xml").write_text(FALLBACK_XML, encoding="utf-8")
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
        w.writerows(FALLBACK_RULES)
    p = run(d, t, r)
    assert p.returncode == 0, p.stderr
    _, g = glosses(d)
    assert g["m1"][("standard",)] == "XX"       # context rule fires on the zz- word
    assert g["m3"][("standard",)] == "AF-eat"[:0] + "AV-eat"  # no zz-: falls through to the table (AF->AV), not kept


# ---- +bound context pattern (maintainer q_cmpr 2026-11-16: "convert only
# more/tja- -> CMPR, and only when tja is bound (not when free-standing)") ----

BOUND_RULES = RULES + [
    ("AF&+bound", "CONTEXT-CONVERT→BB", "AF only in multi-morpheme words"),
]
BOUND_XML = """<TEXT xml:lang="tay" id="t7">
<S id="s1">
  <FORM kindOf="original">x</FORM>
  <W id="w1"><FORM>tja-vulung</FORM>
    <M id="m1"><FORM>tja</FORM><TRANSL xml:lang="eng" kindOf="original">AF</TRANSL></M>
    <M id="m2"><FORM>vulung</FORM><TRANSL xml:lang="eng" kindOf="original">old</TRANSL></M>
  </W>
  <W id="w2"><FORM>tja</FORM>
    <M id="m3"><FORM>tja</FORM><TRANSL xml:lang="eng" kindOf="original">AF</TRANSL></M>
  </W>
</S>
</TEXT>"""


def test_bound_context_pattern(tmp_path):
    d = tmp_path / "XML"
    d.mkdir(parents=True, exist_ok=True)
    (d / "a.xml").write_text(BOUND_XML, encoding="utf-8")
    t = tmp_path / "table.tsv"
    with open(t, "w", newline="") as h:
        w = csv.writer(h, delimiter="\t", lineterminator="\n")
        w.writerow(["source_code", "count", "status", "standard", "basis",
                    "notes", "language_overrides"])
        w.writerows([("NOM", "80", "KEEP", "NOM", "Leipzig", "", "")])
    r = tmp_path / "rules.tsv"
    with open(r, "w", newline="") as h:
        w = csv.writer(h, delimiter="\t", lineterminator="\n")
        w.writerow(["pattern", "replacement", "description"])
        w.writerows(BOUND_RULES)
    p = run(d, t, r)
    assert p.returncode == 0, p.stderr
    _, g = glosses(d)
    assert g["m1"][("standard",)] == "BB"   # bound: rule fires
    assert g["m3"][("standard",)] == "AF"   # free-standing: falls to table, kept


# ---- language-scoped context rules (maintainer, case page Bunun note
# 2026-11-17: "We need to fix the zho side specifically for those items.
# This probably requires some new functionality." — 處格 on Bunun -an words
# must become LV while Kavalan's genuine locative marker an stays LOC) ----

SCOPED_RULES = RULES + [
    ("AF@Kavalan&-an", "CONTEXT-CONVERT→KK", "AF on -an words, Kavalan only"),
]
SCOPED_XML = """<TEXT xml:lang="{lang}" id="t8">
<S id="s1">
  <FORM kindOf="original">x</FORM>
  <W id="w1"><FORM>tayan</FORM>
    <M id="m1"><FORM>tay</FORM><TRANSL xml:lang="eng" kindOf="original">see</TRANSL></M>
    <M id="m2"><FORM>-an</FORM><TRANSL xml:lang="eng" kindOf="original">AF</TRANSL></M>
  </W>
</S>
</TEXT>"""


def _scoped(tmp_path, lang):
    d = tmp_path / "XML"
    d.mkdir(parents=True, exist_ok=True)
    (d / "a.xml").write_text(SCOPED_XML.format(lang=lang), encoding="utf-8")
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
        w.writerows(SCOPED_RULES)
    p = run(d, t, r)
    assert p.returncode == 0, p.stderr
    return glosses(d)[1]


def test_language_scoped_context_rule(tmp_path):
    g = _scoped(tmp_path, "ckv")               # Kavalan: rule fires
    assert g["m2"][("standard",)] == "KK"
    g = _scoped(tmp_path / "b", "tay")         # Atayal: rule skipped, table applies
    assert g["m2"][("standard",)] == "AV"


# ---- positional context patterns: "-an" must mean a NON-INITIAL morpheme,
# "an-" an INITIAL one (Bunun an-sain-un false positive, 2026-11-17: the
# prefix an- must not satisfy the suffix pattern -an) ----

POS_XML = """<TEXT xml:lang="tay" id="t9">
<S id="s1">
  <FORM kindOf="original">x</FORM>
  <W id="w1"><FORM>an-sain</FORM>
    <M id="m1"><FORM>an</FORM><TRANSL xml:lang="eng" kindOf="original">carry</TRANSL></M>
    <M id="m2"><FORM>sain</FORM><TRANSL xml:lang="eng" kindOf="original">AF</TRANSL></M>
  </W>
  <W id="w2"><FORM>tay-an</FORM>
    <M id="m3"><FORM>tay</FORM><TRANSL xml:lang="eng" kindOf="original">see</TRANSL></M>
    <M id="m4"><FORM>an</FORM><TRANSL xml:lang="eng" kindOf="original">AF</TRANSL></M>
  </W>
</S>
</TEXT>"""


def test_suffix_pattern_requires_non_initial_morpheme(tmp_path):
    d = tmp_path / "XML"
    d.mkdir(parents=True, exist_ok=True)
    (d / "a.xml").write_text(POS_XML, encoding="utf-8")
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
        w.writerows(RULES + [("AF&an$", "CONTEXT-CONVERT→SS", "AF on words whose an is non-initial")])
    p = run(d, t, r)
    assert p.returncode == 0, p.stderr
    _, g = glosses(d)
    assert g["m2"][("standard",)] == "AV"   # word's an is INITIAL (prefix): rule must NOT fire; table applies
    assert g["m4"][("standard",)] == "SS"   # word's an is non-initial (suffix): rule fires


# ---- EMBEDDED-CODE: a fullwidth-paren code attached to a lexical gloss is
# rewritten period-joined (LGR Rule 4), the inner atom converted by the table
# (maintainer 2026-11-17, Chang 他（屬格）: "We will need our standardization
# to convert to use period notation (他.GEN) during standardization, but
# leaving the original tier alone.") ----

EMB_TABLE = TABLE + [
    ("屬格", "9", "CONVERT", "GEN", "ruling", "", ""),
]
EMB_RULES = RULES + [
    ("（([^（）]+)）", "EMBEDDED-CODE",
     "fullwidth parens attach a code — rewrite period-joined, look up inner"),
]
EMB_XML = """<TEXT xml:lang="trv" id="t9">
<S id="s1">
  <FORM kindOf="original">x</FORM>
  <W id="w1"><FORM>a</FORM>
    <TRANSL xml:lang="zho" kindOf="original">他（屬格）</TRANSL>
  </W>
  <W id="w2"><FORM>b</FORM>
    <TRANSL xml:lang="zho" kindOf="original">LF-吃-他（屬格）</TRANSL>
  </W>
  <W id="w3"><FORM>c</FORM>
    <TRANSL xml:lang="zho" kindOf="original">他（FIL）</TRANSL>
  </W>
</S>
</TEXT>"""


def make_embedded_corpus(tmp_path):
    d = tmp_path / "XML"
    d.mkdir(parents=True, exist_ok=True)
    (d / "a.xml").write_text(EMB_XML, encoding="utf-8")
    t = tmp_path / "table.tsv"
    with open(t, "w", newline="") as h:
        w = csv.writer(h, delimiter="\t", lineterminator="\n")
        w.writerow(["source_code", "count", "status", "standard", "basis",
                    "notes", "language_overrides"])
        w.writerows(EMB_TABLE)
    r = tmp_path / "rules.tsv"
    with open(r, "w", newline="") as h:
        w = csv.writer(h, delimiter="\t", lineterminator="\n")
        w.writerow(["pattern", "replacement", "description"])
        w.writerows(EMB_RULES)
    return d, t, r


def test_embedded_code_rewritten_period_joined(tmp_path):
    d, t, r = make_embedded_corpus(tmp_path)
    p = run(d, t, r)
    assert p.returncode == 0, p.stderr
    _, g = glosses(d)
    assert g["w1"][("standard",)] == "他.GEN"          # （屬格）→ .GEN
    assert g["w2"][("standard",)] == "LV-吃-他.GEN"    # composite: all atoms convert
    assert g["w1"][("original",)] == "他（屬格）"       # original untouched


def test_embedded_code_undecided_inner_copied_verbatim(tmp_path):
    d, t, r = make_embedded_corpus(tmp_path)
    run(d, t, r)
    _, g = glosses(d)
    # notation standardized even while the inner atom awaits a ruling;
    # the FIL row still reads UNDECIDED in the table (the to-do list)
    assert g["w3"][("standard",)] == "他.FIL"
