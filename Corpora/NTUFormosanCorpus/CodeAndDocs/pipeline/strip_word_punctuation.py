#!/usr/bin/env python3
"""Delete punctuation from word (W) and morpheme (M) FORMs.

Maintainer's ruling, 2026-10-18 (option "Bare <UNCLEAR/>"): "Punctuation
shouldn't be in W FORMs or M FORMs anyway. Delete everywhere in NTU."

NTU writes a word's punctuation into its word and morpheme forms (``haca,``),
copied from the sentence line. This step removes it from every W and M FORM
(every kindOf, every variant). Sentence-level FORMs keep their punctuation; no
PHON or TRANSL is touched.

What counts as punctuation is decided per language, in
``../word_form_characters.tsv``: every character other than a letter or digit
that occurs in a W or M FORM, with its class and action.

  * delete: punctuation (, . ! ? ") -- removed;
  * keep:   a letter of that language's orthography (' is the glottal stop in
            Ortho94 and Ortho113 for every NTU language but Seediq) or a
            morpheme-structure marker (- = < > ~ ∅);
  * hold:   not clear that it is punctuation in that language (. between the
            syllables of a loan, tou.mu; ? standing for an unknown morpheme,
            alupu-?=ini; ...) -- left in place, every occurrence, until the
            maintainer rules.

A character that the table does not list for the language stops the build, so
nothing new is deleted, or kept, without being classified first.

A FORM that would be left with no letter, digit, null marker or <UNCLEAR/> (a
word written only ``,``) is left as it is and reported: deleting would empty it.

Runs after mark_unclear.py (which already writes an untranscribed word's FORM as
a bare <UNCLEAR/>). Idempotent. ``--report`` writes one TSV row per changed or
held FORM.

usage: strip_word_punctuation.py --xml_dir <dir> [--table <tsv>] [--report <tsv>]
"""
import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

from lxml import etree

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
ACTIONS = {"delete", "keep", "hold"}


def load_table(path):
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines()
             if ln.strip() and not ln.startswith("#")]
    table = {}
    for r in csv.DictReader(lines, delimiter="\t", quoting=csv.QUOTE_NONE):
        if r["action"] not in ACTIONS or len(r["char"]) != 1 or f"U+{ord(r['char']):04X}" != r["codepoint"]:
            raise SystemExit(f"strip_word_punctuation: {path}: bad row {r}")
        if (r["lang"], r["char"]) in table:
            raise SystemExit(f"strip_word_punctuation: {path}: duplicate row {r['lang']} {r['char']!r}")
        table[(r["lang"], r["char"])] = r["action"]
    return table


NULLS = set("∅Øø")


def is_content(ch):
    """A letter, a digit or a null-morpheme marker."""
    return ch.isalpha() or ch.isdigit() or ch in NULLS


def write_like(path, root):
    """Rewrite path keeping its own bytes before and after the root element."""
    raw = path.read_text(encoding="utf-8")
    start = raw.index("<" + root.tag)
    end = raw.rindex("</" + root.tag + ">") + len(root.tag) + 3
    body = etree.tostring(root, encoding="unicode", with_tail=False)
    path.write_text(raw[:start] + body + raw[end:], encoding="utf-8")


def process_form(form, lang, table, counts, unlisted):
    """Delete the table's 'delete' characters from form's text segments.

    Returns 'changed', 'held-empty' or None.
    """
    if any(c.tag != "UNCLEAR" for c in form):
        raise SystemExit(f"strip_word_punctuation: FORM has a child other than UNCLEAR: "
                         f"{etree.tostring(form, encoding='unicode')!r}")
    segs = [form.text or ""] + [c.tail or "" for c in form]
    new, dropped = [], Counter()
    for seg in segs:
        out = []
        for ch in seg:
            if is_content(ch):
                out.append(ch)
                continue
            action = table.get((lang, ch))
            if action is None:
                unlisted[(lang, ch)] += 1
                out.append(ch)
            elif action == "delete":
                dropped[ch] += 1
            else:
                out.append(ch)
        new.append("".join(out))
    if not dropped:
        return None
    if len(form) == 0 and not any(is_content(ch) for ch in new[0]):
        counts["FORM held: deleting would empty it"] += 1
        return "held-empty"
    form.text = new[0] or None
    for child, tail in zip(form, new[1:]):
        child.tail = tail or None
    for ch, n in dropped.items():
        counts[f"deleted {lang} {ch!r}"] += n
    counts["FORM elements changed"] += 1
    return "changed"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml_dir", required=True, type=Path)
    ap.add_argument("--table", type=Path,
                    default=Path(__file__).resolve().parent.parent / "word_form_characters.tsv")
    ap.add_argument("--report", type=Path)
    args = ap.parse_args(argv)
    table = load_table(args.table)
    counts, unlisted, report, files = Counter(), Counter(), [], 0
    for path in sorted(args.xml_dir.rglob("*.xml")):
        tree = etree.parse(str(path))
        root = tree.getroot()
        lang = root.get(XML_LANG)
        rel = str(path.relative_to(args.xml_dir))
        changed = False
        for el in root.iter("W", "M"):
            for form in el.findall("FORM"):
                before = etree.tostring(form, encoding="unicode", with_tail=False)
                result = process_form(form, lang, table, counts, unlisted)
                if result is None:
                    continue
                where = f"{el.get('id')} kindOf={form.get('kindOf')}" + (f" ver={form.get('ver')}" if form.get("ver") else "")
                after = etree.tostring(form, encoding="unicode", with_tail=False) if result == "changed" else "(held)"
                report.append((rel, el.tag, where, result, before, after))
                changed |= result == "changed"
        if changed:
            write_like(path, root)
            files += 1
    if unlisted:
        for (lang, ch), n in sorted(unlisted.items()):
            print(f"strip_word_punctuation: {lang} {ch!r} U+{ord(ch):04X} ({n}x) is not in {args.table}",
                  file=sys.stderr)
        raise SystemExit("strip_word_punctuation: unclassified characters; add them to the table first")
    for key in sorted(counts):
        print(f"  {key}: {counts[key]}")
    print(f"files rewritten: {files}")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("w", encoding="utf-8", newline="") as fh:
            out = csv.writer(fh, delimiter="\t", lineterminator="\n")
            out.writerow(["file", "level", "where", "result", "before", "after"])
            out.writerows(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
