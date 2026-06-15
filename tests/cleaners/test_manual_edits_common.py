"""Unit tests for QC/cleaning/manual_edits_common.py (pure helpers)."""
import subprocess
import sys
from pathlib import Path

from lxml import etree

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from QC.cleaning import manual_edits_common as mec


def _s(xml: str) -> etree._Element:
    return etree.fromstring(xml)


def test_strip_s_removes_standard_forms_at_all_levels():
    s = _s(
        '<S id="x">'
        '<FORM kindOf="original">a</FORM>'
        '<FORM kindOf="standard">A</FORM>'
        '<W id="x1"><FORM kindOf="original">a</FORM>'
        '<FORM kindOf="standard">A</FORM></W>'
        "</S>"
    )
    out = mec.strip_s(s)
    kinds = [f.get("kindOf") for f in out.findall(".//FORM")]
    assert kinds == ["original", "original"]


def test_strip_s_removes_all_phon():
    s = _s(
        '<S id="x"><FORM kindOf="original">a</FORM>'
        '<PHON kindOf="original">a</PHON>'
        '<W id="x1"><PHON kindOf="original">a</PHON></W></S>'
    )
    out = mec.strip_s(s)
    assert out.findall(".//PHON") == []


def test_strip_s_drops_after_and_action_attrs():
    s = _s('<S id="x" after="w" action="delete"><FORM kindOf="original">a</FORM></S>')
    out = mec.strip_s(s)
    assert "after" not in out.attrib
    assert "action" not in out.attrib


def test_strip_s_does_not_mutate_input():
    s = _s('<S id="x"><FORM kindOf="standard">A</FORM></S>')
    mec.strip_s(s)
    assert s.findall(".//FORM") != []  # original element untouched


def test_canonical_s_ignores_standard_phon_and_whitespace():
    a = _s('<S id="x">\n  <FORM kindOf="original">a</FORM>\n</S>')
    b = _s(
        '<S id="x"><FORM kindOf="original">a</FORM>'
        '<FORM kindOf="standard">A</FORM><PHON kindOf="original">a</PHON></S>'
    )
    assert mec.canonical_s(a) == mec.canonical_s(b)


def test_canonical_s_distinguishes_different_original_text():
    a = _s('<S id="x"><FORM kindOf="original">a</FORM></S>')
    b = _s('<S id="x"><FORM kindOf="original">b</FORM></S>')
    assert mec.canonical_s(a) != mec.canonical_s(b)


def test_render_s_shows_original_form_and_translations():
    s = _s(
        '<S id="x"><FORM kindOf="original">hala</FORM>'
        '<TRANSL xml:lang="zho">你好</TRANSL></S>'
    )
    out = mec.render_s(s)
    assert "hala" in out and "你好" in out


def test_default_manual_file_is_codeanddocs_sibling(tmp_path):
    xml_dir = tmp_path / "XML"
    xml_dir.mkdir()
    got = mec.default_manual_file(xml_dir)
    assert got == (tmp_path / "CodeAndDocs" / "manual_edits.xml")


def test_changelog_path_swaps_suffix(tmp_path):
    assert mec.changelog_path(tmp_path / "CodeAndDocs" / "manual_edits.xml") == (
        tmp_path / "CodeAndDocs" / "manual_edits.md"
    )


def test_render_s_falls_back_to_bare_form_when_no_original():
    s = _s('<S id="x"><FORM>bare</FORM></S>')
    assert "bare" in mec.render_s(s)


def test_manual_root_roundtrip_and_groups(tmp_path):
    root = mec.new_manual_root()
    fg = mec.get_or_create_file_group(root, "Amis/a.xml")
    fg.append(_s('<S id="S1"><FORM kindOf="original">a</FORM></S>'))
    path = tmp_path / "CodeAndDocs" / "manual_edits.xml"
    mec.write_manual(root, path)
    assert path.exists()
    back = mec.load_manual(path)
    assert mec.find_file_group(back, "Amis/a.xml") is not None
    assert mec.find_file_group(back, "nope.xml") is None


def test_load_manual_missing_returns_none(tmp_path):
    assert mec.load_manual(tmp_path / "absent.xml") is None


def test_upsert_record_replaces_by_id():
    root = mec.new_manual_root()
    fg = mec.get_or_create_file_group(root, "a.xml")
    mec.upsert_record(fg, _s('<S id="S1"><FORM kindOf="original">old</FORM></S>'))
    mec.upsert_record(fg, _s('<S id="S1"><FORM kindOf="original">new</FORM></S>'))
    ss = fg.findall("S")
    assert len(ss) == 1
    assert ss[0].find("FORM").text == "new"


def test_upsert_record_appends_new_id_in_order():
    root = mec.new_manual_root()
    fg = mec.get_or_create_file_group(root, "a.xml")
    mec.upsert_record(fg, _s('<S id="S1"/>'))
    mec.upsert_record(fg, _s('<S id="S2"/>'))
    assert [s.get("id") for s in fg.findall("S")] == ["S1", "S2"]


def test_write_manual_drops_empty_file_groups(tmp_path):
    root = mec.new_manual_root()
    mec.get_or_create_file_group(root, "empty.xml")  # no <S>
    fg = mec.get_or_create_file_group(root, "a.xml")
    fg.append(_s('<S id="S1"/>'))
    path = tmp_path / "m.xml"
    mec.write_manual(root, path)
    back = mec.load_manual(path)
    assert mec.find_file_group(back, "empty.xml") is None
    assert mec.find_file_group(back, "a.xml") is not None


def test_git_root_and_show(tmp_path):
    repo = tmp_path
    (repo / "f.txt").write_text("v1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    subprocess.run(["git", "add", "f.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "c1"], cwd=repo, check=True)
    (repo / "f.txt").write_text("v2\n", encoding="utf-8")  # uncommitted
    assert mec.git_root(repo).resolve() == repo.resolve()
    assert mec.git_show(repo, "HEAD", "f.txt") == b"v1\n"
    assert mec.git_show(repo, "HEAD", "missing.txt") is None


def test_git_root_outside_repo_returns_none(tmp_path):
    # tmp_path here has no git repo initialized
    assert mec.git_root(tmp_path) is None


def test_remove_record_by_id():
    root = mec.new_manual_root()
    fg = mec.get_or_create_file_group(root, "a.xml")
    mec.upsert_record(fg, _s('<S id="S1"/>'))
    assert mec.remove_record(fg, "S1") is True
    assert mec.remove_record(fg, "MISSING") is False
    assert fg.findall("S") == []


def test_git_ref_exists(tmp_path):
    repo = tmp_path
    (repo / "f.txt").write_text("v1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    subprocess.run(["git", "add", "f.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "c1"], cwd=repo, check=True)
    assert mec.git_ref_exists(repo, "HEAD") is True
    assert mec.git_ref_exists(repo, "NOPE") is False
