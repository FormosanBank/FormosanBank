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
    assert [row["id"] for row in rows].count("s36a-opt") == 1
    assert not {"s38a_prime", "s38c_prime"} & {row["id"] for row in rows}


def test_manual_edits_are_pruned_and_absorbed_by_the_transcription() -> None:
    """The six reviewed decisions live in source_examples.tsv, not as records.

    All six of Madeline Boese's 2026-08-07 decisions were re-applied as
    no-ops on every build: the transcription already encodes them, so
    apply_manual_edits.py had nothing to do and warned six times. POL-030
    keeps no-op records by default precisely so that state is visible, and
    reserves --prune for "when the upstream build has genuinely absorbed
    the fix" — which is this case. Pruned with the maintainer's approval
    (2026-09-11); the decisions and their locators survive in
    review_decisions.md, direct_source_checks.tsv and
    rejected_source_examples.tsv.

    The file is kept rather than deleted: an empty MANUAL_EDITS says "no
    hand edits" explicitly, where a missing file says only that nobody
    looked.
    """
    manual_root = ET.parse(ROOT / "CodeAndDocs/manual_edits.xml").getroot()
    assert manual_root.findall("./FILE/S") == [], (
        "manual_edits.xml should carry no records; the transcription owns "
        "these decisions now"
    )

    # The four retained decisions must still be what the build produces, and
    # the two excluded examples must still be absent — the assertions the
    # pruned records used to carry.
    generated = build_root()
    for sentence_id in ("s20c_person", "s20c_car", "s20d", "s36a-opt"):
        assert generated.find(f"S[@id='{sentence_id}']") is not None, (
            f"{sentence_id} must survive in the built corpus"
        )
    ids = {s.get("id") for s in generated.findall("S")}
    assert not {"s38a_prime", "s38c_prime"} & ids

    # POL-028 (amended 2026-09-10): a split's second block takes the first's
    # id plus '-opt'. s36a keeps its id; the i/PREP reading is s36a-opt.
    assert "s36a" in ids and "s36a-opt" in ids
    assert "s36aalt" not in ids, "the pre-POL-028 'alt' spelling must not return"


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
    assert root.find("S[@id='s36a-opt']/FORM").text.endswith("i sayta.")


def test_source_marked_examples_and_alternatives_are_excluded() -> None:
    ids = {sentence.get("id") for sentence in build_root().findall("S")}
    assert {"s20b", "s20d", "s28a", "s36a", "s36a-opt"} <= ids
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
    expected = dict.fromkeys("s18a s18b s20a s28a s30c s30d s32c s33a s33b s33c s36a s36a-opt s36c s37a s38a s38c".split(), ".")
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
    # FORMOSANBANK_ROOT is set by validate.sh; fall back to the checkout this
    # corpus sits in so the suite also runs from a bare `pytest` invocation
    # (four directories up from tests/ is the FormosanBank root).
    sys.path.insert(0, os.environ.get(
        "FORMOSANBANK_ROOT", str(ROOT.parents[1])
    ))
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


