#!/usr/bin/env python3
"""SessionStart hook: install .githooks/commit-msg into this repo's hooks folder.

The repo's hooks folder (core.hooksPath, or <git-common-dir>/hooks) also holds
Git LFS's hooks, so the guard is copied in beside them rather than redirecting
core.hooksPath. Worktrees share the common hooks folder, so one install covers
them all. Runs every session, so a fresh container gets it too. Never blocks.
"""
import filecmp
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True).stdout.strip()


def main() -> int:
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd()).resolve()
    source = root / ".githooks" / "commit-msg"
    if not source.is_file():
        return 0
    hooks = git("config", "--get", "core.hooksPath", cwd=root)
    if hooks:
        hooks_dir = Path(hooks) if Path(hooks).is_absolute() else root / hooks
    else:
        common = git("rev-parse", "--git-common-dir", cwd=root)
        if not common:
            return 0
        common_path = Path(common) if Path(common).is_absolute() else root / common
        hooks_dir = common_path / "hooks"
    target = hooks_dir / "commit-msg"
    try:
        hooks_dir.mkdir(parents=True, exist_ok=True)
        if target.exists() and filecmp.cmp(source, target, shallow=False):
            return 0
        if target.exists():
            shutil.copy2(target, target.with_name("commit-msg.before-guard"))
        shutil.copy2(source, target)
        target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"Installed the shared-change commit guard at {target}", file=sys.stderr)
    except OSError as error:
        print(f"Could not install the commit guard: {error}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
