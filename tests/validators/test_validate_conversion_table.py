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


def _ortho(tmp_path, name, rows, header=("letter", "default")):
    return vct.load_orthography(
        _tsv(tmp_path / name, list(header), [list(r) for r in rows]), "default")


def test_load_conversion_table_reads_rows(tmp_path):
    p = _tsv(tmp_path / "conv.tsv", ["original", "standard"],
             [["T", "tr"], ["x", "NA"], ["y", ""]])
    rows, column = vct.load_conversion_table(p, "standard")
    assert rows == [("T", "tr")]      # NA and empty targets skipped
    assert column == "standard"


def test_audit_confirmed_row(tmp_path):
    original = _ortho(tmp_path, "s.tsv", [["T", "ʈ"]])
    output = _ortho(tmp_path, "o.tsv", [["tr", "ʈ"]])
    report = vct.audit(original, output, [("T", "tr")], "default")
    assert report.rows[0].verdict == vct.Verdict.CONFIRMED


def test_audit_unknown_source(tmp_path):
    original = _ortho(tmp_path, "s.tsv", [["T", "ʈ"]])
    output = _ortho(tmp_path, "o.tsv", [["tr", "ʈ"]])
    report = vct.audit(original, output, [("Z", "tr")], "default")
    assert report.rows[0].verdict == vct.Verdict.UNKNOWN_SOURCE


def test_audit_untokenizable_target(tmp_path):
    original = _ortho(tmp_path, "s.tsv", [["T", "ʈ"]])
    output = _ortho(tmp_path, "o.tsv", [["tr", "ʈ"]])
    report = vct.audit(original, output, [("T", "qq")], "default")
    assert report.rows[0].verdict == vct.Verdict.UNTOKENIZABLE


def test_audit_detects_phoneme_merge(tmp_path):
    # two distinct source IPAs (s, z) both land on output IPA s.
    original = _ortho(tmp_path, "s.tsv", [["s", "s"], ["z", "z"]])
    output = _ortho(tmp_path, "o.tsv", [["c", "s"]])
    report = vct.audit(original, output, [("s", "c"), ("z", "c")], "default")
    assert any(out_ipa == "s" for out_ipa, _ in report.merges)


def test_audit_detects_cant_encode(tmp_path):
    # output distinguishes /p/ and /b/; source can only ever produce /p/.
    original = _ortho(tmp_path, "s.tsv", [["p", "p"]])
    output = _ortho(tmp_path, "o.tsv", [["p", "p"], ["b", "b"]])
    report = vct.audit(original, output, [("p", "p")], "default")
    assert "b" in report.cant_encode
    assert "p" not in report.cant_encode


def test_audit_coverage_gap_and_identity_passthrough(tmp_path):
    # 'a' has no row but is identical in output -> passthrough, no gap.
    # 'q' has no row and no matching output grapheme -> gap.
    original = _ortho(tmp_path, "s.tsv", [["a", "a"], ["q", "q"]])
    output = _ortho(tmp_path, "o.tsv", [["a", "a"]])
    report = vct.audit(original, output, [], "default")
    gaps = {g for g, _ in report.coverage_gaps}
    assert gaps == {"q"}


def test_output_dialects_lists_real_dialects(tmp_path):
    p = _tsv(tmp_path / "o.tsv", ["letter", "Wutai", "Eastern", "default"],
             [["a", "a", "a", "a"]])
    assert vct.output_dialects(p) == ["Wutai", "Eastern"]


def test_output_dialects_single_column_returns_none(tmp_path):
    p = _tsv(tmp_path / "o.tsv", ["letter", "IPA"], [["a", "a"]])
    assert vct.output_dialects(p) == [None]


def test_render_report_has_documented_sections(tmp_path):
    original = _ortho(tmp_path, "s.tsv", [["a", "a"]])
    output = _ortho(tmp_path, "o.tsv", [["a", "a"]])
    report = vct.audit(original, output, [("a", "a")], None)
    text = vct.render_report([report])
    for heading in ("Summary", "Confirmed", "Warnings", "Unresolved",
                    "Information loss", "Coverage", "Table integrity"):
        assert heading in text


def _write_trio(tmp_path, src_rows, out_rows, conv_rows,
                src_h=("letter", "IPA"), out_h=("letter", "default"),
                conv_h=("original", "standard")):
    src = _tsv(tmp_path / "src.tsv", list(src_h), [list(r) for r in src_rows])
    out = _tsv(tmp_path / "out.tsv", list(out_h), [list(r) for r in out_rows])
    conv = _tsv(tmp_path / "conv.tsv", list(conv_h), [list(r) for r in conv_rows])
    return src, out, conv


def _run_cli(src, out, conv):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(src), str(out), str(conv)],
        capture_output=True, text=True,
    )


def test_cli_exit_zero_when_only_warnings(tmp_path):
    # a: (/aː/) -> aa (/aa/) is a warning, not a mismatch.
    src, out, conv = _write_trio(
        tmp_path,
        src_rows=[["a", "a"], [":", "ː"]],
        out_rows=[["a", "a"]],
        conv_rows=[["a:", "aa"]],
    )
    result = _run_cli(src, out, conv)
    assert result.returncode == 0
    assert "length" in result.stdout


def test_cli_exit_nonzero_on_mismatch(tmp_path):
    src, out, conv = _write_trio(
        tmp_path,
        src_rows=[["p", "p"]],
        out_rows=[["b", "b"]],
        conv_rows=[["p", "b"]],
    )
    result = _run_cli(src, out, conv)
    assert result.returncode == 1


def test_cli_smoke_on_real_rukai_files():
    repo = Path(__file__).resolve().parents[2]
    src = repo / "Orthographies" / "Li" / "Rukai.tsv"
    out = repo / "Orthographies" / "Ortho113" / "Rukai.tsv"
    conv = repo / "Orthographies" / "ConversionTables" / "Rukai_Li_113.tsv"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(src), str(out), str(conv)],
        capture_output=True, text=True,
    )
    assert "Summary" in result.stdout
    # a: -> aa is a length-doubling equivalence, reported as a warning.
    assert "a:" in result.stdout
