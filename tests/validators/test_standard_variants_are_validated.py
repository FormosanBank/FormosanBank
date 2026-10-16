"""Character-level standard-tier rules must see `ver="alt"` variants.

POL-028 splits a tier into a base FORM and zero or more `ver="alt"`
variants, and `standardize.py` derives the standard variant from the
original variant exactly as it derives the base. So a standard variant is
machine-owned published text, and "is this text clean?" applies to it.

Most consumers correctly take the base alone -- counting, duplicate
detection, alignment, PHON generation -- because those ask "what does
this sentence say?", and a variant is a secondary reading. These rules
ask a different question, and were skipping variants. Two defects were
found sitting in variants that no validator looked at
(NTUFormosanCorpus, 2026-09-11); this is the half of that gap which is
checkable.
"""
from pathlib import Path

import pytest
from lxml import etree

from QC.validation.rules.text import (
    v110_smart_quotes,
    v111_imbalanced_parens,
    v114_multiple_whitespace,
    v120_null_in_S_standard,
    v133_dash_in_S_standard_FORM,
)

TEXT = """<?xml version='1.0' encoding='UTF-8'?>
<TEXT id="t" citation="c" BibTeX_citation="b" copyright="public domain"
      dialect="Coastal" xml:lang="ami">
  <S id="S1">
    <FORM kindOf="original">mimali</FORM>
    <FORM kindOf="standard">mimali</FORM>
    <FORM kindOf="standard" ver="alt">{variant}</FORM>
    <TRANSL xml:lang="eng">play</TRANSL>
  </S>
</TEXT>
"""


def _tree(tmp_path: Path, variant: str):
    p = tmp_path / "c.xml"
    p.write_text(TEXT.format(variant=variant), encoding="utf-8")
    return etree.parse(str(p)), p


@pytest.mark.parametrize("rule,variant", [
    (v110_smart_quotes, 'mimali “x”'),
    (v111_imbalanced_parens, 'mimali (x'),
    (v114_multiple_whitespace, 'mimali  x'),
    (v133_dash_in_S_standard_FORM, 'mi-mali'),
    (v120_null_in_S_standard, 'mimali ∅'),
], ids=["V110", "V111", "V114", "V133", "V120"])
def test_rule_sees_a_defect_in_the_variant(tmp_path, rule, variant):
    """The base is clean in every case, so any finding comes from the
    variant -- the assertion cannot pass for the wrong reason."""
    tree, path = _tree(tmp_path, variant)
    findings = rule(tree, path, None)
    assert findings, (
        f"{rule.__name__} found nothing; the clean base hid a defect in the "
        f"ver=\"alt\" variant {variant!r}"
    )


def test_a_clean_variant_still_produces_nothing(tmp_path):
    """Guard against the change becoming "always report": a variant that
    is clean must stay silent."""
    tree, path = _tree(tmp_path, "mimali")
    for rule in (v110_smart_quotes, v111_imbalanced_parens,
                 v114_multiple_whitespace, v133_dash_in_S_standard_FORM,
                 v120_null_in_S_standard):
        assert rule(tree, path, None) == [], rule.__name__
