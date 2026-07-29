#!/usr/bin/env python3
"""Validate the public XML audio contract against Hugging Face or local audio."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Iterable

AUDIO_SUFFIXES = {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".wav"}
REPO_ROOT = Path(__file__).resolve().parents[2]


def is_audio(path: str | Path) -> bool:
    return Path(path).suffix.lower() in AUDIO_SUFFIXES


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def load_contract(manifest_path: Path) -> tuple[dict, dict[str, set[str]]]:
    manifest = load_json(manifest_path)
    if manifest.get("schema_version") != 1:
        raise ValueError(f"unsupported manifest schema: {manifest.get('schema_version')}")
    datasets = manifest.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        raise ValueError("manifest datasets must be a non-empty list")
    repo_ids = [dataset.get("repo_id") for dataset in datasets]
    if len(repo_ids) != len(set(repo_ids)):
        raise ValueError("manifest repo_id values must be unique")
    for dataset in datasets:
        repo_id = dataset.get("repo_id")
        revision = dataset.get("revision", "")
        if not isinstance(repo_id, str) or "/" not in repo_id:
            raise ValueError(f"invalid dataset repo_id: {repo_id!r}")
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError(f"{repo_id}: revision must be a 40-character commit SHA")
        if not isinstance(dataset.get("expected_audio_files"), int):
            raise ValueError(f"{repo_id}: expected_audio_files must be an integer")
        batch_2 = dataset.get("rukai_batch_2_files", [])
        if not isinstance(batch_2, list) or not all(
            isinstance(path, str) and is_audio(path) for path in batch_2
        ):
            raise ValueError(f"{repo_id}: rukai_batch_2_files must be audio filenames")

    extras_path = REPO_ROOT / manifest["declared_extras"]
    extras_document = load_json(extras_path)
    if extras_document.get("schema_version") != 1:
        raise ValueError("unsupported declared-extras schema")
    repositories = extras_document.get("repositories", {})
    if not isinstance(repositories, dict):
        raise ValueError("declared-extras repositories must be an object")
    extras: dict[str, set[str]] = {}
    for repo_id, paths in repositories.items():
        if repo_id not in repo_ids:
            raise ValueError(f"declared extras use unmanifested repo {repo_id}")
        if not isinstance(paths, list) or not all(
            isinstance(path, str) and is_audio(path) for path in paths
        ):
            raise ValueError(f"{repo_id}: declared extras must be audio path strings")
        if len(paths) != len(set(paths)):
            raise ValueError(f"{repo_id}: declared extras contain duplicate paths")
        extras[repo_id] = set(paths)
    return manifest, extras


def xml_audio_elements(xml_root: Path) -> Iterable[tuple[Path, ET.Element, ET.Element]]:
    for xml_path in sorted(xml_root.rglob("*.xml")):
        root = ET.parse(xml_path).getroot()
        for audio in root.iter("AUDIO"):
            yield xml_path, root, audio


def expected_remote_paths(dataset: dict) -> set[str]:
    mode = dataset["path_mode"]
    if mode == "explicit":
        return set(dataset["files"])

    xml_root = REPO_ROOT / dataset["xml_root"]
    if mode == "ntu_paiwan_sources":
        result = set()
        for xml_path in sorted(xml_root.rglob("*.xml")):
            root = ET.parse(xml_path).getroot()
            filename = root.get("audio")
            if filename:
                parent = xml_path.relative_to(xml_root).parent
                result.add((parent / filename).as_posix())
        return result

    result: set[str] = set()
    rukai_batch_2 = set(dataset.get("rukai_batch_2_files", []))
    for xml_path, _, audio in xml_audio_elements(xml_root):
        filename = audio.get("file")
        if not filename:
            continue
        relative = xml_path.relative_to(xml_root)
        if mode == "root_file":
            path = Path(filename)
        elif mode == "language_file":
            path = Path(relative.parts[0]) / filename
        elif mode == "xml_stem":
            path = relative.parent / xml_path.stem / filename
        elif mode == "ilrdf":
            path = relative.parent / xml_path.stem
            if relative.parts[0] == "Rukai":
                batch = (
                    "batch_2"
                    if filename in rukai_batch_2
                    else "batch_1"
                )
                path /= batch
            path /= filename
        else:
            raise ValueError(f"unknown path_mode {mode!r}")
        result.add(path.as_posix())
    return result


def expected_local_paths(dataset: dict) -> set[str]:
    if dataset["path_mode"] != "ntu_paiwan_sources":
        return expected_remote_paths(dataset)

    xml_root = REPO_ROOT / dataset["xml_root"]
    result = expected_remote_paths(dataset)
    for xml_path, _, audio in xml_audio_elements(xml_root):
        filename = audio.get("file")
        if filename:
            parent = xml_path.relative_to(xml_root).parent
            result.add((parent / filename).as_posix())
    return result


def selected_datasets(manifest: dict, corpus: str | None) -> list[dict]:
    datasets = manifest["datasets"]
    if corpus is None:
        return datasets
    selected = [dataset for dataset in datasets if dataset["corpus"] == corpus]
    if not selected:
        raise ValueError(f"corpus {corpus!r} is not in the audio manifest")
    return selected


def grouped(datasets: list[dict]) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = defaultdict(list)
    for dataset in datasets:
        result[dataset.get("validation_group", dataset["repo_id"])].append(dataset)
    return result


def format_delta(label: str, paths: set[str], limit: int = 20) -> list[str]:
    if not paths:
        return []
    lines = [f"{label}: {len(paths)}"]
    lines.extend(f"  {path}" for path in sorted(paths)[:limit])
    if len(paths) > limit:
        lines.append(f"  ... {len(paths) - limit} more")
    return lines


def git_repo_files(repo_id: str, revision: str) -> set[str]:
    """List a pinned public Hub tree over anonymous Git without API pagination."""
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    with tempfile.TemporaryDirectory(prefix="formosanbank-hf-tree-") as temp_dir:
        commands = [
            ["git", "init", "--quiet"],
            [
                "git",
                "remote",
                "add",
                "origin",
                f"https://huggingface.co/datasets/{repo_id}",
            ],
            [
                "git",
                "-c",
                "credential.helper=",
                "fetch",
                "--quiet",
                "--depth=1",
                "--filter=blob:none",
                "origin",
                revision,
            ],
        ]
        for command in commands:
            subprocess.run(
                command,
                cwd=temp_dir,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", "FETCH_HEAD"],
            cwd=temp_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
    return set(result.stdout.splitlines())


def validate_online(
    datasets: list[dict],
    extras: dict[str, set[str]],
    file_lister=git_repo_files,
) -> list[str]:
    failures: list[str] = []
    actual_by_repo: dict[str, set[str]] = {}
    for dataset in datasets:
        repo_id = dataset["repo_id"]
        revision = dataset["revision"]
        actual = {
            path for path in file_lister(repo_id, revision) if is_audio(path)
        }
        actual_by_repo[repo_id] = actual
        expected_count = dataset["expected_audio_files"]
        if len(actual) != expected_count:
            failures.append(
                f"{repo_id}: expected {expected_count} audio files, found {len(actual)}"
            )

    for group_name, sources in grouped(datasets).items():
        expected = expected_remote_paths(sources[0])
        actual: set[str] = set()
        declared: set[str] = set()
        for source in sources:
            repo_id = source["repo_id"]
            actual.update(actual_by_repo[repo_id])
            declared.update(extras.get(repo_id, set()))
        failures.extend(format_delta(f"{group_name} missing", expected - actual))
        failures.extend(
            format_delta(f"{group_name} undeclared extras", actual - expected - declared)
        )
        failures.extend(
            format_delta(f"{group_name} stale declarations", declared - actual)
        )
    return failures


def local_audio_paths(destination: Path) -> set[str]:
    if not destination.is_dir():
        return set()
    return {
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file() and is_audio(path)
    }


def validate_local(datasets: list[dict], extras: dict[str, set[str]]) -> list[str]:
    failures: list[str] = []
    for group_name, sources in grouped(datasets).items():
        destinations = {source["destination"] for source in sources}
        if len(destinations) != 1:
            failures.append(
                f"{group_name}: validation group uses multiple destinations"
            )
            continue
        destination = REPO_ROOT / destinations.pop()
        actual = local_audio_paths(destination)
        expected = expected_local_paths(sources[0])
        declared: set[str] = set()
        for source in sources:
            declared.update(extras.get(source["repo_id"], set()))
        failures.extend(format_delta(f"{group_name} local missing", expected - actual))
        failures.extend(
            format_delta(
                f"{group_name} local undeclared extras",
                actual - expected - declared,
            )
        )
        failures.extend(
            format_delta(f"{group_name} local stale declarations", declared - actual)
        )
    return failures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=REPO_ROOT / "audio_sources.json",
    )
    parser.add_argument("--corpus")
    parser.add_argument(
        "--local",
        action="store_true",
        help="Validate downloaded Audio directories instead of Hugging Face.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest, extras = load_contract(args.manifest)
        datasets = selected_datasets(manifest, args.corpus)
        if args.local:
            failures = validate_local(datasets, extras)
        else:
            failures = validate_online(datasets, extras)
    except Exception as exc:
        print(f"audio parity error: {exc}", file=sys.stderr)
        return 2

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    scope = args.corpus or "all public audio datasets"
    location = "local downloads" if args.local else "Hugging Face"
    print(f"Audio parity passed for {scope} against {location}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
