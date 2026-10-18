#!/usr/bin/env python3
"""List the audio files the published XML needs that Hugging Face lacks.

Uploads nothing and needs no network: what Hugging Face holds comes from the
frozen listing in source_data/audio_fingerprints.tsv (kind=main: every file
in the dataset at the revision pinned in the repo-root audio_sources.json,
with its SHA-256), and what each referenced file must contain comes from the
same table (kind=2026: the SHA-256 and real type of every 2026 recording).

    python CodeAndDocs/audio_upload_manifest.py [--local-root /workspace/ILRDF_audio_2026]

For every AUDIO/@file in XML/<Lang>/<Lang>.xml -- in an S or directly under
TEXT (untranscribed) -- at the path validate_hf_audio.py expects
(<Lang>/<Lang>/<file>; for the languages listed in audio_sources.json's
sharded_languages, <Lang>/<Lang>/<shard>/<file>, shard from
validate_hf_audio.name_shard, because Hugging Face allows at most 10,000
files per folder), a file must be put there when that path is not on
Hugging Face with the same bytes. If the frozen listing has the same file
name with the same bytes at another path (the layout before sharding), the
reason is "same bytes at the old path" and hf_old_path says where: a
server-side copy on Hugging Face, no upload. Otherwise the file must be
uploaded: "new name", or "new content under an existing name" when the
file name is on Hugging Face with different bytes. Each such file goes
to docs/audio_upload_manifest.csv with the URL it can be fetched from and,
when the download run kept it, its local copy under
<local-root>/<Lang>/ (the name it was downloaded under; WebM files were kept
as <stem>.webm). The local column depends on the machine it is run on, so
this script is not part of generate_xml.sh.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from audio_recordings import AudioTable
from ilrdf_source import LANGUAGES

BASE = Path(__file__).resolve().parent
XML_DIR = BASE.parent / "XML"
REPO = BASE.parents[2]
sys.path.insert(0, str(REPO))
from QC.validation.validate_hf_audio import name_shard  # noqa: E402
OUT = BASE / "docs" / "audio_upload_manifest.csv"
FIELDS = ["language", "file", "hf_path", "reason", "url", "type", "bytes", "sha256",
          "local_path", "local_present", "placement", "s_id", "hf_old_path"]


def dataset_config() -> dict:
    manifest = json.loads((REPO / "audio_sources.json").read_text(encoding="utf-8"))
    return next(d for d in manifest["datasets"] if d["corpus"] == "ILRDF_Dicts")


def sharded_languages() -> set[str]:
    config = dataset_config()
    if "sharded_languages" not in config:
        raise SystemExit("audio_sources.json: ILRDF_Dicts has no sharded_languages; "
                         "this script needs the sharded Hugging Face layout")
    return set(config["sharded_languages"])


def hf_path(language: str, filename: str, sharded: set[str]) -> str:
    if language in sharded:
        return f"{language}/{language}/{name_shard(filename)}/{filename}"
    return f"{language}/{language}/{filename}"


def _local(local_root: Path, language: str, downloaded_as: str) -> tuple[str, str]:
    candidates = [local_root / language / downloaded_as,
                  local_root / language / (Path(downloaded_as).stem + ".webm")]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate), "yes"
    return str(candidates[0]), "no"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--local-root", type=Path, default=Path("/workspace/ILRDF_audio_2026"))
    args = parser.parse_args()
    table = AudioTable()
    on_hf = {fp.key: fp for fp in table.main.values()}
    sharded = sharded_languages()

    wanted: dict[str, dict] = {}
    problems: list[str] = []
    for language in LANGUAGES:
        root = ET.parse(XML_DIR / language / f"{language}.xml").getroot()
        placed = [(a, "untranscribed", "") for a in root.findall("AUDIO")]
        placed += [(a, "in S", s.get("id")) for s in root.findall("S") for a in s.findall("AUDIO")]
        for audio, placement, s_id in placed:
            name, url = audio.get("file"), audio.get("url", "")
            path = hf_path(language, name, sharded)
            fp = table.by_url.get(url)
            if fp is not None:
                sha, kind, size, downloaded_as = fp.sha256, fp.type, fp.bytes, fp.file
            else:
                main = table.main_file(language, name)
                if main is None:
                    problems.append(f"{path}: main's file, not on Hugging Face")
                    continue
                sha, kind, size, downloaded_as = main.sha256, "", main.bytes, ""
            entry = {"language": language, "file": name, "hf_path": path, "url": url,
                     "type": kind, "bytes": size, "sha256": sha, "placement": placement,
                     "s_id": s_id, "downloaded_as": downloaded_as}
            previous = wanted.get(path)
            if previous is not None and previous["sha256"] != sha:
                problems.append(f"{path}: referenced with two different contents")
            wanted.setdefault(path, entry)

    rows = []
    for path in sorted(wanted):
        entry = wanted[path]
        present = on_hf.get(path)
        if present is not None and present.sha256 == entry["sha256"]:
            continue
        old = table.main_file(entry["language"], entry["file"])
        hf_old_path = ""
        if old is not None and old.sha256 == entry["sha256"]:
            reason, hf_old_path = "same bytes at the old path", old.key
        elif present is None and old is None:
            reason = "new name"
        else:
            reason = "new content under an existing name"
        local_path, local_present = ("", "")
        if entry["downloaded_as"] and not hf_old_path:   # a copy on HF needs no local file
            local_path, local_present = _local(args.local_root, entry["language"],
                                               entry["downloaded_as"])
            if local_present == "yes" and str(os.path.getsize(local_path)) != entry["bytes"]:
                local_present = "size differs"
        rows.append({**{k: entry[k] for k in FIELDS if k in entry},
                     "reason": reason, "local_path": local_path,
                     "local_present": local_present, "hf_old_path": hf_old_path})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    def tally(key: str) -> dict:
        out: dict[str, int] = {}
        for row in rows:
            out[row[key]] = out.get(row[key], 0) + 1
        return dict(sorted(out.items()))
    print(f"referenced files: {len(wanted)}; already on Hugging Face at their path with "
          f"the same bytes: {len(wanted) - len(rows)}; to put in place: {len(rows)} "
          f"({sum(int(r['bytes']) for r in rows):,} bytes)")
    print("to put in place, by reason:", json.dumps(tally("reason")))
    print("to put in place, by type:", json.dumps(tally("type")))
    print("to put in place, by language:", json.dumps(tally("language")))
    print("local copy present:", json.dumps(tally("local_present")))
    for problem in problems:
        print(f"  PROBLEM: {problem}")
    print(f"wrote {OUT}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
