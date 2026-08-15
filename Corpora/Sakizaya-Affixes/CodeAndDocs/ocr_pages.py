#!/usr/bin/env python3
"""Generate page image, Tesseract TSV, and Apple Vision OCR caches."""

from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCAN = ROOT / "Private/source/akiw_2012_sakizaya_affixes_scan.pdf"
CACHE_DIR = ROOT / "Private/cache"
IMAGE_DIR = CACHE_DIR / "page_images_350"
TESSDATA_DIR = CACHE_DIR / "tessdata"
TESSERACT_DIR = CACHE_DIR / "ocr_tsv_350"
VISION_DIR = CACHE_DIR / "vision_ocr_350"


def run(cmd: list[str], **kwargs) -> None:
    subprocess.run(cmd, check=True, cwd=ROOT, **kwargs)


def render_pages(force: bool = False) -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    existing = sorted(IMAGE_DIR.glob("scan_page-*.png"))
    if len(existing) == 174 and not force:
        return
    if not shutil.which("pdftoppm"):
        raise RuntimeError("pdftoppm is required on PATH")
    for image in existing:
        image.unlink()
    run(["pdftoppm", "-r", "350", "-png", str(SOURCE_SCAN), str(IMAGE_DIR / "scan_page")])


def tesseract_pages(force: bool = False) -> None:
    TESSERACT_DIR.mkdir(parents=True, exist_ok=True)
    if not shutil.which("tesseract"):
        raise RuntimeError("tesseract is required on PATH")
    missing_langs = [
        lang for lang in ("eng.traineddata", "chi_tra.traineddata", "chi_tra_vert.traineddata")
        if not (TESSDATA_DIR / lang).exists()
    ]
    if missing_langs:
        raise RuntimeError(
            "missing Tesseract language data in Private/cache/tessdata: "
            + ", ".join(missing_langs)
        )
    for image in sorted(IMAGE_DIR.glob("scan_page-*.png")):
        base = image.stem
        out_base = TESSERACT_DIR / base
        if out_base.with_suffix(".tsv").exists() and not force:
            continue
        env = {"TESSDATA_PREFIX": str(TESSDATA_DIR)}
        with (out_base.with_suffix(".err")).open("w", encoding="utf-8") as err:
            run(
                [
                    "tesseract",
                    str(image),
                    str(out_base),
                    "--psm",
                    "6",
                    "-l",
                    "chi_tra+eng",
                    "-c",
                    "tessedit_create_tsv=1",
                ],
                stderr=err,
                env=env,
            )


def vision_pages(force: bool = False) -> None:
    try:
        from ocrmac.ocrmac import OCR
    except ImportError as exc:
        raise RuntimeError("ocrmac is required for Apple Vision OCR: pip install ocrmac") from exc

    VISION_DIR.mkdir(parents=True, exist_ok=True)
    for image in sorted(IMAGE_DIR.glob("scan_page-*.png")):
        page = int(image.stem.split("-")[-1])
        out = VISION_DIR / f"page-{page:03d}.vision.tsv"
        if out.exists() and out.stat().st_size > 0 and not force:
            continue
        result = OCR(
            str(image),
            recognition_level="accurate",
            language_preference=["zh-Hant", "en-US"],
            detail=True,
        ).recognize(px=True)
        result = sorted(result, key=lambda row: (row[2][1], row[2][0]))
        with out.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerow(["page", "item", "left", "top", "right", "bottom", "conf", "text"])
            for idx, (text, conf, bbox) in enumerate(result, 1):
                left, top, right, bottom = bbox
                writer.writerow(
                    [
                        page,
                        idx,
                        f"{left:.1f}",
                        f"{top:.1f}",
                        f"{right:.1f}",
                        f"{bottom:.1f}",
                        f"{conf:.3f}",
                        text,
                    ]
                )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-tesseract", action="store_true")
    parser.add_argument("--skip-vision", action="store_true")
    args = parser.parse_args()

    render_pages(force=args.force)
    if not args.skip_tesseract:
        tesseract_pages(force=args.force)
    if not args.skip_vision:
        vision_pages(force=args.force)
    print("OCR cache ready under Private/cache/")


if __name__ == "__main__":
    main()
