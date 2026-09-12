#!/usr/bin/env python3
"""Apply the reviewed POL-024 decisions to NTU S translations.

The specialized gloss audit reports every trailing parenthetical without a
``notes`` attribute. The signal is intentionally soft because source-authored
naturalistic elaborations may remain inline. This late pass runs after all
sentence alternatives have been generated and applies the corpus review:

* Grammar parentheticals are lexical or analytic qualifiers and move to notes.
* Sentence parentheticals move to notes except for nine reviewed naturalistic
  elaborations.
* Five story parentheticals are explicit analytic or recording commentary and
  move to notes; the other story cases remain inline.

The complete input manifest is pinned. Any source, parser, or upstream
transformation drift stops the build so a new parenthetical cannot inherit an
old judgment accidentally. The already-applied manifest is also accepted to
keep this repair independently idempotent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from lxml import etree


XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
TRAILING_PAREN = re.compile(r"\(([^()]{2,})\)\s*$")

EXPECTED_INPUT_COUNT = 453
EXPECTED_INPUT_DIGEST = (
    "ddd647305a31083627fa2c58484f922d3b48bc62f2254d6a43541d7b21f7bed9"
)
EXPECTED_RETAINED_COUNT = 60
EXPECTED_RETAINED_DIGEST = (
    "e2bdbf648960fb55e404f9514e6f2cafb1e59ba8f3fa19e94a220c09e3c29aec"
)
EXPECTED_SECTION_COUNTS = Counter({
    "Grammar": 302,
    "Sentences": 95,
    "Stories": 56,
})
EXPECTED_REPAIR_COUNTS = Counter({
    "Grammar": 302,
    "Sentences": 86,
    "Stories": 5,
})

Key = tuple[str, str, str]

NATURALISTIC_SENTENCE_KEYS: frozenset[Key] = frozenset({
    ("Sentences/Kanakanavu/Kanakanavu.xml", "1_S_339", "eng"),
    ("Sentences/Kanakanavu/Kanakanavu.xml", "2_S_1_v1", "zho"),
    ("Sentences/Kanakanavu/Kanakanavu.xml", "2_S_1_v1-opt1", "zho"),
    ("Sentences/Kanakanavu/Kanakanavu.xml", "2_S_1_v2", "zho"),
    ("Sentences/Kanakanavu/Kanakanavu.xml", "2_S_1_v2-opt1", "zho"),
    ("Sentences/Kanakanavu/Kanakanavu.xml", "3_S_502", "eng"),
    ("Sentences/Rukai/Rukai.xml", "20200530-FW-Ken-2_S_9", "zho"),
    ("Sentences/Rukai/Rukai.xml", "20200530-FW-Ken-2_S_9", "eng"),
    ("Sentences/Rukai/Rukai.xml", "20200531-FW-Yongfu-1_S_19", "eng"),
})

STORY_COMMENTARY_KEYS: frozenset[Key] = frozenset({
    (
        "Stories/Kanakanavu/"
        "Kanakanavu_kkvNr_domestic_troubles_Muu.xml",
        "kkvNr_domestic_troubles_Muu_S_41",
        "eng",
    ),
    (
        "Stories/Kanakanavu/Kanakanavu_kkvNr_sad_song_Muu.xml",
        "kkvNr_sad_song_Muu_S_3",
        "eng",
    ),
    (
        "Stories/Kavalan/Kavalan_KavNr-frog_abas.xml",
        "KavNr-frog_abas_S_3",
        "zho",
    ),
    (
        "Stories/Rukai/"
        "Rukai_RukaiNr-work by men and women_taugadhu.xml",
        "RukaiNr-work by men and women_taugadhu_S_83",
        "zho",
    ),
    (
        "Stories/Seediq/Seediq_sdqNr-childhood_micang 2020s.xml",
        "sdqNr-childhood_micang 2020s_S_45",
        "zho",
    ),
})


@dataclass(frozen=True)
class Candidate:
    relative: str
    sentence_id: str
    lang: str
    text: str
    path: Path
    tree: etree._ElementTree
    translation: etree._Element

    @property
    def key(self) -> Key:
        return self.relative, self.sentence_id, self.lang

    @property
    def row(self) -> list[str]:
        return [self.relative, self.sentence_id, self.lang, self.text]


def digest_rows(candidates: list[Candidate]) -> str:
    rows = [candidate.row for candidate in sorted(
        candidates, key=lambda candidate: candidate.row
    )]
    payload = json.dumps(
        rows, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def collect_candidates(xml_dir: Path) -> list[Candidate]:
    candidates: list[Candidate] = []
    for path in sorted(xml_dir.rglob("*.xml")):
        tree = etree.parse(str(path))
        relative = path.relative_to(xml_dir).as_posix()
        for sentence in tree.getroot().findall("S"):
            sentence_id = sentence.get("id") or ""
            for translation in sentence.findall("TRANSL"):
                value = (translation.text or "").strip()
                if translation.get("notes") or not TRAILING_PAREN.search(value):
                    continue
                candidates.append(Candidate(
                    relative=relative,
                    sentence_id=sentence_id,
                    lang=translation.get(XML_LANG) or "",
                    text=value,
                    path=path,
                    tree=tree,
                    translation=translation,
                ))
    return candidates


def split_trailing_parenthetical(value: str) -> tuple[str, str]:
    """Return the text before the final balanced parenthetical and its body."""
    value = value.strip()
    if not value.endswith(")"):
        raise AssertionError(f"translation has no trailing parenthetical: {value!r}")
    depth = 0
    for index in range(len(value) - 1, -1, -1):
        char = value[index]
        if char == ")":
            depth += 1
        elif char == "(":
            depth -= 1
            if depth == 0:
                base = value[:index].rstrip()
                commentary = value[index + 1:-1]
                if not base or len(commentary.strip()) < 2:
                    raise AssertionError(
                        f"unsafe trailing-parenthetical split: {value!r}"
                    )
                return base, commentary
    raise AssertionError(f"unbalanced trailing parenthetical: {value!r}")


def should_repair(candidate: Candidate) -> bool:
    section = candidate.relative.split("/", 1)[0]
    if section == "Grammar":
        return True
    if section == "Sentences":
        return candidate.key not in NATURALISTIC_SENTENCE_KEYS
    if section == "Stories":
        return candidate.key in STORY_COMMENTARY_KEYS
    raise AssertionError(f"unexpected XML section: {candidate.relative}")


def repair_candidate(candidate: Candidate) -> None:
    base, _ = split_trailing_parenthetical(candidate.text)
    candidate.translation.text = base
    candidate.translation.set(
        "notes", f"source translation commentary: {candidate.text}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml-dir", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    xml_dir = args.xml_dir.resolve()

    candidates = collect_candidates(xml_dir)
    digest = digest_rows(candidates)
    if (
        len(candidates) == EXPECTED_RETAINED_COUNT
        and digest == EXPECTED_RETAINED_DIGEST
    ):
        print("Reviewed translation parentheticals already applied")
        print(f"  naturalistic elaborations retained inline: {len(candidates)}")
        return 0
    if len(candidates) != EXPECTED_INPUT_COUNT or digest != EXPECTED_INPUT_DIGEST:
        raise AssertionError(
            "translation-parenthetical input drifted: "
            f"expected {EXPECTED_INPUT_COUNT} rows / {EXPECTED_INPUT_DIGEST}, "
            f"found {len(candidates)} rows / {digest}"
        )

    section_counts = Counter(
        candidate.relative.split("/", 1)[0] for candidate in candidates
    )
    if section_counts != EXPECTED_SECTION_COUNTS:
        raise AssertionError(
            f"translation-parenthetical section counts drifted: {section_counts}"
        )
    present_keys = {candidate.key for candidate in candidates}
    expected_keys = NATURALISTIC_SENTENCE_KEYS | STORY_COMMENTARY_KEYS
    if not expected_keys <= present_keys:
        raise AssertionError(
            "reviewed translation-parenthetical keys missing: "
            f"{sorted(expected_keys - present_keys)}"
        )

    repairs = [candidate for candidate in candidates if should_repair(candidate)]
    repair_counts = Counter(
        candidate.relative.split("/", 1)[0] for candidate in repairs
    )
    if repair_counts != EXPECTED_REPAIR_COUNTS:
        raise AssertionError(
            f"translation-parenthetical repair counts drifted: {repair_counts}"
        )

    changed: dict[Path, etree._ElementTree] = {}
    for candidate in repairs:
        repair_candidate(candidate)
        changed[candidate.path] = candidate.tree

    if not args.dry_run:
        for path, tree in sorted(changed.items()):
            path.write_bytes(etree.tostring(
                tree, xml_declaration=True, encoding="UTF-8"
            ))

    retained = len(candidates) - len(repairs)
    print("Reviewed translation parentheticals passed")
    print(f"  analytic or editorial parentheticals moved to notes: {len(repairs)}")
    print(f"  naturalistic elaborations retained inline: {retained}")
    print(f"  XML files rewritten: {0 if args.dry_run else len(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
