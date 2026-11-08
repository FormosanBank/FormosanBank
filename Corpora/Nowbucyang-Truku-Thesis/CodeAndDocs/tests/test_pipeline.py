"""Source-column regressions from Hsu 2008; PDF page numbers include front matter."""

import sys
import json
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import pipeline  # noqa: E402


def sentence(form, gloss):
    element = ET.Element("S", {"id": "example"})
    pipeline._add_words_and_glosses(
        element, "example", form, form, form, {"gloss_line_clean": gloss}, "zho", gloss
    )
    pipeline._add_word_level_translations(element, "zho")
    return element


def morphemes(word):
    return [(m.findtext("FORM[@kindOf='original']"), m.findtext("TRANSL")) for m in word.findall("M")]


def test_page_75_infix_belongs_to_work_not_the_preceding_noun():
    s = sentence("G-m-bhngil mniq q-m-pah-an ka Lowking.", "g-AF-芒草 在 工作<AF>-LF 主格 人名")
    w = s.findall("W")
    assert morphemes(w[0]) == [("G", "g"), ("m", "AF"), ("bhngil", "芒草")]
    assert morphemes(w[1]) == [("mniq", "在")]
    assert morphemes(w[2]) == [("q-pah", "工作"), ("-m-", "AF"), ("an", "LF")]
    assert w[2].findtext("FORM[@kindOf='original']") == "q<m>pah-an"
    assert w[2].findtext("TRANSL") == "工作<AF>-LF"
    assert [m.get("id") for m in w[2].findall("M")] == ["exampleW3M1", "exampleW3M2", "exampleW3M4"]


def test_page_76_clitics_and_inconsistent_source_angle_notation():
    s = sentence("K-m-elug =ku minq q-m-pah-an =mu.", "k-<AF>路-我 在 工作<AF>-LF-我")
    w = s.findall("W")
    assert morphemes(w[0]) == [("K", "k"), ("m", "AF"), ("elug", "路")]
    assert w[0].findtext("FORM[@kindOf='original']") == "K-m-elug"
    assert w[0].findtext("TRANSL") == "k-<AF>路"
    assert morphemes(w[1]) == [("=ku", "我")]
    assert morphemes(w[2]) == [("minq", "在")]
    assert morphemes(w[3]) == [("q-pah", "工作"), ("-m-", "AF"), ("an", "LF")]
    assert morphemes(w[4]) == [("=mu", "我")]


def test_balanced_sentence_totals_do_not_allow_cross_word_gloss_shifts():
    s = sentence("a-b c", "X Y-Z")
    assert len(s.findall(".//M")) == 3
    assert not s.findall(".//M/TRANSL")
    assert [w.findtext("TRANSL") for w in s.findall("W")] == ["X", "Y-Z"]
    assert not pipeline._morphemes_align("a-b c", "X Y-Z")


def test_page_138_unsplit_name_gloss_does_not_erase_other_word_glosses():
    s = sentence("M-latat paah ptas-an tg-paru Tung-Xuwa ka Lowking.", "AF-出去 從 書寫-LF tg-大 東華 主格 人名")
    words = s.findall("W")
    assert morphemes(words[0]) == [("M", "AF"), ("latat", "出去")]
    assert words[4].findtext("TRANSL") == "東華"
    assert morphemes(words[4]) == [("Tung", None), ("Xuwa", None)]
    assert words[6].findtext("TRANSL") == "人名"


def test_page_126_partial_analysis_preserves_clitic_and_other_word_glosses():
    s = sentence("B-n-arig =ku kingal qrqur.", "買-n-我 一 鑽洞機")
    words = s.findall("W")
    assert words[0].findtext("TRANSL") == "買-n"
    assert not words[0].findall("M/TRANSL")
    assert morphemes(words[1]) == [("=ku", "我")]
    assert morphemes(words[2]) == [("kingal", "一")]
    assert morphemes(words[3]) == [("qrqur", "鑽洞機")]


def test_missing_source_gloss_keeps_segmented_morphemes():
    s = sentence("M-kan=ku", "")
    assert morphemes(s.find("W")) == [("M", None), ("kan", None), ("=ku", None)]


def test_infix_gloss_precedes_suffix_in_manual_word_reconstruction():
    assert pipeline._reconstruct_word_gloss(["q-pah", "-m-", "an"], ["工作", "AF", "LF"]) == "工作<AF>-LF"


def test_canonical_notation_must_preserve_source_letters():
    with pytest.raises(ValueError, match="changes source letters"):
        pipeline._canonical_infix_word("s-m-alu", ["s-alo", "-m-"])


