#!/usr/bin/env python3
"""Apply reviewed ePark standard-form repairs without guessing boundaries.

The ePark source mixes alternatives, teaching notation, code-switching, and
orthographic punctuation. Corpus-wide deletion of those markers is unsafe.
This script therefore resolves only reviewed grammar templates and seven
Puyuma en-dash word boundaries. It also performs the declared exclusions and
technical fixes below.

ASCII hyphens and underscores are deliberately preserved. Hyphens are part of
the reviewed Bunun/Thao source orthographies, and underscore represents schwa
in Atayal (among other source uses). Neither character can be removed safely by
a corpus-wide rule.

Run without --apply for a dry run.  A successful second dry run after applying
must report zero changes.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from lxml import etree


ZERO_WIDTH_CHARS = "\u200b\u200c\u200d\ufeff"


def contains_cjk(text: str) -> bool:
    return any("\u3400" <= char <= "\u9fff" for char in text)


# The recordings for these vocabulary rows pronounce the listed primary form.
# The source template remains verbatim in FORM[@kindOf="original"].
TEMPLATE_SURFACES = {
    ("xue_xi_ci_biao_learning_vocabulary/Saaroa/Saaroa.xml", "87"): "tam",
    ("xue_xi_ci_biao_learning_vocabulary/Saaroa/Saaroa.xml", "103"): "tam",
    ("xue_xi_ci_biao_learning_vocabulary/Saaroa/Saaroa.xml", "104"): "ta",
    ("xue_xi_ci_biao_learning_vocabulary/Rukai/Dawu_Rukai.xml", "1057"): "wa",
    ("xue_xi_ci_biao_learning_vocabulary/Rukai/Dawu_Rukai.xml", "1078"): "ma",
    ("xue_xi_ci_biao_learning_vocabulary/Bunun/Kaqun_Bunun.xml", "545"): "pidangqac",
    ("xue_xi_ci_biao_learning_vocabulary/Bunun/Kaqun_Bunun.xml", "1004"): "al",
    ("xue_xi_ci_biao_learning_vocabulary/Saisiyat/Saisiyat.xml", "475"): "hin",
    ("xue_xi_ci_biao_learning_vocabulary/Saisiyat/Saisiyat.xml", "1076"): "kin",
}


# These en dashes separate a Puyuma word or particle from the preceding word.
# Joining the two sides would invent unattested forms, so replace the boundary
# with a space. Other non-ASCII dashes are retained as source punctuation.
PUYUMA_EN_DASH_WORD_BOUNDARY_IDS = {
    ("wen_hua_pian_cultural_section/Puyuma/Nanwang_Puyuma.xml", value)
    for value in ("359", "364", "370", "375", "380", "428", "431")
}


# These source rows are instructions, bibliographic notes, or explicit
# "no such word" sentinels rather than Formosan utterances. They cannot yield
# an MT-facing surface form and are excluded from the corpus. Their exact
# source text remains recoverable in the checked-in source CSV/XML files.
EXCLUDED_NON_SURFACE_IDS = {
    (
        "ju_xing_pian_gao_zhong_sentence_patterns_senior_high/Amis/Xiuguluan_Amis.xml",
        "213_7614",
    ),
    (
        "ju_xing_pian_gao_zhong_sentence_patterns_senior_high/Bunun/Zhuoqun_Bunun.xml",
        "213_13232",
    ),
    (
        "ju_xing_pian_guo_zhong_sentence_patterns_junior_high/Amis/Xiuguluan_Amis.xml",
        "213_23036",
    ),
    (
        "ju_xing_pian_guo_zhong_sentence_patterns_junior_high/Bunun/Zhuoqun_Bunun.xml",
        "213_26506",
    ),
    ("sheng_huo_hui_hua_pian_daily_conversation/Bunun/Zhuoqun_Bunun.xml", "748"),
    ("xue_xi_ci_biao_learning_vocabulary/Kanakanavu/Kanakanavu.xml", "520"),
    ("xue_xi_ci_biao_learning_vocabulary/Kanakanavu/Kanakanavu.xml", "563"),
    ("xue_xi_ci_biao_learning_vocabulary/Kanakanavu/Kanakanavu.xml", "564"),
    ("xue_xi_ci_biao_learning_vocabulary/Kanakanavu/Kanakanavu.xml", "565"),
    ("xue_xi_ci_biao_learning_vocabulary/Kanakanavu/Kanakanavu.xml", "566"),
    ("xue_xi_ci_biao_learning_vocabulary/Rukai/Dona_Rukai.xml", "537"),
    ("xue_xi_ci_biao_learning_vocabulary/Rukai/Dona_Rukai.xml", "809"),
    ("xue_xi_ci_biao_learning_vocabulary/Saisiyat/Saisiyat.xml", "284"),
    ("xue_xi_ci_biao_learning_vocabulary/Saisiyat/Saisiyat.xml", "596"),
    ("xue_xi_ci_biao_learning_vocabulary/Truku/Truku.xml", "536"),
    ("xue_xi_ci_biao_learning_vocabulary/Truku/Truku.xml", "556"),
    ("xue_xi_ci_biao_learning_vocabulary/Yami/Yami.xml", "791"),
    ("yue_du_shu_xie_pian_reading_writing/Kanakanavu/Kanakanavu.xml", "249"),
}


# Two source-faithful technical artifacts fail current validation and carry no
# linguistic content: a metalinguistic asterisk and an invisible BOM.
TECHNICAL_SOURCE_FIXES = {
    (
        "yue_du_shu_xie_pian_reading_writing/Rukai/Dona_Rukai.xml",
        "243",
        "FORM",
    ): "remove-asterisk",
    (
        "jiu_jie_jiao_cai_nine_level_materials/Bunun/Tanqun_Bunun.xml",
        "399-402",
        "TRANSL",
    ): "remove-zero-width",
}


def normalize_standard(
    text: str,
    *,
    template_surface: str | None = None,
    split_puyuma_en_dash: bool = False,
) -> tuple[str, tuple[str, ...]]:
    if template_surface is not None:
        return template_surface, ("grammar-template",)

    if split_puyuma_en_dash and "–" in text:
        return text.replace("–", " "), ("Puyuma-en-dash-word-boundary",)
    return text, ()


def iter_xml_files(xml_dir: Path) -> list[Path]:
    return sorted(path for path in xml_dir.rglob("*.xml") if path.is_file())


def apply_reviewed_source_fixes(
    tree: etree._ElementTree, relative_path: str
) -> tuple[bool, Counter[str]]:
    changed = False
    reasons: Counter[str] = Counter()
    for element in tree.iter("FORM", "TRANSL"):
        parent = element.getparent()
        if parent is None:
            continue
        key = (relative_path, parent.get("id") or "", element.tag)
        action = TECHNICAL_SOURCE_FIXES.get(key)
        if action == "remove-asterisk" and element.text and "*" in element.text:
            element.text = element.text.replace("*", "")
            changed = True
            reasons["technical-asterisk"] += 1
        elif action == "remove-zero-width" and element.text:
            cleaned = element.text.translate(
                {ord(char): None for char in ZERO_WIDTH_CHARS}
            )
            if cleaned != element.text:
                element.text = cleaned
                changed = True
                reasons["technical-zero-width"] += 1
    return changed, reasons


def process(xml_dir: Path, apply: bool) -> tuple[int, Counter[str]]:
    parser = etree.XMLParser(remove_blank_text=False)
    changed_forms = 0
    reasons: Counter[str] = Counter()

    for path in iter_xml_files(xml_dir):
        relative_path = path.relative_to(xml_dir).as_posix()
        tree = etree.parse(str(path), parser)
        changed_file, technical_reasons = apply_reviewed_source_fixes(
            tree, relative_path
        )
        reasons.update(technical_reasons)

        for sentence in list(tree.iter("S")):
            key = (relative_path, sentence.get("id") or "")
            if key in EXCLUDED_NON_SURFACE_IDS:
                parent = sentence.getparent()
                if parent is None:
                    raise ValueError(f"cannot exclude rootless S: {key}")
                if apply:
                    parent.remove(sentence)
                reasons["excluded-non-surface-row"] += 1
                changed_file = True
                continue
            standard = sentence.find('./FORM[@kindOf="standard"]')
            if standard is None or standard.text is None:
                continue
            normalized, form_reasons = normalize_standard(
                standard.text,
                template_surface=TEMPLATE_SURFACES.get(key),
                split_puyuma_en_dash=key in PUYUMA_EN_DASH_WORD_BOUNDARY_IDS,
            )
            if normalized == standard.text:
                continue
            if not normalized:
                raise ValueError(
                    f"normalization emptied {path}: S id={sentence.get('id')!r}"
                )
            standard.text = normalized
            changed_forms += 1
            reasons.update(form_reasons)
            changed_file = True

        if apply and changed_file:
            tree.write(
                str(path),
                encoding="UTF-8",
                xml_declaration=True,
                pretty_print=False,
            )

    return changed_forms, reasons


def inventory_retained_notation(xml_dir: Path) -> Counter[str]:
    parser = etree.XMLParser(remove_blank_text=False)
    inventory: Counter[str] = Counter()
    markers = {
        "-": "ASCII hyphen",
        "_": "underscore",
        "/": "slash",
        "+": "plus",
        "=": "equals",
    }
    for path in iter_xml_files(xml_dir):
        tree = etree.parse(str(path), parser)
        for sentence in tree.iter("S"):
            standard = sentence.find('./FORM[@kindOf="standard"]')
            text = standard.text if standard is not None else None
            if not text:
                continue
            for marker, label in markers.items():
                if marker in text:
                    inventory[label] += 1
            if "(" in text or ")" in text:
                inventory["parenthesis"] += 1
            if contains_cjk(text):
                inventory["CJK"] += 1
    return inventory


def main() -> int:
    default_xml = Path(__file__).resolve().parents[1] / "XML"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml-dir", type=Path, default=default_xml)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    changed, reasons = process(args.xml_dir.resolve(), args.apply)
    mode = "applied" if args.apply else "would change"
    print(f"{mode}: {changed} direct S-standard forms")
    for reason, count in sorted(reasons.items()):
        print(f"  {reason}: {count}")

    if args.apply:
        inventory = inventory_retained_notation(args.xml_dir.resolve())
        print("retained direct S-standard notation (review required):")
        if inventory:
            for marker, count in sorted(inventory.items()):
                print(f"  {marker}: {count}")
        else:
            print("  none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
