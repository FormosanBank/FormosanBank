"""Re-apply recorded manual edits to a corpus's XML, first in the cleaning
pipeline. Applies upsert/insert/delete from CodeAndDocs/manual_edits.xml,
prunes entries that are no-ops against the current (pre-manual) XML O (with
a console warning), and regenerates CodeAndDocs/manual_edits.md.

See claudeplans/2026-06-15-manual-edits-reproducibility-design.md.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lxml import etree

from QC.cleaning import manual_edits_common as mec


def _s_map(root):
    return {s.get("id"): s for s in root.findall(".//S") if s.get("id")}


def _apply_file(xml_path, file_group, changelog, pruned):
    """Apply one FILE group's operations to xml_path. Returns True if the XML
    file was modified. Appends changelog entries and pruned (rel,id) tuples."""
    rel = file_group.get("path")
    tree = etree.parse(str(xml_path))
    text_root = tree.getroot()
    o_map = _s_map(text_root)
    modified = False

    for record in list(file_group.findall("S")):
        sid = record.get("id")
        if record.get("action") == "delete":
            if sid not in o_map:
                pruned.append((rel, sid)); mec.remove_record(file_group, sid); continue
            target = o_map.pop(sid)
            before = mec.render_s(target)
            target.getparent().remove(target)
            changelog.append({"file": rel, "sid": sid, "action": "deleted",
                              "before": before, "after": None})
            modified = True
            continue

        if sid in o_map:
            if mec.canonical_s(record) == mec.canonical_s(o_map[sid]):
                pruned.append((rel, sid)); mec.remove_record(file_group, sid); continue
            before = mec.render_s(o_map[sid])
            new_el = mec.strip_s(record)  # strip after/action for the live tree
            o_map[sid].getparent().replace(o_map[sid], new_el)
            o_map[sid] = new_el
            changelog.append({"file": rel, "sid": sid, "action": "changed",
                              "before": before, "after": mec.render_s(new_el)})
            modified = True
        else:
            after = record.get("after")
            new_el = mec.strip_s(record)
            anchor = o_map.get(after) if after else None
            if anchor is not None:
                anchor.addnext(new_el)
            else:
                text_root.append(new_el)
            o_map[sid] = new_el
            changelog.append({"file": rel, "sid": sid, "action": "added",
                              "before": None, "after": mec.render_s(new_el)})
            modified = True

    if modified:
        etree.indent(tree, space="    ")
        tree.write(str(xml_path), xml_declaration=True, pretty_print=True, encoding="utf-8")
    return modified


def apply(corpora_path, manual_file) -> int:
    corpora_path = Path(corpora_path).resolve()
    root = mec.load_manual(manual_file)
    if root is None:
        print(f"no manual-edits file found at {manual_file}; nothing to do")
        return 0

    changelog: list[dict] = []
    pruned: list[tuple] = []
    applied_files = 0

    for fg in root.findall("FILE"):
        rel = fg.get("path")
        xml_path = corpora_path / rel
        if not xml_path.exists():
            print(f"WARNING: {rel} not found under {corpora_path}; skipping its manual edits.")
            continue
        if _apply_file(xml_path, fg, changelog, pruned):
            applied_files += 1

    for rel, sid in pruned:
        print(f"WARNING: pruned no-op manual edit: {rel} / {sid}")

    if pruned:
        mec.write_manual(root, manual_file)

    mec.write_changelog(changelog, mec.changelog_path(manual_file))

    print(f"apply: {len(changelog)} edit(s) across {applied_files} file(s); "
          f"{len(pruned)} no-op(s) pruned.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Apply manual_edits.xml to corpus XML")
    parser.add_argument("--corpora_path", required=True, help="the corpus XML root")
    parser.add_argument("--manual_file", default=None,
                        help="manual edits file (default <corpus-root>/CodeAndDocs/manual_edits.xml)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    if not Path(args.corpora_path).exists():
        parser.error(f"--corpora_path does not exist: {args.corpora_path}")
    manual_file = args.manual_file or mec.default_manual_file(args.corpora_path)
    return apply(args.corpora_path, manual_file)


if __name__ == "__main__":
    raise SystemExit(main())
