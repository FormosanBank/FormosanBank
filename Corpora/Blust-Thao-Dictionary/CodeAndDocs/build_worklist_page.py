"""Rebuild the maintainer's worklist page from the current records + findings.

The page is a shell (filters, note boxes, the db wiring) plus three generated
regions: the chip row, the entry list, and the footer counts.  Only those three
are rewritten, so the shell can be hand-edited and survives a regeneration.
"""

import argparse
import collections
import csv
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The rule titles come from the validator, never a second copy here: the copy
# that used to live in this file drifted, so the worklist labelled E03 with its
# old meaning and the maintainer read a card that said something else entirely
# (2026-09-11).
from validate_entries import RULE_TITLES as RULE_TEXT  # noqa: E402
from build_review_page import card_id  # noqa: E402
MAX_SENSES = 24
E = lambda s: html.escape(str(s or ""), quote=True)


def render_entry(entry, rules, details):
    head, page = entry["headword"], entry["printed_page"]
    fmt = entry["format"]
    marker = entry.get("root_marker")
    label = f"format {fmt}" + (f" · {marker}" if marker else "")
    out = [
        f'<article class="entry" data-id="{E(head)}__{page}" '
        f'data-db-id="{E(card_id(head, page))}" '
        f'data-rules="{E(" ".join(rules))}" data-page="{page}" data-head="{E(head)}">',
        f'<header><span class="hw">{E(head)}</span>'
        f'<span class="fmt fmt-{fmt}">{E(label)}</span>'
        f'<span class="pg">printed p.{page}</span>',
    ]
    for rule in rules:
        out.append(f'<span class="rule" title="{E(RULE_TEXT.get(rule, rule))}">{rule}</span>')
    out.append("</header><ul class=\"why\">")
    for detail in details:
        out.append(f"<li>{E(detail)}</li>")
    out.append('</ul><div class="senses">')
    for sense in entry["senses"][:MAX_SENSES]:
        number = sense["number"]
        shown = "—" if number is None else f"{number}{sense.get('subsense') or ''}"
        if sense.get("number_inferred"):
            shown += "*"
        out.append(f'<div class="sense"><span class="num">{E(shown)}</span>'
                   f'<span class="form">{E(sense["form"])}</span>')
        if sense.get("label"):
            out.append(f'<span class="lbl">{E(sense["label"])}</span>')
        out.append(f'<span class="def">{E(sense["definition"])}</span>')
        for example in sense["examples"]:
            out.append(f'<div class="ex"><span class="t">{E(example["thao"])}</span>'
                       f'<span class="b">{E(example.get("exemplifies"))}</span>'
                       f'<span class="e">{E(example["english"])}</span></div>')
        for target in sense.get("cross_references", []):
            out.append(f'<div class="xref">→ {E(target)}</div>')
        out.append("</div>")
    if len(entry["senses"]) > MAX_SENSES:
        out.append(f'<div class="sense"><span class="num">…</span>'
                   f'<span class="def">{len(entry["senses"]) - MAX_SENSES} more senses'
                   f'</span></div>')
    out.append('</div><div class="verdict"></div></article>')
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", required=True, help="the page to rewrite in place")
    ap.add_argument("--records", default=HERE / "entry-records.json")
    ap.add_argument("--findings", default=HERE / "entry-findings.tsv")
    args = ap.parse_args()

    data = json.loads(Path(args.records).read_text(encoding="utf-8"))
    entries = data["entries"]
    first = {}
    for entry in entries:
        first.setdefault((entry["headword"], str(entry["printed_page"])), entry)

    findings = collections.OrderedDict()
    with open(args.findings, encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            findings.setdefault((row["headword"], row["printed_page"]), []).append(row)

    counts = collections.Counter()
    articles = []
    for key, rows in findings.items():
        entry = first.get(key)
        if entry is None:
            continue
        rules = sorted({row["rule"] for row in rows})
        counts.update(rules)
        articles.append(render_entry(entry, rules, [row["detail"] for row in rows]))

    chips = "".join(
        f'<button class="chip" data-rule="{rule}">{rule} <b>{counts[rule]}</b> '
        f'<span>{E(RULE_TEXT.get(rule, rule))}</span></button>'
        for rule in sorted(counts)
    )
    chips += (f'\n<button class="chip" data-rule="ALL" aria-pressed="true">ALL '
              f'<b>{len(articles)}</b></button>')

    senses = sum(len(e["senses"]) for e in entries)
    inferred = sum(1 for e in entries for s in e["senses"] if s.get("number_inferred"))
    examples = sum(len(s["examples"]) for e in entries for s in e["senses"])
    xrefs = sum(len(s.get("cross_references", [])) for e in entries for s in e["senses"])
    notes = sum(len(s["notes"]) for e in entries for s in e["senses"])
    roots = collections.Counter(e.get("root_marker") for e in entries)
    footer = (
        f'{len(entries):,} entries · {senses:,} senses ({inferred} numbers inferred) · '
        f'{examples:,} examples · {xrefs:,} cross-references · '
        f'{roots["bars"]} roots marked with bars, {roots["colon"]} with a bare colon · '
        f'{notes} notes · 100.0% of printed characters consumed<br>'
    )

    page = Path(args.page)
    lines = page.read_text(encoding="utf-8").split("\n")
    chip_start = next(i for i, l in enumerate(lines) if 'class="chips"' in l)
    chip_end = next(i for i, l in enumerate(lines) if 'data-rule="ALL"' in l)
    art_at = next(i for i, l in enumerate(lines) if l.startswith('<article class="entry"'))
    foot_at = next(i for i, l in enumerate(lines) if l.endswith("consumed<br>"))

    lines[art_at] = "".join(articles)
    lines[foot_at] = footer
    lines[chip_start:chip_end + 1] = [f'<div class="bar"><div class="chips">{chips}']
    page.write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(articles)} entries · chips {dict(counts)}")
    print(f"roots: {roots['bars']} bars, {roots['colon']} colon")


if __name__ == "__main__":
    main()
