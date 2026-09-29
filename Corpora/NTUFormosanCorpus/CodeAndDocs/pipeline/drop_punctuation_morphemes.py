#!/usr/bin/env python3
"""Remove punctuation-only morphemes from multimorphemic words.

Maintainer ruling, 2026-09-28: "in a multimorphemic word, if one segment
consists only of puncutation and is not glossed, delete it. If it is glossed
with a non-trivial gloss but there are fewer glosses than segments, also delete
the punctuation-only segment and shift the gloss so it applies to the segment
after the punctuation. If there is no segment after the punctuation, escalate."

Where these come from: a false start or a cut-off word written with its
punctuation, such as ``ta-,`` or ``ta-.``. The builder splits it on ``-``, which
gives a morpheme whose form is ``,`` or ``.``. Left in place, it makes
``apply_prune_and_mirror.py`` judge the word's morphemes unreconcilable. Before
this step, 336 of prune's 1,391 regenerations were triggered by nothing else.

A segment is punctuation-only when its FORM is non-empty but has no letter,
digit or null marker. (An empty FORM is a shell, not punctuation: it is left
for ``apply_prune_and_mirror.py``.) A gloss is non-trivial when it has such content. "Fewer glosses than
segments": fewer of the word's Ms carry a non-trivial gloss than there are Ms.
The shift moves the punctuation segment's glosses (every language together) to
the next M, whose own glosses move on in turn, until an M with no gloss absorbs
the chain. The W's FORM is left as written: its punctuation is source text.
A '=' in front of the deleted piece stays in the M tier, on the M before it
('na=,' -> 'na='), as the corpus writes a clitic whose host is absent.

Escalated (left unchanged, and reported in ``--report``):
  * the punctuation segment is glossed but is the last M;
  * it is glossed, but no gloss-less M follows it to absorb the shift;
  * it is glossed and every segment is glossed (the ruling does not cover this).

    python drop_punctuation_morphemes.py --xml_dir <dir> [--report escalations.tsv] [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "qa"))
from sentence_xml_tests import substantive  # noqa: E402

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def form_text(el) -> str:
    node = el.find("FORM[@kindOf='original']")
    if node is None:
        node = el.find("FORM")
    return "".join(node.itertext()) if node is not None else ""


def glossed(m) -> bool:
    return any(substantive((t.text or "").strip()) and (t.text or "").strip() != "_"
               for t in m.findall("TRANSL"))


def take_glosses(m) -> list:
    out = []
    for t in m.findall("TRANSL"):
        m.remove(t)
        out.append(t)
    return out


def put_glosses(m, transls: list) -> None:
    for t in transls:
        m.append(t)


def separators_before(w_form: str) -> list:
    """The separator in front of each piece of a W FORM, in order ('' for the first).

    Pieces are what the builder cuts at '-' and '=', after infixes are taken
    out, punctuation-only pieces included: 'na=,' -> ['', '='].
    """
    rest = re.sub(r"<[^>]+>", "", (w_form or "").strip())
    out, sep = [], ""
    for part in re.split(r"([-=])", rest):
        if part in ("-", "="):
            sep = part
        elif part.strip():
            out.append(sep)
            sep = ""
    return out


def keep_clitic_boundary(w, ms: list, k: int, stats: Counter) -> None:
    """Deleting piece k must not delete the '=' in front of it.

    'na=,' is a proclitic whose host was cut off; the builder writes it as the
    Ms 'na' and ','. The '=' belongs to 'na', which the corpus writes 'na='
    when it has no host (and '=na' when it is an enclitic). Dropping ',' alone
    would leave no M carrying the W's '=' (V066, HARD).
    """
    seps = separators_before(form_text(w))
    if len(seps) != len(ms) or seps[k] != "=" or k == 0:
        return
    node = ms[k - 1].find("FORM[@kindOf='original']")
    if node is None or (node.text or "").rstrip().endswith("="):
        return
    node.text = (node.text or "").rstrip() + "="
    stats["  '=' kept on the preceding M (clitic whose host was cut off)"] += 1


def repair_word(w, stats: Counter, escalate: list) -> bool:
    changed = False
    while True:
        ms = w.findall("M")
        if len(ms) < 2:
            return changed
        # Punctuation-only: a non-empty form with no letter, digit or null marker.
        # An EMPTY form is a different thing (a shell left by a gloss with more
        # pieces than the form); apply_prune_and_mirror handles those.
        punct = [k for k, m in enumerate(ms)
                 if form_text(m).strip() and not substantive(form_text(m).strip())]
        if not punct:
            return changed
        k = punct[0]
        m = ms[k]
        if not glossed(m):
            keep_clitic_boundary(w, ms, k, stats)
            w.remove(m)
            stats["punctuation-only M, unglossed: deleted"] += 1
            changed = True
            continue
        n_glossed = sum(1 for x in ms if glossed(x))
        why = None
        if n_glossed >= len(ms):
            why = "glossed, and every segment is glossed (not covered by the rule)"
        elif k == len(ms) - 1:
            why = "glossed, and no segment follows it"
        else:
            absorb = next((j for j in range(k + 1, len(ms)) if not glossed(ms[j])), None)
            if absorb is None:
                why = "glossed, and no unglossed segment follows it to absorb the shift"
        if why:
            escalate.append({"W": w.get("id"), "word": form_text(w),
                             "segments": " | ".join(form_text(x) for x in ms),
                             "punctuation segment": form_text(m), "reason": why})
            stats["punctuation-only M: escalated"] += 1
            return changed
        carried = take_glosses(m)
        for j in range(k + 1, absorb + 1):
            # The absorbing M's own TRANSLs are empty or trivial: they are taken
            # off and discarded, so it never ends up with two per language.
            held = take_glosses(ms[j])
            put_glosses(ms[j], carried)
            carried = held
        keep_clitic_boundary(w, ms, k, stats)
        w.remove(m)
        stats["punctuation-only M, glossed: deleted, gloss shifted right"] += 1
        changed = True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", required=True, type=Path)
    ap.add_argument("--report", type=Path, help="write escalations here (TSV)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    stats, escalate, files = Counter(), [], 0
    for path in sorted(args.xml_dir.rglob("*.xml")):
        tree = etree.parse(str(path))
        changed = False
        for w in tree.getroot().iter("W"):
            before = len(escalate)
            if repair_word(w, stats, escalate):
                changed = True
            for row in escalate[before:]:
                row["file"] = path.relative_to(args.xml_dir).as_posix()
        if changed and not args.dry_run:
            tree.write(str(path), encoding="utf-8", xml_declaration=True)
            files += 1
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("w", encoding="utf-8", newline="") as fh:
            cols = ["file", "W", "word", "segments", "punctuation segment", "reason"]
            wr = csv.DictWriter(fh, fieldnames=cols, delimiter="\t")
            wr.writeheader()
            wr.writerows(escalate)
    print(f"files modified: {files}")
    for k in sorted(stats):
        print(f"  {k}: {stats[k]}")
    if args.report:
        print(f"  escalations written to {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
