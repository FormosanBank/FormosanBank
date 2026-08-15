#!/usr/bin/env python3
"""Lock independently transcribed, page-located source checks."""

from __future__ import annotations

import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Private/source/akiw_2012_sakizaya_affixes_scan.pdf"
SOURCE_SHA256 = "fab787faf0e32cd087ba3dc222734132ad4213ca0804b8d5b32a318e66fbbbee"
XML_ROOT = ROOT / "XML/szy"
REPORT_CSV = ROOT / "CodeAndDocs/source_spot_checks.csv"
XML_NS = "http://www.w3.org/XML/1998/namespace"


@dataclass(frozen=True)
class SourceCheck:
    locator: str
    xml_id: str
    original: str
    standard: str
    translation_zho: str
    note: str = ""
    w_glosses_zho: tuple[str, ...] = ()
    last_w_original: str = ""
    first_w_original: str = ""
    first_w_standard: str = ""
    s_original_notes: str = ""
    m_pairs_zho: tuple[tuple[str, str], ...] = ()
    alternate_translations_zho: tuple[str, ...] = ()
    excluded_ungrammatical: bool = False
    excluded_expert_review: bool = False


CHECKS = [
    SourceCheck(
        "PDF page 33 (printed page 13), example 1",
        "AKIW_SZY_2012_EX_001",
        "mi-pa-baybay ci Taydung.",
        "mipabaybay ci Taydung.",
        "Taydung 在掛蚊帳。",
        last_w_original="Taydung",
    ),
    SourceCheck(
        "PDF page 33 (printed page 13), example 2",
        "AKIW_SZY_2012_EX_002",
        "maluk kaku tu lutuk nu kalitang.",
        "maluk kaku tu lutuk nu kalitang.",
        "我在除花生園的雜草。",
        last_w_original="kalitang",
    ),
    SourceCheck(
        "PDF page 38 (printed page 18), example 17a",
        "AKIW_SZY_2012_EX_017A",
        "mi-cebus tu lami' ci bayi.",
        "micebus tu lami' ci bayi.",
        "阿嬤在澆菜。",
    ),
    SourceCheck(
        "PDF page 37 (printed page 17), example 16",
        "AKIW_SZY_2012_EX_016",
        "mi-amay kiya wawa tu piyang i takuwanan.",
        "miamay kiya wawa tu piyang i takuwanan.",
        "那小孩向我要糖果。",
        w_glosses_zho=("主焦-要求", "那", "小孩", "斜格", "糖果", "處所格", "我.斜格-AN"),
    ),
    SourceCheck(
        "PDF page 38 (printed page 18), example 17d",
        "AKIW_SZY_2012_EX_017D",
        "imelang ci Taymu kiyu si-dinget.",
        "imelang ci Taymu kiyu sidinget.",
        "Taymu 生病所以流鼻涕。",
        "Expert review removed the orphaned null-prefix analysis from S and W.",
        first_w_original="imelang",
        first_w_standard="imelang",
    ),
    SourceCheck(
        "PDF page 61 (printed page 41), example 27a",
        "AKIW_SZY_2012_EX_027A",
        "cacay ku luma' i buyu' ni Panay.",
        "cacay ku luma' i buyu' ni Panay.",
        "Panay 在山上只有一間房屋。",
        "Both printed occurrences use Panay; Vision OCR had read the first as Pamay.",
    ),
    SourceCheck(
        "PDF page 112 (printed page 92), example 82a",
        "AKIW_SZY_2012_EX_082A",
        "mulusu' ku tanang nay zais.",
        "mulusu' ku tanang nay zais.",
        "汗由額頭流下。",
        "The unsegmented original is retained separately even though its standard tier matches example 69a.",
        w_glosses_zho=("流下", "主格", "汗水", "從", "額頭"),
    ),
    SourceCheck(
        "PDF page 53 (printed page 33), table 13 row 1",
        "AKIW_SZY_2012_TABLE_ROW_001",
        "a-mumul",
        "amumul",
        "即將出發",
        last_w_original="a-mumul",
        m_pairs_zho=(("a-", "即將進行"), ("mumul", "出發")),
    ),
    SourceCheck(
        "PDF page 53 (printed page 33), table 13 row 2",
        "AKIW_SZY_2012_TABLE_ROW_002",
        "a-muta'",
        "amuta'",
        "噁心想吐",
        m_pairs_zho=(("a-", "即將進行"), ("muta'", "嘔吐")),
    ),
    SourceCheck(
        "PDF page 53 (printed page 33), table 13 row 7",
        "AKIW_SZY_2012_TABLE_ROW_007",
        "a-sawni",
        "asawni",
        "等一下",
        m_pairs_zho=(("a-", "即將進行"), ("sawni", "剛")),
    ),
    SourceCheck(
        "PDF page 127 (printed page 107), table 75 row 289",
        "AKIW_SZY_2012_TABLE_ROW_289",
        "ales-an",
        "alesan",
        "被放棄",
        "The translation follows the corrected table cell, without the adjacent footnote artifact.",
        m_pairs_zho=(("-an", "被動"), ("ales", "放棄")),
    ),
    SourceCheck(
        "PDF page 66 (printed page 46), table 26 row 54",
        "AKIW_SZY_2012_TABLE_ROW_054",
        "ma-menah",
        "mamenah",
        "長痔瘡",
        "The page image confirms 痔瘡; OCR had substituted 痚瘡 and retained a footnote marker.",
        m_pairs_zho=(("ma-", "長、產生"), ("menah", "肛門")),
    ),
    SourceCheck(
        "PDF page 127 (printed page 107), table 75 row 293",
        "AKIW_SZY_2012_TABLE_ROW_293",
        "kan-an",
        "kanan",
        "被吃",
        "The page image prints 吃！ in the root-meaning cell; OCR had changed the punctuation and retained footnote 95.",
        m_pairs_zho=(("-an", "被動"), ("kan", "吃！")),
    ),
    SourceCheck(
        "PDF page 147 (printed page 127), table 94 row 381",
        "AKIW_SZY_2012_TABLE_ROW_381",
        "mu-lecuh-ay",
        "mulecuhay",
        "生產的",
        "The wrapped page-image cell confirms the complete meaning without OCR punctuation artifacts.",
        m_pairs_zho=(("mu-...-ay", "動作行為的施事者或狀態或性質"), ("lecuh", "生產")),
        alternate_translations_zho=("分娩的，例如產婦",),
    ),
    SourceCheck(
        "PDF page 79 (printed page 59), table 37 row 120",
        "AKIW_SZY_2012_TABLE_ROW_120",
        "mu-lesa'",
        "mulesa'",
        "漏水",
        m_pairs_zho=(("mu-", "主事者焦點"), ("lesa'", "漏水（雨）")),
    ),
    SourceCheck(
        "PDF page 85 (printed page 65), table 45 row 154",
        "AKIW_SZY_2012_TABLE_ROW_154",
        "pa-caliw",
        "pacaliw",
        "借（某物）給",
        s_original_notes="source table base/root: caliw; Mandarin meaning: 借",
    ),
    SourceCheck(
        "PDF page 85 (printed page 65), table 45 row 157",
        "AKIW_SZY_2012_TABLE_ROW_157",
        "pa-daesu",
        "padaesu",
        "給恩賜",
        s_original_notes="source table base/root: daesu; Mandarin meaning: 恩賜",
    ),
    SourceCheck(
        "PDF page 85 (printed page 65), table 45 row 158",
        "AKIW_SZY_2012_TABLE_ROW_158",
        "pa-liluc",
        "paliluc",
        "洗禮（受洗）",
        s_original_notes="source table base/root: liluc; Mandarin meaning: 洗禮",
    ),
    SourceCheck(
        "PDF page 87 (printed page 67), table 47 row 165",
        "AKIW_SZY_2012_TABLE_ROW_165",
        "pi-id'id",
        "piid'id",
        "去烤",
        s_original_notes="source table base/root: id'id; Mandarin meaning: 烤",
    ),
    SourceCheck(
        "PDF page 91 (printed page 71), table 51 row 187",
        "AKIW_SZY_2012_TABLE_ROW_187",
        "sa-lungidac",
        "salungidac",
        "最髒",
        s_original_notes="source table base/root: lungidac; Mandarin meaning: 髒兮兮",
    ),
    SourceCheck(
        "PDF page 98 (printed page 78), table 56 row 216",
        "AKIW_SZY_2012_TABLE_ROW_216",
        "si-lusa'",
        "silusa'",
        "流淚",
        m_pairs_zho=(("si-", "產生、長"), ("lusa'", "淚水")),
    ),
    SourceCheck(
        "PDF page 105 (printed page 85), table 62 row 247",
        "AKIW_SZY_2012_TABLE_ROW_247",
        "hali-pahengad",
        "halipahengad",
        "很會欺騙",
        s_original_notes="source table base/root: pahengad; Mandarin meaning: 欺騙",
    ),
    SourceCheck(
        "PDF page 109 (printed page 89), table 68 row 266",
        "AKIW_SZY_2012_TABLE_ROW_266",
        "tada-macebed",
        "tadamacebed",
        "太密集",
        s_original_notes="source table base/root: macebed; Mandarin meaning: 指草生長得很密集或雜草叢生",
    ),
    SourceCheck(
        "PDF page 111 (printed page 91), table 70 row 278",
        "AKIW_SZY_2012_TABLE_ROW_278",
        "tunu-calay",
        "tunucalay",
        "很多網",
        s_original_notes="source table base/root: calay; Mandarin meaning: 絲線（例如蜘蛛絲、電話線、網路線）",
    ),
    SourceCheck(
        "PDF page 124 (printed page 104), table 72 row 282",
        "AKIW_SZY_2012_TABLE_ROW_282",
        "'neng-a",
        "'nenga",
        "坐下！",
        s_original_notes="source table base/root: 'neng; Mandarin meaning: 坐",
    ),
    SourceCheck(
        "PDF page 131 (printed page 111), table 79 row 302",
        "AKIW_SZY_2012_TABLE_ROW_302",
        "bangbang-aw",
        "bangbangaw",
        "要多勉勵",
        m_pairs_zho=(("-aw", "勸使"), ("bangbang", "火燒旺，可延伸有加油")),
    ),
    SourceCheck(
        "PDF page 136 (printed page 116), table 84 row 320",
        "AKIW_SZY_2012_TABLE_ROW_320",
        "balucu'-ay",
        "balucu'ay",
        "心目中的",
        s_original_notes="source table base/root: balucu'; Mandarin meaning: 心",
    ),
    SourceCheck(
        "PDF page 137 (printed page 117), table 84 row 323",
        "AKIW_SZY_2012_TABLE_ROW_323",
        "uli'-ay",
        "uli'ay",
        "茅草的",
        s_original_notes="source table base/root: uli'; Mandarin meaning: 茅草",
    ),
    SourceCheck(
        "PDF page 137 (printed page 117), table 84 row 325",
        "AKIW_SZY_2012_TABLE_ROW_325",
        "pu'nel-ay",
        "pu'nelay",
        "矮的",
        s_original_notes="source table base/root: pu'nel; Mandarin meaning: 矮（形容事物，延伸形容人矮）",
    ),
    SourceCheck(
        "PDF page 145 (printed page 125), table 92 row 362",
        "AKIW_SZY_2012_TABLE_ROW_362",
        "ma-badi'-ay",
        "mabadi'ay",
        "枯萎的",
        m_pairs_zho=(("ma-...-ay", "動作行為的施事者或狀態或性質"), ("badi'", "枯萎")),
    ),
    SourceCheck(
        "PDF page 145 (printed page 125), table 92 row 364",
        "AKIW_SZY_2012_TABLE_ROW_364",
        "ma-id'id-ay",
        "maid'iday",
        "烤過的",
        s_original_notes="source table base/root: id'id; Mandarin meaning: 烤",
    ),
    SourceCheck(
        "PDF page 145 (printed page 125), table 92 row 365",
        "AKIW_SZY_2012_TABLE_ROW_365",
        "ma-limula'-ay",
        "malimula'ay",
        "很會撒嬌的",
        "The page image and embedded scan text confirm both source apostrophes.",
        m_pairs_zho=(("ma-...-ay", "動作行為的施事者或狀態或性質"), ("limula'", "撒嬌")),
    ),
    SourceCheck(
        "PDF page 147 (printed page 127), table 94 row 376",
        "AKIW_SZY_2012_TABLE_ROW_376",
        "mu'-'neng-ay",
        "mu''nengay",
        "坐下的",
        "The page image and embedded scan text confirm the two source apostrophes in the affixed form.",
        m_pairs_zho=(("mu-...-ay", "動作行為的施事者或狀態或性質"), ("'neng", "坐")),
    ),
    SourceCheck(
        "PDF page 146 (printed page 126), table 93 row 375",
        "AKIW_SZY_2012_TABLE_ROW_375",
        "mi-sanga'-an",
        "misanga'an",
        "建造的",
        m_pairs_zho=(("mi-...-an", "動作發生後產生的物體或對象"), ("sanga'", "建造")),
        alternate_translations_zho=("製作的",),
    ),
    SourceCheck(
        "PDF page 148 (printed page 128), table 95 row 388",
        "AKIW_SZY_2012_TABLE_ROW_388",
        "na-sazipa'-an",
        "nasazipa'an",
        "腳印",
        s_original_notes="source table base/root: sazipa'; Mandarin meaning: 腳掌",
    ),
    SourceCheck(
        "PDF page 152 (printed page 132), table 99 row 421",
        "AKIW_SZY_2012_TABLE_ROW_421",
        "pi-badisusu'-i",
        "pibadisusu'i",
        "去採葡萄！",
        s_original_notes="source table base/root: badisusu'; Mandarin meaning: 葡萄",
        m_pairs_zho=(("pi-...-i", "加強使役"), ("badisusu'", "葡萄")),
    ),
    SourceCheck(
        "PDF page 151 (printed page 131), table 98 row 408",
        "AKIW_SZY_2012_TABLE_ROW_408",
        "pa-pili'-en",
        "papili'en",
        "挑選",
        "The page image confirms both source apostrophes; Vision OCR omitted them.",
        m_pairs_zho=(("pa-...-en", "要促使與詞根相關之動作"), ("pili'", "挑")),
    ),
    SourceCheck(
        "PDF page 152 (printed page 132), table 99 row 420",
        "AKIW_SZY_2012_TABLE_ROW_420",
        "pi-badi'-i",
        "pibadi'i",
        "去曬乾！",
        "The page image confirms the glottal mark; the row affix cell conflicts with the heading, prose, and full form.",
        m_pairs_zho=(("pi-...-i", "加強使役"), ("badi'", "枯萎")),
    ),
    SourceCheck(
        "PDF page 154 (printed page 134), table 101 row 433",
        "AKIW_SZY_2012_TABLE_ROW_433",
        "ta-tip-en",
        "tatipen",
        "往西邊！",
        s_original_notes="source table base/root: tip; Mandarin meaning: 西",
    ),
    SourceCheck(
        "PDF page 142 (printed page 122), example 114a",
        "AKIW_SZY_2012_EX_114A",
        "ka-tayza mi-anin tu silaw",
        "katayza mianin tu silaw",
        "去那邊分一點鹹豬肉！",
        "The Sakizaya source line has no sentence-final punctuation.",
    ),
    SourceCheck(
        "PDF page 155 (printed page 135), example 126b",
        "AKIW_SZY_2012_EX_126B",
        "ta-amis-en ku pa-culil tu wawelwel!",
        "taamisen ku paculil tu wawelwel!",
        "機車騎向北方！",
    ),
    SourceCheck(
        "PDF page 78 (printed page 58), example 46b",
        "AKIW_SZY_2012_EX_046B",
        "balaki tu ci Edi' mu-cebu henay.",
        "balaki tu ci Edi' mucebu henay.",
        "Edi'已經長大了還會偷尿床。",
        note="The source has 已經; OCR had confused 已 with 己.",
        w_glosses_zho=("長大", "斜格", "主格", "人名", "主焦-膀胱", "還"),
    ),
    SourceCheck(
        "PDF page 112 (printed page 92), example 81b",
        "AKIW_SZY_2012_EX_081B",
        "tanu-atimela sa ku zikuc anu caay ka-baca.",
        "tanuatimela sa ku zikuc anu caay kabaca.",
        "如果不常洗衣服的話，就會到處都是跳蚤。",
        note="Continuation parsing formerly appended tanu-/SA/KA- gloss cells to FORM.",
        w_glosses_zho=("tanu-跳蚤", "SA", "主格", "衣服", "如果", "沒有", "KA-洗"),
    ),
    SourceCheck(
        "PDF page 112 (printed page 92), example 82b",
        "AKIW_SZY_2012_EX_082B",
        "tanu-tanang sa ku maluk-ay.",
        "tanutanang sa ku malukay.",
        "農夫汗流浹背。",
        note="The following prose confirms tanu-tanang is one morphological word.",
        w_glosses_zho=("很多-汗水", "SA", "主格", "耕田-AY"),
    ),
    SourceCheck(
        "PDF page 115 (printed page 95), example 83a",
        "AKIW_SZY_2012_EX_083A",
        "mi-acaw kaku tu sa-pi-liluc a nanum.",
        "miacaw kaku tu sapililuc a nanum.",
        "我舀洗澡水。",
        w_glosses_zho=("主焦-舀", "我.主格", "斜格", "工焦-洗澡", "繫詞", "水"),
    ),
    SourceCheck(
        "PDF page 138 (printed page 118), example 108b",
        "AKIW_SZY_2012_EX_108B",
        "akik-en kiya nu bayu-ay a buting!",
        "akiken kiya nu bayuay a buting!",
        "去烤鹹水魚！",
        w_glosses_zho=("烤-使役", "那個", "屬格", "海-AY", "繫詞", "魚"),
    ),
    SourceCheck(
        "PDF page 118 (printed page 98), example 87c",
        "AKIW_SZY_2012_EX_087C",
        "tayza kaku mi-pa-dama tu baeket-ay a ni-muku niza.",
        "tayza kaku mipadama tu baeketay a nimuku niza.",
        "我去幫他搬重物。",
        w_glosses_zho=("去", "我.主格", "主焦-使役-扶", "受格", "重-AY", "繫詞", "NI-扛", "他.屬格"),
    ),
    SourceCheck(
        "PDF page 115 (printed page 95), source-starred example 83c",
        "AKIW_SZY_2012_EX_083C",
        "mi-a-acaw ci Kacaw tu lalilucan a nanum.",
        "mi-a-acaw ci Kacaw tu lalilucan a nanum.",
        "",
        "The source-starred ungrammatical example is excluded under POL-016 and retained in the extraction ledger.",
        excluded_ungrammatical=True,
    ),
    SourceCheck(
        "PDF page 121 (printed page 101), source-starred example 91e",
        "AKIW_SZY_2012_EX_091E",
        "u mising ku pi-sa-tais tu malepiay a zikuc.",
        "u mising ku pi-sa-tais tu malepiay a zikuc.",
        "",
        "The source-starred ungrammatical example is excluded under POL-016 and retained in the extraction ledger.",
        excluded_ungrammatical=True,
    ),
    SourceCheck(
        "PDF page 161 (printed page 141), summary row 480",
        "AKIW_SZY_2012_TABLE_ROW_124",
        "na-cila",
        "nacila",
        "昨天",
        "The page image confirms na-cila. The late row is an exact repeat retained as inventory row 124.",
    ),
    SourceCheck(
        "PDF page 163 (printed page 143), comparison row 491",
        "AKIW_SZY_2012_SUMMARY_ROW_491",
        "ma-la-wacu",
        "malawacu",
        "虛弱",
        "Excluded with the full summary-row dataset after expert review.",
        excluded_expert_review=True,
    ),
    SourceCheck(
        "PDF page 166 (printed page 146), comparison row 506",
        "AKIW_SZY_2012_SUMMARY_ROW_506",
        "ma-ngawa'",
        "mangawa'",
        "缺齒",
        "Excluded with the full summary-row dataset after expert review.",
        excluded_expert_review=True,
    ),
    SourceCheck(
        "PDF page 167 (printed page 147), comparison row 517",
        "AKIW_SZY_2012_SUMMARY_ROW_517",
        "pa-talaw",
        "patalaw",
        "使之驚嚇",
        "Excluded with the full summary-row dataset after expert review.",
        excluded_expert_review=True,
    ),
    SourceCheck(
        "PDF page 167 (printed page 147), comparison row 523",
        "AKIW_SZY_2012_SUMMARY_ROW_523",
        "ama-aw",
        "amaaw",
        "親暱稱爸爸",
        "Excluded with the full summary-row dataset after expert review.",
        excluded_expert_review=True,
    ),
    SourceCheck(
        "PDF page 167 (printed page 147), comparison row 525",
        "AKIW_SZY_2012_SUMMARY_ROW_525",
        "sept-ay",
        "septay",
        "四的",
        "Excluded with the full summary-row dataset after expert review.",
        excluded_expert_review=True,
    ),
    SourceCheck(
        "PDF page 163 (printed page 143), comparison row 490",
        "AKIW_SZY_2012_TABLE_ROW_370",
        "ma-palaw-ay",
        "mapalaway",
        "舞者",
        "The repeated form has a distinct late-table source meaning.",
        alternate_translations_zho=("祭司",),
    ),
    SourceCheck(
        "PDF page 167 (printed page 147), comparison row 511",
        "AKIW_SZY_2012_TABLE_ROW_093",
        "mi-lami'",
        "milami'",
        "探菜",
        "The repeated form has a distinct late-table source meaning.",
        alternate_translations_zho=("摘菜",),
    ),
]


