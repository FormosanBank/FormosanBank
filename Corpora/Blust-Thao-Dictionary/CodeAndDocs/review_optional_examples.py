#!/usr/bin/env python3
"""Review page: example sentences carrying optional material Blust marked with ( ).

Each card shows the two readings expansion would give, whether the English
splits with them, and what extract_source.py already produced for the same
record - the entry build does not expand yet, so Hunter's readings are the
check on any proposed scope.
"""

import collections
import glob
import re
import sys
import unicodedata
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_review_page import render, E  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PAREN = re.compile(r"\(([^()]*)\)")
OUT = ROOT / "XML"


def key(text):
    return "".join(
        c.lower() for c in unicodedata.normalize("NFC", text) if c.isalnum()
    )


def readings(form):
    """What Blust's parentheses mean: the material is optional, so two forms."""
    without = re.sub(r"\s*\([^()]*\)", "", form)
    without = re.sub(r"\s+([,.;:?!])", r"\1", re.sub(r"\s+", " ", without)).strip()
    with_it = re.sub(r"\s+", " ", form.replace("(", "").replace(")", "")).strip()
    return without, with_it


def load_hunter():
    out = collections.defaultdict(list)
    for path in sorted(glob.glob(str(OUT / "Thao" / "blust_2003_thao_dictionary_*.xml"))):
        for sentence in etree.parse(path).getroot().findall("S"):
            match = re.match(r"^(.*?)(?:-alt\d+)?(?:-opt\d+(?:in|out))+$", sentence.get("id"))
            if not match:
                continue
            translation = sentence.find("TRANSL")
            out[match.group(1)].append((
                sentence.get("id"),
                sentence.find('FORM[@kindOf="original"]').text or "",
                (translation.text or "") if translation is not None else "",
            ))
    return out


def highlight(text):
    return E(text).replace("(", "<mark>(</mark>").replace(")", "<mark>)</mark>")


def main() -> int:
    hunter = load_hunter()
    rows = []
    for path in sorted(glob.glob(str(OUT / "Thao" / "*examples*.xml"))):
        for sentence in etree.parse(path).getroot().findall("S"):
            form = sentence.find('FORM[@kindOf="original"]').text or ""
            if "(" not in form:
                continue
            translation = sentence.find("TRANSL")
            rows.append((
                sentence.get("id"), sentence.get("source"), form,
                (translation.text or "") if translation is not None else "",
                translation.get("notes") if translation is not None else None,
            ))
    rows.sort(key=lambda row: row[0])

    items, counts = [], collections.Counter()
    for ident, source, form, english, notes in rows:
        thao_n, english_n = len(PAREN.findall(form)), len(PAREN.findall(english))
        if thao_n == 0:
            group = "unbalanced ("
        elif thao_n == english_n:
            group = "paired, splits in step"
        elif english_n == 0:
            group = "English is shared"
        else:
            group = "counts disagree"
        counts[group] += 1
        page = re.search(r"p(\d{4})", ident).group(1)
        without, with_it = readings(form)
        # Matched on the sentence itself, not on the page: this build files an
        # example under the page its ENTRY opens on, while extract_source.py
        # files it under the page it is PRINTED on, and a long entry spans
        # several. `haya (wa) caw m-in-aka-p-acay ...` is p.280 here and p.282
        # there.
        wanted = {key(without), key(with_it)}
        pair = [
            member for members in hunter.values() for member in members
            if key(member[1]) in wanted
        ]
        shipped = "".join(
            f'<div class="row"><span class="lab n">{E(pid.rsplit("-", 1)[1])}</span>'
            f'<span class="thao">{E(text)}</span></div>'
            for pid, text, _ in pair[:4]
        )
        items.append(
            f'<article class="entry" data-id="{E(ident)}" data-group="{E(group)}" '
            f'data-search="{E((form + " " + english + " " + page.lstrip("0")).lower())}">'
            f'<header><span class="hw">{highlight(form)}</span>'
            f'<span class="tag{"" if english_n == 0 else " b"}">{E(group)}</span>'
            f'<span class="pg">p.{page.lstrip("0")} &middot; {E(ident)}</span></header>'
            f'<div class="row"><span class="lab">english</span>'
            f'<span class="eng">{highlight(english) or "&mdash;"}</span></div>'
            + (f'<div class="row"><span class="lab n">note</span><span class="eng">{E(notes)}</span></div>'
               if notes else "")
            + '<div class="row"><span class="lab w">expanding would give</span></div>'
            f'<div class="row"><span class="lab n">without</span><span class="thao">{E(without)}</span></div>'
            f'<div class="row"><span class="lab n">with</span><span class="thao">{E(with_it)}</span></div>'
            + (f'<div class="row"><span class="lab">already shipped in XML/Thao</span></div>{shipped}'
               if shipped else "")
            + f'<div class="row"><span class="pg">{E(source)}</span></div></article>'
        )

    total = len(rows)
    render(
        ROOT / "XML" / ".." / "optional-examples.html",
        title="Optional Material In Examples",
        eyebrow="Blust 2003 Thao Dictionary · optional ( )",
        heading="Two brackets the parser could not close",
        dek=(
            "180 bracketed examples opened this page and the maintainer's rulings closed "
            "all but these. A bracket attached to a word became a <code>ver=\"alt\"</code> "
            "FORM, a bracketed particle stopped pairing with the English beside it, and a "
            "parenthetical that opens in the Thao and closes in the English is now lifted "
            "whole into a note. What remains is <b>not a scope question</b>: two of these "
            "carry an unbalanced bracket, which is a parse defect, and the maintainer has "
            "already said what p.321 should be - three readings sharing one English."
        ),
        footer="XML/Thao; bracketed FORMs went 180 -> 2",
        verdicts=["expand as shown", "English splits too", "not optional material", "needs the page"],
        store="thao-optional",
        groups=[("ALL", total, "")] + [(k, v, "") for k, v in counts.most_common()],
        items=items,
        resolved_heading='Every bracket resolved',
        resolved_note='It opened with <b>180</b> bracketed examples. The last two carried an unbalanced bracket, and the maintainer supplied the readings for both.',
    )
    print(f"optional-examples: {total}  {dict(counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
