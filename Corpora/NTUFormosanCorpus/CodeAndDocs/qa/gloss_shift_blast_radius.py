#!/usr/bin/env python3
"""Did a gloss-shift repair change only the sentences it was aimed at?

Compares two builds of one subcorpus -- ``--baseline`` (without the repairs) and
``--candidate`` (with them) -- sentence by sentence, and sorts every difference
into one of two bins:

* **targeted**: the sentence contains a record named in a repair row that was in
  force for the candidate build. These are expected to change, and each one is
  scored before/after on the published word tier (below).
* **collateral**: anything else that changed -- a sentence no repair names, a
  sentence that appeared or vanished, a file-level attribute. A repair is meant
  to move cells inside one sentence, so any collateral change is a finding, and
  the run exits 1.

Collateral changes are further split by whether they are confined to the
morpheme tier. That split exists because of one known mechanism:
``apply_prune_and_mirror.py --only prune`` rebuilds a flagged sentence's M tier
from a corpus-wide donor pool keyed on word form, taking the *first* occurrence
in file order. Change the glosses of a word early in that order and the M
glosses of the same word in unrelated sentences change with it.

Scoring of targeted sentences uses the word tier of the published XML, the
evidence a user of the corpus sees:

``attested``     gloss cells (English and Chinese) whose (form, gloss) pair occurs
                 on some other W of the same language in the baseline
                 (leave-one-out);
``morph_match``  gloss cells whose gloss implies as many morphemes as the form;
``unglossed``    W elements with no gloss in either language.

A repair should raise ``attested``, and not lower ``morph_match``.

    python gloss_shift_blast_radius.py --baseline <xml dir> --candidate <xml dir> \\
        [--codedocs ..] [--table ../pipeline/gloss_shift_repairs.tsv] \\
        [--statuses accepted,proposed] [--report out.md]
"""
from __future__ import annotations

import argparse
import copy
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from lxml import etree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "pipeline"))
from gloss_shift import REPAIRS_TSV, load_table, norm_form, records_of  # noqa: E402
from sentence_xml_tests import gloss_pieces, morpheme_count  # noqa: E402

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def form_text(el) -> str:
    node = el.find("FORM[@kindOf='original']")
    return "".join(node.itertext()).strip() if node is not None else ""


def gloss(el, lang: str) -> str:
    for t in el.findall("TRANSL"):
        if t.get(XML_LANG) == lang and t.get("ver") is None:
            return (t.text or "").strip()
    return ""


def eng(el) -> str:
    return gloss(el, "eng")


LANGS = ("eng", "zho")   # Grammar glosses in Chinese only; score both


def sentences(root: Path) -> dict:
    """{(language dir, S id): (language dir, file, element)} for a subcorpus build.

    Keyed on the language too: Grammar S ids are only unique within one
    language's file (05_S_13 exists for Kanakanavu, Sakizaya and Seediq).
    """
    out = {}
    for path in sorted(root.rglob("*.xml")):
        tree = etree.parse(str(path))
        for s in tree.getroot().iter("S"):
            out[(path.parent.name, s.get("id"))] = (path.parent.name, path.relative_to(root).as_posix(), s)
    return out


def text_attrs(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): dict(etree.parse(str(p)).getroot().attrib)
            for p in sorted(root.rglob("*.xml"))}


def canon(el) -> bytes:
    return etree.tostring(el, method="c14n")


def without_m(el) -> bytes:
    """The sentence with its M elements, and all indentation, taken out.

    Indentation must go too: removing an element also removes its tail, so the
    whitespace before ``</W>`` differs between a W that had Ms and one that
    did not, though nothing a reader sees does.
    """
    clone = copy.deepcopy(el)
    for m in list(clone.iter("M")):     # list(): removing while iterating skips siblings
        m.getparent().remove(m)
    for node in clone.iter():
        if node.text is not None and not node.text.strip():
            node.text = None
        if node.tail is not None and not node.tail.strip():
            node.tail = None
    return canon(clone)


