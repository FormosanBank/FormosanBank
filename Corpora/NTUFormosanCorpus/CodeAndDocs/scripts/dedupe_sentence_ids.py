#!/usr/bin/env python3
"""dedupe_sentence_ids.py

Disambiguate duplicate <S> ids caused by record-id collisions in the
NTU source JSONs.

A few source files assign the same record id to two *different*
sentences (e.g. ``sentence/Bunun_Isbukun/46.json`` numbers its records
1,2,3,3,4,...). The parsers build S ids as ``{filestem}_S_{record_id}``,
so the collision propagates into the XML: two distinct sentences share
an S id, and their W/M children share ids too. ``parse_sentences.py``
now disambiguates at generation time; this script applies the identical
renaming to already-published XML without a full regeneration.

For the second-and-later occurrence (in document order) of a duplicated
S id, the S id gains a ``-2`` / ``-3`` ... suffix and every descendant
id that starts with the old S id has that prefix rewritten (e.g.
``46_S_3`` -> ``46_S_3-2``, ``46_S_3_W0`` -> ``46_S_3-2_W0``). Element
content is never touched.

Audio safety: AUDIO file names elsewhere in the corpus embed sentence
ids, so renaming an id under a sentence that carries AUDIO could orphan
its files. Any duplicated sentence containing an AUDIO descendant is
therefore skipped with a warning (none exist today: the duplicates are
all in the Sentences subcorpus, which has no audio).

A file is rewritten only if its unmodified tree first re-serializes
byte-identically (lxml, xml declaration, UTF-8). Idempotent.

Usage
-----
    python dedupe_sentence_ids.py            # corpus XML/ by default
    python dedupe_sentence_ids.py --dry-run
"""

import argparse
import collections
import os
from pathlib import Path

import lxml.etree as etree


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def dedupe_file(path, dry_run=False):
    original = open(path, "rb").read()
    tree = etree.parse(path)
    if serialize(tree) != original:
        return None  # round-trip guard: do not touch
    root = tree.getroot()
    sentences = [s for s in root.iter("S")]
    counts = collections.Counter(s.get("id") for s in sentences)
    dup_ids = {i for i, n in counts.items() if i is not None and n > 1}
    if not dup_ids:
        return 0
    renamed = 0
    seen = collections.Counter()
    for s in sentences:
        sid = s.get("id")
        if sid not in dup_ids:
            continue
        seen[sid] += 1
        if seen[sid] == 1:
            continue  # first occurrence keeps its id
        if s.find(".//AUDIO") is not None:
            print(f"  WARNING: not renaming {sid!r} in {path} "
                  f"(sentence carries AUDIO; file names may embed ids)")
            continue
        new_sid = f"{sid}-{seen[sid]}"
        s.set("id", new_sid)
        for child in s.iter():
            cid = child.get("id")
            if child is not s and cid and cid.startswith(sid):
                child.set("id", new_sid + cid[len(sid):])
        renamed += 1
        print(f"  {os.path.basename(path)}: {sid} (occurrence {seen[sid]}) -> {new_sid}")
    if renamed and not dry_run:
        with open(path, "wb") as f:
            f.write(serialize(tree))
    return renamed


def main():
    corpus = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", default=str(corpus / "XML"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total = 0
    skipped = []
    for dirpath, _, filenames in os.walk(args.xml_dir):
        for fn in sorted(filenames):
            if not fn.endswith(".xml"):
                continue
            path = os.path.join(dirpath, fn)
            result = dedupe_file(path, dry_run=args.dry_run)
            if result is None:
                skipped.append(path)
            else:
                total += result
    verb = "would be " if args.dry_run else ""
    print(f"\nsentences {verb}renamed: {total}")
    if skipped:
        print(f"files skipped (round-trip guard): {len(skipped)}")
        for p in skipped:
            print(f"  SKIP: {p}")


if __name__ == "__main__":
    main()
