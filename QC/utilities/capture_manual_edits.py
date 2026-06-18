"""Snapshot hand edits to a corpus's XML into CodeAndDocs/manual_edits.xml.

Dumb snapshotter: for each <S>, compare the working tree (W) against a git
baseline (B, default HEAD) on the strip() basis. B != W -> record strip(W);
present in B but absent in W -> record a delete; new id -> record with an
`after` placement hint. No O, no changelog, no pruning (apply does those).

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


def _s_order(root):
    return [s.get("id") for s in root.findall(".//S") if s.get("id")]


def capture(corpora_path, manual_file, baseline_ref) -> int:
    corpora_path = Path(corpora_path).resolve()
    repo = mec.git_root(corpora_path)
    if repo is None:
        print(f"ERROR: {corpora_path} is not inside a git work tree; "
              f"capture needs a '{baseline_ref}' baseline to diff against.",
              file=sys.stderr)
        return 2

    if not mec.git_ref_exists(repo, baseline_ref):
        print(f"ERROR: baseline ref '{baseline_ref}' does not resolve in the "
              f"git repo at {repo}.", file=sys.stderr)
        return 2

    root = mec.load_manual(manual_file) or mec.new_manual_root()
    dirty = False

    for xml_path in sorted(corpora_path.rglob("*.xml")):
        rel_corpora = xml_path.relative_to(corpora_path).as_posix()
        rel_repo = xml_path.relative_to(repo).as_posix()
        baseline_bytes = mec.git_show(repo, baseline_ref, rel_repo)
        if baseline_bytes is None:
            print(f"WARNING: {rel_corpora} is not present at {baseline_ref}; "
                  f"skipping (treated as new build output, not hand edits).")
            continue

        w_root = etree.parse(str(xml_path)).getroot()
        b_root = etree.fromstring(baseline_bytes)
        w_map, b_map = _s_map(w_root), _s_map(b_root)
        w_order = _s_order(w_root)

        for idx, sid in enumerate(w_order):
            w_s = w_map[sid]
            if sid in b_map:
                if mec.canonical_s(w_s) == mec.canonical_s(b_map[sid]):
                    continue  # B == W: leave untouched
                record = mec.strip_s(w_s)  # change
            else:
                record = mec.strip_s(w_s)  # new S
                if idx > 0:
                    record.set("after", w_order[idx - 1])
            fg = mec.get_or_create_file_group(root, rel_corpora)
            mec.upsert_record(fg, record)
            dirty = True

        for sid in b_map:
            if sid not in w_map:  # deletion
                fg = mec.get_or_create_file_group(root, rel_corpora)
                mec.upsert_record(fg, etree.Element("S", {"id": sid, "action": "delete"}))
                dirty = True

    if dirty:
        mec.write_manual(root, manual_file)
        print(f"capture: wrote {manual_file}")
    else:
        print("capture: no hand edits detected; manual file unchanged.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Snapshot hand edits into manual_edits.xml")
    parser.add_argument("--corpora_path", required=True, help="the corpus XML root")
    parser.add_argument("--manual_file", default=None,
                        help="manual edits file (default <corpus-root>/CodeAndDocs/manual_edits.xml)")
    parser.add_argument("--baseline-ref", dest="baseline_ref", default="HEAD",
                        help="git ref to diff against (default HEAD)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    if not Path(args.corpora_path).exists():
        parser.error(f"--corpora_path does not exist: {args.corpora_path}")
    manual_file = args.manual_file or mec.default_manual_file(args.corpora_path)
    return capture(args.corpora_path, manual_file, args.baseline_ref)


if __name__ == "__main__":
    raise SystemExit(main())
