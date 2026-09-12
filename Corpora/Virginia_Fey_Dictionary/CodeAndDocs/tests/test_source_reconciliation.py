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
    ("S4934", "Nga'ayho han ci nikar a paratoh."),
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


def test_unconfirmed_spelling_does_not_replace_publication(reconciled):
    assert reconciled.findtext('.//S[@id="S3846"]/FORM[@kindOf="original"]') == (
        "Manga'ay kako a tayra haw? Ga'ayto."
    )


def test_distinct_source_meanings_survive(reconciled):
    readings = {}
    for sid in ("S1899", "S1900"):
        sentence = reconciled.find(f'.//S[@id="{sid}"]')
        readings[sid] = [t.text for t in sentence.findall("TRANSL") if t.get(XML_LANG) == "eng"]
    assert readings == {"S1899": ["He separated himeself."], "S1900": ["He was not included."]}


def test_new_ids_do_not_renumber_historical_readings(reconciled):
    ids = {s.get("id") for s in reconciled.iter("S")}
    assert {"S3797", "S3797b", "S5991", "S5991-opt", "S6717", "S6717-opt"} <= ids
    assert not {"S5991b", "S6717b"} & ids


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
