"""Shared XML target discovery for validators.

`CodeAndDocs/` holds reproduction infrastructure — scripts, raw scrapes,
and POL-035 pre-correction snapshots — never published corpus data.
Validating a snapshot copy as if it were corpus data produces false
findings (e.g. V081 sees every snapshotted TEXT id as a cross-corpus
collision with its published original), so discovery skips anything under
a CodeAndDocs directory *relative to the requested root*. Pointing a
validator explicitly at a path inside CodeAndDocs (or at a single file)
still works — the exclusion only applies to descendants found by the
walk.
"""
from pathlib import Path


def discover_xml_files(root: Path) -> list[Path]:
    """Every .xml under root, recursively, skipping CodeAndDocs/ subtrees."""
    root = Path(root)
    if root.is_file():
        return [root] if root.suffix == ".xml" else []
    return sorted(
        p for p in root.rglob("*.xml")
        if "CodeAndDocs" not in p.relative_to(root).parts
    )
