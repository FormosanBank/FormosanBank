"""translated_editions: editions built from approved translations only."""

import json
from pathlib import Path

import site_labels
import translated_editions as te
import translations as tr

EN_SUMMARY = """# Table of contents

* [Welcome](README.md)
* [Corpora](corpora/README.md)
  * [Sample](corpora/sample.md)
"""
HOME = "# Welcome\n\nWelcome to FormosanBank. It holds many languages.\n"
SAMPLE = "# Sample\n\nOne sentence.\n\n## Reproduction and processing\n\nRun it.\n"


def _english(tmp_path: Path) -> Path:
    en = tmp_path / "en"
    (en / "corpora").mkdir(parents=True)
    (en / "SUMMARY.md").write_text(EN_SUMMARY, encoding="utf-8")
    (en / "README.md").write_text(HOME, encoding="utf-8")
    (en / "corpora" / "README.md").write_text("# Corpora\n\nAll of them.\n", encoding="utf-8")
    (en / "corpora" / "sample.md").write_text(SAMPLE, encoding="utf-8")
    return en


def test_no_approved_translations_builds_nothing(tmp_path):
    en = _english(tmp_path)
    ed = tmp_path / "amis"
    ed.mkdir()
    built = te.build_edition(en, ed, tr.TARGETS_BY_CODE["ami"], {}, {}, [])
    assert built == [] and not (ed / "README.md").exists()


def test_formosan_edition_gets_home_page_and_skips_reproduction(tmp_path):
    en = _english(tmp_path)
    ed = tmp_path / "amis"
    ed.mkdir()
    approved = {"Welcome": "AMIS-HOME", "Welcome to FormosanBank.": "AMIS-1", "Sample": "AMIS-T",
                "One sentence.": "AMIS-2", "Run it.": "AMIS-3"}
    built = te.build_edition(en, ed, tr.TARGETS_BY_CODE["ami"], approved, {}, [])
    assert sorted(built) == ["README.md", "corpora/sample.md"]
    home = (ed / "README.md").read_text(encoding="utf-8")
    assert home.startswith("# AMIS-HOME") and "AMIS-1" in home and "It holds many languages." not in home
    sample = (ed / "corpora" / "sample.md").read_text(encoding="utf-8")
    assert "AMIS-2" in sample and "AMIS-3" not in sample  # Reproduction section not translated
    summary = (ed / "SUMMARY.md").read_text(encoding="utf-8")
    assert "* [AMIS-HOME](README.md)" in summary and "corpora/README.md" not in summary


def test_replacement_is_written_at_the_legacy_path(tmp_path):
    en = _english(tmp_path)
    ed = tmp_path / "zh"
    (ed / "bei-jing").mkdir(parents=True)
    (ed / "SUMMARY.md").write_text("* [舊](bei-jing/old.md)\n", encoding="utf-8")
    (ed / "bei-jing" / "old.md").write_text("# 舊頁面\n", encoding="utf-8")
    approved = {"Sample": "樣本", "One sentence.": "一句。"}
    te.build_edition(en, ed, tr.TARGETS_BY_CODE["zho"], approved, {"corpora/sample.md": "bei-jing/old.md"}, [])
    assert (ed / "bei-jing" / "old.md").read_text(encoding="utf-8").startswith("# 樣本")
    assert "* [樣本](bei-jing/old.md)" in (ed / "SUMMARY.md").read_text(encoding="utf-8")


def test_templates_expand_with_translated_language_name():
    unit = site_labels.LANGUAGE_INTRO.format(words="1,000", language="Amis", count="3")
    approved = {site_labels.LANGUAGE_INTRO: "{language} 有 {words} 字，{count} 個語料庫。", "Amis": "阿美語"}
    assert te.expand_templates([unit], approved) == {unit: "阿美語 有 1,000 字，3 個語料庫。"}
    assert te.expand_templates([unit], {site_labels.LANGUAGE_INTRO: "x {language}"}) == {}


def test_tool_data_lists_pages_existing_and_mandarin_help(tmp_path):
    en = _english(tmp_path)
    store = [{"english": "One sentence.", "translation": "draft", "approved": "no", "origin": "mt",
              "translator": "", "dialect": "", "date": "2026-10-18"}]
    mandarin = [{"english": "One sentence.", "translation": "一句。", "approved": "yes", "origin": "human",
                 "translator": "A", "dialect": "", "date": "2026-10-18"}]
    data = te.tool_data(en, tr.TARGETS_BY_CODE["pwn"], store, mandarin)
    sample = [p for p in data["pages"] if p["id"] == "corpora/sample.md"][0]
    assert sample["units"] == ["Sample", "One sentence."]  # Reproduction section left out
    assert data["existing"]["One sentence."] == {"translation": "draft", "approved": False, "origin": "mt", "dialect": ""}
    assert data["mandarin"] == {"One sentence.": "一句。"}
    assert data["format"] == tr.PAYLOAD_FORMAT
    json.dumps(data)  # serialisable
