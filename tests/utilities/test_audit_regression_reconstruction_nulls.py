"""Audit regression: SEALS33 reconstruction labels survive standardization.

Finding (PR #165 audit, 2026-09-09): `standardize.py --remove_accents` read
the `∅` of a Neogrammarian reconstruction label (`*-∅`) as a null morpheme
and removed it, so the published standard tier of both SEALS33 files carried
`… *-h, ma *` — a bare asterisk naming nothing. Fixture:
tests/fixtures/audit_regressions/2026-09-seals33-reconstruction-null-in-standard.xml
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = (
    REPO_ROOT / "tests" / "fixtures" / "audit_regressions"
    / "2026-09-seals33-reconstruction-null-in-standard.xml"
)
STANDARDIZE = REPO_ROOT / "QC" / "utilities" / "standardize.py"


def test_reconstruction_label_survives_but_real_null_unit_does_not(tmp_path):
    corpus = tmp_path / "XML"
    corpus.mkdir()
    work = corpus / FIXTURE.name
    shutil.copy(FIXTURE, work)

    proc = subprocess.run(
        [sys.executable, str(STANDARDIZE), "--remove_accents",
         "--corpora_path", str(corpus)],
        capture_output=True, text=True, cwd=tmp_path,
    )
    assert proc.returncode == 0, proc.stderr

    root = ET.parse(work).getroot()
    standard = {
        s.get("id"): s.findtext("FORM[@kindOf='standard']")
        for s in root.findall("S")
    }
    # The three reconstruction labels are intact, hyphens included.
    assert standard["1"] == (
        "Bnrahan smalu ka hengak laqi tgbukuy *-ʔ, *-h, ma *-∅ Proto-Austronesian"
    )
    # A genuine null unit is still removed, with its bridging hyphen.
    assert standard["2"] == "sitangah kero misa"
    # The original tier is untouched either way.
    originals = [s.findtext("FORM[@kindOf='original']") for s in root.findall("S")]
    assert originals == [
        "Bnrahan smalu ka hengak laqi tgbukuy *-ʔ, *-h, ma *-∅ Proto-Austronesian",
        "∅-sitangah kero-∅ ∅ misa",
    ]
