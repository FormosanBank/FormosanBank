#!/usr/bin/env python3
"""Download and verify the official open-access Thao Dictionary PDF."""

from __future__ import annotations

import argparse
import hashlib
import json
import ssl
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "CodeAndDocs" / "source-lock.json"
PRIVATE_DIR = ROOT / "Private"
SYSTEM_CA_FILE = Path("/etc/ssl/cert.pem")
SSL_CONTEXT = ssl.create_default_context(
    cafile=str(SYSTEM_CA_FILE) if SYSTEM_CA_FILE.exists() else None
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(path: Path, expected_bytes: int, expected_sha256: str) -> None:
    actual_bytes = path.stat().st_size
    actual_sha256 = sha256(path)
    if actual_bytes != expected_bytes or actual_sha256 != expected_sha256:
        raise ValueError(
            f"source mismatch: bytes={actual_bytes}, sha256={actual_sha256}; "
            f"expected bytes={expected_bytes}, sha256={expected_sha256}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the local source without downloading it",
    )
    args = parser.parse_args()
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    destination = PRIVATE_DIR / lock["pdf_filename"]
    if not destination.exists():
        if args.check:
            print(f"Missing source: {destination}", file=sys.stderr)
            return 1
        PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(
            lock["official_pdf_url"],
            headers={"User-Agent": "FormosanBank-source-fetch/1.0"},
        )
        with urllib.request.urlopen(
            request, timeout=120, context=SSL_CONTEXT
        ) as response:
            destination.write_bytes(response.read())
    verify(destination, lock["pdf_bytes"], lock["pdf_sha256"])
    print(f"Verified {destination}: {lock['pdf_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
