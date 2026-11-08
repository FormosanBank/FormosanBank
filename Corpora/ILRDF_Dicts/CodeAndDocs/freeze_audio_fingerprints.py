#!/usr/bin/env python3
"""One-off: freeze the audio fingerprints the build reads into
source_data/audio_fingerprints.tsv.

Not part of reproduction (generate_xml.sh never runs it, and the build never
downloads anything): it converts three working tables, produced where the
ILRDF and Hugging Face hosts are reachable, into the one committed table the
build reads.

    python CodeAndDocs/freeze_audio_fingerprints.py \
        --fingerprints claudeplans/ilrdf-2026-audio-fingerprints.tsv \
        --audio-list   claudeplans/ilrdf-2026-audio-list.tsv \
        --hf-hashes    claudeplans/ilrdf-hf-main-hashes.tsv

Inputs:
  fingerprints  language, file, url, status, bytes, sha256, type -- one row per
                download attempt of a 2026 recording; the LAST row per file
                wins. `type` is the real file type read from the first bytes
                (mp3, webm, mp4, wav, all-zero, unknown:<first 8 bytes>), or
                "same size as <main file> (not downloaded; sha256 is main's)".
  audio-list    language, file, url, main_file, main_size, main_sha256 -- the
                download list; checked against the "same size" rows.
  hf-hashes     path, size, sha256 -- every file in the ILRDF_Dicts Hugging
                Face dataset at the revision pinned in audio_sources.json.

Output columns:
  kind       2026 (a recording in the 2026 source) or main (a file on HF)
  language
  key        2026: the recording's URL; main: its path in the HF dataset
  file       2026: the name it was downloaded under (CodeAndDocs uses it to
             find the local copy); main: the HF file name
  bytes, sha256
  type       2026: mp3 | webm | mp4 | wav | all-zero |
             unknown:0000000000000000 | unreachable (download failed) |
             same-as-main (same size as main_file; not downloaded, sha256 is
             main_file's); main: empty (main's files were not typed)
  main_file  2026 same-as-main rows only
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import re

OUT = Path(__file__).resolve().parent / "source_data" / "audio_fingerprints.tsv"
FIELDS = ["kind", "language", "key", "file", "bytes", "sha256", "type", "main_file"]
_SAME = re.compile(r"^same size as (\S+) \(not downloaded; sha256 is main's\)$")
_TYPES = {"mp3", "webm", "mp4", "wav", "all-zero", "unknown:0000000000000000"}


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def freeze(fingerprints: Path, audio_list: Path, hf_hashes: Path) -> list[dict[str, str]]:
    listed = {row["file"]: row for row in _read(audio_list)}
    last: dict[str, dict[str, str]] = {}
    for row in _read(fingerprints):
        last[row["file"]] = row
    if set(last) != set(listed):
        raise ValueError("fingerprint table and audio list cover different files")
    out: list[dict[str, str]] = []
    for name in sorted(last):
        row = last[name]
        if "sys-dictionary.ilrdf.org.tw" not in row["url"]:
            continue        # main's own files: the HF listing below covers them
        record = {"kind": "2026", "language": row["language"], "key": row["url"],
                  "file": name, "bytes": row["bytes"], "sha256": row["sha256"],
                  "type": row["type"], "main_file": ""}
        if row["status"] != "ok":
            if not row["status"].startswith("failed"):
                raise ValueError(f"{name}: unexpected status {row['status']!r}")
            record.update(type="unreachable", bytes="", sha256="")
        else:
            same = _SAME.match(row["type"])
            if same:
                expected = listed[name]
                if (expected["main_file"] != same.group(1)
                        or expected["main_sha256"] != row["sha256"]
                        or expected["main_size"] != row["bytes"]):
                    raise ValueError(f"{name}: same-size row disagrees with the audio list")
                record.update(type="same-as-main", main_file=same.group(1))
            elif row["type"] not in _TYPES:
                raise ValueError(f"{name}: unexpected type {row['type']!r}")
        out.append(record)
    if len({r["key"] for r in out}) != len(out):
        raise ValueError("a URL appears twice")
    for row in _read(hf_hashes):
        path = row["path"]
        if "/" not in path:
            continue        # .gitattributes, README.md ...
        if not row["sha256"]:
            raise ValueError(f"{path}: no sha256")
        out.append({"kind": "main", "language": path.split("/", 1)[0], "key": path,
                    "file": path.rsplit("/", 1)[1], "bytes": row["size"],
                    "sha256": row["sha256"], "type": "", "main_file": ""})
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fingerprints", type=Path, required=True)
    parser.add_argument("--audio-list", type=Path, required=True)
    parser.add_argument("--hf-hashes", type=Path, required=True)
    args = parser.parse_args()
    rows = freeze(args.fingerprints, args.audio_list, args.hf_hashes)
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    counts: dict[str, int] = {}
    for row in rows:
        key = f"{row['kind']}:{row['type'] or '-'}"
        counts[key] = counts.get(key, 0) + 1
    print(f"wrote {OUT} ({len(rows)} rows): {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
