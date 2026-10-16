#!/usr/bin/env python3
"""Verify the pinned NTU JSON source snapshot used by the build."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SOURCE_DIRS = ("grammar", "sentence", "story")
MANIFEST_PATH = Path("source_snapshot.json")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def record_count(path: Path) -> int:
    payload = json.loads(path.read_text(encoding="utf-8"))
    glosses = payload.get("glosses") if isinstance(payload, dict) else None
    if not isinstance(glosses, list):
        raise ValueError("top-level 'glosses' is not a list")
    return len(glosses)


def local_json_paths(repo_root: Path) -> list[str]:
    paths: list[str] = []
    for directory in SOURCE_DIRS:
        paths.extend(
            path.relative_to(repo_root).as_posix()
            for path in (repo_root / directory).rglob("*.json")
        )
    return sorted(paths)


def verify(repo_root: Path) -> None:
    manifest_file = repo_root / MANIFEST_PATH
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    entries = manifest.get("files")
    if manifest.get("schema_version") != 1 or not isinstance(entries, list):
        raise SystemExit(f"invalid source snapshot manifest: {manifest_file}")

    expected_paths = [entry.get("path") for entry in entries]
    if expected_paths != sorted(expected_paths) or len(expected_paths) != len(set(expected_paths)):
        raise SystemExit("source snapshot paths must be unique and sorted")

    actual_paths = local_json_paths(repo_root)
    if expected_paths != actual_paths:
        missing = sorted(set(expected_paths) - set(actual_paths))
        extra = sorted(set(actual_paths) - set(expected_paths))
        raise SystemExit(
            "source snapshot inventory mismatch: "
            f"missing={missing[:10]} extra={extra[:10]}"
        )

    failures: list[str] = []
    statuses: dict[str, int] = {}
    records = 0
    for entry in entries:
        relative = entry["path"]
        status = entry.get("status")
        statuses[status] = statuses.get(status, 0) + 1
        path = repo_root / relative
        actual_digest = sha256(path)
        if actual_digest != entry.get("sha256"):
            failures.append(f"{relative}: sha256 {actual_digest}")
            continue
        try:
            actual_records = record_count(path)
        except (json.JSONDecodeError, OSError, ValueError) as error:
            failures.append(f"{relative}: {error}")
            continue
        if actual_records != entry.get("records"):
            failures.append(
                f"{relative}: records {actual_records} != {entry.get('records')}"
            )
        records += actual_records

    if failures:
        details = "\n".join(f"  {failure}" for failure in failures[:20])
        raise SystemExit(f"source snapshot verification failed:\n{details}")

    status_summary = ", ".join(f"{key}={value}" for key, value in sorted(statuses.items()))
    print(
        f"verified {len(entries)} pinned JSON files ({records} records; "
        f"{status_summary})"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="directory containing the pinned JSON source folders",
    )
    args = parser.parse_args()
    verify(args.repo_root.resolve())


if __name__ == "__main__":
    main()
