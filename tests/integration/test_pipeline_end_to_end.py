"""One corpus through the full pipeline in canonical order.

Order per QC/README.md: apply_manual_edits (no-op here, exercised in
tests/cleaners/test_manual_edits_survival.py) -> clean_xml -> standardize
-> add_phonology. Asserts the cross-stage invariants each stage's spec
*assumes* about its predecessor — exactly what per-module tests cannot
see:

  clean_xml -> standardize: null glyph is canonical ∅ (POL-012) and
      dashes are ASCII '-' (POL-011) BEFORE standardize looks for null
      units and hyphens; typographic apostrophes are ASCII (POL-010).
  standardize -> add_phonology: standard S-FORM has no null units;
      standard tier exists at S, W, and M; W/M null pairing survives
      (V069's precondition).
  add_phonology output: whole-null M FORM gets PHON '∅'; PHON is
      marker-free and punctuation-free (POL-003).
"""
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from tests._helpers import REPO_ROOT, run_qc_script

FIXTURES = REPO_ROOT / "tests" / "fixtures"


def _pipeline(tmp_path: Path) -> Path:
    corpus_root = tmp_path / "corpus"
    (corpus_root / "XML").mkdir(parents=True)
    shutil.copy(FIXTURES / "pipeline_e2e_source.xml",
                corpus_root / "XML" / "pipeline_e2e_source.xml")
    for script, args in [
        ("QC/cleaning/clean_xml.py",
         ["--corpora_path", str(corpus_root)]),
        ("QC/utilities/standardize.py",
         ["--tsv_path", str(FIXTURES / "rerun_l_to_ll_table.tsv"),
          "--corpora_path", str(corpus_root)]),
        ("QC/utilities/add_phonology.py",
         ["--corpora_path", str(corpus_root)]),
    ]:
        proc = run_qc_script(script, args)
        assert proc.returncode == 0, f"{script}: {proc.stderr}"
    return corpus_root / "XML" / "pipeline_e2e_source.xml"


def test_full_pipeline_invariants(tmp_path):
    out = _pipeline(tmp_path)
    text = out.read_text(encoding="utf-8")
    root = ET.parse(out).getroot()

    # clean_xml handoffs (original tier)
    s_orig = root.find(".//S/FORM[@kindOf='original']").text
    assert "ø" not in s_orig and "∅" in s_orig      # POL-012 canonical glyph
    assert "—" not in s_orig and "-" in s_orig      # POL-011 dash -> ASCII
    assert "’" not in text                          # POL-010 apostrophe
    assert "!!" not in s_orig                       # repeated punct trimmed

    # standardize handoffs
    s_std = root.find(".//S/FORM[@kindOf='standard']").text
    assert "∅" not in s_std                         # null units removed at S
    assert "á" not in s_std                         # accents stripped
    assert "llima" in s_std                         # table applied
    for tier in (".//W", ".//M"):
        for el in root.findall(tier):
            assert el.find("FORM[@kindOf='standard']") is not None

    # W/M null propagation survives standardize (V069's precondition)
    w_std = root.find(".//W/FORM[@kindOf='standard']").text
    m1_std = root.find(".//M/FORM[@kindOf='standard']").text
    assert "∅" in w_std and m1_std == "∅"

    # add_phonology handoffs
    m1_phon = root.find(".//M/PHON[@kindOf='standard']").text
    assert m1_phon == "∅"                           # whole-null FORM -> PHON ∅
    s_phon = root.find(".//S/PHON[@kindOf='standard']").text
    assert s_phon is not None
    for banned in ("-", "=", "<", ">", "!", "∅"):
        assert banned not in s_phon                 # marker-free, null silent
