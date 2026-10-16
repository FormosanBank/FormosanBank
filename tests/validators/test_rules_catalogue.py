"""QC/validation/RULES.md must match the rules that actually run.

A hand-maintained list of rule ids goes stale the first time someone adds a
rule and forgets it, which is the failure mode that made the list worth
having. This test is what keeps it honest: add a rule, regenerate.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "QC/validation/rules_catalogue.py"
CATALOGUE = REPO_ROOT / "QC/validation/RULES.md"

sys.path.insert(0, str(REPO_ROOT))


def test_catalogue_is_current():
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        f"{CATALOGUE.name} is stale — run "
        f"`python QC/validation/rules_catalogue.py`.\n"
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_every_rule_has_a_description():
    from QC.validation.rules_catalogue import collect

    missing = [r[0] for r in collect() if not r[5].strip(".")]
    assert not missing, f"rules with no docstring description: {missing}"


def test_catalogue_names_every_rule_that_runs():
    from QC.validation.rules_catalogue import collect

    text = CATALOGUE.read_text(encoding="utf-8")
    for rule_id, mnemonic, _sev, _scope, _v, _desc in collect():
        assert f"| {rule_id} | `{mnemonic}` |" in text, (
            f"{rule_id} `{mnemonic}` is not in {CATALOGUE.name}"
        )


def test_duplicate_ids_are_reported_not_hidden():
    """A shared rule id makes findings ambiguous, so the catalogue says so.

    V070 is currently claimed by both validate_xml's phon_placement and
    validate_glosses' gloss_code_as_FORM. This asserts the *mechanism*, not
    that particular collision: if the ids are renumbered there is nothing to
    report and the block is absent.
    """
    from QC.validation.rules_catalogue import collect, duplicate_ids

    duplicates = duplicate_ids(collect())
    text = CATALOGUE.read_text(encoding="utf-8")
    if duplicates:
        assert "Duplicate rule ids" in text
        for rule_id in duplicates:
            assert f"**{rule_id}**" in text
    else:
        assert "Duplicate rule ids" not in text
