#!/usr/bin/env python3
"""Audit native and Chinese transcript sections against the official PDFs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import fitz
from rapidfuzz.fuzz import partial_ratio

CODE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = CODE_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from CodeAndDocs.main import LanguageSpec, load_specs, read_sections  # noqa: E402

DATA_ROOT = CODE_ROOT / "data"
DEFAULT_MANIFEST = DATA_ROOT / "source_manifest.csv"
DEFAULT_REPORT = DATA_ROOT / "source_alignment.csv"

_TYPOGRAPHY = str.maketrans(
    {
        "’": "'",
        "‘": "'",
        "＇": "'",
        "`": "'",
        "“": '"',
        "”": '"',
        "＂": '"',
        "「": '"',
        "」": '"',
        "﹁": '"',
        "﹂": '"',
        "（": "(",
        "）": ")",
        "，": ",",
        "；": ";",
        "：": ":",
        "！": "!",
        "？": "?",
        "。": ".",
        "–": "-",
        "—": "-",
    }
)


@dataclass(frozen=True)
class TextBlock:
    page: int
    y: float
    text: str


@dataclass(frozen=True)
class Candidate:
    page_start: int
    page_end: int
    text: str


def normalize_for_alignment(text: str, ignore_terminal_period: bool = False) -> str:
    """Normalize layout and typographic variants without changing letters."""
    normalized = unicodedata.normalize("NFC", text).translate(_TYPOGRAPHY)
    normalized = normalized.replace("\u00ad", "")
    normalized = re.sub(r"[.…]{2,}", "…", normalized)
    normalized = "".join(
        character for character in normalized if not character.isspace()
    )
    if ignore_terminal_period:
        normalized = normalized.removesuffix(".")
    return normalized


def classify_block(text: str) -> str | None:
    latin = sum(character.isascii() and character.isalpha() for character in text)
    cjk = sum(
        "\u3400" <= character <= "\u9fff"
        or "\uf900" <= character <= "\ufaff"
        for character in text
    )
    if latin > cjk:
        return "native"
    if cjk:
        return "chinese"
    return None


def extract_blocks(pdf_path: Path) -> tuple[dict[str, list[TextBlock]], int]:
    """Extract body blocks, excluding page numbers and repeated small headers."""
    channels: dict[str, list[TextBlock]] = {"native": [], "chinese": []}
    with fitz.open(pdf_path) as document:
        page_count = len(document)
        for page_index, page in enumerate(document, start=1):
            for block in page.get_text("dict")["blocks"]:
                if "lines" not in block:
                    continue
                spans = [span for line in block["lines"] for span in line["spans"]]
                text = " ".join(
                    "".join(span["text"] for span in line["spans"])
                    for line in block["lines"]
                ).strip()
                if not text or max((span["size"] for span in spans), default=0) < 10:
                    continue
                channel = classify_block(text)
                if channel:
                    channels[channel].append(
                        TextBlock(page=page_index, y=float(block["bbox"][1]), text=text)
                    )
    for blocks in channels.values():
        blocks.sort(key=lambda block: (block.page, block.y))
    return channels, page_count


def build_candidates(blocks: list[TextBlock]) -> list[Candidate]:
    """Join up to four neighboring blocks to recover split source sections."""
    candidates: list[Candidate] = []
    for start in range(len(blocks)):
        for width in range(1, 5):
            window = blocks[start : start + width]
            if len(window) != width:
                continue
            if window[-1].page - window[0].page > 1:
                continue
            candidates.append(
                Candidate(
                    page_start=window[0].page,
                    page_end=window[-1].page,
                    text=" ".join(block.text for block in window),
                )
            )
    return candidates


def match_section(
    source: str,
    candidates: list[Candidate],
    ignore_terminal_period: bool = False,
) -> tuple[Candidate, float]:
    """Find exact normalized containment and provide a diagnostic fuzzy score."""
    target = normalize_for_alignment(source, ignore_terminal_period)
    normalized = [
        (
            candidate,
            normalize_for_alignment(candidate.text, ignore_terminal_period),
        )
        for candidate in candidates
    ]
    exact = [
        (candidate, text)
        for candidate, text in normalized
        if target and target in text
    ]
    if exact:
        candidate, _ = min(
            exact,
            key=lambda item: (
                len(item[1]) - len(target),
                item[0].page_start,
                item[0].page_end,
            ),
        )
        return candidate, 100.0

    eligible = [item for item in normalized if len(item[1]) >= len(target) * 0.8]
    if not eligible:
        raise ValueError("no PDF block candidate is long enough for the source section")
    candidate, candidate_text = max(
        eligible, key=lambda item: partial_ratio(target, item[1])
    )
    score = partial_ratio(target, candidate_text)
    return candidate, min(float(score), 99.999)


def pdf_for_spec(spec: LanguageSpec) -> Path:
    paths = sorted(spec.source_file.parent.glob("*.pdf"))
    if len(paths) != 1:
        raise ValueError(f"{spec.language}: expected one PDF, found {len(paths)}")
    return paths[0]


def alignment_rows(specs: tuple[LanguageSpec, ...]) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for spec in specs:
        pdf_path = pdf_for_spec(spec)
        blocks, _ = extract_blocks(pdf_path)
        native_sections = read_sections(spec.source_file, spec.sections)
        chinese_sections = read_sections(spec.chinese_file, spec.sections)
        native_candidates = build_candidates(blocks["native"])
        chinese_candidates = build_candidates(blocks["chinese"])
        for section_id, (native_source, chinese_source) in enumerate(
            zip(native_sections, chinese_sections, strict=True)
        ):
            terminal_section = section_id in {0, spec.sections - 1}
            chinese_candidate, chinese_score = match_section(
                chinese_source,
                chinese_candidates,
                ignore_terminal_period=terminal_section,
            )
            page_coherent_native = (
                native_candidates
                if section_id == 0
                else [
                    candidate
                    for candidate in native_candidates
                    if candidate.page_start <= chinese_candidate.page_end
                    and candidate.page_end >= chinese_candidate.page_start
                ]
            )
            native_candidate, native_score = match_section(
                native_source,
                page_coherent_native,
                ignore_terminal_period=terminal_section,
            )
            matches = (
                (
                    "native",
                    spec.source_file,
                    native_candidate,
                    native_score,
                ),
                (
                    "chinese",
                    spec.chinese_file,
                    chinese_candidate,
                    chinese_score,
                ),
            )
            for channel, source_path, candidate, score in matches:
                rows.append(
                    {
                        "language": spec.language,
                        "channel": channel,
                        "section_id": str(section_id),
                        "pdf_page_start": str(candidate.page_start),
                        "pdf_page_end": str(candidate.page_end),
                        "score": f"{score:.3f}",
                        "source_path": source_path.relative_to(CODE_ROOT).as_posix(),
                        "pdf_path": pdf_path.relative_to(CODE_ROOT).as_posix(),
                    }
                )
                if score != 100.0:
                    errors.append(
                        f"{spec.language} {channel} section {section_id}: "
                        f"PDF alignment score {score:.3f}"
                    )
        print(f"{spec.language}: {spec.sections * 2} source sections matched", flush=True)
    return rows, errors


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_kind(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return "official_bilingual_pdf"
    if path.name == "Chinese.txt":
        return "shared_chinese_transcript"
    if path.name == "English.txt":
        return "shared_english_transcript"
    if path.name.endswith("_zh.txt"):
        return "language_chinese_transcript"
    if path.name.endswith("_en.txt"):
        return "language_english_transcript"
    return "native_transcript"


def source_language(path: Path) -> str:
    return "shared" if path.parent.name == "Apologies" else path.parent.name


def manifest_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted((CODE_ROOT / "Apologies").rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".pdf", ".txt"}:
            continue
        sections = ""
        pages = ""
        if path.suffix.lower() == ".txt":
            sections = str(len(path.read_text(encoding="utf-8").splitlines()))
        else:
            with fitz.open(path) as document:
                pages = str(len(document))
        rows.append(
            {
                "path": path.relative_to(CODE_ROOT).as_posix(),
                "sha256": sha256(path),
                "size_bytes": str(path.stat().st_size),
                "kind": source_kind(path),
                "language": source_language(path),
                "sections": sections,
                "pdf_pages": pages,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def verify_manifest(path: Path, current: list[dict[str, str]]) -> list[str]:
    if not path.exists():
        return [f"source manifest does not exist: {path}"]
    with path.open(encoding="utf-8", newline="") as handle:
        recorded = list(csv.DictReader(handle))
    if recorded == current:
        return []
    recorded_by_path = {row["path"]: row for row in recorded}
    current_by_path = {row["path"]: row for row in current}
    errors = []
    for source_path in sorted(recorded_by_path.keys() | current_by_path.keys()):
        if recorded_by_path.get(source_path) != current_by_path.get(source_path):
            errors.append(f"source manifest mismatch: {source_path}")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--refresh-manifest", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    current_manifest = manifest_rows()
    manifest_fields = [
        "path",
        "sha256",
        "size_bytes",
        "kind",
        "language",
        "sections",
        "pdf_pages",
    ]
    if args.refresh_manifest:
        write_csv(args.manifest, current_manifest, manifest_fields)
    manifest_errors = verify_manifest(args.manifest, current_manifest)

    rows, alignment_errors = alignment_rows(load_specs())
    write_csv(
        args.report,
        rows,
        [
            "language",
            "channel",
            "section_id",
            "pdf_page_start",
            "pdf_page_end",
            "score",
            "source_path",
            "pdf_path",
        ],
    )
    errors = manifest_errors + alignment_errors
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"source manifest verified: {len(current_manifest)} files")
    print(f"source alignment verified: {len(rows)} native and Chinese sections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
