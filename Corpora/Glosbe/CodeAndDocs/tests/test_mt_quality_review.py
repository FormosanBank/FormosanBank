from __future__ import annotations

import csv
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
XML_ROOT = ROOT.parent / "XML"

REVIEWED_ROWS = {
    "GLOSBE_ami_eng_TMEM_U002357": (
        "GLOSBE_STATIC_4fdba9386dd2ccf5de1d",
        "Todongen ci Yihofa Patahekal to Sini'adaay Faloco'",
        "Imitate Jehovah's Compassion",
    ),
    "GLOSBE_ami_eng_TMEM_U004167": (
        "GLOSBE_STATIC_67d813451f0b5c7ed8a4",
        "3 Palahad to Paka'metay to Tireng a Capeling",
        "3 Cultivate Self-Control",
    ),
    "GLOSBE_ami_zho_TMEM_U001187": (
        "GLOSBE_REVIEWED_ZHO_58019b201df8cb0f",
        "Ano caka lecad ko pihakelongan no mararamoday, sasamaan pasifana' to wawa, nengnengen ko \"Salicay No Mi'osiay Tamdaw\" i Mikecolay 2002/8/15. (no Kowaping)",
        "關於夫妻信仰不同時該如何教養孩子,請看《守望臺》2002年8月15日刊的＂讀者來函＂。",
    ),
    "GLOSBE_ami_zho_TMEM_U001286": (
        "GLOSBE_REVIEWED_ZHO_e034f37ac28920db",
        "(Nengnengen ko FANGCALAY CUDAD ato KA'ORIP > KAPAH.)",
        "請點選:＂聖經與生活＂>＂青少年＂)或參看《警醒!》",
    ),
    "GLOSBE_ami_zho_TMEM_U001294": (
        "GLOSBE_REVIEWED_ZHO_284494ea3e6e814d",
        "Ilalikor no saka 19 hahekalan, Mikecolay 1895/9/1 (no Padaka) milengoay to tatodong no pilimekan niyaro'.",
        "在19世紀後期,《守望臺》1895年9月1日刊(英語)談到庇護城的預表意義。",
    ),
    "GLOSBE_ami_zho_TMEM_U001688": (
        "GLOSBE_REVIEWED_ZHO_392b6f545b1ba43f",
        "Nengneng ko kamok no JW Tilifi, pili'en ko MALICAYAY ATO NALIFETAN > MIFALICAY TO KA'ORIP KO SO'LINAY KIMAD.",
        "請上JW電視網,點選＂訪談和經歷＂>＂真理改變人生＂。",
    ),
    "GLOSBE_ami_zho_TMEM_U002184": (
        "GLOSBE_REVIEWED_ZHO_3feb4a0091b845ee",
        "Nengnengen ko Mikecolay, 1988/11/1, \"Salicay no Mi'osiay Tamdaw.\"",
        "請看《守望臺》1988年11月1日刊＂讀者來函＂。",
    ),
    "GLOSBE_ami_zho_TMEM_U002186": (
        "GLOSBE_REVIEWED_ZHO_4238ac8212c39667",
        "Nengnengen ko Mikecolay 2010/11/1, \"Todongen ci Yis Mihinom to Mapatayay ko Salawina a Tamdaw.\" (no Kowaping)",
        "另見《守望臺》2010年11月1日刊《效法耶穌,安慰喪親的人》一文。",
    ),
    "GLOSBE_ami_zho_TMEM_U002195": (
        "GLOSBE_REVIEWED_ZHO_facf85570659eff0",
        "( Nengnengen ko FANGCALAY CUDAD ato KA'ORIP > KAPAH.)",
        "請點選:＂聖經與生活＂>＂青少年＂)或參看《警醒!》",
    ),
}


def test_issue_4_reviewed_rows_remain_source_faithful():
    indexed_records = {}
    with (ROOT / "data/processed/xml_index.csv").open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            indexed_records[row["sentence_id"]] = (row["record_id"], row["xml_file"])

    xml_rows = {}
    for path in sorted(XML_ROOT.rglob("*.xml")):
        for sentence in ET.parse(path).getroot().findall("S"):
            xml_rows[sentence.get("id")] = (
                sentence.findtext("FORM", default=""),
                sentence.findtext("TRANSL", default=""),
            )

    assert set(REVIEWED_ROWS) <= set(indexed_records)
    assert set(REVIEWED_ROWS) <= set(xml_rows)
    for sentence_id, (record_id, form, translation) in REVIEWED_ROWS.items():
        indexed_record_id, xml_file = indexed_records[sentence_id]
        assert indexed_record_id == record_id
        assert xml_file.startswith("XML/")
        assert xml_rows[sentence_id] == (form, translation)
