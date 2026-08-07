#!/usr/bin/env python3
"""Extract source-aligned word and morpheme analyses from interlinear examples."""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path

from reconcile_barred_vowels import corrected_word, dictionary_forms


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "raw_data" / "official_text.jsonl"
SOURCE_LEDGER = ROOT / "intermediate" / "source_ledger.csv"
DICTIONARY_LEDGER = ROOT / "intermediate" / "dictionary_ledger.csv"
OUTPUT = ROOT / "intermediate" / "interlinear_ledger.jsonl"
LABEL_RE = re.compile(r"^[（(](\d+(?:-\d+[a-z]?)?)[）)]\s*", re.IGNORECASE)
SUBEXAMPLE_RE = re.compile(r"^[a-z][�.]\s*", re.IGNORECASE)
LATIN_RE = re.compile(r"[A-Za-zʉɄáíúÁÍÚ’']")
CJK_RE = re.compile(r"[\u3400-\u9fff]")
FORM_EDGE_RE = re.compile(r"^[\[“”\"「」『』]+|[\]“”\"「」『』,，.。!?！？:：;；]+$")
STRUCTURAL_LABEL_RE = re.compile(
    r"\]?(?:謂語|主語|補語|述語|受詞|賓語|延伸名詞組|中心語|主事者|"
    r"受事者|受動者|受役物|使動者|名詞謂語|主體|基準體|關係子句)\[?"
)
MORPHEME_SPLIT_RE = re.compile(r"([-=])")
CLITIC_SPLIT_RE = re.compile(r"(=)")
TRANSLATION_TERM_RE = re.compile(r"[；、，。／/（）()]")
BAD_GLOSS_START_RE = re.compile(r"^(?:[.=>-]|格|事焦點|成貌|態改變|係詞|除\.)")
BAD_GLOSS_END_RE = re.compile(r"(?:[.=<-]|主|斜|排|完|狀|受|工|關|非)$")
LEXICON_MISMATCH_COST = 200.0
MAX_SOURCE_MATCH_DISTANCE = 5
MAX_SOURCE_MATCH_RATIO = 0.20
LEXICON: dict[str, set[str]] = {}
BARRED_FORMS: dict[str, set[str]] = {}
TOKEN_JOIN_OVERRIDES = {
    ("kat", "rʉpʉ=cu"): "katʉrʉpʉ=cu",
}

