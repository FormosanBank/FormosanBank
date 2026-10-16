#!/usr/bin/env python3
"""List the audio files the published XML references that Hugging Face lacks.

Uploads nothing. Run deliberately (needs network access to huggingface.co),
never from generate_xml.sh:

    python CodeAndDocs/audio_upload_manifest.py

For every AUDIO/@file in XML/<Lang>/<Lang>.xml -- in an S (transcribed) or
directly under TEXT (untranscribed) -- it asks the dataset revision pinned in
the repo-root audio_sources.json whether the file exists at the path
validate_hf_audio.py expects (<Lang>/<Lang>/<file>; Rukai under batch_1/ or
batch_2/). Files that are missing go to docs/audio_upload_manifest.csv with
the URL they can be fetched from; it also reports main's (2024) files that
the XML references but Hugging Face does not have.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from huggingface_hub import HfApi

from ilrdf_source import LANGUAGES

BASE = Path(__file__).resolve().parent
XML_DIR = BASE.parent / "XML"
REPO = BASE.parents[2]
OUT = BASE / "docs" / "audio_upload_manifest.csv"
_MAIN_FILE = re.compile(r"^[A-Za-z]+_\d+\.mp3$")
CHUNK = 500


def dataset_config() -> dict:
    manifest = json.loads((REPO / "audio_sources.json").read_text(encoding="utf-8"))
    return next(d for d in manifest["datasets"] if d["corpus"] == "ILRDF_Dicts")


def hf_path(language: str, filename: str, batch_2: set[str]) -> str:
    if language == "Rukai":
        batch = "batch_2" if filename in batch_2 else "batch_1"
        return f"Rukai/Rukai/{batch}/{filename}"
    return f"{language}/{language}/{filename}"


def main() -> int:
    config = dataset_config()
    batch_2 = set(config.get("rukai_batch_2_files", []))
    wanted: dict[str, dict] = {}
    for language in LANGUAGES:
        root = ET.parse(XML_DIR / language / f"{language}.xml").getroot()
        for parent, placement in ((root, "untranscribed"),):
            for audio in parent.findall("AUDIO"):
                path = hf_path(language, audio.get("file"), batch_2)
                wanted.setdefault(path, {"language": language, "file": audio.get("file"),
                                         "hf_path": path, "url": audio.get("url", ""),
                                         "placement": placement, "s_id": ""})
        for sentence in root.findall("S"):
            for audio in sentence.findall("AUDIO"):
                path = hf_path(language, audio.get("file"), batch_2)
                wanted.setdefault(path, {"language": language, "file": audio.get("file"),
                                         "hf_path": path, "url": audio.get("url", ""),
                                         "placement": "in S", "s_id": sentence.get("id")})
    api = HfApi()
    present: set[str] = set()
    paths = sorted(wanted)
    for start in range(0, len(paths), CHUNK):
        found = api.get_paths_info(config["repo_id"], paths[start:start + CHUNK],
                                   repo_type="dataset", revision=config["revision"])
        present.update(item.path for item in found)
    missing = [wanted[p] for p in paths if p not in present]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, lineterminator="\n", fieldnames=[
            "language", "file", "hf_path", "url", "placement", "s_id"])
        writer.writeheader()
        writer.writerows(m for m in missing if not _MAIN_FILE.match(m["file"]))
    main_missing = [m for m in missing if _MAIN_FILE.match(m["file"])]
    print(f"referenced files: {len(paths)}; on HF at {config['revision']}: {len(present)}; "
          f"missing: {len(missing)}")
    print(f"wrote {OUT.name}: {len(missing) - len(main_missing)} files to upload")
    by_language: dict[str, int] = {}
    for m in missing:
        if not _MAIN_FILE.match(m["file"]):
            by_language[m["language"]] = by_language.get(m["language"], 0) + 1
    print("to upload, by language:", json.dumps(by_language))
    print(f"main (2024) files referenced but missing from HF: {len(main_missing)}")
    for m in main_missing[:50]:
        print(f"  {m['hf_path']}  ({m['placement']} {m['s_id']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
