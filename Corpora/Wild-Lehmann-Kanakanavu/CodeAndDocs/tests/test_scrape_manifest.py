"""The committed scrape is what manifest.tsv says it is.

Every manifest row's file exists with the recorded size and SHA-256, and every
saved HTML page is in the manifest. Recordings live in the gitignored Audio/
folder, so their check skips when Audio/ is absent.
"""
import csv
import hashlib
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parent.parent       # CodeAndDocs/
CORPUS = CODE.parent
SOURCE = CODE / "source"
MANIFEST = SOURCE / "manifest.tsv"

needs_scrape = pytest.mark.skipif(not MANIFEST.exists(), reason="no scrape yet (run refresh_source.sh)")


def rows(kind=None):
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        return [r for r in csv.DictReader(handle, delimiter="\t") if kind in (None, r["kind"])]


def check(row):
    path = CORPUS / row["local_path"]
    assert path.exists(), f"missing: {path}"
    assert path.stat().st_size == int(row["bytes"]), f"size differs: {path}"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"], f"sha256 differs: {path}"


@needs_scrape
def test_html_and_documents_match_manifest():
    checked = [r for r in rows() if r["kind"] != "media"]
    assert checked, "manifest lists no pages"
    for row in checked:
        check(row)


@needs_scrape
def test_every_saved_page_is_in_manifest():
    listed = {r["local_path"] for r in rows("html")}
    on_disk = {str(p.relative_to(CORPUS)) for p in (SOURCE / "html").rglob("*") if p.is_file()}
    assert on_disk == listed, f"on disk only: {sorted(on_disk - listed)}; listed only: {sorted(listed - on_disk)}"


@needs_scrape
@pytest.mark.skipif(not (CORPUS / "Audio").is_dir(), reason="Audio/ not downloaded")
def test_media_match_manifest():
    media = rows("media")
    assert media, "manifest lists no recordings"
    for row in media:
        check(row)