def targeted_prefixes(codedocs: Path, rows: list) -> dict:
    """{(language dir, S-id prefix): [table rows]} -- where each repair lands.

    In Stories a sentence takes the id of the first record in its s_end group;
    Grammar and Sentences publish one sentence per record. A sentence split
    later in the build (``-opt``, ``-alt2``, ...) keeps its prefix. A repair
    spanning records names every sentence it touches.
    """
    out = defaultdict(list)
    for row in rows:
        path = codedocs / row["source_file"]
        language = path.parent.name.split("_")[0]
        per_record = row["source_file"].startswith(("grammar/", "sentence/"))
        first_of = {}
        start = None
        for rec in records_of(path):
            if start is None or per_record:
                start = rec[0]
            first_of[str(rec[0])] = start
            if rec[1].get("s_end", True):
                start = None
        for rid in row["record_ids"].split("+"):
            key = (language, f"{path.stem}_S_{first_of[rid]}")
            if row not in out[key]:
                out[key].append(row)
    return out


def is_targeted(key: tuple, prefixes: dict):
    language, sid = key
    for lang, p in prefixes:
        if lang == language and re.fullmatch(re.escape(p) + r"(-[A-Za-z0-9]+)*", sid):
            return (lang, p)
    return None


def _pairs(s) -> Counter:
    out = Counter()
    for w in s.findall("W"):
        for gl in LANGS:
            g = gloss(w, gl)
            if g and g != "_":
                out[(norm_form(form_text(w)), gl, g)] += 1
    return out


def lexicon(sents: dict) -> dict:
    lex = defaultdict(Counter)
    for lang, _, s in sents.values():
        lex[lang].update(_pairs(s))
    return lex


def w_score(s, lang: str, lex: dict, own) -> Counter:
    """Word-tier evidence, per gloss cell (English and Chinese), leave-one-out."""
    mine = _pairs(own) if own is not None else Counter()
    c = Counter(words=0, attested=0, morph_match=0, unglossed=0)
    for w in s.findall("W"):
        c["words"] += 1
        f = form_text(w)
        cells = [(gl, gloss(w, gl)) for gl in LANGS]
        cells = [(gl, g) for gl, g in cells if g and g != "_"]
        if not cells:
            c["unglossed"] += 1
            continue
        for gl, g in cells:
            key = (norm_form(f), gl, g)
            if lex[lang][key] - mine[key] > 0:
                c["attested"] += 1
            c["morph_match"] += int(morpheme_count(f) == gloss_pieces(g))
    return c


