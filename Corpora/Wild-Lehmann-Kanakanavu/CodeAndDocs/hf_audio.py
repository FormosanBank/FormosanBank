#!/usr/bin/env python3
"""hf_audio.py -- this corpus's audio on Hugging Face: stage, create (private), check.

The upload itself is the bank's QC/utilities/upload_to_hf.py; this script does
the corpus-specific parts around it (upload_audio_to_hf.sh runs them in order):

  stage   Build Audio_hf/<Language>/<file> from Audio/, holding exactly the
          files the XML's <AUDIO file=...> elements name (hard links, so no
          extra disk space). <Language> is the folder under XML/ (Kanakanavu),
          which is the bank's `language_file` layout (as WilangYutasVideos,
          Whitehorn_Collection, TangRecordingsOfTaroko). Audio/ also holds the
          site's .mp4 videos and the .m4a extractions; those are not
          referenced, so they are not staged: the bank enforces exact parity
          between the XML and the dataset (validate_hf_audio.py).
  create  Create the dataset named in .hf_dataset.yaml as PRIVATE if it does not
          exist yet. upload_to_hf.py would create it with the Hub's default
          visibility, and POL-045 says audio for a corpus not yet published in
          FormosanBank/Corpora is not licensed for reuse. Stops if the dataset
          exists and is public.
  check   Compare the dataset with Audio_hf/ (missing / extra files), report
          whether it is private, and print the revision SHA and file count that
          go into audio_sources.json when the corpus is ported.

Needs huggingface_hub and PyYAML (both in FormosanBank's requirements.txt) and,
for create/check, a Hugging Face token with write access to FormosanBank
(`hf auth login`, or HF_TOKEN).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # the corpus root
XML_ROOT = ROOT / "XML"
AUDIO = ROOT / "Audio"
STAGE = ROOT / "Audio_hf"
CONFIG = ROOT / ".hf_dataset.yaml"
HUB_MANAGED = {".gitattributes", "README.md"}


def expected() -> dict[str, str]:
    """Remote path (<Language>/<file>) -> file name, from every <AUDIO file=...> under XML/."""
    out: dict[str, str] = {}
    for xml in sorted(XML_ROOT.rglob("*.xml")):
        lang = xml.relative_to(XML_ROOT).parts[0]
        for el in ET.parse(xml).getroot().iter("AUDIO"):
            name = el.get("file")
            if name:
                out[f"{lang}/{name}"] = name
    if not out:
        sys.exit(f"no <AUDIO file=...> under {XML_ROOT}")
    return out


def repo_id() -> str:
    import yaml
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    repo = data.get("repo")
    if not isinstance(repo, str) or "/" not in repo:
        sys.exit(f"{CONFIG}: need 'repo: FormosanBank/<name>'")
    return repo


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def stage(_args) -> int:
    want = expected()
    if STAGE.exists():
        shutil.rmtree(STAGE)                    # rebuilt from scratch: nothing stale survives
    problems = []
    total = 0
    for remote, name in sorted(want.items()):
        hits = [p for p in AUDIO.rglob(name) if p.is_file()]
        if len(hits) != 1:
            problems.append(f"{name}: {len(hits)} files named so under {AUDIO}")
            continue
        dst = STAGE / remote
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(hits[0], dst)
        except OSError:
            shutil.copy2(hits[0], dst)
        size = dst.stat().st_size
        total += size
        print(f"  {remote:<45} {size / 1e6:8.1f} MB  sha256 {sha256(dst)[:16]}…")
    if problems:
        print("\n".join(["stage: STOPPED, the XML names audio that is not in Audio/ exactly once:"] + problems), file=sys.stderr)
        return 1
    print(f"stage: {len(want)} files, {total / 1e6:.1f} MB, in {STAGE}")
    return 0


def api():
    from huggingface_hub import HfApi
    return HfApi(token=os.environ.get("HF_TOKEN") or None)


def create(args) -> int:
    hf, repo = api(), repo_id()
    if hf.repo_exists(repo, repo_type="dataset"):
        private = hf.dataset_info(repo).private
        print(f"create: {repo} already exists ({'private' if private else 'PUBLIC'})")
        if not private and not args.allow_public:
            print("create: STOPPED. The dataset is public, but this corpus is not yet published in "
                  "FormosanBank (POL-045). Make it private on the Hub, or pass --allow-public once the "
                  "corpus is ported and audio_permissions.json records it.", file=sys.stderr)
            return 1
        return 0
    if args.dry_run:
        print(f"create: would create {repo} as a PRIVATE dataset (dry run)")
        return 0
    hf.create_repo(repo, repo_type="dataset", private=True, exist_ok=False)
    print(f"create: created {repo} (private)")
    return 0


def check(_args) -> int:
    hf, repo = api(), repo_id()
    want = set(expected())
    info = hf.dataset_info(repo)
    remote = set(hf.list_repo_files(repo, repo_type="dataset")) - HUB_MANAGED
    missing, extra = sorted(want - remote), sorted(remote - want)
    print(f"check: {repo} is {'private' if info.private else 'PUBLIC'}; revision {info.sha}")
    print(f"check: the XML names {len(want)} files; the dataset holds {len(remote)}")
    for f in missing:
        print(f"  missing on the Hub: {f}")
    for f in extra:
        print(f"  on the Hub but not named by the XML: {f}")
    if missing or extra:
        return 1
    print(f"check: exact parity. For audio_sources.json at the port: \"revision\": \"{info.sha}\", "
          f"\"expected_audio_files\": {len(want)}, \"path_mode\": \"language_file\"")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stage", help="build Audio_hf/ from Audio/ and the XML")
    c = sub.add_parser("create", help="create the dataset as private if missing")
    c.add_argument("--dry-run", action="store_true")
    c.add_argument("--allow-public", action="store_true", help="accept an existing public dataset (only after the port)")
    sub.add_parser("check", help="compare the dataset with Audio_hf/")
    args = ap.parse_args()
    return {"stage": stage, "create": create, "check": check}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
