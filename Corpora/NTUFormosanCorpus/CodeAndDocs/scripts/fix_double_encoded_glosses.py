#!/usr/bin/env python3
"""fix_double_encoded_glosses.py

Decode double-encoded XML entities (exactly one level) in element text.

Background
----------
The NTU source JSONs are inconsistent about angle brackets in gloss and
infix notation: most store the real characters (``<RED>cook-LF``,
``t<um>ian``), but a few store HTML-escaped strings (``&lt;RED&gt;cook-LF``).
Where an escaped string reached the XML writer verbatim, serialization
escaped the ``&`` again, so the published file carries ``&amp;lt;`` --
a double encoding. In the decoded text tier this surfaces as the literal
string ``&lt;`` instead of the bracket character ``<`` (flagged by
``validate_text.py`` rule V132).

Survey of the published corpus (2026-06): the only affected file is
``XML/Sentences/Bunun/Bunun.xml`` -- 1,109 TRANSL elements (556 zho /
553 eng; source ``sentence/Bunun_Isbukun/63.json``) plus 3 TRANSL
``notes`` attributes, and the only entities involved are
``&lt;``/``&gt;``. The same file already writes 2,700+ glosses with
real brackets, so decoding converges on the file's own majority
convention. No FORM or PHON text is affected.

The fix replaces literal entity strings (``&lt; &gt; &amp; &quot;
&apos;``) in element text and attribute values with their characters,
in a single
non-iterating pass: exactly one decode level, so a legitimate future
``&amp;amp;`` would become ``&amp;``, never ``&``. After one pass no
literal entity strings remain, making the script idempotent.

Pipeline position: run after the parsers (any order relative to the
other post-hoc repairs); on the published corpus it runs in place.

A file is rewritten only if its unmodified tree first re-serializes
byte-identically (lxml, xml declaration, UTF-8). Idempotent.

Usage
-----
    python fix_double_encoded_glosses.py            # corpus XML/ by default
    python fix_double_encoded_glosses.py --dry-run
"""

import argparse
import collections
import os
import re
from pathlib import Path

import lxml.etree as etree

_ENTITY_RE = re.compile(r"&(amp|apos|lt|gt|quot);")
_ENTITY_CHAR = {"amp": "&", "apos": "'", "lt": "<", "gt": ">", "quot": '"'}


def decode_once(text):
    return _ENTITY_RE.sub(lambda m: _ENTITY_CHAR[m.group(1)], text)


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def process_file(path, dry_run, stats):
    original = open(path, "rb").read()
    tree = etree.parse(path)
    if serialize(tree) != original:
        stats["file skipped: round-trip guard"] += 1
        return False
    modified = False
    for el in tree.getroot().iter():
        text = el.text
        if text and _ENTITY_RE.search(text):
            for ent in _ENTITY_RE.findall(text):
                stats[f"&{ent}; decoded ({el.tag})"] += 1
            el.text = decode_once(text)
            stats[f"elements changed ({el.tag})"] += 1
            modified = True
        for attr, value in el.attrib.items():
            if not _ENTITY_RE.search(value):
                continue
            for ent in _ENTITY_RE.findall(value):
                stats[f"&{ent}; decoded ({el.tag}@{attr})"] += 1
            el.set(attr, decode_once(value))
            stats[f"attributes changed ({el.tag}@{attr})"] += 1
            modified = True
    if modified and not dry_run:
        with open(path, "wb") as f:
            f.write(serialize(tree))
    return modified


def main():
    corpus = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", default=str(corpus / "XML"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    stats = collections.Counter()
    files = 0
    for dirpath, _, filenames in os.walk(args.xml_dir):
        for fn in sorted(filenames):
            if not fn.endswith(".xml"):
                continue
            if process_file(os.path.join(dirpath, fn), args.dry_run, stats):
                files += 1
                print(f"  modified: {fn}")
    print(f"\nfiles {'that would be ' if args.dry_run else ''}modified: {files}")
    for k, v in stats.most_common():
        print(f"  {v:5d}  {k}")


if __name__ == "__main__":
    main()