# The positioned-text layer occasionally merges two adjacent printed gloss
# cells. These source-backed corrections cover the ambiguous cases that
# cannot be recovered from x positions or the dictionary lexicon alone.
# Each tuple is (word index, expected source form, corrected gloss).
GLOSS_OVERRIDES: dict[str, tuple[tuple[int, str, str], ...]] = {
    "song-2018-kanakanavu-S0017": (
        (0, "’akuni", "否定詞.祈使"),
        (1, "ara-pi-piningi", "變成-重疊-外面"),
        (2, "soni", "今天"),
    ),
    "song-2018-kanakanavu-S0027": (
        (3, "Pani", "人名"),
        (4, "Kanapaniana", "人名"),
    ),
    "song-2018-kanakanavu-S0078": (
        (0, "’esi=kara", "在=是非疑問詞"),
        (1, "suan", "（你）那裡"),
    ),
    "song-2018-kanakanavu-S0117": (
        (4, "’arating", "筷子"),
        (5, "tan-taniara", "重疊-日子"),
    ),
    "song-2018-kanakanavu-S0138": (
        (0, "ni-k<ʉm>ʉnʉ=cu", "完成貌-<主事焦點>吃=狀態改變"),
        (1, "kavangvang=kim", "全部=我們.排除.主格"),
    ),
    "song-2018-kanakanavu-S0169": (
        (1, "vanai", "原因"),
        (2, "manu", "孩子"),
    ),
    "song-2018-kanakanavu-S0246": (
        (0, "u-peni", "量詞.非人-多少"),
        (1, "tacau=musu", "狗=你.屬格"),
    ),
    "song-2018-kanakanavu-S0296": (
        (0, "ni-m-uranʉ=cu", "完成貌-主事焦點-幫忙=狀態改變"),
        (1, "’apio", "人名"),
    ),
    "song-2018-kanakanavu-S0346": (
        (0, "tavara’ʉ=kara", "主事焦點.知道=是非疑問詞"),
        (1, "Pori", "人名"),
    ),
    "song-2018-kanakanavu-S0383": (
        (0, "ni-mu-ringai=in=ci", "完成貌-主事焦點-陷阱=如果=狀態改變"),
        (1, "ia", "主題"),
    ),
    "song-2018-kanakanavu-S0390": (
        (0, "vanai", "原因"),
        (1, "sii", "因為"),
    ),
    "song-2018-kanakanavu-S0399": (
        (4, "ni-mu-’uru-’uru", "完成貌-主事焦點-重疊-優先"),
        (5, "arávari", "換位置"),
        (6, "na", "處格"),
    ),
    "song-2018-kanakanavu-S0407": (
        (2, "’apa-cangcangarʉ-ʉn", "使動-快樂-受事焦點"),
        (3, "’aree", "人名"),
    ),
    "song-2018-kanakanavu-S0424": (
        (2, "’apa-cangcangarʉ-ʉn", "使動-快樂-受事焦點"),
        (3, "Pi’i", "人名"),
    ),
    "song-2018-kanakanavu-S0526": (
        (0, "atʉnʉ-ʉn=kee", "找到-受事焦點=他.屬格"),
        (1, "mu-pana’ʉ", "主事焦點-射"),
    ),
    "song-2018-kanakanavu-S0567": (
        (1, "ni-pana’ʉ-a", "完成貌.受事焦點-射-關係詞"),
        (2, "u-cani", "量詞.非人-一"),
    ),
    "song-2018-kanakanavu-S0568": (
        (0, "’akia=cu", "存在.否定詞=狀態改變"),
        (1, "ciasʉ", "亮光"),
    ),
    "song-2018-kanakanavu-S0581": (
        (3, "ni-pana’ʉ-a", "完成貌.受事焦點-射-關係詞"),
        (4, "taniarʉ", "太陽"),
    ),
    "song-2018-kanakanavu-S0602": (
        (0, "arapepe=cu", "空空的=狀態改變"),
        (1, "pui’i", "回去"),
    ),
    "song-2018-kanakanavu-S0625": (
        (4, "ni-mʉkʉ-a", "完成貌-種植-關係詞"),
        (5, "cau", "人"),
    ),
    "song-2018-kanakanavu-S0635": (
        (0, "te=pa=kani", "非實現=還=據說"),
        (1, "pui’i", "回去"),
    ),
    "song-2018-kanakanavu-S0636": (
        (0, "makásua=cu", "那樣=狀態改變"),
        (1, "a’unu-ʉn=cu", "揹（用揹簍，支撐點在頭部）=狀態改變"),
    ),
    "song-2018-kanakanavu-S0642": (
        (5, "u-peni", "量詞.非人-多少"),
        (6, "kusai", "究竟"),
    ),
    "song-2018-kanakanavu-S0644": (
        (3, "ni-ari-tapasʉ-a", "完成貌-手的動作-圖畫-關係詞"),
        (4, "’ʉnai", "土地"),
    ),
    "song-2018-kanakanavu-S0652": (
        (1, "ni-ari-sinatʉ-a", "完成貌-手的動作-文字-關係詞"),
        (2, "nguai", "就是"),
    ),
    "song-2018-kanakanavu-S0693": (
        (0, "pa-ara-’akia", "使動-變成-存在.否定詞"),
        (1, "’apitarʉ", "危險"),
    ),
    "song-2018-kanakanavu-S0230": (
        (3, "te=kara=kasu", "非實現=是非疑問詞=你.主詞"),
        (4, "putukikio", "主事焦點.工作"),
    ),
    "song-2018-kanakanavu-S0688": (
        (4, "ni-mu-’uru-’uru", "完成貌-主事焦點-重疊-先"),
        (5, "arávari", "換位置"),
        (6, "na", "處格"),
    ),
}

# These layouts cannot be recovered from positioned text without inventing a
# word boundary. The word/gloss pairs were checked directly against the page
# images and remain fail-fast source evidence.
ANALYSIS_OVERRIDES: dict[str, tuple[tuple[str, str], ...]] = {
    "song-2018-kanakanavu-S0141": (
        ("’esi=cu", "在=狀態改變"),
        ("’umó’uma", "田"),
        ("sua", "主格"),
        ("karavung", "牛"),
        ("k<um>a-kʉnʉ", "Ca重疊<主事焦點>-吃"),
        ("cʉnʉ", "草"),
    ),
    "song-2018-kanakanavu-S0221": (
        ("aka", "壞"),
    ),
    "song-2018-kanakanavu-S0544": (
        ("aranai", "從"),
        ("meesua", "那時"),
        ("ma-ti’arangʉ=cu", "主事焦點-準備=狀態改變"),
        ("nguani", "他們.主格"),
        ("marínguna", "乾"),
        ("karu", "樹木"),
        ("mataa", "和"),
        ("’uringi", "芒草莖"),
    ),
}

