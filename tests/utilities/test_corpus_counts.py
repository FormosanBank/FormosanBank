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


FIXTURE_XML = REPO_ROOT / "tests" / "fixtures" / "stats_corpus" / "MiniCorpus" / "XML"


class TestAnalyzeFile:
    def test_ami_haian_record(self):
        rec = corpus_counts.analyze_file(FIXTURE_XML / "ami_haian.xml")
        assert rec["language"] == "ami"
        assert rec["dialect"] == "Haian"
        assert rec["word_count"] == 5
        assert rec["sentences"] == 3
        assert rec["segmented_words"] == 3
        assert rec["glossed_words"] == 3
        assert rec["eng_transl_count"] == 5  # two eng TRANSLs in s2 count once
        assert rec["zho_transl_count"] == 3
        assert rec["word_elements"] == 3
        assert rec["morpheme_elements"] == 1
        assert rec["translation_elements"] == 5
        assert rec["audio_elements"] == 0
        assert rec["file_count"] == 1
        # s3 has W-level FORMs but no S-level FORM: contributes 0, warned.
        assert any("no countable FORM" in w for w in rec["warnings"])

    def test_truku_record_and_audio_counts(self):
        rec = corpus_counts.analyze_file(FIXTURE_XML / "trv_truku.xml")
        assert rec["word_count"] == 2
        assert rec["transcribed_audio_count"] == 1
        assert rec["untranscribed_audio_count"] == 1
        assert rec["audio_elements"] == 2
        assert corpus_counts.resolve_language(rec["language"], rec["dialect"]) == "Truku"

    def test_missing_dialect_warns(self):
        rec = corpus_counts.analyze_file(FIXTURE_XML / "ami_nodialect.xml")
        assert rec["word_count"] == 1
        assert rec["dialect"] == ""
        assert any("missing dialect" in w for w in rec["warnings"])

    def test_parse_error_raises(self):
        with pytest.raises(ET.ParseError):
            corpus_counts.analyze_file(FIXTURE_XML / "bad.xml")

    def test_missing_lang_warns(self):
        rec = corpus_counts.analyze_file(FIXTURE_XML.parent.parent / "nolang.xml")
        assert rec["language"] == ""
        assert rec["word_count"] == 1
        assert any("missing xml:lang" in w for w in rec["warnings"])


class TestCollectRecords:
    def test_walks_xml_dir_and_collects_errors(self):
        records, errors = corpus_counts.collect_records(FIXTURE_XML)
        assert len(records) == 4
        assert len(errors) == 1
        assert errors[0]["path"].endswith("bad.xml")
        assert sum(r["word_count"] for r in records) == 11  # 5 + 2 + 3 + 1
