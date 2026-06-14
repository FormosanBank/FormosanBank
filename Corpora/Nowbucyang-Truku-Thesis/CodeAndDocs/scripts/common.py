from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except Exception:  # pragma: no cover - PyYAML is installed for the project run.
    yaml = None


ROOT = Path(__file__).resolve().parents[1]
XML_NS = "http://www.w3.org/XML/1998/namespace"


def load_config(config_path: str | Path = "scripts/config.yaml") -> dict[str, Any]:
    path = Path(config_path)
    if not path.is_absolute():
        path = ROOT / path
    if yaml is None:
        raise RuntimeError("PyYAML is required to read scripts/config.yaml")
    with path.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    cfg["_config_path"] = str(path)
    return cfg


def rpath(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def ensure_dirs() -> None:
    for rel in [
        "data/raw/pdf",
        "data/raw/page_text",
        "data/raw/page_images",
        "data/raw/pdf_metadata",
        "data/processed",
        "data/scripts",
        "scripts",
        "logs",
        "Final_XML",
    ]:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)


def sha256_file(path: str | Path) -> str:
    p = Path(path)
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    out: list[dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line))
    return out


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            fh.write("\n")


def write_csv(path: str | Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_csv_dicts(path: str | Path) -> list[dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def run_cmd(cmd: list[str], timeout: int | None = None, check: bool = False) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{proc.stderr}")
    return proc


def copy_if_missing(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    shutil.copy2(src, dst)


CJK_RE = re.compile(r"[\u3400-\u9fff]")
LATIN_RE = re.compile(r"[A-Za-z]")
FORM_CHARS_RE = re.compile(r"[A-Za-z][A-Za-z0-9='’ʔ?*./<>Ø\\-]*")


def has_cjk(text: str) -> bool:
    return bool(CJK_RE.search(text or ""))


def has_latin(text: str) -> bool:
    return bool(LATIN_RE.search(text or ""))


def cjk_count(text: str) -> int:
    return len(CJK_RE.findall(text or ""))


def normalize_ws(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\s*\n\s*", "\n", text)
    text = re.sub(r" +([。！？；，、,.?!;:])", r"\1", text)
    return text.strip()


def clean_inline(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r" +([。！？；，、,.?!;:])", r"\1", text)
    return text.strip()


def page_text_path(page_one_based: int) -> Path:
    return ROOT / "data/raw/page_text" / f"page_{page_one_based:04d}.txt"


def page_image_path(page_one_based: int) -> Path:
    return ROOT / "data/raw/page_images" / f"page_{page_one_based:04d}.png"


def rel(path: str | Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def log(step: str, message: str) -> None:
    path = ROOT / "logs" / f"{step}.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(message.rstrip() + "\n")


def citation() -> str:
    return (
        "Hsu, Lowking Wei-Cheng 許韋晟. 2008. 太魯閣語構詞法研究 "
        "[Word Formation in Truku]. MA thesis, Graduate Institute of Taiwan "
        "Languages and Language Education, National Hsin-Chu University of Education."
    )


def bibtex() -> str:
    return (
        "@mastersthesis{Hsu_Lowking_Truku_WordFormation_2008, "
        "author = {Hsu, Lowking Wei-Cheng}, "
        "title = {太魯閣語構詞法研究 [Word Formation in Truku]}, "
        "school = {National Hsin-Chu University of Education}, "
        "address = {Hsinchu}, year = {2008}, month = {July}, "
        "note = {Used by FormosanBank with permission}}"
    )


def source_copyright() -> str:
    return "© Lowking Wei-Cheng Hsu / 許韋晟. Used by FormosanBank with permission."


def confidence_rank(value: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get((value or "").lower(), 0)
