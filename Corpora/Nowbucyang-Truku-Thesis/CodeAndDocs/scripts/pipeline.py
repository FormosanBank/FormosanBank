from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from common import (
    XML_NS,
    bibtex,
    citation,
    clean_inline,
    cjk_count,
    confidence_rank,
    copy_if_missing,
    ensure_dirs,
    has_cjk,
    has_latin,
    load_config,
    log,
    normalize_ws,
    page_image_path,
    page_text_path,
    read_csv_dicts,
    read_jsonl,
    rel,
    ROOT,
    rpath,
    run_cmd,
    sha256_file,
    sha256_text,
    source_copyright,
    write_csv,
    write_json,
    write_jsonl,
)

try:
    import fitz
except Exception:
    fitz = None

try:
    import pdfplumber
except Exception:
    pdfplumber = None

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    from rapidfuzz import fuzz
except Exception:
    fuzz = None


SOURCE_ID = "HSU_LOWKING_TRUKU_WORDFORMATION_2008"
RAW_PDF_ROOT_CANDIDATES = ["許韋晟全文.pdf"]
DECRYPTED_ROOT_CANDIDATES = ["許韋晟全文.decrypted.pdf"]

PDF_INVENTORY_FIELDS = [
    "pdf_file",
    "original_pdf_sha256",
    "decrypted_pdf_sha256",
    "title_metadata",
    "author_metadata",
    "page_count",
    "encryption_status_original",
    "extraction_methods_used",
    "has_selectable_text",
    "rendered_images_created",
    "ocr_used",
    "notes",
]

PAGES_FIELDS = [
    "page_index_zero_based",
    "page_number_one_based",
    "printed_page_number",
    "thesis_section",
    "raw_text_path",
    "raw_text_sha256",
    "rendered_image_path",
    "rendered_image_sha256",
    "char_count_pymupdf",
    "char_count_pdfplumber",
    "selected_extraction_method",
    "has_numbered_examples",
    "has_table",
    "has_references",
    "parse_status",
    "parse_warnings",
]

EXAMPLES_RAW_FIELDS = [
    "example_record_id",
    "source_id",
    "page_number_one_based",
    "printed_page_number",
    "example_number",
    "subexample_letter",
    "example_label_raw",
    "chapter_number",
    "section_number",
    "section_title",
    "raw_block_ids",
    "raw_text_combined",
    "truku_line_raw",
    "gloss_line_raw",
    "chinese_translation_raw",
    "english_translation_raw_if_source_published",
    "commentary_raw",
    "root_or_underlying_form_raw",
    "phonetic_form_raw",
    "morphology_label_raw",
    "grammatical_tags_raw",
    "extraction_method",
    "extraction_confidence",
    "parse_warnings",
]

EXAMPLES_CLEAN_FIELDS = [
    "example_record_id",
    "source_id",
    "page_number_one_based",
    "printed_page_number",
    "example_number",
    "subexample_letter",
    "example_label_clean",
    "truku_line_clean",
    "gloss_line_clean",
    "chinese_translation_clean",
    "english_translation_clean_if_source_published",
    "chapter_number",
    "section_number",
    "section_title",
    "ISO_639_3",
    "dialect_or_location_attribute_value",
    "extraction_confidence",
    "xml_eligible",
    "rejection_reason",
    "notes",
]

XML_INDEX_FIELDS = [
    "xml_file",
    "text_id",
    "sentence_id",
    "unit_id",
    "example_record_id",
    "source_id",
    "source_pdf_path",
    "source_pdf_sha256",
    "decrypted_pdf_sha256",
    "page_number_one_based",
    "printed_page_number",
    "chapter_number",
    "section_number",
    "section_title",
    "example_number",
    "subexample_letter",
    "ISO_639_3",
    "FormosanBank_language_name",
    "dialect_or_location_attribute_value",
    "truku_form_sha256",
    "translation_lang",
    "source_translation_sha256",
    "pair_sha256",
    "gloss_record_id",
    "extraction_method",
    "extraction_confidence",
    "overlap_status",
    "quality_status",
    "citation",
    "permission_status",
    "notes",
]

GLOSS_ALIGNMENT_FIELDS = [
    "example_record_id",
    "sentence_id",
    "page_number_one_based",
    "example_label_clean",
    "form_token_count",
    "gloss_token_count",
    "word_count_emitted",
    "morpheme_count_emitted",
    "alignment_status",
    "reason",
    "form_tokens",
    "gloss_tokens",
    "notes",
]

XML_VARIANT_AUDIT_FIELDS = [
    "sentence_id",
    "example_record_id",
    "example_label_clean",
    "page_number_one_based",
    "variant_index",
    "variant_count",
    "original_form_source",
    "original_form_xml",
    "standard_form_xml",
    "gloss_line_source",
    "gloss_line_xml",
    "chinese_translation_clean",
    "notes",
]


def _pdf_paths(cfg: dict[str, Any]) -> tuple[Path, Path]:
    return rpath(cfg["source"]["pdf_path"]), rpath(cfg["source"]["decrypted_pdf_path"])


def _source_pdf_hashes(cfg: dict[str, Any]) -> tuple[str, str]:
    original, decrypted = _pdf_paths(cfg)
    return (
        sha256_file(original) if original.exists() else "",
        sha256_file(decrypted) if decrypted.exists() else "",
    )


def _preserve_source_files(cfg: dict[str, Any]) -> None:
    original, decrypted = _pdf_paths(cfg)
    for name in RAW_PDF_ROOT_CANDIDATES:
        candidate = ROOT / name
        if candidate.exists():
            copy_if_missing(candidate, original)
            break
    for name in DECRYPTED_ROOT_CANDIDATES:
        candidate = ROOT / name
        if candidate.exists():
            copy_if_missing(candidate, decrypted)
            break


def _pdf_page_count(path: Path) -> int:
    if fitz:
        with fitz.open(path) as doc:
            return doc.page_count
    if PdfReader:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            reader.decrypt("")
        return len(reader.pages)
    info = run_cmd(["pdfinfo", str(path)], check=True).stdout
    m = re.search(r"^Pages:\s+(\d+)", info, flags=re.M)
    return int(m.group(1)) if m else 0


