#!/usr/bin/env python3
"""What did changing the source release change in the published XML, and why?

Compares two builds of the corpus -- XML built from an old source release and XML
built from a new one, *with the same pipeline code* -- sentence by sentence. It
ties each sentence back to the source records it is built from, and sorts every
sentence into one of these classes:

``source_changed``    the XML changed and so did its own source records: the
                      expected effect of a new release.
``code_reacted``      the XML changed but its source records did NOT. Something in
                      the pipeline reacted to a change elsewhere: a keyed table now
                      hitting a different item, an id renumbering, a corpus-wide
                      vote or lexicon. Every one needs an explanation.
``masked``            the source records changed but the XML did not. A later step
                      may be suppressing or overriding the change -- or the change
                      was to a field the build does not publish (see the
                      ``changed_fields`` column).
``added`` / ``removed``  a sentence id present in only one build.
``unchanged``         neither changed.

Old and new source files are paired by their local path (``source_release.tsv``
keeps our local names when NTU renames a file), and records by id. A Stories
sentence is its s_end group, named after the first record; a Grammar or
Sentences sentence is one record. Split sentences (``-opt``, ``-alt2``...) share
their parent's records. A record id that starts two groups in one file is keyed
``<id>``, ``<id>-2``, ... in file order, the names ``uniquify_sentence_ids.py``
gives the sentences.

``changed_fields`` names what differs between a sentence's old and new records:
the record dict's keys (``gloss``, ``free``, ``ori``, ``s_end``, ``meta``,
``s_a_span``, ...), or ``record ids`` when the group's records themselves differ.

    python compare_release_builds.py --old-xml OLD/XML --new-xml NEW/XML \\
        --old-json OLD/CodeAndDocs --new-json NEW/CodeAndDocs [--report out.md] [--tsv out.tsv]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from lxml import etree

SUBS = {"Grammar": "grammar", "Sentences": "sentence", "Stories": "story"}
SPLIT = re.compile(r"-[A-Za-z0-9]+$")


def canon_digest(el) -> str:
    return hashlib.sha1(etree.tostring(el, method="c14n")).hexdigest()


def sentences(xml_root: Path) -> dict:
    """{(sub, language dir, S id): (file name, digest of the canonical S)}."""
    out = {}
    for sub in SUBS:
        for path in sorted((xml_root / sub).rglob("*.xml")):
            for s in etree.parse(str(path)).getroot().iter("S"):
                out[(sub, path.parent.name, s.get("id"))] = (path.name, canon_digest(s))
    return out


def group_records(recs: list, per_record: bool) -> dict:
    """{group key: [records]}; a repeated group-start id gets '-2', '-3', ..."""
    groups, seen, key = {}, Counter(), None
    for r in recs:
        if key is None or per_record:
            rid = str(r[0])
            seen[rid] += 1
            key = rid if seen[rid] == 1 else f"{rid}-{seen[rid]}"
            groups[key] = []
        groups[key].append(r)
        if r[1].get("s_end", True):
            key = None
    return groups


def load_records(json_root: Path) -> dict:
    """{(sub, language, stem): {group key: [records]}}."""
    out = {}
    for sub, d in SUBS.items():
        for path in sorted((json_root / d).rglob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            recs = data["glosses"] if isinstance(data, dict) else data
            recs = [r for r in recs if isinstance(r, list) and len(r) > 1 and isinstance(r[1], dict)]
            language = path.parent.name.split("_")[0]
            out[(sub, language, path.stem)] = group_records(recs, per_record=sub != "Stories")
    return out


def records_for(key, index):
    """The records a sentence is built from, or None if its file is unknown.

    Tries the id as written, then with split suffixes peeled off one at a time,
    so 'X_S_6-2' finds a duplicate-start group '6-2' before falling back to '6'.
    """
    sub, language, sid = key
    base = sid
    while True:
        stem, _, rid = base.rpartition("_S_")
        groups = index.get((sub, language, stem))
        if groups is None:
            return None
        if rid in groups:
            return groups[rid]
        if not SPLIT.search(rid):
            return groups.get(rid.rstrip("abcdefgh"), [])
        base = SPLIT.sub("", base)


def changed_fields(old: list, new: list) -> list:
    if [r[0] for r in old] != [r[0] for r in new]:
        return ["record ids"]
    out = set()
    for (_, a), (_, b) in zip(old, new):
        for k in set(a) | set(b):
            if json.dumps(a.get(k), sort_keys=True, ensure_ascii=False) != \
                    json.dumps(b.get(k), sort_keys=True, ensure_ascii=False):
                out.add(k)
    return sorted(out)


def classify(old_s: dict, new_s: dict, old_r: dict, new_r: dict) -> list:
    rows = []
    for key in sorted(set(old_s) | set(new_s)):
        o, n = old_s.get(key), new_s.get(key)
        ro, rn = records_for(key, old_r), records_for(key, new_r)
        fields = [] if ro is None or rn is None else changed_fields(ro, rn)
        src = "unknown" if ro is None or rn is None else ("changed" if fields else "same")
        if o is None:
            cls = "added"
        elif n is None:
            cls = "removed"
        elif o[1] == n[1]:
            cls = "masked" if src == "changed" else "unchanged"
        else:
            cls = {"changed": "source_changed", "same": "code_reacted"}.get(src, "xml_changed_source_unknown")
        rows.append({"subcorpus": key[0], "language": key[1], "sentence": key[2],
                     "file": (o or n)[0], "class": cls, "source_records": src,
                     "changed_fields": ",".join(fields)})
    return rows


CLASSES = ["source_changed", "code_reacted", "masked", "added", "removed",
           "xml_changed_source_unknown", "unchanged"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--old-xml", type=Path, required=True)
    ap.add_argument("--new-xml", type=Path, required=True)
    ap.add_argument("--old-json", type=Path, required=True)
    ap.add_argument("--new-json", type=Path, required=True)
    ap.add_argument("--report", type=Path)
    ap.add_argument("--tsv", type=Path)
    args = ap.parse_args()

    rows = classify(sentences(args.old_xml), sentences(args.new_xml),
                    load_records(args.old_json), load_records(args.new_json))
    counts = Counter((r["subcorpus"], r["class"]) for r in rows)
    shown = [r for r in rows if r["class"] != "unchanged"]
    if args.tsv:
        with args.tsv.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["class"], delimiter="\t")
            w.writeheader()
            w.writerows(shown)
    lines = ["| subcorpus | " + " | ".join(CLASSES) + " |",
             "|---|" + "---|" * len(CLASSES)]
    for sub in SUBS:
        lines.append(f"| {sub} | " + " | ".join(str(counts[(sub, c)]) for c in CLASSES) + " |")
    masked = Counter((r["subcorpus"], r["changed_fields"]) for r in rows if r["class"] == "masked")
    if masked:
        lines += ["", "masked, by the source fields that changed:", "",
                  "| subcorpus | changed fields | sentences |", "|---|---|---|"]
        lines += [f"| {s} | {f} | {n} |" for (s, f), n in sorted(masked.items())]
    text = "\n".join(lines)
    print(text)
    if args.report:
        args.report.write_text("# Release comparison\n\n" + text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