UNANALYZED_SOURCE_IDS = {
    # Example 5-2 has a whole-sentence translation but no printed word gloss.
    "song-2018-kanakanavu-S0046",
    # Footnote 27 gives a sentence and translation without interlinear glosses.
    "song-2018-kanakanavu-S0172",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_pages() -> dict[int, dict[str, object]]:
    return {
        int(record["page"]): record
        for record in (
            json.loads(line)
            for line in SOURCE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }


def group_lines(rows: list[dict[str, object]]) -> list[list[dict[str, object]]]:
    lines: list[list[dict[str, object]]] = []
    for row in sorted(rows, key=lambda item: (int(item["y"]), int(item["x"]))):
        if lines and abs(int(row["y"]) - int(lines[-1][0]["y"])) <= 1:
            lines[-1].append(row)
        else:
            lines.append([row])
    return lines


def line_text(line: list[dict[str, object]]) -> str:
    return " ".join(str(row["text"]).strip() for row in line).strip()


def line_kind(line: list[dict[str, object]]) -> str:
    text = line_text(line)
    latin_count = len(LATIN_RE.findall(text))
    cjk_count = len(CJK_RE.findall(text))
    if latin_count > cjk_count * 2:
        return "form"
    if cjk_count:
        return "gloss"
    if latin_count:
        return "form"
    return "other"


def split_blocks(page: dict[str, object]) -> list[dict[str, object]]:
    rows = [
        row
        for row in page["rows"]
        if int(row["x"]) < 280 and not (int(row["x"]) < 35 and int(row["h"]) > 20)
    ]
    starts = [
        index
        for index, row in enumerate(rows)
        if LABEL_RE.match(str(row["text"]).strip())
    ]
    blocks: list[dict[str, object]] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(rows)
        match = LABEL_RE.match(str(rows[start]["text"]).strip())
        assert match is not None
        blocks.append({"label": match.group(1), "rows": rows[start:end]})
    return blocks


def cleaned_fragment(text: str, *, first: bool = False) -> str:
    text = text.strip()
    if first:
        text = LABEL_RE.sub("", text)
        text = SUBEXAMPLE_RE.sub("", text)
    text = text.replace("�", "")
    text = STRUCTURAL_LABEL_RE.sub(" ", text)
    text = FORM_EDGE_RE.sub("", text)
    text = text.replace("“", "").replace("”", "").replace('"', "")
    text = re.sub(r"(?<=[A-Za-zʉɄáíúÁÍÚ’'])\d+$", "", text)
    text = re.sub(r"^\(([^()\s]+)\)$", r"\1", text)
    return text.strip()


def form_tokens(line: list[dict[str, object]]) -> list[dict[str, object]]:
    tokens: list[dict[str, object]] = []
    for fragment_index, row in enumerate(sorted(line, key=lambda item: int(item["x"]))):
        text = cleaned_fragment(str(row["text"]), first=fragment_index == 0)
        if not text:
            continue
        pieces = re.split(r"\s+|(?<=\w),(?=\w)", text)
        if not pieces:
            continue
        width = max(float(row["w"]), 1.0)
        weights = [max(len(piece), 1) for piece in pieces]
        total_weight = sum(weights)
        consumed = 0
        for piece, weight in zip(pieces, weights, strict=True):
            start = float(row["x"]) + width * consumed / total_weight
            piece = cleaned_fragment(piece)
            consumed += weight
            end = float(row["x"]) + width * consumed / total_weight
            if piece and LATIN_RE.search(piece):
                tokens.append(
                    {
                        "form": correct_analysis_form(piece),
                        "x": start,
                        "end": end,
                    }
                )
    merged: list[dict[str, object]] = []
    for token in tokens:
        previous_form = str(merged[-1]["form"]) if merged else ""
        token_form = str(token["form"])
        joined_override = TOKEN_JOIN_OVERRIDES.get((previous_form, token_form))
        if (
            merged
            and (
                previous_form.count("<") > previous_form.count(">")
                or joined_override is not None
            )
        ):
            merged[-1]["form"] = joined_override or correct_analysis_form(
                previous_form + token_form
            )
            merged[-1]["end"] = token["end"]
        else:
            merged.append(token)
    return merged


def correct_analysis_form(form: str) -> str:
    pieces = MORPHEME_SPLIT_RE.split(form)
    return "".join(
        piece
        if piece in {"-", "="}
        else corrected_word(piece, BARRED_FORMS)
        for piece in pieces
    )


def align_glosses(
    tokens: list[dict[str, object]], gloss_line: list[dict[str, object]]
) -> list[dict[str, str]] | None:
    if not tokens:
        return None
    gloss_rows = sorted(gloss_line, key=lambda item: int(item["x"]))
    assignments: list[list[int]] = [[] for _ in gloss_rows]
    for token_index, token in enumerate(tokens):
        start = float(token["x"])
        containing = [
            row_index
            for row_index, row in enumerate(gloss_rows)
            if float(row["x"]) - 4
            <= start
            <= float(row["x"]) + float(row["w"]) + 4
        ]
        candidates = containing or list(range(len(gloss_rows)))
        row_index = min(
            candidates,
            key=lambda candidate: abs(float(gloss_rows[candidate]["x"]) - start),
        )
        assignments[row_index].append(token_index)

    glosses = ["" for _ in tokens]
    for row, token_indices in zip(gloss_rows, assignments, strict=True):
        text = str(row["text"]).strip().replace("�", ".").strip(" .]")
        if not text or not token_indices:
            return None
        if token_indices != list(range(token_indices[0], token_indices[-1] + 1)):
            return None
        selected_tokens = [tokens[index] for index in token_indices]
        segments = partition_gloss(text, selected_tokens)
        if not segments:
            return None
        for token_index, segment in zip(token_indices, segments, strict=True):
            glosses[token_index] = segment

    if any(not gloss for gloss in glosses):
        return None
    return [
        {"form": str(token["form"]), "gloss": gloss}
        for token, gloss in zip(tokens, glosses, strict=True)
    ]


def expected_gloss_terms(form: str) -> tuple[set[str], list[set[str]]]:
    exact_key = match_key(surface_word(form))
    component_keys = [
        match_key(piece.strip("-="))
        for piece in split_morphemes(form)
        if piece.strip("-=")
    ]
    component_keys = list(dict.fromkeys(component_keys))
    component_keys = [key for key in component_keys if key != exact_key]
    exact = set(LEXICON.get(exact_key, set()))
    components = [
        {term for term in LEXICON.get(key, set()) if term}
        for key in component_keys
    ]
    components = [terms for terms in components if terms]
    return exact, components


def gloss_match_cost(form: str, segment: str) -> float:
    exact, components = expected_gloss_terms(form)
    if exact:
        matching = [term for term in exact if term in segment]
        if not matching:
            return LEXICON_MISMATCH_COST
        extra = min(len(segment) - len(term) for term in matching)
        return max(extra, 0) * 10.0
    if components:
        missing = sum(
            not any(term in segment for term in terms)
            for terms in components
        )
        if missing:
            return LEXICON_MISMATCH_COST * missing
    if str(form)[:1].isupper() and "人名" not in segment:
        return LEXICON_MISMATCH_COST
    return 0.0


def partition_gloss(
    text: str, tokens: list[dict[str, object]]
) -> list[str] | None:
    starts = [float(token["x"]) for token in tokens]
    if len(starts) == 1:
        return [text]
    if len(text) < len(starts):
        return None

    widths = [8.0 if CJK_RE.match(character) else 3.5 for character in text]
    prefix = [0.0]
    for width in widths:
        prefix.append(prefix[-1] + width)

    states: dict[tuple[int, int], tuple[float, list[int]]] = {(0, 0): (0.0, [])}
    for token_index in range(len(starts) - 1):
        next_states: dict[tuple[int, int], tuple[float, list[int]]] = {}
        remaining_tokens = len(starts) - token_index - 1
        for (_, character_index), (cost, boundaries) in states.items():
            maximum = len(text) - remaining_tokens
            for boundary in range(character_index + 1, maximum + 1):
                rendered_end = (
                    starts[token_index] + prefix[boundary] - prefix[character_index]
                )
                gap = starts[token_index + 1] - rendered_end
                boundary_cost = abs(gap) + (abs(gap) if gap < -4 else 0)
                segment = text[character_index:boundary]
                boundary_cost += gloss_match_cost(
                    str(tokens[token_index]["form"]),
                    segment,
                )
                key = (token_index + 1, boundary)
                candidate = (cost + boundary_cost, boundaries + [boundary])
                if key not in next_states or candidate[0] < next_states[key][0]:
                    next_states[key] = candidate
        states = next_states

    if not states:
        return None
    ranked = []
    for cost, boundaries in states.values():
        final_start = boundaries[-1] if boundaries else 0
        cost += gloss_match_cost(str(tokens[-1]["form"]), text[final_start:])
        ranked.append((cost, boundaries))
    _, boundaries = min(ranked, key=lambda item: item[0])
    positions = [0, *boundaries, len(text)]
    return [
        text[positions[index] : positions[index + 1]]
        for index in range(len(positions) - 1)
    ]


def split_morphemes(text: str) -> list[str]:
    pieces = MORPHEME_SPLIT_RE.split(text)
    morphemes: list[str] = []
    current = ""
    for piece in pieces:
        if not piece:
            continue
        if piece in {"-", "="}:
            current += piece
            if current:
                morphemes.append(current)
                current = ""
        else:
            current += piece
    if current:
        morphemes.append(current)
    return morphemes


def split_clitics(text: str) -> list[str]:
    pieces = CLITIC_SPLIT_RE.split(text)
    clitics: list[str] = []
    current = ""
    for piece in pieces:
        if not piece:
            continue
        current += piece
        if piece == "=":
            clitics.append(current)
            current = ""
    if current:
        clitics.append(current)
    return clitics


def split_gloss_morphemes(text: str, target_count: int) -> list[str]:
    morphemes = split_morphemes(text)
    needed = target_count - len(morphemes)
    if needed <= 0:
        return morphemes
    dot_positions = [
        index for index, character in enumerate(text) if character == "."
    ][:needed]
    if len(dot_positions) != needed:
        return morphemes
    selected = set(dot_positions)
    result: list[str] = []
    current = ""
    for index, character in enumerate(text):
        current += character
        if character in {"-", "="} or index in selected:
            result.append(current)
            current = ""
    if current:
        result.append(current)
    return result


def morpheme_form(text: str) -> str:
    """Remove affix apparatus while retaining a printed clitic boundary."""
    return re.sub(r"\([^)]*\)", "", text).replace("-", "")


def add_infix_morphemes(word: dict[str, str]) -> dict[str, object]:
    result: dict[str, object] = dict(word)
    infixes = re.findall(r"<([^>]+)>", word["form"])
    gloss_infixes = re.findall(r"<[^>]+>", word["gloss"])
    if not infixes or len(infixes) != len(gloss_infixes):
        return result

    remainder_form = re.sub(r"<[^>]+>", "", word["form"])
    remainder_gloss = re.sub(r"<[^>]+>", "", word["gloss"])
    forms = split_morphemes(remainder_form)
    glosses = split_gloss_morphemes(remainder_gloss, len(forms))
    if len(forms) != len(glosses) or any(
        not gloss.strip("-=.") for gloss in glosses
    ):
        return result

    result["morphemes"] = [
        {"form": form, "gloss": gloss}
        for form, gloss in zip(infixes, gloss_infixes, strict=True)
    ] + [
        {"form": morpheme_form(form), "gloss": gloss}
        for form, gloss in zip(forms, glosses, strict=True)
    ]
    return result


def add_morphemes(word: dict[str, str]) -> dict[str, object]:
    result: dict[str, object] = dict(word)
    if not any(marker in word["form"] for marker in "-=<>"):
        result["morphemes"] = [
            {"form": word["form"], "gloss": word["gloss"]}
        ]
        return result
    if "<" in word["form"] or ">" in word["form"]:
        return add_infix_morphemes(word)
    forms = split_morphemes(word["form"])
    glosses = split_morphemes(word["gloss"])
    if len(forms) != len(glosses):
        dotted_glosses = split_gloss_morphemes(word["gloss"], len(forms))
        if len(forms) == len(dotted_glosses):
            glosses = dotted_glosses
    if len(forms) != len(glosses) and "=" in word["form"] and "=" in word["gloss"]:
        # Some printed hosts expose internal affix structure in FORM but give a
        # single lexical gloss for the whole host. Preserve the independently
        # aligned clitic boundary without inventing missing affix glosses.
        clitic_forms = split_clitics(word["form"])
        clitic_glosses = split_clitics(word["gloss"])
        if len(clitic_forms) == len(clitic_glosses):
            forms = clitic_forms
            glosses = clitic_glosses
    if len(forms) == len(glosses):
        result["morphemes"] = [
            {
                "form": morpheme_form(form),
                "gloss": gloss,
            }
            for form, gloss in zip(forms, glosses, strict=True)
            if form and gloss
        ]
    return result


def apply_gloss_overrides(
    sentence_id: str, words: list[dict[str, object]]
) -> list[dict[str, object]]:
    for word_index, expected_form, gloss in GLOSS_OVERRIDES.get(sentence_id, ()):
        if word_index >= len(words):
            raise ValueError(
                f"Gloss override index {word_index} is outside {sentence_id}"
            )
        actual_form = str(words[word_index]["form"])
        if actual_form != expected_form:
            raise ValueError(
                f"Gloss override for {sentence_id} expected {expected_form!r}, "
                f"found {actual_form!r}"
            )
        words[word_index] = add_morphemes({"form": actual_form, "gloss": gloss})
    return words


def repair_gloss_boundaries(
    words: list[dict[str, object]],
) -> list[dict[str, object]]:
    repaired = [
        {"form": str(word["form"]), "gloss": str(word["gloss"])}
        for word in words
    ]
    for index in range(len(repaired) - 1):
        current = repaired[index]
        following = repaired[index + 1]
        if (
            str(current["gloss"]).endswith(("主", "屬", "斜"))
            and str(following["gloss"]).startswith("格")
        ):
            current["gloss"] = str(current["gloss"]) + "格"
            following["gloss"] = str(following["gloss"])[1:]
        if (
            str(current["gloss"]).endswith("主")
            and str(following["gloss"]).startswith("事焦點")
        ):
            current["gloss"] = str(current["gloss"])[:-1]
            following["gloss"] = "主" + str(following["gloss"])
        if (
            str(current["gloss"]).endswith(".")
            and str(following["gloss"]).startswith("屬格")
        ):
            current["gloss"] = str(current["gloss"]) + "屬格"
            following["gloss"] = str(following["gloss"])[2:]
    return [
        add_morphemes(
            {"form": str(word["form"]), "gloss": str(word["gloss"])}
        )
        for word in repaired
    ]


def block_words(block: dict[str, object]) -> list[dict[str, object]]:
    lines = group_lines(list(block["rows"]))
    words: list[dict[str, object]] = []
    for index in range(len(lines) - 1):
        if line_kind(lines[index]) != "form" or line_kind(lines[index + 1]) != "gloss":
            continue
        delta = int(lines[index + 1][0]["y"]) - int(lines[index][0]["y"])
        if not 5 <= delta <= 11:
            continue
        aligned = align_glosses(form_tokens(lines[index]), lines[index + 1])
        if aligned:
            words.extend(add_morphemes(word) for word in aligned)
    return words


def surface_word(form: str) -> str:
    form = morpheme_form(form)
    form = re.sub(r"<([^>]+)>", r"\1", form)
    return FORM_EDGE_RE.sub("", form)


def match_key(text: str) -> str:
    text = text.lower().replace("’", "'").replace("ʉ", "u").replace("Ʉ", "u")
    text = "".join(
        character
        for character in unicodedata.normalize("NFD", text)
        if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9']+", "", text)


def edit_distance(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    for left_index, left_character in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_character in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1]
                    + (left_character != right_character),
                )
            )
        previous = current
    return previous[-1]


def select_words(
    target: str, words: list[dict[str, object]]
) -> list[dict[str, object]] | None:
    target_key = match_key(target)
    source_tokens = [match_key(surface_word(str(word["form"]))) for word in words]
    if not target_key or not source_tokens:
        return None
    for start in range(len(source_tokens)):
        combined = ""
        for end in range(start, len(source_tokens)):
            combined += source_tokens[end]
            if combined == target_key:
                return words[start : end + 1]
            if not target_key.startswith(combined):
                break
    best: tuple[float, int, int, int] | None = None
    for start in range(len(source_tokens)):
        combined = ""
        for end in range(start, len(source_tokens)):
            combined += source_tokens[end]
            distance = edit_distance(target_key, combined)
            ratio = distance / max(len(target_key), len(combined))
            candidate = (ratio, distance, start, end + 1)
            if best is None or candidate < best:
                best = candidate
            if len(combined) > len(target_key) * 1.3 + 8:
                break
    if (
        best
        and best[0] <= MAX_SOURCE_MATCH_RATIO
        and best[1] <= MAX_SOURCE_MATCH_DISTANCE
    ):
        return words[best[2] : best[3]]
    return None


def possible_labels(example_label: str) -> list[str]:
    parts = example_label.split("-")
    labels = [example_label]
    while len(parts) > 1:
        parts = parts[:-1]
        labels.append("-".join(parts))
    match = re.match(r"^(\d+-\d+[a-z]?)", example_label, re.IGNORECASE)
    if match:
        labels.append(match.group(1))
        labels.append(re.sub(r"[a-z]$", "", match.group(1), flags=re.IGNORECASE))
    return list(dict.fromkeys(labels))


def narrative_label(example_label: str) -> str | None:
    match = re.fullmatch(r"narrative[123]-(\d{3})", example_label)
    return str(int(match.group(1))) if match else None


def omitted_forms(example_label: str) -> set[str]:
    omissions: set[str] = set()
    if "-no-sua" in example_label or "-without-sua" in example_label:
        omissions.add("sua")
    if "-no-na" in example_label:
        omissions.add("na")
    if "-no-miura" in example_label:
        omissions.add("miʉra")
    return omissions


def without_omitted_forms(
    words: list[dict[str, object]], omissions: set[str]
) -> list[dict[str, object]]:
    if not omissions:
        return words
    omission_keys = {match_key(form) for form in omissions}
    return [
        word
        for word in words
        if match_key(surface_word(str(word["form"]))) not in omission_keys
    ]


def resolve_form_alternatives(
    words: list[dict[str, object]], target: str
) -> list[dict[str, object]]:
    target_key = match_key(target)
    resolved: list[dict[str, object]] = []
    for word in words:
        form = str(word["form"])
        gloss = str(word["gloss"])
        form_options = form.split("/")
        if len(form_options) == 1:
            resolved.append(word)
            continue
        matching_options = [
            (index, option)
            for index, option in enumerate(form_options)
            if match_key(surface_word(option)) in target_key
        ]
        if len(matching_options) != 1:
            resolved.append(word)
            continue
        option_index, selected_form = matching_options[0]
        gloss_options = gloss.split("／")
        selected_gloss = (
            gloss_options[option_index]
            if len(gloss_options) == len(form_options)
            else gloss
        )
        resolved.append(
            add_morphemes(
                {"form": selected_form, "gloss": selected_gloss}
            )
        )
    return resolved


def gloss_boundaries_are_valid(words: list[dict[str, object]]) -> bool:
    return all(
        (
            CJK_RE.search(str(word["gloss"]))
            or match_key(str(word["gloss"]))
            == match_key(surface_word(str(word["form"])))
        )
        and "[" not in str(word["gloss"])
        and "]" not in str(word["gloss"])
        and "謂語" not in str(word["gloss"])
        and "主語" not in str(word["gloss"])
        and not BAD_GLOSS_START_RE.search(str(word["gloss"]))
        and not BAD_GLOSS_END_RE.search(str(word["gloss"]))
        for word in words
    )


def seed_interlinear_lexicon(pages: dict[int, dict[str, object]]) -> None:
    for page_number in [*range(47, 185), *range(221, 263)]:
        for block in split_blocks(pages[page_number]):
            lines = group_lines(list(block["rows"]))
            for index in range(len(lines) - 1):
                if (
                    line_kind(lines[index]) != "form"
                    or line_kind(lines[index + 1]) != "gloss"
                ):
                    continue
                delta = int(lines[index + 1][0]["y"]) - int(lines[index][0]["y"])
                if not 5 <= delta <= 11:
                    continue
                tokens = form_tokens(lines[index])
                gloss_rows = sorted(lines[index + 1], key=lambda item: int(item["x"]))
                if len(tokens) != len(gloss_rows):
                    continue
                if any(
                    abs(float(token["x"]) - float(gloss["x"])) > 12
                    for token, gloss in zip(tokens, gloss_rows, strict=True)
                ):
                    continue
                for token, gloss_row in zip(tokens, gloss_rows, strict=True):
                    form = str(token["form"])
                    gloss = str(gloss_row["text"]).strip().replace("�", ".")
                    if form and gloss:
                        LEXICON.setdefault(match_key(surface_word(form)), set()).add(gloss)
                    forms = split_morphemes(form)
                    glosses = split_morphemes(gloss)
                    if len(forms) > 1 and len(forms) == len(glosses):
                        for morph_form, morph_gloss in zip(
                            forms, glosses, strict=True
                        ):
                            key = match_key(morph_form.strip("-="))
                            if key and morph_gloss:
                                LEXICON.setdefault(key, set()).add(morph_gloss)


def extract() -> list[dict[str, object]]:
    global BARRED_FORMS, LEXICON
    pages = read_pages()
    LEXICON = {}
    dictionary_rows = read_csv(DICTIONARY_LEDGER)
    BARRED_FORMS = dictionary_forms(dictionary_rows)
    for entry in dictionary_rows:
        terms = {
            term
            for term in TRANSLATION_TERM_RE.split(entry["translation"])
            if term
        }
        for form in re.split(r"\s+[/;]\s+|[/;]\s*", entry["form"]):
            if form and " " not in form:
                LEXICON.setdefault(match_key(form), set()).update(terms)
    seed_interlinear_lexicon(pages)
    ledger = [row for row in read_csv(SOURCE_LEDGER) if row["included"] == "yes"]
    blocks_by_page: dict[int, list[dict[str, object]]] = {}
    for page_number in set(int(row["reader_page"]) for row in ledger):
        blocks_by_page[page_number] = split_blocks(pages[page_number])

    analyses: list[dict[str, object]] = []
    for row in ledger:
        page_number = int(row["reader_page"])
        if (
            187 <= page_number < 221
            or row["final_s_id"] in UNANALYZED_SOURCE_IDS
        ):
            continue
        if row["final_s_id"] in ANALYSIS_OVERRIDES:
            analyses.append(
                {
                    "s_id": row["final_s_id"],
                    "reader_page": page_number,
                    "example_label": row["example_label"],
                    "words": [
                        add_morphemes({"form": form, "gloss": gloss})
                        for form, gloss in ANALYSIS_OVERRIDES[
                            row["final_s_id"]
                        ]
                    ],
                }
            )
            continue
        labels = possible_labels(row["example_label"])
        narrative = narrative_label(row["example_label"])
        if narrative:
            labels.insert(0, narrative)
        candidates = [
            block
            for block in blocks_by_page.get(page_number, [])
            if str(block["label"]) in labels
        ]
        page_rows = [
            source_row
            for source_row in pages[page_number]["rows"]
            if int(source_row["x"]) < 280
            and not (int(source_row["x"]) < 35 and int(source_row["h"]) > 20)
        ]
        candidates.append({"label": "page-fallback", "rows": page_rows})
        selected = None
        omissions = omitted_forms(row["example_label"])
        for block in candidates:
            words = resolve_form_alternatives(
                without_omitted_forms(
                    repair_gloss_boundaries(block_words(block)),
                    omissions,
                ),
                row["target_text"],
            )
            selected = select_words(row["target_text"], words)
            if not selected:
                continue
            selected = repair_gloss_boundaries(selected)
            selected = apply_gloss_overrides(row["final_s_id"], selected)
            if gloss_boundaries_are_valid(selected):
                break
            selected = None
        if selected:
            analyses.append(
                {
                    "s_id": row["final_s_id"],
                    "reader_page": page_number,
                    "example_label": row["example_label"],
                    "words": selected,
                }
            )
    return analyses


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    analyses = extract()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(
            json.dumps(analysis, ensure_ascii=False, separators=(",", ":")) + "\n"
            for analysis in analyses
        ),
        encoding="utf-8",
    )
    word_count = sum(len(analysis["words"]) for analysis in analyses)
    morph_count = sum(
        len(word.get("morphemes", []))
        for analysis in analyses
        for word in analysis["words"]
    )
    print(
        f"Wrote {len(analyses)} sentence analyses, {word_count} words, "
        f"and {morph_count} morphemes to {args.output}"
    )


if __name__ == "__main__":
    main()
