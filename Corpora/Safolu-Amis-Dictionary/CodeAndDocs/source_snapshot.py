"""Read or refresh the immutable Moedict example-field snapshot."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
from pathlib import Path

from moedict_formosanbank import iter_moedict_json_files

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / "source_examples.jsonl.gz"
MANIFEST = HERE / "source_manifest.json"


def load_rows(path: Path = SNAPSHOT) -> list[dict]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != manifest["snapshot_sha256"]:
        raise ValueError("Source snapshot differs from source_manifest.json")
    rows = [json.loads(line) for line in gzip.decompress(data).decode("utf-8").splitlines()]
    if [row["source_ordinal"] for row in rows] != list(range(1, manifest["example_fields"] + 1)):
        raise ValueError("Source ordinal coverage differs from the pinned input")
    return rows


def capture(checkout: Path) -> None:
    """Run explicitly when refreshing source, never during XML generation."""
    commit = subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
    ).strip()
    if subprocess.check_output(["git", "-C", str(checkout), "status", "--porcelain"]):
        raise ValueError("Source checkout has local changes")
    rows = []
    files = list(iter_moedict_json_files(checkout / "docs" / "s"))
    if not files:
        raise ValueError("Source checkout has no docs/s dictionary files")
    definitions = 0
    for source_file in files:
        entry = json.loads(source_file.read_text(encoding="utf-8"))
        for h_index, heteronym in enumerate(entry.get("h", []), 1):
            for d_index, definition in enumerate(heteronym.get("d", []), 1):
                definitions += 1
                for e_index, example in enumerate(definition.get("e", []), 1):
                    rows.append({
                        "source_ordinal": len(rows) + 1,
                        "source_file": "docs/s/" + source_file.name,
                        "entry_title": entry.get("t", ""),
                        "heteronym_index": h_index,
                        "definition_index": d_index,
                        "example_index": e_index,
                        "definition": definition.get("f", ""),
                        "raw_example": example,
                    })
    if not rows:
        raise ValueError("Source checkout has no example fields")
    if SNAPSHOT.exists():
        fields = ("source_file", "heteronym_index", "definition_index", "example_index")
        previous = [tuple(row[field] for field in fields) for row in load_rows()]
        current = [tuple(row[field] for field in fields) for row in rows]
        if previous != current:
            raise ValueError("Source field inventory changed; reconcile published IDs before refreshing")
    data = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows)
    compressed = gzip.compress(data.encode("utf-8"), mtime=0)
    SNAPSHOT.write_bytes(compressed)
    manifest = {
        "source": "https://github.com/g0v/amis-moedict",
        "source_commit": commit,
        "source_path": "docs/s",
        "lexical_files": len(files),
        "definitions": definitions,
        "example_fields": len(rows),
        "snapshot_sha256": hashlib.sha256(compressed).hexdigest(),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path, help="Clean g0v/amis-moedict checkout to snapshot")
    capture(parser.parse_args().checkout.resolve())
