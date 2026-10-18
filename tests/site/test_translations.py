"""translations: units, the store, imports, and pages built from approved units."""

import json

import pytest

import site_labels
import translations as tr

PAGE = """---
icon: book
---

# Sample corpus

A first sentence about the source. A second one, e.g. with an abbreviation.

## Source

- One list item. It has two sentences.
- A [linked](https://example.com) **bold** item.

| | Amis |
| --- | --- |
| Word count | 1,234 |

```bash
./CodeAndDocs/generate_xml.sh
```

## Reproduction and processing

Run the build script.
"""


def test_units_are_sentences_items_headings_and_cells():
    units = tr.segments(PAGE)
    assert units[:3] == ["Sample corpus", "A first sentence about the source.",
                         "A second one, e.g. with an abbreviation."]
    assert "One list item." in units and "It has two sentences." in units
    assert "A linked bold item." in units  # links and emphasis flattened
    assert "Amis" in units and "Word count" in units
    assert "1,234" not in units  # numbers are not translatable
    assert not any("generate_xml" in u for u in units)  # code is not translatable
    assert "Run the build script." in units


def test_formosan_editions_skip_reproduction_section():
    units = tr.segments(PAGE, skip_reproduction=True)
    assert "Run the build script." not in units
    assert "Reproduction and processing" not in units


def test_labels_are_excluded_from_page_units():
    units = tr.segments(PAGE, exclude={"Word count", "Source"})
    assert "Word count" not in units and "Source" not in units


def test_render_keeps_only_approved_units_and_links_english():
    approved = {"Sample corpus": "樣本語料庫", "A first sentence about the source.": "第一句。",
                "Source": "來源", "One list item.": "一個項目。"}
    out = tr.render_translated_page(PAGE, approved, skip_reproduction=False,
                                    english_url="/FormosanBank/x/", english_title="Sample corpus")
    assert out.startswith("# 樣本語料庫\n\n[Sample corpus](/FormosanBank/x/)")
    assert "第一句。" in out and "A second one" not in out
    assert "## 來源" in out and "- 一個項目。" in out and "It has two sentences." not in out
    assert "./CodeAndDocs/generate_xml.sh" in out  # code kept as written
    assert "| Word count" not in out  # table header not translated: table left out


def test_page_without_approved_title_is_not_built():
    assert tr.render_translated_page(PAGE, {"Source": "來源"}, skip_reproduction=False,
                                     english_url="/x/", english_title="T") is None


def test_approved_map_takes_newest_approved_row():
    rows = [
        {"english": "Hi.", "translation": "old", "approved": "yes", "origin": "mt", "translator": "", "dialect": "", "date": "2026-01-01"},
        {"english": "Hi.", "translation": "new", "approved": "yes", "origin": "human", "translator": "A", "dialect": "", "date": "2026-02-01"},
        {"english": "Hi.", "translation": "draft", "approved": "no", "origin": "human", "translator": "B", "dialect": "", "date": "2026-03-01"},
    ]
    assert tr.approved_map(rows) == {"Hi.": "new"}


def _payload(items, language="pwn", dialect="Eastern"):
    return {"format": tr.PAYLOAD_FORMAT, "language": language, "translator": "Ana",
            "dialect": dialect, "items": items}


def test_import_adds_rows_without_overwriting():
    store = [{"english": "Hi.", "translation": "mt guess", "approved": "no", "origin": "mt",
              "translator": "", "dialect": "", "date": "2026-01-01"}]
    new_store, report = tr.merge_import(store, _payload([
        {"english": "Hi.", "translation": "mt guess", "approved": True},  # approving prior work
        {"english": "Bye.", "translation": "pwn bye", "approved": True},
        {"english": "Old sentence.", "translation": "x", "approved": False},
    ]), {"Hi.", "Bye."}, today="2026-10-19")
    assert report.ok and len(report.new) == 3
    assert store[0]["approved"] == "no"  # original row untouched
    approving = [r for r in new_store if r["english"] == "Hi." and r["approved"] == "yes"][0]
    assert approving["origin"] == "mt" and approving["translator"] == "Ana"
    assert report.unknown == ["Old sentence."]  # kept as data, but listed


def test_import_blocks_cross_dialect_clash_and_changes_nothing():
    store = [{"english": "Hi.", "translation": "eastern", "approved": "yes", "origin": "human",
              "translator": "X", "dialect": "Eastern", "date": "2026-01-01"}]
    new_store, report = tr.merge_import(store, _payload([
        {"english": "Hi.", "translation": "southern", "approved": True}], dialect="Southern"),
        {"Hi."}, today="2026-10-19")
    assert not report.ok and report.blocked
    assert new_store == store


def test_malformed_payload_is_rejected():
    with pytest.raises(ValueError, match="not a FormosanBank translation file"):
        tr.parse_payload(json.dumps({"format": "other"}))
    with pytest.raises(json.JSONDecodeError):
        tr.parse_payload("{not json")


def test_store_round_trip(tmp_path):
    rows = [{"english": "Hi.", "translation": "嗨\tthere", "approved": "yes", "origin": "human",
             "translator": "A", "dialect": "", "date": "2026-10-19"}]
    tr.save_store("zho", rows, tmp_path)
    loaded = tr.load_store("zho", tmp_path)
    assert loaded[0]["translation"] == "嗨 there"  # tabs cannot break the TSV


def test_labels_cover_headings_rows_and_language_names():
    labels = site_labels.labels()
    for label in ("Languages and dialects", "Notes and caveats", "Word count",
                  "Transcribed words", "Glossed words", "Amis", "Truku", "Coastal",
                  site_labels.LANGUAGE_INTRO):
        assert label in labels
    assert len(labels) == len(set(labels))


def test_label_template_with_broken_placeholder_is_unused():
    t = site_labels.translator({site_labels.FIGURE_TITLE: "{langauge} 語料"})
    assert t(site_labels.FIGURE_TITLE, language="Amis") is None
    t = site_labels.translator({site_labels.FIGURE_TITLE: "{language} 字數"})
    assert t(site_labels.FIGURE_TITLE, language="阿美語") == "阿美語 字數"
