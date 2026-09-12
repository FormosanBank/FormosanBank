"""Regression coverage for the 2026 ePark vocabulary-audio host migration.

The provider retired the ilrdc.tw route and moved each file to the Klokah
vocabulary site, changing the category/item separator from an underscore to a
hyphen. These tests cover the deterministic mapping and the real published
inventory because a synthetic fixture cannot prove that all 42 dialect files
were migrated.
"""

import importlib.util
import sys
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "Corpora"
    / "ePark"
    / "CodeAndDocs"
    / "learning_vocabulary_audio_urls.py"
)
SPEC = importlib.util.spec_from_file_location(
    "learning_vocabulary_audio_urls", MODULE_PATH
)
audio_urls = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = audio_urls
SPEC.loader.exec_module(audio_urls)


def test_normalize_retired_url():
    assert audio_urls.normalize_audio_url(
        "https://ilrdc.tw/tow/2022/audio/word/34/07_27.wav"
    ) == "https://web.klokah.tw/vocabulary/audio/word/34/07-27.wav"


def test_normalize_retired_url_preserves_variable_width_ids():
    assert audio_urls.normalize_audio_url(
        "https://ilrdc.tw/tow/2022/audio/word/1/26_105.wav"
    ) == "https://web.klokah.tw/vocabulary/audio/word/1/26-105.wav"


def test_current_and_unrelated_urls_are_unchanged():
    current = "https://web.klokah.tw/vocabulary/audio/word/34/07-27.wav"
    unrelated = "https://web.klokah.tw/other/audio/example.wav"

    assert audio_urls.normalize_audio_url(current) == current
    assert audio_urls.normalize_audio_url(unrelated) == unrelated


def test_malformed_vocabulary_url_is_rejected():
    with pytest.raises(ValueError, match="Unexpected ePark"):
        audio_urls.normalize_audio_url(
            "https://web.klokah.tw/vocabulary/audio/word/34/07_27.wav"
        )


def test_process_xml_file_changes_only_retired_url(tmp_path):
    path = tmp_path / "sample.xml"
    path.write_text(
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        '<TEXT><S id="1"><FORM kindOf="original">pulaw</FORM>'
        '<AUDIO file="sample.wav" '
        'url="https://ilrdc.tw/tow/2022/audio/word/34/07_27.wav"/>'
        "</S></TEXT>\n",
        encoding="utf-8",
    )

    before = path.read_text(encoding="utf-8")
    dry_run = audio_urls.process_xml_file(path, apply_changes=False)
    assert dry_run.legacy_urls == 1
    assert path.read_text(encoding="utf-8") == before

    applied = audio_urls.process_xml_file(path, apply_changes=True)
    assert applied.legacy_urls == 1
    after = path.read_text(encoding="utf-8")
    assert "https://web.klokah.tw/vocabulary/audio/word/34/07-27.wav" in after
    assert "pulaw" in after
    assert "sample.wav" in after

    second_run = audio_urls.process_xml_file(path, apply_changes=True)
    assert second_run.legacy_urls == 0
    assert second_run.current_urls == 1


def test_published_learning_vocabulary_inventory_uses_current_urls(repo_root):
    xml_root = (
        repo_root
        / "Corpora"
        / "ePark"
        / "XML"
        / "xue_xi_ci_biao_learning_vocabulary"
    )

    report = audio_urls.process_xml_root(xml_root, apply_changes=False)

    assert report.audio_elements > 0
    assert report.legacy_urls == 0
    assert report.current_urls == report.audio_elements
