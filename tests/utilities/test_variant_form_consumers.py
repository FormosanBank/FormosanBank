"""Consumers that pick a FORM by @kindOf alone must still pick the base.

Companion to tests/validators/test_variant_form_selection.py, covering the
consumers that do not use ``find()`` and so were missed by a grep for it:

* ``sample_sentences._collect_forms`` builds a ``{kindOf: text}`` dict, so a
  later variant *overwrites* the base and the human expert reviews the
  wrong string. Live on published WakelinTexts data today.
* the three duplicate-sentence extractors loop over direct children and
  ``break`` on the first FORM of the wanted kind — first match in document
  order, which is a variant whenever one is written first.

POL-028 (revised 2026-09-09); maintainer ruling 2026-09-10 for the
no-base case.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from lxml import etree

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "QC"))

from QC.utilities import find_duplicate_sentences  # noqa: E402
from QC.utilities.sample_sentences import _collect_forms  # noqa: E402
from QC.cleaning import remove_duplicate_sentences  # noqa: E402
from QC.validation import validate_duplicate_sentences  # noqa: E402

_HEAD = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<TEXT id="T1" citation="t" BibTeX_citation="@t{t}" '
    'copyright="t" xml:lang="tao">'
)

# The real shape of WakelinTexts Kwaway/S21W1.
_WAKELIN_W = (
    '<W id="S21W1">'
    '<FORM kindOf="original">manuyung-e</FORM>'
    '<FORM kindOf="original" ver="alt">manuyung</FORM>'
    '<FORM kindOf="standard">manoyong-e</FORM>'
    '<FORM kindOf="standard" ver="alt">manoyong</FORM>'
    "</W>"
)


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "t.xml"
    path.write_text(_HEAD + body + "</TEXT>", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# sample_sentences: the expert-review sampler
# ---------------------------------------------------------------------------

def test_collect_forms_keeps_the_base_not_the_variant():
    w = etree.fromstring(_WAKELIN_W)
    assert _collect_forms(w) == {
        "original": "manuyung-e",
        "standard": "manoyong-e",
    }


def test_collect_forms_ignores_a_variant_only_tier():
    w = etree.fromstring(
        '<W id="W1"><FORM kindOf="original" ver="alt">manuyung</FORM></W>'
    )
    assert _collect_forms(w) == {}


# ---------------------------------------------------------------------------
# The three duplicate-sentence extractors
# ---------------------------------------------------------------------------

_VARIANT_FIRST_S = (
    '<S id="S1">'
    '<FORM kindOf="standard" ver="alt">variant text</FORM>'
    '<FORM kindOf="standard">base text</FORM>'
    "</S>"
)


def test_find_duplicate_sentences_extracts_the_base(tmp_path):
    path = _write(tmp_path, _VARIANT_FIRST_S)
    assert find_duplicate_sentences.extract_forms(str(path), "standard") == [
        ("S1", "base text")
    ]


def test_validate_duplicate_sentences_extracts_the_base(tmp_path):
    path = _write(tmp_path, _VARIANT_FIRST_S)
    assert validate_duplicate_sentences.extract_sentences(
        str(path), "standard"
    ) == [("S1", "base text")]


def test_remove_duplicate_sentences_extracts_the_base(tmp_path):
    path = _write(tmp_path, _VARIANT_FIRST_S)
    got = remove_duplicate_sentences._extract_sentences_lxml(
        str(path), "standard"
    )
    assert got == [
        ("S1", remove_duplicate_sentences.normalize_for_comparison("base text"))
    ]


def test_duplicate_extractors_skip_a_variant_only_sentence(tmp_path):
    """Strict: no base of that kind means nothing to compare."""
    path = _write(
        tmp_path,
        '<S id="S1"><FORM kindOf="standard" ver="alt">variant text</FORM></S>',
    )
    assert find_duplicate_sentences.extract_forms(str(path), "standard") == []
    assert validate_duplicate_sentences.extract_sentences(str(path), "standard") == []
    assert remove_duplicate_sentences._extract_sentences_lxml(str(path), "standard") == []


def test_a_variant_does_not_create_a_false_duplicate(tmp_path):
    """Two sentences whose *variants* coincide are not duplicates."""
    path = _write(
        tmp_path,
        '<S id="S1">'
        '<FORM kindOf="standard">alpha</FORM>'
        '<FORM kindOf="standard" ver="alt">shared</FORM>'
        "</S>"
        '<S id="S2">'
        '<FORM kindOf="standard">beta</FORM>'
        '<FORM kindOf="standard" ver="alt">shared</FORM>'
        "</S>",
    )
    texts = [t for _sid, t in find_duplicate_sentences.extract_forms(str(path), "standard")]
    assert texts == ["alpha", "beta"]
    assert len(set(texts)) == 2


# ---------------------------------------------------------------------------
# rules/text.py's three direct-child FORM helpers
# ---------------------------------------------------------------------------

def test_text_rule_helpers_read_the_base(tmp_path):
    """`for child in s: if ... == kind: return` is first-match in document
    order, so a variant written first stood in for its base."""
    from lxml import etree as _etree

    from QC.validation.rules import text as text_rules

    s = _etree.fromstring(
        '<S id="S1">'
        '<FORM kindOf="original" ver="alt">variant orig</FORM>'
        '<FORM kindOf="original">base orig</FORM>'
        '<FORM kindOf="standard" ver="alt">variant std</FORM>'
        '<FORM kindOf="standard">base std</FORM>'
        "</S>"
    )
    assert text_rules._s_original_form_text(s) == "base orig"
    assert text_rules._s_standard_form_text(s) == "base std"
    assert text_rules._direct_form_by_kind(s, "original") == "base orig"
    assert text_rules._direct_form_by_kind(s, "standard") == "base std"


def test_text_rule_helpers_report_no_base_as_absent():
    from lxml import etree as _etree

    from QC.validation.rules import text as text_rules

    s = _etree.fromstring(
        '<S id="S1"><FORM kindOf="standard" ver="alt">variant std</FORM></S>'
    )
    assert text_rules._s_standard_form_text(s) is None
    assert text_rules._direct_form_by_kind(s, "standard") is None


# ---------------------------------------------------------------------------
# orthography_extract: the corpus text an orthography is inventoried from
# ---------------------------------------------------------------------------

def test_orthography_extract_reads_the_base(tmp_path):
    from QC.orthography.orthography_extract import generate_corpus

    # generate_corpus selects files by the language name in the directory path.
    xml_dir = tmp_path / "XML" / "Yami"
    xml_dir.mkdir(parents=True)
    (xml_dir / "t.xml").write_text(
        _HEAD
        + '<S id="S1">'
        + '<FORM kindOf="standard" ver="alt">qqqq</FORM>'
        + '<FORM kindOf="standard">base text</FORM>'
        + "</S></TEXT>",
        encoding="utf-8",
    )
    corpus = generate_corpus("Yami", str(tmp_path), "standard")
    text = corpus if isinstance(corpus, str) else " ".join(map(str, corpus.values()))
    assert "base text" in text
    assert "qqqq" not in text
