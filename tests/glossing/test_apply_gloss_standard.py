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
