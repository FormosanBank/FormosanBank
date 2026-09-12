"""--warnings_dir keeps the per-run cleaner report out of published XML/ (POL-033).

The default is unchanged, so every existing caller keeps writing beside
--corpora_path; HundredPaiwanStories' build still finds the file where it
moves it from.
"""
from pathlib import Path

import pytest

from QC.cleaning.clean_xml import _warnings_path


def test_default_is_corpora_path(tmp_path):
    xml_dir = tmp_path / "XML"
    xml_dir.mkdir()
    assert _warnings_path(xml_dir, None) == xml_dir / "cleaner_warnings.csv"


def test_warnings_dir_redirects_out_of_the_published_tree(tmp_path):
    xml_dir = tmp_path / "XML"
    xml_dir.mkdir()
    code_dir = tmp_path / "CodeAndDocs"
    got = _warnings_path(xml_dir, code_dir)
    assert got == code_dir / "cleaner_warnings.csv"
    assert xml_dir not in got.parents


def test_warnings_dir_is_created_when_absent(tmp_path):
    target = tmp_path / "CodeAndDocs" / "reports"
    assert not target.exists()
    _warnings_path(tmp_path, target)
    assert target.is_dir()


@pytest.mark.parametrize("empty", ["", None])
def test_falsy_warnings_dir_falls_back_to_the_default(tmp_path, empty):
    assert _warnings_path(tmp_path, empty) == tmp_path / "cleaner_warnings.csv"
