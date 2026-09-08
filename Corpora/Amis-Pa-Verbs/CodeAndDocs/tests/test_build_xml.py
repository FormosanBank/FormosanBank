from __future__ import annotations

import os
import sys
import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "build_xml", ROOT / "CodeAndDocs/build_xml.py"
)
assert SPEC is not None and SPEC.loader is not None
BUILD_XML = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD_XML)


def build_root():
    return BUILD_XML.build_tree(BUILD_XML.read_examples()).getroot()


def strip_derived(sentence: ET.Element) -> bytes:
    stripped = ET.fromstring(ET.tostring(sentence))
    stripped.attrib.pop("after", None)
    stripped.attrib.pop("action", None)
    for parent in stripped.iter():
        for child in list(parent):
            if child.tag == "PHON" or (
                child.tag == "FORM" and child.get("kindOf") == "standard"
            ):
                parent.remove(child)
    for node in stripped.iter():
        if node.text is not None and not node.text.strip():
            node.text = None
        if node.tail is not None and not node.tail.strip():
            node.tail = None
    return ET.tostring(stripped)


def test_development_output_path_is_canonical_xml() -> None:
    assert BUILD_XML.XML_PATH == ROOT / "XML/Amis/pa-verbs.xml"
    assert not (ROOT / "Final_XML").exists()


def test_source_table_is_the_final_reviewed_inventory() -> None:
    rows = BUILD_XML.read_examples()
    assert len(rows) == 29
    assert [row["id"] for row in rows].count("s36aalt") == 1
    assert not {"s38a_prime", "s38c_prime"} & {row["id"] for row in rows}


def test_manual_edit_history_is_retained_as_current_noops() -> None:
    generated = build_root()
    manual_root = ET.parse(ROOT / "CodeAndDocs/manual_edits.xml").getroot()
    records = {
        sentence.get("id"): sentence
        for sentence in manual_root.findall("./FILE/S")
    }
    assert set(records) == {
        "s20c_person",
        "s20c_car",
        "s20d",
        "s36aalt",
        "s38a_prime",
        "s38c_prime",
    }
    for sentence_id in ("s20c_person", "s20c_car", "s20d", "s36aalt"):
        assert strip_derived(records[sentence_id]) == strip_derived(
            generated.find(f"S[@id='{sentence_id}']")
        )
    assert records["s36aalt"].get("after") == "s36a"
    assert records["s38a_prime"].get("action") == "delete"
    assert records["s38c_prime"].get("action") == "delete"


def test_null_is_canonical_at_sentence_word_and_morpheme() -> None:
    sentence = build_root().find("S[@id='s18a']")
    assert sentence is not None
    assert sentence.find("FORM").text == "Papinanum ∅-ci ina ci mamaan."
    null_word = sentence.find("W[@id='s18aw1']")
    assert null_word is not None
    assert null_word.find("FORM").text == "∅-ci"
    assert [node.find("FORM").text for node in null_word.findall("M")] == [
        "∅",
        "ci",
    ]
    assert [node.find("TRANSL").text for node in null_word.findall("M")] == [
        "NOM",
        "NCM",
    ]


def test_sentence_and_word_tiers_have_distinct_segmentation() -> None:
    sentence = build_root().find("S[@id='s20c_person']")
    assert sentence is not None
    assert sentence.find("FORM").text == "Parakaten cingra!"
    assert sentence.find("W/FORM").text == "Pa-rakat-en"


def test_slash_and_case_variants_are_complete_sentences() -> None:
    root = build_root()
    assert root.find("S[@id='s20c_person']/FORM").text == "Parakaten cingra!"
    assert root.find("S[@id='s20c_car']/FORM").text == ("Parakaten kuni a paliding!")
    assert root.find("S[@id='s20d']/FORM").text == "Papirakaten cingra!"
    assert root.find("S[@id='s36a']/FORM").text.endswith("tu sayta.")
    assert root.find("S[@id='s36aalt']/FORM").text.endswith("i sayta.")


def test_source_marked_examples_and_alternatives_are_excluded() -> None:
    ids = {sentence.get("id") for sentence in build_root().findall("S")}
    assert {"s20b", "s20d", "s28a", "s36a", "s36aalt"} <= ids
    assert (
        not {
            "s28b",
            "s30c_prime",
            "s32f",
            "s33d",
            "s36b",
            "s37c",
            "s38a_prime",
            "s38c_prime",
        }
        & ids
    )


def test_printed_pa_fli_boundary_has_no_invented_morpheme_gloss() -> None:
    word = build_root().find("S[@id='s32a']/W[@id='s32aw0']")
    assert word.findtext("FORM") == "Pa-fli"
    assert word.findtext("TRANSL") == "give"
    morphs = word.findall("M")
    assert [m.findtext("FORM") for m in morphs] == ["Pa", "fli"]
    assert [m.get("id") for m in morphs] == ["s32aw0m_a", "s32aw0m_b"]
    assert all(m.find("TRANSL") is None for m in morphs)


def test_source_gloss_typo_has_additive_standard_gloss() -> None:
    root = build_root()
    word = root.find("S[@id='s32b']/W[@id='s32bw0']")
    morph = root.find("S[@id='s32b']/W[@id='s32bw0']/M[@id='s32bw0m1']")
    assert word is not None and morph is not None
    assert word.find("TRANSL[@kindOf='original']").text == "UV-CaU-give"
    assert word.find("TRANSL[@kindOf='standard']").text == "UV-CAU-give"
    assert morph.find("TRANSL[@kindOf='original']").text == "CaU"
    assert morph.find("TRANSL[@kindOf='standard']").text == "CAU"