def w_table(s) -> list:
    return [f"| {k} | `{form_text(w)}` | {eng(w)} |" for k, w in enumerate(s.findall("W"))]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--baseline", type=Path, required=True)
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--codedocs", type=Path, default=HERE.parent)
    ap.add_argument("--table", type=Path, default=REPAIRS_TSV)
    ap.add_argument("--statuses", default="accepted",
                    help="the table statuses that were in force for --candidate")
    ap.add_argument("--report", type=Path, help="also write a Markdown report here")
    ap.add_argument("--allow-collateral", action="store_true",
                    help="report collateral changes but exit 0")
    args = ap.parse_args()

    rows = load_table(args.table, {s.strip() for s in args.statuses.split(",")})
    # Only rows for the subcorpus being compared: a Stories build cannot show a
    # Grammar repair, and listing it as "did not change" would be noise.
    sub = {"grammar": "grammar/", "sentences": "sentence/", "stories": "story/"}.get(
        args.baseline.name.lower())
    if sub:
        rows = [r for r in rows if r["source_file"].startswith(sub)]
    prefixes = targeted_prefixes(args.codedocs, rows)
    base, cand = sentences(args.baseline), sentences(args.candidate)
    lex = lexicon(base)

    changed_t, changed_c, m_only = [], [], []
    for sid in sorted(set(base) | set(cand)):   # sid is (language dir, S id)
        b, c = base.get(sid), cand.get(sid)
        if b is not None and c is not None and canon(b[2]) == canon(c[2]):
            continue
        if is_targeted(sid, prefixes):
            changed_t.append(sid)
        else:
            changed_c.append(sid)
            if b is not None and c is not None and without_m(b[2]) == without_m(c[2]):
                m_only.append(sid)
    base_attrs, cand_attrs = text_attrs(args.baseline), text_attrs(args.candidate)
    attr_diff = sorted(f for f in set(base_attrs) | set(cand_attrs)
                       if base_attrs.get(f) != cand_attrs.get(f))
    untouched = ["/".join(p) for p in prefixes if not any(is_targeted(s, {p: 0}) for s in changed_t)]

    out = [f"# Gloss-shift blast radius", "",
           f"- repair rows in force ({args.statuses}): {len(rows)}, "
           f"aimed at {len(prefixes)} sentence(s)",
           f"- sentences compared: {len(set(base) | set(cand))}",
           f"- targeted sentences that changed: {len(changed_t)}",
           f"- targeted sentences that did NOT change: {len(untouched)} {untouched[:10]}",
           f"- **collateral sentences changed: {len(changed_c)}** "
           f"({len(m_only)} of them only in the M tier)",
           f"- files whose TEXT attributes changed: {len(attr_diff)} {attr_diff[:5]}", ""]

    total_b, total_c = Counter(), Counter()
    if changed_t:
        out += ["## Targeted sentences, word tier before -> after", "",
                "| sentence | attested | morph_match | unglossed |", "|---|---|---|---|"]
        detail = []
        for sid in changed_t:
            b, c = base.get(sid), cand.get(sid)
            lang = (b or c)[0]
            sb = w_score(b[2], lang, lex, b[2]) if b else Counter()
            sc = w_score(c[2], lang, lex, b[2] if b else None) if c else Counter()
            total_b += sb
            total_c += sc
            flag = "" if (sc["attested"] > sb["attested"] and sc["morph_match"] >= sb["morph_match"]) else " ⚠"
            out.append(f"| `{sid[0]}/{sid[1]}`{flag} | {sb['attested']} → {sc['attested']} | "
                       f"{sb['morph_match']} → {sc['morph_match']} | {sb['unglossed']} → {sc['unglossed']} |")
            detail += [f"### `{sid[0]}/{sid[1]}`", "", "| W | form | eng before |", "|---|---|---|",
                       *(w_table(b[2]) if b else []), "",
                       "| W | form | eng after |", "|---|---|---|", *(w_table(c[2]) if c else []), ""]
        out += [f"| **total** | {total_b['attested']} → {total_c['attested']} | "
                f"{total_b['morph_match']} → {total_c['morph_match']} | "
                f"{total_b['unglossed']} → {total_c['unglossed']} |", ""] + detail
    if changed_c:
        out += ["## Collateral changes", "",
                "| sentence | file | only the M tier? |", "|---|---|---|"]
        for sid in changed_c[:200]:
            b, c = base.get(sid), cand.get(sid)
            where = (b or c)[1]
            state = "added" if b is None else "removed" if c is None else ("yes" if sid in m_only else "NO")
            out.append(f"| `{sid[1]}` | {where} | {state} |")
        if len(changed_c) > 200:
            out.append(f"| ... {len(changed_c) - 200} more | | |")
        out.append("")

    text = "\n".join(out) + "\n"
    if args.report:
        args.report.write_text(text, encoding="utf-8")
    print("\n".join(out[:9]))
    if total_b or total_c:
        print(f"targeted word tier: attested {total_b['attested']} -> {total_c['attested']}, "
              f"morph_match {total_b['morph_match']} -> {total_c['morph_match']}, "
              f"unglossed {total_b['unglossed']} -> {total_c['unglossed']}")
    if args.report:
        print(f"report: {args.report}")
    bad = changed_c or attr_diff
    return 1 if bad and not args.allow_collateral else 0


if __name__ == "__main__":
    raise SystemExit(main())
