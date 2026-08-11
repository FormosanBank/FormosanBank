"""standardize_warnings.csv contract: schema, content, no duplication.

The CSV is the operator's triage artifact for c012 (hyphen removed from a
morpheme-segmented standard FORM) and c022 ('*' in a morpheme-segmented
standard FORM); skills read it into run summaries, so its shape is a
contract. Task 1 of the 2026-08-10 test plan made it a per-run report
(POL-033); the last assertion pins that.
"""
import csv
from pathlib import Path

from tests._helpers import REPO_ROOT, run_qc_script

FIXTURES = REPO_ROOT / "tests" / "fixtures"
COLUMNS = ["rule_id", "file", "s_id", "character", "position",
           "form_before", "form_after"]


def _corpus(tmp_path: Path) -> Path:
    corpus = tmp_path / "corpus"
    (corpus / "XML").mkdir(parents=True)
    # Inject a '*' into S1 — the sentence WITH morpheme segmentation:
    # both c012 and c022 are gated on the S having M descendants.
    text = (FIXTURES / "rerun_puyuma_l_to_ll.xml").read_text(encoding="utf-8")
    text = text.replace("lima ∅-ku dálan", "lima ∅-ku *dálan")
    (corpus / "XML" / "warnings_probe.xml").write_text(text, encoding="utf-8")
    return corpus


def _rows(corpus: Path) -> list:
    with open(corpus / "standardize_warnings.csv", newline="",
              encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_schema_and_single_reporting(tmp_path):
    corpus = _corpus(tmp_path)
    args = ["--tsv_path", str(FIXTURES / "rerun_l_to_ll_table.tsv"),
            "--corpora_path", str(corpus)]
    assert run_qc_script("QC/utilities/standardize.py", args).returncode == 0
    rows = _rows(corpus)
    assert rows, "expected at least a c022 row for the injected '*'"
    assert list(rows[0].keys()) == COLUMNS
    c022 = [r for r in rows if r["rule_id"] == "c022"]
    assert c022, f"expected c022 rows; got {rows!r}"
    assert len(c022) == len({(r["s_id"], r["position"]) for r in c022}), (
        "same occurrence reported twice in one run")

    # POL-033 contract: a second run REPLACES the CSV, count unchanged.
    assert run_qc_script("QC/utilities/standardize.py", args).returncode == 0
    assert len(_rows(corpus)) == len(rows)
