"""check_pending_lists.py: a corpus whose XML changes may not stay on a pending list."""
import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("cpl", REPO / "QC" / "validation" / "check_pending_lists.py")
cpl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cpl)


def test_corpora_of_reads_only_published_xml_paths():
    assert cpl.corpora_of([
        "Corpora/ePark/XML/Amis/a.xml",
        "Corpora/ePark/CodeAndDocs/snapshot/XML/x.xml",   # not published XML/
        "Corpora/Glosbe/README.md",
        "QC/validation/validate_xml.py",
        "Corpora/NTUFormosanCorpus/XML/Stories/Amis/s.xml",
    ]) == {"ePark", "NTUFormosanCorpus"}


def _root(tmp_path: Path) -> Path:
    (tmp_path / "generate_xml_pending.txt").write_text("# comment\nePark\nGlosbe\n", encoding="utf-8")
    (tmp_path / "readme_sections_pending.txt").write_text("ePark notes\nRauDong rights\n", encoding="utf-8")
    return tmp_path


def test_sheltered_names_every_list_a_changed_corpus_sits_on(tmp_path):
    root = _root(tmp_path)
    assert cpl.sheltered({"ePark", "RauDong", "SEALS33"}, root) == [
        ("ePark", "generate_xml_pending.txt"),
        ("ePark", "readme_sections_pending.txt"),
        ("RauDong", "readme_sections_pending.txt"),
    ]
    assert cpl.sheltered({"SEALS33"}, root) == []


def test_cli_exits_one_with_an_error_line_per_hit(tmp_path, capsys):
    root = _root(tmp_path)
    changed = tmp_path / "changed.txt"
    changed.write_text("Corpora/ePark/XML/Amis/a.xml\nCorpora/SEALS33/XML/b.xml\n", encoding="utf-8")
    assert cpl.main(["--changed", str(changed), "--repo-root", str(root)]) == 1
    out = capsys.readouterr().out
    assert "::error::ePark changes XML/ in this PR but is still listed in generate_xml_pending.txt" in out
    assert "::error::ePark changes XML/ in this PR but is still listed in readme_sections_pending.txt" in out
    assert "SEALS33" not in [l.split("::error::")[-1].split()[0] for l in out.splitlines() if "::error::" in l]
    changed.write_text("Corpora/SEALS33/XML/b.xml\n", encoding="utf-8")
    assert cpl.main(["--changed", str(changed), "--repo-root", str(root)]) == 0
