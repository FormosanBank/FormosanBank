#!/usr/bin/env python3
"""Bring a corpus's Hugging Face audio dataset back into parity with its XML.

`QC/validation/validate_hf_audio.py` reports two kinds of drift for a
published dataset:

  missing  — an ``AUDIO/@file`` the XML references that the dataset does not
             hold. The clip has to be sliced out of the whole-story recording
             named by ``AUDIO/@url`` and uploaded.
  extras   — a file the dataset holds that no ``AUDIO/@file`` references any
             more, usually because a rebuild changed a sentence's span.

This script performs both halves in a single Hub commit, so the dataset is
never briefly inconsistent, and prints the values that then have to go into
`audio_sources.json` (the new revision SHA and file count).

It is DRY RUN by default. Deleting files from a public dataset is not
reversible from here, so `--apply` is required to touch the Hub at all.

    # see what would change, no network writes, no downloads
    python QC/utilities/sync_hf_audio.py --repo FormosanBank/NTUFormosanCorpus_Stories \
        --xml Corpora/NTUFormosanCorpus/XML/Stories

    # do it (needs HF_TOKEN with write access to the dataset, and ffmpeg)
    python QC/utilities/sync_hf_audio.py --repo FormosanBank/NTUFormosanCorpus_Stories \
        --xml Corpora/NTUFormosanCorpus/XML/Stories --apply

Requirements: huggingface_hub (in requirements.txt), plus `pydub` and a
working `ffmpeg` on PATH for the slicing. Neither is needed for a dry run
that only reports counts (`--no-slice`).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _iter_xml(xml_dir: Path, ref: str | None):
    """Yield (language directory, parsed tree) for every XML under *xml_dir*.

    With *ref*, the files are read out of that git revision instead of the
    working tree, so the dataset can be synced against a branch without
    checking it out -- which matters when the branch is already held by a
    worktree, and when the checkout is shared.
    """
    if ref is None:
        for path in sorted(xml_dir.rglob("*.xml")):
            yield path.parent.name, ET.parse(path)
        return
    rel = xml_dir.resolve().relative_to(REPO_ROOT).as_posix()
    listing = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-tree", "-r", "--name-only", ref, "--", rel],
        capture_output=True, text=True)
    if listing.returncode:
        raise SystemExit(f"cannot read {ref}: {listing.stderr.strip()}")
    names = [n for n in listing.stdout.splitlines() if n.endswith(".xml")]
    if not names:
        raise SystemExit(f"{ref} has no XML under {rel}")
    for name in sorted(names):
        blob = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ref}:{name}"],
                              capture_output=True)
        if blob.returncode:
            raise SystemExit(f"cannot read {ref}:{name}")
        yield Path(name).parent.name, ET.ElementTree(ET.fromstring(blob.stdout))


def referenced_clips(xml_dir: Path, ref: str | None = None) -> dict[str, tuple[str, float, float]]:
    """{clip filename: (source recording url, start seconds, end seconds)}.

    The clip's directory on the Hub mirrors the XML's language directory, so
    the key is returned as the Hub path, e.g. 'Amis/Amis_..._S0.mp3'.
    """
    out: dict[str, tuple[str, float, float]] = {}
    for language, tree in _iter_xml(xml_dir, ref):
        for audio in tree.getroot().iter("AUDIO"):
            name = audio.get("file")
            url = audio.get("url")
            start, end = audio.get("start"), audio.get("end")
            if not (name and url and start is not None and end is not None):
                continue
            key = f"{language}/{name}" if language else name
            if key in out:
                continue
            out[key] = (url, float(start), float(end))
    return out


def hub_files(api, repo_id: str) -> set[str]:
    from huggingface_hub.utils import EntryNotFoundError, RepositoryNotFoundError

    try:
        listing = api.list_repo_files(repo_id=repo_id, repo_type="dataset")
    except (EntryNotFoundError, RepositoryNotFoundError) as exc:
        raise SystemExit(f"cannot read {repo_id}: {exc}")
    return {name for name in listing if name.lower().endswith(".mp3")}


def fetch_source(url: str, cache: Path) -> Path:
    """Download a whole-story recording once, reusing it for every clip."""
    import requests

    target = cache / url.rsplit("/", 1)[-1]
    if target.exists() and target.stat().st_size:
        return target
    cache.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=300) as response:
        response.raise_for_status()
        with target.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1 << 16):
                handle.write(chunk)
    return target


def slice_clip(source: Path, start: float, end: float, target: Path) -> None:
    from pydub import AudioSegment

    target.parent.mkdir(parents=True, exist_ok=True)
    audio = AudioSegment.from_file(source)
    audio[int(start * 1000):int(end * 1000)].export(target, format="mp3")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True,
                        help="dataset repo id, e.g. FormosanBank/NTUFormosanCorpus_Stories")
    parser.add_argument("--xml", required=True, type=Path,
                        help="XML directory whose AUDIO elements are the contract")
    parser.add_argument("--from-ref", default=None,
                        help="read the XML out of this git revision instead of "
                             "the working tree, e.g. "
                             "origin/corpus/ntu-reproducible-pipeline. Lets you "
                             "sync against a branch without checking it out.")
    parser.add_argument("--apply", action="store_true",
                        help="actually slice, upload and delete (default: report only)")
    parser.add_argument("--no-slice", action="store_true",
                        help="report only; do not download or slice anything")
    parser.add_argument("--work-dir", type=Path, default=None,
                        help="where to cache recordings and write clips "
                             "(default: a temporary directory)")
    parser.add_argument("--token", default=os.environ.get("HF_TOKEN"),
                        help="Hugging Face token with write access. Defaults "
                             "to $HF_TOKEN, then to a stored "
                             "`huggingface-cli login`.")
    parser.add_argument("--message", default=None, help="commit message")
    args = parser.parse_args()

    if args.from_ref is None and not args.xml.is_dir():
        raise SystemExit(f"no such XML directory: {args.xml}")

    from huggingface_hub import HfApi

    # token=None lets huggingface_hub use a stored `huggingface-cli login`;
    # token=False would refuse it, which is wrong for anyone already logged in.
    api = HfApi(token=args.token or None)
    wanted = referenced_clips(args.xml, args.from_ref)
    have = hub_files(api, args.repo)

    missing = sorted(set(wanted) - have)
    extras = sorted(have - set(wanted))

    print(f"{args.repo}")
    if args.from_ref:
        print(f"  XML read from   : {args.from_ref}")
    print(f"  referenced by the XML : {len(wanted)}")
    print(f"  present on the Hub    : {len(have)}")
    print(f"  to slice and upload   : {len(missing)}")
    print(f"  to delete             : {len(extras)}")
    for name in missing[:10]:
        url, start, end = wanted[name]
        print(f"      + {name}  [{start}-{end}]")
    if len(missing) > 10:
        print(f"      … {len(missing) - 10} more")
    for name in extras[:10]:
        print(f"      - {name}")
    if len(extras) > 10:
        print(f"      … {len(extras) - 10} more")

    if not missing and not extras:
        print("  already in parity; nothing to do")
        return 0
    if not args.apply:
        print("\ndry run — nothing was changed. Re-run with --apply to act.")
        return 0
    if missing and args.no_slice:
        raise SystemExit("--no-slice cannot be combined with --apply when clips are missing")
    try:
        whoami = api.whoami()
    except Exception:
        raise SystemExit(
            "--apply needs write access. Either run `huggingface-cli login`, "
            "or set HF_TOKEN to a token with write permission on the dataset:\n"
            "    export HF_TOKEN=hf_xxxxxxxx\n"
            "    python QC/utilities/sync_hf_audio.py ... --apply")
    print(f"  authenticated as: {whoami.get('name', '?')}")

    from huggingface_hub import CommitOperationAdd, CommitOperationDelete

    context = (tempfile.TemporaryDirectory() if args.work_dir is None
               else None)
    work = Path(context.name) if context else args.work_dir
    work.mkdir(parents=True, exist_ok=True)
    cache = work / "recordings"

    operations = []
    try:
        by_source: dict[str, list[str]] = defaultdict(list)
        for name in missing:
            by_source[wanted[name][0]].append(name)
        for index, (url, names) in enumerate(sorted(by_source.items()), 1):
            print(f"  [{index}/{len(by_source)}] {url.rsplit('/', 1)[-1]} "
                  f"→ {len(names)} clip(s)")
            source = fetch_source(url, cache)
            for name in names:
                _, start, end = wanted[name]
                target = work / "clips" / name
                slice_clip(source, start, end, target)
                operations.append(
                    CommitOperationAdd(path_in_repo=name, path_or_fileobj=str(target)))
        operations.extend(CommitOperationDelete(path_in_repo=name) for name in extras)

        message = args.message or (
            f"Sync audio with the published XML: +{len(missing)} clip(s), "
            f"-{len(extras)} no longer referenced")
        info = api.create_commit(repo_id=args.repo, repo_type="dataset",
                                 operations=operations, commit_message=message)
    finally:
        if context:
            context.cleanup()

    revision = getattr(info, "oid", None) or getattr(info, "commit_id", None)
    print(f"\ncommitted {len(operations)} operation(s)")
    print(f"  revision: {revision}")
    print(f"  audio files now: {len(wanted)}")
    print("\nUpdate audio_sources.json for this dataset:")
    print(f'    "revision": "{revision}",')
    print(f'    "expected_audio_files": {len(wanted)}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
