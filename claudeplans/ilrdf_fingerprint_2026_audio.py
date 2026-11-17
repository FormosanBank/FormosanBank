#!/usr/bin/env python3
"""Fingerprint the recordings the ILRDF_Dicts rebuild needs: 132,404 from the 2026 source + 74 of main's (Hugging Face).

Run on the Mac (the container cannot reach ILRDF), from the FormosanBank checkout root:

    python3 claudeplans/ilrdf_fingerprint_2026_audio.py              # download, fingerprint, delete

Downloads each file with curl to a temporary file, records its SHA-256, size and real file type (from its
first bytes, not its name), then deletes it (or, with --keep, moves it to ../ILRDF_audio_2026/<Lang>/, about
16 GB in all). Files that turn out to be WebM are always kept, saved under a .webm name (in ../ILRDF_audio_2026/
with --keep, otherwise ../ILRDF_audio_webm/); they are not converted. Results are appended line by line to
claudeplans/ilrdf-2026-audio-fingerprints.tsv, so the script can be stopped and re-run: it skips files already
recorded. Failed downloads are recorded with status=failed and retried on the next run.

Python standard library + curl only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent            # claudeplans/
LIST = HERE / "ilrdf-2026-audio-list.tsv"         # language, file, url
OUT = HERE / "ilrdf-2026-audio-fingerprints.tsv"
WEBM_DIR = HERE.parent.parent / "ILRDF_audio_webm"  # sibling of the FormosanBank checkout
KEEP_DIR = HERE.parent.parent / "ILRDF_audio_2026"  # with --keep: every downloaded file, <Lang>/<file>
KEEP = False
SIZE_FIRST = False
FIELDS = ["language", "file", "url", "status", "bytes", "sha256", "type"]


def file_type(b: bytes) -> str:
    if not b:
        return "empty"
    if not b.strip(b"\x00"):
        return "all-zero"
    if b[:3] == b"ID3" or (len(b) > 1 and b[0] == 0xFF and (b[1] & 0xE0) == 0xE0):
        return "mp3"
    if b[:4] == b"\x1a\x45\xdf\xa3":
        return "webm" if b"webm" in b[:64] else "matroska"
    if b[:4] == b"RIFF" and b[8:12] == b"WAVE":
        return "wav"
    if b[:4] == b"OggS":
        return "ogg"
    if b[4:8] == b"ftyp":
        return "mp4"
    if b.lstrip()[:1] in (b"<", b"{"):
        return "html-or-json (error page?)"
    return "unknown:" + b[:8].hex()


def done_files() -> set[str]:
    if not OUT.exists():
        return set()
    with OUT.open(encoding="utf-8", newline="") as f:
        return {r["file"] for r in csv.DictReader(f, delimiter="\t") if r["status"] == "ok"}


def remote_size(url: str) -> int | None:
    """File size from the server without downloading: a 1-byte ranged GET, read from Content-Range.
    (ILRDF answers HEAD without Content-Length but gives `content-range: bytes 0-0/<size>`; checked 2026-10-17.)"""
    r = subprocess.run(["curl", "-sL", "--retry", "3", "--max-time", "60", "-r", "0-0", "-D", "-", "-o", os.devnull, url],
                       capture_output=True, text=True, errors="replace")
    total = re.findall(r"(?im)^content-range:\s*bytes\s+\d+-\d+/(\d+)", r.stdout)
    return int(total[-1]) if r.returncode == 0 and total else None

def fetch(row: dict, tmpdir: str) -> dict:
    if SIZE_FIRST and row.get("main_size"):
        size = remote_size(row["url"])
        if size is not None and size == int(row["main_size"]):
            # Same size as main's recording for this sentence: in 26,780 files fetched in full before this mode
            # existed, size equality and byte identity coincided every time (0 exceptions either way).
            return dict(row, status="ok", bytes=size, sha256=row["main_sha256"],
                        type=f"same size as {row['main_file']} (not downloaded; sha256 is main's)")
    tmp = os.path.join(tmpdir, row["file"])
    r = subprocess.run(["curl", "-sfL", "--retry", "4", "--retry-delay", "3", "--max-time", "120",
                        "-o", tmp, row["url"]], capture_output=True)
    if r.returncode != 0 or not os.path.exists(tmp):
        return dict(row, status=f"failed(curl {r.returncode})", bytes="", sha256="", type="")
    data = Path(tmp).read_bytes()
    kind = file_type(data)
    if kind in ("webm", "matroska"):  # kept under its real extension (maintainer ruling 2026-10-17: name, don't convert)
        dest = (KEEP_DIR if KEEP else WEBM_DIR) / row["language"] / (Path(row["file"]).stem + ".webm")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(tmp, dest)
    elif KEEP:
        dest = KEEP_DIR / row["language"] / row["file"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(tmp, dest)
    else:
        os.remove(tmp)
    return dict(row, status="ok", bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), type=kind)


def step1(workers: int, limit: int | None) -> None:
    with LIST.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    done = done_files()
    todo = [r for r in rows if r["file"] not in done][:limit]
    print(f"{len(rows)} files listed, {len(done)} already fingerprinted, {len(todo)} to do now", flush=True)
    new = not OUT.exists()
    lock = threading.Lock()
    counts: dict[str, int] = {}
    began = time.monotonic()
    with OUT.open("a", encoding="utf-8", newline="") as out, tempfile.TemporaryDirectory() as tmpdir:
        w = csv.DictWriter(out, fieldnames=FIELDS, delimiter="\t", extrasaction="ignore")
        if new:
            w.writeheader()
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(fetch, r, tmpdir) for r in todo]
            for n, fut in enumerate(as_completed(futs), 1):
                res = fut.result()
                key = res["type"] or res["status"]
                with lock:
                    w.writerow(res); out.flush()
                    counts[key] = counts.get(key, 0) + 1
                if n % 25 == 0 or n == len(todo):
                    rate = n / max(time.monotonic() - began, 1e-9)
                    left = (len(todo) - n) / rate / 60 if rate else float("inf")
                    print(f"  {n}/{len(todo)}  {rate * 60:.1f} files/min, ~{left:.0f} min left  "
                          f"last: {res['language']} {res['file']}  {dict(sorted(counts.items()))}", flush=True)
    print("Done. By type/status this run:", dict(sorted(counts.items())))
    print(f"Results: {OUT}")
    if any(k in counts for k in ("webm", "matroska")):
        print(f"WebM files saved with a .webm name in {KEEP_DIR if KEEP else WEBM_DIR}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4, help="parallel downloads (default 4)")
    ap.add_argument("--limit", type=int, default=None, help="only do this many (for a trial run)")
    ap.add_argument("--size-first", action="store_true",
                    help="for sentences main already has a recording for: compare sizes first, download only if different")
    ap.add_argument("--keep", action="store_true", help="keep every file in ../ILRDF_audio_2026/ (about 16 GB) for the upload")
    a = ap.parse_args()
    KEEP = a.keep
    SIZE_FIRST = a.size_first
    step1(a.workers, a.limit)
