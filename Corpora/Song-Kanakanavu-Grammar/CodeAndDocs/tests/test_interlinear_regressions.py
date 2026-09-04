from __future__ import annotations

import csv
import re
import sys
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
XML_ROOT = ROOT.parent / "XML"
sys.path.insert(0, str(ROOT / "scripts"))

import extract_dictionary  # noqa: E402
import extract_interlinear  # noqa: E402
import build_xml  # noqa: E402
import normalize_standard_forms  # noqa: E402
from normalize_standard_forms import strip_accents  # noqa: E402


BOUND_CITATION_IDS = {
    "song-2018-kanakanavu-dictionary-0005",
    "song-2018-kanakanavu-dictionary-0084",
    "song-2018-kanakanavu-dictionary-0106",
    "song-2018-kanakanavu-dictionary-0133",
    "song-2018-kanakanavu-dictionary-0252",
    "song-2018-kanakanavu-dictionary-0366",
    "song-2018-kanakanavu-dictionary-0440",
    "song-2018-kanakanavu-dictionary-0502",
    "song-2018-kanakanavu-dictionary-0566",
    "song-2018-kanakanavu-dictionary-0705",
    "song-2018-kanakanavu-dictionary-0754",
}


@lru_cache(maxsize=1)
def analyses_by_id() -> dict[str, dict[str, object]]:
    return {
        str(analysis["s_id"]): analysis
        for analysis in extract_interlinear.extract()
    }


def word_pairs(
    analyses: dict[str, dict[str, object]], sentence_id: str
) -> list[tuple[str, str]]:
    return [
        (str(word["form"]), str(word["gloss"]))
        for word in analyses[sentence_id]["words"]  # type: ignore[index]
    ]


def test_interlinear_counts_and_positioned_text_boundaries() -> None:
    analyses = analyses_by_id()
    words = [
        word
        for analysis in analyses.values()
        for word in analysis["words"]  # type: ignore[index]
    ]

    assert len(analyses) == 650
    assert len(words) == 3_477
    assert sum(len(word.get("morphemes", [])) for word in words) == 5_048

    assert word_pairs(
        analyses, "song-2018-kanakanavu-S0029"
    ) == [
        ("m-aningcau", "主事焦點-漂亮"),
        ("cina=maku", "媽媽=我.屬格"),
    ]
    assert word_pairs(
        analyses, "song-2018-kanakanavu-S0509"
    ) == [
        ("ma-tasa’ai", "主事焦點-躺"),
        ("na", "處格"),
        ("ta-tarʉ", "重疊-床"),
    ]
    assert word_pairs(
        analyses, "song-2018-kanakanavu-S0602"
    ) == [
        ("arapepe=cu", "空空的=狀態改變"),
        ("pui’i", "回去"),
    ]
    assert word_pairs(
        analyses, "song-2018-kanakanavu-S0693"
    ) == [
        ("pa-ara-’akia", "使動-變成-存在.否定詞"),
        ("’apitarʉ", "危險"),
    ]


def test_embedded_quote_form_is_split_into_source_words() -> None:
    analyses = analyses_by_id()
    assert word_pairs(
        analyses, "song-2018-kanakanavu-S0695"
    ) == [
        ("aranai", "從"),
        ("meesua", "那時"),
        ("Namásia=cu", "那瑪夏=狀態改變"),
        ("kisa-ʉn", "稱為-受事焦點"),
        ("Kanakanavu", "卡那卡那富"),
        ("sua", "主格"),
        ("cakʉran", "河"),
        ("isi", "這"),
    ]


def test_dot_separated_source_glosses_still_build_morphemes() -> None:
    analyses = analyses_by_id()
    words = analyses["song-2018-kanakanavu-S0226"]["words"]  # type: ignore[index]
    assert [
        (morpheme["form"], morpheme["gloss"])
        for morpheme in words[0]["morphemes"]
    ] == [
        ("ma", "主事焦點."),
        ("cangcangarʉ", "開心"),
        ("=kara", "=是非疑問詞"),
        ("=kasu", "=你.主格"),
    ]


