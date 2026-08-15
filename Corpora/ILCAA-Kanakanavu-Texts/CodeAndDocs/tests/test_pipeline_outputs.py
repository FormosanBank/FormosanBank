import csv
import json
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


def jsonl(path: str):
    p = ROOT / path
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_toc_has_44_entries_and_part_counts():
    with (ROOT / "data/processed/toc_entries.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 44
    counts = {}
    for row in rows:
        counts[row["part_number"]] = counts.get(row["part_number"], 0) + 1
    assert counts == {"1": 7, "2": 4, "3": 11, "4": 22}


def test_sentence_minimum_accounted_for():
    units = jsonl("data/processed/sentence_units.jsonl")
    grammar_units = [u for u in units if u["text_id"].endswith("GRAMMATICAL_INTRODUCTION_EXAMPLES")]
    assert len(units) == 1431
    assert len(grammar_units) == 48
    assert {u["grammar_example_number"] for u in grammar_units} == set(range(1, 41))
    assert all(u["source_line_clean"] for u in units if u["quality_status"] == "xml_eligible")
    assert all(u["free_translation_clean"] for u in units if u["quality_status"] == "xml_eligible")
    assert not [u for u in units if u["quality_status"] == "xml_eligible_source_only"]


def test_page_bottom_translations_are_recovered_without_footnotes():
    expected = {
        "ILCAA_KANAKANAVU_TEXTS_002_THE_BIG_FLOOD_U0031": "At that time, (people) were always very happy.",
        "ILCAA_KANAKANAVU_TEXTS_011_NAPARAMACI_U0133": "The people were playing while dancing.",
        "ILCAA_KANAKANAVU_TEXTS_012_HUNTING_U0006": "I can only teach you in that way.",
        "ILCAA_KANAKANAVU_TEXTS_013_FISHING_U0007": "In those days, I sold my fish.",
        "ILCAA_KANAKANAVU_TEXTS_028_PANGOLIN_II_U0027": "As for her body, her skin appeared to be the same color as a pangolin.",
        "ILCAA_KANAKANAVU_TEXTS_029_SNAKE_U0016": 'I looked up. "What kind of wasp is it?" I said.',
        "ILCAA_KANAKANAVU_TEXTS_029_SNAKE_U0058": "My children from Taichung all came to see me, their father.",
        "ILCAA_KANAKANAVU_TEXTS_031_A_RECKLESS_MOTHER_U0013": "The girl could stand up, and her mother left (for work).",
        "ILCAA_KANAKANAVU_TEXTS_035_SETTING_UP_TRAPS_II_U0008": "It would be bad should I tell a lie, all elders would know it.",
        "ILCAA_KANAKANAVU_TEXTS_041_AN_EVENT_AT_NAPALANGA_U0021": "His wife was standing up to follow him.",
        "ILCAA_KANAKANAVU_TEXTS_041_AN_EVENT_AT_NAPALANGA_U0031": "The man disappeared and he had been broken into pieces.",
        "ILCAA_KANAKANAVU_TEXTS_042_A_DANGEROUS_NARROW_STREAM_WITH_WHITE_STONES_U0027": "Two days later, the Paiwan who saw (the snake) died.",
    }
    units = {u["unit_id"]: u for u in jsonl("data/processed/sentence_units.jsonl")}
    assert set(expected) <= set(units)
    for unit_id, translation in expected.items():
        unit = units[unit_id]
        assert unit["free_translation_clean"] == translation
        assert unit["quality_status"] == "xml_eligible"
        assert len(unit["translation_line_ids"]) == 1

    all_line_ids = {
        line_id
        for unit in units.values()
        for field in ("source_line_ids", "gloss_line_ids", "translation_line_ids")
        for line_id in unit[field]
    }
    assert "p0207_v027" not in all_line_ids
    assert "p0207_v028" not in all_line_ids


def test_final_xml_shape_and_langs():
    xml_dir = ROOT / "XML/xnb"
    files = sorted(xml_dir.glob("*.xml"))
    assert len(files) == 45
    assert files[0].name == "ILCAA_KanakanavuTexts_000_grammatical_introduction_examples.xml"
    for path in files:
        root = ET.parse(path).getroot()
        assert root.tag == "TEXT"
        assert root.attrib["{http://www.w3.org/XML/1998/namespace}lang"] == "xnb"
        assert root.attrib["dialect"] == "Kanakanavu"
        assert root.attrib["citation"]
        assert root.attrib["BibTeX_citation"]
        for transl in root.iter("TRANSL"):
            assert transl.attrib["{http://www.w3.org/XML/1998/namespace}lang"] == "eng"


def test_translation_kindof_is_owned_by_tier():
    xml_dir = ROOT / "XML/xnb"
    for path in xml_dir.glob("*.xml"):
        root = ET.parse(path).getroot()
        for sentence in root.iter("S"):
            direct_translations = [child for child in sentence if child.tag == "TRANSL"]
            assert direct_translations
            assert all("kindOf" not in transl.attrib for transl in direct_translations)
        for parent_name in ("W", "M"):
            for parent in root.iter(parent_name):
                glosses = parent.findall("TRANSL")
                assert glosses
                assert all(gloss.attrib.get("kindOf") == "original" for gloss in glosses)


def test_word_and_morpheme_gloss_tiers_are_structurally_consistent():
    xml_dir = ROOT / "XML/xnb"
    w_count = 0
    m_count = 0
    w_gloss_count = 0
    m_gloss_count = 0
    w_original_infix_count = 0
    w_gloss_infix_count = 0
    m_infix_count = 0
    for path in xml_dir.glob("*.xml"):
        root = ET.parse(path).getroot()
        for word in root.iter("W"):
            w_count += 1
            gloss = word.find("TRANSL")
            assert gloss is not None
            assert gloss.attrib.get("kindOf") == "original"
            assert "".join(gloss.itertext()).strip() or gloss.find("UNCLEAR") is not None
            w_gloss_count += 1
            original = word.find('./FORM[@kindOf="original"]')
            if original is not None and "<" in (original.text or "") and ">" in (original.text or ""):
                w_original_infix_count += 1
            if "<" in (gloss.text or "") and ">" in (gloss.text or ""):
                w_gloss_infix_count += 1
            assert word.findall("M"), "POL-023 requires at least one M per W"
        for morph in root.iter("M"):
            m_count += 1
            gloss = morph.find("TRANSL")
            assert gloss is not None
            assert gloss.attrib.get("kindOf") == "original"
            assert "".join(gloss.itertext()).strip() or gloss.find("UNCLEAR") is not None
            m_gloss_count += 1
            for form in morph.findall("FORM"):
                assert "<" not in (form.text or "") and ">" not in (form.text or "")
            original = morph.find('./FORM[@kindOf="original"]')
            text = original.text if original is not None else ""
            if text.startswith("-") and text.endswith("-"):
                m_infix_count += 1
    assert w_count == w_gloss_count
    assert m_count == m_gloss_count
    assert w_original_infix_count == w_gloss_infix_count == m_infix_count
    assert m_infix_count > 0


def test_standard_and_phon_tiers_are_shared_tool_generated():
    xml_dir = ROOT / "XML/xnb"
    original_forms = []
    parent_count = 0
    for path in xml_dir.glob("*.xml"):
        root = ET.parse(path).getroot()
        for form in root.iter("FORM"):
            text = form.text or ""
            if form.attrib.get("kindOf") == "original":
                original_forms.append(text)
        for parent_name in ("S", "W", "M"):
            for parent in root.iter(parent_name):
                parent_count += 1
                for kind in ("original", "standard"):
                    assert parent.find(f'./FORM[@kindOf="{kind}"]') is not None
                    phon = parent.find(f'./PHON[@kindOf="{kind}"]')
                    assert phon is not None and (phon.text or "").strip()
    assert original_forms
    assert parent_count == 29735
    assert any(any(ord(ch) > 127 for ch in text) for text in original_forms)


def test_every_xml_sentence_indexed():
    with (ROOT / "data/processed/xml_index.csv").open(encoding="utf-8") as f:
        index_ids = {row["sentence_id"] for row in csv.DictReader(f)}
    xml_ids = set()
    for path in (ROOT / "XML/xnb").glob("*.xml"):
        root = ET.parse(path).getroot()
        xml_ids.update(s.attrib["id"] for s in root.findall("S"))
    assert xml_ids
    assert xml_ids == index_ids
    assert len(xml_ids) == 1455


def test_grammar_introduction_examples_in_final_xml():
    path = ROOT / "XML/xnb/ILCAA_KanakanavuTexts_000_grammatical_introduction_examples.xml"
    root = ET.parse(path).getroot()
    assert root.attrib["source"].startswith("Kanakanavu Texts (2026), grammatical introduction examples")
    sentences = root.findall("S")
    assert len(sentences) == 48
    forms = ["".join(s.find('./FORM[@kindOf=\"original\"]').itertext()) for s in sentences]
    assert forms[0] == "t<um>a-taŋi maanu"
    first_word = sentences[0].find("W")
    assert first_word is not None
    assert "".join(first_word.find('./FORM[@kindOf="original"]').itertext()) == "t<um>a-taŋi"
    assert "naini sua [k<um>a-kaən uuru]" in forms
    assert "naini sua [kaən-a]" in forms
    assert "a-pa-kaən-a maanu uuru." in forms
    assert all("kaən-ən=musu" not in form for form in forms)
    assert all("*" not in form for form in forms)

    units = {u["unit_id"]: u for u in jsonl("data/processed/sentence_units.jsonl")}
    assert units[
        "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_U0025"
    ]["source_line_clean"] == "naini sua [kaən-a/*kaən-ən=musu]"
    assert units[
        "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_U0032"
    ]["source_line_clean"] == "a-pa-kaən-a (*sua) maanu uuru."
    marked = sentences[31].find('./FORM[@kindOf="original"]')
    assert marked is not None
    assert "source_notation_audit.csv" in marked.attrib["notes"]


def test_wrapped_gloss_continuation_keeps_word_alignment():
    path = ROOT / "XML/xnb/ILCAA_KanakanavuTexts_011_naparamaci.xml"
    root = ET.parse(path).getroot()
    sentence = root.find('./S[@id="ILCAA_KANAKANAVU_TEXTS_011_NAPARAMACI_S0117"]')
    assert sentence is not None
    glosses = {
        word.find('./FORM[@kindOf="original"]').text: "".join(word.find("TRANSL").itertext()).strip()
        for word in sentence.findall("W")
    }
    assert glosses["tia=pila-paliʔ-in"] == "FUT=contribute-leave-UV"
    assert glosses["vuku=maku"] == "belt=1SG.GEN"
    assert glosses["u-cani"] == "NUM-one"
    assert glosses["maamia"] == "only"

    sentence = root.find('./S[@id="ILCAA_KANAKANAVU_TEXTS_011_NAPARAMACI_S0132"]')
    assert sentence is not None
    glosses = {
        word.find('./FORM[@kindOf="original"]').text: "".join(word.find("TRANSL").itertext()).strip()
        for word in sentence.findall("W")
    }
    assert glosses["ʔaisi=kan=cu"] == "exist=said=COS"

    sentence = root.find('./S[@id="ILCAA_KANAKANAVU_TEXTS_011_NAPARAMACI_S0112"]')
    assert sentence is not None
    glosses = {
        word.find('./FORM[@kindOf="original"]').text: "".join(word.find("TRANSL").itertext()).strip()
        for word in sentence.findall("W")
    }
    assert glosses["kaʔan=kita"] == "NEG=1INCL.NOM"
    translation = sentence.find("TRANSL")
    assert translation is not None
    assert "".join(translation.itertext()).strip().startswith("Therefore,")


def test_sentence_translations_preserve_meaningful_parentheses():
    cases = [
        (
            "ILCAA_KanakanavuTexts_000_grammatical_introduction_examples.xml",
            "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_S0003",
            '"When I shoot (the sun), friend, let\'s dive into the water," (he said).',
        ),
        (
            "ILCAA_KanakanavuTexts_011_naparamaci.xml",
            "ILCAA_KANAKANAVU_TEXTS_011_NAPARAMACI_S0132",
            "As the sun passed and went down, all the people, who had gathered together, were waiting. They were (there) to pacify the sun.",
        ),
        (
            "ILCAA_KanakanavuTexts_028_pangolin_ii.xml",
            "ILCAA_KANAKANAVU_TEXTS_028_PANGOLIN_II_S0016",
            "She brought it to the place (field hut) where she was to chase away birds.",
        ),
        (
            "ILCAA_KanakanavuTexts_031_a_reckless_mother.xml",
            "ILCAA_KANAKANAVU_TEXTS_031_A_RECKLESS_MOTHER_S0014",
            "What I had heard is that, the mother was weeding (with a hoe).",
        ),
    ]
    for filename, sentence_id, expected in cases:
        root = ET.parse(ROOT / "XML/xnb" / filename).getroot()
        sentence = root.find(f'./S[@id="{sentence_id}"]')
        assert sentence is not None
        translation = sentence.find('./TRANSL[@xml:lang="eng"]', {"xml": "http://www.w3.org/XML/1998/namespace"})
        assert translation is not None
        assert "".join(translation.itertext()).strip() == expected



def test_trailing_editorial_parentheticals_use_translation_notes():
    cases = {
        "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_S0023": (
            "The place of drawing water is where I killed a pig.",
            "Tsuchida 1976: 49",
        ),
        "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_S0024": (
            "'Who is eating (cooked rice)?'",
            "pseudo-cleft",
        ),
        "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_S0025": (
            "'What do you eat?!'",
            "pseudo-cleft",
        ),
        "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_S0026": (
            "'What did he use to cook rice?'",
            "pseudo-cleft",
        ),
        "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_S0027": (
            "'What are you angry for!'",
            "pseudo-cleft",
        ),
        "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_S0028": (
            "'Avia is eating the fish.'",
            "AV Indicative",
        ),
        "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_S0029": (
            "'Avia ate the fish.'",
            "UV Indicative",
        ),
        "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_S0039": (
            "I am tying up these pieces of wood.",
            "Liu 2014",
        ),
        "ILCAA_KANAKANAVU_TEXTS_032_KILLING_A_SNAKE_BROUGHT_A_CURSE_ON_A_PERSON_S0028": (
            '"Because there was a snake blocking me (on the path)."',
            "He replied.",
        ),
    }
    found = {}
    for path in (ROOT / "XML/xnb").glob("*.xml"):
        for sentence in ET.parse(path).getroot().findall("S"):
            if sentence.attrib["id"] not in cases:
                continue
            translation = sentence.find("TRANSL")
            assert translation is not None
            found[sentence.attrib["id"]] = (
                "".join(translation.itertext()).strip(),
                translation.attrib.get("notes", ""),
            )
    assert found == cases


def test_sentence_translations_preserve_printed_characters_and_notes():
    cases = [
        (
            "ILCAA_KanakanavuTexts_011_naparamaci.xml",
            "ILCAA_KANAKANAVU_TEXTS_011_NAPARAMACI_S0009",
            "She went—at that time the river was muddy. The girl went (there) to fish with a net, as she said.",
        ),
        (
            "ILCAA_KanakanavuTexts_034_setting_up_traps.xml",
            "ILCAA_KANAKANAVU_TEXTS_034_SETTING_UP_TRAPS_S0005",
            "Because the deceased brother who took me was called Sumio 澄男.",
        ),
        (
            "ILCAA_KanakanavuTexts_034_setting_up_traps.xml",
            "ILCAA_KANAKANAVU_TEXTS_034_SETTING_UP_TRAPS_S0037",
            "At that time, it was really…",
        ),
        (
            "ILCAA_KanakanavuTexts_008_a_legendary_malicious_spirit.xml",
            "ILCAA_KANAKANAVU_TEXTS_008_A_LEGENDARY_MALICIOUS_SPIRIT_S0012",
            '"I\'ve got no (more) water (lit, my water is no more), somebody had spilled it this afternoon," said (she).',
        ),
    ]
    for filename, sentence_id, expected in cases:
        root = ET.parse(ROOT / "XML/xnb" / filename).getroot()
        sentence = root.find(f'./S[@id="{sentence_id}"]')
        assert sentence is not None
        translation = sentence.find("TRANSL")
        assert translation is not None
        assert "".join(translation.itertext()).strip() == expected


def test_no_non_xml_in_final_xml():
    assert all(path.suffix == ".xml" for path in (ROOT / "XML/xnb").iterdir() if path.is_file())


def test_source_coverage_and_notation_ledgers_are_complete():
    with (ROOT / "data/processed/source_unit_coverage.csv").open(encoding="utf-8") as handle:
        coverage = list(csv.DictReader(handle))
    assert len(coverage) == 1431
    assert all(row["xml_action"] == "included" for row in coverage)
    assert sum(
        row["translation_action"]
        == "included_translation_with_source_editorial_note_attribute"
        for row in coverage
    ) == 9
    assert sum(
        row["translation_action"] == "included_exact_source_translation"
        for row in coverage
    ) == 1422
    assert sum(bool(row["translation_note"]) for row in coverage) == 9
    assert all(row["xml_translation"] for row in coverage)
    assert all(row["source_translation"] for row in coverage)
    assert sum(row["word_morpheme_action"] == "omitted_source_square_bracket_analysis_notation" for row in coverage) == 4
    assert sum(row["word_morpheme_action"] == "expanded_variants_with_aligned_w_m" for row in coverage) == 24

    with (ROOT / "data/processed/source_notation_audit.csv").open(encoding="utf-8") as handle:
        notation = list(csv.DictReader(handle))
    assert len(notation) == 29
    assert sum(row["created_variants"] != "none" for row in notation) == 24
    exclusions = [row for row in notation if row["excluded_sentences"] != "none"]
    assert len(exclusions) == 2
    assert {row["source_sentence_label"] for row in exclusions} == {"(23b)", "(26a)"}
    assert any("asterisk" in row["notation_types"] for row in notation)
    assert any("slash" in row["notation_types"] for row in notation)

    with (ROOT / "data/processed/coverage_by_page.csv").open(encoding="utf-8") as handle:
        pages = list(csv.DictReader(handle))
    assert len(pages) == 252
    assert {int(row["physical_page"]) for row in pages} == set(range(1, 253))


def test_every_raw_qc_finding_is_resolved_or_source_justified():
    with (ROOT / "data/processed/qc_finding_review.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert all(row["status"] == "justified" for row in rows)
    assert all(row["disposition"] and row["source_evidence"] for row in rows)
    blocking_hard = [
        row for row in rows
        if row["severity"] == "HARD"
        and row["validator"] in {"xml", "text", "gloss"}
    ]
    assert not blocking_hard
    duplicate_hard = [
        row for row in rows
        if row["severity"] == "HARD" and row["validator"] == "duplicate"
    ]
    assert not duplicate_hard
    reference_warnings = [
        row for row in rows
        if row["severity"] == "WARN" and row["rule_id"] == "reference_comparison"
    ]
    assert not reference_warnings

    standardization_review = (
        ROOT / "data/processed/standardization_review.md"
    ).read_text(encoding="utf-8")
    assert "Original and standard PHON are regenerated" in standardization_review
    assert "Standard FORM is regenerated" in standardization_review
    assert "physical page 16, printed page 11" in standardization_review.lower()

    validation_report = (
        ROOT / "data/processed/validation_report.md"
    ).read_text(encoding="utf-8")
    assert "Final status: PASS" in validation_report
    assert "Unresolved finding rows: 0" in validation_report
    assert "Gloss scrape G012 actionable translation-note findings: 0" in validation_report


def test_reviewed_phonology_rules_and_mapping_gaps_are_explicit():
    root = ET.parse(
        ROOT / "XML/xnb/ILCAA_KanakanavuTexts_001_shooting_the_sun.xml"
    ).getroot()
    sentence = root.find('./S[@id="ILCAA_KANAKANAVU_TEXTS_001_SHOOTING_THE_SUN_S0009"]')
    assert sentence is not None
    assert sentence.find('./PHON[@kindOf="original"]').text.startswith("ʂiʂi")
    sentence = root.find('./S[@id="ILCAA_KANAKANAVU_TEXTS_001_SHOOTING_THE_SUN_S0020"]')
    assert sentence is not None
    assert "taʔitʂiki" in sentence.find('./PHON[@kindOf="original"]').text

    with (ROOT / "data/processed/phonology_mapping_review.csv").open(
        encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 77
    assert all("*" in row["phon"] for row in rows)
    assert all(set(row["unmapped_foreign_letters"]) <= set("bdgjzBDGJZ") for row in rows)


def test_cleaner_probe_is_disposable_and_documented():
    report = (ROOT / "data/processed/cleaner_probe.md").read_text(encoding="utf-8")
    assert "Cleaner exit code: 0" in report
    assert "S-original forms checked: 1455" in report
    assert "S-original forms changed by the cleaner:" in report
    assert "S-original forms changed by the cleaner: 5" in report
    assert "Hyphen characters before/after: 5476/5476" in report
    assert "Equals characters before/after: 2529/2529" in report
    assert "do not promote the disposable cleaner output" in report


def test_seeded_random_source_xml_audit_is_reviewed_and_reproducible():
    with (ROOT / "data/processed/random_source_xml_audit.csv").open(
        encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 30
    assert rows[0]["unit_id"] == "ILCAA_KANAKANAVU_TEXTS_021_LITTLE_PEOPLE_U0011"
    assert rows[-1]["unit_id"] == "ILCAA_KANAKANAVU_TEXTS_029_SNAKE_U0053"
    assert {row["seed"] for row in rows} == {"20260810"}
    assert all(row["status"] == "PASS" for row in rows)
    assert all(row["visual_review"].startswith("PASS") for row in rows)
    assert all(not row["findings"] for row in rows)
    assert len({row["text_id"] for row in rows}) == 23
    assert len({row["physical_page"] for row in rows}) == 28
    assert sum(int(row["actual_w_count"]) for row in rows) == 206
    assert sum(int(row["actual_m_count"]) for row in rows) == 376
    assert all(row["source_form"] == row["actual_original"] for row in rows)
    assert all(
        row["expected_translation"] == row["actual_translation"] for row in rows
    )
    assert all(row["source_token_support"].endswith("(1.000)") for row in rows)
    assert all(row["gloss_token_support"].endswith("(1.000)") for row in rows)
    assert all(
        row["translation_token_support"].endswith("(1.000)") for row in rows
    )

    report = (ROOT / "data/processed/source_xml_comparison_report.md").read_text(
        encoding="utf-8"
    )
    assert "## Seeded Random Source Checks" in report
    assert "sample size: 30" in report
    assert "S/W/M source-to-XML rows passed: 30; failed: 0" in report