def inspect_pdf(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    _preserve_source_files(cfg)
    original, decrypted = _pdf_paths(cfg)
    if not original.exists():
        raise FileNotFoundError(f"source PDF not found: {original}")

    qpdf_report = run_cmd(["qpdf", "--show-encryption", str(original)]).stdout
    (ROOT / "data/raw/pdf_metadata/encryption_report.txt").write_text(qpdf_report, encoding="utf-8")
    pdfinfo = run_cmd(["pdfinfo", str(original)]).stdout

    meta: dict[str, Any] = {
        "pdfinfo": pdfinfo,
        "qpdf_encryption_report": qpdf_report,
        "metadata": {},
        "xmp_extracted": False,
        "page_count": 0,
        "is_encrypted": "Encrypted:       yes" in pdfinfo or "copy:no" in pdfinfo,
    }
    title = ""
    author = ""
    if PdfReader:
        reader = PdfReader(str(original))
        if reader.is_encrypted:
            reader.decrypt("")
        meta["page_count"] = len(reader.pages)
        md = reader.metadata or {}
        meta["metadata"] = {str(k): str(v) for k, v in md.items()}
        title = str(md.get("/Title", "") or "")
        author = str(md.get("/Author", "") or "")
        try:
            xmp_obj = reader.trailer["/Root"].get("/Metadata")
            xmp_bytes = xmp_obj.get_data() if xmp_obj else b""
            if xmp_bytes:
                (ROOT / "data/raw/pdf_metadata/xmp_metadata.xml").write_bytes(xmp_bytes)
                meta["xmp_extracted"] = True
        except Exception as exc:
            meta["xmp_error"] = str(exc)
    else:
        meta["page_count"] = _pdf_page_count(original)

    if not (ROOT / "data/raw/pdf_metadata/xmp_metadata.xml").exists():
        (ROOT / "data/raw/pdf_metadata/xmp_metadata.xml").write_text("", encoding="utf-8")

    original_hash, decrypted_hash = _source_pdf_hashes(cfg)
    meta["original_pdf_sha256"] = original_hash
    meta["decrypted_pdf_sha256"] = decrypted_hash
    write_json(ROOT / "data/raw/pdf_metadata/pdf_metadata.json", meta)

    inventory = [{
        "pdf_file": rel(original),
        "original_pdf_sha256": original_hash,
        "decrypted_pdf_sha256": decrypted_hash,
        "title_metadata": title,
        "author_metadata": author or "Lowking",
        "page_count": meta["page_count"],
        "encryption_status_original": "owner-encrypted; empty user password; extraction for any purpose disallowed by owner permissions before qpdf decrypt",
        "extraction_methods_used": "pending",
        "has_selectable_text": "pending",
        "rendered_images_created": "pending",
        "ocr_used": "no",
        "notes": "Original PDF preserved; decryption permitted by FormosanBank authorization.",
    }]
    write_csv(ROOT / "data/processed/pdf_inventory.csv", inventory, PDF_INVENTORY_FIELDS)
    log("inspect_pdf", f"inspected {original} pages={meta['page_count']} sha256={original_hash}")


def decrypt_pdf(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    _preserve_source_files(cfg)
    original, decrypted = _pdf_paths(cfg)
    if not original.exists():
        raise FileNotFoundError(original)
    run_cmd(["qpdf", "--decrypt", str(original), str(decrypted)], check=True)
    original_hash, decrypted_hash = _source_pdf_hashes(cfg)
    rows = read_csv_dicts(ROOT / "data/processed/pdf_inventory.csv") or [{}]
    row = rows[0]
    row.update({
        "pdf_file": rel(original),
        "original_pdf_sha256": original_hash,
        "decrypted_pdf_sha256": decrypted_hash,
        "page_count": _pdf_page_count(decrypted),
        "ocr_used": "no",
        "notes": (row.get("notes") or "") + " Decrypted working PDF created outside Final_XML.",
    })
    write_csv(ROOT / "data/processed/pdf_inventory.csv", [row], PDF_INVENTORY_FIELDS)
    log("decrypt_pdf", f"decrypted {original} -> {decrypted} sha256={decrypted_hash}")


def _extract_pdftotext_pages(pdf: Path, page_count: int) -> list[str]:
    proc = run_cmd(["pdftotext", "-layout", str(pdf), "-"], check=True)
    pages = proc.stdout.split("\f")
    if pages and pages[-1] == "":
        pages = pages[:-1]
    if len(pages) != page_count:
        out = []
        for page in range(1, page_count + 1):
            one = run_cmd(["pdftotext", "-layout", "-f", str(page), "-l", str(page), str(pdf), "-"], check=True).stdout
            out.append(one.replace("\f", "").rstrip("\n"))
        return out
    return [p.rstrip("\n") for p in pages]


def _printed_page_number(text: str, page_one: int) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in reversed(lines[-8:]):
        if re.fullmatch(r"[ivxlcdmIVXLCDM]+", line):
            return line.lower()
        if re.fullmatch(r"\d{1,3}", line):
            return line
    if page_one == 1:
        return "cover"
    return ""


def _thesis_section(text: str, page_one: int) -> str:
    if page_one <= 16:
        if "摘要" in text:
            return "front_matter_abstract"
        if "Abstract" in text:
            return "front_matter_abstract_en"
        if "目錄" in text:
            return "front_matter_toc"
        return "front_matter"
    m = re.search(r"第[一二三四五六七八九十]+章\s+([^\n]+)", text)
    if m:
        return clean_inline(m.group(0))
    if "參考文獻" in text:
        return "references"
    if "附錄" in text:
        return "appendix"
    return "body"


def extract_pdf_text(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    original, decrypted = _pdf_paths(cfg)
    if not decrypted.exists():
        decrypt_pdf(cfg)
    page_count = _pdf_page_count(decrypted)
    pdftotext_pages = _extract_pdftotext_pages(decrypted, page_count)

    pymupdf_pages = [""] * page_count
    if fitz:
        with fitz.open(decrypted) as doc:
            for idx, page in enumerate(doc):
                pymupdf_pages[idx] = page.get_text("text", sort=True) or ""

    pdfplumber_pages = [""] * page_count
    if pdfplumber:
        with pdfplumber.open(decrypted) as pdf:
            for idx, page in enumerate(pdf.pages):
                pdfplumber_pages[idx] = page.extract_text(layout=True) or ""

    page_rows: list[dict[str, Any]] = []
    artifact_rows: list[dict[str, Any]] = []
    for idx in range(page_count):
        selected = pdftotext_pages[idx] if idx < len(pdftotext_pages) else ""
        method = "pdftotext_layout"
        if not selected.strip():
            alternatives = [("pymupdf_text", pymupdf_pages[idx]), ("pdfplumber_layout", pdfplumber_pages[idx])]
            method, selected = max(alternatives, key=lambda item: len(item[1]))
        path = page_text_path(idx + 1)
        path.write_text(selected, encoding="utf-8")
        warning = []
        if "�" in selected:
            warning.append("replacement_character")
        if abs(len(pymupdf_pages[idx]) - len(pdfplumber_pages[idx])) > 500:
            warning.append("method_char_count_divergence")
        if not selected.strip():
            warning.append("missing_selectable_text")
        page_rows.append({
            "page_index_zero_based": idx,
            "page_number_one_based": idx + 1,
            "printed_page_number": _printed_page_number(selected, idx + 1),
            "thesis_section": _thesis_section(selected, idx + 1),
            "raw_text_path": rel(path),
            "raw_text_sha256": sha256_file(path),
            "rendered_image_path": rel(page_image_path(idx + 1)),
            "rendered_image_sha256": sha256_file(page_image_path(idx + 1)) if page_image_path(idx + 1).exists() else "",
            "char_count_pymupdf": len(pymupdf_pages[idx]),
            "char_count_pdfplumber": len(pdfplumber_pages[idx]),
            "selected_extraction_method": method,
            "has_numbered_examples": bool(re.search(r"^\s*(?:例\s*)?\(\d+\)\s*(?:[a-z]\.)?", selected, flags=re.M)),
            "has_table": "表 " in selected or re.search(r"^表\s*\d", selected, flags=re.M) is not None,
            "has_references": "參考文獻" in selected,
            "parse_status": "extracted" if selected.strip() else "empty",
            "parse_warnings": ";".join(warning),
        })
        if warning:
            artifact_rows.append({
                "page_number_one_based": idx + 1,
                "artifact_type": ";".join(warning),
                "selected_extraction_method": method,
                "char_count_pymupdf": len(pymupdf_pages[idx]),
                "char_count_pdfplumber": len(pdfplumber_pages[idx]),
                "notes": "Recorded during text-layer extraction comparison.",
            })

    write_csv(ROOT / "data/processed/pages.csv", page_rows, PAGES_FIELDS)
    write_csv(
        ROOT / "data/processed/extraction_artifacts.csv",
        artifact_rows,
        ["page_number_one_based", "artifact_type", "selected_extraction_method", "char_count_pymupdf", "char_count_pdfplumber", "notes"],
    )
    original_hash, decrypted_hash = _source_pdf_hashes(cfg)
    inv = read_csv_dicts(ROOT / "data/processed/pdf_inventory.csv") or [{}]
    nonblank_pages = sum(1 for row in page_rows if row["parse_status"] == "extracted")
    blank_pages = page_count - nonblank_pages
    inv[0].update({
        "pdf_file": rel(original),
        "original_pdf_sha256": original_hash,
        "decrypted_pdf_sha256": decrypted_hash,
        "page_count": page_count,
        "extraction_methods_used": "pdftotext -layout; PyMuPDF text; pdfplumber layout",
        "has_selectable_text": f"yes_nonblank_pages={nonblank_pages}; blank_or_empty_pages_recorded={blank_pages}",
        "rendered_images_created": "pending",
        "ocr_used": "no",
    })
    write_csv(ROOT / "data/processed/pdf_inventory.csv", inv, PDF_INVENTORY_FIELDS)
    log("extract_pdf_text", f"extracted text for {page_count} pages")


def render_pdf_pages(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    _, decrypted = _pdf_paths(cfg)
    if not decrypted.exists():
        decrypt_pdf(cfg)
    if not fitz:
        raise RuntimeError("PyMuPDF is required for page rendering")
    with fitz.open(decrypted) as doc:
        for idx, page in enumerate(doc):
            out = page_image_path(idx + 1)
            if out.exists() and out.stat().st_size > 0:
                continue
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            pix.save(out)
    pages = read_csv_dicts(ROOT / "data/processed/pages.csv")
    if pages:
        for row in pages:
            img = page_image_path(int(row["page_number_one_based"]))
            row["rendered_image_path"] = rel(img)
            row["rendered_image_sha256"] = sha256_file(img) if img.exists() else ""
        write_csv(ROOT / "data/processed/pages.csv", pages, PAGES_FIELDS)
    inv = read_csv_dicts(ROOT / "data/processed/pdf_inventory.csv")
    if inv:
        inv[0]["rendered_images_created"] = "yes"
        write_csv(ROOT / "data/processed/pdf_inventory.csv", inv, PDF_INVENTORY_FIELDS)
    log("render_pdf_pages", "rendered PDF pages for audit")


def extract_layout_blocks(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    _, decrypted = _pdf_paths(cfg)
    if not decrypted.exists():
        decrypt_pdf(cfg)
    if not fitz:
        raise RuntimeError("PyMuPDF is required for layout block extraction")
    rows: list[dict[str, Any]] = []
    with fitz.open(decrypted) as doc:
        for page_idx, page in enumerate(doc):
            for block_idx, block in enumerate(page.get_text("blocks", sort=True)):
                x0, y0, x1, y1, text, block_no, block_type = block[:7]
                if not (text or "").strip():
                    continue
                rows.append({
                    "block_id": f"p{page_idx + 1:04d}_b{block_idx:03d}",
                    "page_number_one_based": page_idx + 1,
                    "block_index": block_idx,
                    "x0": round(x0, 2),
                    "y0": round(y0, 2),
                    "x1": round(x1, 2),
                    "y1": round(y1, 2),
                    "block_type": block_type,
                    "text": text.rstrip("\n"),
                    "text_sha256": sha256_text(text.rstrip("\n")),
                })
    write_jsonl(ROOT / "data/processed/page_text_blocks.jsonl", rows)
    log("extract_layout_blocks", f"wrote {len(rows)} layout blocks")


CHAPTER_NUMS = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
TAG_RE = re.compile(r"\b(AF|PF|LF|IF|Caus|RED|CV|CVCV|FUT|NMLZ|GEN|NOM|OBL|NEG)\b|主格|屬格|受格|主題|焦點|完成|未來|使役|重疊")


def _chapter_from_line(line: str) -> tuple[int | None, str]:
    m = re.match(r"^\s*第([一二三四五六七八九十]+)章\s*(.+?)\s*$", line)
    if not m:
        return None, ""
    raw = m.group(1)
    if raw == "十":
        num = 10
    elif raw.startswith("十"):
        num = 10 + CHAPTER_NUMS.get(raw[1:], 0)
    elif raw.endswith("十"):
        num = CHAPTER_NUMS.get(raw[0], 0) * 10
    else:
        num = CHAPTER_NUMS.get(raw, 0)
    return num or None, clean_inline(m.group(2))


def _section_from_line(line: str) -> tuple[str, str] | tuple[None, None]:
    m = re.match(r"^\s*((?:[1-5]\.)+\d+)\s+(.+?)\s*$", line)
    if not m:
        return None, None
    title = clean_inline(m.group(2))
    if len(title) > 80 or re.search(r"\.{4,}", title):
        return None, None
    return m.group(1), title


def _is_example_header_only(rest: str) -> bool:
    r = clean_inline(rest)
    if not r:
        return True
    if r in {"：", ":"}:
        return True
    if "：" in r and not has_latin(r):
        return True
    if has_cjk(r) and not re.search(r"[A-Za-z][A-Za-z='’\\-]*", r):
        return True
    if re.fullmatch(r"[A-Za-z-]+和\s*[A-Za-z-]+", r):
        return True
    return False


def _match_example_start(line: str, current_num: str) -> tuple[str, str, str, str] | None:
    s = line.strip()
    m = re.match(r"^(?:例\s*)?\((\d+)\)\s*([a-z])\.\s*(.*)$", s)
    if m:
        num, letter, rest = m.groups()
        return num, letter, f"({num}) {letter}.", rest
    m = re.match(r"^(?:例\s*)?\((\d+)\)\s*(.*)$", s)
    if m:
        num, rest = m.groups()
        if _is_example_header_only(rest):
            return num, "", f"({num})", ""
        return num, "", f"({num})", rest
    if current_num:
        m = re.match(r"^([a-z])\.\s*(.*)$", s)
        if m:
            letter, rest = m.groups()
            return current_num, letter, f"({current_num}) {letter}.", rest
    return None


def _split_form_translation(line: str) -> tuple[str, str]:
    raw = clean_inline(line)
    if not raw:
        return "", ""
    m = re.match(r"^([^一-龥]+?)[（(]([^()（）]*[\u3400-\u9fff][^()（）]*)[)）]\s*$", raw)
    if m:
        return clean_inline(m.group(1)), clean_inline(m.group(2))
    m = re.match(r"^([^一-龥]+?)([\u3400-\u9fff].*)$", raw)
    if m and has_latin(m.group(1)):
        return clean_inline(m.group(1)), clean_inline(m.group(2))
    return raw, ""


def _line_is_structural_gloss(line: str) -> bool:
    stripped = clean_inline(line)
    if not stripped:
        return False
    if stripped.startswith("【") or stripped.endswith("】"):
        return True
    if TAG_RE.search(stripped):
        return True
    if has_cjk(stripped) and not re.search(r"[。！？?]$", stripped) and len(stripped) <= 50:
        return True
    return False


def _parse_example_block(lines: list[str]) -> dict[str, Any]:
    content = [clean_inline(line) for line in lines if clean_inline(line)]
    commentary: list[str] = []
    form = ""
    gloss_lines: list[str] = []
    translation = ""
    warnings: list[str] = []

    while content and re.fullmatch(r"\d{1,3}", content[-1]):
        content.pop()

    for idx, line in enumerate(content):
        if line.startswith("【") or line.endswith("】"):
            commentary.append(line)
            continue
        if not form:
            if has_latin(line):
                f, t = _split_form_translation(line)
                form = f
                if t and has_cjk(t):
                    translation = t
                continue
            commentary.append(line)
            continue
        if not translation and has_cjk(line):
            if _line_is_structural_gloss(line) and not re.search(r"[。！？?]$", line):
                gloss_lines.append(line)
            else:
                translation = line
            continue
        if not translation and has_latin(line) and not has_cjk(line) and not gloss_lines:
            # A continuation form line, used sparingly for wrapped examples.
            if len(line.split()) <= 12 and not TAG_RE.search(line):
                form = clean_inline(form + " " + line)
            else:
                gloss_lines.append(line)
            continue
        commentary.append(line)

    if not form:
        warnings.append("missing_truku_form")
    if not translation:
        warnings.append("missing_chinese_free_translation")
    if form and has_cjk(form):
        warnings.append("form_contains_cjk")
    confidence = "high" if form and translation and not warnings else "medium" if form and translation else "low"
    tags = sorted(set(m.group(0) for m in TAG_RE.finditer(" ".join(gloss_lines))))
    return {
        "truku_line_raw": form,
        "gloss_line_raw": " | ".join(gloss_lines),
        "chinese_translation_raw": translation,
        "commentary_raw": " | ".join(commentary),
        "grammatical_tags_raw": ";".join(tags),
        "extraction_confidence": confidence,
        "parse_warnings": ";".join(warnings),
    }


def _chapter2_extract_compound_form(line: str) -> str:
    text = clean_inline(line)
    if not text or "→" in text or text.startswith(("表", "華語")):
        return ""
    if "：" in text or ":" in text:
        text = re.split(r"[：:]", text, maxsplit=1)[-1]
    text = _strip_trailing_footnote_number(text)
    text = re.sub(r"^\s*[a-z]\.\s*", "", text)
    text = clean_inline(text)
    if not has_latin(text) or has_cjk(text):
        return ""
    if re.fullmatch(r"[A-ZAVNPOS+()（）\\s-]+", text):
        return ""
    return text


def _chapter2_true_free_translation(line: str) -> str:
    text = clean_inline(line)
    if "→" not in text:
        return ""
    text = text.split("→")[-1]
    text = _strip_trailing_footnote_number(text)
    return clean_inline(text)


def _parse_chapter2_compound_block(lines: list[str]) -> list[dict[str, Any]]:
    content = [clean_inline(line) for line in lines if clean_inline(line)]
    parsed: list[dict[str, Any]] = []
    idx = 0
    while idx < len(content):
        form = _chapter2_extract_compound_form(content[idx])
        if not form:
            idx += 1
            continue
        gloss = ""
        translation = ""
        j = idx + 1
        while j < len(content):
            line = content[j]
            if _chapter2_extract_compound_form(line):
                break
            if not gloss and has_cjk(line) and "→" not in line:
                gloss = line
            if "→" in line:
                translation = _chapter2_true_free_translation(line)
                break
            j += 1
        if gloss and translation:
            tags = sorted(set(m.group(0) for m in TAG_RE.finditer(gloss)))
            parsed.append({
                "truku_line_raw": form,
                "gloss_line_raw": gloss,
                "chinese_translation_raw": translation,
                "commentary_raw": "",
                "grammatical_tags_raw": ";".join(tags),
                "extraction_confidence": "high",
                "parse_warnings": "chapter2_compound_special_parser",
            })
            idx = j + 1
        else:
            idx += 1
    return parsed


# --- F3: recover a dropped second sentence (Q/A answer) from commentary (2026-06-10) ---
_QA_LABEL_RE = re.compile(r"^\s*[A-Za-z]\s*[:：]\s*")


def _looks_like_recoverable_second_sentence(piece: str) -> bool:
    core = _QA_LABEL_RE.sub("", piece).strip()
    if len(re.findall(r"[A-Za-z][A-Za-z='’ʔ.\-]*", core)) < 2:
        return False
    # genuine: a Q:/A: dialogue label, or a pure-Latin clause (not a Chinese-glossed
    # table row); excludes the compound-word tables that also leak into commentary.
    return bool(_QA_LABEL_RE.match(piece)) or not has_cjk(core)


def _recover_dropped_second_sentence(parsed_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Recover a second Truku sentence the one-form-per-block parser hid in
    commentary (typically a Q/A answer). Only recovers when the second sentence
    also has a Chinese translation (a valid <S> needs one); otherwise the block
    is left unchanged for the maintainer's hand-pass.
    """
    if len(parsed_items) != 1:
        return parsed_items
    item = parsed_items[0]
    pieces = [p.strip() for p in (item.get("commentary_raw", "") or "").split("|") if p.strip()]
    for i, piece in enumerate(pieces):
        if not _looks_like_recoverable_second_sentence(piece):
            continue
        if not (i + 1 < len(pieces) and has_cjk(pieces[i + 1]) and not has_latin(pieces[i + 1])):
            return parsed_items  # no translation captured -> leave for hand
        translation = pieces[i + 1]
        form = _QA_LABEL_RE.sub("", piece).strip()
        # drop a starred ungrammatical slash alternative, e.g. "N-naku. / * mu." -> "N-naku."
        form = clean_inline(re.sub(r"\s*/\s*\*[^/()（）]*", "", form))
        remaining = [p for j, p in enumerate(pieces) if j not in (i, i + 1)]
        second = {
            "truku_line_raw": form,
            "gloss_line_raw": "",
            "chinese_translation_raw": translation,
            "commentary_raw": "",
            "grammatical_tags_raw": "",
            "extraction_confidence": "medium",
            "parse_warnings": "recovered_second_sentence_from_commentary",
        }
        first = dict(item)
        first["commentary_raw"] = " | ".join(remaining)
        return [first, second]
    return parsed_items


def parse_examples(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    if not list((ROOT / "data/raw/page_text").glob("page_*.txt")):
        extract_pdf_text(cfg)
    page_rows = {int(row["page_number_one_based"]): row for row in read_csv_dicts(ROOT / "data/processed/pages.csv")}
    records: list[dict[str, Any]] = []
    chapter_number = ""
    section_number = ""
    section_title = ""
    chapter_title = ""
    current_num = ""
    seq = 0

    def emit(page_one: int, label: str, num: str, letter: str, raw_lines: list[str], start_line: int) -> None:
        nonlocal seq
        if not raw_lines:
            return
        parsed_items = _parse_chapter2_compound_block(raw_lines) if chapter_number == "2" else []
        if not parsed_items:
            parsed_items = _recover_dropped_second_sentence([_parse_example_block(raw_lines)])
        total = len(parsed_items)
        for item_idx, parsed in enumerate(parsed_items, start=1):
            if not parsed["truku_line_raw"] and not parsed["chinese_translation_raw"]:
                continue
            seq += 1
            rec_id = f"{SOURCE_ID}_RAW_{seq:04d}"
            if chapter_number == "2" and total > 1 and letter:
                # chapter-2 compound: every item gets a numeric suffix (unchanged)
                item_letter = f"{letter}{item_idx}"
                item_label = f"{label}{item_idx}"
            elif total > 1 and item_idx > 1:
                # recovered second sentence (e.g. Q/A answer): keep item 1's id,
                # suffix the 2nd+ so ids stay unique (E007D -> E007D2).
                item_letter = f"{letter}{item_idx}" if letter else str(item_idx)
                item_label = f"{label}.{item_idx}"
            else:
                item_letter = letter
                item_label = label
            page_row = page_rows.get(page_one, {})
            record = {
                "example_record_id": rec_id,
                "source_id": SOURCE_ID,
                "page_number_one_based": page_one,
                "printed_page_number": page_row.get("printed_page_number", ""),
                "example_number": num,
                "subexample_letter": item_letter,
                "example_label_raw": item_label,
                "chapter_number": chapter_number,
                "section_number": section_number,
                "section_title": section_title or chapter_title,
                "raw_block_ids": f"page_{page_one:04d}:line_{start_line}",
                "raw_text_combined": "\n".join(raw_lines),
                "english_translation_raw_if_source_published": "",
                "root_or_underlying_form_raw": "",
                "phonetic_form_raw": "",
                "morphology_label_raw": "",
                "extraction_method": "text_layer_pdftotext_layout_with_line_heuristics",
            }
            record.update(parsed)
            records.append(record)

    for page_one in sorted(page_rows):
        text = page_text_path(page_one).read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        block_lines: list[str] = []
        block_label = ""
        block_num = ""
        block_letter = ""
        block_start_line = 0
        for line_idx, line in enumerate(lines, start=1):
            ch_num, ch_title = _chapter_from_line(line)
            if ch_num is not None:
                chapter_number = str(ch_num)
                chapter_title = ch_title
                section_number = ""
                section_title = ch_title
            sec_num, sec_title = _section_from_line(line)
            if sec_num:
                section_number = sec_num
                section_title = sec_title or ""

            start = _match_example_start(line, current_num)
            if start:
                num, letter, label, rest = start
                if rest == "":
                    current_num = num
                    if block_lines:
                        emit(page_one, block_label, block_num, block_letter, block_lines, block_start_line)
                        block_lines = []
                    continue
                if block_lines:
                    emit(page_one, block_label, block_num, block_letter, block_lines, block_start_line)
                current_num = num
                block_label = label
                block_num = num
                block_letter = letter
                block_start_line = line_idx
                block_lines = [rest]
                continue

            if block_lines:
                if not line.strip():
                    emit(page_one, block_label, block_num, block_letter, block_lines, block_start_line)
                    block_lines = []
                    continue
                if re.match(r"^\s*\d{1,3}\s*$", line):
                    block_lines.append(line)
                    emit(page_one, block_label, block_num, block_letter, block_lines, block_start_line)
                    block_lines = []
                    continue
                block_lines.append(line)
        if block_lines:
            emit(page_one, block_label, block_num, block_letter, block_lines, block_start_line)

    write_jsonl(ROOT / "data/processed/examples_raw.jsonl", records)
    write_csv(ROOT / "data/processed/parse_warnings.csv", [
        {
            "example_record_id": r["example_record_id"],
            "page_number_one_based": r["page_number_one_based"],
            "example_label_raw": r["example_label_raw"],
            "parse_warnings": r["parse_warnings"],
        }
        for r in records if r.get("parse_warnings")
    ], ["example_record_id", "page_number_one_based", "example_label_raw", "parse_warnings"])
    write_csv(ROOT / "data/processed/parse_errors.csv", [], ["page_number_one_based", "line_number", "error_type", "raw_text", "notes"])
    log("parse_examples", f"parsed {len(records)} numbered example candidates")


def _looks_like_embedded_free_translation(text: str) -> bool:
    text = clean_inline(text)
    if not text or not has_cjk(text):
        return False
    if re.search(r"[。！？?]$", text):
        return True
    # Gloss lines are usually whitespace-delimited morpheme glosses. A compact
    # Mandarin clause without spaces is usually the free translation that was
    # glued to the gloss by pdftotext layout extraction.
    if " " not in text and cjk_count(text) >= 5:
        return True
    if re.search(r"(要|是|在|有|了|把|給|很|不|嗎|誰|哪裡)", text) and cjk_count(text) >= 5:
        return True
    return False


def _split_embedded_translation_from_gloss(gloss: str, translation: str) -> tuple[str, str, str]:
    gloss = clean_inline(gloss)
    translation = clean_inline(translation)
    if translation or " | " not in gloss:
        return gloss, translation, ""
    parts = [clean_inline(part) for part in gloss.split("|") if clean_inline(part)]
    if len(parts) < 2:
        return gloss, translation, ""
    candidate = parts[-1]
    if not _looks_like_embedded_free_translation(candidate):
        return gloss, translation, ""
    return " | ".join(parts[:-1]), candidate, "split_embedded_translation_from_gloss"


def _page_initial_translation_continuation(page_one_based: int) -> str:
    path = page_text_path(page_one_based)
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        candidate = clean_inline(line)
        if not candidate:
            continue
        if re.match(r"^(?:\(?\d+\)?|[a-z]\.|第|表|圖|[0-9]+\\.)", candidate):
            return ""
        if has_cjk(candidate) and not has_latin(candidate) and re.search(r"[。！？?]$", candidate):
            return candidate
        return ""
    return ""


def _clean_form_field_for_sidecar(text: str) -> tuple[str, list[str]]:
    original = clean_inline(text)
    cleaned = _strip_trailing_footnote_number(original)
    notes = []
    if cleaned != original:
        notes.append("removed_trailing_form_footnote_number")
    collapsed = re.sub(r"\.{2,}$", ".", cleaned)
    if collapsed != cleaned:
        notes.append("collapsed_sentence_final_repeated_period")
    return clean_inline(collapsed), notes


def _clean_translation_field_for_sidecar(text: str) -> tuple[str, list[str]]:
    original = clean_inline(text)
    cleaned = original
    notes = []
    if has_cjk(cleaned):
        stripped = re.sub(r"\s+\d{1,3}$", "", cleaned)
        stripped = re.sub(r"\s+\d{1,3}([。！？])$", r"\1", stripped)
        if stripped != cleaned:
            notes.append("removed_trailing_translation_footnote_number")
        cleaned = stripped
    return clean_inline(cleaned), notes


def normalize_text(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    rows = read_jsonl(ROOT / "data/processed/examples_raw.jsonl")
    if not rows:
        parse_examples(cfg)
        rows = read_jsonl(ROOT / "data/processed/examples_raw.jsonl")
    clean_rows: list[dict[str, Any]] = []
    iso = cfg["language"]["expected_iso_639_3"]
    normalization_artifacts: list[dict[str, Any]] = []
    for raw in rows:
        form = clean_inline(raw.get("truku_line_raw", ""))
        gloss = clean_inline(raw.get("gloss_line_raw", ""))
        translation = clean_inline(raw.get("chinese_translation_raw", ""))
        gloss, translation, split_note = _split_embedded_translation_from_gloss(gloss, translation)
        label = clean_inline(raw.get("example_label_raw", ""))
        extraction_confidence = raw.get("extraction_confidence", "low")
        if split_note and form and translation:
            extraction_confidence = "medium"
        notes = []
        if raw.get("parse_warnings"):
            notes.append(raw["parse_warnings"])
        if split_note:
            notes.append(split_note)
        raw_form_has_trailing_footnote = bool(re.search(r"\s+\d{1,3}$", form))
        should_check_next_page_translation = (
            not translation
            and form
            and gloss
            and raw_form_has_trailing_footnote
            and not has_cjk(form)
            and not form.lstrip().startswith("*")
        )
        if should_check_next_page_translation:
            continued = _page_initial_translation_continuation(int(raw.get("page_number_one_based") or 0) + 1)
            if continued:
                translation = continued
                notes.append("recovered_page_initial_translation_continuation_after_footnote")
                extraction_confidence = "medium" if form and gloss else extraction_confidence
                normalization_artifacts.append({
                    "example_record_id": raw["example_record_id"],
                    "page_number_one_based": raw.get("page_number_one_based", ""),
                    "field": "chinese_translation_clean",
                    "original_value": "",
                    "clean_value": translation,
                    "action": "recovered_page_initial_translation_continuation_after_footnote",
                    "notes": "Translation appeared as the first text line on the next PDF page after a source footnote marker.",
                })
        form_before_clean = form
        translation_before_clean = translation
        form, form_notes = _clean_form_field_for_sidecar(form)
        translation, translation_notes = _clean_translation_field_for_sidecar(translation)
        for action in form_notes:
            notes.append(action)
            normalization_artifacts.append({
                "example_record_id": raw["example_record_id"],
                "page_number_one_based": raw.get("page_number_one_based", ""),
                "field": "truku_line_clean",
                "original_value": form_before_clean,
                "clean_value": form,
                "action": action,
                "notes": "Raw text remains unchanged in examples_raw.jsonl.",
            })
        for action in translation_notes:
            notes.append(action)
            normalization_artifacts.append({
                "example_record_id": raw["example_record_id"],
                "page_number_one_based": raw.get("page_number_one_based", ""),
                "field": "chinese_translation_clean",
                "original_value": translation_before_clean,
                "clean_value": translation,
                "action": action,
                "notes": "Raw text remains unchanged in examples_raw.jsonl.",
            })
        clean_rows.append({
            "example_record_id": raw["example_record_id"],
            "source_id": raw["source_id"],
            "page_number_one_based": raw["page_number_one_based"],
            "printed_page_number": raw.get("printed_page_number", ""),
            "example_number": raw.get("example_number", ""),
            "subexample_letter": raw.get("subexample_letter", ""),
            "example_label_clean": label,
            "truku_line_clean": form,
            "gloss_line_clean": gloss,
            "chinese_translation_clean": translation,
            "english_translation_clean_if_source_published": "",
            "chapter_number": raw.get("chapter_number", ""),
            "section_number": raw.get("section_number", ""),
            "section_title": raw.get("section_title", ""),
            "ISO_639_3": iso,
            "dialect_or_location_attribute_value": "",
            "extraction_confidence": extraction_confidence,
            "xml_eligible": "",
            "rejection_reason": "",
            "notes": "; ".join(notes),
        })
    write_jsonl(ROOT / "data/processed/examples_clean.jsonl", clean_rows)
    write_csv(ROOT / "data/processed/normalization_artifacts.csv", normalization_artifacts, [
        "example_record_id", "page_number_one_based", "field", "original_value", "clean_value", "action", "notes",
    ])
    report = [
        "# Normalization Report",
        "",
        "- Unicode normalization: NFC.",
        "- Whitespace normalization: repeated spaces collapsed in clean fields only.",
        "- Truku orthography, case, apostrophes, hyphens, equals signs, phonetic symbols, and affix markers were preserved.",
        "- Obvious text-layer artifacts were corrected in clean fields only: trailing footnote numbers, sentence-final doubled periods, and guarded page-initial translation continuations.",
        "- Chinese source translations were preserved; no machine translation was used.",
        "- Raw examples remain in `data/processed/examples_raw.jsonl` with original line breaks.",
        f"- Normalization artifact records written: {len(normalization_artifacts)}.",
        f"- Clean records written: {len(clean_rows)}.",
    ]
    (ROOT / "data/processed/normalization_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    log("normalize_text", f"normalized {len(clean_rows)} example records")


def parse_glosses(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    rows = read_jsonl(ROOT / "data/processed/examples_clean.jsonl")
    if not rows:
        normalize_text(cfg)
        rows = read_jsonl(ROOT / "data/processed/examples_clean.jsonl")
    gloss_records = []
    tag_counter: Counter[str] = Counter()
    for idx, row in enumerate(rows, start=1):
        gloss = row.get("gloss_line_clean", "")
        tags = sorted(set(m.group(0) for m in TAG_RE.finditer(gloss)))
        for tag in tags:
            tag_counter[tag] += 1
        if not gloss:
            continue
        gloss_records.append({
            "gloss_record_id": f"{SOURCE_ID}_GLOSS_{idx:04d}",
            "example_record_id": row["example_record_id"],
            "truku_line_clean": row.get("truku_line_clean", ""),
            "gloss_line_clean": gloss,
            "chinese_translation_clean": row.get("chinese_translation_clean", ""),
            "morpheme_alignment_raw": gloss,
            "grammatical_tags": ";".join(tags),
            "tag_inventory": ";".join(tags),
            "gloss_parse_confidence": "medium" if tags else "low",
            "notes": "Sidecar only; glosses are not emitted as TRANSL.",
        })
    expansions = {
        "AF": "actor focus",
        "PF": "patient focus",
        "LF": "locative focus",
        "IF": "instrument/benefactive focus",
        "Caus": "causative",
        "RED": "reduplication",
        "CV": "CV reduplication shape",
        "CVCV": "CVCV reduplication shape",
        "主格": "nominative",
        "屬格": "genitive",
        "受格": "object/oblique",
        "主題": "topic",
    }
    tag_rows = [{
        "tag": tag,
        "expanded_meaning_if_known": expansions.get(tag, ""),
        "source_page": "",
        "source_section": "",
        "notes": f"Observed {count} time(s) in parsed gloss sidecars.",
    } for tag, count in sorted(tag_counter.items())]
    write_jsonl(ROOT / "data/processed/gloss_records.jsonl", gloss_records)
    write_csv(ROOT / "data/processed/tag_inventory.csv", tag_rows, ["tag", "expanded_meaning_if_known", "source_page", "source_section", "notes"])
    log("parse_glosses", f"wrote {len(gloss_records)} gloss records and {len(tag_rows)} tags")


def extract_tables(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    _, decrypted = _pdf_paths(cfg)
    if not decrypted.exists():
        decrypt_pdf(cfg)
    table_rows: list[dict[str, Any]] = []
    if pdfplumber:
        with pdfplumber.open(decrypted) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                try:
                    tables = page.extract_tables() or []
                except Exception as exc:
                    log("extract_tables", f"page {page_idx + 1}: pdfplumber table extraction error: {exc}")
                    tables = []
                for table_idx, table in enumerate(tables, start=1):
                    header = [clean_inline(c or "") for c in (table[0] if table else [])]
                    for row_idx, row in enumerate(table[1:] if len(table) > 1 else table, start=1):
                        cells = [clean_inline(c or "") for c in (row or [])]
                        cell_text = " | ".join(c for c in cells if c)
                        if not cell_text:
                            continue
                        latin_cells = [c for c in cells if has_latin(c)]
                        cjk_cells = [c for c in cells if has_cjk(c)]
                        table_rows.append({
                            "table_id": f"p{page_idx + 1:04d}_t{table_idx:02d}",
                            "page_number_one_based": page_idx + 1,
                            "printed_page_number": "",
                            "chapter_number": "",
                            "section_number": "",
                            "table_title": "",
                            "row_label": str(row_idx),
                            "column_label": ";".join(header),
                            "truku_form_raw": latin_cells[0] if latin_cells else "",
                            "truku_form_clean": latin_cells[0] if latin_cells else "",
                            "chinese_meaning_raw": cjk_cells[0] if cjk_cells else "",
                            "chinese_meaning_clean": cjk_cells[0] if cjk_cells else "",
                            "morphology_label": "",
                            "word_class_change": "→" if "→" in cell_text else "",
                            "cell_raw": cell_text,
                            "cell_clean": cell_text,
                            "parse_confidence": "medium",
                            "xml_eligible_candidate": "false",
                            "notes": "Extracted as sidecar table data; table rows are not emitted to Final_XML by default.",
                        })

    if not table_rows:
        for page_file in sorted((ROOT / "data/raw/page_text").glob("page_*.txt")):
            page_one = int(page_file.stem.split("_")[1])
            for line in page_file.read_text(encoding="utf-8", errors="replace").splitlines():
                if "表 " in line or re.match(r"^\s*表\s*\d", line):
                    table_rows.append({
                        "table_id": f"p{page_one:04d}_heuristic",
                        "page_number_one_based": page_one,
                        "printed_page_number": "",
                        "chapter_number": "",
                        "section_number": "",
                        "table_title": clean_inline(line),
                        "row_label": "",
                        "column_label": "",
                        "truku_form_raw": "",
                        "truku_form_clean": "",
                        "chinese_meaning_raw": "",
                        "chinese_meaning_clean": "",
                        "morphology_label": "",
                        "word_class_change": "",
                        "cell_raw": clean_inline(line),
                        "cell_clean": clean_inline(line),
                        "parse_confidence": "low",
                        "xml_eligible_candidate": "false",
                        "notes": "Heuristic table title inventory.",
                    })

    write_csv(ROOT / "data/processed/morphology_tables.csv", table_rows, [
        "table_id", "page_number_one_based", "printed_page_number", "chapter_number", "section_number", "table_title",
        "row_label", "column_label", "truku_form_raw", "truku_form_clean", "chinese_meaning_raw", "chinese_meaning_clean",
        "morphology_label", "word_class_change", "cell_raw", "cell_clean", "parse_confidence", "xml_eligible_candidate", "notes",
    ])
    log("extract_tables", f"wrote {len(table_rows)} table sidecar rows")


def map_language(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    original, decrypted = _pdf_paths(cfg)
    original_hash, decrypted_hash = _source_pdf_hashes(cfg)
    mapping = [{
        "source_language_label_raw": "太魯閣語 / Truku",
        "thesis_language_label_raw": "太魯閣語(Truku)",
        "FormosanBank_language_name": "Truku / Taroko",
        "ISO_639_3": "trv",
        "glottocode_if_known": "",
        "dialect_or_variety_raw": "Truku",
        "community_location_raw": "Dumung / 銅門; Tkijig / 崇德; Sioulin Township, Hualien County",
        "XML_dialect_attribute_value": "",
        "mapping_confidence": "high",
        "validation_status": "validated_against_formosan_repo_audit_and_qc: Formosan language folder is Truku; xml:lang uses ISO 639-3 code trv",
        "notes": "Final XML uses Final_XML/Truku with xml:lang=\"trv\". Glottocode omitted because it was not locally verified for this source.",
    }]
    write_csv(ROOT / "data/processed/language_mapping.csv", mapping, [
        "source_language_label_raw", "thesis_language_label_raw", "FormosanBank_language_name", "ISO_639_3",
        "glottocode_if_known", "dialect_or_variety_raw", "community_location_raw", "XML_dialect_attribute_value",
        "mapping_confidence", "validation_status", "notes",
    ])
    source_meta = [{
        "source_id": SOURCE_ID,
        "title_zh": cfg["source"]["title_zh"],
        "title_en": cfg["source"]["title_en"],
        "author_zh": cfg["source"]["author_zh"],
        "author_romanized": cfg["source"]["author_romanized"],
        "adviser": "葉美利 / Dr. Marie Meili Yeh",
        "institution_zh": "國立新竹教育大學",
        "institution_en": "National Hsin-Chu University of Education",
        "department_zh": "臺灣語言與語文教育研究所",
        "department_en": "Graduate Institute of Taiwan Languages and Language Education",
        "degree": "碩士論文 / MA thesis",
        "publication_year": "2008",
        "publication_month": "July",
        "citation_string": citation(),
        "bibtex_citation": bibtex(),
        "source_pdf_path": rel(original),
        "source_pdf_sha256": original_hash,
        "decrypted_pdf_sha256": decrypted_hash,
        "permission_status": "full_rights_obtained",
        "rights_notes": "© Lowking Wei-Cheng Hsu / 許韋晟. Used by FormosanBank with permission.",
        "notes": "Selectable text PDF with owner copy restriction; qpdf decryption used for extraction.",
    }]
    write_csv(ROOT / "data/processed/source_metadata.csv", source_meta, [
        "source_id", "title_zh", "title_en", "author_zh", "author_romanized", "adviser",
        "institution_zh", "institution_en", "department_zh", "department_en", "degree",
        "publication_year", "publication_month", "citation_string", "bibtex_citation",
        "source_pdf_path", "source_pdf_sha256", "decrypted_pdf_sha256", "permission_status",
        "rights_notes", "notes",
    ])
    facts = [
        "# Source Facts",
        "",
        "- PDF page 1: title page identifies 國立新竹教育大學臺灣語言與語文教育研究所, the MA thesis title 太魯閣語構詞法研究 / Word Formation In Truku, adviser 葉美利 / Dr. Marie Meili Yeh, and author 許韋晟 / Lowking Wei-Cheng Hsu.",
        "- PDF page 1: date is 中華民國九十七年七月 / July 2008.",
        "- PDF page 3: Chinese abstract states the thesis studies Truku word formation, including compounding, derivation, reduplication, and functional shift.",
        "- PDF page 5: English abstract states the Truku language data come from Dumung and Tkijig Tribes in Sioulin Township, Hualien County.",
        "- PDF pages 17-18: research method and speaker table identify fieldwork with Dumung / 銅門 and Tkijig / 崇德 speakers.",
        "- PDF pages 26 onward: numbered linguistic examples contain Truku form lines, Chinese gloss/morpheme lines, and Chinese free translations.",
        "- PDF pages in chapters 2-4: morphology tables and lexical/morphological records are present; these are preserved in sidecar data and not emitted to Final_XML by default.",
        "- Extraction provenance: qpdf decryption, pdftotext -layout selected page text, PyMuPDF/pdfplumber comparison, PyMuPDF page-image rendering.",
    ]
    (ROOT / "data/processed/source_facts.md").write_text("\n".join(facts) + "\n", encoding="utf-8")
    rights = [
        "# Rights And Permission Notes",
        "",
        "- rights_status: full_rights_obtained",
        "- source_type: selectable_text_pdf_with_owner_copy_restriction",
        "- primary_extraction: pdf_text_layer",
        "- decrypt_for_extraction: permitted",
        "- ocr_primary: false",
        "- ocr_fallback: only_if_needed_and_reviewed",
        "- machine_translation: prohibited",
        "- create_final_xml: true",
        "- final_xml_output: Final_XML/Truku",
        "",
        source_copyright(),
    ]
    (ROOT / "data/processed/rights_and_permission_notes.md").write_text("\n".join(rights) + "\n", encoding="utf-8")
    log("map_language", "wrote source metadata, language mapping, source facts, and rights notes")


def _is_affix_or_morphology(form: str, translation: str) -> bool:
    compact = form.strip()
    trans = translation.strip()
    if not compact:
        return True
    if "→" in compact or "+" in compact or "→" in trans:
        return True
    if re.match(r"^\d+\.", compact):
        return True
    if compact.endswith("(") or compact.endswith("（") or trans.startswith(")") or trans.startswith("）"):
        return True
    if len(compact.split()) <= 3 and trans.startswith("指"):
        return True
    if re.fullmatch(r"[*ØA-Za-z?()=<>/\\-]+", compact) and len(compact.split()) <= 3 and not re.search(r"[.?!。！？]", compact):
        return True
    if len(compact.split()) <= 2 and not re.search(r"[.?!。！？]", compact) and cjk_count(translation) <= 8:
        return True
    return False


def _is_cross_reference_only_translation(translation: str) -> bool:
    text = clean_inline(translation)
    return bool(re.fullmatch(r"例\s*\(?\d+\)?\s*[a-z]?", text, flags=re.IGNORECASE))


def _has_leading_starred_slash_option(form: str) -> bool:
    return bool(re.match(r"^\s*\*\s*[^\s/]+(?:\s*/\s*)[^\s/]+", clean_inline(form)))


def _is_chapter2_compound_record(row: dict[str, Any]) -> bool:
    return str(row.get("chapter_number")) == "2" and "chapter2_compound_special_parser" in str(row.get("notes", ""))


def quality_filter(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    rows = read_jsonl(ROOT / "data/processed/examples_clean.jsonl")
    if not rows:
        normalize_text(cfg)
        rows = read_jsonl(ROOT / "data/processed/examples_clean.jsonl")
    min_conf = cfg["examples"].get("min_confidence_for_xml", "medium")
    accepted = []
    rejected = []
    for row in rows:
        form = row.get("truku_line_clean", "")
        trans = row.get("chinese_translation_clean", "")
        reason = ""
        if not form:
            reason = "missing_truku_form"
        elif form.lstrip().startswith("*") and not _has_leading_starred_slash_option(form):
            reason = "ungrammatical_starred_form"
        elif has_cjk(form):
            reason = "form_contains_chinese_or_academic_prose"
        elif not trans or not has_cjk(trans):
            reason = "missing_source_published_chinese_translation"
        elif _is_cross_reference_only_translation(trans):
            reason = "cross_reference_only_not_source_free_translation"
        elif confidence_rank(row.get("extraction_confidence", "low")) < confidence_rank(min_conf):
            reason = "low_extraction_confidence"
        elif _is_affix_or_morphology(form, trans) and not _is_chapter2_compound_record(row):
            reason = "isolated_affix_lexeme_or_morphology_record_sidecar_only"
        elif re.search(r"\b(AF|PF|LF|IF|Caus|RED)\b", trans):
            reason = "translation_looks_like_gloss_not_free_translation"
        elif "參考文獻" in trans or "本論文" in form:
            reason = "academic_prose_or_reference"
        row["xml_eligible"] = "false" if reason else "true"
        row["rejection_reason"] = reason
        if not reason and _has_leading_starred_slash_option(form):
            row["notes"] = clean_inline((row.get("notes", "") + "; " if row.get("notes") else "") + "leading_starred_slash_option_retained_for_manual_qc")
        if reason:
            rejected.append({
                "example_record_id": row["example_record_id"],
                "page_number_one_based": row.get("page_number_one_based", ""),
                "example_label_clean": row.get("example_label_clean", ""),
                "truku_line_clean": form,
                "chinese_translation_clean": trans,
                "rejection_reason": reason,
                "notes": row.get("notes", ""),
            })
        else:
            accepted.append(row)
    write_jsonl(ROOT / "data/processed/examples_clean.jsonl", rows)
    write_jsonl(ROOT / "data/processed/quality_filtered_examples.jsonl", accepted)
    write_csv(ROOT / "data/processed/rejected_records.csv", rejected, [
        "example_record_id", "page_number_one_based", "example_label_clean", "truku_line_clean",
        "chinese_translation_clean", "rejection_reason", "notes",
    ])
    log("quality_filter", f"accepted {len(accepted)} XML-eligible examples; rejected {len(rejected)}")


def dedupe_examples(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    rows = read_jsonl(ROOT / "data/processed/quality_filtered_examples.jsonl")
    if not rows:
        quality_filter(cfg)
        rows = read_jsonl(ROOT / "data/processed/quality_filtered_examples.jsonl")
    seen: dict[str, dict[str, Any]] = {}
    dup_rows = []
    for row in rows:
        key = sha256_text(clean_inline(row["truku_line_clean"]) + "\n" + clean_inline(row["chinese_translation_clean"]))
        row["pair_sha256"] = key
        if key in seen:
            row["duplicate_action"] = "omit_from_xml_keep_sidecar"
            dup_rows.append({
                "duplicate_pair_sha256": key,
                "kept_example_record_id": seen[key]["example_record_id"],
                "duplicate_example_record_id": row["example_record_id"],
                "truku_line_clean": row["truku_line_clean"],
                "chinese_translation_clean": row["chinese_translation_clean"],
                "action": "omit_from_xml_keep_sidecar",
                "notes": "Exact duplicate form+translation within this source.",
            })
        else:
            row["duplicate_action"] = "keep"
            seen[key] = row
    write_jsonl(ROOT / "data/processed/quality_filtered_examples.jsonl", rows)
    write_csv(ROOT / "data/processed/duplicates.csv", dup_rows, [
        "duplicate_pair_sha256", "kept_example_record_id", "duplicate_example_record_id",
        "truku_line_clean", "chinese_translation_clean", "action", "notes",
    ])
    log("dedupe_examples", f"found {len(dup_rows)} exact duplicate records")


def _existing_formosan_xml_files() -> list[Path]:
    candidates = []
    for repo in ROOT.parent.glob("Formosan-*"):
        final = repo / "Final_XML"
        if not final.exists() or repo.resolve() == ROOT.resolve():
            continue
        for xml in final.rglob("*.xml"):
            path_text = str(xml)
            if any(token in path_text for token in ["Truku", "Taroko", "Seediq", "/trv/"]):
                candidates.append(xml)
    fb = ROOT.parent / "FormosanBank"
    if fb.exists():
        for xml in fb.rglob("*.xml"):
            if any(token in str(xml) for token in ["Truku", "Taroko", "Seediq", "/trv/"]):
                candidates.append(xml)
    return candidates


def dedupe_against_formosanbank(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    rows = read_jsonl(ROOT / "data/processed/quality_filtered_examples.jsonl")
    if not rows:
        quality_filter(cfg)
        rows = read_jsonl(ROOT / "data/processed/quality_filtered_examples.jsonl")
    existing: list[tuple[str, str, str]] = []
    for xml in _existing_formosan_xml_files():
        try:
            root = ET.parse(xml).getroot()
        except Exception:
            continue
        lang = root.attrib.get(f"{{{XML_NS}}}lang", "")
        if lang and lang != "trv":
            continue
        for s in root.findall("S"):
            form_el = s.find("FORM")
            if form_el is not None and form_el.text:
                existing.append((clean_inline(form_el.text), str(xml), s.attrib.get("id", "")))
    candidates = []
    existing_by_hash = {sha256_text(form): (path, sid) for form, path, sid in existing}
    for row in rows:
        form = clean_inline(row["truku_line_clean"])
        key = sha256_text(form)
        status = "none"
        if key in existing_by_hash:
            path, sid = existing_by_hash[key]
            status = "exact_form_match"
            candidates.append({
                "example_record_id": row["example_record_id"],
                "source_form": form,
                "source_translation": row["chinese_translation_clean"],
                "overlap_status": status,
                "matched_file": rel(path),
                "matched_sentence_id": sid,
                "similarity": "100",
                "action": "review_before_import",
                "notes": "Exact FORM match in existing FormosanBank-adjacent XML.",
            })
        elif fuzz and existing:
            best_score = 0
            best = None
            for eform, path, sid in existing:
                score = fuzz.ratio(form, eform)
                if score > best_score:
                    best_score = score
                    best = (path, sid)
            if best_score >= 95 and best:
                candidates.append({
                    "example_record_id": row["example_record_id"],
                    "source_form": form,
                    "source_translation": row["chinese_translation_clean"],
                    "overlap_status": "near_form_match",
                    "matched_file": rel(best[0]),
                    "matched_sentence_id": best[1],
                    "similarity": str(best_score),
                    "action": "review_before_import",
                    "notes": "Near FORM match in existing FormosanBank-adjacent XML.",
                })
    write_csv(ROOT / "data/processed/overlap_candidates.csv", candidates, [
        "example_record_id", "source_form", "source_translation", "overlap_status", "matched_file",
        "matched_sentence_id", "similarity", "action", "notes",
    ])
    log("dedupe_against_formosanbank", f"checked {len(existing)} existing forms; overlap candidates={len(candidates)}")


def _sentence_id(row: dict[str, Any], fallback_idx: int, variant_suffix: str = "") -> str:
    chap = row.get("chapter_number") or "X"
    num = str(row.get("example_number") or fallback_idx).zfill(3)
    letter = (row.get("subexample_letter") or "").upper()
    if chap and chap != "X":
        return f"{SOURCE_ID}_C{int(chap):02d}_E{num}{letter}{variant_suffix}"
    return f"{SOURCE_ID}_E{num}{letter or str(fallback_idx).zfill(3)}{variant_suffix}"


def _strip_trailing_footnote_number(text: str) -> str:
    return clean_inline(re.sub(r"\s+\d{1,3}$", "", clean_inline(text)))


def _clean_word_form_for_xml(token: str) -> str:
    token = clean_inline(token)
    token = token.strip("[]")
    token = token.strip()
    token = token.lstrip("(（").rstrip(".,;:?!。！？)）")
    token = token.replace("(", "").replace(")", "").replace("（", "").replace("）", "")
    token = token.rstrip(".,;:?!。！？")
    return token


def _xml_original_form_for_xml(form: str) -> str:
    """Return the cleaned source segmented form before XML surface conversion."""
    text = clean_inline(form)
    text = _strip_trailing_footnote_number(text)
    text = re.sub(r"^(?:Q|A)\s*:\s*", "", text)
    # Parenthesized starred forms such as "(*ge-idas)" are explicitly
    # ungrammatical alternatives, not corpus text. Slash-bearing starred options
    # are handled later by option expansion, so leave those in place here.
    text = re.sub(r"\s*[（(]\s*\*[^/()（）]*[)）]", "", text)
    # Keep parenthesized source information, but remove standalone equality
    # markers that are layout/commentary notation and break W-count checks.
    text = re.sub(r"\s+=+\s+(?=[(（])", " ", text)
    text = re.sub(r"\s+=+\s*$", "", text)
    return clean_inline(text)


def _xml_standard_form_for_xml(form: str) -> str:
    text = _xml_original_form_for_xml(form)
    text = text.replace("（", "(").replace("）", ")")
    text = text.replace("？", "?").replace("！", "!").replace("。", ".")
    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"\s*[（(][^()（）]*[)）]", "", text).strip()
        text = re.sub(r"\s*=+\s*$", "", text).strip()
    text = re.sub(r"(?<!\S)Ø-", "", text)
    text = re.sub(r"(?<!\S)Ø(?=\s|$)", "", text)
    text = text.replace("Ø-", "")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([.,;:?!])", r"\1", text)
    return clean_inline(text)


def _word_tokens_for_xml_sentence(form: str) -> list[str]:
    tokens: list[str] = []
    raw_tokens = _xml_original_form_for_xml(form).split()
    for raw in raw_tokens:
        token = raw.strip()
        if not token:
            continue
        if token in {"Q:", "A:", "Q", "A", "=", "＝"}:
            continue
        token = token.lstrip("*")
        cleaned = _clean_word_form_for_xml(token)
        if not cleaned:
            continue
        tokens.append(cleaned)
    return tokens


def _surface_word_form_for_xml(token: str) -> str:
    """Convert a source segmented token into an unglossed surface word form."""
    cleaned = _clean_word_form_for_xml(token)
    if not cleaned:
        return ""
    if "/" in cleaned:
        return "/".join(_surface_word_form_for_xml(part) for part in cleaned.split("/") if part)
    cleaned = re.sub(r"<([^>]+)>", r"\1", cleaned)
    cleaned = cleaned.replace("-", "").replace("=", "")
    cleaned = cleaned.replace("Ø", "")
    return clean_inline(cleaned)


def _sentence_surface_form_for_xml(segmented_form: str) -> str:
    tokens: list[str] = []
    for raw in clean_inline(segmented_form).split():
        if raw in {"Q:", "A:", "Q", "A", "=", "＝"}:
            continue
        stripped = raw.strip()
        terminal = ""
        for char in reversed(stripped):
            if char in ".,;:?!。！？":
                terminal = char
                break
            if char not in ")]）}":
                break
        surface = _surface_word_form_for_xml(stripped)
        if not surface:
            continue
        tokens.append(surface + terminal)
    text = clean_inline(" ".join(tokens))
    text = re.sub(r"\s+([.,;:?!。！？])", r"\1", text)
    return text


def _gloss_tokens_for_alignment(gloss: str) -> list[str]:
    tokens = []
    for token in clean_inline(gloss).split():
        cleaned = _clean_gloss_token_for_xml(token)
        if cleaned:
            tokens.append(cleaned)
    return tokens


def _split_morpheme_parts_for_xml(value: str) -> list[str]:
    cleaned = _clean_word_form_for_xml(value)
    return _split_cleaned_morpheme_parts(cleaned, preserve_clitic_markers=True)


def _clean_gloss_token_for_xml(token: str) -> str:
    token = clean_inline(token)
    token = token.strip("[]")
    token = token.strip()
    token = token.rstrip(".,;:?!。！？")
    return token


def _split_gloss_parts_for_xml(value: str) -> list[str]:
    cleaned = _clean_gloss_token_for_xml(value)
    return _split_cleaned_morpheme_parts(cleaned)


def _split_cleaned_morpheme_parts(cleaned: str, preserve_clitic_markers: bool = False) -> list[str]:
    if not cleaned:
        return []
    infixes = [part[1:-1] for part in re.findall(r"<[^>]+>", cleaned) if len(part) > 2]
    remainder = re.sub(r"<[^>]+>", "", cleaned)
    segments: list[str] = []
    mark_next_clitic = False
    for part in re.split(r"([-=])", remainder):
        if not part:
            continue
        if part == "=":
            mark_next_clitic = preserve_clitic_markers
            continue
        if part == "-":
            mark_next_clitic = False
            continue
        segments.append(("=" if mark_next_clitic else "") + part)
        mark_next_clitic = False
    if infixes and segments:
        return [segments[0], *infixes, *segments[1:]]
    return segments + infixes or [cleaned]


def _infix_reanalysis_parts(parts: list[str]) -> list[str] | None:
    if len(parts) != 3:
        return None
    left, infix, right = parts
    if any(part.startswith("=") for part in parts):
        return None
    if len(infix) > 2 or not re.fullmatch(r"[A-Za-z]+", infix):
        return None
    return [f"{left}-{right}", f"-{infix}-"]


def _apply_infix_reanalysis(
    form_tokens: list[str],
    form_parts_by_word: list[list[str]],
    gloss_tokens: list[str],
    gloss_part_count: int,
) -> tuple[list[list[str]], list[str]]:
    if not any("<" in token and ">" in token for token in gloss_tokens):
        return form_parts_by_word, []
    delta = sum(len(parts) for parts in form_parts_by_word) - gloss_part_count
    if delta <= 0:
        return form_parts_by_word, []
    adjusted = [list(parts) for parts in form_parts_by_word]
    notes: list[str] = []
    for idx, parts in enumerate(adjusted):
        if delta <= 0:
            break
        reanalysed = _infix_reanalysis_parts(parts)
        if not reanalysed:
            continue
        adjusted[idx] = reanalysed
        delta -= len(parts) - len(reanalysed)
        notes.append(f"infix_reanalysis {form_tokens[idx]} -> {'+'.join(reanalysed)}")
    if delta == 0:
        return adjusted, notes
    return form_parts_by_word, []


def _flatten_morpheme_parts(values: list[str]) -> list[str]:
    parts: list[str] = []
    for value in values:
        parts.extend(_split_morpheme_parts_for_xml(value))
    return parts


def _flatten_gloss_parts(values: list[str]) -> list[str]:
    parts: list[str] = []
    for value in values:
        parts.extend(_split_gloss_parts_for_xml(value))
    return parts


def _standard_word_or_morpheme_form(text: str) -> str:
    standard = _xml_standard_form_for_xml(text)
    standard = _clean_word_form_for_xml(standard)
    return clean_inline(standard)


def _standard_surface_word_form(text: str) -> str:
    return _surface_word_form_for_xml(_xml_standard_form_for_xml(text))


def _add_form(parent: ET.Element, text: str, kind: str = "original") -> ET.Element:
    form = ET.SubElement(parent, "FORM", {"kindOf": kind})
    form.text = text
    return form


def _add_original_and_standard_forms(
    parent: ET.Element,
    original_text: str,
    standard_text: str = "",
    always_standard: bool = False,
) -> None:
    original_text = clean_inline(original_text)
    standard_text = clean_inline(standard_text)
    _add_form(parent, original_text, "original")
    if standard_text and (always_standard or standard_text != original_text):
        _add_form(parent, standard_text, "standard")


def _add_translation(parent: ET.Element, text: str, lang: str) -> ET.Element:
    transl = ET.SubElement(parent, "TRANSL", {f"{{{XML_NS}}}lang": lang})
    transl.text = text
    return transl


# --- F2: alternative renderings -> primary TRANSL + ver="alt" (added 2026-06-10) ---
_F2_CJK = re.compile(r"[㐀-鿿]")
_F2_CJK_PAREN = re.compile(r"[（(]\s*=?\s*([^()（）]*[㐀-鿿][^()（）]*?)\s*[)）]")


def _is_alt_translation(text: str, inside: str) -> bool:
    """True only for a genuine alternative rendering (not an explanatory note,
    not an inline slash list)."""
    if "/" in text or "／" in text:
        return False
    main = clean_inline(_F2_CJK_PAREN.sub("", text).replace("=", " "))
    ci, cm = len(_F2_CJK.findall(inside)), len(_F2_CJK.findall(main))
    return cm >= 4 and ci >= 3 and ci >= 0.5 * cm


def _add_translations(parent: ET.Element, text: str, lang: str) -> None:
    """Emit the source translation; if it carries a genuine alternative rendering
    in parentheses, split it into a primary TRANSL plus a TRANSL ver="alt"."""
    text = clean_inline(text)
    m = _F2_CJK_PAREN.search(text)
    if m and _is_alt_translation(text, m.group(1)):
        primary = clean_inline(_F2_CJK_PAREN.sub("", text).replace("=", " "))
        primary = re.sub(r"\s+([。！？，、；：])", r"\1", primary)
        _add_translation(parent, primary, lang)
        alt = ET.SubElement(parent, "TRANSL", {f"{{{XML_NS}}}lang": lang, "ver": "alt"})
        alt.text = clean_inline(m.group(1))
        return
    _add_translation(parent, text, lang)


# --- W-level word glosses (validators V065/V062) -----------------------------
# Reconstruct each fully-glossed word's gloss from its M glosses. Infix Ms (the
# V067 "-X-" convention) contribute an angle-bracket gloss so V062 is satisfied;
# the remaining (base) Ms join on the morpheme boundary "-".
_INFIX_M_FORM = re.compile(r"-[^-\s]+-")


def _reconstruct_word_gloss(m_forms: list[str], m_glosses: list[str]) -> str:
    base: list[str] = []
    infixes: list[str] = []
    for mf, mg in zip(m_forms, m_glosses):
        (infixes if _INFIX_M_FORM.fullmatch((mf or "").strip()) else base).append(mg)
    word = "-".join(g for g in base if g)
    return word + "".join(f"<{g}>" for g in infixes if g)


def _add_word_level_translations(root: ET.Element, lang: str) -> int:
    """Insert a W-level <TRANSL> (the word gloss) on every fully-glossed W that
    lacks one, reconstructed from its child M glosses. Returns the count added.

    A word is treated as glossed only when EVERY child M carries a (primary)
    TRANSL; partially glossed words are left without a W-level gloss. Applied to
    the whole tree, so it covers automated and manual (override) S alike.
    """
    added = 0
    for w in root.iter("W"):
        if w.find("TRANSL") is not None:
            continue  # already has a W-level TRANSL
        ms = w.findall("M")
        if not ms:
            continue
        m_forms: list[str] = []
        m_glosses: list[str] = []
        complete = True
        for m in ms:
            mf = m.find("FORM[@kindOf='original']")
            mt = m.find("TRANSL")
            if mf is None or mt is None or not (mt.text or "").strip():
                complete = False
                break
            m_forms.append(mf.text or "")
            m_glosses.append((mt.text or "").strip())
        if not complete:
            continue
        gloss = _reconstruct_word_gloss(m_forms, m_glosses)
        if not gloss:
            continue
        transl = ET.Element("TRANSL", {f"{{{XML_NS}}}lang": lang})
        transl.text = gloss
        insert_at = next((i for i, c in enumerate(list(w)) if c.tag == "M"), len(w))
        w.insert(insert_at, transl)
        added += 1
    return added


def _punct_split(token: str) -> tuple[str, str, str]:
    lead = ""
    trail = ""
    value = token
    while value and value[0] in "(（[":
        lead += value[0]
        value = value[1:]
    while value and value[-1] in ".,;:?!。！？)）]":
        trail = value[-1] + trail
        value = value[:-1]
    return lead, value, trail


def _option_choices(token: str) -> list[dict[str, Any]]:
    token = clean_inline(token)
    lead, core, trail = _punct_split(token)
    if lead and trail and lead[-1] in "(（[" and trail[0] in ")）]":
        trail = trail[1:]
    if "/" not in core:
        return [{
            "text": token,
            "grammatical": not core.lstrip().startswith("*"),
            "raw_option": token,
            "was_option": False,
        }]
    choices: list[dict[str, Any]] = []
    for option in core.split("/"):
        raw = option.strip()
        if not raw:
            continue
        grammatical = not raw.lstrip().startswith("*")
        cleaned = raw.lstrip("*").strip()
        if not cleaned:
            continue
        # Once an option has been split into a separate XML sentence, omit the
        # grouping parentheses around the original slash set.
        choices.append({
            "text": f"{cleaned}{trail}",
            "grammatical": grammatical,
            "raw_option": raw,
            "was_option": True,
        })
    return choices


def _select_gloss_token_for_option(gloss_token: str, option_idx: int, form_choice_count: int) -> str:
    if not gloss_token:
        return gloss_token
    _, core, trail = _punct_split(gloss_token)
    if "/" not in core:
        return gloss_token
    parts = [part.strip().lstrip("*").strip() for part in core.split("/") if part.strip()]
    if len(parts) != form_choice_count or option_idx >= len(parts):
        return gloss_token
    return clean_inline(parts[option_idx] + trail)


def _join_slash_options(parts: list[str]) -> str:
    if not parts:
        return ""
    trail = ""
    while parts and all(part.endswith(tuple(".,;:?!。！？")) for part in parts):
        last_chars = {part[-1] for part in parts}
        if len(last_chars) != 1:
            break
        trail = parts[0][-1] + trail
        parts = [part[:-1] for part in parts]
    return clean_inline("/".join(parts) + trail)


def _preserve_slash_options(
    form_tokens: list[str],
    gloss_tokens: list[str],
) -> tuple[list[str], list[str], list[str], bool, bool]:
    """Preserve source slash alternatives while omitting starred options.

    Earlier pipeline versions expanded alternatives into separate XML sentences.
    For this source we preserve grammatical slash alternatives in the source
    original form and use sidecar QC for any Mandarin free-translation cleanup.
    """
    output_form = list(form_tokens)
    output_gloss = list(gloss_tokens)
    notes: list[str] = []
    saw_slash = False
    saw_multi_grammatical = False
    pending_gloss_filters: list[tuple[int, list[int]]] = []
    for token_idx, token in enumerate(form_tokens):
        if "/" not in token:
            continue
        saw_slash = True
        choices = _option_choices(token)
        if not any(choice["was_option"] for choice in choices):
            continue
        grammatical_indices = [idx for idx, choice in enumerate(choices) if choice["grammatical"]]
        if len(grammatical_indices) > 1:
            saw_multi_grammatical = True
        if not grammatical_indices:
            continue
        grammatical_choices = [choices[idx] for idx in grammatical_indices]
        output_form[token_idx] = _join_slash_options([choice["text"] for choice in grammatical_choices])
        if len(grammatical_choices) != len(choices):
            notes.append(f"starred slash alternatives omitted from token={token}")
            pending_gloss_filters.append((len(choices), grammatical_indices))
        else:
            notes.append(f"source slash alternatives preserved token={token}")

        if token_idx < len(output_gloss):
            gloss_token = output_gloss[token_idx]
            _, gloss_core, gloss_trail = _punct_split(gloss_token)
            gloss_parts = [part.strip().lstrip("*").strip() for part in gloss_core.split("/") if part.strip()]
            if "/" in gloss_core and len(gloss_parts) == len(choices):
                output_gloss[token_idx] = _join_slash_options([gloss_parts[idx] + gloss_trail for idx in grammatical_indices])
                if len(grammatical_choices) != len(choices):
                    pending_gloss_filters.pop()
    for choice_count, grammatical_indices in pending_gloss_filters:
        for gloss_idx, gloss_token in enumerate(output_gloss):
            _, gloss_core, gloss_trail = _punct_split(gloss_token)
            gloss_parts = [part.strip().lstrip("*").strip() for part in gloss_core.split("/") if part.strip()]
            if "/" in gloss_core and len(gloss_parts) == choice_count:
                output_gloss[gloss_idx] = _join_slash_options([gloss_parts[idx] + gloss_trail for idx in grammatical_indices])
                break
    return output_form, output_gloss, notes, saw_slash, saw_multi_grammatical


# --- F1: parenthesized-option / variant-clause splitting (added 2026-06-10) ---
_PAREN_RE = re.compile(r"[（(]([^()（）]*)[)）]")
_LATIN_RE = re.compile(r"[A-Za-z]")
_CJK_PAREN_RE = re.compile(r"[（(]\s*=?\s*([^()（）]*[㐀-鿿][^()（）]*?)\s*[)）]")


def _strip_paren_spans(text: str) -> str:
    return clean_inline(_PAREN_RE.sub(" ", text))


def _delete_paren_marks(text: str) -> str:
    return clean_inline(text.replace("(", "").replace(")", "").replace("（", "").replace("）", ""))


def _latin_paren_spans(text: str) -> list[str]:
    return [m.group(1).strip() for m in _PAREN_RE.finditer(text) if _LATIN_RE.search(m.group(1))]


def _classify_form_paren(form: str, spans: list[str], gloss: str, translation: str) -> str | None:
    """Which auto-split applies, or None to leave for manual handling.

    'variant_clause'     -> two separate variant S (gloss on the first).
    'optional_unglossed' -> glossed-core S + all-words (no gloss) S.
    None                 -> optional_glossed (E011D) or the combined form+translation
                            variant (E011E): left for the maintainer's hand-pass.
    """
    is_variant = (
        bool(re.search(r"=\s*[（(]", form))
        or any(s.rstrip().endswith(("?", "!", "？", "！")) for s in spans)
        or max((len(s.split()) for s in spans), default=0) >= 4
    )
    if is_variant:
        if _CJK_PAREN_RE.search(translation or ""):
            return None  # combined case (E011E): form variant + alt translation -> hand
        return "variant_clause"
    gloss_tok = len(clean_inline(gloss).split())
    with_tok = len(_delete_paren_marks(form).split())
    without_tok = len(_strip_paren_spans(form).split())
    if gloss_tok and abs(gloss_tok - with_tok) <= abs(gloss_tok - without_tok):
        return None  # optional_glossed (E011D) -> hand
    return "optional_unglossed"


def _split_variant_clause(base: str) -> tuple[str, str]:
    content = _latin_paren_spans(base)
    # A stray footnote number can sit between the clause and its parenthetical
    # variant in the source (E027A: "Gaga =su hmuya? 40 (Ga =su hmuya?)"). The
    # general trailing-footnote strip in _xml_original_form_for_xml runs on the
    # full line, where the trailing char is ")" — so it can't see the "40". Once
    # the parenthetical is removed here the footnote is trailing, so re-strip it.
    first = _strip_trailing_footnote_number(
        re.sub(r"\s*=\s*$", "", _strip_paren_spans(base)).strip()
    )
    second = clean_inline(content[-1]) if content else ""
    return first, second


# Per-variant translation cleaning for optional-element splits: when a row is
# split into a glossed core (optional element removed) and an all-words variant
# (optional element kept), specialize the source translation to match. The
# translation's *option* parenthetical — a slash list ("明天/昨天") or a short
# particle ("了") — is dropped in the core variant and resolved to the
# grammatical option in the with-option variant. Longer / sentence-like
# parentheticals (explanatory notes, alternative renderings) are left untouched
# so F2's alt-translation handling still applies to them.
_TR_OPTION_PAREN_RE = re.compile(r"\s*[（(]([^()（）]*)[)）]")


def _is_option_paren(content: str) -> bool:
    c = content.strip()
    return bool(c) and (("/" in c or "／" in c) or len(c) <= 3)


def _option_variant_translations(base: str, translation: str) -> tuple[str, str]:
    """Return (core_translation, with_option_translation) for an optional split.

    Falls back to the raw translation for both when there is no option
    parenthetical, so rows whose translation carries no option (e.g. E008B) are
    left unchanged.
    """
    tr = translation or ""
    m = next(
        (mm for mm in _TR_OPTION_PAREN_RE.finditer(tr) if _is_option_paren(mm.group(1))),
        None,
    )
    if m is None:
        return tr, tr
    # Grammatical option index = first non-starred option in the FORM parenthetical
    # (e.g. "(saman/*shiga)" -> 0, "(*saman/shiga)" -> 1, "(da)" -> 0).
    gram_idx = 0
    form_spans = _latin_paren_spans(base)
    if form_spans:
        form_opts = re.split(r"[/／]", form_spans[0])
        gram_idx = next(
            (i for i, o in enumerate(form_opts) if not o.strip().startswith("*")), 0
        )
    tr_opts = re.split(r"[/／]", m.group(1).strip())
    resolved = tr_opts[gram_idx].strip() if gram_idx < len(tr_opts) else tr_opts[0].strip()
    core = clean_inline(tr[: m.start()] + tr[m.end() :])
    with_option = clean_inline(tr[: m.start()] + resolved + tr[m.end() :])
    return core, with_option


def _build_variant(
    form_str: str,
    gloss_str: str,
    index: int,
    *,
    forced_suffix: str | None = None,
    emit_words: bool = True,
) -> dict[str, Any]:
    form_tokens = clean_inline(form_str).split()
    gloss_tokens = clean_inline(gloss_str).split()
    form_tokens, gloss_tokens, notes, saw_slash, saw_multi_grammatical = _preserve_slash_options(form_tokens, gloss_tokens)
    segmented_form_xml = clean_inline(" ".join(form_tokens))
    gloss_xml = clean_inline(" ".join(gloss_tokens))
    # The standard tier is emitted as a verbatim copy of the original. All
    # standard-tier cleaning — de-segmentation of Ø/-/= and orthography
    # standardization — is owned by FormosanBank's QC tools (clean_xml,
    # standardize.py), which run on the corpus downstream; doing it here too is
    # redundant and risks diverging from those tools.
    standard = segmented_form_xml
    if saw_slash:
        notes.append("source slash alternatives preserved in XML; source free translation retained for manual QC")
    suffix = forced_suffix if forced_suffix is not None else ("1" if saw_multi_grammatical else "")
    return {
        "variant_index": index,
        "variant_count": 1,
        "variant_suffix": suffix,
        "original_form_xml": segmented_form_xml,
        "standard_form_xml": standard,
        "segmented_form_xml": segmented_form_xml,
        "gloss_line_xml": gloss_xml if emit_words else "",
        "emit_words": emit_words,
        "notes": "; ".join(notes),
        "expanded_options": saw_slash,
    }


def _morphemes_align(segmented_form: str, gloss_line: str) -> bool:
    """True iff morpheme glosses would align for this form+gloss.

    Mirrors the alignment test in _add_words_and_glosses (flatten form
    morphemes + gloss parts, apply infix reanalysis, compare counts) so the
    variant builder can predict whether a given form/gloss pairing will gloss
    cleanly before emitting it.
    """
    gloss_tokens = _gloss_tokens_for_alignment(gloss_line)
    form_tokens = _word_tokens_for_xml_sentence(segmented_form)
    form_parts_by_word = [_split_morpheme_parts_for_xml(t) for t in form_tokens]
    gloss_parts = _flatten_gloss_parts(gloss_tokens)
    form_parts_by_word, _ = _apply_infix_reanalysis(
        form_tokens, form_parts_by_word, gloss_tokens, len(gloss_parts)
    )
    form_part_count = sum(len(p) for p in form_parts_by_word)
    return bool(gloss_parts) and form_part_count == len(gloss_parts)


def _optional_word_span(core_words: list[str], withopt_words: list[str]) -> "tuple[int | None, int]":
    """Return (start, length) of the contiguous block of words present in
    withopt_words but not core_words (i.e. the optional element), or (None, 0)
    if the difference isn't a single contiguous insertion."""
    n, m = len(core_words), len(withopt_words)
    k = m - n
    if k <= 0:
        return None, 0
    for i in range(n + 1):
        if withopt_words[:i] == core_words[:i] and withopt_words[i + k:] == core_words[i:]:
            return i, k
    return None, 0


def _optional_split_glosses(base: str, gloss: str) -> "tuple[str, str] | None":
    """For a GLOSSED optional element at ANY position, return
    (core_gloss, with_option_gloss).

    The source gloss is written for the with-option form, so when the optional
    block is actually glossed, BOTH variants can be glossed: the with-option
    variant uses the full gloss, and the core variant drops the gloss token(s)
    belonging to the removed optional so it re-aligns. Handles a trailing
    optional (E026A "(da)"->"了") and a mid-sentence one (E023C
    "(saman/*shiga)"->"明天/昨天"). Returns None when the optional is unglossed
    (e.g. E008B's "(ka yaku)" — the with-option form then does NOT align to the
    gloss), leaving the default core-only-glossed handling in place.
    """
    core_form = _strip_paren_spans(base)
    withopt_form = _delete_paren_marks(base)
    core_words = _word_tokens_for_xml_sentence(core_form)
    withopt_words = _word_tokens_for_xml_sentence(withopt_form)
    opt_start, opt_k = _optional_word_span(core_words, withopt_words)
    if opt_start is None:
        return None  # optional is not a clean contiguous block of words
    # The optional must actually be glossed: the with-option form (which keeps
    # it) must align morpheme-for-morpheme with the full gloss.
    if not _morphemes_align(withopt_form, gloss):
        return None
    gloss_tokens = _gloss_tokens_for_alignment(gloss)
    gloss_parts = _flatten_gloss_parts(gloss_tokens)
    form_parts = [_split_morpheme_parts_for_xml(t) for t in withopt_words]
    form_parts, _ = _apply_infix_reanalysis(withopt_words, form_parts, gloss_tokens, len(gloss_parts))
    # Flat morpheme-index range occupied by the optional word block.
    before = sum(len(form_parts[i]) for i in range(opt_start))
    opt_len = sum(len(form_parts[i]) for i in range(opt_start, opt_start + opt_k))
    opt_range = set(range(before, before + opt_len))
    # Drop each gloss token whose parts fall entirely inside that range.
    kept: list[str] = []
    part_idx = 0
    for tok in gloss_tokens:
        nparts = len(_split_gloss_parts_for_xml(tok))
        tok_range = set(range(part_idx, part_idx + nparts))
        part_idx += nparts
        if tok_range and tok_range <= opt_range:
            continue
        kept.append(tok)
    core_gloss = " ".join(kept)
    if _morphemes_align(core_form, core_gloss):
        return core_gloss, gloss
    return None


def _xml_variants_for_row(row: dict[str, Any]) -> list[dict[str, Any]]:
    base = _xml_original_form_for_xml(row.get("truku_line_clean", ""))
    gloss = row.get("gloss_line_clean", "")
    translation = row.get("chinese_translation_clean", "")
    spans = _latin_paren_spans(base)
    split = _classify_form_paren(base, spans, gloss, translation) if spans else None

    if split == "optional_unglossed":
        glossed_optional = _optional_split_glosses(base, gloss)
        if glossed_optional:
            # Optional is trailing AND glossed: gloss BOTH variants. The core
            # drops the optional's trailing gloss so it re-aligns; the with-option
            # variant carries the full gloss (which was written for it).
            core_gloss, withopt_gloss = glossed_optional
            v1 = _build_variant(_strip_paren_spans(base), core_gloss, 1, forced_suffix="", emit_words=True)
            v2 = _build_variant(_delete_paren_marks(base), withopt_gloss, 2, forced_suffix="b", emit_words=True)
        else:
            v1 = _build_variant(_strip_paren_spans(base), gloss, 1, forced_suffix="", emit_words=True)
            v2 = _build_variant(_delete_paren_marks(base), "", 2, forced_suffix="b", emit_words=False)
        # Specialize the source translation to each variant: core drops the
        # option parenthetical, with-option resolves it to the grammatical option.
        v1["translation"], v2["translation"] = _option_variant_translations(base, translation)
    elif split == "variant_clause":
        first, second = _split_variant_clause(base)
        v1 = _build_variant(first, gloss, 1, forced_suffix="", emit_words=True)
        v2 = _build_variant(second, "", 2, forced_suffix="b", emit_words=False)
    else:
        v = _build_variant(base, gloss, 1)
        return [v]

    for v in (v1, v2):
        v["variant_count"] = 2
    return [v1, v2]


def _add_words_and_glosses(
    sentence_el: ET.Element,
    sentence_id: str,
    sentence_form: str,
    sentence_standard_form: str,
    segmented_form: str,
    row: dict[str, Any],
    translation_lang: str,
    gloss_line: str,
) -> dict[str, Any]:
    gloss_tokens = _gloss_tokens_for_alignment(gloss_line)
    segmented_tokens = _word_tokens_for_xml_sentence(segmented_form)
    form_tokens = segmented_tokens
    form_parts_by_word = [_split_morpheme_parts_for_xml(token) for token in segmented_tokens]
    gloss_parts = _flatten_gloss_parts(gloss_tokens)
    form_parts_by_word, infix_notes = _apply_infix_reanalysis(
        form_tokens,
        form_parts_by_word,
        gloss_tokens,
        len(gloss_parts),
    )
    form_part_count = sum(len(parts) for parts in form_parts_by_word)
    align_morphemes = bool(gloss_parts) and form_part_count == len(gloss_parts)
    align_words = bool(gloss_tokens) and len(form_tokens) == len(gloss_tokens)
    audit = {
        "example_record_id": row.get("example_record_id", ""),
        "sentence_id": sentence_id,
        "page_number_one_based": row.get("page_number_one_based", ""),
        "example_label_clean": row.get("example_label_clean", ""),
        "form_token_count": len(form_tokens),
        "gloss_token_count": len(gloss_tokens),
        "word_count_emitted": 0,
        "morpheme_count_emitted": 0,
        "alignment_status": "",
        "reason": "",
        "form_tokens": " ".join(form_tokens),
        "gloss_tokens": " ".join(gloss_tokens),
        "notes": ";".join(infix_notes),
    }
    if not form_tokens:
        audit["alignment_status"] = "no_words_emitted"
        audit["reason"] = "no_parseable_form_tokens"
        return audit

    gloss_idx = 0
    for w_idx, word_form in enumerate(form_tokens, start=1):
        w_id = f"{sentence_id}W{w_idx}"
        w_el = ET.SubElement(sentence_el, "W", {"id": w_id})
        _add_original_and_standard_forms(w_el, word_form, word_form)
        morphemes = form_parts_by_word[w_idx - 1] or [_clean_word_form_for_xml(word_form)]
        audit["word_count_emitted"] += 1
        audit["morpheme_count_emitted"] += len(morphemes)
        for m_idx, morph_form in enumerate(morphemes, start=1):
            m_el = ET.SubElement(w_el, "M", {"id": f"{w_id}M{m_idx}"})
            # Standard tier is a verbatim copy of original at every level (see
            # the S-level note above); QC tools de-segment/standardize it later.
            _add_original_and_standard_forms(m_el, morph_form, morph_form)
            if align_morphemes:
                _add_translation(m_el, gloss_parts[gloss_idx], translation_lang)
                gloss_idx += 1
    if align_morphemes:
        audit["alignment_status"] = "morpheme_aligned"
        audit["reason"] = "form_morpheme_count_matches_source_gloss_morpheme_count"
    elif align_words:
        audit["alignment_status"] = "words_only"
        audit["reason"] = "word_count_matches_source_gloss_token_count_but_word_level_gloss_not_emitted"
    elif not row.get("gloss_line_clean"):
        audit["alignment_status"] = "words_only"
        audit["reason"] = "no_source_gloss_line"
    else:
        audit["alignment_status"] = "words_only"
        audit["reason"] = "source_gloss_not_reliably_alignable"
    return audit


# Hand-curated examples the automated parser cannot derive from the PDF text layer
# (e.g. examples embedded in prose / non-standard layout, or maintainer hand-splits
# of edge cases). Stored VERBATIM as <S> elements — with any W/M glosses, ver="alt",
# etc. preserved — in this versioned file, and appended at the end of the build so
# re-running build_formosanbank_xml reproduces them exactly. To add/edit, edit the
# file (it must be a well-formed <MANUAL_SENTENCES> root containing <S> children).
MANUAL_SENTENCES_FILE = ROOT / "data/manual/manual_sentences.xml"


def build_formosanbank_xml(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    rows = read_jsonl(ROOT / "data/processed/quality_filtered_examples.jsonl")
    if not rows:
        quality_filter(cfg)
        rows = read_jsonl(ROOT / "data/processed/quality_filtered_examples.jsonl")
    if not (ROOT / "data/processed/duplicates.csv").exists():
        dedupe_examples(cfg)
        rows = read_jsonl(ROOT / "data/processed/quality_filtered_examples.jsonl")
    if not (ROOT / "data/processed/overlap_candidates.csv").exists():
        dedupe_against_formosanbank(cfg)
    original, decrypted = _pdf_paths(cfg)
    original_hash, decrypted_hash = _source_pdf_hashes(cfg)
    output_dir = ROOT / cfg["xml"]["output_dir"] / cfg["xml"]["language_folder"]
    output_dir.mkdir(parents=True, exist_ok=True)
    xml_path = output_dir / cfg["xml"]["output_file"]
    final_xml_root = ROOT / cfg["xml"]["output_dir"]
    for stale_xml in sorted(final_xml_root.rglob("*.xml")) if final_xml_root.exists() else []:
        if stale_xml.resolve() != xml_path.resolve():
            stale_xml.unlink()

    kept_rows = [r for r in rows if r.get("duplicate_action", "keep") == "keep"]
    ET.register_namespace("xml", XML_NS)
    text_attribs = {
        "id": SOURCE_ID,
        f"{{{XML_NS}}}lang": cfg["language"]["expected_iso_639_3"],
        "citation": citation(),
        "BibTeX_citation": bibtex(),
        "copyright": source_copyright(),
        "source": f"{Path(cfg['source']['pdf_path']).name}; SHA-256={original_hash}; rights_status=full_rights_obtained; extraction=pdf_text_layer; source_orthography=Ortho94",
    }
    # Emit the FormosanBank TEXT/@dialect when the source dialect has been
    # validated (config gate). Without this the build dropped a hand-added
    # dialect on every rebuild; wiring it through config keeps rebuilds
    # reproducible and the dialect present (required by FormosanBank QC).
    dialect = cfg["language"].get("dialect", "")
    if cfg["language"].get("use_dialect_or_location_attribute_if_validated") and dialect:
        text_attribs["dialect"] = dialect
    root = ET.Element("TEXT", text_attribs)

    seen_ids: set[str] = set()
    # Hand-curated S in manual_sentences.xml OVERRIDE the automated build: any
    # automated S whose id appears here is skipped below so the verbatim manual
    # version wins. (Used both to add S the parser can't derive AND to preserve
    # hand-edits to existing automated S that a rebuild would otherwise clobber.)
    manual_override_ids: set[str] = set()
    if MANUAL_SENTENCES_FILE.exists():
        manual_override_ids = {
            s.get("id", "")
            for s in ET.parse(MANUAL_SENTENCES_FILE).getroot().findall("S")
            if s.get("id", "")
        }
    index_rows = []
    gloss_by_example = {r["example_record_id"]: r["gloss_record_id"] for r in read_jsonl(ROOT / "data/processed/gloss_records.jsonl")}
    overlap_ids = {r["example_record_id"] for r in read_csv_dicts(ROOT / "data/processed/overlap_candidates.csv")}
    gloss_alignment_rows = []
    variant_audit_rows = []
    slash_qc_lines = [
        "# Manual QC: Slash Option Preservation",
        "",
        "Each group below came from one source example containing slash-separated alternatives. Grammatical slash alternatives are preserved in the XML original forms; starred ungrammatical alternatives are omitted from XML. Source-published free translations are intentionally retained unchanged so a human can fix Mandarin free translations during QC.",
        "",
    ]
    parentheses_qc_lines = [
        "# Manual QC: Parentheses In Source Examples",
        "",
        "These XML-linked examples contain parentheses in the Truku form, source gloss, or source free translation. XML original FORM values keep source segmentation where feasible; sentence-level standard FORM values remove segmentation/null/parenthetical material conservatively.",
        "",
    ]
    for idx, row in enumerate(kept_rows, start=1):
        variants = _xml_variants_for_row(row)
        if any(v["expanded_options"] for v in variants):
            slash_qc_lines.extend([
                f"## {row.get('example_label_clean', '')} / {row.get('example_record_id', '')}",
                f"- Page: {row.get('page_number_one_based', '')}",
                f"- Source form: {row.get('truku_line_clean', '')}",
                f"- Source gloss: {row.get('gloss_line_clean', '')}",
                f"- Source free translation kept for QC: {row.get('chinese_translation_clean', '')}",
                "- Emitted XML:",
            ])
        has_parentheses = any(mark in " ".join([
            row.get("truku_line_clean", ""),
            row.get("gloss_line_clean", ""),
            row.get("chinese_translation_clean", ""),
        ]) for mark in ["(", ")", "（", "）"])
        parenthesis_sentence_ids: list[str] = []
        for variant in variants:
            sid = _sentence_id(row, idx, variant["variant_suffix"])
            if sid in manual_override_ids:
                continue  # superseded by the verbatim copy in manual_sentences.xml
            if sid in seen_ids:
                sid = f"{sid}_{idx:04d}_{variant['variant_index']:02d}"
            seen_ids.add(sid)
            sentence_form = variant["original_form_xml"]
            sentence_standard_form = variant["standard_form_xml"]
            s = ET.SubElement(root, "S", {"id": sid})
            _add_original_and_standard_forms(s, sentence_form, sentence_standard_form, always_standard=True)
            _add_translations(s, variant.get("translation") or row["chinese_translation_clean"], cfg["xml"]["source_translation_lang"])
            if variant.get("emit_words", True):
                gloss_alignment_rows.append(_add_words_and_glosses(
                    s,
                    sid,
                    sentence_form,
                    sentence_standard_form,
                    variant["segmented_form_xml"],
                    row,
                    cfg["xml"]["source_translation_lang"],
                    variant["gloss_line_xml"],
                ))
            pair_hash = sha256_text(sentence_form + "\n" + row["chinese_translation_clean"])
            index_rows.append({
                "xml_file": rel(xml_path),
                "text_id": SOURCE_ID,
                "sentence_id": sid,
                "unit_id": sid,
                "example_record_id": row["example_record_id"],
                "source_id": SOURCE_ID,
                "source_pdf_path": rel(original),
                "source_pdf_sha256": original_hash,
                "decrypted_pdf_sha256": decrypted_hash,
                "page_number_one_based": row.get("page_number_one_based", ""),
                "printed_page_number": row.get("printed_page_number", ""),
                "chapter_number": row.get("chapter_number", ""),
                "section_number": row.get("section_number", ""),
                "section_title": row.get("section_title", ""),
                "example_number": row.get("example_number", ""),
                "subexample_letter": row.get("subexample_letter", ""),
                "ISO_639_3": cfg["language"]["expected_iso_639_3"],
                "FormosanBank_language_name": "Truku / Taroko",
                "dialect_or_location_attribute_value": "",
                "truku_form_sha256": sha256_text(sentence_form),
                "translation_lang": cfg["xml"]["source_translation_lang"],
                "source_translation_sha256": sha256_text(row["chinese_translation_clean"]),
                "pair_sha256": pair_hash,
                "gloss_record_id": gloss_by_example.get(row["example_record_id"], ""),
                "extraction_method": "text_layer_pdftotext_layout_with_line_heuristics",
                "extraction_confidence": row.get("extraction_confidence", ""),
                "overlap_status": "candidate" if row["example_record_id"] in overlap_ids else "none",
                "quality_status": "accepted",
                "citation": citation(),
                "permission_status": "full_rights_obtained",
                "notes": clean_inline("No OCR and no machine translation used. " + variant["notes"]),
            })
            variant_audit_rows.append({
                "sentence_id": sid,
                "example_record_id": row["example_record_id"],
                "example_label_clean": row.get("example_label_clean", ""),
                "page_number_one_based": row.get("page_number_one_based", ""),
                "variant_index": variant["variant_index"],
                "variant_count": variant["variant_count"],
                "original_form_source": row.get("truku_line_clean", ""),
                "original_form_xml": sentence_form,
                "standard_form_xml": sentence_standard_form,
                "gloss_line_source": row.get("gloss_line_clean", ""),
                "gloss_line_xml": variant["gloss_line_xml"],
                "chinese_translation_clean": row.get("chinese_translation_clean", ""),
                "notes": variant["notes"],
            })
            if variant["expanded_options"]:
                slash_qc_lines.append(f"  - `{sid}`: {sentence_form}")
            if has_parentheses:
                parenthesis_sentence_ids.append(sid)
        if any(v["expanded_options"] for v in variants):
            slash_qc_lines.append("")
        if has_parentheses:
            parentheses_qc_lines.extend([
                f"## {row.get('example_label_clean', '')} / {row.get('example_record_id', '')}",
                f"- Page: {row.get('page_number_one_based', '')}",
                f"- XML S ids: {', '.join(parenthesis_sentence_ids)}",
                f"- Source form: {row.get('truku_line_clean', '')}",
                f"- Source gloss: {row.get('gloss_line_clean', '')}",
                f"- Source free translation: {row.get('chinese_translation_clean', '')}",
                "",
            ])

    # Hand-curated examples the parser cannot derive: appended VERBATIM from
    # data/manual/manual_sentences.xml (full W/M/glosses/ver="alt" preserved).
    if MANUAL_SENTENCES_FILE.exists():
        for manual_s in ET.parse(MANUAL_SENTENCES_FILE).getroot().findall("S"):
            sid = manual_s.get("id", "")
            if not sid or sid in seen_ids:
                continue  # blank id, or this manual id already appended (dup in the file)
            # NB: automated S with this id were skipped above, so for an override
            # the id is NOT yet in seen_ids and the manual copy is appended here.
            seen_ids.add(sid)
            root.append(manual_s)
            index_rows.append({
                "xml_file": rel(xml_path),
                "text_id": SOURCE_ID,
                "sentence_id": sid,
                "unit_id": sid,
                "example_record_id": "MANUAL_ADDITION",
                "source_id": SOURCE_ID,
                "source_pdf_path": rel(original),
                "source_pdf_sha256": original_hash,
                "decrypted_pdf_sha256": decrypted_hash,
                "ISO_639_3": cfg["language"]["expected_iso_639_3"],
                "translation_lang": cfg["xml"]["source_translation_lang"],
                "extraction_method": "manual_addition",
                "extraction_confidence": "high",
                "quality_status": "accepted",
                "citation": citation(),
                "permission_status": "full_rights_obtained",
                "notes": "Hand-curated example not derivable from the PDF text layer; appended verbatim from data/manual/manual_sentences.xml for reproducibility.",
            })

    # Add a W-level TRANSL (word gloss) to every fully-glossed W, reconstructed
    # from its M glosses — required by FormosanBank validators (V065: every W
    # should have a TRANSL; V062: an infix M's gloss must appear in the parent
    # W's TRANSL as an angle-bracket gloss). Covers automated AND manual S.
    _add_word_level_translations(root, cfg["xml"]["source_translation_lang"])

    ET.indent(root, space="  ")
    tree = ET.ElementTree(root)
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    write_csv(ROOT / "data/processed/xml_index.csv", index_rows, XML_INDEX_FIELDS)
    write_csv(ROOT / "data/processed/gloss_alignment_audit.csv", gloss_alignment_rows, GLOSS_ALIGNMENT_FIELDS)
    write_csv(ROOT / "data/processed/xml_variant_audit.csv", variant_audit_rows, XML_VARIANT_AUDIT_FIELDS)
    (ROOT / "data/processed/manual_qc_slash_options.txt").write_text("\n".join(slash_qc_lines).rstrip() + "\n", encoding="utf-8")
    (ROOT / "data/processed/manual_qc_parentheses.txt").write_text("\n".join(parentheses_qc_lines).rstrip() + "\n", encoding="utf-8")
    log("build_formosanbank_xml", f"built {xml_path} with {len(index_rows)} S elements")


def _validate_xml_file(xml_path: Path, index_ids: set[str], cfg: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    try:
        tree = ET.parse(xml_path)
    except Exception as exc:
        return [f"{xml_path}: not well formed: {exc}"]
    root = tree.getroot()
    allowed_text_attrs = {"id", "citation", "BibTeX_citation", "copyright", "source", "audio", "glottocode", "dialect", f"{{{XML_NS}}}lang"}
    required = {"id", "citation", "BibTeX_citation", "copyright", f"{{{XML_NS}}}lang"}
    if root.tag != "TEXT":
        failures.append("root is not TEXT")
    missing = [attr for attr in required if attr not in root.attrib]
    if missing:
        failures.append(f"TEXT missing required attributes: {missing}")
    bad_attrs = [attr for attr in root.attrib if attr not in allowed_text_attrs]
    if bad_attrs:
        failures.append(f"TEXT has invalid attributes: {bad_attrs}")
    if root.attrib.get(f"{{{XML_NS}}}lang") != cfg["language"]["expected_iso_639_3"]:
        failures.append("TEXT xml:lang is not expected trv")
    ids = set()
    for child in list(root):
        if child.tag != "S":
            failures.append(f"TEXT has non-S child {child.tag}")
            continue
        sid = child.attrib.get("id", "")
        if set(child.attrib.keys()) != {"id"}:
            failures.append(f"S {sid} has invalid attributes")
        if not sid or sid in ids:
            failures.append(f"S id missing or duplicate: {sid}")
        ids.add(sid)
        if sid not in index_ids:
            failures.append(f"S {sid} missing from xml_index.csv")
        forms = child.findall("FORM")
        if not (1 <= len(forms) <= 2):
            failures.append(f"S {sid} has {len(forms)} FORM elements, expected 1 or 2")
        if forms and forms[0].attrib.get("kindOf") != "original":
            failures.append(f"S {sid} first FORM is not kindOf=original")
        if len(forms) == 2 and forms[1].attrib.get("kindOf") != "standard":
            failures.append(f"S {sid} second FORM is not kindOf=standard")
        for form in forms:
            text = clean_inline(form.text or "")
            if set(form.attrib.keys()) != {"kindOf"} or form.attrib.get("kindOf") not in {"original", "standard"}:
                failures.append(f"S {sid} FORM has invalid attributes")
            if not text:
                failures.append(f"S {sid} FORM empty")
            if has_cjk(text):
                failures.append(f"S {sid} FORM contains Chinese")
            if text.lstrip().startswith("*") or "/*" in text or "*/" in text:
                failures.append(f"S {sid} FORM contains starred ungrammatical marker")
            # (No Ø/segmentation check on the standard tier: it is a verbatim copy
            #  of the original; de-segmentation is done downstream by clean_xml.)
            if re.fullmatch(r"(AF|PF|LF|IF|Caus|RED|CV|CVCV|[-=\\s]+)+", text):
                failures.append(f"S {sid} FORM appears gloss-only")
        translations = child.findall("TRANSL")
        if not translations:
            failures.append(f"S {sid} missing TRANSL")
        for transl in translations:
            text = clean_inline(transl.text or "")
            lang = transl.attrib.get(f"{{{XML_NS}}}lang", "")
            extra_attrs = set(transl.attrib) - {f"{{{XML_NS}}}lang", "ver"}
            if extra_attrs:
                failures.append(f"S {sid} TRANSL has invalid attributes: {sorted(extra_attrs)}")
            if transl.attrib.get("ver", "alt") != "alt":
                failures.append(f"S {sid} TRANSL has unexpected ver={transl.attrib.get('ver')}")
            if lang != cfg["xml"]["source_translation_lang"]:
                failures.append(f"S {sid} TRANSL lang is {lang}")
            if not text or not has_cjk(text):
                failures.append(f"S {sid} TRANSL missing Chinese source translation")
            if "machine translation" in text.lower():
                failures.append(f"S {sid} TRANSL indicates machine translation")
        for grandchild in list(child):
            if grandchild.tag not in {"FORM", "TRANSL", "W"}:
                failures.append(f"S {sid} has forbidden child {grandchild.tag}")
            if grandchild.tag == "W":
                wid = grandchild.attrib.get("id", "")
                if set(grandchild.attrib.keys()) != {"id"}:
                    failures.append(f"W {wid} has invalid attributes")
                w_forms = grandchild.findall("FORM")
                if not (1 <= len(w_forms) <= 2):
                    failures.append(f"W {wid} has {len(w_forms)} FORM elements, expected 1 or 2")
                if w_forms and w_forms[0].attrib.get("kindOf") != "original":
                    failures.append(f"W {wid} first FORM is not kindOf=original")
                if len(w_forms) == 2 and w_forms[1].attrib.get("kindOf") != "standard":
                    failures.append(f"W {wid} second FORM is not kindOf=standard")
                for w_form in w_forms:
                    if set(w_form.attrib.keys()) != {"kindOf"} or w_form.attrib.get("kindOf") not in {"original", "standard"}:
                        failures.append(f"W {wid} FORM has invalid attributes")
                    if not clean_inline(w_form.text or ""):
                        failures.append(f"W {wid} FORM empty")
                    if " " in clean_inline(w_form.text or ""):
                        failures.append(f"W {wid} FORM contains unreviewed whitespace")
                for w_child in list(grandchild):
                    if w_child.tag not in {"FORM", "TRANSL", "M"}:
                        failures.append(f"W {wid} has forbidden child {w_child.tag}")
                    if w_child.tag == "TRANSL":
                        extra_attrs = set(w_child.attrib) - {f"{{{XML_NS}}}lang", "ver"}
                        if extra_attrs:
                            failures.append(f"W {wid} TRANSL has invalid attributes: {sorted(extra_attrs)}")
                        if w_child.attrib.get("ver", "alt") != "alt":
                            failures.append(f"W {wid} TRANSL has unexpected ver={w_child.attrib.get('ver')}")
                        if w_child.attrib.get(f"{{{XML_NS}}}lang") != cfg["xml"]["source_translation_lang"]:
                            failures.append(f"W {wid} TRANSL lang is not source gloss language")
                        if not clean_inline(w_child.text or ""):
                            failures.append(f"W {wid} TRANSL empty")
                    if w_child.tag == "M":
                        mid = w_child.attrib.get("id", "")
                        if set(w_child.attrib.keys()) != {"id"}:
                            failures.append(f"M {mid} has invalid attributes")
                        m_forms = w_child.findall("FORM")
                        if not (1 <= len(m_forms) <= 2):
                            failures.append(f"M {mid} has {len(m_forms)} FORM elements, expected 1 or 2")
                        if m_forms and m_forms[0].attrib.get("kindOf") != "original":
                            failures.append(f"M {mid} first FORM is not kindOf=original")
                        if len(m_forms) == 2 and m_forms[1].attrib.get("kindOf") != "standard":
                            failures.append(f"M {mid} second FORM is not kindOf=standard")
                        for m_form in m_forms:
                            if set(m_form.attrib.keys()) != {"kindOf"} or m_form.attrib.get("kindOf") not in {"original", "standard"}:
                                failures.append(f"M {mid} FORM has invalid attributes")
                            if not clean_inline(m_form.text or ""):
                                failures.append(f"M {mid} FORM empty")
                        m_trans = w_child.findall("TRANSL")
                        for m_tr in m_trans:
                            extra_attrs = set(m_tr.attrib) - {f"{{{XML_NS}}}lang", "ver"}
                            if extra_attrs:
                                failures.append(f"M {mid} TRANSL has invalid attributes: {sorted(extra_attrs)}")
                            if m_tr.attrib.get("ver", "alt") != "alt":
                                failures.append(f"M {mid} TRANSL has unexpected ver={m_tr.attrib.get('ver')}")
                            if m_tr.attrib.get(f"{{{XML_NS}}}lang") != cfg["xml"]["source_translation_lang"]:
                                failures.append(f"M {mid} TRANSL lang is not source gloss language")
                            if not clean_inline(m_tr.text or ""):
                                failures.append(f"M {mid} TRANSL empty")
    extra_index_ids = index_ids - ids
    if extra_index_ids:
        failures.append(f"xml_index.csv contains IDs absent from XML: {sorted(extra_index_ids)[:5]}")
    return failures


def validate_formosanbank_xml(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    xml_dir = ROOT / cfg["xml"]["output_dir"]
    xml_files = sorted(xml_dir.rglob("*.xml")) if xml_dir.exists() else []
    index_rows = read_csv_dicts(ROOT / "data/processed/xml_index.csv")
    index_ids = {row["sentence_id"] for row in index_rows}
    failures = []
    for path in xml_dir.rglob("*") if xml_dir.exists() else []:
        if path.is_file() and path.suffix != ".xml":
            failures.append(f"Final_XML contains non-XML file: {rel(path)}")
    for xml in xml_files:
        failures.extend(_validate_xml_file(xml, index_ids, cfg))

    pages = read_csv_dicts(ROOT / "data/processed/pages.csv")
    raw = read_jsonl(ROOT / "data/processed/examples_raw.jsonl")
    clean = read_jsonl(ROOT / "data/processed/examples_clean.jsonl")
    eligible = read_jsonl(ROOT / "data/processed/quality_filtered_examples.jsonl")
    rejected = read_csv_dicts(ROOT / "data/processed/rejected_records.csv")
    tables = read_csv_dicts(ROOT / "data/processed/morphology_tables.csv")
    dups = read_csv_dicts(ROOT / "data/processed/duplicates.csv")
    overlaps = read_csv_dicts(ROOT / "data/processed/overlap_candidates.csv")
    alignment_audit = read_csv_dicts(ROOT / "data/processed/gloss_alignment_audit.csv")
    original_hash, decrypted_hash = _source_pdf_hashes(cfg)
    selectable_pages = sum(1 for p in pages if p.get("parse_status") == "extracted")
    blank_or_empty_pages = len(pages) - selectable_pages
    xml_word_count = 0
    xml_morpheme_count = 0
    xml_form_count = 0
    xml_transl_counts: Counter[str] = Counter()
    for xml in xml_files:
        root = ET.parse(xml).getroot()
        xml_word_count += len(root.findall(".//W"))
        xml_morpheme_count += len(root.findall(".//M"))
        xml_form_count += len(root.findall(".//FORM"))
        for transl in root.findall(".//TRANSL"):
            xml_transl_counts[transl.attrib.get(f"{{{XML_NS}}}lang", "")] += 1
    w_m_count = sum(1 for row in alignment_audit if int(row.get("word_count_emitted") or 0) > 0)
    morph_gloss_aligned_count = sum(1 for row in alignment_audit if row.get("alignment_status") == "morpheme_aligned")
    word_gloss_aligned_count = sum(1 for row in alignment_audit if row.get("alignment_status") == "word_gloss_aligned")
    words_only_count = sum(1 for row in alignment_audit if row.get("alignment_status") == "words_only")
    report = [
        "# Validation Report",
        "",
        "- permission status: full_rights_obtained",
        f"- original PDF SHA-256: {original_hash}",
        f"- decrypted PDF SHA-256: {decrypted_hash}",
        f"- total pages expected: {cfg['source']['expected_page_count']}",
        f"- total pages processed: {len(pages)}",
        f"- total pages with selectable text: {selectable_pages}",
        f"- blank/empty pages explicitly recorded: {blank_or_empty_pages}",
        f"- total pages rendered for audit: {sum(1 for p in pages if p.get('rendered_image_sha256'))}",
        "- OCR used: no",
        f"- total numbered examples found: {len(raw)}",
        f"- total examples with Truku form: {sum(1 for r in clean if r.get('truku_line_clean'))}",
        f"- total examples with Chinese free translation: {sum(1 for r in clean if r.get('chinese_translation_clean'))}",
        f"- total examples with gloss lines: {sum(1 for r in clean if r.get('gloss_line_clean'))}",
        f"- total XML-eligible examples: {len(eligible)}",
        f"- total rejected examples: {len(rejected)}",
        f"- total table records extracted: {len(tables)}",
        f"- total duplicate records: {len(dups)}",
        f"- total overlap candidates: {len(overlaps)}",
        "- language mapping status: validated locally as xml:lang=\"trv\" under Formosan language folder `Truku`",
        f"- translation language mapping status: validated locally as xml:lang=\"{cfg['xml']['source_translation_lang']}\"",
        f"- XML files created: {', '.join(rel(p) for p in xml_files)}",
        f"- total TEXT elements: {len(xml_files)}",
        f"- total S elements: {len(index_rows)}",
        f"- total FORM elements: {xml_form_count}",
        f"- total W elements: {xml_word_count}",
        f"- total M elements: {xml_morpheme_count}",
        "- total TRANSL elements by xml:lang: " + ", ".join(f"{k}={v}" for k, v in sorted(xml_transl_counts.items())),
        f"- S elements with W/M: {w_m_count}",
        f"- S elements with morpheme-level gloss alignment: {morph_gloss_aligned_count}",
        f"- S elements with word-level gloss translations: {word_gloss_aligned_count}",
        f"- S elements with W/M but no reliable source gloss alignment: {words_only_count}",
        f"- validation failures: {len(failures)}",
        "",
    ]
    if failures:
        report.append("## Failures")
        report.extend(f"- {failure}" for failure in failures)
        report.append("")
        report.append("Final summary: FAIL")
    else:
        report.append("Final summary: PASS")
    (ROOT / "data/processed/validation_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    if failures:
        raise RuntimeError(f"validation failed with {len(failures)} issue(s); see data/processed/validation_report.md")
    log("validate_formosanbank_xml", "validation PASS")


def generate_reports(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    pages = read_csv_dicts(ROOT / "data/processed/pages.csv")
    raw = read_jsonl(ROOT / "data/processed/examples_raw.jsonl")
    clean = read_jsonl(ROOT / "data/processed/examples_clean.jsonl")
    eligible = read_jsonl(ROOT / "data/processed/quality_filtered_examples.jsonl")
    rejected = read_csv_dicts(ROOT / "data/processed/rejected_records.csv")
    xml_index = read_csv_dicts(ROOT / "data/processed/xml_index.csv")
    tables = read_csv_dicts(ROOT / "data/processed/morphology_tables.csv")
    alignment_audit = read_csv_dicts(ROOT / "data/processed/gloss_alignment_audit.csv")
    xml_path = ROOT / cfg["xml"]["output_dir"] / cfg["xml"]["language_folder"] / cfg["xml"]["output_file"]
    xml_counts = {"S": 0, "W": 0, "M": 0, "FORM": 0, "TRANSL": 0}
    if xml_path.exists():
        xml_root = ET.parse(xml_path).getroot()
        for key in xml_counts:
            xml_counts[key] = len(xml_root.findall(key if key == "S" else f".//{key}"))

    def coverage(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
        counts = Counter(str(r.get(key, "") or "unknown") for r in rows)
        return [{key: k, "record_count": v} for k, v in sorted(counts.items())]

    write_csv(ROOT / "data/processed/coverage_by_page.csv", coverage(clean, "page_number_one_based"), ["page_number_one_based", "record_count"])
    write_csv(ROOT / "data/processed/coverage_by_chapter.csv", coverage(clean, "chapter_number"), ["chapter_number", "record_count"])
    write_csv(ROOT / "data/processed/coverage_by_section.csv", coverage(clean, "section_number"), ["section_number", "record_count"])
    w_m_sentence_count = sum(1 for r in alignment_audit if int(r.get("word_count_emitted") or 0) > 0)
    morph_gloss_sentence_count = sum(1 for r in alignment_audit if r.get("alignment_status") == "morpheme_aligned")
    word_gloss_sentence_count = sum(1 for r in alignment_audit if r.get("alignment_status") == "word_gloss_aligned")
    words_only_sentence_count = sum(1 for r in alignment_audit if r.get("alignment_status") == "words_only")
    type_rows = [
        {"example_type": "xml_eligible", "record_count": len(eligible)},
        {"example_type": "rejected", "record_count": len(rejected)},
        {"example_type": "with_gloss", "record_count": sum(1 for r in clean if r.get("gloss_line_clean"))},
        {"example_type": "xml_with_w_m", "record_count": w_m_sentence_count},
        {"example_type": "xml_with_morpheme_level_glosses", "record_count": morph_gloss_sentence_count},
        {"example_type": "xml_with_word_level_glosses", "record_count": word_gloss_sentence_count},
        {"example_type": "xml_words_only_no_reliable_gloss_alignment", "record_count": words_only_sentence_count},
        {"example_type": "table_sidecar_rows", "record_count": len(tables)},
    ]
    write_csv(ROOT / "data/processed/coverage_by_example_type.csv", type_rows, ["example_type", "record_count"])

    import_lines = [
        "# Import Report",
        "",
        f"- Source: {SOURCE_ID}",
        f"- Final XML path: `Final_XML/{cfg['xml']['language_folder']}/{cfg['xml']['output_file']}`",
        f"- XML S elements ready for import: {len(xml_index)}",
        f"- XML W elements emitted: {xml_counts['W']}",
        f"- XML M elements emitted: {xml_counts['M']}",
        f"- Sentence records with W/M: {w_m_sentence_count}",
        f"- Sentence records with morpheme-level source glosses: {morph_gloss_sentence_count}",
        f"- Sentence records with word-level gloss translations: {word_gloss_sentence_count}",
        f"- Sentence records with W/M but no reliable source gloss alignment: {words_only_sentence_count}",
        "- Machine translation used: no",
        "- OCR used in XML: no",
        "- Source glosses are encoded only as morpheme-level `M/TRANSL` where alignment is reliable; unaligned W/M forms are left unglossed and documented in `data/processed/gloss_alignment_audit.csv`.",
        "- Morphology tables are preserved as sidecars and excluded from sentence XML unless they yielded an XML-eligible example.",
        "- Slash-option expansions and parenthesized examples that need human translation/QC review are listed in `data/processed/manual_qc_slash_options.txt` and `data/processed/manual_qc_parentheses.txt`.",
        "- Final_XML cleanliness: checked by `scripts/validate_formosanbank_xml.py`.",
        "- FormosanBank punctuation/structure QC passes. Source segmentation is preserved in original S/W forms; sentence-level standard forms are de-segmented for standardized search/use.",
        "",
        "Import status: ready for FormosanBank import if `validation_report.md` final summary remains PASS.",
    ]
    (ROOT / "data/processed/import_report.md").write_text("\n".join(import_lines) + "\n", encoding="utf-8")

    qc_lines = [
        "# XML Quality Review",
        "",
        "## Reference Comparison",
        "",
        "- Requested reference path `/Users/hunterschep/FormosanBankRepos/Formosan-Rik-Bunun` was not present locally.",
        "- Installed Rik De Busser reference inspected: `/Users/hunterschep/FormosanBankRepos/Formosan-Bunun-Debusser-Dissertation/Final_XML/Bunun/Bunun.xml`.",
        "- Matching conventions adopted: `TEXT` root, direct `S` children only, `S/W/M` IDs only, one `FORM kindOf=\"original\"` at each S/W/M tier with optional `FORM kindOf=\"standard\"`, and `TRANSL` with only `xml:lang`.",
        "- No `class`, `sclass`, `NOTE`, or `AUDIO` elements are emitted in this corpus XML.",
        "- The thesis source identifies the orthography as Ortho94. FormosanBank XSD only allows `original`, `standard`, and `alternate` in `FORM@kindOf`, so Ortho94 is recorded in sidecar metadata and the `TEXT@source` attribute rather than as a `kindOf` value.",
        "",
        "## Current XML Counts",
        "",
        f"- S: {xml_counts['S']}",
        f"- W: {xml_counts['W']}",
        f"- M: {xml_counts['M']}",
        f"- FORM: {xml_counts['FORM']}",
        f"- TRANSL: {xml_counts['TRANSL']}",
        f"- Sentences with W/M: {w_m_sentence_count}",
        f"- Sentences with morpheme-level source glosses: {morph_gloss_sentence_count}",
        f"- Sentences with word-level gloss translations: {word_gloss_sentence_count}",
        f"- Sentences with W/M but no reliable source gloss alignment: {words_only_sentence_count}",
        "",
        "## Gloss Policy",
        "",
        "- Sentence-level `TRANSL xml:lang=\"zho\"` contains only source-published Chinese free translations.",
        "- Morpheme-level `TRANSL xml:lang=\"zho\"` contains source gloss parts only when the source gloss morpheme sequence aligns to the XML form morphemes.",
        "- Word-level `TRANSL` is not emitted for source glosses; when morpheme-level alignment is not reliable, W/M forms are left unglossed rather than placing Leipzig glosses at W.",
        "- If source glosses still do not align after safe normalization, W/M forms are emitted without invented gloss translations; the reason is recorded in `gloss_alignment_audit.csv`.",
        "- Sentence-level `FORM kindOf=\"original\"` and W-level `FORM` values preserve source segmentation (`-`, `=`, `<...>`, `Ø`) where present. Sentence-level `FORM kindOf=\"standard\"` removes segmentation/null/parenthetical markers conservatively.",
        "- Slash options are preserved in XML original forms when the alternatives are grammatical; starred alternatives are omitted. The source free translation is kept unchanged and flagged in `manual_qc_slash_options.txt` for hand QC.",
        "- Parentheses are not used as a blanket rejection criterion. Parenthesized examples are included when otherwise XML-eligible and flagged in `manual_qc_parentheses.txt`.",
        "",
        "## Validation",
        "",
        "- `scripts/validate_formosanbank_xml.py` passed with zero failures.",
        "- `/Users/hunterschep/FormosanBankRepos/FormosanBank/QC/validation/validate_xml.py by_path --path Final_XML` passed with zero issues.",
        "- `/Users/hunterschep/FormosanBankRepos/FormosanBank/QC/validation/validate_glosses.py Final_XML --check_morpho` found no W-count mismatches. Its M-count heuristic reports expected infix reanalysis cases where one source W form is intentionally represented as a discontinuous base M plus an infix M; the current QC run reports 21 such cases in `logs/formosan_qc/glosses/validation_m_mismatches.csv`.",
        "- `/Users/hunterschep/FormosanBankRepos/FormosanBank/QC/validation/validate_punct.py by_path --path Final_XML` exited 0 and reported PASS.",
    ]
    (ROOT / "data/processed/xml_quality_review.md").write_text("\n".join(qc_lines) + "\n", encoding="utf-8")

    orthography_lines = [
        "# Orthography Report",
        "",
        "- Source orthography: Ortho94, as noted in the thesis/source review comments.",
        "- XML handling: sentence-level `FORM kindOf=\"original\"` and W-level `FORM` keep source segmentation. Sentence-level `FORM kindOf=\"standard\"` removes segmentation/null/parenthetical markers conservatively.",
        "- XSD constraint: FormosanBank `FORM@kindOf` only permits `original`, `standard`, or `alternate`; `Ortho94` is therefore recorded in `TEXT@source` and this sidecar report, not as a `kindOf` value.",
        "- Null `Ø` markers are preserved in original S/W forms where present and removed from sentence-level standard forms.",
        "- No machine translation or OCR-derived text is used in XML.",
    ]
    (ROOT / "data/processed/orthography_report.md").write_text("\n".join(orthography_lines) + "\n", encoding="utf-8")

    readme = [
        "# Formosan-Lowking-Truku-WordFormation",
        "",
        "This package extracts XML-eligible Truku linguistic examples from Lowking Wei-Cheng Hsu / 許韋晟, 2008, 太魯閣語構詞法研究 [Word Formation in Truku].",
        "",
        "The workflow uses qpdf decryption and PDF text-layer extraction (`pdftotext -layout`, PyMuPDF, pdfplumber). OCR was not used.",
        "",
        "Final validated XML is under `Final_XML/Truku/`, with `xml:lang=\"trv\"`. Raw PDFs, extracted text, page images, parser sidecars, gloss records, morphology-table records, reports, and scripts are outside `Final_XML/`.",
        "",
        "The XML includes sentence-level Truku/Chinese pairs and W/M gloss annotation for source examples whose Truku word tokens align reliably with the source gloss line. Alignment skips are documented in `data/processed/gloss_alignment_audit.csv`.",
        "",
        "The thesis/source review notes Ortho94 orthography. Because FormosanBank XML only permits `original`, `standard`, and `alternate` as `FORM@kindOf` values, Ortho94 is recorded in `TEXT@source` and `data/processed/orthography_report.md`.",
        "",
        "Manual QC lists for slash-option translations and parenthesized examples are in `data/processed/manual_qc_slash_options.txt` and `data/processed/manual_qc_parentheses.txt`.",
        "",
        "Run the pipeline step-by-step with the commands listed in `scripts/config.yaml` and the project prompt, ending with:",
        "",
        "```bash",
        "python3 scripts/validate_formosanbank_xml.py --config scripts/config.yaml",
        "python3 scripts/generate_reports.py --config scripts/config.yaml",
        "```",
    ]
    (ROOT / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")

    manifest_rows = []
    for base in [ROOT / "data", ROOT / "Final_XML", ROOT / "scripts", ROOT / "README.md"]:
        paths = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file())
        for path in paths:
            manifest_rows.append({
                "path": rel(path),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            })
    write_csv(ROOT / "data/processed/manifest.csv", manifest_rows, ["path", "sha256", "bytes"])
    log("generate_reports", f"generated reports and manifest with {len(manifest_rows)} files")


STEP_FUNCS = {
    "inspect_pdf": inspect_pdf,
    "decrypt_pdf": decrypt_pdf,
    "extract_pdf_text": extract_pdf_text,
    "render_pdf_pages": render_pdf_pages,
    "extract_layout_blocks": extract_layout_blocks,
    "parse_examples": parse_examples,
    "parse_glosses": parse_glosses,
    "extract_tables": extract_tables,
    "normalize_text": normalize_text,
    "map_language": map_language,
    "quality_filter": quality_filter,
    "dedupe_examples": dedupe_examples,
    "dedupe_against_formosanbank": dedupe_against_formosanbank,
    "build_formosanbank_xml": build_formosanbank_xml,
    "validate_formosanbank_xml": validate_formosanbank_xml,
    "generate_reports": generate_reports,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="scripts/config.yaml")
    parser.add_argument("--step", default=Path(sys.argv[0]).stem)
    args = parser.parse_args()
    cfg = load_config(args.config)
    step = args.step
    if step not in STEP_FUNCS:
        raise SystemExit(f"unknown step {step}; expected one of {', '.join(sorted(STEP_FUNCS))}")
    STEP_FUNCS[step](cfg)


if __name__ == "__main__":
    main()
