from __future__ import annotations

import argparse
import os
import signal
import sys
from typing import Iterable, List

from huggingface_hub import HfApi, snapshot_download


def signal_handler(signum, frame):
    print("\n\nReceived interrupt signal. Exiting gracefully...")
    sys.exit(0)


def list_formosanbank_datasets() -> List[str]:
    api = HfApi()
    datasets = api.list_datasets(author="FormosanBank")
    dataset_ids = [d.id for d in datasets if d.id]
    dataset_ids.sort()
    return dataset_ids


def display_datasets(dataset_ids: Iterable[str]) -> None:
    print("Available FormosanBank datasets:")
    for idx, dataset_id in enumerate(dataset_ids, start=1):
        print(f"  {idx:>2}. {dataset_id}")


def normalize_dataset_id(value: str) -> str:
    value = value.strip()
    if "/" not in value:
        return f"FormosanBank/{value}"
    return value


def parse_selection(selection: str, dataset_ids: List[str]) -> List[str]:
    selection = selection.strip()
    if not selection:
        return []

    if selection.lower() in {"all", "*"}:
        return dataset_ids

    chosen: List[str] = []
    tokens = [tok.strip() for tok in selection.replace(" ", ",").split(",") if tok.strip()]

    for token in tokens:
        if token.isdigit():
            idx = int(token)
            if 1 <= idx <= len(dataset_ids):
                chosen.append(dataset_ids[idx - 1])
            else:
                raise ValueError(f"Selection index out of range: {token}")
        else:
            normalized = normalize_dataset_id(token)
            if normalized in dataset_ids:
                chosen.append(normalized)
            else:
                raise ValueError(f"Unknown dataset: {token}")

    # Remove duplicates while preserving order
    seen = set()
    deduped = []
    for item in chosen:
        if item not in seen:
            deduped.append(item)
            seen.add(item)

    return deduped


def ensure_output_dir(path: str) -> str:
    path = os.path.abspath(os.path.expanduser(path))
    os.makedirs(path, exist_ok=True)
    return path


def download_dataset(dataset_id: str, output_dir: str) -> None:
    dataset_name = dataset_id.split("/")[-1]
    target_dir = os.path.join(output_dir, dataset_name)
    os.makedirs(target_dir, exist_ok=True)

    print(f"\nDownloading {dataset_id} -> {target_dir}")
    snapshot_download(
        repo_id=dataset_id,
        repo_type="dataset",
        local_dir=target_dir,
        local_dir_use_symlinks=False,
        max_workers=1,
    )
    print(f"Completed: {dataset_id}")


def prompt_for_output_dir() -> str:
    while True:
        output_dir = input("Enter output directory path: ").strip()
        if output_dir:
            return output_dir
        print("Please enter a valid directory path.")


def prompt_for_selection(dataset_ids: List[str]) -> List[str]:
    while True:
        selection = input(
            "\nSelect datasets (numbers, names, or 'all'; separate with commas): "
        )
        try:
            chosen = parse_selection(selection, dataset_ids)
        except ValueError as exc:
            print(str(exc))
            continue

        if not chosen:
            print("No datasets selected. Please try again.")
            continue
        return chosen


def main() -> None:
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(
        description="Interactively download FormosanBank datasets from Hugging Face."
    )
    parser.add_argument(
        "--output_dir",
        help="Directory to save downloaded datasets (will be created if missing).",
    )
    parser.add_argument(
        "--datasets",
        nargs="*",
        help=(
            "Datasets to download (names or full ids). If omitted, an interactive "
            "prompt will be shown."
        ),
    )
    args = parser.parse_args()

    dataset_ids = list_formosanbank_datasets()
    if not dataset_ids:
        print("No datasets found for FormosanBank.")
        sys.exit(1)

    display_datasets(dataset_ids)

    if args.datasets:
        selection = ",".join(args.datasets)
        chosen = parse_selection(selection, dataset_ids)
    else:
        chosen = prompt_for_selection(dataset_ids)

    output_dir = args.output_dir or prompt_for_output_dir()
    output_dir = ensure_output_dir(output_dir)

    print(f"\nSaving datasets to: {output_dir}")
    for dataset_id in chosen:
        download_dataset(dataset_id, output_dir)

    print("\nAll downloads completed.")


if __name__ == "__main__":
    main()
