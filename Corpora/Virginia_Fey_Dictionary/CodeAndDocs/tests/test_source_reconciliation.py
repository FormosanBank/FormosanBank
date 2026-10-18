"""Source witnesses and retained corrections, independent of repair-table values."""

import shutil
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
from lxml import etree

CODE = Path(__file__).resolve().parents[1]
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


@pytest.fixture(scope="module")
def reconciled(tmp_path_factory):
    path = tmp_path_factory.mktemp("source") / "Amis.xml"
    shutil.copyfile(CODE / "pre_correction_snapshot/Amis/Amis.xml", path)
    subprocess.run(
        [sys.executable, str(CODE / "reconcile_source.py"), "--path", str(path)],
        check=True, capture_output=True, text=True,
    )
    return etree.parse(str(path))


@pytest.mark.parametrize("sentence_id,expected", [
    ("S167", "Masaso'araw kita anini."),
    ("S2278", "Maolah kako a tayra a misalama."),
    ("S2805", "Palafacen koya kolong ta ira a makilim nira ko kakaenen."),
    ("S2908", "Cilamit ko sowal no Kawas i faloco' ako."),
    ("S4934", "Nga'ayho han ci Nikar a paratoh."),
    ("S3797b", "nanamanan a demak"),
    ("S6913", "o pakoyocay."),
    ("S6717", "O kalatolo konini."),
    ("S1730", "Mihakeno ci Pitiro ci Yisan."),
    ("S1899", "Mihawitid cingra."),
    ("S1900", "Mahawitid cingra."),
    ("S6905", "karakimaday a tamdaw"),
    ("S2591", "Mikiric ko nanom to sera."),
    ("S6914", "Cingra ko mafana'ay."),
    ("S3969", "Payniyaniyah kita a mitolon"),
    ("S6922", "Kinapinapina kako a milicay cingraan"),
    ("S5203", "Safaw cecay ko fafoy niyam."),
])
def test_restores_source_words(reconciled, sentence_id, expected):
    # Raw source / corrected Word rows cited in source_field_repairs.tsv and
    # source_decisions.json, including whole-word and word-internal omissions.
    assert reconciled.findtext(f'.//S[@id="{sentence_id}"]/FORM[@kindOf="original"]') == expected


def test_sentence_initial_capital_g_is_ng(reconciled):
    # Maintainer 2026-10-17 (S3846/S4934): "Both Ng in original".
    assert reconciled.findtext('.//S[@id="S3846"]/FORM[@kindOf="original"]') == (
        "Manga'ay kako a tayra haw? Nga'ayto."
    )
    assert reconciled.findtext('.//S[@id="S4934"]/FORM[@kindOf="original"]').startswith("Nga'ayho")


def test_generated_g_follows_source_guide():
    # Guide page 20: g is the ng sound; shared Ortho113 phonology gives /ŋ/.
    sentence = etree.parse(str(CODE.parent / "XML/Amis/Amis.xml")).find('.//S[@id="S3846"]')
    assert sentence.findtext('FORM[@kindOf="original"]') == "Manga'ay kako a tayra haw? Nga'ayto."
    assert sentence.findtext('FORM[@kindOf="standard"]') == "Manga'ay kako a tayra haw? Nga'ayto."
    for kind in ("original", "standard"):
        assert sentence.findtext(f'PHON[@kindOf="{kind}"]') == (
            "maŋaʡaj kak[o|u] a tajra ħaw ŋaʡajt[o|u]"
        )


def test_distinct_source_meanings_survive(reconciled):
    readings = {}
    for sid in ("S1899", "S1900"):
        sentence = reconciled.find(f'.//S[@id="{sid}"]')
        readings[sid] = [t.text for t in sentence.findall("TRANSL") if t.get(XML_LANG) == "eng"]
    assert readings == {"S1899": ["He separated himeself."], "S1900": ["He was not included."]}


def test_new_ids_do_not_renumber_historical_readings(reconciled):
    ids = {s.get("id") for s in reconciled.iter("S")}
    assert {"S3797", "S3797b", "S5991", "S6717", "S6717-opt"} <= ids
    assert not {"S5991b", "S6717b"} & ids


