#!/usr/bin/env python3
"""Derive one surface reading for each ePark sentence-level standard FORM.

The ePark source preserves slash-ordered variants, parenthetical teaching
alternatives, morphology templates, and explicit morpheme boundaries.  Those
source strings stay in FORM[@kindOf="original"].  This script updates only the
direct S/FORM[@kindOf="standard"] text, apart from two narrowly reviewed
technical cleanups documented in ``TECHNICAL_SOURCE_FIXES``.

Run without --apply for a dry run.  A successful second dry run after applying
must report zero changes.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

from lxml import etree


CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")
PAREN_RE = re.compile(r"\([^()]*\)")
SPACE_RE = re.compile(r"\s+")
FULL_CLAUSE_ALT_RE = re.compile(r"(?<=[.!?])\s*/\s*")
TOKEN_ALT_RE = re.compile(r"(?P<left>\S+?)\s*/\s*(?P<right>\S+)")
TRAILING_PUNCT_RE = re.compile(r"([.!?,;:]+)$")
ZERO_WIDTH_RE = re.compile("[\u200b\u200c\u200d\ufeff]")


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


# These en dashes occur inside analyzed Puyuma words. Other non-ASCII dashes
# are reviewed prose punctuation or sound notation and are intentionally kept.
INTERNAL_EN_DASH_IDS = {
    ("wen_hua_pian_cultural_section/Puyuma/Nanwang_Puyuma.xml", value)
    for value in ("359", "364", "370", "375", "380", "428", "431")
}


# These source rows are instructions, bibliographic notes, or explicit
# "no such word" sentinels rather than Formosan utterances. They cannot yield
# an MT-facing surface form and are excluded from the corpus. Their exact
# source text remains recoverable in the checked-in source CSV/XML files.
EXCLUDED_NON_SURFACE_IDS = {
    ("ju_xing_pian_gao_zhong_sentence_patterns_senior_high/Bunun/Zhuoqun_Bunun.xml", "213_13232"),
    ("ju_xing_pian_guo_zhong_sentence_patterns_junior_high/Bunun/Zhuoqun_Bunun.xml", "213_26506"),
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
    ("yue_du_shu_xie_pian_reading_writing/Amis/Hengchun_Amis.xml", "211"),
    ("yue_du_shu_xie_pian_reading_writing/Atayal/YilanZeaol_Atayal.xml", "86"),
    ("yue_du_shu_xie_pian_reading_writing/Kanakanavu/Kanakanavu.xml", "231"),
    ("yue_du_shu_xie_pian_reading_writing/Kanakanavu/Kanakanavu.xml", "334"),
    ("yue_du_shu_xie_pian_reading_writing/Kanakanavu/Kanakanavu.xml", "407"),
    ("yue_du_shu_xie_pian_reading_writing/Paiwan/Central_Paiwan.xml", "26"),
    ("yue_du_shu_xie_pian_reading_writing/Rukai/Dona_Rukai.xml", "7"),
    ("yue_du_shu_xie_pian_reading_writing/Saisiyat/Saisiyat.xml", "41"),
}


# These are genuine Saisiyat song lines whose source presentation encloses the
# complete line in parentheses. Keep the content and drop only the display
# punctuation.
UNWRAP_WHOLE_PAREN_IDS = {
    ("wen_hua_pian_cultural_section/Saisiyat/Saisiyat.xml", str(value))
    for value in range(380, 391)
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


def strip_parenthetical_alternatives(text: str) -> str:
    previous = None
    while text != previous:
        previous = text
        text = PAREN_RE.sub("", text)
    return text


def choose_first_slash_alternatives(text: str) -> str:
    """Select the first source-ordered clause or lexical alternative."""
    while match := FULL_CLAUSE_ALT_RE.search(text):
        boundary = re.search(r"[.!?]", text[match.end() :])
        if boundary is None:
            text = text[: match.start()]
            break
        rejected_end = match.end() + boundary.end()
        text = text[: match.start()] + text[rejected_end:]

    def keep_left(match: re.Match[str]) -> str:
        left = match.group("left")
        right = match.group("right")
        punctuation = TRAILING_PUNCT_RE.search(right)
        if punctuation and not TRAILING_PUNCT_RE.search(left):
            return left + punctuation.group(1)
        return left

    previous = None
    while text != previous and "/" in text:
        previous = text
        text = TOKEN_ALT_RE.sub(keep_left, text)
    return text.replace("/", "")


def normalize_standard(
    text: str,
    *,
    template_surface: str | None = None,
    remove_internal_en_dash: bool = False,
    unwrap_outer_parentheses: bool = False,
) -> tuple[str, tuple[str, ...]]:
    if template_surface is not None:
        return template_surface, ("grammar-template",)

    reasons: list[str] = []
    normalized = text
    if unwrap_outer_parentheses and normalized.startswith("(") and normalized.endswith(")"):
        normalized = normalized[1:-1]
        reasons.append("outer-display-parentheses")
    if "(" in normalized or ")" in normalized:
        normalized = strip_parenthetical_alternatives(normalized)
        reasons.append("parenthetical-alternative")
    if "(" in normalized or ")" in normalized:
        normalized = normalized.replace("(", "").replace(")", "")
        reasons.append("unmatched-parenthesis")
    if "/" in normalized:
        normalized = choose_first_slash_alternatives(normalized)
        reasons.append("slash-alternative")
    if "-" in normalized:
        normalized = normalized.replace("-", "")
        reasons.append("morpheme-boundary")
    if "_" in normalized:
        normalized = normalized.replace("_", "")
        reasons.append("infix-placeholder")
    if remove_internal_en_dash and "–" in normalized:
        normalized = normalized.replace("–", "")
        reasons.append("unicode-morpheme-boundary")
    if CJK_RE.search(normalized):
        normalized = CJK_RE.sub("", normalized)
        reasons.append("inline-teaching-note")

    normalized = SPACE_RE.sub(" ", normalized).strip()
    normalized = re.sub(r"\s+([,.!?;:])", r"\1", normalized)
    normalized = re.sub(r"([.!?])\1+", r"\1", normalized)
    return normalized, tuple(reasons)


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
            cleaned = ZERO_WIDTH_RE.sub("", element.text)
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
                remove_internal_en_dash=key in INTERNAL_EN_DASH_IDS,
                unwrap_outer_parentheses=key in UNWRAP_WHOLE_PAREN_IDS,
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


def find_residuals(xml_dir: Path) -> Counter[str]:
    parser = etree.XMLParser(remove_blank_text=False)
    residuals: Counter[str] = Counter()
    markers = {
        "-": "ASCII dash",
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
                    residuals[label] += 1
            if CJK_RE.search(text):
                residuals["CJK"] += 1
    return residuals


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
        residuals = find_residuals(args.xml_dir.resolve())
        print("residual direct S-standard markers:")
        if residuals:
            for marker, count in sorted(residuals.items()):
                print(f"  {marker}: {count}")
            return 1
        print("  none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
