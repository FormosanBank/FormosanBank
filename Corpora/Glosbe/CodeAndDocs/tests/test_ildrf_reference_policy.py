from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from scripts.glosbe_pipeline import (
    PROCESSED,
    ROOT,
    dedupe_key,
    form_group_key,
    lexical_form_text_for_xml,
    lexical_reference_decisions,
    load_config,
    load_ildrf_reference_lexicon,
    repo_path,
)


def config_with_reference_or_skip():
    config = load_config("scripts/config.yaml")
    reference_repo = repo_path(config["ildrf_reference_lexicon"]["derived_repo"])
    if not reference_repo.is_dir():
        pytest.skip("ILRDF-derived reference repository is not available")
    return config


def test_published_config_targets_standard_xml_directory():
    config = load_config("scripts/config.yaml")

    assert config["xml"]["output_dir"] == "../XML"
    assert (ROOT / config["xml"]["output_dir"]).resolve() == (Path(ROOT).parent / "XML").resolve()


def test_reference_files_are_explicit_and_truku_only_for_trv():
    reference = load_ildrf_reference_lexicon(config_with_reference_or_skip())

    assert {row["language"] for row in reference.file_stats} == {"ami", "tay", "trv", "xsy"}
    assert next(row for row in reference.file_stats if row["language"] == "trv")["file"] == (
        "Final_XML/Truku/Dictionary_Truku_trv.xml"
    )
    assert dedupe_key("yako") not in reference.glosses["trv"]
    assert all(
        "Seediq" not in path
        for paths in reference.source_files["trv"].values()
        for path in paths
    )


def test_lexical_form_normalization_matches_qc_apostrophe_cleanup():
    assert lexical_form_text_for_xml(" nga ˈ ay ") == "nga'ay"
    assert lexical_form_text_for_xml("kapaymae’iyaehan") == "kapaymae'iyaehan"


def test_reference_comparison_never_excludes_structurally_valid_rows():
    if not (PROCESSED / "dictionary_entries_deduped.jsonl").is_file():
        pytest.skip("development dictionary sidecar is not included in the public corpus")
    groups, audit, rejected, review, _ = lexical_reference_decisions(
        config_with_reference_or_skip()
    )

    assert len(audit) == 1305
    assert len(groups) == len(review) == 1156
    assert {row["action"] for row in audit} == {"keep_in_xml"}
    assert Counter(row["reference_status"] for row in audit) == {
        "source_not_attested": 529,
        "gloss_unmapped": 528,
        "target_supported_by_mapping": 209,
        "different_from_mapping": 39,
    }
    assert Counter(row["rejection_reason"] for row in rejected) == {
        "target_cross_reference_or_invalid_note": 12,
        "source_numeric_or_punct_only": 1,
        "identical_source_target": 1,
    }


def test_lexical_xml_preserves_distinct_targets_as_alternates():
    lexical_files = sorted((Path(ROOT).parent / "XML").glob("*/Glosbe_*_lexical.xml"))
    sentences = []
    translations = []
    for path in lexical_files:
        root = ET.parse(path).getroot()
        sentences.extend(root.findall("S"))
        translations.extend(root.findall(".//TRANSL"))

    assert len(lexical_files) == 4
    assert len(sentences) == 1156
    assert len(translations) == 1305
    assert Counter(translation.get("ver", "primary") for translation in translations) == {
        "primary": 1156,
        "alt": 149,
    }
    for sentence in sentences:
        same_language = sentence.findall("TRANSL")
        assert all(
            translation.get("ver") == "alt"
            for translation in same_language[1:]
        )

    apostrophe_group = [
        sentence
        for sentence in sentences
        if form_group_key(sentence.findtext("FORM", default="")) == "kapaymae'iyaehan"
    ]
    assert len(apostrophe_group) == 1
    assert {translation.text for translation in apostrophe_group[0].findall("TRANSL")} == {
        "crosswalk",
        "pedestrian crossing",
    }


def test_missing_reference_repository_aborts(tmp_path):
    config = load_config("scripts/config.yaml")
    config["ildrf_reference_lexicon"]["derived_repo"] = str(tmp_path / "missing")

    with pytest.raises(FileNotFoundError):
        load_ildrf_reference_lexicon(config)
