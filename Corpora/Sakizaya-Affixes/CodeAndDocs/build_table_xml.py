#!/usr/bin/env python3
"""Build FormosanBank XML from Akiw 2012 affix inventory table rows."""

from __future__ import annotations

import csv
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from xml_tiers import add_form_pair, add_translation


ROOT = Path(__file__).resolve().parents[1]
VISION_OCR_DIR = ROOT / "Private/cache/vision_ocr_350"
TABLE_XML_PATH = ROOT / "XML/szy/akiw_2012_sakizaya_affixes_table_rows.xml"
REPORT_CSV = ROOT / "CodeAndDocs/table_extraction_report.csv"
SOURCE_DATA_DIR = ROOT / "CodeAndDocs/source_data"

XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("xml", XML_NS)


@dataclass
class OcrItem:
    page: int
    left: float
    top: float
    right: float
    bottom: float
    text: str


@dataclass
class TableRow:
    seq: int
    page: int
    form: str
    meaning_zho: str
    source_context: str
    raw_ocr: str
    status: str = "include"
    note: str = ""
    retained_xml_id: str = ""

    @property
    def xml_id(self) -> str:
        return f"AKIW_SZY_2012_TABLE_ROW_{self.seq:03d}"

    @property
    def source_label(self) -> str:
        return f"affix inventory table row {self.seq}; OCR page {self.page}"

    @property
    def base_form(self) -> str:
        return source_base_fields(self.form, self.source_context)[0]

    @property
    def base_meaning_zho(self) -> str:
        return source_base_fields(self.form, self.source_context)[1]

    @property
    def affix(self) -> AffixAnalysis:
        return affix_analysis_for_seq(self.seq)


@dataclass(frozen=True)
class AffixAnalysis:
    start: int
    end: int
    form: str
    meaning_zho: str
    source_table: str


# Source-transcribed table headings, row ranges, and OCR corrections live in
# CSV so the generator code does not own linguistic or source-critical data.
def load_affix_analyses() -> tuple[AffixAnalysis, ...]:
    path = SOURCE_DATA_DIR / "affix_analyses.csv"
    analyses: list[AffixAnalysis] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            analyses.append(
                AffixAnalysis(
                    start=int(row["start_seq"]),
                    end=int(row["end_seq"]),
                    form=row["affix_form"],
                    meaning_zho=row["affix_function_zho"],
                    source_table=row["source_table"],
                )
            )
    return tuple(analyses)


