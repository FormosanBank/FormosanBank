"""Manual-edits guarantees the per-script tests do not cover.

1. Survival: an applied hand edit is still present after clean_xml and
   standardize run (the pipeline order puts apply_manual_edits FIRST;
   nothing later may undo the edit), and the regenerated standard tier
   reflects it (POL-002: editing the original is the only durable way
   to change the standard).
2. Reapply semantics (ruling 2026-08-10): a second apply against XML
   that already contains the edit detects the record as a no-op, warns
   saliently, and KEEPS it — the record is still needed for the next
   fresh rebuild. Only `--prune` removes no-op records (an explicit
   maintenance action for when the upstream build absorbed the fix).
"""
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from tests._helpers import REPO_ROOT, run_qc_script

FIXTURES = REPO_ROOT / "tests" / "fixtures"


def _corpus_with_edit(tmp_path: Path) -> Path:
    """A corpus whose manual_edits.xml rewrites S2's original FORM."""
    corpus = tmp_path / "corpus"
    (corpus / "XML").mkdir(parents=True)
    (corpus / "CodeAndDocs").mkdir()
    shutil.copy(FIXTURES / "rerun_puyuma_l_to_ll.xml",
                corpus / "XML" / "rerun_puyuma_l_to_ll.xml")
    # Upsert record: same S id, corrected original text ("talal" ->
    # "talral"); standard/PHON stripped per the manual-edits contract.
    # FILE/@path is relative to the corpora_path (the XML root).
    (corpus / "CodeAndDocs" / "manual_edits.xml").write_text(
        """<?xml version="1.0" ?>
<MANUAL_EDITS>
    <FILE path="rerun_puyuma_l_to_ll.xml">
        <S id="S2">
            <FORM kindOf="original">talral na l</FORM>
            <TRANSL xml:lang="eng">plain sentence</TRANSL>
        </S>
    </FILE>
</MANUAL_EDITS>
""", encoding="utf-8")
    return corpus


def _s2_form(corpus: Path, kind: str) -> str:
    root = ET.parse(corpus / "XML" / "rerun_puyuma_l_to_ll.xml").getroot()
    for s in root.findall("S"):
        if s.get("id") == "S2":
            return s.find(f"FORM[@kindOf='{kind}']").text
    raise AssertionError("S2 missing")


def test_edit_survives_full_pipeline(tmp_path):
    corpus = _corpus_with_edit(tmp_path)
    for script, args in [
        # apply_manual_edits takes the XML root; the manual file resolves
        # to its ../CodeAndDocs/manual_edits.xml sibling.
        ("QC/cleaning/apply_manual_edits.py",
         ["--corpora_path", str(corpus / "XML")]),
        ("QC/cleaning/clean_xml.py", ["--corpora_path", str(corpus)]),
        ("QC/utilities/standardize.py",
         ["--tsv_path", str(FIXTURES / "rerun_l_to_ll_table.tsv"),
          "--corpora_path", str(corpus)]),
    ]:
        proc = run_qc_script(script, args)
        assert proc.returncode == 0, f"{script}: {proc.stderr}"
    assert _s2_form(corpus, "original") == "talral na l"
    assert "tallrall" in _s2_form(corpus, "standard"), (
        "standard tier must be regenerated FROM the edited original")


def test_reapply_keeps_record_and_leaves_xml_alone(tmp_path):
    """Ruling 2026-08-10: reapply is a warned no-op — XML stable, record
    kept; only --prune removes it."""
    corpus = _corpus_with_edit(tmp_path)
    script = "QC/cleaning/apply_manual_edits.py"
    argv = ["--corpora_path", str(corpus / "XML")]
    manual = corpus / "CodeAndDocs" / "manual_edits.xml"

    assert run_qc_script(script, argv).returncode == 0
    xml_after_first = (corpus / "XML" / "rerun_puyuma_l_to_ll.xml").read_bytes()
    assert "S2" in manual.read_text(encoding="utf-8")

    second = run_qc_script(script, argv)
    assert second.returncode == 0
    xml_after_second = (corpus / "XML" / "rerun_puyuma_l_to_ll.xml").read_bytes()
    assert xml_after_second == xml_after_first, "reapply must not change XML"
    out = (second.stdout + second.stderr).lower()
    assert "no-op" in out and "kept" in out
    assert "S2" in manual.read_text(encoding="utf-8"), (
        "record must survive reapply (needed for the next fresh rebuild)")

    pruned = run_qc_script(script, argv + ["--prune"])
    assert pruned.returncode == 0
    assert "S2" not in manual.read_text(encoding="utf-8"), (
        "--prune removes no-op records (explicit maintenance action)")