def test_same_form_sentences_are_one_sentence(reconciled):
    # Maintainer 2026-10-17: "Merge each pair into one S with ver=\"alt\" translations (POL-025)".
    ids = {s.get("id") for s in reconciled.iter("S")}
    merged_away = {"S2843", "S3026", "S6916", "S6241", "S5023", "S5280", "S5703", "S5991-opt"}
    assert not merged_away & ids
    forms = [s.findtext('FORM[@kindOf="original"]') for s in reconciled.iter("S")]
    assert len(forms) == len(set(forms)) == 2042
    s1945 = [(t.get(XML_LANG), t.get("ver"), t.text) for t in reconciled.find('.//S[@id="S1945"]').findall("TRANSL")]
    assert s1945 == [("eng", None, "rainbow"), ("zho", None, "彩虹"), ("eng", "alt", "a rainbow")]


def test_only_source_content_notes_remain(reconciled):
    # Maintainer 2026-10-17: drop notes that only repeat converter-damaged sheet text.
    notes = {s.get("id"): s.find('FORM[@kindOf="original"]').get("notes") for s in reconciled.iter("S")}
    assert notes["S3560"] is None
    assert notes["S4934"] is None
    assert notes["S1193"] == "Katalawan ko demak nira. Literally"
    assert notes["S5991"] == "talakal / tilo ni Idek."
    assert "S6908" not in notes  # ceco. dropped (maintainer 2026-10-17)
    assert sum(1 for n in notes.values() if n) == 74


@pytest.mark.parametrize("sentence_id,expected", [
    ("S277", "This is evidence of his spirituality."),
    ("S2868", "I know how to do it."),
    ("S3943", "希望你講得頭頭是道"),
    ("S5977", "他正翹首企盼著"),
    ("S6504", "Go with me to his home."),
])
def test_retains_reviewed_translation_repairs(reconciled, sentence_id, expected):
    sentence = reconciled.find(f'.//S[@id="{sentence_id}"]')
    assert expected in [t.text for t in sentence.findall("TRANSL")]


def test_audit_rejects_form_loss_even_when_counts_match(reconciled, tmp_path):
    path = tmp_path / "corrupted.xml"
    tree = etree.ElementTree(etree.fromstring(etree.tostring(reconciled)))
    tree.find('.//S[@id="S2908"]/FORM[@kindOf="original"]').text = (
        "Cilamit ko sowal no was i faloco' ako."
    )
    tree.write(str(path), encoding="utf-8", xml_declaration=True)
    result = subprocess.run(
        [sys.executable, str(CODE / "audit_source_alignment.py"), "--path", str(path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "S2908: original FORM differs" in result.stdout


def test_reconciliation_rejects_changed_baseline(tmp_path):
    path = tmp_path / "changed-baseline.xml"
    path.write_bytes((CODE / "pre_correction_snapshot/Amis/Amis.xml").read_bytes() + b"\n")
    result = subprocess.run(
        [sys.executable, str(CODE / "reconcile_source.py"), "--path", str(path)],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "not the pinned POL-035 baseline" in result.stderr


def test_recorded_word_correction_cannot_be_overwritten(tmp_path):
    shutil.copyfile(CODE / "source_decisions.json", tmp_path / "source_decisions.json")
    (tmp_path / "source_field_repairs.tsv").write_text(
        "source_row\tsource_form\tform\tevidence\traw_form\n"
        "4934\tGa'ayho han  r a paratoh.\tGa'ayho han ci Nikar a paratoh."
        "\tr.txt:618\tGa'ayho han ci Nikar a paratoh.\n"
    )
    spec = importlib.util.spec_from_file_location("reconcile_source", CODE / "reconcile_source.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(SystemExit, match="duplicate source decision for row 4934"):
        module.load_decisions(tmp_path / "source_decisions.json")


def test_round_three_rulings(reconciled):
    # Maintainer 2026-10-17 (Fey review round 3).
    assert reconciled.findtext('.//S[@id="S4934"]/FORM[@kindOf="original"]') == "Nga'ayho han ci Nikar a paratoh."
    assert reconciled.findtext('.//S[@id="S6901"]/FORM[@kindOf="original"]') == "ano imatini."
    s413 = [(t.get(XML_LANG), t.get("ver"), t.text) for t in reconciled.find('.//S[@id="S413"]').findall("TRANSL")]
    assert s413 == [
        ("eng", None, "He saved me (physically)"),
        ("eng", "alt", "He saved me (spiritually)"),
        ("zho", None, "他救我，由肉體上如從溺水之險境中"),
        ("zho", "alt", "他救我，精神或屬靈上"),
    ]
