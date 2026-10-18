#!/usr/bin/env python3
"""Delete words (W) whose FORM is only punctuation, and their token in the sentence.

Maintainer's ruling, 2026-10-18 (NTU Word Forms page), on the five such words
-- Bunun bnNr-frog_Ciang S_34 '.', S_64 ',', S_78 ',', S_159 '.' (glossed
(咳嗽)/(cough)) and Seediq sdqNr-childhood_micang 2020s S_185 ',' (glossed
PART): option "Delete these W (sentence unchanged)", with the note "But I'd
delete those from those sentences, too."

So for every W whose FORMs are all made only of punctuation (no letter, digit,
null marker or morpheme marker; the same test as validator V164), the W (with
its M) is removed, and so is the standalone punctuation token it stands for in
each sentence-level FORM: the token and the space before it (after it, if it
opens the sentence) -- 'adiia, . a,' -> 'adiia, a,'. No other punctuation in
the sentence is touched.

Which token: of the sentence's standalone tokens equal to the W's FORM, the one
with the number of letter-bearing tokens before it closest to the number of
letter-bearing words before the W. If two are equally close, or there is no
such token, the build stops.

Runs in finish_tiers before the prune, align_ids (which renumbers the words that
follow) and the standard tier + PHON (which are derived from the edited FORMs).
Idempotent: a second run finds nothing.

    python drop_punctuation_words.py --xml_dir <dir> [--report <tsv>]
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

from lxml import etree

NOT_PUNCTUATION = frozenset("'ʼ’ˈ^-=<>~∅Øø")


def only_punctuation(text: str) -> bool:
    chars = [ch for ch in text if not ch.isspace()]
    return bool(chars) and all(unicodedata.category(ch)[0] in "PS" and ch not in NOT_PUNCTUATION
                               for ch in chars)


def has_letter(token: str) -> bool:
    return any(ch.isalnum() for ch in token)


def drop_token(form, token: str, words_before: int, where: str) -> str | None:
    """Remove the standalone token from form's text; return the new text (None: absent)."""
    if len(form):
        raise SystemExit(f"drop_punctuation_words: {where}: sentence FORM has child elements")
    text = form.text or ""
    spans = [m.span() for m in re.finditer(r"\S+", text)]
    cands = []
    for i, (a, b) in enumerate(spans):
        if text[a:b] == token:
            before = sum(1 for x, y in spans[:i] if has_letter(text[x:y]))
            cands.append((abs(before - words_before), i))
    if not cands:
        return None
    cands.sort()
    if len(cands) > 1 and cands[0][0] == cands[1][0]:
        raise SystemExit(f"drop_punctuation_words: {where}: cannot tell which {token!r} in {text!r}")
    i = cands[0][1]
    a, b = spans[i]
    if i > 0:
        a = spans[i - 1][1]            # with the space before it
    elif i + 1 < len(spans):
        b = spans[i + 1][0]            # opening token: with the space after it
    return text[:a] + text[b:]


def remove_keep_layout(el):
    parent, prev = el.getparent(), el.getprevious()
    if prev is not None:
        prev.tail = el.tail
    else:
        parent.text = el.tail
    parent.remove(el)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml_dir", required=True, type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args(argv)
    counts, report, files = Counter(), [], 0
    for path in sorted(args.xml_dir.rglob("*.xml")):
        raw = path.read_bytes()
        tree = etree.parse(str(path))
        changed = False
        for s in tree.getroot().iter("S"):
            ws = s.findall("W")
            for k, w in enumerate(ws):
                forms = w.findall("FORM")
                if not forms or not all(only_punctuation("".join(f.itertext())) for f in forms):
                    continue
                token = "".join(forms[0].itertext()).strip()
                before = sum(1 for x in ws[:k] if any(has_letter("".join(f.itertext())) for f in x.findall("FORM")))
                for sf in s.findall("FORM"):
                    old = sf.text
                    new = drop_token(sf, token, before, w.get("id"))
                    if new is None:
                        counts["sentence FORM without the token (left)"] += 1
                        continue
                    sf.text = new
                    counts["sentence FORM tokens removed"] += 1
                    report.append((path.name, s.get("id"), f"S FORM kindOf={sf.get('kindOf')}", old, new))
                report.append((path.name, s.get("id"), f"W {w.get('id')} removed",
                               etree.tostring(w, encoding="unicode", with_tail=False), ""))
                counts["W removed"] += 1
                counts["M removed"] += len(w.findall("M"))
                remove_keep_layout(w)
                changed = True
        if changed:
            decl = raw.split(b"?>", 1)[0] + b"?>\n" if raw.startswith(b"<?xml") else b""
            body = etree.tostring(tree.getroot(), encoding="unicode").encode("utf-8")
            path.write_bytes(decl + body + (b"\n" if raw.endswith(b"\n") else b""))
            files += 1
    for key in sorted(counts):
        print(f"  {key}: {counts[key]}")
    print(f"files rewritten: {files}")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("w", encoding="utf-8", newline="") as fh:
            out = csv.writer(fh, delimiter="\t", lineterminator="\n")
            out.writerow(["file", "s_id", "where", "before", "after"])
            out.writerows(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
