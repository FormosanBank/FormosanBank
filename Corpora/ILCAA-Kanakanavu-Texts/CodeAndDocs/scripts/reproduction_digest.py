#!/usr/bin/env python3
"""Print a path-independent digest of the generated corpus state."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = [
    ROOT / "README.md",
    ROOT / "data/processed/manifest.csv",
    ROOT / "data/processed/source_unit_coverage.csv",
    ROOT / "data/processed/source_notation_audit.csv",
    ROOT / "data/processed/qc_finding_review.csv",
    ROOT / "data/processed/validation_report.md",
    ROOT / "data/processed/source_xml_comparison_report.md",
]


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    xml_outputs = sorted((ROOT / "XML/xnb").glob("*.xml"))
    outputs = [*OUTPUTS, *xml_outputs]
    missing = [path for path in OUTPUTS if not path.is_file()]
    if len(xml_outputs) != 45:
        raise SystemExit(f"Expected 45 XML files, found {len(xml_outputs)}")
    if missing:
        raise SystemExit(
            "Missing generated output: "
            + ", ".join(str(path.relative_to(ROOT)) for path in missing)
        )
    digest = hashlib.sha256()
    for path in outputs:
        relative = path.relative_to(ROOT).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_digest(path).encode("ascii"))
        digest.update(b"\n")
    print(digest.hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
