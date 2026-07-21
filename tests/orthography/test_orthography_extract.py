from collections import Counter

from QC.orthography.orthography_extract import visualize


def test_visualize_handles_empty_punctuation_inventory(tmp_path):
    info = {
        "unique_characters": {"a"},
        "character_frequency": Counter({"a": 1}),
        "character_classes": {"Ll": {"a"}},
        "2-grams": Counter({"aa": 1}),
        "punctuation": Counter(),
        "word_frequency": Counter({"a": 1}),
    }

    visualize(info, tmp_path)

    assert (tmp_path / "punctuation_frequencies.png").is_file()
