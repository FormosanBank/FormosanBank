"""check_site: the link checker that gates every deploy."""

from pathlib import Path

import pytest

import check_site


def _page(path: Path, body: str = "<h1>T</h1>") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'<html lang="en">{body}</html>', encoding="utf-8")
    return path


def test_relative_link_resolves_within_the_site(tmp_path):
    source = _page(tmp_path / "guide" / "index.html")
    target, _ = check_site.resolve_target(tmp_path, source, "../index.html")
    assert target == tmp_path / "index.html"


def test_absolute_link_with_project_base_resolves(tmp_path):
    source = _page(tmp_path / "index.html")
    target, _ = check_site.resolve_target(tmp_path, source, "/FormosanBank/zh/")
    assert target == tmp_path / "zh" / "index.html"
    target, _ = check_site.resolve_target(
        tmp_path, source, "https://formosanbank.github.io/FormosanBank/zh/"
    )
    assert target == tmp_path / "zh" / "index.html"


def test_absolute_link_outside_project_base_is_invalid(tmp_path):
    source = _page(tmp_path / "index.html")
    with pytest.raises(ValueError, match="outside"):
        check_site.resolve_target(tmp_path, source, "/zh/")


def test_external_link_is_reported_as_external(tmp_path):
    source = _page(tmp_path / "index.html")
    with pytest.raises(ValueError, match="external"):
        check_site.resolve_target(tmp_path, source, "https://example.com/x")


def test_check_site_reports_broken_link_and_two_h1(tmp_path):
    _page(tmp_path / "index.html", '<h1>A</h1><h1>B</h1><a href="missing/">x</a>')
    errors = check_site.check_site(tmp_path)
    assert any("expected one h1, found 2" in e for e in errors)
    assert any("missing target" in e for e in errors)


def test_parse_page_collects_duplicate_ids(tmp_path):
    page = tmp_path / "p.html"
    page.write_text('<html lang="en"><h1>A</h1><div id="x"></div><div id="x"></div></html>', encoding="utf-8")
    parsed = check_site.parse_page(page)
    assert parsed.duplicate_ids == {"x"} and parsed.h1_count == 1 and parsed.language == "en"
