#!/usr/bin/env python3
"""Add dialect="unknown" to every TEXT that lacks a dialect attribute.

Maintainer ruling (2026-08-11, POL-038 committed-script requirement): a
TEXT missing dialect metadata gets ``dialect="unknown"`` unless the article
unambiguously identifies its own dialect. No Wikipedias article does —
these are community-written encyclopedia pages with no dialect statement,
and Wikipedia authorship mixes dialect backgrounds — so the whole corpus
(all five language Wikipedias) gets ``unknown``. In the pre-fix published
corpus NO TEXT carried a dialect attribute (13,278 files; V036 baseline).

Note for trv: ``dialect="unknown"`` keeps the Seediq Wikipedia counted as
Seediq under the corpus counting rules (trv counts as Truku only with an
explicit ``dialect="Truku"``) — consistent with how this corpus has always
been counted. Whether the trv Wikipedia should instead be labeled Truku is
a maintainer call, flagged in the Phase B sweep report.

Edits are byte-minimal: ``dialect="unknown"`` is inserted into the ``<TEXT``
open tag immediately after the ``xml:lang`` attribute; nothing is
re-serialized. Idempotent: TEXTs that already have any dialect attribute
are left untouched.
"""

import argparse
import re
import sys
from pathlib import Path

TEXT_TAG_RE = re.compile(r"<TEXT\b[^>]*>", re.DOTALL)
LANG_ATTR_RE = re.compile(r'(xml:lang="[^"]*")')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpora_path", type=Path,
                    default=Path(__file__).resolve().parent.parent / "XML",
                    help="Wikipedias XML root (default: sibling XML/)")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change without writing")
    args = ap.parse_args()

    changed = 0
    for f in sorted(args.corpora_path.rglob("*.xml")):
        raw = f.read_text(encoding="utf-8")
        m = TEXT_TAG_RE.search(raw)
        if not m:
            sys.exit(f"no TEXT open tag in {f}")
        tag = m.group(0)
        if "dialect=" in tag:
            continue
        if not LANG_ATTR_RE.search(tag):
            sys.exit(f"TEXT in {f} has no xml:lang to anchor the insert")
        new_tag = LANG_ATTR_RE.sub(r'\1 dialect="unknown"', tag, count=1)
        if not args.dry_run:
            f.write_text(raw[:m.start()] + new_tag + raw[m.end():],
                         encoding="utf-8")
        changed += 1

    verb = "would add" if args.dry_run else "added"
    print(f'{verb} dialect="unknown" to {changed} TEXTs')


if __name__ == "__main__":
    main()
