"""language_pages: per-language pages and the tall, log-scale growth figures."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import language_pages as lp
import prepare_site
import site_stats

HISTORY = [
    # commit 1: Amis only
    {"date": "2025-01-01T00:00:00+00:00", "commit": "c1", "corpus": "A", "language": "Amis", "dialect": "Coastal",
     "words": "100", "transcribed_words": "40", "segmented_words": "0", "glossed_words": "0",
     "zho_transl_count": "100", "eng_transl_count": "0"},
    # commit 2: Amis grows, Wikipedias adds Amis, Thao appears
    {"date": "2025-06-01T00:00:00+00:00", "commit": "c2", "corpus": "A", "language": "Amis", "dialect": "Coastal",
     "words": "150", "transcribed_words": "40", "segmented_words": "10", "glossed_words": "10",
     "zho_transl_count": "150", "eng_transl_count": "0"},
    {"date": "2025-06-01T00:00:00+00:00", "commit": "c2", "corpus": "Wikipedias", "language": "Amis", "dialect": "unknown",
     "words": "1000", "transcribed_words": "0", "segmented_words": "0", "glossed_words": "0",
     "zho_transl_count": "0", "eng_transl_count": "0"},
    {"date": "2025-06-01T00:00:00+00:00", "commit": "c2", "corpus": "B", "language": "Thao", "dialect": "unknown",
     "words": "7", "transcribed_words": "0", "segmented_words": "0", "glossed_words": "0",
     "zho_transl_count": "0", "eng_transl_count": "0"},
]


def test_growth_series_language_and_exclusion():
    amis = lp.growth_series(HISTORY, language="Amis")
    assert [p.values["words"] for p in amis][:2] == [100, 1150]
    thao = lp.growth_series(HISTORY, language="Thao")
    assert [p.values["words"] for p in thao][:2] == [0, 7]  # absent at c1 counts zero
    no_wiki = lp.growth_series(HISTORY, exclude_corpora=frozenset({"Wikipedias"}))
    assert [p.values["words"] for p in no_wiki][:2] == [100, 157]


def test_growth_series_extends_last_state_to_today():
    series = lp.growth_series(HISTORY)
    assert series[-1].values == series[-2].values
    assert series[-1].date > series[-2].date


def _plot_area(svg: str) -> tuple[float, float]:
    root = ET.fromstring(svg)
    ns = {"s": "http://www.w3.org/2000/svg"}
    # matplotlib writes the axes background as the first path in <g id="patch_2">
    patch = root.find(".//s:g[@id='patch_2']/s:path", ns)
    numbers = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", patch.get("d"))]
    xs, ys = numbers[0::2], numbers[1::2]
    return max(xs) - min(xs), max(ys) - min(ys)


def test_figure_plot_area_is_twice_as_tall_as_wide_and_log_scaled():
    svg = lp.render_growth_svg(lp.growth_series(HISTORY, language="Amis"), "Amis: words over time")
    width, height = _plot_area(svg)
    assert height / width == pytest.approx(2.0, rel=0.01)
    for label in ("Total words", "Transcribed words", "Segmented words", "Glossed words"):
        assert label in svg
    # log axis: matplotlib labels decade ticks 10^1, 10^2, 10^3
    assert "<!-- $\\mathdefault{10^{2}}$ -->" in svg and "<!-- $\\mathdefault{10^{3}}$ -->" in svg


def test_figure_survives_all_zero_series():
    svg = lp.render_growth_svg(lp.growth_series(HISTORY, language="Kavalan"), "Kavalan")
    assert svg.startswith("<?xml")



@pytest.fixture
def rows():
    return site_stats.load_stats(Path(__file__).parent / "fixtures" / "statistics")


def test_language_page_sections_and_links(rows):
    pages = [prepare_site.CorpusPage("Mini", "mini", "Mini corpus", "", "", "")]
    multi = {"Amis", "Seediq", "Babuza-Favorlang"}
    text = lp.language_page("Amis", rows, HISTORY, pages, "amis-growth.svg", multi)
    assert text.startswith("# Amis\n")
    assert "FormosanBank holds 350 words of Amis, in 1 corpus." in text
    assert "## Dialects" in text and "| | Coastal | unknown |" in text
    assert "* [Mini corpus](../the-bank-architecture/corpora/mini.md): 350 words" in text
    assert "](figures/amis-growth.svg)" in text
    yami = lp.language_page("Yami", rows, HISTORY, pages, "yami-growth.svg", multi)
    assert "## Dialects" not in yami


def test_languages_nav_inserted_before_corpora():
    summary = "* Arch\n  * [Corpora](the-bank-architecture/corpora/README.md)\n    * [A](x.md)\n"
    out = lp.languages_nav(summary, ["Amis", "Thao"])
    assert out.index("[Languages](languages/README.md)") < out.index("[Corpora]")
    assert "    * [Amis](languages/amis.md)" in out


def test_real_stats_give_one_page_per_language(tmp_path):
    root = Path(prepare_site.__file__).resolve().parents[2]
    rows = site_stats.load_stats(root / "statistics")
    names = lp.write_language_pages(tmp_path, rows, [], prepare_site.load_corpus_pages(root))
    assert len(names) == len({r["language_name"] for r in rows if r["word_count"]})
    assert {"Amis", "Truku", "Seediq", "Babuza-Favorlang"} <= set(names)
    for name in names:
        assert (tmp_path / "languages" / f"{lp.language_slug(name)}.md").is_file()
        assert (tmp_path / "languages" / "figures" / f"{lp.language_slug(name)}-growth.svg").is_file()


def test_every_generated_sentence_matches_a_label_template(rows):
    # Found live 2026-10-19: the page said "in 12 corpuses" while the label
    # said "corpora", so a translated template could never apply.
    import site_labels
    import translated_editions as te
    import translations as tr
    pages = [prepare_site.CorpusPage("Mini", "mini", "Mini corpus", "", "", "")]
    multi = {"Amis", "Seediq", "Babuza-Favorlang"}
    for language in ("Amis", "Yami"):
        text = lp.language_page(language, rows, HISTORY, pages, "x.svg", multi)
        assert "corpuses" not in text
        units = [u for u in tr.segments(text) if u not in site_labels.labels()]
        approved = {label: "T" + label for label in site_labels.labels()}
        expanded = te.expand_templates(units, approved)
        leftover = [u for u in units if u not in expanded and u != language]
        assert leftover == [], leftover
