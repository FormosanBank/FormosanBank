#!/usr/bin/env python3
"""Verify the published source audio against CodeAndDocs/audio_manifest.json.

Three checks. None of them downloads audio:

    verify_sources.py           the manifest agrees with the Paradisec metadata
                                committed in Metadata/, and with the revision
                                the downloader actually uses
    verify_sources.py --live    it agrees with the pinned Hugging Face revision.
                                Hugging Face stores each LFS object under its
                                SHA-256, so this checks 13.6 GB of audio in one
                                API call without transferring any of it
    verify_sources.py --local   the WAVs already in Audio/Truku are the files
                                the manifest names (hashes what is on disk)

This is verification, not build. `generate_xml.sh` does not run it, and the
corpus reproduces from the committed metadata without it (POL-047: build only).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from make_xml import CORPUS_ROOT, item_recordings, load_metadata

MANIFEST = Path(__file__).resolve().parent / "audio_manifest.json"
AUDIO_DIR = CORPUS_ROOT / "Audio" / "Truku"
FORMOSANBANK_ROOT = Path(os.environ.get("FORMOSANBANK_ROOT", CORPUS_ROOT.parent.parent))
AUDIO_SOURCES = FORMOSANBANK_ROOT / "audio_sources.json"
CORPUS = "TangRecordingsOfTaroko"


def load_manifest(path: Path = MANIFEST) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and not set(value) - set("0123456789abcdef")


def validate_manifest(manifest: dict, metadata: dict) -> None:
    """The manifest describes exactly the recordings the metadata enumerates."""
    if manifest.get("schema_version") != 1:
        raise ValueError("audio manifest schema_version must be 1")

    revision = manifest.get("source", {}).get("revision", "")
    if len(revision) != 40 or set(revision) - set("0123456789abcdef"):
        raise ValueError(f"pinned revision is not a full commit: {revision!r}")

    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("audio manifest lists no files")

    names = [entry.get("file") for entry in entries]
    if len(names) != len(set(names)) or any(
        not isinstance(name, str) or Path(name).name != name for name in names
    ):
        raise ValueError("audio manifest filenames must be unique basenames")

    covered: dict[str, set[str]] = {}
    for entry in entries:
        name = entry["file"]
        item_id = entry.get("paradisec_item")
        if item_id not in metadata:
            raise ValueError(f"unknown Paradisec item for {name}: {item_id}")
        item = metadata[item_id]
        if entry.get("source_url") != item.get("@id"):
            raise ValueError(f"source URL drift for {name}")
        if entry.get("hf_path") != f"Truku/{name}":
            raise ValueError(f"unexpected Hugging Face path for {name}")
        if name not in item_recordings(item):
            raise ValueError(f"metadata does not enumerate {name}")
        if not isinstance(entry.get("bytes"), int) or entry["bytes"] <= 0:
            raise ValueError(f"missing or invalid byte size for {name}")
        if not _is_sha256(entry.get("sha256")):
            raise ValueError(f"missing or malformed SHA-256 for {name}")
        covered.setdefault(item_id, set()).add(name)

    if set(covered) != set(metadata):
        raise ValueError("manifest and committed metadata describe different items")
    for item_id, item in metadata.items():
        missing = set(item_recordings(item)) - covered[item_id]
        if missing:
            raise ValueError(f"{item_id} is missing from the manifest: {sorted(missing)}")


def validate_pin(manifest: dict, path: Path = AUDIO_SOURCES) -> None:
    """The manifest pins the same revision the downloader will fetch.

    Without this the two can drift apart silently, and `--live` would then be
    checking a revision nobody downloads.
    """
    contract = json.loads(path.read_text(encoding="utf-8"))
    datasets = [d for d in contract["datasets"] if d["corpus"] == CORPUS]
    if len(datasets) != 1:
        raise ValueError(f"expected one {CORPUS} dataset in {path.name}, found {len(datasets)}")
    dataset, source = datasets[0], manifest["source"]
    for key in ("repo_id", "revision"):
        if dataset[key] != source[key]:
            raise ValueError(
                f"{path.name} {key} is {dataset[key]!r}, manifest says {source[key]!r}"
            )
    if dataset["expected_audio_files"] != len(manifest["files"]):
        raise ValueError(
            f"{path.name} expects {dataset['expected_audio_files']} audio files, "
            f"manifest lists {len(manifest['files'])}"
        )


def live_inventory(manifest: dict) -> list[dict]:
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


def verify_live(manifest: dict) -> None:
    expected = {entry["hf_path"]: (entry["bytes"], entry["sha256"]) for entry in manifest["files"]}
    actual = {
        row["path"]: (row["size"], row.get("lfs", {}).get("oid"))
        for row in live_inventory(manifest)
        if row.get("type") == "file" and str(row.get("path", "")).endswith(".wav")
    }
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        changed = sorted(p for p in set(actual) & set(expected) if actual[p] != expected[p])
        raise SystemExit(
            "pinned Hugging Face audio has drifted: "
            f"missing={missing}, extra={extra}, changed={changed}"
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_local(manifest: dict, audio_dir: Path = AUDIO_DIR) -> None:
    missing, wrong = [], []
    for entry in manifest["files"]:
        path = audio_dir / entry["file"]
        if not path.is_file():
            missing.append(entry["file"])
        elif path.stat().st_size != entry["bytes"] or sha256_file(path) != entry["sha256"]:
            wrong.append(entry["file"])
    if missing or wrong:
        raise SystemExit(
            f"local audio does not match the manifest: missing={missing}, differing={wrong}. "
            "Move differing local copies aside, then run download_audio_data.sh and verify again."
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="also check the pinned Hugging Face revision")
    parser.add_argument("--local", action="store_true",
                        help="also hash the WAVs already downloaded to Audio/Truku")
    args = parser.parse_args(argv)

    manifest = load_manifest()
    metadata = load_metadata()
    validate_manifest(manifest, metadata)
    validate_pin(manifest)
    print(
        f"Manifest agrees with the committed metadata: {len(manifest['files'])} recordings "
        f"across {len(metadata)} Paradisec items, pinned at "
        f"{manifest['source']['revision'][:12]}."
    )
    if args.live:
        verify_live(manifest)
        print("Pinned Hugging Face audio matches the manifest, byte size and SHA-256.")
    if args.local:
        verify_local(manifest)
        print(f"Local audio in {AUDIO_DIR.name}/ matches the manifest.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
