"""Upload a corpus's audio folder to HuggingFace dataset repo(s).

Works for corpora under FormosanBank/Corpora/<Name>/ and for per-corpus dev
repos. The target is recorded in .hf_dataset.yaml at the corpus root so future
runs don't re-prompt. Two layouts are supported:

  # Single dataset (one repo for the whole Audio/ tree):
  repo: FormosanBank/YutasWilang

  # Per-subdir datasets (one repo per top-level subdir — e.g. per language).
  # Each immediate subdir of the audio folder is uploaded to its own repo:
  repo_template: FormosanBank/ILRDF_Dict_{group}
  split_by: subdir
  audio_dir: Final_audio        # optional; default "Audio"

`{group}` is substituted with each subdir name (e.g. Amis -> ILRDF_Dict_Amis).
`audio_dir` (or --audio-dir) overrides the default "Audio" folder name, so the
tool also runs against a dev repo's Final_audio/ before porting.

If .hf_dataset.yaml is missing, the user is asked to select an existing
FormosanBank dataset or create a new one (single-dataset mode); the choice is
written back. Split mode must be configured by writing .hf_dataset.yaml.

Default mode is an incremental upload (new/changed files only, never deletes).
With --sync, also removes remote files not present locally so each remote
matches its local folder exactly.
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
DEFAULT_AUDIO_DIR = "Audio"
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
        description="Upload a corpus's audio folder to HuggingFace dataset repo(s).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "The target is read from .hf_dataset.yaml at the corpus root\n"
            "(single dataset via 'repo:', or per-subdir via 'repo_template:' +\n"
            "'split_by: subdir'). If absent, you'll be prompted to set up a\n"
            "single dataset."
        ),
    )
    p.add_argument("--path", default=".",
                   help="Corpus root directory (contains the audio folder). Default: cwd.")
    p.add_argument("--audio-dir", default=None,
                   help=f"Audio folder name under --path. Overrides the .hf_dataset.yaml "
                        f"'audio_dir' and the default '{DEFAULT_AUDIO_DIR}'.")
    p.add_argument("--sync", action="store_true",
                   help="Also delete remote files not present locally. Default never deletes.")
    p.add_argument("--dry-run", action="store_true",
                   help="Show what would happen; make no remote changes.")
    p.add_argument("--yes", action="store_true",
                   help="Skip confirmation prompts (for unattended runs).")
    p.add_argument("--num-workers", type=int, default=1,
                   help="Parallelism for hf upload-large-folder. Default 1 for reliability.")
    return p.parse_args()


def die(msg, code=1) -> NoReturn:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)


def info(msg):
    print(msg, file=sys.stderr)


def read_config(root):
    """Parse .hf_dataset.yaml into a config dict, or None if absent.

    Returns {mode: 'single', repo, audio_dir} or
            {mode: 'split', repo_template, audio_dir}.
    """
    f = root / HIDDEN_FILE
    if not f.is_file():
        return None
    try:
        data = yaml.safe_load(f.read_text()) or {}
    except yaml.YAMLError as e:
        die(f"{f} is malformed: {e}")
    audio_dir = data.get("audio_dir")
    if "repo_template" in data or data.get("split_by"):
        tmpl = data.get("repo_template")
        if not isinstance(tmpl, str) or "{group}" not in tmpl:
            die(f"{f}: 'repo_template' must be a string containing '{{group}}' "
                f"(e.g. 'FormosanBank/ILRDF_Dict_{{group}}').")
        if data.get("split_by") != "subdir":
            die(f"{f}: 'split_by' must be 'subdir' for per-subdir datasets.")
        return {"mode": "split", "repo_template": tmpl, "audio_dir": audio_dir}
    repo = data.get("repo")
    if not isinstance(repo, str) or "/" not in repo:
        die(f"{f}: need either 'repo: org/name' or 'repo_template:' + 'split_by: subdir'.")
    return {"mode": "single", "repo": repo, "audio_dir": audio_dir}


def write_single_repo(root, repo_id):
    (root / HIDDEN_FILE).write_text(yaml.safe_dump({"repo": repo_id}, sort_keys=False))
    info(f"Wrote {root / HIDDEN_FILE}")


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
    info(f"Repo {repo_id} does not exist on HuggingFace.")
    if dry_run:
        die(f"Cannot proceed in dry-run mode when {repo_id} doesn't exist.")
    if not confirm(f"Create {repo_id} now?", assume_yes=assume_yes):
        sys.exit(1)
    api.create_repo(repo_id, repo_type="dataset", exist_ok=False)
    info(f"Created {repo_id}")


def local_file_set(folder):
    out = set()
    for p in folder.rglob("*"):
        if p.is_file() and p.name != ".DS_Store":
            out.add(str(p.relative_to(folder)).replace(os.sep, "/"))
    return out


def sync_deletions(api, repo_id, folder, dry_run, assume_yes):
    info(f"Listing remote files in {repo_id}...")
    remote = set(api.list_repo_files(repo_id, repo_type="dataset")) - HUB_MANAGED_FILES
    local = local_file_set(folder)
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


def upload(repo_id, folder, num_workers, dry_run):
    cmd = [
        "hf", "upload-large-folder", repo_id, str(folder),
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


def push_one(api, repo_id, folder, args):
    """Ensure a repo exists, optionally sync deletions, and upload one folder."""
    ensure_repo_exists(api, repo_id, dry_run=args.dry_run, assume_yes=args.yes)
    if args.sync:
        sync_deletions(api, repo_id, folder, dry_run=args.dry_run, assume_yes=args.yes)
    upload(repo_id, folder, args.num_workers, dry_run=args.dry_run)


def check_hf_cli():
    from shutil import which
    if which("hf") is None:
        die("'hf' command not found. Install with: pip install 'huggingface_hub[cli]'")


def subdir_groups(audio_dir):
    return sorted(d.name for d in audio_dir.iterdir() if d.is_dir())


def count_files(folder):
    return sum(1 for p in folder.rglob("*") if p.is_file() and p.name != ".DS_Store")


def main():
    args = parse_args()
    check_hf_cli()

    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        die(f"--path {root} is not a directory")
    config = read_config(root)

    audio_name = args.audio_dir or (config or {}).get("audio_dir") or DEFAULT_AUDIO_DIR
    audio_dir = root / audio_name
    if not audio_dir.is_dir():
        die(f"No '{audio_name}/' directory found at {root} "
            f"(set 'audio_dir' in {HIDDEN_FILE} or pass --audio-dir).")

    api = HfApi()
    try:
        api.whoami()
    except Exception as e:
        die(f"Not authenticated to HuggingFace ({e.__class__.__name__}: {e}). "
            f"Run 'hf auth login'.")

    # No config yet → interactive single-dataset setup (split must be hand-written).
    if config is None:
        repo_id = select_or_create_repo(api, default_name=root.name,
                                        assume_yes=args.yes, dry_run=args.dry_run)
        write_single_repo(root, repo_id)
        config = {"mode": "single", "repo": repo_id}

    mode = "sync" if args.sync else "incremental upload"
    if args.dry_run:
        mode += " (dry-run)"
    info(f"Corpus root: {root}")
    info(f"Audio dir  : {audio_dir}")
    info(f"Mode       : {mode}")

    if config["mode"] == "single":
        repo_id = config["repo"]
        info(f"Target     : {repo_id} ({count_files(audio_dir)} files)")
        push_one(api, repo_id, audio_dir, args)
        if not args.dry_run:
            print(f"https://huggingface.co/datasets/{repo_id}")
        return

    # split mode: one dataset per immediate subdir
    tmpl = config["repo_template"]
    groups = subdir_groups(audio_dir)
    if not groups:
        die(f"split_by subdir, but {audio_dir} has no subdirectories to upload.")
    info(f"Target     : {tmpl} — {len(groups)} datasets (one per subdir)")
    for g in groups:
        repo_id = tmpl.format(group=g)
        gdir = audio_dir / g
        info(f"\n=== {g} → {repo_id} ({count_files(gdir)} files) ===")
        push_one(api, repo_id, gdir, args)
    if not args.dry_run:
        print(f"Uploaded {len(groups)} datasets: " + ", ".join(tmpl.format(group=g) for g in groups))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(130)
