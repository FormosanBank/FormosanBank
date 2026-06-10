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