def test_apostrophe_is_the_ordinary_amis_letter() -> None:
    """Wu's apostrophe is the bank's apostrophe: ' = /ʡ/, not /ʔ/.

    An earlier pass read it as the glottal stop on the strength of Wu's
    dissertation key and converted it to Ortho113's '^'. That was reverted on
    2026-09-11 (maintainer) because the evidence does not carry it:

    * Ortho94 and Ortho113 **agree** — both give ' = ʡ and ^ = ʔ — so the
      claim departed from both standards, not from one of them.
    * The corpus offers no internal support: the apostrophe appears in two
      tokens of a single word type, and neither 'q' nor '^' occurs at all, so
      there is no two-way glottal contrast here to record.
    * The bank spells this very lexeme with an apostrophe. Whole-word
      matching (ma)na'ay 'not want' across every ami corpus — excluding the
      unrelated root fana' 'know' — finds 81 standard-tier occurrences with
      "'" and none with '^', ILRDF_Dicts among them.

    So the standard tier keeps the apostrophe and both PHON tiers give /ʡ/,
    which is what Orthographies/Ortho94 and Amis_94_113.tsv produce without
    any corpus-specific rule. Only Wu's dissertation p. xviii could overturn
    this, and it has not been read.
    """
    root = ET.parse(BUILD_XML.XML_PATH).getroot()
    expected = {
        "s36a": ("Mana'ay kaku pananum tu sayta.", "Mana'ay kako pananom to sayta."),
        "s36a-opt": ("Mana'ay kaku pananum i sayta.", "Mana'ay kako pananom i sayta."),
        "s36aw0": ("Ma-na'ay", "Ma-na'ay"),
        "s36a-optw0": ("Ma-na'ay", "Ma-na'ay"),
        "s36aw0m1": ("na'ay", "na'ay"),
        "s36a-optw0m1": ("na'ay", "na'ay"),
    }
    affected = {}
    for parent in root.iter():
        original = parent.findtext("FORM[@kindOf='original']")
        if original and "'" in original:
            affected[parent.get("id")] = parent
    assert set(affected) == set(expected)
    for identity, (original, standard) in expected.items():
        parent = affected[identity]
        assert parent.findtext("FORM[@kindOf='original']") == original
        # The apostrophe survives standardization: it is the same letter in
        # Ortho94 and Ortho113, so no rule touches it.
        assert parent.findtext("FORM[@kindOf='standard']") == standard
        for kind in ("original", "standard"):
            phon = parent.findtext("PHON[@kindOf='%s']" % kind)
            assert "ʡ" in phon, (identity, kind, phon)
            assert "ʔ" not in phon, (identity, kind, phon)
    # And '^' must not appear anywhere in the corpus.
    for form in root.iter("FORM"):
        assert "^" not in (form.text or "")


def test_source_attribute_comes_from_the_manifest() -> None:
    """TEXT/@source points a reader back to the paper (POL-053 whitelist).

    The XML is distributed on its own, so a user holding only the file needs
    the source pointer in it — not solely in the corpus README. Built from
    source_manifest.tsv rather than retyped, so the URL and hash live in one
    place (POL-039).
    """
    manifest = BUILD_XML.tsv_rows(BUILD_XML.SOURCE_MANIFEST)
    assert len(manifest) == 1
    source = build_root().get("source")
    assert source is not None, "TEXT/@source must be set"
    assert manifest[0]["url"] in source
    assert manifest[0]["sha256"] in source
    assert len(manifest[0]["sha256"]) == 64


def test_gloss_standardization_is_table_driven() -> None:
    """The CaU -> CAU normalization lives in a TSV, not in the code (POL-039).

    POL-036 makes gloss standardization additive: the source gloss is kept
    and the standardized one recorded alongside it.
    """
    pairs = BUILD_XML.read_gloss_standardizations()
    assert ("CaU", "CAU") in pairs
    # longest source first, so a longer label is never clipped by a prefix
    assert [len(original) for original, _ in pairs] == sorted(
        (len(original) for original, _ in pairs), reverse=True
    )

    word = build_root().find("S[@id='s32b']/W[@id='s32bw0']")
    glosses = word.findall("TRANSL")
    assert [(g.get("kindOf"), g.text) for g in glosses] == [
        ("original", "UV-CaU-give"),
        ("standard", "UV-CAU-give"),
    ]
    # No `ver` on either: `kindOf` discriminates them, and `ver` means
    # "alternative reading" (POL-025), which a standardization is not. V085
    # demanded one until it learned to group on kindOf (2026-09-11).
    assert all(g.get("ver") is None for g in glosses)


def test_translation_notes_come_from_the_source_table() -> None:
    """Translation notes are source data, so they live in the TSV (POL-039)."""
    rows = {row["id"]: row for row in BUILD_XML.read_examples()}
    assert rows["s20c_person"]["translation_1_notes"]
    assert rows["s20c_car"]["translation_2_notes"]

    root = build_root()
    person = root.findall("S[@id='s20c_person']/TRANSL")
    assert person[0].get("notes") == rows["s20c_person"]["translation_1_notes"]
    car = root.findall("S[@id='s20c_car']/TRANSL")
    assert car[1].get("ver") == "alt"
    assert car[1].get("notes") == rows["s20c_car"]["translation_2_notes"]
    # The note survives a TSV round-trip with its embedded double quotes.
    assert '"i.e."' in car[1].get("notes")
