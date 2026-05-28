"""Tests for QC/utilities/find_duplicate_sentences.py.

Migrated from QC/test_find_duplicate_sentences.py.

Note on the Glosbe corpus dependency: this test plants sentences extracted
from the actual Glosbe corpus at Corpora/Glosbe/XML/Amis/amis_glosbe.xml
and verifies that the matcher finds them. A synthetic fixture would not
exercise the diversity of real Glosbe-derived sentences (varying
punctuation, casing, length), which is exactly what this matcher needs
to handle. Per the design doc's real-corpus exception, this dependency
is explicit and intentional.
"""
import sys
import xml.sax.saxutils
from collections import defaultdict
from pathlib import Path

import pytest

# Import the module under test
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "QC" / "utilities"))
from find_duplicate_sentences import extract_standard_forms  # noqa: E402

GLOSBE_XML = REPO / "Corpora" / "Glosbe" / "XML" / "Amis" / "amis_glosbe.xml"


@pytest.fixture(scope="module")
def glosbe_sample():
    """First 5 standard sentences from the Glosbe corpus."""
    if not GLOSBE_XML.is_file():
        pytest.skip(f"Glosbe corpus not found at {GLOSBE_XML}")
    out = []
    for sid, text in extract_standard_forms(str(GLOSBE_XML)):
        if text.strip():
            out.append((sid, text))
        if len(out) >= 5:
            break
    return out


@pytest.fixture(scope="module")
def glosbe_index():
    """Lowercased text -> list of S ids, built from the Glosbe corpus."""
    if not GLOSBE_XML.is_file():
        pytest.skip(f"Glosbe corpus not found at {GLOSBE_XML}")
    idx = defaultdict(list)
    for gid, text in extract_standard_forms(str(GLOSBE_XML)):
        idx[text.lower()].append(gid)
    return idx


def test_extract_standard_forms_round_trips(fixtures_dir):
    """Sentence ids and FORM text are read correctly from a minimal fixture.

    valid_minimal.xml has distinct content in its two FORM tiers
    ("Halo (orig)." vs "Halo (std)."), so this assertion catches a
    regression where extract_standard_forms returns the original tier
    instead of the standard tier.
    """
    forms = extract_standard_forms(str(fixtures_dir / "valid_minimal.xml"))
    assert len(forms) == 1
    assert forms[0][0] == "S_1"
    assert forms[0][1] == "Halo (std)."


def test_word_level_forms_are_excluded(fixtures_dir):
    """FORM elements inside <W> (not direct children of <S>) are not extracted."""
    forms = extract_standard_forms(str(fixtures_dir / "valid_with_word_level.xml"))
    texts = [t for _, t in forms]
    assert "SHOULD_NOT_MATCH" not in texts
    assert "A real sentence" in texts


def test_invented_sentences_produce_no_false_positives(fixtures_dir, glosbe_index):
    forms = extract_standard_forms(str(fixtures_dir / "invented_no_match.xml"))
    false_positives = [(sid, text) for sid, text in forms if text.lower() in glosbe_index]
    assert false_positives == []


def test_planted_glosbe_sentences_round_trip_through_extract_and_match(
    tmp_path, glosbe_sample, glosbe_index
):
    """Plant Glosbe sentences in a separate corpus with new IDs; verify the
    extractor + lower-case lookup round-trip finds each one back in Glosbe.

    This mirrors the original hand-rolled test's design: copying glosbe
    sentences into a *separate* corpus (with `PLANTED_*` ids) and then
    looking each extracted text up in glosbe_index exercises the full
    pipeline — file I/O + parse + extract + lowercase + index lookup.
    Asserting that `glosbe_sample` is a subset of `glosbe_index` directly,
    without the planting step, would be tautological since glosbe_sample
    IS the first 5 entries of the index.
    """
    sentences_xml = "\n".join(
        f'  <S id="PLANTED_{i}">\n'
        f'    <FORM kindOf="standard">{xml.sax.saxutils.escape(text)}</FORM>\n'
        f'  </S>'
        for i, (_, text) in enumerate(glosbe_sample, 1)
    )
    planted_xml = tmp_path / "planted.xml"
    planted_xml.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<TEXT id="PLANTED" citation="test" BibTeX_citation="@test{test}" '
        'copyright="test" xml:lang="ami">\n'
        f'{sentences_xml}\n'
        '</TEXT>\n'
    )

    extracted = extract_standard_forms(str(planted_xml))
    assert len(extracted) == len(glosbe_sample), (
        f"expected {len(glosbe_sample)} extracted sentences, got {len(extracted)}"
    )

    missing = [
        (sid, text) for sid, text in extracted
        if text.lower() not in glosbe_index
    ]
    assert missing == [], (
        f"planted sentences not found in glosbe_index after round-trip: {missing}"
    )


def test_case_insensitive_matching(tmp_path, glosbe_sample, glosbe_index):
    """Sentences extracted from upper-cased XML are findable in the lower-cased index."""
    _, sample_text = glosbe_sample[0]
    # Build a small XML at runtime with the sample text uppercased. We need a
    # corpus-derived sentence here (not a synthetic one) so the lookup against
    # glosbe_index is meaningful. Inline-via-tmp_path rather than a standalone
    # fixture because the content depends on the actual Glosbe corpus state.
    upper_xml = tmp_path / "upper.xml"
    upper_xml.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<TEXT id="TEST_UP" citation="test" BibTeX_citation="@test{test}" copyright="test" xml:lang="ami">\n'
        f'  <S id="UPPER_1">\n'
        f'    <FORM kindOf="standard">{xml.sax.saxutils.escape(sample_text.upper())}</FORM>\n'
        '  </S>\n'
        '</TEXT>\n'
    )
    forms = extract_standard_forms(str(upper_xml))
    assert any(text.lower() in glosbe_index for _, text in forms), (
        f"upper-cased extract of {sample_text!r} not found in lower-cased glosbe_index"
    )