def test_source_explicit_infix_builds_validator_safe_morphemes() -> None:
    analyses = analyses_by_id()
    words = analyses["song-2018-kanakanavu-S0050"]["words"]  # type: ignore[index]
    infixed = words[2]
    assert [
        (morpheme["form"], morpheme["gloss"])
        for morpheme in infixed["morphemes"]
    ] == [
        ("t-ituru", "告知-"),
        ("-in-", "<完成貌>"),
        ("ʉn", "受事焦點"),
        ("=cu", "=狀態改變"),
        ("=kee", "=他.屬格"),
    ]


def test_infix_and_clitic_unit_boundaries_follow_current_policy() -> None:
    assert extract_interlinear.split_morphemes("host=clitic=last") == [
        "host",
        "=clitic",
        "=last",
    ]
    assert extract_interlinear.split_clitics("host-part=clitic=last") == [
        "host-part",
        "=clitic",
        "=last",
    ]

    stacked = extract_interlinear.add_morphemes(
        {
            "form": "t<in><Vm>angʉ",
            "gloss": "<完成貌><主事焦點>哭",
        }
    )
    assert stacked["morphemes"] == [
        {"form": "t-angʉ", "gloss": "哭"},
        {"form": "-in-", "gloss": "<完成貌>"},
        {"form": "-Vm-", "gloss": "<主事焦點>"},
    ]


def test_page_image_morpheme_overrides_are_exact_and_fail_closed() -> None:
    analyses = analyses_by_id()
    expected = {
        ("song-2018-kanakanavu-S0318", 2): [
            {"form": "t-i", "gloss": "重疊"},
            {"form": "-in-", "gloss": "<完成貌>"},
            {"form": "taini", "gloss": "丟"},
        ],
        ("song-2018-kanakanavu-S0422", 1): [
            {"form": "m", "gloss": None},
            {"form": "ukʉrʉ", "gloss": None},
        ],
        ("song-2018-kanakanavu-S0609", 14): [
            {"form": "ka", "gloss": "處在-"},
            {"form": "cangcangarʉ", "gloss": "重疊-快樂-"},
            {"form": "a", "gloss": "關係詞"},
        ],
        ("song-2018-kanakanavu-S0636", 4): [
            {"form": "pa", "gloss": "使動-"},
            {"form": "arivivini", "gloss": "跟隨在後"},
            {"form": "ʉn", "gloss": None},
        ],
        ("song-2018-kanakanavu-S0678", 5): [
            {"form": "t-a", "gloss": None},
            {"form": "-um-", "gloss": "<主事焦點>-"},
            {"form": "túturu", "gloss": "告知"},
        ],
    }
    for (sentence_id, word_index), morphemes in expected.items():
        assert analyses[sentence_id]["words"][word_index]["morphemes"] == morphemes

    with pytest.raises(ValueError, match="Morpheme override"):
        extract_interlinear.apply_morpheme_overrides(
            "song-2018-kanakanavu-S0422",
            [{"form": "changed", "gloss": "拿著"}, {"form": "x", "gloss": "x"}],
        )


