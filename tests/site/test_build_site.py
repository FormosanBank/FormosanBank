"""build_site: the site lands where asked, and an empty site fails the build."""

import pytest

import build_site


def test_empty_or_missing_site_fails(tmp_path):
    with pytest.raises(SystemExit, match="no HTML pages"):
        build_site.count_pages(tmp_path / "missing")
    (tmp_path / "empty").mkdir()
    with pytest.raises(SystemExit, match="no HTML pages"):
        build_site.count_pages(tmp_path / "empty")


def test_pages_are_counted(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "index.html").write_text("<html></html>")
    (tmp_path / "a" / "index.html").write_text("<html></html>")
    assert build_site.count_pages(tmp_path) == 2
