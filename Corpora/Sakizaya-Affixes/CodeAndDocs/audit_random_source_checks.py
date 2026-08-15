#!/usr/bin/env python3
"""Audit a locked, seeded random sample transcribed from source page images."""

from __future__ import annotations

import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "CodeAndDocs"
SOURCE = ROOT / "Private/source/akiw_2012_sakizaya_affixes_scan.pdf"
SOURCE_SHA256 = "fab787faf0e32cd087ba3dc222734132ad4213ca0804b8d5b32a318e66fbbbee"
XML_ROOT = ROOT / "XML/szy"
REPORT_CSV = CODE / "random_source_checks.csv"
RANDOM_SEED = 20260810
XML_NS = "http://www.w3.org/XML/1998/namespace"


@dataclass(frozen=True)
class Check:
    dataset: str
    unit: str
    page: int
    form: str
    meaning: str
    glosses: tuple[str, ...] = ()
    affix_pair: tuple[str, str] = ()
    root_pair: tuple[str, str] = ()
    status: str = "include"
    retained_xml_id: str = ""
    judgement: str = ""
    edge_case: str = ""
    required_m_pairs: tuple[tuple[str, str], ...] = ()

    @property
    def source_locator(self) -> str:
        label = "example" if self.dataset == "numbered" else "row"
        return f"PDF page {self.page}; {label} {self.unit}"

    @property
    def xml_id(self) -> str:
        if self.retained_xml_id:
            return self.retained_xml_id
        if self.dataset == "numbered":
            digits = "".join(character for character in self.unit if character.isdigit())
            suffix = self.unit[len(digits) :].upper()
            return f"AKIW_SZY_2012_EX_{int(digits):03d}{suffix}"
        prefix = "TABLE_ROW" if self.dataset == "inventory" else "SUMMARY_ROW"
        return f"AKIW_SZY_2012_{prefix}_{int(self.unit):03d}"

    @property
    def theory(self) -> str:
        if self.status == "excluded_ungrammatical":
            return (
                "The source-starred ungrammatical example is preserved in the source ledger "
                "and excluded from released XML under POL-016."
            )
        if self.status == "excluded_exact_repeat":
            return (
                "The repeated source FORM must link to the retained S; a distinct source "
                "meaning must remain as a primary or alternate S translation."
            )
        if self.judgement:
            return (
                "The source asterisk is a grammatical judgement stored in original-FORM "
                "notes; it is not FORM text, and no unattested translation or gloss is added."
            )
        if self.dataset == "numbered":
            return (
                "The source sentence and Mandarin translation map to S; each aligned gloss "
                "cell maps to its W, with source hyphen alignment represented at M level."
            )
        return (
            "The source affixed form and full meaning map to S/W; the printed affix/function "
            "and root/meaning analysis maps to two M tiers."
        )