def test_page_225_translation_matches_the_printed_source() -> None:
    with (ROOT / "intermediate" / "source_ledger.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    row = next(row for row in rows if row["example_label"] == "narrative1-026")
    assert row["translation"] == "躺到床上。"


def test_every_printed_interlinear_record_is_recovered() -> None:
    analyses = analyses_by_id()
    with (ROOT / "intermediate" / "source_ledger.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if row["included"] == "yes"
        ]
    expected = {
        row["final_s_id"]
        for row in rows
        if not 187 <= int(row["reader_page"]) < 221
        and row["final_s_id"] not in extract_interlinear.UNANALYZED_SOURCE_IDS
    }
    assert set(analyses) == expected


def test_short_cross_page_and_optional_examples_are_not_skipped() -> None:
    analyses = analyses_by_id()
    assert word_pairs(
        analyses, "song-2018-kanakanavu-S0015"
    ) == [
        ("mate’i-a", "留-祈使.主事焦點"),
        ("ti’ingi", "一些"),
        ("kʉnʉ-a", "吃-關係詞"),
    ]
    assert word_pairs(
        analyses, "song-2018-kanakanavu-S0086"
    ) == [
        ("’esi", "在"),
        ("t<um>a-tang", "Ca重疊<主事焦點>-哭"),
        ("ma-manu", "重疊-小孩"),
    ]
    assert word_pairs(
        analyses, "song-2018-kanakanavu-S0143"
    ) == [
        ("’una", "存在"),
        ("vántuku=maku", "錢=我.屬格"),
    ]
    assert [word["form"] for word in analyses[
        "song-2018-kanakanavu-S0303"
    ]["words"]] == ["mara’an", "Riau", "arapana’ʉ"]
    assert [word["form"] for word in analyses[
        "song-2018-kanakanavu-S0304"
    ]["words"]] == ["mara’an", "sua", "Riau", "arapana’ʉ"]


def test_morpheme_forms_preserve_infix_gaps_and_clitic_boundaries() -> None:
    analyses = analyses_by_id()
    words = [
        word
        for analysis in analyses.values()
        for word in analysis["words"]  # type: ignore[index]
    ]
    morphemes = [
        morpheme
        for word in words
        for morpheme in word.get("morphemes", [])
    ]
    assert all("(" not in morpheme["form"] for morpheme in morphemes)
    assert all(")" not in morpheme["form"] for morpheme in morphemes)
    assert all("<" not in morpheme["form"] for morpheme in morphemes)
    assert all(">" not in morpheme["form"] for morpheme in morphemes)

    for word in words:
        morph_forms = [str(morpheme["form"]) for morpheme in word.get("morphemes", [])]
        if "<" not in str(word["form"]):
            assert all("-" not in form for form in morph_forms)
            continue
        infixes = re.findall(r"<([^>]+)>", str(word["form"]))
        assert all(f"-{infix}-" in morph_forms for infix in infixes)
        gap_form = re.sub(
            r"<[^>]+>",
            extract_interlinear.INFIX_GAP,
            str(word["form"]),
        )
        gap_form = re.sub(
            f"{extract_interlinear.INFIX_GAP}+",
            extract_interlinear.INFIX_GAP,
            gap_form,
        )
        expected_roots = [
            extract_interlinear.morpheme_form(form)
            for form in extract_interlinear.split_morphemes(gap_form)
            if extract_interlinear.INFIX_GAP in form
        ]
        assert len(expected_roots) == 1
        assert expected_roots[0] in morph_forms

    clitic_words = [word for word in words if "=" in str(word["form"])]
    assert clitic_words
    assert all(
        any(str(morpheme["form"]).startswith("=") for morpheme in word["morphemes"])
        for word in clitic_words
    )
    assert all(
        not str(morpheme["form"]).endswith("=")
        for word in clitic_words
        for morpheme in word["morphemes"]
    )

    unsegmented = [
        word
        for word in words
        if not any(marker in str(word["form"]) for marker in "-=<>")
    ]
    assert all(
        word["morphemes"] == [
            {"form": word["form"], "gloss": word["gloss"]}
        ]
        for word in unsegmented
    )


def test_xml_word_forms_preserve_segmentation_and_omit_parenthetical_notation() -> None:
    assert build_xml.xml_word_form("cina=maku") == "cina=maku"
    assert build_xml.xml_word_form("t<um>a-tang") == "t<um>a-tang"
    assert build_xml.xml_word_form("’arup(a)-ara") == "’arup-ara"

    analyses = analyses_by_id()
    word = analyses["song-2018-kanakanavu-S0410"]["words"][2]  # type: ignore[index]
    assert word["morphemes"] == [
        {"form": "’arup", "gloss": "互相-"},
        {"form": "ara", "gloss": "拿"},
    ]


def test_source_alternatives_follow_the_selected_sentence_variant() -> None:
    analyses = analyses_by_id()
    assert [word["form"] for word in analyses[
        "song-2018-kanakanavu-S0038"
    ]["words"]][1] == "Pani"
    assert [word["form"] for word in analyses[
        "song-2018-kanakanavu-S0039"
    ]["words"]][1] == "kasua"
    assert [word["form"] for word in analyses[
        "song-2018-kanakanavu-S0431"
    ]["words"]][3] == "saa"
    assert [word["form"] for word in analyses[
        "song-2018-kanakanavu-S0432"
    ]["words"]][3] == "sua"


def test_generated_xml_respects_shared_segmentation_policy() -> None:
    tree = ET.parse(
        XML_ROOT
        / "Kanakanavu"
        / "Song_2018_Kanakanavu_Grammar.xml"
    )
    words = tree.findall(".//W")
    morphemes = tree.findall(".//M")

    assert len(words) == 3_477
    assert len(morphemes) == 5_048
    assert any(
        "=" in (form.text or "")
        for word in words
        for form in word.findall("FORM")
    )
    for word in words:
        original_word = word.find("./FORM[@kindOf='original']")
        original_text = original_word.text if original_word is not None else ""
        for morpheme in word.findall("./M"):
            for form in morpheme.findall("FORM"):
                form_text = form.text or ""
                assert not any(marker in form_text for marker in "()<>")
                if "-" in form_text:
                    assert "<" in original_text
                if "=" in form_text:
                    assert form_text.startswith("=")
        for kind in ("original", "standard"):
            word_form = word.find(f"./FORM[@kindOf='{kind}']")
            if word_form is None or "=" not in (word_form.text or ""):
                continue
            assert any(
                "=" in (form.text or "")
                for morpheme in word.findall("./M")
                for form in morpheme.findall(f"./FORM[@kindOf='{kind}']")
            )


def test_analytic_translation_parentheticals_are_preserved_as_notes() -> None:
    tree = ET.parse(
        XML_ROOT
        / "Kanakanavu"
        / "Song_2018_Kanakanavu_Grammar.xml"
    )
    expected = {
        "song-2018-kanakanavu-S0143": (
            "我有錢。",
            "我有錢。（=我的錢存在）",
        ),
        "song-2018-kanakanavu-S0149": (
            "我沒有錢。",
            "我沒有錢。（=我的錢沒有）",
        ),
    }
    for sentence_id, (primary, source_translation) in expected.items():
        translation = tree.find(
            f"./S[@id='{sentence_id}']/TRANSL[@xml:lang='zho']",
            {"xml": "http://www.w3.org/XML/1998/namespace"},
        )
        assert translation is not None
        assert translation.text == primary
        assert translation.get("notes") == source_translation


def test_page_69_analysis_typo_is_repaired_in_the_original_tier() -> None:
    """Reader p.69 prints 'takananga' in the sentence line of example 4-9 and
    'takanaga' in its own aligned analysis line — a typesetting slip, since the
    corpus attests 'takananga' 22x and 'takanaga' only in that one analysis.

    The extraction ledger still records exactly what the page prints; the
    repair is a recorded manual edit (CodeAndDocs/manual_edits.xml) applied to
    the ORIGINAL tier, from which the standard tier and PHON regenerate. Before
    the repair, the bare 'g' had no Ortho113 mapping and surfaced as '*' in the
    original PHON."""
    analyses = analyses_by_id()
    assert analyses["song-2018-kanakanavu-S0012"]["words"][3]["form"] == (
        "takanaga=kasu"
    )

    with (ROOT / "intermediate" / "source_ledger.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        row = next(
            row
            for row in csv.DictReader(handle)
            if row["final_s_id"] == "song-2018-kanakanavu-S0012"
        )
    assert "takananga kasu" in row["target_text"]

    root = ET.parse(
        XML_ROOT
        / "Kanakanavu"
        / "Song_2018_Kanakanavu_Grammar.xml"
    ).getroot()
    word = root.find(".//W[@id='song-2018-kanakanavu-S0012-W004']")
    assert word is not None
    assert word.findtext("./FORM[@kindOf='original']") == "takananga=kasu"
    assert word.findtext("./FORM[@kindOf='standard']") == "takananga=kasu"
    assert word.findtext("./PHON[@kindOf='original']") == "takanaŋakasu"
    morpheme = word.find("./M[@id='song-2018-kanakanavu-S0012-W004-M01']")
    assert morpheme is not None
    assert morpheme.findtext("./FORM[@kindOf='original']") == "takananga"
    assert morpheme.findtext("./FORM[@kindOf='standard']") == "takananga"
    clitic = word.find("./M[@id='song-2018-kanakanavu-S0012-W004-M02']")
    assert clitic is not None
    assert clitic.findtext("./FORM[@kindOf='original']") == "=kasu"
    assert clitic.findtext("./FORM[@kindOf='standard']") == "=kasu"


def test_review_gate_rejects_reordered_positioned_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lines = build_xml.OFFICIAL_TEXT.read_text(encoding="utf-8").splitlines()
    lines[0], lines[1] = lines[1], lines[0]
    mutated = tmp_path / "official_text.jsonl"
    mutated.write_text("\n".join(lines) + "\n", encoding="utf-8")
    monkeypatch.setattr(build_xml, "OFFICIAL_TEXT", mutated)
    with pytest.raises(ValueError, match="missing, duplicated, or reordered"):
        build_xml.assert_closed_review()


def test_standard_manifest_rejects_changed_source_input(tmp_path: Path) -> None:
    source = (
        XML_ROOT
        / "Kanakanavu"
        / "Song_2018_Kanakanavu_Grammar.xml"
    )
    target = tmp_path / source.name
    tree = ET.parse(source)
    original = tree.find(
        ".//S[@id='song-2018-kanakanavu-S0469']/FORM[@kindOf='original']"
    )
    assert original is not None
    original.text = (original.text or "") + "x"
    tree.write(target, encoding="UTF-8", xml_declaration=True)
    with pytest.raises(ValueError, match="Source input changed"):
        normalize_standard_forms.process_file(target)


def test_standard_surface_manifest_has_exact_reviewed_outputs() -> None:
    decisions = normalize_standard_forms.load_decisions()

    variants = decisions[
        ("dictionary", "song-2018-kanakanavu-dictionary-0006")
    ]
    assert variants.expected_input == "aracaini / araceni / araceen"
    assert variants.output_forms == ("aracaini", "araceni", "araceen")

    optional_word = decisions[
        ("dictionary", "song-2018-kanakanavu-dictionary-0696")
    ]
    assert optional_word.expected_input == "'akia (na)"
    assert optional_word.output_forms == ("'akia na", "'akia")

    for record_id in sorted(BOUND_CITATION_IDS):
        decision = decisions[("dictionary", record_id)]
        assert decision.output_forms == ()
        assert decision.decision_class == "bound_form_entry_excluded"

    lyric = decisions[("grammar", "song-2018-kanakanavu-S0477")]
    assert lyric.output_forms == (
        "mati'ara'aravang 'aa 'aravang vatu 'aravang vatu! "
        "tisa'ʉ ku 'apasʉ.",
    )


def test_bound_citation_forms_are_excluded_at_extraction() -> None:
    entries = extract_dictionary.extract_entries()
    by_id = {entry["entry_id"]: entry for entry in entries}

    excluded = {
        entry["entry_id"] for entry in entries if entry["included"] == "no"
    }
    assert excluded == BOUND_CITATION_IDS
    assert all(
        by_id[entry_id]["form"].endswith("-") for entry_id in BOUND_CITATION_IDS
    )
    assert all(
        bool(entry["exclusion_reason"]) == (entry["included"] == "no")
        for entry in entries
    )

    # Exclusion must not renumber the ledger: IDs stay deterministic over the
    # full extracted sequence; the published XML simply keeps gaps.
    assert [entry["entry_id"] for entry in entries] == [
        f"song-2018-kanakanavu-dictionary-{index:04d}"
        for index in range(1, len(entries) + 1)
    ]


def test_generated_direct_standard_surfaces_are_marker_free() -> None:
    grammar = ET.parse(
        XML_ROOT
        / "Kanakanavu"
        / "Song_2018_Kanakanavu_Grammar.xml"
    ).getroot()
    dictionary = ET.parse(
        XML_ROOT
        / "Kanakanavu"
        / "Song_2018_Kanakanavu_Grammar_Dictionary.xml"
    ).getroot()

    # The two reviewed break-dash surfaces legitimately contain "-" as
    # punctuation; exempt their exact accent-folded texts, nothing else.
    decisions = normalize_standard_forms.load_decisions()
    reviewed_dash_surfaces = frozenset(
        strip_accents(decision.output_forms[0])
        for decision in decisions.values()
        if decision.decision_class == "source_break_punctuation_single_dash"
    )
    assert len(reviewed_dash_surfaces) == 2
    normalize_standard_forms.assert_marker_free(
        grammar, dictionary=False, allowed=reviewed_dash_surfaces
    )
    normalize_standard_forms.assert_marker_free(dictionary, dictionary=True)

    by_id = {sentence.get("id"): sentence for sentence in dictionary.findall("./S")}

    # Source-defined variant forms are split into separate S entries before
    # the standard tier is created: same TRANSL, one clean form per entry,
    # the printed apparatus preserved in the original tier's notes.
    assert not dictionary.findall(".//FORM[@kindOf='alternate']")
    split_ids = [
        "song-2018-kanakanavu-dictionary-0006",
        "song-2018-kanakanavu-dictionary-0006a",
        "song-2018-kanakanavu-dictionary-0006b",
    ]
    expected_forms = ["aracaini", "araceni", "araceen"]
    translations = set()
    for entry_id, form_text in zip(split_ids, expected_forms, strict=True):
        entry = by_id[entry_id]
        original = entry.find("./FORM[@kindOf='original']")
        assert original.text == form_text
        assert "aracaini / araceni / araceen" in original.get("notes")
        assert entry.find("./FORM[@kindOf='standard']").text == form_text
        assert entry.find("./PHON[@kindOf='standard']") is not None
        translations.add(entry.find("./TRANSL").text)
    assert len(translations) == 1

    optional_ids = {
        "song-2018-kanakanavu-dictionary-0696": "'akia na",
        "song-2018-kanakanavu-dictionary-0696a": "'akia",
    }
    for entry_id, form_text in optional_ids.items():
        assert by_id[entry_id].find("./FORM[@kindOf='original']").text == form_text

    grammar_by_id = {
        sentence.get("id"): sentence for sentence in grammar.findall("./S")
    }
    assert grammar_by_id["song-2018-kanakanavu-S0469"].find(
        "./FORM[@kindOf='standard']"
    ).text == (
        "'akuni arakukunu mataa Pani sumasima'ʉ-nguai sua napa'ici tamna "
        "manu Pani."
    )
    assert grammar_by_id["song-2018-kanakanavu-S0472"].find(
        "./FORM[@kindOf='standard']"
    ).text == "ikim-'atai 'apio mataa iku."
    # The original tier records the reviewed double-hyphen correction, and the
    # single dash survives into both PHON tiers as punctuation (no '*').
    for sid in ("song-2018-kanakanavu-S0469", "song-2018-kanakanavu-S0472"):
        sentence = grammar_by_id[sid]
        assert "typewriter double-hyphen" in sentence.find(
            "./FORM[@kindOf='original']"
        ).get("notes")
        assert "--" not in sentence.find("./FORM[@kindOf='original']").text
        for phon in sentence.findall("./PHON"):
            assert "*" not in (phon.text or "")
    assert grammar_by_id["song-2018-kanakanavu-S0477"].find(
        "./FORM[@kindOf='standard']"
    ).text == (
        "mati'ara'aravang 'aa 'aravang vatu 'aravang vatu! "
        "tisa'ʉ ku 'apasʉ."
    )

    # Bound citation forms are deleted from the published XML entirely: the
    # ledger documents the exclusion, and no dictionary form ends in a hyphen.
    assert not set(by_id) & BOUND_CITATION_IDS
    # 756 published records; the 114 split records emit 228 entries after 26
    # variants that duplicate another record's (form, translation) are dropped.
    assert len(by_id) == 870
    assert not any(
        (form.text or "").endswith("-")
        for sentence in dictionary.findall("./S")
        for form in sentence.findall("./FORM")
    )

    # Split variants that duplicate another record's (form, translation) are
    # removed; the owning record keeps the form. Example: the pronoun record
    # 0072 (ikim; kim; mia; kimia) keeps only ikim because kim, mia, and
    # kimia are standalone source records.
    dropped = normalize_standard_forms.DUPLICATE_VARIANT_ENTRY_IDS
    assert len(dropped) == 26
    assert not dropped & set(by_id)
    assert by_id["song-2018-kanakanavu-dictionary-0072"].find(
        "./FORM[@kindOf='original']"
    ).text == "ikim"
    assert by_id["song-2018-kanakanavu-dictionary-0127"].find(
        "./FORM[@kindOf='original']"
    ).text == "kim"

    # After the drop, (form, translation) pairs are globally unique.
    pairs = [
        (
            sentence.find("./FORM[@kindOf='original']").text,
            sentence.find("./TRANSL").text,
        )
        for sentence in dictionary.findall("./S")
    ]
    assert len(pairs) == len(set(pairs))

    for sentence in dictionary.findall("./S"):
        children = list(sentence)
        translation_index = next(
            index for index, child in enumerate(children) if child.tag == "TRANSL"
        )
        assert all(
            child.tag in {"FORM", "PHON"}
            for child in children[:translation_index]
        )


def test_stress_and_shared_phonology_tiers() -> None:
    roots = [
        ET.parse(path).getroot()
        for path in sorted(XML_ROOT.rglob("*.xml"))
    ]
    original_forms = [
        form
        for root in roots
        for form in root.findall(".//FORM[@kindOf='original']")
    ]
    standard_forms = [
        form
        for root in roots
        for form in root.findall(".//FORM")
        if form.get("kindOf") in {"standard", "alternate"}
    ]
    accents = "áéíóúÁÉÍÓÚ"
    assert any(any(character in (form.text or "") for character in accents) for form in original_forms)
    assert all(
        not any(character in (form.text or "") for character in accents)
        for form in standard_forms
    )

    original_phon = [
        phon
        for root in roots
        for phon in root.findall(".//PHON[@kindOf='original']")
    ]
    standard_phon = [
        phon
        for root in roots
        for phon in root.findall(".//PHON[@kindOf='standard']")
    ]
    assert len(original_phon) == len(original_forms)
    assert len(standard_phon) == sum(
        1
        for root in roots
        for form in root.findall(".//FORM[@kindOf='standard']")
    )
    assert any("[r|ɾ]" in (phon.text or "") for phon in standard_phon)

    grammar = roots[0]
    sentence = grammar.find(".//S[@id='song-2018-kanakanavu-S0009']")
    assert sentence is not None
    assert "'itúmuru" in sentence.findtext("./FORM[@kindOf='original']", "")
    assert "*" not in sentence.findtext("./PHON[@kindOf='original']", "")
