#!/usr/bin/env python3
"""Apply reviewed ILRDF sentence-standard repairs without guessing boundaries.

Hyphens have mixed uses in the dictionaries, including proper names,
morphology, punctuation, and Bunun/Thao orthography. Underscores represent
Atayal schwa. Both are retained. This script resolves the reviewed slash,
equals, and parenthetical alternatives and applies explicit repairs for source
extraction artifacts. FORM[@kindOf="original"] remains unchanged.

Run without --apply for a dry run.  A successful second dry run after applying
must report zero changes.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

from lxml import etree


PAREN_RE = re.compile(r"\([^()]*\)")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")
SPACE_RE = re.compile(r"\s+")
FULL_CLAUSE_ALT_RE = re.compile(r"(?<=[.!?])\s*/\s*")
TOKEN_ALT_RE = re.compile(r"(?P<left>\S+?)\s*/\s*(?P<right>\S+)")
TRAILING_PUNCT_RE = re.compile(r"([.!?,;:]+)$")


REVIEWED_SLASH_IDS = {
    "Atayal_2728",
    "Atayal_4629",
    "Atayal_4760",
    "Atayal_5144",
    "Bunun_4696",
    "Bunun_4697",
    "Bunun_4698",
    "Bunun_4699",
    "Bunun_4948",
    "Bunun_4949",
    "Bunun_4950",
    "Bunun_4951",
    "Bunun_4952",
    "Bunun_4953",
    "Bunun_5986",
    "Bunun_6450",
    "Bunun_7761",
    "Bunun_7780",
    "Bunun_8407",
    "Bunun_8408",
    "Paiwan_5128",
    "Paiwan_5320",
    "Sakizaya_5353",
    "Tsou_148",
    "Tsou_200",
    "Tsou_561",
    "Tsou_949",
    "Tsou_1187",
    "Tsou_1189",
    "Tsou_1210",
    "Tsou_2726",
    "Tsou_2864",
}

REVIEWED_EQUALS_IDS = {"Thao_1332", "Thao_4429"}


# Exact standard-tier repairs supported by the dictionary headword, a duplicate
# clean example sentence, or an unambiguous Chinese editor-note boundary.
STANDARD_OVERRIDES = {
    "Kavalan_2291": "nikisasan na tangayaw ay mawtu zau.",
    "Puyuma_888": "sagar mi mabareturetuk dratu buwa dra gamut.",
    "Saaroa_341": "apuaʉnʉmʉ cucuana 'asaruna.",
    "Saaroa_832": "kukicumia tʉnʉmʉa saliaisa hlakana'ana.",
    "Saaroa_1716": "ʉnʉmʉ paapuhla ualuia laihla upatu.",
    "Saaroa_2431": "muasala 'isiparʉtʉnʉmʉ mutatungusu saliamiapihlihli.",
    "Saaroa_3575": "hla'alua maci kapitanʉia ihlaisa macahlia malialualu.",
    "Saaroa_3988": "marua aʉnʉmʉ tapuhlacungu mucukuhlu tapikakua miararuma.",
    "Sakizaya_2511": "u miasikay i satakalaway a luma' 101 ci Panay.",
    "Thao_583": "finlhuqiza ihu buut? ua! finlhuqiza iaku, finlhuqiza mani ihu?",
    "Thao_2539": "mataqaz yaku sa pazay.",
    "Thao_3612": "uka mihu a patatash, haya naak a patatash arahu matash.",
    "Yami_4596": "rarayan mo si wari mo no takzes.",
}


def strip_parenthetical_alternatives(text: str) -> str:
    """Keep the source-preferred outer reading and remove parenthetical ones."""
    previous = None
    while text != previous:
        previous = text
        text = PAREN_RE.sub("", text)
    return text


def choose_first_slash_alternatives(text: str) -> str:
    """Choose the source's first slash-ordered surface alternative.

    A slash after sentence punctuation separates complete clause variants.  A
    slash inside a clause separates neighboring lexical variants.  In the
    latter case punctuation carried by the rejected token is retained.
    """
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
    text: str, *, sentence_id: str | None = None
) -> tuple[str, tuple[str, ...]]:
    override = STANDARD_OVERRIDES.get(sentence_id or "")
    if override is not None:
        return override, ("reviewed-source-repair",)

    reasons: list[str] = []
    normalized = text

    if sentence_id in REVIEWED_EQUALS_IDS and "=" in normalized:
        normalized = normalized.split("=", 1)[0]
        reasons.append("equals-alternative")
    if "(" in normalized or ")" in normalized:
        normalized = strip_parenthetical_alternatives(normalized)
        reasons.append("parenthetical-alternative")
    if sentence_id in REVIEWED_SLASH_IDS and "/" in normalized:
        normalized = choose_first_slash_alternatives(normalized)
        reasons.append("slash-alternative")

    if reasons:
        normalized = SPACE_RE.sub(" ", normalized).strip()
        normalized = re.sub(r"\s+([,.!?;:])", r"\1", normalized)
        normalized = re.sub(r"([.!?])\1+", r"\1", normalized)
    return normalized, tuple(reasons)


def iter_xml_files(xml_dir: Path) -> list[Path]:
    return sorted(path for path in xml_dir.rglob("*.xml") if path.is_file())


def process(xml_dir: Path, apply: bool) -> tuple[int, Counter[str]]:
    parser = etree.XMLParser(remove_blank_text=False)
    changed_forms = 0
    reasons: Counter[str] = Counter()

    for path in iter_xml_files(xml_dir):
        tree = etree.parse(str(path), parser)
        changed_file = False
        for sentence in tree.iter("S"):
            standard = sentence.find('./FORM[@kindOf="standard"]')
            if standard is None or standard.text is None:
                continue
            normalized, form_reasons = normalize_standard(
                standard.text, sentence_id=sentence.get("id")
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
    markers = {"-": "dash", "_": "underscore", "/": "slash", "=": "equals"}
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
            if CJK_RE.search(text):
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