def source_hash() -> str:
    digest = hashlib.sha256()
    with SOURCE.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def xml_rows() -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for xml_path in sorted(XML_ROOT.glob("*.xml")):
        for sentence in ET.parse(xml_path).getroot().findall("S"):
            original_form = sentence.find('./FORM[@kindOf="original"]')
            forms = {
                form.attrib.get("kindOf", ""): form.text or ""
                for form in sentence.findall("FORM")
            }
            translation = next(
                (
                    element.text or ""
                    for element in sentence.findall("TRANSL")
                    if element.attrib.get(f"{{{XML_NS}}}lang") == "zho"
                ),
                "",
            )
            rows[sentence.attrib["id"]] = {
                "original": forms.get("original", ""),
                "standard": forms.get("standard", ""),
                "translation_zho": translation,
                "alternate_translations_zho": [
                    element.text or ""
                    for element in sentence.findall("TRANSL")
                    if element.attrib.get(f"{{{XML_NS}}}lang") == "zho"
                    and element.attrib.get("ver") == "alt"
                ],
                "w_glosses_zho": [
                    next(
                        (
                            element.text or ""
                            for element in word.findall("TRANSL")
                            if element.attrib.get(f"{{{XML_NS}}}lang") == "zho"
                        ),
                        "",
                    )
                    for word in sentence.findall("W")
                ],
                "last_w_original": next(
                    (
                        form.text or ""
                        for word in reversed(sentence.findall("W"))
                        for form in word.findall("FORM")
                        if form.attrib.get("kindOf") == "original"
                    ),
                    "",
                ),
                "first_w_original": next(
                    (
                        form.text or ""
                        for word in sentence.findall("W")
                        for form in word.findall("FORM")
                        if form.attrib.get("kindOf") == "original"
                    ),
                    "",
                ),
                "first_w_standard": next(
                    (
                        form.text or ""
                        for word in sentence.findall("W")
                        for form in word.findall("FORM")
                        if form.attrib.get("kindOf") == "standard"
                    ),
                    "",
                ),
                "s_original_notes": (
                    original_form.attrib.get("notes", "")
                    if original_form is not None
                    else ""
                ),
                "m_pairs_zho": [
                    (
                        next(
                            (
                                form.text or ""
                                for form in morpheme.findall("FORM")
                                if form.attrib.get("kindOf") == "original"
                            ),
                            "",
                        ),
                        next(
                            (
                                transl.text or ""
                                for transl in morpheme.findall("TRANSL")
                                if transl.attrib.get(f"{{{XML_NS}}}lang") == "zho"
                            ),
                            "",
                        ),
                    )
                    for word in sentence.findall("W")
                    for morpheme in word.findall("M")
                ],
            }
    return rows


