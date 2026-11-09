#!/usr/bin/env python3
"""Mirror kanakanavu.info: every same-site HTML page, plus its recordings.

What it does, in order:
  1. Crawls breadth-first from the home page, following every same-site link
     to an HTML page (www. and http:// are folded into https://kanakanavu.info).
     The site has no sitemap and refuses directory listings (/_Media/ is 403),
     so a file no page links to cannot be found.
  2. Saves each page's bytes exactly as served (the site declares iso-8859-1
     and writes non-ASCII as numeric entities); nothing is decoded or cleaned.
  3. Downloads every linked recording (MP3/MP4/...) into the media directory,
     checking the byte count against Content-Length. A file already on disk
     with the server's size is kept, not fetched again.
  4. Writes, sorted by URL so a rerun on an unchanged site diffs empty:
       <out>/manifest.tsv               one row per file saved
       <out>/links_not_downloaded.tsv   every other link seen, with the reason
       <out>/last_refresh.txt           date and counts of this run

Images and site-design files (CSS/JS/Flash players) are deliberately not
downloaded (setup choice, 2026-11-06: HTML, MP3 and MP4 only); they are listed
in links_not_downloaded.tsv. A same-site link of a type this script does not
know makes it exit 3, so new kinds of content are never skipped silently.

TLS: the server presents a certificate for *.checkdomain.de, not for
kanakanavu.info, so verification is turned off for this host only.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import hashlib
import sys
import time
import urllib.parse
import warnings
from pathlib import Path

import requests
import urllib3
from bs4 import BeautifulSoup

START = "https://kanakanavu.info/"
SITE_HOSTS = {"kanakanavu.info", "www.kanakanavu.info"}
USER_AGENT = "FormosanBank corpus scraper (research use, with the site owner's permission)"

HTML_EXT = {"html", "htm", ""}                      # "" = directory URL (…/)
MEDIA_EXT = {"mp3", "mp4", "wav", "m4a", "m4v", "ogg", "flv", "mov", "aif", "aiff"}
DOC_EXT = {"pdf", "txt", "rtf", "doc", "docx", "xml", "eaf", "csv", "xls", "xlsx", "zip"}
# Single files fetched despite their type (path -> why). The site's gloss
# index is an image in the Language Documentation sidebar; maintainer, round 1
# (2026-11-06): add it.
WANTED = {"/_Media/pastedgraphic-36_med_hr.png": "gloss index (sidebar image, Language Documentation page)"}
NOT_DOWNLOADED = {                                  # ext -> reason
    **{e: "image (not selected for download)" for e in ("jpeg", "jpg", "png", "gif", "ico", "svg")},
    **{e: "site design file (not selected for download)" for e in ("css", "js", "swf")},
}


def ext_of(path: str) -> str:
    last = path.rsplit("/", 1)[-1]
    return last.rsplit(".", 1)[-1].lower() if "." in last else ""


def canonical(url: str) -> str | None:
    """Same-site URL -> one canonical https form; other sites -> None."""
    p = urllib.parse.urlparse(url)
    if p.scheme not in ("http", "https") or p.hostname not in SITE_HOSTS:
        return None
    path = p.path or "/"
    if path.endswith("/index.html"):                # …/x/index.html is …/x/
        path = path[: -len("index.html")]
    return urllib.parse.urlunparse(("https", "kanakanavu.info", path, "", p.query, ""))


def links_in(page_url: str, html: bytes) -> list[str]:
    """Every URL a page refers to: href/src/data/poster, plus Flash flashvars."""
    soup = BeautifulSoup(html, "lxml")
    raw: list[str] = []
    for tag in soup.find_all(True):
        for attr in ("href", "src", "data", "poster"):
            value = tag.get(attr)
            if isinstance(value, str):
                raw.append(value)
        if tag.name == "param" and tag.get("name") == "flashvars":
            for pair in str(tag.get("value", "")).split("&"):
                _, _, value = pair.partition("=")
                if "." in value and " " not in value:
                    raw.append(value)
    out = []
    for value in raw:
        value = value.strip()
        if not value or value.startswith(("#", "mailto:", "javascript:", "tel:", "data:")):
            continue
        out.append(urllib.parse.urljoin(page_url, value).split("#", 1)[0])
    return out


def local_html_path(out: Path, url: str) -> Path:
    path = urllib.parse.urlparse(url).path
    if path.endswith("/"):
        path += "index.html"
    return out / "html" / path.lstrip("/")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def get(session: requests.Session, url: str, **kw) -> requests.Response:
    """GET with three tries; raises on the last failure."""
    for attempt in range(3):
        try:
            return session.get(url, timeout=60, **kw)
        except requests.RequestException as exc:
            if attempt == 2:
                raise
            print(f"  retry {attempt + 1} after {type(exc).__name__}: {url}", file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    raise AssertionError("unreachable")


def download(session: requests.Session, url: str, dest: Path) -> tuple[requests.Response, str]:
    """Stream url to dest unless dest already has the server's byte count."""
    head = session.head(url, timeout=60, allow_redirects=True)
    head.raise_for_status()
    expected = int(head.headers["Content-Length"])
    if dest.exists() and dest.stat().st_size == expected:
        return head, "kept (already on disk, size matches server)"
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    with get(session, url, stream=True) as resp:
        resp.raise_for_status()
        with part.open("wb") as handle:
            for block in resp.iter_content(1 << 20):
                handle.write(block)
    got = part.stat().st_size
    if got != expected:
        raise RuntimeError(f"{url}: got {got} bytes, server said {expected}")
    part.replace(dest)
    return head, "downloaded"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True, help="where HTML, documents and the manifests go (committed)")
    ap.add_argument("--media-dir", type=Path, required=True, help="where recordings go (gitignored)")
    ap.add_argument("--root", type=Path, required=True, help="corpus root; manifest paths are relative to it")
    ap.add_argument("--delay", type=float, default=0.5, help="seconds between requests")
    args = ap.parse_args()
    out, media_dir, root = args.out.resolve(), args.media_dir.resolve(), args.root.resolve()

    print("TLS verification is OFF for kanakanavu.info "
          "(it serves a *.checkdomain.de certificate).")
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    warnings.filterwarnings("ignore", message=".*doesn't match a supported version.*")
    session = requests.Session()
    session.verify = False
    session.headers["User-Agent"] = USER_AGENT

    referenced_from: dict[str, set[str]] = collections.defaultdict(set)
    pages: dict[str, requests.Response] = {}
    other: set[str] = set()                         # non-HTML targets, canonical or external
    queue, seen = [START], {START}
    errors: list[str] = []

    # 1-2. Crawl and save pages.
    while queue:
        url = queue.pop(0)
        resp = get(session, url)
        time.sleep(args.delay)
        print(f"{resp.status_code}  {len(resp.content):>8}  {url}")
        if resp.status_code != 200:
            errors.append(f"HTTP {resp.status_code}: {url}")
            continue
        pages[url] = resp
        dest = local_html_path(out, url)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(resp.content)
        for link in links_in(url, resp.content):
            target = canonical(link) or link
            referenced_from[target].add(url)
            if canonical(link) and ext_of(urllib.parse.urlparse(target).path) in HTML_EXT:
                if target not in seen:
                    seen.add(target)
                    queue.append(target)
            else:
                other.add(target)

    # 3. Recordings and documents; everything else is listed with a reason.
    manifest_rows, skipped_rows, unknown = [], [], []
    for url, resp in pages.items():
        dest = local_html_path(out, url)
        manifest_rows.append(("html", url, dest.relative_to(root), resp, "downloaded"))
    for url in sorted(other):
        if canonical(url) is None:
            skipped_rows.append((url, "external", "not on kanakanavu.info"))
            continue
        path = urllib.parse.urlparse(url).path
        ext = ext_of(path)
        name = urllib.parse.unquote(path.rsplit("/", 1)[-1])
        if ext in MEDIA_EXT or ext in DOC_EXT or path in WANTED:
            kind, dest = ("media", media_dir / name) if ext in MEDIA_EXT else ("document", out / "files" / name)
            try:
                resp, how = download(session, url, dest)
            except Exception as exc:                # noqa: BLE001 — reported, then exit 1
                errors.append(f"{url}: {exc}")
                print(f"FAILED  {url}: {exc}")
                continue
            time.sleep(args.delay)
            print(f"{how:<45}  {dest.stat().st_size:>10}  {url}")
            manifest_rows.append((kind, url, dest.relative_to(root), resp, how))
        elif ext in NOT_DOWNLOADED:
            skipped_rows.append((url, ext, NOT_DOWNLOADED[ext]))
        else:
            unknown.append(url)
            skipped_rows.append((url, ext or "(none)", "UNRECOGNISED TYPE: review and extend scrape_site.py"))

    # 4. Manifests.
    with (out / "manifest.tsv").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("kind\turl\tlocal_path\tbytes\tsha256\tcontent_type\tlast_modified\tetag\treferenced_from\n")
        for kind, url, rel, resp, _ in sorted(manifest_rows, key=lambda r: r[1]):
            local = root / rel
            handle.write("\t".join([
                kind, url, str(rel), str(local.stat().st_size), sha256_of(local),
                resp.headers.get("Content-Type", ""), resp.headers.get("Last-Modified", ""),
                resp.headers.get("ETag", "").strip('"'), ";".join(sorted(referenced_from.get(url, ()))),
            ]) + "\n")
    with (out / "links_not_downloaded.tsv").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("url\ttype\treason\treferenced_from\n")
        for url, ext, reason in sorted(skipped_rows):
            handle.write(f"{url}\t{ext}\t{reason}\t{';'.join(sorted(referenced_from.get(url, ())))}\n")

    counts = collections.Counter(r[0] for r in manifest_rows)
    summary = (f"refreshed {datetime.date.today().isoformat()} from {START}\n"
               f"html pages: {counts['html']}\nmedia files: {counts['media']}\n"
               f"documents: {counts['document']}\nlinks not downloaded: {len(skipped_rows)}\n"
               f"errors: {len(errors)}\nunrecognised same-site links: {len(unknown)}\n")
    (out / "last_refresh.txt").write_text(summary, encoding="utf-8")
    print("\n" + summary, end="")
    for line in errors:
        print("ERROR  " + line, file=sys.stderr)
    for url in unknown:
        print("UNRECOGNISED  " + url, file=sys.stderr)
    if errors:
        return 1
    return 3 if unknown else 0


if __name__ == "__main__":
    sys.exit(main())