# Seeded, stratified selection made before transcription. The first 30 cases
# sample numbered examples, inventory rows, and late tables. The final six are
# status-stratified edge draws covering repeats and unique late-table rows.
CHECKS = (
    Check("numbered", "4", 33, "u kadabu ni Buya kaku.", "我是Buya 的媳婦。", ("普名標記", "媳婦", "屬格", "人名", "我.主格")),
    Check("numbered", "15", 37, "ma-duka ku abala nu maku.", "我的肩膀受傷了。", ("主焦-傷", "主格", "肩膀", "屬格", "M-我.屬格")),
    Check("numbered", "17b", 38, "ma-talaw kaku tu alisalap.", "我很怕蜈蚣。", ("主焦-害怕", "我.主格", "斜格", "蜈蚣")),
    Check("numbered", "51b", 83, "nu canan ku ni-pazeng ni Tuy i sulu?", "Tuy 的倉庫放置什麼東西？", ("屬格", "什麼", "主格", "名物化-放", "屬格", "人名", "處所格", "倉庫")),
    Check("numbered", "55a", 86, "bangsis ku balu nu mami'.", "柚子的花很香。", ("香", "主格", "花", "屬格", "柚子")),
    Check("numbered", "63a", 94, "kapah ku balucu' nu apet aku.", "我的妯娌心很善良。", ("善良", "主格", "心", "屬格", "妯娌", "我.屬格")),
    Check("numbered", "70a", 99, "kapah azih-en kiya ngawa' nu katalalan.", "牛的那隻角看起來很好。", ("好", "看-受焦", "那個", "角", "屬格", "牛")),
    Check("numbered", "84c", 115, "a-mi-lupas tu ni-paluma-an nu maku.", "我將要採收我種植的水蜜桃。", ("即將-主焦-桃子", "斜格", "NI-種植-處焦", "屬格", "m-我.屬格")),
    Check(
        "numbered",
        "85d",
        116,
        "amidang tacuwa sa ka-subuk tu!",
        "",
        status="excluded_ungrammatical",
        judgement="* (ungrammatical)",
    ),
    Check(
        "numbered",
        "124c",
        153,
        "pi-adead-i tu pa-zikuc-an ni Kacaw!",
        "去翻 Kacaw 的衣櫥！",
        ("PI-翻-I", "斜格", "PA-衣服-處焦", "屬格", "人名"),
        edge_case="Page-image repair distinguishes source 翻 from OCR 番 in the first gloss cell.",
        required_m_pairs=(("adead", "翻"),),
    ),
    Check("inventory", "3", 53, "a-paluma", "將要種", affix_pair=("a-", "即將進行"), root_pair=("paluma", "種")),
    Check("inventory", "26", 59, "ka-wili", "左邊", affix_pair=("ka-", "方位"), root_pair=("wili", "左")),
    Check("inventory", "52", 66, "ma-izang", "流血", affix_pair=("ma-", "長、產生"), root_pair=("izang", "血")),
    Check("inventory", "61", 67, "ma-kudus", "很瘦", affix_pair=("ma-", "感覺、覺得"), root_pair=("kudus", "瘦")),
    Check("inventory", "144", 84, "pa-ciid", "長芽", affix_pair=("pa-", "動詞化"), root_pair=("ciid", "枝")),
    Check("inventory", "166", 87, "pi-kilim", "去找", affix_pair=("pi-", "動詞化，表祈使"), root_pair=("kilim", "找")),
    Check("inventory", "207", 96, "si-ebuy", "穿襪子", affix_pair=("si-", "穿戴"), root_pair=("ebuy", "襪子")),
    Check("inventory", "225", 101, "ta-pabaw", "往上", affix_pair=("ta-", "方向性"), root_pair=("pabaw", "上面")),
    Check("inventory", "287", 126, "paluma-an", "種的地方", affix_pair=("-an", "處所或地方"), root_pair=("paluma", "種")),
    Check("inventory", "319", 136, "amis-ay", "北方的", affix_pair=("-ay", "狀態或性質"), root_pair=("amis", "北")),
    Check("inventory", "328", 137, "tanaya'-ay", "長的", affix_pair=("-ay", "狀態或性質"), root_pair=("tanaya'", "長")),
    Check("inventory", "360", 144, "ka-si-lupas-an", "水蜜桃產期", affix_pair=("ka-si-...-an", "特定的時間"), root_pair=("lupas", "桃子、水蜜桃")),
    Check("summary", "435", 157, "hali-emu", "愛吃年糕", status="excluded_exact_repeat", retained_xml_id="AKIW_SZY_2012_TABLE_ROW_241"),
    Check("summary", "460", 159, "imelang-ay", "病人", status="excluded_exact_repeat", retained_xml_id="AKIW_SZY_2012_TABLE_ROW_305"),
    Check("summary", "466", 160, "pi-nanum", "要喝水！", status="excluded_exact_repeat", retained_xml_id="AKIW_SZY_2012_TABLE_ROW_162"),
    Check("summary", "471", 160, "atip-en", "去夾！", status="excluded_exact_repeat", retained_xml_id="AKIW_SZY_2012_TABLE_ROW_334"),
    Check("summary", "475", 160, "adidem-an", "桑樹園", status="excluded_exact_repeat", retained_xml_id="AKIW_SZY_2012_TABLE_ROW_284"),
    Check("summary", "498", 166, "hali-kan", "愛吃", status="excluded_exact_repeat", retained_xml_id="AKIW_SZY_2012_TABLE_ROW_246"),
    Check("summary", "499", 166, "hina-puling", "常跌倒", status="excluded_exact_repeat", retained_xml_id="AKIW_SZY_2012_TABLE_ROW_255"),
    Check("summary", "501", 166, "ka-laway", "大嘴巴", status="excluded_exact_repeat", retained_xml_id="AKIW_SZY_2012_TABLE_ROW_020"),
    Check("numbered", "31a", 64, "balud-han ni Kacaw ku kasuy.", "Kacaw 將木材綑綁起來。", ("綁-受焦", "屬格", "人名", "主格", "木材"), status="excluded_exact_repeat", retained_xml_id="AKIW_SZY_2012_EX_018C"),
    Check("numbered", "94a", 126, "paluma kaku tu paza' i nu zikuz-an nu luma'.", "我在我家後院種香蕉。", ("種", "我.主格", "斜格", "香蕉", "處所格", "屬格", "後面-處焦", "屬格", "家"), status="excluded_exact_repeat", retained_xml_id="AKIW_SZY_2012_EX_021A"),
    Check("inventory", "183", 91, "sa-aledah", "講話很刺耳", status="excluded_exact_repeat", retained_xml_id="AKIW_SZY_2012_TABLE_ROW_182"),
    Check("inventory", "281", 124, "lekal-a", "起來！", status="excluded_exact_repeat", retained_xml_id="AKIW_SZY_2012_TABLE_ROW_280"),
    Check(
        "summary",
        "492",
        163,
        "ma-lalikid",
        "豐年祭",
        affix_pair=("ma-", "文化相關詞彙"),
        root_pair=("lalikid", "被流走"),
        edge_case="Unique late-table source analysis must survive as M tiers, not only in the CSV ledger.",
    ),
    Check(
        "summary",
        "495",
        163,
        "si-sepi",
        "有福氣的",
        affix_pair=("si-", "文化相關詞彙"),
        root_pair=("sepi", "夢"),
        edge_case="Unique late-table source analysis must survive as M tiers, not only in the CSV ledger.",
    ),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def direct_translation(element: ET.Element) -> str:
    return next(
        (
            translation.text or ""
            for translation in element.findall("TRANSL")
            if translation.attrib.get(f"{{{XML_NS}}}lang") == "zho"
            and not translation.attrib.get("ver")
        ),
        "",
    )


def xml_rows() -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for path in sorted(XML_ROOT.glob("*.xml")):
        for sentence in ET.parse(path).getroot().findall("S"):
            original = sentence.find('./FORM[@kindOf="original"]')
            words = sentence.findall("W")
            rows[sentence.attrib["id"]] = {
                "source": sentence.attrib.get("source", ""),
                "original": original.text or "" if original is not None else "",
                "original_notes": original.attrib.get("notes", "") if original is not None else "",
                "standard_present": sentence.find('./FORM[@kindOf="standard"]') is not None,
                "translation": direct_translation(sentence),
                "translations": tuple(
                    translation.text or ""
                    for translation in sentence.findall("TRANSL")
                    if translation.attrib.get(f"{{{XML_NS}}}lang") == "zho"
                ),
                "w_originals": tuple(
                    (word.find('./FORM[@kindOf="original"]').text or "")
                    for word in words
                    if word.find('./FORM[@kindOf="original"]') is not None
                ),
                "w_glosses": tuple(direct_translation(word) for word in words),
                "m_pairs": tuple(
                    (
                        morpheme.find('./FORM[@kindOf="original"]').text or "",
                        direct_translation(morpheme),
                    )
                    for word in words
                    for morpheme in word.findall("M")
                    if morpheme.find('./FORM[@kindOf="original"]') is not None
                ),
            }
    return rows


def report_index() -> dict[tuple[str, str], dict[str, str]]:
    numbered = {
        ("numbered", f"{int(row['example'])}{row['subexample']}"): row
        for row in read_csv(CODE / "extraction_report.csv")
    }
    inventory = {
        ("inventory", str(int(row["seq"]))): row
        for row in read_csv(CODE / "table_extraction_report.csv")
    }
    summary = {
        ("summary", str(int(row["seq"]))): row
        for row in read_csv(CODE / "summary_table_extraction_report.csv")
    }
    return numbered | inventory | summary


def source_report_checks(check: Check, report: dict[str, str]) -> list[str]:
    failures: list[str] = []
    if report["status"] != check.status:
        failures.append("source disposition")
    if int(report["page"]) != check.page:
        failures.append("source page")
    if report["form"] != check.form:
        failures.append("source FORM")
    meaning_field = "translation_zho" if check.dataset == "numbered" else "meaning_zho"
    if report[meaning_field] != check.meaning:
        failures.append("source translation/meaning")
    if report.get("retained_xml_id", "") != check.retained_xml_id:
        failures.append("retained XML link")
    if check.dataset == "numbered":
        expected_gloss = " ".join(check.glosses)
        if report["source_gloss"] != expected_gloss:
            failures.append("source gloss transcription")
        if report["source_judgement"] != check.judgement:
            failures.append("source judgement")
    elif check.status == "include":
        if (report["affix_form"], report["affix_function_zho"]) != check.affix_pair:
            failures.append("source affix analysis")
        if (report["base_form"], report["base_meaning_zho"]) != check.root_pair:
            failures.append("source root analysis")
    return failures


def xml_checks(check: Check, actual: dict[str, object]) -> list[str]:
    failures: list[str] = []
    if actual["original"] != check.form:
        failures.append("XML S original FORM")
    if not actual["standard_present"]:
        failures.append("XML S standard FORM")
    if check.meaning:
        if check.meaning not in actual["translations"]:
            failures.append("XML S translation/alternate")
    elif actual["translations"]:
        failures.append("unattested XML S translation")
    if check.status == "include":
        if check.dataset == "numbered":
            expected_source = f"PDF page {check.page}; example {check.unit}"
        elif check.dataset == "inventory":
            expected_source = f"PDF page {check.page}; affix inventory row {int(check.unit)}"
        else:
            report = report_index()[(check.dataset, check.unit)]
            expected_source = f"PDF page {check.page}; {report['source_table']} row {int(check.unit)}"
        if actual["source"] != expected_source:
            failures.append("XML source locator")
    if check.dataset == "numbered":
        if check.judgement:
            if any(actual["w_glosses"]):
                failures.append("unattested XML W gloss")
        elif actual["w_glosses"] != check.glosses:
            failures.append("XML W gloss sequence")
        if actual["original_notes"] != check.judgement:
            failures.append("XML source judgement note")
        if not set(check.required_m_pairs).issubset(set(actual["m_pairs"])):
            failures.append("XML required M FORM/TRANSL pair")
    elif check.status == "include":
        if actual["w_originals"] != (check.form,):
            failures.append("XML W original FORM")
        if actual["m_pairs"] != (check.affix_pair, check.root_pair):
            failures.append("XML affix/root M pairs")
    return failures


def run_checks() -> list[dict[str, str]]:
    if len(CHECKS) != 36:
        raise RuntimeError(f"Expected 36 locked random checks, found {len(CHECKS)}")
    if sha256(SOURCE) != SOURCE_SHA256:
        raise RuntimeError("Source scan hash changed since the page-image review")

    reports = report_index()
    actual_rows = xml_rows()
    results: list[dict[str, str]] = []
    for order, check in enumerate(CHECKS, 1):
        report = reports.get((check.dataset, check.unit))
        failures = ["source report row missing"] if report is None else source_report_checks(check, report)
        actual = actual_rows.get(check.xml_id)
        if check.status == "excluded_ungrammatical":
            if actual is not None:
                failures.append("excluded source-starred XML row present")
        elif actual is None:
            failures.append("retained/generated XML row missing")
        else:
            failures.extend(xml_checks(check, actual))
        results.append(
            {
                "selection_seed": str(RANDOM_SEED),
                "selection_order": str(order),
                "stratum": check.dataset,
                "source_locator": check.source_locator,
                "source_form": check.form,
                "source_translation_or_meaning": check.meaning,
                "mapping_theory": check.theory,
                "expected_disposition": check.status,
                "actual_xml_id": check.xml_id,
                "edge_case_or_remediation": check.edge_case,
                "status": "pass" if not failures else "fail",
                "failures": "; ".join(failures),
            }
        )
    return results


def write_results(rows: list[dict[str, str]]) -> None:
    with REPORT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

def main() -> None:
    rows = run_checks()
    write_results(rows)
    failures = [row for row in rows if row["status"] != "pass"]
    print(f"random source checks: {len(rows)}")
    print(f"random source check failures: {len(failures)}")
    if failures:
        print(json.dumps(failures, ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
