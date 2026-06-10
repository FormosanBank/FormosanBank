"""Tests for QC/corpus_counts.py — the single source of truth for
FormosanBank counting rules (tokenization, tier selection, language
resolution, per-file analysis records)."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "QC"))

import corpus_counts


class TestCountWords:
    def test_plain_words(self):
        assert corpus_counts.count_words("ina kaen wawa") == 3

    def test_digit_only_chunk_counts(self):
        # Joshua's rule 1: whitespace-separated digit-only chunks ARE words.
        assert corpus_counts.count_words("ina 123 wawa") == 3

    def test_punctuation_only_chunks_do_not_count(self):
        assert corpus_counts.count_words("ina wawa .") == 2
        assert corpus_counts.count_words("? ! — … \" '") == 0

    def test_mixed_alnum_and_punct_chunk_counts_once(self):
        assert corpus_counts.count_words("ma- kaen?") == 2

    def test_empty_and_none(self):
        assert corpus_counts.count_words("") == 0
        assert corpus_counts.count_words("   ") == 0
        assert corpus_counts.count_words(None) == 0

    def test_unicode_letters_count(self):
        # ʉ is a Unicode letter used in Formosan orthographies.
        assert corpus_counts.count_words("kʉnʉ ʉ") == 2


def _sentence(*forms):
    """Build an <S> with (kindOf, text) FORM children."""
    s = ET.Element("S")
    for kind, text in forms:
        f = ET.SubElement(s, "FORM", {"kindOf": kind})
        f.text = text
    return s


class TestSelectSentenceForm:
    def test_prefers_standard(self):
        s = _sentence(("original", "orig text"), ("standard", "std text"))
        assert corpus_counts.select_sentence_form(s) == "std text"

    def test_falls_back_to_original_when_no_standard(self):
        s = _sentence(("original", "orig text"))
        assert corpus_counts.select_sentence_form(s) == "orig text"

    def test_falls_back_when_standard_is_empty(self):
        s = _sentence(("standard", "   "), ("original", "orig text"))
        assert corpus_counts.select_sentence_form(s) == "orig text"

    def test_none_when_no_usable_form(self):
        assert corpus_counts.select_sentence_form(_sentence()) is None
        assert corpus_counts.select_sentence_form(_sentence(("original", ""))) is None

    def test_ignores_w_level_forms(self):
        # S-tier only: a FORM nested under W must not be selected.
        s = ET.Element("S")
        w = ET.SubElement(s, "W")
        f = ET.SubElement(w, "FORM", {"kindOf": "standard"})
        f.text = "word-level"
        assert corpus_counts.select_sentence_form(s) is None


class TestResolveLanguage:
    def test_plain_code(self):
        assert corpus_counts.resolve_language("ami", "Haian") == "Amis"

    def test_trv_truku_dialect_is_truku(self):
        assert corpus_counts.resolve_language("trv", "Truku") == "Truku"
        assert corpus_counts.resolve_language("trv", "truku") == "Truku"

    def test_trv_other_dialect_is_seediq(self):
        assert corpus_counts.resolve_language("trv", "Tgdaya") == "Seediq"
        assert corpus_counts.resolve_language("trv", "unknown") == "Seediq"
        assert corpus_counts.resolve_language("trv", "") == "Seediq"

    def test_case_and_whitespace_normalized(self):
        assert corpus_counts.resolve_language(" AMI ", "x") == "Amis"

    def test_unknown_or_missing_code_returns_none(self):
        assert corpus_counts.resolve_language("xx", "y") is None
        assert corpus_counts.resolve_language("", "y") is None
        assert corpus_counts.resolve_language(None, "y") is None