def run_checks() -> list[dict[str, str]]:
    if source_hash() != SOURCE_SHA256:
        raise RuntimeError("Source scan SHA-256 does not match the manually reviewed PDF")

    indexed = xml_rows()
    results: list[dict[str, str]] = []
    for check in CHECKS:
        actual = indexed.get(check.xml_id, {})
        if check.excluded_ungrammatical or check.excluded_expert_review:
            mismatches = ["excluded_row_present"] if actual else []
        else:
            mismatches = [
                field
                for field in ("original", "standard", "translation_zho")
                if actual.get(field, "") != getattr(check, field)
            ]
        if check.w_glosses_zho and actual.get("w_glosses_zho", []) != list(
            check.w_glosses_zho
        ):
            mismatches.append("w_glosses_zho")
        if check.last_w_original and actual.get("last_w_original", "") != check.last_w_original:
            mismatches.append("last_w_original")
        if check.first_w_original and actual.get("first_w_original", "") != check.first_w_original:
            mismatches.append("first_w_original")
        if check.first_w_standard and actual.get("first_w_standard", "") != check.first_w_standard:
            mismatches.append("first_w_standard")
        legacy_table_root = check.s_original_notes.startswith("source table base/root: ")
        if legacy_table_root:
            expected = check.s_original_notes.removeprefix("source table base/root: ")
            root, separator, meaning = expected.partition("; Mandarin meaning: ")
            actual_pairs = actual.get("m_pairs_zho", [])
            if actual.get("s_original_notes", "") or not actual_pairs or actual_pairs[-1] != (
                root,
                meaning if separator else "",
            ):
                mismatches.append("root_m_pair")
        elif check.s_original_notes and actual.get("s_original_notes", "") != check.s_original_notes:
            mismatches.append("s_original_notes")
        if check.m_pairs_zho and actual.get("m_pairs_zho", []) != list(check.m_pairs_zho):
            mismatches.append("m_pairs_zho")
        if check.alternate_translations_zho and actual.get(
            "alternate_translations_zho", []
        ) != list(check.alternate_translations_zho):
            mismatches.append("alternate_translations_zho")
        results.append(
            {
                "source_locator": check.locator,
                "xml_id": check.xml_id,
                "status": "pass" if not mismatches else "fail",
                "original": actual.get("original", ""),
                "standard": actual.get("standard", ""),
                "translation_zho": actual.get("translation_zho", ""),
                "w_glosses_zho": json.dumps(
                    actual.get("w_glosses_zho", []),
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                "last_w_original": actual.get("last_w_original", ""),
                "first_w_original": actual.get("first_w_original", ""),
                "first_w_standard": actual.get("first_w_standard", ""),
                "s_original_notes": actual.get("s_original_notes", ""),
                "m_pairs_zho": json.dumps(
                    actual.get("m_pairs_zho", []),
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                "alternate_translations_zho": json.dumps(
                    actual.get("alternate_translations_zho", []),
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                "note": "; ".join(
                    [check.note, f"mismatch: {', '.join(mismatches)}" if mismatches else ""]
                ).strip("; "),
            }
        )
    return results


def write_reports(rows: list[dict[str, str]]) -> None:
    with REPORT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

def main() -> None:
    rows = run_checks()
    write_reports(rows)
    failures = sum(row["status"] != "pass" for row in rows)
    print(f"independent source spot checks: {len(rows)}")
    print(f"independent source spot-check failures: {failures}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
