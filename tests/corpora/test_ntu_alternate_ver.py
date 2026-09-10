"""NTUFormosanCorpus variant FORMs use the POL-028 ver="alt" spelling.

POL-028 was revised on 2026-09-09: a variant reading is a FORM whose
``kindOf`` names its tier plus ``ver="alt"``. The older spelling,
``kindOf="alternate"``, names no tier — so a variant cannot say which
base it varies from, and ``standardize.py`` cannot derive its standard
counterpart because nothing knows which tier it belongs to. It is
deprecated and reported by V157 (SOFT).

NTU's build (PR #224) landed one day after that revision and emitted 191
FORMs in the old spelling, taking the bank-wide V157 count from 8 back to
199. These tests hold the corpus to the current spelling and to the two
POL-028 invariants that follow from it.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import pytest

NTU_XML = (
    Path(__file__).resolve().parents[2]
    / "Corpora" / "NTUFormosanCorpus" / "XML"
)

TIERS = ("original", "standard")


def _xml_files() -> list[Path]:
    return sorted(NTU_XML.rglob("*.xml"))


@pytest.fixture(scope="module")
def nodes() -> list[tuple[Path, ET.Element]]:
    """Every element that has at least one direct FORM child."""
    out = []
    for path in _xml_files():
        root = ET.parse(path).getroot()
        for node in root.iter():
            if node.find("FORM") is not None:
                out.append((path, node))
    return out


def test_corpus_is_present():
    """Guard: an empty glob would make every other test vacuously pass."""
    assert _xml_files(), f"no XML found under {NTU_XML}"


def test_no_form_uses_the_deprecated_alternate_kindof(nodes):
    offenders = [
        (path.name, node.get("id"))
        for path, node in nodes
        for form in node.findall("FORM")
        if form.get("kindOf") == "alternate"
    ]
    assert offenders == [], (
        f"{len(offenders)} FORM(s) still use kindOf='alternate' "
        f"(V157); first few: {offenders[:5]}"
    )


def test_every_variant_has_exactly_one_base_in_its_own_tier(nodes):
    """POL-028 / V149: a variant is a variant *of* something."""
    broken = []
    for path, node in nodes:
        forms = node.findall("FORM")
        for tier in TIERS:
            same = [f for f in forms if f.get("kindOf") == tier]
            variants = [f for f in same if f.get("ver") is not None]
            bases = [f for f in same if f.get("ver") is None]
            if variants and len(bases) != 1:
                broken.append((path.name, node.get("id"), tier, len(bases)))
    assert broken == [], f"variants without exactly one base: {broken[:5]}"


def test_each_original_variant_has_a_derived_standard_variant(nodes):
    """POL-028: the standard tier is derived (POL-002), so its variants
    are derived too — one standard variant per original variant."""
    mismatched = []
    for path, node in nodes:
        forms = node.findall("FORM")
        counts = Counter(
            f.get("kindOf") for f in forms if f.get("ver") is not None
        )
        # Only nodes that have a standard tier at all: a corpus with no
        # standard tier is a different (documented) situation.
        if not any(f.get("kindOf") == "standard" for f in forms):
            continue
        if counts.get("original", 0) != counts.get("standard", 0):
            mismatched.append(
                (path.name, node.get("id"),
                 counts.get("original", 0), counts.get("standard", 0))
            )
    assert mismatched == [], (
        "original/standard variant counts disagree "
        f"(file, id, n_original, n_standard): {mismatched[:5]}"
    )


def test_ver_values_are_in_the_allowlist(nodes):
    """V156: FORM/@ver shares TRANSL's allowlist."""
    bad = {
        form.get("ver")
        for _path, node in nodes
        for form in node.findall("FORM")
        if form.get("ver") not in (None, "alt")
    }
    assert bad == set(), f"unexpected FORM/@ver values: {bad}"


# ---------------------------------------------------------------------------
# Step 14 must not record a variant across an unresolved slash alternation
# ---------------------------------------------------------------------------

def test_no_wm_variant_carries_a_paren_or_slash(nodes):
    """V121 (HARD) forbids a paren or slash in a W/M FORM.

    The source writes `ngu-/mu-(a-)drusa`: a slash alternation whose SECOND
    reading carries optional material. Step 14 of the builder records optional
    material as a variant, but it runs long before
    `resolve_slash_alternatives`, so it produced base `ngu-/mu-drusa` and
    variant `ngu-/mu-a-drusa`. Only the base was ever de-slashed; the variant
    kept the slash and, once POL-028 derivation gave it a standard-tier
    counterpart, the same V121 finding was reported twice.
    """
    import re
    offenders = [
        (path.name, node.get("id"), form.get("kindOf"), form.text)
        for path, node in nodes
        if node.tag in ("W", "M")
        for form in node.findall("FORM")
        if form.get("ver") is not None and re.search(r"[()/]", form.text or "")
    ]
    assert offenders == [], (
        f"{len(offenders)} variant FORM(s) carry a paren or slash: {offenders[:4]}"
    )


def test_step14_skips_a_word_whose_form_is_a_slash_alternation():
    """The predicate that gates step 14.

    Optional material inside a real alternation belongs to ONE reading, and
    which reading survives is not settled until resolve_slash_alternatives
    runs. A trailing or empty slash is not an alternation — one real reading —
    so optional material there is unambiguous and step 14 still applies.
    """
    import sys
    pipeline = (
        Path(__file__).resolve().parents[2]
        / "Corpora" / "NTUFormosanCorpus" / "CodeAndDocs" / "pipeline"
    )
    if str(pipeline) not in sys.path:
        sys.path.insert(0, str(pipeline))
    from pipeline_sentences import spans_slash_alternation

    # Real alternation: the '(a-)' sits inside the reading that is discarded.
    assert spans_slash_alternation("ngu-/mu-(a-)drusa") is True
    # Trailing slash: one real reading, optional material unambiguous.
    assert spans_slash_alternation("hinolaong(-an),/") is False
    assert spans_slash_alternation("(Hx),/") is False
    # No slash at all: the ordinary step-14 case.
    assert spans_slash_alternation("ka(z)") is False
    assert spans_slash_alternation("kangavas(=an)") is False
