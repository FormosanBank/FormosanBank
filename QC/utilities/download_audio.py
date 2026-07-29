#!/usr/bin/env python3
"""Download public FormosanBank audio from the canonical Hugging Face manifest."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from huggingface_hub import snapshot_download


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from QC.validation.validate_hf_audio import (  # noqa: E402
    AUDIO_SUFFIXES,
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


def download_datasets(datasets: list[dict]) -> None:
    for dataset in datasets:
        destination = REPO_ROOT / dataset["destination"]
        destination.mkdir(parents=True, exist_ok=True)
        print(
            f"Downloading {dataset['repo_id']}@{dataset['revision'][:12]} "
            f"to {dataset['destination']}"
        )
        snapshot_download(
            dataset["repo_id"],
            repo_type="dataset",
            revision=dataset["revision"],
            local_dir=destination,
            allow_patterns=allow_patterns(),
            token=False,
        )
        cache = destination / ".cache" / "huggingface"
        if cache.exists():
            shutil.rmtree(cache)
        parent = cache.parent
        if parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()


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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest, extras = load_contract(args.manifest)
        datasets = selected_datasets(manifest, args.corpus)
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

        before = destination_counts(datasets)
        download_datasets(datasets)
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