def test_every_word_has_m_and_only_paired_source_glosses_are_tiered() -> None:
    root = build_root()
    assert all(word.findall("M") for word in root.findall(".//W"))
    analyzed_nodes = root.findall(".//W") + root.findall(".//M")
    paired = [
        node
        for node in analyzed_nodes
        if node.find("TRANSL[@kindOf='standard']") is not None
    ]
    assert len(paired) == 2
    assert all(
        node.find("TRANSL[@kindOf='original']") is not None for node in paired
    )
    assert all(
        node.find("TRANSL").get("kindOf") is None
        for node in analyzed_nodes
        if node not in paired and node.find("TRANSL") is not None
    )


def test_alternate_translations_and_notes_are_explicit() -> None:
    root = build_root()
    translations = root.findall("S[@id='s18c']/TRANSL")
    assert [node.get("ver") for node in translations] == [None, "alt"]

    person = root.find("S[@id='s20c_person']/TRANSL")
    assert person.text == "Walk with him!"
    assert person.get("notes") == "The causee is a little child."

    car = root.findall("S[@id='s20c_car']/TRANSL")
    assert [node.text for node in car] == ["Drive this car!", "Make this car run!"]
    assert [node.get("ver") for node in car] == [None, "alt"]
    assert car[1].get("notes") == 'Introduced by "i.e." in the source.'


def test_ids_are_unique_and_ascii_safe() -> None:
    ids = [node.get("id") for node in build_root().iter() if node.get("id")]
    assert len(ids) == len(set(ids))
    assert all(value.isascii() and "'" not in value for value in ids)


def test_obligatory_i_is_kept_without_reassigning_following_word_ids() -> None:
    sentence = build_root().find("S[@id='s32c']")
    assert sentence.findtext("FORM") == "Mapafli aku ku payau i ci mayawan."
    assert [w.get("id") for w in sentence.findall("W")] == [
        "s32cw0", "s32cw1", "s32cw2", "s32cw3", "s32cwi", "s32cw4", "s32cw5"
    ]
    assert sentence.findtext("W[@id='s32cwi']/FORM") == "i"
    assert sentence.findtext("W[@id='s32cwi']/TRANSL") == "PREP"
    assert sentence.findtext("W[@id='s32cwi']/M/TRANSL") == "PREP"
    assert sentence.findtext("W[@id='s32cw4']/FORM") == "ci"
    assert sentence.findtext("W[@id='s32cw5']/FORM") == "mayaw-an"


def test_sentence_endings_match_printed_pages_6_to_10() -> None:
    # Independent visual inventory; do not derive expectations from the TSV.
    expected = dict.fromkeys("s18a s18b s20a s28a s30c s30d s32c s33a s33b s33c s36a s36aalt s36c s37a s38a s38c".split(), ".")
    expected.update(dict.fromkeys("s20b s20c_person s20c_car s20d s37b s38b".split(), "!"))
    for sentence in build_root().findall("S"):
        text = sentence.findtext("FORM")
        if sentence.get("id") in expected:
            assert text.endswith(expected[sentence.get("id")])
        else:
            assert text[-1] not in ".!?"
    assert all(not w.findtext("FORM").endswith((".", "!")) for w in build_root().iter("W"))


def test_spelling_corrections_preserve_identifiers() -> None:
    rows = BUILD_XML.read_examples()
    before = BUILD_XML.build_tree(rows).getroot()
    row = next(r for r in rows if r["id"] == "s32c")
    row["segmented_form"] = row["segmented_form"].replace("payau", "paysu")
    after = BUILD_XML.build_tree(rows).getroot()
    assert [e.get("id") for e in before.iter() if e.get("id")] == [
        e.get("id") for e in after.iter() if e.get("id")
    ]


def test_source_reviewed_gloss_mismatches_have_exact_scope() -> None:
    from lxml import etree
    sys.path.insert(0, os.environ["FORMOSANBANK_ROOT"])
    from QC.validation.rules.gloss_scrape import g001_marker_skeleton_parity
    root = build_root()
    expected = [
        ("s32a", "s32aw0", "Pa-fli", "give"),
        ("s33c", "s33cw1", "ni", "GEN-NCM"),
        ("s33c", "s33cw3", "ku", "NOM-NCM"),
    ]
    for sid, wid, form, gloss in expected:
        w = root.find(f"S[@id='{sid}']/W[@id='{wid}']")
        assert w.findtext("FORM") == form
        assert w.findtext("TRANSL") == gloss
    tree = etree.ElementTree(etree.fromstring(ET.tostring(root)))
    findings = g001_marker_skeleton_parity(tree, BUILD_XML.XML_PATH)
    assert [(f.rule_id, f.location, f.count) for f in findings] == [
        ("G001", f"S={sid} W={wid}", 1) for sid, wid, _, _ in expected
    ]


def test_final_null_and_original_phonology_are_preserved() -> None:
    root = ET.parse(BUILD_XML.XML_PATH).getroot()
    assert root.findtext("S[@id='s32b']/W[@id='s32bw1']/PHON[@kindOf='original']") == "aku"
    assert root.findtext("S[@id='s18a']/W[@id='s18aw1']/PHON[@kindOf='original']") == "ʦi"
    assert root.findtext("S[@id='s18a']/W[@id='s18aw1']/M[@id='s18aw1m0']/PHON[@kindOf='original']") == "∅"
