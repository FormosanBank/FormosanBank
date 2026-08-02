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

AUDIO_SUFFIXES = {
    ".aac",
    ".aif",
    ".aiff",
    ".flac",
    ".m4a",
    ".mov",
    ".mp3",
    ".mp4",
    ".ogg",
    ".opus",
    ".wav",
    ".webm",
    ".wma",
}
REPO_ROOT = Path(__file__).resolve().parents[2]


def is_audio(path: str | Path) -> bool:
    return Path(path).suffix.lower() in AUDIO_SUFFIXES


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def license_family(value: str) -> str:
    """Normalize spelling and omit the version for XML/license comparison."""
    return " ".join(re.findall(r"[A-Z]+", value.upper()))


def load_contract(
    manifest_path: Path,
) -> tuple[dict, dict[str, set[str]], dict]:
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
        permission_id = dataset.get("permission_id")
        if not isinstance(permission_id, str) or not permission_id:
            raise ValueError(f"{repo_id}: permission_id must be a non-empty string")
        batch_2 = dataset.get("rukai_batch_2_files", [])
        if not isinstance(batch_2, list) or not all(
            isinstance(path, str) and is_audio(path) for path in batch_2
        ):
            raise ValueError(f"{repo_id}: rukai_batch_2_files must be audio filenames")

    permissions_path = REPO_ROOT / manifest["permissions"]
    permissions = load_json(permissions_path)
    if permissions.get("schema_version") != 2:
        raise ValueError("unsupported audio-permissions schema")
    sources = permissions.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("audio permissions sources must be a non-empty list")
    if not all(isinstance(source, dict) for source in sources):
        raise ValueError("audio permission sources must be objects")
    permission_ids = [source.get("permission_id") for source in sources]
    if len(permission_ids) != len(set(permission_ids)):
        raise ValueError("audio permission_id values must be unique")
    source_by_id: dict[str, dict] = {}
    permission_repo_ids: set[str] = set()
    for source in sources:
        permission_id = source.get("permission_id")
        if not isinstance(permission_id, str) or not permission_id:
            raise ValueError("audio permission_id must be a non-empty string")
        status = source.get("status")
        if status not in {"published_public", "development_private"}:
            raise ValueError(f"{permission_id}: invalid permission status {status!r}")
        if not isinstance(source.get("corpus"), str) or not source["corpus"]:
            raise ValueError(f"{permission_id}: corpus must be a non-empty string")
        if not isinstance(source.get("basis"), str) or not source["basis"]:
            raise ValueError(f"{permission_id}: basis must be a non-empty string")
        repositories = source.get("hf_repositories")
        if not isinstance(repositories, list) or not repositories:
            raise ValueError(
                f"{permission_id}: hf_repositories must be a non-empty list"
            )
        for repository in repositories:
            if not isinstance(repository, dict):
                raise ValueError(
                    f"{permission_id}: hf_repositories entries must be objects"
                )
            repo_id = repository.get("repo_id")
            access = repository.get("access")
            if not isinstance(repo_id, str) or "/" not in repo_id:
                raise ValueError(f"{permission_id}: invalid HF repo_id {repo_id!r}")
            if repo_id in permission_repo_ids:
                raise ValueError(
                    f"{repo_id}: appears in multiple audio permission sources"
                )
            permission_repo_ids.add(repo_id)
            if access not in {"public", "private"}:
                raise ValueError(
                    f"{repo_id}: invalid Hugging Face access state {access!r}"
                )
            if status == "published_public" and access != "public":
                raise ValueError(
                    f"{permission_id}: published repositories must be public"
                )
            if status == "development_private" and access != "private":
                raise ValueError(
                    f"{permission_id}: development repositories must be private"
                )
        if status == "published_public":
            if not isinstance(source.get("license"), str) or not source["license"]:
                raise ValueError(
                    f"{permission_id}: published source requires a license"
                )
            if not isinstance(source.get("hf_license"), str) or not source["hf_license"]:
                raise ValueError(
                    f"{permission_id}: published source requires an HF license id"
                )
            if not isinstance(source.get("approval_record"), str) or not source[
                "approval_record"
            ]:
                raise ValueError(
                    f"{permission_id}: published source requires an approval record"
                )
            xml_path = source.get("xml_path")
            if not isinstance(xml_path, str) or not (REPO_ROOT / xml_path).is_dir():
                raise ValueError(
                    f"{permission_id}: published XML path does not exist: {xml_path}"
                )
            xml_files = sorted((REPO_ROOT / xml_path).rglob("*.xml"))
            if not xml_files:
                raise ValueError(f"{permission_id}: published XML path has no XML")
            xml_licenses = {
                license_family(ET.parse(path).getroot().get("copyright", ""))
                for path in xml_files
            }
            expected_license = license_family(source["license"])
            if xml_licenses != {expected_license}:
                raise ValueError(
                    f"{permission_id}: XML licenses {sorted(xml_licenses)!r} do not "
                    f"match {source['license']!r}"
                )
        source_by_id[permission_id] = source

    for dataset in datasets:
        repo_id = dataset["repo_id"]
        permission_id = dataset["permission_id"]
        source = source_by_id.get(permission_id)
        if source is None:
            raise ValueError(
                f"{repo_id}: permission_id {permission_id!r} is not in "
                "audio_permissions.json"
            )
        if source["status"] != "published_public":
            raise ValueError(
                f"{repo_id}: source {permission_id!r} is not published in "
                "FormosanBank"
            )
        public_repositories = {
            repository["repo_id"]
            for repository in source["hf_repositories"]
            if repository["access"] == "public"
        }
        if repo_id not in public_repositories:
            raise ValueError(
                f"{repo_id}: is not a public repository under permission "
                f"{permission_id!r}"
            )

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
    return manifest, extras, permissions


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


