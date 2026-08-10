"""validate_registries: cross-file consistency as SOFT findings.

Maintainer ruling 2026-08-10 (POL-034): registries may be legitimately
out of sync mid-migration, so consistency findings are SOFT and never
fail the run. Only an unreadable registry is HARD (exit 1). The findings
CSV uses the standard one-CSV shape so the same triage tooling applies.

Tests build a miniature repo layout under tmp_path and point the
validator at it with --repo-root; they never depend on the real
registries (which drift). The mini standards.csv is generated from the
live ISO_TO_LANGUAGE so V150 (language missing from standards) stays
quiet unless a test removes a row on purpose.
"""
import csv
from pathlib import Path

from QC.validation._dialect_inventory import ISO_TO_LANGUAGE
from tests._helpers import run_qc_script

SCRIPT = "QC/validation/validate_registries.py"


def _mini_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "Orthographies" / "Ortho113").mkdir(parents=True)
    (root / "Orthographies" / "ConversionTables").mkdir(parents=True)
    rows = "".join(
        f"{language},Ortho113\n"
        for language in sorted(set(ISO_TO_LANGUAGE.values()))
    )
    (root / "standards.csv").write_text(
        "language,standard_orthography\n" + rows, encoding="utf-8")
    (root / "dialects.csv").write_text(
        "Language,Official,Chinese,glottocode,OtherNames\n"
        "Puyuma,Nanwang,南王,nanw1234,\n"
        "Amis,Coastal,海岸,cent2104,\n",
        encoding="utf-8")
    return root


def _run(root: Path, out: Path):
    return run_qc_script(SCRIPT, ["--repo-root", str(root),
                                  "--csv", str(out)])


def _findings(csv_path: Path) -> list:
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def test_consistent_mini_repo_is_clean(tmp_path):
    root = _mini_repo(tmp_path)
    proc = _run(root, tmp_path / "f.csv")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "V15" not in proc.stdout


def test_language_missing_from_standards_is_soft(tmp_path):
    root = _mini_repo(tmp_path)
    lines = (root / "standards.csv").read_text(encoding="utf-8").splitlines()
    (root / "standards.csv").write_text(
        "\n".join(line for line in lines if not line.startswith("Amis,"))
        + "\n", encoding="utf-8")
    proc = _run(root, tmp_path / "f.csv")
    assert proc.returncode == 0, "SOFT findings must not fail the run"
    assert "V150" in proc.stdout


def test_unknown_conversion_table_dialect_is_soft(tmp_path):
    root = _mini_repo(tmp_path)
    (root / "Orthographies" / "ConversionTables"
     / "Puyuma_Test_113.tsv").write_text(
        "original\tNanwan\nl\tll\n", encoding="utf-8")  # typo'd dialect
    out = tmp_path / "f.csv"
    proc = _run(root, out)
    assert proc.returncode == 0
    assert "V152" in proc.stdout
    rows = [r for r in _findings(out) if r["rule_id"] == "V152"]
    assert rows and rows[0]["severity"] == "SOFT"
    assert "Nanwan" in rows[0]["message"]


def test_missing_scheme_folder_is_soft(tmp_path):
    root = _mini_repo(tmp_path)
    text = (root / "standards.csv").read_text(encoding="utf-8")
    (root / "standards.csv").write_text(
        text.replace("Amis,Ortho113", "Amis,OrthoNope"), encoding="utf-8")
    proc = _run(root, tmp_path / "f.csv")
    assert proc.returncode == 0
    assert "V151" in proc.stdout


def test_unknown_rules_sidecar_dialect_is_soft(tmp_path):
    root = _mini_repo(tmp_path)
    (root / "Orthographies" / "Ortho113" / "Puyuma.rules.tsv").write_text(
        "pattern\treplacement\tdialect\nx\ty\tNanwan\nx\ty\tdefault\n",
        encoding="utf-8")
    proc = _run(root, tmp_path / "f.csv")
    assert proc.returncode == 0
    assert "V153" in proc.stdout


def test_unreadable_registry_is_hard_exit(tmp_path):
    root = _mini_repo(tmp_path)
    (root / "standards.csv").unlink()
    proc = _run(root, tmp_path / "f.csv")
    assert proc.returncode == 1


def test_legacy_variant_notation_in_profile_is_soft(tmp_path):
    """V154: profile IPA cells must use [x|y], not legacy x~y (POL-013)."""
    root = _mini_repo(tmp_path)
    (root / "Orthographies" / "Ortho113" / "Amis.tsv").write_text(
        "letter\tstandard\nb\tb~v\nv\t[b|v]\n", encoding="utf-8")
    proc = _run(root, tmp_path / "f.csv")
    assert proc.returncode == 0
    assert "V154" in proc.stdout
    rows = [r for r in _findings(tmp_path / "f.csv")
            if r["rule_id"] == "V154"]
    assert rows and rows[0]["character"] == "b~v"


def test_bracket_variant_notation_is_clean(tmp_path):
    root = _mini_repo(tmp_path)
    (root / "Orthographies" / "Ortho113" / "Amis.tsv").write_text(
        "letter\tstandard\nb\t[b|v]\nd\t[ɬ|ɮ]\n", encoding="utf-8")
    proc = _run(root, tmp_path / "f.csv")
    assert proc.returncode == 0
    assert "V154" not in proc.stdout


def test_comma_separated_sidecar_dialects_all_checked(tmp_path):
    """V153 must split dialect cells on commas like the rules engine does:
    'Zhuoqun,Kaqun' is two canonical names, not one unknown one (the
    false positive in the 2026-08-10 baseline run)."""
    root = _mini_repo(tmp_path)
    (root / "dialects.csv").write_text(
        "Language,Official,Chinese,glottocode,OtherNames\n"
        "Bunun,Zhuoqun,卓群,taki1252,\n"
        "Bunun,Kaqun,卡群,taki1251,\n",
        encoding="utf-8")
    (root / "Orthographies" / "Ortho113" / "Bunun.rules.tsv").write_text(
        "pattern\treplacement\tdescription\tdialect\n"
        "x\ty\tok\tZhuoqun,Kaqun\n"
        "x\ty\tbad\tZhuoqun,Nanwan\n",
        encoding="utf-8")
    out = tmp_path / "f.csv"
    proc = _run(root, out)
    assert proc.returncode == 0
    rows = [r for r in _findings(out) if r["rule_id"] == "V153"]
    assert [r["character"] for r in rows] == ["Nanwan"], (
        f"only the genuinely unknown name should fire; got {rows!r}")
