#!/usr/bin/env python3
"""Extract the pinned Joby Utrecht table into a deterministic source ledger."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any


EXPECTED_PDF_SHA256 = "b871304347ed74f55ea7a8277eab8cd7336427034223eab8c987540ceaa054a4"
EXPECTED_PDF_BYTES = 1_096_429
EXPECTED_PAGES = 75
EXPECTED_ROWS = 1_061

COLUMN_NAMES = (
    "um_formosana",
    "um_belgica",
    "vdv_dutch",
    "vdv_siraya",
    "english",
    "murakami",
    "gospel_formulary_equivalent",
    "variation",
    "etyma",
    "other_sources",
)

# The PDF was printed from a spreadsheet. These bands are the stable left
# edges of its ten data columns, with seven-point allowances for hanging
# punctuation at the next column boundary.
COLUMN_BANDS = (
    (70.0, 140.0),
    (140.0, 215.0),
    (215.0, 280.0),
    (280.0, 360.0),
    (360.0, 445.0),
    (445.0, 507.0),
    (507.0, 578.0),
    (578.0, 617.0),
    (617.0, 667.0),
    (667.0, 842.0),
)

PRIMARY_COLUMN_COUNT = 5


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_pdf(path: Path) -> None:
    size = path.stat().st_size
    if size != EXPECTED_PDF_BYTES:
        raise ValueError(f"unexpected Joby PDF size: {size}")
    digest = sha256_file(path)
    if digest != EXPECTED_PDF_SHA256:
        raise ValueError(f"unexpected Joby PDF SHA-256: {digest}")


def run_pdftotext(path: Path) -> str:
    executable = shutil.which("pdftotext")
    if executable is None:
        raise RuntimeError("pdftotext is required to extract the source table")
    result = subprocess.run(
        [executable, "-tsv", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _column_for_word(left: float) -> int | None:
    for index, (start, end) in enumerate(COLUMN_BANDS, start=1):
        if start <= left < end:
            return index
    return None


def _row_starts(words: list[dict[str, str]]) -> dict[int, list[float]]:
    flow_lines: dict[tuple[int, int, int, int], list[dict[str, str]]] = defaultdict(
        list
    )
    for word in words:
        if word["level"] != "5":
            continue
        key = (
            int(word["page_num"]),
            int(word["par_num"]),
            int(word["block_num"]),
            int(word["line_num"]),
        )
        flow_lines[key].append(word)

    page_lines: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for (page, _paragraph, _block, line_number), line_words in flow_lines.items():
        primary_words: dict[int, list[dict[str, str]]] = defaultdict(list)
        for word in line_words:
            column = _column_for_word(float(word["left"]))
            if column is not None and column <= PRIMARY_COLUMN_COUNT:
                primary_words[column].append(word)

        for column, column_words in primary_words.items():
            top = min(float(word["top"]) for word in column_words)
            if not 145.0 <= top < 550.0:
                continue
            page_lines[page].append(
                {"column": column, "line_number": line_number, "top": top}
            )

    starts_by_page: dict[int, list[float]] = {}
    for page in range(1, EXPECTED_PAGES + 1):
        lines = page_lines[page]
        candidates: list[float] = []
        for line in lines:
            if line["column"] != 1:
                continue
            top = line["top"]
            same_top_starts = {
                other["column"]
                for other in lines
                if 2 <= other["column"] <= 5
                and other["line_number"] == 0
                and abs(other["top"] - top) < 0.3
            }
            near_starts = {
                other["column"]
                for other in lines
                if 2 <= other["column"] <= 5
                and other["line_number"] == 0
                and -0.3 <= other["top"] - top <= 11.5
            }
            if (line["line_number"] == 0 and near_starts) or len(same_top_starts) >= 2:
                candidates.append(top)

        starts: list[float] = []
        for top in sorted(set(candidates)):
            if not starts or top - starts[-1] >= 20.0:
                starts.append(top)
        starts_by_page[page] = starts
    return starts_by_page


def _page_top_orphans(
    by_page: dict[int, list[dict[str, Any]]],
    starts_by_page: dict[int, list[float]],
    page: int,
) -> list[dict[str, Any]]:
    """Words above `page`'s first detected row start, which no band would claim.

    They are the tail of an entry begun on the previous page: its column-1 cell
    ended there, so the lines here start no row of their own and would otherwise
    be discarded silently.
    """
    starts = starts_by_page.get(page) or []
    if not starts:
        return []
    ceiling = starts[0] - 0.3
    return [item for item in by_page.get(page, []) if item["top"] < ceiling]


def extract_rows(tsv: str) -> list[dict[str, Any]]:
    words = list(csv.DictReader(io.StringIO(tsv), delimiter="\t"))
    starts_by_page = _row_starts(words)

    page_words: dict[int, list[dict[str, Any]]] = defaultdict(list)
    page_markers: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for word in words:
        if word["level"] != "5":
            continue
        page = int(word["page_num"])
        top = float(word["top"])
        left = float(word["left"])
        if not 145.0 <= top < 550.0:
            continue
        if 50.0 <= left < 70.0:
            page_markers[page].append({"left": left, "text": word["text"], "top": top})
            continue
        column = _column_for_word(left)
        if column is None:
            continue
        page_words[page].append(
            {"column": column, "left": left, "text": word["text"], "top": top}
        )

    records: list[dict[str, Any]] = []
    for page in range(1, EXPECTED_PAGES + 1):
        starts = starts_by_page[page]
        for page_index, top in enumerate(starts):
            end = (
                starts[page_index + 1] - 0.3 if page_index + 1 < len(starts) else 550.0
            )
            # A row start is only ever recognised from a column-1 line, so a row
            # whose continuation lines carry no column-1 word and fall at the top
            # of the next page would lose them: they precede that page's first
            # start and so belong to no band at all. The last row of a page
            # therefore also claims the next page's leading orphan lines.
            spill: list[dict[str, Any]] = []
            spill_markers: list[dict[str, Any]] = []
            if page_index + 1 == len(starts):
                spill = _page_top_orphans(page_words, starts_by_page, page + 1)
                spill_markers = _page_top_orphans(
                    page_markers, starts_by_page, page + 1
                )

            cells: dict[str, str] = {}
            for column, name in enumerate(COLUMN_NAMES, start=1):
                items = sorted(
                    (
                        item
                        for item in page_words[page]
                        if item["column"] == column and top - 0.3 <= item["top"] < end
                    ),
                    key=lambda item: (round(item["top"], 1), item["left"]),
                ) + sorted(
                    (item for item in spill if item["column"] == column),
                    key=lambda item: (round(item["top"], 1), item["left"]),
                )
                cells[name] = " ".join(item["text"] for item in items).strip()

            marker_items = sorted(
                (item for item in page_markers[page] if top - 0.3 <= item["top"] < end),
                key=lambda item: (item["top"], item["left"]),
            ) + sorted(spill_markers, key=lambda item: (item["top"], item["left"]))
            records.append(
                {
                    "source_row": len(records) + 1,
                    "pdf_page": page,
                    "pdf_top": round(top, 3),
                    "um_page_marker": " ".join(
                        item["text"] for item in marker_items
                    ).strip(),
                    **cells,
                }
            )

    if len(records) != EXPECTED_ROWS:
        raise ValueError(
            f"expected {EXPECTED_ROWS} extracted rows, found {len(records)}"
        )
    return records


def build_ledger(pdf_path: Path, tsv_path: Path | None = None) -> dict[str, Any]:
    """The pinned table as a deterministic ledger.

    `tsv_path` is the saved output of `pdftotext -tsv` on the pinned PDF. It
    exists so the corpus rebuilds from a FormosanBank checkout alone (POL-048):
    the PDF is public but is not stored here, and poppler need not be installed
    to regenerate from a committed extraction.
    """
    if tsv_path is not None:
        rows = extract_rows(tsv_path.read_text(encoding="utf-8"))
    else:
        verify_pdf(pdf_path)
        rows = extract_rows(run_pdftotext(pdf_path))
    row_payload = json.dumps(
        rows, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )
    return {
        "extraction_schema": 1,
        "source": {
            "bytes": EXPECTED_PDF_BYTES,
            "pages": EXPECTED_PAGES,
            "path": "Private/JobyUtrechtManuscript.pdf",
            "sha256": EXPECTED_PDF_SHA256,
        },
        "row_count": len(rows),
        "rows_sha256": hashlib.sha256(row_payload.encode("utf-8")).hexdigest(),
        "rows": rows,
    }


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pdf", type=Path, default=root / "Private" / "JobyUtrechtManuscript.pdf"
    )
    parser.add_argument(
        "--tsv",
        type=Path,
        default=None,
        help="saved `pdftotext -tsv` output; use instead of the PDF (POL-048)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "CodeAndDocs" / "source" / "source_records.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tsv = args.tsv
    if tsv is None:
        default_tsv = Path(__file__).resolve().parent / "source" / "pdftotext.tsv"
        if default_tsv.exists() and not args.pdf.exists():
            tsv = default_tsv
    ledger = build_ledger(args.pdf, tsv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n")
    print(f"Extracted {ledger['row_count']} rows to {args.output}")
    print(f"Rows SHA-256: {ledger['rows_sha256']}")


if __name__ == "__main__":
    main()
