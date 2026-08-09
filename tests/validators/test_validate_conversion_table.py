import subprocess
import sys
from pathlib import Path

import pytest

from QC.validation import validate_conversion_table as vct

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "QC" / "validation" / "validate_conversion_table.py"
)


def _tsv(path: Path, header: list[str], rows: list[list[str]]) -> Path:
    lines = ["\t".join(header)] + ["\t".join(r) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_select_value_column_prefers_dialect():
    cols = ["letter", "Wutai", "Eastern", "default"]
    assert vct.select_value_column(cols, "Eastern", key="letter") == "Eastern"


def test_dialect_column_selected_per_dialect_with_default_fallback():
    cols = ["letter", "Wutai", "Eastern", "default"]
    # Dona has no column -> fall back to 'default'
    assert vct.select_value_column(cols, "Dona", key="letter") == "default"


def test_single_value_column_profile():
    cols = ["letter", "IPA"]
    assert vct.select_value_column(cols, "Wutai", key="letter") == "IPA"


def test_select_value_column_ambiguous_raises():
    cols = ["original", "Southern", "Coastal"]
    with pytest.raises(ValueError):
        vct.select_value_column(cols, "Malan", key="original")


def test_load_orthography_maps_grapheme_to_ipa(tmp_path):
    p = _tsv(tmp_path / "src.tsv", ["letter", "IPA"],
             [["T", "ʈ"], ["t", "t"], ["x", "NA"]])
    ortho = vct.load_orthography(p, "Wutai")
    assert ortho.ipa_of == {"T": "ʈ", "t": "t"}  # NA row skipped


def test_tokenize_longest_match_is_case_sensitive(tmp_path):
    # 'tr' is one grapheme; must not split into t + r, and 'T' != 't'.
    letters = ["tr", "t", "r", "T"]
    graphemes, unmatched = vct.tokenize("trT", letters)
    assert graphemes == ["tr", "T"]
    assert unmatched == []


def test_target_ipa_tokenizes_multigrapheme_target(tmp_path):
    # 'tr' -> ʈ (single grapheme); 'aa' -> a + a (two graphemes).
    out = _tsv(tmp_path / "out.tsv", ["letter", "default"],
               [["tr", "ʈ"], ["a", "a"]])
    output = vct.load_orthography(out, "default")
    assert vct.target_ipa("tr", output) == ("ʈ", [])
    assert vct.target_ipa("aa", output) == ("aa", [])


def test_target_ipa_reports_untokenizable(tmp_path):
    out = _tsv(tmp_path / "out.tsv", ["letter", "default"], [["a", "a"]])
    output = vct.load_orthography(out, "default")
    ipa, unmatched = vct.target_ipa("aq", output)
    assert ipa is None
    assert "q" in unmatched


def test_exact_ipa_match_is_confirmed():
    assert vct.reconcile("ʈ", "ʈ") == (vct.Verdict.CONFIRMED, "")


def test_tiebar_ligature_is_confirmed():
    # ʦ and t͡s are the same single segment -> no warning.
    verdict, _ = vct.reconcile("ʦ", "t͡s")
    assert verdict == vct.Verdict.CONFIRMED


def test_length_notation_is_warning():
    verdict, reason = vct.reconcile("aː", "aa")  # aː vs aa
    assert verdict == vct.Verdict.WARNING
    assert "length" in reason


def test_bare_digraph_affricate_is_warning():
    # bare 'ts' (possibly a cluster) vs affricate t͡s -> ambiguous.
    verdict, reason = vct.reconcile("ts", "t͡s")
    assert verdict == vct.Verdict.WARNING
    assert "affricate" in reason


def test_true_mismatch():
    assert vct.reconcile("p", "b")[0] == vct.Verdict.MISMATCH


def test_short_vowel_not_equated_with_long():
    # length expansion must not make short 'a' match long 'aː'/'aa'.
    assert vct.reconcile("a", "aa")[0] == vct.Verdict.MISMATCH
