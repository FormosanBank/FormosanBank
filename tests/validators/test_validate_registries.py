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
    # languages.csv mirrors the live ISO map so the mini repo carries the
    # full registry set the validator reads (V155, POL-040).
    lang_rows = "".join(
        f"{code},{name},\n" for code, name in sorted(ISO_TO_LANGUAGE.items()))
    (root / "languages.csv").write_text(
        "ISO639-3,Language,Notes\n" + lang_rows, encoding="utf-8")
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


def test_conversion_table_column_naming_a_language_is_clean(tmp_path):
    """V152 (2026-08-12): a value column may name a *language*, not only an
    Official dialect — single-dialect languages write the language name
    itself in @dialect (dialect="Tsou")."""
    root = _mini_repo(tmp_path)
    (root / "Orthographies" / "ConversionTables"
     / "Tsou_Test_113.tsv").write_text(
        "original\tTsou\nl\tll\n", encoding="utf-8")
    out = tmp_path / "f.csv"
    proc = _run(root, out)
    assert proc.returncode == 0
    assert "V152" not in proc.stdout, proc.stdout


def test_conversion_table_column_naming_an_iso_sharing_language_is_clean(
        tmp_path):
    """The real defect: Seediq_94_113.tsv / Seediq_Church_113.tsv carry a
    'Truku' value column. Truku shares ISO trv with Seediq — it is named in
    languages.csv and carries its own dialects.csv Language row, and
    validate_conversion_table --dialect Truku passes — so V152 must not fire
    on it."""
    root = _mini_repo(tmp_path)
    with open(root / "dialects.csv", "a", encoding="utf-8") as f:
        f.write("Seediq,Tegudaya,德固達雅,teke1282,\n")
        f.write("Truku,,,,\n")
    with open(root / "languages.csv", "a", encoding="utf-8") as f:
        f.write("trv,Truku,shares trv with Seediq\n")
    (root / "Orthographies" / "ConversionTables"
     / "Seediq_Test_113.tsv").write_text(
        "original\tTegudaya\tTruku\nl\tll\tl\n", encoding="utf-8")
    out = tmp_path / "f.csv"
    proc = _run(root, out)
    assert proc.returncode == 0
    assert not [r for r in _findings(out) if r["rule_id"] == "V152"], (
        f"V152 must accept a language column; got {_findings(out)!r}")


def test_conversion_table_typo_column_still_fires_beside_languages(tmp_path):
    """The widened V152 must not swallow a genuine typo: 'Nanwan' names
    neither a dialect nor a language."""
    root = _mini_repo(tmp_path)
    (root / "Orthographies" / "ConversionTables"
     / "Puyuma_Test_113.tsv").write_text(
        "original\tPuyuma\tNanwan\nl\tl\tll\n", encoding="utf-8")
    out = tmp_path / "f.csv"
    proc = _run(root, out)
    assert proc.returncode == 0
    rows = [r for r in _findings(out) if r["rule_id"] == "V152"]
    assert [r["character"] for r in rows] == ["Nanwan"], (
        f"only the unknown name should fire; got {rows!r}")


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


def test_dialects_language_missing_from_languages_registry_is_soft(tmp_path):
    root = _mini_repo(tmp_path)
    with open(root / "dialects.csv", "a", encoding="utf-8") as f:
        f.write("Atlantean,Deep,深,atla1234,\n")
    out = tmp_path / "f.csv"
    assert _run(root, out).returncode == 0
    rows = _findings(out)
    assert any(r["rule_id"] == "V155" and "Atlantean" in r["message"]
               for r in rows)


def test_languages_csv_duplicate_or_uppercase_code_is_soft(tmp_path):
    root = _mini_repo(tmp_path)
    with open(root / "languages.csv", "a", encoding="utf-8") as f:
        f.write("AMI,Amis,\n")     # uppercase AND duplicate of ami
    out = tmp_path / "f.csv"
    assert _run(root, out).returncode == 0
    v155 = [r for r in _findings(out) if r["rule_id"] == "V155"]
    assert len(v155) >= 2          # not-lowercase + duplicate
