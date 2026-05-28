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
    """Sentence ids and FORM text are read correctly from a minimal fixture."""
    # valid_minimal.xml has one S (S_1) with FORM "Halo."
    forms = extract_standard_forms(str(fixtures_dir / "valid_minimal.xml"))
    assert len(forms) == 1
    assert forms[0][0] == "S_1"
    assert forms[0][1] == "Halo."


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


def test_real_glosbe_sentences_are_found(glosbe_sample, glosbe_index):
    """Sentences planted from the real Glosbe corpus should be matchable."""
    planted_gids = {gid for gid, _ in glosbe_sample}
    found_gids = set()
    for _, text in glosbe_sample:
        if text.lower() in glosbe_index:
            for hit_gid in glosbe_index[text.lower()]:
                found_gids.add(hit_gid)
    assert planted_gids.issubset(found_gids), (
        f"missing matches: {planted_gids - found_gids}"
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
