#!/usr/bin/env python3
"""One-time import of reviewed published transcripts; never part of a build."""

import argparse
import csv
import hashlib
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_directory", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    manifest = root / "CodeAndDocs/video_manifest.tsv"
    with manifest.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames
        rows = list(reader)
    # Read all required inputs before replacing any file.
    sources = {
        row["source_path"]: (args.source_directory / Path(row["source_path"]).name).read_bytes()
        for row in rows if row["source_path"]
    }
    for row in rows:
        if not row["source_path"]:
            continue
        data = sources[row["source_path"]]
        destination = root / row["source_path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        row["source_sha256"] = hashlib.sha256(data).hexdigest()
        row["source_bytes"] = str(len(data))
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Imported {len(sources)} reviewed transcripts; inspect the source and manifest diff.")


if __name__ == "__main__":
    main()
