#!/usr/bin/env python3
"""Deterministically re-id duplicated S ids in Virginia_Fey_Dictionary XML.

Background (maintainer ruling, 2026-08-11 sweep): the hand-cleaned XML
carries two *distinct* dictionary entries under the single sentence id
``S3797`` ("kananaman a demak" vs "namanan a demak"). Duplicate S ids break
the schema's uniqueness guarantee (validate_xml HARD finding) and orphan any
id-keyed tooling (manual_edits records, external citations).

Fix scheme — **letter suffix** (``S3797`` → ``S3797b`` for the second
occurrence in document order; ``c``, ``d``, … if a triplicate ever appears):

* every pre-existing id in this corpus matches ``^S[0-9]+$``, so a
  letter-suffixed id can never collide with any published id (the script
  additionally verifies non-collision against the file's full id set);
* the alternative — next-free integer — was rejected because the integer ids
  derive from the upstream amis-data row numbering, where absent integers are
  meaningful gaps; claiming one would silently fabricate a source row, and
  the resulting id would be indistinguishable from a genuine source-numbered
  entry. The suffix makes the administrative re-id self-evident.

This is a deliberate, announced POL-037 stable-id change (exactly one id
affected: the second ``S3797``). Per POL-038, the POL-035 pre-correction
snapshot is fixed ONLY by running this script against it — never by hand:

    python fix_duplicate_ids.py --path CodeAndDocs/pre_correction_snapshot

The published pipeline (``make_xml.sh``) also runs it over ``XML/`` as its
first step; because the snapshot the pipeline restores from already carries
the fix, that run is an idempotent no-op guard. The edit is textual and
touches only the ``id`` attribute of the duplicated ``<S>`` opening tags —
no reserialization, so every other byte of the file is untouched.
"""

import argparse
import os
import re
import sys
from collections import Counter

from lxml import etree

_ID_RE = re.compile(r"^S[0-9]+$")


def _suffix(n):
    """1st extra occurrence -> 'b', 2nd -> 'c', ..."""
    return chr(ord("b") + n - 1)


def fix_file(path):
    """Re-id 2nd+ occurrences of duplicated S ids in ``path``.

    Returns list of (old_id, new_id) changes (empty if file already clean).
    """
    tree = etree.parse(path)
    ids = [s.get("id") for s in tree.iter("S")]
    counts = Counter(ids)
    dups = {i: c for i, c in counts.items() if c > 1}
    if not dups:
        return []

    id_set = set(ids)
    changes = []  # (old_id, occurrence_index_in_document_order, new_id)
    for dup_id, count in sorted(dups.items()):
        if not _ID_RE.match(dup_id):
            sys.exit(
                f"ERROR: duplicated id {dup_id!r} in {path} does not match "
                f"^S[0-9]+$ — the letter-suffix scheme's no-collision argument "
                f"does not hold; refusing to guess."
            )
        for occ in range(2, count + 1):
            new_id = dup_id + _suffix(occ - 1)
            if new_id in id_set:
                sys.exit(
                    f"ERROR: replacement id {new_id!r} already exists in "
                    f"{path}; refusing to collide (POL-037)."
                )
            id_set.add(new_id)
            changes.append((dup_id, occ, new_id))

    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()

    # Textual, targeted edit: replace the Nth occurrence of the exact <S
    # opening tag attribute id="X" for each duplicate beyond the first.
    for old_id, occurrence, new_id in changes:
        pattern = re.compile(r'(<S\b[^>]*\bid=")' + re.escape(old_id) + r'(")')
        seen = 0
        out, last = [], 0
        replaced = False
        for m in pattern.finditer(text):
            seen += 1
            if seen == occurrence:
                out.append(text[last : m.start()])
                out.append(m.group(1) + new_id + m.group(2))
                last = m.end()
                replaced = True
                break
        if not replaced:
            sys.exit(
                f"ERROR: could not locate occurrence {occurrence} of "
                f'id="{old_id}" textually in {path}.'
            )
        out.append(text[last:])
        text = "".join(out)

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)

    # Post-verify: reparse; all S ids unique; only ids changed.
    new_tree = etree.parse(path)
    new_ids = [s.get("id") for s in new_tree.iter("S")]
    if len(new_ids) != len(set(new_ids)):
        sys.exit(f"ERROR: {path} still has duplicate S ids after fix.")
    if len(new_ids) != len(ids):
        sys.exit(f"ERROR: S count changed in {path} — aborting.")
    return [(old, new) for old, _, new in changes]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--path",
        required=True,
        help="XML file, or directory to scan recursively for .xml files "
        "(e.g. XML/ or CodeAndDocs/pre_correction_snapshot/)",
    )
    args = ap.parse_args()

    targets = []
    if os.path.isfile(args.path):
        targets = [args.path]
    else:
        for root, _dirs, files in os.walk(args.path):
            targets.extend(
                os.path.join(root, f) for f in sorted(files) if f.endswith(".xml")
            )
    if not targets:
        sys.exit(f"ERROR: no XML files under {args.path}")

    total = 0
    for path in targets:
        for old_id, new_id in fix_file(path):
            print(f"{path}: {old_id} (2nd+ occurrence) -> {new_id}")
            total += 1
    if total == 0:
        print("No duplicate S ids found — nothing to do (idempotent no-op).")


if __name__ == "__main__":
    main()
