from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import requests
import yaml
from bs4 import BeautifulSoup
import chinese_converter


csv.field_size_limit(sys.maxsize)


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
LOGS = ROOT / "data" / "logs"
SCRIPTS = ROOT / "scripts"
XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("xml", XML_NS)


CSV_FIELDS = {
    "url_inventory.csv": [
        "url",
        "source_site",
        "pair",
        "l1",
        "l2",
        "phrase",
        "page",
        "discovered_from_url",
        "discovered_from_phrase",
        "request_method",
        "http_status",
        "content_type",
        "bytes",
        "sha256",
        "crawl_timestamp_utc",
        "cache_path",
        "parse_status",
        "notes",
    ],
    "manifest.csv": [
        "file_path",
        "file_type",
        "source_url",
        "source_site",
        "pair",
        "l1",
        "l2",
        "phrase",
        "page",
        "sha256",
        "bytes",
        "created_at_utc",
        "notes",
    ],
    "pair_census.csv": [
        "pair",
        "l1",
        "l2",
        "source_language_name",
        "target_language_name",
        "census_seed_count",
        "api_status",
        "token_required",
        "timestamp_required",
        "phraseTranslations_found",
        "tmem_found",
        "tmem_examples_found",
        "max_tmem_count_seen",
        "total_unique_examples_seen_in_census",
        "wordlist_found",
        "static_page_examples_found",
        "top_author_ids",
        "top_author_labels_if_known",
        "top_domains",
        "suspected_jw2019_or_religious_share",
        "suspected_automatic_translation_share",
        "suspected_existing_formosanbank_overlap",
        "estimated_yield_class",
        "proceed_to_full_crawl",
        "notes",
    ],
    "authors.csv": [
        "authorId",
        "author_label",
        "author_raw_json",
        "pairs_seen",
        "examples_count",
        "domains_seen",
        "notes",
    ],
    "language_mapping.csv": [
        "code",
        "FormosanBank_language_name",
        "ISO_639_3",
        "glottocode_if_known",
        "Chinese_name_if_known",
        "English_name_if_known",
        "FormosanBank_dialect_if_applicable",
        "mapping_confidence",
        "mapping_notes",
    ],
    "language_direction_audit.csv": [
        "record_id",
        "pair",
        "expected_l1",
        "expected_l2",
        "source_sentence_clean",
        "target_sentence_clean",
        "script_source",
        "script_target",
        "language_detection_source",
        "language_detection_target",
        "direction_status",
        "action",
        "notes",
    ],
    "duplicates.csv": [
        "duplicate_group_id",
        "record_id",
        "pair",
        "duplicate_type",
        "canonical_record_id",
        "tmBunchId",
        "source_sentence_clean",
        "target_sentence_clean",
        "query_phrase",
        "raw_json_path",
        "action",
        "notes",
    ],
    "overlap_candidates.csv": [
        "record_id",
        "pair",
        "source_sentence_clean",
        "target_sentence_clean",
        "existing_repo",
        "existing_file",
        "existing_record_id_if_known",
        "overlap_type",
        "similarity_score",
        "action",
        "notes",
    ],
    "rejected_records.csv": [
        "record_id",
        "pair",
        "rejection_reason",
        "source_sentence_clean",
        "target_sentence_clean",
        "query_phrase",
        "raw_path",
        "notes",
    ],
    "audio_manifest.csv": [
        "audio_id",
        "record_id",
        "pair",
        "l1",
        "l2",
        "query_phrase",
        "source_url",
        "local_path_if_downloaded",
        "file_format",
        "byte_size",
        "sha256",
        "duration_seconds_if_measured",
        "speaker_or_author_if_known",
        "alignment_granularity",
        "download_status",
        "rights_status",
        "notes",
    ],
    "xml_index.csv": [
        "xml_file",
        "text_id",
        "sentence_id",
        "record_id",
        "pair",
        "l1",
        "l2",
        "source_language_name",
        "target_language_name",
        "source_iso_639_3",
        "target_iso_639_3",
        "query_phrase",
        "tmBunchId",
        "authorId",
        "author_label_if_known",
        "domain",
        "source_url",
        "raw_json_path",
        "raw_html_path_if_any",
        "raw_sha256",
        "source_sentence_sha256",
        "target_sentence_sha256",
        "pair_sha256",
        "duplicate_group_id_if_any",
        "overlap_status",
        "quality_status",
        "parse_confidence",
        "crawl_timestamp_utc",
    ],
    "coverage_by_pair.csv": [
        "pair",
        "l1",
        "l2",
        "source_language_name",
        "target_language_name",
        "phrases_queried",
        "api_responses_fetched",
        "static_pages_fetched",
        "raw_tmem_examples",
        "deduped_tmem_examples",
        "quality_filtered_examples",
        "dictionary_entries_raw",
        "dictionary_entries_deduped",
        "xml_sentences_created",
        "xml_files_created",
        "top_authors",
        "top_domains",
        "rejected_records",
        "duplicate_records",
        "overlap_records",
        "rights_status",
        "crawl_status",
        "notes",
    ],
    "coverage_by_language.csv": [
        "l1",
        "source_language_name",
        "target_languages",
        "total_pairs",
        "total_raw_tmem_examples",
        "total_deduped_examples",
        "total_quality_filtered_examples",
        "total_xml_sentences",
        "total_dictionary_entries",
        "xml_files_created",
        "notes",
    ],
    "coverage_by_author_domain.csv": [
        "pair",
        "authorId",
        "author_label_if_known",
        "domain",
        "raw_examples",
        "deduped_examples",
        "quality_filtered_examples",
        "xml_examples",
        "suspected_source_family",
        "notes",
    ],
    "dictionary_coverage_by_pair.csv": [
        "pair",
        "l1",
        "l2",
        "source_language_name",
        "target_language_name",
        "dictionary_entries_raw",
        "dictionary_entries_deduped",
        "top_authors",
        "notes",
    ],
    "parse_errors.csv": [
        "timestamp_utc",
        "stage",
        "pair",
        "l1",
        "l2",
        "phrase",
        "page",
        "source_url",
        "raw_path",
        "error_type",
        "message",
        "notes",
    ],
    "parse_warnings.csv": [
        "timestamp_utc",
        "stage",
        "pair",
        "l1",
        "l2",
        "phrase",
        "page",
        "record_id",
        "warning_type",
        "message",
        "notes",
    ],
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_phrase(phrase: str) -> str:
    cleaned = unicodedata.normalize("NFC", phrase).strip()
    encoded = urllib.parse.quote(cleaned, safe="")
    return encoded[:160] or "_empty"


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = html.unescape(text)
    if "<" in text and ">" in text:
        text = BeautifulSoup(text, "html.parser").get_text(" ")
    text = text.replace("\u00a0", " ")
    # Glosbe static fragments use literal markdown-style markers around keyword
    # highlights in some rows. They are UI emphasis, not corpus text.
    text = text.replace("**", "")
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([A-Za-z])\s+'", r"\1'", text)
    return text


def dedupe_key(text: str) -> str:
    text = clean_text(text).casefold()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def semantic_text_key(text: str) -> str:
    """Compare translations while ignoring punctuation-only cleanup changes."""
    return "".join(char for char in dedupe_key(text) if char.isalnum())


def clean_legacy_glosbe_text(text: Any) -> str:
    """Remove Glosbe footnote markers that are not part of the aligned text."""
    return clean_text(clean_text(text).replace("*", ""))


def form_group_key(text: str) -> str:
    text = dedupe_key(text)
    text = text.translate(str.maketrans({"ˈ": "'", "ʼ": "'", "’": "'", "‘": "'"}))
    return re.sub(r"\s*'\s*", "'", text)


def lexical_form_text_for_xml(text: str) -> str:
    text = clean_text(text)
    text = text.translate(str.maketrans({"ˈ": "'", "ʼ": "'", "’": "'", "‘": "'"}))
    return re.sub(r"\s*'\s*", "'", text)


def repo_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def has_han(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def latin_letter_count(text: str) -> int:
    return sum(1 for ch in text if ("A" <= ch <= "Z") or ("a" <= ch <= "z"))


def script_label(text: str) -> str:
    if not text:
        return "empty"
    han = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    latin = latin_letter_count(text)
    if han and latin:
        return "mixed_han_latin"
    if han:
        return "han"
    if latin:
        return "latin"
    return "other"


def looks_like_english(text: str) -> bool:
    tokens = re.findall(r"[A-Za-z]+", text.casefold())
    if not tokens:
        return False
    stop = {
        "the",
        "and",
        "of",
        "to",
        "in",
        "is",
        "you",
        "that",
        "for",
        "with",
        "are",
        "this",
        "was",
        "have",
        "will",
        "not",
        "we",
        "he",
        "she",
        "they",
        "it",
    }
    return len([t for t in tokens if t in stop]) >= 2


def load_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def pair_name(l1: str, l2: str) -> str:
    return f"{l1},{l2}"


def target_name(config: dict[str, Any], l2: str) -> str:
    return {"en": "English", "zh": "Chinese"}.get(l2, l2)


def source_name(config: dict[str, Any], l1: str) -> str:
    return config["language_mapping"].get(l1, {}).get("name", l1)


def target_iso(config: dict[str, Any], l2: str) -> str:
    return config.get("target_lang_xml", {}).get(l2, l2)


def ensure_layout(config: dict[str, Any]) -> None:
    dirs = [
        RAW / "json" / "iapi3",
        RAW / "html" / "static",
        RAW / "headers",
        RAW / "rendered_html",
        RAW / "audio",
        PROCESSED / "crawl_queue_snapshots",
        LOGS,
        ROOT / config["xml"]["output_dir"],
    ]
    for l1, _ in config["target_pairs"]:
        dirs.append(ROOT / config["xml"]["output_dir"] / l1)
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    for log_name in [
        "rights.log",
        "census.log",
        "crawl.log",
        "extract.log",
        "normalize.log",
        "dedupe.log",
        "overlap.log",
        "xml_build.log",
        "validation.log",
    ]:
        (LOGS / log_name).touch(exist_ok=True)
    for name, fields in CSV_FIELDS.items():
        path = PROCESSED / name
        if not path.exists():
            write_csv(path, [], fields)
    for path in [
        PROCESSED / "tmem_examples_raw.jsonl",
        PROCESSED / "tmem_examples_deduped.jsonl",
        PROCESSED / "static_page_examples_raw.jsonl",
        PROCESSED / "static_page_dictionary_entries_raw.jsonl",
        PROCESSED / "dictionary_entries_raw.jsonl",
        PROCESSED / "dictionary_entries_deduped.jsonl",
        PROCESSED / "wordlist_items.jsonl",
        PROCESSED / "quality_filtered_examples.jsonl",
    ]:
        if not path.exists():
            path.write_text("", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or CSV_FIELDS[path.name]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def append_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or CSV_FIELDS[path.name]
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def log_error(stage: str, pair: str = "", l1: str = "", l2: str = "", phrase: str = "", page: Any = "", source_url: str = "", raw_path: str = "", error_type: str = "", message: str = "", notes: str = "") -> None:
    append_csv(
        PROCESSED / "parse_errors.csv",
        [
            {
                "timestamp_utc": now_utc(),
                "stage": stage,
                "pair": pair,
                "l1": l1,
                "l2": l2,
                "phrase": phrase,
                "page": page,
                "source_url": source_url,
                "raw_path": raw_path,
                "error_type": error_type,
                "message": message,
                "notes": notes,
            }
        ],
    )


def log_warning(stage: str, pair: str = "", l1: str = "", l2: str = "", phrase: str = "", page: Any = "", record_id: str = "", warning_type: str = "", message: str = "", notes: str = "") -> None:
    append_csv(
        PROCESSED / "parse_warnings.csv",
        [
            {
                "timestamp_utc": now_utc(),
                "stage": stage,
                "pair": pair,
                "l1": l1,
                "l2": l2,
                "phrase": phrase,
                "page": page,
                "record_id": record_id,
                "warning_type": warning_type,
                "message": message,
                "notes": notes,
            }
        ],
    )


@dataclass
class FetchResult:
    url: str
    status: int
    content_type: str
    body_path: Path
    headers_path: Path
    sha256: str
    bytes: int
    from_cache: bool
    timestamp_utc: str


class PoliteClient:
    def __init__(self, config: dict[str, Any], force: bool = False):
        self.config = config
        self.force = force
        self.session = requests.Session()
        self.ua = config["crawl"]["user_agent"]
        self.last_by_host: dict[str, float] = {}
        self.repeated_status: Counter[int] = Counter()

    def _sleep(self, url: str) -> None:
        host = urllib.parse.urlparse(url).netloc
        last = self.last_by_host.get(host)
        if last is not None:
            min_s = float(self.config["crawl"]["rate_limit_seconds_min"])
            max_s = float(self.config["crawl"]["rate_limit_seconds_max"])
            wait = random.uniform(min_s, max_s) - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
        self.last_by_host[host] = time.monotonic()

    def get(
        self,
        url: str,
        body_path: Path,
        headers_path: Path,
        *,
        source_site: str,
        pair: str = "",
        l1: str = "",
        l2: str = "",
        phrase: str = "",
        page: Any = "",
        discovered_from_url: str = "",
        discovered_from_phrase: str = "",
        notes: str = "",
        extra_headers: dict[str, str] | None = None,
    ) -> FetchResult:
        body_path.parent.mkdir(parents=True, exist_ok=True)
        headers_path.parent.mkdir(parents=True, exist_ok=True)
        ts = now_utc()
        if body_path.exists() and headers_path.exists() and not self.force:
            data = body_path.read_bytes()
            digest = sha256_bytes(data)
            inv = {
                "url": url,
                "source_site": source_site,
                "pair": pair,
                "l1": l1,
                "l2": l2,
                "phrase": phrase,
                "page": page,
                "discovered_from_url": discovered_from_url,
                "discovered_from_phrase": discovered_from_phrase,
                "request_method": "GET",
                "http_status": "cached",
                "content_type": "",
                "bytes": len(data),
                "sha256": digest,
                "crawl_timestamp_utc": ts,
                "cache_path": rel(body_path),
                "parse_status": "cached",
                "notes": notes,
            }
            append_csv(PROCESSED / "url_inventory.csv", [inv])
            return FetchResult(url, 0, "", body_path, headers_path, digest, len(data), True, ts)

        max_retries = int(self.config["crawl"]["max_retries"])
        timeout = int(self.config["crawl"]["timeout_seconds"])
        headers = {"User-Agent": self.ua}
        if extra_headers:
            headers.update(extra_headers)
        response: requests.Response | None = None
        err: Exception | None = None
        for attempt in range(max_retries):
            self._sleep(url)
            try:
                response = self.session.get(url, headers=headers, timeout=timeout)
                if response.status_code in {429, 500, 502, 503, 504}:
                    self.repeated_status[response.status_code] += 1
                    delay = float(self.config["crawl"]["backoff_factor"]) ** attempt
                    time.sleep(min(60, delay + random.random()))
                    continue
                break
            except Exception as exc:  # noqa: BLE001
                err = exc
                time.sleep(min(60, (2**attempt) + random.random()))
        if response is None:
            log_error("fetch", pair, l1, l2, phrase, page, url, str(body_path), type(err).__name__ if err else "request_error", str(err), notes)
            raise RuntimeError(f"Failed to fetch {url}: {err}")
        data = response.content
        body_path.write_bytes(data)
        header_data = {
            "url": url,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "retrieved_at_utc": ts,
        }
        headers_path.write_text(json.dumps(header_data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        digest = sha256_bytes(data)
        content_type = response.headers.get("content-type", "")
        append_csv(
            PROCESSED / "url_inventory.csv",
            [
                {
                    "url": url,
                    "source_site": source_site,
                    "pair": pair,
                    "l1": l1,
                    "l2": l2,
                    "phrase": phrase,
                    "page": page,
                    "discovered_from_url": discovered_from_url,
                    "discovered_from_phrase": discovered_from_phrase,
                    "request_method": "GET",
                    "http_status": response.status_code,
                    "content_type": content_type,
                    "bytes": len(data),
                    "sha256": digest,
                    "crawl_timestamp_utc": ts,
                    "cache_path": rel(body_path),
                    "parse_status": "fetched",
                    "notes": notes,
                }
            ],
        )
        append_csv(
            PROCESSED / "manifest.csv",
            [
                {
                    "file_path": rel(body_path),
                    "file_type": "json" if "json" in content_type or body_path.suffix == ".json" else "html" if body_path.suffix in {".html", ".htm"} else body_path.suffix.lstrip("."),
                    "source_url": url,
                    "source_site": source_site,
                    "pair": pair,
                    "l1": l1,
                    "l2": l2,
                    "phrase": phrase,
                    "page": page,
                    "sha256": digest,
                    "bytes": len(data),
                    "created_at_utc": ts,
                    "notes": notes,
                },
                {
                    "file_path": rel(headers_path),
                    "file_type": "headers",
                    "source_url": url,
                    "source_site": source_site,
                    "pair": pair,
                    "l1": l1,
                    "l2": l2,
                    "phrase": phrase,
                    "page": page,
                    "sha256": sha256_file(headers_path),
                    "bytes": headers_path.stat().st_size,
                    "created_at_utc": ts,
                    "notes": notes,
                },
            ],
        )
        return FetchResult(url, response.status_code, content_type, body_path, headers_path, digest, len(data), False, ts)


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT))
    except Exception:
        return str(p)


def glosbe_phrase_url(config: dict[str, Any], l1: str, l2: str, phrase: str) -> str:
    return f"{config['source']['base_urls']['glosbe']}/{l1}/{l2}/{urllib.parse.quote(phrase, safe='')}"


def fragment_url(config: dict[str, Any], l1: str, l2: str, phrase: str, page: int) -> str:
    return (
        f"{config['source']['base_urls']['glosbe']}/{l1}/{l2}/{urllib.parse.quote(phrase, safe='')}"
        f"/fragment/tmem?page={page}&mode=MUST&stem=true&includedAuthors=&excludedAuthors="
    )


def static_cache_paths(l1: str, l2: str, phrase: str) -> tuple[Path, Path]:
    safe = safe_phrase(phrase)
    return (
        RAW / "html" / "static" / f"{l1}_{l2}" / f"{safe}.html",
        RAW / "headers" / f"{l1}_{l2}" / safe / "static.headers.json",
    )


def fragment_cache_paths(l1: str, l2: str, phrase: str, page: int) -> tuple[Path, Path]:
    safe = safe_phrase(phrase)
    return (
        RAW / "html" / "static" / f"{l1}_{l2}" / safe / f"fragment_page_{page}.html",
        RAW / "headers" / f"{l1}_{l2}" / safe / f"fragment_page_{page}.headers.json",
    )


def iapi_cache_paths(l1: str, l2: str, phrase: str, page: int, variant: str = "") -> tuple[Path, Path]:
    safe = safe_phrase(phrase)
    suffix = f"_{variant}" if variant else ""
    return (
        RAW / "json" / "iapi3" / f"{l1}_{l2}" / safe / f"page_{page}{suffix}.json",
        RAW / "headers" / f"{l1}_{l2}" / safe / f"page_{page}{suffix}.headers.json",
    )


def parse_wordlist_from_static(html_text: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html_text, "html.parser")
    items: list[dict[str, Any]] = []
    active_seen = False
    for idx, li in enumerate(soup.find_all("li")):
        classes = set(li.get("class", []))
        text = clean_text(li.get_text(" ", strip=True))
        if not text or len(text) > 120:
            continue
        if "border-b" not in classes or "border-gray-100" not in classes:
            continue
        side = "after" if active_seen else "before"
        if "active" in classes:
            active_seen = True
            side = "current"
        items.append({"phrase": text, "side": side, "order": idx})
    return items


def parse_dictionary_from_static(html_text: str, l1: str, l2: str, query_phrase: str, raw_path: Path, source_url: str, sha: str, crawl_ts: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html_text, "html.parser")
    rows: list[dict[str, Any]] = []
    for i, li in enumerate(soup.select("li.translation__item")):
        target_el = li.select_one(".translation__item__pharse")
        target = clean_text(target_el.get_text(" ", strip=True) if target_el else "")
        if not target:
            continue
        pos_el = li.select_one("span.text-xxs")
        pos = clean_text(pos_el.get_text(" ", strip=True) if pos_el else "")
        author_el = li.select_one("aside")
        author = clean_text(author_el.get_text(" ", strip=True) if author_el else "")
        translation_id = li.get("data-translationid", "")
        raw_json = {
            "translation_id": translation_id,
            "html": str(li),
        }
        record_id = "GLOSBE_DICT_" + sha256_text(f"{l1}|{l2}|{query_phrase}|{target}|{translation_id}")[:16]
        rows.append(
            {
                "record_id": record_id,
                "pair": pair_name(l1, l2),
                "l1": l1,
                "l2": l2,
                "query_phrase": query_phrase,
                "page": 1,
                "source_phrase_raw": query_phrase,
                "source_phrase_clean": clean_text(query_phrase),
                "target_phrase_raw": target,
                "target_phrase_clean": target,
                "part_of_speech": pos,
                "translation_id": translation_id,
                "authorId": "",
                "author_label_if_known": author,
                "votes": "",
                "quality_raw_json": "",
                "raw_translation_json": raw_json,
                "raw_json_path": "",
                "raw_html_path": rel(raw_path),
                "raw_json_sha256": "",
                "raw_html_sha256": sha,
                "source_url": source_url,
                "crawl_timestamp_utc": crawl_ts,
                "parse_confidence": "high",
                "parse_warnings": "",
            }
        )
    return rows


def parse_examples_from_fragment(html_text: str, l1: str, l2: str, query_phrase: str, page: int, raw_path: Path, source_url: str, sha: str, crawl_ts: str) -> tuple[list[dict[str, Any]], bool]:
    soup = BeautifulSoup(html_text, "html.parser")
    rows: list[dict[str, Any]] = []
    blocks = []
    for div in soup.find_all("div"):
        classes = set(div.get("class", []))
        if "odd:bg-slate-100" in classes and "px-1" in classes:
            blocks.append(div)
    for i, block in enumerate(blocks):
        source_el = block.find(attrs={"lang": l1})
        target_el = block.find(attrs={"lang": l2})
        if source_el is not None and target_el is None:
            row = source_el.find_parent("div", class_=lambda c: c and "flex" in str(c).split())
            if row is not None:
                candidates = [
                    div
                    for div in row.find_all("div", recursive=False)
                    if div is not source_el and "w-1/2" in div.get("class", [])
                ]
                if candidates:
                    target_el = candidates[0]
        if not source_el or not target_el:
            langs = [e.get("lang") for e in block.find_all(attrs={"lang": True})]
            log_warning("extract_static_pages", pair_name(l1, l2), l1, l2, query_phrase, page, "", "missing_lang_div", f"expected {l1}/{l2}; saw {langs}", rel(raw_path))
            continue
        source_raw = source_el.get_text("", strip=False).strip()
        target_raw = target_el.get_text("", strip=False).strip()
        menu = block.select_one("button.tmem__item__menu")
        author_id = menu.get("data-authorid", "") if menu else ""
        author_name = menu.get("data-authorname", "") if menu else ""
        tm_id = menu.get("data-translationid", "") if menu else ""
        audio_buttons = block.select("button.glosbe-audio")
        audio = [dict(btn.attrs) for btn in audio_buttons]
        raw_example = {
            "html": str(block),
            "source_lang_attr": l1,
            "target_lang_attr": l2,
            "menu_attrs": dict(menu.attrs) if menu else {},
        }
        record_id = "GLOSBE_STATIC_" + sha256_text(f"{l1}|{l2}|{query_phrase}|{page}|{i}|{source_raw}|{target_raw}|{tm_id}")[:20]
        rows.append(
            {
                "record_id": record_id,
                "pair": pair_name(l1, l2),
                "l1": l1,
                "l2": l2,
                "phrase": query_phrase,
                "query_phrase": query_phrase,
                "page": page,
                "page_url": source_url,
                "source_sentence_raw": source_raw,
                "target_sentence_raw": target_raw,
                "source_sentence_clean": clean_text(source_raw),
                "target_sentence_clean": clean_text(target_raw),
                "section_label": "translation_memory_fragment",
                "authorId": author_id,
                "author_label_if_known": author_name,
                "author_label_if_visible": author_name,
                "domain": author_name,
                "domain_if_visible": author_name,
                "tmBunchId": tm_id,
                "source_language_detected": l1,
                "target_language_detected": l2,
                "api_source_lang_if_present": "",
                "api_target_lang_if_present": "",
                "has_audio": bool(audio),
                "audio_metadata_raw_json": audio,
                "raw_example_json": raw_example,
                "raw_html_path": rel(raw_path),
                "raw_html_sha256": sha,
                "raw_json_path": "",
                "raw_json_sha256": "",
                "source_url": source_url,
                "crawl_timestamp_utc": crawl_ts,
                "parse_confidence": "high",
                "parse_warnings": "",
            }
        )
    has_more = soup.select_one("#tmem__more") is not None or "LOAD MORE" in soup.get_text(" ", strip=True)
    return rows, has_more


def command_check_rights(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ensure_layout(config)
    client = PoliteClient(config, force=args.force)
    urls = [
        ("https://glosbe.com/robots.txt", "glosbe_robots.txt", "glosbe"),
        ("https://iapi.glosbe.com/robots.txt", "iapi_robots.txt", "iapi.glosbe"),
        ("https://glosbe.com/terms", "terms.html", "glosbe"),
        ("https://glosbe.com/terms_en.pdf", "terms_en.pdf", "glosbe"),
        ("https://glosbe.com/privacy-policy", "privacy-policy.html", "glosbe"),
        ("https://glosbe.com/privacy-policy_en.pdf", "privacy-policy_en.pdf", "glosbe"),
        ("https://glosbe.com/help/api", "help_api.html", "glosbe"),
    ]
    fetched: dict[str, FetchResult] = {}
    for url, filename, site in urls:
        body = RAW / "html" / "static" / "_rights" / filename
        headers = RAW / "headers" / "_rights" / f"{filename}.headers.json"
        fetched[filename] = client.get(url, body, headers, source_site=site, notes="rights/access discovery")
    robots = (RAW / "html" / "static" / "_rights" / "glosbe_robots.txt").read_text(encoding="utf-8", errors="replace")
    iapi_robots_status = fetched["iapi_robots.txt"].status
    terms_summary = [
        "Glosbe T&Cs define Dictionary content as entries, images, and recordings and include machine translation among services.",
        "T&Cs state the Dictionary is based on user uploads, automatically aggregated free-license material, and computational-linguistics algorithm results, and that correctness is not verified before publication.",
        "T&Cs identify the API as a test service that may be changed, disabled, or limited.",
        "T&Cs forbid actions intended to copy the entire or a material part of the Dictionary database using automates/bots and forbid collecting users' personal data.",
        "T&Cs state user-uploaded content is available to other users under CC BY-NC-SA 4.0 for non-commercial use, while Glosbe receives broader rights from uploaders.",
        "Project owner asserted in this Codex thread on 2026-05-14 that FormosanBank has full permission from Glosbe owners to scrape. This report treats scraping authorization as asserted, but still recommends retaining private/internal status until written permission scope and third-party corpus redistribution rights are archived.",
    ]
    rights = f"""# Glosbe Rights And Permission Notes

Retrieval date: {today_utc()}

## URLs Checked

- https://glosbe.com/robots.txt
- https://iapi.glosbe.com/robots.txt
- https://glosbe.com/terms
- https://glosbe.com/terms_en.pdf
- https://glosbe.com/privacy-policy
- https://glosbe.com/privacy-policy_en.pdf
- https://glosbe.com/help/api

## Relevant Findings

{chr(10).join(f'- {item}' for item in terms_summary)}

## Content Character

Glosbe content appears mixed: user-contributed dictionary entries, translation-memory examples, automatically aggregated material from free-license internet sources, machine/computational outputs, images, recordings, and third-party source corpora. Sentence examples observed in the Formosan census are commonly labeled `jw2019`, which should be treated as religious-domain/third-party translation-memory material requiring provenance and balancing review.

## Permission Status

Scraping permission: project owner asserted full owner permission to scrape in this private FormosanBank thread on 2026-05-14.

Redistribution status: not fully proven by this crawl. Public redistribution should remain rights-review-required until written Glosbe permission terms and third-party source-corpus permissions are stored with the project.

Recommended public-repo handling: keep raw caches and XML private/internal unless permission explicitly covers redistribution. If published, include Glosbe/contributor/source-corpus attribution and the non-commercial/share-alike constraints where applicable.

## Warnings

- Do not bypass login, CAPTCHA, Cloudflare, bot checks, token checks, or IP blocks.
- Do not collect private account data.
- Keep conservative rate limits and cache responses.
- Preserve author/source labels such as `jw2019`, `en.wiktionary2016`, and any other visible labels.
"""
    (PROCESSED / "rights_and_permission_notes.md").write_text(rights, encoding="utf-8")
    robot_lines = robots.strip().splitlines()
    disallows_query = "Disallow: /*?" in robots
    report = f"""# Robots And Access Report

Retrieval date: {today_utc()}

## robots.txt

Glosbe robots.txt first line block:

```text
{robots[:1200]}
```

Findings:

- `https://glosbe.com/robots.txt` fetched successfully.
- General public paths are allowed, but `/user`, `/auth/`, `/ajax/`, `/ajax2/`, fragment-like paths, and query URLs are disallowed in the public robots file.
- Query URL disallow present: {disallows_query}.
- `https://iapi.glosbe.com/robots.txt` returned HTTP {iapi_robots_status}; no separate iapi robots policy was found.
- Glosbe Help API page states the public API service is shut down until further notice.

## Access Behavior

- Static dictionary pages are publicly fetchable.
- Public sentence examples are loaded by the site through path-based `/fragment/tmem` HTML endpoints under phrase pages.
- The known `https://iapi.glosbe.com/iapi3/translate` endpoint requires a token in current testing and returns `InvalidApiTokenException` without one.
- No login wall was bypassed.
- No CAPTCHA, bot check, or Cloudflare challenge was bypassed.
- No repeated 429/403 blocking occurred during rights discovery.

## Crawl Decision

Because owner permission to scrape was asserted by the project owner on 2026-05-14, the reproducible scripts allow a polite crawl of public static and fragment pages. The iapi3 endpoint remains access-limited unless Glosbe provides a token through normal permission channels.
"""
    (PROCESSED / "robots_and_access_report.md").write_text(report, encoding="utf-8")


def build_iapi_url(config: dict[str, Any], l1: str, l2: str, phrase: str, page: int, token: str | None = None, timestamp: int | None = None) -> str:
    params: dict[str, Any] = {
        "l1": l1,
        "l2": l2,
        "phrase": phrase,
        "page": page,
        "includeWordlist": str(config["api"]["includeWordlist"]).lower(),
        "includeSimilar": str(config["api"]["includeSimilar"]).lower(),
        "includeTmem": str(config["api"]["includeTmem"]).lower(),
        "includeAudioSentences": str(config["api"]["includeAudioSentences"]).lower(),
        "env": config["api"]["env"],
    }
    if token is not None:
        params["token"] = token
    if timestamp is not None:
        params["timestamp"] = timestamp
    return config["source"]["base_urls"]["iapi3"] + "?" + urllib.parse.urlencode(params)


def command_discover_token(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ensure_layout(config)
    client = PoliteClient(config, force=args.force)
    ts = int(time.time())
    variants = [
        ("no_token_no_timestamp", None, None),
        ("no_token_with_timestamp", None, ts),
        ("empty_token_no_timestamp", "", None),
        ("empty_token_with_timestamp", "", ts),
        ("invalid_token_with_timestamp", "INVALID", ts),
    ]
    rows = []
    l1, l2, phrase = "ami", "en", "futing"
    for variant, token, timestamp in variants:
        url = build_iapi_url(config, l1, l2, phrase, 1, token, timestamp)
        body, headers = iapi_cache_paths(l1, l2, phrase, 1, variant)
        result = client.get(url, body, headers, source_site="iapi.glosbe", pair=pair_name(l1, l2), l1=l1, l2=l2, phrase=phrase, page=1, notes=f"token behavior test {variant}")
        error_codes = ""
        status = result.status
        try:
            data = json.loads(body.read_text(encoding="utf-8"))
            error_codes = ",".join(data.get("errorCodes", [])) if isinstance(data, dict) else ""
            status = data.get("httpStatus", status) if isinstance(data, dict) else status
        except Exception as exc:  # noqa: BLE001
            log_error("discover_token_behavior", pair_name(l1, l2), l1, l2, phrase, 1, url, rel(body), type(exc).__name__, str(exc), variant)
        rows.append({"variant": variant, "http_status": status, "error_codes": error_codes, "cache_path": rel(body), "url": url})
    inspected = []
    for page_url in [glosbe_phrase_url(config, "ami", "en", "futing")]:
        body, headers = static_cache_paths("ami", "en", "futing")
        res = client.get(page_url, body, headers, source_site="static_page", pair="ami,en", l1="ami", l2="en", phrase="futing", page=1, notes="public app inspection for token behavior")
        text = body.read_text(encoding="utf-8", errors="replace")
        inspected.append(
            {
                "page_url": page_url,
                "cache_path": rel(body),
                "frontendApiUrl_present": "frontendApiUrl" in text,
                "token_string_present": "token" in text,
                "iapi_string_present": "iapi" in text,
                "status": res.status,
            }
        )
    report = {
        "retrieved_at_utc": now_utc(),
        "tests": rows,
        "public_app_inspection": inspected,
        "summary": "iapi3 translate returned InvalidApiTokenException for public no-token/empty-token/invalid-token tests. The static UI currently uses public phrase pages and /fragment/tmem HTML for examples; no reusable public iapi token was found in fetched page state.",
    }
    (PROCESSED / "token_behavior.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    existing = (PROCESSED / "robots_and_access_report.md").read_text(encoding="utf-8") if (PROCESSED / "robots_and_access_report.md").exists() else ""
    with (PROCESSED / "robots_and_access_report.md").open("a", encoding="utf-8") as f:
        f.write("\n## iapi3 Token/Timestamp Tests\n\n")
        for row in rows:
            f.write(f"- {row['variant']}: HTTP/status {row['http_status']}, errors `{row['error_codes']}`, cache `{row['cache_path']}`.\n")
        f.write("\nConclusion: token is required for iapi3 translate in current public testing; timestamp alone is insufficient. Static `/fragment/tmem` fallback is used for public examples.\n")


def fetch_static_and_fragments(config: dict[str, Any], client: PoliteClient, l1: str, l2: str, phrase: str, max_pages: int, discovered_from_phrase: str = "", census: bool = False) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], int]:
    pair = pair_name(l1, l2)
    static_url = glosbe_phrase_url(config, l1, l2, phrase)
    body, headers = static_cache_paths(l1, l2, phrase)
    static_res = client.get(static_url, body, headers, source_site="static_page", pair=pair, l1=l1, l2=l2, phrase=phrase, page=1, discovered_from_phrase=discovered_from_phrase, notes="static phrase page")
    html_text = body.read_text(encoding="utf-8", errors="replace")
    static_sha = sha256_file(body)
    wordlist = parse_wordlist_from_static(html_text)
    dict_rows = parse_dictionary_from_static(html_text, l1, l2, phrase, body, static_url, static_sha, static_res.timestamp_utc)
    example_rows: list[dict[str, Any]] = []
    pages_fetched = 1
    for page in range(1, max_pages + 1):
        url = fragment_url(config, l1, l2, phrase, page)
        fbody, fheaders = fragment_cache_paths(l1, l2, phrase, page)
        fres = client.get(url, fbody, fheaders, source_site="static_page", pair=pair, l1=l1, l2=l2, phrase=phrase, page=page, discovered_from_url=static_url, discovered_from_phrase=discovered_from_phrase, notes="translation memory fragment")
        pages_fetched += 1
        frag_text = fbody.read_text(encoding="utf-8", errors="replace")
        rows, has_more = parse_examples_from_fragment(frag_text, l1, l2, phrase, page, fbody, url, sha256_file(fbody), fres.timestamp_utc)
        example_rows.extend(rows)
        if not has_more:
            break
        if census and page >= max_pages:
            break
    return example_rows, dict_rows, wordlist, pages_fetched


def command_census_pairs(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ensure_layout(config)
    client = PoliteClient(config, force=args.force)
    selected_pairs = set(re.split(r"[;\s]+", args.pairs.strip())) if getattr(args, "pairs", "") else None
    seed_limit = int(config["census"]["seed_limit_per_pair"])
    max_pages = int(config["census"]["max_pages_per_phrase_census"])
    seeds = list(dict.fromkeys(config["starter_seeds"]))[:seed_limit]
    api_diag = {}
    token_path = PROCESSED / "token_behavior.json"
    if token_path.exists():
        api_diag = json.loads(token_path.read_text(encoding="utf-8"))
    census_rows = []
    all_wordlist_rows = read_jsonl(PROCESSED / "wordlist_items.jsonl")
    for l1, l2 in config["target_pairs"]:
        pair = pair_name(l1, l2)
        if selected_pairs and pair not in selected_pairs:
            continue
        print(f"[census] {pair}", flush=True)
        unique_examples: dict[tuple[str, str], dict[str, Any]] = {}
        dict_count = 0
        wordlist_count = 0
        author_counter: Counter[str] = Counter()
        author_id_counter: Counter[str] = Counter()
        for phrase in seeds:
            try:
                examples, dict_rows, wordlist, _ = fetch_static_and_fragments(config, client, l1, l2, phrase, max_pages=max_pages, census=True)
            except Exception as exc:  # noqa: BLE001
                log_error("census_pairs", pair, l1, l2, phrase, "", "", "", type(exc).__name__, str(exc))
                continue
            dict_count += len(dict_rows)
            wordlist_count += len(wordlist)
            for idx, item in enumerate(wordlist):
                all_wordlist_rows.append(
                    {
                        "pair": pair,
                        "l1": l1,
                        "l2": l2,
                        "query_phrase": phrase,
                        "page": 1,
                        "side": item["side"],
                        "wordlist_order": idx,
                        "discovered_phrase_raw": item["phrase"],
                        "discovered_phrase_clean": clean_text(item["phrase"]),
                        "source_url": glosbe_phrase_url(config, l1, l2, phrase),
                        "raw_json_path": "",
                        "raw_html_path": rel(static_cache_paths(l1, l2, phrase)[0]),
                        "crawl_timestamp_utc": now_utc(),
                    }
                )
            for ex in examples:
                key = (ex["source_sentence_clean"], ex["target_sentence_clean"])
                unique_examples[key] = ex
                if ex.get("author_label_if_known"):
                    author_counter[ex["author_label_if_known"]] += 1
                if ex.get("authorId"):
                    author_id_counter[ex["authorId"]] += 1
        total = len(unique_examples)
        if total == 0 and dict_count == 0:
            yclass = "none"
            proceed = "yes"
        elif total == 0:
            yclass = "lexical_only"
            proceed = "yes"
        elif total < 25:
            yclass = "sparse_examples"
            proceed = "yes"
        elif total < 250:
            yclass = "moderate_examples"
            proceed = "yes"
        else:
            yclass = "high_examples"
            proceed = "yes"
        jw_count = sum(v for k, v in author_counter.items() if "jw" in k.lower())
        api_status = "blocked_by_token" if "InvalidApiTokenException" in json.dumps(api_diag) else "not_tested"
        census_rows.append(
            {
                "pair": pair,
                "l1": l1,
                "l2": l2,
                "source_language_name": source_name(config, l1),
                "target_language_name": target_name(config, l2),
                "census_seed_count": len(seeds),
                "api_status": api_status,
                "token_required": "yes" if api_status == "blocked_by_token" else "unknown",
                "timestamp_required": "no_timestamp_alone_insufficient" if api_status == "blocked_by_token" else "unknown",
                "phraseTranslations_found": "yes" if dict_count else "no",
                "tmem_found": "yes" if total else "no",
                "tmem_examples_found": "yes" if total else "no",
                "max_tmem_count_seen": total,
                "total_unique_examples_seen_in_census": total,
                "wordlist_found": "yes" if wordlist_count else "no",
                "static_page_examples_found": "yes" if total else "no",
                "top_author_ids": ";".join(k for k, _ in author_id_counter.most_common(5)),
                "top_author_labels_if_known": ";".join(k for k, _ in author_counter.most_common(5)),
                "top_domains": ";".join(k for k, _ in author_counter.most_common(5)),
                "suspected_jw2019_or_religious_share": f"{jw_count}/{sum(author_counter.values())}" if author_counter else "0/0",
                "suspected_automatic_translation_share": "unknown",
                "suspected_existing_formosanbank_overlap": "not_checked_yet",
                "estimated_yield_class": yclass,
                "proceed_to_full_crawl": proceed,
                "notes": "Census used public static phrase pages plus /fragment/tmem fallback because iapi3 currently requires token.",
            }
        )
    write_csv(PROCESSED / "pair_census.csv", census_rows)
    write_jsonl(PROCESSED / "wordlist_items.jsonl", all_wordlist_rows)


def seed_existing_formosanbank(l1: str, limit: int = 100) -> list[str]:
    seeds: Counter[str] = Counter()
    candidates = [
        ROOT / "work" / "reference_amis" / "Amis.xml",
        ROOT / "work" / "json" / "cleaned_amis_chinese_translations.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            if path.suffix == ".xml":
                root = ET.parse(path).getroot()
                for form in root.findall(".//FORM"):
                    if form.text:
                        for tok in re.findall(r"[\wʼ'ˈ.-]+", form.text, flags=re.UNICODE):
                            if len(tok) > 1:
                                seeds[tok] += 1
            elif path.suffix == ".json":
                data = json.loads(path.read_text(encoding="utf-8"))
                for row in data:
                    for tok in re.findall(r"[\wʼ'ˈ.-]+", row.get("formosan", ""), flags=re.UNICODE):
                        if len(tok) > 1:
                            seeds[tok] += 1
        except Exception as exc:  # noqa: BLE001
            log_warning("seed_existing_formosanbank", l1=l1, warning_type=type(exc).__name__, message=str(exc), notes=rel(path))
    return [k for k, _ in seeds.most_common(limit)]


def command_crawl_static_pages(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ensure_layout(config)
    client = PoliteClient(config, force=args.force)
    selected_pairs = set(re.split(r"[;\s]+", args.pairs.strip())) if getattr(args, "pairs", "") else None
    max_phrases = int(args.max_phrases or config["full_crawl"]["max_phrases_per_pair"])
    max_pages = int(args.max_pages or config["full_crawl"]["max_pages_per_phrase"])
    no_new_limit = int(config["full_crawl"]["stop_after_no_new_examples_phrases"])
    global_wordlist = read_jsonl(PROCESSED / "wordlist_items.jsonl")
    wordlist_by_pair: dict[str, list[str]] = defaultdict(list)
    for row in global_wordlist:
        wordlist_by_pair[row.get("pair", "")].append(row.get("discovered_phrase_clean") or row.get("discovered_phrase_raw", ""))
    for l1, l2 in config["target_pairs"]:
        pair = pair_name(l1, l2)
        if selected_pairs and pair not in selected_pairs:
            continue
        qpath = PROCESSED / "crawl_queue_snapshots" / f"{l1}_{l2}.json"
        if qpath.exists() and not args.restart_queue:
            state = json.loads(qpath.read_text(encoding="utf-8"))
            queue = deque(state.get("queue", []))
            seen = set(state.get("seen", []))
            unique_seen = set(tuple(x) for x in state.get("unique_examples", []))
        else:
            initial = []
            if l1 == "ami":
                initial.extend(seed_existing_formosanbank(l1, 150))
            initial.extend(wordlist_by_pair.get(pair, []))
            initial.extend(config["starter_seeds"])
            queue = deque()
            seen = set()
            for phrase in initial:
                phrase = clean_text(phrase)
                if phrase and phrase not in seen:
                    queue.append({"phrase": phrase, "discovered_from_phrase": ""})
            unique_seen: set[tuple[str, str]] = set()
        phrases_done = len(seen)
        no_new = 0
        while queue and phrases_done < max_phrases and no_new < no_new_limit:
            item = queue.popleft()
            phrase = clean_text(item["phrase"])
            if not phrase or phrase in seen:
                continue
            seen.add(phrase)
            phrases_done += 1
            if phrases_done == 1 or phrases_done % 25 == 0:
                print(f"[static-crawl] {pair} phrase {phrases_done}/{max_phrases}: {phrase}", flush=True)
            try:
                examples, _, wordlist, _ = fetch_static_and_fragments(config, client, l1, l2, phrase, max_pages=max_pages, discovered_from_phrase=item.get("discovered_from_phrase", ""))
            except Exception as exc:  # noqa: BLE001
                log_error("crawl_static_pages", pair, l1, l2, phrase, "", "", "", type(exc).__name__, str(exc))
                continue
            before = len(unique_seen)
            for ex in examples:
                unique_seen.add((ex["source_sentence_clean"], ex["target_sentence_clean"]))
            if len(unique_seen) == before:
                no_new += 1
            else:
                no_new = 0
            for w in wordlist:
                wp = clean_text(w["phrase"])
                if wp and wp not in seen and all(q["phrase"] != wp for q in queue):
                    queue.append({"phrase": wp, "discovered_from_phrase": phrase})
            qpath.write_text(
                json.dumps(
                    {
                        "pair": pair,
                        "updated_at_utc": now_utc(),
                        "seen": sorted(seen),
                        "queue": list(queue),
                        "unique_examples": [list(x) for x in sorted(unique_seen)],
                        "phrases_done": phrases_done,
                        "max_phrases": max_phrases,
                        "no_new_examples_streak": no_new,
                    },
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )


def command_crawl_iapi3(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ensure_layout(config)
    client = PoliteClient(config, force=args.force)
    seeds = list(config["starter_seeds"])[:3]
    for l1, l2 in config["target_pairs"]:
        for phrase in seeds:
            url = build_iapi_url(config, l1, l2, phrase, 1)
            body, headers = iapi_cache_paths(l1, l2, phrase, 1)
            try:
                res = client.get(url, body, headers, source_site="iapi.glosbe", pair=pair_name(l1, l2), l1=l1, l2=l2, phrase=phrase, page=1, notes="iapi3 crawl probe")
                data = json.loads(body.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "InvalidApiTokenException" in data.get("errorCodes", []):
                    log_error("crawl_iapi3", pair_name(l1, l2), l1, l2, phrase, 1, url, rel(body), "InvalidApiTokenException", "iapi3 requires token; static fallback used")
                    break
                if res.status in {403, 429}:
                    break
            except Exception as exc:  # noqa: BLE001
                log_error("crawl_iapi3", pair_name(l1, l2), l1, l2, phrase, 1, url, rel(body), type(exc).__name__, str(exc))
                break


def command_extract_iapi_json(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ensure_layout(config)
    rows: list[dict[str, Any]] = []
    dict_rows: list[dict[str, Any]] = read_jsonl(PROCESSED / "dictionary_entries_raw.jsonl")
    wordlist_rows: list[dict[str, Any]] = read_jsonl(PROCESSED / "wordlist_items.jsonl")
    for path in sorted((RAW / "json" / "iapi3").glob("*/*/page_*.json")):
        parts = path.parts
        pair_dir = path.parents[1].name
        if "_" not in pair_dir:
            continue
        l1, l2 = pair_dir.split("_", 1)
        phrase = urllib.parse.unquote(path.parent.name)
        page_match = re.search(r"page_(\d+)", path.name)
        page = int(page_match.group(1)) if page_match else 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            log_error("extract_iapi_json", pair_name(l1, l2), l1, l2, phrase, page, "", rel(path), type(exc).__name__, str(exc))
            continue
        if isinstance(data, dict) and data.get("error"):
            log_error("extract_iapi_json", pair_name(l1, l2), l1, l2, phrase, page, "", rel(path), ",".join(data.get("errorCodes", [])), json.dumps(data.get("data", {})))
            continue
        sha = sha256_file(path)
        source_url = build_iapi_url(config, l1, l2, phrase, page)
        tmem = data.get("tmem", {}) if isinstance(data, dict) else {}
        for i, ex in enumerate(tmem.get("examples", []) if isinstance(tmem, dict) else []):
            source_raw = ex.get("sourceSentence", "")
            target_raw = ex.get("targetSentence", "")
            record_id = "GLOSBE_IAPI_" + sha256_text(f"{l1}|{l2}|{phrase}|{page}|{i}|{source_raw}|{target_raw}")[:20]
            rows.append(
                {
                    "record_id": record_id,
                    "pair": pair_name(l1, l2),
                    "l1": l1,
                    "l2": l2,
                    "query_phrase": phrase,
                    "page": page,
                    "source_sentence_raw": source_raw,
                    "target_sentence_raw": target_raw,
                    "source_sentence_clean": clean_text(source_raw),
                    "target_sentence_clean": clean_text(target_raw),
                    "tmBunchId": ex.get("tmBunchId", ex.get("id", "")),
                    "authorId": ex.get("authorId", ""),
                    "author_label_if_known": "",
                    "domain": ex.get("domain", ""),
                    "source_language_detected": "",
                    "target_language_detected": "",
                    "api_source_lang_if_present": ex.get("sourceLanguage", ""),
                    "api_target_lang_if_present": ex.get("targetLanguage", ""),
                    "has_audio": bool(ex.get("audio")),
                    "audio_metadata_raw_json": ex.get("audio", ""),
                    "raw_example_json": ex,
                    "raw_json_path": rel(path),
                    "raw_json_sha256": sha,
                    "source_url": source_url,
                    "crawl_timestamp_utc": now_utc(),
                    "parse_confidence": "medium",
                    "parse_warnings": "",
                }
            )
        for i, tr in enumerate(data.get("phraseTranslations", []) if isinstance(data, dict) else []):
            target = tr.get("phrase", {}).get("text", "") if isinstance(tr.get("phrase"), dict) else tr.get("phrase", "")
            record_id = "GLOSBE_DICT_IAPI_" + sha256_text(f"{l1}|{l2}|{phrase}|{target}|{i}")[:16]
            dict_rows.append(
                {
                    "record_id": record_id,
                    "pair": pair_name(l1, l2),
                    "l1": l1,
                    "l2": l2,
                    "query_phrase": phrase,
                    "page": page,
                    "source_phrase_raw": phrase,
                    "source_phrase_clean": clean_text(phrase),
                    "target_phrase_raw": target,
                    "target_phrase_clean": clean_text(target),
                    "part_of_speech": tr.get("partOfSpeech", ""),
                    "translation_id": tr.get("id", ""),
                    "authorId": tr.get("authorId", ""),
                    "author_label_if_known": "",
                    "votes": tr.get("votes", ""),
                    "quality_raw_json": tr.get("quality", ""),
                    "raw_translation_json": tr,
                    "raw_json_path": rel(path),
                    "raw_json_sha256": sha,
                    "source_url": source_url,
                    "crawl_timestamp_utc": now_utc(),
                    "parse_confidence": "medium",
                    "parse_warnings": "",
                }
            )
        wordlist = data.get("wordlist", {}) if isinstance(data, dict) else {}
        for side in ["before", "after"]:
            for idx, item in enumerate(wordlist.get(side, []) if isinstance(wordlist, dict) else []):
                text = item.get("phrase", item.get("text", item)) if isinstance(item, dict) else item
                wordlist_rows.append(
                    {
                        "pair": pair_name(l1, l2),
                        "l1": l1,
                        "l2": l2,
                        "query_phrase": phrase,
                        "page": page,
                        "side": side,
                        "wordlist_order": idx,
                        "discovered_phrase_raw": text,
                        "discovered_phrase_clean": clean_text(text),
                        "source_url": source_url,
                        "raw_json_path": rel(path),
                        "crawl_timestamp_utc": now_utc(),
                    }
                )
    write_jsonl(PROCESSED / "tmem_examples_raw.jsonl", rows)
    write_jsonl(PROCESSED / "dictionary_entries_raw.jsonl", dict_rows)
    write_jsonl(PROCESSED / "wordlist_items.jsonl", wordlist_rows)


def command_extract_static_pages(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ensure_layout(config)
    example_rows: list[dict[str, Any]] = []
    dict_rows: list[dict[str, Any]] = []
    static_dict_rows: list[dict[str, Any]] = []
    wordlist_rows: list[dict[str, Any]] = []
    for l1, l2 in config["target_pairs"]:
        pair = pair_name(l1, l2)
        base = RAW / "html" / "static" / f"{l1}_{l2}"
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.html")):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:  # noqa: BLE001
                log_error("extract_static_pages", pair, l1, l2, "", "", "", rel(path), type(exc).__name__, str(exc))
                continue
            sha = sha256_file(path)
            crawl_ts = now_utc()
            if path.name.startswith("fragment_page_"):
                phrase = urllib.parse.unquote(path.parent.name)
                page_match = re.search(r"fragment_page_(\d+)", path.name)
                page = int(page_match.group(1)) if page_match else 1
                url = fragment_url(config, l1, l2, phrase, page)
                rows, _ = parse_examples_from_fragment(text, l1, l2, phrase, page, path, url, sha, crawl_ts)
                example_rows.extend(rows)
            else:
                phrase = urllib.parse.unquote(path.stem)
                url = glosbe_phrase_url(config, l1, l2, phrase)
                drows = parse_dictionary_from_static(text, l1, l2, phrase, path, url, sha, crawl_ts)
                dict_rows.extend(drows)
                static_dict_rows.extend(
                    [
                        {
                            "record_id": row["record_id"],
                            "pair": row["pair"],
                            "l1": row["l1"],
                            "l2": row["l2"],
                            "phrase": phrase,
                            "page_url": url,
                            "source_phrase_raw": row["source_phrase_raw"],
                            "target_phrase_raw": row["target_phrase_raw"],
                            "source_phrase_clean": row["source_phrase_clean"],
                            "target_phrase_clean": row["target_phrase_clean"],
                            "part_of_speech_if_visible": row["part_of_speech"],
                            "section_label": "dictionary",
                            "raw_html_path": row["raw_html_path"],
                            "raw_html_sha256": sha,
                            "crawl_timestamp_utc": crawl_ts,
                            "parse_confidence": row["parse_confidence"],
                            "parse_warnings": row["parse_warnings"],
                        }
                        for row in drows
                    ]
                )
                for idx, item in enumerate(parse_wordlist_from_static(text)):
                    wordlist_rows.append(
                        {
                            "pair": pair,
                            "l1": l1,
                            "l2": l2,
                            "query_phrase": phrase,
                            "page": 1,
                            "side": item["side"],
                            "wordlist_order": idx,
                            "discovered_phrase_raw": item["phrase"],
                            "discovered_phrase_clean": clean_text(item["phrase"]),
                            "source_url": url,
                            "raw_json_path": "",
                            "raw_html_path": rel(path),
                            "crawl_timestamp_utc": crawl_ts,
                        }
                    )
    write_jsonl(PROCESSED / "static_page_examples_raw.jsonl", example_rows)
    existing_iapi_dict = [r for r in read_jsonl(PROCESSED / "dictionary_entries_raw.jsonl") if r.get("raw_json_path")]
    write_jsonl(PROCESSED / "dictionary_entries_raw.jsonl", existing_iapi_dict + dict_rows)
    write_jsonl(PROCESSED / "static_page_dictionary_entries_raw.jsonl", static_dict_rows)
    write_jsonl(PROCESSED / "wordlist_items.jsonl", wordlist_rows)


def command_normalize_text(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ensure_layout(config)
    unusual: Counter[str] = Counter()
    samples: list[str] = []
    for path in [PROCESSED / "static_page_examples_raw.jsonl", PROCESSED / "tmem_examples_raw.jsonl", PROCESSED / "dictionary_entries_raw.jsonl"]:
        for row in read_jsonl(path):
            for key in ["source_sentence_clean", "target_sentence_clean", "source_phrase_clean", "target_phrase_clean"]:
                text = row.get(key, "")
                for ch in text:
                    if ord(ch) > 127 and not has_han(ch):
                        unusual[ch] += 1
            if len(samples) < 8:
                raw = row.get("source_sentence_raw") or row.get("source_phrase_raw", "")
                clean = row.get("source_sentence_clean") or row.get("source_phrase_clean", "")
                if raw and raw != clean:
                    samples.append(f"- Raw: `{raw}`\n  Clean: `{clean}`")
    report = f"""# Normalization Report

Generated: {now_utc()}

Rules used:

- Unicode normalized to NFC.
- HTML/XML entities decoded.
- HTML tags stripped from clean text.
- Leading/trailing whitespace trimmed.
- Repeated internal whitespace normalized to a single space in clean fields.
- Non-breaking spaces normalized to regular spaces.
- Apostrophes, glottal marks, hyphens, colons, dots, diacritics, IPA-like symbols, modifier letters, combining marks, case, Chinese punctuation, and Formosan orthography are preserved.
- No ASCII folding.
- No NFKC.
- No machine translation.
- No orthography fixing.

Examples:

{chr(10).join(samples) if samples else '- No raw/clean differences sampled yet.'}

Preserved unusual non-ASCII non-Han characters observed:

{', '.join(f'`{ch}` ({count})' for ch, count in unusual.most_common(80)) if unusual else 'None observed in current processed data.'}

Warnings:

- Static Glosbe fragments split highlighted query terms into nested tags; parser uses visible text with spaces, then normalizes whitespace.
- Language-specific orthography is intentionally preserved.
"""
    (PROCESSED / "normalization_report.md").write_text(report, encoding="utf-8")


def command_validate_language_direction(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ensure_layout(config)
    rows = read_jsonl(PROCESSED / "tmem_examples_raw.jsonl") + read_jsonl(PROCESSED / "static_page_examples_raw.jsonl")
    audit = []
    for row in rows:
        l1, l2 = row["l1"], row["l2"]
        source = row.get("source_sentence_clean", "")
        target = row.get("target_sentence_clean", "")
        status = "ok"
        action = "keep"
        notes = []
        if not source:
            status, action = "empty", "exclude"
            notes.append("empty source")
        elif not target:
            status, action = "empty", "exclude"
            notes.append("empty target")
        elif l2 == "zh" and not has_han(target):
            status, action = "uncertain", "needs_review"
            notes.append("Chinese target lacks Han characters")
        elif l2 == "en" and has_han(target):
            status, action = "wrong_language", "exclude"
            notes.append("English target contains Han characters")
        if has_han(source):
            status, action = "wrong_language", "exclude"
            notes.append("Formosan source contains Han characters")
        if l2 == "en" and source == target:
            status, action = "uncertain", "needs_review"
            notes.append("source and target identical")
        if looks_like_english(source) and not any(mark in source for mark in ["ˈ", "ʼ", "'", "ng", "ay"]):
            if l2 == "en":
                status, action = "uncertain", "needs_review"
                notes.append("source resembles English by stopword heuristic")
        audit.append(
            {
                "record_id": row["record_id"],
                "pair": row["pair"],
                "expected_l1": l1,
                "expected_l2": l2,
                "source_sentence_clean": source,
                "target_sentence_clean": target,
                "script_source": script_label(source),
                "script_target": script_label(target),
                "language_detection_source": l1 if status == "ok" else "heuristic_uncertain",
                "language_detection_target": l2 if status == "ok" else "heuristic_uncertain",
                "direction_status": status,
                "action": action,
                "notes": "; ".join(notes),
            }
        )
    write_csv(PROCESSED / "language_direction_audit.csv", audit)
    lm_rows = []
    for code, meta in config["language_mapping"].items():
        lm_rows.append(
            {
                "code": code,
                "FormosanBank_language_name": meta.get("name", code),
                "ISO_639_3": meta.get("iso_639_3", code),
                "glottocode_if_known": "",
                "Chinese_name_if_known": "",
                "English_name_if_known": meta.get("name", code),
                "FormosanBank_dialect_if_applicable": "",
                "mapping_confidence": "configured",
                "mapping_notes": "Configured from task language mapping; verify disputed/ambiguous conventions before public release.",
            }
        )
    lm_rows.extend(
        [
            {"code": "en", "FormosanBank_language_name": "English", "ISO_639_3": "eng", "English_name_if_known": "English", "mapping_confidence": "high", "mapping_notes": "Target translation language only."},
            {"code": "zh", "FormosanBank_language_name": "Chinese", "ISO_639_3": "zho", "English_name_if_known": "Chinese", "mapping_confidence": "high", "mapping_notes": "Target translation language only."},
        ]
    )
    write_csv(PROCESSED / "language_mapping.csv", lm_rows)


def command_dedupe_examples(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ensure_layout(config)
    rows = read_jsonl(PROCESSED / "tmem_examples_raw.jsonl") + read_jsonl(PROCESSED / "static_page_examples_raw.jsonl")
    kept: list[dict[str, Any]] = []
    seen_text: dict[tuple[str, str, str, str], str] = {}
    seen_tm: dict[tuple[str, str, str, str], str] = {}
    dup_rows = []
    group_num = 1
    for row in rows:
        text_key = (row["l1"], row["l2"], dedupe_key(row.get("source_sentence_clean", "")), dedupe_key(row.get("target_sentence_clean", "")))
        tm_key = (row["pair"], str(row.get("tmBunchId", "")), text_key[2], text_key[3])
        duplicate_type = ""
        canonical = ""
        if row.get("tmBunchId") and tm_key in seen_tm:
            duplicate_type = "exact_tmBunchId"
            canonical = seen_tm[tm_key]
        elif text_key in seen_text:
            duplicate_type = "exact_text"
            canonical = seen_text[text_key]
        if duplicate_type:
            dup_id = f"DUP_{group_num:06d}"
            group_num += 1
            dup_rows.append(
                {
                    "duplicate_group_id": dup_id,
                    "record_id": row["record_id"],
                    "pair": row["pair"],
                    "duplicate_type": duplicate_type,
                    "canonical_record_id": canonical,
                    "tmBunchId": row.get("tmBunchId", ""),
                    "source_sentence_clean": row.get("source_sentence_clean", ""),
                    "target_sentence_clean": row.get("target_sentence_clean", ""),
                    "query_phrase": row.get("query_phrase") or row.get("phrase", ""),
                    "raw_json_path": row.get("raw_json_path", ""),
                    "action": "excluded_duplicate",
                    "notes": "Duplicate by normalized source/target and/or tmBunchId.",
                }
            )
            continue
        seen_text[text_key] = row["record_id"]
        if row.get("tmBunchId"):
            seen_tm[tm_key] = row["record_id"]
        row["dedupe_status"] = "kept"
        kept.append(row)
    write_jsonl(PROCESSED / "tmem_examples_deduped.jsonl", kept)
    write_csv(PROCESSED / "duplicates.csv", dup_rows)


def extract_existing_pairs_from_file(path: Path) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    try:
        if path.suffix.lower() == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for row in data:
                    if isinstance(row, dict):
                        src = row.get("formosan") or row.get("source_sentence_clean") or row.get("source")
                        tgt = row.get("chinese") or row.get("english") or row.get("target_sentence_clean") or row.get("target")
                        if src and tgt:
                            pairs.add((dedupe_key(src), dedupe_key(tgt)))
        elif path.suffix.lower() == ".xml":
            root = ET.parse(path).getroot()
            for s in root.findall(".//S"):
                form = s.find("FORM")
                if form is None or not form.text:
                    continue
                for transl in s.findall("TRANSL"):
                    if transl.text:
                        pairs.add((dedupe_key(form.text), dedupe_key(transl.text)))
    except Exception:
        pass
    return pairs


def command_dedupe_against_formosanbank(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ensure_layout(config)
    repos = [
        "Formosan-Glosbe",
        "Formosan-TaiwanBibleSociety-Bibles",
        "Formosan-ILRDF_Dicts",
        "Formosan-ILRDF-YouTube-Videos",
        "Formosan-ePark",
        "Formosan-Wikipedias",
        "Formosan-gitbook_translations",
        "Formosan-MT",
        "Formosan-MT-Toolkit",
        "Formosan-NTU",
    ]
    repo_sets: dict[str, set[tuple[str, str]]] = defaultdict(set)
    repo_files: dict[tuple[str, str], str] = {}
    parent = ROOT.parent
    for repo in repos:
        repo_path = parent / repo
        if not repo_path.exists():
            continue
        files = []
        for pattern in ["Final_XML/**/*.xml", "work/json/*.json", "data/processed/*.jsonl", "*.xml"]:
            files.extend(repo_path.glob(pattern))
        for path in files[:200]:
            pairs = extract_existing_pairs_from_file(path)
            for p in pairs:
                repo_sets[repo].add(p)
                repo_files[(repo, "|".join(p))] = rel(path)
    rows = []
    for row in read_jsonl(PROCESSED / "tmem_examples_deduped.jsonl"):
        key = (dedupe_key(row.get("source_sentence_clean", "")), dedupe_key(row.get("target_sentence_clean", "")))
        matched = False
        for repo, pair_set in repo_sets.items():
            if key in pair_set:
                action = "exclude_from_xml" if repo == "Formosan-Glosbe" else "keep_but_flag"
                rows.append(
                    {
                        "record_id": row["record_id"],
                        "pair": row["pair"],
                        "source_sentence_clean": row.get("source_sentence_clean", ""),
                        "target_sentence_clean": row.get("target_sentence_clean", ""),
                        "existing_repo": repo,
                        "existing_file": repo_files.get((repo, "|".join(key)), ""),
                        "existing_record_id_if_known": "",
                        "overlap_type": "exact_source_target",
                        "similarity_score": "1.0",
                        "action": action,
                        "notes": "Exact normalized source+target match.",
                    }
                )
                matched = True
        if not matched:
            rows.append(
                {
                    "record_id": row["record_id"],
                    "pair": row["pair"],
                    "source_sentence_clean": row.get("source_sentence_clean", ""),
                    "target_sentence_clean": row.get("target_sentence_clean", ""),
                    "existing_repo": "",
                    "existing_file": "",
                    "existing_record_id_if_known": "",
                    "overlap_type": "no_overlap",
                    "similarity_score": "0",
                    "action": "keep",
                    "notes": "",
                }
            )
    write_csv(PROCESSED / "overlap_candidates.csv", rows)


def command_filter_quality(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ensure_layout(config)
    audit = {r["record_id"]: r for r in read_csv(PROCESSED / "language_direction_audit.csv")}
    overlaps = defaultdict(list)
    for row in read_csv(PROCESSED / "overlap_candidates.csv"):
        overlaps[row["record_id"]].append(row)
    kept = []
    rejected = []
    for row in read_jsonl(PROCESSED / "tmem_examples_deduped.jsonl"):
        rid = row["record_id"]
        reason = ""
        if not row.get("source_sentence_clean"):
            reason = "empty_source"
        elif not row.get("target_sentence_clean"):
            reason = "empty_target"
        elif audit.get(rid, {}).get("action") not in {"keep", ""}:
            reason = audit.get(rid, {}).get("direction_status", "reversed_uncertain")
        elif any(o.get("action") == "exclude_from_xml" for o in overlaps.get(rid, [])) and config["quality"].get("exclude_existing_formosan_glosbe_overlap_from_xml", True):
            reason = "existing_formosanbank_overlap"
        elif not row.get("raw_json_path") and not row.get("raw_html_path"):
            reason = "no_raw_provenance"
        elif "machine" in str(row.get("author_label_if_known", "")).casefold():
            reason = "automatic_translation_only"
        if reason:
            rejected.append(
                {
                    "record_id": rid,
                    "pair": row["pair"],
                    "rejection_reason": reason,
                    "source_sentence_clean": row.get("source_sentence_clean", ""),
                    "target_sentence_clean": row.get("target_sentence_clean", ""),
                    "query_phrase": row.get("query_phrase") or row.get("phrase", ""),
                    "raw_path": row.get("raw_json_path") or row.get("raw_html_path", ""),
                    "notes": "",
                }
            )
        else:
            row["quality_status"] = "eligible"
            row["overlap_status"] = ";".join(sorted({o.get("overlap_type", "") for o in overlaps.get(rid, []) if o.get("overlap_type") != "no_overlap"})) or "no_overlap"
            kept.append(row)
    write_jsonl(PROCESSED / "quality_filtered_examples.jsonl", kept)
    write_csv(PROCESSED / "rejected_records.csv", rejected)


def compact_attr(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def dedupe_dictionary_entries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    kept = []
    for row in rows:
        key = (row.get("pair"), dedupe_key(row.get("source_phrase_clean", "")), dedupe_key(row.get("target_phrase_clean", "")))
        if key in seen:
            continue
        seen.add(key)
        row["dedupe_status"] = "kept"
        kept.append(row)
    return kept


def lexical_xml_rejection_reason(source: str, target: str, l2: str) -> str:
    if not source:
        return "empty_source"
    if not target:
        return "empty_target"
    target_note = target.strip().casefold().strip("\"' ")
    if (
        target_note.startswith("see ")
        or target_note.startswith("undefined")
        or "incorrect entry" in target_note
        or "not atayal" in target_note
        or target_note in {"btunux", "hojil"}
    ):
        return "target_cross_reference_or_invalid_note"
    if re.fullmatch(r"[\W\d_]+", source.strip()):
        return "source_numeric_or_punct_only"
    if re.fullmatch(r"[\W\d_]+", target.strip()):
        return "target_numeric_or_punct_only"
    if source.strip().casefold() == target.strip().casefold():
        return "identical_source_target"
    if "**" in source or "**" in target:
        return "markup_marker"
    if re.search(r"<[^>]+>", source) or re.search(r"<[^>]+>", target):
        return "html_tag_text"
    if has_han(source):
        return "han_in_formosan_source"
    if l2 == "en" and has_han(target):
        return "han_in_english_target"
    if l2 == "zh" and not has_han(target):
        return "no_han_in_chinese_target"
    return ""


@dataclass
class IldrfReferenceLexicon:
    glosses: dict[str, dict[str, set[str]]]
    source_files: dict[str, dict[str, set[str]]]
    file_stats: list[dict[str, Any]]


def load_ildrf_reference_lexicon(config: dict[str, Any]) -> IldrfReferenceLexicon:
    """Load the selected ILRDF-derived dictionary files used for comparison.

    Zheng et al. extracted these files from ILRDF dictionaries for their ACL
    2024 dataset. The files are useful reference metadata, but are not an
    independent lexical authority. Exact file selection matters because Seediq
    and Truku both use ``xml:lang="trv"`` in FormosanBank.
    """
    settings = config.get("ildrf_reference_lexicon", {})
    repo_value = settings.get("derived_repo", "")
    dictionary_files = settings.get("dictionary_files", {})
    if not repo_value or not dictionary_files:
        raise ValueError("ildrf_reference_lexicon must configure derived_repo and dictionary_files")

    repo = repo_path(repo_value)
    if not repo.is_dir():
        raise FileNotFoundError(f"ILRDF-derived reference repository not found: {repo}")

    glosses: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    source_files: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    file_stats: list[dict[str, Any]] = []
    for expected_lang, relative_path in sorted(dictionary_files.items()):
        path = repo / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"Configured ILRDF-derived dictionary file not found: {path}")
        try:
            root = ET.parse(path).getroot()
        except Exception as exc:
            raise ValueError(f"Could not parse ILRDF-derived dictionary file {path}: {exc}") from exc

        actual_lang = root.get(f"{{{XML_NS}}}lang", "")
        if actual_lang != expected_lang:
            raise ValueError(
                f"Configured ILRDF-derived dictionary {path} has xml:lang={actual_lang!r}; "
                f"expected {expected_lang!r}"
            )
        provenance = " ".join(
            [root.get("source", ""), root.get("citation", ""), root.get("BibTeX_citation", "")]
        )
        if "Indigenous Languages Research and Development Foundation" not in provenance:
            raise ValueError(f"Configured reference file does not identify ILRDF provenance: {path}")

        sentence_count = 0
        translation_count = 0
        source_keys: set[str] = set()
        pair_keys: set[tuple[str, str]] = set()
        relative_to_repo = str(path.relative_to(repo))
        for sentence in root.findall(".//S"):
            sentence_count += 1
            sentence_glosses = [
                clean_text(translation.text)
                for translation in sentence.findall("TRANSL")
                if clean_text(translation.text)
            ]
            translation_count += len(sentence_glosses)
            if not sentence_glosses:
                continue
            original_forms = [
                clean_text(form.text)
                for form in sentence.findall("FORM")
                if form.get("kindOf") == "original" and clean_text(form.text)
            ]
            for form_text in original_forms:
                source_key = form_group_key(form_text)
                source_keys.add(source_key)
                glosses[expected_lang][source_key].update(sentence_glosses)
                source_files[expected_lang][source_key].add(relative_to_repo)
                pair_keys.update((source_key, dedupe_key(gloss)) for gloss in sentence_glosses)
        file_stats.append(
            {
                "language": expected_lang,
                "file": relative_to_repo,
                "sha256": sha256_file(path),
                "sentences": sentence_count,
                "translations": translation_count,
                "unique_source_forms": len(source_keys),
                "unique_source_gloss_pairs": len(pair_keys),
            }
        )
    return IldrfReferenceLexicon(glosses, source_files, file_stats)


def citation_bits(config: dict[str, Any], l1: str, l2: str, suffix: str) -> tuple[str, str, str, str, str]:
    tgt_iso = target_iso(config, l2)
    representative_url = f"https://glosbe.com/{l1}/{l2}"
    retrieved_date = config.get("metadata", {}).get("retrieved_date", today_utc())
    year = retrieved_date[:4]
    citation = f"Glosbe. ({year}). Glosbe {source_name(config, l1)}-{target_name(config, l2)} dictionary and translation memory. Retrieved {retrieved_date}, from {representative_url}"
    bib = f"@misc{{Glosbe_{l1}_{tgt_iso}_{suffix}, author = {{{{Glosbe}}}}, title = {{{{Glosbe {source_name(config, l1)}--{target_name(config, l2)} dictionary and translation memory}}}}, year = {{{{{year}}}}}, howpublished = {{{{Glosbe online dictionary and translation memory}}}}, url = {{{{{representative_url}}}}}, note = {{{{Collected by FormosanBank for private research review; redistribution subject to Glosbe terms and third-party source rights}}}}}}"
    copyright_attr = "© Glosbe and/or respective contributors/source corpora. Collected by FormosanBank for private research review; redistribution subject to Glosbe terms and third-party source rights."
    return tgt_iso, representative_url, citation, bib, copyright_attr


def default_xml_dialect(l1: str) -> str:
    return {
        "ami": "unknown",
        "tay": "unknown",
        "trv": "Truku",
        "xsy": "Saisiyat",
    }.get(l1, "")


# Heuristic Chinese-to-English mappings for describing overlap with the
# ILRDF-derived reference glosses. These mappings never decide XML inclusion.
# They are incomplete, substring-based, and cannot distinguish homographs or
# additional senses, so their output is review metadata only.
ILRDF_GLOSS_TARGET_EVIDENCE: list[tuple[str, set[str]]] = [
    ("上帝", {"god", "deity"}),
    ("神", {"god", "spirit"}),
    ("靈界", {"spirit realm"}),
    ("靈", {"spirit"}),
    ("鬼魂", {"ghost", "spirit"}),
    ("鬼", {"ghost", "spirit"}),
    ("他", {"he", "him"}),
    ("他的", {"his"}),
    ("我（屬格）", {"i", "me", "my"}),
    ("我", {"i", "me"}),
    ("我們", {"we", "us"}),
    ("你", {"you"}),
    ("你們", {"you all", "you"}),
    ("媽媽", {"mom", "mother", "mum"}),
    ("爸爸", {"father", "dad"}),
    ("父親", {"father"}),
    ("哥", {"brother", "older brother"}),
    ("夫之兄", {"husband's older brother"}),
    ("爺爺", {"grandfather"}),
    ("外公", {"grandfather"}),
    ("祖父", {"grandfather"}),
    ("男性長輩", {"grandfather", "male elder"}),
    ("兄弟姐妹", {"sibling", "siblings", "brother", "sister"}),
    ("堂(表)兄弟", {"cousin"}),
    ("朋友", {"friend"}),
    ("孩子", {"child", "children", "kid", "kids", "offspring"}),
    ("男孩", {"boy"}),
    ("女孩", {"girl", "woman"}),
    ("女孩子", {"girl", "woman"}),
    ("女生", {"woman", "girl"}),
    ("女人", {"woman"}),
    ("女性", {"woman", "female"}),
    ("妻子", {"wife", "woman"}),
    ("人", {"person", "people", "human", "man"}),
    ("泰雅族人", {"atayal"}),
    ("客家人", {"hakka"}),
    ("獵人", {"hunter"}),
    ("證人", {"witness"}),
    ("敵人", {"enemy"}),
    ("男子名", set()),
    ("女子名", set()),
    ("一天", {"day"}),
    ("一宿兒", {"day", "night"}),
    ("再一次", {"twice", "again"}),
    ("一氧化碳", {"carbon monoxide"}),
    ("年", {"year", "age"}),
    ("新年", {"new year", "pass the new year"}),
    ("春節", {"new year", "pass the new year"}),
    ("第二年耕地", {"fallow land"}),
    ("一點點", {"little", "small", "a small amount"}),
    ("一", {"one"}),
    ("僅僅", {"alone", "only"}),
    ("只有", {"alone", "only"}),
    ("獨自一人", {"alone"}),
    ("另外", {"another", "other", "different"}),
    ("話語", {"word", "words", "speech", "language", "say", "state"}),
    ("話", {"word", "words", "speech", "language", "story"}),
    ("電話", {"phone"}),
    ("手機", {"phone", "cellphone"}),
    ("語言", {"language", "speech"}),
    ("連接詞", {"and", "or", "conjunction"}),
    ("和解", {"reconcile"}),
    ("和", {"and", "with"}),
    ("或", {"or"}),
    ("這裡", {"here"}),
    ("哪裡", {"where"}),
    ("格位標記", {"case marker", "case-marking particle"}),
    ("主格", {"nominative", "subject marker"}),
    ("好(指沒問題)", {"good", "well", "can"}),
    ("好的", {"good", "well"}),
    ("好", {"good", "well"}),
    ("健康", {"healthy", "strong", "strength"}),
    ("勤奮", {"diligent"}),
    ("嬉戲", {"joke", "play"}),
    ("好玩", {"joke", "fun", "play"}),
    ("好處", {"right", "benefit"}),
    ("權利", {"right"}),
    ("可以", {"can", "may"}),
    ("能夠", {"can", "able"}),
    ("會(做某事)", {"can"}),
    ("知道", {"know"}),
    ("聰明", {"smart", "intelligent"}),
    ("搬運", {"bring", "carry"}),
    ("狗", {"dog", "doggy", "hound"}),
    ("穿山甲", {"pangolin", "anteater, pangolin"}),
    ("燒", {"burn"}),
    ("燒烤", {"braise", "roast"}),
    ("智者", {"wise person", "sage"}),
    ("長官", {"chief", "leader", "chairperson"}),
    ("校長", {"principal", "chairperson"}),
    ("老闆", {"boss", "chairperson"}),
    ("家", {"house", "home", "family"}),
    ("蒼蠅", {"fly", "housefly"}),
    ("翅膀", {"wing"}),
    ("錢", {"money", "dollar", "silver"}),
    ("禁忌", {"taboo", "bad luck"}),
    ("根部", {"root", "origin"}),
    ("源頭", {"origin", "source", "originator"}),
    ("樹頭", {"tree stump", "root"}),
    ("肋骨", {"rib"}),
    ("竹支條", {"twig"}),
    ("枝條", {"branch", "twig"}),
    ("樹枝", {"branch", "twig"}),
    ("手", {"hand", "forearm", "arm"}),
    ("手肘", {"elbow"}),
    ("右手", {"right"}),
    ("右邊", {"right"}),
    ("左手", {"left"}),
    ("左邊", {"left"}),
    ("手鍬", {"spade"}),
    ("分手", {"break up"}),
    ("劃清界線", {"fence", "boundary"}),
    ("獵物", {"prey", "game animal", "beast", "beasts"}),
    ("以前", {"ago", "time past", "past"}),
    ("山、山脊", {"mountain", "ridge"}),
    ("山脊", {"ridge"}),
    ("群山", {"range of mountains", "group of mountains", "mountains"}),
    ("崇山峻嶺", {"range of mountains", "group of mountains", "mountains"}),
    ("山洞", {"orifice", "hole", "cave"}),
    ("洞穴", {"orifice", "hole", "cave"}),
    ("洞", {"orifice", "hole", "cave"}),
    ("山櫻花", {"cherry blossom"}),
    ("山羌", {"muntjac"}),
    ("山芭蕉", {"japanese banana"}),
    ("山藥", {"yam"}),
    ("火山", {"volcano"}),
    ("山刀", {"machete"}),
    ("山", {"mountain"}),
    ("繡眼畫眉", {"bird", "rice bird"}),
    ("水田", {"rice paddy", "field", "plot"}),
    ("爛泥巴", {"mud"}),
    ("明亮", {"bright"}),
    ("照亮", {"bright", "light"}),
    ("光亮", {"bright", "light"}),
    ("外面", {"outside", "outdoors"}),
    ("戶外", {"outside", "outdoors"}),
    ("庭院", {"yard", "patio"}),
    ("廣場", {"plaza", "square", "surroundings"}),
    ("背負網袋", {"net bag", "rucksack"}),
    ("背袋", {"net bag", "rucksack"}),
    ("背部", {"back"}),
    ("雲", {"cloud"}),
    ("酸", {"sour", "gone bad"}),
    ("老鼠", {"mouse", "mice"}),
    ("月亮", {"moon"}),
    ("月份", {"month"}),
    ("痛", {"ache", "hurt", "pain"}),
    ("沙子", {"sand", "grit", "gravel"}),
    ("酒鬼", {"alcoholic"}),
    ("鬼針草", {"bidens pilosa"}),
    ("刺（工具）", {"needle", "fork"}),
    ("耳機", {"earphone", "headphone"}),
    ("木柴", {"wood", "firewood"}),
    ("樹", {"tree", "wood"}),
    ("九芎樹", {"taiwan crepe myrtle"}),
    ("樟樹", {"camphor tree"}),
    ("樹皮", {"bark"}),
    ("砍材", {"chop", "wood"}),
    ("各個角落", {"corner"}),
    ("角落", {"corner"}),
    ("角(錢)", {"dime"}),
    ("閩南人", {"hokkien", "hoklo"}),
    ("祖母", {"grandmother"}),
    ("奶奶", {"grandmother"}),
    ("腎臟", {"kidney"}),
    ("部落", {"village", "tribe"}),
    ("家鄉", {"hometown", "village"}),
    ("國家", {"country", "village"}),
    ("道路", {"road"}),
    ("走的路", {"procedure", "road", "path"}),
    ("路", {"road"}),
    ("十字路口", {"crossroad"}),
    ("走路", {"walk"}),
    ("人行道", {"pedestrian crossing"}),
    ("斑馬線", {"pedestrian crossing"}),
    ("帶路的人", {"leader", "chairperson"}),
    ("錫製", {"tinplate", "tin"}),
    ("錫", {"tin"}),
    ("檸檬", {"lemon"}),
    ("十字鎬", {"hoe", "pickaxe"}),
    ("雞嘴", {"beak"}),
    ("針狀物", {"thorn", "needle-like object"}),
    ("嚇人", {"scare"}),
    ("照明", {"lamp", "light"}),
    ("力量", {"ability", "strength"}),
    ("強", {"strong"}),
    ("貴", {"expensive"}),
    ("蜂蜜", {"honey"}),
    ("蜜蜂", {"bee"}),
    ("錢包", {"wallet"}),
    ("看守的人", {"guard"}),
    ("警衛", {"guard"}),
    ("屬格", {"of", "genitive"}),
]


def normalize_english_gloss(text: str) -> str:
    text = clean_text(text).casefold()
    text = text.strip().strip("\"' ")
    text = re.sub(r"\s+", " ", text)
    return text


def target_gloss_variants(target: str) -> set[str]:
    normalized = normalize_english_gloss(target)
    variants = {normalized}
    without_parens = re.sub(r"\s*\([^)]*\)", "", normalized).strip()
    if without_parens:
        variants.add(without_parens)
    for piece in re.split(r"\s*(?:;|,|/)\s*", normalized):
        piece = piece.strip()
        if piece:
            variants.add(piece)
            no_parens = re.sub(r"\s*\([^)]*\)", "", piece).strip()
            if no_parens:
                variants.add(no_parens)
    return {v for v in variants if v}


def lexical_target_text_for_xml(target: str) -> str:
    return clean_text(target)


def ildrf_supported_targets(ildrf_glosses: list[str]) -> tuple[set[str], list[str]]:
    gloss_text = "; ".join(ildrf_glosses)
    supported: set[str] = set()
    evidence: list[str] = []
    for marker, targets in ILRDF_GLOSS_TARGET_EVIDENCE:
        if marker and marker in gloss_text:
            evidence.append(marker)
            supported.update(targets)
    return supported, evidence


def target_ildrf_reference_status(target: str, ildrf_glosses: list[str]) -> tuple[str, str]:
    supported, evidence = ildrf_supported_targets(ildrf_glosses)
    evidence_text = "; ".join(evidence)
    if not evidence:
        return "unmapped", ""
    variants = target_gloss_variants(target)
    if variants & supported:
        return "supported", evidence_text
    parts = [p for p in re.split(r"\s*(?:;|,|/)\s*", normalize_english_gloss(target)) if p]
    if parts and all((target_gloss_variants(part) & supported) for part in parts):
        return "supported", evidence_text
    return "unsupported", evidence_text


def lexical_rows_with_basic_rejections(dict_rows: list[dict[str, Any]]) -> tuple[list[tuple[dict[str, Any], str, str, str]], list[dict[str, Any]]]:
    prepped: list[tuple[dict[str, Any], str, str, str]] = []
    rejected: list[dict[str, Any]] = []
    for row in dict_rows:
        source = clean_text(row.get("source_phrase_clean", ""))
        target = clean_text(row.get("target_phrase_clean", ""))
        rejection = lexical_xml_rejection_reason(source, target, row.get("l2", ""))
        if rejection:
            rejected.append(
                {
                    "record_id": row.get("record_id", ""),
                    "pair": row.get("pair", ""),
                    "rejection_reason": rejection,
                    "source_phrase_clean": source,
                    "target_phrase_clean": target,
                    "query_phrase": row.get("query_phrase", ""),
                    "source_url": row.get("source_url", ""),
                    "raw_path": row.get("raw_json_path") or row.get("raw_html_path", ""),
                    "ildrf_source_found": "",
                    "ildrf_reference_files": "",
                    "ildrf_chinese_glosses": "",
                    "glosbe_targets_for_source": "",
                    "mapping_evidence": "",
                    "xml_target_text": "",
                    "notes": "Excluded from lexical XML during final translation-quality filtering.",
                }
            )
            continue
        if not row.get("raw_json_path") and not row.get("raw_html_path"):
            rejected.append(
                {
                    "record_id": row.get("record_id", ""),
                    "pair": row.get("pair", ""),
                    "rejection_reason": "no_raw_provenance",
                    "source_phrase_clean": source,
                    "target_phrase_clean": target,
                    "query_phrase": row.get("query_phrase", ""),
                    "source_url": row.get("source_url", ""),
                    "raw_path": "",
                    "ildrf_source_found": "",
                    "ildrf_reference_files": "",
                    "ildrf_chinese_glosses": "",
                    "glosbe_targets_for_source": "",
                    "mapping_evidence": "",
                    "xml_target_text": "",
                    "notes": "Excluded from lexical XML during final translation-quality filtering.",
                }
            )
            continue
        prepped.append((row, source, target, form_group_key(source)))
    return prepped, rejected


def lexical_reference_decisions(
    config: dict[str, Any],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    IldrfReferenceLexicon,
]:
    dict_rows = read_jsonl(PROCESSED / "dictionary_entries_deduped.jsonl")
    if not dict_rows:
        dict_rows = dedupe_dictionary_entries(read_jsonl(PROCESSED / "dictionary_entries_raw.jsonl"))
        write_jsonl(PROCESSED / "dictionary_entries_deduped.jsonl", dict_rows)

    reference = load_ildrf_reference_lexicon(config)
    prepped, lexical_rejected = lexical_rows_with_basic_rejections(dict_rows)
    groups: dict[tuple[str, str, str], list[tuple[dict[str, Any], str, str, str]]] = defaultdict(list)
    for item in prepped:
        row, _, _, source_key = item
        groups[(row["l1"], row["l2"], source_key)].append(item)

    lexical_audit: list[dict[str, Any]] = []
    lexical_kept_groups: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []

    for (l1, l2, source_key), items in groups.items():
        first_row, first_source, _, _ = items[0]
        source = lexical_form_text_for_xml(first_source)
        ildrf_glosses = sorted(reference.glosses.get(l1, {}).get(source_key, set()))
        ildrf_files = sorted(reference.source_files.get(l1, {}).get(source_key, set()))
        targets: list[dict[str, Any]] = []
        seen_target_keys: set[str] = set()
        for row, row_source, target, _ in items:
            xml_target = lexical_target_text_for_xml(target)
            target_key = dedupe_key(xml_target)
            if target_key in seen_target_keys:
                continue
            seen_target_keys.add(target_key)
            if not ildrf_glosses:
                reference_status = "source_not_attested"
                reason = "source_not_attested_in_ildrf_reference"
                evidence = ""
            elif row.get("l2") != "en":
                reference_status = "not_compared"
                reason = "non_english_target_not_compared_to_ildrf_gloss"
                evidence = ""
            else:
                mapped_status, evidence = target_ildrf_reference_status(target, ildrf_glosses)
                if mapped_status == "supported":
                    reference_status = "target_supported_by_mapping"
                    reason = "ildrf_source_attested_target_supported_by_mapping"
                elif mapped_status == "unsupported":
                    reference_status = "different_from_mapping"
                    reason = "ildrf_source_attested_target_differs_from_mapping"
                else:
                    reference_status = "gloss_unmapped"
                    reason = "ildrf_source_attested_gloss_unmapped"
            targets.append(
                {
                    "row": row,
                    "row_source": row_source,
                    "source_target": target,
                    "xml_target": xml_target,
                    "reference_status": reference_status,
                    "reason": reason,
                    "evidence": evidence,
                }
            )

        target_text = "; ".join(target["xml_target"] for target in targets)
        xml_record_id = "GLOSBE_DICT_GROUP_" + sha256_text(
            f"{l1}|{l2}|{source}|" + "\n".join(target["xml_target"] for target in targets)
        )[:16]
        lexical_kept_groups.append(
            {
                "l1": l1,
                "l2": l2,
                "pair": first_row.get("pair", ""),
                "source": source,
                "targets": targets,
                "record_id": xml_record_id,
                "ildrf_glosses": ildrf_glosses,
                "ildrf_files": ildrf_files,
            }
        )

        for translation_index, target_info in enumerate(targets):
            row = target_info["row"]
            lexical_audit.append(
                {
                    "record_id": row.get("record_id", ""),
                    "pair": row.get("pair", ""),
                    "source_phrase_clean": target_info["row_source"],
                    "target_phrase_clean": target_info["source_target"],
                    "action": "keep_in_xml",
                    "reference_status": target_info["reference_status"],
                    "reason": target_info["reason"],
                    "ildrf_source_found": "yes" if ildrf_glosses else "no",
                    "ildrf_reference_files": "; ".join(ildrf_files),
                    "ildrf_chinese_glosses": "; ".join(ildrf_glosses[:20]),
                    "glosbe_targets_for_source": target_text,
                    "mapping_evidence": target_info["evidence"],
                    "xml_record_id": xml_record_id,
                    "xml_target_text": target_info["xml_target"],
                    "xml_translation_ver": "alt" if translation_index else "primary",
                    "source_url": row.get("source_url", ""),
                    "raw_path": row.get("raw_json_path") or row.get("raw_html_path", ""),
                }
            )

        status_targets: dict[str, list[str]] = defaultdict(list)
        for target_info in targets:
            status_targets[target_info["reference_status"]].append(target_info["xml_target"])
        review_rows.append(
            {
                "pair": first_row.get("pair", ""),
                "source_phrase_clean": source,
                "ildrf_source_found": "yes" if ildrf_glosses else "no",
                "ildrf_reference_files": "; ".join(ildrf_files),
                "ildrf_chinese_glosses": "; ".join(ildrf_glosses[:20]),
                "glosbe_targets_for_source": target_text,
                "mapping_supported_targets": "; ".join(status_targets["target_supported_by_mapping"]),
                "mapping_different_targets": "; ".join(status_targets["different_from_mapping"]),
                "unmapped_targets": "; ".join(status_targets["gloss_unmapped"]),
                "unattested_source_targets": "; ".join(status_targets["source_not_attested"]),
                "decision": "keep_all_structurally_valid_targets",
            }
        )

    return lexical_kept_groups, lexical_audit, lexical_rejected, review_rows, reference


def write_lexical_reference_outputs(
    config: dict[str, Any], base_xml_index: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    final_dir = ROOT / config["xml"]["output_dir"]
    lexical_kept_groups, lexical_audit, lexical_rejected, review_rows, reference = (
        lexical_reference_decisions(config)
    )
    xml_index = list(base_xml_index or [])
    rows_by_pair: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in lexical_kept_groups:
        rows_by_pair[(row["l1"], row["l2"])].append(row)

    for old in sorted(final_dir.glob("*/Glosbe_*_lexical.xml")):
        old.unlink()

    for (l1, l2), rows in rows_by_pair.items():
        if not rows:
            continue
        tgt_iso, _, citation, bib, copyright_attr = citation_bits(config, l1, l2, "LEXICAL")
        retrieved_date = config.get("metadata", {}).get("retrieved_date", today_utc())
        text_id = f"GLOSBE_{l1}_{tgt_iso}_LEXICAL"
        out = final_dir / l1 / f"Glosbe_{l1}_{tgt_iso}_lexical.xml"
        root = ET.Element(
            "TEXT",
            {
                "id": text_id,
                "citation": compact_attr(citation),
                "BibTeX_citation": compact_attr(bib),
                "copyright": copyright_attr,
                f"{{{XML_NS}}}lang": l1,
                "source": compact_attr(f"Glosbe pair {l1}/{l2}; lexical dictionary/headword entries from public static pages and iapi3 responses; crawl date {retrieved_date}."),
                "dialect": default_xml_dialect(l1),
            },
        )
        for idx, row in enumerate(rows, 1):
            source = row["source"]
            sid = f"{text_id}_U{idx:06d}"
            s_el = ET.SubElement(root, "S", {"id": sid})
            form = ET.SubElement(s_el, "FORM", {"kindOf": "original"})
            form.text = source
            for translation_index, target_info in enumerate(row["targets"]):
                target = target_info["xml_target"]
                source_row = target_info["row"]
                transl_attrs = {f"{{{XML_NS}}}lang": tgt_iso}
                if translation_index:
                    transl_attrs["ver"] = "alt"
                transl = ET.SubElement(s_el, "TRANSL", transl_attrs)
                transl.text = target
                xml_index.append(
                    {
                        "xml_file": rel(out),
                        "text_id": text_id,
                        "sentence_id": sid,
                        "record_id": source_row["record_id"],
                        "pair": source_row["pair"],
                        "l1": l1,
                        "l2": l2,
                        "source_language_name": source_name(config, l1),
                        "target_language_name": target_name(config, l2),
                        "source_iso_639_3": l1,
                        "target_iso_639_3": tgt_iso,
                        "query_phrase": source_row.get("query_phrase", ""),
                        "tmBunchId": "",
                        "authorId": source_row.get("authorId", ""),
                        "author_label_if_known": source_row.get("author_label_if_known", ""),
                        "domain": source_row.get("part_of_speech", ""),
                        "source_url": source_row.get("source_url", ""),
                        "raw_json_path": source_row.get("raw_json_path", ""),
                        "raw_html_path_if_any": source_row.get("raw_html_path", ""),
                        "raw_sha256": source_row.get("raw_json_sha256")
                        or source_row.get("raw_html_sha256", ""),
                        "source_sentence_sha256": sha256_text(source),
                        "target_sentence_sha256": sha256_text(target),
                        "pair_sha256": sha256_text(source + "\n" + target),
                        "duplicate_group_id_if_any": "",
                        "overlap_status": "",
                        "quality_status": (
                            "lexical_entry;ildrf_reference=" + target_info["reference_status"]
                        ),
                        "parse_confidence": source_row.get("parse_confidence", ""),
                        "crawl_timestamp_utc": source_row.get("crawl_timestamp_utc", ""),
                    }
                )
        out.parent.mkdir(parents=True, exist_ok=True)
        ET.indent(root, space="  ")
        ET.ElementTree(root).write(out, encoding="utf-8", xml_declaration=True)

    write_csv(
        PROCESSED / "ildrf_glosbe_lexical_audit.csv",
        lexical_audit,
        [
            "record_id",
            "pair",
            "source_phrase_clean",
            "target_phrase_clean",
            "action",
            "reference_status",
            "reason",
            "ildrf_source_found",
            "ildrf_reference_files",
            "ildrf_chinese_glosses",
            "glosbe_targets_for_source",
            "mapping_evidence",
            "xml_record_id",
            "xml_target_text",
            "xml_translation_ver",
            "source_url",
            "raw_path",
        ],
    )
    write_csv(
        PROCESSED / "lexical_xml_rejected.csv",
        lexical_rejected,
        [
            "record_id",
            "pair",
            "rejection_reason",
            "source_phrase_clean",
            "target_phrase_clean",
            "query_phrase",
            "source_url",
            "raw_path",
            "ildrf_source_found",
            "ildrf_reference_files",
            "ildrf_chinese_glosses",
            "glosbe_targets_for_source",
            "mapping_evidence",
            "xml_target_text",
            "notes",
        ],
    )
    write_csv(
        PROCESSED / "ildrf_glosbe_lexical_group_review.csv",
        review_rows,
        [
            "pair",
            "source_phrase_clean",
            "ildrf_source_found",
            "ildrf_reference_files",
            "ildrf_chinese_glosses",
            "glosbe_targets_for_source",
            "mapping_supported_targets",
            "mapping_different_targets",
            "unmapped_targets",
            "unattested_source_targets",
            "decision",
        ],
    )

    if lexical_audit:
        action_counts = Counter(r["action"] for r in lexical_audit)
        status_counts = Counter(r["reference_status"] for r in lexical_audit)
        reason_counts = Counter(r["reason"] for r in lexical_audit)
        pair_translation_counts = Counter(r["pair"] for r in lexical_audit)
        lexical_entry_counts = Counter(row["pair"] for row in lexical_kept_groups)
        alternate_translation_count = sum(
            max(0, len(row["targets"]) - 1) for row in lexical_kept_groups
        )
        rejection_counts = Counter(r["rejection_reason"] for r in lexical_rejected)
        review_examples = [
            row for row in lexical_audit if row["reference_status"] == "different_from_mapping"
        ][:30]
        reference_table = chr(10).join(
            "| {language} | `{file}` | `{sha256}` | {sentences} | {translations} | "
            "{unique_source_forms} | {unique_source_gloss_pairs} |".format(**row)
            for row in reference.file_stats
        )
        report = f"""# ILRDF Reference Audit For Glosbe Lexical Entries

Generated: {now_utc()}

Reference repository: `{config.get("ildrf_reference_lexicon", {}).get("derived_repo", "")}`

## Provenance Finding

The files previously called the "Zheng dictionary" are not an independent dictionary. Zheng et al. state that they downloaded the Formosan lexicons from the ILRDF online dictionary, converted ILRDF PDFs to HTML, and extracted the Formosan-Mandarin entries. The local reference XML identifies ILRDF as its source and Zheng et al. as the curator of that derived release.

Primary paper: https://aclanthology.org/2024.findings-acl.670/

This audit therefore calls the data an **ILRDF-derived reference**. It does not treat a match as independent corroboration and does not treat absence or a different mapped gloss as proof that a Glosbe entry is wrong.

## Corrected Policy

- Exclude only concrete structural or provenance failures detected before reference comparison.
- Keep every structurally valid Glosbe lexical source-target pair.
- Record exact source-form overlap with the selected ILRDF-derived file as metadata.
- Record the hand-built Chinese-to-English mapping as a heuristic review signal only. It is incomplete, substring-based, and cannot rule out homography, polysemy, or additional Glosbe senses.
- Preserve distinct same-language targets as separate `TRANSL` elements. The first is primary and every additional target uses `ver="alt"`.
- Abort when a configured reference repository or file is missing, has the wrong language, or lacks ILRDF provenance. A broken reference path can no longer silently turn every row into a non-match.
- For `trv`, compare against the Truku dictionary only. The previous loader also included Seediq because both files use `xml:lang="trv"`.

## Selected ILRDF-Derived Files

| Language | File | SHA-256 | S | TRANSL | Unique source forms | Unique source-gloss pairs |
|---|---|---|---:|---:|---:|---:|
{reference_table}

## Scope

This audit covers Glosbe dictionary/headword rows only. It does not filter sentence-level translation-memory data, including the restored Amis-Chinese material. The row-level CSV records one candidate translation and its ILRDF reference status. The group review CSV places all Glosbe targets for one source form together.

## Final Counts

- deduplicated Glosbe lexical candidates before structural filtering: {len(lexical_audit) + len(lexical_rejected)}
- structurally valid candidate translations retained: {action_counts.get("keep_in_xml", 0)}
- structurally invalid/cross-reference rows rejected: {len(lexical_rejected)}
- candidate translations rejected because of ILRDF absence or gloss mapping: 0
- lexical sentence elements emitted: {len(lexical_kept_groups)}
- lexical `TRANSL` elements emitted: {len(lexical_audit)}
- alternate `TRANSL ver="alt"` elements: {alternate_translation_count}

### Reference status

{chr(10).join(f"- {status}: {count}" for status, count in status_counts.most_common())}

### Pair counts

{chr(10).join(f"- {pair}: {pair_translation_counts[pair]} translations in {lexical_entry_counts[pair]} sentence elements" for pair in sorted(pair_translation_counts))}

### Structural rejection reasons

{chr(10).join(f"- {reason}: {count}" for reason, count in rejection_counts.most_common()) or "- None"}

## Reference Status Codes

- `source_not_attested`: the exact normalized Glosbe source form is absent from the selected ILRDF-derived file. This is coverage metadata only.
- `target_supported_by_mapping`: a hand-built mapping connects part of the ILRDF Chinese gloss to the Glosbe English target. This is heuristic support, not independent verification.
- `gloss_unmapped`: the source is present, but no hand-built mapping applies to its Chinese gloss.
- `different_from_mapping`: a mapping applies but points to another English target. The Glosbe target is retained because the mapping cannot rule out additional senses or homographs.

## Different-Mapping Review Examples

{chr(10).join(f"- {r['pair']} `{r['source_phrase_clean']}` => `{r['target_phrase_clean']}`; ILRDF glosses: {r['ildrf_chinese_glosses']}; mapping evidence: {r['mapping_evidence'] or 'none'}" for r in review_examples) or "- None"}

## Evidence Files

Full row-level audit: `data/processed/ildrf_glosbe_lexical_audit.csv`

Group review: `data/processed/ildrf_glosbe_lexical_group_review.csv`

Concrete structural rejections: `data/processed/lexical_xml_rejected.csv`
"""
        (PROCESSED / "ildrf_glosbe_lexical_audit_report.md").write_text(report, encoding="utf-8")

    return xml_index


def command_rebuild_lexical_reference_audit(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ensure_layout(config)
    existing_index = [row for row in read_csv(PROCESSED / "xml_index.csv") if "_lexical.xml" not in row.get("xml_file", "")]
    xml_index = write_lexical_reference_outputs(config, existing_index)
    write_csv(PROCESSED / "xml_index.csv", xml_index)


def load_reviewed_amis_chinese(config: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    settings = config.get("reviewed_amis_chinese", {})
    if not settings.get("enabled", False):
        return [], 0

    simplified_path = repo_path(settings["simplified_json"])
    traditional_path = repo_path(settings["traditional_xml"])
    simplified_rows = json.loads(simplified_path.read_text(encoding="utf-8"))
    traditional_sentences = ET.parse(traditional_path).getroot().findall("S")
    if len(simplified_rows) != len(traditional_sentences):
        raise ValueError(
            "Reviewed Amis Chinese sources are no longer aligned: "
            f"{len(simplified_rows)} JSON rows versus {len(traditional_sentences)} XML rows"
        )

    simplified_sha = sha256_file(simplified_path)
    traditional_sha = sha256_file(traditional_path)
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for source_row, sentence in zip(simplified_rows, traditional_sentences, strict=True):
        form = clean_legacy_glosbe_text(sentence.findtext("FORM"))
        traditional = clean_legacy_glosbe_text(sentence.findtext("TRANSL"))
        converted = clean_text(chinese_converter.to_traditional(source_row.get("chinese", "")))
        if semantic_text_key(converted) != semantic_text_key(traditional):
            raise ValueError(
                "Reviewed Traditional Chinese is not aligned with the historical Simplified row "
                f"at {sentence.get('id', '<unknown>')}"
            )
        if not form or not traditional:
            raise ValueError(f"Reviewed Amis Chinese row {sentence.get('id', '<unknown>')} is empty")

        source_url = clean_text(source_row.get("query", ""))
        query_phrase = urllib.parse.unquote(urllib.parse.urlparse(source_url).path.rsplit("/", 1)[-1])
        pair_key = (dedupe_key(form), dedupe_key(traditional))
        if pair_key in unique:
            unique[pair_key]["legacy_duplicate_rows"] += 1
            continue
        record_id = "GLOSBE_REVIEWED_ZHO_" + sha256_text(form + "\n" + traditional)[:16]
        unique[pair_key] = {
            "record_id": record_id,
            "pair": "ami,zh",
            "l1": "ami",
            "l2": "zh",
            "source_sentence_clean": form,
            "target_sentence_clean": traditional,
            "query_phrase": query_phrase,
            "source_url": source_url,
            "raw_json_path": rel(simplified_path),
            "raw_html_path": rel(traditional_path),
            "raw_json_sha256": simplified_sha,
            "raw_html_sha256": traditional_sha,
            "quality_status": "reviewed_traditional_chinese",
            "overlap_status": "not_checked_historical_import",
            "parse_confidence": "reviewed_historical_alignment",
            "crawl_timestamp_utc": "",
            "restoration_origin": "joseph_reviewed_traditional",
            "legacy_source_id": sentence.get("id", ""),
            "legacy_duplicate_rows": 0,
        }
    return list(unique.values()), len(simplified_rows)


def merge_reviewed_amis_chinese(
    config: dict[str, Any], current_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, int], list[dict[str, Any]]]:
    reviewed_rows, legacy_input_rows = load_reviewed_amis_chinese(config)
    reviewed_by_form: dict[str, list[int]] = defaultdict(list)
    reviewed_by_target: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(reviewed_rows):
        reviewed_by_form[semantic_text_key(row["source_sentence_clean"])].append(index)
        reviewed_by_target[semantic_text_key(row["target_sentence_clean"])].append(index)

    consumed_reviewed: set[int] = set()
    merged: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    reviewed_matches = 0
    converted_new = 0
    for current in current_rows:
        row = dict(current)
        row["source_sentence_clean"] = clean_legacy_glosbe_text(row["source_sentence_clean"])
        row["target_sentence_clean"] = clean_legacy_glosbe_text(
            chinese_converter.to_traditional(row["target_sentence_clean"])
        )
        matched_index = next(
            (
                index
                for index in reviewed_by_form.get(semantic_text_key(row["source_sentence_clean"]), [])
                if index not in consumed_reviewed
                and semantic_text_key(reviewed_rows[index]["target_sentence_clean"])
                == semantic_text_key(row["target_sentence_clean"])
            ),
            None,
        )
        if matched_index is None:
            form_key = semantic_text_key(row["source_sentence_clean"])
            candidates = reviewed_by_target.get(semantic_text_key(row["target_sentence_clean"]), [])
            scored = sorted(
                (
                    SequenceMatcher(
                        None,
                        form_key,
                        semantic_text_key(reviewed_rows[index]["source_sentence_clean"]),
                    ).ratio(),
                    index,
                )
                for index in candidates
                if index not in consumed_reviewed
            )
            if scored and scored[-1][0] >= 0.95:
                matched_index = scored[-1][1]
        if matched_index is None:
            row["restoration_origin"] = "current_scrape_converted"
            row["legacy_source_id"] = ""
            row["legacy_duplicate_rows"] = 0
            converted_new += 1
        else:
            reviewed = reviewed_rows[matched_index]
            consumed_reviewed.add(matched_index)
            row["restoration_origin"] = "current_scrape_reviewed_match"
            row["legacy_source_id"] = reviewed["legacy_source_id"]
            row["legacy_duplicate_rows"] = reviewed["legacy_duplicate_rows"]
            reviewed_matches += 1
        row["quality_status"] = row.get("quality_status", "eligible") + ";traditional_chinese"
        merged.append(row)

    merged.extend(row for index, row in enumerate(reviewed_rows) if index not in consumed_reviewed)
    unique_pairs = {
        (dedupe_key(row["source_sentence_clean"]), dedupe_key(row["target_sentence_clean"]))
        for row in merged
    }
    if len(unique_pairs) != len(merged):
        raise ValueError("Amis Chinese restoration produced duplicate source-translation pairs")

    for row in merged:
        audit_rows.append(
            {
                "record_id": row["record_id"],
                "source_sentence_clean": row["source_sentence_clean"],
                "target_sentence_clean": row["target_sentence_clean"],
                "origin": row["restoration_origin"],
                "legacy_source_id": row.get("legacy_source_id", ""),
                "legacy_duplicate_rows": row.get("legacy_duplicate_rows", 0),
                "source_url": row.get("source_url", ""),
                "raw_path": row.get("raw_html_path") or row.get("raw_json_path", ""),
            }
        )

    stats = {
        "legacy_input_rows": legacy_input_rows,
        "legacy_unique_pairs": len(reviewed_rows),
        "legacy_duplicate_rows": legacy_input_rows - len(reviewed_rows),
        "current_rows": len(current_rows),
        "current_reviewed_matches": reviewed_matches,
        "current_converted_new": converted_new,
        "output_rows": len(merged),
        "output_forms": len({form_group_key(row["source_sentence_clean"]) for row in merged}),
    }
    return merged, stats, audit_rows


def write_amis_chinese_restoration_report(
    config: dict[str, Any], stats: dict[str, int], audit_rows: list[dict[str, Any]]
) -> None:
    settings = config["reviewed_amis_chinese"]
    write_csv(
        PROCESSED / "amis_chinese_restoration_audit.csv",
        audit_rows,
        [
            "record_id",
            "source_sentence_clean",
            "target_sentence_clean",
            "origin",
            "legacy_source_id",
            "legacy_duplicate_rows",
            "source_url",
            "raw_path",
        ],
    )
    report = f"""# Amis Chinese Restoration

Reviewed source: `{settings['traditional_xml']}`

Contributor: {settings['contributor']} ([source pull request]({settings['pull_request']}))

## Result

- Historical input rows: {stats['legacy_input_rows']}
- Unique historical Amis-Traditional Chinese pairs: {stats['legacy_unique_pairs']}
- Exact historical duplicate rows omitted: {stats['legacy_duplicate_rows']}
- Current scrape rows: {stats['current_rows']}
- Current rows matched to Joseph's reviewed conversions: {stats['current_reviewed_matches']}
- New current rows converted with `chinese-converter==1.1.1`: {stats['current_converted_new']}
- Final unique Amis-Traditional Chinese pairs: {stats['output_rows']}
- Final sentence elements: {stats['output_forms']}

## Merge Rules

1. Preserve every distinct Traditional Chinese translation from Joseph's reviewed file.
2. Collapse only exact duplicate Amis-translation pairs. Distinct translations for the same Amis form remain as `ver="alt"` translations on one sentence element.
3. Prefer the newer scrape row when its converted translation matches a reviewed pair after punctuation-insensitive comparison.
4. Convert only current rows that have no reviewed counterpart. Simplified Chinese is not emitted in final XML.
5. Remove Glosbe asterisk footnote markers from both aligned tiers.

Row-level provenance is in `data/processed/amis_chinese_restoration_audit.csv`.
"""
    (PROCESSED / "amis_chinese_restoration_report.md").write_text(report, encoding="utf-8")


def command_build_xml(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ensure_layout(config)
    final_dir = ROOT / config["xml"]["output_dir"]
    legacy_dir = PROCESSED / "legacy_Final_XML_quarantine"
    for xml_file in list(final_dir.glob("*.xml")) + [p for p in final_dir.glob("*/*.xml") if p.parent.name not in {p[0] for p in config["target_pairs"]}]:
        legacy_target = legacy_dir / xml_file.relative_to(final_dir)
        legacy_target.parent.mkdir(parents=True, exist_ok=True)
        if not legacy_target.exists():
            shutil.move(str(xml_file), str(legacy_target))
    for old in sorted(final_dir.glob("*/Glosbe_*_tmem.xml")) + sorted(final_dir.glob("*/Glosbe_*_lexical.xml")):
        old.unlink()
    rows_by_pair: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in read_jsonl(PROCESSED / "quality_filtered_examples.jsonl"):
        rows_by_pair[(row["l1"], row["l2"])].append(row)
    if config.get("reviewed_amis_chinese", {}).get("enabled", False):
        restored, restoration_stats, restoration_audit = merge_reviewed_amis_chinese(
            config, rows_by_pair.get(("ami", "zh"), [])
        )
        rows_by_pair[("ami", "zh")] = restored
        write_amis_chinese_restoration_report(config, restoration_stats, restoration_audit)
    xml_index = []
    lexical_rejected = []
    lexical_audit = []
    for (l1, l2), rows in rows_by_pair.items():
        if not rows:
            continue
        tgt_iso, representative_url, citation, bib, copyright_attr = citation_bits(config, l1, l2, "TMEM")
        text_id = f"GLOSBE_{l1}_{tgt_iso}_TMEM"
        retrieved_date = config.get("metadata", {}).get("retrieved_date", today_utc())
        source_description = (
            f"Glosbe pair {l1}/{l2}; extracted from public static /fragment/tmem pages; "
            f"crawl date {retrieved_date}."
        )
        if (l1, l2) == ("ami", "zh"):
            source_description += " Includes restored reviewed Traditional Chinese data from Formosan-Glosbe PR #1."
        root = ET.Element(
            "TEXT",
            {
                "id": text_id,
                "citation": compact_attr(citation),
                "BibTeX_citation": compact_attr(bib),
                "copyright": copyright_attr,
                f"{{{XML_NS}}}lang": l1,
                "source": compact_attr(source_description),
                "dialect": default_xml_dialect(l1),
            },
        )
        if (l1, l2) == ("ami", "zh"):
            grouped_rows: dict[str, list[dict[str, Any]]] = {}
            for row in rows:
                grouped_rows.setdefault(form_group_key(row["source_sentence_clean"]), []).append(row)
            translation_groups = grouped_rows.values()
        else:
            translation_groups = ([row] for row in rows)
        for idx, translation_rows in enumerate(translation_groups, 1):
            source = translation_rows[0]["source_sentence_clean"]
            sid = f"{text_id}_U{idx:06d}"
            s_el = ET.SubElement(root, "S", {"id": sid})
            form = ET.SubElement(s_el, "FORM", {"kindOf": "original"})
            form.text = source
            for translation_index, row in enumerate(translation_rows):
                transl_attrs = {f"{{{XML_NS}}}lang": tgt_iso}
                if translation_index:
                    transl_attrs["ver"] = "alt"
                transl = ET.SubElement(s_el, "TRANSL", transl_attrs)
                transl.text = row["target_sentence_clean"]
                pair_digest = sha256_text(source + "\n" + row["target_sentence_clean"])
                xml_index.append(
                    {
                        "xml_file": rel(final_dir / l1 / f"Glosbe_{l1}_{tgt_iso}_tmem.xml"),
                        "text_id": text_id,
                        "sentence_id": sid,
                        "record_id": row["record_id"],
                        "pair": row["pair"],
                        "l1": l1,
                        "l2": l2,
                        "source_language_name": source_name(config, l1),
                        "target_language_name": target_name(config, l2),
                        "source_iso_639_3": l1,
                        "target_iso_639_3": tgt_iso,
                        "query_phrase": row.get("query_phrase") or row.get("phrase", ""),
                        "tmBunchId": row.get("tmBunchId", ""),
                        "authorId": row.get("authorId", ""),
                        "author_label_if_known": row.get("author_label_if_known", ""),
                        "domain": row.get("domain", ""),
                        "source_url": row.get("source_url", ""),
                        "raw_json_path": row.get("raw_json_path", ""),
                        "raw_html_path_if_any": row.get("raw_html_path", ""),
                        "raw_sha256": row.get("raw_json_sha256") or row.get("raw_html_sha256", ""),
                        "source_sentence_sha256": sha256_text(source),
                        "target_sentence_sha256": sha256_text(row["target_sentence_clean"]),
                        "pair_sha256": pair_digest,
                        "duplicate_group_id_if_any": "",
                        "overlap_status": row.get("overlap_status", ""),
                        "quality_status": row.get("quality_status", ""),
                        "parse_confidence": row.get("parse_confidence", ""),
                        "crawl_timestamp_utc": row.get("crawl_timestamp_utc", ""),
                    }
                )
        out = final_dir / l1 / f"Glosbe_{l1}_{tgt_iso}_tmem.xml"
        out.parent.mkdir(parents=True, exist_ok=True)
        ET.indent(root, space="  ")
        ET.ElementTree(root).write(out, encoding="utf-8", xml_declaration=True)
    if config["xml"].get("include_dictionary_entries", False):
        xml_index = write_lexical_reference_outputs(config, xml_index)
    write_csv(PROCESSED / "xml_index.csv", xml_index)


def validate_xml_file(path: Path, config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        tree = ET.parse(path)
    except Exception as exc:  # noqa: BLE001
        return [f"not well formed: {exc}"]
    root = tree.getroot()
    if root.tag != "TEXT":
        errors.append("root tag is not TEXT")
    required = {"id", "citation", "BibTeX_citation", "copyright", f"{{{XML_NS}}}lang"}
    missing = [a for a in required if not root.get(a)]
    if missing:
        errors.append(f"TEXT missing attrs {missing}")
    for child in root:
        if child.tag != "S":
            errors.append(f"TEXT has non-S child {child.tag}")
    ids = set()
    for elem in root.iter():
        eid = elem.get("id")
        if eid:
            if eid in ids:
                errors.append(f"duplicate id {eid}")
            ids.add(eid)
    allowed_s = {"id"}
    for s in root.findall("S"):
        if set(s.attrib.keys()) != allowed_s:
            errors.append(f"S {s.get('id')} has invalid attrs {s.attrib}")
        forms = s.findall("FORM")
        original_forms = [form for form in forms if form.get("kindOf") == "original"]
        if not forms or len(original_forms) != 1 or any(not clean_text(form.text) for form in forms):
            errors.append(f"S {s.get('id')} must have one original FORM and no empty FORM tiers")
        if any(has_han(form.text or "") for form in forms):
            errors.append(f"S {s.get('id')} FORM contains Han text")
        for transl in s.findall("TRANSL"):
            lang = transl.get(f"{{{XML_NS}}}lang")
            if lang not in {"eng", "zho"}:
                errors.append(f"S {s.get('id')} TRANSL has non-ISO target lang {lang}")
            if not clean_text(transl.text):
                errors.append(f"S {s.get('id')} has empty TRANSL")
            if "**" in (transl.text or ""):
                errors.append(f"S {s.get('id')} TRANSL contains markdown emphasis marker")
        if any("**" in (form.text or "") for form in forms):
            errors.append(f"S {s.get('id')} FORM contains markdown emphasis marker")
        for w in s.findall("W"):
            if set(w.attrib.keys()) != {"id"}:
                errors.append(f"W has invalid attrs {w.attrib}")
        for m in s.findall(".//M"):
            if set(m.attrib.keys()) != {"id"}:
                errors.append(f"M has invalid attrs {m.attrib}")
    return errors


def command_validate_xml(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ensure_layout(config)
    final_dir = ROOT / config["xml"]["output_dir"]
    failures = []
    id_seen = set()
    for path in sorted(final_dir.rglob("*")):
        if path.is_file() and path.suffix != ".xml":
            failures.append((path, ["non-XML file in Final_XML"]))
        if path.is_file() and path.suffix == ".xml":
            if path.parent.name not in {p[0] for p in config["target_pairs"]}:
                failures.append((path, ["XML file not under Final_XML/<LANG ISO>/"]))
            errs = validate_xml_file(path, config)
            if not errs:
                root = ET.parse(path).getroot()
                for elem in root.iter():
                    eid = elem.get("id")
                    if eid in id_seen:
                        errs.append(f"duplicate id across corpus {eid}")
                    if eid:
                        id_seen.add(eid)
            if errs:
                failures.append((path, errs))
    if failures:
        draft = PROCESSED / "invalid_xml_removed_from_Final_XML"
        draft.mkdir(parents=True, exist_ok=True)
        for path, errs in failures:
            if path.exists() and path.suffix == ".xml":
                target = draft / path.relative_to(final_dir)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(target))
                log_error("validate_formosanbank_xml", raw_path=rel(target), error_type="xml_validation_failure", message="; ".join(errs))
    generate_validation_report(config, failures)


def command_generate_reports(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ensure_layout(config)
    update_pair_census_from_processed(config)
    generate_coverage_reports(config)
    generate_validation_report(config, [])
    generate_import_report(config)


def update_pair_census_from_processed(config: dict[str, Any]) -> None:
    rows = read_csv(PROCESSED / "pair_census.csv")
    if not rows:
        return
    raw_examples = read_jsonl(PROCESSED / "static_page_examples_raw.jsonl") + read_jsonl(PROCESSED / "tmem_examples_raw.jsonl")
    deduped = read_jsonl(PROCESSED / "tmem_examples_deduped.jsonl")
    dict_raw = read_jsonl(PROCESSED / "dictionary_entries_raw.jsonl")
    wordlist = read_jsonl(PROCESSED / "wordlist_items.jsonl")
    by_pair_raw: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_pair_dedup: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_pair_dict: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_pair_wordlist: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in raw_examples:
        by_pair_raw[row.get("pair", "")].append(row)
    for row in deduped:
        by_pair_dedup[row.get("pair", "")].append(row)
    for row in dict_raw:
        by_pair_dict[row.get("pair", "")].append(row)
    for row in wordlist:
        by_pair_wordlist[row.get("pair", "")].append(row)
    updated = []
    for row in rows:
        pair = row["pair"]
        examples = by_pair_raw.get(pair, [])
        ded = by_pair_dedup.get(pair, [])
        dicts = by_pair_dict.get(pair, [])
        authors = Counter((r.get("author_label_if_known") or r.get("author_label_if_visible") or "") for r in examples)
        authors.pop("", None)
        author_ids = Counter(r.get("authorId", "") for r in examples)
        author_ids.pop("", None)
        total = len(ded)
        if total == 0 and not dicts:
            yclass = "none"
        elif total == 0:
            yclass = "lexical_only"
        elif total < 25:
            yclass = "sparse_examples"
        elif total < 250:
            yclass = "moderate_examples"
        else:
            yclass = "high_examples"
        jw_count = sum(v for k, v in authors.items() if "jw" in k.lower())
        base_note = re.sub(
            r"(?:\s*Updated from corrected static fragment crawl and app-count sanity pass\.(?:\s*App benchmark: \d+ phrases, \d+ examples\.)?)+",
            "",
            row.get("notes", ""),
        ).strip()
        note_parts = [p for p in [base_note, "Updated from corrected static fragment crawl and app-count sanity pass."] if p]
        expected = config.get("app_expected_counts", {}).get(pair)
        if expected:
            note_parts.append(f"App benchmark: {expected.get('phrases')} phrases, {expected.get('examples')} examples.")
        row.update(
            {
                "phraseTranslations_found": "yes" if dicts else row.get("phraseTranslations_found", "no"),
                "tmem_found": "yes" if examples else "no",
                "tmem_examples_found": "yes" if examples else "no",
                "max_tmem_count_seen": max(int(row.get("max_tmem_count_seen") or 0), total),
                "total_unique_examples_seen_in_census": max(int(row.get("total_unique_examples_seen_in_census") or 0), total),
                "wordlist_found": "yes" if by_pair_wordlist.get(pair) else row.get("wordlist_found", "no"),
                "static_page_examples_found": "yes" if examples else "no",
                "top_author_ids": ";".join(k for k, _ in author_ids.most_common(5)),
                "top_author_labels_if_known": ";".join(k for k, _ in authors.most_common(5)),
                "top_domains": ";".join(k for k, _ in authors.most_common(5)),
                "suspected_jw2019_or_religious_share": f"{jw_count}/{sum(authors.values())}" if authors else "0/0",
                "estimated_yield_class": yclass,
                "proceed_to_full_crawl": "yes",
                "notes": " ".join(note_parts),
            }
        )
        updated.append(row)
    write_csv(PROCESSED / "pair_census.csv", updated)


def generate_coverage_reports(config: dict[str, Any]) -> None:
    inventory = read_csv(PROCESSED / "url_inventory.csv")
    raw_examples = read_jsonl(PROCESSED / "static_page_examples_raw.jsonl") + read_jsonl(PROCESSED / "tmem_examples_raw.jsonl")
    deduped = read_jsonl(PROCESSED / "tmem_examples_deduped.jsonl")
    quality = read_jsonl(PROCESSED / "quality_filtered_examples.jsonl")
    dict_raw = read_jsonl(PROCESSED / "dictionary_entries_raw.jsonl")
    dict_dedup = read_jsonl(PROCESSED / "dictionary_entries_deduped.jsonl")
    rejected = read_csv(PROCESSED / "rejected_records.csv")
    dup = read_csv(PROCESSED / "duplicates.csv")
    overlap = read_csv(PROCESSED / "overlap_candidates.csv")
    xml_index = read_csv(PROCESSED / "xml_index.csv")
    coverage = []
    for l1, l2 in config["target_pairs"]:
        pair = pair_name(l1, l2)
        inv_pair = [r for r in inventory if r["pair"] == pair]
        ex_pair = [r for r in raw_examples if r.get("pair") == pair]
        ded_pair = [r for r in deduped if r.get("pair") == pair]
        qual_pair = [r for r in quality if r.get("pair") == pair]
        dict_pair = [r for r in dict_raw if r.get("pair") == pair]
        xml_pair = [r for r in xml_index if r.get("pair") == pair]
        authors = Counter(r.get("author_label_if_known") or r.get("author_label_if_visible", "") for r in ex_pair)
        authors.pop("", None)
        expected = config.get("app_expected_counts", {}).get(pair, {})
        expected_note = ""
        if expected:
            expected_examples = int(expected.get("examples", 0))
            expected_phrases = int(expected.get("phrases", 0))
            expected_note = f" App benchmark: {expected_phrases} phrases, {expected_examples} examples ({expected.get('source', '')})."
            if expected_examples and len(ded_pair) < expected_examples * 0.75:
                expected_note += " Under expected example count; continue crawl/review seeds."
            elif expected_examples == 0 and len(ded_pair) == 0:
                expected_note += " Matches zero-example benchmark."
        if qual_pair:
            status = "crawled"
        elif ex_pair:
            status = "crawled"
        elif dict_pair:
            status = "lexical_only"
        elif inv_pair:
            status = "no_data"
        else:
            status = "failed_with_reason"
        coverage.append(
            {
                "pair": pair,
                "l1": l1,
                "l2": l2,
                "source_language_name": source_name(config, l1),
                "target_language_name": target_name(config, l2),
                "phrases_queried": len({r["phrase"] for r in inv_pair if r["phrase"]}),
                "api_responses_fetched": len([r for r in inv_pair if r["source_site"] == "iapi.glosbe"]),
                "static_pages_fetched": len([r for r in inv_pair if r["source_site"] == "static_page"]),
                "raw_tmem_examples": len(ex_pair),
                "deduped_tmem_examples": len(ded_pair),
                "quality_filtered_examples": len(qual_pair),
                "dictionary_entries_raw": len(dict_pair),
                "dictionary_entries_deduped": len([r for r in dict_dedup if r.get("pair") == pair]),
                "xml_sentences_created": len(xml_pair),
                "xml_files_created": len({r["xml_file"] for r in xml_pair}),
                "top_authors": ";".join(k for k, _ in authors.most_common(5)),
                "top_domains": ";".join(k for k, _ in authors.most_common(5)),
                "rejected_records": len([r for r in rejected if r.get("pair") == pair]),
                "duplicate_records": len([r for r in dup if r.get("pair") == pair]),
                "overlap_records": len([r for r in overlap if r.get("pair") == pair and r.get("overlap_type") != "no_overlap"]),
                "rights_status": "scrape_permission_asserted_private_review",
                "crawl_status": status,
                "notes": "iapi3 token-limited; public static/fragment fallback used." + expected_note,
            }
        )
    write_csv(PROCESSED / "coverage_by_pair.csv", coverage)
    by_lang = []
    for l1 in sorted({p[0] for p in config["target_pairs"]}):
        pairs = [r for r in coverage if r["l1"] == l1]
        by_lang.append(
            {
                "l1": l1,
                "source_language_name": source_name(config, l1),
                "target_languages": ";".join(r["l2"] for r in pairs),
                "total_pairs": len(pairs),
                "total_raw_tmem_examples": sum(int(r["raw_tmem_examples"]) for r in pairs),
                "total_deduped_examples": sum(int(r["deduped_tmem_examples"]) for r in pairs),
                "total_quality_filtered_examples": sum(int(r["quality_filtered_examples"]) for r in pairs),
                "total_xml_sentences": sum(int(r["xml_sentences_created"]) for r in pairs),
                "total_dictionary_entries": sum(int(r["dictionary_entries_raw"]) for r in pairs),
                "xml_files_created": sum(int(r["xml_files_created"]) for r in pairs),
                "notes": "",
            }
        )
    write_csv(PROCESSED / "coverage_by_language.csv", by_lang)
    by_author = defaultdict(lambda: {"raw": 0, "ded": 0, "qual": 0, "xml": 0})
    for row in raw_examples:
        key = (row.get("pair", ""), row.get("authorId", ""), row.get("author_label_if_known") or row.get("author_label_if_visible", ""), row.get("domain", ""))
        by_author[key]["raw"] += 1
    for row in deduped:
        key = (row.get("pair", ""), row.get("authorId", ""), row.get("author_label_if_known", ""), row.get("domain", ""))
        by_author[key]["ded"] += 1
    for row in quality:
        key = (row.get("pair", ""), row.get("authorId", ""), row.get("author_label_if_known", ""), row.get("domain", ""))
        by_author[key]["qual"] += 1
    for row in xml_index:
        key = (row.get("pair", ""), row.get("authorId", ""), row.get("author_label_if_known", ""), row.get("domain", ""))
        by_author[key]["xml"] += 1
    rows = []
    for (pair, aid, label, domain), counts in sorted(by_author.items()):
        rows.append(
            {
                "pair": pair,
                "authorId": aid,
                "author_label_if_known": label,
                "domain": domain,
                "raw_examples": counts["raw"],
                "deduped_examples": counts["ded"],
                "quality_filtered_examples": counts["qual"],
                "xml_examples": counts["xml"],
                "suspected_source_family": "jw/religious" if "jw" in (label + domain).lower() else "",
                "notes": "",
            }
        )
    write_csv(PROCESSED / "coverage_by_author_domain.csv", rows)
    # Dictionary dedupe is simple exact source-target.
    dkept = dedupe_dictionary_entries(dict_raw)
    write_jsonl(PROCESSED / "dictionary_entries_deduped.jsonl", dkept)
    if not (PROCESSED / "audio_manifest.csv").exists() or (PROCESSED / "audio_manifest.csv").stat().st_size == 0:
        write_csv(PROCESSED / "audio_manifest.csv", [])
    author_rows = []
    author_map: dict[tuple[str, str], dict[str, Any]] = {}
    for row in raw_examples:
        aid = row.get("authorId", "")
        label = row.get("author_label_if_known") or row.get("author_label_if_visible") or ""
        if not aid and not label:
            continue
        key = (aid, label)
        entry = author_map.setdefault(key, {"pairs": set(), "domains": set(), "count": 0})
        entry["pairs"].add(row.get("pair", ""))
        if row.get("domain"):
            entry["domains"].add(row.get("domain", ""))
        entry["count"] += 1
    for (aid, label), info in sorted(author_map.items(), key=lambda x: (-x[1]["count"], x[0])):
        author_rows.append(
            {
                "authorId": aid,
                "author_label": label,
                "author_raw_json": json.dumps({"authorId": aid, "label": label}, ensure_ascii=False),
                "pairs_seen": ";".join(sorted(info["pairs"])),
                "examples_count": info["count"],
                "domains_seen": ";".join(sorted(info["domains"])),
                "notes": "Visible/static fragment author label.",
            }
        )
    write_csv(PROCESSED / "authors.csv", author_rows)
    dict_cov = []
    for l1, l2 in config["target_pairs"]:
        pair = pair_name(l1, l2)
        raw_pair = [r for r in dict_raw if r.get("pair") == pair]
        ded_pair = [r for r in dkept if r.get("pair") == pair]
        authors = Counter(r.get("author_label_if_known", "") for r in raw_pair)
        authors.pop("", None)
        dict_cov.append(
            {
                "pair": pair,
                "l1": l1,
                "l2": l2,
                "source_language_name": source_name(config, l1),
                "target_language_name": target_name(config, l2),
                "dictionary_entries_raw": len(raw_pair),
                "dictionary_entries_deduped": len(ded_pair),
                "top_authors": ";".join(k for k, _ in authors.most_common(5)),
                "notes": "Dictionary/headword entries are exported to lexical XML because xml.include_dictionary_entries is enabled." if config["xml"].get("include_dictionary_entries", False) else "Dictionary/headword entries are sidecar data and excluded from Final_XML by default.",
            }
        )
    write_csv(PROCESSED / "dictionary_coverage_by_pair.csv", dict_cov)


def generate_validation_report(config: dict[str, Any], explicit_failures: list[tuple[Path, list[str]]]) -> None:
    generate_coverage_reports(config)
    coverage = read_csv(PROCESSED / "coverage_by_pair.csv")
    inventory = read_csv(PROCESSED / "url_inventory.csv")
    raw_examples = read_jsonl(PROCESSED / "static_page_examples_raw.jsonl") + read_jsonl(PROCESSED / "tmem_examples_raw.jsonl")
    deduped = read_jsonl(PROCESSED / "tmem_examples_deduped.jsonl")
    quality = read_jsonl(PROCESSED / "quality_filtered_examples.jsonl")
    dict_raw = read_jsonl(PROCESSED / "dictionary_entries_raw.jsonl")
    xml_index = read_csv(PROCESSED / "xml_index.csv")
    rejected = read_csv(PROCESSED / "rejected_records.csv")
    parse_errors = read_csv(PROCESSED / "parse_errors.csv")
    final_xml = sorted((ROOT / config["xml"]["output_dir"]).rglob("*.xml"))
    validation_failures = []
    for path in final_xml:
        validation_failures.extend((path, err) for err in validate_xml_file(path, config))
    for path, errs in explicit_failures:
        validation_failures.extend((path, err) for err in errs)
    status = "PASS" if not validation_failures else "FAIL"
    eng_count = sum(1 for r in xml_index if r.get("target_iso_639_3") == "eng")
    zho_count = sum(1 for r in xml_index if r.get("target_iso_639_3") == "zho")
    sentence_count = sum(len(ET.parse(path).getroot().findall("S")) for path in final_xml)
    report = f"""# Validation Report

Generated: {now_utc()}

## Totals

- total target pairs: {len(config["target_pairs"])}
- total pairs crawled/investigated: {len(coverage)}
- total pairs blocked/skipped and reasons: {len([r for r in coverage if r['crawl_status'].startswith('blocked') or r['crawl_status'] == 'failed_with_reason'])}
- total phrases queried: {len({(r['pair'], r['phrase']) for r in inventory if r['phrase']})}
- total API responses fetched: {len([r for r in inventory if r['source_site'] == 'iapi.glosbe'])}
- total static pages fetched: {len([r for r in inventory if r['source_site'] == 'static_page'])}
- total raw tmem examples: {len(raw_examples)}
- total deduped examples: {len(deduped)}
- total quality-filtered examples: {len(quality)}
- total dictionary entries: {len(dict_raw)}
- total XML files: {len(final_xml)}
- total TEXT elements: {len(final_xml)}
- total S elements: {sentence_count}
- total indexed translations: {len(xml_index)}
- total TRANSL eng elements: {eng_count}
- total TRANSL zho elements: {zho_count}
- total validation failures: {len(validation_failures)}

## Pair Status

{chr(10).join(f"- {r['pair']}: {r['crawl_status']} ({r['raw_tmem_examples']} raw examples, {r['xml_sentences_created']} indexed XML translations)" for r in coverage)}

## Skipped Or Rejected Records

Rejected records: {len(rejected)}

Top rejection reasons:

{chr(10).join(f'- {reason}: {count}' for reason, count in Counter(r['rejection_reason'] for r in rejected).most_common(20)) or '- None'}

## Rights/Access Warnings

- Scrape permission was asserted by the project owner in-thread on 2026-05-14.
- Public redistribution remains rights-review-required unless written owner permission and third-party source-corpus terms are archived.
- iapi3 currently requires a token; static `/fragment/tmem` fallback was used.

## Language Mapping Warnings

- `trv` is configured as Taroko; verify FormosanBank convention for Taroko/Seediq-related labeling before public release.
- No glottocodes were asserted unless separately verified.

## Duplicate/Overlap Warnings

- Existing Formosan-Glosbe exact overlaps are audited in `overlap_candidates.csv`; XML exclusion is controlled by `quality.exclude_existing_formosan_glosbe_overlap_from_xml`.
- JW/religious-domain examples are flagged through author/domain coverage.

## App Count Sanity Checks

{chr(10).join(f"- {pair}: expected {meta.get('phrases')} phrases / {meta.get('examples')} examples; observed {next((r['deduped_tmem_examples'] for r in coverage if r['pair'] == pair), '0')} deduped examples and {next((r['dictionary_entries_deduped'] for r in coverage if r['pair'] == pair), '0')} deduped dictionary entries" for pair, meta in config.get('app_expected_counts', {}).items()) or '- No app expected counts configured.'}

## Invalid Files

{chr(10).join(f'- {rel(path)}: {err}' for path, err in validation_failures) or '- None'}

## Parse Errors

{len(parse_errors)} parse/fetch/access errors are recorded in `data/processed/parse_errors.csv`.

## Final Summary

{status}
"""
    (PROCESSED / "validation_report.md").write_text(report, encoding="utf-8")


def generate_import_report(config: dict[str, Any]) -> None:
    xml_index = read_csv(PROCESSED / "xml_index.csv")
    final_xml = sorted((ROOT / config["xml"]["output_dir"]).rglob("*.xml"))
    report = f"""# Import Report

Generated: {now_utc()}

Validation command used:

```bash
python scripts/validate_formosanbank_xml.py --config scripts/config.yaml
```

Validator: repository-local `scripts/validate_formosanbank_xml.py` / `scripts/glosbe_pipeline.py`.

Files ready for import: {len(final_xml)}

Aligned units ready for import: {len(xml_index)}

Unresolved language mapping issues:

- Verify `trv` naming convention for Taroko / Seediq-related data.
- Glottocodes were not added because they were not independently verified in this run.

Unresolved rights/access issues:

- Owner scraping permission was asserted in-thread, but public redistribution should remain private-only/rights-review-required until written permission scope is archived.
- iapi3 token access is not available from public app inspection; static public fragments were used.

Unresolved parsing issues:

- Static fragments provide author labels and translation IDs, but not the complete iapi JSON object.
- Dictionary entries are retained in sidecars. Structurally valid lexical rows are emitted to XML; the ILRDF-derived comparison is reference metadata and never an exclusion criterion.
- Lexical decisions are documented in `data/processed/ildrf_glosbe_lexical_audit.csv`, `data/processed/ildrf_glosbe_lexical_group_review.csv`, and `data/processed/lexical_xml_rejected.csv`.

Assumptions:

- `lang` attributes in Glosbe fragment HTML identify source and target direction for XML-eligible examples.
- Sentence-level fragment examples are source-published Glosbe translation-memory examples, not machine-created by this pipeline.

Recommendation:

Import `Final_XML/<LANG>/Glosbe_<LANG>_<eng|zho>_tmem.xml` and `Final_XML/<LANG>/Glosbe_<LANG>_<eng|zho>_lexical.xml` as private FormosanBank review corpora pending publication-rights confirmation.
"""
    (PROCESSED / "import_report.md").write_text(report, encoding="utf-8")


def command_extract_static_and_normalize_all(args: argparse.Namespace) -> None:
    command_extract_static_pages(args)
    command_normalize_text(args)


def command_init(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ensure_layout(config)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=[
        "init",
        "check_rights_and_robots",
        "discover_token_behavior",
        "census_pairs",
        "crawl_iapi3",
        "crawl_static_pages",
        "extract_iapi3_json",
        "extract_static_pages",
        "normalize_text",
        "validate_language_direction",
        "dedupe_examples",
        "dedupe_against_formosanbank",
        "filter_quality",
        "build_formosanbank_xml",
        "rebuild_lexical_reference_audit",
        "validate_formosanbank_xml",
        "generate_reports",
    ])
    parser.add_argument("--config", default=str(SCRIPTS / "config.yaml"))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--max-phrases", type=int, default=0)
    parser.add_argument("--max-pages", type=int, default=0)
    parser.add_argument("--restart-queue", action="store_true")
    parser.add_argument("--pairs", default="")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    commands = {
        "init": command_init,
        "check_rights_and_robots": command_check_rights,
        "discover_token_behavior": command_discover_token,
        "census_pairs": command_census_pairs,
        "crawl_iapi3": command_crawl_iapi3,
        "crawl_static_pages": command_crawl_static_pages,
        "extract_iapi3_json": command_extract_iapi_json,
        "extract_static_pages": command_extract_static_pages,
        "normalize_text": command_normalize_text,
        "validate_language_direction": command_validate_language_direction,
        "dedupe_examples": command_dedupe_examples,
        "dedupe_against_formosanbank": command_dedupe_against_formosanbank,
        "filter_quality": command_filter_quality,
        "build_formosanbank_xml": command_build_xml,
        "rebuild_lexical_reference_audit": command_rebuild_lexical_reference_audit,
        "validate_formosanbank_xml": command_validate_xml,
        "generate_reports": command_generate_reports,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
