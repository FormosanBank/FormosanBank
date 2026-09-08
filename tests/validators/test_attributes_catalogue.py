"""QC/validation/ATTRIBUTES.md must match the XSD that actually validates.

Same contract as test_rules_catalogue.py: the documented attribute set is
generated, so it cannot drift from the schema. POL-053 requires an
attribute to be declared, annotated, catalogued and given a policy entry;
this test enforces the first three.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "QC/validation/attributes_catalogue.py"
CATALOGUE = REPO_ROOT / "QC/validation/ATTRIBUTES.md"

sys.path.insert(0, str(REPO_ROOT))


def test_catalogue_is_current():
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        f"{CATALOGUE.name} is stale — run "
        f"`python QC/validation/attributes_catalogue.py`.\n"
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_every_attribute_is_documented():
    from QC.validation.attributes_catalogue import collect

    missing = [
        f"{element}/@{attribute}"
        for element, attribute, _use, _values, doc in collect()
        if not doc.strip()
    ]
    assert not missing, f"attributes with no xs:documentation: {missing}"


def test_catalogue_names_every_attribute():
    from QC.validation.attributes_catalogue import collect

    text = CATALOGUE.read_text(encoding="utf-8")
    for element, attribute, _use, _values, _doc in collect():
        assert f"| `{attribute}` |" in text, (
            f"{element}/@{attribute} is not in {CATALOGUE.name}"
        )


def test_enumerated_values_are_surfaced():
    from QC.validation.attributes_catalogue import collect

    rows = {(e, a): v for e, a, _u, v, _d in collect()}
    assert rows[("FORM", "kindOf")] == "original | standard | alternate"
    assert rows[("TRANSL", "kindOf")] == "original | standard"
    assert rows[("PHON", "kindOf")] == "original | standard"


def test_required_attributes_are_marked():
    from QC.validation.attributes_catalogue import collect

    rows = {(e, a): u for e, a, u, _v, _d in collect()}
    assert rows[("TEXT", "id")] == "required"
    assert rows[("FORM", "kindOf")] == "required"
    assert rows[("TEXT", "source")] == "optional"