def test_source_angle_notation_alone_does_not_collapse_a_prefix():
    s = sentence("T-m-pucing", "t-<AF>-番刀")
    assert morphemes(s.find("W")) == [("T", "t"), ("m", "AF"), ("pucing", "番刀")]
    assert s.findtext("W/TRANSL") == "t-<AF>-番刀"


def test_source_hashes_are_available_without_private_pdfs():
    cfg = pipeline.load_config(Path(__file__).resolve().parents[1] / "scripts/config.yaml")
    original, decrypted = pipeline._source_pdf_hashes(cfg)
    assert original == "4778f3a756a9b9c450777dbc1c775f9eb38587845683b5315a723e029a249749"
    assert len(decrypted) == 64


def test_manual_source_gloss_cannot_override_a_prior_correction():
    s = sentence("T-m-kacing", "t-AF-牛")
    word = s.find("W")
    word.remove(word.find("TRANSL"))
    pipeline._add_manual_source_word_glosses(s, "t-<AF>-牛")
    assert word.findtext("TRANSL") == "t-<AF>-牛"
    word.remove(word.find("TRANSL"))
    pipeline._add_manual_source_word_glosses(s, "t-<AF>-羊")
    assert word.find("TRANSL") is None
    word.append(ET.fromstring('<TRANSL xml:lang="zho">reviewed reading</TRANSL>'))
    pipeline._add_manual_source_word_glosses(s, "t-<AF>-牛")
    assert word.findtext("TRANSL") == "reviewed reading"


def test_page_95_unlabelled_second_example_uses_its_own_source_id():
    rows = pipeline.read_jsonl(pipeline.ROOT / "data/processed/examples_clean.jsonl")
    before = [r["example_record_id"] for r in rows]
    additions = pipeline._reviewed_source_additions(rows)
    assert [r["example_record_id"] for r in rows] == before
    assert len(additions) == 7
    row = next(r for r in additions if r["sentence_id"].endswith("C03_E036B_P095"))
    assert row["truku_line_clean"] == "Tama Lowking ka emp-txiluy nii."
    assert row["gloss_line_clean"] == "爸爸 人名 主格 emp-打鐵 這"
    assert row["chinese_translation_clean"] == "這個鐵匠是 Lowking 的爸爸。"
    assert pipeline._sentence_id(row, 1).endswith("C03_E036B_P095")
    assert pipeline._sentence_id(row, 999) == pipeline._sentence_id(row, 1)
    assert pipeline._sentence_id(row, 1, "b").endswith("C03_E036B_P095-opt")


def test_changed_source_block_requires_review_before_recovery(tmp_path, monkeypatch):
    rows = pipeline.read_jsonl(pipeline.ROOT / "data/processed/examples_clean.jsonl")
    raw = pipeline.read_jsonl(pipeline.ROOT / "data/processed/examples_raw.jsonl")
    parent = next(r for r in raw if r["example_record_id"].endswith("RAW_0244"))
    parent["raw_text_combined"] = parent["raw_text_combined"].replace("Tama Lowking", "Tama Tusi")
    manual = tmp_path / "data/manual"
    processed = tmp_path / "data/processed"
    manual.mkdir(parents=True)
    processed.mkdir(parents=True)
    shutil.copy2(pipeline.ROOT / "data/manual/source_additions.csv", manual)
    (processed / "examples_raw.jsonl").write_text(json.dumps(parent) + "\n")
    monkeypatch.setattr(pipeline, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="Source lines changed"):
        pipeline._reviewed_source_additions(rows)
    (manual / "source_additions.csv").unlink()
    with pytest.raises(FileNotFoundError, match="required source-addition"):
        pipeline._reviewed_source_additions(rows)


def test_source_examples_without_free_translations_remain_untranslated():
    rows = pipeline.read_jsonl(pipeline.ROOT / "data/processed/examples_clean.jsonl")
    additions = pipeline._reviewed_source_additions(rows)
    for suffix in ["C01_E019A_P037", "C01_E020A_P038", "C03_E011B_P079"]:
        row = next(r for r in additions if r["sentence_id"].endswith(suffix))
        assert row["chinese_translation_clean"] == ""
        assert row["gloss_line_clean"]
        s = sentence(row["truku_line_clean"], row["gloss_line_clean"])
        pipeline._add_translations(s, row["chinese_translation_clean"], "zho")
        assert s.find("TRANSL") is None
        assert s.findall(".//W/TRANSL")


def test_page_37_literal_nominalization_reading_stays_separate():
    s = ET.Element("S")
    pipeline._add_translations(s, "飲料 (喝的東西)", "zho", "literal")
    assert [(t.text, t.get("ver")) for t in s.findall("TRANSL")] == [("飲料", None), ("喝的東西", "alt")]
