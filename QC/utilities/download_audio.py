#!/usr/bin/env python3
"""Download public FormosanBank audio from the canonical Hugging Face manifest."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from QC.validation.validate_hf_audio import (  # noqa: E402
    AUDIO_SUFFIXES,
    is_audio,
    load_contract,
    local_audio_paths,
    selected_datasets,
    validate_local,
    validate_online,
)


def allow_patterns() -> list[str]:
    result = []
    for suffix in sorted(AUDIO_SUFFIXES):
        result.extend((f"*{suffix}", f"**/*{suffix}"))
    return result


def run_git(directory: Path, *arguments: str) -> None:
    env = {
        **os.environ,
        "GIT_LFS_SKIP_SMUDGE": "1",
        "GIT_TERMINAL_PROMPT": "0",
    }
    subprocess.run(
        ["git", "-c", "credential.helper=", *arguments],
        cwd=directory,
        env=env,
        check=True,
    )


def require_git_lfs() -> None:
    if shutil.which("git") is None:
        raise RuntimeError("git is required to download public audio")
    if shutil.which("git-lfs") is None:
        raise RuntimeError(
            "git-lfs is required to download public audio; "
            "install it from https://git-lfs.com/"
        )


def is_lfs_pointer(path: Path) -> bool:
    if path.stat().st_size > 1024:
        return False
    return path.read_bytes().startswith(b"version https://git-lfs.github.com/spec/")


def move_audio_files(
    source: Path, destination: Path, expected_count: int
) -> int:
    audio_files = [
        path
        for path in source.rglob("*")
        if path.is_file() and is_audio(path)
    ]
    if len(audio_files) != expected_count:
        raise RuntimeError(
            f"staged checkout has {len(audio_files)} audio files; "
            f"expected {expected_count}"
        )
    pointers = [path for path in audio_files if is_lfs_pointer(path)]
    if pointers:
        raise RuntimeError(
            f"Git LFS left {len(pointers)} audio pointers unresolved; "
            f"first: {pointers[0].relative_to(source)}"
        )

    moved = 0
    for path in audio_files:
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_file() and target.stat().st_size == path.stat().st_size:
            continue
        shutil.move(path, target)
        moved += 1
    return moved


def destination_counts(datasets: list[dict]) -> dict[str, int]:
    return {
        destination: len(local_audio_paths(REPO_ROOT / destination))
        for destination in {dataset["destination"] for dataset in datasets}
    }


def run_post_download(commands: list[list[str]]) -> None:
    for command in commands:
        expanded = [
            sys.executable if value == "{python}" else str(REPO_ROOT / value)
            if value.startswith("Corpora/") or value.startswith("QC/")
            else value
            for value in command
        ]
        subprocess.run(expanded, cwd=REPO_ROOT, check=True)


def download_datasets(datasets: list[dict], workers: int = 64) -> None:
    include = ",".join(allow_patterns())
    cache_root = REPO_ROOT / ".audio-download-cache"
    for dataset in datasets:
        destination = REPO_ROOT / dataset["destination"]
        destination.mkdir(parents=True, exist_ok=True)
        print(
            f"Downloading {dataset['repo_id']}@{dataset['revision'][:12]} "
            f"to {dataset['destination']}"
        )
        cache_name = (
            dataset["repo_id"].replace("/", "__") + "-" + dataset["revision"][:12]
        )
        checkout = cache_root / cache_name
        checkout.mkdir(parents=True, exist_ok=True)
        if not (checkout / ".git").is_dir():
            run_git(checkout, "init", "--quiet")
            run_git(
                checkout,
                "remote",
                "add",
                "origin",
                f"https://huggingface.co/datasets/{dataset['repo_id']}",
            )
        run_git(
            checkout,
            "config",
            "lfs.concurrenttransfers",
            str(workers),
        )
        run_git(
            checkout,
            "fetch",
            "--quiet",
            "--depth=1",
            "origin",
            dataset["revision"],
        )
        run_git(checkout, "checkout", "--quiet", "--force", "--detach", "FETCH_HEAD")
        run_git(checkout, "lfs", "pull", f"--include={include}")
        moved = move_audio_files(
            checkout,
            destination,
            expected_count=dataset["expected_audio_files"],
        )
        shutil.rmtree(checkout)
        if cache_root.is_dir() and not any(cache_root.iterdir()):
            cache_root.rmdir()
        print(f"Installed {moved} new or changed audio files.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=REPO_ROOT / "audio_sources.json",
    )
    parser.add_argument("--corpus", required=True)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check the remote contract without downloading audio.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=64,
        help="Concurrent Git LFS transfers (default: 64).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.workers < 1:
            raise ValueError("--workers must be at least 1")
        manifest, extras, permissions = load_contract(args.manifest)
        try:
            datasets = selected_datasets(manifest, args.corpus)
        except ValueError:
            withheld = [
                source
                for source in permissions["sources"]
                if source["corpus"] == args.corpus
                and source["status"] == "withheld_pending_permission"
            ]
            if not withheld:
                raise
            print(
                f"Audio withheld for {args.corpus}: source-specific "
                "redistribution permission is not verified. "
                "See AUDIO-PERMISSIONS.md.",
                file=sys.stderr,
            )
            return 3
        failures = validate_online(datasets, extras)
        if failures:
            print("\n".join(failures), file=sys.stderr)
            return 1

        if args.dry_run:
            for dataset in datasets:
                print(
                    f"{dataset['repo_id']} -> {dataset['destination']} "
                    f"({dataset['expected_audio_files']} audio files)"
                )
            return 0

        require_git_lfs()
        before = destination_counts(datasets)
        download_datasets(datasets, workers=args.workers)
        after_download = destination_counts(datasets)

        commands = []
        seen = set()
        for dataset in datasets:
            command = dataset.get("post_download")
            if command and tuple(command) not in seen:
                commands.append(command)
                seen.add(tuple(command))
        run_post_download(commands)
        after_post = destination_counts(datasets)

        failures = validate_local(datasets, extras)
        if failures:
            print("\n".join(failures), file=sys.stderr)
            return 1

        downloaded = sum(
            max(0, after_download[path] - before[path]) for path in before
        )
        generated = sum(
            max(0, after_post[path] - after_download[path]) for path in before
        )
        present = sum(after_post.values())
        print(
            f"Audio ready for {args.corpus}: present={present}, "
            f"downloaded={downloaded}, generated={generated}, missing=0"
        )
        return 0
    except Exception as exc:
        print(f"audio download failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