def load_table_row_fixes() -> dict[int, dict[str, str | int]]:
    path = SOURCE_DATA_DIR / "table_row_fixes.csv"
    fixes: dict[int, dict[str, str | int]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            seq = int(row["seq"])
            if seq in fixes:
                raise RuntimeError(f"Duplicate table row fix: {seq}")
            fixes[seq] = {
                "page": int(row["page"]),
                "form": row["form"],
                "meaning_zho": row["meaning_zho"],
                "source_context": row["source_context"],
                "allow_affix_form_mismatch": row["allow_affix_form_mismatch"].lower()
                == "true",
                "note": row["note"],
            }
    return fixes


AFFIX_ANALYSES = load_affix_analyses()
MANUAL_ROW_FIXES = load_table_row_fixes()
SOURCE_AFFIX_FORM_EXCEPTIONS = {
    seq
    for seq, fix in MANUAL_ROW_FIXES.items()
    if fix["allow_affix_form_mismatch"]
}


def affix_analysis_for_seq(seq: int) -> AffixAnalysis:
    matches = [analysis for analysis in AFFIX_ANALYSES if analysis.start <= seq <= analysis.end]
    if len(matches) != 1:
        raise RuntimeError(f"Inventory row {seq} has {len(matches)} affix analyses")
    return matches[0]


def ensure_vision_ocr_cache() -> None:
    required = VISION_OCR_DIR / "page-174.vision.tsv"
    if required.exists() and required.stat().st_size > 0:
        return
    script = ROOT / "CodeAndDocs/ocr_pages.py"
    subprocess.run([sys.executable, str(script), "--skip-tesseract"], check=True, cwd=ROOT)


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def has_roman(text: str) -> bool:
    return bool(re.search(r"[A-Za-z]", text))


def has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def clean_form(text: str) -> str:
    form = text.replace("’", "'").replace("‘", "'").replace("`", "'")
    form = form.replace("！", "'").replace("。", "")
    form = re.sub(r"\s+", " ", form).strip()
    form = re.sub(r"-\s+", "-", form)
    form = re.sub(r"\s+-", "-", form)
    form = re.sub(r"[\s\"〞\d]+$", "", form)
    return form.strip()


def split_form_and_tail(text: str) -> tuple[str, str]:
    normalized = text.replace("’", "'").replace("‘", "'").replace("`", "'").replace("！", "'")
    match = re.match(
        r"\s*([A-Za-z][A-Za-z'\.\-]*(?:\s*-\s*[A-Za-z'\.]+|\s+[A-Za-z][A-Za-z'\.\-]*)*)",
        normalized,
    )
    if not match:
        return "", text
    return clean_form(match.group(1)), normalized[match.end() :].strip()


def clean_meaning(text: str) -> str:
    cleaned = re.sub(r"\s+", "", text)
    cleaned = re.sub(r"[$\"〞]?\d+$", "", cleaned)
    cleaned = re.sub(r"[\"'“”＂〞]+$", "", cleaned)
    return cleaned.strip()


def clean_context(text: str) -> str:
    cleaned = clean_text(text)
    cleaned = cleaned.replace("•", "...")
    cleaned = cleaned.replace("！", "'")
    cleaned = re.sub(r"\bS1-", "si-", cleaned)
    cleaned = re.sub(r"\bmU-", "mu-", cleaned)
    cleaned = re.sub(r"\bSi-", "si-", cleaned)
    cleaned = re.sub(r"\btUSUZ\b", "tusuz", cleaned)
    cleaned = re.sub(r"--+", "-", cleaned)
    cleaned = re.sub(r"[$〞]?\d+\b", "", cleaned)
    cleaned = re.sub(r"(?<=[A-Za-z'\-])\s+(?=[A-Za-z'\-])", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def looks_like_affix_notation(text: str) -> bool:
    return bool(re.search(r"[-.…•]", text)) and not has_cjk(text)


def derive_base_from_form(form: str, affix_notation: str = "") -> str:
    pieces = [piece for piece in form.split("-") if piece]
    if len(pieces) <= 1:
        return form.strip("-")

    normalized_affix = affix_notation.replace("…", "...").replace("•", "...")
    if "..." in normalized_affix:
        prefix, suffix = normalized_affix.split("...", 1)
        prefix_count = len([piece for piece in prefix.split("-") if piece])
        suffix_count = len([piece for piece in suffix.split("-") if piece])
        end = len(pieces) - suffix_count if suffix_count else len(pieces)
        base = "-".join(pieces[prefix_count:end])
        if base:
            return base
    if normalized_affix.startswith("-") and not normalized_affix.endswith("-"):
        return "-".join(pieces[:-1])
    return "-".join(pieces[1:])


def source_base_fields(form: str, source_context: str) -> tuple[str, str]:
    """Recover the printed base/root and its Mandarin meaning from left table cells."""

    parts = [part.strip() for part in source_context.split("|") if part.strip()]
    affix = ""
    base = ""
    meaning = ""
    if len(parts) >= 3:
        affix, base, meaning = parts[0], parts[1], " | ".join(parts[2:])
    elif len(parts) == 2:
        first, second = parts
        if looks_like_affix_notation(first) and not has_cjk(second):
            affix, base = first, second
        elif looks_like_affix_notation(first):
            affix, meaning = first, second
        else:
            base, meaning = first, second
    elif parts:
        only = parts[0]
        if looks_like_affix_notation(only):
            affix = only
        elif has_cjk(only):
            meaning = only
        else:
            base = only

    if not base:
        base = derive_base_from_form(form, affix)
    normalized_base = base.replace("’", "'").replace("‘", "'").replace("`", "'")
    return normalized_base.rstrip("-").strip(), meaning.strip()


def load_page_items(page: int) -> list[OcrItem]:
    path = VISION_OCR_DIR / f"page-{page:03d}.vision.tsv"
    if not path.exists():
        return []
    items: list[OcrItem] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            text = clean_text(row.get("text") or "")
            if not text:
                continue
            items.append(
                OcrItem(
                    page=page,
                    left=float(row["left"]),
                    top=float(row["top"]),
                    right=float(row["right"]),
                    bottom=float(row["bottom"]),
                    text=text,
                )
            )
    return items


def group_items_into_rows(items: list[OcrItem]) -> list[list[OcrItem]]:
    groups: list[dict[str, object]] = []
    for item in sorted(items, key=lambda entry: ((entry.top + entry.bottom) / 2, entry.left)):
        center_y = (item.top + item.bottom) / 2
        for group in groups:
            if abs(center_y - float(group["center_y"])) < 32:
                group_items = group["items"]
                assert isinstance(group_items, list)
                group_items.append(item)
                group["center_y"] = (
                    float(group["center_y"]) * (len(group_items) - 1) + center_y
                ) / len(group_items)
                break
        else:
            groups.append({"center_y": center_y, "items": [item]})
    return [sorted(group["items"], key=lambda entry: entry.left) for group in groups]  # type: ignore[index]


def parse_table_row(items: list[OcrItem]) -> TableRow | None:
    numbered = [(index, item) for index, item in enumerate(items) if re.fullmatch(r"\d{1,3}", item.text)]
    if not numbered:
        return None
    seq_index, seq_item = numbered[0]
    seq = int(seq_item.text)
    if not (1 <= seq <= 434):
        return None
    after = items[seq_index + 1 :]
    if not any(has_roman(item.text) for item in after) or not any(has_cjk(item.text) for item in after):
        return None

    form_index: int | None = None
    for index, item in enumerate(after):
        if not has_roman(item.text):
            continue
        form, tail = split_form_and_tail(item.text)
        if not form:
            continue
        if re.fullmatch(r"[A-Za-z]+-+|-[A-Za-z]+|[A-Za-z]+-\.+", form):
            continue
        right_text = " ".join(piece.text for piece in after[index + 1 :])
        if has_cjk(tail) or has_cjk(right_text):
            form_index = index
    if form_index is None:
        return None

    form, tail = split_form_and_tail(after[form_index].text)
    meaning_parts = [tail] if has_cjk(tail) else []
    for item in after[form_index + 1 :]:
        if has_cjk(item.text):
            meaning_parts.append(item.text)
    meaning = clean_meaning("".join(meaning_parts))
    if not form or not meaning:
        return None

    raw_ocr = " | ".join(item.text for item in items)
    return TableRow(
        seq=seq,
        page=seq_item.page,
        form=form,
        meaning_zho=meaning,
        source_context=clean_context(" | ".join(item.text for item in after[:form_index])),
        raw_ocr=raw_ocr,
    )


def parse_rows_from_ocr() -> list[TableRow]:
    ensure_vision_ocr_cache()
    by_seq: dict[int, TableRow] = {}
    for page in range(50, 157):
        for row_items in group_items_into_rows(load_page_items(page)):
            parsed = parse_table_row(row_items)
            if parsed is None:
                continue
            existing = by_seq.get(parsed.seq)
            parsed_score = len(parsed.raw_ocr) + len(parsed.meaning_zho) * 3
            existing_score = len(existing.raw_ocr) + len(existing.meaning_zho) * 3 if existing else -1
            if parsed_score > existing_score:
                by_seq[parsed.seq] = parsed

    for seq, fix in MANUAL_ROW_FIXES.items():
        existing_raw = by_seq[seq].raw_ocr if seq in by_seq else ""
        by_seq[seq] = TableRow(
            seq=seq,
            page=int(fix["page"]),
            form=str(fix["form"]),
            meaning_zho=str(fix["meaning_zho"]),
            source_context=str(fix["source_context"]),
            raw_ocr=existing_raw,
            note=str(fix["note"]),
        )

    return [by_seq[seq] for seq in sorted(by_seq)]


def classify_rows(rows: list[TableRow]) -> list[TableRow]:
    """Account for exact repeats while retaining every page-located source row."""

    seen: dict[str, TableRow] = {}
    for row in rows:
        first = seen.get(row.form)
        if first is not None:
            row.status = "excluded_exact_repeat"
            row.retained_xml_id = first.xml_id
            row.note = (
                f"{row.note} Exact source-form repeat of inventory row {first.seq}; "
                f"represented by {first.xml_id}. This row's meaning remains in the ledger "
                "and is emitted as an alternate translation when distinct."
            ).strip()
        else:
            seen[row.form] = row
    return rows


def validate_source_bases(rows: list[TableRow]) -> None:
    failures: list[str] = []
    for row in rows:
        if not row.base_form or not re.fullmatch(r"[A-Za-z'’-]+", row.base_form):
            failures.append(f"row {row.seq}: invalid base {row.base_form!r}")
            continue
        normalized_base = row.base_form.lower().replace("’", "'").replace("-", "")
        normalized_form = row.form.lower().replace("’", "'").replace("-", "")
        if normalized_base not in normalized_form:
            failures.append(
                f"row {row.seq}: base {row.base_form!r} is not represented in {row.form!r}"
            )
    if failures:
        raise ValueError("Source-table base validation failed:\n" + "\n".join(failures))

    covered = {
        seq
        for analysis in AFFIX_ANALYSES
        for seq in range(analysis.start, analysis.end + 1)
    }
    if covered != set(range(1, 435)):
        raise ValueError("Affix analysis ranges must cover inventory rows 1-434 exactly")

    for row in rows:
        affix_letters = Counter(char.lower() for char in row.affix.form if char.isalpha())
        form_letters = Counter(char.lower() for char in row.form if char.isalpha())
        if affix_letters - form_letters and row.seq not in SOURCE_AFFIX_FORM_EXCEPTIONS:
            failures.append(
                f"row {row.seq}: affix {row.affix.form!r} is not represented in {row.form!r}"
            )
    if failures:
        raise ValueError("Source-table affix validation failed:\n" + "\n".join(failures))


def write_report(rows: list[TableRow]) -> None:
    REPORT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            lineterminator="\n",
            fieldnames=[
                "status",
                "seq",
                "page",
                "affix_form",
                "affix_function_zho",
                "affix_source",
                "form",
                "meaning_zho",
                "base_form",
                "base_meaning_zho",
                "source_context",
                "raw_ocr",
                "note",
                "retained_xml_id",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "status": row.status,
                    "seq": row.seq,
                    "page": row.page,
                    "affix_form": row.affix.form,
                    "affix_function_zho": row.affix.meaning_zho,
                    "affix_source": row.affix.source_table,
                    "form": row.form,
                    "meaning_zho": row.meaning_zho,
                    "base_form": row.base_form,
                    "base_meaning_zho": row.base_meaning_zho,
                    "source_context": row.source_context,
                    "raw_ocr": row.raw_ocr,
                    "note": row.note,
                    "retained_xml_id": row.retained_xml_id,
                }
            )


def write_xml(rows: list[TableRow]) -> None:
    TABLE_XML_PATH.parent.mkdir(parents=True, exist_ok=True)
    root = ET.Element(
        "TEXT",
        {
            "id": "AKIW_SZY_2012_SAKIZAYA_AFFIXES_TABLE_ROWS",
            "citation": (
                "Akiw, Chung-Wen Hsu. 2012. The Study of Affixes in Sakizaya. "
                "Master's thesis, National Dong Hwa University."
            ),
            "BibTeX_citation": (
                "@mastersthesis{Akiw_2012_Sakizaya_Affixes, "
                "author = {Akiw, Chung-Wen Hsu}, "
                "title = {The Study of Affixes in Sakizaya}, "
                "school = {National Dong Hwa University}, "
                "year = {2012}}"
            ),
            "copyright": (
                "Author permission recorded on Basecamp card 8176965975; "
                "private development corpus pending maintainer port-in approval."
            ),
            f"{{{XML_NS}}}lang": "szy",
            "source": (
                "akiw_2012_sakizaya_affixes_scan.pdf; affix inventory table rows; "
                "SHA-256 fab787faf0e32cd087ba3dc222734132ad4213ca0804b8d5b32a318e66fbbbee"
            ),
            "glottocode": "saki1247",
            "dialect": "Sakizaya",
        },
    )

    alternate_translations: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        if row.status == "excluded_exact_repeat" and row.retained_xml_id:
            alternate_translations[row.retained_xml_id].append(row.meaning_zho)

    for row in rows:
        if row.status != "include":
            continue
        sentence = ET.SubElement(
            root,
            "S",
            {
                "id": row.xml_id,
                "source": f"PDF page {row.page}; affix inventory row {row.seq}",
            },
        )
        add_form_pair(sentence, row.form)
        add_translation(sentence, row.meaning_zho)
        for alternate in alternate_translations.get(row.xml_id, []):
            if alternate != row.meaning_zho:
                add_translation(sentence, alternate, ver="alt")
        word = ET.SubElement(sentence, "W", {"id": f"{row.xml_id}W1"})
        add_form_pair(word, row.form)
        add_translation(word, row.meaning_zho, kind_of="original")

        affix = ET.SubElement(word, "M", {"id": f"{row.xml_id}W1M1"})
        add_form_pair(affix, row.affix.form)
        add_translation(affix, row.affix.meaning_zho, kind_of="original")

        root_morpheme = ET.SubElement(word, "M", {"id": f"{row.xml_id}W1M2"})
        add_form_pair(root_morpheme, row.base_form)
        add_translation(root_morpheme, row.base_meaning_zho, kind_of="original")

    ET.indent(root, space="    ")
    ET.ElementTree(root).write(TABLE_XML_PATH, encoding="utf-8", xml_declaration=True)


def main() -> None:
    rows = parse_rows_from_ocr()
    validate_source_bases(rows)
    rows = classify_rows(rows)
    write_report(rows)
    write_xml(rows)
    included = sum(1 for row in rows if row.status == "include")
    print(f"Wrote {TABLE_XML_PATH}")
    print(f"Wrote {REPORT_CSV}")
    print(f"Included {included} table rows")


if __name__ == "__main__":
    main()