def validate_hf_inventory(manifest: dict, permissions: dict, api=None) -> list[str]:
    """Enforce public published audio and private development audio on the Hub."""
    if api is None:
        from huggingface_hub import HfApi

        api = HfApi(token=False)

    organization = permissions["hf_organization"]
    public_datasets = {
        item.id
        for item in api.list_datasets(author=organization, full=True)
        if not getattr(item, "private", False) and not getattr(item, "gated", False)
    }
    manifested = {dataset["repo_id"] for dataset in manifest["datasets"]}
    published = {
        repository["repo_id"]
        for source in permissions["sources"]
        if source["status"] == "published_public"
        for repository in source["hf_repositories"]
    }
    public_non_audio = permissions.get("public_non_audio_datasets")
    if not isinstance(public_non_audio, list) or not all(
        isinstance(repo_id, str) and "/" in repo_id
        for repo_id in public_non_audio
    ):
        raise ValueError("public_non_audio_datasets must be a list of repo IDs")
    allowed = published | set(public_non_audio)

    failures: list[str] = []
    failures.extend(
        format_delta(
            "unapproved public Hugging Face datasets",
            public_datasets - allowed,
        )
    )
    failures.extend(
        format_delta(
            "published audio datasets not anonymously public",
            published - public_datasets,
        )
    )
    failures.extend(
        format_delta(
            "canonical audio datasets missing publication records",
            manifested - published,
        )
    )

    for repo_id in public_non_audio:
        files = api.list_repo_files(
            repo_id,
            repo_type="dataset",
            token=False,
        )
        audio = {path for path in files if is_audio(path)}
        failures.extend(
            format_delta(f"{repo_id} declared non-audio but contains audio", audio)
        )

    public_models = [
        item
        for item in api.list_models(author=organization, full=True)
        if not getattr(item, "private", False) and not getattr(item, "gated", False)
    ]
    public_spaces = [
        item
        for item in api.list_spaces(author=organization, full=True)
        if not getattr(item, "private", False) and not getattr(item, "gated", False)
    ]
    for repo_type, items in (("model", public_models), ("space", public_spaces)):
        for item in items:
            files = api.list_repo_files(
                item.id,
                repo_type=repo_type,
                token=False,
            )
            audio = {path for path in files if is_audio(path)}
            failures.extend(
                format_delta(
                    f"{item.id} public {repo_type} contains unapproved audio",
                    audio,
                )
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
        manifest, extras, permissions = load_contract(args.manifest)
        datasets = selected_datasets(manifest, args.corpus)
        if args.local:
            failures = validate_local(datasets, extras)
        else:
            failures = validate_hf_inventory(manifest, permissions)
            failures.extend(validate_online(datasets, extras))
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
