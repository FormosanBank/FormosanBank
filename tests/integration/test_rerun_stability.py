"""clean_xml idempotence guard.

clean_xml's steady-state input is its own prior output (published
corpora are re-cleaned), so run2(run1(x)) == run1(x) is a hard
requirement. It holds empirically today (verified 2026-08-10 over all
dirty fixtures) but not by construction — every future cleaning rule
whose output falls inside another rule's input domain breaks it
silently. This test is the guard that rule runs into.

Maintainer ruling 2026-08-10: clean_xml only — standardize and
add_phonology are regenerators (they rebuild derived tiers from the
original tier on every run) and need no rerun test.

The assertion compares run 2 against run 1 — never run 1 against the
input, because a first run may legitimately reformat serialization.
"""
import shutil

from tests._helpers import REPO_ROOT, run_qc_script, snapshot_tree

FIXTURES = REPO_ROOT / "tests" / "fixtures"


def test_clean_xml_idempotent_over_all_fixtures(tmp_path):
    """XML is a fixed point after run 1; the whole tree after run 2.

    The warnings sidecar legitimately differs between run 1 and run 2:
    run 1 reports characters it then transformed (c002b stress marks
    etc.), run 2 reports only warn-only findings that survive cleaning.
    Per POL-033 each CSV correctly describes its own run. So the
    contract is: every XML byte-identical from run 1 on, and the entire
    tree (sidecar included) byte-identical from run 2 on.
    """
    corpus = tmp_path / "corpus" / "XML"
    corpus.mkdir(parents=True)
    for fixture in FIXTURES.glob("*.xml"):
        shutil.copy(fixture, corpus / fixture.name)
    argv = ["--corpora_path", str(tmp_path / "corpus")]

    for run in range(1, 4):
        proc = run_qc_script("QC/cleaning/clean_xml.py", argv)
        assert proc.returncode == 0, f"run {run}: {proc.stderr}"
        snap = snapshot_tree(tmp_path / "corpus")
        if run == 1:
            xml1 = {k: v for k, v in snap.items() if k.endswith(".xml")}
        elif run == 2:
            xml2 = {k: v for k, v in snap.items() if k.endswith(".xml")}
            changed = [k for k in xml1 if xml2.get(k) != xml1[k]]
            assert not changed, f"run 2 changed XML: {changed}"
            snap2 = snap
        else:
            changed = [k for k in snap2 if snap.get(k) != snap2[k]]
            changed += [k for k in snap if k not in snap2]
            assert not changed, f"run 3 changed tree: {changed}"
