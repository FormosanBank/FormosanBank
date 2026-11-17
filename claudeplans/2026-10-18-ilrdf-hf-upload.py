#!/usr/bin/env python3
"""Put FormosanBank/ILRDF_Dicts on Hugging Face into the 2026 sharded layout (run on the Mac).

RESUMABLE: it works out what to do from whatever the dataset holds now, so
after any failure just run the same command again.

Run from the folder that holds FormosanBank/, ILRDF_upload_2026/ and the
ILRDF_upload_2026_* files (the container's /workspace):

    ~/hf-upload-env/bin/python FormosanBank/claudeplans/2026-10-18-ilrdf-hf-upload.py         # dry run: plan only
    ~/hf-upload-env/bin/python FormosanBank/claudeplans/2026-10-18-ilrdf-hf-upload.py --go    # do it

(~/hf-upload-env/bin/python is the virtual environment with huggingface_hub; Homebrew's
python3 does not have it.)

Why: Hugging Face refuses more than 10,000 files in one folder. Ruling
2026-10-18 ("Shard big languages by name (Recommended)"): Bunun, Rukai and
Yami files live in 16 subfolders, <Lang>/<Lang>/<shard>/<file>, shard = first
hex digit of the SHA-256 of the UTF-8 file name. The target path list was
computed in the container by QC/validation/validate_hf_audio.py (branch
qc/ilrdf-hf-sharding) from the ILRDF branch XML and written to
ILRDF_upload_2026_expected.json (132,530 audio paths).

What it does:
0. First deletes every audio file on main that the failed run added (it is
   not in the revision FormosanBank main pins, PINNED below), that is not
   already at its target path, and whose exact bytes (file name AND sha256)
   are in the local staging tree. Nothing in FormosanBank main reads them,
   and step 2 re-uploads them to their shard path from staging. This makes
   room in folders the failed run filled (e.g. Bunun/Bunun) before any
   shard subfolder is created there.
1. Reads the target list, the staging manifest (ILRDF_upload_2026_manifest.tsv:
   old path, bytes, sha256 of the 33,817 new files staged in
   ILRDF_upload_2026/, which is keyed by the OLD, unsharded paths) and lists
   every file on the dataset's main branch.
2. For each target path that is not there yet:
   - the same file name is on Hugging Face at another path -> server-side
     copy (CommitOperationCopy; nothing is uploaded);
   - otherwise -> upload the staged file (found by file name, checked
     against its sha256 first).
3. Then deletes every audio path on Hugging Face that is not in the target:
   the old unsharded copies, the 112 ruled deletions, and files the
   failed run uploaded under old paths.
4. Commits in batches of at most 500 operations: all copies, then all
   uploads, then all deletions, so every recording always exists somewhere
   and no folder ever gains files beyond its target. Each commit names its
   parent, so nothing is applied on top of an unexpected state.
5. Checks the audio on main == the target, and prints the revision to pin.

Needs huggingface_hub 1.x or older (CommitOperationCopy), and a write login
(`huggingface-cli login`, `hf auth login`, or HF_TOKEN).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import huggingface_hub

_major = int(huggingface_hub.__version__.split(".")[0])
if _major >= 2 or not hasattr(huggingface_hub, "CommitOperationCopy"):
    sys.exit(f"STOP: huggingface_hub {huggingface_hub.__version__} is not supported here "
             "(need < 2, with CommitOperationCopy). Install a 1.x release: "
             "~/hf-upload-env/bin/python -m pip install 'huggingface_hub<2'")

from huggingface_hub import (  # noqa: E402
    CommitOperationAdd,
    CommitOperationCopy,
    CommitOperationDelete,
    HfApi,
)

REPO = "FormosanBank/ILRDF_Dicts"
REPO_TYPE = "dataset"
PINNED = "b2afa779919ae1dad3875e1e6fc05fca1c3a52c1"   # what FormosanBank main reads
BATCH = 500
FOLDER_LIMIT = 10_000
AUDIO = (".aac", ".aif", ".aiff", ".flac", ".m4a", ".mov", ".mp3", ".mp4",
         ".ogg", ".opus", ".wav", ".webm", ".wma")
RETRY_STATUSES = {429, 500, 502, 503, 504}


def is_audio(path: str) -> bool:
    return path.lower().endswith(AUDIO)


def name_of(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def folder_of(path: str) -> str:
    return path.rsplit("/", 1)[0] if "/" in path else ""


@dataclass
class Staged:
    old_path: str
    local: Path
    size: int
    sha256: str


@dataclass
class Plan:
    stray: list[str] = field(default_factory=list)                   # phase 0 deletions
    in_place: int = 0
    copies: list[tuple[str, str]] = field(default_factory=list)      # (src, dst)
    uploads: list[tuple[str, Staged]] = field(default_factory=list)  # (dst, staged)
    deletes: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)


def load_target(path: Path) -> set[str]:
    target = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(target, list) or not all(isinstance(p, str) for p in target):
        sys.exit(f"STOP: {path} must be a JSON list of paths")
    if len(target) != len(set(target)):
        sys.exit(f"STOP: {path} lists a path twice")
    names = Counter(name_of(p) for p in target)
    twice = [n for n, c in names.items() if c > 1]
    if twice:
        sys.exit(f"STOP: {len(twice)} file names appear at two target paths, e.g. {twice[:3]}")
    return set(target)


def load_staging(manifest: Path, stage: Path) -> dict[str, Staged]:
    by_name: dict[str, Staged] = {}
    lines = manifest.read_text(encoding="utf-8").splitlines()
    if lines[0].split("\t") != ["hf_path", "bytes", "sha256"]:
        sys.exit(f"STOP: unexpected header in {manifest}: {lines[0]!r}")
    for line in lines[1:]:
        old_path, size, sha = line.split("\t")
        name = name_of(old_path)
        if name in by_name:
            sys.exit(f"STOP: file name {name} is staged twice")
        by_name[name] = Staged(old_path, stage / old_path, int(size), sha)
    return by_name


def _lfs_sha(entry) -> str | None:
    lfs = getattr(entry, "lfs", None)
    if lfs is None:
        return None
    sha = getattr(lfs, "sha256", None)
    if sha is None and isinstance(lfs, dict):
        sha = lfs.get("sha256")
    return sha


def call_hub(call, *args, what: str, **kwargs):
    """Retry throttling (429) and server errors; anything else is re-raised."""
    delay = 30.0
    for attempt in range(1, 7):
        try:
            return call(*args, **kwargs)
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status not in RETRY_STATUSES or attempt == 6:
                raise
            wait = delay + random.uniform(0, delay / 2)
            print(f"  hugging face {status} on {what} (attempt {attempt}/6); "
                  f"retrying in {wait:.0f}s", flush=True)
            time.sleep(wait)
            delay = min(delay * 2, 600)


def list_remote(api, revision: str) -> dict[str, str | None]:
    """Every file at `revision`: path -> LFS sha256 (None when not LFS)."""
    result: dict[str, str | None] = {}
    entries = call_hub(lambda: list(api.list_repo_tree(
        REPO, recursive=True, repo_type=REPO_TYPE, revision=revision)),
        what="list_repo_tree")
    for entry in entries:
        if hasattr(entry, "blob_id") or hasattr(entry, "lfs"):   # a file, not a folder
            result[entry.path] = _lfs_sha(entry)
    return result


def stray_uploads(target: set[str], remote: dict[str, str | None], pinned: set[str],
                  staged: dict[str, Staged]) -> list[str]:
    """Phase 0: audio the failed run added, not at a target path, bytes held locally."""
    result = []
    for path, sha in remote.items():
        if not is_audio(path) or path in pinned or path in target:
            continue
        local = staged.get(name_of(path))
        if local is not None and sha is not None and sha == local.sha256:
            result.append(path)
    return sorted(result)


def make_plan(target: set[str], remote: dict[str, str | None],
              staged: dict[str, Staged], pinned: set[str]) -> Plan:
    stray = stray_uploads(target, remote, pinned, staged)
    remote = {p: sha for p, sha in remote.items() if p not in set(stray)}
    plan = Plan(stray=stray)
    remote_audio = {p for p in remote if is_audio(p)}
    where: dict[str, list[str]] = defaultdict(list)
    for path in sorted(remote_audio):
        where[name_of(path)].append(path)

    for dst in sorted(target):
        if dst in remote_audio:
            plan.in_place += 1
            continue
        name = name_of(dst)
        want = staged[name].sha256 if name in staged else None
        sources = where.get(name, [])
        shas = {remote[s] for s in sources if remote[s] is not None}
        if sources:
            if len(shas) > 1:
                plan.problems.append(f"{dst}: {name} is on Hugging Face at {len(sources)} "
                                     f"paths with different contents: {sources}")
            elif want is not None and shas and shas != {want}:
                plan.problems.append(f"{dst}: {sources[0]} on Hugging Face has sha256 "
                                     f"{shas.pop()}, the staged file has {want}")
            else:
                plan.copies.append((sources[0], dst))
        elif name in staged:
            plan.uploads.append((dst, staged[name]))
        else:
            plan.problems.append(f"{dst}: not on Hugging Face and not staged")

    plan.deletes = sorted(remote_audio - target)
    return plan


def folder_entries(paths) -> tuple[Counter, Counter]:
    """(files directly in each folder, subfolders directly in each folder)."""
    files: Counter = Counter()
    subfolders: dict[str, set[str]] = defaultdict(set)
    for path in paths:
        folder = folder_of(path)
        files[folder] += 1
        parts = folder.split("/") if folder else []
        for i in range(1, len(parts)):
            subfolders["/".join(parts[:i])].add(parts[i])
    return files, Counter({k: len(v) for k, v in subfolders.items()})


def print_plan(plan: Plan, remote: dict[str, str | None], target: set[str],
               ruled_deletes: set[str]) -> int:
    """Print the plan; return the largest folder file count at any point."""
    remote_audio = {p for p in remote if is_audio(p)}
    print(f"audio on Hugging Face now: {len(remote_audio)} "
          f"(plus {len(remote) - len(remote_audio)} other files, left alone)")
    print(f"phase 0 deletions:         {len(plan.stray)} (added by the failed run, not at "
          f"their target path, bytes in staging; re-uploaded below)")
    start_audio = remote_audio
    remote_audio = remote_audio - set(plan.stray)
    print(f"target audio paths:        {len(target)}")
    print(f"  already in place:        {plan.in_place}")
    print(f"  server-side copies:      {len(plan.copies)}")
    print(f"  uploads from staging:    {len(plan.uploads)}"
          f" ({sum(s.size for _, s in plan.uploads):,} bytes)")
    print(f"deletions afterwards:      {len(plan.deletes)}")
    target_names = {name_of(p) for p in target}
    kinds = Counter(
        "ruled deletion (ILRDF_upload_2026_delete.txt)" if p in ruled_deletes
        else "old path of a file that is in the target" if name_of(p) in target_names
        else "OTHER: file name not in the target, not a ruled deletion"
        for p in plan.deletes)
    for kind, count in sorted(kinds.items()):
        print(f"  {count:6d}  {kind}")
    other = [p for p in plan.deletes
             if p not in ruled_deletes and name_of(p) not in target_names]
    for path in other[:50]:
        print(f"          {path}")
    by_lang = defaultdict(Counter)
    for _, dst in plan.copies:
        by_lang[dst.split("/")[0]]["copy"] += 1
    for dst, _ in plan.uploads:
        by_lang[dst.split("/")[0]]["upload"] += 1
    for path in plan.deletes:
        by_lang[path.split("/")[0]]["delete"] += 1
    print("by language (copy / upload / delete):")
    for lang in sorted(by_lang):
        c = by_lang[lang]
        print(f"  {lang:12s} {c['copy']:6d} {c['upload']:6d} {c['delete']:6d}")

    # Largest folder now, after copies+uploads (before deletions), and at the end.
    after_adds = remote_audio | {d for _, d in plan.copies} | {d for d, _ in plan.uploads}
    worst = 0
    for label, paths in (("now", start_audio), ("after phase 0", remote_audio),
                         ("after copies and uploads", after_adds),
                         ("at the end", target)):
        files, subs = folder_entries(paths)
        folder, count = files.most_common(1)[0]
        # counted as files + subfolders, in case the Hub counts both
        worst = max(worst, max(n + subs.get(f, 0) for f, n in files.items()))
        print(f"largest folder {label}: {folder} with {count} files")
        close = [(f, n, subs.get(f, 0)) for f, n in files.items() if n + subs.get(f, 0) > 9_000]
        for f, n, s in sorted(close):
            print(f"    near the limit: {f}: {n} files + {s} subfolders")
    return worst


def batches(items: list, size: int = BATCH):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def commit(api, head: str, operations: list, message: str) -> str:
    info = call_hub(api.create_commit, REPO, operations, commit_message=message,
                    repo_type=REPO_TYPE, parent_commit=head, what=message)
    oid = getattr(info, "oid", None) or api.dataset_info(REPO).sha
    return oid


def execute(api, plan: Plan, head: str) -> str:
    n = len(plan.stray)
    for i, batch in enumerate(batches(plan.stray), 1):
        ops = [CommitOperationDelete(path_in_repo=path) for path in batch]
        head = commit(api, head, ops, f"ILRDF 2026: remove {len(ops)} files the failed upload "
                                      f"put at old paths ({i}/{-(-n // BATCH)})")
        print(f"  phase 0 deletions committed: {min(i * BATCH, n)}/{n}  head {head[:12]}", flush=True)
    n = len(plan.copies)
    for i, batch in enumerate(batches(plan.copies), 1):
        ops = [CommitOperationCopy(src_path_in_repo=src, path_in_repo=dst) for src, dst in batch]
        head = commit(api, head, ops, f"ILRDF sharding: copy {len(ops)} files into "
                                      f"name-shard folders ({i}/{-(-n // BATCH)})")
        print(f"  copies committed: {min(i * BATCH, n)}/{n}  head {head[:12]}", flush=True)
    n = len(plan.uploads)
    for i, batch in enumerate(batches(plan.uploads), 1):
        ops = []
        for dst, staged in batch:
            if not staged.local.is_file():
                sys.exit(f"STOP: staged file missing: {staged.local}")
            got = sha256_of(staged.local)
            if got != staged.sha256:
                sys.exit(f"STOP: {staged.local} has sha256 {got}, manifest says {staged.sha256}")
            ops.append(CommitOperationAdd(path_in_repo=dst, path_or_fileobj=str(staged.local)))
        head = commit(api, head, ops, f"ILRDF 2026: upload {len(ops)} new recordings "
                                      f"({i}/{-(-n // BATCH)})")
        print(f"  uploads committed: {min(i * BATCH, n)}/{n}  head {head[:12]}", flush=True)
    n = len(plan.deletes)
    for i, batch in enumerate(batches(plan.deletes), 1):
        ops = [CommitOperationDelete(path_in_repo=path) for path in batch]
        head = commit(api, head, ops, f"ILRDF 2026: remove {len(ops)} files not in the "
                                      f"sharded layout ({i}/{-(-n // BATCH)})")
        print(f"  deletions committed: {min(i * BATCH, n)}/{n}  head {head[:12]}", flush=True)
    return head


def main(argv: list[str] | None = None, api=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--go", action="store_true", help="actually copy, upload and delete")
    ap.add_argument("--root", type=Path, default=Path.cwd(),
                    help="folder holding ILRDF_upload_2026/ and its files (default: here)")
    args = ap.parse_args(argv)
    root = args.root
    api = api or HfApi()

    target = load_target(root / "ILRDF_upload_2026_expected.json")
    files, _ = folder_entries(target)
    if max(files.values()) > FOLDER_LIMIT:
        sys.exit(f"STOP: the target puts {max(files.values())} files in one folder")
    staged = load_staging(root / "ILRDF_upload_2026_manifest.tsv", root / "ILRDF_upload_2026")
    ruled = set((root / "ILRDF_upload_2026_delete.txt").read_text(encoding="utf-8").split())

    head = api.dataset_info(REPO).sha
    print("dataset head:", head)
    remote = list_remote(api, head)
    pinned = set(list_remote(api, PINNED))
    print(f"files at the pinned revision {PINNED[:12]}: {len(pinned)}")
    plan = make_plan(target, remote, staged, pinned)
    worst = print_plan(plan, remote, target, ruled)
    if plan.problems:
        print(f"STOP: {len(plan.problems)} problems; nothing was changed:")
        for problem in plan.problems[:50]:
            print("  ", problem)
        return 1
    if worst > FOLDER_LIMIT:
        print(f"STOP: some folder would hold {worst} files + subfolders; nothing was changed")
        return 1
    commits = sum(-(-len(x) // BATCH)
                  for x in (plan.stray, plan.copies, plan.uploads, plan.deletes))
    print(f"commits needed: {commits} (at most {BATCH} operations each)")
    if not args.go:
        print("Dry run only. Re-run with --go to do it.")
        return 0

    if commits:
        head = execute(api, plan, head)

    head = api.dataset_info(REPO).sha
    audio = {p for p in list_remote(api, head) if is_audio(p)}
    missing, extra = sorted(target - audio), sorted(audio - target)
    print("new head:", head)
    print("audio files at new head:", len(audio))
    print("missing vs target:", len(missing), missing[:5])
    print("extra vs target:", len(extra), extra[:5])
    if not missing and not extra:
        print(f"DONE. Pin revision {head}, expected_audio_files {len(audio)}")
        return 0
    print("NOT DONE: the file set does not match. Run the same command again; "
          "if it still does not match, paste this output to Claude.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
