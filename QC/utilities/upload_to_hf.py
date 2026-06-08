"""Upload a corpus's Audio/ folder to a HuggingFace dataset repo.

Works for corpora under FormosanBank/Corpora/<Name>/ and for per-corpus dev repos.
The target HF repo is recorded in .hf_dataset.yaml at the corpus root so future
runs don't re-prompt. If the file is missing, the user is asked whether to
select an existing FormosanBank dataset or create a new one; either way the
choice is written to .hf_dataset.yaml.

Default mode is an incremental upload (new/changed files only, never deletes).
With --sync, also removes remote files not present locally so the remote
matches the local Audio/ tree exactly.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

import yaml
from huggingface_hub import HfApi
from huggingface_hub.errors import HfHubHTTPError

HIDDEN_FILE = ".hf_dataset.yaml"
AUDIO_DIR_NAME = "Audio"
DEFAULT_ORG = "FormosanBank"
EXCLUDE_PATTERN = "**/.DS_Store"

# Hub-managed files that should never be deleted by --sync, even though they
# aren't present locally. The Hub auto-creates .gitattributes; README.md is
# typically maintained on the dataset page itself.
HUB_MANAGED_FILES = {".gitattributes", "README.md"}

# Reliability knobs inherited from the original upload_hf_datasets.sh.
# The Hub CLI's optional Rust backends (Xet / hf_transfer) can fail on many
# small files with "failed to fill whole buffer". Disabling them forces the
# pure-Python uploader: slower but more reliable.
UPLOAD_ENV = {
    "HF_HUB_DISABLE_XET": "1",
    "HF_HUB_ENABLE_HF_TRANSFER": "0",
}


def parse_args():
    p = argparse.ArgumentParser(
        description="Upload a corpus's Audio/ folder to a HuggingFace dataset repo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "The target repo is read from .hf_dataset.yaml at the corpus root.\n"
            "If absent, you'll be prompted to select an existing FormosanBank\n"
            "dataset or create a new one; the choice is then written to that file."
        ),
    )
    p.add_argument(
        "--path",
        default=".",
        help="Corpus root directory (must contain an Audio/ subfolder). Default: cwd.",
    )
    p.add_argument(
        "--sync",
        action="store_true",
        help="Also delete remote files not present locally. Default mode never deletes.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen; make no remote changes.",
    )
    p.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompts (for unattended runs).",
    )
    p.add_argument(
        "--num-workers",
        type=int,
        default=1,
        help="Parallelism for hf upload-large-folder. Default 1 for reliability.",
    )
    return p.parse_args()


def die(msg, code=1) -> NoReturn:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)


def info(msg):
    print(msg, file=sys.stderr)


def find_corpus_root(path_str):
    root = Path(path_str).expanduser().resolve()
    if not root.is_dir():
        die(f"--path {root} is not a directory")
    audio = root / AUDIO_DIR_NAME
    if not audio.is_dir():
        die(f"No {AUDIO_DIR_NAME}/ directory found at {root}")
    return root, audio


def read_hidden(root):
    f = root / HIDDEN_FILE
    if not f.is_file():
        return None
    try:
        data = yaml.safe_load(f.read_text()) or {}
    except yaml.YAMLError as e:
        die(f"{f} is malformed: {e}")
    repo = data.get("repo")
    if not isinstance(repo, str) or "/" not in repo:
        die(f"{f} missing or invalid 'repo:' field (expected 'org/name')")
    return repo


def write_hidden(root, repo_id):
    f = root / HIDDEN_FILE
    f.write_text(yaml.safe_dump({"repo": repo_id}, sort_keys=False))
    info(f"Wrote {f}")


def prompt(msg, default=None):
    suffix = f" [{default}]" if default else ""
    return input(f"{msg}{suffix}: ").strip() or (default or "")


def confirm(msg, assume_yes):
    if assume_yes:
        return True
    return prompt(f"{msg} [y/N]").lower() in ("y", "yes")


def select_or_create_repo(api, default_name, assume_yes, dry_run):
    if assume_yes:
        die(f"No {HIDDEN_FILE} and --yes was given; cannot prompt interactively. "
            f"Run once without --yes to set up the repo.")
    if dry_run:
        die(f"No {HIDDEN_FILE} and --dry-run was given. Run once without --dry-run "
            f"to select or create the target repo.")
    while True:
        choice = prompt(
            f"No {HIDDEN_FILE} found. (s)elect existing {DEFAULT_ORG} dataset, "
            f"(c)reate new, (q)uit"
        ).lower()
        if choice == "q":
            sys.exit(0)
        if choice == "s":
            repo = select_existing(api)
            if repo:
                return repo
        elif choice == "c":
            repo = create_new(api, default_name)
            if repo:
                return repo
        else:
            info("Please answer s, c, or q.")


def select_existing(api):
    info(f"Fetching datasets under '{DEFAULT_ORG}'...")
    try:
        datasets = sorted(api.list_datasets(author=DEFAULT_ORG), key=lambda d: d.id)
    except HfHubHTTPError as e:
        info(f"Failed to list datasets: {e}")
        return None
    if not datasets:
        info(f"No datasets found under {DEFAULT_ORG}.")
        return None
    for i, d in enumerate(datasets, 1):
        print(f"  {i:3d}. {d.id}")
    raw = prompt("Pick a number (blank to cancel)")
    if not raw:
        return None
    try:
        return datasets[int(raw) - 1].id
    except (ValueError, IndexError):
        info("Invalid selection.")
        return None


def create_new(api, default_name):
    name = prompt(f"New repo name under {DEFAULT_ORG}/", default=default_name)
    if not name:
        return None
    repo_id = f"{DEFAULT_ORG}/{name}"
    if not confirm(f"Create dataset repo '{repo_id}'?", assume_yes=False):
        return None
    try:
        api.create_repo(repo_id, repo_type="dataset", exist_ok=False)
    except HfHubHTTPError as e:
        info(f"Could not create repo: {e}")
        return None
    info(f"Created {repo_id}")
    return repo_id


def ensure_repo_exists(api, repo_id, dry_run, assume_yes):
    if api.repo_exists(repo_id, repo_type="dataset"):
        return
    info(f"Repo {repo_id} does not exist on HuggingFace ({HIDDEN_FILE} may be stale).")
    if dry_run:
        die("Cannot proceed in dry-run mode when the target repo doesn't exist.")
    if not confirm(f"Create {repo_id} now?", assume_yes=assume_yes):
        sys.exit(1)
    api.create_repo(repo_id, repo_type="dataset", exist_ok=False)
    info(f"Created {repo_id}")


def local_file_set(audio_dir):
    out = set()
    for p in audio_dir.rglob("*"):
        if p.is_file() and p.name != ".DS_Store":
            out.add(str(p.relative_to(audio_dir)).replace(os.sep, "/"))
    return out


def sync_deletions(api, repo_id, audio_dir, dry_run, assume_yes):
    info(f"Listing remote files in {repo_id}...")
    remote = set(api.list_repo_files(repo_id, repo_type="dataset")) - HUB_MANAGED_FILES
    local = local_file_set(audio_dir)
    extras = sorted(remote - local)
    if not extras:
        info("--sync: nothing to delete (remote already matches local).")
        return
    print(f"--sync: {len(extras)} file(s) on remote not present locally:")
    for f in extras:
        print(f"  - {f}")
    if dry_run:
        info("(dry-run: not deleting)")
        return
    if not confirm(f"Delete these {len(extras)} file(s) from {repo_id}?", assume_yes=assume_yes):
        die("Aborted by user.")
    api.delete_files(
        repo_id=repo_id,
        repo_type="dataset",
        delete_patterns=extras,
        commit_message=f"Sync: delete {len(extras)} file(s) not present locally",
    )
    info(f"Deleted {len(extras)} file(s).")


def upload(repo_id, audio_dir, num_workers, dry_run):
    cmd = [
        "hf", "upload-large-folder", repo_id, str(audio_dir),
        "--repo-type=dataset",
        "--num-workers", str(num_workers),
        "--exclude", EXCLUDE_PATTERN,
    ]
    info("Running: " + " ".join(cmd))
    if dry_run:
        info("(dry-run: not uploading)")
        return
    env = {**os.environ, **UPLOAD_ENV}
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        die("hf upload-large-folder failed", code=result.returncode)


def check_hf_cli():
    from shutil import which
    if which("hf") is None:
        die("'hf' command not found. Install with: pip install 'huggingface_hub[cli]'")


def main():
    args = parse_args()
    check_hf_cli()
    root, audio_dir = find_corpus_root(args.path)
    api = HfApi()

    try:
        api.whoami()
    except Exception as e:
        die(f"Not authenticated to HuggingFace ({e.__class__.__name__}: {e}). "
            f"Run 'hf auth login'.")

    repo_id = read_hidden(root)
    if repo_id is None:
        repo_id = select_or_create_repo(
            api, default_name=root.name,
            assume_yes=args.yes, dry_run=args.dry_run,
        )
        write_hidden(root, repo_id)
    else:
        info(f"Using repo from {HIDDEN_FILE}: {repo_id}")

    ensure_repo_exists(api, repo_id, dry_run=args.dry_run, assume_yes=args.yes)

    file_count = sum(
        1 for p in audio_dir.rglob("*")
        if p.is_file() and p.name != ".DS_Store"
    )
    mode = "sync" if args.sync else "incremental upload"
    if args.dry_run:
        mode += " (dry-run)"
    info(f"Corpus root: {root}")
    info(f"Audio dir  : {audio_dir} ({file_count} files)")
    info(f"Repo       : {repo_id}")
    info(f"Mode       : {mode}")

    if args.sync:
        sync_deletions(api, repo_id, audio_dir,
                       dry_run=args.dry_run, assume_yes=args.yes)

    upload(repo_id, audio_dir, args.num_workers, dry_run=args.dry_run)

    if not args.dry_run:
        print(f"https://huggingface.co/datasets/{repo_id}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(130)
