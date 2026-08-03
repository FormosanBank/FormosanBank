from __future__ import annotations

import argparse
import csv
import hashlib
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
FINAL_XML = ROOT / "Final_XML"
XML_NS = "http://www.w3.org/XML/1998/namespace"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def has_han(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def numeric_or_punct_only(text: str) -> bool:
    return bool(text.strip()) and bool(re.fullmatch(r"[\W\d_]+", text.strip()))


def source_looks_english(text: str) -> bool:
    tokens = re.findall(r"[A-Za-z]+", text.casefold())
    if len(tokens) < 3:
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
        "my",
        "your",
        "his",
        "her",
        "our",
        "their",
    }
    marker = re.search(r"[':ˈʼ]|ng|ay|aw|an|en|ux|iy|ae|oe|S", text)
    return sum(t in stop for t in tokens) / len(tokens) >= 0.6 and not marker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-csv", default=str(PROCESSED / "final_xml_translation_audit.csv"))
    parser.add_argument("--output-report", default=str(PROCESSED / "final_xml_translation_audit_report.md"))
    args = parser.parse_args()

    xml_index: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(PROCESSED / "xml_index.csv"):
        xml_index[(row.get("xml_file", ""), row.get("sentence_id", ""))].append(row)
    rows: list[dict[str, str]] = []
    raw_hash_cache: dict[str, str] = {}

    for path in sorted(FINAL_XML.rglob("*.xml")):
        rel_xml = str(path.relative_to(ROOT))
        root = ET.parse(path).getroot()
        text_id = root.get("id", "")
        text_lang = root.get(f"{{{XML_NS}}}lang", "")
        xml_type = "lexical" if "_LEXICAL" in text_id or "_lexical" in path.name else "tmem"
        for s in root.findall("S"):
            sid = s.get("id", "")
            form = s.findtext("FORM", default="") or ""
            translations = s.findall("TRANSL") or [None]
            for transl_el in translations:
                target = transl_el.text if transl_el is not None and transl_el.text else ""
                target_lang = transl_el.get(f"{{{XML_NS}}}lang", "") if transl_el is not None else ""
                candidates = xml_index.get((rel_xml, sid), [])
                idx = next(
                    (
                        row
                        for row in candidates
                        if row.get("target_sentence_sha256") == sha256_text(target)
                    ),
                    candidates[0] if len(candidates) == 1 else {},
                )
                high: list[str] = []
                review: list[str] = []

                if not form.strip():
                    high.append("empty_form")
                if not target.strip():
                    high.append("empty_translation")
                if has_han(form):
                    high.append("han_in_formosan_form")
                if target_lang == "eng" and has_han(target):
                    high.append("han_in_english_translation")
                if target_lang == "zho" and not has_han(target):
                    high.append("no_han_in_chinese_translation")
                if "**" in form or "**" in target:
                    high.append("markdown_highlight_marker")
                if re.search(r"<[^>]+>", form) or re.search(r"<[^>]+>", target):
                    high.append("html_tag_text")
                if numeric_or_punct_only(form):
                    high.append("form_numeric_or_punct_only")
                if numeric_or_punct_only(target):
                    high.append("translation_numeric_or_punct_only")
                if xml_type == "lexical" and form.strip().casefold() == target.strip().casefold():
                    high.append("lexical_identical_source_target")
                if not idx:
                    high.append("missing_xml_index_row")
                else:
                    if idx.get("source_sentence_sha256") and idx["source_sentence_sha256"] != sha256_text(form):
                        high.append("source_hash_mismatch")
                    if idx.get("target_sentence_sha256") and idx["target_sentence_sha256"] != sha256_text(target):
                        high.append("target_hash_mismatch")
                    raw_path = idx.get("raw_json_path") or idx.get("raw_html_path_if_any")
                    if not raw_path:
                        high.append("missing_raw_provenance")
                    else:
                        full_raw = ROOT / raw_path
                        if not full_raw.exists():
                            high.append("raw_path_missing")
                        elif idx.get("raw_sha256"):
                            cached = raw_hash_cache.setdefault(str(full_raw), sha256_file(full_raw))
                            if cached != idx.get("raw_sha256"):
                                high.append("raw_sha256_mismatch")
                if form.strip().casefold() == target.strip().casefold() and xml_type != "lexical":
                    review.append("identical_source_target")
                if source_looks_english(form):
                    review.append("source_looks_english_by_stopword_heuristic")

                status = "fail" if high else "review" if review else "pass"
                rows.append(
                    {
                        "xml_file": rel_xml,
                        "text_id": text_id,
                        "sentence_id": sid,
                        "xml_type": xml_type,
                        "formosan_lang": text_lang,
                        "target_lang": target_lang,
                        "record_id": idx.get("record_id", ""),
                        "pair": idx.get("pair", ""),
                        "status": status,
                        "high_risk_issues": ";".join(high),
                        "review_issues": ";".join(review),
                        "form": form,
                        "translation": target,
                        "raw_path": idx.get("raw_json_path") or idx.get("raw_html_path_if_any", ""),
                        "source_url": idx.get("source_url", ""),
                    }
                )

    fields = [
        "xml_file",
        "text_id",
        "sentence_id",
        "xml_type",
        "formosan_lang",
        "target_lang",
        "record_id",
        "pair",
        "status",
        "high_risk_issues",
        "review_issues",
        "form",
        "translation",
        "raw_path",
        "source_url",
    ]
    write_csv(Path(args.output_csv), rows, fields)

    by_status = Counter(row["status"] for row in rows)
    by_issue = Counter(
        issue
        for row in rows
        for issue in row["high_risk_issues"].split(";")
        if issue
    )
    review_issue = Counter(
        issue
        for row in rows
        for issue in row["review_issues"].split(";")
        if issue
    )
    by_file = Counter(row["xml_file"] for row in rows if row["status"] != "pass")
    failed_examples = [row for row in rows if row["status"] == "fail"][:25]
    review_examples = [row for row in rows if row["status"] == "review"][:25]

    report = f"""# Final XML Translation Audit

Generated audit file: `{Path(args.output_csv).relative_to(ROOT)}`

## Scope

- XML files audited: {len(list(FINAL_XML.rglob("*.xml")))}
- XML units audited: {len(rows)}
- pass: {by_status.get("pass", 0)}
- review: {by_status.get("review", 0)}
- fail: {by_status.get("fail", 0)}

## High-Risk Issues

{chr(10).join(f"- {issue}: {count}" for issue, count in by_issue.most_common()) or "- None"}

## Review-Only Issues

{chr(10).join(f"- {issue}: {count}" for issue, count in review_issue.most_common()) or "- None"}

## Non-Passing Units By File

{chr(10).join(f"- {path}: {count}" for path, count in by_file.most_common()) or "- None"}

## Failed Examples

{chr(10).join(f"- {row['sentence_id']} `{row['high_risk_issues']}`: {row['form']} => {row['translation']}" for row in failed_examples) or "- None"}

## Review Examples

{chr(10).join(f"- {row['sentence_id']} `{row['review_issues']}`: {row['form']} => {row['translation']}" for row in review_examples) or "- None"}

## Interpretation

`fail` means the unit is not acceptable for Final_XML without remediation. `review` means the unit passed hard checks but may warrant human spot-checking because of conservative heuristics.
"""
    Path(args.output_report).write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
