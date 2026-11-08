#!/usr/bin/env python3
"""Audit every entry of pourrias-poinsot.txt against the format the build expects; list every deviation.

Expected format of one entry (after printed-line wraps are joined and glued entries split, see build):

    HEAD：BODY
    HEAD  = GROUP ( " = " GROUP )*            GROUP = [ROOT " - "] FORM ("," FORM)* plus optional {X} markers, <n>
    BODY  = SENSE ( "；" SENSE )*  with examples introduced by " - "  as  AMIS：CHINESE

Each check below names one way an entry can depart from that. The audit only reports; it changes nothing.
Writes CodeAndDocs/data/format_audit.tsv (line, part, check, detail) and prints counts with examples.
"""

from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_amis_chinese_xml as B  # noqa: E402

CJK = B.CJK
MARK = B.MARKER
LAT = re.compile(r"[A-Za-z]")
WORD = re.compile(r"[A-Za-z'’‘][A-Za-z'’‘]*")


def alpha(word: str) -> str:
    return re.sub(r"[^a-z]", "", word.lower())


def first_word(text: str) -> str:
    m = WORD.search(text)
    return m.group(0) if m else ""


def balanced(text: str, pairs: str) -> bool:
    depth = 0
    for ch in text:
        if ch in pairs[0::2]:
            depth += 1
        elif ch in pairs[1::2]:
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def checks(entry: str, prev_head: str, next_head: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    head_raw, _, body_raw = entry.partition("：")
    head_masked = MARK.sub(lambda m: " " * len(m.group(0)), head_raw)
    head = MARK.sub(" ", head_raw)
    body = MARK.sub(" ", body_raw)

    # ---- head word
    if "：" not in entry:
        out.append(("H0 no colon", entry[:60]))
    if CJK.search(head_masked):
        out.append(("H1 Chinese before the colon", head_raw[:60]))
    if re.search(r"[(（]", head):
        out.append(("H2 parentheses in the head word", head_raw[:60]))
    first_group = re.split(r"\s*[=＝]\s*", head)[0]
    first_form = re.split(r"\s+-\s*|\s*-\s+|,", first_group)[0]
    first_form = re.sub(r"<\d+>|[(（][^)）]*[)）]", " ", first_form).strip()
    if len(first_form.split()) >= 2:   # words separated by spaces (acak-maacak is a root-derived pair, not two words)
        out.append(("H3 head word of two or more words", first_form))
    if re.search(r"-\s*\{[^}]*\}\s+[A-Za-z'’]", head_raw):
        out.append(("H4 marker between root and a word without a dash", head_raw[:60]))
    if not LAT.search(head):
        out.append(("H5 head word has no Amis", head_raw[:60]))
    h = alpha(first_word(head))
    if prev_head and next_head and h and not (alpha(prev_head) <= h <= alpha(next_head)) and alpha(prev_head) <= alpha(next_head):
        out.append(("H6 head word out of alphabetical order", f"{prev_head} < {first_word(head)} < {next_head}"))
    if len(re.findall(r"\s+-\s+", first_group)) >= 2 and "," not in first_group:
        out.append(("H7 three or more dash parts in the head word", first_group[:60]))

    # ---- body
    if not CJK.search(body):
        out.append(("B1 no Chinese in the body", body_raw[:60]))
    for seg in re.split(r"(?:^|\s)-\s*(?=[“\"‘'’]?[A-Za-z])", body)[1:]:
        before = seg.split("；")[0]
        if not CJK.search(before) and "：" not in before:
            out.append(("B2 example with no translation", before.strip()[:60]))
    for m in re.finditer(r"(?<=[㐀-鿿，。！？）)])\s+([A-Za-z'’][A-Za-z'’]*)\s*(?:-|=|＝|\{)", body_raw):
        w = alpha(m.group(1))
        if h and next_head and h <= w <= alpha(next_head) and len(w) > 2:
            out.append(("B3 possible second entry glued on", body_raw[max(0, m.start() - 10):m.start() + 40]))
    # numbered lists "1) … 2) …" and Bible references printed without "(" ("…”詩：106,7)") are not unbalanced
    if not balanced(re.sub(r"(?:(?<=[\s：:])|^)\d[)）](?=\s|[\u3400-\u9fff])|(?<=[”“\x22])\s*[\u3400-\u9fff]{1,3}\s*[：:]?\s*\d+\s*[,，]\s*\d+\s*[)）]", " ", entry), "()（）"):
        out.append(("B4 unbalanced parentheses", entry[-60:]))
    # the typists often open a quotation with ” as well as close it ("”天主的話…”", "”Rakay”"); that is balanced
    # the typists use “ and ” both for opening and closing ("”天主的話…”", "“Ano ira …“(利 13,2)"): a pair is any two
    o, c = entry.count("“"), entry.count("”")
    if (o + c) % 2:
        out.append(("B5 unbalanced quotation marks", entry[-60:]))
    if re.search(r"[-（(，,、]\s*$|[A-Za-z]\s*$", entry) and not re.search(r"[㐀-鿿][^㐀-鿿]*$", entry[-3:]):
        out.append(("B6 entry ends mid-phrase (page end or wrap?)", entry[-50:]))
    if re.search(r"？？|\(\s*？\s*\)|（\s*？\s*）", entry):
        out.append(("B7 the compiler's own (？)", ""))
    for piece in re.split(r"[；;]", body_raw):
        tags = set(MARK.findall(piece)) & set(B.DIALECT_CODES)
        if tags and (" - " in piece or "=" in piece or "＝" in piece or WORD.search(MARK.sub(" ", piece))):
            out.append(("B8 dialect marker in a piece that also holds Amis", piece.strip()[:60]))
    for run in re.finditer(r"[A-Za-z][A-Za-z'’]*(?:[ \-]+[A-Za-z'’]+)+", body):
        start = run.start()
        prev = body[max(0, start - 2):start]
        if CJK.search(prev) and "：" not in body[run.end():run.end() + 2]:
            out.append(("B9 Amis/Latin words inside Chinese, not an example", run.group(0)[:60]))
    return out


def main() -> None:
    raw = B.load_source(B.SOURCE_TXT)
    joined, _ = B.apply_wraps(B.apply_corrections(raw))
    parts = B.apply_splits(joined)
    keys = sorted(parts)
    heads = {k: first_word(B.split_head_body(parts[k])[0]) for k in keys}
    rows = ["line\tpart\tcheck\tdetail\tentry"]
    count: collections.Counter = collections.Counter()
    examples: dict[str, list[str]] = collections.defaultdict(list)
    flagged_entries: set = set()
    for i, k in enumerate(keys):
        prev_head = heads[keys[i - 1]] if i else ""
        next_head = heads[keys[i + 1]] if i + 1 < len(keys) else ""
        # parentheses are checked after the ruled closing rule (build: close_dangling, card r5-unbalanced-3833)
        for name, detail in checks(B.close_dangling(parts[k]), prev_head, next_head):
            count[name] += 1
            flagged_entries.add(k)
            rows.append(f"{k[0]}\t{k[1]}\t{name}\t{detail}\t{parts[k]}")
            if len(examples[name]) < 4:
                examples[name].append(f"{k[0]}: {parts[k][:110]}")
    out = B.DATA / "format_audit.tsv"
    out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"entries: {len(keys)}; entries with at least one deviation: {len(flagged_entries)}")
    for name in sorted(count):
        print(f"\n{count[name]:6}  {name}")
        for e in examples[name]:
            print("          " + e)
    print(f"\nfull list: {out}")


if __name__ == "__main__":
    main()
