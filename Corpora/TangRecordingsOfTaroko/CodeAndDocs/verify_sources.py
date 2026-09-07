#!/usr/bin/env python3
"""Verify the committed source manifest against metadata and pinned HF state."""

from __future__ import annotations

import argparse
import json
import subprocess

from make_xml import load_manifest, load_metadata, validate_manifest


def live_inventory(manifest: dict[str, object]) -> list[dict[str, object]]:
    source = manifest["source"]
    url = (
        f"https://huggingface.co/api/datasets/{source['repo_id']}/tree/"
        f"{source['revision']}?recursive=true&expand=true"
    )
    result = subprocess.run(
        ["curl", "--location", "--fail", "--silent", "--show-error", url],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def verify_live(manifest: dict[str, object]) -> None:
    expected = {
        entry["hf_path"]: (entry["source_bytes"], entry["source_sha256"])
        for entry in manifest["files"]
    }
    actual = {
        row["path"]: (row["size"], row.get("lfs", {}).get("oid"))
        for row in live_inventory(manifest)
        if row.get("type") == "file" and str(row.get("path", "")).endswith(".wav")
    }
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        changed = sorted(
            path for path in set(actual) & set(expected) if actual[path] != expected[path]
        )
        raise SystemExit(
            f"pinned Hugging Face inventory drift: missing={missing}, "
            f"extra={extra}, changed={changed}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    manifest = load_manifest()
    metadata = load_metadata()
    validate_manifest(manifest, metadata)
    missing_prepared = [
        entry["file"]
        for entry in manifest["files"]
        if not all(
            entry.get(key)
            for key in ("prepared_bytes", "prepared_sha256", "prepared_frames")
        )
    ]
    if missing_prepared:
        raise SystemExit(f"prepared identities are not pinned: {missing_prepared}")
    if args.live:
        verify_live(manifest)
    print(
        f"Verified {len(manifest['files'])} source and prepared audio identities "
        f"across {len(metadata)} PARADISEC items."
    )


if __name__ == "__main__":
    main()
